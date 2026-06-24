import os
import httpx
import json
from dotenv import load_dotenv

load_dotenv()

# Cloud URLs
NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/audio/transcriptions"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Keys
NVIDIA_KEY = os.getenv("NVIDIA_NIM_API_KEY")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")

# Local AI Config
USE_LOCAL_AI = os.getenv("USE_LOCAL_AI", "false").lower() == "true"
LOCAL_WHISPER_URL = os.getenv("LOCAL_WHISPER_URL")
LOCAL_OLLAMA_URL = os.getenv("LOCAL_OLLAMA_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

async def transcribe_audio(audio_bytes: bytes) -> str:
    files = {'file': ('audio.webm', audio_bytes, 'audio/webm')}
    
    if USE_LOCAL_AI:
        if not LOCAL_WHISPER_URL:
            print("Error: LOCAL_WHISPER_URL no configurado.")
            return ""
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    LOCAL_WHISPER_URL,
                    files=files,
                    timeout=15.0
                )
                response.raise_for_status()
                result = response.json()
                return result.get('text', '')
        except Exception as e:
            print(f"Local STT Error: {e}")
            return ""
    else:
        if not NVIDIA_KEY:
            print("Warning: NVIDIA API key missing. Mocking STT.")
            return "launch youtube"
            
        try:
            data = {'model': 'nvidia/nemotron-3.5-asr'}
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    NVIDIA_API_URL,
                    headers={"Authorization": f"Bearer {NVIDIA_KEY}"},
                    data=data,
                    files=files,
                    timeout=10.0
                )
                response.raise_for_status()
                result = response.json()
                return result.get('text', '')
        except Exception as e:
            print(f"Cloud STT Error: {e}")
            return ""

async def parse_intent(transcription: str) -> dict:
    system_prompt = """
    You are an intent parser for a TV remote. Output ONLY valid JSON. 
    Allowed actions: 'launch_kiosk', 'media_control', 'search'. 
    Example: {"action": "launch_kiosk", "parameters": {"target_id": "youtube", "search_query": "gatos"}}
    """
    
    if USE_LOCAL_AI:
        if not LOCAL_OLLAMA_URL:
            print("Error: LOCAL_OLLAMA_URL no configurado.")
            return {"action": "error"}
            
        try:
            async with httpx.AsyncClient() as client:
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
                return json.loads(content)
        except Exception as e:
            print(f"Local LLM Error: {e}")
            return {"action": "error"}
    else:
        if not OPENROUTER_KEY:
            print("Warning: OpenRouter key missing. Mocking LLM.")
            return {"action": "launch_kiosk", "parameters": {"target_id": "youtube"}}
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    OPENROUTER_API_URL,
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_KEY}",
                        "HTTP-Referer": "http://localhost",
                        "X-Title": "LinuxRemotePlayer"
                    },
                    json={
                        "model": "meta-llama/llama-3.1-8b-instruct:free",
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
                return json.loads(content)
        except Exception as e:
            print(f"Cloud LLM Error: {e}")
            return {"action": "error"}
