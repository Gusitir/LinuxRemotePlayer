#!/bin/bash
set -e

# P7: Release process
# 1. Bump version in VERSION file.
# 2. Run ./scripts/build_deb.sh
# 3. Upload dist/linuxremoteplayer_<VERSION>_all.deb to website/downloads/
# 4. Update website/latest.json with new version, url, and sha256.

cd "$(dirname "${BASH_SOURCE[0]}")/.."

if [ ! -f "VERSION" ]; then
    echo "VERSION file not found! (e.g. echo 1.1.0 > VERSION)"
    exit 1
fi
VERSION=$(cat VERSION)

echo "Building linuxremoteplayer_${VERSION}_all.deb..."

# Clean old dist
rm -rf pkg dist
mkdir -p dist

# Create staging directories
mkdir -p pkg/opt/linuxremoteplayer
mkdir -p pkg/DEBIAN
mkdir -p pkg/usr/local/bin
mkdir -p pkg/etc/sudoers.d
mkdir -p pkg/usr/share/applications
mkdir -p pkg/usr/share/icons/hicolor/512x512/apps

cp frontend/icon-512.png pkg/usr/share/icons/hicolor/512x512/apps/linuxremoteplayer.png

cat <<EOF > pkg/usr/share/applications/linuxremoteplayer-panel.desktop
[Desktop Entry]
Type=Application
Name=Remote Linux Player
Comment=Panel de estado y emparejamiento
Exec=sh -c 'chromium --app=https://127.0.0.1:8000/status || chromium-browser --app=https://127.0.0.1:8000/status'
Icon=linuxremoteplayer
Categories=AudioVideo;Video;Player;
Terminal=false
EOF

# Copy core components
cp -r backend frontend scripts VERSION pkg/opt/linuxremoteplayer/

# Cleanup excluded items
cd pkg/opt/linuxremoteplayer
rm -rf backend/.venv backend/certs backend/.pairing_token backend/.env backend/__pycache__ scripts/__pycache__
cd ../../..

