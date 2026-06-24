const statusEl = document.getElementById('status');
const suggestedGrid = document.getElementById('suggested-grid');
const appsGrid = document.getElementById('apps-grid');
let ws;

const host = window.location.hostname === '' || window.location.hostname === 'localhost' ? '127.0.0.1' : window.location.hostname;
const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
const wsUrl = `${protocol}${host}:8000/ws`;
const apiUrl = `${window.location.protocol}//${host}:8000/api`;

function connect() {
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        statusEl.textContent = 'Connected';
        statusEl.className = 'text-green-500 text-sm font-bold';
    };

    ws.onclose = () => {
        statusEl.textContent = 'Disconnected - Retrying...';
        statusEl.className = 'text-red-500 text-sm font-bold';
        setTimeout(connect, 2000);
    };

    ws.onerror = (err) => {
        console.error('WebSocket Error:', err);
    };
}

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

async function fetchApps() {
    try {
        const res = await fetch(`${apiUrl}/apps`);
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const data = await res.json();
        
        // Render suggested kiosks
        suggestedGrid.innerHTML = data.suggested_kiosks.map(app => `
            <div onclick="launchKiosk('${app.url}')" class="bg-gray-800 p-4 rounded-xl flex flex-col items-center justify-center cursor-pointer active:scale-95 transition-transform border border-gray-700">
                <div class="w-12 h-12 bg-blue-600 rounded-full mb-2 flex items-center justify-center text-xl font-bold">${app.name[0]}</div>
                <span class="text-xs text-center truncate w-full">${app.name}</span>
            </div>
        `).join('');

        // Render native apps (limit to 12 for UI brevity during MVP)
        appsGrid.innerHTML = data.installed_apps.slice(0, 12).map(app => `
            <div class="bg-gray-800 p-4 rounded-xl flex flex-col items-center justify-center cursor-pointer active:scale-95 transition-transform opacity-50 border border-gray-700">
                <div class="w-10 h-10 bg-gray-600 rounded-lg mb-2"></div>
                <span class="text-xs text-center truncate w-full">${app.name}</span>
            </div>
        `).join('');
    } catch (e) {
        console.error("Failed to load apps:", e);
    }
}

async function launchKiosk(url) {
    if (navigator.vibrate) navigator.vibrate(100);
    try {
        const res = await fetch(`${apiUrl}/kiosk/launch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    } catch (e) {
        console.error("Launch Error:", e);
    }
}

async function killKiosk() {
    if (navigator.vibrate) navigator.vibrate([50, 50, 50]);
    try {
        const res = await fetch(`${apiUrl}/kiosk/kill`, { method: 'POST' });
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    } catch (e) {
        console.error("Kill Error:", e);
    }
}

// Init
connect();
fetchApps();
