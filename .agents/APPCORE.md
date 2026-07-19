# APPCORE — mapa del código (re-sincronizado por Claude 2026-07-18, base v1.7.3)

# DIRECTORIES
- /backend/: FastAPI server (Python). /frontend/: PWA estática (vanilla JS, sin build).
- /scripts/: bash (install, build_deb, update, uninstall, bootstrap) + check_css_sync.py.
- /website/: Vercel landing + install.sh bootstrap + /downloads (.deb) + latest.json.
- /supabase/functions/: Edge Functions (stripe-webhook, validate-license, send-feedback).
- /.agents/: contexto IA (AGENTS, CURRENT, PLAN, TESTING, APPCORE, archive/, AUDITS/,
  skills/manage_context = skill `reindex`).

# ENDPOINTS backend/main.py (verificado con grep 2026-07-18; gate entre paréntesis)
- Pairing: /api/pairing-pin (local), POST /api/pair (LAN sin auth, PIN 6 dígitos un solo
  uso TTL 120s + anti-brute-force 5/IP), /api/pairing-token (+/regenerate) (local),
  /api/pairing-qr (local, SVG segno).
- Estado: /api/status (local; version, mode[LRP_MODE], licensed, adblock_status, ips,
  clientes, uinput_ok, buy_url — la latencia la mide el panel client-side),
  /status (local, sirve status.html), /health /api/config /api/ca /api/icon/{app_id}
  (abiertos por diseño).
- Control: /api/apps (token; responde {"type":"discovery_sync", suggested_kiosks,
  installed_apps}), /api/kiosk/launch|kill, /api/panel/show, /api/app/launch (token;
  TODOS via asyncio.to_thread — C-01, no bloquear event loop), /api/debug (token).
- Licencia: /api/license/activate|status (token; activate persiste LICENSE_TOKEN en
  .env + os.environ).
- OTA: /api/update/check (local_or_token; lee latest.json), /api/update/apply (token ->
  sudo lrp-update), /api/system/update (local -> update.sh).
- monitor_idle_panel: panel a los 45s si 0 clientes Y sin audio (pactl sink-inputs con
  env=gui_env(); requiere pulseaudio-utils) Y sin procesos propios.

# WS PROTOCOL (frontend->backend; handler en main.py ~700-880)
- {"type":"auth","token"} (malo -> close 1008) / {"type":"ping"} -> {"type":"pong"}
  (el cliente mide RTT y lo muestra en el HUD).
- {"type":"input","device":"gamepad","action":"press","key":"KEY_*"} (whitelist).
- {"type":"pointer","dx","dy"|"click":"left"|"right"|"back"(BTN_SIDE)|"scroll":N}.
- {"type":"text","text"} (<=500 chars; teclas según KEYBOARD_LAYOUT).
- {"type":"combo","name":"browser_back"(->BTN_SIDE, fallback Alt+Left)|"close_window"}.
- Intents de voz (tras audio binario -> STT+LLM): launch_kiosk, media_control, search.

# CRITICAL FILES (1-3 líneas c/u)
- backend/main.py (~880 líneas): todo lo anterior + PinManager + SUGGESTED_KIOSKS.
- backend/auth.py: verify_access (PAIRING_TOKEN); licencia vía Edge Function
  (LICENSE_API_URL) con cache de gracia 72h. Sin secretos Supabase en dispositivo.
- backend/input_emulator.py: UInput caps range(1,105) (incluye RIGHTALT=100).
  CHAR_KEYS por KEYBOARD_LAYOUT us|es|latam con AltGr; "/"=KPSLASH universal.
  Gap conocido: < > (KEY_102ND) y corchetes AltGr. VirtualMouse: BTN_LEFT/RIGHT/SIDE.
- backend/kiosk.py: find_browser FIREFOX primero (perfil ~/.config/lrp-kiosk-ff;
  snap: ~/snap/firefox/common/lrp-kiosk), fallback brave/chromium (--user-data-dir
  ~/.config/lrp-kiosk). kill: SIGTERM + espera 10s -> SIGKILL. close_all: wmctrl
  (X11) -> fallback KWin DBus (qdbus6|qdbus, unloadScript+loadScript+run,
  DBUS addr desde XDG_RUNTIME_DIR/bus). adblock_status: shields|ubo-firefox|ubol|none.
