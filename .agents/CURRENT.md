# ESTADO ACTUAL (2026-07-24, cierre de sesión)

VERSION publicada: **1.8.0**. **1.8.9 construida y AUDITADA APTO, commiteada en el clon
WSL (`~/lrp-release`, commit `cefe4d5`) y SIN PUSHEAR** → primera acción de la próxima
sesión. Repo **PÚBLICO** (se privatiza en T-57). Licencia Elastic 2.0. Flujo/roles: AGENTS.md.
Historia de v1.7.x/v1.8 y de cada sesión: CONTEXT.md + git.

## ⚠️ ROMPIMIENTO EN VIVO — ARREGLAR PRIMERO
La web publicada anuncia **`soporte@linuxremoteplayer.com`** en 16 lugares (index, docs,
changelog, ES y EN) pero **el dominio todavía NO está comprado** → todo correo de soporte
REBOTA hoy. Se resuelve solo cuando el dueño compre el dominio (próxima sesión, T-52); si
se demora, revertir a un correo que exista. Aparte, `website/gracias.html:226` quedó con
el correo viejo `aeciminer02@gmail.com` (se rehace en T-51 con el flujo Paddle).

## FASE ACTIVA: v1.9 — LANZAMIENTO (plan maestro: PLAN_v1.9.md)
ai-proxy + anti-abuso + licencia 1-dispositivo + Paddle $5 + dominio + web + release +
privatizar. Tareas T-46..T-59.
- **BLOQUES A+B CERRADOS** (T-46..T-50, validados E2E en device 2026-07-22): ai-proxy
  deployado, backend sin llaves de IA (las viejas de Together REVOCADAS), cuota 60,
  mudanza de licencia con takeover, kill-switch. **Consecuencia: el 1.8.0 publicado tiene
  la voz MUERTA para instalaciones nuevas** — por eso urge publicar 1.8.9.
- **T-50b, T-53a..d HECHAS y LIVE**: rediseño total del sitio ES+EN (landing/docs/
  changelog), 3 temas con selector, instalación 1-comando por .deb (NO git → T-54 casi
  resuelta), capturas reales, pricing, donaciones Ko-fi placeholder, voz bilingüe.
  Pendientes de T-53: video demo y `gracias.html`. Placeholders: PADDLE / KOFI / VIDEO.
- **T-58 HECHA** (2026-07-24, commit `ae27a31`): identidad app↔web unificada. Detalle
  técnico en APPCORE (skins.css) y en PLAN.md/PH17.
- **T-59 Release 1.8.9 AUDITADA APTO** (2026-07-24): sha256 `890211c8…bf87c` con
  cuádruple match (latest.json == .deb == .sha256 == copia en downloads); el contenido del
  .deb coincide archivo por archivo con el árbol del commit; app.js 1574 líneas íntegro;
  sw.js `lrp-1.8.9`; `data-skin="day"`; `scripts/dev` NO empaquetado; el commit toca
  exactamente 6 archivos. **Falta: push + validación en device.**

## PRÓXIMOS PASOS (en orden)
1. **Push de T-59 — OJO, los dos clones DIVERGIERON.** Ambos cuelgan de `107a8ce`: el
   clon WSL tiene `cefe4d5` (el release) y el repo Windows tiene 3 commits de docs
   (`6676d80`, `3ed50ae`, `34011b3`). El orden importa:
   a. Primero WSL:  `cd ~/lrp-release && git push origin main`
   b. Después Windows: `git pull --rebase origin main` y recién ahí `git push origin main`
   c. Verificar que Vercel deployó y que `latest.json` sirve 1.8.9 con el sha `890211c8…`
   Después el dueño prueba el OTA 1.8.0→1.8.9 en device.
2. **Validación device de T-58**: el `apple-mobile-web-app-status-bar-style` pasó de
   `black-translucent` a `default` → **mirar el notch en iPhone en standalone**. Es el
   único cambio de T-58 que no pude verificar sin hardware.
