# CURRENT — estado vivo
<!-- Formato: AGENTS.md §FORMATO. IDs (B/N/D/H/C) son anclas estables: citalos, no copies el texto.
     Compactado 2026-07-27 (12.8KB -> techo 8KB): el detalle de cada auditoria esta en git log. -->

```yaml
version_publicada:   1.8.9    # LIVE desde 2026-07-26 (T-60). sha 890211c8…bf87c
dominio:             https://www.linuxremoteplayer.com  # comprado y sirviendo desde Vercel
alias_vercel:        linux-remote-player.vercel.app     # VIVO a proposito: es el canal OTA
correo_soporte:      support@linuxremoteplayer.com      # el viejo soporte@ NO existia
fase_activa:         v1.9 -> PLAN_v1.9.md   # tareas T-46..T-63
repo:                publico; se privatiza en T-57
licencia:            Elastic 2.0
ultima_sesion:       2026-07-27
pruebas_device:      TESTING.md (matriz ciclo 1.8.9; DESBLOQUEADA por T-60)
docs_humanos:        docs/ARCHITECTURE.md (la forma) + docs/DEVELOPING.md (como trabajar)
historia:            CONTEXT.md + git log
```

## B — BLOQUEANTES (rotos AHORA, en produccion)

- **B1b · `website/gracias.html:226` publica el gmail PERSONAL del dueño**
  (`aeciminer02@gmail.com`), no un correo de empresa. La pagina de "gracias por comprar" es
  de las que MIRA un procesador de pagos: un gmail personal ahi resta credibilidad en la
  revision de Paddle. Se rehace en T-51. (B1 original — el `soporte@` que rebotaba — cerrada
  en T-61.)
- **B2 · `apt remove` incumple la doc.** El `prerm` del .deb SOLO para+deshabilita el
  servicio. NO libera licencia, NO borra regla UFW 8000/tcp, NO borra
  `/etc/udev/rules.d/99-uinput.rules`, NO desenmascara `sleep.target`. Las 4 SI estan en
  `scripts/uninstall.sh`, que `apt remove` nunca ejecuta y que ni va dentro del .deb.
  `website/docs.html` (ES+EN) manda a `sudo apt remove` y promete las 4.
  *Efecto:* el que desinstala sigue ocupando su slot de dispositivo.
  *Fix candidato:* empaquetar uninstall.sh y llamarlo desde el prerm; un fallo suyo
  JAMAS debe bloquear el `apt remove`. Verificacion en TESTING §E.

## N — SIGUIENTE (orden estricto)

1. **N1 · el dueño ejecuta TESTING.md** (empezar por los ⛔). Nada lo bloquea.
2. **N2 · corregir la web AL PUBLICAR v1.9.0, no antes** (parte de T-56). La web vende los
   temas como Pro y T-62 ya los libero en el codigo: hasta que el `.deb` nuevo este
   publicado, cambiarlas haria mentir a la web al reves para todo el que tenga 1.8.9.
   Lineas: `website/index.html:148,254,299` + `website/en/index.html:148,256,301`.
3. **N3 · migrar las URLs de maquina al dominio propio, DENTRO del release v1.9.0** (para
   que el cambio de canal OTA viaje en un `.deb` auditado, no en un hotfix del sitio).
   T-61 cambio solo lo que ve un humano; siguen en `vercel.app` a proposito:
   `website/latest.json` (deb_url), `website/install.sh` (MANIFEST_URL),
   `backend/main.py:416` (buy_url) y `:555` (UPDATE_MANIFEST_URL),
   `scripts/build_deb.sh:122`, `frontend/app.js:61,249,1255`, `README.md`.
   **Regla que no cambia: el alias `vercel.app` NO se apaga nunca** — las PWA 1.8.x leen
   `latest.json` ahi y matarlo mata el OTA de todo lo ya instalado.
