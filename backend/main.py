from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from input_emulator import gamepad
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

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            if payload.get("type") == "input" and payload.get("device") == "gamepad":
                action = payload.get("action")
                key = payload.get("key")
                if action == "press" and key:
                    gamepad.press_button(key)
                    
            await websocket.send_text(json.dumps({"status": "received", "payload": payload}))
    except WebSocketDisconnect:
        print("Client disconnected")
