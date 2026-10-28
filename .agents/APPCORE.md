# APPCORE - mapa factual del codigo 1.99.2 (base estable 1.9.1)

```yaml
verified_at: 2026-10-17T07:30:00-05:00
source_commit: "50da3ca (worktree codex/debian-foundation HEAD; T-132..T-142 apto, G4 APTO)"
producto: servicio Python/FastAPI + PWA estatica servido en LAN (LRP OS Appliance v2.0-dev)
```

Este mapa contiene arquitectura observada en el repo. No contiene planes, tareas, veredictos,
fases futuras ni estado de bugs.

## PURPOSE Y USERS

- Convierte una PC Linux con sesion grafica en un control de TV para hogares; el usuario opera
  desde cualquier telefono en la misma red mediante la PWA, sin app store.
- La interfaz sirve touchpad con franja de scroll independiente, teclado, transporte multimedia
  mediante rueda radial Mantatomic SVG, dock de accesos rápidos dinámicos (Quick Dock), LRP App
  Hub con catálogo y búsqueda, y comandos de voz 100% locales en CPU.

## CONSTRAINTS E INVARIANTS

- El runtime requiere Debian 13 stable amd64 minimal con systemd, uinput y sesion grafica
  Xorg/Openbox administrada por LRP; la PWA no tiene build frontend y el paquete debe
  construirse en filesystem Linux nativo, nunca desde `/mnt`.
- El control normal funciona por LAN y token de pairing; REST mutante y WebSocket aplican gates y
  allowlists server-side. CORS no habilita origins.
- El runtime v2.0 opera 100% offline y local en hardware mínimo (Intel Core i5-3470, 8 GB RAM,
  Intel HD Graphics 2500); voz opera con whisper.cpp AVX1 y motor NLU local Needle 2 en CPU
  (`backend/local_intent.py`), sin depender de Supabase `ai-proxy` ni Together en runtime.
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
- Loopback o token: `/api/update/check` y `/api/panel/show` (permite lanzamiento inmediato de OSD por scripts locales).
- Token `X-Auth-Token`: `/api/debug`, `/api/apps`, `/api/update/apply`, `/api/kiosk/launch`,
  `/api/kiosk/kill` y `/api/app/launch`.
- Plataforma de sistema (`/api/system/*`, con token o loopback):
  - Audio PipeWire: `GET /api/system/audio`, `POST /api/system/audio/sink`, `POST /api/system/audio/volume`.
  - Red y periféricos: `GET /api/system/wifi`, `POST /api/system/wifi/connect`, `GET /api/system/bluetooth`,
    `GET /api/system/display`, `GET /api/system/onboarding`, `POST /api/system/onboarding/hotspot/{start,stop}`.
  - Energía HTPC: `POST /api/system/power/{suspend|reboot|poweroff|restart-service}`.
- PH24/T-144: `/api/license/status`, `/api/license/activate` y `/api/license/takeover` son **stubs locales
  inertes** (`licensed=true`, `source=local`, `plan=appliance`), sin red ni estado; T-145 los retira del
  backend y del frontend. `/api/status` ya no consulta licencia.
- `POST /api/pair` no exige token: valida PIN de 6 digitos con expiracion de 120 segundos,
  limites globales y por IP, y devuelve el token local.
- CORS no permite origins; los endpoints mutantes validan token o loopback segun la ruta.
- `KioskLaunchBody` limita URL a `http://`/`https://`; `AppLaunchBody` limita id a 128 caracteres;
  las claves de media y teclas permitidas usan allowlists en `main.py` e `input_emulator.py`.
- Lanzamiento de panel OSD: inmediato en arranque y ante ausencia de ventanas (`wmctrl -l`); delay de
  45s restringido a desconexión con medios en reproducción (T-132).

## WEBSOCKET

- `GET /ws` acepta token en query o recibe un frame JSON `{"type":"auth","token":...}`;
  la autenticacion inicial expira a los 3 segundos y falla con cierre 1008.
- Frames JSON observados: `ping`/`pong`, `input` gamepad, `pointer`, `text`, `combo` y la accion
  `media_control`. Los frames binarios son audio PCM y se procesan en el pipeline STT local.
- ASTRA-02: La regeneración o rotación del token de pairing revoca y desconecta inmediatamente todas
  las conexiones WebSocket autenticadas activas.
- ASTRA-03: Los comandos de voz por frames binarios se procesan de forma asíncrona fuera del bucle
  de recepción de frames WebSocket, evitando bloqueos de ping/pong y desconexiones de clientes.
- Heartbeat: intervalo de 10s con tolerancia ampliada a 8s; reseteo inmediato de temporizador al
  recibir `pong` (D43 resuelve desconexiones periódicas a los 15s).
- Hay dos token buckets por conexion: rapido para pointer/ping y lento para el resto. Texto se
  trunca a 500 caracteres; audio se limita a 512000 bytes.

## PAIRING, PERSISTENCIA Y AUDIO

- `backend/auth.py` carga `PAIRING_TOKEN` desde entorno o `backend/.pairing_token` (permisos 0600) y
  expone solo `verify_access`; desde T-144 no hay validación de licencia, caché
  (`.license_cache`) ni consulta a Supabase. Revocación inmediata de WebSockets (ASTRA-02).
