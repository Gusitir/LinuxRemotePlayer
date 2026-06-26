# AI_TASK — Remote UI Redesign (touchpad, media, keyboard)

```yaml
meta:
  doc_type: machine_executable_task_spec
  audience: LLM_CODE_AGENT (Gemini)
  human_readable: false
  repo_root: "Proyecto WebApp - LinuxRemotePlayer"
  reviewer: auditor will verify after you finish
  apply_order: strict_top_to_bottom
```

## 0. AGENT_INSTRUCTIONS

```
ROLE: Apply the tasks below to the repository, exactly.

HARD RULES:
- R1. Write COMPLETE files. Never truncate. If a file is given in full (TYPE=write_full),
      its final content MUST be byte-for-byte what is shown between the BEGIN/END markers.
- R2. For TYPE=edit, locate FIND verbatim and replace with REPLACE. FIND must match exactly
      (indentation included). If a FIND is not found, STOP and report "BLOCKED <id>".
- R3. Do NOT modify any file not listed in TASKS. In particular DO NOT touch
      backend/input_emulator.py — it is already implemented (its interface is in section 2).
- R4. Python = 4-space indent, no tabs. Keep existing behavior unless a task changes it.
- R5. After applying everything, run section VERIFICATION. Every check must pass.
- R6. Do NOT git commit or push. Leave the working tree for human review.
- R7. Output a final report: APPLIED / SKIPPED / VERIFICATION results.
```

## 1. SCOPE

```
Goal: replace the remote UI with: media app row (+ "more"), a touchpad that drives a
mouse pointer, mic button, Home/Back, D-pad+OK, volume +/- , mute, media transport
(prev/playpause/next), and a system-keyboard bridge with a Done button.

Files to change:
  backend/main.py          -> 3 edits (TYPE=edit)
  frontend/index.html      -> full rewrite (TYPE=write_full)
  frontend/app.js          -> full rewrite (TYPE=write_full)
  frontend/sw.js           -> 1 edit (cache bump)

Already done (DO NOT TOUCH):
  backend/input_emulator.py  (virtual keyboard + virtual mouse + text typing)
```

## 2. BACKEND CONTRACT (already implemented in input_emulator.py)

```
input_emulator.gamepad.press_button(key_name: str)   # e.g. "KEY_UP", "KEY_PLAYPAUSE"
input_emulator.gamepad.type_text(text: str)          # types arbitrary text via evdev
input_emulator.mouse.move(dx: int, dy: int)          # relative pointer move
input_emulator.mouse.click(button="left"|"right")    # mouse click
Both are async. They no-op with a [Mock] print when evdev is unavailable.
```

WebSocket JSON message protocol (frontend -> backend, text frames):

```
{"type":"input","device":"gamepad","action":"press","key":"KEY_UP"}   -> key press
{"type":"pointer","dx":7,"dy":-3}                                       -> mouse move
{"type":"pointer","click":"left"}                                       -> mouse click
{"type":"text","text":"hello"}                                          -> type text
{"action":"media_control","parameters":{"key":"KEY_PLAYPAUSE"}}         -> media key
```

---

# 3. TASKS

## TASK B1 — backend/main.py : import the mouse
```
type: edit
file: backend/main.py
```
FIND:
```python
from input_emulator import gamepad
```
REPLACE:
```python
from input_emulator import gamepad, mouse
```

## TASK B2 — backend/main.py : expand the media app list
```
type: edit
file: backend/main.py
```
FIND:
```python
        "suggested_kiosks": [
            {"id": "netflix", "name": "Netflix", "url": "https://netflix.com", "icon": "netflix"},
            {"id": "youtube", "name": "YouTube", "url": "https://youtube.com/tv", "icon": "youtube"},
            {"id": "twitch", "name": "Twitch", "url": "https://twitch.tv", "icon": "twitch"}
        ]
```
REPLACE:
```python
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
```

