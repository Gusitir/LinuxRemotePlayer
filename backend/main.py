"""Main FastAPI application server and endpoints for Linux Remote Player."""
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
from dotenv import load_dotenv
import io
try:
    import segno
except ImportError:
    segno = None

import auth

try:
    from config import (
        get_env_file, get_token_file, get_ca_cert_file, secure_permissions
    )
except ImportError:
    from backend.config import (
        get_env_file, get_token_file, get_ca_cert_file, secure_permissions
    )

load_dotenv(get_env_file())

from input_emulator import gamepad, mouse
from discovery import get_installed_apps
from kiosk import launch_kiosk, gui_env
from ai_pipeline import voice_command
from auth import verify_access

logger = logging.getLogger("main")

global_dropped_fast = 0
global_dropped_slow = 0

active_authenticated_websockets: set[WebSocket] = set()


async def revoke_all_websockets(code: int = 1008, reason: str = "Token revoked"):
    """ASTRA-02: Forcibly closes all active authenticated WebSocket sessions."""
    global active_authenticated_websockets
    to_close = list(active_authenticated_websockets)
    active_authenticated_websockets.clear()
    for ws in to_close:
        try:
            await ws.close(code=code)
        except Exception as e:
            logger.debug(f"Error closing revoked WebSocket: {e}")

# H9: /docs, /redoc y /openapi.json responden SIN gate a cualquiera en la LAN y enumeran
# toda la superficie de la API. Se apagan por defecto. El default es CERRADO a proposito:
# un .env sin LRP_DEV, o de un usuario en modo escritorio, tiene que quedar cerrado igual.
# En una maquina de desarrollo se enciende poniendo LRP_DEV=true a mano en backend/.env.
_DEV_DOCS = os.getenv("LRP_DEV", "false").lower() == "true"

app = FastAPI(
    title="LinuxRemotePlayer API",
    docs_url="/docs" if _DEV_DOCS else None,
    redoc_url="/redoc" if _DEV_DOCS else None,
    openapi_url="/openapi.json" if _DEV_DOCS else None,
)

# SEC-01 CORS allow_origins=[] (rely on same-origin only)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    from system_platform import router as system_router
except ImportError:
    from backend.system_platform import router as system_router

app.include_router(system_router)

def voice_enabled() -> bool:
    """Preferencia LOCAL de privacidad. PH24: ya no depende de ninguna licencia;
    se lee en cada consulta para que el toggle surta efecto sin reiniciar."""
    return os.getenv("ENABLE_VOICE", "true").lower() == "true"


import audio
logger.info(f"Audio backend selected: {audio.get_audio_backend() or 'None (uinput fallback)'}")

# Read VERSION file (C2-3)
VERSION = "1.0.0"
version_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "VERSION"))
if os.path.exists(version_path):
    try:
        with open(version_path, "r") as f:
            VERSION = f.read().strip()
    except Exception:
        pass

connected_clients = 0
last_input_time = time.time()
client_disconnected_during_media_time = 0.0

# B34: anti-tormenta del panel idle. Sin cooldown, un perfil corrupto hacia que el
# watchdog relanzara cada 5 s y apilara hasta 3 Firefox.
PANEL_RETRY_MIN_INTERVAL = 30.0
PANEL_RETRY_STREAK_INTERVAL = 120.0
PANEL_FAIL_STREAK_LIMIT = 3
_last_panel_attempt = 0.0
_panel_fail_streak = 0


