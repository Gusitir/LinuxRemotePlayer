SESSION: 2026-07-24 (Claude Opus 5 — identidad visual, release 1.8.9, spec de Skins 2.0)
T-58: skins de la app alineadas 1:1 con la paleta del sitio — day (clara) POR DEFECTO y
gratis, night, cafe, anime; ids viejos migran en setSkin() (free dark->day SIN toast, Pro
dark/neon->night). Logo rehecho ("Touchpad": pad de puntos en tinta sobre crema con play
verde), icon.svg + 6 PNG de app y web; scripts/dev/generate_png_icons.py reescrito (y su
ROOT_DIR arreglado, roto desde T-35). LECCIÓN TÉCNICA: el marcado histórico asume fondo
OSCURO, así que la skin clara lo rompía; se resolvió con un bloque PUENTE en skins.css que
reasigna las utilidades neutras de tailwind-lite a variables de skin — toda clase neutra
nueva hay que puentearla. La auditoría DE REFERENCIAS (no solo de comportamiento) encontró
que la web publicitaba los temas viejos "Dark, Day, Neon" en ES y EN: corregido. También
se cazó un riesgo propio: el <symbol> del candado bajo display:none rompe <use> en WebKit
(la PWA corre en Safari iOS) -> se oculta con position/overflow.
T-59 Release 1.8.9 (Gemini ejecutó, Claude auditó APTO contra el .deb REAL vía WSL):
cuádruple match de sha256, contenido del paquete idéntico al árbol del commit, app.js
1574 líneas, sw.js lrp-1.8.9. COMMITEADA EN EL CLON WSL Y SIN PUSHEAR — es lo primero de
la próxima sesión. Nota: el 1.8.0 publicado tiene la voz muerta para instalaciones nuevas
(las llaves de Together se revocaron en T-50), así que publicar 1.8.9 es lo que vuelve
vendible la voz.
DECISIONES DEL DUEÑO: las 7 skins planeadas van GRATIS como gancho (el Pro se venderá con
skins adicionales en v2.0); roster Day/Night/Cafe/Cozy(ex-anime)/Cyberpunk/Gato/Perro, con
etiqueta "Accesibilidad" en las dos últimas; Voz 2.0 repriorizada a v2.0. Dominio APLAZADO
a la próxima sesión.
HALLAZGO NUEVO (apareció al podar CURRENT): la web LIVE anuncia soporte@linuxremoteplayer.com
en 16 lugares y ese dominio todavía no está comprado -> los correos de soporte rebotan hoy.
PH17 (Theme Packs / Skins 2.0) especificada para v1.9.1 con los 4 mockups del dueño fijados
en .agents/design/skins2/. Lo importante: NO son paletas — cambian posición de botones, qué
botones existen y agregan etiquetas de texto que no están en el DOM. Diseño: atributo
data-layout independiente de data-skin, cada skin fijada a un layout para que la matriz de
QA quede en N. Críticas aceptadas por el dueño: el D-Pad se QUEDA en el layout accesible
(para quien no controla un puntero es más fácil que un cursor libre); "INICIO" se saca
porque es killKiosk() y mata la app en curso; el engranaje de Ajustes se queda (sin él el
usuario queda atrapado en el modo accesible); "Edgerunners" no se usa (marca de CD Projekt/
Trigger). CURRENT.md compactado 10.2KB -> ~5KB; APPCORE re-sincronizado (entrada de
skins.css + generador de iconos; status-bar ya no es black-translucent).

INIT: 2026-06-24
Project started. Repo initialized.
Target: Local Linux PC controlled by mobile PWA via WS. Heavy AI offloaded to cloud. No local inference.
Current objective: Scaffolding Phase 1.

