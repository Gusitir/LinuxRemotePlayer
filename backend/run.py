"""Entrypoint with automatic, self-healing HTTPS and two-tier CA structure.
"""
import os
import re
import socket
import subprocess
import uvicorn
import logging
import threading
import time

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("run")

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

CERT_DIR = os.path.join(os.path.dirname(__file__), "certs")
CA_KEY_FILE = os.path.join(CERT_DIR, "ca.key")
CA_CERT_FILE = os.path.join(CERT_DIR, "ca.pem")
KEY_FILE = os.path.join(CERT_DIR, "key.pem")
CERT_FILE = os.path.join(CERT_DIR, "cert.pem")


def detect_ip():
    """Best-effort primary LAN IPv4 (no packets are actually sent)."""
    # 1. UDP trick
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("1.1.1.1", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and ip != "127.0.0.1":
            return ip
    except Exception:
        pass

    # 2. subprocess ip route (Linux)
    try:
        out = subprocess.run(["ip", "-4", "route", "get", "1.1.1.1"], capture_output=True, text=True, check=True).stdout
        m = re.search(r"src\s+([0-9.]+)", out)
        if m and m.group(1) != "127.0.0.1":
            return m.group(1)
    except Exception:
        pass

    # 3. hostname -I (Linux)
    try:
        out = subprocess.run(["hostname", "-I"], capture_output=True, text=True, check=True).stdout.strip()
        ips = [x for x in out.split() if x != "127.0.0.1"]
        if ips:
            return ips[0]
    except Exception:
        pass

    # 4. socket name lookup
    try:
        hostname = socket.gethostname()
        addrs = socket.getaddrinfo(hostname, None)
        for addr in addrs:
            ip = addr[4][0]
            if re.match(r"^[0-9.]+$", ip) and ip != "127.0.0.1" and not ip.startswith("169.254"):
                return ip
    except Exception:
        pass

    return "127.0.0.1"


def cert_identity():
    """Return (ip, fqdn) from the existing leaf cert, or (None, None)."""
    if not os.path.exists(CERT_FILE):
        return None, None
    try:
        out = subprocess.run(
            ["openssl", "x509", "-in", CERT_FILE, "-noout", "-text"],
            capture_output=True, text=True, check=True,
        ).stdout
        dns_names = re.findall(r"DNS:([a-zA-Z0-9.-]+)", out)
        ip_addrs = re.findall(r"IP Address:([0-9.]+)", out)

        ip = next((x for x in ip_addrs if x != "127.0.0.1"), None)
        if not ip and ip_addrs:
            ip = ip_addrs[0]
        fqdn = next((x for x in dns_names if x != "localhost"), None)
        if not fqdn and dns_names:
            fqdn = dns_names[0]

        return ip, fqdn
    except Exception:
        return None, None


def ensure_cert(ip, fqdn):
    """Generate/refresh CA and self-signed leaf cert. Returns True if HTTPS is ready."""
    os.makedirs(CERT_DIR, exist_ok=True)

    # 1. Generate CA if not exists
    if not os.path.exists(CA_KEY_FILE) or not os.path.exists(CA_CERT_FILE):
        try:
            logger.info("Generating new CA key and certificate...")
            subprocess.run(
                ["openssl", "genrsa", "-out", CA_KEY_FILE, "2048"],
                check=True, capture_output=True
            )
            subprocess.run(
                ["openssl", "req", "-x509", "-new", "-nodes", "-key", CA_KEY_FILE,
                 "-sha256", "-days", "3650", "-subj", "/CN=LinuxRemotePlayer CA", "-out", CA_CERT_FILE],
                check=True, capture_output=True
            )
            os.chmod(CA_KEY_FILE, 0o600)
            logger.info("CA key and certificate generated successfully.")
        except Exception as ex:
            logger.error(f"Could not generate CA certificate ({ex})")
            return False

    # 2. Check if Leaf cert needs regeneration
    existing_ip, existing_fqdn = cert_identity()
    if os.path.exists(KEY_FILE) and os.path.exists(CERT_FILE) and existing_ip == ip and existing_fqdn == fqdn:
        return True

    logger.info(f"Generating leaf cert for IP: {ip}, FQDN: {fqdn}")
    try:
        # Generate leaf key
        subprocess.run(
            ["openssl", "genrsa", "-out", KEY_FILE, "2048"],
            check=True, capture_output=True
        )
        os.chmod(KEY_FILE, 0o600)

        # Generate CSR
        csr_file = os.path.join(CERT_DIR, "leaf.csr")
        subprocess.run(
            ["openssl", "req", "-new", "-key", KEY_FILE, "-subj", f"/CN={ip}", "-out", csr_file],
            check=True, capture_output=True
        )

        # Create temp ext file for SANs
        ext_file = os.path.join(CERT_DIR, "leaf.ext")
        with open(ext_file, "w") as f:
            f.write(f"subjectAltName=IP:{ip},DNS:{fqdn},DNS:localhost,IP:127.0.0.1\n")

        # Sign leaf cert with CA
        subprocess.run(
            ["openssl", "x509", "-req", "-in", csr_file, "-CA", CA_CERT_FILE, "-CAkey", CA_KEY_FILE,
             "-CAcreateserial", "-out", CERT_FILE, "-days", "825", "-sha256", "-extfile", ext_file],
            check=True, capture_output=True
        )

        # Cleanup
        if os.path.exists(csr_file):
            os.remove(csr_file)
        if os.path.exists(ext_file):
            os.remove(ext_file)

        logger.info(f"Leaf certificate for {ip} and {fqdn} generated successfully.")
        return True
    except Exception as ex:
        logger.warning(f"Could not generate leaf cert ({ex}). Falling back to HTTP.")
        return False


def monitor_ip(initial_ip):
    while True:
        time.sleep(60)
        current_ip = detect_ip()
        if current_ip != initial_ip:
            if os.getenv("INVOCATION_ID"):
                logger.warning(f"IP changed from {initial_ip} to {current_ip}. Restarting service to self-heal.")
                os._exit(3)
            else:
                logger.warning(
                    f"IP changed from {initial_ip} to {current_ip}. "
                    f"Clients may disconnect. Please restart the service to regenerate the certificate."
                )


if __name__ == "__main__":
    ip = detect_ip()
    fqdn = f"{socket.gethostname()}.local"

    # Start IP monitor thread
    monitor_thread = threading.Thread(target=monitor_ip, args=(ip,), daemon=True)
    monitor_thread.start()

    https_ok = ensure_cert(ip, fqdn)
    kwargs = {"host": HOST, "port": PORT}
    
    # R-08 pairing URL logging
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    supabase_active = bool(SUPABASE_URL and SUPABASE_KEY)
    
    token = ""
    if not supabase_active:
        token_file = os.path.join(os.path.dirname(__file__), ".pairing_token")
        if os.path.exists(token_file):
            try:
                with open(token_file, "r") as f:
                    token = f.read().strip()
            except Exception as e:
                logger.error(f"Could not read .pairing_token file: {e}")

    if https_ok:
        kwargs["ssl_keyfile"] = KEY_FILE
        kwargs["ssl_certfile"] = CERT_FILE
        if token:
            logger.info(f"HTTPS ready -> https://{fqdn}:{PORT}/?token={token} or https://{ip}:{PORT}/?token={token}")
        else:
            logger.info(f"HTTPS ready -> https://{fqdn}:{PORT} or https://{ip}:{PORT}")
        logger.info("[WARNING] Recomended to use static IP or DHCP reservation for stable PWA pairing.")
    else:
        if token:
            logger.info(f"HTTP only -> http://{ip}:{PORT}/?token={token} (mic will NOT work on phones)")
        else:
            logger.info(f"HTTP only -> http://{ip}:{PORT} (mic will NOT work on phones)")

    uvicorn.run("main:app", **kwargs)