3. **T-52 dominio** (el dueño lo trae): dominio en Vercel + `soporte@` real + Resend.
   OJO: mantener viva la URL `vercel.app` o redirigir — las PWA 1.8.x leen `latest.json` ahí.
4. T-51 Paddle (alta, producto $5, webhook, compra real + refund) → T-55 docs →
   T-56 release v1.9.0 → T-57 privatizar.

## DECISIONES VIGENTES
- **Pagos: PADDLE** (Stripe no opera para vendedores en Ecuador). PayPal plan B.
  Donaciones por Ko-fi. Validación = compra real $5 + refund.
- **Nombre comercial: LinuxRemotePlayer** (rebrand cancelado), "LRP" como marca corta.
- **Precio:** Pro único $5 lifetime al lanzar; suscripción recién con Voz 2.0.
- **Skins (2026-07-24):** las 7 planeadas van GRATIS y son el gancho; el Pro se venderá
  con skins ADICIONALES en v2.0. Roster: Day (default), Night, Cafe, Cozy (renombrar
  desde `anime`), Cyberpunk, Gato y Perro (etiqueta "Accesibilidad", botonera recortada).
  Especificación completa + set de botones + críticas: **PH17 en PLAN.md** (v1.9.1).
  Mockups en `.agents/design/skins2/`. **Pendiente del dueño: los wallpapers definitivos**
  (para Gato/Perro mandar el TILE, no el pantallazo — son patrones sin costura).
- **Voz 2.0 repriorizada a v2.0** (PH19): meta = que "pon video de gatos" REPRODUZCA en
  vez de quedarse en la búsqueda. Orden 1→2→3: keymaps por sitio primero; el control del
  DOM (WebDriver BiDi, el equivalente Firefox de las DevTools) al final y con la nota de
  seguridad del puerto de depuración.

## HALLAZGOS ABIERTOS (no bloquean)
- **Cold-start de voz:** tras inactividad el 1er comando tarda segundos (Edge Function
  dormida + Whisper frío). Mitigación: keep-alive. Evaluar con datos reales post-lanzamiento.
- **Whisper alucina con silencio:** mic apretado sin hablar → texto fantasma → acción rara.
  No es regresión. Arreglo barato: descartar audios <~1s antes de facturar.
- **OTA no es transparente:** actualiza al cerrar/reabrir la PWA, no sola. Aceptado.
- Voz: falta intent "volumen al máximo" (hoy sube 1 paso).
- Latente baja prio: `showInstallScreen` usa `appUI.hidden=true` pero `#app-ui` tiene
  `.flex` (el autor gana al `[hidden]` del UA); `showPairingScreen` lo esquiva con
  `style.display`. Unificar.
- `bootstrap.sh` (instalador por git-clone) es legacy y muere con el repo privado (T-54).
- CSS muerto en `tailwind-lite.css`: utilidades cyan/fuchsia de los swatches de skin
  viejos (~12 líneas), sin uso desde T-58.
- Backlog app: el header dice "Remote Linux Player" (orden invertido); "Okular" duplicado
  en apps detectadas; verificar en T-56 que `apt remove` libere la licencia.
- T-43/T-44 (reestructura .agents) siguen absorbidas en T-55.

## CHECKLIST DEL DUEÑO (fuera de código)
- [ ] **Push de 1.8.9** (paso 1 de arriba) y probar el OTA en device.
- [ ] **Notch en iPhone** tras el cambio de status-bar (T-58).
- [ ] **Comprar el dominio** + correo empresarial (desbloquea T-52 y el rebote de soporte).
- [ ] **Wallpapers definitivos** de las skins nuevas (tiles para Gato/Perro).
- [ ] Confirmar que el ai-proxy quedó redeployado con el prompt bilingüe (T-53d) y probar
      un comando en inglés.
- [ ] Screenshots del sitio: siguen mostrando la skin anime, ya no el look por defecto (T-56).
- [ ] `supabase functions deploy send-feedback --no-verify-jwt` (pendiente desde v1.5).
- [ ] Privatizar el repo al lanzar (T-57).
