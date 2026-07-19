# ESTADO ACTUAL

## AUDITORIA T-21 (7d29dbc): **APTO** [Claude 2026-07-19, RECTIFICADA]
Primer dictamen fue NO APTO por "backslashes en build_deb.sh:53" — FALSA ALARMA por
CARRERA DE EDICION: el auditor leyo el working tree MIENTRAS Gemini seguia editando
(el dueno lo habia avisado); el grep capturo un borrador transitorio que Gemini
corrigio antes de cerrar. Desempate con `git show HEAD:` (object store): slashes
correctos, status limpio, hash identico -> el commit siempre estuvo bien. TC-04
CANCELADA. LECCION (2 reglas nuevas de auditoria):
(a) AUDITAR SOLO tras el STOP explicito del ejecutor — nunca con edicion en curso;
(b) auditar contra COMMITS (`git show HEAD:archivo` / `git show <hash>`), no contra
    el working tree, que puede estar a medio editar.
Resto de T-21 verificado: placeholder sw.js OK, sed OK, guard OK, docs OK.

## PROXIMO PASO [vigente 2026-07-19] — T-22 RELEASE v1.7.5 **AUTORIZADO**
1. GEMINI: T-22 procedimiento estandar (clon fresco WSL, guard del sw.js debe pasar,
   sha256 real pegado, verificacion en vivo pegada). EVIDENCIA EXTRA: extraer del .deb
   la linea 1 del sw.js empaquetado -> debe decir 'lrp-1.7.5'.
2. CLAUDE: verificacion en vivo + extraccion propia del sw.js del .deb -> GO.
3. DUENO: boton a 1.7.5 (confirmacion limpia H3) + reinstalar PWA (ultima vez) +
   re-smoke + VOZ (DeepSeek: F:\Mi unidad\TESTING\VOICE_SETUP_DEEPSEEK.md).
NOTA HIGIENE: CURRENT.md con encoding mixto y sobrepeso -> COMPACTAR al cerrar v1.7.5.

VERSION commiteada y PUBLICADA: 1.7.2. Repo PRIVADO. Licencia: Elastic 2.0.
Fase activa: TESTING INTENSIVO finalizado. PH14c en PLAN.md.
Modelos: Gemini 3.5 Pro ejecuta; Claude (tier "Fable5 Alto" desde 2026-07-17) planifica
y audita 窶・toda afirmaciﾃｳn con salida real de comando.

## RESUMEN v1.6/v1.7 (cerrados; detalle en .agents/archive/ y git log)
- v1.6.0 (2026-07-14): bugs del HTPC + hardening. G-01..G-18 + C-01..C-10 auditados.
  Smoke-test 7/7 funcional. Release verificado en vivo (sha256 match).
- v1.7.0 (2026-07-14): migraciﾃｳn a Firefox + uBlock Origin vﾃｭa policies.json, CA por
  polﾃｭtica, Home en Wayland (KWin DBus), pactl deps, opciﾃｳn no-suspensiﾃｳn, higiene .deb.
  F-01..F-07 + FC-01..FC-03 auditados APTO. Release verificado en vivo.
- v1.7.1 (2026-07-17): correcciones de testing. Instalador robusto, PIN-first,
  layout 16:9, voz iOS, HUD latencia. T-01..T-13, TC-01..TC-02 auditados APTO.
- v1.7.2 (2026-07-18): hotfix crﾃｭtico [T-14]. Updater OTA desacoplado del cgroup del
  servicio con `systemd-run`. Release verificado en vivo:
  sha256 783b8d07da8ea0c34ce49edb0b3d330b78146311a29c5d1601451f55c50a10ee == manifest.

## AUDITORﾃ喉 T-16/T-17 [Claude 2026-07-18]
Verificaciﾃｳn independiente: node --check OK; check_css_sync exit 0; diffs revisados.
- T-16 (3dc4523) **APTO** 窶・black-translucent + .app-header con media standalone +
  --app-h con listeners completos (load/resize/orientation/pageshow/visualViewport).
  Drawers conservan su env() propio 笨・ **VIGILAR en smoke**: visualViewport.height se
  encoge cuando abre el teclado de iOS -> el layout puede comprimirse mientras se
  escribe. Si molesta, cambiar a ignorar el resize de teclado (comparar alturas).
