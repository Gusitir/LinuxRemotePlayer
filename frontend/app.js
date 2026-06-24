const statusEl = document.getElementById('status');
let ws;

function connect() {
    const host = window.location.hostname === '' || window.location.hostname === 'localhost' ? '127.0.0.1' : window.location.hostname;
    const url = `ws://${host}:8000/ws`;
    ws = new WebSocket(url);

    ws.onopen = () => {
        statusEl.textContent = 'Connected';
        statusEl.className = 'text-green-500 text-sm';
    };

    ws.onclose = () => {
        statusEl.textContent = 'Disconnected - Retrying...';
        statusEl.className = 'text-red-500 text-sm';
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
        
        if (navigator.vibrate) {
            navigator.vibrate(50);
        }
    }
}

connect();