## TASK B3 — backend/main.py : new WebSocket text dispatcher
```
type: edit
file: backend/main.py
note: adds pointer + text handling, expands media keys, stops echoing the full payload.
```
FIND:
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

                await websocket.send_text(json.dumps({"status": "received", "payload": payload}))
```
REPLACE:
```python
                msg_type = payload.get("type")
                if msg_type == "input" and payload.get("device") == "gamepad":
                    action = payload.get("action")
                    key = payload.get("key")
                    if action == "press" and key:
                        await gamepad.press_button(key)
                    await websocket.send_text(json.dumps({"status": "received"}))
                elif msg_type == "pointer":
                    click = payload.get("click")
                    if click:
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
```

---

## TASK F1 — frontend/index.html : full rewrite
```
type: write_full
file: frontend/index.html
```
BEGIN_FILE frontend/index.html
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, minimum-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>Remote Player</title>
    <link rel="manifest" href="manifest.json">
    <meta name="theme-color" content="#1f2937">
    <link rel="apple-touch-icon" href="icon.svg">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="Remote Kiosk">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
      html, body { touch-action: manipulation; overscroll-behavior: none; }
      body { -webkit-touch-callout: none; }
      button { touch-action: manipulation; -webkit-tap-highlight-color: transparent; }
      .util-btn { background:#374151; border-radius:0.6rem; padding:0.55rem 0; font-size:1.15rem; }
      .util-btn:active { background:#4b5563; }
      .ctrl-round { width:3rem; height:3rem; border-radius:9999px; background:#374151; display:flex; align-items:center; justify-content:center; font-size:1.1rem; }
      .ctrl-round:active { background:#4b5563; }
      .dpad { background:#374151; border-radius:0.6rem; display:flex; align-items:center; justify-content:center; font-size:1rem; }
      .dpad:active { background:#4b5563; }
      .dpad-ok { background:#2563eb; border-radius:9999px; display:flex; align-items:center; justify-content:center; font-weight:bold; }
      .dpad-ok:active { background:#3b82f6; }
      #touchpad { background-image: radial-gradient(rgba(255,255,255,0.10) 1px, transparent 1px); background-size: 12px 12px; touch-action: none; }
    </style>
</head>
<body class="bg-gray-900 text-white flex flex-col h-screen select-none">

    <!-- Browser tab: install tutorial -->
    <div id="install-ui" hidden class="flex-1 flex flex-col items-center justify-center text-center p-6 gap-4 overflow-y-auto">
        <img src="icon.svg" alt="" class="w-24 h-24 rounded-2xl">
        <h1 class="text-2xl font-bold text-blue-400">Instala Remote Kiosk</h1>
        <p class="text-gray-300 max-w-sm">Para usar el control, añádela a tu pantalla de inicio. Se abrirá como una app, sin la barra del navegador.</p>
        <button id="install-btn" style="display:none" class="bg-green-600 px-6 py-3 rounded-full font-bold active:bg-green-400">Instalar app</button>
        <div id="steps-ios" hidden class="text-left bg-gray-800 rounded-xl p-4 max-w-sm w-full">
            <p class="font-bold mb-2 text-blue-300">iPhone / iPad (Safari)</p>
            <svg viewBox="0 0 240 170" aria-hidden="true" class="w-full max-w-[200px] mx-auto mb-3">
                <rect x="74" y="8" width="92" height="154" rx="16" fill="#0b1220" stroke="#374151" stroke-width="2"/>
                <rect x="82" y="20" width="76" height="104" rx="6" fill="#111827"/>
                <rect x="76" y="130" width="88" height="30" fill="#1f2937"/>
                <circle cx="120" cy="145" r="15" fill="none" stroke="#22c55e" stroke-width="2.5"/>
                <g stroke="#e5e7eb" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M113 145 v9 a2 2 0 0 0 2 2 h10 a2 2 0 0 0 2 -2 v-9"/>
                    <line x1="120" y1="139" x2="120" y2="152"/>
                    <polyline points="116,143 120,139 124,143"/>
                </g>
                <path d="M192 92 q-22 28 -54 47" fill="none" stroke="#22c55e" stroke-width="2"/>
                <polygon points="138,141 148,139 144,149" fill="#22c55e"/>
                <text x="150" y="88" fill="#22c55e" font-size="13" font-weight="bold" font-family="sans-serif">Compartir</text>
            </svg>
            <ol class="list-decimal list-inside space-y-1 text-sm text-gray-300">
                <li>Toca <b>Compartir</b> (el cuadro con la flecha).</li>
                <li>Elige <b>"Añadir a pantalla de inicio"</b>.</li>
                <li>Toca <b>Añadir</b> y abre desde el nuevo icono.</li>
            </ol>
        </div>
        <div id="steps-android" hidden class="text-left bg-gray-800 rounded-xl p-4 max-w-sm w-full">
            <p class="font-bold mb-2 text-blue-300">Android (Chrome)</p>
            <svg viewBox="0 0 240 170" aria-hidden="true" class="w-full max-w-[200px] mx-auto mb-3">
                <rect x="74" y="8" width="92" height="154" rx="16" fill="#0b1220" stroke="#374151" stroke-width="2"/>
                <rect x="76" y="10" width="88" height="24" fill="#1f2937"/>
                <rect x="82" y="15" width="58" height="14" rx="7" fill="#374151"/>
                <circle cx="155" cy="22" r="12" fill="none" stroke="#22c55e" stroke-width="2.5"/>
                <g fill="#e5e7eb">
                    <circle cx="155" cy="16" r="1.8"/>
                    <circle cx="155" cy="22" r="1.8"/>
                    <circle cx="155" cy="28" r="1.8"/>
                </g>
                <rect x="82" y="40" width="76" height="116" rx="6" fill="#111827"/>
                <path d="M132 74 q26 -18 22 -40" fill="none" stroke="#22c55e" stroke-width="2"/>
                <polygon points="150,36 157,42 148,45" fill="#22c55e"/>
                <text x="118" y="82" fill="#22c55e" font-size="13" font-weight="bold" font-family="sans-serif" text-anchor="middle">Menú</text>
            </svg>
            <ol class="list-decimal list-inside space-y-1 text-sm text-gray-300">
                <li>Pulsa el menú <b>tres puntos</b> (arriba a la derecha).</li>
                <li>Elige <b>"Instalar app"</b> o <b>"Añadir a pantalla de inicio"</b>.</li>
                <li>Confirma y abre desde el nuevo icono.</li>
            </ol>
        </div>
        <p class="text-xs text-gray-500 max-w-sm">¿Ya la instalaste? Ábrela desde el icono, no desde el navegador.</p>
    </div>

    <!-- Installed app: the remote -->
    <div id="app-ui" class="flex-1 flex flex-col min-h-0">
        <div class="px-4 pt-2 flex justify-between items-center">
            <span class="text-xs text-gray-500">Remote Kiosk</span>
            <span id="status" class="text-red-500 text-xs font-bold">Disconnected</span>
        </div>

        <div class="px-3 pt-2">
            <div id="apps-row" class="grid grid-cols-5 gap-2"></div>
            <div id="apps-more" class="grid grid-cols-5 gap-2 mt-2" hidden></div>
            <button id="more-btn" onclick="toggleMore()" class="w-full mt-1 text-xs text-gray-400 py-1">Más apps</button>
        </div>

        <div class="flex-1 px-3 py-3 min-h-0">
            <div id="touchpad" class="w-full h-full rounded-2xl bg-gray-700/30 border border-gray-600"></div>
        </div>

        <div class="flex justify-center mb-2">
            <button id="mic-btn" onmousedown="startVoice()" onmouseup="stopVoice()" onmouseleave="stopVoice()" ontouchstart="startVoice()" ontouchend="stopVoice()"
                class="w-16 h-16 rounded-full bg-green-500/80 active:bg-green-400 flex items-center justify-center text-2xl shadow-[0_0_22px_rgba(34,197,94,0.55)] select-none">&#127908;</button>
        </div>

        <div class="px-3 pb-2 grid grid-cols-5 gap-2">
            <button onclick="openKeyboard()" class="util-btn" title="Teclado">&#9000;</button>
            <button onclick="sendMedia('KEY_PREVIOUSSONG')" class="util-btn">&#9198;</button>
            <button onclick="sendMedia('KEY_PLAYPAUSE')" class="util-btn">&#9199;</button>
            <button onclick="sendMedia('KEY_NEXTSONG')" class="util-btn">&#9197;</button>
            <button onclick="sendMedia('KEY_MUTE')" class="util-btn">&#128263;</button>
        </div>

        <div class="bg-slate-600/30 px-4 py-4 rounded-t-3xl flex items-center justify-between gap-2">
            <div class="flex flex-col gap-3">
                <button onclick="homeAction()" class="ctrl-round" title="Home (cierra app)">&#127968;</button>
                <button onclick="sendKey('KEY_ESC')" class="ctrl-round" title="Atrás">&#8617;</button>
            </div>
            <div class="grid grid-cols-3 grid-rows-3 gap-1 w-36 h-36">
                <div></div>
                <button onclick="sendKey('KEY_UP')" class="dpad">&#9650;</button>
                <div></div>
                <button onclick="sendKey('KEY_LEFT')" class="dpad">&#9664;</button>
                <button onclick="sendKey('KEY_ENTER')" class="dpad-ok">OK</button>
                <button onclick="sendKey('KEY_RIGHT')" class="dpad">&#9654;</button>
                <div></div>
                <button onclick="sendKey('KEY_DOWN')" class="dpad">&#9660;</button>
                <div></div>
            </div>
            <div class="flex flex-col gap-3">
                <button onclick="sendMedia('KEY_VOLUMEUP')" class="ctrl-round">+</button>
                <button onclick="sendMedia('KEY_VOLUMEDOWN')" class="ctrl-round">&#8211;</button>
            </div>
        </div>
    </div>

    <!-- System keyboard bridge -->
    <div id="kb-bar" hidden class="fixed bottom-0 left-0 right-0 bg-gray-800 p-2 flex gap-2 items-center z-50 border-t border-gray-700">
        <input id="kb-input" type="text" autocomplete="off" autocapitalize="none" autocorrect="off" spellcheck="false"
            class="flex-1 bg-gray-700 rounded px-3 py-2 text-white outline-none" placeholder="Escribe... se envía a la TV">
        <button onclick="closeKeyboard()" class="bg-green-600 px-4 py-2 rounded font-bold">Done</button>
    </div>

    <script src="app.js"></script>
    <script>
      if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => navigator.serviceWorker.register('sw.js').catch(console.error));
      }
    </script>
</body>
</html>
```
END_FILE frontend/index.html

