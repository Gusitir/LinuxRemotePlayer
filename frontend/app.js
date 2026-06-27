const statusEl = document.getElementById('status');
let ws;
let mediaRecorder;
let audioChunks = [];
let suggestedApps = [];
let installedApps = [];

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

const ICON_PLUS = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon"><path d="M5 12h14"/><path d="M12 5v14"/></svg>';

function wsSend(obj) {
    if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(obj));
}

let toastTimer = null;
function toast(msg) {
    let t = document.getElementById('toast');
    if (!t) {
        t = document.createElement('div');
        t.id = 'toast';
        t.style.cssText = 'position:fixed;left:50%;bottom:90px;transform:translateX(-50%);background:#111827;color:#fff;padding:10px 16px;border-radius:9999px;font-size:13px;z-index:60;box-shadow:0 4px 14px rgba(0,0,0,.5);opacity:0;transition:opacity .2s;pointer-events:none';
        document.body.appendChild(t);
    }
    t.textContent = msg;
    t.style.opacity = '1';
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { t.style.opacity = '0'; }, 1800);
}

function comingSoon() { toast('Próximamente'); }
function openSettings() { const d = document.getElementById('settings-drawer'); if (d) d.classList.add('open'); }
function closeSettings() { const d = document.getElementById('settings-drawer'); if (d) d.classList.remove('open'); }

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
// Transport (play/seek) uses ordinary keys so they hit the FOREGROUND kiosk window,
// not whatever holds the system media session (e.g. a background browser tab).
// Volume/mute stay as media keys because those act globally at the OS mixer.
function sendKey(key) { wsSend({ type: 'input', device: 'gamepad', action: 'press', key }); if (navigator.vibrate) navigator.vibrate(35); }
function sendMedia(key) { wsSend({ action: 'media_control', parameters: { key } }); if (navigator.vibrate) navigator.vibrate(25); }
function homeAction() { killKiosk(); }

// --- Touchpad pointer (tap = left click, long-press = right click) ---
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
        if (padLast && padMoved < 10) {
            const dur = Date.now() - padDown;
            if (dur < 250) { wsSend({ type: 'pointer', click: 'left' }); if (navigator.vibrate) navigator.vibrate(20); }
            else if (dur > 500) { wsSend({ type: 'pointer', click: 'right' }); if (navigator.vibrate) navigator.vibrate([20, 40]); }
        }
        padLast = null;
    };
    pad.addEventListener('pointerup', padEnd);
    pad.addEventListener('pointercancel', () => { padLast = null; });
}

// --- Scroll strip (drag vertically -> mouse wheel) ---
const scrollStrip = document.getElementById('scroll-strip');
let scLast = null, scAcc = 0;
const SCROLL_STEP = 18;
if (scrollStrip) {
    scrollStrip.addEventListener('pointerdown', (e) => { scrollStrip.setPointerCapture(e.pointerId); scLast = e.clientY; scAcc = 0; });
    scrollStrip.addEventListener('pointermove', (e) => {
        if (scLast === null) return;
        scAcc += e.clientY - scLast;
        scLast = e.clientY;
        while (Math.abs(scAcc) >= SCROLL_STEP) {
            // Drag down -> content scrolls down (REL_WHEEL negative).
            wsSend({ type: 'pointer', scroll: scAcc > 0 ? -1 : 1 });
            scAcc += scAcc > 0 ? -SCROLL_STEP : SCROLL_STEP;
        }
    });
    const scEnd = () => { scLast = null; };
    scrollStrip.addEventListener('pointerup', scEnd);
    scrollStrip.addEventListener('pointercancel', scEnd);
}

// --- System keyboard bridge ---
const kbBar = document.getElementById('kb-bar');
const kbInput = document.getElementById('kb-input');
let kbPrev = '';
function openKeyboard() { if (!kbBar) return; kbBar.style.display = 'flex'; kbInput.value = ''; kbPrev = ''; kbInput.focus(); }
function closeKeyboard() { if (!kbBar) return; kbInput.blur(); kbBar.style.display = 'none'; }
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

// --- Apps: usage, custom apps, tiles ---
function getUsage() { try { return JSON.parse(localStorage.getItem('app_usage') || '{}'); } catch (e) { return {}; } }
function bumpUsage(id) { const u = getUsage(); u[id] = (u[id] || 0) + 1; localStorage.setItem('app_usage', JSON.stringify(u)); }

