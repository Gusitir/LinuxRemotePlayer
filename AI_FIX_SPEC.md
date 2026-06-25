# AI_FIX_SPEC — LinuxRemotePlayer Audit Remediation

```yaml
meta:
  doc_type: machine_executable_fix_spec
  audience: LLM_CODE_AGENT (Gemini)
  human_readable: false
  repo_root: "Proyecto WebApp - LinuxRemotePlayer"
  language_stack: [python3.10+, fastapi, vanilla_js, bash]
  generated_by: audit
  date: 2026-06-24
  apply_order: strict_top_to_bottom
  total_tasks: 16
```

## 0. AGENT_INSTRUCTIONS

```
ROLE: You are a code-fixing agent. Apply every TASK below to the repository.
GOAL: Resolve audit findings (security, blocker, correctness, completeness).

RULES:
- R1. Apply tasks in PRIORITY order: P0 first, then P1, then P2, then P3.
- R2. Each TASK is atomic and self-contained. Apply fully or skip; never half-apply.
- R3. For TYPE=replace: locate FIND verbatim, substitute with REPLACE.
- R4. For TYPE=append: add REPLACE block at END of FILE.
- R5. For TYPE=insert_after: locate ANCHOR verbatim, insert REPLACE immediately after it.
- R6. MATCH_RULE: FIND/ANCHOR must match exactly (chars, indentation, order).
      If the only difference is trailing whitespace or blank-line spacing,
      apply the change described in INTENT at the same location. Never guess
      beyond INTENT.
- R7. Python indentation = 4 spaces, NO tabs. Preserve surrounding indentation.
- R8. Do NOT reformat, re-order, or touch code outside the FIND/REPLACE region.
- R9. Do NOT invent new files except where TASK TYPE=create_file.
- R10. After ALL tasks: run section VERIFICATION. Every check must pass.
- R11. If a FIND cannot be located AND INTENT is ambiguous, STOP and emit:
       "BLOCKED: <task_id> <reason>". Do not continue to next task blindly
       unless the next task is independent (independence noted per task).
- R12. Some tasks add a runtime dependency on an env var or DB column.
       These are listed in SCHEMA_AND_ENV. Apply those too.
```

## 1. PROJECT_MAP

```
backend/main.py            FastAPI entry: REST + WebSocket router + static mount
backend/input_emulator.py  evdev/UInput virtual keyboard-gamepad
backend/ai_pipeline.py     STT (NVIDIA NIM / local Whisper) + LLM intent parse
backend/auth.py            Supabase license check + rate limit
backend/discovery.py       parse /usr/share/applications/*.desktop
backend/kiosk.py           launch browser in --kiosk
backend/requirements.txt   python deps (unpinned)
backend/.env.example       env template
frontend/index.html        PWA shell (Tailwind CDN)
frontend/app.js            WS client + MediaRecorder + REST calls
scripts/install.sh         systemd installer (appliance/desktop)
```

## 2. FINDINGS_INDEX (audit -> task)

```
F1  P0 BLOCKER   evdev fails: /dev/uinput perms not set by installer -> T1
F2  P0 SECURITY  WS control path + kiosk REST have NO auth (LAN takeover) -> T2,T3,T4,T5,T6
F3  P0 SECURITY  CORS allow_credentials=True reflects any origin -> T7
F4  P1 SECURITY  kiosk URL built from raw LLM target_id (injection) -> T8
F5  P1 FEATURE   media_control parsed but does nothing -> T9,T10
F6  P1 LOGIC     rate limit never resets daily (lifetime cap, not /day) -> T11
F7  P2 ROBUST    audio blob size unbounded (DoS) -> T12
F8  P2 PORTABLE  frontend hardcodes :8000, ignores location.port -> T13
F9  P2 CONFIG    NVIDIA ASR model hardcoded + name unverified -> T14
F10 P2 REPRO     requirements.txt unpinned -> T15
F11 P3 FEATURE   native apps discovered but not launchable (exec unused) -> T16
```

---

# 3. TASKS

## P0 — BLOCKER + SECURITY (apply first)

