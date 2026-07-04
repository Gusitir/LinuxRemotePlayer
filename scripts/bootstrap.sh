#!/bin/bash
# ==============================================================================
# LinuxRemotePlayer One-Line Bootstrapper Script (C2-6)
# ==============================================================================
set -e

# Repository URL placeholder - Sync with target repository
REPO_URL="https://github.com/Gusitir/LinuxRemotePlayer.git"
INSTALL_DIR="/opt/linuxremoteplayer"

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo curl -fsSL ... | sudo bash)"
  exit 1
fi

echo "======================================"
echo " Preparing LinuxRemotePlayer Clone   "
echo "======================================"

# Install git if missing
if ! command -v git >/dev/null 2>&1; then
    echo "[i] Installing git..."
    apt-get update
    apt-get install -y git
fi

# Clone or update directory
if [ -d "$INSTALL_DIR" ]; then
    echo "[i] Update directory exists. Pulling latest commits..."
    cd "$INSTALL_DIR"
    git pull
else
    echo "[i] Cloning repository to $INSTALL_DIR..."
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

# Fix ownership so that SUDO_USER can compile/run update script without permission issues
if [ -n "$SUDO_USER" ]; then
    chown -R "$SUDO_USER":"$SUDO_USER" "$INSTALL_DIR"
fi

# Execute the main installer
echo "[i] Running main installation script..."
exec bash "$INSTALL_DIR/scripts/install.sh"
