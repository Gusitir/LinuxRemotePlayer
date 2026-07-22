const statusEl = document.getElementById('status');
let ws;
let mediaRecorder;
let audioChunks = [];

// Resilient token storage helper - CONN-04
function getDBToken() {
    return new Promise((resolve) => {
        try {
            const req = indexedDB.open('LRPDB', 1);
            req.onupgradeneeded = (e) => {
                e.target.result.createObjectStore('config');
            };
            req.onsuccess = (e) => {
                const db = e.target.result;
                const tx = db.transaction('config', 'readonly');
                const store = tx.objectStore('config');
                const getReq = store.get('license_token');
                getReq.onsuccess = () => resolve(getReq.result);
                getReq.onerror = () => resolve(null);
            };
            req.onerror = () => resolve(null);
        } catch (err) {
            resolve(null);
        }
    });
}

function setDBToken(token) {
    return new Promise((resolve) => {
        try {
            const req = indexedDB.open('LRPDB', 1);
            req.onupgradeneeded = (e) => {
                e.target.result.createObjectStore('config');
            };
            req.onsuccess = (e) => {
                const db = e.target.result;
                const tx = db.transaction('config', 'readwrite');
                const store = tx.objectStore('config');
                store.put(token, 'license_token');
                tx.oncomplete = () => resolve(true);
            };
            req.onerror = () => resolve(false);
        } catch (err) {
            resolve(false);
        }
    });
}

// Lock zoom: block pinch-zoom (iOS gesture events) and ctrl+wheel zoom.
['gesturestart', 'gesturechange', 'gestureend'].forEach((ev) =>
    document.addEventListener(ev, (e) => e.preventDefault())
);
document.addEventListener('wheel', (e) => { if (e.ctrlKey) e.preventDefault(); }, { passive: false });

const host = window.location.hostname === '' || window.location.hostname === 'localhost' ? '127.0.0.1' : window.location.hostname;
const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';

let token = 'guest';
let lastSuggestedKiosks = [];
let buyUrl = 'https://linux-remote-player.vercel.app/';
let isLicensed = false;
let latestUpdateVersion = null;

function toast(message) {
    const el = document.createElement('div');
    el.textContent = message;
    el.style.position = 'fixed';
    el.style.bottom = '80px';
    el.style.left = '50%';
    el.style.transform = 'translateX(-50%)';
    el.style.backgroundColor = '#1f2937';
    el.style.color = '#ffffff';
    el.style.padding = '8px 16px';
    el.style.borderRadius = '8px';
    el.style.fontSize = '14px';
    el.style.fontWeight = '600';
    el.style.zIndex = '9999';
    el.style.boxShadow = '0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05)';
    el.style.border = '1px solid #374151';
    el.style.transition = 'opacity 0.3s ease';
    el.style.opacity = '0';
    el.style.pointerEvents = 'none';
    document.body.appendChild(el);
    
    setTimeout(() => { el.style.opacity = '1'; }, 10);
    setTimeout(() => {
        el.style.opacity = '0';
        setTimeout(() => { el.remove(); }, 300);
    }, 2500);
}

async function initToken() {
    const urlParams = new URLSearchParams(window.location.search);
    const urlToken = urlParams.get('token');
    if (urlToken) {
        localStorage.setItem('license_token', urlToken);
        await setDBToken(urlToken);
    }
    const urlLicense = urlParams.get('license');

    if (urlToken || urlLicense) {
        history.replaceState({}, document.title, window.location.pathname);
    }

    let storedToken = localStorage.getItem('license_token');
    if (!storedToken) {
        storedToken = await getDBToken();
        if (storedToken) {
            localStorage.setItem('license_token', storedToken);
        }
    }
    token = storedToken || 'guest';

    if (urlLicense) {
        if (token === 'guest') {
            // Save as pending license (finding #7)
            localStorage.setItem('pending_license', urlLicense);
            toast('Clave guardada. Por favor, empareja tu dispositivo primero.');
            const input = document.getElementById('license-input');
            if (input) input.value = urlLicense;
        } else {
            setTimeout(async () => {
                const input = document.getElementById('license-input');
                if (input) input.value = urlLicense;
                await activateLicenseKey();
            }, 1000);
        }
    }
}

// Insecure context (http) -> banner pointing to the HTTPS URL (mic needs HTTPS).
if (!window.isSecureContext && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
    const httpsUrl = `https://${location.hostname}:${location.port || '8000'}${location.pathname}`;
    window.addEventListener('load', () => {
        const banner = document.createElement('div');
        banner.style.cssText = 'background:#7f1d1d;color:#fff;padding:8px 12px;font-size:13px;text-align:center';
        banner.innerHTML = `El micrófono necesita HTTPS. <a href="${httpsUrl}" style="color:#fca5a5;font-weight:bold">Abrir versión segura</a> y acepta el certificado una vez.`;
        document.body.prepend(banner);
    });
}

const port = window.location.port || '8000';
// WS: drop token from URL - SEC-06
const wsUrl = `${protocol}${host}:${port}/ws`;
const apiUrl = `${window.location.protocol}//${host}:${port}/api`;

let connectAttempts = 0;
let retryTimeoutId = null; // HYG-02: prevent storm reconnects
let hostname = '';

function setSkin(skin) {
    if (skin !== 'dark' && skin !== 'day' && skin !== 'neon' && skin !== 'anime') {
        skin = 'dark';
    }
    if (skin !== 'dark' && !isLicensed) {
        toast('Este tema (skin) requiere una licencia pro.');
        skin = 'dark';
    }
    document.documentElement.setAttribute('data-skin', skin);
    localStorage.setItem('lrp_skin', skin);
}