### TASK T1
```
id: T1
priority: P0
file: scripts/install.sh
type: insert_after
intent: Grant /dev/uinput access so evdev UInput stops failing (Phase 6 blocker).
        Load uinput module on boot, add udev rule, add user to 'input' group.
independent: true
```
ANCHOR:
```bash
apt-get install -y python3-venv python3-dev ufw
```
INSERT_AFTER (place these lines immediately below the anchor):
```bash

# --- evdev / uinput permissions (FIX F1: Phase 6 blocker) ---
modprobe uinput || true
echo uinput > /etc/modules-load.d/uinput.conf
echo 'KERNEL=="uinput", MODE="0660", GROUP="input", OPTIONS+="static_node=uinput"' > /etc/udev/rules.d/99-uinput.rules
usermod -aG input "$SUDO_USER"
udevadm control --reload-rules && udevadm trigger
echo "[i] Added '$SUDO_USER' to 'input' group. REBOOT or re-login required before uinput works."
```
POST_CONDITION: After reboot, `id $USER` lists group `input`; `ls -l /dev/uinput` shows group `input` mode `crw-rw----`.

---

### TASK T2
```
id: T2
priority: P0
file: backend/auth.py
type: append
intent: Add access-control helper (no counter increment) + optional offline pairing
        token. Used to gate WebSocket and kiosk REST endpoints.
independent: false (required by T4,T5,T6)
```
APPEND (add at end of file):
```python


PAIRING_TOKEN = os.getenv("PAIRING_TOKEN")


def verify_access(token: str) -> bool:
    """Access gate WITHOUT incrementing usage. Returns True if token may control host.
    Modes:
    - Supabase configured: token must exist in 'licenses' table.
    - Supabase off + PAIRING_TOKEN set: token must equal PAIRING_TOKEN.
    - Supabase off + no PAIRING_TOKEN: dev mode -> allow with warning.
    """
    if not token:
        return False
    if not supabase:
        if PAIRING_TOKEN:
            return token == PAIRING_TOKEN
        print("Warning: No Supabase and no PAIRING_TOKEN. Access control DISABLED (dev mode).")
        return True
    try:
        res = supabase.table('licenses').select('token').eq('token', token).execute()
        return bool(res.data)
    except Exception as e:
        print(f"Access check error: {e}")
        return False
```
POST_CONDITION: `from auth import verify_access` imports without error.

---

### TASK T3
```
id: T3
priority: P0
file: backend/main.py
type: replace
intent: Extend FastAPI import to include Header, Depends, HTTPException (needed for auth dep).
independent: false
```
FIND:
```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
```
REPLACE:
```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Header, Depends, HTTPException
```

---

### TASK T4
```
id: T4
priority: P0
file: backend/main.py
type: replace
intent: Import verify_access alongside existing auth import.
independent: false
```
FIND:
```python
from auth import validate_license_and_increment
```
REPLACE:
```python
from auth import validate_license_and_increment, verify_access
```

---

### TASK T5
```
id: T5
priority: P0
file: backend/main.py
type: replace
intent: Add stdlib imports needed by later tasks (re, subprocess, quote_plus).
independent: false
```
FIND:
```python
import json
```
REPLACE:
```python
import json
import re
import subprocess
from urllib.parse import quote_plus
```
NOTE: `re`,`subprocess`,`quote_plus` are consumed by T8 and T16. Importing now is harmless if T16 skipped.

---

### TASK T6
```
id: T6
priority: P0
file: backend/main.py
type: replace
intent: (a) Define require_token dependency. (b) Gate /api/kiosk/launch with it.
independent: false (depends on T2,T3,T4)
```
FIND:
```python
@app.post("/api/kiosk/launch")
async def start_kiosk(payload: dict):
```
REPLACE:
```python
def require_token(x_auth_token: str = Header(default="")):
    if not verify_access(x_auth_token):
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.post("/api/kiosk/launch", dependencies=[Depends(require_token)])
async def start_kiosk(payload: dict):
```

---

### TASK T6b
```
id: T6b
priority: P0
file: backend/main.py
type: replace
intent: Gate /api/kiosk/kill with require_token.
independent: false (depends on T6)
```
FIND:
```python
@app.post("/api/kiosk/kill")
```
REPLACE:
```python
@app.post("/api/kiosk/kill", dependencies=[Depends(require_token)])
```

---

### TASK T6c
```
id: T6c
priority: P0
file: backend/main.py
type: replace
intent: Reject unauthorized WebSocket connections (control + audio channel).
independent: false (depends on T2,T4)
```
FIND:
```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = "guest"):
    await websocket.accept()
    try:
```
REPLACE:
```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = "guest"):
    await websocket.accept()
    if not await asyncio.to_thread(verify_access, token):
        await websocket.send_text(json.dumps({"status": "error", "message": "Unauthorized"}))
        await websocket.close(code=1008)
        return
    try:
```