---

## TASK F2 — frontend/app.js : full rewrite
```
type: write_full
file: frontend/app.js
```
BEGIN_FILE frontend/app.js
```javascript
const statusEl = document.getElementById('status');
let ws;
let mediaRecorder;
let audioChunks = [];

// Lock zoom: block pinch-zoom (iOS gesture events) and ctrl+wheel zoom.
['gesturestart', 'gesturechange', 'gestureend'].forEach((ev) =>
    document.addEventListener(ev, (e) => e.preventDefault())
);
document.addEventListener('wheel', (e) => { if (e.ctrlKey) e.preventDefault(); }, { passive: false });

const host = window.location.hostname === '' || window.location.hostname === 'localhost' ? '127.0.0.1' : window.location.hostname;
const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';

// Pairing: persist ?token= from the URL (e.g. a QR link), then clean the address bar.
const urlToken = new URLSearchParams(window.location.search).get('token');
if (urlToken) {
    localStorage.setItem('license_token', urlToken);
    history.replaceState({}, document.title, window.location.pathname);
}
const token = localStorage.getItem('license_token') || 'guest';

// Insecure context (http) -> banner pointing to the HTTPS URL (mic needs HTTPS).
if (!window.isSecureContext && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
    const httpsUrl = `https://${location.hostname}:${location.port || '8000'}${location.pathname}`;
    window.addEventListener('load', () => {
        const banner = document.createElement('div');
        banner.style.cssText = 'background:#7f1d1d;color:#fff;padding:8px 12px;font-size:13px;text-align:center';
        banner.innerHTML = `El microfono necesita HTTPS. <a href="${httpsUrl}" style="color:#fca5a5;font-weight:bold">Abrir version segura</a> y acepta el certificado una vez.`;
        document.body.prepend(banner);
    });
}