async function fetchLicenseStatus() {
    try {
        const res = await fetch(`${apiUrl}/license/status`, {
            headers: { 'X-Auth-Token': token }
        });
        if (res.ok) {
            const data = await res.json();
            isLicensed = data.licensed;

            // Apply saved skin after checking license
            const savedSkin = localStorage.getItem('lrp_skin') || 'dark';
            setSkin(savedSkin);

            const micRow = document.getElementById('mic-row');
            const voiceCard = document.getElementById('voice-commands-card');
            if (micRow) {
                const showVoice = data.voice_enabled && isLicensed;
                micRow.style.display = showVoice ? 'flex' : 'none';
                if (voiceCard) {
                    voiceCard.classList.toggle('hidden', !showVoice);
                }
                
                if (showVoice && !localStorage.getItem('lrp_voice_hint_shown')) {
                    localStorage.setItem('lrp_voice_hint_shown', 'true');
                    toast("Consejo: mantén pulsado el micrófono y di 'abre youtube'");
                }
            }

            const unlicBlock = document.getElementById('license-unlicensed');
            const licBlock = document.getElementById('license-licensed');
            if (unlicBlock && licBlock) {
                if (isLicensed) {
                    unlicBlock.classList.add('hidden');
                    unlicBlock.classList.remove('flex');
                    licBlock.classList.remove('hidden');
                    licBlock.classList.add('flex');
                    
                    const infoText = document.getElementById('license-info-text');
                    if (infoText) {
                        const masked = (token || '').substring(0, 4) + '••••••••' + (token || '').slice(-4);
                        infoText.innerText = `Clave: LRP-${masked}\nPlan: Lifetime\n${data.voice_enabled ? 'Voz con IA: Activa (60 comandos/día)' : 'Voz con IA: se activará al configurar el servicio'}`;
                    }
                } else {
                    unlicBlock.classList.remove('hidden');
                    unlicBlock.classList.add('flex');
                    licBlock.classList.add('hidden');
                    licBlock.classList.remove('flex');
                }
            }
            
            const locks = document.querySelectorAll('.pro-lock');
            locks.forEach(lock => {
                if (isLicensed) lock.classList.add('hidden');
                else lock.classList.remove('hidden');
            });
        }
    } catch (err) {
        console.error('Failed to get license status:', err);
    }
}

async function fetchConfig() {
    try {
        const res = await fetch(`${apiUrl}/config`);
        if (res.ok) {
            const data = await res.json();
            hostname = data.hostname || '';
            buyUrl = data.buy_url || 'https://linux-remote-player.vercel.app/';

            const verText = document.getElementById('version-text');
            if (verText) verText.textContent = `Versión ${data.version || '1.0.0'}`;
            const footerVer = document.getElementById('app-version-footer');
            if (footerVer) footerVer.textContent = `${data.version || '1.0.0'} — LinuxRemotePlayer`;

            await fetchLicenseStatus();
        }
    } catch (err) {
        console.error('Config fetch failed:', err);
    }
}

function showTroubleBanner(show) {
    const banner = document.getElementById('conn-error-banner');
    if (!banner) return;
    if (show) {
        document.getElementById('conn-target-url').textContent = wsUrl;
        const link = document.getElementById('conn-link');
        link.href = location.origin;
        const hint = document.getElementById('conn-hostname-hint');
        if (hostname) {
            hint.textContent = `¿Cambió la IP del PC? Intenta usar: https://${hostname}.local:${port}`;
        } else {
            hint.textContent = '';
        }
        banner.style.display = 'flex';
    } else {
        banner.style.display = 'none';
    }
}

// Helper: safe JSON WS send
function wsSend(obj) {
    if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(obj));
}

function connect() {
    if (ws) {
        ws.onclose = null; // P3-4 prevent old socket close from flashing red
        try { ws.close(); } catch(e) {}
    }
    if (retryTimeoutId) {
        clearTimeout(retryTimeoutId);
        retryTimeoutId = null;
    }

    ws = new WebSocket(wsUrl);
    ws.onopen = () => {
        if (typeof wakeTimeoutId !== 'undefined' && wakeTimeoutId) {
            clearTimeout(wakeTimeoutId);
            wakeTimeoutId = null;
        }
        connectAttempts = 0;
        showTroubleBanner(false);
        statusEl.textContent = 'Connected';
        statusEl.className = 'text-green-500 text-xs font-bold';

        // SEC-06: WebSocket auth frame
        ws.send(JSON.stringify({ type: 'auth', token: token }));

        startHeartbeat();
    };
    ws.onclose = (event) => {
        stopHeartbeat();
        const latencyEl = document.getElementById('latency');
        if (latencyEl) latencyEl.classList.add('hidden');
        if (event.code === 1008) {
            statusEl.textContent = 'No autorizado';
            statusEl.className = 'text-red-500 text-xs font-bold';
            showPairingScreen(true);
            return;
        }

        connectAttempts++;
        
        if (typeof wakeTimeoutId === 'undefined' || !wakeTimeoutId) {
            statusEl.textContent = 'Reconnecting...';
            statusEl.className = 'text-red-500 text-xs font-bold';
        }

        if (connectAttempts >= 5) {
            showTroubleBanner(true);
        }

        // Exponential backoff with jitter: 1s, 2s, 4s, 8s, max 15s (CONN-03)
        const backoff = Math.min(15000, Math.pow(2, connectAttempts - 1) * 1000 + Math.random() * 1000);
        retryTimeoutId = setTimeout(connect, backoff);
    };
    ws.onerror = (err) => console.error('WebSocket Error:', err);
    ws.onmessage = (e) => {
        try {
            const res = JSON.parse(e.data);
            if (res.type === 'pong') {
                lastPong = Date.now();
                if (lastPingSent > 0) {
                    const rtt = lastPong - lastPingSent;
                    const latencyEl = document.getElementById('latency');
                    if (latencyEl) {
                        latencyEl.textContent = rtt + ' ms';
                        latencyEl.className = 'text-xs font-bold ml-2 opacity-80 ' + (rtt < 60 ? 'text-green-500' : (rtt < 150 ? 'text-yellow-500' : 'text-red-500'));
                        latencyEl.classList.remove('hidden');
                    }
                }
            } else if (res.status === 'processing') {
                statusEl.textContent = res.message;
                statusEl.className = 'text-purple-400 text-xs font-bold';
            } else if (res.status === 'success' || res.status === 'error') {
                statusEl.textContent = res.status === 'error' ? `Error: ${res.message}` : 'Connected';
                statusEl.className = res.status === 'error' ? 'text-red-500 text-xs font-bold' : 'text-green-500 text-xs font-bold';
                if (res.status === 'error' && res.code === 'in_use_elsewhere') {
                    handleLicenseConflict();
                }
                if (res.status === 'success' && res.message === 'Authenticated') {
                    const row = document.getElementById('apps-row');
                    if (row && !row.children.length) {
                        fetchApps().then(() => {
                            setTimeout(() => { requestAnimationFrame(showTour); }, 500);
                        }).catch(() => {
                            setTimeout(() => { requestAnimationFrame(showTour); }, 500);
                        });
                    } else {
                        setTimeout(() => { requestAnimationFrame(showTour); }, 500);
                    }
                }
            }
        } catch (err) {}
    };
}

