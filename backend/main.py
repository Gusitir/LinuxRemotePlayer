import asyncio
import json
import os
import re
import socket
import subprocess
import time
import logging
from urllib.parse import quote_plus

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Header, Depends, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from dotenv import set_key
import httpx
import io
import segno
import auth

from input_emulator import gamepad, mouse
from discovery import get_installed_apps
from kiosk import launch_kiosk, kill_existing_kiosks, gui_env
from ai_pipeline import transcribe_audio, parse_intent
from auth import validate_license_and_increment, verify_access, is_license_valid_cached_or_online

logger = logging.getLogger("main")

app = FastAPI(title="LinuxRemotePlayer API")

# SEC-01 CORS allow_origins=[] (rely on same-origin only)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

VOICE_ENABLED = os.getenv("ENABLE_VOICE", "false").lower() == "true"

# COR-07 Log startup error if ENABLE_VOICE is true but keys are missing
if VOICE_ENABLED:
    import ai_pipeline
    if ai_pipeline.USE_LOCAL_AI:
        if not ai_pipeline.LOCAL_WHISPER_URL or not ai_pipeline.LOCAL_OLLAMA_URL:
            logger.error("ENABLE_VOICE is True, but local AI Whisper/Ollama URLs are missing.")
    else:
        if not ai_pipeline.NVIDIA_KEY or not ai_pipeline.OPENROUTER_KEY:
            logger.error("ENABLE_VOICE is True, but Cloud NVIDIA/OpenRouter API keys are missing.")

# Read VERSION file (C2-3)
VERSION = "1.0.0"
version_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "VERSION"))
if os.path.exists(version_path):
    try:
        with open(version_path, "r") as f:
            VERSION = f.read().strip()
    except Exception:
        pass


def is_newer_version(current_ver: str, latest_ver: str) -> bool:
    try:
        c_parts = [int(x) for x in current_ver.lstrip('v').split('.')]
        l_parts = [int(x) for x in latest_ver.lstrip('v').split('.')]
        return l_parts > c_parts
    except Exception:
        return latest_ver != current_ver


# HYG-03 Constants organization
SUGGESTED_KIOSKS = [
    {"id": "netflix", "name": "Netflix", "url": "https://netflix.com", "color": "#E50914"},
    {"id": "youtube", "name": "YouTube", "url": "https://youtube.com/tv", "color": "#FF0000"},
    {"id": "hulu", "name": "Hulu", "url": "https://hulu.com", "color": "#1CE783"},
    {"id": "hbomax", "name": "Max", "url": "https://play.max.com", "color": "#7B2BF9"},
    {"id": "primevideo", "name": "Prime Video", "url": "https://www.primevideo.com", "color": "#00A8E1"},
    {"id": "disney", "name": "Disney+", "url": "https://www.disneyplus.com", "color": "#113CCF"},
    {"id": "spotify", "name": "Spotify", "url": "https://open.spotify.com", "color": "#1DB954"},
    {"id": "twitch", "name": "Twitch", "url": "https://twitch.tv", "color": "#9146FF"},
    {"id": "plex", "name": "Plex", "url": "https://app.plex.tv", "color": "#E5A00D"}
]

SUGGESTED_KIOSKS_MAP = {k["id"]: k["url"] for k in SUGGESTED_KIOSKS}

MEDIA_KEYS = {
    "KEY_VOLUMEUP", "KEY_VOLUMEDOWN", "KEY_MUTE", "KEY_PLAYPAUSE",
    "KEY_PLAY", "KEY_PAUSE", "KEY_STOP", "KEY_NEXTSONG",
    "KEY_PREVIOUSSONG", "KEY_FASTFORWARD", "KEY_REWIND"
}


# COR-09 Pydantic Request Models
class KioskLaunchBody(BaseModel):
    url: str

    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        if not v.startswith("http://") and not v.startswith("https://"):
            raise ValueError("URL must start with http:// or https://")
        return v


class AppLaunchBody(BaseModel):
    id: str = Field(..., max_length=128)


class ActivateBody(BaseModel):
    key: str = Field(..., min_length=1)


class TokenBucket:
    """WS token bucket rate limiter (SEC-07)."""
    def __init__(self, rate: float, capacity: float):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()

    def consume(self, amount: float = 1.0) -> bool:
        now = time.time()
        elapsed = now - self.last_update
        self.last_update = now
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False


def require_token(x_auth_token: str = Header(default="")):
    if not verify_access(x_auth_token):
        raise HTTPException(status_code=401, detail="Unauthorized")