SESSION: 2026-07-20 (Claude Opus 4.8 — cierre v1.7.8 + fase v1.8 limpieza)
v1.7.8 publicada y ACEPTADA por el dueño como "completamente funcional y vendible" (fix del
card de voz: T-30 classList.toggle vs .hidden !important; release T-31, auditado en vivo).
OTA: no auto-recarga sola, pero cerrar/reabrir la PWA actualiza -> el dueño lo dio por SUFICIENTE
(hacerlo seamless = candidato v1.9). Testing intensivo cerrado a satisfacción.
FASE v1.8 (limpieza pre-lanzamiento, plan en PLAN_v1.8.md), HECHO y pusheado a main:
T-32 auditoria de secretos (0 fugas en 145 commits), T-33 purga IA legacy (solo cloud Together;
fuera modo local/MOCK/defaults NVIDIA-OpenRouter), T-34 borrar pair.html (muerto), T-35 scripts
one-shot -> scripts/dev/ + .deb mas magro, T-36 borrar docs/archive, T-37 limpieza backend
(pyflakes: imports/vars muertos, behavior-neutral), T-43/T-44 reestructura .agents. T-38 no-op
(frontend ya limpio), T-39 (partir main.py) DIFERIDO a v1.9.
LECCION del dueño: NO borrar AGENTS.md (los agentes lo leen primero) ni CONTEXT.md (handoff);
el README a actualizar es el de la RAIZ (GitHub), no uno en .agents.
v1.8 COMPLETA (2026-07-20): T-40/T-41 (README+web factual: Firefox no Chromium, precio $5,
stack Together) + T-45 Release v1.8.0 hechos, auditados y LIVE (sha 2be02de9...0508;
.deb 281KB; validado en device por el dueño). FASE v1.8 CERRADA. Pendientes que van a v1.9:
screenshots reales README/web; email soporte -> soporte@<dominio>; app.js "100 cmds/dia" ->
60; Stripe LIVE producto $5 USD. SIGUIENTE: v1.9 (lanzamiento: ai-proxy con llaves fuera del
device, licencia 1-dispositivo + rotacion por correo, anti-abuso IA, Stripe LIVE, dominio,
rebrand PH-WEB, privatizar repo). Ejecuta Gemini, audita Claude. Ver AGENTS.md.

SESSION: 2026-07-17..20 (Claude — ciclo v1.7.1..v1.7.7 completo, cerrada por contexto)
Testing intensivo ejecutado y triado -> 29 tareas + 6 correcciones auditadas -> 8
releases verificadas en vivo. Sagas resueltas: OTA (cgroup/prerm/gate — H3 OK
DEFINITIVO con botón limpio), voz end-to-end (crash keys, webm/iOS, prompt dinámico,
search restaurada, guía de comandos en UI), PWA auto-actualizable (SW versionado por
build + controllerchange reload), viewport iOS determinista, detector de apps abierto.
Stack voz ratificado: whisper-large-v3 + Qwen2.5-7B-Turbo (Together).
DISEÑOS DECIDIDOS (en PLAN.md): licencia 1-dispositivo con takeover + rotación por
correo; anti-abuso IA (cap 512KB, kill-switch gasto, cuota por plan); pricing (Pro
único $5 al lanzar, sub recién con Voz 2.0); PH19 Voz 2.0 (misma app, intents
modulares, keymaps por sitio); PH-WEB rediseño.
INCIDENTES DE PROCESO con lección: falso NO APTO por auditar working tree en edición
(-> auditar commits tras STOP); 3x evidencia afirmada sin correr (-> pegar salidas);
guard CSS cazó su primera deriva real. Skill global agents-workflow (~/.claude/skills)
creada + contrato de archivos + regla 11.
ESTADO AL CIERRE: v1.7.7 publicada con GO; falta SOLO la validación final del dueño
(4 checks de voz + card + Dolphin) para cerrar el testing. Plan v1.7.1 archivado;
CURRENT compactado 20KB->4KB. Siguiente: v1.9 (ai-proxy+licencias+Stripe+web).

SESSION: 2026-07-17 (Claude — reanudación, limpieza y testing intensivo)
v1.7.0 (Firefox) publicada y verificada en vivo el 07-14; smoke-test formal pendiente.
CAMBIO DE MODELO (nota del dueño): el auditor Claude pasó de "Fable5 Supercode" a
"Fable5 Alto". Disciplina intacta: toda afirmación con salida real de comando.
LIMPIEZA .md: TESTING.md de raíz ELIMINADO (obsoleto: Chromium/git-clone); nuevo plan
intensivo en .agents/TESTING.md (matriz A-J). Planes cerrados movidos a .agents/archive/
(PLAN_GEMINI_v1.6, PLAN_GEMINI_v1.7, AUDIT_G07_G13_Report). README actualizado.
PRÓXIMO: dueño ejecuta la matriz; fallas -> plan v1.7.1/v1.8.
PENDIENTES GRANDES: ai-proxy (bloquea venta de voz, prerrequisito APK v2.0),
Stripe LIVE + dominio + Resend, deploy send-feedback, G-15/G-16 (via matriz F1/F2).

SESSION: 2026-07-13 (Claude — análisis/planificación)
Verificado contra repo: B1/B3 del AUDIT_v1.5 cerrados en git (165cf4b, e0865f1); C2 (main.py:352)
y C3 (app.js:61,226) persisten; .deb 1.4.0 aún rastreado en website/downloads/; deploy de
send-feedback sin confirmar. Creado .agents/PLAN_GEMINI_v1.5.1.md (Gemini programa, Claude
planifica y audita; tareas T1-T5 con criterios de aceptación). PLAN.md: +PH14. CURRENT.md
reescrito con estado verificado. Próximo: reporte de bugs del testing v1.5.0 en HTPC manda.
