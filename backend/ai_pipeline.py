import os
import httpx
import json
from dotenv import load_dotenv

load_dotenv()

NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/audio/transcriptions"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

NVIDIA_KEY = os.getenv("NVIDIA_NIM_API_KEY")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")

async def transcribe_audio(audio_bytes: bytes) -> str:
    if not NVIDIA_KEY:
        print("Warning: NVIDIA API key missing. Mocking STT.")
        return "launch youtube"
        
    try:
        files = {'file': ('audio.webm', audio_bytes, 'audio/webm')}
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
        print(f"STT Error: {e}")
        return ""

async def parse_intent(transcription: str) -> dict:
    if not OPENROUTER_KEY:
        print("Warning: OpenRouter key missing. Mocking LLM.")
        return {"action": "launch_kiosk", "parameters": {"target_id": "youtube"}}

    system_prompt = """
    You are an intent parser for a TV remote. Output ONLY valid JSON. 
    Allowed actions: 'launch_kiosk', 'media_control', 'search'. 
    Example: {"action": "launch_kiosk", "parameters": {"target_id": "youtube", "search_query": "gatos"}}
    """
    
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
        print(f"LLM Error: {e}")
        return {"action": "error"}
