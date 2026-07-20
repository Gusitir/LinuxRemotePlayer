# ESTADO ACTUAL (compactado 2026-07-20 al cierre de sesión; histórico en git + archive/)

VERSION publicada: **1.7.7** (verificada en vivo: sha 02b2c406...8c35b match doble,
sw.js del .deb = lrp-1.7.7). Repo PRIVADO. Licencia Elastic 2.0.
Modelos: Gemini 3.5 Pro ejecuta; Claude (Fable5 Alto) planifica/audita.
HTPC del dueño: v1.7.5 instalada, PWA fresca 1.7.5. Voz CONFIGURADA en su .env
(stack validado: STT openai/whisper-large-v3 + LLM Qwen/Qwen2.5-7B-Instruct-Turbo
en Together; llaves solo en el .env del HTPC y del PC dev — gitignored, verificado).

## ÚNICO PENDIENTE DEL CICLO v1.7.x — validación final del dueño
Botón 1.7.5 -> 1.7.7, cerrar/reabrir la PWA UNA vez (última manual; T-28 activa el
auto-reload en adelante), y 4 checks:
1. Voz: "Abre Netflix" / "Sube el volumen" / "Pausa" / "busca recetas de cocina"
2. Ajustes -> card "Comandos de voz" (apps dinámicas del catálogo)
3. Drawer -> Dolphin visible (detector abierto)
- TODO OK -> declarar TESTING INTENSIVO CERRADO (matriz completa en TESTING.md,
  H3 OK definitivo) y arrancar v1.9.
- ALGO FALLA -> triar con causa raíz -> nuevo PLAN_GEMINI_v1.7.8.md.

## CICLO v1.7.x CERRADO EN CÓDIGO (resumen; planes en .agents/archive/)
- v1.7.1..v1.7.7: 29 tareas + 6 correcciones, todas auditadas con verificación
  independiente. 8 releases verificadas en vivo (sha256 + extracción del .deb).
- Bugs de sistema exterminados: OTA cgroup-suicide (systemd-run), prerm que
  deshabilitaba en upgrade, gate is-enabled, certutil colgado (NSS password),
  viewport iOS no determinista, MediaRecorder webm en iOS, SW cache congelado
  (ahora auto-versionado por build + auto-reload en controllerchange).
- Voz end-to-end validada: audio iOS(mp4)->magic bytes->Whisper->Qwen->intent, con
  prompt dinámico (apps inyectadas de SUGGESTED_KIOSKS), defensa server-side
  (normalización target/key), errores con etapa, guía de comandos en la UI.

## PRÓXIMO MILESTONE: v1.9 — LANZAMIENTO (especificado en PLAN.md)
ai-proxy Edge Function (llaves fuera del dispositivo) + PH-ANTIABUSO (cap 512KB
server-side, kill-switch de gasto, cuota por plan, métricas) + PH-LICENCIAS
(1 dispositivo con takeover confirmado + rotación de key por correo) + Stripe LIVE +
dominio propio + rebrand + PH-WEB (rediseño, capturas, video, precio $5).
PH-PRICING: recomendación registrada = Pro único $5 al lanzar; suscripción recién
con Voz 2.0. Roadmap post-lanzamiento: Skins 2.0 -> APK -> Archivos -> Gamepad ->
Voz 2.0 (PH15-PH19 en PLAN.md).

## REGLAS OPERATIVAS VIGENTES (destilado; detalle en AGENTS.md)
- Un commit por tarea [T-NN]; git add SELECTIVO; evidencia = salida real PEGADA.
- Auditor: verificar contra COMMITS (git show), SOLO tras STOP explícito del
  ejecutor (falso NO APTO por carrera de edición ya ocurrió). Re-ejecutar checks
  siempre (3 veces el ejecutor reportó evidencia que no corrió).
- Releases: clon fresco WSL; sha256 real; verificación en vivo doble (ejecutor y
  auditor) incluyendo extraer el sw.js/archivos clave del .deb publicado.
- Guard CSS (scripts/check_css_sync.py) corre en cada cambio de frontend — ya cazó
  deriva real (T-29). py_compile/node --check sobre ruta Windows real OK; builds
  SOLO en WSL; mount /mnt trunca archivos grandes (leer con harness).
- DeepSeek (asistente en el HTPC): solo config/diagnóstico, jamás código; sus
  hotfix de emergencia se PORTAN a repo o el OTA los pisa.

## HALLAZGOS GEMINI
(vacío — anotar aquí lo fuera de alcance, sin código)

## CHECKLIST DEL DUEÑO (fuera de código)
- [ ] Validación final 1.7.7 (arriba) -> reportar a Claude.
- [ ] `supabase functions deploy send-feedback --no-verify-jwt` (pendiente desde v1.5).
- [x] Basura temporal borrada (test.sh, scratch/, .agents/logs_temp/) — 2026-07-20.
- [ ] Commit+push de este cierre de .agents (repo limpio salvo estos .md + .env.example).
