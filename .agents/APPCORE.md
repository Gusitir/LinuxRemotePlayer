# APPCORE — mapa del código (re-sincronizado por Claude 2026-07-20, base v1.7.7)

# DIRECTORIES
- /backend/: FastAPI server (Python). /frontend/: PWA estática (vanilla JS, sin build).
- /scripts/: bash (install, build_deb, update, uninstall, bootstrap) + check_css_sync.py.
- /website/: Vercel landing + install.sh bootstrap + /downloads (.deb) + latest.json.
- /supabase/functions/: Edge Functions (stripe-webhook, validate-license, send-feedback).
- /.agents/: contexto IA (README índice, WORKFLOW proceso, CURRENT, PLAN, PLAN_v1.8,
  TESTING, APPCORE, archive/, AUDITS/, skills/manage_context = skill `reindex`).

# ENDPOINTS backend/main.py (gate entre paréntesis)
- Pairing: /api/pairing-pin (local), POST /api/pair (LAN sin auth, PIN 6 dígitos un solo
  uso TTL 120s + anti-brute-force 5/IP), /api/pairing-token (+/regenerate) (local),
  /api/pairing-qr (local, SVG segno).
- Estado: /api/status (local; version, mode[LRP_MODE], licensed, adblock_status, ips,
  clientes, uinput_ok, buy_url — latencia la mide el panel client-side),
  /status (local, sirve status.html), /health /api/config /api/ca /api/icon/{app_id}
  (abiertos por diseño).
- Control: /api/apps (token; responde {"type":"discovery_sync", suggested_kiosks,
  installed_apps}), /api/kiosk/launch|kill, /api/panel/show, /api/app/launch (token;
  TODOS via asyncio.to_thread — C-01), /api/debug (token).
- Licencia: /api/license/activate|status (token; activate persiste LICENSE_TOKEN en
  .env + os.environ).
- OTA: /api/update/check (local_or_token; lee latest.json), /api/update/apply (token ->
  sudo lrp-update), /api/system/update (local -> update.sh).
- monitor_idle_panel: panel a los 45s si 0 clientes Y sin audio (pactl sink-inputs con
  env=gui_env(); requiere pulseaudio-utils) Y sin procesos propios.

# WS PROTOCOL (frontend->backend; handler en main.py ~700-880)
- {"type":"auth","token"} (malo -> close 1008) / {"type":"ping"} -> {"type":"pong"}
  (cliente mide RTT y lo muestra en HUD).
- {"type":"input","device":"gamepad","action":"press","key":"KEY_*"} (whitelist).
- {"type":"pointer","dx","dy"|"click":"left"|"right"|"back"(BTN_SIDE)|"scroll":N}.
- {"type":"text","text"} (<=500 chars; teclas según KEYBOARD_LAYOUT).
- {"type":"combo","name":"browser_back"(->BTN_SIDE, fallback Alt+Left)|"close_window"}.
- Audio binario (<=5MB HOY; bajar a ~512KB en v1.9/anti-abuso) -> STT+LLM. Intents:
  launch_kiosk, media_control, search. Handler ENDURECIDO (T-26): target.lower().strip()
  contra SUGGESTED_KIOSKS_MAP; media key .upper()+prefijo KEY_ contra whitelist; errores
  con etapa ("Voz: error STT/LLM/app no reconocida"); log de tamaño de binario recibido.

# CRITICAL FILES (1-3 líneas c/u)
- backend/main.py (~880 líneas): endpoints + WS + PinManager + SUGGESTED_KIOSKS(_MAP) +
  MEDIA_KEYS. main.py:~53 usa CLOUD_STT_KEY/CLOUD_LLM_KEY (NO NVIDIA_KEY — crasheaba).
  El handler de voz pasa valid_targets=[k["id"] for k in SUGGESTED_KIOSKS] a parse_intent.
- backend/auth.py: verify_access (PAIRING_TOKEN); licencia vía Edge Function
  (LICENSE_API_URL) con cache de gracia 72h. Sin secretos Supabase en dispositivo.
- backend/input_emulator.py: UInput caps range(1,105) (incluye RIGHTALT=100).
  CHAR_KEYS por KEYBOARD_LAYOUT us|es|latam con AltGr; "/"=KPSLASH universal.
  Gap conocido: < > (KEY_102ND) y corchetes AltGr. VirtualMouse: BTN_LEFT/RIGHT/SIDE.
- backend/discovery.py: get_installed_apps escanea .desktop. SIN filtro de categorías
  (T-25: SKIP_CATEGORIES eliminado -> Dolphin/terminal/apps de sistema visibles);
  SOLO filtra NoDisplay/Hidden.
- backend/kiosk.py: find_browser FIREFOX primero (perfil ~/.config/lrp-kiosk-ff;
  snap: ~/snap/firefox/common/lrp-kiosk), fallback brave/chromium. kill: SIGTERM +
  espera 10s -> SIGKILL. close_all: wmctrl (X11) -> fallback KWin DBus (qdbus6|qdbus,
  unloadScript+loadScript+run, DBUS addr desde XDG_RUNTIME_DIR/bus).
  adblock_status: shields|ubo-firefox|ubol|none.
- backend/run.py: HTTPS self-healing, CA dos niveles (ca.pem estable + leaf por
  IP/FQDN), monitor_ip reinicia bajo systemd al cambiar IP.