4. **N4** → T-51 Paddle (alta, producto $5, webhook, compra real + refund; arrastra B1b y
   H11) → T-55 docs (absorbe T-43/T-44) → T-56 release v1.9.0 → T-57 privatizar.

## HECHO (fase v1.9 — detalle de cada auditoria en git log)

- **T-46..T-50** ai-proxy + anti-abuso + licencia 1-dispositivo. Validado E2E en device
  2026-07-22 pero **sobre un build de prueba, no sobre un .deb publicado** → revalidar
  en TESTING §C/§D. El device ya no tiene llaves de IA.
- **T-50b, T-53a..d** sitio ES+EN completo y LIVE. Falta de T-53: video demo y
  `gracias.html`. Placeholders vivos: PADDLE / KOFI / VIDEO.
- **T-58** identidad app↔web (`ae27a31`). Detalle tecnico: APPCORE §skins.css.
- **T-59 + T-60** release 1.8.9 construido, auditado y PUBLICADO. sha
  `890211c8d65742d81415356195c8601c42316a6d8f53710c51780e2d072bf87c` con cuadruple match
  (latest.json == .deb == .sha256 == copia en downloads), identico en el dominio y en el
  alias vercel, y el .deb servido pesa exactamente lo que el blob del commit (309912 B).
- **T-61** (`014269f`) dominio propio + `support@` en la web. Solo `website/`.
- **T-62** (`4c52165`) **skins liberadas** — implementa D4. `setSkin()` ya no consulta
  `isLicensed`; `FREE_SKIN` → `DEFAULT_SKIN`; `dark`/`neon` resueltos en `LEGACY_SKINS`;
  candados `.pro-lock`, `<symbol id="ico-lock">` y etiquetas `(Pro)` eliminados.
  La VOZ sigue siendo Pro (`isLicensed` sobrevive en 4 puntos, a proposito).
  **Todavia NO llega al device: necesita el release v1.9.0.**
- **T-63** (`03581cc`) **doc de FastAPI oculta** — cierra H9. Verificado en RUNTIME (no por
  inspeccion): `/docs`, `/redoc`, `/openapi.json` y `/docs/oauth2-redirect` no existen sin
  `LRP_DEV`, y aparecen con `true`/`TRUE`. **Se uso `LRP_DEV` y NO `LRP_MODE`** porque
  `LRP_MODE=desktop` es un modo de usuario final real, no de desarrollo, y su default
  (`appliance`) habria apagado la doc tambien en la PC del desarrollador.

## D — DECISIONES VIGENTES (no re-litigar)

- **D1 · pagos: PADDLE.** Stripe no opera para vendedores en Ecuador. PayPal plan B.
  Donaciones por Ko-fi. Validacion = compra real $5 + refund. Paddle REVISA el sitio
  antes de aprobar → por eso web y dominio van ANTES del alta.
- **D2 · nombre comercial: LinuxRemotePlayer** (rebrand cancelado); "LRP" marca corta.
- **D3 · precio:** Pro unico $5 lifetime al lanzar. Suscripcion recien con Voz 2.0.
- **D4 · skins: las 7 planeadas van GRATIS**, son el gancho; el Pro se vendera con skins
  ADICIONALES en v2.0. Roster: Day (default), Night, Cafe, Cozy (**renombrar** desde
  `anime`), Cyberpunk, Gato y Perro (etiqueta "Accesibilidad", botonera recortada).
  Spec, set de botones y criticas: **PLAN.md §PH17** (v1.9.1). Mockups:
  `.agents/design/skins2/`. Falta del dueño: wallpapers (C3).
  **Codigo: las 4 primeras ya existen y ya estan libres (T-62); las otras 3 son PH17.**
- **D5 · Voz 2.0 repriorizada a v2.0** (PLAN.md §PH19). Meta: que "pon video de gatos"
  REPRODUZCA, no que se quede en la busqueda. Orden 1→2→3: keymaps por sitio primero;
  control del DOM (WebDriver BiDi, el equivalente Firefox de las DevTools) al final, con
  la nota de seguridad del puerto de depuracion.
