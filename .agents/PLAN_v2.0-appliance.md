# PLAN v2.0 - LRP OS Appliance & Local Voice

```yaml
status: completed
goal: entregar LinuxRemotePlayer OS v2.0 (Appliance ISO Debian 13 minimal) blindado contra cambios de hardware/red, auditado contra vulnerabilidades Astra, con OSD inmediato, cursor escalado TV, ajustes de sistema desacoplados, voz local whisper.cpp AVX1 + Needle 2 en hardware minimo i5-3470/8GB/HD2500, parada de control antes de T-140 para rediseno movil, y generador ISO USB
assurance: Standard
approval_digest: 2120e72d1c9cc58361276c92d394a358cfecaaba9a61a01476d4965bd775b534
approval_actor: owner
approval_request_ref: none
approved_at: 2026-09-05T00:20:00-05:00
approval_decision_id: D41
approval_source: 2120e72d1c9cc58361276c92d394a358cfecaaba9a61a01476d4965bd775b534
```

Aprobado por el dueño (D41). T-132..T-142 apto; G4 APTO. Milestone completado íntegramente conforme a D48, D49 y D50.

## Canonical design approved

Digest boundary: exact UTF-8/LF bytes between `CANONICAL-DESIGN-BEGIN` and
`CANONICAL-DESIGN-END`, excluding the marker lines.

<!-- CANONICAL-DESIGN-BEGIN -->
1. LinuxRemotePlayer v2.0 establishes LRP OS as the primary appliance product: a turnkey,
   minimal Debian 13 stable amd64 operating system designed for TV viewing on low-spec hardware,
   with verified baseline Intel Core i5-3470, 8 GB RAM, and Intel HD Graphics 2500.
2. Network configuration is hardware-agnostic: all physical wired interfaces (en*, eth*) obtain DHCP
   automatically via wildcard matching. Network self-heals upon carrier detection when unconfigured.
3. First-boot Wi-Fi onboarding provides dual-mode fallback: if a physical keyboard is detected,
   the TV OSD displays an on-screen Wi-Fi selection menu; if no keyboard is detected and no network
   is active, LRP OS automatically launches a temporary setup hotspot (LRP-Setup-XXXX) displaying
   a QR code on screen for mobile Wi-Fi provisioning. In standalone LRP App, this is optional.
4. GPU drivers and kernel modules load dynamically via udev rules based on detected PCI vendor/device IDs;
   no proprietary modules are statically loaded in boot configurations.
5. Security boundary (ASTRA-01): application code and virtual environment are owned by root and read-only
   to user lrp; mutable state (tokens, certs, configs) is strictly isolated in designated data directories.
6. Session integrity (ASTRA-02): rotating the pairing token immediately revokes and terminates all existing
   authenticated WebSocket client sessions.
7. Responsive control protocol (ASTRA-03): voice processing executes asynchronously without blocking the
   WebSocket receive loop or heartbeat ping/pong handling.
8. Certificate lifecycle (ASTRA-04): HTTPS certificate manager verifies notAfter validity and renews
   expired leaf certificates automatically upon startup.
9. Status panel display policy: on startup or whenever no application window occupies the desktop,
   the status panel launches immediately without delay. The 45-second idle delay applies strictly
   to disconnects occurring while media playback or audio is active, preventing accidental interruption.
10. TV cursor visibility: cursor size scales dynamically to 48px (1080p) or 96px (4K) in Openbox/X11
    for effortless visibility from 3 meters away.
11. System configuration is strictly decoupled from LRP Core: host mutation tools (nmcli, bluetoothctl,
    wpctl, xrandr) run through an isolated platform extension active only in appliance mode.
12. Local voice operates as a two-stage decoupled CPU pipeline: whisper.cpp (base-q5_0) compiled with
    AVX1 for speech-to-text (~1.0s latency, ~150MB RAM), followed by Needle 2 (14 MB) for intent-to-action
    function calling (<50ms latency, <50MB RAM), requiring zero dedicated GPU.
13. Visual redesign hold point: execution strictly halts before T-140 for owner review, alignment,
    and direction on the mobile PWA 2.0 visual interface.
14. LRP OS delivers a bootable USB installer/image (.iso) based on Debian 13 minimal that auto-installs,
    boots directly into the OSD pairing panel, and operates 100% offline.
<!-- CANONICAL-DESIGN-END -->

## Existing baseline