---

### TASK T7
```
id: T7
priority: P0
file: backend/main.py
type: replace
intent: FIX F3. allow_credentials=True with allow_origins=["*"] makes Starlette
        reflect ANY origin with credentials. App uses no cookies; disable credentials.
independent: true
```
FIND:
```python
    allow_credentials=True,
```
REPLACE:
```python
    allow_credentials=False,
```

---

## P1 — SECURITY + FEATURE + LOGIC

### TASK T8
```
id: T8
priority: P1
file: backend/main.py
type: replace
intent: FIX F4 + F5(part). Sanitize LLM-provided target_id before building URL;
        URL-encode search query; implement media_control to inject media keys.
independent: false (needs T5 imports; needs T9 evdev caps for media keys to register)
```
FIND:
```python
                    if action == "launch_kiosk":
                        target = params.get("target_id")
                        if target:
                            url = f"https://{target}.com"
                            if target == "youtube":
                                url = f"https://youtube.com/results?search_query={params.get('search_query', '')}"
                            launch_kiosk(url)
                            await websocket.send_text(json.dumps({"status": "success", "message": "Launched app"}))
                    elif action == "media_control":
                        print(f"Media control requested: {params}")
```
REPLACE:
```python
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
```

---

### TASK T9
```
id: T9
priority: P1
file: backend/input_emulator.py
type: replace
intent: FIX F5. Register media keys (volume up/down/mute) in UInput capabilities
        so media_control injection from T8 is accepted by the kernel device.
independent: true
```
FIND:
```python
        keys = list(range(1, 100)) + [e.BTN_A, e.BTN_B, e.BTN_X, e.BTN_Y, e.BTN_START, e.BTN_SELECT, e.BTN_DPAD_UP, e.BTN_DPAD_DOWN, e.BTN_DPAD_LEFT, e.BTN_DPAD_RIGHT, e.KEY_UP, e.KEY_DOWN, e.KEY_LEFT, e.KEY_RIGHT, e.KEY_ENTER, e.KEY_ESC, e.KEY_BACKSPACE, e.KEY_PLAYPAUSE]
```
REPLACE:
```python
        keys = list(range(1, 100)) + [e.BTN_A, e.BTN_B, e.BTN_X, e.BTN_Y, e.BTN_START, e.BTN_SELECT, e.BTN_DPAD_UP, e.BTN_DPAD_DOWN, e.BTN_DPAD_LEFT, e.BTN_DPAD_RIGHT, e.KEY_UP, e.KEY_DOWN, e.KEY_LEFT, e.KEY_RIGHT, e.KEY_ENTER, e.KEY_ESC, e.KEY_BACKSPACE, e.KEY_PLAYPAUSE, e.KEY_VOLUMEUP, e.KEY_VOLUMEDOWN, e.KEY_MUTE, e.KEY_NEXTSONG, e.KEY_PREVIOUSSONG]
```

---

### TASK T10
```
id: T10
priority: P1
file: frontend/index.html
type: replace
intent: Expose media controls in PWA (volume down / mute / volume up) wired to
        the now-functional media_control path. Sends WS input with media key codes.
independent: true
note: sendKey() already emits {type:input,device:gamepad,...}. Backend T8 routes
      KEY_VOLUME* via media path only if action=media_control. To keep one code path,
      these buttons call sendMedia(); add sendMedia() in T10b.
```
FIND:
```html
            <div class="flex flex-col gap-4">
                <button onclick="sendKey('KEY_ESC')" class="bg-red-600 w-16 h-16 rounded-full active:bg-red-400 font-bold">Back</button>
            </div>
```
REPLACE:
```html
            <div class="flex flex-col gap-2">
                <button onclick="sendKey('KEY_ESC')" class="bg-red-600 w-16 h-16 rounded-full active:bg-red-400 font-bold">Back</button>
                <div class="flex gap-2">
                    <button onclick="sendMedia('KEY_VOLUMEDOWN')" class="bg-gray-700 w-12 h-10 rounded-lg active:bg-gray-500 font-bold">V-</button>
                    <button onclick="sendMedia('KEY_MUTE')" class="bg-gray-700 w-12 h-10 rounded-lg active:bg-gray-500 font-bold">M</button>
                    <button onclick="sendMedia('KEY_VOLUMEUP')" class="bg-gray-700 w-12 h-10 rounded-lg active:bg-gray-500 font-bold">V+</button>
                </div>
            </div>
```

