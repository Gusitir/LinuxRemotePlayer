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
import uuid
import shutil
from datetime import datetime, timezone

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("run")

OPENSSL_BIN = (
    os.getenv("OPENSSL_BIN")
    or shutil.which("openssl")
    or shutil.which("openssl.exe")
    or (r"C:\Program Files\Git\usr\bin\openssl.exe" if os.path.exists(r"C:\Program Files\Git\usr\bin\openssl.exe") else "openssl")
)

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

try:
    from config import (
        get_certs_dir, get_ca_key_file, get_ca_cert_file, get_key_file, get_cert_file,
        get_token_file, secure_permissions
    )
except ImportError:
    from backend.config import (
        get_certs_dir, get_ca_key_file, get_ca_cert_file, get_key_file, get_cert_file,
        get_token_file, secure_permissions
    )

CERT_DIR = str(get_certs_dir())
CA_KEY_FILE = str(get_ca_key_file())
CA_CERT_FILE = str(get_ca_cert_file())
KEY_FILE = str(get_key_file())
CERT_FILE = str(get_cert_file())


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
            [OPENSSL_BIN, "x509", "-in", CERT_FILE, "-noout", "-text"],
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


def parse_cert_dates(cert_file: str) -> tuple[datetime | None, datetime | None]:
    """Extract (notBefore, notAfter) as timezone-aware UTC datetimes from the first certificate in cert_file."""
    if not os.path.exists(cert_file):
        return None, None
    try:
        out = subprocess.run(
            [OPENSSL_BIN, "x509", "-in", cert_file, "-noout", "-dates"],
            capture_output=True, text=True, check=True
        ).stdout
        nb_match = re.search(r"notBefore=(.+)", out)
        na_match = re.search(r"notAfter=(.+)", out)
        if not nb_match or not na_match:
            return None, None

        def _parse(val_str: str) -> datetime:
            clean = " ".join(val_str.replace("GMT", "").replace("UTC", "").strip().split())
            return datetime.strptime(clean, "%b %d %H:%M:%S %Y").replace(tzinfo=timezone.utc)

        return _parse(nb_match.group(1)), _parse(na_match.group(1))
    except Exception as e:
        logger.debug(f"Failed to parse cert dates for {cert_file}: {e}")
        return None, None


def is_cert_expiring_or_invalid(cert_file: str, min_hours: float = 48.0, current_time: datetime | None = None) -> bool:
    """ASTRA-04: Check if certificate is expired, corrupted, or expiring within min_hours (default 48h).
    Includes RTC desynchronization safeguard: if current system clock is prior to notBefore,
    assume the clock is corrupted/desynchronized (e.g. dead CMOS battery reset to 1970/2000),
    and do NOT invalidate the certificate based on erroneous system time.
    """
    not_before, not_after = parse_cert_dates(cert_file)
    if not not_before or not not_after:
        logger.info(f"Certificate {cert_file} is unreadable or has invalid dates. Renewal required.")
        return True

    now = current_time or datetime.now(timezone.utc)

    # RTC Safeguard: system clock behind cert issuance time (dead battery / unsynced RTC)
    if now < not_before:
        logger.warning(
            f"System clock ({now.isoformat()}) is prior to certificate notBefore ({not_before.isoformat()}). "
            "Suspected RTC desynchronization (e.g. CMOS battery reset). Preserving existing certificate."
        )
        return False

    # Check expiration: if expired or expiring within min_hours (default 48h)
    time_remaining = (not_after - now).total_seconds()
    if time_remaining <= min_hours * 3600:
        logger.info(
            f"Certificate {cert_file} is expiring or expired (notAfter={not_after.isoformat()}, "
            f"remaining={time_remaining / 3600:.1f}h <= {min_hours}h). Triggering regeneration."
        )
        return True

    return False


def ensure_full_chain() -> None:
    """B11: uvicorn envia tal cual lo que haya en ssl_certfile. Con la hoja sola, un cliente
    que no tenga la CA instalada -o que la tenga vieja porque se regeneraron los
    certificados- recibe SEC_ERROR_BAD_SIGNATURE. Hay que servir hoja + CA, en ese orden.
    Idempotente: si el archivo ya trae los dos certificados, no hace nada."""
    try:
        if not os.path.exists(CERT_FILE) or not os.path.exists(CA_CERT_FILE):
            return
        with open(CERT_FILE, "r") as f:
            body = f.read()
        if body.count("BEGIN CERTIFICATE") >= 2:
            return
        with open(CA_CERT_FILE, "r") as f:
            ca = f.read()
        if not body.endswith("\n"):
            body += "\n"
        with open(CERT_FILE, "w") as f:
            f.write(body + ca)
        logger.info("Cadena de certificados completada (ca.pem concatenado a cert.pem).")
    except Exception as e:
        logger.warning(f"No se pudo completar la cadena de certificados: {e}")