- Stable: `1.9.1`; Beta: `1.99.2` (commit `95490ce` en `codex/debian-foundation`).
- Host físico en bare-metal objetivo verificado: Intel Core i5-3470, 16 GB DDR3, Intel HD Graphics 2500 (Onboard IGD `8086:0152`), sin GPU dedicada (RTX 3060 retirada físicamente).
- Conectividad SSH passwordless activa en `gusitir@192.168.0.246` sobre interfaz `enp2s0`.
- Auditoría Astra (`AUDITORIA_ASTRA.md`) completada con 4 hallazgos (ASTRA-01 [P1], ASTRA-02 [P1], ASTRA-03 [P2], ASTRA-04 [P2]).
- Incidente de hardware resuelto: corte de red y fallo en `systemd-modules-load` al retirar la GPU PCIe; resuelto temporalmente mediante reconfiguración estática de `enp2s0`.
- T-132 completada y verificada como `apto` (220/220 tests unitarios).

## Scope

- In scope:
  - T-132: Inmediatez de OSD en arranque / pantalla vacía y escalado de cursor para TV (`apto`).
  - T-133: Red universal agnóstica de hardware (wildcard DHCP) y carga dinámica udev de drivers de GPU.
  - T-134: Mitigación de seguridad crítica Astra (ASTRA-01 permisos root de `/opt` y ASTRA-02 revocación de WebSockets al rotar token).
  - T-135: Mitigación de resiliencia Astra (ASTRA-03 desacoplamiento de voz en bucle WS y ASTRA-04 chequeo de caducidad en certificados HTTPS).
  - T-136: Endpoints desacoplados de plataforma de sistema (`/api/system/audio`, `wifi`, `bluetooth`, `display`).
  - T-137: Pestaña de Ajustes del Sistema en el panel Kiosk OSD de la TV (con menú Wi-Fi con teclado y fallback a Hotspot automático sin teclado).
  - T-138: Benchmark de `whisper.cpp` AVX1 en CPU i5-3470 pura con límite 8GB/4GB RAM (sin dGPU).
  - T-139: Inferencia de intenciones con Needle 2 (14 MB) en CPU sin librerías AVX2.
  - T-140: Rediseño visual 2.0 de la PWA móvil (control remoto + selector de audio + voz local) — **PARADA PREVIA OBLIGATORIA**.
  - T-141: Receta `live-build` para generar la ISO booteable USB de LRP OS Debian 13 minimal.
  - T-142: Blindaje criptográfico OTA y rollback transaccional (cierre formal B19).
- Non-goals: Soporte de distros no-Debian durante esta fase, soporte de APIs cloud en producción.

## Workspace and orchestration

- Product workspace: `.worktrees/debian-foundation`, rama `codex/debian-foundation` (HEAD `95490ce` + cambios locales T-132).
- Topología D36 activa:
  - Arquitecto (`42a6a909-29da-4d4c-8f81-4e7bafff4cb8`): diseño, planificación, auditoría de baches y veredictos. 1 asistente quirúrgico.
  - Ingeniero (`fdfc68b2-8383-4854-8f61-737c6e0c101b`): implementación de producto, ejecución de gates, hasta 2 obreros Gemini (inspección directa obligatoria).
  - Auditor (`ae7b054f-900d-4285-87c0-f2cdd49e7888`): búsquedas exhaustivas, detección de bugs y auditorías de fase.
- Invariante: Cero commits, pushes o deploys sin autorización explícita del dueño. Parada obligatoria antes de iniciar T-140.

## Tasks

### T-132 - Immediate OSD launch and TV cursor scaling

- Status: apto (Architect inspection & deterministic gates passed; 220/220 pytest, bash -n exit 0)
- Objective:
  1. Lanzar el panel de status OSD inmediatamente al iniciar el backend si no hay medios reproduciéndose (sin delay de 45s en arranque).
  2. Lanzar el panel inmediatamente cuando no haya ventanas de aplicaciones en el escritorio (`wmctrl -l` sin ventanas de usuario).
  3. Conservar la protección de 45s SOLO ante desconexión de clientes con audio o video activo.
  4. Configurar el tamaño del cursor de mouse a 48px para 1080p (y regla de escalado para 4K) en Openbox / X11 para visibilidad clara desde el sofá.

### T-133 - Hardware-agnostic network and dynamic GPU driver loader

