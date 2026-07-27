# CURRENT — estado vivo
<!-- Formato: AGENTS.md §FORMATO. IDs (B/N/D/H/C) son anclas estables: citalos, no copies el texto. -->

```yaml
version_publicada:   1.8.9    # LIVE desde 2026-07-26 (T-60). sha 890211c8…bf87c
dominio:             https://www.linuxremoteplayer.com  # comprado y sirviendo desde Vercel
alias_vercel:        linux-remote-player.vercel.app     # VIVO a proposito: es el canal OTA
correo_soporte:      support@linuxremoteplayer.com      # el viejo soporte@ NO existia
fase_activa:         v1.9 -> PLAN_v1.9.md   # tareas T-46..T-61
repo:                publico; se privatiza en T-57
licencia:            Elastic 2.0
ultima_sesion:       2026-07-26
pruebas_device:      TESTING.md (matriz ciclo 1.8.9; DESBLOQUEADA por T-60)
docs_humanos:        docs/ARCHITECTURE.md (la forma) + docs/DEVELOPING.md (como trabajar)
historia:            CONTEXT.md + git log
```

## B — BLOQUEANTES (rotos AHORA, en produccion)

- ~~**B1 · correo de soporte rebota.**~~ **CERRADA en T-61** (2026-07-26): dominio comprado
  y las 14 ocurrencias de `soporte@` en `website/` pasaron a `support@`. Verificado en vivo.
  **Queda el resto B1b:** `website/gracias.html:226` publica el gmail PERSONAL del dueño
  (`aeciminer02@gmail.com`), no un correo de empresa. La pagina de "gracias por comprar" es
  de las que MIRA un procesador de pagos — un gmail personal ahi resta credibilidad en la
  revision de Paddle. Se rehace en T-51.
- **B2 · `apt remove` incumple la doc.** El `prerm` del .deb SOLO para+deshabilita el
  servicio. NO libera licencia, NO borra regla UFW 8000/tcp, NO borra
  `/etc/udev/rules.d/99-uinput.rules`, NO desenmascara `sleep.target`. Las 4 SI estan en
  `scripts/uninstall.sh`, que `apt remove` nunca ejecuta y que ni va dentro del .deb.
  `website/docs.html` (ES+EN) manda a `sudo apt remove` y promete las 4.
  *Efecto:* el que desinstala sigue ocupando su slot de dispositivo.
  *Fix candidato:* empaquetar uninstall.sh y llamarlo desde el prerm; un fallo suyo
  JAMAS debe bloquear el `apt remove`. Verificacion en TESTING §E.
- ~~**B3 · voz muerta en lo publicado.**~~ **CERRADA en T-60** (2026-07-26): 1.8.9 esta LIVE,
  las instalaciones nuevas van por ai-proxy. La voz vuelve a ser vendible.

## N — SIGUIENTE (orden estricto)

1. **N1 · el dueño ejecuta TESTING.md** (empezar por los ⛔). Ya no hay nada que lo bloquee.
2. **N2 · T-62 liberar las skins** (implementa D4). Hoy `app.js` §setSkin gatea todo lo que
   no sea `day` tras `isLicensed` → el dueño en su propio device solo ve `day`. Va DENTRO
   del release v1.9.0 (T-56), no en un release aparte: decidido 2026-07-26.
3. **N3 · T-63 ocultar la doc de FastAPI** (implementa H9). Va antes de T-56.
4. **N4 · migrar las URLs de maquina al dominio propio.** T-61 cambio solo lo que ve un
   humano. Siguen en `vercel.app` a proposito: `website/latest.json` (deb_url),
   `website/install.sh` (MANIFEST_URL), `backend/main.py:416` (buy_url) y `:555`
   (UPDATE_MANIFEST_URL), `scripts/build_deb.sh:122`, `frontend/app.js:61,249,1255`,
   `README.md`. **Se migran DENTRO del release v1.9.0** para que el cambio de canal OTA
   viaje en un `.deb` auditado, no en un hotfix del sitio.
   **Regla que no cambia: el alias `vercel.app` NO se apaga nunca** — las PWA 1.8.x leen
   `latest.json` ahi y matarlo mata el OTA de todo lo ya instalado.
5. **N5** → T-51 Paddle (alta, producto $5, webhook, compra real + refund) → T-55 docs
   (absorbe T-43/T-44) → T-56 release v1.9.0 → T-57 privatizar.

## HECHO (fase v1.9)

- **T-46..T-50** ai-proxy + anti-abuso + licencia 1-dispositivo. Validado E2E en device
  2026-07-22 pero **sobre un build de prueba, no sobre un .deb publicado** → revalidar
  en TESTING §C/§D. El device ya no tiene llaves de IA.
- **T-50b, T-53a..d** sitio ES+EN completo y LIVE (landing/docs/changelog, 3 temas,
  instalacion 1-comando por .deb → T-54 casi resuelta, pricing, Ko-fi, voz bilingue).
  Falta de T-53: video demo y `gracias.html`. Placeholders: PADDLE / KOFI / VIDEO.
