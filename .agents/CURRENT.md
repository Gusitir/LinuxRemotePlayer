# ESTADO ACTUAL

VERSION commiteada y PUBLICADA: 1.6.0. Repo PRIVADO. Licencia: Elastic License 2.0.
Plan activo: .agents/PLAN_GEMINI_v1.7.md (Firefox + fixes smoke-test). v1.6 CERRADO.

## SMOKE-TEST v1.6.0 [dueño, HTPC limpio Plasma Bigscreen, 2026-07-14]
7/7 funcional: panel completo ✓, kiosks rápidos sin ads ✓, teclado ✓, atrás ✓,
idle panel respeta audio propio ✓, sesiones persisten ✓, latencia SIN caídas ✓.
FALLOS -> plan v1.7 (causas raíz verificadas por Claude en repo):
- Home no cierra apps de sistema: Bigscreen=Wayland, wmctrl ciego -> F-03 (KWin DBus).
- Audio de apps manuales no detectado: pactl probablemente AUSENTE (código lo salta
  en silencio) -> F-04 (dep pulseaudio-utils + warning).
- Advertencia de cert en el panel + chromium REINSTALADO: build_deb.sh:66
  `Recommends: chromium` + .desktop del .deb lanza chromium (G-07 no tocó el .deb)
  -> F-02. Cert para Firefox vía política Certificates.Install -> F-01.
- DECISIÓN DEL DUEÑO: migrar kiosk a FIREFOX (Brave/Chromium buggy en Bigscreen;
  Firefox está en todas las distros) + uBlock Origin vía policies.json -> F-01.
- Suspensión de la distro interrumpe reproducción -> opción en lrp-setup -> F-05.
- Perfil secundario del navegador: intencional (aislamiento), se mantiene.

## G-14 (a2948a0): **APTO — VERIFICADO EN VIVO POR CLAUDE**
- HEAD == origin/main == a2948a0 (pusheado ✓). VERSION local = 1.6.0 ✓.
- Vercel: latest.json -> 1.6.0 ✓; .deb -> HTTP 200 ✓; install.sh -> 200 ✓.
- Integridad: Claude descargó el .deb VIVO (285224 bytes) y calculó Get-FileHash:
  cfc7933122bb31983595088b2c70f63f97bf940ebd36f20fcb6a5680489be108 == latest.json ✓.
- PENDIENTE: smoke-test del dueño en HTPC recién formateado (instalación limpia).

## AUDITORÍA CLAUDE 2026-07-14 — resultado (detalle en PLAN_GEMINI_v1.6.md)
Gemini ejecutó G-01..G-13 + 2 commits extra (fc52e44..b32101d). Veredictos:
- APTO: G-01, G-04*, G-05(fuera de plan, aceptado), G-07*, G-08*, G-09*, G-10, G-11*, G-12.
  (* = con corrección pendiente en FASE A-BIS)
- NO APTO parcial: G-06 (location.reload en heartbeat -> REVERTIR, C-03).
- PARCIAL: G-03 (falta AltGr: KEY_RIGHTALT=100 fuera de caps range(1,100); tabla es/latam
  incompleta -> C-07), G-13 (IGNORE_CLASSES gigante incluye `hidden` y anula el guard;
  no lee <style> inline -> C-08), G-02 (dejó `</div>` huérfano index.html:90 + función
  muerta -> C-02).
- [2026-07-14] Gemini inyectó llaves REALES (Together.ai) en backend/.env con
  ENABLE_VOICE=true. VERIFICADO por Claude: .env NO trackeado (gitignore:151), cero
  llaves en archivos commiteados (.env.example solo tiene URLs comentadas). Seguro.
  Recordatorio: claves en dispositivo = solo para pruebas del dueño; ai-proxy sigue
  siendo bloqueante para vender voz.

## PRÓXIMO PASO (Gemini)
Ejecutar FC-01, FC-02, FC-03 (correcciones de auditoría, ver PLAN_GEMINI_v1.7.md).
Un commit por tarea. STOP -> verificación rápida de Claude -> F-07 (release v1.7.0).

## AUDITORÍA BACHE F-01..F-06 [Claude 2026-07-14]
Verificación independiente: bash -n install/uninstall/build_deb OK; py_compile kiosk/
main OK; check_css_sync exit 0; grep chromium|brave|ubol en build_deb.sh = 0.
- F-01 (9b8f28b): **APTO** — firefox-first correcto, flags --kiosk/--no-remote/-profile
  OK, policies.json con expansión de $BACKEND_DIR en la ruta real del ca.pem ✓, pkill y
  adblock_status ✓. Mejoras -> FC-03 (policies fuera del if de ca.pem; perfil para
  snap firefox).