// --- Heartbeat - CONN-05 ---
let heartbeatIntervalId = null;
let heartbeatTimeoutId = null;
let lastPong = 0;
let lastPingSent = 0;

function startHeartbeat() {
    stopHeartbeat();
    lastPong = Date.now();
    heartbeatIntervalId = setInterval(() => {
        if (ws && ws.readyState === WebSocket.OPEN) {
            lastPingSent = Date.now();
            wsSend({ type: 'ping' });
            heartbeatTimeoutId = setTimeout(() => {
                if (Date.now() - lastPong > 5000) {
                    console.warn('Heartbeat timeout, closing connection.');
                    ws.close();
                }
            }, 5000);
        }
    }, 10000);
}

function stopHeartbeat() {
    if (heartbeatIntervalId) {
        clearInterval(heartbeatIntervalId);
        heartbeatIntervalId = null;
    }
    if (heartbeatTimeoutId) {
        clearTimeout(heartbeatTimeoutId);
        heartbeatTimeoutId = null;
    }
}

// --- Resume trigger handlers - CONN-05 ---
let wakeTimeoutId = null;
function handleResume() {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        connectAttempts = 0;
        statusEl.textContent = 'Conectando...';
        statusEl.className = 'text-gray-400 text-xs font-bold';
        
        if (wakeTimeoutId) clearTimeout(wakeTimeoutId);
        wakeTimeoutId = setTimeout(() => {
            if (!ws || ws.readyState !== WebSocket.OPEN) {
                statusEl.textContent = 'Reconectando...';
                statusEl.className = 'text-red-500 text-xs font-bold';
                wakeTimeoutId = null;
            }
        }, 3000);
        
        connect();
    } else {
        wsSend({ type: 'ping' });
    }
}
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
        handleResume();
    }
});
window.addEventListener('online', handleResume);


// --- Keys / media ---
function sendKey(key) { wsSend({ type: 'input', device: 'gamepad', action: 'press', key }); if (navigator.vibrate) navigator.vibrate(35); }
function sendMedia(key) { wsSend({ action: 'media_control', parameters: { key } }); if (navigator.vibrate) navigator.vibrate(25); }
function homeAction() { killKiosk(); }

// --- Touchpad pointer & Nav Mode ---
let navMode = (localStorage.getItem('nav_mode') === 'true');
function toggleNavMode() {
    navMode = !navMode;
    localStorage.setItem('nav_mode', navMode);
    updateNavUI();
}
function updateNavUI() {
    const btn = document.getElementById('btn-nav-mode');
    const overlay = document.getElementById('nav-overlay');
    const hint = document.getElementById('nav-hint');
    if (!btn || !overlay) return;
    if (navMode) {
        btn.classList.add('util-active');
        btn.classList.remove('text-gray-400');
        overlay.classList.remove('hidden');
        if (hint && localStorage.getItem('nav_hint_done') !== 'true') {
            hint.classList.remove('opacity-0');
            hint.classList.add('opacity-100');
            setTimeout(() => {
                hint.classList.remove('opacity-100');
                hint.classList.add('opacity-0');
                localStorage.setItem('nav_hint_done', 'true');
            }, 3000);
        }
    } else {
        btn.classList.remove('util-active');
        btn.classList.add('text-gray-400');
        overlay.classList.add('hidden');
        if (hint) {
            hint.classList.remove('opacity-100');
            hint.classList.add('opacity-0');
        }
    }
}
document.addEventListener('DOMContentLoaded', updateNavUI);

const pad = document.getElementById('touchpad');
let padLast = null, padMoved = 0, padDown = 0, accX = 0, accY = 0, rafPending = false;
let navInterval = null, navAxis = null;
const POINTER_SENS = 1.6;

function flushPointer() {
    rafPending = false;
    if (accX || accY) { wsSend({ type: 'pointer', dx: Math.round(accX * POINTER_SENS), dy: Math.round(accY * POINTER_SENS) }); accX = 0; accY = 0; }
}

if (pad) {
    pad.addEventListener('pointerdown', (e) => { 
        pad.setPointerCapture(e.pointerId); 
        padLast = { x: e.clientX, y: e.clientY }; 
        padMoved = 0; 
        padDown = Date.now(); 
        navAxis = null;
        if (navInterval) { clearInterval(navInterval); navInterval = null; }
    });
    pad.addEventListener('pointermove', (e) => {
        if (!padLast) return;
        const dx = e.clientX - padLast.x, dy = e.clientY - padLast.y;
        
        if (navMode) {
            if (!navAxis && (Math.abs(dx) >= 40 || Math.abs(dy) >= 40)) {
                navAxis = Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? 'KEY_RIGHT' : 'KEY_LEFT') : (dy > 0 ? 'KEY_DOWN' : 'KEY_UP');
                sendKey(navAxis);
                if (navigator.vibrate) navigator.vibrate(15);
                padMoved = 100; // prevent tap
                navInterval = setInterval(() => {
                    sendKey(navAxis);
                    if (navigator.vibrate) navigator.vibrate(15);
                }, 300);
            }
        } else {
            padLast = { x: e.clientX, y: e.clientY };
            padMoved += Math.abs(dx) + Math.abs(dy);
            accX += dx; accY += dy;
            if (!rafPending) { rafPending = true; requestAnimationFrame(flushPointer); }
        }
    });
    const padEnd = () => {
        if (navInterval) { clearInterval(navInterval); navInterval = null; }
        if (padLast && padMoved < 10 && (!navMode || !navAxis)) {
            const dur = Date.now() - padDown;
            if (navMode) {
                if (dur < 250) {
                    sendKey('KEY_ENTER');
                    if (navigator.vibrate) navigator.vibrate(20);
                } else if (dur >= 500) {
                    sendKey('KEY_ESC');
                    if (navigator.vibrate) navigator.vibrate([20, 40]);
                }
            } else {
                if (dur < 250) {
                    wsSend({ type: 'pointer', click: 'left' });
                    if (navigator.vibrate) navigator.vibrate(20);
                } else if (dur > 500) {
                    wsSend({ type: 'pointer', click: 'right' });
                    if (navigator.vibrate) navigator.vibrate([20, 40]);
                }
            }
        }
        padLast = null;
    };
    pad.addEventListener('pointerup', padEnd);
    pad.addEventListener('pointercancel', () => { 
        padLast = null; 
        if (navInterval) { clearInterval(navInterval); navInterval = null; } 
    });
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
            wsSend({ type: 'pointer', scroll: scAcc > 0 ? -1 : 1 });
            scAcc += scAcc > 0 ? -SCROLL_STEP : SCROLL_STEP;
        }
    });
    const scEnd = () => { scLast = null; };
    scrollStrip.addEventListener('pointerup', scEnd);
    scrollStrip.addEventListener('pointercancel', scEnd);
}

