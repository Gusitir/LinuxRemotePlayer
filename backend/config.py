"""Configuration and central path resolution for LinuxRemotePlayer.

Enforces ASTRA-01:
- Application code & venv in /opt/linuxremoteplayer remain strictly owned by root:root (0755/0644).
- All mutable state (.env, .pairing_token, .license_cache, certs/) is isolated
  in /var/lib/linuxremoteplayer (owned by lrp:lrp, mode 0700).
- Development environments transparently fall back to backend/ directory.
"""
import os
import sys
import logging
from pathlib import Path

logger = logging.getLogger("config")

BACKEND_DIR = Path(__file__).resolve().parent
REPO_DIR = BACKEND_DIR.parent

APPLIANCE_DATA_DIR = Path("/var/lib/linuxremoteplayer")


def get_data_dir() -> Path:
    """Returns the base directory for mutable data.
    
    Priority:
    1. Explicit LRP_DATA_DIR environment variable (tests / overrides).
    2. /var/lib/linuxremoteplayer if present or if running installed in /opt/linuxremoteplayer.
    3. BACKEND_DIR (development mode / Windows).
    """
    if "LRP_DATA_DIR" in os.environ:
        p = Path(os.environ["LRP_DATA_DIR"]).resolve()
        try:
            p.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        return p

    # Check if running on Debian appliance or if /var/lib/linuxremoteplayer exists
    if APPLIANCE_DATA_DIR.is_dir() or str(BACKEND_DIR).startswith("/opt/linuxremoteplayer"):
        try:
            APPLIANCE_DATA_DIR.mkdir(parents=True, exist_ok=True)
            return APPLIANCE_DATA_DIR
        except (PermissionError, OSError) as e:
            logger.debug(f"Could not use {APPLIANCE_DATA_DIR}: {e}")

    return BACKEND_DIR


def get_env_file() -> Path:
    """Path to the mutable .env configuration file."""
    data_dir = get_data_dir()
    primary = data_dir / ".env"
    if "LRP_DATA_DIR" in os.environ:
        return primary
    if primary.is_file():
        return primary
    legacy = BACKEND_DIR / ".env"
    if legacy.is_file():
        return legacy
    return primary


def get_token_file() -> Path:
    """Path to the pairing token file."""
    data_dir = get_data_dir()
    primary = data_dir / ".pairing_token"
    if "LRP_DATA_DIR" in os.environ:
        return primary
    if primary.is_file():
        return primary
    legacy = BACKEND_DIR / ".pairing_token"
    if legacy.is_file():
        return legacy
    return primary


def get_license_cache_file() -> Path:
    """Path to the license verification cache."""
    data_dir = get_data_dir()
    primary = data_dir / ".license_cache"
    if "LRP_DATA_DIR" in os.environ:
        return primary
    if primary.is_file():
        return primary
    legacy = BACKEND_DIR / ".license_cache"
    if legacy.is_file():
        return legacy
    return primary


def get_certs_dir() -> Path:
    """Directory holding TLS certificates and keys."""
    data_dir = get_data_dir()
    primary = data_dir / "certs"
    if "LRP_DATA_DIR" in os.environ:
        return primary
    if primary.is_dir():
        return primary
    legacy = BACKEND_DIR / "certs"
    if legacy.is_dir():
        return legacy
    return primary


def get_ca_key_file() -> Path:
    return get_certs_dir() / "ca.key"


def get_ca_cert_file() -> Path:
    return get_certs_dir() / "ca.pem"


def get_key_file() -> Path:
    return get_certs_dir() / "key.pem"


def get_cert_file() -> Path:
    return get_certs_dir() / "cert.pem"


def secure_permissions(path: Path, is_dir: bool = False) -> None:
    """Applies secure permissions (0700 for dirs, 0600 for files) if supported."""
    if os.name == "nt":
        return
    try:
        if is_dir:
            os.chmod(path, 0o700)
        else:
            os.chmod(path, 0o600)
    except OSError as e:
        logger.debug(f"Could not set secure permissions on {path}: {e}")