- T-17 (a1f4487) **APTO CON CORRECCIﾃ哲 TC-03** 窶・decisiﾃｳn por is_native correcta
  (pin construye is_native:true; sugeridas van por URL; fallback letra, adiﾃｳs
  icon.svg). PERO los nativos anclados quedaron SIN botﾃｳn de eliminar (antes tenﾃｭan
  "ocultar", que tampoco funcionaba).
- TC-03 (correcciﾃｳn en createAppTile para permitir eliminar apps nativas ancladas usando is_native).

## TC-03 (57e2f85): **APTO** [Claude 2026-07-18] 窶・condiciﾃｳn :762 y handler :830
verificados (filtro por id exacto), node OK, push OK.

## AUDITORﾃ喉 T-19 (92daa86): **APTO** [Claude 2026-07-18]
Verificaciﾃｳn independiente: heredocs extraﾃｭdos con awk -> bash -n OK ambos; gate
`$1 = "remove"` presente 2 veces (system + user); ruta del user unit COINCIDE con
install.sh (~/.config/systemd/user/); daemon-reload + enable + restart por existencia 笨・

## RELEASE v1.7.4 窶・**GO de Claude [2026-07-18]**: verificado en vivo (sha 5552715...
match, HEAD==origin). El dueﾃｱo puede actualizar por botﾃｳn (+recovery 1 comando).

## 笞 HALLAZGO DEL DUEﾃ前 [2026-07-18]: PWAs instaladas no reciben fixes -> T-21 [ALTO]
sw.js:1 = 'lrp-v16' congelado desde v1.6 (confirmado por Claude). Assets cache-first
jamﾃ｡s se refrescan sin bump -> PWA con HTML nuevo + CSS viejo. Ademﾃ｡s iOS hornea las
metas (status-bar-style) AL INSTALAR -> T-16 requiere REINSTALAR la PWA en el telﾃｩfono.
Fix T-21 (placeholder __LRP_VERSION__ + sed en build + guard) y T-22 (release v1.7.5
de cierre) en PLAN_GEMINI_v1.7.1.md. El "no pidiﾃｳ certificado": excepciﾃｳn por origen
guardada en Safari 窶・benigno.

## 笨・H3 COMPLETADO [2026-07-19] 窶・botﾃｳn 1.7.3->1.7.4 SIN intervenciﾃｳn
Encontrﾃｳ la actualizaciﾃｳn, aplicﾃｳ, servicio sobreviviﾃｳ, reconectﾃｳ solo, muestra 1.7.4.
Mecanismo probable del "milagro": el postinst nuevo reescribiﾃｳ lrp-update EN PLENA
ejecuciﾃｳn y bash (lectura perezosa) ejecutﾃｳ el tramo final con la lﾃｳgica T-19 nueva.
Confirmaciﾃｳn bajo condiciones 100% limpias: update 1.7.4 -> 1.7.5 (llega con T-21).
PWA 1.7.4 reinstalada por el dueﾃｱo: sin diferencia visual = esperado (T-20 no tocﾃｳ
frontend; los fixes visuales ya estaban en su instalaciﾃｳn fresca de 1.7.3).

## PRﾃ店IMO PASO
1. GEMINI: T-21 (versionado automﾃ｡tico del cache del SW). STOP -> auditorﾃｭa.
2. CLAUDE: APTO -> autorizar T-22 (release v1.7.5 窶・cierre del ciclo).
3. DUEﾃ前: re-smoke pendiente con la PWA fresca: frﾃｭo vs relanzado idﾃｩnticos en ambos
   iPhones; teclado abierto (ﾂｿlayout OK?); iconos de marca; ﾃ・en nativas; VOZ.
   Con 1.7.5: botﾃｳn de nuevo (confirmaciﾃｳn limpia) y el testing queda CERRADO.

## APPCORE RE-SINCRONIZADO [Claude 2026-07-18] 窶・skill `reindex` ejecutada
APPCORE.md reescrito contra el repo real (estaba congelado en v1.5: decﾃｭa Chromium,
sin adblock_status/mode/is_native/systemd-run). Verificado con grep: 22 endpoints con
sus gates, protocolo WS actual (pointer back, RTT), archivos crﾃｭticos v1.7.3.
La skill quedﾃｳ redefinida como `reindex` (.agents/skills/manage_context/SKILL.md).

