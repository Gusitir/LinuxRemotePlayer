# CONTEXT — decisiones y handoffs (v3)

> **COMPACT 2026-10-29.** Historia previa a D56 resumida a una línea por hito. El texto completo
> sigue en Git: `git show dcd26f5:.agents/CONTEXT.md` (895 líneas) y, para el tramo anterior a D56,
> `git show f698e18:.agents/CONTEXT.md`. D56 y D57 se conservan íntegras.

## Historia compactada (2026-06 → 2026-10-27)

| Fecha | Hito |
|---|---|
| 2026-06/08 | Nace la PWA-WS; se abre B19 (OTA root sin firma) y bloquea release pública; giro a voz local sin premium ni nube. |
| 2026-08-21 | Adopción v3: AGENTS autoridad, CURRENT estado, INDEX navegación, TESTING solo checks humanos, planes scope, APPCORE arquitectura; corrige D27; CAVEMAN durable. |
| 2026-08-21 | **D28**: betas opt-in reemplazan gate físico; 1.99.x instalable; stable no las descubre; B19 aceptado como riesgo. |
| 2026-08-22 | Integración beta verificada por SHA (`latest.json` 1.9.1, beta 1.99.1); T-121 espera HTPC. |
| 2026-08-23 | HANDOFF con main sincronizado; T-121 bloqueado por evidencia humana. |
| 2026-08-23 | **D29**: separa evidencia IA de humana; TST-DEVICE-001 `[SKIP]` aceptado; T-121 sin APTO. |
| 2026-08-23 | **D30**: BETA-FOUNDATION cerrada APTO (T-117..T-121); backup `complete` con hashes verificados (407bb66). |
| 2026-08-28 | **D31**: Debian 13 amd64 minimal único, Xorg/Openbox administrado, RTX 3060 única GPU; Plasma/Wayland/multidistro fuera. |
| 2026-08-28 | **D32**: contrato de paquetes Debian (lightdm, xorg, openbox, nvidia 550); prohíbe `.run`/nvidia-open; T-122 APTO. |
| 2026-08-31 | T-123..T-126 APTO: NVIDIA bootstrap, sesión Xorg/Openbox no-root, instalador y Firefox ESR kiosk (147/147). |
| 2026-08-31 | T-127..T-129 APTO: uinput, PipeWire, Avahi, UFW 8000/5353, sleep masked, rollback y docs Debian-only. |
| 2026-09-01 | T-130 prebuild: VERSION 1.99.2, builder/control/updater amd64 (190 pass). |
| 2026-09-01 | **D33**: topología de dos niveles (luego superada por D36). **D34**: selector de audio diferido. |
| 2026-09-01 | T-130 físico: 98bb9f1/SHA `a0b54c85`, 205/205; corrige token, mDNS y HDMI; reset físico sin evidencia. |
| 2026-09-01 | T-130 APTO: beta 1.99.2 pública, manifiesto=artefacto; stable 1.9.1. |
| 2026-09-01 | **D35**: instalación de un comando con hasta 2 reboots (fail-closed, TTY); OTA 1.99.1→1.99.2 pasó. |
| 2026-09-02 | MAINTAIN y REINDEX: control al día contra 98bb9f1 (207/207); deuda `state_applied_ok()`. |
| 2026-09-03 | **D36**: topología Arquitecto/Ingeniero/Auditor con IDs. **D37**: cierra Debian HTPC (G4 APTO, 95490ce). |
| 2026-09-03 | **D38**: aprueba PLAN_v2.0-appliance (LRP OS como producto; mínimo i5-3470/8GB/HD2500). |
| 2026-09-03 | **D39**: política `/boost` (prohibido a obreros, autorizado a Auditor, reservado a Arquitecto). |
| 2026-09-04 | **D40**: plan maestro regenerado; baseline 192.168.0.246; ASTRA-01..04. |
| 2026-09-05 | **D41**: plan v2.0 final con Wi-Fi dual y hotspot `LRP-Setup`; T-133..T-139 APTO; incluye D43 (rueda, play, mic). |
| 2026-09-07 | **D44..D47**: UI móvil (feedback táctil, edición, contraste, iconos, squircle) e invariante B1 intacta. |
| 2026-09-07 | HANDOFF T-140 APTO (261/261); siguiente ISO factory. |
| 2026-10-17 | **D48**: prioridad producto, sin suites por tarea, Cero-IO con workers flash. **D49**: briefs unitarios con anclas. |
| 2026-10-17 | **D50**: cierra PLAN_v2.0-appliance (T-140, T-141, T-142 con firma Ed25519; G4 APTO 59/59). |
| 2026-10-21 | MAINTAIN a main 88cf2f6; B19 cerrado en rama, no en main. |
| 2026-10-21 | **D51**: release 2.0.0 (merge `--no-ff`, beta congelada, rebuild como 2.0.0). **D52**: rotación del ancla OTA (privada perdida). |
| 2026-10-22 | **D53**: migración `D:`→`G:`; estabilizar sobre el appliance por SSH y construir la ISO una sola vez; B20–B25; "no boot device" era `BootOrder`. |
| 2026-10-22 | **D54**: tríada persistente coder/auditor/asistente, recibos ≤12 líneas, escritor único, 3 NO APTO escalan. |
| 2026-10-27 | **D55**: cierra el bloque D53 (`[T-149]` B20–B26 + GRUB/plymouth, `[T-144]` backend sin licencia); HTPC inalcanzable ese día. |

