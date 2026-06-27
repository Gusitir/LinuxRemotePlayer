import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Header, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from input_emulator import gamepad, mouse
from discovery import get_installed_apps
from kiosk import launch_kiosk, kill_existing_kiosks, gui_env
from ai_pipeline import transcribe_audio, parse_intent
from auth import validate_license_and_increment, verify_access
import json
import re
import subprocess
from urllib.parse import quote_plus
import os
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="LinuxRemotePlayer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

VOICE_ENABLED = os.getenv("ENABLE_VOICE", "false").lower() == "true"

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/config")
def get_config():
    return {"voice_enabled": VOICE_ENABLED}

@app.get("/api/debug")
def debug_info():
    import input_emulator
    return {
        "evdev_available": input_emulator.EVDEV_AVAILABLE,
        "is_ui_created": getattr(input_emulator.gamepad, 'ui', None) is not None,
        "os": __import__('platform').system()
    }

@app.get("/api/apps")
def list_apps():
    return {
        "type": "discovery_sync",
        "installed_apps": get_installed_apps(),
        "suggested_kiosks": [
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
    }

def require_token(x_auth_token: str = Header(default="")):
    if not verify_access(x_auth_token):
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.post("/api/kiosk/launch", dependencies=[Depends(require_token)])
async def start_kiosk(payload: dict):
    target = payload.get("url")
    if target:
        success = launch_kiosk(target)
        return {"status": "success" if success else "error"}
    return {"status": "error", "message": "Missing url"}

@app.post("/api/kiosk/kill", dependencies=[Depends(require_token)])
async def stop_kiosk():
    kill_existing_kiosks()
    return {"status": "success"}

@app.post("/api/app/launch", dependencies=[Depends(require_token)])
async def launch_native_app(payload: dict):
    app_id = payload.get("id")
    if not app_id:
        return {"status": "error", "message": "Missing id"}
    match = next((a for a in get_installed_apps() if a["id"] == app_id), None)
    if not match or not match.get("exec"):
        return {"status": "error", "message": "App not found"}
    import shlex
    cleaned = re.sub(r'%[a-zA-Z]', '', match["exec"]).strip()
    try:
        subprocess.Popen(shlex.split(cleaned), env=gui_env(), stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
        return {"status": "success"}
    except Exception as ex:
        return {"status": "error", "message": str(ex)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = "guest"):
    await websocket.accept()
    if not await asyncio.to_thread(verify_access, token):
        await websocket.send_text(json.dumps({"status": "error", "message": "Unauthorized"}))
        await websocket.close(code=1008)
        return
    try:
        while True:
            message = await websocket.receive()

            if message.get("type") == "websocket.disconnect":
                break

            if message.get("bytes"):
                if not VOICE_ENABLED:
                    await websocket.send_text(json.dumps({"status": "error", "message": "Voice disabled"}))
                    continue
                audio_data = message.get("bytes")
                if len(audio_data) > 5_000_000:
                    await websocket.send_text(json.dumps({"status": "error", "message": "Audio too large"}))
                    continue

                # Correr peticion sincrona a supabase en un thread
                is_valid = await asyncio.to_thread(validate_license_and_increment, token)
                if not is_valid:
                    await websocket.send_text(json.dumps({"status": "error", "message": "Rate limit exceeded or invalid license."}))
                    continue

                await websocket.send_text(json.dumps({"status": "processing", "message": "Listening..."}))
                text = await transcribe_audio(audio_data)

                if text:
                    await websocket.send_text(json.dumps({"status": "processing", "message": f"Intent: {text}"}))
                    intent = await parse_intent(text)

                    action = intent.get("action")
                    params = intent.get("parameters", {})

                    if action == "launch_kiosk":
                        target = params.get("target_id")
                        if target:
                            safe_target = re.sub(r'[^a-z0-9]', '', str(target).lower())
                            if not safe_target:
                                await websocket.send_text(json.dumps({"status": "error", "message": "Invalid target"}))
                                continue
                            url = f"https://{safe_target}.com"
                            if safe_target == "youtube":
                                query = quote_plus(params.get('search_query', ''))
                                url = f"https://youtube.com/results?search_query={query}"
                            launch_kiosk(url)
                            await websocket.send_text(json.dumps({"status": "success", "message": "Launched app"}))
                    elif action == "media_control":
                        media_key = params.get("key")
                        allowed_media = {"KEY_VOLUMEUP", "KEY_VOLUMEDOWN", "KEY_MUTE", "KEY_PLAYPAUSE"}
                        if media_key in allowed_media:
                            await gamepad.press_button(media_key)
                            await websocket.send_text(json.dumps({"status": "success", "message": f"Media: {media_key}"}))
                        else:
                            await websocket.send_text(json.dumps({"status": "error", "message": "Invalid media key"}))
                    elif action == "search":
                        query = quote_plus(params.get("search_query", ""))
                        if query:
                            launch_kiosk(f"https://www.youtube.com/results?search_query={query}")
                            await websocket.send_text(json.dumps({"status": "success", "message": f"Searching: {params.get('search_query', '')}"}))
                        else:
                            await websocket.send_text(json.dumps({"status": "error", "message": "Empty search"}))
                    else:
                        await websocket.send_text(json.dumps({"status": "error", "message": "Unknown action"}))
                else:
                    await websocket.send_text(json.dumps({"status": "error", "message": "Could not understand audio"}))

            elif message.get("text"):
                data = message.get("text")
                try:
                    payload = json.loads(data)
                except json.JSONDecodeError:
                    await websocket.send_text(json.dumps({"status": "error", "message": "Invalid JSON format"}))
                    continue

                msg_type = payload.get("type")
                if msg_type == "input" and payload.get("device") == "gamepad":
                    action = payload.get("action")
                    key = payload.get("key")
                    if action == "press" and key:
                        await gamepad.press_button(key)
                    await websocket.send_text(json.dumps({"status": "received"}))
                elif msg_type == "pointer":
                    click = payload.get("click")
                    if payload.get("scroll") is not None:
                        await mouse.scroll(payload.get("scroll", 0))
                    elif click:
                        await mouse.click("right" if click == "right" else "left")
                    else:
                        await mouse.move(payload.get("dx", 0), payload.get("dy", 0))
                elif msg_type == "text":
                    await gamepad.type_text(payload.get("text", ""))
                elif payload.get("action") == "media_control":
                    media_key = payload.get("parameters", {}).get("key")
                    allowed_media = {"KEY_VOLUMEUP", "KEY_VOLUMEDOWN", "KEY_MUTE", "KEY_PLAYPAUSE", "KEY_PLAY", "KEY_PAUSE", "KEY_STOP", "KEY_NEXTSONG", "KEY_PREVIOUSSONG", "KEY_FASTFORWARD", "KEY_REWIND"}
                    if media_key in allowed_media:
                        await gamepad.press_button(media_key)
                    await websocket.send_text(json.dumps({"status": "received"}))
    except WebSocketDisconnect:
        print("Client disconnected")

frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")