## H3 PARCIAL [2026-07-18] 窶・cgroup fix 笨・ restart final 笨・-> T-19 [CRﾃ控ICO]
Botﾃｳn funcionﾃｳ, unit transitoria sobreviviﾃｳ, dpkg completﾃｳ (ii 1.7.3) 窶・T-14 validado.
FALLO NUEVO (journal): prerm hace stop+DISABLE sin distinguir upgrade de remove ->
el gate `is-enabled` de lrp-update salta el restart -> rama --user -> "not found" ->
servicio muerto+disabled. Fix T-19 en PLAN_GEMINI_v1.7.1.md (prerm con $1 +
restart por existencia con enable). Recovery del dueﾃｱo:
`sudo systemctl enable --now linuxremoteplayer`. Release v1.7.4 tras APTO (T-20).
OJO: 1.7.3->1.7.4 vﾃｭa botﾃｳn dejarﾃ｡ el servicio caﾃｭdo otra vez (updater instalado =
el de 1.7.3); recovery 1 comando; ciclo 100% limpio se valida en 1.7.4->1.7.5.

## PRﾃ店IMO PASO (histﾃｳrico) 窶・DUEﾃ前: la prueba de H3
1. Ajustes -> Buscar actualizaciﾃｳn -> "Actualizar a v1.7.3" -> el servicio debe
   sobrevivir (systemd-run), reconectar solo y mostrar 1.7.3. H3 笨・= testing cerrado.
   Si falla: cat /tmp/lrp-update.log + journalctl -u lrp-update-job + status del servicio.
2. Re-smoke: frﾃｭo vs relanzado idﾃｩnticos (ambos iPhones); teclado abierto (ﾂｿlayout
   aceptable? 窶・nota visualViewport); iconos de marca de vuelta; ﾃ・en nativas
   ancladas; VOZ (pendiente desde T-13).
3. Despuﾃｩs: commit+push de .agents (APPCORE/SKILL/planes sin trackear) y decidir
   siguiente frente: ai-proxy (v1.9, desbloquea venta) recomendado.

## AUDITORﾃ喉 T-14 [Claude 2026-07-18] 窶・**APTO**
- T-14 (de50b03): re-exec systemd-run al TOPE del lrp-update embebido, guard
  LRP_DETACHED + command -v, redirect de log tras el exec, set -e despuﾃｩs (orden
  correcto). Restart final presente (system + user). Verificaciﾃｳn INDEPENDIENTE de
  Claude: heredoc extraﾃｭdo con awk -> bash -n OK.
- Notas no bloqueantes: (a) doble-tap del botﾃｳn Actualizar -> el segundo systemd-run
  falla por unit activa = benigno (previene apt concurrente); (b) --collect
  garbage-colecta units fallidas.

## PRﾃ店IMO PASO 窶・RELEASE v1.7.2 **AUTORIZADO por Claude [2026-07-18]**
1. GEMINI: procedimiento estﾃ｡ndar (clon fresco WSL, .deb+sha256 REAL, borrar 1.7.1
   de downloads, latest.json 1.7.2, commit + push, verificaciﾃｳn EN VIVO con salidas).
2. CLAUDE: verificaciﾃｳn en vivo independiente -> GO.
3. DUEﾃ前: actualizar 1.7.1 -> 1.7.2 con `sudo lrp-update` MANUAL desde terminal del
   HTPC (el updater instalado aﾃｺn es el buggy 窶・huevo-gallina). El BOTﾃ哲 (H3) se
   valida reciﾃｩn en la actualizaciﾃｳn 1.7.2 -> siguiente release.
   Pendientes de smoke v1.7.1: visual completo (border-box en todas las pantallas,
   tooltip, nav-mode, HUD latencia, favicons, icono iOS, voz T-13). Luego J1/J2.

## AUDITORﾃ喉 BACHE T-01..T-13 [Claude 2026-07-17]
Verificaciﾃｳn independiente: node --check OK; check_css_sync exit 0; bash -n ﾃ・4 OK;
PNG apple-touch-icon = 180x180 real (header leﾃｭdo por Claude); endpoint /api/icon/{id}
del frontend COINCIDE con la ruta del backend (main.py:488); push verificado.
- T-01 (dfe45ce) **APTO** 窶・policies ANTES de certutil 笨・ pwfile + </dev/null en ambas
  llamadas 笨・ warning y continuaciﾃｳn 笨・ Nota menor: el fallback del panel aﾃｺn invoca
  chromium (inofensivo, no estﾃ｡ instalado) 窶・cosmﾃｩtico para otro dﾃｭa.