- **D6 · demo interactiva en la web** (2026-07-26): minijuego con control simulado + "TV"
  que reacciona, con las 4 skins. Spec: **PLAN.md §PH20** (v1.9.1). Dos reglas que NO se
  negocian: etiqueta de SIMULACION visible, y CERO red (un endpoint de IA abierto desde el
  sitio publico seria gratis para cualquiera). Va despues de PH17 o en la misma tanda, o
  hereda la deuda de los layouts nuevos. **No bloquea Paddle** (esa va con capturas, C5).
- **D7 · `Techlm77/LinuxPlay` NO es competencia: es otra categoria** (GPL-2.0, 622 estrellas,
  ultimo push 2025-11-10 → dormido; revisado 2026-07-26). Ellos hacen streaming de
  escritorio (FFmpeg + UDP → cliente Qt en otra PC); LRP no transmite video, la TV ya ES la
  pantalla. Se tocan solo en inyectar input y en el handshake por PIN.
  - **NO se rebrandea** (D2 sigue, el dominio ya esta comprado). La colision de nombre es
    real —ellos tienen SEO, nosotros nos privatizamos— y se mitiga apoyandose en el dominio
    propio y en "LRP", y hablando del problema del sillon/HTPC, no de "remote player".
  - **Diferenciador factual para la web:** su README avisa que NO cifra el trafico y manda a
    tunelizar por WireGuard/SSH; LRP hace HTTPS con CA propia + PIN desde el minuto uno.
    Decirlo SIN nombrarlos (comparar de frente es ruido legal inutil).
  - Su codigo NO entra acá ni en el contexto de ningun agente: **AGENTS.md §CODIGO DE
    TERCEROS**. Unico dato aprovechable de su README: usan UDP y no TCP para input y
    gamepad → tenerlo en cuenta al medir latencia en PH18.

## H — HALLAZGOS ABIERTOS (no bloquean)

- **H11** `backend/.env.example:20` trae `BUY_URL=https://buy.stripe.com/test_5kQ3...`:
  Stripe en modo TEST cuando los pagos ya son Paddle (D1). Ese archivo es la plantilla del
  `.env` real → el boton "comprar" de un device instalado apunta a un checkout de prueba de
  una pasarela que no se va a usar. Se arregla en T-51, con la URL definitiva.
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
- Cerradas: **H9** (T-63), **H10** (docs/DEVELOPING.md).

## C — CHECKLIST DEL DUEÑO (operativo; lo del device esta en TESTING.md)

- [x] **C1** push de 1.8.9 (T-60). · [x] **C2** dominio + `support@` publicados (T-61).
- [ ] **C8** mandarte un correo de prueba a `support@linuxremoteplayer.com` y confirmar que
      LLEGA. La web ya lo publica en 14 lugares: si el buzon no existe, B1 sigue viva
      disfrazada. Un minuto, y es prerrequisito de Paddle.
- [ ] **C3** wallpapers definitivos de las skins nuevas. Para Gato/Perro mandar **el TILE**
      (~400x400), no el pantallazo: son patrones sin costura y tilear ya esta soportado
      (`--bg-repeat`/`--bg-size`). Un tile pesa ~30KB vs ~170KB del full-screen.
- [ ] **C4** redeployar ai-proxy con el prompt bilingue si no se hizo (T-53d). Se verifica
      en TESTING C2 y es ⛔ porque **la web ya vende la voz en ingles**.
- [ ] **C5** screenshots nuevas del sitio: las actuales muestran la skin anime, que ya no
      es el look por defecto (T-56).
- [ ] **C6** `supabase functions deploy send-feedback --no-verify-jwt` (pendiente desde v1.5).
- [ ] **C7** privatizar el repo al lanzar (T-57).
