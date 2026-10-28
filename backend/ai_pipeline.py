"""Voice pipeline client and local STT/NLU orchestrator (v2.0).

Voice commands are processed 100% locally and offline on the appliance:
1. In-memory audio transcoding (WebM/Opus or MP4/AAC -> WAV PCM 16kHz mono).
2. Energy-based VAD and silence filtering.
3. Whisper.cpp AVX1 speech-to-text inference.
4. Deterministic Local NLU Intent Engine (<50ms).
"""
import os
import asyncio
import logging
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

from local_stt import WhisperRunner
from local_intent import parse_intent

logger = logging.getLogger("ai_pipeline")

load_dotenv()

_whisper_runner: Optional[WhisperRunner] = None


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