async def check_and_launch_status_panel() -> bool:
    """T-132: Immediately launch status panel when TV desktop is empty and appliance idle panel is enabled.
    Preserves 45s safety delay ONLY if a client disconnected while media was actively playing."""
    import kiosk
    global _last_panel_attempt, _panel_fail_streak

    if os.getenv("APPLIANCE_IDLE_PANEL", "").lower() != "true":
        return False

    # B34: backoff anti-tormenta SOLO mientras haya fallos acumulados. Un panel que
    # acaba de abrirse no debe bloquear un relanzamiento legitimo (p. ej. stop_kiosk).
    if _panel_fail_streak > 0:
        retry_interval = (
            PANEL_RETRY_STREAK_INTERVAL
            if _panel_fail_streak >= PANEL_FAIL_STREAK_LIMIT
            else PANEL_RETRY_MIN_INTERVAL
        )
        if time.time() - _last_panel_attempt < retry_interval:
            return False

    if kiosk.is_status_panel_running():
        return False

    media_active = await asyncio.to_thread(kiosk.is_media_active)
    if media_active:
        return False

    # Check 45s safety delay if client disconnected during active playback
    global client_disconnected_during_media_time
    if connected_clients == 0 and client_disconnected_during_media_time > 0.0:
        elapsed = time.time() - client_disconnected_during_media_time
        if elapsed < 45.0:
            logger.debug(f"Media stopped but client disconnected during media; waiting safety delay ({elapsed:.1f}s / 45s)")
            return False

    port = os.getenv("PORT", "8000")
    # B30: cache-busting por arranque; Firefox reusaba el HTML viejo del panel.
    status_url = f"https://127.0.0.1:{port}/status?v={int(time.time())}"
    logger.info(f"Empty TV desktop detected -> launching status panel ({status_url})")
    success = await asyncio.to_thread(kiosk.launch_kiosk, status_url)
    if success:
        # D4: sin ventana de bloqueo tras un lanzamiento exitoso.
        _panel_fail_streak = 0
    else:
        _last_panel_attempt = time.time()
        _panel_fail_streak += 1
        if _panel_fail_streak == PANEL_FAIL_STREAK_LIMIT:
            logger.warning(
                f"Status panel launch failed {_panel_fail_streak} times in a row; "
                f"backing off {int(PANEL_RETRY_STREAK_INTERVAL)}s to avoid a kiosk restart storm."
            )
    return success


async def monitor_idle_panel():
    """T-132: Monitor TV state and show status panel when desktop is empty,
    preserving 45s safety delay ONLY if client disconnected during active media.

    T-156: mientras el panel esta en pantalla, cierra popups/ventanas de Firefox ajenas.
    """
    while True:
        await asyncio.sleep(5)
        try:
            import kiosk
            if kiosk.is_kiosk_running() and kiosk.is_status_panel_running():
                still_there = await asyncio.to_thread(kiosk.enforce_panel_window)
                if not still_there:
                    logger.info("Panel window disappeared; relaunching the status panel.")
                    await asyncio.to_thread(kiosk.kill_existing_kiosks)
            await check_and_launch_status_panel()
        except Exception as e:
            logger.debug(f"Error in monitor_idle_panel: {e}")


@app.on_event("startup")
async def startup_event():
    # T-132: Immediate OSD status launch on startup if idle panel enabled (< 3s)
    if os.getenv("APPLIANCE_IDLE_PANEL", "").lower() == "true":
        try:
            await check_and_launch_status_panel()
        except Exception as e:
            logger.warning(f"Failed to launch status panel on startup: {e}")
    asyncio.create_task(monitor_idle_panel())



