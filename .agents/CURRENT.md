# ESTADO ACTUAL (2026-07-22, cierre de sesión)

VERSION publicada: **1.8.0** (LIVE en Vercel; sha 2be02de9...0508 triple-match,
sw.js=lrp-1.8.0, app.js 1522 líneas no truncado — auditado y VALIDADO en device).
Repo **PÚBLICO** (se privatiza en v1.9). Licencia Elastic 2.0. Flujo/roles: ver AGENTS.md.
Voz producción validada: Together (whisper-large-v3 + Qwen2.5-7B). Llaves solo en el
.env del HTPC y del PC dev (gitignored; T-32 confirmó 0 filtraciones en el historial).

## v1.7.8 — ACEPTADO por el dueño como "completamente funcional y vendible" (2026-07-20)
Bug del card de voz corregido (T-30) y publicado (T-31). El dueño validó en device: voz,
apps de sistema (Dolphin), y card de voz OK. **OTA:** no auto-recarga sola mientras la app
está abierta, pero al CERRAR/REABRIR la PWA ya toma la actualización → el dueño lo dio por
SUFICIENTE. (Hacer el auto-reload realmente transparente = candidato v1.9; ver HALLAZGOS.)
Testing intensivo: cerrado a satisfacción del dueño.

## FASE v1.8 — CERRADA (2026-07-20): limpieza/optimización pre-lanzamiento (plan en PLAN_v1.8.md)
Release v1.8.0 auditado, LIVE y VALIDADO en device por el dueño. App "100% lista y profesional".
SIGUIENTE: v1.9 (lanzamiento, abajo). Resumen de lo hecho:
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
- **T-45 Release v1.8.0 = HECHO** (commit 9884440; .deb 281KB más magro; sha 2be02de9...0508
  triple-match; pusheado, Vercel LIVE, regresión device OK). FASE v1.8 CERRADA.
- Screenshots reales de README/web quedan PENDIENTES → v1.9 (con rebrand PH-WEB).

## FASE ACTIVA: v1.9 — LANZAMIENTO (plan maestro: PLAN_v1.9.md, arrancada 2026-07-21)
ai-proxy Edge Function (llaves fuera del device) + PH-ANTIABUSO (cap 512KB, kill-switch,
cuota por plan, métricas) + PH-LICENCIAS (1 dispositivo + mudanza; rotación manual
documentada) + **Paddle** LIVE $5 USD + dominio propio + rebrand + PH-WEB + matar
bootstrap.sh + release v1.9.0 + privatizar repo. Tareas T-46..T-57 (ver PLAN_v1.9.md).
**BLOQUES A+B CERRADOS (2026-07-22):** T-46 schema v3 aplicado ✓, T-47 ai-proxy
deployado + smoke 6/6 ✓, T-48 backend→proxy ✓, T-49 mudanza PWA + cuota 60 ✓,
T-50 E2E device VALIDADO (voz vía proxy, 1cmd=1consumo, takeover, kill-switch;
keys Together viejas REVOCADAS — el device ya no tiene llaves de IA).
Commits: 6fe6001, c9d3f52, ad615e9, ab7d794. Build de prueba 1.8.9 (no publicado).
**PAGOS (decidido 2026-07-21): Stripe NO opera en Ecuador → PADDLE** (MoR, Ecuador OK,
manual por dashboard, sin plugin, sin sandbox; validación = compra real $5 + refund).
PayPal plan B. Patreon/Creem descartados. Donaciones: sección "Apoyá el proyecto" en
la web (T-53) con Ko-fi como placeholder (+cripto opcional); rail de retiro se decide después.
**REBRAND CANCELADO (dueño, 2026-07-22): el nombre comercial ES LinuxRemotePlayer**
(descriptivo=SEO, equity acumulado), con "LRP" como marca corta (logo/favicon; ya vive
en las keys LRP-). T-52 queda solo dominio+email (linuxremoteplayer.com como opción
natural; compra pendiente — la tarjeta del dueño dio error en el registrador, lo arregla).
Ko-fi CONFIRMADO para donaciones (acumular en PayPal, retirar >$50 que es donde renta).
**T-50b HECHA** (fix cards items-start, 8d51ae6). **T-53 CASI COMPLETA y LIVE en Vercel**
(commits 3196fa3, eb01d18, a886ebb, 05edc7d — auditados APTO, dueño validó "perfecto"):
rediseño total ES+EN (landing/docs/changelog), 3 temas (claro DEFAULT/café/navy, selector
esquina + localStorage), instalación 1-comando (website/install.sh ya era .deb-based, NO
git — sobrevive repo privado = T-54 casi resuelta), capturas reales en phone-frames,
matriz compat honesta, pricing Free/Pro $5, donaciones Ko-fi placeholder, FAQ→docs,
hreflang. Voz BILINGÜE (prompt ai-proxy ES+EN, T-53d) — **dueño debía redeployar ai-proxy
en dashboard y probar comando en inglés: CONFIRMAR al retomar.**
Pendientes T-53: video demo (placeholder en hero listo), gracias.html (se rehace en T-51
con flujo Paddle). Placeholders marcados: PLACEHOLDER-PADDLE / -KOFI / -VIDEO.
**PRÓXIMA SESIÓN: el dueño viene con DOMINIO (linuxremoteplayer.com) + correo empresarial
→ T-52 (dominio en Vercel, email soporte ya escrito en la web, Resend; OJO: mantener URL
vercel.app viva o redirect — las PWA 1.8.0 leen latest.json ahí) → T-51 Paddle (alta,
producto $5, paddle-webhook, compra real + refund) → T-55 docs → T-56 release v1.9.0 →
T-57 privatizar.**
**T-58 HECHA (2026-07-24, sin publicar aún): identidad app↔web unificada.** Skins de la
app = las 3 del sitio: **day (clara) POR DEFECTO y única gratis**, night (navy) y cafe
(madera) Pro, anime Pro intacta. Ids viejos migran en `setSkin()` (free `dark`→`day` sin
toast; Pro `dark`/`neon`→`night`). Logo rehecho ("Touchpad") en icon.svg + 6 PNG (app y
web); `scripts/dev/generate_png_icons.py` reescrito y con su `ROOT_DIR` arreglado (roto
desde T-35). `skins.css` lleva un bloque PUENTE que reasigna las utilidades neutras de
tailwind-lite (`border-gray-700`, `text-gray-300`, …) a variables de skin — sin eso la
skin clara rompe el marcado histórico; clases neutras nuevas hay que puentearlas.
Auditoría de referencias encontró y corrigió: la web publicitaba "Temas (Pro): Dark, Day,
Neon" (ES+EN, index.html:148 y :254) → ahora Day incluido + Night/Café/Anime Pro.
OJO device: `apple-mobile-web-app-status-bar-style` pasó a `default` → probar notch en iPhone.
T-43/T-44 (reestructura .agents) quedaron colgadas de v1.8 → absorbidas en T-55.
Backlog app anotado: header PWA dice "Remote Linux Player" (orden invertido); "Okular"
duplicado en apps detectadas; verificar en T-56 que `apt remove` invoque el release de
licencia (la doc ya lo afirma).
PH-PRICING: Pro único $5 al lanzar; suscripción recién con Voz 2.0. Roadmap post-lanzamiento:
multi-distro (Arch/Fedora/etc.) + Skins 2.0 → APK → Archivos → Gamepad → Voz 2.0 (PLAN.md).