// --- System keyboard bridge - COR-03 prefix/suffix diff ---
const kbBar = document.getElementById('kb-bar');
const kbInput = document.getElementById('kb-input');
let kbPrev = '';
function openKeyboard() { if (!kbBar) return; kbBar.hidden = false; kbInput.value = ''; kbPrev = ''; kbInput.focus(); }
function closeKeyboard() { if (!kbBar) return; kbInput.blur(); kbBar.hidden = true; }
if (kbInput) {
    kbInput.addEventListener('input', () => {
        const v = kbInput.value;
        let i = 0;
        while (i < kbPrev.length && i < v.length && kbPrev[i] === v[i]) {
            i++;
        }
        const backspaces = kbPrev.length - i;
        const suffix = v.slice(i);

        if (backspaces > 0) {
            for (let b = 0; b < backspaces; b++) {
                wsSend({ type: 'input', device: 'gamepad', action: 'press', key: 'KEY_BACKSPACE' });
            }
        }
        if (suffix.length > 0) {
            wsSend({ type: 'text', text: suffix });
        }
        kbPrev = v;
    });
    kbInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); wsSend({ type: 'input', device: 'gamepad', action: 'press', key: 'KEY_ENTER' }); } });
}

// --- Voice - COR-02 pointer listeners ---
let micHeld = false;
let micStartMs = 0;
let micTimerId = null;
let micDisplayTimerId = null;
let micDiscard = false;

async function startVoice() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) { toast('Captura de audio no soportada (requiere HTTPS).'); return; }
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        if (!micHeld) {
            // Cancelado durante la espera (ej. iOS delay)
            stream.getTracks().forEach(t => t.stop());
            return;
        }
        let mimeType = '';
        if (MediaRecorder.isTypeSupported('audio/webm')) mimeType = 'audio/webm';
        else if (MediaRecorder.isTypeSupported('audio/mp4')) mimeType = 'audio/mp4';
        
        const options = mimeType ? { mimeType } : {};
        mediaRecorder = new MediaRecorder(stream, options);
        mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) audioChunks.push(e.data); };
        mediaRecorder.onstop = () => {
            if (!micDiscard && audioChunks.length > 0) {
                const blob = mimeType ? new Blob(audioChunks, { type: mimeType }) : new Blob(audioChunks);
                if (ws && ws.readyState === WebSocket.OPEN) ws.send(blob);
            }
            audioChunks = [];
            stream.getTracks().forEach((t) => t.stop());
        };
        mediaRecorder.start();
        micDiscard = false;

        const overlay = document.getElementById('mic-overlay');
        const timerEl = document.getElementById('mic-timer');
        if (overlay && timerEl) {
            overlay.classList.remove('hidden');
            overlay.classList.add('flex');
            let secs = 0;
            timerEl.textContent = '00:00';
            micDisplayTimerId = setInterval(() => {
                secs++;
                timerEl.textContent = '00:0' + secs;
            }, 1000);
        }

        micTimerId = setTimeout(() => {
            stopVoice(false);
        }, 8000);

        if (navigator.vibrate) navigator.vibrate(50);
        statusEl.textContent = 'Listening...'; statusEl.className = 'text-blue-400 text-xs font-bold';
    } catch (e) { console.error('Mic denied', e); toast('Error de micrófono: ' + e.name); }
}

function stopVoice(cancel) {
    if (micTimerId) { clearTimeout(micTimerId); micTimerId = null; }
    if (micDisplayTimerId) { clearInterval(micDisplayTimerId); micDisplayTimerId = null; }
    
    const overlay = document.getElementById('mic-overlay');
    if (overlay) {
        overlay.classList.add('hidden');
        overlay.classList.remove('flex');
    }

    if (mediaRecorder && mediaRecorder.state === 'recording') {
        micDiscard = cancel;
        mediaRecorder.stop();
        if (navigator.vibrate && !cancel) navigator.vibrate([40, 40]);
        if (!cancel) {
            statusEl.textContent = 'Processing AI...'; statusEl.className = 'text-purple-400 text-xs font-bold';
        } else {
            statusEl.textContent = 'Cancelado'; statusEl.className = 'text-gray-400 text-xs font-bold';
            setTimeout(() => { if (statusEl.textContent === 'Cancelado') statusEl.textContent = 'Connected'; }, 2000);
        }
    }
}

const micBtn = document.getElementById('mic-btn');
if (micBtn) {
    micBtn.addEventListener('pointerdown', (e) => {
        e.preventDefault();
        micHeld = true;
        micStartMs = Date.now();
        if (mediaRecorder && mediaRecorder.state === 'recording') return;
        startVoice();
    });
    micBtn.addEventListener('pointerup', (e) => {
        e.preventDefault();
        micHeld = false;
        const duration = Date.now() - micStartMs;
        if (duration < 250) {
            stopVoice(true);
            toast('Mantén pulsado para hablar');
        } else {
            stopVoice(false);
        }
    });
    micBtn.addEventListener('pointercancel', (e) => {
        e.preventDefault();
        micHeld = false;
        stopVoice(true);
    });
    micBtn.addEventListener('pointerleave', (e) => {
        if (micHeld) {
            micHeld = false;
            stopVoice(true);
        }
    });
}

// --- App grid (most-used first + more) - SEC-03 XSS DOM construction ---
function getUsage() { try { return JSON.parse(localStorage.getItem('app_usage') || '{}'); } catch (e) { return {}; } }
function bumpUsage(id) { const u = getUsage(); u[id] = (u[id] || 0) + 1; localStorage.setItem('app_usage', JSON.stringify(u)); }
function getCustomApps() { try { return JSON.parse(localStorage.getItem('custom_apps') || '[]'); } catch(e) { return []; } }
function getHiddenApps() { try { return JSON.parse(localStorage.getItem('hidden_apps') || '[]'); } catch(e) { return []; } }

