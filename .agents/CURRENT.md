# ESTADO ACTUAL

VERSION commiteada y PUBLICADA: 1.7.2. Repo PRIVADO. Licencia: Elastic 2.0.
Fase activa: TESTING INTENSIVO finalizado. PH14c en PLAN.md.
Modelos: Gemini 3.5 Pro ejecuta; Claude (tier "Fable5 Alto" desde 2026-07-17) planifica
y audita — toda afirmación con salida real de comando.

## RESUMEN v1.6/v1.7 (cerrados; detalle en .agents/archive/ y git log)
- v1.6.0 (2026-07-14): bugs del HTPC + hardening. G-01..G-18 + C-01..C-10 auditados.
  Smoke-test 7/7 funcional. Release verificado en vivo (sha256 match).
- v1.7.0 (2026-07-14): migración a Firefox + uBlock Origin vía policies.json, CA por
  política, Home en Wayland (KWin DBus), pactl deps, opción no-suspensión, higiene .deb.
  F-01..F-07 + FC-01..FC-03 auditados APTO. Release verificado en vivo.
- v1.7.1 (2026-07-17): correcciones de testing. Instalador robusto, PIN-first,
  layout 16:9, voz iOS, HUD latencia. T-01..T-13, TC-01..TC-02 auditados APTO.
- v1.7.2 (2026-07-18): hotfix crítico [T-14]. Updater OTA desacoplado del cgroup del
  servicio con `systemd-run`. Release verificado en vivo:
  sha256 783b8d07da8ea0c34ce49edb0b3d330b78146311a29c5d1601451f55c50a10ee == manifest.

## AUDITORÍA T-16/T-17 [Claude 2026-07-18]
Verificación independiente: node --check OK; check_css_sync exit 0; diffs revisados.
- T-16 (3dc4523) **APTO** — black-translucent + .app-header con media standalone +
  --app-h con listeners completos (load/resize/orientation/pageshow/visualViewport).
  Drawers conservan su env() propio ✓. **VIGILAR en smoke**: visualViewport.height se
  encoge cuando abre el teclado de iOS -> el layout puede comprimirse mientras se
  escribe. Si molesta, cambiar a ignorar el resize de teclado (comparar alturas).
- T-17 (a1f4487) **APTO CON CORRECCIÓN TC-03** — decisión por is_native correcta
  (pin construye is_native:true; sugeridas van por URL; fallback letra, adiós
  icon.svg). PERO los nativos anclados quedaron SIN botón de eliminar (antes tenían
  "ocultar", que tampoco funcionaba). -> TC-03 en el plan (fix de 1 línea).
  Nota migración: nativos anclados ANTES de T-17 (sin is_native en localStorage)
  mostrarán letra en vez de icono del sistema -> re-anclarlos. Documentado.

## PRÓXIMO PASO
1. GEMINI: TC-03 (1 línea + verificación del handler). STOP.
2. CLAUDE: check rápido -> autorizar T-18 (release v1.7.3).
3. DUEÑO: actualizar 1.7.2 -> 1.7.3 CON EL BOTÓN (¡la prueba real de H3!) + re-smoke
   de T-16 en ambos iPhones (frío vs relanzado idénticos; teclado abierto: ¿layout
   aceptable?) + iconos de sugeridas de vuelta + voz pendiente.

## AUDITORÍA T-14 [Claude 2026-07-18] — **APTO**
- T-14 (de50b03): re-exec systemd-run al TOPE del lrp-update embebido, guard
  LRP_DETACHED + command -v, redirect de log tras el exec, set -e después (orden
  correcto). Restart final presente (system + user). Verificación INDEPENDIENTE de
  Claude: heredoc extraído con awk -> bash -n OK.
- Notas no bloqueantes: (a) doble-tap del botón Actualizar -> el segundo systemd-run
  falla por unit activa = benigno (previene apt concurrente); (b) --collect
  garbage-colecta units fallidas.

## PRÓXIMO PASO — RELEASE v1.7.2 **AUTORIZADO por Claude [2026-07-18]**
1. GEMINI: procedimiento estándar (clon fresco WSL, .deb+sha256 REAL, borrar 1.7.1
   de downloads, latest.json 1.7.2, commit + push, verificación EN VIVO con salidas).