# HYG-03 Constants organization
SUGGESTED_KIOSKS = [
    {"id": "netflix", "name": "Netflix", "url": "https://netflix.com", "color": "#E50914"},
    {"id": "youtube", "name": "YouTube", "url": "https://youtube.com", "color": "#FF0000"},
    {"id": "plutotv", "name": "Pluto TV", "url": "https://pluto.tv", "color": "#FAD000"},
    {"id": "kick", "name": "Kick", "url": "https://kick.com", "color": "#53FC18"},
    {"id": "tiktok", "name": "TikTok", "url": "https://www.tiktok.com", "color": "#FE2C55"},
    {"id": "instagram", "name": "Instagram", "url": "https://www.instagram.com", "color": "#E4405F"},
    {"id": "facebook", "name": "Facebook", "url": "https://www.facebook.com", "color": "#1877F2"},
    {"id": "hbomax", "name": "Max", "url": "https://play.max.com", "color": "#7B2BF9"},
    {"id": "primevideo", "name": "Prime Video", "url": "https://www.primevideo.com", "color": "#00A8E1"},
    {"id": "disney", "name": "Disney+", "url": "https://www.disneyplus.com", "color": "#113CCF"},
    {"id": "stremio", "name": "Stremio", "url": "https://web.stremio.com", "color": "#8a5a99"},
    {"id": "crunchyroll", "name": "Crunchyroll", "url": "https://www.crunchyroll.com", "color": "#F47521"},
    {"id": "appletv", "name": "Apple TV+", "url": "https://tv.apple.com", "color": "#555555"},
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
        client_host = client_host.replace("::ffff:", "")
    if client_host not in ["127.0.0.1", "localhost", "::1"]:
        logger.warning(f"Blocked non-local access attempt from {client_host}")
        raise HTTPException(status_code=403, detail="Forbidden. Local access only.")


def require_local_or_token(request: Request, x_auth_token: str = Header(default="")):
    client_host = request.client.host
    if client_host.startswith("::ffff:"):
        client_host = client_host.replace("::ffff:", "")
    if client_host in ["127.0.0.1", "localhost", "::1"]:
        return
    if verify_access(x_auth_token):
        return
    raise HTTPException(status_code=401, detail="Unauthorized")

# P1-1: PIN Manager
import hmac

class PinManager:
    def __init__(self):
        self.pin: str = None
        self.expires_at: float = 0.0
        self.failed_attempts: dict = {}  # ip -> {"count": int, "locked_until": float}
        self.global_failed: int = 0
        self.global_window_start: float = time.time()

    def generate_pin(self) -> str:
        import secrets
        # 6 random digits
        self.pin = "".join(str(secrets.randbelow(10)) for _ in range(6))
        self.expires_at = time.time() + 120.0
        self.global_failed = 0
        self.global_window_start = time.time()
        logger.info("Generated new 6-digit PIN for pairing.")
        return self.pin

    def get_valid_pin(self) -> tuple[str, float]:
        now = time.time()
        if not self.pin or now > self.expires_at:
            self.generate_pin()
        return self.pin, max(0.0, self.expires_at - time.time())

    def consume_pin(self):
        self.pin = None
        self.expires_at = 0.0

pin_manager = PinManager()

class PairPinBody(BaseModel):
    pin: str

@app.get("/api/pairing-pin")
def get_pairing_pin(request: Request):
    require_local(request)
    pin, expires_in = pin_manager.get_valid_pin()
    return {"pin": pin, "expires_in": int(expires_in)}

@app.post("/api/pair")
def pair_with_pin(body: PairPinBody, request: Request):
    # LAN-accessible, NO auth
    client_ip = request.client.host
    if client_ip.startswith("::ffff:"):
        client_ip = client_ip.replace("::ffff:", "")
    now = time.time()

    # Global brute-force guard (20 fails / minute)
    if now - pin_manager.global_window_start > 60:
        pin_manager.global_failed = 0
        pin_manager.global_window_start = now
    
    if pin_manager.global_failed >= 20:
        pin_manager.generate_pin() # Invalidates current PIN
        pin_manager.global_failed = 0
        raise HTTPException(status_code=429, detail="Global PIN rate limit exceeded. Check TV for new PIN.")

    # Per-IP guard (5 fails / 60s)
    ip_state = pin_manager.failed_attempts.get(client_ip, {"count": 0, "locked_until": 0.0})
    if now < ip_state["locked_until"]:
        raise HTTPException(status_code=429, detail="Demasiados intentos, espera un minuto")
    
    if not pin_manager.pin or now > pin_manager.expires_at:
        raise HTTPException(status_code=410, detail="El PIN expiró, en la TV aparecerá uno nuevo")

    if not hmac.compare_digest(pin_manager.pin, body.pin):
        pin_manager.global_failed += 1
        ip_state["count"] += 1
        if ip_state["count"] >= 5:
            ip_state["locked_until"] = now + 60.0
            ip_state["count"] = 0
        pin_manager.failed_attempts[client_ip] = ip_state
        raise HTTPException(status_code=401, detail="PIN incorrecto")

    # Success
    pin_manager.consume_pin()
    # Reset lockouts for this IP
    pin_manager.failed_attempts.pop(client_ip, None)
    return {"token": auth.PAIRING_TOKEN}


@app.get("/api/pairing-token")
@app.get("/api/token")
def get_pairing_token(request: Request):
    require_local(request)
    return {"token": auth.PAIRING_TOKEN}


@app.post("/api/pairing-token/regenerate")
@app.post("/api/token/regenerate")
async def regenerate_pairing_token(request: Request):
    require_local(request)
    import secrets
    new_token = secrets.token_urlsafe(16)
    token_path = get_token_file()
    try:
        token_path.parent.mkdir(parents=True, exist_ok=True)
        with open(token_path, "w") as f:
            f.write(new_token)
        secure_permissions(token_path)
        auth.PAIRING_TOKEN = new_token
        logger.info("Pairing token regenerated via local API.")
        await revoke_all_websockets(code=1008, reason="Token rotated")
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
        qr.save(out, kind='svg', scale=6, dark='#000000', light='#ffffff', border=4)
        svg_content = out.getvalue().decode('utf-8')
        # Inject viewBox if missing, so CSS can scale it properly
        if 'viewBox=' not in svg_content:
            import re
            match = re.search(r'width="(\d+)"\s+height="(\d+)"', svg_content)
            if match:
                w, h = match.groups()
                svg_content = svg_content.replace('<svg ', f'<svg viewBox="0 0 {w} {h}" ', 1)
        return Response(content=svg_content, media_type="image/svg+xml")
    except Exception as e:
        logger.error(f"Failed to generate pairing QR: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


def get_ips():
    """IPv4 de las interfaces reales, sin dependencias externas.

    psutil no forma parte del .deb y su ImportError dejaba la lista vacia
    siempre (la app mostraba 0 IPs). Se usa /sys/class/net + ioctl SIOCGIFADDR.
    """
    ips = []
    try:
        import fcntl
        import socket
        import struct

        ignored_prefixes = ("docker", "br-", "veth", "virbr", "tun", "tap")
        valid_ips = []
        tailscale_ips = []

        try:
            interfaces = sorted(os.listdir("/sys/class/net"))
        except OSError:
            interfaces = []

        for interface in interfaces:
            if interface == "lo" or any(interface.startswith(p) for p in ignored_prefixes):
                continue
            try:
                probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                # 0x8915 = SIOCGIFADDR
                packed = struct.pack("256s", interface[:15].encode("utf-8"))
                address = socket.inet_ntoa(
                    fcntl.ioctl(probe.fileno(), 0x8915, packed)[20:24]
                )
                probe.close()
            except OSError:
                continue
            if not address or address.startswith("127.") or address == "0.0.0.0":
                continue
            if interface.startswith("tailscale"):
                tailscale_ips.append((interface, address))
            else:
                valid_ips.append((interface, address))

        def sort_key(item):
            iface, ip = item
            score = 10
            preferred = ("wlan", "eth", "en", "wl")
            if any(iface.startswith(p) for p in preferred):
                score -= 5
            if ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172."):
                score -= 5
            return score

        valid_ips.sort(key=sort_key)

        if not valid_ips and tailscale_ips:
            valid_ips = tailscale_ips

        for iface, ip in valid_ips:
            ips.append(f"{iface}: {ip}")
    except Exception:
        pass
    return ips


@app.get("/api/status")
async def get_api_status(request: Request):
    require_local(request)
    import kiosk
    import input_emulator

    # T-150b: payload publico sin modo, licencia, voz ni checkout. El panel solo lee
    # estas claves; el resto de la superficie comercial ya no existe.
    return {
        "version": VERSION,
        "network_ips": get_ips(),
        "pairing_token": auth.PAIRING_TOKEN,
        "connected_clients": connected_clients,
        "last_input_timestamp": last_input_time,
        "uinput_ok": getattr(input_emulator.mouse, 'ui', None) is not None,
        "kiosk_active": getattr(kiosk, "_kiosk_proc", None) is not None,
        "adblock_status": kiosk.adblock_status(),
    }


@app.get("/status")
def get_status_html(request: Request):
    require_local(request)
    html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "status.html"))
    if os.path.exists(html_path):
        from fastapi.responses import FileResponse
        # B29: evita panel obsoleto tras deploy/upgrade (Firefox reusaba el HTML viejo).
        return FileResponse(html_path, headers={"Cache-Control": "no-store, must-revalidate"})
    raise HTTPException(status_code=404, detail="status.html missing")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/config")
