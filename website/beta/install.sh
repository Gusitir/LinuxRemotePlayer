#!/bin/bash
set -e

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (curl -fsSL https://www.linuxremoteplayer.com/beta/install.sh | sudo bash)"
    exit 1
fi

MANIFEST_URL="https://www.linuxremoteplayer.com/beta/latest.json"
WORK_DIR=$(mktemp -d)
trap 'rm -rf "$WORK_DIR"' EXIT
MANIFEST_FILE="$WORK_DIR/latest.json"

curl -fsSL "$MANIFEST_URL" -o "$MANIFEST_FILE"

if ! python3 - "$MANIFEST_FILE" "$WORK_DIR/metadata" <<'PY'
import json
import re
import sys
from urllib.parse import urlparse

manifest_path, metadata_path = sys.argv[1:]
try:
    with open(manifest_path, encoding="utf-8") as stream:
        data = json.load(stream)
    version = data["version"]
    deb_url = data["deb_url"]
    architecture = data["architecture"]
    sha256 = data["sha256"]
    if not isinstance(version, str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        raise ValueError("invalid version")
    if not isinstance(deb_url, str) or urlparse(deb_url).scheme != "https" or "\n" in deb_url:
        raise ValueError("invalid deb_url")
    if architecture != "amd64":
        raise ValueError("invalid architecture")
    filename = urlparse(deb_url).path.rsplit("/", 1)[-1]
    if filename != f"linuxremoteplayer_{version}_amd64.deb":
        raise ValueError("invalid package filename")
    if not isinstance(sha256, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", sha256):
        raise ValueError("invalid sha256")
except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
    print(f"Invalid beta manifest: {exc}", file=sys.stderr)
    raise SystemExit(1)

with open(metadata_path, "w", encoding="ascii") as stream:
    stream.write(f"{version}\n{deb_url}\n{sha256.lower()}\n")
PY
then
    exit 1
fi

VERSION=$(sed -n '1p' "$WORK_DIR/metadata")
DEB_URL=$(sed -n '2p' "$WORK_DIR/metadata")
SHA256=$(sed -n '3p' "$WORK_DIR/metadata")
DEB_FILE="linuxremoteplayer_${VERSION}_amd64.deb"
cd "$WORK_DIR"
curl -fsSL -o "$DEB_FILE" "$DEB_URL"
echo "$SHA256  $DEB_FILE" | sha256sum -c -

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y "./$DEB_FILE"

ENV_FILE=/opt/linuxremoteplayer/backend/.env
ENV_DIR=$(dirname "$ENV_FILE")
mkdir -p "$ENV_DIR"
ENV_TMP=$(mktemp "$ENV_DIR/.env.XXXXXX")
if [ -f "$ENV_FILE" ]; then
    awk '
        /^[[:space:]]*LRP_CHANNEL[[:space:]]*=/ { next }
        { print }
        END { print "LRP_CHANNEL=beta" }
    ' "$ENV_FILE" > "$ENV_TMP"
    chmod --reference="$ENV_FILE" "$ENV_TMP"
    chown --reference="$ENV_FILE" "$ENV_TMP"
else
    printf '%s\n' 'LRP_CHANNEL=beta' > "$ENV_TMP"
    chmod 600 "$ENV_TMP"
fi
mv -f "$ENV_TMP" "$ENV_FILE"

if [ -e /dev/tty ]; then
    set +e
    /usr/local/bin/lrp-setup --apply --approve --unattended < /dev/tty
    SETUP_RC=$?
    set -e
    case "$SETUP_RC" in
        0) ;;
        20) echo "[i] Reboot required. Run: sudo lrp-setup --resume" ;;
        *) echo "[!] Setup failed (rc=$SETUP_RC). Run: sudo lrp-setup --apply --approve --unattended" >&2; exit "$SETUP_RC" ;;
    esac
else
    echo "[!] No interactive terminal. Run: sudo lrp-setup --apply --approve --unattended" >&2
    exit 20
fi