function setTileFavicon(img, domain) {
    const ddg = `https://icons.duckduckgo.com/ip3/${domain}.ico`;
    const s2 = `https://www.google.com/s2/favicons?domain=${domain}&sz=128`;
    
    let step = 0;
    img.onerror = () => {
        step++;
        if (step === 1) {
            img.src = s2;
        } else {
            const div = document.createElement('div');
            div.className = 'w-full h-full flex items-center justify-center text-white font-bold text-xl bg-gray-700 uppercase';
            div.textContent = domain.replace(/^www\./i, '').charAt(0);
            img.replaceWith(div);
        }
    };
    img.onload = () => {
        if (step === 1 && img.naturalWidth <= 16) {
            // s2 default generic icon is usually 16x16
            img.onerror();
        }
    };
    img.src = ddg;
}

function createAppTile(app) {
    const div = document.createElement('div');
    div.className = 'relative flex flex-col items-center gap-1 cursor-pointer active:scale-95';
    div.dataset.url = app.url || '';
    div.dataset.id = app.id || '';
    if (app.is_native) div.dataset.native = 'true';

    const iconWrapper = document.createElement('div');
    iconWrapper.className = 'w-12 h-12 rounded-full overflow-hidden flex items-center justify-center bg-gray-800 shrink-0';

    if (app.is_native && app.id) {
        const img = document.createElement('img');
        img.src = `/api/icon/${app.id}`;
        img.className = 'w-10 h-10 object-contain';
        img.onerror = () => {
            const fb = document.createElement('div');
            fb.className = 'text-gray-300 font-bold text-2xl';
            fb.textContent = app.name ? app.name.charAt(0).toUpperCase() : '?';
            img.replaceWith(fb);
        };
        iconWrapper.appendChild(img);
    } else if (app.url) {
        try {
            const domain = new URL(app.url).hostname;
            const img = document.createElement('img');
            img.className = 'w-full h-full object-cover';
            iconWrapper.appendChild(img);
            setTileFavicon(img, domain);
        } catch(e) {
            const fb = document.createElement('div');
            fb.className = 'text-gray-300 font-bold text-2xl';
            fb.textContent = app.name ? app.name.charAt(0).toUpperCase() : '?';
            iconWrapper.appendChild(fb);
        }
    } else {
        const fb = document.createElement('div');
        fb.className = 'text-gray-300 font-bold text-2xl';
        fb.textContent = app.name ? app.name.charAt(0).toUpperCase() : '?';
        iconWrapper.appendChild(fb);
    }

    const span = document.createElement('span');
    span.className = 'text-[10px] text-gray-300 truncate w-full text-center';
    span.textContent = app.name || '';

    div.appendChild(iconWrapper);
    div.appendChild(span);

    if (app.id && (app.id.startsWith('custom_') || app.is_native)) {
        const delBtn = document.createElement('button');
        delBtn.textContent = '×';
        delBtn.className = 'absolute -top-1 right-2 bg-red-600 hover:bg-red-700 text-white rounded-full w-4 h-4 flex items-center justify-center text-xs font-bold border border-gray-900';
        delBtn.dataset.remove = app.id;
        delBtn.title = 'Eliminar';
        div.appendChild(delBtn);
    } else if (app.id && !app.is_native) {
        const hideBtn = document.createElement('button');
        hideBtn.textContent = '×';
        hideBtn.className = 'absolute -top-1 right-2 bg-gray-600 hover:bg-gray-500 text-white rounded-full w-4 h-4 flex items-center justify-center text-xs font-bold border border-gray-900 opacity-60 hover:opacity-100 transition-opacity';
        hideBtn.dataset.hide = app.id;
        hideBtn.title = 'Ocultar';
        div.appendChild(hideBtn);
    }

    return div;
}

function renderApps(kiosks) {
    const usage = getUsage();
    const customApps = getCustomApps();
    const hiddenApps = getHiddenApps();
    
    const visibleKiosks = kiosks.filter(k => !hiddenApps.includes(k.id));
    const allKiosks = [...customApps, ...visibleKiosks];
    const sorted = allKiosks.sort((a, b) => (usage[b.id] || 0) - (usage[a.id] || 0));

    const row = document.getElementById('apps-row');
    row.innerHTML = '';
    sorted.slice(0, 5).forEach((app) => {
        row.appendChild(createAppTile(app));
    });

    const drawer = document.getElementById('drawer-grid');
    drawer.innerHTML = '';
    sorted.forEach((app) => {
        drawer.appendChild(createAppTile(app));
    });

    
    let restoreBtn = document.getElementById('restore-hidden-apps');
    if (!restoreBtn) {
        restoreBtn = document.createElement('button');
        restoreBtn.id = 'restore-hidden-apps';
        restoreBtn.className = 'text-blue-400 text-sm mt-4 underline text-center w-full block hover:text-blue-300';
        restoreBtn.onclick = () => {
            localStorage.setItem('hidden_apps', '[]');
            renderApps(lastSuggestedKiosks);
            toast('Apps restauradas');
        };
        drawer.parentNode.insertBefore(restoreBtn, drawer.nextSibling);
    }
    
    if (hiddenApps.length > 0) {
        restoreBtn.textContent = `Restablecer apps ocultas (${hiddenApps.length})`;
        restoreBtn.style.display = 'block';
    } else {
        restoreBtn.style.display = 'none';
    }
}

function handleAppLaunchClick(e) {
    const removeBtn = e.target.closest('[data-remove]');
    if (removeBtn) {
        e.stopPropagation();
        e.preventDefault();
        const removeId = removeBtn.dataset.remove;
        let customApps = getCustomApps();
        customApps = customApps.filter(app => app.id !== removeId);
        localStorage.setItem('custom_apps', JSON.stringify(customApps));
        renderApps(lastSuggestedKiosks);
        toast('Aplicación eliminada');
        return;
    }

    const hideBtn = e.target.closest('[data-hide]');
    if (hideBtn) {
        e.stopPropagation();
        e.preventDefault();
        const hideId = hideBtn.dataset.hide;
        let hidden = getHiddenApps();
        if (!hidden.includes(hideId)) {
            hidden.push(hideId);
            localStorage.setItem('hidden_apps', JSON.stringify(hidden));
        }
        renderApps(lastSuggestedKiosks);
        toast('App oculta');
        return;
    }

    const tile = e.target.closest('[data-id]');
    if (tile) {
        const id = tile.dataset.id;
        if (tile.dataset.native === 'true') {
            launchNativeApp(id);
        } else if (tile.dataset.url) {
            launchKiosk(tile.dataset.url, id);
        }
    }
}
document.getElementById('apps-row').addEventListener('click', handleAppLaunchClick);
document.getElementById('drawer-grid').addEventListener('click', handleAppLaunchClick);

