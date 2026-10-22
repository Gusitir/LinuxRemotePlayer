# BUGS.md — registro desde 1.9.x

Este archivo no planifica: registra estado, manifestación y resolución. Las tareas viven en
PLAN/CURRENT. No tiene techo. Los bugs previos a 1.9.x viven en git y `archive/`.

# ABIERTOS

## B19 — OTA root sin autenticidad

**CRÍTICO · bloquea la siguiente release pública**

`lrp-update` instala como root un `.deb` y comprueba un sha256 servido por el mismo origen.
Detecta corrupción, no un origen comprometido. Quien controle Vercel/DNS/dominio puede entregar
un paquete y un hash hostiles. No existe timer: el usuario debe pulsar Actualizar, pero la app
lo invita a hacerlo. Plan: PLAN §GATE-OTA. Debe cerrarse en 2.0.0 antes de publicarla.

## B19b — TOCTOU y nombre predecible en `/tmp`

El actualizador usa un nombre predecible y separa verificación de instalación. Debe trabajar en
un `mktemp` root-only y mantener identificado el mismo inode/artefacto hasta instalarlo.

## M1 — migración incompleta nube/licencias

**Abierto por decisión D16-D18; todavía no es un defecto de 1.9.1.**

Backend, frontend, sitio y Supabase contienen Together, `ai-proxy`, licencias, compra, cuotas y
textos Paddle. Se resuelve como migración coordinada de 2.0.0 en PH24, incluida la web y la
retirada del servicio Supabase de keys/IA; no borrando referencias aisladas.

Incluye los hallazgos antes separados:

- **H23:** ayuda promete “Temas Pro” inexistentes.
- **H24:** botón de compra cae a la home aun con `BUY_URL` vacío.
- **H25:** la UI presenta parte del token de pairing como si fuera clave de licencia.
- **H11/H20:** placeholders/webhook/correo comercial quedan superados por la nueva visión.

Se consideran cerrados solo cuando no queden gates, activación, claves, checkout ni promesas de
premium en el artefacto, sitio ES/EN y documentación.

## H19 — QR con query puede caer en Offline

El QR usa `/?token=...`; las búsquedas del service worker no ignoran el query. Con red lenta o
backend caído no coincide con `/` precacheado y una rama puede no resolver la promesa.

## H12 — versión backend/PWA puede divergir

Tras OTA, una PWA que no se cierre puede conservar shell anterior. Comparar versiones y realizar
una actualización controlada del service worker, sin bucles de recarga.

## H5 — ocultación de pantallas inconsistente

Una pantalla usa `hidden` mientras `.flex` puede ganar; otra escribe `style.display`. Unificar
la máquina de estados y probar onboarding, pairing y reconexión.

## H21 — `theme-color` no refresca en iOS moderno

En iPhone 12 cambia al reabrir la PWA; en iPhone 8+ lo hace en vivo. No hay workaround aceptado.

## L3 — puerto de automatización del navegador

CDP/BiDi puede controlar sesiones autenticadas. Si se adopta: `127.0.0.1`, perfil dedicado,
privilegios mínimos, apagado por defecto y adaptadores por sitio. MPRIS tiene prioridad.

## Menores

- `auth.py` compara un secreto con `==` en un camino; usar comparación constante.
- Fuentes bold/regular son el mismo archivo y se descargan/precachean dos veces.
- El `.deb` depende de `build-essential`, innecesario para un appliance final.
- El instalador imprimía el token de pairing en el scrollback; **resuelto en 1.99.2** (ya no se lee ni imprime `.pairing_token`; token expuesto durante diagnóstico rotado).
- `%input` en sudoers es más amplio que el usuario exacto del servicio.
- `scripts/debian/platform-bootstrap.sh` definía `state_applied_ok()` dos veces; **resuelto en 1.99.2 / T-131** (duplicado eliminado, preservada la llamada a `state_applied_audio_bus_ok`).

# CERRADOS

## B1 — HUD desplazado en iPhone

**Cerrado en 1.9.1, T-79, validado en iPhone 8+ y 12.** La causa era
`viewport-fit=cover`; al reabrir iOS duplicaba el safe area. El porqué permanece comentado en
`frontend/index.html`.

## B18 — Actualizar dependía de `/tmp/lrp-update.log`

**Cerrado en 1.9.1, T-78.** El backend dejó de abrir el log y usa `DEVNULL`; el actualizador
administra su salida en `/var/log`.

## H6 — `bootstrap.sh` incompatible con repo privado

**Cerrado en 1.9.1, T-80.** Se eliminó el script, su documentación y `GITHUB_REPO` muerto.

## B1b — correo personal en `gracias.html`

**Cerrado antes del savepoint 1.9.1.** Usa `support@linuxremoteplayer.com`.

## H22 — eliminar/ocultar siempre visible

**Cerrado en v2.0, T-140.** Retirados los botones `×` permanentes de las tarjetas en App Hub;
reemplazados por interacción deliberada de pulsación prolongada (*long-press* de 450ms con vibración
háptica) para fijar y desfijar aplicaciones del Quick Dock, con badge sutil de chincheta.

## L1 — STT local aún no seleccionado

**Cerrado en v2.0, T-138.** Medido exhaustivamente en hardware mínimo real bare-metal (Intel Core
i5-3470, 4 cores AVX1, sin AVX2 ni dGPU). whisper.cpp compilado con `-DGGML_AVX=ON -DGGML_AVX2=OFF`.
Seleccionado `ggml-base-q5_1`: 2.6s de latencia promedio, 136.9 MB RAM pico, 100% precisión en
corpus gold español/inglés y cero SIGILL. Descartado `small` por latencia excesiva (~9.4s).

