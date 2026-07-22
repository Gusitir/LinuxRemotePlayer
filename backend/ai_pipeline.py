"""AI pipeline client — sends voice commands to the ai-proxy Edge Function (v1.9).

The HTPC holds NO AI provider keys: the proxy (Supabase Edge Function) validates
license/device/quota server-side and calls Together AI (STT + intent LLM).
"""
import os
import json
import hashlib
import logging
import uuid
import httpx
from dotenv import load_dotenv

logger = logging.getLogger("ai_pipeline")

load_dotenv()

AI_PROXY_URL = os.getenv(
    "AI_PROXY_URL",
    "https://tbijfdbtauzxbsbkujbs.functions.supabase.co/ai-proxy",
)

# Module-level shared httpx.AsyncClient (lazy init) — reused across requests (COR-07).
_client = None

_device_id = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=httpx.Timeout(35.0, connect=5.0))
    return _client


def get_device_id() -> str:
    """Stable anonymous device id: sha256 of /etc/machine-id (hostname+MAC fallback)."""
    global _device_id
    if _device_id is None:
        raw = ""
        try:
            with open("/etc/machine-id", "r") as f:
                raw = f.read().strip()
        except Exception as e:
            logger.warning(f"Could not read /etc/machine-id ({e}); using fallback id.")
        if not raw:
            raw = f"{os.uname().nodename}-{uuid.getnode()}"
        _device_id = hashlib.sha256(raw.encode()).hexdigest()
    return _device_id


async def voice_command(audio_bytes: bytes, valid_targets: list = None) -> dict:
    """Send one voice command to the ai-proxy; returns the proxy's JSON dict.

    Success: {"ok": True, "text": ..., "intent": {...}, "remaining_today": N}.
    Failure: {"ok": False, "reason": <no_speech|quota_exceeded|in_use_elsewhere|
    invalid_license|service_disabled|global_cap|audio_too_large|stt_error|
    llm_error|proxy_unreachable|http_NNN>}.
    """
    token = os.getenv("LICENSE_TOKEN", "")
    if not token:
        return {"ok": False, "reason": "invalid_license"}

    # Container by magic bytes: MP4/ftyp (iOS) vs WebM/EBML (Android/desktop default)
    filename = "audio.webm"
    mime = "audio/webm"
    if len(audio_bytes) > 8 and audio_bytes[4:8] == b"ftyp":
        filename = "audio.m4a"
        mime = "audio/mp4"

    data = {
        "token": token,
        "device_id": get_device_id(),
        "targets": json.dumps(valid_targets or []),
    }
    files = {"audio": (filename, audio_bytes, mime)}
    try:
        response = await get_client().post(AI_PROXY_URL, data=data, files=files)
        try:
            body = response.json()
        except Exception:
            body = {}
        if response.status_code == 200:
            return body
        reason = body.get("reason") or body.get("error") or f"http_{response.status_code}"
        logger.warning(f"ai-proxy returned {response.status_code}: {reason}")
        return {"ok": False, "reason": reason}
    except Exception as e:
        logger.error(f"ai-proxy unreachable: {e}")
        return {"ok": False, "reason": "proxy_unreachable"}
