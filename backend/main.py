from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from input_emulator import gamepad
from discovery import get_installed_apps
from kiosk import launch_kiosk, kill_existing_kiosks
import json

app = FastAPI(title="LinuxRemotePlayer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/apps")
def list_apps():
    return {
        "type": "discovery_sync",
        "installed_apps": get_installed_apps(),
        "suggested_kiosks": [
            {"id": "netflix", "name": "Netflix", "url": "https://netflix.com", "icon": "netflix"},
            {"id": "youtube", "name": "YouTube", "url": "https://youtube.com/tv", "icon": "youtube"},
            {"id": "twitch", "name": "Twitch", "url": "https://twitch.tv", "icon": "twitch"}
        ]
    }

@app.post("/api/kiosk/launch")
async def start_kiosk(payload: dict):
    target = payload.get("url")
    if target:
        success = launch_kiosk(target)
        return {"status": "success" if success else "error"}
    return {"status": "error", "message": "Missing url"}

@app.post("/api/kiosk/kill")
async def stop_kiosk():
    kill_existing_kiosks()
    return {"status": "success"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"status": "error", "message": "Invalid JSON format"}))
                continue
            
            if payload.get("type") == "input" and payload.get("device") == "gamepad":
                action = payload.get("action")
                key = payload.get("key")
                if action == "press" and key:
                    await gamepad.press_button(key)
                    
            await websocket.send_text(json.dumps({"status": "received", "payload": payload}))
    except WebSocketDisconnect:
        print("Client disconnected")
