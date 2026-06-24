# **SYSTEM DIRECTIVE: Ecosistema Remote Kiosk \- Full Stack Architecture & Implementation Guide**

**TARGET AUDIENCE: LLM/AI CODE GENERATOR** **PURPOSE:** Single-source-of-truth for generating a Linux-based HTPC/Desktop remote control ecosystem (PWA \+ Python Backend \+ Cloud AI). Adhere strictly to the architectural decisions, tech stack, and workflows defined below.

## **1\. PROJECT OVERVIEW & CONSTRAINTS**

* **Core Product:** A "Plug & Play" remote control system bridging a mobile PWA (client) and a Linux PC (server) via local WebSockets, leveraging Cloud AI for voice commands.  
* **Target OS:** Linux (Debian/Ubuntu-based distributions, targeting KDE Plasma Bigscreen, Linux Mint, Ubuntu). Must be display-server agnostic (X11 and Wayland compatible).  
* **Hardware Constraints (Client PC):** Assume low-end hardware (old CPUs, limited RAM, no discrete GPU). Therefore, **NO LOCAL AI INFERENCE**. All heavy lifting (STT/LLM) MUST be offloaded to Cloud APIs to prevent CPU throttling and video playback stuttering.  
* **Monetization Strategy:** Lifetime license ($4.99) tied to a Supabase backend enforcing a "Fair Use Policy" (e.g., max 60 voice commands/day) to cap cloud API costs. Local inputs (buttons/gamepad) are unlimited.

## **2\. TECHNOLOGY STACK**

* **Frontend (Mobile PWA):** HTML5, CSS3 (Tailwind recommended), Vanilla JS (or lightweight framework). MediaRecorder API (audio capture), WebSockets API, Vibration API (haptics), LocalStorage (token persistence).  
* **Backend (Local Linux Server):** Python 3.10+, FastAPI (REST \+ WebSockets), uvicorn.  
* **Linux System Interaction (Python Libs):**  
  * evdev (python-evdev): For zero-latency virtual gamepad creation (uinput) and multimedia key injection. (Bypasses X11/Wayland restrictions).  
  * subprocess / os: For executing Kiosk mode browsers and process management.  
* **AI Cloud APIs:**  
  * **STT (Speech-to-Text):** NVIDIA NIM API (Nemotron-3.5-ASR) for real-time, high-accuracy, low-cost transcription. (Fallback: Groq Whisper API).  
  * **LLM (Intent Parsing):** OpenRouter API (Targeting free tier models like meta-llama/llama-3.1-8b-instruct:free). MUST return structured JSON only.  
* **Cloud Backend (Licensing & Limits):** Supabase (PostgreSQL, Auth, Edge Functions/Webhooks for Stripe, Row Level Security \- RLS).

## **3\. CORE MODULES & WORKFLOWS (IMPLEMENTATION SPECS)**

### **Module A: The Local Backend (FastAPI Core)**

* **Role:** The bridge between the PWA, the Linux OS, and Cloud APIs. Runs as a systemd service (multi-user.target).  
* **Initialization:** On startup, determine local IP, generate a session token (if not paired), and expose a pairing mechanism (QR code generation pointing to local IP \+ token).  
* **WebSocket Handler:** Maintains persistent connection with the PWA. Receives JSON payloads (button presses, gamepad events) and binary/base64 audio chunks.

### **Module B: Hardware Emulation (evdev integration)**

* **Directive:** Do NOT use xdotool or pyautogui as primary inputs due to Wayland incompatibility. Use kernel-level evdev.  
* **Gamepad Mode:** Instantiate a virtual gamepad device using evdev.UInput.  
  * Map PWA WebSocket events (e.g., {"event": "pad\_press", "btn": "A"}) to evdev.ecodes (e.g., BTN\_A).  
  * Required support: D-Pad, A, B, X, Y, Start, Select.  
* **Media Mode:** Inject standard multimedia keys (KEY\_PLAYPAUSE, KEY\_VOLUMEUP, KEY\_VOLUMEDOWN, KEY\_MUTE).

### **Module C: App Discovery & Kiosk Launcher**