- T-02 (8a55f7e) APTO 窶・mensaje PIN-first correcto, un enlace token como alternativa.
- T-03 (9e34ead) **CORRECCIﾃ哲 TC-01** 窶・`exec` mata el fallback si lrp-setup falta
  (bash no-interactivo muere en exec fallido). Revertir a llamada directa.
- T-04 (402c917) APTO. - T-07 (679a69c) APTO*. - T-08 (916f31f) APTO*.
- T-05 (0bc1470) APTO CON NOTA 窶・aﾃｱadiﾃｳ `box-sizing: border-box` GLOBAL: es el reset
  que siempre faltﾃｳ en tailwind-lite (explica varios overflows histﾃｳricos) PERO mueve
  el modelo de caja de TODA la app -> validar visualmente todas las pantallas en el
  smoke. Media query max-height:750px razonable.
- T-06 (0d873a2) APTO CON PROCESO 窶・lﾃｳgica OK; el commit BARRIﾃ・backend/.env.example
  (cambios del workspace de Claude, no suyos). Estado final correcto (modelo 8B de
  producciﾃｳn). Regla reforzada: `git add` selectivo, jamﾃ｡s `git add -A` en tareas.
- T-09 (93f108a) APTO 窶・endpoint verificado contra backend.
- T-10 (89efd39) **CORRECCIﾃ哲 TC-02** 窶・commit vacﾃｭo: PNG ya era 180x180 笨・pero NO
  aﾃｱadiﾃｳ sizes= ni el link en pair.html que pedﾃｭa la spec.
- T-13 (791ae40) **APTO** 窶・carrera resuelta (micHeld post-await + tracks.stop),
  failsafe 8s, overlay, cancel <250ms. Nota: cancelar arrastrando fuera no dispararﾃ｡
  en touch (implicit pointer capture) 窶・cubierto por <250ms + failsafe, aceptable.
(* = validaciﾃｳn visual pendiente en dispositivo, smoke de v1.7.1)

## AUDITORﾃ喉 TC-01/TC-02 [Claude 2026-07-17] 窶・APTO
- TC-01 (98f986a): exec retirado, fallback intacto; bash -n OK (verificado por Claude).
- TC-02 (4874dd8): sizes="180x180" en index.html y pair.html 笨・ Commits selectivos 笨・

## 笞 H3 FALLﾃ・[2026-07-18] 窶・OTA vﾃｭa botﾃｳn deja el servicio caﾃｭdo
Causa raﾃｭz (Claude, confirmada en build_deb.sh + logs del dueﾃｱo): el updater corre
DENTRO del cgroup del servicio; el prerm del .deb detiene el servicio -> systemd mata
el cgroup completo -> dpkg muere a mitad. -> **T-14 [CRﾃ控ICO]** en PLAN_GEMINI_v1.7.1.md
(re-exec vﾃｭa systemd-run como unit transitoria). Release v1.7.2 tras T-14.
Recuperaciﾃｳn del HTPC ejecutada por el dueﾃｱo: dpkg --configure -a + reinstalar deb +
restart. OJO: 1.7.1->1.7.2 se actualiza MANUAL (updater instalado sigue buggy);
el botﾃｳn se re-valida en 1.7.2 -> siguiente.

## PRﾃ店IMO PASO 窶・T-12 RELEASE v1.7.1 **AUTORIZADO por Claude [2026-07-17]** (EJECUTADO)
1. GEMINI: procedimiento estﾃ｡ndar de release (clon fresco WSL, .deb+sha256 REAL a
   website/downloads/ borrando 1.7.0, latest.json, commit [T-12] + push, verificaciﾃｳn
   EN VIVO con salidas pegadas). NO romper el flujo OTA: el dueﾃｱo instalarﾃ｡ esta
   versiﾃｳn CON EL BOTﾃ哲 Actualizar de la app.
2. CLAUDE: verificaciﾃｳn en vivo independiente -> GO.
3. DUEﾃ前: Ajustes -> Buscar actualizaciﾃｳn -> Actualizar (ﾂ｡prueba H3 real!) + smoke
   visual: layout iPhone 8 Plus en TODAS las pantallas (border-box global), tooltip,
   nav-mode, latencia HUD, favicons, icono iOS, voz (toque corto no graba, pastilla
   se apaga sola, tope 8s). Luego J1/J2 (desinstalaciﾃｳn) cuando quiera.

