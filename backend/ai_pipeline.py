import os
import httpx
import json
import re
import logging
from dotenv import load_dotenv

logger = logging.getLogger("ai_pipeline")

load_dotenv()

# Cloud AI endpoints. Defaults target the validated production stack (Together AI:
# Whisper-large-v3 for STT + Qwen2.5-7B-Instruct-Turbo for intent). Override any of
# these via backend/.env to use another OpenAI-compatible provider.
CLOUD_STT_URL = os.getenv("CLOUD_STT_URL", "https://api.together.xyz/v1/audio/transcriptions")
CLOUD_STT_KEY = os.getenv("CLOUD_STT_KEY")
CLOUD_STT_MODEL = os.getenv("CLOUD_STT_MODEL", "openai/whisper-large-v3")

CLOUD_LLM_URL = os.getenv("CLOUD_LLM_URL", "https://api.together.xyz/v1/chat/completions")
CLOUD_LLM_KEY = os.getenv("CLOUD_LLM_KEY")
CLOUD_LLM_MODEL = os.getenv("CLOUD_LLM_MODEL", "Qwen/Qwen2.5-7B-Instruct-Turbo")

# Module-level shared httpx.AsyncClient (lazy init) — reused across requests (COR-07).
_client = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=httpx.Timeout(20.0, connect=5.0))
    return _client


def clean_json_content(content: str) -> str:
    """Strip markdown code-block fences and extract the first JSON object block."""
    content = content.strip()
    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)
    m = re.search(r"(\{.*\})", content, re.DOTALL)
    if m:
        return m.group(1)
    return content


async def transcribe_audio(audio_bytes: bytes) -> str:
    """Speech-to-text via the configured cloud STT endpoint.

    Detects the container by magic bytes (WebM/EBML vs MP4/ftyp) so iOS (mp4) and
    Android/desktop (webm) recordings are both sent with the right filename/mime.
    Returns the transcription text, or "" on any error.
    """
    filename = 'audio.webm'
    mime = 'audio/webm'
    if audio_bytes.startswith(b'\x1a\x45\xdf\xa3'):
        pass
    elif len(audio_bytes) > 8 and audio_bytes[4:8] == b'ftyp':
        filename = 'audio.m4a'
        mime = 'audio/mp4'

    if not CLOUD_STT_KEY:
        logger.error("CLOUD_STT_KEY missing — voice STT disabled.")
        return ""

    files = {'file': (filename, audio_bytes, mime)}
    try:
        response = await get_client().post(
            CLOUD_STT_URL,
            headers={"Authorization": f"Bearer {CLOUD_STT_KEY}"},
            data={'model': CLOUD_STT_MODEL},
            files=files,
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json().get('text', '')
    except Exception as e:
        logger.error(f"Cloud STT Error: {e}")
        return ""


async def parse_intent(transcription: str, valid_targets: list = None) -> dict:
    """Parse a Spanish voice command into a structured intent via the cloud LLM.

    The system prompt is built dynamically from `valid_targets` (the apps actually
    available on this device) — app ids are never hardcoded. Returns a dict whose
    "action" is launch_kiosk | media_control | search, or {"action": "error"}.
    """
    if valid_targets is None:
        valid_targets = []

    valid_apps_str = ", ".join(valid_targets)

    system_prompt = f"""
You are an intent parser for a TV remote. Output ONLY valid JSON.
Allowed actions: 'launch_kiosk', 'media_control', 'search'.

Valid app targets (launch_kiosk): [{valid_apps_str}]
Valid media keys (media_control): KEY_VOLUMEUP, KEY_VOLUMEDOWN, KEY_MUTE, KEY_PLAYPAUSE, KEY_PLAY, KEY_PAUSE, KEY_STOP, KEY_NEXTSONG, KEY_PREVIOUSSONG, KEY_FASTFORWARD, KEY_REWIND

NOTE: The user speaks Spanish. Map synonyms accordingly (e.g., sube/baja volumen, pausa, silencio, adelanta...).

Examples:
1. "abre netflix" -> {{"action": "launch_kiosk", "parameters": {{"target_id": "netflix"}}}}
2. "pon youtube de gatitos" -> {{"action": "launch_kiosk", "parameters": {{"target_id": "youtube", "search_query": "gatitos"}}}}
3. "sube el volumen" -> {{"action": "media_control", "parameters": {{"key": "KEY_VOLUMEUP"}}}}
4. "pausa el video" -> {{"action": "media_control", "parameters": {{"key": "KEY_PLAYPAUSE"}}}}
5. "silencio" -> {{"action": "media_control", "parameters": {{"key": "KEY_MUTE"}}}}
6. "busca recetas de cocina" -> {{"action": "search", "parameters": {{"search_query": "recetas de cocina"}}}}
"""

    if not CLOUD_LLM_KEY:
        logger.error("CLOUD_LLM_KEY missing — voice intent disabled.")
        return {"action": "error"}

    try:
        response = await get_client().post(
            CLOUD_LLM_URL,
            headers={"Authorization": f"Bearer {CLOUD_LLM_KEY}"},
            json={
                "model": CLOUD_LLM_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": transcription},
                ],
                "response_format": {"type": "json_object"},
            },
            timeout=10.0,
        )
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        intent = json.loads(clean_json_content(content))
        action = intent.get("action")
        if action not in {"launch_kiosk", "media_control", "search"}:
            logger.warning(f"Invalid voice intent action parsed: {action}")
            return {"action": "error"}
        return intent
    except Exception as e:
        logger.error(f"Cloud LLM Error: {e}")
        return {"action": "error"}