- backend/ai_pipeline.py: STT/LLM cloud configurable por env (CLOUD_STT_URL/KEY/MODEL,
  CLOUD_LLM_*). STACK PRODUCCIÓN VALIDADO (2026-07-19): STT openai/whisper-large-v3,
  LLM Qwen/Qwen2.5-7B-Instruct-Turbo en Together (nemotron-streaming y Llama-3.1 dan
  400). transcribe_audio detecta formato por magic bytes (webm 0x1A45DFA3 / mp4 'ftyp'
  offset 4). parse_intent(transcription, valid_targets): system_prompt DINÁMICO (apps
  inyectadas, jamás hardcodeadas) + keys media exactas + ejemplos ES. SOLO cloud: modo IA
  local + MOCK + defaults NVIDIA/OpenRouter ELIMINADOS (T-33); defaults ahora = Together.
  PENDIENTE VENTA: ai-proxy Edge Function (claves fuera del dispositivo).
- backend/.env(.example): ENABLE_VOICE, CLOUD_* (whisper+qwen), KEYBOARD_LAYOUT,
  LRP_MODE (escrito por install.sh), PAIRING_TOKEN, LICENSE_*, BUY_URL.
- frontend/index.html (~85KB): status-bar black-translucent + .app-header con
  max(env(safe-area-inset-top)) en standalone; altura por var(--app-h). Onboarding
  SOLO PIN. mic-overlay + ejemplos de comandos. Card "Comandos de voz" en Ajustes.
  Registro SW con reg.update() en visibilitychange/pageshow + controllerchange->reload
  (T-28, auto-actualización). Iconos Lucide inline. Media query max-height:750px.
- frontend/app.js (~1500 líneas): WS client (backoff, reconnect-on-wake, RTT HUD).
  Voz push-to-talk: micHeld anti-carrera, failsafe 8s, overlay, cancel <250ms; mime
  dinámico (isTypeSupported webm->mp4->default, iOS) + toast en error. createAppTile:
  is_native -> /api/icon/{id}; con url -> setTileFavicon (DDG->S2->LETRA); × si custom_
  o is_native. #voice-apps-list poblado desde lastSuggestedKiosks (loadApps). Hint de
  voz primera vez (localStorage lrp_voice_hint_shown). updateAppHeight -> --app-h.
- frontend/status.html: panel TV. /api/pairing-qr, latencia RTT, modo TV/Escritorio,
  badge adblock, buy-link clicable, meta refresh 3600, Mantenimiento.
- frontend/sw.js: CACHE = 'lrp-__LRP_VERSION__' (placeholder; build_deb inyecta la
  versión real -> cada release invalida cache -> PWA recibe assets frescos).
  network-first shell (/, index, app.js), cache-first assets.
- frontend/tailwind-lite.css: subset a mano + reset border-box GLOBAL + utilidades.
  Guard: scripts/check_css_sync.py (IGNORE_CLASSES~4) corre en build_deb (ABORTA si
  hay clase usada sin definir; ya cazó deriva real en T-29).
- scripts/install.sh (= lrp-setup): modo 1|2 -> LRP_MODE en .env; LRP_NOSLEEP -> mask
  sleep/suspend (uninstall unmask); KEYBOARD_LAYOUT; instala firefox-esr||firefox +
  pulseaudio-utils wmctrl qdbus libnss3-tools; escribe /etc/firefox/policies/policies.json
  SIEMPRE (uBlock force_installed + Certificates.Install ca.pem + EME); certutil
  NO-interactivo (pwfile + </dev/null); CA a trust del sistema POST-arranque (espera
  ca.pem 30s); UFW OpenSSH||22 fallback; mensaje final PIN-first.
- scripts/build_deb.sh: empaqueta .deb; inyecta VERSION en sw.js + guard; embebe
  lrp-setup, lrp-update, sudoers, prerm. lrp-update: RE-EXEC vía systemd-run
  --unit=lrp-update-job (escapa del cgroup del servicio — fix T-14) + restart por
  EXISTENCIA del unit (T-19, no is-enabled). prerm: stop+disable SOLO en "remove"
  (T-19, upgrade solo stop). Recommends: firefox-esr|firefox, pulseaudio-utils.
- website/install.sh: bootstrap curl|bash -> baja .deb por latest.json + sha256 ->
  apt install -> encadena lrp-setup (llamada directa, NO exec).

# SALES PIPELINE
- Cliente=PWA (PIN pairing). Servidor=.deb vía website/install.sh. OTA por latest.json.
- Stripe TEST -> webhook -> licencia por email (Resend) -> activar en app.
- Licencia Pro ÚNICA lifetime cubrirá todo lo premium (voz, APK, archivos, skins,
  gamepad) — roadmap PH15-PH19 en PLAN.md. Licencia 1-dispositivo + rotación: v1.9.
- FALTA PARA VENDER: ai-proxy, Stripe LIVE, dominio propio + Resend verificado.

# reindex: tras cada release o si el índice miente, verificar contra el repo REAL
# (grep endpoints/rutas/protocolos), corregir rancio, añadir nuevo, borrar muerto.
# Nunca escribir lo no verificado. Anotar "APPCORE re-sincronizado <fecha>" en CURRENT.
