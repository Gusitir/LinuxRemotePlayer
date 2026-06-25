const statusEl = document.getElementById('status');
const suggestedGrid = document.getElementById('suggested-grid');
const appsGrid = document.getElementById('apps-grid');
let ws;
let mediaRecorder;
let audioChunks = [];

const host = window.location.hostname === '' || window.location.hostname === 'localhost' ? '127.0.0.1' : window.location.hostname;
const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
const token = localStorage.getItem('license_token') || 'guest';
const port = window.location.port || '8000';
const wsUrl = `${protocol}${host}:${port}/ws?token=${token}`;
const apiUrl = `${window.location.protocol}//${host}:${port}/api`;

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

    ws.onmessage = (e) => {
        try {
            const res = JSON.parse(e.data);
            if (res.status === 'processing') {
                statusEl.textContent = res.message;
                statusEl.className = 'text-purple-400 font-bold';
            } else if (res.status === 'success' || res.status === 'error') {
                statusEl.textContent = res.status === 'error' ? `Error: ${res.message}` : 'Connected';
                statusEl.className = res.status === 'error' ? 'text-red-500 font-bold' : 'text-green-500 font-bold';
            }
        } catch (err) {}
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

function sendMedia(mediaKey) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        const payload = { action: "media_control", parameters: { key: mediaKey } };
        ws.send(JSON.stringify(payload));
        if (navigator.vibrate) navigator.vibrate(30);
    }
}

async function startVoice() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        alert("Audio capture is not supported.");
        return;
    }
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });

        mediaRecorder.ondataavailable = e => {
            if (e.data.size > 0) audioChunks.push(e.data);
        };

        mediaRecorder.onstop = () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(audioBlob);
            }
            audioChunks = [];
            stream.getTracks().forEach(track => track.stop());
        };

        mediaRecorder.start();
        if (navigator.vibrate) navigator.vibrate(50);
        statusEl.textContent = 'Listening...';
        statusEl.className = 'text-blue-400 font-bold';
    } catch (e) {
        console.error("Mic access denied", e);
    }
}

function stopVoice() {
    if (mediaRecorder && mediaRecorder.state === "recording") {
        mediaRecorder.stop();
        if (navigator.vibrate) navigator.vibrate([50, 50]);
        statusEl.textContent = 'Processing AI...';
        statusEl.className = 'text-purple-400 font-bold';
    }
}

async function fetchApps() {
    try {
        const res = await fetch(`${apiUrl}/apps`);
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const data = await res.json();

        suggestedGrid.innerHTML = (data.suggested_kiosks || []).map(app => `
            <div onclick="launchKiosk('${app.url}')" class="bg-gray-800 p-4 rounded-xl flex flex-col items-center justify-center cursor-pointer active:scale-95 transition-transform border border-gray-700">
                <div class="w-12 h-12 bg-blue-600 rounded-full mb-2 flex items-center justify-center text-xl font-bold">${app.name[0]}</div>
                <span class="text-xs text-center truncate w-full">${app.name}</span>
            </div>
        `).join('');

        appsGrid.innerHTML = (data.installed_apps || []).slice(0, 12).map(app => `
            <div onclick="launchApp('${app.id}')" class="bg-gray-800 p-4 rounded-xl flex flex-col items-center justify-center cursor-pointer active:scale-95 transition-transform border border-gray-700">
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
            headers: { 'Content-Type': 'application/json', 'X-Auth-Token': token },
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
        const res = await fetch(`${apiUrl}/kiosk/kill`, { method: 'POST', headers: { 'X-Auth-Token': token } });
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    } catch (e) {
        console.error("Kill Error:", e);
    }
}

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

connect();
fetchApps();
