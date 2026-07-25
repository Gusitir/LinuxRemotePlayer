# CURRENT — estado vivo
<!-- Formato: AGENTS.md §FORMATO. IDs (B/N/D/H/C) son anclas estables: citalos, no copies el texto. -->

```yaml
version_publicada:   1.8.0
version_construida:  1.8.9    # AUDITADA APTO, commit cefe4d5, SIN PUBLICAR
donde_vive:          clon WSL ~/lrp-release (fuera de este repo, invisible al leer git)
fase_activa:         v1.9 -> PLAN_v1.9.md   # tareas T-46..T-59
repo:                publico; se privatiza en T-57
licencia:            Elastic 2.0
ultima_sesion:       2026-07-24
pruebas_device:      TESTING.md (matriz ciclo 1.8.9; 9 items ⛔)
historia:            CONTEXT.md + git log
```

## B — BLOQUEANTES (rotos AHORA, en produccion)

- **B1 · correo de soporte rebota.** La web LIVE publica `soporte@linuxremoteplayer.com`
  en 16 sitios (index/docs/changelog, ES+EN) y **el dominio no esta comprado**. Se cierra
  con C2. Si C2 se demora, revertir a un correo que exista.
  Aparte `website/gracias.html:226` quedo con el correo viejo (se rehace en T-51).
- **B2 · `apt remove` incumple la doc.** El `prerm` del .deb SOLO para+deshabilita el
  servicio. NO libera licencia, NO borra regla UFW 8000/tcp, NO borra
  `/etc/udev/rules.d/99-uinput.rules`, NO desenmascara `sleep.target`. Las 4 SI estan en
  `scripts/uninstall.sh`, que `apt remove` nunca ejecuta y que ni va dentro del .deb.
  `website/docs.html` (ES+EN) manda a `sudo apt remove` y promete las 4.
  *Efecto:* el que desinstala sigue ocupando su slot de dispositivo.
  *Fix candidato:* empaquetar uninstall.sh y llamarlo desde el prerm; un fallo suyo
  JAMAS debe bloquear el `apt remove`. Verificacion en TESTING §E.
- **B3 · voz muerta en lo publicado.** El 1.8.0 que esta en la web llama a Together
  directo con llaves revocadas en T-50 → instalacion nueva = voz rota. **Publicar 1.8.9
  es lo que vuelve vendible la voz.** Se cierra con N1.

## N — SIGUIENTE (orden estricto)

1. **N1 · push de 1.8.9. LOS DOS CLONES DIVERGIERON** (ambos cuelgan de `107a8ce`):
   WSL tiene el release `cefe4d5`; Windows tiene los commits de docs. Orden obligatorio:
   `cd ~/lrp-release && git push origin main` → luego en Windows
   `git pull --rebase origin main && git push origin main` → verificar que `latest.json`
   sirve 1.8.9 con sha `890211c8…bf87c`. Desbloquea TODA la matriz de TESTING.
2. **N2 · el dueño ejecuta TESTING.md** (empezar por los ⛔).
3. **N3 · T-52 dominio** (bloqueado por C2). En Vercel: **mantener viva la URL
   `vercel.app` o redirigir** — las PWA 1.8.x leen `latest.json` ahi; matarla mata el OTA
   de todo lo instalado.
4. **N4** → T-51 Paddle (alta, producto $5, webhook, compra real + refund) → T-55 docs
   (absorbe T-43/T-44) → T-56 release v1.9.0 → T-57 privatizar.

## HECHO (fase v1.9)

- **T-46..T-50** ai-proxy + anti-abuso + licencia 1-dispositivo. Validado E2E en device
  2026-07-22 pero **sobre un build de prueba, no sobre un .deb publicado** → revalidar
  en TESTING §C/§D. El device ya no tiene llaves de IA.
- **T-50b, T-53a..d** sitio ES+EN completo y LIVE (landing/docs/changelog, 3 temas,
  instalacion 1-comando por .deb → T-54 casi resuelta, pricing, Ko-fi, voz bilingue).
  Falta de T-53: video demo y `gracias.html`. Placeholders: PADDLE / KOFI / VIDEO.