def detect_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("1.1.1.1", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and ip != "127.0.0.1":
            return ip
    except Exception:
        pass
    return "127.0.0.1"


def require_local(request: Request):
    client_host = request.client.host
    if client_host.startswith("::ffff:"):
        client_host = client_host[7:]
    if client_host not in ("127.0.0.1", "::1", "localhost"):
        raise HTTPException(status_code=403, detail="Forbidden. Local access only.")


@app.get("/api/pairing-token")
def get_pairing_token(request: Request):
    require_local(request)
    return {"token": auth.PAIRING_TOKEN}


@app.post("/api/pairing-token/regenerate")
def regenerate_pairing_token(request: Request):
    require_local(request)
    import secrets
    new_token = secrets.token_urlsafe(16)
    token_file = os.path.abspath(os.path.join(os.path.dirname(__file__), ".pairing_token"))
    try:
        with open(token_file, "w") as f:
            f.write(new_token)
        os.chmod(token_file, 0o600)
        auth.PAIRING_TOKEN = new_token
        logger.info("Pairing token regenerated via local API.")
        return {"status": "success", "token": new_token}
    except Exception as e:
        logger.error(f"Failed to regenerate .pairing_token: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/pairing-qr")
def get_pairing_qr(request: Request):
    require_local(request)
    lan_ip = detect_ip()
    port = os.getenv("PORT", "8000")
    pairing_url = f"https://{lan_ip}:{port}/?token={auth.PAIRING_TOKEN}"
    try:
        qr = segno.make(pairing_url)
        out = io.BytesIO()
        qr.save(out, kind='svg', scale=6, dark='#3b82f6', finder_dark='#22c55e')
        return Response(content=out.getvalue(), media_type="image/svg+xml")
    except Exception as e:
        logger.error(f"Failed to generate pairing QR: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/config")
def get_config():
    return {
        "voice_enabled": VOICE_ENABLED,
        "hostname": socket.gethostname(),
        "version": VERSION,
        "buy_url": os.getenv("BUY_URL", "https://buy.stripe.com/mock-link")
    }


@app.get("/api/ca")
def get_ca():
    ca_path = os.path.join(os.path.dirname(__file__), "certs", "ca.pem")
    if os.path.exists(ca_path):
        return FileResponse(ca_path, media_type="application/x-pem-file", filename="ca.pem")
    raise HTTPException(status_code=404, detail="CA certificate not found")


@app.get("/api/debug", dependencies=[Depends(require_token)])
def debug_info():
    import input_emulator
    return {
        "evdev_available": input_emulator.EVDEV_AVAILABLE,
        "is_ui_created": getattr(input_emulator.gamepad, 'ui', None) is not None,
        "os": __import__('platform').system()
    }


@app.get("/api/apps", dependencies=[Depends(require_token)])
def list_apps():
    return {
        "type": "discovery_sync",
        "installed_apps": get_installed_apps(),
        "suggested_kiosks": SUGGESTED_KIOSKS
    }


@app.post("/api/license/activate", dependencies=[Depends(require_token)])
async def activate_license(payload: ActivateBody):
    valid = await asyncio.to_thread(is_license_valid_cached_or_online, payload.key)
    if not valid:
        raise HTTPException(status_code=400, detail="Clave no válida")
    try:
        env_file = os.path.abspath(os.path.join(os.path.dirname(__file__), ".env"))
        if not os.path.exists(env_file):
            with open(env_file, "w") as f:
                f.write("")
        await asyncio.to_thread(set_key, env_file, "LICENSE_TOKEN", payload.key)
        try:
            os.chmod(env_file, 0o600)
        except Exception as pe:
            logger.warning(f"Could not set secure permissions on .env file: {pe}")
        os.environ["LICENSE_TOKEN"] = payload.key
        return {"status": "success", "plan": "lifetime"}
    except Exception as e:
        logger.error(f"Failed to save license key: {e}")
        raise HTTPException(status_code=500, detail="Error interno al guardar la clave")


@app.get("/api/license/status", dependencies=[Depends(require_token)])
async def get_license_status():
    license_token = os.getenv("LICENSE_TOKEN", "")
    licensed = await asyncio.to_thread(is_license_valid_cached_or_online, license_token)
    return {
        "licensed": licensed,
        "plan": "lifetime" if licensed else None,
        "voice_enabled": VOICE_ENABLED
    }


@app.get("/api/update/check", dependencies=[Depends(require_token)])
async def check_update():
    repo = os.getenv("GITHUB_REPO", "agustin/linuxremoteplayer")
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(url)
        if res.status_code == 200:
            data = res.json()
            latest = data.get("tag_name", "").lstrip('v')
            if latest:
                update_avail = is_newer_version(VERSION, latest)
                return {
                    "current": VERSION,
                    "latest": latest,
                    "update_available": update_avail
                }
    except Exception as e:
        logger.warning(f"Failed to check GitHub releases: {e}")
    return {
        "current": VERSION,
        "latest": None,
        "update_available": False
    }


@app.post("/api/update/apply", dependencies=[Depends(require_token)])
async def apply_update():
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts", "update.sh"))
    if not os.path.exists(script_path):
        raise HTTPException(status_code=404, detail="Update script not found")
    try:
        with open("/tmp/lrp-update.log", "a") as log_file:
            subprocess.Popen(
                ["bash", script_path],
                stdout=log_file,
                stderr=log_file,
                start_new_session=True
            )
        return {"status": "started"}
    except Exception as e:
        logger.error(f"Failed to start update script: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/kiosk/launch", dependencies=[Depends(require_token)])
async def start_kiosk(payload: KioskLaunchBody):
    success = launch_kiosk(payload.url)
    if success:
        return {"status": "success"}
    raise HTTPException(status_code=400, detail="Failed to launch kiosk")


@app.post("/api/kiosk/kill", dependencies=[Depends(require_token)])
async def stop_kiosk():
    kill_existing_kiosks()
    return {"status": "success"}


@app.post("/api/app/launch", dependencies=[Depends(require_token)])
async def launch_native_app(payload: AppLaunchBody):
    app_id = payload.id
    match = next((a for a in get_installed_apps() if a["id"] == app_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="App not found")
    if not match.get("exec"):
        raise HTTPException(status_code=400, detail="App executable path missing")

    import shlex
    cleaned = re.sub(r'%[a-zA-Z]', '', match["exec"]).strip()
    try:
        subprocess.Popen(shlex.split(cleaned), env=gui_env(), stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
        return {"status": "success"}
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = "guest"):
    await websocket.accept()

    # SEC-06 WS query param fallback and auth initialization
    auth_token = token
    is_authenticated = False

    if auth_token and auth_token != "guest":
        if await asyncio.to_thread(verify_access, auth_token):
            is_authenticated = True

    rate_limiter = TokenBucket(rate=60.0, capacity=120.0)
    auth_start = time.time()

    async def safe_send_json(data):
        try:
            await websocket.send_text(json.dumps(data))
        except RuntimeError:
            logger.debug("Attempted to send text on closed WebSocket.")

    try:
        while True:
            # 3s authentication timeout (SEC-06)
            if not is_authenticated:
                remaining = 3.0 - (time.time() - auth_start)
                if remaining <= 0:
                    logger.warning("WebSocket auth timeout exceeded.")
                    await safe_send_json({"status": "error", "message": "Auth timeout"})
                    await websocket.close(code=1008)
                    return
                try:
                    message = await asyncio.wait_for(websocket.receive(), timeout=remaining)
                except asyncio.TimeoutError:
                    logger.warning("WebSocket auth timeout exceeded.")
                    await safe_send_json({"status": "error", "message": "Auth timeout"})
                    await websocket.close(code=1008)
                    return
            else:
                message = await websocket.receive()

            if message.get("type") == "websocket.disconnect":
                break

            if message.get("bytes"):
                if not is_authenticated:
                    await safe_send_json({"status": "error", "message": "Unauthorized"})
                    await websocket.close(code=1008)
                    return

                if not VOICE_ENABLED:
                    await safe_send_json({"status": "error", "message": "Voice disabled"})
                    continue
                audio_data = message.get("bytes")
                if len(audio_data) > 5_000_000:
                    await safe_send_json({"status": "error", "message": "Audio too large"})
                    continue

                # Query valid license from local environment / Edge Function cache
                license_token = os.getenv("LICENSE_TOKEN", "")
                is_valid = await asyncio.to_thread(validate_license_and_increment, license_token)
                if not is_valid:
                    await safe_send_json({"status": "error", "message": "Rate limit exceeded or invalid license."})
                    continue

                await safe_send_json({"status": "processing", "message": "Listening..."})
                text = await transcribe_audio(audio_data)

                if text:
                    await safe_send_json({"status": "processing", "message": f"Intent: {text}"})
                    intent = await parse_intent(text)

                    action = intent.get("action")
                    params = intent.get("parameters", {})

                    # COR-01 WS Voice responses in all branches
                    if action == "launch_kiosk":
                        target = params.get("target_id")
                        if target:
                            # SEC-04 voice target whitelist
                            target_url = SUGGESTED_KIOSKS_MAP.get(target)
                            if target_url:
                                if target == "youtube":
                                    query = quote_plus(params.get('search_query', ''))
                                    target_url = f"https://youtube.com/results?search_query={query}"
                                success = launch_kiosk(target_url)
                                if success:
                                    await safe_send_json({"status": "success", "message": "Launched app"})
                                else:
                                    await safe_send_json({"status": "error", "message": "Failed to launch app"})
                            else:
                                await safe_send_json({"status": "error", "message": f"App no reconocida: {target}"})
                        else:
                            await safe_send_json({"status": "error", "message": "Target missing"})
                    elif action == "media_control":
                        media_key = params.get("key")
                        if media_key in MEDIA_KEYS:
                            await gamepad.press_button(media_key)
                            await safe_send_json({"status": "success", "message": f"Media: {media_key}"})
                        else:
                            await safe_send_json({"status": "error", "message": "Invalid media key"})
                    elif action == "search":
                        query = quote_plus(params.get("search_query", ""))
                        if query:
                            success = launch_kiosk(f"https://www.youtube.com/results?search_query={query}")
                            if success:
                                await safe_send_json({"status": "success", "message": f"Searching: {params.get('search_query', '')}"})
                            else:
                                await safe_send_json({"status": "error", "message": "Failed to search"})
                        else:
                            await safe_send_json({"status": "error", "message": "Empty search"})
                    else:
                        await safe_send_json({"status": "error", "message": "Unknown action"})
                else:
                    await safe_send_json({"status": "error", "message": "Could not understand audio"})

            elif message.get("text"):
                # SEC-07 Rate limit checks
                if not rate_limiter.consume():
                    logger.warning("WS message dropped due to rate limit threshold.")
                    continue

                data = message.get("text")
                try:
                    payload = json.loads(data)
                except json.JSONDecodeError:
                    await safe_send_json({"status": "error", "message": "Invalid JSON format"})
                    continue

                msg_type = payload.get("type")

                # SEC-06 auth frame
                if msg_type == "auth":
                    auth_token = payload.get("token")
                    if auth_token and await asyncio.to_thread(verify_access, auth_token):
                        is_authenticated = True
                        await safe_send_json({"status": "success", "message": "Authenticated"})
                    else:
                        await safe_send_json({"status": "error", "message": "Unauthorized"})
                        await websocket.close(code=1008)
                        return
                    continue

                if not is_authenticated:
                    await safe_send_json({"status": "error", "message": "Unauthorized"})
                    await websocket.close(code=1008)
                    return

                # CONN-05 Ping/Pong
                if msg_type == "ping":
                    await safe_send_json({"type": "pong"})
                    continue

                if msg_type == "input" and payload.get("device") == "gamepad":
                    action = payload.get("action")
                    key = payload.get("key")
                    if action == "press" and key:
                        # Whitelist check propagated to WS response (COR-10)
                        from input_emulator import ALLOWED_KEYS
                        if key in ALLOWED_KEYS:
                            await gamepad.press_button(key)
                            await safe_send_json({"status": "received"})
                        else:
                            await safe_send_json({"status": "error", "message": "Disallowed key"})
                    else:
                        await safe_send_json({"status": "error", "message": "Invalid gamepad payload"})
                elif msg_type == "pointer":
                    click = payload.get("click")
                    if payload.get("scroll") is not None:
                        await mouse.scroll(payload.get("scroll", 0))
                    elif click:
                        await mouse.click("right" if click == "right" else "left")
                    else:
                        await mouse.move(payload.get("dx", 0), payload.get("dy", 0))
                elif msg_type == "text":
                    text_payload = payload.get("text", "")
                    # SEC-07 payload limit cap
                    if len(text_payload) > 500:
                        logger.warning(f"Truncating incoming text payload from {len(text_payload)} to 500 chars.")
                        text_payload = text_payload[:500]
                    await gamepad.type_text(text_payload)
                elif payload.get("action") == "media_control":
                    media_key = payload.get("parameters", {}).get("key")
                    if media_key in MEDIA_KEYS:
                        await gamepad.press_button(media_key)
                        await safe_send_json({"status": "received"})
                    else:
                        await safe_send_json({"status": "error", "message": "Disallowed key"})
                else:
                    # COR-10 unknown messages
                    await safe_send_json({"status": "error", "message": f"unknown_type: {msg_type}"})

    except WebSocketDisconnect:
        logger.info("Client disconnected")

frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")