* **Discovery Engine:** Scan standard FreeDesktop paths (/usr/share/applications/\*.desktop, \~/.local/share/applications/\*.desktop).  
  * Parse .desktop files. Filter by categories (e.g., AudioVideo, Network, Game).  
  * Serve a JSON list of installed apps to the PWA upon connection to populate the dynamic launcher UI.  
* **Kiosk Engine:** Launch WebApps securely.  
  * *Pre-launch:* Execute pkill \-f '--kiosk' to kill existing instances and free RAM.  
  * *Launch command:* Use subprocess.Popen to execute: chromium-browser \--app={TARGET\_URL} \--kiosk (or google-chrome).

### **Module D: The AI Pipeline (Voice Command Workflow)**

1. **PWA:** User holds "Mic" button \-\> Captures audio \-\> Sends payload to FastAPI.  
2. **Auth & Rate Limit:** FastAPI intercepts \-\> Queries Supabase: SELECT commands\_today FROM licenses WHERE token \= {session\_token}.  
   * If commands\_today \>= 60: Return error to PWA. Abort pipeline.  
   * If valid: Proceed.  
3. **STT Request:** FastAPI sends audio bytes to NVIDIA NIM API (Nemotron-3.5-ASR).  
   * *Expectation:* Rapid return of transcribed text (e.g., "pon un video de gatos en youtube").  
4. **LLM Request:** FastAPI sends text to OpenRouter API.  
   * *System Prompt Imperative:* "You are an intent parser for a TV remote. Output ONLY valid JSON. Allowed actions: 'launch\_kiosk', 'media\_control', 'search'. Example: {"action": "launch\_kiosk", "target": "youtube", "query": "gatos"}."  
5. **Execution & Logging:**  
   * FastAPI parses JSON.  
   * Executes local action (e.g., triggers Module C to launch YouTube with query params).  
   * Async call to Supabase to increment commands\_today.

### **Module E: Installation Automation (install.sh)**

* **Role:** Bash script for zero-friction user setup.  
* **Interactive Logic:** Prompt user: "Is this a dedicated TV/HTPC appliance? (Y/N)".  
  * **If Y (Appliance Mode):** Detect Display Manager (check paths /etc/sddm.conf.d/ or /etc/lightdm/). Inject Autologin configuration for the current $USER to bypass password screens on boot. Set FastAPI systemd service to start at graphical.target.  
  * **If N (Desktop Mode):** Preserve password security. Configure FastAPI as a user-level service (systemctl \--user enable ...).  
* **Dependencies:** Install python3-venv, python3-dev, required apt packages, create virtual environment, and pip install \-r requirements.txt. Configure ufw to allow traffic on FastAPI port (e.g., 5000).

## **4\. JSON SCHEMAS & DATA STRUCTURES**

### **A. Discovery Payload (FastAPI \-\> PWA)**

`{`  
  `"type": "discovery_sync",`  
  `"installed_apps": [`  
    `{"id": "vlc", "name": "VLC Media Player", "icon": "vlc", "type": "native"},`  
    `{"id": "kodi", "name": "Kodi", "icon": "kodi", "type": "native"}`  
  `],`  
  `"suggested_kiosks": [`  
    `{"id": "netflix", "name": "Netflix", "url": "[https://netflix.com](https://netflix.com)", "icon": "netflix"}`  
  `]`  
`}`

### **B. WebSocket Control Payload (PWA \-\> FastAPI)**

`{`  
  `"type": "input",`  
  `"device": "gamepad",`   
  `"action": "press",`  
  `"key": "BTN_A"`  
`}`

### **C. LLM Output Expectation (OpenRouter \-\> FastAPI)**

`{`  
  `"intent_confidence": 0.95,`  
  `"action": "launch_kiosk",`  
  `"parameters": {`  
    `"target_id": "youtube",`  
    `"search_query": "gatos divertidos"`  
  `}`  
`}`

## **5\. DEVELOPMENT STARTING POINT (PROMPT INSTRUCTIONS)**

When processing this directive to begin coding, begin by scaffolding the project structure. Prioritize the FastAPI core (main.py) and the evdev implementation (input\_emulator.py) to establish the low-latency local control baseline before integrating the external Cloud APIs.