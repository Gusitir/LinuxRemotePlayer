const statusEl = {
    get textContent() {
        const el = document.getElementById('status');
        return el ? el.textContent : '';
    },
    set textContent(val) {
        const el = document.getElementById('status');
        const s = String(val != null ? val : '');
        const displayVal = (s === 'Connected' ? 'Stable' : s);
        if (el) el.textContent = displayVal;
        const icon = document.getElementById('conn-icon');
        if (icon) {
            if (s === 'Connected' || s === 'Stable') icon.className = 'text-emerald-400';
            else if (s.includes('Reconnecting') || s.includes('Reconectando') || s.includes('Error') || s.includes('No autorizado')) icon.className = 'text-red-500';
            else if (s.includes('Conectando')) icon.className = 'text-yellow-400';
            else if (s.includes('Listening') || s.includes('Processing')) icon.className = 'text-purple-400';
        }
    },
    get className() {
        const el = document.getElementById('status');
        return el ? el.className : '';
    },
    set className(val) {
        const el = document.getElementById('status');
        if (el) el.className = val;
    }
};
let lastLongPressTime = 0;
let ws;

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
}

const port = window.location.port || '8000';
// WS: drop token from URL - SEC-06
const wsUrl = `${protocol}${host}:${port}/ws`;
const apiUrl = `${window.location.protocol}//${host}:${port}/api`;

let connectAttempts = 0;
let retryTimeoutId = null; // HYG-02: prevent storm reconnects
let hostname = '';

const DEFAULT_SKIN = 'day';
const SKINS = ['day', 'night', 'cafe', 'anime'];
// Ids anteriores a v1.9 -> equivalente en la paleta nueva. 'dark' ahora es 'night'.
const LEGACY_SKINS = { neon: 'night', dark: 'night' };
const SKIN_THEME_COLOR = {
    day: '#f6f2ea',
    night: '#070A0E',
    cafe: '#261b12',
    anime: '#111827'
};

function updateSkinSwatches(activeSkin) {
    document.querySelectorAll('.skin-swatch').forEach(btn => {
        const skinId = btn.dataset.skin || (btn.getAttribute('onclick') || '').match(/setSkin\(['"]([^'"]+)['"]\)/)?.[1];
        if (skinId === activeSkin) {
            btn.classList.add('active');
            btn.setAttribute('aria-selected', 'true');
            const check = btn.querySelector('.skin-swatch-check');
            if (check) check.classList.remove('hidden');
        } else {
            btn.classList.remove('active');
            btn.setAttribute('aria-selected', 'false');
            const check = btn.querySelector('.skin-swatch-check');
            if (check) check.classList.add('hidden');
        }
    });
}

function setSkin(skin) {
    if (LEGACY_SKINS[skin]) skin = LEGACY_SKINS[skin];
    if (SKINS.indexOf(skin) === -1) {
        skin = DEFAULT_SKIN;
    }
    document.documentElement.setAttribute('data-skin', skin);
    localStorage.setItem('lrp_skin', skin);
    const themeMeta = document.querySelector('meta[name="theme-color"]');
    if (themeMeta) themeMeta.setAttribute('content', SKIN_THEME_COLOR[skin]);
    updateSkinSwatches(skin);
}

// Aplicación inmediata de skin al cargar script
const initialSkin = localStorage.getItem('lrp_skin') || DEFAULT_SKIN;
setSkin(initialSkin);