- backend/run.py: HTTPS self-healing, CA dos niveles (ca.pem estable + leaf por
  IP/FQDN), monitor_ip reinicia bajo systemd al cambiar IP.
- backend/ai_pipeline.py: STT/LLM cloud configurable por env (CLOUD_STT_URL/KEY/MODEL,
  CLOUD_LLM_*). Producción verificada en Together: STT nemotron-3.5-asr-streaming-0.6b,
  LLM meta-llama/Llama-3.1-8B-Instruct. Modo local Whisper+Ollama intacto.
  PENDIENTE VENTA: ai-proxy Edge Function (claves fuera del dispositivo).
- backend/.env(.example): ENABLE_VOICE, CLOUD_*, KEYBOARD_LAYOUT, LRP_MODE
  (appliance|desktop, escrito por install.sh), PAIRING_TOKEN, LICENSE_*, BUY_URL.
- frontend/index.html (~85KB): status-bar black-translucent + .app-header con
  max(env(safe-area-inset-top)) en standalone; altura por var(--app-h). Onboarding
  SOLO PIN (sin token manual). mic-overlay (voz). Iconos Lucide inline
  (borrar=delete, nav=move, panel=activity). Media query max-height:750px (16:9).
- frontend/app.js (~1500 líneas): WS client (backoff, reconnect-on-wake, RTT HUD).
  Voz push-to-talk: micHeld anti-carrera post-getUserMedia, failsafe 8s, overlay,
  cancel <250ms/pointerleave. createAppTile: is_native -> /api/icon/{id};
  con url -> setTileFavicon (DDG -> Google S2 -> LETRA); × si custom_ o is_native
  (nativos anclados viven en localStorage custom_apps con is_native:true).
  updateAppHeight -> --app-h (load/resize/orientation/pageshow/visualViewport).
- frontend/status.html: panel TV. /api/pairing-qr, latencia RTT client-side, modo
  TV/Escritorio, badge adblock, buy-link clicable, meta refresh 3600, Mantenimiento.
- frontend/sw.js: CACHE lrp-v16; network-first shell (/, index, app.js),
  cache-first assets. BUMP del nombre al cambiar assets cache-first.
- frontend/tailwind-lite.css: subset a mano + reset border-box GLOBAL + utilidades
  compiladas. Guard: scripts/check_css_sync.py (IGNORE_CLASSES=4) corre en build_deb.
- scripts/install.sh (= lrp-setup): modo 1|2 -> LRP_MODE en .env; LRP_NOSLEEP ->
  mask sleep/suspend targets (uninstall los unmask); KEYBOARD_LAYOUT (localectl +
  prompt); instala firefox-esr||firefox + pulseaudio-utils wmctrl qdbus libnss3-tools;
  escribe /etc/firefox/policies/policies.json SIEMPRE (uBlock force_installed +
  Certificates.Install ca.pem + EME); certutil NO-interactivo (pwfile + </dev/null);
  CA a trust del sistema POST-arranque (espera ca.pem 30s); UFW OpenSSH||22 fallback;
  mensaje final PIN-first.
- scripts/build_deb.sh: empaqueta .deb; embebe lrp-setup, lrp-update y sudoers.
  lrp-update: RE-EXEC vía systemd-run --unit=lrp-update-job (escapa del cgroup del
  servicio — fix T-14; sin esto el OTA se suicida), log a /tmp/lrp-update.log,
  restart final. Recommends: firefox-esr|firefox, pulseaudio-utils.
- website/install.sh: bootstrap curl|bash -> baja .deb por latest.json + sha256 ->
  apt install -> encadena lrp-setup (llamada directa, NO exec).

# SALES PIPELINE
- Cliente=PWA (PIN pairing). Servidor=.deb vía website/install.sh. OTA por latest.json.
- Stripe TEST -> webhook -> licencia por email (Resend) -> activar en app.
- Licencia Pro ÚNICA lifetime cubrirá todo lo premium (voz, APK, archivos, skins) —
  ver roadmap PH15-PH18 en PLAN.md.
- FALTA PARA VENDER: ai-proxy, Stripe LIVE, dominio propio + Resend verificado.