function toggleMore() { const m = document.getElementById('apps-more'); if (m) m.hidden = !m.hidden; }

async function fetchApps() {
    try {
        const res = await fetch(`${apiUrl}/apps`, {
            headers: { 'X-Auth-Token': token }
        });
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();
        lastSuggestedKiosks = data.suggested_kiosks || [];
        const voiceList = document.getElementById('voice-apps-list');
        if (voiceList) {
            voiceList.innerText = lastSuggestedKiosks.map(k => k.name || k.id).join(', ');
        }
        renderApps(lastSuggestedKiosks);
        renderNativeList(data.installed_apps || []);
    } catch (e) { console.error('Failed to load apps:', e); }
}

async function launchKiosk(url, id) {
    if (id) bumpUsage(id);
    if (navigator.vibrate) navigator.vibrate(80);
    toast('Abriendo aplicación...');
    try {
        const res = await fetch(`${apiUrl}/kiosk/launch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-Auth-Token': token },
            body: JSON.stringify({ url })
        });
        if (!res.ok) throw new Error('HTTP ' + res.status);
        toast('Aplicación abierta');
    } catch (e) {
        console.error('Launch error:', e);
        toast('Error al abrir la aplicación');
    }
}

async function killKiosk() {
    if (navigator.vibrate) navigator.vibrate([50, 50, 50]);
    toast('Cerrando aplicación...');
    try {
        const res = await fetch(`${apiUrl}/kiosk/kill`, {
            method: 'POST',
            headers: { 'X-Auth-Token': token }
        });
        if (!res.ok) throw new Error('HTTP ' + res.status);
        toast('Aplicación cerrada');
    } catch (e) {
        console.error('Kill error:', e);
        toast('Error al cerrar la aplicación');
    }
}

async function showPanel() {
    if (navigator.vibrate) navigator.vibrate(50);
    toast('Abriendo panel...');
    try {
        const res = await fetch(`${apiUrl}/panel/show`, {
            method: 'POST',
            headers: { 'X-Auth-Token': token }
        });
        if (!res.ok) throw new Error('HTTP ' + res.status);
        toast('Panel abierto en TV');
    } catch (e) {
        console.error('Show panel error:', e);
        toast('Error al abrir el panel');
    }
}

function sendCombo(name) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'combo', name: name }));
        if (navigator.vibrate) navigator.vibrate(30);
    }
}

// Long press for close app
const btnCloseApp = document.getElementById('btn-close-app');
if (btnCloseApp) {
    let pressTimer;
    const startPress = (e) => {
        if (e.type !== 'mousedown') e.preventDefault(); // allow touch
        pressTimer = setTimeout(() => {
            sendCombo('close_window');
            toast('App cerrada (Alt+F4)');
            if (navigator.vibrate) navigator.vibrate([100, 50, 100]);
        }, 800); // 800ms long press
    };
    const cancelPress = () => {
        clearTimeout(pressTimer);
    };
    btnCloseApp.addEventListener('pointerdown', startPress);
    btnCloseApp.addEventListener('pointerup', (e) => {
        cancelPress();
        if (e.pointerType === 'touch' || e.type === 'pointerup') {
            toast('Mantén pulsado para cerrar la app');
        }
    });
    btnCloseApp.addEventListener('pointercancel', cancelPress);
    btnCloseApp.addEventListener('pointerleave', cancelPress);
}

// --- Native apps SEC-03 delegated listener ---
function renderNativeList(apps) {
    const container = document.getElementById('native-list');
    if (!container) return;
    container.innerHTML = '';

    apps.forEach((app) => {
        const div = document.createElement('div');
        div.className = 'flex justify-between items-center skin-bg-btn p-2 rounded';

        const nameSpan = document.createElement('span');
        nameSpan.className = 'text-xs truncate flex-1 skin-text-main';
        nameSpan.textContent = app.name;

        const btnContainer = document.createElement('div');
        btnContainer.className = 'flex gap-2';

        const addBtn = document.createElement('button');
        addBtn.className = 'skin-bg-panel px-3 py-1 rounded text-xs font-bold skin-text-main';
        addBtn.textContent = '+ Añadir';
        addBtn.onclick = () => {
            const customApps = getCustomApps();
            if (!customApps.some(a => a.id === app.id)) {
                customApps.push({
                    id: app.id,
                    name: app.name,
                    is_native: true,
                    color: '#10b981'
                });
                localStorage.setItem('custom_apps', JSON.stringify(customApps));
                renderApps(lastSuggestedKiosks);
                toast('Añadido a favoritos');
            } else {
                toast('Ya está en favoritos');
            }
        };

        const btn = document.createElement('button');
        btn.className = 'skin-accent px-3 py-1 rounded text-xs font-bold text-white shadow-sm';
        btn.textContent = 'Abrir';
        btn.dataset.id = app.id;

        btnContainer.appendChild(addBtn);
        btnContainer.appendChild(btn);

        div.appendChild(nameSpan);
        div.appendChild(btnContainer);
        container.appendChild(div);
    });
}
document.getElementById('native-list').addEventListener('click', (e) => {
    const btn = e.target.closest('button[data-id]');
    if (btn) {
        launchNativeApp(btn.dataset.id);
    }
});

async function launchNativeApp(id) {
    if (navigator.vibrate) navigator.vibrate(100);
    toast('Abriendo aplicación nativa...');
    try {
        const res = await fetch(`${apiUrl}/app/launch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-Auth-Token': token },
            body: JSON.stringify({ id })
        });
        if (!res.ok) throw new Error('HTTP ' + res.status);
        toast('Aplicación nativa abierta');
    } catch (e) {
        console.error('App launch error:', e);
        toast('Error al abrir la aplicación nativa');
    }
}

function addCustomApp() {
    const nameInput = document.getElementById('new-app-name');
    const urlInput = document.getElementById('new-app-url');
    const name = nameInput.value.trim();
    const urlStr = urlInput.value.trim();

    if (!name || !urlStr) {
        toast('Por favor, rellena todos los campos.');
        return;
    }

    try {
        const url = new URL(urlStr);
        if (url.protocol !== 'http:' && url.protocol !== 'https:') {
            throw new Error('Protocolo no soportado');
        }
    } catch (err) {
        toast('Por favor, introduce una URL válida (http/https).');
        return;
    }

    const customApps = getCustomApps();
    const newId = 'custom_' + Date.now();
    customApps.push({ id: newId, name, url: urlStr, color: '#3b82f6' });
    localStorage.setItem('custom_apps', JSON.stringify(customApps));

    nameInput.value = '';
    urlInput.value = '';
    fetchApps();
}

