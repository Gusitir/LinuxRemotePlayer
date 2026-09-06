"""Voice pipeline client and local STT/NLU orchestrator (v2.0).

Voice commands are processed 100% locally and offline on the appliance:
1. In-memory audio transcoding (WebM/Opus or MP4/AAC -> WAV PCM 16kHz mono).
2. Energy-based VAD and silence filtering.
3. Whisper.cpp AVX1 speech-to-text inference.
4. Deterministic Local NLU Intent Engine (<50ms).
"""
import os
import json
import asyncio
import hashlib
import logging
import uuid
from typing import Optional, List, Dict, Any
import httpx
from dotenv import load_dotenv

from local_stt import WhisperRunner
from local_intent import parse_intent

logger = logging.getLogger("ai_pipeline")

load_dotenv()

AI_PROXY_URL = os.getenv(
    "AI_PROXY_URL",
    "https://tbijfdbtauzxbsbkujbs.functions.supabase.co/ai-proxy",
)

# Module-level shared httpx.AsyncClient (lazy init) — reused across requests (COR-07).
_client = None
_device_id = None
_whisper_runner: Optional[WhisperRunner] = None


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


def get_whisper_runner() -> WhisperRunner:
    """Lazy initialize whisper.cpp runner with appliance defaults."""
    global _whisper_runner
    if _whisper_runner is None:
        _whisper_runner = WhisperRunner()
    return _whisper_runner


async def voice_command(audio_bytes: bytes, valid_targets: Optional[List[str]] = None) -> Dict[str, Any]:
    """Process a voice command 100% locally on the appliance.

    Zero external API dependencies: operates fully offline with VAD, whisper.cpp AVX1,
    and local deterministic NLU intent parsing.

    Success: {"ok": True, "text": ..., "intent": {...}, "stt_metrics": {...}}.
    Failure: {"ok": False, "reason": <empty_audio|no_speech|stt_error|...>}
    """
    if not audio_bytes:
        return {"ok": False, "reason": "empty_audio"}

    runner = get_whisper_runner()
    model_name = os.getenv("LRP_WHISPER_MODEL", "ggml-base-q5_1.bin")

    # ASTRA-03: Execute CPU-bound STT in a separate thread to keep WebSocket loop unblocked
    stt_res = await asyncio.to_thread(
        runner.transcribe,
        audio_bytes=audio_bytes,
        model_name=model_name,
        language="es",
    )

    if not stt_res.get("ok"):
        reason = stt_res.get("reason", "stt_error")
        return {"ok": False, "reason": reason}

    transcribed_text = stt_res.get("text", "").strip()
    if not transcribed_text:
        return {"ok": False, "reason": "no_speech"}

    # Local NLU Intent Engine (<50ms)
    intent = parse_intent(transcribed_text, valid_targets=valid_targets)

    return {
        "ok": True,
        "text": transcribed_text,
        "intent": intent,
        "stt_metrics": {
            "latency_ms": stt_res.get("latency_ms"),
            "rtf": stt_res.get("rtf"),
            "peak_rss_mb": stt_res.get("peak_rss_mb"),
            "model": stt_res.get("model"),
        },
        "nlu_latency_ms": intent.get("latency_ms", 0.0),
    }


async def proxy_license_action(action: str, token: str, force: bool = False) -> dict:
    """Call the ai-proxy JSON branch: action = 'activate' | 'release'."""
    payload = {"action": action, "token": token, "device_id": get_device_id()}
    if force:
        payload["force"] = True
    try:
        response = await get_client().post(AI_PROXY_URL, json=payload)
        try:
            body = response.json()
        except Exception:
            body = {}
        body.setdefault("status", "error")
        body["http"] = response.status_code
        return body
    except Exception as e:
        logger.error(f"ai-proxy unreachable for {action}: {e}")
        return {"status": "unreachable"}