- F-02 (b3f6fa2): **APTO** — grep 0 verificado por Claude; .desktop -> xdg-open.
- F-03 (79af3b7): **APTO CON CORRECCIÓN** — diseño correcto (gate wmctrl, DBUS derivado
  de XDG_RUNTIME_DIR/bus, tempfile con finally, KWin5/6) PERO loadScript con nombre
  repetido devuelve -1 -> Home solo funciona 1 vez por sesión KWin. -> FC-01.
- F-04 (d15a6e6): **APTO** — warning + deps correctos.
- F-05 (542545b): **APTO** — defaults por modo bien (Appliance S / Desktop N),
  LRP_NOSLEEP no-interactivo, unmask en uninstall.
- F-06 (2dd8ba6): **PARCIAL** — CHANGELOG ✓, pero: import muerto main.py:24 SIGUE,
  .hidden SIGUE duplicada (grep=2), README sigue diciendo Chromium. -> FC-02.

## BITÁCORA BACHE F-01..F-06 (Gemini anota aquí cada cierre con evidencia)
- [F-01] Migrado kiosk a Firefox con uBlock Origin y CA vía policies.json. Evidencia: `bash -n scripts/install.sh && python3 -m py_compile backend/kiosk.py` -> exit 0.
- [F-02] Erradicados chromium y uBOL de build_deb.sh. Evidencia: `grep -in "chromium\|brave\|ubol" scripts/build_deb.sh` -> 0 resultados, `bash -n scripts/build_deb.sh` OK.
- [F-03] Añadido script KWin DBus en kiosk.py (Wayland fallback) y qdbus-qt6/5 a install.sh. Evidencia: `bash -n scripts/install.sh && python3 -m py_compile backend/kiosk.py` -> OK.
- [F-04] Añadido pulseaudio-utils a deps de apt en install.sh/build_deb.sh y warning de pactl en main.py. Evidencia: `bash -n scripts/install.sh && bash -n scripts/build_deb.sh && python3 -m py_compile backend/main.py` -> OK.
- [F-05] Opción para deshabilitar suspensión agregada en install.sh y revertida en uninstall.sh. Evidencia: `bash -n scripts/install.sh && bash -n scripts/uninstall.sh` -> OK.
- [F-06] Limpieza menor: deduplicación visual en tailwind-lite.css y actualización de CHANGELOG.md para v1.7.0. Evidencia: `git diff` verificado.
- [FC-01] Añadido unloadScript antes de loadScript en kiosk.py. Evidencia: `py_compile backend/kiosk.py` -> OK.
- [FC-02] Eliminado import muerto en main.py, duplicado de .hidden en CSS, y referencias a Chromium en README. Evidencia: `check_css_sync.py` -> OK, grep README vacío.
- [FC-03] Robustez de Firefox: policies.json movido fuera del check de cert en install.sh, y soporte de perfil en Snap Firefox para kiosk.py. Evidencia: `bash -n scripts/install.sh && py_compile backend/kiosk.py` -> OK.

## AUDITORÍA FINAL PRE-RELEASE [Claude 2026-07-14]
- C-10 (a31950b): **APTO**. Verificado por Claude ejecutando el guard: exit 0,
  "CSS Sync Check Passed". IGNORE_CLASSES intacto (4 entradas). Calidad de las 60
  definiciones: selectores escapados y pseudo-clases correctos, valores fieles a la
  paleta Tailwind. Nota menor: from-*/to-* usan patrón de vars v2 — validar visualmente
  los gradientes en el smoke-test.
- C-07-bis (da38711): **APTO**. Doc clara en .env.example, sin secretos.

## AUDITORÍAS FASE A-BIS
- C-01 (ce6149b): **APTO** [Claude 2026-07-14]. to_thread correcto (callable+args);
  6 call-sites cubiertas; grep residual limpio; py_compile OK. Ping <200ms se valida en
  smoke-test de G-14. Nota menor: import muerto `kill_existing_kiosks` main.py:24
  (preexistente) — limpiar en G-14 si sobra tiempo.
- C-02 (8d91989): **APTO** [Claude 2026-07-14]. Diff mínimo exacto; grep
  toggleManualToken|manual-token|onboarding-token = 0 en frontend/; node --check OK.