// --- Settings and Token save ---
function openSettings() {
    const d = document.getElementById('settings-drawer');
    if (d) d.classList.add('open');
}
function closeSettings() {
    const d = document.getElementById('settings-drawer');
    if (d) d.classList.remove('open');
}
function openDrawer() {
    const d = document.getElementById('app-drawer');
    if (d) d.classList.add('open');
    const panel = document.getElementById('add-panel');
    if (panel) panel.style.display = 'block';
}
function closeDrawer() {
    const d = document.getElementById('app-drawer');
    if (d) d.classList.remove('open');
}
function comingSoon() {
    toast('Esta sección estará disponible próximamente.');
}



async function activateLicenseKey(force = false) {
    const input = document.getElementById('license-input');
    if (!input) return;
    const key = input.value.trim();
    if (!key) {
        toast('Por favor, ingresa una clave de licencia.');
        return;
    }
    toast('Activando licencia...');
    try {
        const res = await fetch(`${apiUrl}/license/activate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Auth-Token': token
            },
            body: JSON.stringify({ key, force })
        });
        if (res.ok) {
            toast('Licencia activada con éxito. Actualizando...');
            input.value = '';
            setTimeout(() => {
                fetchLicenseStatus();
            }, 1000);
        } else if (res.status === 409) {
            const move = confirm('Esta licencia está activa en otro dispositivo. ¿Mudarla aquí? El otro dispositivo perderá el premium.');
            if (move) {
                await activateLicenseKey(true);
            } else {
                toast('Activación cancelada.');
            }
        } else {
            const err = await res.json();
            toast(`Error: ${err.detail || 'Clave inválida'}`);
        }
    } catch (err) {
        console.error('Failed to activate license:', err);
        toast('Error de red al activar licencia.');
    }
}

let licenseConflictPrompted = false;
async function handleLicenseConflict() {
    if (licenseConflictPrompted) return;
    licenseConflictPrompted = true;
    const move = confirm('Tu licencia está activa en otro dispositivo. ¿Mudarla aquí? El otro dispositivo perderá el premium.');
    if (move) {
        try {
            const res = await fetch(`${apiUrl}/license/takeover`, {
                method: 'POST',
                headers: { 'X-Auth-Token': token }
            });
            if (res.ok) {
                toast('Licencia mudada a este dispositivo. Probá la voz de nuevo.');
            } else {
                toast('No se pudo mudar la licencia.');
            }
        } catch (err) {
            console.error('Takeover failed:', err);
            toast('Error de red al mudar la licencia.');
        }
    }
    setTimeout(() => { licenseConflictPrompted = false; }, 10000);
}

async function checkUpdate() {
    const btn = document.getElementById('update-btn');
    if (!btn) return;

    if (latestUpdateVersion) {
        applyUpdate();
        return;
    }

    toast('Buscando actualizaciones...');
    try {
        const res = await fetch(`${apiUrl}/update/check`, {
            headers: { 'X-Auth-Token': token }
        });
        if (res.ok) {
            const data = await res.json();
            if (data.update_available) {
                latestUpdateVersion = data.latest;
                btn.textContent = `Actualizar a v${data.latest}`;
                btn.className = 'bg-green-600 px-3 py-1 rounded text-xs font-bold active:bg-green-500';
                toast(`Actualización disponible: v${data.latest}`);
            } else {
                toast('La app está actualizada');
            }
        } else {
            toast('Error al comprobar actualizaciones');
        }
    } catch (err) {
        console.error(err);
        toast('Error de conexión');
    }
}

async function applyUpdate() {
    toast('Aplicando actualización...');
    try {
        const res = await fetch(`${apiUrl}/update/apply`, {
            method: 'POST',
            headers: { 'X-Auth-Token': token }
        });
        if (res.ok) {
            toast('Actualizando... la app se reconectará sola');
            closeSettings();
        } else {
            toast('Error al aplicar actualización');
        }
    } catch (err) {
        console.error(err);
        toast('Error de conexión');
    }
}

function buyLicense() {
    window.open(buyUrl, '_blank');
}

const WEBSITE_URL = 'https://linux-remote-player.vercel.app/';

function shareApp() {
    const shareData = {
        title: 'LinuxRemotePlayer',
        text: '🎬 Convertí mi PC Linux en una Smart TV con control remoto desde el móvil. Touchpad, teclado, apps y voz. Mirá:',
        url: WEBSITE_URL
    };
    if (navigator.share) {
        navigator.share(shareData).catch(() => {});
    } else {
        const text = `${shareData.text} ${shareData.url}`;
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(() => {
                toast('Enlace copiado — pégalo donde quieras');
            }).catch(() => {
                toast('No se pudo copiar el enlace automáticamente');
            });
        } else {
            toast('Compartir no soportado en este dispositivo');
        }
    }
}

async function sendFeedback() {
    const msgEl = document.getElementById('feedback-msg');
    const emailEl = document.getElementById('feedback-email');
    if (!msgEl) return;
    const msg = msgEl.value.trim();
    if (!msg) {
        toast('El mensaje está vacío');
        return;
    }
    
    toast('Enviando...');
    try {
        const res = await fetch('https://tbijfdbtauzxbsbkujbs.functions.supabase.co/send-feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: msg,
                email: emailEl ? emailEl.value.trim() : '',
                version: '1.4.0'
            })
        });
        if (!res.ok) throw new Error('HTTP ' + res.status);
        toast('Feedback enviado. ¡Gracias!');
        msgEl.value = '';
        if (emailEl) emailEl.value = '';
    } catch(e) {
        toast('Feedback enviado.'); 
        msgEl.value = '';
    }
}

function showTour() {
    if (localStorage.getItem('tour_done')) return;
    
    const overlay = document.createElement('div');
    overlay.className = 'fixed inset-0 z-[100] flex flex-col items-center justify-center pointer-events-auto transition-opacity duration-300';
    
    const steps = [
        { text: "Tus apps favoritas — un toque y se abren en la TV", highlightId: "apps-row" },
        { text: "Desliza para mover el puntero. El botón cruceta lo convierte en flechas", highlightId: "touchpad" },
        { text: "Multimedia, volumen, Atrás y Home", highlightId: "control-cluster" },
        { text: "Todo lo demás vive en Ajustes — incluidos los tutoriales", highlightId: "btn-settings" }
    ];
    
    let currentStep = 0;
    
    const box = document.createElement('div');
    box.className = 'bg-gray-800 text-white rounded-xl p-4 m-4 max-w-sm w-[90%] shadow-2xl border border-gray-600 relative z-10 transition-all';
    
    const textEl = document.createElement('p');
    textEl.className = 'text-sm font-bold mb-4';
    
    const flexBtn = document.createElement('div');
    flexBtn.className = 'flex justify-between items-center';
    
    const skipBtn = document.createElement('button');
    skipBtn.textContent = 'Saltar';
    skipBtn.className = 'text-gray-400 text-xs font-bold px-2 py-1';
    
    const nextBtn = document.createElement('button');
    nextBtn.className = 'bg-blue-600 hover:bg-blue-500 px-4 py-1.5 rounded-lg text-sm font-bold text-white';
    
    flexBtn.appendChild(skipBtn);
    flexBtn.appendChild(nextBtn);
    box.appendChild(textEl);
    box.appendChild(flexBtn);
    
    const highlight = document.createElement('div');
    highlight.className = 'absolute rounded-xl pointer-events-none transition-all duration-300 ring-2 ring-blue-500 shadow-[0_0_0_9999px_rgba(0,0,0,0.8)]';
    highlight.style.zIndex = '-1';
    
    overlay.appendChild(highlight);
    overlay.appendChild(box);
    document.body.appendChild(overlay);
    
    function renderStep() {
        if (currentStep >= steps.length) {
            finishTour();
            return;
        }
        const s = steps[currentStep];
        textEl.textContent = s.text;
        nextBtn.textContent = currentStep === steps.length - 1 ? 'Terminar' : 'Siguiente';
        
        const target = document.getElementById(s.highlightId);
        if (!target) {
            currentStep++;
            renderStep();
            return;
        }
        updatePosition();
    }
    
    function updatePosition() {
        if (currentStep >= steps.length) return;
        const s = steps[currentStep];
        const target = document.getElementById(s.highlightId);
        if (target) {
            const rect = target.getBoundingClientRect();
            highlight.style.left = (rect.left - 4) + 'px';
            highlight.style.top = (rect.top - 4) + 'px';
            highlight.style.width = (rect.width + 8) + 'px';
            highlight.style.height = (rect.height + 8) + 'px';
            
            const spaceAbove = rect.top;
            const spaceBelow = window.innerHeight - rect.bottom;
            
            // Elegir el lado con más espacio disponible
            if (spaceBelow > spaceAbove) {
                box.style.marginTop = Math.max(0, rect.bottom + 20) + 'px';
                box.style.marginBottom = '0';
                overlay.style.justifyContent = 'flex-start';
            } else {
                box.style.marginTop = '0';
                box.style.marginBottom = Math.max(0, window.innerHeight - rect.top + 20) + 'px';
                overlay.style.justifyContent = 'flex-end';
            }
        }
    }
    
    const ro = new ResizeObserver(() => updatePosition());
    ro.observe(document.body);
    
    function finishTour() {
        localStorage.setItem('tour_done', 'true');
        overlay.style.opacity = '0';
        ro.disconnect();
        setTimeout(() => overlay.remove(), 300);
    }
    
    nextBtn.onclick = () => { currentStep++; renderStep(); };
    skipBtn.onclick = finishTour;
    
    setTimeout(renderStep, 100);
}

function relaunchTour() {
    localStorage.removeItem('tour_done');
    closeSettings();
    showTour();
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
            + '<p class="text-gray-300 max-w-sm">Abre Remote Linux Player desde el icono de tu pantalla de inicio.</p></div>';
    }
});

const isMobile = /android|iphone|ipad|ipod/i.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);

function showPairingScreen(show) {
    const appUI = document.getElementById('app-ui');
    const pairingUI = document.getElementById('pairing-prompt-ui');
    if (appUI) appUI.style.display = show ? 'none' : 'flex';
    if (pairingUI) pairingUI.hidden = !show;
}

async function checkPinInput(input) {
    input.value = input.value.replace(/[^0-9]/g, '');
    const errorMsg = document.getElementById('pin-error-msg');
    if (errorMsg) errorMsg.classList.add('hidden');

    if (input.value.length === 6) {
        input.disabled = true;
        try {
            const res = await fetch(`${apiUrl}/pair`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pin: input.value })
            });
            const data = await res.json();
            if (res.ok && data.token) {
                await handlePairingSuccess(data.token);
                input.value = '';
            } else {
                if (errorMsg) {
                    errorMsg.textContent = data.detail || 'PIN incorrecto';
                    errorMsg.classList.remove('hidden');
                }
                if (res.status === 401) input.value = '';
            }
        } catch (e) {
            if (errorMsg) {
                errorMsg.textContent = 'Error de conexión';
                errorMsg.classList.remove('hidden');
            }
        } finally {
            input.disabled = false;
            if (input.value.length < 6) input.focus();
        }
    }
}

async function handlePairingSuccess(val) {
    if (!val) return;
    localStorage.setItem('license_token', val);
    await setDBToken(val);
    token = val;
    
    toast('Dispositivo emparejado con éxito');
    showPairingScreen(false);

    // Always connect after onboarding; activate any pending license afterwards.
    fetchConfig().then(() => {
        connect();
        fetchApps();
    });
    const pending = localStorage.getItem('pending_license');
    if (pending) {
        localStorage.removeItem('pending_license');
        setTimeout(async () => {
            const input = document.getElementById('license-input');
            if (input) input.value = pending;
            await activateLicenseKey();
        }, 1200);
    }
}

initToken().then(() => {
    const licenseInput = document.getElementById('license-input');
    if (licenseInput) {
        licenseInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                activateLicenseKey();
            }
        });
    }

    if (!isStandalone && isMobile) {
        showInstallScreen();
    } else {
        if (token === 'guest') {
            showPairingScreen(true);
        } else {
            showPairingScreen(false);
            fetchConfig().then(() => {
                connect();
                fetchApps();
            });
        }
    }
});

function updateAppHeight() {
    const h = window.visualViewport ? window.visualViewport.height : window.innerHeight;
    document.documentElement.style.setProperty('--app-h', h + 'px');
}
window.addEventListener('load', updateAppHeight);
window.addEventListener('resize', updateAppHeight);
window.addEventListener('orientationchange', updateAppHeight);
window.addEventListener('pageshow', updateAppHeight);
if (window.visualViewport) {
    window.visualViewport.addEventListener('resize', updateAppHeight);
}
updateAppHeight();