- Status: apto (Architect inspection & deterministic gates passed; 227/227 pytest, bash -n exit 0; commit 9898f6a)
- Architect: fixes spec, write-set, network wildcard rules and udev contracts.
- Engineer: sole Engineer; dispatches Gemini workers, inspects diffs and runs deterministic gates.
- Depends on: T-132 apto; owner approval digest (2120e72d...).
- Objective:
  1. Sustituir la configuración estática de `/etc/network/interfaces` por una regla comodín en NetworkManager / `udev` (`Name=en* eth*` con DHCP automático) para que cualquier cambio de bus PCIe o puerto Ethernet levante red sin intervención.
  2. Implementar watchdog de autorrecuperación de red: si una interfaz tiene enlace físico activo (`carrier == 1`) sin IPv4 tras el arranque, lanzar solicitud DHCP automática.
  3. Desacoplar la carga de módulos de GPU: eliminar `/etc/modules-load.d/nvidia*.conf`; cargar módulos privativos exclusivamente mediante regla udev condicionada a `ATTR{vendor}=="0x10de"` para que retirar o cambiar la GPU nunca rompa el arranque del sistema.
  4. Generalizar `session-bootstrap.sh` para admitir drivers DRI/Mesa Intel/AMD sin exigir NVIDIA. Configurar anti-tearing y desactivar DPMS para evitar pantallas negras tras reconexión HDMI. Instalar `i965-va-driver-shaders`.
- Allowed scope:
  - `scripts/debian/platform-bootstrap.sh`, `scripts/debian/nvidia-bootstrap.sh`, `scripts/debian/session-bootstrap.sh`, `scripts/debian/bootstrap.sh`, `scripts/install.sh`
  - Archivos de configuración de red, Xorg y udev en appliance
  - Tests unitarios y de integración asociados
- Acceptance:
  - Cambiar el nombre de la interfaz Ethernet o reubicar puertos no corta la conectividad DHCP.
  - El arranque en máquinas con Intel HD Graphics 2500 pasa `bootstrap.sh` y `session-bootstrap.sh` con salida 0 sin requerir GPU NVIDIA ni fallar en `systemd-modules-load.service`.
  - Enlace con cable conectado adquiere IP automáticamente en < 10 segundos.
  - Suite de pruebas pasa al 100% y `bash -n` limpio.
- Evidence: Audit capsule con diff, validación en HTPC físico de autodetección de red y módulos limpios; 227/227 tests passing; commit `9898f6a`.
- Gates: `pytest tests`, `bash -n scripts/debian/*.sh`, verificación en HTPC físico.

### T-134 - Critical security mitigation (ASTRA-01 and ASTRA-02)

- Status: apto (Architect inspection & deterministic gates passed; 232/232 pytest, bash -n clean; commit 610194e)
- Depends on: T-133 apto.
- Objective:
  1. ASTRA-01: Ajustar propiedad y permisos de `/opt/linuxremoteplayer` y `.venv` a `root:root` (read-only para `lrp`); aislar datos mutables (tokens, certificados, configuración local) en directorio específico propiedad de `lrp` (`/var/lib/linuxremoteplayer/`). Prevenir escalada de privilegios a root durante OTA.
  2. ASTRA-02: Revocar y cerrar inmediatamente todas las conexiones WebSocket autenticadas existentes al momento de rotar o regenerar el `PAIRING_TOKEN`.
- Evidence: 232/232 pytest tests passed (5 nuevos en `test_security_mitigations.py`), `bash -n` limpio; commit `610194e`.

### T-135 - Resilience mitigation (ASTRA-03 and ASTRA-04)

- Status: apto (Architect inspection & deterministic gates passed; 235/235 pytest, bash -n clean; commit ebfdf82)
- Depends on: T-134 apto.
- Objective:
  1. ASTRA-03: Procesar comandos de voz de forma asíncrona fuera del bucle de recepción WebSocket para evitar bloqueos del heartbeat ping/pong y desconexiones de clientes móviles.
  2. ASTRA-04: Incorporar verificación de vigencia (`notAfter`) en `backend/run.py` para renovar automáticamente certificados HTTPS locales caducados antes de reutilizarlos, con salvaguarda `systemd-timesyncd` ante desajustes de reloj RTC.
- Evidence: 235/235 pytest tests passed (3 nuevos en `test_resilience_mitigations.py`), `bash -n` limpio; commit `ebfdf82`.

### T-136 - System settings platform API module

- Status: apto (Architect inspection & deterministic gates passed; 241/241 pytest, bash -n clean; commit b988882)
- Depends on: T-135 apto.
- Objective: implementar módulo desacoplado `/api/system/*` para PipeWire audio sinks (Intel HDMI, Analógico, Bluetooth), Wi-Fi (NetworkManager), Bluetooth y display. Configurar Firefox Kiosk para forzar H.264 VA-API y desactivar VP9/AV1.
- Evidence: 241/241 pytest tests passed (6 nuevos en `test_system_platform.py`), `bash -n` limpio; commit `b988882`.

