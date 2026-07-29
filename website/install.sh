#!/bin/bash
set -e

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (curl -fsSL https://www.linuxremoteplayer.com/install.sh | sudo bash)"
  exit 1
fi

echo "======================================"
echo " LinuxRemotePlayer Initial Installer  "
echo "======================================"

MANIFEST_URL="https://www.linuxremoteplayer.com/latest.json"
echo "Fetching latest version from $MANIFEST_URL..."
LATEST_JSON=$(curl -fsSL "$MANIFEST_URL")
VERSION=$(echo "$LATEST_JSON" | grep -o '"version"\s*:\s*"[^"]*"' | cut -d'"' -f4)
DEB_URL=$(echo "$LATEST_JSON" | grep -o '"deb_url"\s*:\s*"[^"]*"' | cut -d'"' -f4)
SHA256=$(echo "$LATEST_JSON" | grep -o '"sha256"\s*:\s*"[^"]*"' | cut -d'"' -f4)

if [ -z "$VERSION" ] || [ -z "$DEB_URL" ]; then
    echo "Error parsing latest.json"
    exit 1
fi

cd /tmp
echo "Downloading v$VERSION from $DEB_URL..."
curl -fsSL -o "linuxremoteplayer_${VERSION}_all.deb" "$DEB_URL"

echo "Verifying checksum..."
echo "$SHA256 linuxremoteplayer_${VERSION}_all.deb" | sha256sum -c -

echo "Installing package..."
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y "./linuxremoteplayer_${VERSION}_all.deb"

echo "Package installed. Running setup..."
# OJO: NO usar `exec < /dev/tty`. Este script llega por `curl | sudo bash`, o sea que bash
# lee el SCRIPT desde stdin; reemplazar stdin hace que bash pase a leer las lineas
# siguientes del script desde el teclado y el instalador se corta a la mitad en silencio.
# La redireccion va SOLO en la llamada, para que lrp-setup pueda hacer sus preguntas.
if [ -e /dev/tty ]; then
    /usr/local/bin/lrp-setup < /dev/tty || echo -e "\n[!] La configuracion automatica no pudo ejecutarse. Ejecutala a mano:\n    sudo lrp-setup\n"
else
    echo -e "\n[!] No hay terminal interactiva disponible. Ejecuta la configuracion a mano:\n    sudo lrp-setup\n"
fi
