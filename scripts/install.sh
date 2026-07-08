#!/bin/bash
set -e

echo "======================================"
echo " LinuxRemotePlayer Installer          "
echo "======================================"

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo ./install.sh)"
  exit 1
fi

if [ -z "$SUDO_USER" ]; then
  echo "Error: SUDO_USER is not set. Please run the script via 'sudo ./install.sh' and not directly as root."
  exit 1
fi

USER_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)

if [ ! -t 0 ] && [ -e /dev/tty ]; then exec < /dev/tty; fi

if [ -n "$LRP_MODE" ]; then
    mode="$LRP_MODE"
    echo "[i] Using mode from LRP_MODE environment variable: $mode"
else
    echo "1) Appliance Mode (Dedicated TV Kiosk - system-wide service)"
    echo "2) Desktop Mode (Standard App - user-level service)"
    read -p "Select installation mode [1/2]: " mode
fi

# Install dependencies (including avahi-daemon for mDNS hostname resolution)
apt-get update
apt-get install -y python3-venv python3-dev ufw openssl avahi-daemon
systemctl enable --now avahi-daemon || true

# --- evdev / uinput permissions (FIX F1: Phase 6 blocker) ---
modprobe uinput || true
echo uinput > /etc/modules-load.d/uinput.conf
echo 'KERNEL=="uinput", MODE="0660", GROUP="input", OPTIONS+="static_node=uinput"' > /etc/udev/rules.d/99-uinput.rules
usermod -aG input "$SUDO_USER"
udevadm control --reload-rules && udevadm trigger
echo "[i] Added '$SUDO_USER' to 'input' group. REBOOT or re-login required before uinput works."

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

# Setup Venv
BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../backend" && pwd)"
cd "$BACKEND_DIR"

if [ ! -d ".venv" ]; then
    sudo -u "$SUDO_USER" bash -c "python3 -m venv .venv"
fi
sudo -u "$SUDO_USER" bash -c "source .venv/bin/activate && pip install -r requirements.txt"

# Configure UFW
ufw allow 8000/tcp
if ufw status | grep -q "inactive"; then
  echo "[!] WARNING: UFW firewall is currently INACTIVE. The allow rule for port 8000 will have no effect until you enable it (sudo ufw enable)."
fi

# Pre-generate pairing token if not exists (SEC-01)
sudo -u "$SUDO_USER" "$BACKEND_DIR/.venv/bin/python" -c "
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

    # Added After=display-manager.service (COR-04)
    cat <<EOF > /etc/systemd/system/linuxremoteplayer.service
[Unit]
Description=Linux Remote Player Backend API
After=graphical.target network.target display-manager.service

[Service]
Type=simple
User=$SUDO_USER
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
    USER_SVC_DIR="$USER_HOME/.config/systemd/user"
    sudo -u "$SUDO_USER" mkdir -p "$USER_SVC_DIR"

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
    chown -R "$SUDO_USER":"$SUDO_USER" "$USER_HOME/.config"

    export XDG_RUNTIME_DIR="/run/user/$(id -u "$SUDO_USER")"
    sudo -u "$SUDO_USER" XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" systemctl --user daemon-reload
    sudo -u "$SUDO_USER" XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" systemctl --user enable linuxremoteplayer.service
    sudo -u "$SUDO_USER" XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" systemctl --user restart linuxremoteplayer.service
    echo "User-level service enabled and started."

    echo "Creating desktop shortcut for Status Panel..."
    APPS_DIR="$USER_HOME/.local/share/applications"
    sudo -u "$SUDO_USER" mkdir -p "$APPS_DIR"
    cat <<EOF > "$APPS_DIR/linuxremoteplayer-panel.desktop"
[Desktop Entry]
Version=1.0
Name=Remote Linux Player Panel
Comment=Linux Remote Player Status Panel
Exec=chromium --app=https://127.0.0.1:8000/status
Icon=remote-linux-player
Terminal=false
Type=Application
Categories=Utility;
EOF
    chown "$SUDO_USER":"$SUDO_USER" "$APPS_DIR/linuxremoteplayer-panel.desktop"
    echo "Desktop shortcut created."
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