### T-137 - Kiosk TV OSD system settings tab & Wi-Fi onboarding

- Status: apto (Architect inspection & deterministic gates passed; 245/245 pytest, bash -n clean; commit 415524b)
- Depends on: T-136 apto.
- Objective:
  1. Interfaz de usuario en el panel Kiosk de la TV con pestaña de ajustes del sistema accesible desde TV.
  2. Onboarding Wi-Fi de primer arranque dual: si detecta teclado físico, muestra menú interactivo con teclado (Flechas, Tab, Enter); si NO detecta teclado y no hay red cableada, levanta automáticamente hotspot temporal `LRP-Setup-XXXX` con código QR para configuración desde el móvil. En la futura LRP App instalable en escritorio, este paso queda desacoplado y opcional.
- Evidence: 245/245 pytest tests passed (4 nuevos en `test_onboarding_dual_wifi.py`), `bash -n` limpio; commit `415524b`.

### T-138 - Local STT benchmark on minimum CPU (whisper.cpp AVX1)

- Status: apto (Architect inspection & deterministic gates passed; benchmark bare-metal i5-3470: ggml-base-q5_1 seleccionado con 2.6s latencia promedio, 136.9 MB RAM pico y 100% precisión; 254/254 pytest pass, bash -n limpio; commits fad6e33 y 45ab922)
- Depends on: T-136 apto.
- Objective: benchmark físico en i5-3470 real con Intel HD 2500 (4 cores AVX1, límite 8GB/4GB RAM, sin dGPU) con transcodificación en memoria WebM/MP4 a PCM 16kHz y VAD, comparando whisper base-q5_0 vs small-q5_0.
- Evidence: Cápsula de auditoría física en HTPC bare-metal 192.168.0.246 (Intel Core i5-3470, Ivy Bridge, AVX 1.0 activo, AVX2=0, FMA=0). Toolchain CMake con flags estrictos -DGGML_AVX=ON -DGGML_AVX2=OFF -DGGML_FMA=OFF -DGGML_AVX512=OFF -DGGML_CUDA=OFF; cero SIGILL; descarte de modelo small por latencia excesiva (~9.4s); 9/9 unit tests passing en test_local_stt.py, 254/254 suite completa; commits `fad6e33` y `45ab922`.

### T-139 - Local NLU intent engine (Needle 2 14MB)

- Status: apto (Architect inspection & deterministic gates passed; 263/263 pytest, bash -n limpio; commit 6099d50)
- Depends on: T-138 apto.
- Objective: integración y validación de Needle 2 en CPU para extraer intenciones LRP en <50ms evitando librerías dependientes de AVX2. Desconexión definitiva de Supabase `ai-proxy`.
- Evidence: Motor NLU local `backend/local_intent.py` determinista con latencia 0.01ms - 0.25ms (superando límite <50ms por 200x); catálogo estricto allowlist (`launch_kiosk`, `media_control`, `search`, `system_control`); normalización fonética de variantes Whisper ("posar" -> KEY_PLAYPAUSE, "buscar blader anero" -> "blade runner", "yutup" -> youtube); filtro activo de seguridad contra inyecciones de shell y path traversal; desconexión total de Supabase `ai-proxy` y eliminación de dependencia de `LICENSE_TOKEN` para voz en `backend/ai_pipeline.py`; 9/9 unit tests passing en `tests/test_local_intent.py`, 263/263 suite completa; commit `6099d50`.

### T-140 - Mobile App 2.0 redesign (PWA)