const port = window.location.port || '8000';
const wsUrl = `${protocol}${host}:${port}/ws?token=${token}`;
const apiUrl = `${window.location.protocol}//${host}:${port}/api`;

function wsSend(obj) {
    if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(obj));
}

function connect() {
    ws = new WebSocket(wsUrl);
    ws.onopen = () => { statusEl.textContent = 'Connected'; statusEl.className = 'text-green-500 text-xs font-bold'; };
    ws.onclose = () => { statusEl.textContent = 'Reconnecting...'; statusEl.className = 'text-red-500 text-xs font-bold'; setTimeout(connect, 2000); };
    ws.onerror = (err) => console.error('WebSocket Error:', err);
    ws.onmessage = (e) => {
        try {
            const res = JSON.parse(e.data);
            if (res.status === 'processing') { statusEl.textContent = res.message; statusEl.className = 'text-purple-400 text-xs font-bold'; }
            else if (res.status === 'success' || res.status === 'error') {
                statusEl.textContent = res.status === 'error' ? `Error: ${res.message}` : 'Connected';
                statusEl.className = res.status === 'error' ? 'text-red-500 text-xs font-bold' : 'text-green-500 text-xs font-bold';
            }
        } catch (err) {}
    };
}

// --- Keys / media ---
function sendKey(key) { wsSend({ type: 'input', device: 'gamepad', action: 'press', key }); if (navigator.vibrate) navigator.vibrate(35); }
function sendMedia(key) { wsSend({ action: 'media_control', parameters: { key } }); if (navigator.vibrate) navigator.vibrate(25); }
function homeAction() { killKiosk(); }

