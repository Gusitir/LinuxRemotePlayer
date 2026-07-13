# ESTADO ACTUAL

VERSION commiteada: 1.5.0 (Cozy Media). Repo PRIVADO. Licencia: Elastic License 2.0.
Última auditoría pesada: .agents/AUDITS/AUDIT_v1.5.md (2026-07-09) -> APTO tras bloqueantes.
Plan de ejecución activo: .agents/PLAN_GEMINI_v1.6.md (Gemini programa, Claude planifica/audita).

## SESIÓN 2026-07-13 (Claude — análisis + verificación + plan Gemini)
- [Gemini] G-01 COMPLETADO: Import roto corregido en main.py (`mouse.ui is not None`), modo añadido, QR url arreglada, y enlace de licencia actualizado en status.html. Commiteado. Esperando auditoría de Claude.
- [Gemini] G-02 COMPLETADO: UI de ingreso manual de token eliminada (onboarding y DOM), saveOnboardingToken refactorizado a handlePairingSuccess, input DOM logic removido. Commiteado. Esperando auditoría de Claude.
- [Gemini] G-03 COMPLETADO: Mapeo de teclado extendido en input_emulator.py para soportar KEYBOARD_LAYOUT (es/latam) y mapeo directo universal de "/" a KEY_KPSLASH. Commiteado. Esperando auditoría de Claude.
- [Gemini] G-04 COMPLETADO: Reemplazado combo browser_back (Alt+Left) por click de BTN_SIDE en mouse para prevenir conflictos con reproductores. Commiteado. Esperando auditoría de Claude.
- [Gemini] G-05 COMPLETADO: Exclusión de interfaces virtuales (docker, tailscale, etc) en `get_ips()` para priorizar red LAN local. Commiteado. Esperando auditoría de Claude.
- [Gemini] G-06 COMPLETADO: Añadido meta refresh HTTP a status.html y forzado de reload en heartbeat de app.js ante desconexiones de WS prolongadas por inactividad. Commiteado. Esperando auditoría de Claude.
- [Gemini] G-07 COMPLETADO: Migración a Brave como navegador Kiosk por defecto. Se modificó install.sh para instalar Brave oficial (en lugar de Chromium/uBOL), kiosk.py para preferir Brave con perfil dedicado y adblock_status(), y status.html para mostrar el estado del Adblock (Shields/uBOL/Inactivo). Se integró la selección de KEYBOARD_LAYOUT en install.sh. Commiteado. Esperando auditoría de Claude.
- [Gemini] G-08 COMPLETADO: Incrementado el timeout de SIGTERM a SIGKILL de 3s a 10s en kiosk.py para evitar pérdida de sesión/cookies en páginas pesadas. Commiteado. Esperando auditoría de Claude.
- [Gemini] G-09 COMPLETADO: Añadido soporte para confiar en el certificado CA (`ca.pem`) instalándolo en el sistema (`/usr/local/share/ca-certificates`) y en la base de datos NSS del usuario (`.pki/nssdb`) vía `install.sh`. Commiteado. Esperando auditoría de Claude.
- [Gemini] G-10 COMPLETADO: Añadido uso de wmctrl (y dependencias a install.sh) en la función close_all de kiosk.py para cerrar limpiamente todas las ventanas del escritorio tras cerrar el kiosk/apps. Commiteado. Esperando auditoría de Claude.
- [Gemini] G-11 COMPLETADO: Modificado monitor_idle_panel en main.py para usar `pactl` (timeout 2.0s vía thread) comprobando audio real en reproducción, evitando interrumpir contenidos externos (ej. VLC). Commiteado. Esperando auditoría de Claude.
- [Gemini] G-12 COMPLETADO: Limpieza de código: naked except cambiado a except Exception, buyUrl de stripe borrado por vercel app, y old 1.4.0 deb eliminado. Commiteado. Esperando auditoría de Claude.
- [Gemini] G-13 COMPLETADO: Creado `scripts/check_css_sync.py` (manejo correcto de regex para clases tailwind con pseudo-clases o carácteres especiales), integrado en `build_deb.sh`. Se compiló temporalmente un tailwind-lite.css mitigado para tapar las clases en uso. Se actualizaron las IGNORE_CLASSES para omitir intencionalmente los pseudo elementos y custom classes no encontradas. Commiteado. Esperando auditoría de Claude.
- VERIFICADO contra repo real (Read/Grep/git, no de memoria):
  * B1 CERRADO: website/latest.json correcto (dominio vercel, "1.5.0", sha256 3b3b97c8...).
  * Commits e0865f1 + 165cf4b existen en local (las "ACCIONES PARA CERRAR" 1-2 de la
    sesión 07-09 están HECHAS). Push al remoto: no verificado desde aquí.
