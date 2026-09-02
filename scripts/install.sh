#!/bin/bash
set -e

echo "======================================"
echo " LinuxRemotePlayer Installer          "
echo "======================================"

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo ./install.sh)"
  exit 1
fi

TARGET_USER="lrp"
USER_RECORD=$(getent passwd "$TARGET_USER" 2>/dev/null || true)
if [ -z "$USER_RECORD" ]; then
    echo "[!] ABORTANDO: T-124 user lrp is required; it will not be created."
    exit 1
fi
IFS=: read -r _ _ USER_UID _ _ USER_HOME USER_SHELL <<EOF
$USER_RECORD
EOF
if [ "$USER_UID" = "0" ] || [ "$USER_HOME" != "/home/lrp" ] || [ "$USER_SHELL" != "/bin/bash" ] || [ ! -d "$USER_HOME" ]; then
    echo "[!] ABORTANDO: existing lrp must be non-root with /home/lrp and /bin/bash."
    exit 1
fi

echo "[i] Configurando para el usuario: $TARGET_USER"

if [ ! -t 0 ] && [ -e /dev/tty ]; then exec < /dev/tty; fi

AUTO_LAYOUT="us"
if command -v localectl >/dev/null 2>&1; then
    _x11=$(localectl status | grep 'X11 Layout' | awk '{print $3}' | tr -d ' ' || true)
    if [ "$_x11" = "es" ] || [ "$_x11" = "latam" ]; then
        AUTO_LAYOUT="$_x11"
    fi
fi

if [ "${LRP_NONINTERACTIVE:-0}" = 1 ]; then
    kb_layout="${LRP_KEYBOARD:-${KEYBOARD_LAYOUT:-$AUTO_LAYOUT}}"
elif [ -n "$LRP_KEYBOARD" ]; then
    kb_layout="$LRP_KEYBOARD"
else
    echo "¿Selecciona layout de teclado de esta PC?"
    echo "[1] US (defecto)"
    echo "[2] ES (España)"
    echo "[3] LATAM"
    read -p "Selección (detectado: $AUTO_LAYOUT) [1/2/3/Enter]: " kb_ans
    case "$kb_ans" in
        2) kb_layout="es" ;;
        3) kb_layout="latam" ;;
        1) kb_layout="us" ;;
        *) kb_layout="$AUTO_LAYOUT" ;;
    esac
fi

# Install dependencies (including avahi-daemon for mDNS hostname resolution)
apt-get update
apt-get install -y python3-venv python3-dev openssl wmctrl pulseaudio-utils firefox-esr

# Define BACKEND_DIR for systemd paths and token generation
BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../backend" && pwd)"
cd "$BACKEND_DIR"

# Normalize every legacy mode assignment while preserving all other environment lines.
if grep -Eq "^[[:space:]]*LRP_MODE[[:space:]]*=" "$BACKEND_DIR/.env" 2>/dev/null; then
    sed -i -E 's/^[[:space:]]*LRP_MODE[[:space:]]*=.*$/LRP_MODE=htpc/' "$BACKEND_DIR/.env"
else
    echo "LRP_MODE=htpc" >> "$BACKEND_DIR/.env"
fi

# Write keyboard layout to .env
if grep -q "^KEYBOARD_LAYOUT=" "$BACKEND_DIR/.env" 2>/dev/null; then
    sed -i "s/^KEYBOARD_LAYOUT=.*/KEYBOARD_LAYOUT=$kb_layout/" "$BACKEND_DIR/.env"
else
    echo "KEYBOARD_LAYOUT=$kb_layout" >> "$BACKEND_DIR/.env"
fi

# (Venv is now managed by the .deb postinst script globally)

# Fix permissions: Give full ownership of the app directory to the user
# so they can write tokens, caches, and logs without sudo errors.
chown -R "$TARGET_USER":"$TARGET_USER" /opt/linuxremoteplayer


# Validate venv dependencies
if [ -f /opt/linuxremoteplayer/.deps_incomplete ] || ! "$BACKEND_DIR/.venv/bin/python" -c "import fastapi, evdev, segno" 2>/dev/null; then
    echo -e "\n\e[31m[!] Dependencias incompletas. La instalación falló durante 'pip install'.\e[0m"
    echo -e "\e[31m[!] Ejecuta: sudo /opt/linuxremoteplayer/backend/.venv/bin/pip install -r /opt/linuxremoteplayer/backend/requirements.txt\e[0m"
    echo -e "\e[31m[!] Luego vuelve a ejecutar: sudo lrp-setup\e[0m"
    exit 1
fi
rm -f /opt/linuxremoteplayer/.deps_incomplete

# Pre-generate pairing token if not exists (SEC-01)
sudo -u "$TARGET_USER" "$BACKEND_DIR/.venv/bin/python" -c "
import os, secrets
token_file = os.path.join('$BACKEND_DIR', '.pairing_token')
if not os.path.exists(token_file):
    token = secrets.token_urlsafe(16)
    with open(token_file, 'w') as f:
        f.write(token)
    os.chmod(token_file, 0o600)
"

