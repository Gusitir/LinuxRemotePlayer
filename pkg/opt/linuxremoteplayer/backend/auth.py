import os
import secrets
import logging
import hashlib
import json
from datetime import datetime, timezone
import httpx
from dotenv import load_dotenv

logger = logging.getLogger("auth")

load_dotenv()

LICENSE_API_URL = os.getenv("LICENSE_API_URL", "https://tbijfdbtauzxbsbkujbs.functions.supabase.co/validate-license")
CACHE_FILE = os.path.join(os.path.dirname(__file__), ".license_cache")
PAIRING_TOKEN = os.getenv("PAIRING_TOKEN")

# SEC-01 auto-generated pairing token
if not PAIRING_TOKEN:
    token_file = os.path.join(os.path.dirname(__file__), ".pairing_token")
    if os.path.exists(token_file):
        try:
            with open(token_file, "r") as f:
                PAIRING_TOKEN = f.read().strip()
        except Exception as e:
            logger.error(f"Could not read .pairing_token file: {e}")
    if not PAIRING_TOKEN:
        PAIRING_TOKEN = secrets.token_urlsafe(16)
        try:
            with open(token_file, "w") as f:
                f.write(PAIRING_TOKEN)
            os.chmod(token_file, 0o600)
            logger.info("Generated auto-provisioned pairing token.")
        except Exception as e:
            logger.error(f"Could not write .pairing_token file: {e}")


def validate_license_and_increment(license_token: str) -> bool:
    if not license_token:
        logger.warning("License token is missing/empty.")
        return False

    token_hash = hashlib.sha256(license_token.encode()).hexdigest()

    # 1. Try online validation via Supabase Edge Function
    if LICENSE_API_URL:
        try:
            # Synchronous httpx call (executed inside asyncio.to_thread in main.py)
            with httpx.Client(timeout=3.0) as client:
                res = client.post(LICENSE_API_URL, json={"token": license_token, "consume": True})
            if res.status_code == 200:
                data = res.json()
                if data.get("valid") and data.get("active"):
                    try:
                        with open(CACHE_FILE, "w") as f:
                            json.dump({
                                "token_hash": token_hash,
                                "last_ok_iso": datetime.now(timezone.utc).isoformat()
                            }, f)
                    except Exception as ce:
                        logger.error(f"Failed to write license cache: {ce}")
                    return True
                else:
                    logger.warning(f"License token rejected by server: {data}")
                    if os.path.exists(CACHE_FILE):
                        try:
                            os.remove(CACHE_FILE)
                        except Exception:
                            pass
                    return False
            elif res.status_code == 429:
                logger.warning("License daily cap reached or rate-limited.")
                return False
            else:
                logger.warning(f"License API returned status {res.status_code}: {res.text}")
        except Exception as e:
            logger.warning(f"Failed to connect to license API ({e}). Checking offline grace...")

    # 2. Offline grace check (72 hours cache fallback)
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
                        logger.info("Allowing voice request via offline grace license cache (<72h).")
                        return True
                    else:
                        logger.warning("Offline grace cache expired (>72h).")
            else:
                logger.warning("Offline grace cache token hash mismatch.")
        except Exception as ce:
            logger.error(f"Failed to read/parse license cache: {ce}")

    logger.error("Sin conexión con el servidor de licencias")
    return False


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