// --- Touchpad pointer ---
const pad = document.getElementById('touchpad');
let padLast = null, padMoved = 0, padDown = 0, accX = 0, accY = 0, rafPending = false;
const POINTER_SENS = 1.6;
function flushPointer() {
    rafPending = false;
    if (accX || accY) { wsSend({ type: 'pointer', dx: Math.round(accX * POINTER_SENS), dy: Math.round(accY * POINTER_SENS) }); accX = 0; accY = 0; }
}
if (pad) {
    pad.addEventListener('pointerdown', (e) => { pad.setPointerCapture(e.pointerId); padLast = { x: e.clientX, y: e.clientY }; padMoved = 0; padDown = Date.now(); });
    pad.addEventListener('pointermove', (e) => {
        if (!padLast) return;
        const dx = e.clientX - padLast.x, dy = e.clientY - padLast.y;
        padLast = { x: e.clientX, y: e.clientY };
        padMoved += Math.abs(dx) + Math.abs(dy);
        accX += dx; accY += dy;
        if (!rafPending) { rafPending = true; requestAnimationFrame(flushPointer); }
    });
    const padEnd = () => {
        if (padLast && padMoved < 10 && Date.now() - padDown < 250) { wsSend({ type: 'pointer', click: 'left' }); if (navigator.vibrate) navigator.vibrate(20); }
        padLast = null;
    };
    pad.addEventListener('pointerup', padEnd);
    pad.addEventListener('pointercancel', () => { padLast = null; });
}