- **T-58** identidad app↔web (commit `ae27a31`). Detalle tecnico: APPCORE §skins.css.
- **T-60** push del release **AUDITADO APTO** (2026-07-26). Los dos clones divergidos
  reunidos en `origin/main`; `cefe4d5` es ancestro; HEAD `50acd92` tras el rebase (0
  conflictos). Verificado EN VIVO: `latest.json` = 1.8.9 con sha
  `890211c8d65742d81415356195c8601c42316a6d8f53710c51780e2d072bf87c` **identico en el
  dominio y en el alias vercel**, y el `.deb` responde 200 con 309912 bytes = exactamente
  el tamaño del blob del commit.
- **T-61** dominio + correo en la web **AUDITADO APTO** (2026-07-26, commit `014269f`,
  6 archivos, todos bajo `website/`). 0 ocurrencias de `soporte@` en `website/`; las 14 de
  `support@` con el reparto exacto esperado; `vercel.app` sobrevive SOLO en `latest.json` e
  `install.sh` (las dos exclusiones pedidas) y el commit no toca ninguno de los dos.
  Verificado que `copyCommand()` lee `#cmd-text.textContent` → no hay URL duplicada en el
  JS de copiar, lo copiado siempre coincide con lo mostrado.
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
  **Estado del codigo (verificado 2026-07-26):** las 4 primeras YA EXISTEN en
  `frontend/skins.css`, pero `app.js` §setSkin todavia las gatea tras `isLicensed` — o sea
  D4 esta DECIDIDA pero NO implementada. Liberarla = tarea T-62, dentro de v1.9.0 (N2).
- **D6 · demo interactiva en la web** (pedido 2026-07-26): minijuego con control simulado +
  "TV" que reacciona, corriendo con las 4 skins. Spec: **PLAN.md §PH20** (v1.9.1). Dos
  reglas que NO se negocian: va etiquetada como SIMULACION visible, y NO hace red (un
  endpoint de IA abierto desde el sitio publico seria gratis para cualquiera). Va DESPUES
  de PH17 o en la misma tanda, o hereda la deuda de los layouts nuevos.
  **No bloquea la revision de Paddle**: esa se hace con capturas de la skin Day (C5).
- **D5 · Voz 2.0 repriorizada a v2.0** (PLAN.md §PH19). Meta: que "pon video de gatos"
  REPRODUZCA, no que se quede en la busqueda. Orden 1→2→3: keymaps por sitio primero;
  control del DOM (WebDriver BiDi, el equivalente Firefox de las DevTools) al final, con
  la nota de seguridad del puerto de depuracion.

## H — HALLAZGOS ABIERTOS (no bloquean)

- **H9 · la doc automatica de FastAPI esta expuesta.** `backend/main.py:34` crea
  `FastAPI(title=...)` sin pasar `docs_url=None` / `redoc_url=None` / `openapi_url=None`,
  asi que `/docs`, `/redoc` y `/openapi.json` responden **sin gate** a cualquiera en la LAN.
  Los endpoints en si siguen protegidos (no es una brecha), pero enumera toda la superficie
  de la API y un revisor de seguridad lo va a marcar en un producto de pago.
  **DECIDIDO (dueño, 2026-07-24): OCULTARLA.** Razon: expone el mapa completo de la API en
  la LAN y eso es puerta libre para clonar el producto. Fix: pasar `docs_url=None`,
  `redoc_url=None`, `openapi_url=None` cuando `LRP_MODE=appliance`, y dejarla activa en dev
  (donde sigue siendo la referencia de endpoints para un colaborador, ver docs/DEVELOPING §6).
  Tarea pendiente, va antes de T-56.
- **H10 · falta guia de extension** ("como se modifica"): como agregar un intent de voz, una
  app soportada o un layout de teclado; convenciones; como probar un cambio. Es la seccion
  mas consultada de la doc de cualquier proyecto grande. El protocolo WS —el contrato mas
  importante del producto— solo vive comprimido en APPCORE, que esta escrito para agentes.
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

- [x] **C1** push de 1.8.9 — HECHO 2026-07-26 (T-60, auditado APTO).
- [x] **C2** dominio `linuxremoteplayer.com` comprado + `support@` publicado (T-61).
      Falta solo confirmar que el buzon RECIBE de verdad (ver C8).
- [ ] **C8** mandarte un correo de prueba a `support@linuxremoteplayer.com` y confirmar que
      llega. El sitio ya lo publica en 14 lugares: si el buzon no existe todavia, seguimos
      con B1 pero disfrazada. Es un minuto y es prerrequisito de Paddle.
- [ ] **C3** wallpapers definitivos de las skins nuevas. Para Gato/Perro mandar **el TILE**
      (~400x400), no el pantallazo: son patrones sin costura y tilear ya esta soportado
      (`--bg-repeat`/`--bg-size`). Un tile pesa ~30KB vs ~170KB del full-screen.
- [ ] **C4** redeployar ai-proxy con el prompt bilingue si no se hizo (T-53d). Se verifica
      en TESTING C2 y es ⛔ porque **la web ya vende la voz en ingles**.
- [ ] **C5** screenshots nuevas del sitio: las actuales muestran la skin anime, que ya no
      es el look por defecto (T-56).
- [ ] **C6** `supabase functions deploy send-feedback --no-verify-jwt` (pendiente desde v1.5).
- [ ] **C7** privatizar el repo al lanzar (T-57).
