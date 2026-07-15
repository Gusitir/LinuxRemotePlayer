#!/bin/bash
# ==============================================================================
# LinuxRemotePlayer Uninstaller Script (C2-5)
# ==============================================================================
set -e

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo ./uninstall.sh)"
  exit 1
fi

echo "======================================"
echo " LinuxRemotePlayer Uninstaller        "
echo "======================================"
read -p "Esto eliminará LinuxRemotePlayer de tu sistema. ¿Continuar? [y/N]: " confirm

if [[ ! "$confirm" =~ ^[yY]$ ]]; then
    echo "Desinstalación cancelada."
    exit 0
fi

# Stop and disable system services
echo "[i] Stopping and disabling systemd services..."
if [ -f "/etc/systemd/system/linuxremoteplayer.service" ]; then
    systemctl stop linuxremoteplayer.service || true
    systemctl disable linuxremoteplayer.service || true
    rm -f "/etc/systemd/system/linuxremoteplayer.service"
    systemctl daemon-reload
    echo "[+] Removed system service."
fi

# Stop and disable user-level services for SUDO_USER if applicable
if [ -n "$SUDO_USER" ]; then
    USER_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)
    USER_SVC="$USER_HOME/.config/systemd/user/linuxremoteplayer.service"
    if [ -f "$USER_SVC" ]; then
        export XDG_RUNTIME_DIR="/run/user/$(id -u "$SUDO_USER")"
        sudo -u "$SUDO_USER" XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" systemctl --user stop linuxremoteplayer.service || true
        sudo -u "$SUDO_USER" XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" systemctl --user disable linuxremoteplayer.service || true
        rm -f "$USER_SVC"
        sudo -u "$SUDO_USER" XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" systemctl --user daemon-reload
        echo "[+] Removed user service."
    fi
fi

# Remove input/uinput udev rules
echo "[i] Removing uinput rules..."
if [ -f "/etc/udev/rules.d/99-uinput.rules" ]; then
    rm -f "/etc/udev/rules.d/99-uinput.rules"
fi
if [ -f "/etc/modules-load.d/uinput.conf" ]; then
    rm -f "/etc/modules-load.d/uinput.conf"
fi
udevadm control --reload-rules || true
udevadm trigger || true
echo "[+] Uinput permissions reverted."

# Remove UFW firewall rules
echo "[i] Reverting firewall configuration..."
ufw delete allow 8000/tcp || true

# Remove generated files and environments
BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../backend" && pwd)"
echo "[i] Cleaning up files under $BACKEND_DIR..."
rm -rf "$BACKEND_DIR/.venv"
rm -rf "$BACKEND_DIR/certs"
rm -rf "$BACKEND_DIR/.pairing_token"
rm -rf "$BACKEND_DIR/.license_cache"
rm -rf "$BACKEND_DIR/__pycache__"

echo "[i] Restaurando opciones de suspensión (unmask)..."
systemctl unmask sleep.target suspend.target hibernate.target hybrid-sleep.target || true

echo "======================================"
echo " Desinstalación básica completada.   "
echo "======================================"
echo "Pasos manuales recomendados:"
echo " 1. Remover al usuario del grupo input:"
echo "    sudo gpasswd -d $SUDO_USER input"
echo " 2. Eliminar la carpeta clonada del repositorio:"
echo "    rm -rf $(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo " 3. Chromium y avahi-daemon no han sido desinstalados ya que pueden ser usados por otros servicios."
echo "======================================"