## HALLAZGOS v1.9 (anotados 2026-07-22, no bloquean lanzamiento)
- **Cold-start de voz:** tras inactividad, el 1er comando tarda varios segundos
  (Edge Function dormida + Whisper frío en Together); después vuela. Mitigación
  posible: keep-alive/warmer. Evaluar post-lanzamiento con datos reales.
- **Whisper alucina con silencio:** mic apretado sin hablar → texto fantasma →
  acción rara (busca/pausa). NO es regresión (pre-proxy igual). Mitigación barata:
  descartar audios <~1s (client o proxy) antes de facturar. Pulir en v1.9 si da el
  tiempo, si no post-lanzamiento.
- Smoke test T-47 registró 2 consumos donde se esperaba 1 → RESUELTO en T-50:
  contabilidad exacta en device real (6 mic = 6 usage_log = 6 commands_today);
  fue doble ejecución del curl S5.

## HALLAZGOS / FUTURO (fuera de alcance de v1.8)
- **OTA auto-reload no es transparente:** hoy actualiza al cerrar/reabrir la PWA, no sola
  mientras está abierta. Aceptado como suficiente para vender; hacerlo seamless = v1.9.
- Voz: falta intent "volumen al máximo" (hoy sube 1 paso). Va al ampliar comandos avanzados.
- Latente baja prio: showInstallScreen usa `appUI.hidden=true` pero #app-ui tiene `.flex`
  (autor gana al UA `[hidden]`); showPairingScreen lo esquiva con `style.display`. Revisar.
- bootstrap.sh (instalador por git-clone) posible legacy; se rompería con repo privado (v1.9).
- **Email de soporte web = aeciminer02@gmail.com** (correo secundario de TEST del dueño; queda
  funcionando; user-facing en index.html:870/887 y gracias.html:226/7). CAMBIAR a
  soporte@<dominio> al comprar el dominio (v1.9).
- **Precio:** la web ya muestra $5 USD (T-41) pero el link Stripe sigue TEST (9.99 EUR). v1.9:
  crear producto $5 USD en Stripe LIVE + cambiar el link en index.html.
- **Cuota voz:** web dice 60/día; app.js dice "100 cmds/día". Unificar app a 60 (quick fix o v1.9).

## CHECKLIST DEL DUEÑO (fuera de código)
- [ ] **Screenshots reales** del device (app en TV + control en teléfono) → para README/website (T-40/T-41).
- [ ] `supabase functions deploy send-feedback --no-verify-jwt` (pendiente desde v1.5).
- [ ] (v1.9) Privatizar el repo en el lanzamiento.
- [x] Validación 1.7.8 en device: aceptada como vendible (2026-07-20).