function getCustomApps() { try { return JSON.parse(localStorage.getItem('custom_apps') || '[]'); } catch (e) { return []; } }
function saveCustomApps(arr) { localStorage.setItem('custom_apps', JSON.stringify(arr)); }
const PALETTE = ['#ef4444', '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6', '#ec4899', '#14b8a6'];

function allApps() { return [...suggestedApps, ...getCustomApps()]; }

function faviconUrl(url) {
    try { return `https://www.google.com/s2/favicons?sz=64&domain=${new URL(url).hostname}`; }
    catch (e) { return ''; }
}

function tileHTML(app, removable) {
    const color = app.color || '#2563eb';
    const initial = (app.name || '?').charAt(0).toUpperCase();
    const isNative = app.kind === 'native';
    const onclick = isNative ? `launchNative('${app.nativeId}','${app.id}')` : `launchKiosk('${app.url}','${app.id}')`;
    const fav = isNative ? '' : faviconUrl(app.url);
    const img = fav ? `<img src="${fav}" alt="" class="relative w-7 h-7" onerror="this.remove()">` : '';
    const remove = removable
        ? `<button onclick="event.stopPropagation(); removeCustomApp('${app.id}')" class="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-red-600 text-white text-xs flex items-center justify-center z-10">x</button>`
        : '';
    return `<div onclick="${onclick}" class="applauncher relative flex flex-col items-center gap-1 cursor-pointer">
        ${remove}
        <div class="w-12 h-12 rounded-full relative flex items-center justify-center overflow-hidden" style="background:${color}">
            <span class="absolute inset-0 flex items-center justify-center text-lg font-bold text-white">${initial}</span>
            ${img}
        </div>
        <span class="text-[10px] text-gray-300 truncate w-full text-center">${app.name}</span>
    </div>`;
}

function plusTileHTML() {
    return `<div onclick="toggleAddPanel()" class="applauncher flex flex-col items-center gap-1 cursor-pointer">
        <div class="w-12 h-12 rounded-full border-2 border-dashed border-gray-500 flex items-center justify-center text-gray-400">${ICON_PLUS}</div>
        <span class="text-[10px] text-gray-400 text-center">Añadir</span>
    </div>`;
}

function renderMainRow() {
    const usage = getUsage();
    const sorted = [...allApps()].sort((a, b) => (usage[b.id] || 0) - (usage[a.id] || 0));
    const row = document.getElementById('apps-row');
    if (row) row.innerHTML = sorted.slice(0, 5).map((a) => tileHTML(a, false)).join('');
}

// --- App drawer ---
function openDrawer() { renderDrawer(); const d = document.getElementById('app-drawer'); if (d) d.classList.add('open'); }
function closeDrawer() { const d = document.getElementById('app-drawer'); if (d) d.classList.remove('open'); const p = document.getElementById('add-panel'); if (p) p.style.display = 'none'; }
function toggleAddPanel() { const p = document.getElementById('add-panel'); if (p) p.style.display = p.style.display === 'none' ? 'block' : 'none'; }

function renderDrawer() {
    const custom = getCustomApps();
    const grid = [
        ...suggestedApps.map((a) => tileHTML(a, false)),
        ...custom.map((a) => tileHTML(a, true)),
        plusTileHTML(),
    ].join('');
    const g = document.getElementById('drawer-grid');
    if (g) g.innerHTML = grid;
    renderNativeList();
}

