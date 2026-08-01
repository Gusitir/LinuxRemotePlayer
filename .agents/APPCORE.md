# APPCORE — mapa del código (re-sincronizado 2026-07-31 contra el repo, base v1.9.1)
# Índice para AGENTES. Leerlo ANTES de grepear. La doc para humanos es docs/ARCHITECTURE.md.
# Conteos de líneas RE-MEDIDOS el 31/07: los diez estaban viejos y dos archivos distintos
# declaraban el mismo número. Si los tocás, medí ANTES de escribir (AGENTS §FORMATO).
#
# CONVENCIÓN DE ANCLAS: los pares tipo `T-70/B9` son HISTÓRICOS. El **T-NN** es el ancla
# durable y se encuentra en `git log --oneline --grep "T-70"`. El B/H es el hallazgo que lo
# origino y **ya esta CERRADO: no lo busques en CURRENT**, que solo lista lo abierto.
# Estan para explicar POR QUE ese codigo es asi, no para que sigas el puntero.

# DIRECTORIES
- /backend/: FastAPI (Python). /frontend/: PWA estática (vanilla JS, sin build).
- /scripts/: install, build_deb, update, uninstall, lrp-cleanup + check_css_sync.py (guard,
  corre en el build). *`bootstrap.sh` murio en T-80 al privatizarse el repo.*
- /website/: Vercel — landing ES+EN, install.sh, /downloads (.deb), latest.json (canal OTA).
- /supabase/functions/: Edge Functions (ai-proxy, validate-license, stripe-webhook[legacy],
  send-feedback). **Editarlas en el repo NO las despliega.**
- /.agents/: contexto IA. /docs/: para humanos. /.agents/archive/: fases cerradas, NO reusar.

# ENDPOINTS backend/main.py (1013 líneas · gate entre paréntesis)
- **Doc automática APAGADA** (T-63/H9): /docs, /redoc, /openapi.json solo existen con
  `LRP_DEV=true`. NO usar LRP_MODE para esto: `desktop` es modo de usuario, no de dev.
- Pairing: /api/pairing-pin (local) · POST /api/pair (LAN sin auth; PIN 6 dígitos un solo
  uso TTL 120s + anti-brute-force 5/IP) · /api/pairing-token (+/regenerate) (local) ·
  /api/pairing-qr (local, SVG segno; codifica `https://<ip>:<port>/?token=<PAIRING_TOKEN>`).
- Estado: /api/status (local) · /status (sirve status.html) · /health · /api/config ·
  /api/ca · /api/icon/{app_id} (abiertos por diseño).
  **/api/status y /api/config devuelven el MISMO `buy_url`**, vacío por defecto
  (PLACEHOLDER-PADDLE, se llena en T-51).
- Control (token): /api/apps (→ discovery_sync) · /api/kiosk/launch|kill · /api/panel/show ·
  /api/app/launch · /api/debug. TODOS vía asyncio.to_thread.
- Licencia (token): /api/license/activate|status|takeover.
  **activate persiste LICENSE_TOKEN Y `ENABLE_VOICE=true`** (T-71/B10: sin eso, quien ya era
  Pro se quedaba sin micrófono para siempre).
- Voz (token): **POST /api/voice/toggle** (T-68/D10) — el usuario puede apagarla; el arranque
  NUNCA pisa un `false` explícito.
- OTA: /api/update/check (local_or_token) · /api/update/apply (token → `sudo lrp-update`,
  habilitado por `/etc/sudoers.d/linuxremoteplayer`) · /api/system/update (local).
- `voice_enabled()` es FUNCIÓN, no constante: se lee en cada consulta porque activar la
  licencia escribe el .env y una constante no lo vería sin reiniciar.
- monitor_idle_panel: panel a los 45s si 0 clientes Y sin audio Y sin procesos propios.

# WS PROTOCOL (frontend→backend; handler en main.py)
- {"type":"auth","token"} (malo → close 1008) · {"type":"ping"} → pong (RTT en el HUD).
- {"type":"input","device":"gamepad","action":"press","key":"KEY_*"} (whitelist).
- {"type":"pointer","dx","dy"|"click":"left"|"right"|"back"(BTN_SIDE)|"scroll":N}.
- {"type":"text","text"} (≤500 chars, según KEYBOARD_LAYOUT).
- {"type":"combo","name":"browser_back"|"close_window"}.
- Audio binario → STT+LLM vía ai-proxy. Intents: launch_kiosk, media_control, search.
  Handler endurecido (T-26): target contra SUGGESTED_KIOSKS_MAP, media key contra whitelist.

# CRITICAL FILES
- backend/main.py (1013 ln): endpoints + WS + PinManager + SUGGESTED_KIOSKS + MEDIA_KEYS.
- backend/auth.py (89 ln): verify_access; licencia por Edge Function con cache de gracia 72h.
  **PAIRING_TOKEN: lee el env y si no está cae a `backend/.pairing_token`** (lo escribe
  install.sh). NO vive en el .env — creerlo costó dar B12 por cerrado sin estarlo.