// --- System keyboard bridge ---
const kbBar = document.getElementById('kb-bar');
const kbInput = document.getElementById('kb-input');
let kbPrev = '';
function openKeyboard() { if (!kbBar) return; kbBar.hidden = false; kbInput.value = ''; kbPrev = ''; kbInput.focus(); }
function closeKeyboard() { if (!kbBar) return; kbInput.blur(); kbBar.hidden = true; }
if (kbInput) {
    kbInput.addEventListener('input', () => {
        const v = kbInput.value;
        if (v.length > kbPrev.length) { wsSend({ type: 'text', text: v.slice(kbPrev.length) }); }
        else if (v.length < kbPrev.length) { for (let i = 0; i < kbPrev.length - v.length; i++) wsSend({ type: 'input', device: 'gamepad', action: 'press', key: 'KEY_BACKSPACE' }); }
        kbPrev = v;
    });
    kbInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); wsSend({ type: 'input', device: 'gamepad', action: 'press', key: 'KEY_ENTER' }); } });
}

// --- Voice ---
async function startVoice() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) { alert('Captura de audio no soportada (requiere HTTPS).'); return; }
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
        mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) audioChunks.push(e.data); };
        mediaRecorder.onstop = () => {
            const blob = new Blob(audioChunks, { type: 'audio/webm' });
            if (ws && ws.readyState === WebSocket.OPEN) ws.send(blob);
            audioChunks = [];
            stream.getTracks().forEach((t) => t.stop());
        };
        mediaRecorder.start();
        if (navigator.vibrate) navigator.vibrate(50);
        statusEl.textContent = 'Listening...'; statusEl.className = 'text-blue-400 text-xs font-bold';
    } catch (e) { console.error('Mic denied', e); }
}
function stopVoice() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        if (navigator.vibrate) navigator.vibrate([40, 40]);
        statusEl.textContent = 'Processing AI...'; statusEl.className = 'text-purple-400 text-xs font-bold';
    }
}

// --- App grid (most-used first + more) ---
function getUsage() { try { return JSON.parse(localStorage.getItem('app_usage') || '{}'); } catch (e) { return {}; } }
function bumpUsage(id) { const u = getUsage(); u[id] = (u[id] || 0) + 1; localStorage.setItem('app_usage', JSON.stringify(u)); }

function appTile(app) {
    const color = app.color || '#2563eb';
    const initial = (app.name || '?').charAt(0);
    return `<div onclick="launchKiosk('${app.url}','${app.id}')" class="flex flex-col items-center gap-1 cursor-pointer active:scale-95">
        <div class="w-12 h-12 rounded-full flex items-center justify-center text-lg font-bold" style="background:${color}">${initial}</div>
        <span class="text-[10px] text-gray-300 truncate w-full text-center">${app.name}</span>
    </div>`;
}

function renderApps(kiosks) {
    const usage = getUsage();
    const sorted = [...kiosks].sort((a, b) => (usage[b.id] || 0) - (usage[a.id] || 0));
    document.getElementById('apps-row').innerHTML = sorted.slice(0, 5).map(appTile).join('');
    const rest = sorted.slice(5);
    document.getElementById('apps-more').innerHTML = rest.map(appTile).join('');
    const moreBtn = document.getElementById('more-btn');
    if (moreBtn) moreBtn.style.display = rest.length ? 'block' : 'none';
}

function toggleMore() { const m = document.getElementById('apps-more'); if (m) m.hidden = !m.hidden; }

async function fetchApps() {
    try {
        const res = await fetch(`${apiUrl}/apps`);
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();
        renderApps(data.suggested_kiosks || []);
    } catch (e) { console.error('Failed to load apps:', e); }
}