---

### TASK T10b
```
id: T10b
priority: P1
file: frontend/app.js
type: insert_after
intent: Add sendMedia() helper that emits a media_control WS message.
independent: false (pairs with T10, T8)
```
ANCHOR:
```javascript
function sendKey(btnCode) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        const payload = {
            type: "input",
            device: "gamepad",
            action: "press",
            key: btnCode
        };
        ws.send(JSON.stringify(payload));
        if (navigator.vibrate) navigator.vibrate(50);
    }
}
```
INSERT_AFTER:
```javascript

function sendMedia(mediaKey) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        const payload = { action: "media_control", parameters: { key: mediaKey } };
        ws.send(JSON.stringify(payload));
        if (navigator.vibrate) navigator.vibrate(30);
    }
}
```
WARNING_FOR_AGENT: The current WS text handler in backend/main.py only routes
text payloads where `payload.get("type") == "input"`. The media_control action is
handled ONLY inside the AUDIO branch (after STT). To make sendMedia() work over the
TEXT channel, ALSO apply TASK T10c.

---

### TASK T10c
```
id: T10c
priority: P1
file: backend/main.py
type: replace
intent: Route text-channel media_control messages to evdev (so PWA media buttons work
        without voice). Adds an elif to the text-message handler.
independent: false (pairs with T10b)
```
FIND:
```python
                if payload.get("type") == "input" and payload.get("device") == "gamepad":
                    action = payload.get("action")
                    key = payload.get("key")
                    if action == "press" and key:
                        await gamepad.press_button(key)
```
REPLACE:
```python
                if payload.get("type") == "input" and payload.get("device") == "gamepad":
                    action = payload.get("action")
                    key = payload.get("key")
                    if action == "press" and key:
                        await gamepad.press_button(key)
                elif payload.get("action") == "media_control":
                    media_key = payload.get("parameters", {}).get("key")
                    allowed_media = {"KEY_VOLUMEUP", "KEY_VOLUMEDOWN", "KEY_MUTE", "KEY_PLAYPAUSE", "KEY_NEXTSONG", "KEY_PREVIOUSSONG"}
                    if media_key in allowed_media:
                        await gamepad.press_button(media_key)
```

---

### TASK T11
```
id: T11
priority: P1
file: backend/auth.py
type: replace (2 sub-edits T11a + T11b)
intent: FIX F6. Make the 60-commands limit reset PER DAY (currently never resets).
        Requires DB column 'last_reset' (see SCHEMA_AND_ENV).
independent: true
```
T11a FIND:
```python
        res = supabase.table('licenses').select('commands_today').eq('token', token).execute()
```
T11a REPLACE:
```python
        res = supabase.table('licenses').select('commands_today, last_reset').eq('token', token).execute()
```

T11b FIND:
```python
        commands = res.data[0].get('commands_today', 0)
```
T11b REPLACE:
```python
        from datetime import date
        today = date.today().isoformat()
        row = res.data[0]
        commands = row.get('commands_today', 0) or 0
        if row.get('last_reset') != today:
            commands = 0
            supabase.table('licenses').update({'commands_today': 0, 'last_reset': today}).eq('token', token).execute()
```
POST_CONDITION: counter logic still reads `if commands >= 60:` after this block; do not remove that line.

---

## P2 — ROBUSTNESS / PORTABILITY / CONFIG

### TASK T12
```
id: T12
priority: P2
file: backend/main.py
type: replace
intent: FIX F7. Reject oversized audio blobs (>5MB) before processing.
independent: true
```
FIND:
```python
                audio_data = message.get("bytes")
```
REPLACE:
```python
                audio_data = message.get("bytes")
                if len(audio_data) > 5_000_000:
                    await websocket.send_text(json.dumps({"status": "error", "message": "Audio too large"}))
                    continue
```

---