## BITﾃ，ORA BACHE T-01..T-13 (Gemini)
- **T-01 a T-06**: Completados en sesiﾃｳn previa.
- **T-07**: Nav-mode rediseﾃｱado (flechas absolutas al borde y texto temporal opaco). `node --check frontend/app.js` OK (sin salida/errores).
- **T-08**: Indicador de latencia (RTT) calculado en `app.js` e insertado junto a 'Connected' con colores de Tailwind (`text-green-500`, etc). `node --check frontend/app.js` OK.
- **T-09**: Favicons corrigidos. Apps de sistema usan `/api/icon/`. Custom apps usan chain DDG -> Google S2 -> Div generado con inicial de la URL. `node --check frontend/app.js` OK.
- **T-10**: `apple-touch-icon.png` verificado mediante Python/PIL. Ya se encontraba opaco y a resoluciﾃｳn (180x180). Se generﾃｳ commit vacﾃｭo de confirmaciﾃｳn.
- **T-13**: Aﾃｱadida variable `micHeld`, validaciﾃｳn post-getUserMedia y failsafe de 8s. Aﾃｱadido `mic-overlay` a `index.html` con contador. Evento `pointerleave` aﾃｱadido. Clases sincronizadas en CSS. `node --check frontend/app.js` OK, `python scripts/check_css_sync.py` OK.
- **TC-01**: Eliminado `exec` de la llamada a `lrp-setup` en `website/install.sh` para restaurar el fallback `sudo lrp-setup`. `bash -n website/install.sh` OK.
- **TC-02**: Etiqueta `<link rel="apple-touch-icon">` actualizada con `sizes="180x180"` en `index.html` y `pair.html`.
## LIMPIEZA 2026-07-17 (esta sesiﾃｳn)
- TESTING.md de raﾃｭz ELIMINADO (obsoleto: Chromium, install por git clone). Sustituido
  por .agents/TESTING.md. README actualizado (2 referencias).
- Archivados en .agents/archive/: PLAN_GEMINI_v1.6.md, PLAN_GEMINI_v1.7.md,
  AUDIT_G07_G13_Report.md. CURRENT.md compactado (histﾃｳrico en git).
- AGENTS.md: registrados TESTING.md, archive/ y el cambio de modelo.

## HALLAZGOS GEMINI
(Gemini: anota aquﾃｭ lo que encuentres fuera del alcance de tu tarea. NO lo arregles.)

## 笞 ENTORNO 窶・regla permanente
El mount de bash (/mnt) TRUNCA archivos grandes (app.js real ~1400 lﾃｭneas). Leer/editar/
auditar SOLO con herramientas del harness; builds .deb SOLO en WSL con clon fresco.
py_compile/node --check sobre la ruta real (Windows) es vﾃ｡lido. Aplica tambiﾃｩn a Gemini:
verificar `wc -l` vs lo que su herramienta lee antes de editar archivos grandes.

## CHECKLIST DEL DUEﾃ前 (pendiente)
- [ ] Ejecutar matriz de testing (.agents/TESTING.md) y traer RESULTADOS.
- [ ] `supabase functions deploy send-feedback --no-verify-jwt` (sin confirmar desde v1.5).
- [ ] Commit+push de esta limpieza (.agents reorganizado + TESTING.md raﾃｭz eliminado).

## PENDIENTES GRANDES ANTES DE VENDER
- [ ] ai-proxy Edge Function (claves fuera del dispositivo). Bloquea venta de voz;
      prerrequisito del APK v2.0 (FASE E en archive/PLAN_GEMINI_v1.6.md; PH15 en PLAN.md).
- [ ] Stripe modo LIVE + dominio propio + verificaciﾃｳn de dominio en Resend.
- [ ] Deuda conocida teclado: < > (KEY_102ND) y corchetes AltGr en es/latam.

## HISTORIAL DE FASES (resumen)
- F1-8 MVP+seguridad; C1-C6 comercializaciﾃｳn; F9 emparejamiento PIN; F10 (v1.4) pulido;
  F11 (v1.5) Cozy Media; F12 (v1.6) bugs HTPC+hardening; F13 (v1.7) Firefox.
- F14 (actual): testing intensivo v1.7.0 -> correcciones -> luego ai-proxy / APK v2.0.
