# ESTADO ACTUAL (2026-07-20)

VERSION publicada: **1.7.8** (LIVE en Vercel; sha f89fcd19...2ac53f triple-match,
sw.js=lrp-1.7.8, app.js 1522 líneas no truncado — auditado). Repo **PÚBLICO** (se
privatiza en v1.9). Licencia Elastic 2.0. Flujo/roles: ver AGENTS.md.
Voz producción validada: Together (whisper-large-v3 + Qwen2.5-7B). Llaves solo en el
.env del HTPC y del PC dev (gitignored; T-32 confirmó 0 filtraciones en el historial).

## v1.7.8 — ACEPTADO por el dueño como "completamente funcional y vendible" (2026-07-20)
Bug del card de voz corregido (T-30) y publicado (T-31). El dueño validó en device: voz,
apps de sistema (Dolphin), y card de voz OK. **OTA:** no auto-recarga sola mientras la app
está abierta, pero al CERRAR/REABRIR la PWA ya toma la actualización → el dueño lo dio por
SUFICIENTE. (Hacer el auto-reload realmente transparente = candidato v1.9; ver HALLAZGOS.)
Testing intensivo: cerrado a satisfacción del dueño.

## FASE ACTIVA: v1.8 — LIMPIEZA/OPTIMIZACIÓN pre-lanzamiento (plan en PLAN_v1.8.md)
Objetivo: dejar todo limpio/profesional antes de v1.9. Termina con release v1.8.0 +
regresión en device. Progreso:
- **HECHAS y auditadas APTO:** T-32 auditoría secretos (0 filtraciones, 145 commits);
  T-33 purga IA legacy (solo cloud Together; fuera local/mock/defaults NVIDIA); T-34
  eliminar pair.html (muerto); T-35 scripts one-shot → scripts/dev/ + .deb más magro;
  T-36 borrar docs/archive; T-37 limpieza backend (pyflakes: imports/vars muertos,
  behavior-neutral). Commits c1975ac, c1e2795, df5079b, 1a41d3e, 61d5126 (pusheados).
- **T-38 frontend = no-op** (0 console.log; ya limpio). **T-39 (partir main.py) = DIFERIDO a v1.9**
  (opcional, riesgoso pre-lanzamiento). → LIMPIEZA DE CÓDIGO CERRADA.
- **T-43/T-44 = EN CURSO:** reestructura .agents (WORKFLOW.md + README índice; consolidar).
- **T-40 README raíz + T-41 website = HECHAS** (factual: stack IA→Together, layout real,
  Firefox no Chromium, precio $5, email fuera de comentarios; screenshots SIGUEN pendientes).
  Commits 4320a73, 7397f99.
- **PENDIENTE:** T-42 licencias + T-45 Release v1.8.0 (CHANGELOG, build WSL nativo, latest.json,
  OTA) — al final, ejecuta Gemini + audita Claude + regresión device del dueño.

## PRÓXIMO MILESTONE: v1.9 — LANZAMIENTO (especificado en PLAN.md)
ai-proxy Edge Function (llaves fuera del device) + PH-ANTIABUSO (cap 512KB, kill-switch,
cuota, métricas) + PH-LICENCIAS (1 dispositivo + rotación por correo) + Stripe LIVE +
dominio propio + rebrand + PH-WEB (rediseño, capturas, video, precio $5) + privatizar repo.
PH-PRICING: Pro único $5 al lanzar; suscripción recién con Voz 2.0. Roadmap post-lanzamiento:
multi-distro (Arch/Fedora/etc.) + Skins 2.0 → APK → Archivos → Gamepad → Voz 2.0 (PLAN.md).

## HALLAZGOS / FUTURO (fuera de alcance de v1.8)
- **OTA auto-reload no es transparente:** hoy actualiza al cerrar/reabrir la PWA, no sola
  mientras está abierta. Aceptado como suficiente para vender; hacerlo seamless = v1.9.
- Voz: falta intent "volumen al máximo" (hoy sube 1 paso). Va al ampliar comandos avanzados.
- Latente baja prio: showInstallScreen usa `appUI.hidden=true` pero #app-ui tiene `.flex`
  (autor gana al UA `[hidden]`); showPairingScreen lo esquiva con `style.display`. Revisar.
- bootstrap.sh (instalador por git-clone) posible legacy; se rompería con repo privado (v1.9).
- **Email de soporte web = aeciminer02@gmail.com** (era placeholder; user-facing en index.html:870/887
  y gracias.html:226/7). Confirmar o reemplazar por el real ANTES de vender.
- **Precio:** la web ya muestra $5 USD (T-41) pero el link Stripe sigue TEST (9.99 EUR). v1.9:
  crear producto $5 USD en Stripe LIVE + cambiar el link en index.html.
- **Cuota voz:** web dice 60/día; app.js dice "100 cmds/día". Unificar app a 60 (quick fix o v1.9).

## CHECKLIST DEL DUEÑO (fuera de código)
- [ ] **Screenshots reales** del device (app en TV + control en teléfono) → para README/website (T-40/T-41).
- [ ] `supabase functions deploy send-feedback --no-verify-jwt` (pendiente desde v1.5).
- [ ] (v1.9) Privatizar el repo en el lanzamiento.
- [x] Validación 1.7.8 en device: aceptada como vendible (2026-07-20).
