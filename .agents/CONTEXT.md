INIT: 2026-06-24
Project started. Repo initialized.
Target: Local Linux PC controlled by mobile PWA via WS. Heavy AI offloaded to cloud. No local inference.
Current objective: Scaffolding Phase 1.

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
