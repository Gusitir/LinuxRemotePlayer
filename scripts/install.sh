#!/bin/bash
set -e

echo "======================================"
echo " LinuxRemotePlayer Installer          "
echo "======================================"

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo ./install.sh)"
  exit 1
fi

TARGET_USER=""
if [ -n "$SUDO_USER" ] && [ "$SUDO_USER" != "root" ]; then
    TARGET_USER="$SUDO_USER"
elif logname >/dev/null 2>&1 && [ "$(logname)" != "root" ]; then
    TARGET_USER="$(logname)"
else
    # Try to find the active graphical session owner
    if command -v loginctl >/dev/null 2>&1; then
        TARGET_USER=$(loginctl list-sessions --no-legend | awk '$3!="root"{print $3; exit}')
    fi
fi

if [ -n "$TARGET_USER" ]; then
    read -p "¿Qué usuario usará la TV? [$TARGET_USER]: " PROMPT_USER
    if [ -n "$PROMPT_USER" ]; then
        TARGET_USER="$PROMPT_USER"
    fi
else
    read -p "¿Qué usuario usará la TV?: " TARGET_USER
fi

if [ -z "$TARGET_USER" ] || [ "$TARGET_USER" = "root" ]; then
    echo -e "\e[31m[!] ABORTANDO: No se pudo determinar un usuario válido o se especificó 'root'. Nunca configures este servicio para root.\e[0m"
    exit 1
fi

echo "[i] Configurando para el usuario: $TARGET_USER"
USER_HOME=$(getent passwd "$TARGET_USER" | cut -d: -f6)

if [ ! -t 0 ] && [ -e /dev/tty ]; then exec < /dev/tty; fi

if [ -n "$LRP_MODE" ]; then
    mode="$LRP_MODE"
    echo "[i] Using mode from LRP_MODE environment variable: $mode"
else
    read -p "¿Esta PC está dedicada a la TV? [S/n]: " ans
    if [ "$ans" = "n" ] || [ "$ans" = "N" ]; then
        mode="2"
    else
        mode="1"
    fi
fi

# Install dependencies (including avahi-daemon for mDNS hostname resolution)
apt-get update
apt-get install -y python3-venv python3-dev ufw openssl avahi-daemon
systemctl enable --now avahi-daemon || true

# --- evdev / uinput permissions (FIX F1: Phase 6 blocker) ---
modprobe uinput || true
echo uinput > /etc/modules-load.d/uinput.conf
echo 'KERNEL=="uinput", MODE="0660", GROUP="input", OPTIONS+="static_node=uinput"' > /etc/udev/rules.d/99-uinput.rules
usermod -aG input "$TARGET_USER"
udevadm control --reload-rules && udevadm trigger
echo "[i] Added '$TARGET_USER' to 'input' group. REBOOT or re-login required before uinput works."

# --- Ensure Chromium is installed ---
if command -v chromium >/dev/null 2>&1 || command -v chromium-browser >/dev/null 2>&1; then
    echo "[i] Chromium already installed."
else
    echo "[i] Chromium not found. Installing..."
    if apt-get install -y chromium; then
        echo "[i] Installed 'chromium'."
    elif apt-get install -y chromium-browser; then
        echo "[i] Installed 'chromium-browser'."
    elif command -v snap >/dev/null 2>&1 && snap install chromium; then
        echo "[i] Installed Chromium via snap."
    else
        echo "[!] Could not install Chromium automatically. Install it manually: sudo apt install chromium"
    fi
fi

# Define BACKEND_DIR for systemd paths and token generation
BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../backend" && pwd)"
cd "$BACKEND_DIR"

# (Venv is now managed by the .deb postinst script globally)

# Fix permissions: Give full ownership of the app directory to the user
# so they can write tokens, caches, and logs without sudo errors.
chown -R "$TARGET_USER":"$TARGET_USER" /opt/linuxremoteplayer

