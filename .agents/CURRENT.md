# ESTADO ACTUAL (compactado 2026-07-20 al cierre de sesión; histórico en git + archive/)

VERSION publicada: **1.7.8** (LIVE en Vercel 2026-07-20; sha f89fcd19...2ac53f
triple-match latest.json==.deb==.sha256, sw.js=lrp-1.7.8, app.js 1522 líneas no
truncado — auditado por Claude vía wsl al clon nativo). Repo PRIVADO. Elastic 2.0.
Modelos (2026-07-20): **Gemini 3.5 Flash** ejecuta (chat fresco, brief completo por
tarea); Claude (**Opus 4.8**) planifica/audita. Se agotó Fable5.
HTPC del dueño: v1.7.5 instalada, PWA fresca 1.7.5. Voz CONFIGURADA en su .env
(stack validado: STT openai/whisper-large-v3 + LLM Qwen/Qwen2.5-7B-Instruct-Turbo
en Together; llaves solo en el .env del HTPC y del PC dev — gitignored, verificado).

## CICLO v1.7.8 — cerrado en código + publicado; falta PRUEBA OTA del dueño
Validación 1.7.7 del dueño (2026-07-20): 2/4 OK. Voz funciona; Dolphin+apps sistema OK.
Fallo real: card "Comandos de voz" NO aparecía → causa raíz: `.hidden{...!important}`
vencía al inline `style.display` (app.js:183). Fix T-30 = `classList.toggle('hidden',...)`
(commit b46cafd, auditado APTO). T-31 = Release v1.7.8 (commit a0b568b, auditado APTO,
LIVE). Detalle del ciclo en PLAN_GEMINI_v1.7.8.md.
- OTA 1.7.5→1.7.7 requería reinstalar = ESPERADO (1.7.5 shipeó antes del auto-reload).
- **ÚNICO PENDIENTE: el dueño abre la PWA (1.7.7) SIN reinstalar y confirma:**
  (a) auto-recarga sola a 1.7.8, (b) card "Comandos de voz" visible en Ajustes.
  ✅ ambos → OTA VERIFICADO end-to-end + TESTING INTENSIVO CERRADO → arrancar v1.9.
  ❌ no auto-recarga → problema REAL de OTA (no esperado) → triar causa raíz.

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

## HALLAZGOS / FUTURO (fuera de alcance, sin código aún)
- Voz: falta intent "volumen al máximo" (hoy sube 1 paso). Meter al ampliar comandos
  avanzados por app. NO es bug, es feature pendiente (reportado por el dueño 2026-07-20).
- Latente baja prioridad (no reportado, flujo real anda): showInstallScreen usa
  `appUI.hidden = true` pero #app-ui tiene clase `.flex` (autor) que gana al UA `[hidden]`;
  showPairingScreen lo esquiva con `style.display`. Revisar si algún día no oculta la app UI.

## CHECKLIST DEL DUEÑO (fuera de código)
- [x] Validación 1.7.7 reportada (2/4 OK) -> fixes en 1.7.8 (LIVE).
- [ ] **PRUEBA OTA:** abrir PWA (1.7.7) SIN reinstalar -> confirmar auto-reload a 1.7.8
      + card de voz visible -> reportar a Claude (cierra testing intensivo).
- [ ] `supabase functions deploy send-feedback --no-verify-jwt` (pendiente desde v1.5).
- [x] Basura temporal borrada (test.sh, scratch/, .agents/logs_temp/) — 2026-07-20.
- [ ] Commit de .agents (CURRENT + PLAN_GEMINI_v1.7.8) — repo limpio salvo estos .md.