chmod +x pkg/opt/linuxremoteplayer/scripts/*.sh

# DEBIAN/control
cat <<EOF > pkg/DEBIAN/control
Package: linuxremoteplayer
Version: ${VERSION}
Architecture: all
Maintainer: LinuxRemotePlayer
Description: Remote Linux Player API and web interface
Depends: python3, python3-venv, python3-dev, build-essential, openssl, avahi-daemon
Recommends: chromium | chromium-browser, ufw
EOF

# DEBIAN/postinst
cat <<'EOF' > pkg/DEBIAN/postinst
#!/bin/bash
set -e

# Permissions for evdev / uinput
modprobe uinput || true
echo uinput > /etc/modules-load.d/uinput.conf
echo 'KERNEL=="uinput", MODE="0660", GROUP="input", OPTIONS+="static_node=uinput"' > /etc/udev/rules.d/99-uinput.rules
udevadm control --reload-rules || true
udevadm trigger || true

BACKEND_DIR=/opt/linuxremoteplayer/backend
cd "$BACKEND_DIR"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
set +e
if ! .venv/bin/pip install -r requirements.txt; then
    echo "[!] Advertencia: falló pip install. Dependencias incompletas."
    touch /opt/linuxremoteplayer/.deps_incomplete
fi
set -e

# Create lrp-setup
cat <<'INNEREOF' > /usr/local/bin/lrp-setup
#!/bin/bash
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo lrp-setup)"
  exit 1
fi
cd /opt/linuxremoteplayer/scripts
./install.sh
INNEREOF
chmod 755 /usr/local/bin/lrp-setup

# Create lrp-update wrapper
cat <<'INNEREOF' > /usr/local/bin/lrp-update
#!/bin/bash
set -e
export DEBIAN_FRONTEND=noninteractive
MANIFEST_URL="${UPDATE_MANIFEST_URL:-https://linux-remote-player.vercel.app/latest.json}"
echo "Checking $MANIFEST_URL for updates..."
LATEST_JSON=$(curl -fsSL "$MANIFEST_URL")
VERSION=$(echo "$LATEST_JSON" | grep -o '"version"\s*:\s*"[^"]*"' | cut -d'"' -f4)
DEB_URL=$(echo "$LATEST_JSON" | grep -o '"deb_url"\s*:\s*"[^"]*"' | cut -d'"' -f4)
SHA256=$(echo "$LATEST_JSON" | grep -o '"sha256"\s*:\s*"[^"]*"' | cut -d'"' -f4)

cd /tmp
echo "Downloading $DEB_URL..."
# Snap-packaged curl cannot write files outside $HOME (error 23). Fall back to wget.
if ! curl -fsSL -o "linuxremoteplayer_${VERSION}_all.deb" "$DEB_URL" 2>/dev/null; then
    echo "[!] curl no pudo escribir el archivo (¿curl de snap?). Intentando con wget..."
    wget -qO "linuxremoteplayer_${VERSION}_all.deb" "$DEB_URL"
fi
if [ ! -s "linuxremoteplayer_${VERSION}_all.deb" ]; then
    echo "[!] ERROR: no se pudo descargar la actualización. Instala el curl real: sudo apt install curl"
    exit 1
fi

echo "$SHA256 linuxremoteplayer_${VERSION}_all.deb" | sha256sum -c -

apt-get install -y --reinstall "./linuxremoteplayer_${VERSION}_all.deb"

# Restart services depending on mode
if systemctl is-enabled linuxremoteplayer.service &>/dev/null; then
    systemctl restart linuxremoteplayer.service || true
else
    # find user services
    for d in /run/user/*; do
        if [ -d "$d" ]; then
            uid=$(basename "$d")
            sudo -u "#$uid" XDG_RUNTIME_DIR="$d" systemctl --user restart linuxremoteplayer.service || true
        fi
    done
fi

# Update uBlock Origin Lite (in the user's HOME — snap Chromium cannot read /opt)
echo "Actualizando uBlock Origin Lite..."
UBOL_HOME=$(getent passwd "${SUDO_USER:-root}" | cut -d: -f6)
if [ -n "$UBOL_HOME" ] && [ "$UBOL_HOME" != "/root" ]; then
    UBOL_DIR="$UBOL_HOME/lrp-extensions/ubol"
else
    UBOL_DIR="/opt/linuxremoteplayer/extensions/ubol"
fi
mkdir -p "$UBOL_DIR"
if curl -fsSL "https://github.com/uBlockOrigin/uBOL-home/releases/latest/download/uBOLite_mv3.zip" -o /tmp/ubol.zip 2>/dev/null || wget -qO /tmp/ubol.zip "https://github.com/uBlockOrigin/uBOL-home/releases/latest/download/uBOLite_mv3.zip"; then
    unzip -qo /tmp/ubol.zip -d "$UBOL_DIR" || true
    rm -f /tmp/ubol.zip
else
    echo "[!] No se pudo actualizar uBOL (continuando sin él)."
fi
# Fix ownership of the extension dir for the real user
if [ -n "$SUDO_USER" ] && [ "$SUDO_USER" != "root" ]; then
    chown -R "$SUDO_USER":"$SUDO_USER" "$(dirname "$UBOL_DIR")" 2>/dev/null || true
fi
INNEREOF
chmod 755 /usr/local/bin/lrp-update

echo "================================================="
echo " Instalación base completada. "
echo " Ejecuta: sudo lrp-setup para configurar tu modo."
echo "================================================="
EOF
chmod 755 pkg/DEBIAN/postinst

# DEBIAN/prerm
cat <<'EOF' > pkg/DEBIAN/prerm
#!/bin/bash
set -e
systemctl stop linuxremoteplayer.service 2>/dev/null || true
systemctl disable linuxremoteplayer.service 2>/dev/null || true

for d in /run/user/*; do
    if [ -d "$d" ]; then
        uid=$(basename "$d")
        sudo -u "#$uid" XDG_RUNTIME_DIR="$d" systemctl --user stop linuxremoteplayer.service 2>/dev/null || true
        sudo -u "#$uid" XDG_RUNTIME_DIR="$d" systemctl --user disable linuxremoteplayer.service 2>/dev/null || true
    fi
done

update-desktop-database /usr/share/applications 2>/dev/null || true
gtk-update-icon-cache /usr/share/icons/hicolor 2>/dev/null || true
EOF
chmod 755 pkg/DEBIAN/prerm

# sudoers
echo "%input ALL=(root) NOPASSWD: /usr/local/bin/lrp-update" > pkg/etc/sudoers.d/linuxremoteplayer
chmod 440 pkg/etc/sudoers.d/linuxremoteplayer

chmod -R 0755 pkg/DEBIAN

dpkg-deb --root-owner-group --build pkg dist/linuxremoteplayer_${VERSION}_all.deb
cd dist
sha256sum linuxremoteplayer_${VERSION}_all.deb > linuxremoteplayer_${VERSION}_all.deb.sha256
echo "Done! Wrote dist/linuxremoteplayer_${VERSION}_all.deb and sha256."