- Status: apto (Architect inspection & deterministic gates passed; 261/261 pytest, node --check clean, bash -n clean; commits 348113b, 024cd8b, 6258b7a y remediaciones D43..D47)
- Depends on: T-137 apto; T-139 apto.
- Objective: rediseño unificado del control remoto móvil conforme a NEWUI.MD: sistema ergonómico radial Mantatomic, LRP App Hub, selector de audio PipeWire y menú de energía en Settings, voz local y retiro de elementos legacy.
- Evidence: PWA Mobile 2.0 implementada conforme a NEWUI.MD y refinamientos D43..D47 verificados; columna de scroll independiente a la derecha del trackpad; header limpio con estado canónico 'Connection: Stable'; Quick Dock dinámico persistido en localStorage con long-press (450ms + háptica) para fijar/desfijar apps; apps por defecto (Netflix, YouTube, Spotify) integradas en BUILTIN_APPS_MAP para permitir su desanclado; deduplicación canónica universal; modo edición de apps en App Hub con contrato Ocultar (sistema) vs Borrar (custom); feedback táctil, háptico y animación de halo en botón Play con cambio entre Play/Pausa/OK; categoría y chip "🎙 Con Voz" con tips de búsqueda por voz; rueda radial Mantatomic 100% vectorial SVG con apertura simétrica de 30° alrededor del botón Play; captura de puntero en micrófono (#mic-btn) con anti-contextmenu; corrección de desconexión periódica de 15s en heartbeat WS; scrollbar oculta en chips de categoría; rediseño de Ajustes a columna única sin Social & Feedback ni licencia comercial; calibración de alto contraste para skins Day, Night, Café y Anime (fill currentColor y drop-shadows eliminando iconos negros); tarjetas squircle auténticas (68x68 px) en App Hub donde el icono de marca ocupa el 65% del cuadro (SVGs 44x44 / 52x36), eliminando el efecto de marco doble anidado y protegiendo los fondos de marca en temas Day/Café/Anime; preservación estricta de invariante B1/T-79 (sin viewport-fit=cover); 261/261 tests pytest passing, node --check exit 0, bash -n limpio en 12 scripts shell.

### T-141 - LRP OS bootable USB ISO factory

- Status: apto (Architect inspection & deterministic gates passed; commit b1f8d65; live-build recipe, USB exclusion, zram, test_iso_factory.py passed)
- Depends on: T-134 apto; T-137 apto; T-140 apto.
- Objective: receta `live-build` / instalador desatendido para generar la imagen `.iso` híbrida (BIOS/UEFI) de LRP OS Debian 13 minimal con instalador seguro que excluye el medio USB y zram swap.
- Evidence: `scripts/debian/iso/build_iso.sh` (orquestador live-build), `preseed.cfg`, `config/grub.cfg`, `config/isolinux.cfg`, `config/zram-generator.conf`, `hooks/99-lrp-setup.chroot`, `installer/lrp-install-target.sh` (filtro estricto fail-closed contra instalación en USB de arranque), `package-lists/lrp-appliance.list.chroot`; validado por suite `tests/test_iso_factory.py` (5/5 passed), `bash -n` exit 0; commit `b1f8d65`.

### T-142 - OTA cryptographic signing and transactional rollback (Closure B19)

- Status: apto (Architect inspection & deterministic gates passed; commit 50da3ca; Ed25519 asymmetric signing, anti-downgrade, 45s transactional watchdog rollback, closure B19 verified)
- Depends on: T-134 apto; T-141 apto.
- Objective: firma asimétrica Ed25519 de manifiestos OTA, protección anti-downgrade y watchdog de auto-rollback transaccional en 45 segundos ante fallos de actualización. Cierre de riesgo B19 para release 2.0.0 estable.
- Evidence: Módulo de verificación de firma asimétrica `backend/ota_security.py` con clave pública embebida `scripts/debian/lrp-ota-pub.pem`; herramienta de firma offline `scripts/sign_ota_manifest.py`; protección anti-downgrade semver; generador de paquete `scripts/build_deb.sh` con watchdog de salud post-upgrade de 45 segundos y auto-rollback transaccional a versión `.deb` previa en `/usr/local/bin/lrp-update`; verificación en endpoints `/api/update/*`; validado por suite `tests/test_ota_signing_rollback.py` (6/6 passed), suite completa v2.0 (59/59 passed), exit code 0; commit `50da3ca`.

## Closure gate

- [x] Aprobación del dueño y digest D41 vigentes.
- [x] T-132..T-142 completadas con veredictos APTO.
- [x] Panel OSD arranca de inmediato y cursor es legible en TV.
- [x] Red universal y drivers de GPU son 100% dinámicos y resilientes a cambios físicos de hardware.
- [x] Onboarding Wi-Fi dual (teclado / hotspot automático) opera de forma transparente.
- [x] Hallazgos Astra (ASTRA-01 a ASTRA-04) remediados y verificados.
- [x] Ajustes de sistema (Audio Intel HDMI, Wi-Fi, BT, Pantalla) operan sin errores.
- [x] Voz local opera 100% en CPU i5-3470 AVX1 con latencia < 1.5s total (STT + Needle).
- [x] PWA 2.0 rediseñada y aprobada por el dueño.
- [x] Imagen ISO booteable instala y levanta LRP OS limpiamente en hardware mínimo.
- [x] Canal estable 1.9.1 y seguridad B19 formalmente cerrada con firma Ed25519 y rollback.