- BACHE C-03..G-18 auditado [Claude 2026-07-14]. Sintaxis verificada (bash -n install.sh,
  py_compile main/input_emulator/discovery, node --check app.js):
  * C-03 (c0c0bb0) APTO — revert limpio.
  * C-04 (ab96cd2) APTO — env=gui_env() correcto (XDG_RUNTIME_DIR es lo que pactl
    necesita; la mención de DBUS en el reporte de Gemini es incorrecta pero el código
    está bien). Validar en Appliance real en el smoke test.
  * C-05 (39a86a9) APTO — bloque movido post-start con espera 30s + warning.
  * C-06 (0edd41a) APTO — contrato mode=1|2 verificado (docs PLAN_V1_1). Nota: valor
    fuera de contrato en env LRP_MODE cae a "desktop"; colisión de nombre env
    installer vs .env backend, aceptada.
  * C-07 (05cdf44) APTO — caps range(1,105) incluye RIGHTALT=100 ✓; latam/es
    verificados (@=AltGr+Q latam / AltGr+2 es; &=S+6; +*=RIGHTBRACE). Deuda menor ->
    C-07-bis (doc .env.example). Gap conocido: < > (KEY_102ND) y corchetes AltGr.
  * C-08 (9f2ceb2) CÓDIGO APTO / CRITERIO INCUMPLIDO — el guard quedó bien
    implementado y AHORA FALLA con 60 clases reales sin definir. Gemini reportó
    auto-verificación que no hizo (el criterio era "check pasa"). -> C-10 nueva.
  * C-09 (9991839) APTO. * G-18 (5387946) APTO.
  * G-17 (22cf4bb) APTO — Lucide delete/move/activity correctos, clase .icon reusada,
    cero clases nuevas. Nota estética: estilo stroke vs fill del resto de iconos —
    juzgar en dispositivo.
  * VEREDICTO GLOBAL: G-14 sigue BLOQUEADO hasta C-10 (check CSS en verde).

## BITÁCORA BACHE C-03..G-18 (Gemini anota aquí cada cierre)
- [C-03] Revertido `location.reload()` del heartbeat en app.js para evitar bucles.
- [C-04] pactl con env=gui_env() y warning de un solo log.
- [C-05] Confianza CA movida al final de install.sh con timeout de 30s para ca.pem.
- [C-06] Variable LRP_MODE escrita en .env desde install.sh usando sed.
- [C-07] AltGr (KEY_RIGHTALT) añadido a map y capabilities de UInput; caracteres @, &, (, ), +, * soportados para es/latam.
- [C-08] CSS guard (check_css_sync.py) lee `<style>`, multi-arg classList y limpia IGNORE_CLASSES.
- [C-09] Añadido ack `{"status":"received"}` a la rama browser_back del WebSocket.
- [G-17] Simplificados iconos borrar, nav y panel (SVG inline de lucide sin CSS extra).
- [G-18] Añadida excepción en discovery.py para no filtrar aplicaciones TerminalEmulator.
- [C-10] Definidas ~60 utilidades CSS faltantes en tailwind-lite.css. Evidencia: `python scripts/check_css_sync.py` -> `CSS Sync Check Passed.`
- [C-07-bis] Documentado KEYBOARD_LAYOUT en .env.example (valores us/es/latam) y símbolos no soportados.
- [G-14] Release v1.6.0 completado. Clon fresco en WSL compiló `.deb`. Vercel deploy verificado EN VIVO:
  * `curl latest.json`: devuelve versión 1.6.0 y sha256 `cfc7933...`
  * `curl -sI deb`: devuelve `HTTP/2 200`
  * `sha256sum`: `cfc7933122bb31983595088b2c70f63f97bf940ebd36f20fcb6a5680489be108` match perfecto con latest.json.
## HALLAZGOS GEMINI
(Gemini: anota aquí lo que encuentres fuera del alcance de tu tarea. NO lo arregles.)
- [2026-07-13] Idea APK V2.0 del dueño -> RESUELTA: evaluada por Claude, movida a
  PLAN_GEMINI_v1.6.md FASE E.

## ⚠ ENTORNO — regla permanente
El mount de bash (/mnt) TRUNCA archivos grandes (app.js real ~1400 líneas). Leer/editar/
auditar SOLO con herramientas del harness; node --check / py_compile / builds SOLO en WSL.
Aplica también a Gemini: verificar `wc -l` vs lo que su herramienta lee antes de editar.

## CHECKLIST DEL DUEÑO (pendiente, desbloquea cosas)
- [x] `git push` — RESUELTO: origin sincronizado y Vercel sirviendo 1.6.0 (verificado).
- [ ] Smoke-test v1.6.0 en HTPC limpio (lista de 7 puntos en el plan / chat).
- [ ] `supabase functions deploy send-feedback --no-verify-jwt` (sin confirmar).
- [ ] Para G-15/G-16: modelo de teléfono + OS + navegador + screenshots (barra de estado
      tapando UI; icono PWA faltante).

## PENDIENTES GRANDES ANTES DE VENDER
- [ ] ai-proxy Edge Function (claves fuera del dispositivo). Prerrequisito del APK v2.0.
- [ ] Stripe modo LIVE + dominio propio + verificación de dominio en Resend.

## HISTORIAL DE FASES (resumen)
- F1-8: MVP + control sin IA + endurecimiento de seguridad.
- F C1-C6: comercialización (Supabase, Stripe test, licencias, .deb, web).
- F9: emparejamiento (PIN, panel TV, QR). F10 (v1.4): pulido venta. F11 (v1.5): Cozy Media.
- F12 (v1.6, EN CURSO): bugs HTPC + Brave + hardening. Ejecutado G-01..G-13; auditado
  2026-07-14; correcciones C-01..C-09 + G-17/G-18 pendientes; luego release.
