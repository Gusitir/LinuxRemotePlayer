import os
import httpx
import json
import re
import logging
from dotenv import load_dotenv

logger = logging.getLogger("ai_pipeline")

load_dotenv()

# Cloud URLs (Configurable to support Together AI, OpenRouter, NVIDIA, etc.)
CLOUD_STT_URL = os.getenv("CLOUD_STT_URL", "https://integrate.api.nvidia.com/v1/audio/transcriptions")
CLOUD_LLM_URL = os.getenv("CLOUD_LLM_URL", "https://openrouter.ai/api/v1/chat/completions")

# Keys
CLOUD_STT_KEY = os.getenv("CLOUD_STT_KEY", os.getenv("NVIDIA_NIM_API_KEY"))
CLOUD_LLM_KEY = os.getenv("CLOUD_LLM_KEY", os.getenv("OPENROUTER_API_KEY"))

# Models
CLOUD_STT_MODEL = os.getenv("CLOUD_STT_MODEL", os.getenv("NVIDIA_ASR_MODEL", "nvidia/nemotron-3.5-asr"))
CLOUD_LLM_MODEL = os.getenv("CLOUD_LLM_MODEL", "meta-llama/llama-3.1-8b-instruct:free")

# Local AI Config
USE_LOCAL_AI = os.getenv("USE_LOCAL_AI", "false").lower() == "true"
LOCAL_WHISPER_URL = os.getenv("LOCAL_WHISPER_URL")
LOCAL_OLLAMA_URL = os.getenv("LOCAL_OLLAMA_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

MOCK_AI = os.getenv("MOCK_AI", "false").lower() == "true"

# COR-07: Module-level shared httpx.AsyncClient (lazy init)
_client = None

def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=httpx.Timeout(20.0, connect=5.0))
    return _client


def clean_json_content(content: str) -> str:
    """Strip markdown code block fences and extract the first JSON object block."""
    content = content.strip()
    # Strip leading ```json or ```
    content = re.sub(r"^```(?:json)?\s*", "", content)
    # Strip trailing ```
    content = re.sub(r"\s*```$", "", content)
    # Extract outer {...}
    m = re.search(r"(\{.*\})", content, re.DOTALL)
    if m:
        return m.group(1)
    return content


async def transcribe_audio(audio_bytes: bytes) -> str:
    filename = 'audio.webm'
    mime = 'audio/webm'
    if audio_bytes.startswith(b'\x1a\x45\xdf\xa3'):
        pass
    elif len(audio_bytes) > 8 and audio_bytes[4:8] == b'ftyp':
        filename = 'audio.m4a'
        mime = 'audio/mp4'

    files = {'file': (filename, audio_bytes, mime)}
    client = get_client()

    if USE_LOCAL_AI:
        if not LOCAL_WHISPER_URL:
            logger.error("LOCAL_WHISPER_URL not configured.")
            return ""

        try:
            response = await client.post(
                LOCAL_WHISPER_URL,
                files=files,
                timeout=15.0
            )
            response.raise_for_status()
            result = response.json()
            return result.get('text', '')
        except Exception as e:
            logger.error(f"Local STT Error: {e}")
            return ""
    else:
        if not CLOUD_STT_KEY:
            if MOCK_AI:
                logger.info("Cloud STT API key missing. MOCK_AI active -> mock transcription.")
                return "launch youtube"
            logger.error("CLOUD_STT_KEY missing and MOCK_AI disabled.")
            return ""

        try:
            data = {'model': CLOUD_STT_MODEL}
            response = await client.post(
                CLOUD_STT_URL,
                headers={"Authorization": f"Bearer {CLOUD_STT_KEY}"},
                data=data,
                files=files,
                timeout=10.0
            )
            response.raise_for_status()
            result = response.json()
            return result.get('text', '')
        except Exception as e:
            logger.error(f"Cloud STT Error: {e}")
            return ""


async def parse_intent(transcription: str) -> dict:
    system_prompt = """
    You are an intent parser for a TV remote. Output ONLY valid JSON.
    Allowed actions: 'launch_kiosk', 'media_control', 'search'.
    Example: {"action": "launch_kiosk", "parameters": {"target_id": "youtube", "search_query": "gatos"}}
    """
    client = get_client()

    if USE_LOCAL_AI:
        if not LOCAL_OLLAMA_URL:
            logger.error("LOCAL_OLLAMA_URL not configured.")
            return {"action": "error"}

        try:
            response = await client.post(
                LOCAL_OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": transcription}
                    ],
                    "response_format": {"type": "json_object"}
                },
                timeout=20.0
            )
            response.raise_for_status()
            content = response.json()['choices'][0]['message']['content']
            cleaned = clean_json_content(content)
            intent = json.loads(cleaned)
            
            # Validation
            action = intent.get("action")
            if action not in {"launch_kiosk", "media_control", "search"}:
                logger.warning(f"Invalid voice intent action parsed: {action}")
                return {"action": "error"}
            return intent
        except Exception as e:
            logger.error(f"Local LLM Error: {e}")
            return {"action": "error"}
    else:
        if not CLOUD_LLM_KEY:
            if MOCK_AI:
                logger.info("Cloud LLM API key missing. MOCK_AI active -> mock intent.")
                return {"action": "launch_kiosk", "parameters": {"target_id": "youtube"}}
            logger.error("CLOUD_LLM_KEY missing and MOCK_AI disabled.")
            return {"action": "error"}

        try:
            response = await client.post(
                CLOUD_LLM_URL,
                headers={
                    "Authorization": f"Bearer {CLOUD_LLM_KEY}",
                    "HTTP-Referer": "http://localhost",
                    "X-Title": "LinuxRemotePlayer"
                },
                json={
                    "model": CLOUD_LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": transcription}
                    ],
                    "response_format": {"type": "json_object"}
                },
                timeout=10.0
            )
            response.raise_for_status()
            content = response.json()['choices'][0]['message']['content']
            cleaned = clean_json_content(content)
            intent = json.loads(cleaned)
            
            # Validation
            action = intent.get("action")
            if action not in {"launch_kiosk", "media_control", "search"}:
                logger.warning(f"Invalid voice intent action parsed: {action}")
                return {"action": "error"}
            return intent
        except Exception as e:
            logger.error(f"Cloud LLM Error: {e}")
            return {"action": "error"}