# P5: Ad-blocking (uBlock Origin Lite)
# IMPORTANT: installed in the user's HOME, NOT /opt — snap-packaged Chromium
# (Ubuntu/KDE Neon) cannot read /opt due to snap confinement.
UBOL_DIR="$USER_HOME/lrp-extensions/ubol"
echo "[i] Descargando uBlock Origin Lite para bloqueo de anuncios en el Kiosko..."
mkdir -p "$UBOL_DIR"
# The release asset is version-stamped (e.g. uBOLite_2026.614.1502.chromium.zip),
# so there is NO stable /latest/download/<fixed-name> URL. Resolve it from the API.
UBOL_ZIP_URL=$(curl -fsSL "https://api.github.com/repos/uBlockOrigin/uBOL-home/releases/latest" 2>/dev/null \
    | grep -o '"browser_download_url": *"[^"]*\.chromium\.zip"' | head -n1 | cut -d'"' -f4)
if [ -z "$UBOL_ZIP_URL" ]; then
    UBOL_ZIP_URL="https://github.com/uBlockOrigin/uBOL-home/releases/latest/download/uBOLite.chromium.zip"
fi
echo "[i] uBOL: $UBOL_ZIP_URL"
if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$UBOL_ZIP_URL" -o /tmp/ubol.zip 2>/dev/null || wget -qO /tmp/ubol.zip "$UBOL_ZIP_URL"
else
    wget -qO /tmp/ubol.zip "$UBOL_ZIP_URL"
