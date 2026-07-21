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
FALTA v1.8: T-40 README raiz + T-41 website (factual; screenshots PENDIENTES del dueño),
T-42 licencias + T-45 Release v1.8.0 (build WSL + latest.json + OTA + regresion device).
Ejecuta Gemini 3.5 Flash, audita Claude. Flujo completo en AGENTS.md.

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