### TASK T13
```
id: T13
priority: P2
file: frontend/app.js
type: replace
intent: FIX F8. Derive port from window.location.port (fallback 8000) instead of
        hardcoding :8000, so non-8000 deployments work.
independent: true
```
FIND:
```javascript
const host = window.location.hostname === '' || window.location.hostname === 'localhost' ? '127.0.0.1' : window.location.hostname;
const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
const token = localStorage.getItem('license_token') || 'guest';
const wsUrl = `${protocol}${host}:8000/ws?token=${token}`;
const apiUrl = `${window.location.protocol}//${host}:8000/api`;
```
REPLACE:
```javascript
const host = window.location.hostname === '' || window.location.hostname === 'localhost' ? '127.0.0.1' : window.location.hostname;
const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
const token = localStorage.getItem('license_token') || 'guest';
const port = window.location.port || '8000';
const wsUrl = `${protocol}${host}:${port}/ws?token=${token}`;
const apiUrl = `${window.location.protocol}//${host}:${port}/api`;
```

---

### TASK T14
```
id: T14
priority: P2
file: backend/ai_pipeline.py
type: replace
intent: FIX F9. Make NVIDIA ASR model name configurable via env (the hardcoded
        'nvidia/nemotron-3.5-asr' is UNVERIFIED and may not exist on NVIDIA NIM).
independent: true
```
FIND:
```python
            data = {'model': 'nvidia/nemotron-3.5-asr'}
```
REPLACE:
```python
            data = {'model': os.getenv("NVIDIA_ASR_MODEL", "nvidia/nemotron-3.5-asr")}
```
ACTION_REQUIRED_BY_HUMAN: Verify the real model id in NVIDIA NIM ASR catalog and set
NVIDIA_ASR_MODEL in .env. Known-plausible alternatives: parakeet / canary family.

---

### TASK T15
```
id: T15
priority: P2
file: backend/requirements.txt
type: replace
intent: FIX F10. Pin dependency ranges for reproducible installs.
independent: true
```
FIND:
```
fastapi
uvicorn[standard]
evdev
python-dotenv
supabase
httpx
```
REPLACE:
```
fastapi>=0.110,<1.0
uvicorn[standard]>=0.27,<1.0
evdev>=1.6,<2.0
python-dotenv>=1.0,<2.0
supabase>=2.4,<3.0
httpx>=0.26,<1.0
```

---

## P3 — OPTIONAL FEATURE (apply only if all P0–P2 pass)

### TASK T16
```
id: T16
priority: P3
file: backend/main.py
type: insert_after
intent: FIX F11. Native apps are discovered but cannot be launched (Exec unused).
        Add gated /api/app/launch that runs the .desktop Exec safely (strip %-field
        codes, shlex split, no shell). Requires T5 (re, subprocess) + T6 (require_token).
independent: false
skip_if_uncertain: true
```
ANCHOR:
```python
    kill_existing_kiosks()
    return {"status": "success"}