- **T-58** identidad app↔web (commit `ae27a31`). Detalle tecnico: APPCORE §skins.css.
- **T-59** release 1.8.9 **AUDITADO APTO**: sha `890211c8…bf87c` con cuadruple match
  (latest.json == .deb == .sha256 == copia en downloads); contenido del .deb identico
  archivo por archivo al arbol del commit; app.js 1574 lineas; sw.js `lrp-1.8.9`;
  `data-skin="day"`; `scripts/dev` no empaquetado; el commit toca exactamente 6 archivos.

## D — DECISIONES VIGENTES (no re-litigar)

- **D1 · pagos: PADDLE.** Stripe no opera para vendedores en Ecuador. PayPal plan B.
  Donaciones por Ko-fi. Validacion = compra real $5 + refund. Paddle REVISA el sitio
  antes de aprobar → por eso web y dominio van ANTES del alta.
- **D2 · nombre comercial: LinuxRemotePlayer** (rebrand cancelado); "LRP" marca corta.
- **D3 · precio:** Pro unico $5 lifetime al lanzar. Suscripcion recien con Voz 2.0.
- **D4 · skins: las 7 planeadas van GRATIS**, son el gancho; el Pro se vendera con skins
  ADICIONALES en v2.0. Roster: Day (default), Night, Cafe, Cozy (**renombrar** desde
  `anime`), Cyberpunk, Gato y Perro (etiqueta "Accesibilidad", botonera recortada).
  Spec completa, set de botones y criticas: **PLAN.md §PH17** (v1.9.1).
  Mockups: `.agents/design/skins2/`. Falta del dueño: wallpapers (ver C3).
- **D5 · Voz 2.0 repriorizada a v2.0** (PLAN.md §PH19). Meta: que "pon video de gatos"
  REPRODUZCA, no que se quede en la busqueda. Orden 1→2→3: keymaps por sitio primero;
  control del DOM (WebDriver BiDi, el equivalente Firefox de las DevTools) al final, con
  la nota de seguridad del puerto de depuracion.

## H — HALLAZGOS ABIERTOS (no bloquean)

- **H1** cold-start de voz: 1er comando tras inactividad tarda segundos (Edge Function
  dormida + Whisper frio). Mitigacion: keep-alive. Medir en TESTING C3 antes de decidir.
- **H2** Whisper alucina con silencio → texto fantasma → accion rara. No es regresion.
  Arreglo barato: descartar audios <~1s antes de facturar.
- **H3** OTA no es transparente: actualiza al cerrar/reabrir la PWA, no sola. Aceptado.
- **H4** falta intent "volumen al maximo" (hoy sube 1 paso).
- **H5** `showInstallScreen` usa `appUI.hidden=true` pero `#app-ui` tiene `.flex` (el autor
  gana al `[hidden]` del UA); `showPairingScreen` lo esquiva con `style.display`. Unificar.
- **H6** `bootstrap.sh` (instala por git-clone) es legacy y muere con el repo privado (T-54).
- **H7** CSS muerto en `tailwind-lite.css`: utilidades cyan/fuchsia de los swatches viejos
  (~12 lineas), sin uso desde T-58. El guard no lo caza (solo detecta usada-sin-definir).
- **H8** backlog visual: el header dice "Remote Linux Player" (orden invertido); "Okular"
  duplicado en apps detectadas.

## C — CHECKLIST DEL DUEÑO (operativo; lo del device esta en TESTING.md)

- [ ] **C1** push de 1.8.9 (= N1).
- [ ] **C2** comprar dominio + correo empresarial. Desbloquea N3 y cierra B1.
- [ ] **C3** wallpapers definitivos de las skins nuevas. Para Gato/Perro mandar **el TILE**
      (~400x400), no el pantallazo: son patrones sin costura y tilear ya esta soportado
      (`--bg-repeat`/`--bg-size`). Un tile pesa ~30KB vs ~170KB del full-screen.
- [ ] **C4** redeployar ai-proxy con el prompt bilingue si no se hizo (T-53d). Se verifica
      en TESTING C2 y es ⛔ porque **la web ya vende la voz en ingles**.
- [ ] **C5** screenshots nuevas del sitio: las actuales muestran la skin anime, que ya no
      es el look por defecto (T-56).
- [ ] **C6** `supabase functions deploy send-feedback --no-verify-jwt` (pendiente desde v1.5).
- [ ] **C7** privatizar el repo al lanzar (T-57).
