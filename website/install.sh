#!/bin/bash
set -e

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (curl -fsSL https://linux-remote-player.vercel.app/install.sh | sudo bash)"
  exit 1
fi

echo "======================================"
echo " LinuxRemotePlayer Initial Installer  "
echo "======================================"

MANIFEST_URL="https://linux-remote-player.vercel.app/latest.json"
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

if [ ! -t 0 ] && [ -e /dev/tty ]; then exec < /dev/tty; fi
echo "Package installed. Running setup..."
/usr/local/bin/lrp-setup