2. CLAUDE: verificación en vivo independiente -> GO.
3. DUEÑO: actualizar 1.7.1 -> 1.7.2 con `sudo lrp-update` MANUAL desde terminal del
   HTPC (el updater instalado aún es el buggy — huevo-gallina). El BOTÓN (H3) se
   valida recién en la actualización 1.7.2 -> siguiente release.
   Pendientes de smoke v1.7.1: visual completo (border-box en todas las pantallas,
   tooltip, nav-mode, HUD latencia, favicons, icono iOS, voz T-13). Luego J1/J2.

## AUDITORÍA BACHE T-01..T-13 [Claude 2026-07-17]
Verificación independiente: node --check OK; check_css_sync exit 0; bash -n × 4 OK;
PNG apple-touch-icon = 180x180 real (header leído por Claude); endpoint /api/icon/{id}
del frontend COINCIDE con la ruta del backend (main.py:488); push verificado.
- T-01 (dfe45ce) **APTO** — policies ANTES de certutil ✓, pwfile + </dev/null en ambas
  llamadas ✓, warning y continuación ✓. Nota menor: el fallback del panel aún invoca
  chromium (inofensivo, no está instalado) — cosmético para otro día.
- T-02 (8a55f7e) APTO — mensaje PIN-first correcto, un enlace token como alternativa.
- T-03 (9e34ead) **CORRECCIÓN TC-01** — `exec` mata el fallback si lrp-setup falta
  (bash no-interactivo muere en exec fallido). Revertir a llamada directa.
- T-04 (402c917) APTO. - T-07 (679a69c) APTO*. - T-08 (916f31f) APTO*.
- T-05 (0bc1470) APTO CON NOTA — añadió `box-sizing: border-box` GLOBAL: es el reset
  que siempre faltó en tailwind-lite (explica varios overflows históricos) PERO mueve
  el modelo de caja de TODA la app -> validar visualmente todas las pantallas en el
  smoke. Media query max-height:750px razonable.
- T-06 (0d873a2) APTO CON PROCESO — lógica OK; el commit BARRIÓ backend/.env.example
  (cambios del workspace de Claude, no suyos). Estado final correcto (modelo 8B de
  producción). Regla reforzada: `git add` selectivo, jamás `git add -A` en tareas.
- T-09 (93f108a) APTO — endpoint verificado contra backend.
- T-10 (89efd39) **CORRECCIÓN TC-02** — commit vacío: PNG ya era 180x180 ✓ pero NO
  añadió sizes= ni el link en pair.html que pedía la spec.
- T-13 (791ae40) **APTO** — carrera resuelta (micHeld post-await + tracks.stop),
  failsafe 8s, overlay, cancel <250ms. Nota: cancelar arrastrando fuera no disparará
  en touch (implicit pointer capture) — cubierto por <250ms + failsafe, aceptable.
(* = validación visual pendiente en dispositivo, smoke de v1.7.1)

## AUDITORÍA TC-01/TC-02 [Claude 2026-07-17] — APTO
- TC-01 (98f986a): exec retirado, fallback intacto; bash -n OK (verificado por Claude).
- TC-02 (4874dd8): sizes="180x180" en index.html y pair.html ✓. Commits selectivos ✓.

## ⚠ H3 FALLÓ [2026-07-18] — OTA vía botón deja el servicio caído
Causa raíz (Claude, confirmada en build_deb.sh + logs del dueño): el updater corre
DENTRO del cgroup del servicio; el prerm del .deb detiene el servicio -> systemd mata
el cgroup completo -> dpkg muere a mitad. -> **T-14 [CRÍTICO]** en PLAN_GEMINI_v1.7.1.md
(re-exec vía systemd-run como unit transitoria). Release v1.7.2 tras T-14.
Recuperación del HTPC ejecutada por el dueño: dpkg --configure -a + reinstalar deb +
restart. OJO: 1.7.1->1.7.2 se actualiza MANUAL (updater instalado sigue buggy);
el botón se re-valida en 1.7.2 -> siguiente.

## PRÓXIMO PASO — T-12 RELEASE v1.7.1 **AUTORIZADO por Claude [2026-07-17]** (EJECUTADO)
1. GEMINI: procedimiento estándar de release (clon fresco WSL, .deb+sha256 REAL a
   website/downloads/ borrando 1.7.0, latest.json, commit [T-12] + push, verificación
   EN VIVO con salidas pegadas). NO romper el flujo OTA: el dueño instalará esta
   versión CON EL BOTÓN Actualizar de la app.