## L2 — acciones de IA necesitan frontera de seguridad

**Cerrado en v2.0, T-139.** Motor NLU local `backend/local_intent.py` (Needle 2, <0.25ms de latencia en CPU)
con catálogo estricto allowlist (`launch_kiosk`, `media_control`, `search`, `system_control`),
normalización fonética y filtro activo de sanitización que rechaza caracteres de inyección de shell
(`;`, `&`, `|`, `` ` ``, `$`, `>`, `<`, `\`) y secuencias de path traversal.

## ASTRA-01 — Escalada de lrp a root durante OTA

**Cerrado en v2.0, T-134 (commit `610194e`).** Código de aplicación y entorno virtual `.venv` bajo
propiedad `root:root` (read-only para usuario `lrp`). Estado mutable (tokens, certs, configs)
aislado estrictamente en `/var/lib/linuxremoteplayer/`. Previene inyección en `.venv/bin/pip` durante OTA.

## ASTRA-02 — Persistencia de WebSockets al regenerar token

**Cerrado en v2.0, T-134 (commit `610194e`).** `regenerate_pairing_token()` revoca inmediatamente
todas las sesiones WebSocket autenticadas activas, cerrando sus conexiones antes de persistir el nuevo token.

## ASTRA-03 — Desconexión de control remoto por bloqueo en voz

**Cerrado en v2.0, T-135 (commit `ebfdf82`).** Comandos de voz binarios procesados de forma asíncrona
mediante background task fuera del bucle de recepción WebSocket, permitiendo que ping/pong continúe
sin interrupción durante inferencias lentas.

## ASTRA-04 — Certificados HTTPS caducados no renovados

**Cerrado en v2.0, T-135 (commit `ebfdf82`).** `backend/run.py` verifica la vigencia `notAfter` del
certificado de hoja en cada arranque y lo renueva automáticamente si ha caducado, con salvaguarda
de sincronización horaria vía `systemd-timesyncd`.

## BUG-WS-HEARTBEAT — Desconexión periódica cliente WebSocket cada 15s

**Cerrado en v2.0, T-140 / D43.** El temporizador `heartbeatTimeoutId` en `frontend/app.js` no se
cancelaba al recibir el frame `pong` del servidor, causando que el cliente cerrara erróneamente su
propio socket cada 15 segundos por falso timeout. Resuelto cancelando el timeout inmediatamente al
recibir `pong` y ampliando la tolerancia a 8 segundos.

## AUD-001 — `cryptography` no declarada: el backend no arranca en el .deb

**Cerrado — commit `c484274` (2026-10-21).** `backend/requirements.txt:7` declara
`cryptography>=42,<48`; `scripts/build_deb.sh:71` la añade a `Depends`; `scripts/install.sh:118`
valida el import. Verificado en venv limpio: `pip install -r backend/requirements.txt` +
`import fastapi, evdev, segno, cryptography, ota_security` → `IMPORT_OK 47.0.0`.

## AUD-002 — OTA no publicable: manifiestos sin firma y versión no promovible

**Abierto — bloqueado por clave.** `scripts/build_deb.sh:212-216` aborta si el manifiesto no trae
`signature`; `website/latest.json` y `website/beta/latest.json` no la traen. `VERSION` = `1.99.2`:
el bump a `2.0.0` rompe `tests/test_beta_release.py:21` y `tests/test_debian_release.py:20,51,53`
hasta actualizar fixtures y artefactos. Estado de clave: `scripts/debian/lrp-ota-pub.pem` es Ed25519;
`~/.ssh/prod_rsa_private.pem` es RSA 2048 y **no** corresponde. La clave privada Ed25519 está fuera
del repo (offline) y no fue localizada. Requiere que el dueño aporte la clave o autorice rotación del
ancla de confianza.

## AUD-003 — preseed de la ISO pide paquetes inexistentes en trixie

**Cerrado — commit `c484274` (2026-10-21).** `scripts/debian/iso/preseed.cfg:64-65` usa ahora
`python3-evdev`, `i965-va-driver` e `intel-media-va-driver`, existentes en Debian 13. Falta rebuild y
prueba real del instalador `d-i` (pendiente TST-DEVICE).

## AUD-004 — ISO sin arranque BIOS coherente

**Abierto, no bloqueante.** `build_iso.sh:164` usa `--bootloader grub-efi` mientras `:135` copia
`grub.cfg` a `grub-pc`; no se crea partición EF02 y `lrp-install-target.sh:330` hace `grub-install
i386-pc || true`. La ISO híbrida declarada no arranca por BIOS.

## AUD-005 — Instalador con ejecución de shell sobre campos de `lsblk`

**Abierto, no bloqueante.** `lrp-install-target.sh:95` hace `eval "$line"` sobre campos derivados de
`lsblk` (incluido el modelo del USB) → RCE como root; `hook:77,83` auto-instala sin confirmación.
Además `hook:13,25` fija `lrp/lrp` con NOPASSWD.

## AUD-006 — ASTRA-03 cubre el frame pero no las tareas de audio

**Abierto, no bloqueante.** El audio binario no pasa por `TokenBucket` (`main.py:1005-1027`), así que
un cliente autenticado puede encolar tareas de voz ilimitadas (CPU/RAM).

