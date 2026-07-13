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

AUTO_LAYOUT="us"
if command -v localectl >/dev/null 2>&1; then
    _x11=$(localectl status | grep 'X11 Layout' | awk '{print $3}' | tr -d ' ' || true)
    if [ "$_x11" = "es" ] || [ "$_x11" = "latam" ]; then
        AUTO_LAYOUT="$_x11"
    fi
fi

if [ -n "$LRP_KEYBOARD" ]; then
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
apt-get install -y python3-venv python3-dev ufw openssl avahi-daemon libnss3-tools wmctrl
systemctl enable --now avahi-daemon || true

# --- evdev / uinput permissions (FIX F1: Phase 6 blocker) ---
modprobe uinput || true
echo uinput > /etc/modules-load.d/uinput.conf
echo 'KERNEL=="uinput", MODE="0660", GROUP="input", OPTIONS+="static_node=uinput"' > /etc/udev/rules.d/99-uinput.rules
usermod -aG input "$TARGET_USER"
udevadm control --reload-rules && udevadm trigger
echo "[i] Added '$TARGET_USER' to 'input' group. REBOOT or re-login required before uinput works."

# --- Ensure Brave Browser is installed ---
if command -v brave-browser >/dev/null 2>&1; then
    echo "[i] Brave Browser already installed."
else
    echo "[i] Brave Browser not found. Installing via official apt repository..."
    apt-get install -y curl
    curl -fsSLo /usr/share/keyrings/brave-browser-archive-keyring.gpg https://brave-browser-apt-release.s3.brave.com/brave-browser-archive-keyring.gpg
    echo "deb [signed-by=/usr/share/keyrings/brave-browser-archive-keyring.gpg] https://brave-browser-apt-release.s3.brave.com/ stable main" | tee /etc/apt/sources.list.d/brave-browser-release.list
    apt-get update
    if apt-get install -y brave-browser; then
        echo "[i] Installed 'brave-browser'."
    else
        echo "[!] Could not install Brave automatically. Install it manually."
    fi
fi

# Define BACKEND_DIR for systemd paths and token generation
BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../backend" && pwd)"
cd "$BACKEND_DIR"

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

# Trust the CA certificate in the system and the user's NSS db (for Brave/Chromium)
if [ -f "$BACKEND_DIR/certs/ca.pem" ]; then
    echo "[i] Installing LRP CA certificate to system trust..."
    cp "$BACKEND_DIR/certs/ca.pem" /usr/local/share/ca-certificates/lrp-ca.crt
    update-ca-certificates >/dev/null 2>&1
    
    echo "[i] Installing LRP CA certificate to user NSS db..."
    USER_NSSDB="$USER_HOME/.pki/nssdb"
    sudo -u "$TARGET_USER" mkdir -p "$USER_NSSDB"
    # Ensure NSS DB is initialized
    sudo -u "$TARGET_USER" certutil -d sql:"$USER_NSSDB" -N --empty-password 2>/dev/null || true
    sudo -u "$TARGET_USER" certutil -d sql:"$USER_NSSDB" -A -t "C,," -n "LRP CA" -i "$BACKEND_DIR/certs/ca.pem" || true
fi

# P5: Ad-blocking (uBlock Origin Lite) -> Removed for Brave

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
sudo -u "$TARGET_USER" DISPLAY=:0 XDG_RUNTIME_DIR="/run/user/$(id -u "$TARGET_USER")" xdg-open "https://127.0.0.1:8000/status" 2>/dev/null || sudo -u "$TARGET_USER" DISPLAY=:0 XDG_RUNTIME_DIR="/run/user/$(id -u "$TARGET_USER")" chromium --app="https://127.0.0.1:8000/status" 2>/dev/null || true

echo "======================================"
echo " Panel de estado (ábrelo en el navegador"
echo " de ESTA TV si no se abrió solo):        "
echo "   https://localhost:8000/status"
echo "   https://127.0.0.1:8000/status"
echo "======================================"
