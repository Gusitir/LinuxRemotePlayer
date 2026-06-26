#!/bin/bash
# Generate a self-signed TLS certificate for the local LAN IP.
# Required so the PWA can use the microphone (getUserMedia needs a secure context).
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERT_DIR="$SCRIPT_DIR/../backend/certs"
mkdir -p "$CERT_DIR"

# Best-effort detection of the primary LAN IP.
IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
if [ -z "$IP" ]; then
    IP="127.0.0.1"
fi

echo "Generating self-signed cert for IP: $IP"
openssl req -x509 -newkey rsa:2048 -nodes \
    -keyout "$CERT_DIR/key.pem" \
    -out "$CERT_DIR/cert.pem" \
    -days 825 \
    -subj "/CN=$IP" \
    -addext "subjectAltName=IP:$IP"

chmod 600 "$CERT_DIR/key.pem"
echo "Done. Certs written to: $CERT_DIR"
echo "Note: phones must accept the self-signed certificate once (browser warning)."
