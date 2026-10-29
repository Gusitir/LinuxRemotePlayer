#!/bin/bash
set -e

# P7: Release process
# 1. Bump version in VERSION file.
# 2. Run ./scripts/build_deb.sh
# 3. Upload dist/linuxremoteplayer_<VERSION>_amd64.deb to website/downloads/

cd "$(dirname "${BASH_SOURCE[0]}")/.."

if [ ! -f "VERSION" ]; then
    echo "VERSION file not found! (e.g. echo 1.1.0 > VERSION)"
    exit 1
fi
VERSION=$(cat VERSION)

echo "Building linuxremoteplayer_${VERSION}_amd64.deb..."

echo "Running CSS sync check..."
python3 scripts/check_css_sync.py

# Clean old dist
rm -rf pkg dist
mkdir -p dist

# Create staging directories
mkdir -p pkg/opt/linuxremoteplayer
mkdir -p pkg/DEBIAN
mkdir -p pkg/usr/share/applications
mkdir -p pkg/usr/share/icons/hicolor/512x512/apps

cp frontend/icon-512.png pkg/usr/share/icons/hicolor/512x512/apps/linuxremoteplayer.png

cat <<EOF > pkg/usr/share/applications/linuxremoteplayer-panel.desktop
[Desktop Entry]
Type=Application
Name=LinuxRemotePlayer
Comment=Panel de estado y emparejamiento
Exec=xdg-open https://127.0.0.1:8000/status
Icon=linuxremoteplayer
Categories=AudioVideo;Video;Player;
Terminal=false
EOF

# Copy core components
cp -r backend frontend scripts VERSION pkg/opt/linuxremoteplayer/

# Inject VERSION into service worker for PWA cache invalidation
sed -i "s/__LRP_VERSION__/${VERSION}/" pkg/opt/linuxremoteplayer/frontend/sw.js
grep -q "lrp-${VERSION}" pkg/opt/linuxremoteplayer/frontend/sw.js || { echo "ERROR: sw.js sin versionar"; exit 1; }

# Cleanup excluded items (secrets, caches, and dev/build-only tooling not needed at runtime)
cd pkg/opt/linuxremoteplayer
rm -rf backend/.venv backend/certs backend/.pairing_token backend/.env backend/__pycache__ \
       scripts/__pycache__ scripts/dev scripts/build_deb.sh scripts/check_css_sync.py
cd ../../..

chmod +x pkg/opt/linuxremoteplayer/scripts/*.sh
chmod 0755 pkg/opt/linuxremoteplayer/scripts/debian/*.sh

# DEBIAN/control
cat <<EOF > pkg/DEBIAN/control
Package: linuxremoteplayer
Version: ${VERSION}
Architecture: amd64
Maintainer: LinuxRemotePlayer
Description: LinuxRemotePlayer API and web interface
Depends: python3, python3-venv, python3-dev, build-essential, openssl, sudo, curl, ca-certificates, python3-cryptography
Recommends: firefox-esr, ufw, pulseaudio-utils
EOF

# DEBIAN/postinst
cat <<'EOF' > pkg/DEBIAN/postinst
#!/bin/bash
set -e

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

# ASTRA-01: Ensure root:root ownership and 0755/0644 on /opt/linuxremoteplayer and .venv
chown -R root:root /opt/linuxremoteplayer
find /opt/linuxremoteplayer -type d -exec chmod 0755 {} +
find /opt/linuxremoteplayer -type f -exec chmod 0644 {} +
find /opt/linuxremoteplayer/scripts -type f -name "*.sh" -exec chmod 0755 {} +
if [ -d /opt/linuxremoteplayer/backend/.venv/bin ]; then
    chmod 0755 /opt/linuxremoteplayer/backend/.venv/bin/*
fi

# Ensure /var/lib/linuxremoteplayer exists and is owned by lrp:lrp 0700
if id -u lrp >/dev/null 2>&1; then
    mkdir -p /var/lib/linuxremoteplayer
    for _f in .env .pairing_token; do
        if [ -f "/opt/linuxremoteplayer/backend/$_f" ] && [ ! -f "/var/lib/linuxremoteplayer/$_f" ]; then
            cp -p "/opt/linuxremoteplayer/backend/$_f" "/var/lib/linuxremoteplayer/$_f"
            rm -f "/opt/linuxremoteplayer/backend/$_f"
        fi
    done
    if [ -d "/opt/linuxremoteplayer/backend/certs" ] && [ ! -d "/var/lib/linuxremoteplayer/certs" ]; then
        cp -rp "/opt/linuxremoteplayer/backend/certs" "/var/lib/linuxremoteplayer/certs"
        rm -rf "/opt/linuxremoteplayer/backend/certs"
    fi
    chown -R lrp:lrp /var/lib/linuxremoteplayer
    chmod 0700 /var/lib/linuxremoteplayer
fi

# Unattended bootstrap resume is invoked directly (no wrapper).
if grep -q '^phase=complete$' /var/lib/linuxremoteplayer/bootstrap/state 2>/dev/null \
   && grep -q '^phase=complete$' /var/lib/linuxremoteplayer/session/state 2>/dev/null \
   && command -v systemd-run >/dev/null 2>&1; then
    systemd-run --unit="linuxremoteplayer-bootstrap-ota-$$" --on-active=30s --no-block \
        /opt/linuxremoteplayer/scripts/debian/bootstrap.sh --resume --unattended || true
fi

echo "================================================="
echo " Paquete base instalado."
echo ""
echo " FALTA UN PASO. Para configurar el servicio ejecuta:"
echo "     sudo /opt/linuxremoteplayer/scripts/debian/bootstrap.sh --apply --approve"
echo "     sudo /opt/linuxremoteplayer/scripts/debian/bootstrap.sh --apply --approve --unattended"
echo "================================================="
EOF
chmod 755 pkg/DEBIAN/postinst

# DEBIAN/prerm
cat <<'EOF' > pkg/DEBIAN/prerm
#!/bin/bash
set -e
systemctl stop linuxremoteplayer.service 2>/dev/null || true
if [ "$1" = "remove" ]; then
    systemctl disable linuxremoteplayer.service 2>/dev/null || true
fi

# Limpieza de sistema SOLO al desinstalar de verdad. dpkg tambien corre el prerm
# en cada actualizacion con $1="upgrade": si esto se ejecutara ahi, cada update
# borraria las reglas udev y liberaria la licencia del dispositivo. Ver T-19.
if [ "$1" = "remove" ]; then
    if [ -x /opt/linuxremoteplayer/scripts/lrp-cleanup.sh ]; then
        /opt/linuxremoteplayer/scripts/lrp-cleanup.sh || true
    fi
fi

update-desktop-database /usr/share/applications 2>/dev/null || true
gtk-update-icon-cache /usr/share/icons/hicolor 2>/dev/null || true
EOF
chmod 755 pkg/DEBIAN/prerm

chmod -R 0755 pkg/DEBIAN

dpkg-deb --root-owner-group --build pkg dist/linuxremoteplayer_${VERSION}_amd64.deb
cd dist
sha256sum linuxremoteplayer_${VERSION}_amd64.deb > linuxremoteplayer_${VERSION}_amd64.deb.sha256
echo "Done! Wrote dist/linuxremoteplayer_${VERSION}_amd64.deb and sha256."