def get_config():
    return {
        "hostname": socket.gethostname(),
        "version": VERSION,
    }


@app.get("/api/ca")
def get_ca():
    ca_path = str(get_ca_cert_file())
    if os.path.exists(ca_path):
        return FileResponse(ca_path, media_type="application/x-pem-file", filename="ca.pem")
    raise HTTPException(status_code=404, detail="CA certificate not found")


@app.get("/api/debug", dependencies=[Depends(require_token)])
def debug_info():
    import input_emulator
    return {
        "evdev_available": input_emulator.EVDEV_AVAILABLE,
        "is_ui_created": getattr(input_emulator.gamepad, 'ui', None) is not None,
        "mouse_ui_created": getattr(input_emulator.mouse, 'ui', None) is not None,
        "dropped_msgs_last_min": {
            "fast": global_dropped_fast,
            "slow": global_dropped_slow
        },
        "os": __import__('platform').system()
    }


@app.get("/api/apps", dependencies=[Depends(require_token)])
def list_apps():
    return {
        "type": "discovery_sync",
        "installed_apps": get_installed_apps(),
        "suggested_kiosks": SUGGESTED_KIOSKS
    }


@app.get("/api/icon/{app_id}")
async def get_app_icon(app_id: str):
    from fastapi.responses import FileResponse
    match = next((a for a in get_installed_apps() if a["id"] == app_id), None)
    if not match or not match.get("icon"):
        raise HTTPException(status_code=404, detail="Icon not found")
    
    icon_val = match["icon"]
    if icon_val.startswith("/"):
        if os.path.exists(icon_val):
            return FileResponse(icon_val)
    else:
        for ext in [".png", ".svg", ".xpm"]:
            p = f"/usr/share/pixmaps/{icon_val}{ext}"
            if os.path.exists(p): return FileResponse(p)
            for res in ["48x48", "64x64", "128x128", "256x256", "scalable"]:
                p2 = f"/usr/share/icons/hicolor/{res}/apps/{icon_val}{ext}"
                if os.path.exists(p2): return FileResponse(p2)
    raise HTTPException(status_code=404, detail="Icon not found on disk")


