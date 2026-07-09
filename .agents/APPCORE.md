# DIRECTORIES
- /backend/: FastAPI server (Python).
- /frontend/: PWA static files (vanilla JS, no build step). Also serves TV status panel.
- /scripts/: bash (install, build_deb, update, uninstall, bootstrap).
- /website/: Vercel landing + Stripe buy link + /downloads (.deb) + latest.json + install.sh.
- /supabase/functions/: Edge Functions (stripe-webhook, validate-license, send-feedback).

# CRITICAL FILES
- backend/main.py: FastAPI + WS router. REST: /api/config(version,buy_url,voice), /api/apps,
  /api/kiosk/launch|kill, /api/app/launch, /api/debug, /api/ca, /api/license/status|activate,
  /api/update/check(require_local_or_token)|apply, /api/system/update, /api/panel/show,
  /api/status, /api/pairing-pin(require_local), /api/pair(LAN,no auth), /api/pairing-qr,
  /api/pairing-token(+regenerate). PinManager (6-digit, 120s TTL, brute-force guard).
  connected_clients counter + monitor_idle_panel() background task. SUGGESTED_KIOSKS catalog.
  require_local / require_local_or_token / require_token deps.
- backend/auth.py: verify_access (local PAIRING_TOKEN only). validate_license_and_increment
  + is_license_valid_cached_or_online -> HTTPS to LICENSE_API_URL (Edge Function); 72h offline
  grace cache (.license_cache). NO supabase secrets on device.
- backend/audio.py: volume/mute via wpctl(PipeWire)/pactl(Pulse)/amixer(ALSA). Used for
  KEY_VOLUMEUP/DOWN/MUTE (uinput media keys don't work without a DE daemon).
- backend/input_emulator.py: UInput. ALLOWED_KEYS whitelist (incl KEY_LEFTMETA). COMBOS
  (browser_back=Alt+Left, close_window=Alt+F4) via press_combo. Startup guard logs missing caps.
- backend/kiosk.py: Chromium kiosk. close_all() kills kiosk + tracked native procs.
  is_ubol_active(). --load-extension=<uBOL in ~/lrp-extensions/ubol> (+ /opt fallback;
  snap Chromium canNOT read /opt). gui_env (DISPLAY/WAYLAND/XAUTHORITY).
- backend/run.py: self-healing HTTPS. Two-tier CA (ca.pem + leaf per IP+FQDN). monitor_ip
  self-restarts under systemd on IP change.
- backend/ai_pipeline.py: STT+LLM (NVIDIA/OpenRouter or local). Only if ENABLE_VOICE=true.
  NOTE: for sale, keys must move to an ai-proxy Edge Function (NOT yet done).
- backend/.env.example: ENABLE_VOICE, LICENSE_API_URL, LICENSE_TOKEN, GITHUB_REPO, BUY_URL,
  NVIDIA/OPENROUTER keys, PAIRING_TOKEN.
- frontend/index.html: remote UI (apps row, touchpad+nav-overlay+scroll, mic-row, utility row
  [keyboard/backspace/nav-mode/panel/OS-menu], control cluster). PIN pairing screen. Drawers:
  apps + settings (categories: Licencia/Temas/Actualización/Social/Tutoriales). Reicon SVG icons.
- frontend/app.js: WS client (auth frame, heartbeat, reconnect-on-wake). touchpad pointer +
  nav mode. PIN pair (checkPinInput->/api/pair). license activate/status. skins (setSkin,
  license-gated). hideable apps. coach-marks tour. update check/apply. feedback.
- frontend/status.html: TV status panel (/status, require_local). PIN + QR + live status +
  Mantenimiento (update button + change-mode tutorial). Auto-opens on idle (APPLIANCE_IDLE_PANEL).
- frontend/skins.css: [data-skin] dark/day/neon(Pro)/anime(Pro). CSS vars.
- frontend/tailwind-lite.css: hand-compiled utility subset (offline). MUST stay in sync with
  markup — missing classes silently break layout (see .hidden / overflow bugs).
- frontend/sw.js: service worker (CACHE lrp-v15; network-first shell, cache-first assets).
- scripts/install.sh: interactive core (invoked by lrp-setup). TARGET_USER resolution,
  uinput, avahi, UFW(allow SSH first), systemd (Appliance/Desktop, idempotent), uBOL, panel
  autolaunch, KDE .desktop entry.
- scripts/build_deb.sh: builds .deb; embeds lrp-setup + lrp-update + sudoers drop-in +
  /usr/share/applications entry + hicolor icon.
- scripts/update.sh: thin wrapper -> sudo /usr/local/bin/lrp-update (OTA via latest.json).

# WS PROTOCOL (frontend->backend)
- {"type":"auth","token":...} / {"type":"ping"} (->pong)
- {"type":"input","device":"gamepad","action":"press","key":"KEY_*"} (whitelisted)
- {"type":"combo","name":"browser_back"|"close_window"}
- {"type":"pointer","dx","dy"|"click":"left"|"right"|"scroll":N}
- {"type":"text","text":...} (<=500 chars)
- {"action":"media_control","parameters":{"key":"KEY_*"}} (audio.py for vol/mute)
- binary audio -> STT/LLM (only ENABLE_VOICE + valid license)

# SALES PIPELINE
- Client=PWA (PIN pairing, no store). Server=.deb via curl website/install.sh.
- Stripe (TEST now) -> webhook -> license key by email (Resend) -> activate in app.
- License validation + (future) AI all via Edge Functions; NO keys on device.
- REMAINING FOR SALE: real Stripe live, ai-proxy Edge Function for voice, own domain +
  Resend domain verification.