async function fetchConfig() {
    try {
        const res = await fetch(`${apiUrl}/config`);
        if (res.ok) {
            const data = await res.json();
            hostname = data.hostname || '';

            const footerVer = document.getElementById('app-version-footer');
            if (footerVer) footerVer.textContent = `${data.version || '1.0.0'} — LinuxRemotePlayer`;
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
        statusEl.textContent = 'Stable';
        statusEl.className = 'text-emerald-400 font-medium';

        // SEC-06: WebSocket auth frame
        ws.send(JSON.stringify({ type: 'auth', token: token }));

        startHeartbeat();
    };
    ws.onclose = (event) => {
        stopHeartbeat();
        const latencyEl = document.getElementById('latency');
        if (latencyEl) {
            latencyEl.textContent = 'Latency: --ms';
            latencyEl.className = 'text-[10px] font-mono text-gray-400';
        }
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
                if (heartbeatTimeoutId) {
                    clearTimeout(heartbeatTimeoutId);
                    heartbeatTimeoutId = null;
                }
                lastPong = Date.now();
                if (lastPingSent > 0) {
                    const rtt = lastPong - lastPingSent;
                    const latencyEl = document.getElementById('latency');
                    if (latencyEl) {
                        latencyEl.textContent = 'Latency: ' + rtt + 'ms';
                        latencyEl.className = 'text-[10px] font-mono ' + (rtt < 60 ? 'text-emerald-400' : (rtt < 150 ? 'text-yellow-400' : 'text-red-500'));
                        latencyEl.classList.remove('hidden');
                    }
                }
            } else if (res.status === 'processing') {
                statusEl.textContent = res.message;
                statusEl.className = 'text-purple-400 text-xs font-bold';
            } else if (res.status === 'success' || res.status === 'error') {
                statusEl.textContent = res.status === 'error' ? `Error: ${res.message}` : 'Connected';
                statusEl.className = res.status === 'error' ? 'text-red-500 text-xs font-bold' : 'text-green-500 text-xs font-bold';
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
            if (heartbeatTimeoutId) clearTimeout(heartbeatTimeoutId);
            heartbeatTimeoutId = setTimeout(() => {
                if (Date.now() - lastPong > 8000) {
                    console.warn('Heartbeat timeout, closing connection.');
                    ws.close();
                }
            }, 8000);
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
let isMediaPlaying = false;

function updatePlayStateUI() {
    const heroBtn = document.getElementById('btn-hero-play');
    const heroPlay = document.getElementById('hero-vector-play');
    const heroPause = document.getElementById('hero-vector-pause');
    const heroOk = document.getElementById('hero-vector-ok');
    const heroIcon = document.getElementById('hero-center-icon');

    if (!heroBtn) return;

    if (navMode) {
        if (heroPlay) heroPlay.classList.add('hidden');
        if (heroPause) heroPause.classList.add('hidden');
        if (heroOk) heroOk.classList.remove('hidden');
        heroBtn.classList.remove('is-playing');
        heroBtn.setAttribute('title', 'Confirmar (Enter)');
        if (heroIcon) heroIcon.textContent = 'OK';
        return;
    }

    if (heroOk) heroOk.classList.add('hidden');

    if (isMediaPlaying) {
        if (heroPlay) heroPlay.classList.add('hidden');
        if (heroPause) heroPause.classList.remove('hidden');
        heroBtn.classList.add('is-playing');
        heroBtn.setAttribute('title', 'Pausar (Espacio)');
        if (heroIcon) heroIcon.textContent = '⏸';
    } else {
        if (heroPlay) heroPlay.classList.remove('hidden');
        if (heroPause) heroPause.classList.add('hidden');
        heroBtn.classList.remove('is-playing');
        heroBtn.setAttribute('title', 'Reproducir (Espacio)');
        if (heroIcon) heroIcon.textContent = '▶';
    }
}

function toggleNavMode() {
    navMode = !navMode;
    localStorage.setItem('nav_mode', navMode);
    updateNavUI();
}

function onHeroCenterPress() {
    if (navigator.vibrate) navigator.vibrate(35);
    const heroBtn = document.getElementById('btn-hero-play');
    if (heroBtn) {
        heroBtn.classList.add('pressed');
        setTimeout(() => heroBtn.classList.remove('pressed'), 180);
    }
    if (navMode) {
        sendKey('KEY_ENTER');
    } else {
        isMediaPlaying = !isMediaPlaying;
        sendKey('KEY_SPACE');
        updatePlayStateUI();
    }
}

function updateNavUI() {
    const btn = document.getElementById('btn-nav-mode');
    const overlay = document.getElementById('nav-overlay');
    const hint = document.getElementById('nav-hint');

    updatePlayStateUI();

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
document.addEventListener('DOMContentLoaded', () => {
    updateNavUI();
    renderQuickDock();

    const heroBtn = document.getElementById('btn-hero-play');
    if (heroBtn) {
        const pressStart = () => heroBtn.classList.add('pressed');
        const pressEnd = () => heroBtn.classList.remove('pressed');
        heroBtn.addEventListener('pointerdown', pressStart);
        heroBtn.addEventListener('pointerup', pressEnd);
        heroBtn.addEventListener('pointercancel', pressEnd);
        heroBtn.addEventListener('pointerleave', pressEnd);
    }
});

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
const scrollThumb = document.getElementById('scroll-thumb');
let scLast = null, scAcc = 0;
const SCROLL_STEP = 18;
if (scrollStrip) {
    scrollStrip.addEventListener('pointerdown', (e) => {
        scrollStrip.setPointerCapture(e.pointerId);
        scLast = e.clientY;
        scAcc = 0;
        if (scrollThumb) {
            scrollThumb.classList.add('active');
        }
    });
    scrollStrip.addEventListener('pointermove', (e) => {
        if (scLast === null) return;
        const delta = e.clientY - scLast;
        scAcc += delta;
        scLast = e.clientY;
        if (scrollThumb) {
            const rect = scrollStrip.getBoundingClientRect();
            const relY = Math.max(0, Math.min(rect.height - 24, e.clientY - rect.top - 12));
            scrollThumb.style.transform = `translateY(${relY - (rect.height / 2 - 12)}px)`;
        }
        while (Math.abs(scAcc) >= SCROLL_STEP) {
            wsSend({ type: 'pointer', scroll: scAcc > 0 ? -1 : 1 });
            scAcc += scAcc > 0 ? -SCROLL_STEP : SCROLL_STEP;
        }
    });
    const scEnd = () => {
        scLast = null;
        if (scrollThumb) {
            scrollThumb.classList.remove('active');
            scrollThumb.style.transform = 'translateY(0px)';
        }
    };
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
            div.className = 'w-full h-full flex items-center justify-center skin-text-on-accent font-bold text-xl skin-accent uppercase';
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

let activeKioskAppId = null;
let activeKioskUrl = null;

const BUILTIN_APPS_MAP = {
    netflix: { id: 'netflix', name: 'Netflix', url: 'https://netflix.com', category: 'video', color: '#E50914', iconText: 'Netflix' },
    youtube: { id: 'youtube', name: 'YouTube', url: 'https://youtube.com/tv', category: 'video', color: '#FF0000', iconText: 'YouTube' },
    spotify: { id: 'spotify', name: 'Spotify', url: 'https://open.spotify.com', category: 'music', color: '#1DB954', iconText: 'Spotify' },
    animeav1: { id: 'animeav1', name: 'AnimeAV1', url: 'https://animeav1.com', category: 'video', color: '#7C3AED', iconText: 'AV1' },
    stremio: { id: 'stremio', name: 'Stremio', url: 'https://web.stremio.com', category: 'video', color: '#6A38A0', iconText: 'Stremio' },
    animeflv: { id: 'animeflv', name: 'AnimeFLV', url: 'https://www3.animeflv.net', category: 'video', color: '#EA580C', iconText: 'FLV' },
    crunchyroll: { id: 'crunchyroll', name: 'Crunchyroll', url: 'https://www.crunchyroll.com', category: 'video', color: '#F47521', iconText: 'CR' },
    youtubetv: { id: 'youtubetv', name: 'YouTube TV', url: 'https://tv.youtube.com', category: 'video', color: '#FF0000', iconText: 'YT TV' },
    disneyplus: { id: 'disneyplus', name: 'Disney+', url: 'https://www.disneyplus.com', category: 'video', color: '#113CCF', iconText: 'D+' },
    primevideo: { id: 'primevideo', name: 'Prime Video', url: 'https://www.primevideo.com', category: 'video', color: '#00A8E1', iconText: 'Prime' },
    plutotv: { id: 'plutotv', name: 'Pluto TV', url: 'https://pluto.tv', category: 'video', color: '#FFD700', iconText: 'Pluto' },
    twitch: { id: 'twitch', name: 'Twitch', url: 'https://www.twitch.tv', category: 'web', color: '#9146FF', iconText: 'Twitch' },
    kick: { id: 'kick', name: 'Kick', url: 'https://kick.com', category: 'web', color: '#53FC18', iconText: 'Kick' },
    appletv: { id: 'appletv', name: 'Apple TV+', url: 'https://tv.apple.com', category: 'video', color: '#1C1C1E', iconText: 'TV+' },
    kodi: { id: 'kodi', name: 'Kodi', url: 'https://kodi.tv', category: 'video', color: '#17B2E7', iconText: 'Kodi' },
    retroarch: { id: 'retroarch', name: 'RetroArch', url: 'https://web.retroarch.com', category: 'web', color: '#333333', iconText: 'Retro' },
    tiktok: { id: 'tiktok', name: 'TikTok', url: 'https://www.tiktok.com', category: 'web', color: '#010101', iconText: 'TikTok' },
    hbomax: { id: 'hbomax', name: 'Max', url: 'https://play.max.com', category: 'video', color: '#002BE7', iconText: 'Max' }
};

const APP_CATALOG_PRESETS = Object.values(BUILTIN_APPS_MAP);

function normalizeUrl(url) {
    if (!url) return '';
    try {
        const u = new URL(url);
        let host = u.hostname.toLowerCase().replace(/^www\./, '');
        let path = u.pathname.replace(/\/+$/, '');
        return `${host}${path}`;
    } catch (e) {
        return String(url).toLowerCase().trim().replace(/^https?:\/\//, '').replace(/^www\./, '').replace(/\/+$/, '');
    }
}

function getCanonicalAppKey(app) {
    if (!app) return '';
    const id = (app.id || '').toLowerCase().trim();
    if (id === 'disney' || id === 'disneyplus') return 'disneyplus';
    if (id === 'youtube' || id === 'yt') return 'youtube';
    if (id === 'youtubetv' || id === 'youtube_tv' || id === 'yt-tv' || id === 'yt_tv') return 'youtubetv';
    if (id === 'hbomax' || id === 'max') return 'hbomax';
    if (id === 'spotify') return 'spotify';
    if (id === 'tiktok') return 'tiktok';
    if (id === 'animeav1') return 'animeav1';
    if (id === 'animeflv') return 'animeflv';
    if (id === 'crunchyroll') return 'crunchyroll';
    if (id === 'stremio') return 'stremio';
    if (id === 'primevideo' || id === 'prime') return 'primevideo';
    if (id === 'plutotv' || id === 'pluto') return 'plutotv';
    if (id === 'twitch') return 'twitch';
    if (id === 'kick') return 'kick';
    if (id === 'appletv' || id === 'apple_tv') return 'appletv';
    if (id === 'kodi') return 'kodi';
    if (id === 'retroarch') return 'retroarch';

    if (BUILTIN_APPS_MAP[id]) return id;

    // Match by URL against builtin apps
    if (app.url) {
        const normUrl = normalizeUrl(app.url);
        for (const [bId, bApp] of Object.entries(BUILTIN_APPS_MAP)) {
            if (bApp.url && normalizeUrl(bApp.url) === normUrl) {
                return bId;
            }
        }
    }

    // Match by Name against builtin apps
    const normName = (app.name || '').toLowerCase().replace(/[^a-z0-9]/g, '');
    for (const [bId, bApp] of Object.entries(BUILTIN_APPS_MAP)) {
        const bName = (bApp.name || '').toLowerCase().replace(/[^a-z0-9]/g, '');
        if (normName && (normName === bName || normName.includes(bName) || bName.includes(normName))) {
            return bId;
        }
    }

    return id;
}

const DEFAULT_PINNED_APPS = ['netflix', 'youtube', 'spotify'];

function getPinnedApps() {
    try {
        const val = localStorage.getItem('lrp_pinned_apps');
        if (val !== null) {
            const parsed = JSON.parse(val);
            if (Array.isArray(parsed)) {
                return Array.from(new Set(parsed.map(id => getCanonicalAppKey({ id })).filter(Boolean)));
            }
        }
    } catch(e) {}
    return [...DEFAULT_PINNED_APPS];
}

function setPinnedApps(pinned) {
    try {
        const deduped = Array.from(new Set((pinned || []).map(id => getCanonicalAppKey({ id })).filter(Boolean)));
        localStorage.setItem('lrp_pinned_apps', JSON.stringify(deduped));
    } catch(e) {}
}

function isAppPinned(id) {
    const canonId = getCanonicalAppKey({ id });
    return getPinnedApps().includes(canonId);
}

function updateAppPinBadges() {
    const pinned = getPinnedApps();
    document.querySelectorAll('#drawer-grid [data-id]').forEach(tile => {
        const id = tile.dataset.id;
        const canonId = getCanonicalAppKey({ id });
        const card = tile.querySelector('.squircle-card');
        if (!card) return;
        const existingBadge = card.querySelector('.pin-badge');
        if (pinned.includes(canonId)) {
            if (!existingBadge) {
                const pinBadge = document.createElement('div');
                pinBadge.className = 'pin-badge';
                pinBadge.title = 'Anclada al Quick Dock';
                pinBadge.innerHTML = `<svg viewBox="0 0 24 24" fill="currentColor" class="w-2.5 h-2.5"><path d="M16 12V4h1V2H7v2h1v8l-2 2v2h5.2v6h1.6v-6H18v-2l-2-2z"/></svg>`;
                card.appendChild(pinBadge);
            }
        } else {
            if (existingBadge) existingBadge.remove();
        }
    });
}

function togglePinApp(appId) {
    const canonId = getCanonicalAppKey({ id: appId });
    let pinned = Array.from(new Set(getPinnedApps()));
    if (pinned.includes(canonId)) {
        if (pinned.length <= 1) {
            toast('Al menos una app debe quedar anclada');
            return;
        }
        pinned = pinned.filter(id => id !== canonId);
        toast('Desanclada del dock');
    } else {
        if (pinned.length >= 4) {
            toast('Máximo 4 apps ancladas en Quick Dock');
            return;
        }
        pinned.push(canonId);
        toast('Anclada al dock');
    }
    setPinnedApps(pinned);
    renderQuickDock();
    updateAppPinBadges();
}

function findAppMetadata(id) {
    const canonId = getCanonicalAppKey({ id });
    const custom = getCustomApps().find(a => getCanonicalAppKey(a) === canonId);
    if (custom) return { ...custom, id: canonId };
    const kiosk = (lastSuggestedKiosks || []).find(a => getCanonicalAppKey(a) === canonId);
    if (kiosk) return { ...kiosk, id: canonId };
    if (BUILTIN_APPS_MAP[canonId]) return BUILTIN_APPS_MAP[canonId];
    const preset = APP_CATALOG_PRESETS.find(a => getCanonicalAppKey(a) === canonId);
    if (preset) return preset;
    return { id: canonId, name: id, url: '' };
}

function getAppIconElement(app, size = 'card') {
    const iconBox = document.createElement('div');
    const canonId = getCanonicalAppKey(app);
    const name = (app.name || '').toLowerCase();
    const isCard = (size === 'card');

    // For cards: 68x68 authentic squircle container.
    // For dock: 44x44 (w-11 h-11) rounded-xl icon box.
    const baseClass = isCard 
        ? 'squircle-card select-none flex items-center justify-center shrink-0 shadow-sm overflow-hidden relative'
        : 'w-11 h-11 rounded-xl select-none flex items-center justify-center shrink-0 shadow-sm overflow-hidden relative';

    // SVG sizing:
    // Square logos: 44x44 (w-11 h-11) in card (~65% of 68px box), 28x28 (w-7 h-7) in dock.
    const svgSquare = isCard ? 'w-11 h-11' : 'w-7 h-7';
    // Wide logos (Disney+, Apple TV+, YouTube TV): 52x36 (w-13 h-9) in card, 28x20 (w-7 h-5) in dock.
    const svgWide = isCard ? 'w-13 h-9' : 'w-7 h-5';
    const svgYtTv = isCard ? 'w-13 h-10' : 'w-7 h-6';
    const imgSize = isCard ? 'w-11 h-11 object-contain' : 'w-7 h-7 object-contain';
    const initialTextClass = isCard ? 'text-xl font-bold tracking-tight' : 'text-xs font-bold tracking-tight';

    const setSvgContent = (svgHtml, svgClass) => {
        iconBox.innerHTML = svgHtml;
        if (iconBox.firstElementChild) {
            iconBox.firstElementChild.setAttribute('class', svgClass);
        }
    };
    const setInitialFallback = (text, textColorClass = 'skin-text-main') => {
        iconBox.innerHTML = '';
        const span = document.createElement('span');
        span.className = `${textColorClass} ${initialTextClass}`;
        span.textContent = text;
        iconBox.appendChild(span);
    };

    // 1. KNOWN BRANDS (High-res crisp official SVGs)
    if (canonId === 'netflix' || name.includes('netflix')) {
        iconBox.className = `${baseClass} bg-black border border-red-600/40`;
        setSvgContent('<svg viewBox="0 0 24 24"><path fill="#B81D24" d="M4.5 2h3.2v20c-1.1-.2-2.1-.4-3.2-.6V2z"/><path fill="#B81D24" d="M16.3 2h3.2v19.4c-1.1.2-2.1.4-3.2.6V2z"/><path fill="#E50914" d="M4.5 2h3.5l11.5 19.4c-1.1.2-2.3.4-3.5.6L4.5 4.5V2z"/></svg>', svgSquare);
        return iconBox;
    }
    if (canonId === 'youtube' || (name.includes('youtube') && !name.includes('tv') && canonId !== 'youtubetv')) {
        iconBox.className = `${baseClass} bg-[#1A1D24] border border-red-500/40`;
        setSvgContent('<svg viewBox="0 0 24 24"><path fill="#FF0000" d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814z"/><polygon fill="#FFFFFF" points="9.545,15.568 15.818,12 9.545,8.432"/></svg>', svgSquare);
        return iconBox;
    }
    if (canonId === 'youtubetv' || (name.includes('youtube') && name.includes('tv'))) {
        iconBox.className = `${baseClass} bg-[#1A1D24] border border-red-500/40`;
        setSvgContent('<svg viewBox="0 0 28 24"><path fill="#FF0000" d="M18 5.5c-.2-.7-.7-1.3-1.4-1.5C15.3 3.6 10 3.6 10 3.6s-5.3 0-6.6.4C2.7 4.2 2.2 4.8 2 5.5 1.6 6.8 1.6 9.6 1.6 9.6s0 2.8.4 4.1c.2.7.7 1.3 1.4 1.5 1.3.4 6.6.4 6.6.4s5.3 0 6.6-.4c.7-.2 1.2-.8 1.4-1.5.4-1.3.4-4.1.4-4.1s0-2.8-.4-4.1z"/><polygon fill="#FFFFFF" points="8.5,12 13,9.6 8.5,7.2"/><text x="20" y="12" fill="#FFFFFF" font-family="system-ui, sans-serif" font-weight="900" font-size="8">TV</text></svg>', svgYtTv);
        return iconBox;
    }
    if (canonId === 'spotify' || name.includes('spotify')) {
        iconBox.className = `${baseClass} bg-[#1A1D24] border border-green-500/40`;
        setSvgContent('<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="12" fill="#1DB954"/><path fill="#000000" d="M17.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/></svg>', svgSquare);
        return iconBox;
    }
    if (canonId === 'disneyplus' || name.includes('disney')) {
        iconBox.className = `${baseClass} bg-[#081024] border border-blue-500/40`;
        setSvgContent('<svg viewBox="0 0 28 20"><path fill="#0063e5" d="M3.5 16c5-2 16-5 22-1"/><path fill="#ffffff" d="M10.5 4c2.8 0 4.8 1.8 4.8 4.6 0 3.2-2.5 5.4-5.6 5.4H5V4h5.5zm-2.8 7.6h2.2c1.7 0 2.9-1.1 2.9-3 0-1.6-1-2.4-2.5-2.4H7.7v5.4z"/><path fill="#ffffff" d="M19.5 9.5v-3h1.8v3h3v1.8h-3v3h-1.8v-3h-3v-1.8h3z"/></svg>', svgWide);
        return iconBox;
    }
    if (canonId === 'primevideo' || name.includes('prime')) {
        iconBox.className = `${baseClass} bg-[#000511] border border-sky-500/40`;
        setSvgContent('<svg viewBox="0 0 24 24"><path fill="#00A8E1" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14.5c-3.1 0-5.5-1.5-6-3.2.1 0 .2.1.3.1 2.3 0 4.4-.9 6.2-2.2l.6.4c-1.8 1.4-3.9 2.4-6.3 2.5 1 .9 2.8 1.4 5.2 1.4 2.2 0 4.1-.5 5.5-1.3-.2-.3-.5-.7-.8-1-1.3.7-3 1.1-4.7 1.1zm6-3.8c-.3.4-.8.7-1.3.9l-.3-.6c.4-.2.8-.4 1-.7l.6.4z"/><polygon fill="#FFFFFF" points="10,7.5 15,10.5 10,13.5"/></svg>', svgSquare);
        return iconBox;
    }
    if (canonId === 'twitch' || name.includes('twitch')) {
        iconBox.className = `${baseClass} bg-[#9146FF] border border-purple-400/50`;
        setSvgContent('<svg viewBox="0 0 24 24"><path fill="#FFFFFF" d="M2.15 2l-1.8 4.5v13.5h5.4V24l4.05-4h3.15l7.65-7.5V2H2.15zm16.65 9.2l-3.6 3.6H12l-2.7 2.7v-2.7H5.25V4.25h13.55v6.95zM14.85 6.5h2.25v6.3h-2.25V6.5zm-5.4 0h2.25v6.3H9.45V6.5z"/></svg>', svgSquare);
        return iconBox;
    }
    if (canonId === 'crunchyroll' || name.includes('crunchyroll')) {
        iconBox.className = `${baseClass} bg-[#141416] border border-orange-500/40`;
        setSvgContent('<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" fill="#F47521"/><path fill="#FFFFFF" d="M12 4C7.58 4 4 7.58 4 12c0 2.41 1.07 4.57 2.77 6.05C6.28 16.9 6 15.48 6 14c0-3.31 2.69-6 6-6 1.48 0 2.9.28 4.05.77C14.57 5.07 12.41 4 12 4z"/><circle cx="14.5" cy="13.5" r="3.5" fill="#FFFFFF"/></svg>', svgSquare);
        return iconBox;
    }
    if (canonId === 'appletv' || name.includes('apple tv')) {
        iconBox.className = `${baseClass} bg-[#0F0F12] border border-white/20`;
        setSvgContent('<svg viewBox="0 0 28 20"><path fill="#FFFFFF" d="M7.8 7.3c-.6.8-1.5 1.3-2.3 1.2-.1-.9.3-1.8.8-2.4.6-.7 1.6-1.2 2.3-1.2.1.9-.3 1.7-.8 2.4zm.8 1.3c-1.3-.1-2.4.7-3 .7-.6 0-1.6-.7-2.6-.7-1.3 0-2.6.8-3.3 2-1.4 2.4-.4 5.9 1 7.9.7 1 1.5 2.1 2.6 2.1 1 0 1.5-.7 2.7-.7s1.6.7 2.7.7c1.1 0 1.8-1 2.5-2 .8-1.1 1.1-2.2 1.1-2.3 0-.1-2.2-.9-2.2-3.4 0-2.1 1.7-3.1 1.8-3.2-1-1.5-2.5-1.7-3-1.7z"/><text x="14" y="15" fill="#FFFFFF" font-family="system-ui, sans-serif" font-weight="700" font-size="10">tv+</text></svg>', svgWide);
        return iconBox;
    }
    if (canonId === 'kodi' || name.includes('kodi')) {
        iconBox.className = `${baseClass} bg-[#091522] border border-cyan-500/40`;
        setSvgContent('<svg viewBox="0 0 24 24"><rect width="16" height="16" x="4" y="4" rx="3" transform="rotate(45 12 12)" fill="#17B2E7"/><path fill="#FFFFFF" d="M10 7.5v9h1.8v-3.8l3.4 3.8h2.3l-3.9-4.3 3.6-4.7h-2.2l-3.2 4.1v-4.1H10z"/></svg>', svgSquare);
        return iconBox;
    }
    if (canonId === 'retroarch' || name.includes('retroarch')) {
        iconBox.className = `${baseClass} bg-[#13151B] border border-white/20`;
        setSvgContent('<svg viewBox="0 0 24 24"><path fill="#FFFFFF" d="M7 4h10v2H7V4zm-2 3h14v2H5V7zm-2 3h18v2H3v-2zm0 3h3v3H3v-3zm5 0h8v3H8v-3zm10 0h3v3h-3v-3zm-13 4h2v2H5v-2zm14 0h2v2h-2v-2zM8 9h2v2H8V9zm8 0h2v2h-2V9z"/></svg>', svgSquare);
        return iconBox;
    }
    if (canonId === 'stremio' || name.includes('stremio')) {
        iconBox.className = `${baseClass} bg-[#1A0E2E] border border-purple-500/40`;
        setSvgContent('<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10.5" fill="#3F2563"/><polygon fill="#FFFFFF" points="9.5,7 17,12 9.5,17"/><polygon fill="#A855F7" points="9.5,7 13.5,12 9.5,17"/></svg>', svgSquare);
        return iconBox;
    }
    if (canonId === 'plutotv' || name.includes('pluto')) {
        iconBox.className = `${baseClass} bg-[#FFDA00] border border-yellow-300`;
        setSvgContent('<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" fill="#000000"/><text x="12" y="15" fill="#FFDA00" font-family="system-ui, sans-serif" font-weight="900" font-size="8.5" text-anchor="middle">pluto</text></svg>', svgSquare);
        return iconBox;
    }
    if (canonId === 'kick' || name.includes('kick')) {
        iconBox.className = `${baseClass} bg-[#080B10] border border-green-500/40`;
        setSvgContent('<svg viewBox="0 0 24 24"><rect width="24" height="24" rx="5" fill="#05080C"/><path fill="#53FC18" d="M5 4h4v6.2l4.8-6.2h4.9l-5.6 7 5.9 9H14l-5-7.8V20H5V4z"/></svg>', svgSquare);
        return iconBox;
    }
    if (canonId === 'animeav1' || name.includes('animeav1') || name.includes('av1')) {
        iconBox.className = `${baseClass} bg-[#190A2C] border border-purple-500/50`;
        setSvgContent('<svg viewBox="0 0 24 24"><rect width="22" height="22" x="1" y="1" rx="6" fill="#7C3AED"/><polygon fill="#22D3EE" points="6,6 14,12 6,18"/><text x="14" y="15.5" fill="#FFFFFF" font-family="system-ui, sans-serif" font-weight="900" font-size="8">AV1</text></svg>', svgSquare);
        return iconBox;
    }
    if (canonId === 'animeflv' || name.includes('animeflv')) {
        iconBox.className = `${baseClass} bg-[#18181B] border border-orange-600/40`;
        setSvgContent('<svg viewBox="0 0 24 24"><rect width="22" height="22" x="1" y="1" rx="6" fill="#EA580C"/><text x="12" y="15" fill="#FFFFFF" font-family="system-ui, sans-serif" font-weight="900" font-size="8" text-anchor="middle">FLV</text></svg>', svgSquare);
        return iconBox;
    }
    if (canonId === 'tiktok' || name.includes('tiktok')) {
        iconBox.className = `${baseClass} bg-black border border-pink-500/40`;
        setSvgContent('<svg viewBox="0 0 24 24"><path fill="#25F4EE" d="M16.6 5.82s.51.5 0 0A4.278 4.278 0 0 1 15.54 3h-3.09v12.4a2.59 2.59 0 0 1-2.59 2.5 2.6 2.6 0 0 1-2.6-2.6 2.6 2.6 0 0 1 2.6-2.6c.33 0 .64.06.93.16V9.6a5.67 5.67 0 0 0-.93-.08A5.69 5.69 0 0 0 4.16 15.2a5.69 5.69 0 0 0 5.69 5.69 5.69 5.69 0 0 0 5.69-5.69V8.71a7.41 7.41 0 0 0 4.46 1.49V7.1a4.34 4.34 0 0 1-3.4-1.28z"/><path fill="#FE2C55" d="M17.6 6.82s.51.5 0 0A4.278 4.278 0 0 1 16.54 4h-3.09v12.4a2.59 2.59 0 0 1-2.59 2.5 2.6 2.6 0 0 1-2.6-2.6 2.6 2.6 0 0 1 2.6-2.6c.33 0 .64.06.93.16V10.6a5.67 5.67 0 0 0-.93-.08A5.69 5.69 0 0 0 5.16 16.2a5.69 5.69 0 0 0 5.69 5.69 5.69 5.69 0 0 0 5.69-5.69V9.71a7.41 7.41 0 0 0 4.46 1.49V8.1a4.34 4.34 0 0 1-3.4-1.28z"/></svg>', svgSquare);
        return iconBox;
    }
    if (canonId === 'hbomax' || name.includes('max') || name.includes('hbo')) {
        iconBox.className = `${baseClass} bg-[#001452] border border-blue-600/40`;
        setSvgContent('<svg viewBox="0 0 24 24"><rect width="22" height="22" x="1" y="1" rx="6" fill="#002BE7"/><text x="12" y="15" fill="#FFFFFF" font-family="system-ui, sans-serif" font-weight="900" font-size="8.5" text-anchor="middle">MAX</text></svg>', svgSquare);
        return iconBox;
    }

    // 2. NATIVE SYSTEM APPS
    if (app.is_native && app.id) {
        iconBox.className = `${baseClass} surface-glass border border-white/10`;
        const img = document.createElement('img');
        img.src = `/api/icon/${app.id}`;
        img.className = imgSize;
        img.onerror = () => {
            setInitialFallback((app.name || canonId).slice(0, 2).toUpperCase(), 'skin-text-main');
        };
        iconBox.appendChild(img);
        return iconBox;
    }

    // 3. WEB APPS WITH URL (High-res Favicons via DuckDuckGo / Google s2 for both Dock & Library)
    if (app.url) {
        iconBox.className = `${baseClass} surface-glass border border-white/10`;
        try {
            const domain = new URL(app.url).hostname;
            const img = document.createElement('img');
            img.className = `${imgSize} rounded-md`;
            img.onerror = () => {
                setInitialFallback((app.name || canonId).slice(0, 2).toUpperCase(), 'skin-text-main');
            };
            setTileFavicon(img, domain);
            iconBox.appendChild(img);
        } catch(e) {
            setInitialFallback((app.name || canonId).slice(0, 2).toUpperCase(), 'skin-text-main');
        }
        return iconBox;
    }

    // 4. FALLBACK INITIALS / COLOR
    if (app.color) {
        iconBox.className = `${baseClass} border border-white/10`;
        iconBox.style.backgroundColor = app.color;
        const text = app.iconText || (app.name || canonId).slice(0, 3);
        setInitialFallback(text, 'text-white');
        return iconBox;
    }

    iconBox.className = `${baseClass} surface-glass border border-white/10`;
    setInitialFallback((app.name || canonId).slice(0, 2).toUpperCase(), 'skin-text-main');
    return iconBox;
}

function createMoreBtn() {
    const btn = document.createElement('button');
    btn.id = 'more-btn';
    btn.onclick = () => openDrawer();
    btn.className = 'flex-1 py-1 flex flex-col items-center gap-1 rounded-xl active:bg-white/10 transition';
    btn.title = 'Más Apps';
    btn.innerHTML = `
        <div class="w-11 h-11 rounded-xl surface-glass flex items-center justify-center border border-white/10 shadow-sm text-gray-300">
            <svg viewBox="0 0 24 24" fill="currentColor" class="w-6 h-6"><circle cx="5" cy="12" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="19" cy="12" r="2"/></svg>
        </div>
        <span class="text-[10px] font-medium text-gray-300">Más Apps</span>
    `;
    return btn;
}

function renderQuickDock() {
    const dock = document.getElementById('quick-dock');
    if (!dock) return;
    const moreBtn = document.getElementById('more-btn') || createMoreBtn();
    dock.innerHTML = '';

    const pinnedIds = Array.from(new Set(getPinnedApps()));
    pinnedIds.forEach(id => {
        const app = findAppMetadata(id);
        const btn = document.createElement('button');
        btn.className = 'flex-1 py-1 flex flex-col items-center gap-1 rounded-xl active:bg-white/10 transition';
        btn.title = app.name || id;
        btn.onclick = () => {
            if (app.is_native) {
                launchNativeApp(app.id);
            } else if (app.url) {
                launchKiosk(app.url, app.id);
            }
        };

        const iconBox = getAppIconElement(app, 'dock');
        const lbl = document.createElement('span');
        lbl.className = 'text-[10px] font-medium text-gray-300 truncate max-w-[64px] text-center';
        lbl.textContent = app.name || id;

        btn.appendChild(iconBox);
        btn.appendChild(lbl);
        dock.appendChild(btn);
    });

    if (moreBtn) {
        dock.appendChild(moreBtn);
    }
}

let appHubCategory = 'all';
let appHubFilterText = '';
let isEditAppsMode = false;

function toggleEditAppsMode() {
    isEditAppsMode = !isEditAppsMode;
    const btn = document.getElementById('btn-edit-apps');
    const lbl = document.getElementById('btn-edit-label');
    const icon = document.getElementById('btn-edit-icon');

    if (btn) {
        if (isEditAppsMode) {
            btn.classList.add('active');
            if (lbl) lbl.textContent = 'Listo';
            if (icon) icon.innerHTML = `<polyline points="20 6 9 17 4 12"/>`;
            toast('Modo edición: toca para ocultar o borrar');
        } else {
            btn.classList.remove('active');
            if (lbl) lbl.textContent = 'Editar';
            if (icon) icon.innerHTML = `<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>`;
        }
    }
    renderApps(lastSuggestedKiosks);
}

function isCustomApp(appId) {
    const canonId = getCanonicalAppKey({ id: appId });
    if (BUILTIN_APPS_MAP[canonId]) return false;
    const customApps = getCustomApps();
    return customApps.some(a => getCanonicalAppKey(a) === canonId || a.id === appId);
}

function toggleHideApp(appId) {
    const canonId = getCanonicalAppKey({ id: appId });
    let hidden = getHiddenApps().map(id => getCanonicalAppKey({ id }));
    if (hidden.includes(canonId) || hidden.includes(appId)) {
        hidden = hidden.filter(id => id !== canonId && id !== appId);
        toast('App visible de nuevo');
    } else {
        hidden.push(canonId);
        // Also unpin if pinned
        let pinned = getPinnedApps().filter(id => id !== canonId && id !== appId);
        setPinnedApps(pinned);
        toast('App oculta (puedes restaurarla en Modo Edición)');
    }
    localStorage.setItem('hidden_apps', JSON.stringify(Array.from(new Set(hidden))));
    renderApps(lastSuggestedKiosks);
}

function deleteCustomApp(appId) {
    const canonId = getCanonicalAppKey({ id: appId });
    let customApps = getCustomApps();
    const appToDelete = customApps.find(a => getCanonicalAppKey(a) === canonId || a.id === appId);
    customApps = customApps.filter(a => getCanonicalAppKey(a) !== canonId && a.id !== appId);
    localStorage.setItem('custom_apps', JSON.stringify(customApps));
    let pinned = getPinnedApps().filter(id => id !== canonId && id !== appId);
    setPinnedApps(pinned);
    toast(`App ${appToDelete ? appToDelete.name : ''} eliminada`);
    renderApps(lastSuggestedKiosks);
}

function setAppHubCategory(cat) {
    appHubCategory = cat;
    const chips = document.querySelectorAll('#hub-chips .hub-chip');
    chips.forEach(chip => {
        if (chip.dataset.category === cat) {
            chip.classList.add('active');
        } else {
            chip.classList.remove('active');
        }
    });
    filterAppHub();
}

function filterAppHub() {
    const input = document.getElementById('hub-search-input');
    appHubFilterText = (input ? input.value : '').toLowerCase().trim();
    renderApps(lastSuggestedKiosks);
}

function toggleCustomAppPanel() {
    const panel = document.getElementById('add-panel');
    if (!panel) return;
    panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
}

function createAppTile(app, isHidden = false) {
    const div = document.createElement('div');
    div.className = 'app-item relative flex flex-col items-center gap-1 cursor-pointer select-none';
    div.dataset.url = app.url || '';
    div.dataset.id = app.id || '';
    div.style.webkitTouchCallout = 'none';
    div.style.webkitUserSelect = 'none';
    div.style.userSelect = 'none';
    if (app.is_native) div.dataset.native = 'true';

    if (isHidden) {
        div.classList.add('is-hidden-app');
    }

    const cardWrapper = document.createElement('div');
    cardWrapper.className = 'relative shrink-0';

    const card = getAppIconElement(app, 'card');
    cardWrapper.appendChild(card);

    // Live Indicator for active app
    if (activeKioskAppId && (app.id === activeKioskAppId || (app.url && activeKioskUrl === app.url))) {
        const liveDot = document.createElement('span');
        liveDot.className = 'live-indicator absolute top-1.5 left-1.5';
        card.appendChild(liveDot);
        card.style.borderColor = 'rgba(16, 185, 129, 0.5)';
        card.style.boxShadow = '0 0 10px rgba(16, 185, 129, 0.25)';
    }

    // Pin badge for apps in Quick Dock (top-right of app card)
    if (app.id && isAppPinned(app.id) && !isEditAppsMode) {
        const pinBadge = document.createElement('div');
        pinBadge.className = 'pin-badge';
        pinBadge.title = 'Anclada al Quick Dock';
        pinBadge.innerHTML = `<svg viewBox="0 0 24 24" fill="currentColor" class="w-2.5 h-2.5"><path d="M16 12V4h1V2H7v2h1v8l-2 2v2h5.2v6h1.6v-6H18v-2l-2-2z"/></svg>`;
        card.appendChild(pinBadge);
    }

    // Edit mode action buttons
    if (isEditAppsMode && app.id) {
        const actionBtn = document.createElement('button');
        if (isHidden) {
            // Restore/Unhide button
            actionBtn.className = 'edit-action-btn edit-unhide-btn bg-emerald-600 text-white hover:scale-110 active:scale-95 transition';
            actionBtn.title = 'Mostrar aplicación';
            actionBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="w-3.5 h-3.5"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`;
            actionBtn.onclick = (e) => {
                e.stopPropagation();
                e.preventDefault();
                toggleHideApp(app.id);
            };
        } else if (isCustomApp(app.id)) {
            // Delete button for custom user-added apps
            actionBtn.className = 'edit-action-btn edit-delete-btn bg-rose-600 text-white hover:scale-110 active:scale-95 transition';
            actionBtn.title = 'Eliminar aplicación';
            actionBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="w-3.5 h-3.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`;
            actionBtn.onclick = (e) => {
                e.stopPropagation();
                e.preventDefault();
                deleteCustomApp(app.id);
            };
        } else {
            // Hide button for builtin apps
            actionBtn.className = 'edit-action-btn edit-hide-btn bg-amber-600 text-white hover:scale-110 active:scale-95 transition';
            actionBtn.title = 'Ocultar aplicación (no se borra)';
            actionBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="w-3.5 h-3.5"><line x1="1" y1="23" x2="23" y2="1"/><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/></svg>`;
            actionBtn.onclick = (e) => {
                e.stopPropagation();
                e.preventDefault();
                toggleHideApp(app.id);
            };
        }
        cardWrapper.appendChild(actionBtn);
    }

    const span = document.createElement('span');
    span.className = 'text-[11px] font-medium text-gray-300 truncate w-full text-center px-0.5 mt-0.5 pointer-events-none';
    span.textContent = app.name || '';

    div.appendChild(cardWrapper);
    div.appendChild(span);

    // Long-press (450ms with haptic vibration) to pin/unpin from Quick Dock (only when NOT in edit mode)
    if (app.id && !isEditAppsMode) {
        let pressTimer = null;
        let startX = 0, startY = 0;
        let triggered = false;

        div.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            e.stopPropagation();
        });

        div.addEventListener('pointerdown', (e) => {
            startX = e.clientX;
            startY = e.clientY;
            triggered = false;
            pressTimer = setTimeout(() => {
                triggered = true;
                lastLongPressTime = Date.now();
                div.dataset.longPressTriggered = 'true';
                if (navigator.vibrate) navigator.vibrate(50);
                togglePinApp(app.id);
            }, 450);
        });

        div.addEventListener('pointermove', (e) => {
            if (pressTimer) {
                const dist = Math.hypot(e.clientX - startX, e.clientY - startY);
                if (dist > 10) {
                    clearTimeout(pressTimer);
                    pressTimer = null;
                }
            }
        });

        const cancelPress = (e) => {
            if (pressTimer) {
                clearTimeout(pressTimer);
                pressTimer = null;
            }
            if (triggered) {
                if (e) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                setTimeout(() => { triggered = false; }, 300);
            }
        };

        div.addEventListener('pointerup', cancelPress);
        div.addEventListener('pointercancel', cancelPress);
        div.addEventListener('pointerleave', cancelPress);
    }

    return div;
}

function renderApps(kiosks) {
    renderQuickDock();
    const usage = getUsage();
    const customApps = getCustomApps();
    const hiddenApps = getHiddenApps().map(id => getCanonicalAppKey({ id }));

    // Map ensuring all default/builtin apps always exist in library with canonical IDs
    const appMap = new Map();
    Object.values(BUILTIN_APPS_MAP).forEach(app => {
        const key = getCanonicalAppKey(app);
        appMap.set(key, { ...app, id: key, is_builtin: true });
    });

    (kiosks || []).forEach(k => {
        if (!k) return;
        const key = getCanonicalAppKey(k);
        if (key) {
            const existing = appMap.get(key) || {};
            appMap.set(key, { ...existing, ...k, id: key });
        }
    });

    let customChanged = false;
    const sanitizedCustom = [];
    customApps.forEach(c => {
        if (!c) return;
        const key = getCanonicalAppKey(c);
        if (!key) return;

        if (BUILTIN_APPS_MAP[key]) {
            // It's a duplicate of a builtin app! Consolidate metadata onto builtin and remove from customApps
            const existing = appMap.get(key) || {};
            appMap.set(key, { ...existing, ...c, id: key, is_builtin: true, is_custom: false });
            customChanged = true;
        } else {
            // Truly custom app - check for duplicates inside customApps
            if (!sanitizedCustom.some(sc => sc.id === key || (sc.url && normalizeUrl(sc.url) === normalizeUrl(c.url)))) {
                const customObj = { ...c, id: key, is_custom: true };
                sanitizedCustom.push(customObj);
                appMap.set(key, customObj);
            } else {
                customChanged = true;
            }
        }
    });

    if (customChanged) {
        try {
            localStorage.setItem('custom_apps', JSON.stringify(sanitizedCustom));
        } catch(_) {}
    }

    const allApps = Array.from(appMap.values());
    const visibleKiosks = allApps.filter(k => !hiddenApps.includes(k.id));
    const sorted = visibleKiosks.sort((a, b) => (usage[b.id] || 0) - (usage[a.id] || 0));

    const row = document.getElementById('apps-row');
    if (row) {
        row.innerHTML = '';
        sorted.slice(0, 5).forEach((app) => {
            row.appendChild(createAppTile(app, false));
        });
    }

    const drawer = document.getElementById('drawer-grid');
    if (drawer) {
        drawer.innerHTML = '';

        // In edit mode: show candidate apps including hidden ones
        const candidateApps = isEditAppsMode ? allApps : visibleKiosks;

        const filteredForDrawer = candidateApps.filter(app => {
            if (appHubCategory !== 'all') {
                const cat = app.category || (app.name && /spotify|radio|music/i.test(app.name) ? 'music' : 'video');
                if (cat !== appHubCategory && (appHubCategory === 'web' && !app.url)) return false;
            }
            if (appHubFilterText) {
                const name = (app.name || '').toLowerCase();
                const url = (app.url || '').toLowerCase();
                if (!name.includes(appHubFilterText) && !url.includes(appHubFilterText)) return false;
            }
            return true;
        });

        // Sort: unhidden first, then hidden, then by usage
        const sortedDrawerApps = filteredForDrawer.sort((a, b) => {
            const aHidden = hiddenApps.includes(a.id);
            const bHidden = hiddenApps.includes(b.id);
            if (aHidden !== bHidden) return aHidden ? 1 : -1;
            return (usage[b.id] || 0) - (usage[a.id] || 0);
        });

        if (sortedDrawerApps.length === 0) {
            const emptyNotice = document.createElement('div');
            emptyNotice.className = 'col-span-4 text-center text-xs text-gray-500 py-4';
            emptyNotice.textContent = 'No se encontraron aplicaciones';
            drawer.appendChild(emptyNotice);
        } else {
            sortedDrawerApps.forEach((app) => {
                const isHidden = hiddenApps.includes(app.id);
                drawer.appendChild(createAppTile(app, isHidden));
            });
        }
    }

    let restoreBtn = document.getElementById('restore-hidden-apps');
    if (!restoreBtn && drawer) {
        restoreBtn = document.createElement('button');
        restoreBtn.id = 'restore-hidden-apps';
        restoreBtn.className = 'text-blue-400 text-xs mt-3 underline text-center w-full block hover:text-blue-300';
        restoreBtn.onclick = () => {
            localStorage.setItem('hidden_apps', '[]');
            renderApps(lastSuggestedKiosks);
            toast('Apps restauradas');
        };
        drawer.parentNode.insertBefore(restoreBtn, drawer.nextSibling);
    }
    
    if (restoreBtn) {
        if (hiddenApps.length > 0) {
            restoreBtn.textContent = `Restablecer apps ocultas (${hiddenApps.length})`;
            restoreBtn.style.display = 'block';
        } else {
            restoreBtn.style.display = 'none';
        }
    }
}

function handleAppLaunchClick(e) {
    if (isEditAppsMode && e.target.closest('#drawer-grid')) {
        e.preventDefault();
        e.stopPropagation();
        return;
    }
    if (Date.now() - lastLongPressTime < 1000) {
        e.preventDefault();
        e.stopPropagation();
        return;
    }
    const tile = e.target.closest('[data-id]');
    if (tile) {
        if (tile.dataset.longPressTriggered === 'true') {
            delete tile.dataset.longPressTriggered;
            return;
        }
        const id = tile.dataset.id;
        if (tile.dataset.native === 'true') {
            launchNativeApp(id);
        } else if (tile.dataset.url) {
            launchKiosk(tile.dataset.url, id);
        }
    }
}
const appsRowEl = document.getElementById('apps-row');
if (appsRowEl) appsRowEl.addEventListener('click', handleAppLaunchClick);
const drawerGridEl = document.getElementById('drawer-grid');
if (drawerGridEl) drawerGridEl.addEventListener('click', handleAppLaunchClick);

function toggleMore() { const m = document.getElementById('apps-more'); if (m) m.hidden = !m.hidden; }

async function fetchApps() {
    try {
        const res = await fetch(`${apiUrl}/apps`, {
            headers: { 'X-Auth-Token': token }
        });
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();
        lastSuggestedKiosks = data.suggested_kiosks || [];
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
        activeKioskAppId = id || null;
        activeKioskUrl = url || null;
        renderApps(lastSuggestedKiosks);
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
        activeKioskAppId = null;
        activeKioskUrl = null;
        renderApps(lastSuggestedKiosks);
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
        btn.className = 'skin-accent px-3 py-1 rounded text-xs font-bold skin-text-on-accent shadow-sm';
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
        activeKioskAppId = id || null;
        activeKioskUrl = null;
        renderApps(lastSuggestedKiosks);
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

    const testApp = { name, url: urlStr };
    const canonKey = getCanonicalAppKey(testApp);

    if (BUILTIN_APPS_MAP[canonKey]) {
        // App already exists in library! If hidden, unhide it.
        const hidden = getHiddenApps();
        if (hidden.includes(canonKey)) {
            localStorage.setItem('hidden_apps', JSON.stringify(hidden.filter(h => h !== canonKey)));
            renderApps(lastSuggestedKiosks);
            toast(`${name} ya existe y ha sido restaurada.`);
        } else {
            toast(`${name} ya está disponible en la biblioteca.`);
        }
        nameInput.value = '';
        urlInput.value = '';
        return;
    }

    const customApps = getCustomApps();
    if (customApps.some(a => getCanonicalAppKey(a) === canonKey || (a.url && normalizeUrl(a.url) === normalizeUrl(urlStr)))) {
        toast('Esta aplicación ya fue añadida.');
        return;
    }

    const newId = 'custom_' + Date.now();
    customApps.push({ id: newId, name, url: urlStr, color: '#3b82f6' });
    localStorage.setItem('custom_apps', JSON.stringify(customApps));

    nameInput.value = '';
    urlInput.value = '';
    renderApps(lastSuggestedKiosks);
    toast('Aplicación añadida con éxito');
}

// --- PipeWire Audio Controls ---
async function loadAudioSettings() {
    const container = document.getElementById('settings-audio-sinks');
    const slider = document.getElementById('settings-audio-vol-slider');
    const valLabel = document.getElementById('settings-audio-vol-val');
    if (!container) return;

    try {
        const res = await fetch(`${apiUrl}/system/audio`, {
            headers: { 'X-Auth-Token': token }
        });
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();

        container.innerHTML = '';
        if (!data.sinks || data.sinks.length === 0) {
            container.innerHTML = '<div class="text-xs text-gray-400 italic">No se detectaron salidas de audio</div>';
        } else {
            data.sinks.forEach(sink => {
                const btn = document.createElement('button');
                btn.type = 'button';
                const isActive = sink.active || (sink.id === data.active_sink);
                btn.className = `w-full p-2.5 rounded-lg text-left text-xs flex items-center justify-between transition border ${
                    isActive
                    ? 'bg-blue-600/20 border-blue-500/60 text-blue-300 font-semibold shadow-sm'
                    : 'bg-black/20 border-gray-700/60 text-gray-300 hover:bg-white/5'
                }`;

                let icon = '🔈';
                const nLower = (sink.name || '').toLowerCase();
                if (nLower.includes('hdmi') || nLower.includes('digital') || nLower.includes('tv')) {
                    icon = '📺';
                } else if (nLower.includes('blue') || nLower.includes('bt')) {
                    icon = '🎧';
                }

                btn.innerHTML = `
                    <span class="flex items-center gap-2 truncate flex-1">
                        <span>${icon}</span>
                        <span class="truncate">${sink.name || sink.id}</span>
                    </span>
                    ${isActive ? '<span class="text-blue-400 text-[10px] uppercase font-bold tracking-wider shrink-0 ml-2">Activo</span>' : ''}
                `;
                btn.onclick = () => applyAudioSink(sink.id);
                container.appendChild(btn);
            });
        }

        if (slider && typeof data.volume === 'number') {
            slider.value = data.volume;
            if (valLabel) valLabel.textContent = `${data.volume}%`;
        }
    } catch (e) {
        console.warn('Failed to load audio settings:', e);
        container.innerHTML = '<div class="text-xs text-gray-400 italic">No disponible</div>';
    }
}

async function applyAudioSink(sinkId) {
    if (navigator.vibrate) navigator.vibrate(20);
    toast('Cambiando salida de audio...');
    try {
        const res = await fetch(`${apiUrl}/system/audio/sink`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-Auth-Token': token },
            body: JSON.stringify({ sink_id: sinkId })
        });
        if (!res.ok) throw new Error('HTTP ' + res.status);
        toast('Salida de audio actualizada');
        loadAudioSettings();
    } catch (e) {
        console.error('Audio sink error:', e);
        toast('Error al cambiar salida de audio');
    }
}

let volumeDebounceTimer = null;
function onAudioVolumeSliderInput(val) {
    const valLabel = document.getElementById('settings-audio-vol-val');
    if (valLabel) valLabel.textContent = `${val}%`;
    clearTimeout(volumeDebounceTimer);
    volumeDebounceTimer = setTimeout(() => {
        applyAudioVolume(val);
    }, 250);
}

async function applyAudioVolume(val) {
    try {
        await fetch(`${apiUrl}/system/audio/volume`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-Auth-Token': token },
            body: JSON.stringify({ volume: parseInt(val, 10), sink_id: '@DEFAULT_AUDIO_SINK@' })
        });
    } catch (e) {
        console.warn('Failed to set volume:', e);
    }
}

// --- Power Management Controls (2-Step Safety Modal) ---
let pendingPowerAction = null;

function confirmPowerAction(action, label) {
    pendingPowerAction = action;
    const modal = document.getElementById('power-confirm-modal');
    const title = document.getElementById('power-modal-title');
    const desc = document.getElementById('power-modal-desc');
    if (!modal) return;

    if (title) title.textContent = label;
    if (desc) {
        if (action === 'suspend') {
            desc.textContent = 'El HTPC entrará en modo suspensión de bajo consumo.';
        } else if (action === 'reboot') {
            desc.textContent = 'El equipo se reiniciará por completo. La conexión se perderá momentáneamente.';
        } else if (action === 'poweroff') {
            desc.textContent = 'El equipo se apagará por completo. Para volver a encenderlo usarás el botón físico o Wake-on-LAN.';
        } else if (action === 'restart-service') {
            desc.textContent = 'Se reiniciará únicamente el servicio web de Linux Remote Player.';
        }
    }
    modal.classList.remove('hidden');
    if (navigator.vibrate) navigator.vibrate([30, 30]);
}

function closePowerModal() {
    const modal = document.getElementById('power-confirm-modal');
    if (modal) modal.classList.add('hidden');
    pendingPowerAction = null;
}

async function executePendingPowerAction() {
    if (!pendingPowerAction) return;
    const action = pendingPowerAction;
    closePowerModal();
    if (navigator.vibrate) navigator.vibrate([50, 100, 50]);
    toast(`Ejecutando acción: ${action}...`);

    try {
        const res = await fetch(`${apiUrl}/system/power/${action}`, {
            method: 'POST',
            headers: { 'X-Auth-Token': token }
        });
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();
        toast(data.message || 'Acción completada');
    } catch (e) {
        console.error('Power action error:', e);
        toast('Error al ejecutar acción de energía');
    }
}

// --- Settings and Token save ---
function openSettings() {
    const d = document.getElementById('settings-drawer');
    if (d) d.classList.add('open');
    loadAudioSettings();
}
function closeSettings() {
    const d = document.getElementById('settings-drawer');
    if (d) d.classList.remove('open');
}
function openDrawer() {
    const d = document.getElementById('app-drawer');
    if (d) d.classList.add('open');
    renderApps(lastSuggestedKiosks);
}
function closeDrawer() {
    const d = document.getElementById('app-drawer');
    if (d) d.classList.remove('open');
    if (isEditAppsMode) {
        toggleEditAppsMode();
    }
}
function comingSoon() {
    toast('Esta sección estará disponible próximamente.');
}

const WEBSITE_URL = 'https://www.linuxremoteplayer.com/';

function shareApp() {
    const shareData = {
        title: 'LinuxRemotePlayer',
        text: '🎬 Convertí mi PC Linux en una Smart TV con control remoto desde el móvil. Touchpad, teclado y apps. Mirá:',
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

function sendFeedback() {
    const msgEl = document.getElementById('feedback-msg');
    if (!msgEl) return;
    if (!msgEl.value.trim()) {
        toast('El mensaje está vacío');
        return;
    }
    // T-150d: sin backend de feedback; no hay envío remoto.
    toast('Feedback no disponible en esta versión.');
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
    box.className = 'skin-bg-panel skin-text-main rounded-xl p-4 m-4 max-w-sm w-[90%] shadow-2xl border border-gray-600 relative z-10 transition-all';
    
    const textEl = document.createElement('p');
    textEl.className = 'text-sm font-bold mb-4';
    
    const flexBtn = document.createElement('div');
    flexBtn.className = 'flex justify-between items-center';
    
    const skipBtn = document.createElement('button');
    skipBtn.textContent = 'Saltar';
    skipBtn.className = 'text-gray-400 text-xs font-bold px-2 py-1';
    
    const nextBtn = document.createElement('button');
    nextBtn.className = 'bg-blue-600 hover:bg-blue-500 px-4 py-1.5 rounded-lg text-sm font-bold skin-text-on-accent';
    
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
// T-151c: banner de instalacion en la web destino del QR (no bloquea el control).
const APK_URL = '/downloads/lrp.apk';
const APK_AVAILABLE = false;
const INSTALL_BANNER_DISMISSED = 'lrp_install_banner_dismissed';

function detectInstallPlatform() {
    const forced = new URLSearchParams(location.search).get('platform');
    if (forced === 'ios' || forced === 'android' || forced === 'desktop') return forced;
    const ua = navigator.userAgent || '';
    if (/iphone|ipad|ipod/i.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)) return 'ios';
    if (/android/i.test(ua)) return 'android';
    return 'desktop';
}

function dismissInstallBanner() {
    const banner = document.getElementById('install-banner');
    if (banner) banner.hidden = true;
    try { localStorage.setItem(INSTALL_BANNER_DISMISSED, '1'); } catch (e) {}
}

function renderInstallBanner() {
    const banner = document.getElementById('install-banner');
    if (!banner) return;
    if (isStandalone) {
        banner.hidden = true;
        return;
    }
    try {
        if (localStorage.getItem(INSTALL_BANNER_DISMISSED) === '1') {
            banner.hidden = true;
            return;
        }
    } catch (e) {}
    const platform = detectInstallPlatform();
    if (platform === 'desktop') {
        banner.hidden = true;
        return;
    }
    const title = document.getElementById('install-banner-title');
    const desc = document.getElementById('install-banner-desc');
    const action = document.getElementById('install-banner-action');
    if (platform === 'ios') {
        if (title) title.textContent = 'Añadir a pantalla de inicio';
        if (desc) desc.textContent = 'Compartir → Añadir a pantalla de inicio';
        if (action) action.hidden = true;
    } else {
        const apkReady = APK_AVAILABLE;
        if (title) title.textContent = 'Instalar la app';
        if (action) {
            action.hidden = false;
            action.textContent = apkReady ? 'Descargar APK' : 'APK próximamente';
            action.classList.toggle('is-disabled', !apkReady);
            if (apkReady) action.href = APK_URL;
            else action.removeAttribute('href');
        }
        if (desc) {
            desc.textContent = apkReady
                ? 'Descargá el APK para usar LRP como app en tu Android.'
                : 'APK próximamente. Mientras tanto: Chrome → menú ⋮ → Instalar aplicación.';
        }
    }
    banner.hidden = false;
}

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
            + '<p class="text-gray-300 max-w-sm">Abre LinuxRemotePlayer desde el icono de tu pantalla de inicio.</p></div>';
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

    fetchConfig().then(() => {
        connect();
        fetchApps();
    });
}

initToken().then(() => {
    // T-151c: la web muestra un banner descartable en vez del tutorial a pantalla completa.
    renderInstallBanner();
    if (token === 'guest') {
        showPairingScreen(true);
    } else {
        showPairingScreen(false);
        fetchConfig().then(() => {
            connect();
            fetchApps();
        });
    }
});

function updateAppHeight() {
    const h = window.visualViewport ? window.visualViewport.height : window.innerHeight;
    document.documentElement.style.setProperty('--app-h', h + 'px');
}

// B1: al volver del segundo plano, iOS todavia reporta la altura ANTERIOR en el momento en
// que disparan pageshow/visibilitychange -- la vista se asienta unos frames despues. Si se
// escribe ese numero viejo y es mayor que el viewport real, el body queda mas alto que la
// pantalla y los botones de abajo se van fuera de vista. Por eso NO alcanza con tener el
// listener (ya estaban): hay que re-leer cuando la disposicion ya se acomodo.
// Se mide tres veces a proposito -- ya, al frame siguiente, y a los 300ms -- porque el
// momento exacto en que iOS actualiza el valor no es estable entre modelos ni versiones.
function updateAppHeightSettled() {
    updateAppHeight();
    requestAnimationFrame(updateAppHeight);
    setTimeout(updateAppHeight, 300);
}

window.addEventListener('load', updateAppHeight);
window.addEventListener('resize', updateAppHeight);
window.addEventListener('orientationchange', updateAppHeightSettled);
window.addEventListener('pageshow', updateAppHeightSettled);
// visibilitychange es el que dispara de verdad al reabrir una PWA instalada en iOS:
// pageshow puede no llegar si la pagina no venia del bfcache.
document.addEventListener('visibilitychange', function () {
    if (!document.hidden) updateAppHeightSettled();
});
if (window.visualViewport) {
    window.visualViewport.addEventListener('resize', updateAppHeight);
}
updateAppHeight();