@app.post("/api/kiosk/launch", dependencies=[Depends(require_token)])
async def start_kiosk(payload: KioskLaunchBody):
    success = await asyncio.to_thread(launch_kiosk, payload.url)
    if success:
        return {"status": "success"}
    raise HTTPException(status_code=400, detail="Failed to launch kiosk")


@app.post("/api/kiosk/kill", dependencies=[Depends(require_token)])
async def stop_kiosk():
    import kiosk
    global last_input_time, client_disconnected_during_media_time
    last_input_time = time.time()
    client_disconnected_during_media_time = 0.0  # Deliberate user close; no disconnect delay
    await asyncio.to_thread(kiosk.close_all)
    if os.getenv("APPLIANCE_IDLE_PANEL", "").lower() == "true":
        asyncio.create_task(check_and_launch_status_panel())
    return {"status": "success"}


@app.post("/api/panel/show", dependencies=[Depends(require_local_or_token)])
async def show_panel():
    port = os.getenv("PORT", "8000")
    url = f"https://127.0.0.1:{port}/status"
    success = await asyncio.to_thread(launch_kiosk, url)
    if success:
        return {"status": "success"}
    raise HTTPException(status_code=400, detail="Failed to show panel")


@app.post("/api/app/launch", dependencies=[Depends(require_token)])
async def launch_native_app(payload: AppLaunchBody):
    app_id = payload.id
    match = next((a for a in get_installed_apps() if a["id"] == app_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="App not found")
    if not match.get("exec"):
        raise HTTPException(status_code=400, detail="App executable path missing")

    import shlex
    import kiosk
    cleaned = re.sub(r'%[a-zA-Z]', '', match["exec"]).strip()
    
    def _do_launch():
        proc = subprocess.Popen(shlex.split(cleaned), env=gui_env(), stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
        kiosk._native_procs.append(proc)
        
    try:
        await asyncio.to_thread(_do_launch)
        return {"status": "success"}
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = "guest"):
    await websocket.accept()

    # SEC-06 WS query param fallback and auth initialization
    auth_token = token
    is_authenticated = False

    global connected_clients, last_input_time
    if auth_token and auth_token != "guest":
        if await asyncio.to_thread(verify_access, auth_token):
            is_authenticated = True
            connected_clients += 1
            active_authenticated_websockets.add(websocket)

    fast_bucket = TokenBucket(rate=240.0, capacity=480.0)
    slow_bucket = TokenBucket(rate=30.0, capacity=60.0)
    auth_start = time.time()

    ws_send_lock = asyncio.Lock()

    async def safe_send_json(data):
        try:
            async with ws_send_lock:
                await websocket.send_text(json.dumps(data))
        except (RuntimeError, WebSocketDisconnect):
            logger.debug("Attempted to send text on closed WebSocket.")
        except Exception as e:
            logger.debug(f"Error sending on WebSocket: {e}")

    active_voice_tasks: set[asyncio.Task] = set()

    async def handle_voice_message(audio_data: bytes):
        try:
            await safe_send_json({"status": "processing", "message": "Listening..."})
            valid_targets = [k["id"] for k in SUGGESTED_KIOSKS]
            result = await voice_command(audio_data, valid_targets=valid_targets)

            if result.get("ok"):
                text = result.get("text", "")
                await safe_send_json({"status": "processing", "message": f"Intent: {text}"})
                intent = result.get("intent") or {"action": "error"}

                if intent.get("action") == "error":
                    await safe_send_json({"status": "error", "message": "Voz: error LLM"})
                    return

                action = intent.get("action")
                params = intent.get("parameters", {})

                if action == "launch_kiosk":
                    target = params.get("target_id")
                    if target:
                        target = str(target).lower().strip()
                        target_url = SUGGESTED_KIOSKS_MAP.get(target)
                        if target_url:
                            if target == "youtube":
                                query = quote_plus(params.get('search_query', ''))
                                target_url = f"https://youtube.com/results?search_query={query}"
                            success = await asyncio.to_thread(launch_kiosk, target_url)
                            if success:
                                await safe_send_json({"status": "success", "message": "Launched app"})
                            else:
                                await safe_send_json({"status": "error", "message": "Failed to launch app"})
                        else:
                            await safe_send_json({"status": "error", "message": f"Voz: app '{target}' no reconocida"})
                    else:
                        await safe_send_json({"status": "error", "message": "Target missing"})
                elif action == "media_control":
                    media_key = params.get("key")
                    if media_key:
                        media_key = str(media_key).upper().strip()
                        if not media_key.startswith("KEY_"):
                            media_key = f"KEY_{media_key}"
                            
                        if media_key in MEDIA_KEYS:
                            import audio
                            import kiosk
                            if media_key == "KEY_VOLUMEUP":
                                if not audio.set_volume(5): await gamepad.press_button(media_key)
                            elif media_key == "KEY_VOLUMEDOWN":
                                if not audio.set_volume(-5): await gamepad.press_button(media_key)
                            elif media_key == "KEY_MUTE":
                                if not audio.toggle_mute(): await gamepad.press_button(media_key)
                            elif media_key == "KEY_PLAYPAUSE" and getattr(kiosk, "_kiosk_proc", None) is not None:
                                await gamepad.press_button("KEY_SPACE")
                            else:
                                await gamepad.press_button(media_key)
                            await safe_send_json({"status": "success", "message": f"Media: {media_key}"})
                        else:
                            await safe_send_json({"status": "error", "message": "Invalid media key"})
                    else:
                        await safe_send_json({"status": "error", "message": "Invalid media key"})
                elif action == "search":
                    query = quote_plus(params.get("search_query", ""))
                    if query:
                        success = await asyncio.to_thread(launch_kiosk, f"https://www.youtube.com/results?search_query={query}")
                        if success:
                            await safe_send_json({"status": "success", "message": f"Searching: {params.get('search_query', '')}"})
                        else:
                            await safe_send_json({"status": "error", "message": "Failed to search"})
                    else:
                        await safe_send_json({"status": "error", "message": "Empty search"})
                elif action == "system_control":
                    cmd = params.get("command")
                    if cmd in ("toggle_osd", "open_settings"):
                        target_url = "https://127.0.0.1:8000/status"
                        if cmd == "open_settings":
                            target_url = "https://127.0.0.1:8000/status?tab=settings"
                        success = await asyncio.to_thread(launch_kiosk, target_url)
                        if success:
                            await safe_send_json({"status": "success", "message": f"System: {cmd}"})
                        else:
                            await safe_send_json({"status": "error", "message": "Failed system action"})
                    elif cmd == "close_kiosk":
                        import kiosk
                        await asyncio.to_thread(kiosk.close_kiosk)
                        await safe_send_json({"status": "success", "message": "Kiosk closed"})
                    else:
                        await safe_send_json({"status": "error", "message": "Unknown system command"})
                else:
                    await safe_send_json({"status": "error", "message": "Unknown action"})
            else:
                reason = result.get("reason", "error")
                # PH24: la voz corre local; no hay cuotas, licencias ni proxy que reportar.
                voice_errors = {
                    "empty_audio": "Voz: audio vacío",
                    "no_speech": "Voz: no se entendió el audio",
                    "audio_too_large": "Audio too large",
                    "stt_error": "Voz: error STT",
                    "llm_error": "Voz: error LLM",
                }
                await safe_send_json({"status": "error", "code": reason,
                                      "message": voice_errors.get(reason, "Voz: error del servicio")})
        except asyncio.CancelledError:
            logger.debug("Voice processing task cancelled.")
        except Exception as e:
            logger.error(f"Error in async voice processing task: {e}")

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
                global last_input_time
                last_input_time = time.time()

                if not voice_enabled():
                    await safe_send_json({"status": "error", "message": "Voice disabled"})
                    continue
                audio_data = message.get("bytes")
                logger.info(f"Received binary audio message: {len(audio_data)} bytes")
                if len(audio_data) > 512_000:
                    await safe_send_json({"status": "error", "message": "Audio too large"})
                    continue

                # ASTRA-03: Decouple voice processing from main WebSocket receive loop
                # into a background task per connection, preventing slow STT/LLM inference
                # from blocking concurrent ping/pong or heartbeats.
                v_task = asyncio.create_task(handle_voice_message(audio_data))
                active_voice_tasks.add(v_task)
                v_task.add_done_callback(active_voice_tasks.discard)

            elif message.get("text"):
                data = message.get("text")
                try:
                    payload = json.loads(data)
                except json.JSONDecodeError:
                    await safe_send_json({"status": "error", "message": "Invalid JSON format"})
                    continue

                msg_type = payload.get("type")

                # SEC-07 Rate limit checks
                if msg_type in ("pointer", "ping"):
                    if not fast_bucket.consume():
                        global global_dropped_fast
                        global_dropped_fast += 1
                        continue
                else:
                    if not slow_bucket.consume():
                        global global_dropped_slow
                        global_dropped_slow += 1
                        logger.warning("WS message dropped due to rate limit threshold.")
                        continue

                # SEC-06 auth frame
                if msg_type == "auth":
                    auth_token = payload.get("token")
                    if auth_token and await asyncio.to_thread(verify_access, auth_token):
                        if not is_authenticated:
                            is_authenticated = True
                            connected_clients += 1
                            active_authenticated_websockets.add(websocket)
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
                
                last_input_time = time.time()

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
                elif msg_type == "combo":
                    name = payload.get("name")
                    if name == "browser_back":
                        success = await mouse.click("back")
                        if not success:
                            await gamepad.press_combo(name)
                        await safe_send_json({"status": "received"})
                    elif name:
                        await gamepad.press_combo(name)
                        await safe_send_json({"status": "received"})
                    else:
                        await safe_send_json({"status": "error", "message": "Combo name missing"})
                elif payload.get("action") == "media_control":
                    media_key = payload.get("parameters", {}).get("key")
                    if media_key in MEDIA_KEYS:
                        import audio
                        import kiosk
                        if media_key == "KEY_VOLUMEUP":
                            if not audio.set_volume(5): await gamepad.press_button(media_key)
                        elif media_key == "KEY_VOLUMEDOWN":
                            if not audio.set_volume(-5): await gamepad.press_button(media_key)
                        elif media_key == "KEY_MUTE":
                            if not audio.toggle_mute(): await gamepad.press_button(media_key)
                        elif media_key == "KEY_PLAYPAUSE" and getattr(kiosk, "_kiosk_proc", None) is not None:
                            await gamepad.press_button("KEY_SPACE")
                        else:
                            await gamepad.press_button(media_key)
                        await safe_send_json({"status": "received"})
                    else:
                        await safe_send_json({"status": "error", "message": "Disallowed key"})
                else:
                    # COR-10 unknown messages
                    await safe_send_json({"status": "error", "message": f"unknown_type: {msg_type}"})

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    finally:
        for v_task in list(active_voice_tasks):
            if not v_task.done():
                v_task.cancel()
        active_voice_tasks.clear()
        active_authenticated_websockets.discard(websocket)
        if is_authenticated:
            connected_clients = max(0, connected_clients - 1)
            try:
                import kiosk
                if kiosk.is_media_active():
                    global client_disconnected_during_media_time
                    client_disconnected_during_media_time = time.time()
                    logger.info("Client disconnected during active media; armed 45s safety delay.")
            except Exception as e:
                logger.debug(f"Error checking active media on disconnect: {e}")

frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")
