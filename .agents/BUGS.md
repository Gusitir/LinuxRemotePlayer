# BUGS.md — registro desde 1.9.x

Este archivo no planifica: registra estado, manifestación y resolución. Las tareas viven en
PLAN/CURRENT. No tiene techo. Los bugs previos a 1.9.x viven en git y `archive/`.

# ABIERTOS

## B19 — OTA root sin autenticidad

**CRÍTICO · bloquea la siguiente release pública**

`lrp-update` instala como root un `.deb` y comprueba un sha256 servido por el mismo origen.
Detecta corrupción, no un origen comprometido. Quien controle Vercel/DNS/dominio puede entregar
un paquete y un hash hostiles. No existe timer: el usuario debe pulsar Actualizar, pero la app
lo invita a hacerlo. Plan: PLAN §GATE-OTA.

## B19b — TOCTOU y nombre predecible en `/tmp`

El actualizador usa un nombre predecible y separa verificación de instalación. Debe trabajar en
un `mktemp` root-only y mantener identificado el mismo inode/artefacto hasta instalarlo.

## M1 — migración incompleta nube/licencias

**Abierto por decisión D16-D18; todavía no es un defecto de 1.9.1.**

Backend, frontend, sitio y Supabase contienen Together, `ai-proxy`, licencias, compra, cuotas y
textos Paddle. Se resuelve como migración coordinada en PH24, no borrando referencias aisladas.

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

## H22 — eliminar/ocultar siempre visible

Cada icono muestra permanentemente su acción destructiva. Debe existir modo edición o una
interacción deliberada.

## H21 — `theme-color` no refresca en iOS moderno

En iPhone 12 cambia al reabrir la PWA; en iPhone 8+ lo hace en vivo. No hay workaround aceptado.

## L1 — STT local aún no seleccionado

SenseVoice-Small no soporta español. Whisper base/small y runtimes se deben medir con corpus
propio antes de declarar soporte o hardware mínimo. No aceptar cifras de terceros como resultado.

## L2 — acciones de IA necesitan frontera de seguridad

Needle debe emitir exclusivamente esquemas allowlist. El backend debe validar herramienta,
argumentos, confianza, estado y necesidad de confirmación. Nunca shell, sudo o texto ejecutable.

## L3 — puerto de automatización del navegador

CDP/BiDi puede controlar sesiones autenticadas. Si se adopta: `127.0.0.1`, perfil dedicado,
privilegios mínimos, apagado por defecto y adaptadores por sitio. MPRIS tiene prioridad.

## Menores

- `auth.py` compara un secreto con `==` en un camino; usar comparación constante.
- Fuentes bold/regular son el mismo archivo y se descargan/precachean dos veces.
- El `.deb` depende de `build-essential`, innecesario para un appliance final.
- El instalador imprime el token de pairing en el scrollback.
- `%input` en sudoers es más amplio que el usuario exacto del servicio.

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