```
INSERT_AFTER:
```python


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
        subprocess.Popen(shlex.split(cleaned), stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
        return {"status": "success"}
    except Exception as ex:
        return {"status": "error", "message": str(ex)}
```

### TASK T16b
```
id: T16b
priority: P3
file: frontend/app.js
type: replace
intent: Make native app tiles clickable -> call /api/app/launch; remove opacity-50.
independent: false (pairs with T16)
```
FIND:
```javascript
        appsGrid.innerHTML = (data.installed_apps || []).slice(0, 12).map(app => `
            <div class="bg-gray-800 p-4 rounded-xl flex flex-col items-center justify-center cursor-pointer active:scale-95 transition-transform opacity-50 border border-gray-700">
                <div class="w-10 h-10 bg-gray-600 rounded-lg mb-2"></div>
                <span class="text-xs text-center truncate w-full">${app.name}</span>
            </div>
        `).join('');
```
REPLACE:
```javascript
        appsGrid.innerHTML = (data.installed_apps || []).slice(0, 12).map(app => `
            <div onclick="launchApp('${app.id}')" class="bg-gray-800 p-4 rounded-xl flex flex-col items-center justify-center cursor-pointer active:scale-95 transition-transform border border-gray-700">
                <div class="w-10 h-10 bg-gray-600 rounded-lg mb-2"></div>
                <span class="text-xs text-center truncate w-full">${app.name}</span>
            </div>
        `).join('');
```

### TASK T16c
```
id: T16c
priority: P3
file: frontend/app.js
type: insert_after
intent: Add launchApp() helper (sends auth header).
independent: false (pairs with T16)
```
ANCHOR:
```javascript
async function killKiosk() {
    if (navigator.vibrate) navigator.vibrate([50, 50, 50]);
    try {
        const res = await fetch(`${apiUrl}/kiosk/kill`, { method: 'POST' });
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    } catch (e) {
        console.error("Kill Error:", e);
    }
}
```
INSERT_AFTER:
```javascript

async function launchApp(id) {
    if (navigator.vibrate) navigator.vibrate(100);
    try {
        const res = await fetch(`${apiUrl}/app/launch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-Auth-Token': token },
            body: JSON.stringify({ id })
        });
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    } catch (e) {
        console.error("App launch error:", e);
    }
}
```

---

## P0 FRONTEND — auth header on gated REST (apply with P0 block)

### TASK T17
```
id: T17
priority: P0
file: frontend/app.js
type: replace
intent: After T6/T6b gate kiosk endpoints, frontend MUST send X-Auth-Token or it
        gets 401. Add header to launchKiosk fetch.
independent: false (depends on T6)
```
FIND:
```javascript
        const res = await fetch(`${apiUrl}/kiosk/launch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });
```
REPLACE:
```javascript
        const res = await fetch(`${apiUrl}/kiosk/launch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-Auth-Token': token },
            body: JSON.stringify({ url })
        });
```

### TASK T17b
```
id: T17b
priority: P0
file: frontend/app.js
type: replace
intent: Add X-Auth-Token header to killKiosk fetch.
independent: false (depends on T6b)
```
FIND:
```javascript
        const res = await fetch(`${apiUrl}/kiosk/kill`, { method: 'POST' });
```
REPLACE:
```javascript
        const res = await fetch(`${apiUrl}/kiosk/kill`, { method: 'POST', headers: { 'X-Auth-Token': token } });
```

---

## P0 ENV — pairing/config template

### TASK T18
```
id: T18
priority: P0
file: backend/.env.example
type: append
intent: Document new env vars introduced by T2 (PAIRING_TOKEN) and T14 (NVIDIA_ASR_MODEL).
independent: true
```
APPEND:
```
# Access control (Auditoria): shared pairing token used when Supabase is OFF.
# If empty AND Supabase off -> control endpoints are UNAUTHENTICATED (dev only).
PAIRING_TOKEN=
# STT model id override. VERIFY real NVIDIA NIM ASR model name before production.
NVIDIA_ASR_MODEL=nvidia/nemotron-3.5-asr
```

---

# 4. SCHEMA_AND_ENV (out-of-code requirements)

```
DB_SUPABASE:
  table: licenses
  add_column:
    name: last_reset
    type: text        # ISO date 'YYYY-MM-DD'; nullable; default NULL
  reason: required by T11 daily-reset logic.
  sql: |
    alter table licenses add column if not exists last_reset text;

ENV (.env, runtime):
  PAIRING_TOKEN:    set to a random secret on each install (recommended even with Supabase off)
  NVIDIA_ASR_MODEL: set to verified model id
```

---

# 5. VERIFICATION (run after applying; all must pass)

```
V1 SYNTAX_PY:
   python -m py_compile backend/main.py backend/auth.py backend/ai_pipeline.py backend/input_emulator.py
   EXPECT: exit 0

V2 IMPORT:
   cd backend && python -c "import main"
   EXPECT: no traceback (mock warnings about missing keys are OK)

V3 BOOT:
   cd backend && uvicorn main:app --host 127.0.0.1 --port 8000 &
   curl -s http://127.0.0.1:8000/health
   EXPECT: {"status":"ok"}

V4 AUTH_REST (must 401 without token when PAIRING_TOKEN set / Supabase on):
   curl -s -o /dev/null -w "%{http_code}" -X POST http://127.0.0.1:8000/api/kiosk/kill
   EXPECT: 401  (in pure dev mode with no Supabase and no PAIRING_TOKEN -> 200 is acceptable)

V5 CORS:
   grep -n "allow_credentials=False" backend/main.py
   EXPECT: 1 match

V6 UINPUT_INSTALLER:
   grep -n "99-uinput.rules" scripts/install.sh
   EXPECT: 1 match

V7 NO_UNVERIFIED_HARDCODE:
   grep -n "os.getenv(\"NVIDIA_ASR_MODEL\"" backend/ai_pipeline.py
   EXPECT: 1 match

V8 JS_SANITY:
   node --check frontend/app.js
   EXPECT: exit 0
```

---

# 6. DONE_CRITERIA

```
- All P0 + P1 + P2 tasks applied.
- V1..V8 pass.
- P3 (T16*) applied only if confident; else report "P3 SKIPPED".
- Emit final report:
    APPLIED: [list task ids]
    SKIPPED: [list + reason]
    SCHEMA_TODO: last_reset column, env vars set y/n
    VERIFICATION: V1..V8 pass/fail
- DO NOT commit/push unless instructed. Leave working tree modified for human review.
```
```
END_OF_SPEC
```