async function launchKiosk(url, id) {
    if (id) bumpUsage(id);
    if (navigator.vibrate) navigator.vibrate(80);
    try {
        const res = await fetch(`${apiUrl}/kiosk/launch`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Auth-Token': token }, body: JSON.stringify({ url }) });
        if (!res.ok) throw new Error('HTTP ' + res.status);
    } catch (e) { console.error('Launch error:', e); }
}

async function killKiosk() {
    if (navigator.vibrate) navigator.vibrate([50, 50, 50]);
    try {
        const res = await fetch(`${apiUrl}/kiosk/kill`, { method: 'POST', headers: { 'X-Auth-Token': token } });
        if (!res.ok) throw new Error('HTTP ' + res.status);
    } catch (e) { console.error('Kill error:', e); }
}

// --- Browser tab vs installed app ---
const isStandalone = window.matchMedia('(display-mode: standalone)').matches
    || window.matchMedia('(display-mode: fullscreen)').matches
    || window.matchMedia('(display-mode: minimal-ui)').matches
    || window.navigator.standalone === true;

let deferredPrompt = null;
window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    const btn = document.getElementById('install-btn');
    if (btn) btn.style.display = 'inline-block';
});

function showInstallScreen() {
    const appUI = document.getElementById('app-ui');
    const installUI = document.getElementById('install-ui');
    if (appUI) appUI.hidden = true;
    if (installUI) installUI.hidden = false;
    const ua = navigator.userAgent || '';
    const isIOS = /iphone|ipad|ipod/i.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
    const iosSteps = document.getElementById('steps-ios');
    const androidSteps = document.getElementById('steps-android');
    if (iosSteps) iosSteps.hidden = !isIOS;
    if (androidSteps) androidSteps.hidden = isIOS;
    const btn = document.getElementById('install-btn');
    if (btn) {
        btn.addEventListener('click', async () => {
            if (!deferredPrompt) return;
            deferredPrompt.prompt();
            await deferredPrompt.userChoice;
            deferredPrompt = null;
            btn.style.display = 'none';
        });
    }
}

window.addEventListener('appinstalled', () => {
    const installUI = document.getElementById('install-ui');
    if (installUI) {
        installUI.innerHTML = '<div class="flex-1 flex flex-col items-center justify-center text-center p-6 gap-3">'
            + '<h1 class="text-2xl font-bold text-green-500">Instalada!</h1>'
            + '<p class="text-gray-300 max-w-sm">Abre Remote Kiosk desde el icono de tu pantalla de inicio.</p></div>';
    }
});

if (isStandalone) {
    connect();
    fetchApps();
} else {
    showInstallScreen();
}
```
END_FILE frontend/app.js

---

## TASK F3 — frontend/sw.js : bump cache version (force update)
```
type: edit
file: frontend/sw.js
```
FIND:
```javascript
const CACHE = 'lrp-v5';
```
REPLACE:
```javascript
const CACHE = 'lrp-v6';
```

---

# 4. VERIFICATION (run after applying; all must pass)

```
V1  cd backend && python -m py_compile main.py input_emulator.py auth.py ai_pipeline.py kiosk.py discovery.py
    EXPECT: exit 0

V2  node --check frontend/app.js
    EXPECT: exit 0

V3  grep -n "from input_emulator import gamepad, mouse" backend/main.py    -> 1 match
    grep -n "\"type\": \"pointer\"" frontend/app.js  (pointer messages present) -> >=1
    grep -n "id=\"touchpad\"" frontend/index.html     -> 1 match
    grep -n "id=\"kb-bar\"" frontend/index.html        -> 1 match
    grep -n "lrp-v6" frontend/sw.js                    -> 1 match

V4  Boot smoke test (needs deps installed):
      cd backend && python -c "import main" 2>&1 | grep -vi warning
    EXPECT: no traceback

V5  HTML well-formed:
      python -c "import html.parser,sys; p=html.parser.HTMLParser(); p.feed(open('frontend/index.html',encoding='utf-8').read()); print('html ok')"
    EXPECT: html ok
```

# 5. DONE_CRITERIA

```
- B1, B2, B3, F1, F2, F3 applied.
- V1..V5 pass.
- backend/input_emulator.py UNCHANGED.
- No git commit / push.
- Report:
    APPLIED: [ids]
    SKIPPED: [ids + reason]
    VERIFICATION: V1..V5 pass/fail
```
```
END_OF_SPEC
```
