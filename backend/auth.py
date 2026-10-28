"""Authentication and pairing tokens.

PH24: this module no longer knows about licenses. Every installed route works
without a license token, without a cloud call and without quota; the only
credential here is the local pairing token.
"""
import os
import secrets
import logging
from dotenv import load_dotenv

logger = logging.getLogger("auth")

try:
    from config import get_env_file, get_token_file, secure_permissions
except ImportError:
    from backend.config import get_env_file, get_token_file, secure_permissions

load_dotenv(get_env_file())

PAIRING_TOKEN = os.getenv("PAIRING_TOKEN")

# SEC-01 auto-generated pairing token
if not PAIRING_TOKEN:
    token_path = get_token_file()
    if token_path.is_file():
        try:
            with open(token_path, "r") as f:
                PAIRING_TOKEN = f.read().strip()
        except Exception as e:
            logger.error(f"Could not read .pairing_token file: {e}")
    if not PAIRING_TOKEN:
        PAIRING_TOKEN = secrets.token_urlsafe(16)
        try:
            token_path.parent.mkdir(parents=True, exist_ok=True)
            with open(token_path, "w") as f:
                f.write(PAIRING_TOKEN)
            secure_permissions(token_path)
            logger.info("Generated auto-provisioned pairing token.")
        except Exception as e:
            logger.error(f"Could not write .pairing_token file: {e}")


def verify_access(token: str) -> bool:
    """Access gate WITHOUT incrementing usage. Returns True if token matches the local PAIRING_TOKEN."""
    if not token:
        return False
    return token == PAIRING_TOKEN