- `backend/run.py` persiste CA, clave y hoja bajo `backend/certs`. ASTRA-04 verifica vigencia (`notAfter`)
  y renueva hojas HTTPS caducadas en startup con sincronización horaria vía `systemd-timesyncd`.
- `backend/ai_pipeline.py` orquesta la voz de forma 100% local y offline: transcodificación PCM 16kHz
  en memoria -> VAD -> whisper.cpp AVX1 (`ggml-base-q5_1`, ~2.6s latencia, ~137MB RAM) en thread asíncrono
  -> `backend/local_intent.py` (Needle 2, regex/pattern matching determinista, latencia <0.25ms, catálogo
  estricto allowlist `launch_kiosk`, `media_control`, `search`, `system_control`, normalización fonética y
  filtro contra inyecciones de shell y path traversal). Desacoplado de Supabase `ai-proxy` y sin licencia.

## INPUT, KIOSK Y SERVICIO

- `backend/input_emulator.py` usa evdev/uinput para teclado virtual, texto, pointer y teclas de
  media; soporta mapas `us`, `es` y `latam`.
- `backend/kiosk.py` solo acepta Firefox ESR en `/usr/bin/firefox-esr`, con perfil dedicado
  `~/.config/lrp-kiosk-firefox`; optimizado para VA-API H.264 (`media.ffmpeg.vaapi.enabled=true`)
  desactivando decodificación por software de VP9/AV1; mantiene el grupo de proceso rastreado y
  cierra ventanas solo con `wmctrl`. Verificación de disponibilidad de display X11 (`is_display_ready`)
  para prevenir condiciones de carrera en arranque del HTPC.
- `scripts/install.sh` exige el usuario `lrp` existente, fija `LRP_MODE=htpc`, elimina unidades
  user legacy, genera un unico servicio systemd `User=lrp` ordenado tras display manager y red,
  e invoca `scripts/debian/platform-bootstrap.sh` para uinput, PipeWire, Avahi, UFW, sleep/DPMS y CA.
  ASTRA-01: `/opt/linuxremoteplayer` y `.venv` pertenecen a `root:root` (read-only para `lrp`),
  aislando datos mutables en `/var/lib/linuxremoteplayer/`.
- `scripts/uninstall.sh` detiene servicios y ejecuta cleanup de licencia, udev, firewall, suspension,
  certificados, cache y entorno virtual.

## BUILD, PACKAGE, ISO Y UPDATE

- `scripts/build_deb.sh` ejecuta `scripts/check_css_sync.py`, empaqueta clave pública `scripts/debian/lrp-ota-pub.pem`, copia `backend/`, `frontend/`, `scripts/` y `VERSION` a staging, estampa la versión en `frontend/sw.js`, genera maintainer scripts y produce `dist/linuxremoteplayer_<VERSION>_amd64.deb` y su `.sha256`.
- Control Debian: `Architecture: amd64`; `Depends: python3, python3-venv, python3-dev, build-essential, openssl, sudo, curl, ca-certificates`; `Recommends: firefox-esr, ufw, pulseaudio-utils`.
- El `postinst` crea el venv, instala requirements y genera `/usr/local/bin/lrp-setup` y `/usr/local/bin/lrp-update`. El wrapper conserva funciones y `main "$@"; exit $?` porque se reescribe durante `apt-get install`.
- `prerm` siempre detiene el servicio y solo deshabilita/limpia cuando `$1` es `remove`; el cleanup no se ejecuta en `upgrade`.
- **Firma criptográfica OTA y rollback transaccional (T-142, cierre B19)**:
  * `backend/ota_security.py`: verificación asimétrica Ed25519 de manifiestos firmados digitalmente (`signature`), validación anti-downgrade semver, y consulta a clave pública embebida `/opt/linuxremoteplayer/scripts/debian/lrp-ota-pub.pem`.
  * `scripts/sign_ota_manifest.py`: herramienta offline para firmar digitalmente manifiestos JSON con clave privada Ed25519.
  * `/usr/local/bin/lrp-update`: descarga a `/tmp`, verifica firma Ed25519 y SHA256 antes de instalar; implementa watchdog post-upgrade de 45 segundos y auto-rollback transaccional automático a la versión previa si el servicio no levanta.
  * `POST /api/update/apply` y `GET /api/update/check`: endpoints con validación asimétrica de actualización.