fi
if [ -s /tmp/ubol.zip ]; then
    command -v unzip >/dev/null 2>&1 || apt-get install -y unzip
    unzip -qo /tmp/ubol.zip -d "$UBOL_DIR" || echo "[!] No se pudo extraer uBOL; el kiosk funcionará sin bloqueador."
    rm -f /tmp/ubol.zip
    if [ -d "$UBOL_DIR" ] && [ ! -f "$UBOL_DIR/manifest.json" ]; then
        SUBDIR=$(find "$UBOL_DIR" -mindepth 1 -maxdepth 1 -type d | head -n 1)
        if [ -n "$SUBDIR" ] && [ -f "$SUBDIR/manifest.json" ]; then
            mv "$SUBDIR"/* "$UBOL_DIR"/
            rmdir "$SUBDIR"
        fi
    fi
else
    echo "[!] No se pudo descargar el bloqueador de anuncios; el kiosk funcionará sin él."
fi
chown -R "$TARGET_USER":"$TARGET_USER" "$USER_HOME/lrp-extensions" 2>/dev/null || true

# Validate venv dependencies
if [ -f /opt/linuxremoteplayer/.deps_incomplete ] || ! "$BACKEND_DIR/.venv/bin/python" -c "import fastapi, evdev, segno" 2>/dev/null; then
    echo -e "\n\e[31m[!] Dependencias incompletas. La instalación falló durante 'pip install'.\e[0m"
    echo -e "\e[31m[!] Ejecuta: sudo /opt/linuxremoteplayer/backend/.venv/bin/pip install -r /opt/linuxremoteplayer/backend/requirements.txt\e[0m"
    echo -e "\e[31m[!] Luego vuelve a ejecutar: sudo lrp-setup\e[0m"
    exit 1
fi
rm -f /opt/linuxremoteplayer/.deps_incomplete

# Configure UFW
ufw allow 8000/tcp
if [ "$mode" = "1" ]; then
    echo "[i] Enabling UFW firewall for Appliance Mode (allowing OpenSSH first)..."
    ufw allow OpenSSH || ufw allow 22/tcp
    ufw --force enable
else
    if ufw status | grep -q "inactive"; then
      echo "[!] WARNING: UFW firewall is currently INACTIVE. The allow rule for port 8000 will have no effect until you enable it (sudo ufw enable)."
    fi
fi

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

if [ "$mode" == "1" ]; then
    echo "Configuring Appliance Mode..."
    echo "[!] Note: Autologin configuration must be done manually depending on your Display Manager."

    echo "[i] Disabling screen locker and DPMS for KDE Plasma..."
    sudo -u "$TARGET_USER" bash -c '
        if command -v kwriteconfig5 >/dev/null 2>&1; then
            KWRITE="kwriteconfig5"
        elif command -v kwriteconfig6 >/dev/null 2>&1; then
            KWRITE="kwriteconfig6"
        else
            KWRITE=""
        fi
        if [ -n "$KWRITE" ]; then
            $KWRITE --file kscreenlockerrc --group Daemon --key Autolock false
            $KWRITE --file kscreenlockerrc --group Daemon --key LockOnResume false
            $KWRITE --file powermanagementprofilesrc --group AC --group DPMSControl --key idleTime 0
            $KWRITE --file powermanagementprofilesrc --group AC --group SuspendSession --key idleTime 0
            $KWRITE --file powermanagementprofilesrc --group AC --group DimDisplay --key idleTime 0
        fi
    '

    USER_SVC_DIR="$USER_HOME/.config/systemd/user"
    if [ -f "$USER_SVC_DIR/linuxremoteplayer.service" ]; then
        echo "[i] Removing previous Desktop Mode configuration..."
        export XDG_RUNTIME_DIR="/run/user/$(id -u "$TARGET_USER")"
        sudo -u "$TARGET_USER" XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" systemctl --user stop linuxremoteplayer.service 2>/dev/null || true
        sudo -u "$TARGET_USER" XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" systemctl --user disable linuxremoteplayer.service 2>/dev/null || true
        rm -f "$USER_SVC_DIR/linuxremoteplayer.service"
    fi

    # Added After=display-manager.service (COR-04)
    cat <<EOF > /etc/systemd/system/linuxremoteplayer.service
[Unit]
Description=Linux Remote Player Backend API
After=graphical.target network.target display-manager.service

[Service]
Type=simple
User=$TARGET_USER
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
    echo "System-wide service enabled and started."

else
    echo "Configuring Desktop Mode..."
    
    if [ -f /etc/systemd/system/linuxremoteplayer.service ]; then
        echo "[i] Removing previous Appliance Mode configuration..."
        systemctl stop linuxremoteplayer.service 2>/dev/null || true
        systemctl disable linuxremoteplayer.service 2>/dev/null || true
        rm -f /etc/systemd/system/linuxremoteplayer.service
        systemctl daemon-reload
    fi

    USER_SVC_DIR="$USER_HOME/.config/systemd/user"
    sudo -u "$TARGET_USER" mkdir -p "$USER_SVC_DIR"

    cat <<EOF > "$USER_SVC_DIR/linuxremoteplayer.service"
[Unit]
Description=Linux Remote Player Backend API
After=network.target

[Service]
Type=simple
WorkingDirectory=$BACKEND_DIR
ExecStart="$BACKEND_DIR/.venv/bin/python" run.py
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF
    chown -R "$TARGET_USER":"$TARGET_USER" "$USER_HOME/.config"

    export XDG_RUNTIME_DIR="/run/user/$(id -u "$TARGET_USER")"
    sudo -u "$TARGET_USER" XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" systemctl --user daemon-reload
    sudo -u "$TARGET_USER" XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" systemctl --user enable linuxremoteplayer.service
    sudo -u "$TARGET_USER" XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" systemctl --user restart linuxremoteplayer.service
    echo "User-level service enabled and started."
fi

HOSTNAME_LOCAL="$(hostname).local"
IP_ADDR=$(python3 -c "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(('1.1.1.1', 80)); print(s.getsockname()[0]); s.close()" || echo "<your-ip>")

TOKEN="guest"
TOKEN_FILE="$BACKEND_DIR/.pairing_token"
if [ -f "$TOKEN_FILE" ]; then
  TOKEN=$(cat "$TOKEN_FILE" | tr -d ' \n\r')
fi

echo "======================================"
echo " Installation Complete!               "
echo " Access PWA at:                       "
echo "   https://$HOSTNAME_LOCAL:8000/?token=$TOKEN"
echo "   https://$IP_ADDR:8000/?token=$TOKEN"
echo "======================================"

sudo -u "$TARGET_USER" kbuildsycoca6 --noincremental 2>/dev/null || sudo -u "$TARGET_USER" kbuildsycoca5 2>/dev/null || true

echo "[i] Waiting for service to start..."
for i in {1..15}; do
  if curl -sk https://127.0.0.1:8000/health >/dev/null 2>&1; then break; fi
  sleep 1
done

echo "[i] Launching Status Panel..."
sudo -u "$TARGET_USER" DISPLAY=:0 XDG_RUNTIME_DIR="/run/user/$(id -u "$TARGET_USER")" xdg-open "https://127.0.0.1:8000/status" 2>/dev/null || sudo -u "$TARGET_USER" DISPLAY=:0 XDG_RUNTIME_DIR="/run/user/$(id -u "$TARGET_USER")" chromium --app="https://127.0.0.1:8000/status" 2>/dev/null || echo -e "\n[!] No se pudo abrir automáticamente. Abre: https://$IP_ADDR:8000/status"