function renderNativeList() {
    const el = document.getElementById('native-list');
    if (!el) return;
    if (!installedApps.length) {
        el.innerHTML = '<p class="text-xs text-gray-500">No se detectaron apps del sistema (o el backend no corre en Linux).</p>';
        return;
    }
    el.innerHTML = installedApps.slice(0, 80).map((a) => {
        const safeName = String(a.name).replace(/'/g, "\\'");
        return `<div class="flex items-center justify-between bg-gray-700 rounded px-3 py-2">
            <span class="truncate flex-1 cursor-pointer" onclick="launchNative('${a.id}')">${a.name}</span>
            <button onclick="event.stopPropagation(); addNativeApp('${a.id}','${safeName}')" class="text-blue-400 text-xs ml-2 whitespace-nowrap">+ Añadir</button>
        </div>`;
    }).join('');
}

function addCustomApp() {
    const nameEl = document.getElementById('new-app-name');
    const urlEl = document.getElementById('new-app-url');
    if (!nameEl || !urlEl) return;
    const name = (nameEl.value || '').trim();
    let url = (urlEl.value || '').trim();
    if (!name || !url) { alert('Escribe un nombre y una URL.'); return; }
    if (!/^https?:\/\//i.test(url)) url = 'https://' + url;
    const apps = getCustomApps();
    apps.push({ id: 'custom-' + Date.now(), name, url, color: PALETTE[apps.length % PALETTE.length] });
    saveCustomApps(apps);
    nameEl.value = ''; urlEl.value = '';
    renderDrawer();
    renderMainRow();
}

function removeCustomApp(id) {
    saveCustomApps(getCustomApps().filter((a) => a.id !== id));
    renderDrawer();
    renderMainRow();
}

async function fetchApps() {
    try {
        const res = await fetch(`${apiUrl}/apps`);
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();
        suggestedApps = data.suggested_kiosks || [];
        installedApps = data.installed_apps || [];
        renderMainRow();
    } catch (e) { console.error('Failed to load apps:', e); }
}

async function launchKiosk(url, id) {
    if (id) bumpUsage(id);
    const a = allApps().find((x) => x.id === id);
    toast('Abriendo ' + (a ? a.name : 'app') + '...');
    if (navigator.vibrate) navigator.vibrate(80);
    closeDrawer();
    try {
        const res = await fetch(`${apiUrl}/kiosk/launch`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Auth-Token': token }, body: JSON.stringify({ url }) });
        if (!res.ok) throw new Error('HTTP ' + res.status);
    } catch (e) { console.error('Launch error:', e); }
}

async function launchNative(nativeId, usageId) {
    if (usageId) bumpUsage(usageId);
    const a = installedApps.find((x) => x.id === nativeId) || allApps().find((x) => x.nativeId === nativeId);
    toast('Abriendo ' + (a ? a.name : 'app') + '...');
    if (navigator.vibrate) navigator.vibrate(80);
    closeDrawer();
    try {
        const res = await fetch(`${apiUrl}/app/launch`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Auth-Token': token }, body: JSON.stringify({ id: nativeId }) });
        if (!res.ok) throw new Error('HTTP ' + res.status);
    } catch (e) { console.error('Native launch error:', e); }
}

function addNativeApp(nativeId, name) {
    const apps = getCustomApps();
    if (apps.some((a) => a.nativeId === nativeId)) { toast(name + ' ya está en el menú'); return; }
    apps.push({ id: 'native-' + nativeId, name, kind: 'native', nativeId, color: PALETTE[apps.length % PALETTE.length] });
    saveCustomApps(apps);
    renderDrawer();
    renderMainRow();
    toast(name + ' añadido al menú');
}

async function killKiosk() {
    if (navigator.vibrate) navigator.vibrate([50, 50, 50]);
    try {
        const res = await fetch(`${apiUrl}/kiosk/kill`, { method: 'POST', headers: { 'X-Auth-Token': token } });
        if (!res.ok) throw new Error('HTTP ' + res.status);
    } catch (e) { console.error('Kill error:', e); }
}

async function loadConfig() {
    try {
        const res = await fetch(`${apiUrl}/config`);
        if (!res.ok) return;
        const cfg = await res.json();
        if (!cfg.voice_enabled) {
            const m = document.getElementById('mic-row');
            if (m) m.style.display = 'none';
        }
    } catch (e) {}
}

// --- Where to show the remote vs the install tutorial ---
const ua = navigator.userAgent || '';
const isMobile = /android|iphone|ipad|ipod/i.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
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
    if (appUI) appUI.style.display = 'none';
    if (installUI) installUI.style.display = 'flex';
    const isIOS = /iphone|ipad|ipod/i.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
    const iosSteps = document.getElementById('steps-ios');
    const androidSteps = document.getElementById('steps-android');
    if (iosSteps) iosSteps.style.display = isIOS ? 'block' : 'none';
    if (androidSteps) androidSteps.style.display = isIOS ? 'none' : 'block';
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

// Show the remote when installed OR on a desktop/computer (so it can be tested there).
// Only mobile-browser-not-installed gets the install tutorial.
if (!isStandalone && isMobile) {
    showInstallScreen();
} else {
    connect();
    fetchApps();
    loadConfig();
}
