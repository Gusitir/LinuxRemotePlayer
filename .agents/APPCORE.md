# APPCORE - mapa factual del codigo publicado 1.9.1

```yaml
verified_at: 2026-08-23T23:59:01-05:00
source_commit: "407bb66 (dirty: backup receipt metadata in APPCORE, CONTEXT, CURRENT and INDEX; pre-existing lochi.png preserved)"
producto: servicio Python/FastAPI + PWA estatica servido en LAN
```

Este mapa contiene arquitectura observada en el repo. No contiene planes, tareas, veredictos,
fases futuras ni estado de bugs.

## PURPOSE Y USERS

- Convierte una PC Linux con sesion grafica en un control de TV para hogares; el usuario opera
  desde cualquier telefono en la misma red mediante la PWA, sin app store.
- La interfaz sirve touchpad, teclado, transporte multimedia, lanzadores de sitios/apps y voz
  condicionada por licencia.

## CONSTRAINTS E INVARIANTS

- El runtime requiere Linux Debian/Ubuntu con systemd, uinput y sesion grafica; la PWA no tiene
  build frontend y el paquete debe construirse en filesystem Linux nativo, nunca desde `/mnt`.
- El control normal funciona por LAN y token de pairing; REST mutante y WebSocket aplican gates y
  allowlists server-side. CORS no habilita origins.
- El dispositivo no contiene credenciales de proveedores ni inferencia local; voz depende del proxy
  cloud y Together, mientras touch/input/kiosk permanecen en el equipo.
- La cadena de versionado es `VERSION` -> service worker -> paquete -> `latest.json`; el artefacto
  publicado debe conservar su SHA256.

## TOPOLOGIA Y ENTRYPOINTS

- `backend/run.py` detecta IP, crea CA/hoja HTTPS por maquina, monitoriza cambios de IP y arranca
  Uvicorn con `main:app`.
- `backend/main.py` crea la aplicacion FastAPI, monta `frontend/` como contenido estatico y lanza
  el panel idle como tarea de startup.
- `frontend/index.html` + `frontend/app.js` + CSS/manifest/service worker forman una PWA vanilla;
  no existe paso de build frontend.
- `backend/requirements.txt` declara FastAPI, Uvicorn, evdev, dotenv, httpx y segno.

## REST Y TRUST BOUNDARIES

- Sin autenticacion: `/health`, `/api/config`, `/api/ca` y `/api/icon/{app_id}`. La documentacion
  OpenAPI (`/docs`, `/redoc`, `/openapi.json`) solo existe con `LRP_DEV=true`.
- Solo loopback: `/api/pairing-pin`, `/api/pairing-token`, `/api/pairing-token/regenerate`,
  `/api/pairing-qr`, `/api/status`, `/status` y `/api/system/update`.
- Loopback o token: `/api/update/check`.
- Token `X-Auth-Token`: `/api/debug`, `/api/apps`, `/api/license/activate`, `/api/voice/toggle`,
  `/api/license/takeover`, `/api/license/status`, `/api/update/apply`, `/api/kiosk/launch`,
  `/api/kiosk/kill`, `/api/panel/show` y `/api/app/launch`.
- `POST /api/pair` no exige token: valida PIN de 6 digitos con expiracion de 120 segundos,
  limites globales y por IP, y devuelve el token local.
- CORS no permite origins; los endpoints mutantes validan token o loopback segun la ruta.
- `KioskLaunchBody` limita URL a `http://`/`https://`; `AppLaunchBody` limita id a 128 caracteres;
  las claves de media y teclas permitidas usan allowlists en `main.py` e `input_emulator.py`.

## WEBSOCKET

- `GET /ws` acepta token en query o recibe un frame JSON `{"type":"auth","token":...}`;
  la autenticacion inicial expira a los 3 segundos y falla con cierre 1008.
- Frames JSON observados: `ping`/`pong`, `input` gamepad, `pointer`, `text`, `combo` y la accion
  `media_control`. Los frames binarios son audio y requieren voz habilitada y autenticacion.
- Hay dos token buckets por conexion: rapido para pointer/ping y lento para el resto. Texto se
  trunca a 500 caracteres; audio se rechaza sobre 512000 bytes.
- El frontend envia el frame auth, heartbeat cada 10 segundos, reconexion con backoff y captura
  push-to-talk mediante `MediaRecorder`.

## PAIRING, PERSISTENCIA Y AUDIO

- `backend/auth.py` carga `PAIRING_TOKEN` desde entorno o `backend/.pairing_token`, generando el
  archivo con permisos 0600 si falta. Verifica igualdad exacta del token.
- `.env` guarda configuracion local, licencia y `ENABLE_VOICE`; `.license_cache` guarda hash de
  licencia y ultima validacion correcta con gracia offline de 72 horas.
- `backend/run.py` persiste CA, clave y hoja bajo `backend/certs`; la CA usa sufijo derivado de
  `machine-id` y la hoja incluye IP, hostname y localhost.