- **Generador ISO Appliance (T-141)**:
  * `scripts/debian/iso/build_iso.sh`: orquestador `live-build` (`lb config`/`lb build`) que genera imagen `.iso` híbrida BIOS/UEFI de LRP OS sobre Debian 13 minimal.
  * `scripts/debian/iso/installer/lrp-install-target.sh`: instalador target desatendido con exclusión estricta fail-closed del medio USB booteable; instala GRUB EFI **firmado** (shim), crea la entrada NVRAM `LRP-OS` y la pone primera en `BootOrder`, deja el fallback `EFI/BOOT/BOOTX64.EFI` y escribe `/var/log/lrp-install-report.txt` con `live_boot_mode`, `nvram_entry`, `bios_grub` y `hosts` (T-149).
  * `scripts/debian/iso/config/zram-generator.conf`: configuración zram0 swap al 50% de RAM.
  * `scripts/debian/iso/config/`: assets inyectados por `includes.chroot` — `hosts` (B20), `default-grub`
    (`GRUB_BACKGROUND`, timeout oculto, `GRUB_DISTRIBUTOR="LRP OS"`), `lrp-splash.png` (1920x1080,
    verde `#10B981` + icono) y `plymouth/{lrp.plymouth,lrp.script}` (tema de arranque).
  * `scripts/debian/iso/hooks/99-lrp-setup.chroot`: provisionamiento chroot de `lrp`, autologin por
    `agetty` en tty1 con `startx` (cursor visible, B26), tema plymouth, unit del backend con
    `DISPLAY`, `XDG_RUNTIME_DIR` y `DBUS_SESSION_BUS_ADDRESS`, reglas uinput y firstboot service.
- `website/beta/install.sh` valida manifiesto `1.99.2`/`amd64`/nombre de archivo/SHA, instala el `.deb` y ejecuta `lrp-setup`; `website/install.sh`, `latest.json` y `website/downloads/` conservan el canal estable publicado 1.9.1.

## CLOUD, DATABASE Y WEBSITE

- **Estado 2.0 (T-144, 2026-10-22)**: el runtime instalado ya **no** usa ninguna de estas superficies:
  `backend/auth.py`, `ai_pipeline.py`, `config.py` y `main.py` no tienen licencia, proxy, cuotas ni
  activación, y `backend/.env.example` ya no publica `LICENSE_*` ni `BUY_URL`. Lo que sigue describe
  código **legacy** de Supabase que T-146/T-147 retiran del sitio y del servicio.
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

## BETA RELEASE SURFACES (1.99.2, DEBIAN HTPC)

- Stable release remains `1.9.1`; its public `latest.json` is stable-only and does not discover beta.
- `VERSION` is `1.99.2`; `website/beta/latest.json` declares `architecture: amd64`, deb URL
  `linuxremoteplayer_1.99.2_amd64.deb` y SHA256
  `a0b54c85fff7842a25676546c8d105455c603fb202eb53510fbff622442a83e9`; el sidecar publicado
  coincide.
- The public beta installer (`website/beta/install.sh`) is reachable and enforces the amd64
  manifest/filename/SHA contract; the website is a beta notice with curl enrollment ES/EN
  declaring Debian 13 amd64 minimal, Xorg/Openbox, Firefox ESR and RTX 3060 initial certification.
- These facts describe the published `88cf2f6` state on `main` (`VERSION` `1.99.2`). The v2.0
  appliance modules (`backend/ota_security.py`, `backend/local_intent.py`, `backend/system_platform.py`,
  `scripts/debian/iso/`) live only on `codex/debian-foundation` @ `50da3ca`, 17 commits ahead of
  `main` and unmerged at `88cf2f6`; they are not present in `main`. The worktree D35 rebuild is
  committed on that branch and its published sidecar matches manifest `a0b54c…`.

## ACOPLAMIENTOS FACTUALES

- `VERSION` -> `build_deb.sh` -> `frontend/sw.js` -> paquete -> `website/beta/latest.json` (beta) o `website/latest.json` (estable).
- `frontend/app.js` y `frontend/status.html` consumen las rutas REST; `app.js` consume `/ws`.
- `ai_pipeline.py` orquesta whisper.cpp y `local_intent.py` de forma 100% local; desacoplado de `ai-proxy`.
- `main.py` depende de `input_emulator.py`, `kiosk.py`, `discovery.py`, `audio.py`, `auth.py`, `system_platform.py` y `local_intent.py`.
- `backend/.env.example`, `website/install.sh`, `docs/ARCHITECTURE.md` y `docs/DEVELOPING.md`
  describen superficies de configuracion, instalacion y desarrollo.

## VERIFICACION DISPONIBLE

- `tests/` contiene suites tracked: baseline Debian, NVIDIA/session/platform bootstraps,
  instalador `htpc`, kiosk Firefox ESR, rollback, release Debian/beta, mitigaciones de seguridad y
  resiliencia Astra (`test_security_mitigations.py`, `test_resilience_mitigations.py`), plataforma de
  sistema (`test_system_platform.py`), onboarding Wi-Fi (`test_onboarding_dual_wifi.py`), benchmark
  STT (`test_local_stt.py`), motor NLU local (`test_local_intent.py`), generador ISO (`test_iso_factory.py`)
  y firma criptográfica/rollback OTA (`test_ota_signing_rollback.py`). El conteo de tests y su
  veredicto pertenecen a `PLAN_v2.0-appliance.md` (evidencia G4); MAINTAIN no los re-ejecuta.
- El gate ejecutable del build es `python3 scripts/check_css_sync.py` mas la comprobacion de
  versionado del service worker; la documentacion tambien prescribe `node --check` y `py_compile`.
- La verificacion de device pertenece a `.agents/TESTING.md` y requiere hardware real; este job no
  ejecuta producto ni device.
