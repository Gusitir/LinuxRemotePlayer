# APPCORE - mapa factual del codigo LRP OS 1.0.0-dev (open source GPL-3.0)

```yaml
verified_at: 2026-10-29T05:20:00-05:00
source_commit: "dcd26f5 (main; F1/F2 cerradas, D56)"
producto: ISO Debian appliance + panel kiosk + PWA/APK de control (LRP OS 1.0.0)
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
- `scripts/install.sh` exige el usuario `lrp` existente, elimina unidades user legacy, genera un único
  servicio systemd `User=lrp` ordenado tras display manager y red, e invoca
  `scripts/debian/platform-bootstrap.sh` para uinput, PipeWire, Avahi, UFW, sleep/DPMS y CA.
  Ya no escribe `LRP_MODE` ni instala `lrp-setup` (D56/T-150).
  ASTRA-01: `/opt/linuxremoteplayer` y `.venv` pertenecen a `root:root` (read-only para `lrp`),
  aislando datos mutables en `/var/lib/linuxremoteplayer/`.
- `scripts/uninstall.sh` detiene servicios y ejecuta cleanup de udev, firewall, suspensión,
  certificados, cache y entorno virtual (sin superficie de licencia).

## BUILD, PAQUETE E ISO

- `scripts/build_deb.sh` ejecuta `scripts/check_css_sync.py`, copia `backend/`, `frontend/`, `scripts/`
  y `VERSION` a staging, estampa la versión en `frontend/sw.js` y produce
  `dist/linuxremoteplayer_<VERSION>_amd64.deb` + `.sha256`. El `.deb` es **artefacto interno** del
  build: no se distribuye suelto ni instala updater, `lrp-setup` ni clave OTA (D56/T-150).
- Control Debian: `Architecture: amd64`; `Depends: python3, python3-venv, python3-dev, build-essential,
  openssl, sudo, curl, ca-certificates` (+ `python3-cryptography`, pendiente de podar); `Recommends:
  firefox-esr, ufw, pulseaudio-utils`. El `postinst` crea el venv e instala requirements.
- `prerm` detiene el servicio; el cleanup completo solo ocurre en `remove`.
- **Generador ISO Appliance (T-141/T-149)**:
  * `scripts/debian/iso/build_iso.sh`: orquestador `live-build` (`lb config`/`lb build`) que genera la
    ISO híbrida BIOS/UEFI sobre Debian 13 minimal e inyecta assets por `includes.chroot`.
  * `scripts/debian/iso/installer/lrp-install-target.sh`: instalador desatendido con exclusión
    fail-closed del medio USB; instala GRUB EFI **firmado** (shim), crea la entrada NVRAM `LRP-OS` y la
    pone primera en `BootOrder`, deja el fallback `EFI/BOOT/BOOTX64.EFI` y escribe
    `/var/log/lrp-install-report.txt` (`live_boot_mode`, `nvram_entry`, `bios_grub`, `hosts`).
  * `scripts/debian/iso/config/`: `zram-generator.conf`, `hosts` (B20), `default-grub`
    (`GRUB_BACKGROUND`, timeout oculto, `GRUB_DISTRIBUTOR="LRP OS"`), `lrp-splash.png` (verde `#10B981`
    + icono) y `plymouth/{lrp.plymouth,lrp.script}`.
  * `scripts/debian/iso/hooks/99-lrp-appliance.chroot`: provisiona `lrp`, autologin por `agetty` en
    tty1 con `startx` (cursor visible, B26), tema plymouth, unit del backend con `DISPLAY`,
    `XDG_RUNTIME_DIR` y `DBUS_SESSION_BUS_ADDRESS`, reglas uinput y firstboot service.
- Distribución 1.0.0: la ISO y el APK se publican como **GitHub Release**; la web estática (Vercel,
  `website/vercel.json` con `cleanUrls`) solo enlaza y muestra checksums, avisos GPL y créditos.

## SUPERFICIES RETIRADAS (D56)

Licencia, premium, compra, cuotas, activación, proxy cloud, Supabase, OTA (updater, firma de
manifiestos, rollback, `latest.json`, canal beta) y modo appliance **no existen** en 1.0.0: se
eliminaron en T-150 (commits `30dbd69`…`6df950e`). Su código y diseño viven solo en `legacy/2.0`
(tag `v2.0.0-legacy`). No quedan rutas `/api/license/*`, `/api/update/*`, `/api/voice/toggle`,
`supabase/`, `backend/ota_security.py` ni scripts de update.

La web 1.0.0 (`website/`) es estática: landing ES/EN, docs, descarga de ISO/APK y avisos GPL; se
publica en Vercel por integración Git (push a `main`), no por CI ni `vercel` CLI.

## ACOPLAMIENTOS FACTUALES

- `VERSION` -> `build_deb.sh` -> `frontend/sw.js` -> `.deb` -> ISO; el release publica ISO + APK +
  `SHA256SUMS` en GitHub Releases y la web solo enlaza.
- `frontend/app.js` y `frontend/status.html` consumen las rutas REST; `app.js` consume `/ws`.
- `ai_pipeline.py` orquesta whisper.cpp y `local_intent.py` de forma 100% local, sin red ni cuota (la
  UI de voz está oculta hasta T-157).
- `main.py` depende de `input_emulator.py`, `kiosk.py`, `discovery.py`, `audio.py`, `auth.py`,
  `system_platform.py` y `local_intent.py`.
- `backend/.env.example`, `docs/ARCHITECTURE.md` y `docs/DEVELOPING.md` describen configuración,
  arquitectura y build (se reescriben en T-152 para 1.0.0).

## VERIFICACION DISPONIBLE

- `tests/` cubre baseline Debian, bootstraps NVIDIA/session/platform, instalador, kiosk Firefox ESR,
  rollback de cleanup, release Debian, mitigaciones de seguridad y resiliencia Astra, plataforma de
  sistema, onboarding Wi-Fi, STT local, motor NLU local y generador ISO. El conteo vive en el gate de
  fase de `PLAN_v1.0.0-public.md`; MAINTAIN no re-ejecuta suites (D57).
- Gate ejecutable del build: `python3 scripts/check_css_sync.py` y el versionado del service worker;
  `node --check` y `py_compile` para los cambios de código.
- La verificación de device pertenece a `.agents/TESTING.md` y requiere el HTPC; este job no ejecuta
  producto ni device.