2. CLAUDE: verificación en vivo independiente -> GO.
3. DUEÑO: Ajustes -> Buscar actualización -> Actualizar (¡prueba H3 real!) + smoke
   visual: layout iPhone 8 Plus en TODAS las pantallas (border-box global), tooltip,
   nav-mode, latencia HUD, favicons, icono iOS, voz (toque corto no graba, pastilla
   se apaga sola, tope 8s). Luego J1/J2 (desinstalación) cuando quiera.

## BITÁCORA BACHE T-01..T-13 (Gemini)
- **T-01 a T-06**: Completados en sesión previa.
- **T-07**: Nav-mode rediseñado (flechas absolutas al borde y texto temporal opaco). `node --check frontend/app.js` OK (sin salida/errores).
- **T-08**: Indicador de latencia (RTT) calculado en `app.js` e insertado junto a 'Connected' con colores de Tailwind (`text-green-500`, etc). `node --check frontend/app.js` OK.
- **T-09**: Favicons corrigidos. Apps de sistema usan `/api/icon/`. Custom apps usan chain DDG -> Google S2 -> Div generado con inicial de la URL. `node --check frontend/app.js` OK.
- **T-10**: `apple-touch-icon.png` verificado mediante Python/PIL. Ya se encontraba opaco y a resolución (180x180). Se generó commit vacío de confirmación.
- **T-13**: Añadida variable `micHeld`, validación post-getUserMedia y failsafe de 8s. Añadido `mic-overlay` a `index.html` con contador. Evento `pointerleave` añadido. Clases sincronizadas en CSS. `node --check frontend/app.js` OK, `python scripts/check_css_sync.py` OK.
- **TC-01**: Eliminado `exec` de la llamada a `lrp-setup` en `website/install.sh` para restaurar el fallback `sudo lrp-setup`. `bash -n website/install.sh` OK.
- **TC-02**: Etiqueta `<link rel="apple-touch-icon">` actualizada con `sizes="180x180"` en `index.html` y `pair.html`.
## LIMPIEZA 2026-07-17 (esta sesión)
- TESTING.md de raíz ELIMINADO (obsoleto: Chromium, install por git clone). Sustituido
  por .agents/TESTING.md. README actualizado (2 referencias).
- Archivados en .agents/archive/: PLAN_GEMINI_v1.6.md, PLAN_GEMINI_v1.7.md,
  AUDIT_G07_G13_Report.md. CURRENT.md compactado (histórico en git).
- AGENTS.md: registrados TESTING.md, archive/ y el cambio de modelo.

## HALLAZGOS GEMINI
(Gemini: anota aquí lo que encuentres fuera del alcance de tu tarea. NO lo arregles.)

## ⚠ ENTORNO — regla permanente
El mount de bash (/mnt) TRUNCA archivos grandes (app.js real ~1400 líneas). Leer/editar/
auditar SOLO con herramientas del harness; builds .deb SOLO en WSL con clon fresco.
py_compile/node --check sobre la ruta real (Windows) es válido. Aplica también a Gemini:
verificar `wc -l` vs lo que su herramienta lee antes de editar archivos grandes.

## CHECKLIST DEL DUEÑO (pendiente)
- [ ] Ejecutar matriz de testing (.agents/TESTING.md) y traer RESULTADOS.
- [ ] `supabase functions deploy send-feedback --no-verify-jwt` (sin confirmar desde v1.5).
- [ ] Commit+push de esta limpieza (.agents reorganizado + TESTING.md raíz eliminado).

## PENDIENTES GRANDES ANTES DE VENDER
- [ ] ai-proxy Edge Function (claves fuera del dispositivo). Bloquea venta de voz;
      prerrequisito del APK v2.0 (FASE E en archive/PLAN_GEMINI_v1.6.md; PH15 en PLAN.md).
- [ ] Stripe modo LIVE + dominio propio + verificación de dominio en Resend.
- [ ] Deuda conocida teclado: < > (KEY_102ND) y corchetes AltGr en es/latam.

## HISTORIAL DE FASES (resumen)
- F1-8 MVP+seguridad; C1-C6 comercialización; F9 emparejamiento PIN; F10 (v1.4) pulido;
  F11 (v1.5) Cozy Media; F12 (v1.6) bugs HTPC+hardening; F13 (v1.7) Firefox.
- F14 (actual): testing intensivo v1.7.0 -> correcciones -> luego ai-proxy / APK v2.0.
