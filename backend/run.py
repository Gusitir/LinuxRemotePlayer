"""Entrypoint with automatic, self-healing HTTPS.

Why: the PWA microphone (getUserMedia) and service workers require a *secure
context*. Served over plain http://<lan-ip>:8000 the browser blocks the mic on
phones. This launcher generates a self-signed certificate for the current LAN IP
on startup, and regenerates it automatically if the IP changes (e.g. new DHCP
lease) so HTTPS keeps working with zero manual steps.

The only remaining friction is a one-time "accept the certificate" prompt the
first time each phone connects (unavoidable with self-signed certs).
"""
import os
import re
import socket
import subprocess
import uvicorn

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

CERT_DIR = os.path.join(os.path.dirname(__file__), "certs")
KEY_FILE = os.path.join(CERT_DIR, "key.pem")
CERT_FILE = os.path.join(CERT_DIR, "cert.pem")


def detect_ip():
    """Best-effort primary LAN IPv4 (no packets are actually sent)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def cert_ip():
    """Return the IP the existing cert was issued for, or None."""
    if not os.path.exists(CERT_FILE):
        return None
    try:
        out = subprocess.run(
            ["openssl", "x509", "-in", CERT_FILE, "-noout", "-text"],
            capture_output=True, text=True, check=True,
        ).stdout
        m = re.search(r"IP Address:([0-9.]+)", out)
        if m:
            return m.group(1)
        m = re.search(r"CN\s*=\s*([0-9.]+)", out)
        return m.group(1) if m else None
    except Exception:
        return None


def ensure_cert(ip):
    """Generate/refresh a self-signed cert for `ip`. Returns True if HTTPS is ready."""
    if os.path.exists(CERT_FILE) and os.path.exists(KEY_FILE) and cert_ip() == ip:
        return True
    os.makedirs(CERT_DIR, exist_ok=True)
    try:
        subprocess.run(
            ["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
             "-keyout", KEY_FILE, "-out", CERT_FILE, "-days", "825",
             "-subj", f"/CN={ip}", "-addext", f"subjectAltName=IP:{ip}"],
            check=True, capture_output=True,
        )
        os.chmod(KEY_FILE, 0o600)
        print(f"[run] (Re)generated self-signed cert for {ip}")
        return True
    except Exception as ex:
        print(f"[run] WARNING: could not generate cert ({ex}). Falling back to HTTP.")
        return False


if __name__ == "__main__":
    ip = detect_ip()
    https_ok = ensure_cert(ip)
    kwargs = {"host": HOST, "port": PORT}
    if https_ok:
        kwargs["ssl_keyfile"] = KEY_FILE
        kwargs["ssl_certfile"] = CERT_FILE
        print(f"[run] HTTPS ready -> https://{ip}:{PORT}")
    else:
        print(f"[run] HTTP only -> http://{ip}:{PORT} (mic will NOT work on phones)")
    uvicorn.run("main:app", **kwargs)