- `backend/ai_pipeline.py` no contiene claves de proveedor: envia audio, token, hash de device y
  targets al endpoint `AI_PROXY_URL` de Supabase y devuelve su JSON.
- La voz actual llama Together para STT Whisper e interpretacion Qwen desde `ai-proxy`; las
  acciones aceptadas son `launch_kiosk`, `media_control` y `search`.

## INPUT, KIOSK Y SERVICIO

- `backend/input_emulator.py` usa evdev/uinput para teclado virtual, texto, pointer y teclas de
  media; soporta mapas `us`, `es` y `latam`.
- `backend/kiosk.py` prefiere Firefox, luego Brave y Chromium; mantiene procesos y cierra ventanas
  mediante wmctrl o fallback KWin DBus.
- `scripts/install.sh` configura usuario, modo desktop/appliance, dependencias, uinput, UFW,
  Firefox, certificados y servicios systemd.
- `scripts/uninstall.sh` detiene servicios y ejecuta cleanup de licencia, udev, firewall, suspension,
  certificados, cache y entorno virtual.

## BUILD, PACKAGE Y UPDATE

- `scripts/build_deb.sh` ejecuta `scripts/check_css_sync.py`, copia `backend/`, `frontend/`,
  `scripts/` y `VERSION` a staging, estampa la version en `frontend/sw.js`, genera maintainer
  scripts y produce `dist/linuxremoteplayer_<VERSION>_all.deb` y su `.sha256`.
- El `postinst` crea el venv, instala requirements y genera `/usr/local/bin/lrp-update`; el wrapper
  conserva funciones y `main "$@"; exit $?` porque se reescribe durante `apt-get install`.
- `prerm` siempre detiene el servicio y solo deshabilita/limpia cuando `$1` es `remove`; el cleanup
  no se ejecuta en `upgrade`.
- `POST /api/update/apply` inicia `/usr/local/bin/lrp-update` con sudo; el fallback de desarrollo
  usa `scripts/update.sh`. El updater descarga `latest.json`, verifica SHA256 y reinstala el `.deb`.
- `website/install.sh` descarga el manifiesto, el `.deb`, verifica SHA256 y ejecuta apt; `latest.json`
  y `website/downloads/` contienen el canal publicado 1.9.1.

## CLOUD, DATABASE Y WEBSITE

- `supabase/functions/ai-proxy/index.ts` aplica tamano maximo, rate limit, kill-switch, limite
  global, licencia, activacion de device y cuota antes de llamar Together.
- `supabase/functions/validate-license/index.ts` valida licencia y puede consumir cuota mediante
  RPC. `send-feedback` filtra mensaje y limita envios antes de Resend.
- `supabase/functions/stripe-webhook/index.ts` permanece como codigo de webhook Stripe; el device
  no lo invoca directamente. Su despliegue no se puede demostrar desde este repo.
- `backend/supabase_schema.sql` define `licenses`, `plan_quotas`, `activations`, `usage_log`,
  `service_state` y RPC de licencia, activacion, cuota y voz.
- `website/` contiene landing ES/EN, docs, terminos, changelog, instalador, capturas, fuentes,
  `latest.json` y artefactos `.deb`/SHA publicados.
- `website/latest.json` apunta a version `1.9.1`, URL del `.deb` y SHA256; las paginas consumen el
  manifiesto para actualizar el enlace de descarga.

## BETA-FOUNDATION RELEASE SURFACES

- Stable release remains `1.9.1`; its public `latest.json` is stable-only and does not discover beta.
- The beta source/release `1.99.1` supports the explicit channel enum and durable beta-channel marker.
- The public beta manifest advertises `1.99.1` and the public beta installer is reachable; the beta
  artifact SHA256 is `8d4a19834eca05eda0e3f8b9c77817e6baaa19fb1bd823e30b5a726b6cb9c894`.
- The website is a minimal beta notice with curl enrollment; stable manifest and required assets
  remain reachable.
- These facts describe the closed distribution milestone only; no future STT, model or Needle
  implementation is claimed here.

## ACOPLAMIENTOS FACTUALES

- `VERSION` -> `build_deb.sh` -> `frontend/sw.js` -> paquete -> `website/latest.json`.
- `frontend/app.js` y `frontend/status.html` consumen las rutas REST; `app.js` consume `/ws`.
- `ai_pipeline.py` depende del contrato multipart/JSON de `ai-proxy`.
- `main.py` depende de `input_emulator.py`, `kiosk.py`, `discovery.py`, `audio.py` y `auth.py`.
- `backend/.env.example`, `website/install.sh`, `docs/ARCHITECTURE.md` y `docs/DEVELOPING.md`
  describen superficies de configuracion, instalacion y desarrollo.

## VERIFICACION DISPONIBLE

- No hay tests automatizados tracked en `tests/` ni en otro directorio de pruebas.
- El gate ejecutable del build es `python3 scripts/check_css_sync.py` mas la comprobacion de
  versionado del service worker; la documentacion tambien prescribe `node --check` y `py_compile`.
- La verificacion de device pertenece a `.agents/TESTING.md` y requiere hardware real; este job no
  ejecuta producto ni device.