- backend/run.py (262 ln): HTTPS self-healing. CA de dos niveles: `ca.pem` **con sufijo único
  por máquina** (`/etc/machine-id[:8]`, respaldo uuid4 — T-72/B14: sin eso, reinstalar creaba
  otra CA con el MISMO nombre y los navegadores daban SEC_ERROR_BAD_SIGNATURE) + hoja por
  IP/FQDN. `ensure_full_chain()` concatena ca.pem al cert.pem (idempotente) y se llama donde
  se configura uvicorn, NO dentro de ensure_cert — esa retorna temprano y no repararía una
  instalación existente. monitor_ip reinicia al cambiar la IP (regenera la hoja, NUNCA la CA).
- backend/input_emulator.py: UInput caps range(1,105). CHAR_KEYS por KEYBOARD_LAYOUT
  us|es|latam con AltGr. Gap: `< >` (KEY_102ND) y corchetes AltGr.
- backend/discovery.py: escanea .desktop, SIN filtro de categorías; solo NoDisplay/Hidden.
  (Okular duplicado = dos .desktop reales de Plasma Bigscreen, NO es defecto.)
- backend/kiosk.py: FIREFOX primero (perfil lrp-kiosk-ff), fallback brave/chromium.
  kill: SIGTERM +10s → SIGKILL. close_all: wmctrl → KWin DBus.
- backend/ai_pipeline.py: STT/LLM SOLO por ai-proxy; **sin llaves de IA en el device**.
  Stack validado: whisper-large-v3 + Qwen2.5-7B-Turbo (Together).
- backend/.env(.example): ENABLE_VOICE (lo enciende la activación de licencia, no el usuario),
  KEYBOARD_LAYOUT, LRP_MODE, LICENSE_*, BUY_URL (vacío, PLACEHOLDER-PADDLE), LRP_DEV=false.
- frontend/app.js (1583 ln): WS client (backoff, reconnect-on-wake, RTT HUD). Voz
  push-to-talk (micHeld anti-carrera, failsafe 8s, mime dinámico webm→mp4 iOS).
  **DEFAULT_SKIN, no FREE_SKIN**: las 4 skins son GRATIS desde T-62; `isLicensed` ya solo
  gatea la VOZ. updateAppHeight → `--app-h` (el porque, y por que NO vuelve
  `viewport-fit=cover`, esta comentado en `frontend/index.html`; detalle en PLAN §T-79).
- frontend/index.html (457 ln): status-bar `default` + .app-header con safe-area.
  Onboarding solo PIN. Selector de temas SIN candados.
- frontend/sw.js: CACHE = 'lrp-__LRP_VERSION__' (build_deb inyecta la versión → cada release
  invalida la caché). network-first shell, cache-first assets.
  **Trampa conocida:** `caches.match` compara la URL COMPLETA, así que un `?token=` no
  matchea el precache y devuelve "Offline" (bug del QR, sin arreglar).
- frontend/tailwind-lite.css (931 ln): subset a mano. Guard check_css_sync.py ABORTA el build
  si hay clase usada sin definir. NO detecta CSS muerto (al revés).
- frontend/skins.css (299 ln): 4 skins por `data-skin`. **Bloque PUENTE al final**: el
  marcado histórico asume fondo OSCURO, así que toda clase neutra nueva hay que puentearla
  o la skin clara se rompe.
- scripts/build_deb.sh (248 ln): empaqueta, inyecta VERSION en sw.js, corre el guard CSS,
  embebe lrp-setup / lrp-update / sudoers / postinst / prerm.
  **lrp-update: TODO en funciones y `main "$@"; exit $?` en la MISMA línea** — el postinst
  reescribe ese archivo mientras corre y bash lee por offset de byte; sin eso el OTA dejaba
  el servicio MUERTO (T-70/B9). Lleva `trap` que reinicia pase lo que pase.
  **prerm: la limpieza SOLO con `$1 = "remove"`** — dpkg lo invoca también en `upgrade` y ahí
  borraría las reglas del sistema de todos los equipos (T-64, trampa de T-19).
- scripts/lrp-cleanup.sh (69 ln): limpieza NO interactiva, **sin `set -e`, siempre `exit 0`**
  (un fallo suyo jamás puede abortar un `apt remove`). La comparten prerm y uninstall.sh.
  Libera licencia → udev → ufw → unmask sleep → borra `.env`, `.pairing_token`, `certs/` y la
  CA del sistema. **El borrado va ÚLTIMO: el primer paso lee el .env para liberar la licencia.**
- scripts/install.sh (385 ln): modo 1|2 → LRP_MODE; LRP_NOSLEEP → mask sleep/suspend;
  instala firefox + deps; policies.json (uBlock + CA + EME); **CA al trust del sistema y al
  NSS de Firefox, borrando antes la entrada previa** (T-72); UFW con OpenSSH primero.
- website/install.sh: `curl | sudo bash`. **NO usar `exec < /dev/tty`**: bash lee el script
  desde stdin y reemplazarlo corta el instalador a la mitad en silencio (T-67/B7).

# SALES PIPELINE
- Cliente = PWA (pairing por PIN). Servidor = .deb vía website/install.sh. OTA por latest.json.
- Pagos: **PADDLE** (Stripe no opera en Ecuador). El `stripe-webhook` es legacy.
- Licencia Pro única lifetime; 1 dispositivo con mudanza autoservicio.
- FALTA PARA VENDER: alta de Paddle, correo verificado, capturas.

# reindex: tras cada release, verificar contra el repo REAL (grep endpoints/rutas/tamaños),
# corregir lo rancio, borrar lo muerto. Nunca escribir lo no verificado.
# Protocolo detallado: .agents/skills/manage_context/SKILL.md