def ensure_cert(ip, fqdn):
    """Generate/refresh CA and self-signed leaf cert. Returns True if HTTPS is ready."""
    from pathlib import Path
    os.makedirs(CERT_DIR, exist_ok=True)
    secure_permissions(Path(CERT_DIR), is_dir=True)

    # 1. Generate CA if not exists
    if not os.path.exists(CA_KEY_FILE) or not os.path.exists(CA_CERT_FILE):
        try:
            logger.info("Generating new CA key and certificate...")
            # B14: el nombre de la CA lleva un sufijo unico por instalacion. Si dos CA distintas
            # comparten nombre, un navegador que guardo la vieja intenta validar la nueva con la
            # llave vieja y tira SEC_ERROR_BAD_SIGNATURE -- un error que el usuario no puede
            # saltear. Con nombres distintos el peor caso es "emisor desconocido", que se acepta
            # y se resuelve reinstalando el ca.pem.
            try:
                with open("/etc/machine-id", "r") as mid:
                    ca_suffix = mid.read().strip()[:8]
            except Exception:
                ca_suffix = uuid.uuid4().hex[:8]
            ca_subject = f"/CN=LinuxRemotePlayer CA {ca_suffix}"

            subprocess.run(
                [OPENSSL_BIN, "genrsa", "-out", CA_KEY_FILE, "2048"],
                check=True, capture_output=True
            )
            subprocess.run(
                [OPENSSL_BIN, "req", "-x509", "-new", "-nodes", "-key", CA_KEY_FILE,
                 "-sha256", "-days", "3650", "-subj", ca_subject, "-out", CA_CERT_FILE],
                check=True, capture_output=True
            )
            os.chmod(CA_KEY_FILE, 0o600)
            logger.info("CA key and certificate generated successfully.")
        except Exception as ex:
            logger.error(f"Could not generate CA certificate ({ex})")
            return False

    # 2. Check if Leaf cert needs regeneration
    existing_ip, existing_fqdn = cert_identity()
    cert_matches = (
        os.path.exists(KEY_FILE)
        and os.path.exists(CERT_FILE)
        and existing_ip == ip
        and existing_fqdn == fqdn
    )
    if cert_matches and not is_cert_expiring_or_invalid(CERT_FILE, min_hours=48.0):
        return True

    logger.info(f"Generating leaf cert for IP: {ip}, FQDN: {fqdn}")
    try:
        # Generate leaf key
        subprocess.run(
            [OPENSSL_BIN, "genrsa", "-out", KEY_FILE, "2048"],
            check=True, capture_output=True
        )
        os.chmod(KEY_FILE, 0o600)

        # Generate CSR
        csr_file = os.path.join(CERT_DIR, "leaf.csr")
        subprocess.run(
            [OPENSSL_BIN, "req", "-new", "-key", KEY_FILE, "-subj", f"/CN={ip}", "-out", csr_file],
            check=True, capture_output=True
        )

        # Create temp ext file for SANs
        ext_file = os.path.join(CERT_DIR, "leaf.ext")
        with open(ext_file, "w") as f:
            f.write(f"subjectAltName=IP:{ip},DNS:{fqdn},DNS:localhost,IP:127.0.0.1\n")

        # Sign leaf cert with CA
        subprocess.run(
            [OPENSSL_BIN, "x509", "-req", "-in", csr_file, "-CA", CA_CERT_FILE, "-CAkey", CA_KEY_FILE,
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


def get_initial_ip(timeout: float = 8.0) -> str:
    """Best-effort initial LAN IPv4.
    During system boot on appliance hardware, DHCP may take 1-3s to acquire a lease.
    Polls detect_ip() up to timeout seconds so the service does not initialize on loopback
    and then immediately reboot."""
    start = time.time()
    while time.time() - start < timeout:
        ip = detect_ip()
        if ip and ip != "127.0.0.1":
            return ip
        time.sleep(0.5)
    return "127.0.0.1"


def monitor_ip(initial_ip):
    """Monitors local IP changes to trigger self-healing.
    If initial_ip was 127.0.0.1 (machine booted without active network or late DHCP),
    checks frequently (every 2.0s) so it recovers as soon as an interface comes online.
    Once on a valid LAN IP, checks every 60s."""
    while True:
        poll_interval = 2.0 if initial_ip == "127.0.0.1" else 60.0
        time.sleep(poll_interval)
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
    ip = get_initial_ip(timeout=8.0)
    fqdn = f"{socket.gethostname()}.local"

    # Start IP monitor thread
    monitor_thread = threading.Thread(target=monitor_ip, args=(ip,), daemon=True)
    monitor_thread.start()

    https_ok = ensure_cert(ip, fqdn)
    kwargs = {"host": HOST, "port": PORT}
    
    # R-08 pairing URL logging
    token = ""
    token_path = get_token_file()
    if token_path.is_file():
        try:
            with open(token_path, "r") as f:
                token = f.read().strip()
        except Exception as e:
            logger.error(f"Could not read .pairing_token file: {e}")

    if https_ok:
        # Se llama ACA y no dentro de ensure_cert() a proposito: ensure_cert retorna
        # temprano cuando el certificado ya existe y la IP no cambio, asi que una
        # instalacion que ya quedo con la hoja sola nunca se repararia. Aca corre siempre.
        ensure_full_chain()
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