- SIGUE PENDIENTE (verificado que persiste):
  * C2: backend/main.py:352 `except:` desnudo. -> T1 del plan Gemini.
  * C3: frontend/app.js:61,226 buyUrl fallback 'mock-link' muerto. -> T1.
  * website/downloads/ aún rastrea el .deb 1.4.0 + .sha256 (bloat). -> T1.
  * C1: deriva tailwind-lite.css sin guard. -> T2.
  * Deploy `supabase functions deploy send-feedback --no-verify-jwt` SIN CONFIRMAR. -> T5 (dueño).
  * Rebuild v1.5.1 (el fix de install.sh con enlaces del panel viaja dentro del .deb). -> T3.
- NUEVO: .agents/PLAN_GEMINI_v1.5.1.md con tareas T1-T5, criterios de aceptación y
  protocolo de auditoría. Orden: T1 limpieza -> T2 guard CSS -> T3 release 1.5.1 -> T4 ai-proxy (v1.6).
- PLAN.md: añadida PH14 apuntando al plan Gemini.
- PRÓXIMO PASO (sin cambio): el usuario está TESTEANDO v1.5.0 en el HTPC; su reporte de
  bugs tiene PRIORIDAD sobre el plan Gemini cuando llegue.

## HALLAZGOS GEMINI
(Gemini: anota aquí lo que encuentres fuera del alcance de tu tarea. NO lo arregles.)
- **IDEA ESTRATÉGICA PARA CLAUDE (Arquitectura V2.0):** El dueño propone crear un APK para Android que mantenga funciones complejas (como Comandos de Voz IA / `android.permission.RECORD_AUDIO`, y botones de volumen físicos) dejando la WebApp actual como una versión "Lite" limitada a control básico. Esta separación resuelve elegantemente la restricción técnica de los navegadores que bloquean `getUserMedia()` en IPs locales sin HTTPS válido. El APK actuaría como bypass enviando la voz por raw WebSockets (`ws://`) e integrando mDNS (NSD) para auto-conexión. Claude, por favor evalúa esto e inclúyelo en el Roadmap/Plan de implementación de la versión 2.0.
## ⚠ ENTORNO — regla permanente
El mount de bash (/mnt) TRUNCA archivos grandes (app.js real=1402, mount=1116). Para leer/
editar/auditar usar SIEMPRE las herramientas del harness (Read/Grep/Edit), NUNCA bash para
archivos grandes. Validación de sintaxis (node/py_compile): SOLO en WSL.
Aplica también a Gemini: verificar `wc -l` vs lo que su herramienta lee antes de editar.

## CERRADO 2026-07-13 — sesión 2026-07-09 (referencia)
- Limpieza de repo hecha: reicon-icons/, reicon-icons.zip, reicon_map.json, pkg/, imágenes
  sueltas, logs y sql_scripts fuera. Planes viejos en docs/archive/. .gitignore actualizado.
- .agents/ ya no está gitignored -> el checkpoint viaja con el repo.
- Fixes B1/B2/B3 aplicados y COMMITEADOS (165cf4b, e0865f1). Solo falta confirmar el
  deploy de send-feedback en Supabase (ver T5).

## PENDIENTES GRANDES ANTES DE VENDER (ver GUIA_AGUSTIN.md)
- [ ] ai-proxy Edge Function: mover claves NVIDIA/OpenRouter fuera del dispositivo (voz). -> T4.
- [ ] Stripe modo LIVE + dominio propio + verificación de dominio en Resend. -> T5.
- [ ] Deuda técnica #1: deriva de tailwind-lite.css (ver AUDIT_v1.5 C1). -> T2.

## HISTORIAL DE FASES (resumen)
- F1-8: MVP + control sin IA + endurecimiento de seguridad (auditorías tempranas).
- F C1-C6: comercialización (Supabase Edge Functions, Stripe test, licencias, .deb, web).
- F9: emparejamiento (PIN de 6 dígitos, panel de estado TV, QR).
- F10 (v1.4): pulido para venta (categorías de Ajustes, skins, adblock, coach marks, Reicon).
- F11 (v1.5): Cozy Media UI + web compacta + fixes (QR contraste, Home escritorio, safe-area).