## 2026-10-29 · D56 — Giro a ISO open source GPL-3.0 (1.0.0)

El dueño redefine el proyecto: deja de ser un appliance comercial con licencia y OTA y pasa a ser una
**ISO de código abierto para portfolio**. Se retira toda la superficie comercial y se archiva el
desarrollo previo.

Decisiones aprobadas:

1. **Licencia**: GPL-3.0 para el proyecto nuevo **y** para el código previo (rama legacy incluida).
2. **Producto**: ISO Debian que arranca al panel; el móvil controla. Sin nube, sin cuentas, sin
   licencia, sin premium, sin telemetría.
3. **Sin OTA**: el updater, la firma Ed25519, el rollback, los manifiestos y el canal beta se eliminan.
   Las versiones se publican por release del repositorio. B19/B19b se cierran por eliminación.
4. **Archivo**: rama `legacy/2.0` + tag anotado `v2.0.0-legacy` (con `LICENSE` GPL-3.0 y `NOTICE`),
   para conservar el aprendizaje de licencias, web comercial y planes no consolidados. `main` sigue
   como 1.0.0.
5. **Instalación**: Android recibe **APK TWA** servida desde la web (sideload, sin Play Store, con
   `assetlinks.json`); iOS recibe tutorial de PWA; desktop instrucciones neutras.
6. **Web**: sirve ISO y APK con checksums, avisos de licencia y créditos de terceros; documentación de
   build. Repo público desde el inicio.
7. **Versión**: 1.0.0. Todo lo comercial (2.0.0) queda archivado.
8. **Voz diferida**: Needle 3 y voice-to-text quedan para T-157; hasta entonces micrófono y voz se
   desactivan y ocultan en la UI. No se borra el backend de voz.
9. **Bluetooth**: alcance reducido a encendido/apagado y lista de dispositivos.
10. **B19/B19b/M1** quedan superados por este giro y se cierran al ejecutar T-150.

El plan vigente pasa a `PLAN_v1.0.0-public.md` (T-150..T-155, T-157); `PLAN_v2.0.0-release.md` queda
como histórico del ciclo anterior.

## 2026-10-29 · D57 — Testeo por fase, producto primero

Instrucción del dueño durante F1: **priorizar producto sobre testeo**. Los gates de tarea quedan
limitados a micro-checks (<5 s: `py_compile`, `node --check`, `bash -n`, greps de aceptación); la
**suite completa corre una sola vez al cierre de cada fase** (G4) y otra vez antes del release. Los
bugs se resuelven al final de la fase con testeo dirigido, no tarea por tarea. La cobertura se **poda**
(se borran tests de funciones retiradas) en vez de crecer.

Motivo: cada corrida completa cuesta ~6 min y convirtió tareas de 2 minutos en ciclos de 20, frenando
el producto. No cambia el estándar de evidencia: el cierre de fase sigue exigiendo suite verde y
verificación en el HTPC.

## 2026-10-29 · D58 — Distribución: GitHub Releases + Vercel por Git

Decisión del dueño: los binarios (ISO, APK y `SHA256SUMS`) se publican como **GitHub Releases** del
repo público; la web estática se publica en **Vercel por integración Git** (push a `main`), sin CI ni
`vercel` CLI. Dominio `www.linuxremoteplayer.com` (alias `linux-remote-player.vercel.app` a mantener).
La ISO mide ~2 GiB: medirla en T-154 y partirla si excede el límite de 2 GiB por asset; plan B,
Cloudflare R2. El método de deploy se documentará en `docs/DEPLOY.md` (T-152).

## 2026-10-29 · D59 — Handoff: LRP OS 1.0.0 publicado

Cierre de la fase de publicación. El proyecto queda **retomable y desatendido** con este estado:

- **Release público `v1.0.0`** (latest) en `Gusitir/LinuxRemotePlayer` con ISO (`5cc67f10…`,
  2 093 056 000 B), APK (`fcfb76e0…`, 24 400 B) y `SHA256SUMS`; digests de la API iguales a los locales.
- **Repo público** con GPL-3.0; auditoría de secretos limpia (nunca se versionaron `.env`, keystores ni
  claves privadas).
- **Web 1.0.0** en producción (Vercel) con descargas, avisos GPL y documentación de build/deploy.
- **ISO validada en QEMU UEFI** end-to-end (instalación, reinicio automático, arranque desde disco y
  panel), y **APK compilada y firmada** con `lrp-keys/android-release.jks` (fuera del repo).

Queda pendiente solo lo que necesita manos del dueño: instalar la ISO en el HTPC y correr `dpkg -V` y
los checks de `TESTING.md` (`1.0.0 · release público`), probar el APK en un Android real, y la revisión
legal de términos (B39).

Cómo retomar: leer `CURRENT.md` (next_action), `PLAN_v1.0.0-public.md` (T-154 en curso, T-157 diferida)
y `docs/DEVELOPING.md` para reconstruir el entorno. Para republicar: `gh release create` está descrito
en `docs/DEPLOY.md`; el build de ISO vive en `scripts/debian/iso/`.
