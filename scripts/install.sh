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

echo "1) Appliance Mode (Dedicated TV Kiosk - system-wide service)"
echo "2) Desktop Mode (Standard App - user-level service)"
read -p "Select installation mode [1/2]: " mode

# Install dependencies
apt-get update
apt-get install -y python3-venv python3-dev ufw

# --- evdev / uinput permissions (FIX F1: Phase 6 blocker) ---
modprobe uinput || true
echo uinput > /etc/modules-load.d/uinput.conf
echo 'KERNEL=="uinput", MODE="0660", GROUP="input", OPTIONS+="static_node=uinput"' > /etc/udev/rules.d/99-uinput.rules
usermod -aG input "$SUDO_USER"
udevadm control --reload-rules && udevadm trigger
echo "[i] Added '$SUDO_USER' to 'input' group. REBOOT or re-login required before uinput works."

# Setup Venv
BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../backend" && pwd)"
cd "$BACKEND_DIR"

if [ ! -d ".venv" ]; then
    sudo -u "$SUDO_USER" bash -c "python3 -m venv .venv"
fi
sudo -u "$SUDO_USER" bash -c "source .venv/bin/activate && pip install -r requirements.txt"

# Configure UFW
ufw allow 8000/tcp

if [ "$mode" == "1" ]; then
    echo "Configuring Appliance Mode..."
    echo "[!] Note: Autologin configuration must be done manually depending on your Display Manager."

    cat <<EOF > /etc/systemd/system/linuxremoteplayer.service
[Unit]
Description=Linux Remote Player Backend API
After=graphical.target network.target

[Service]
Type=simple
User=$SUDO_USER
WorkingDirectory=$BACKEND_DIR
ExecStart="$BACKEND_DIR/.venv/bin/uvicorn" main:app --host 0.0.0.0 --port 8000
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
ExecStart="$BACKEND_DIR/.venv/bin/uvicorn" main:app --host 0.0.0.0 --port 8000
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
fi

echo "======================================"
echo " Installation Complete!               "
echo " Access PWA at: http://<your-ip>:8000 "
echo "======================================"