# --- HTTPS (automatic) ---
echo "[i] HTTPS will be enabled automatically on first start (self-signed cert)."

cleanup_legacy_user_unit() {
    local legacy_user="$1" legacy_record legacy_home legacy_uid legacy_unit
    [ -n "$legacy_user" ] && [ "$legacy_user" != root ] || return 0
    legacy_record=$(getent passwd "$legacy_user" 2>/dev/null || true)
    [ -n "$legacy_record" ] || return 0
    legacy_home=$(printf '%s\n' "$legacy_record" | awk -F: 'NF >= 7 {print $6}')
    legacy_uid=$(id -u "$legacy_user" 2>/dev/null || true)
    legacy_unit="$legacy_home/.config/systemd/user/linuxremoteplayer.service"
    [ -n "$legacy_uid" ] && [ -f "$legacy_unit" ] || return 0
    sudo -u "$legacy_user" XDG_RUNTIME_DIR="/run/user/$legacy_uid" systemctl --user stop linuxremoteplayer.service 2>/dev/null || true
    sudo -u "$legacy_user" XDG_RUNTIME_DIR="/run/user/$legacy_uid" systemctl --user disable linuxremoteplayer.service 2>/dev/null || true
    rm -f "$legacy_unit"
}
cleanup_legacy_user_unit "$TARGET_USER"
if [ -n "${SUDO_USER:-}" ] && [ "$SUDO_USER" != root ] && [ "$SUDO_USER" != "$TARGET_USER" ]; then
    cleanup_legacy_user_unit "$SUDO_USER"
fi

cat <<EOF > /etc/systemd/system/linuxremoteplayer.service
[Unit]
Description=Linux Remote Player Backend API
Wants=network-online.target
After=display-manager.service network-online.target

[Service]
Type=simple
User=lrp
WorkingDirectory=$BACKEND_DIR
Environment="APPLIANCE_IDLE_PANEL=true"
ExecStart="$BACKEND_DIR/.venv/bin/python" run.py
Restart=always
RestartSec=5

[Install]
WantedBy=graphical.target
EOF
systemctl daemon-reload
systemctl enable linuxremoteplayer.service
systemctl restart linuxremoteplayer.service

echo "Configuring Debian HTPC Mode..."
echo "[i] Autologin is managed by the T-124 LightDM session bootstrap."

HOSTNAME_LOCAL="$(hostname).local"
IP_ADDR=$(python3 -c "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(('1.1.1.1', 80)); print(s.getsockname()[0]); s.close()" || echo "<your-ip>")

echo "======================================"
echo "    LinuxRemotePlayer installed!      "
echo "======================================"
echo " Pasos para conectar tu teléfono:"
echo "   1) Abre en tu teléfono:"
echo "      https://$HOSTNAME_LOCAL:8000"
echo "      (o https://$IP_ADDR:8000)"
echo "   2) Acepta la advertencia de certificado (solo la primera vez)."
echo "   3) Escribe el PIN que muestra el panel en tu TV."
echo " "
echo "   Introduce el PIN que muestra el panel en tu TV para emparejar."
echo "======================================"

echo "[i] Waiting for service to start..."
for i in {1..15}; do
  if curl -sk https://127.0.0.1:8000/health >/dev/null 2>&1; then break; fi
  sleep 1
done

echo "[i] Waiting for CA certificate generation (up to 30s)..."
for i in {1..30}; do
  if [ -f "$BACKEND_DIR/certs/ca.pem" ]; then break; fi
  sleep 1
done

# Write policies before system trust setup so policy creation cannot be blocked.
echo "[i] Configuring Firefox policies..."
mkdir -p /etc/firefox/policies
cat <<EOFJSON > /etc/firefox/policies/policies.json
{
  "policies": {
    "ExtensionSettings": {
      "uBlock0@raymondhill.net": {
        "installation_mode": "force_installed",
        "install_url": "https://addons.mozilla.org/firefox/downloads/latest/ublock-origin/latest.xpi"
      }
    },
    "Certificates": {
      "ImportEnterpriseRoots": true,
      "Install": ["$BACKEND_DIR/certs/ca.pem"]
    },
    "EncryptedMediaExtensions": { "Enabled": true },
    "DisableFirefoxStudies": true,
    "OverrideFirstRunPage": "",
    "NoDefaultBookmarks": true
  }
}
EOFJSON

PLATFORM_CA_PATH=""
[ -f "$BACKEND_DIR/certs/ca.pem" ] && PLATFORM_CA_PATH="$BACKEND_DIR/certs/ca.pem"
echo "[i] Applying Debian platform configuration..."
if [ -n "$PLATFORM_CA_PATH" ]; then
    /opt/linuxremoteplayer/scripts/debian/platform-bootstrap.sh --apply --approve --ca-path "$PLATFORM_CA_PATH"
else
    /opt/linuxremoteplayer/scripts/debian/platform-bootstrap.sh --apply --approve
fi

echo "======================================"
echo " Panel de estado (ábrelo en el navegador"
echo " de ESTA TV si no se abrió solo):        "
echo "   https://localhost:8000/status"
echo "   https://127.0.0.1:8000/status"
echo "======================================"
