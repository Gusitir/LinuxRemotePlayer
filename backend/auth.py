"""Authentication, pairing tokens, and license verification."""
import os
import secrets
import logging
import hashlib
import json
from datetime import datetime, timezone
import httpx
from dotenv import load_dotenv

logger = logging.getLogger("auth")

try:
    from config import get_env_file, get_token_file, get_license_cache_file, secure_permissions
except ImportError:
    from backend.config import get_env_file, get_token_file, get_license_cache_file, secure_permissions

load_dotenv(get_env_file())

LICENSE_API_URL = os.getenv("LICENSE_API_URL", "https://tbijfdbtauzxbsbkujbs.functions.supabase.co/validate-license")
CACHE_FILE = str(get_license_cache_file())
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


def is_license_valid_cached_or_online(license_token: str) -> bool:
    if not license_token:
        return False
    token_hash = hashlib.sha256(license_token.encode()).hexdigest()
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                cache = json.load(f)
            if cache.get("token_hash") == token_hash:
                last_ok_str = cache.get("last_ok_iso")
                if last_ok_str:
                    last_ok = datetime.fromisoformat(last_ok_str)
                    delta = datetime.now(timezone.utc) - last_ok
                    if delta.total_seconds() < 72 * 3600:
                        return True
        except Exception:
            pass

    if LICENSE_API_URL:
        try:
            with httpx.Client(timeout=2.0) as client:
                res = client.post(LICENSE_API_URL, json={"token": license_token, "consume": False})
            if res.status_code == 200:
                data = res.json()
                if data.get("valid") and data.get("active"):
                    try:
                        with open(CACHE_FILE, "w") as f:
                            json.dump({
                                "token_hash": token_hash,
                                "last_ok_iso": datetime.now(timezone.utc).isoformat()
                            }, f)
                    except Exception:
                        pass
                    return True
                else:
                    if os.path.exists(CACHE_FILE):
                        try:
                            os.remove(CACHE_FILE)
                        except Exception:
                            pass
                    return False
        except Exception:
            pass
    return False


def verify_access(token: str) -> bool:
    """Access gate WITHOUT incrementing usage. Returns True if token matches the local PAIRING_TOKEN."""
    if not token:
        return False
    return token == PAIRING_TOKEN
