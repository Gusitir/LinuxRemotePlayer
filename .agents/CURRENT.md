# CURRENT — estado vivo
<!-- Formato: AGENTS.md §FORMATO. IDs (B/N/D/H/C) son anclas: citalos, no copies el texto.
     Tamaño ~11KB, POR ENCIMA del techo de 8KB. Se compacto a 8.9KB el 2026-07-27 y volvio a
     crecer el mismo dia al reabrirse B1 y entrar H12 — que son bloqueantes vivos y no se
     podan. El espacio se recupera CERRANDO items (B1, B2, H11, H12), no borrando el porque.
     El detalle de cada auditoria esta en git log, no aca. -->

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

- **B1 · REABIERTA 2026-07-27: `support@linuxremoteplayer.com` NO recibe.** T-61 arreglo el
  string en la web (14 lugares) pero el buzon no existe: la prueba de C8 rebota con
  `554 5.7.1 Relay access denied`. **El DNS esta bien** — MX a `eforward1..5.
  registrar-servers.com` (reenvio gratuito de Namecheap) + SPF puesto. El 554 de ESOS
  servidores significa que el alias `support` no esta dado de alta en el panel: comprar el
  dominio no crea buzones. *Fix inmediato:* Namecheap → Domain List → Manage → Redirect
  Email → alias `support` → destino gmail.
  **Ojo, eso NO alcanza para vender:** el reenvio de Namecheap es SOLO de recepcion, y las
  respuestas saldrian desde el gmail personal — el mismo problema de credibilidad que B1b.
  Antes de cerrar T-51 hace falta un buzon que pueda ENVIAR como support@ (Namecheap Private
  Email ~$10-14/año sin tocar DNS, o Zoho gratis cambiando los MX).
- **B1b · `website/gracias.html:226` publica el gmail PERSONAL del dueño**
  (`aeciminer02@gmail.com`). La pagina de "gracias por comprar" es de las que MIRA un
  procesador de pagos: un gmail personal ahi resta credibilidad. Se rehace en T-51.
- **B2 · `apt remove` incumple la doc.** El `prerm` del .deb SOLO para+deshabilita el
  servicio. NO libera licencia, NO borra la regla UFW 8000/tcp, NO borra
  `/etc/udev/rules.d/99-uinput.rules`, NO desenmascara `sleep.target` — las 4 SI estan en
  `scripts/uninstall.sh`, que `apt remove` nunca ejecuta y que ni siquiera va dentro del
  .deb, mientras `website/docs.html` (ES+EN) manda a `sudo apt remove` y promete las 4.
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
   T-61 cambio solo lo que ve un humano; el resto sigue en `vercel.app` a proposito —
   lista exacta de archivos y lineas: `git grep -n "linux-remote-player.vercel.app"`.
   **Regla que no cambia: el alias `vercel.app` NO se apaga nunca** — las PWA 1.8.x leen
   `latest.json` ahi y matarlo mata el OTA de todo lo ya instalado.
4. **N4** → T-51 Paddle (alta, producto $5, webhook, compra real + refund; arrastra B1b y
   H11) → T-55 docs (absorbe T-43/T-44) → T-56 release v1.9.0 → T-57 privatizar.

## HECHO (fase v1.9 — todas auditadas APTO; la evidencia esta en git log)

- **T-46..T-50** ai-proxy + anti-abuso + licencia 1-dispositivo. Validado E2E en device
  2026-07-22 pero **sobre un build de prueba, no sobre un .deb publicado** → revalidar
  en TESTING §C/§D. El device ya no tiene llaves de IA.
- **T-50b, T-53a..d** sitio ES+EN completo y LIVE. Falta de T-53: video demo y
  `gracias.html`. Placeholders vivos: PADDLE / KOFI / VIDEO.
- **T-58** identidad app↔web (`ae27a31`). Detalle tecnico: APPCORE §skins.css.
- **T-59 + T-60** release 1.8.9 construido y PUBLICADO. sha
  `890211c8d65742d81415356195c8601c42316a6d8f53710c51780e2d072bf87c`, cuadruple match,
  identico en el dominio y en el alias vercel.
- **T-61** (`014269f`) dominio propio + `support@` en la web. Solo `website/`.
- **T-62** (`4c52165`) **skins liberadas** (implementa D4): `setSkin()` ya no consulta
  `isLicensed`, y se fueron los candados y las etiquetas `(Pro)`. La VOZ sigue siendo Pro.
  **Todavia NO llega al device: necesita el release v1.9.0.**
- **T-63** (`03581cc`) **doc de FastAPI oculta** (cierra H9), verificado en runtime.
  **Se uso `LRP_DEV` y NO `LRP_MODE`** porque `LRP_MODE=desktop` es un modo de usuario final
  real, no de desarrollo, y su default (`appliance`) habria apagado la doc tambien en la PC
  del desarrollador.

## D — DECISIONES VIGENTES (no re-litigar)

- **D1 · pagos: PADDLE.** Stripe no opera para vendedores en Ecuador. PayPal plan B.
  Donaciones por Ko-fi. Validacion = compra real $5 + refund. Paddle REVISA el sitio
  antes de aprobar → por eso web y dominio van ANTES del alta.
- **D2 · nombre comercial: LinuxRemotePlayer** (rebrand cancelado); "LRP" marca corta.
- **D3 · precio:** Pro unico $5 lifetime al lanzar. Suscripcion recien con Voz 2.0.
- **D4 · skins: las 7 planeadas van GRATIS**, son el gancho; el Pro se vendera con skins
  ADICIONALES en v2.0. Roster, spec, set de botones y criticas: **PLAN.md §PH17** (v1.9.1);
  mockups en `.agents/design/skins2/`. Falta del dueño: wallpapers (C3).
  **Codigo: las 4 que existen ya estan libres (T-62); las otras 3 son PH17.**
- **D5 · Voz 2.0 repriorizada a v2.0** (PLAN.md §PH19). Meta: que "pon video de gatos"
  REPRODUZCA, no que se quede en la busqueda. Orden 1→2→3: keymaps por sitio primero;
  control del DOM (WebDriver BiDi, el equivalente Firefox de las DevTools) al final, con
  la nota de seguridad del puerto de depuracion.
- **D6 · demo interactiva en la web** (2026-07-26): minijuego con control simulado + "TV"
  que reacciona, con las 4 skins. Spec: **PLAN.md §PH20** (v1.9.1). Dos reglas que NO se
  negocian: etiqueta de SIMULACION visible, y CERO red. Va con PH17 o despues, nunca antes.
  **No bloquea Paddle** (esa va con capturas, C5).
- **D7 · `Techlm77/LinuxPlay` NO es competencia: es otra categoria** (GPL-2.0; ellos hacen
  streaming de escritorio, LRP no transmite video). **NO se rebrandea.** Analisis, mitigacion
  de la colision de nombre y el diferenciador de cifrado usable en la web:
  **PLAN.md §MERCADO**. Su codigo no entra acá: **AGENTS.md §CODIGO DE TERCEROS**.

## H — HALLAZGOS ABIERTOS (no bloquean)

- **H12 · el numero de version que muestra la app NO describe la interfaz que estas usando.**
  Sale en vivo de `/api/status` (o sea del BACKEND), mientras el HTML/JS los sirve el service
  worker desde su cache. Si la cache no rota, la app dice "1.8.9" mientras muestra la UI de
  1.8.0. Detectado 2026-07-27 en el device del dueño: reportaba 1.8.9 con `dark` por defecto
  y las skins viejas (`dark/day/neon/anime`), que es exactamente 1.8.0 — el 1.8.9 trae `day`
  por defecto y `day/night/cafe/anime`.
  *Por que importa mas alla de este caso:* cualquier cliente que actualice puede reportar
  "actualice y no cambio nada", y el numero de version le da la razon. Suma a H3.
  *Candidato a fix:* que el frontend exponga SU propia version (la que inyecta build_deb en
  `sw.js`) y que el panel muestre las dos, o avise cuando no coinciden.
  Diagnostico pendiente del dueño: si el HTPC tiene los archivos 1.8.9 en
  `/opt/linuxremoteplayer/frontend/`, el problema es la cache del telefono; si no, no se
  aplico el .deb.
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

- [x] **C1** push de 1.8.9 (T-60). · [x] **C2** dominio comprado + `support@` en la web (T-61).
- [!] **C8 · FALLO 2026-07-27.** El correo de prueba rebota: el alias no existe. Dar de alta
      el reenvio en Namecheap (ver B1) y REPETIR la prueba. Prerrequisito de Paddle.
- [ ] **C9** diagnostico del device (ver H12): correr en el HTPC
      `cat /opt/linuxremoteplayer/VERSION` y
      `grep -o 'data-skin="[a-z]*"' /opt/linuxremoteplayer/frontend/index.html`.
      Si dice `day` → la cache del telefono esta vieja. Si dice `dark` → el .deb no se aplico.
- [ ] **C3** wallpapers de las skins nuevas. Para Gato/Perro mandar **el TILE** (~400x400),
      no el pantallazo: son patrones sin costura, tilear ya esta soportado
      (`--bg-repeat`/`--bg-size`) y un tile pesa ~30KB vs ~170KB del full-screen.
- [ ] **C4** redeployar ai-proxy con el prompt bilingue si no se hizo (T-53d). ⛔ en
      TESTING C2 porque **la web ya vende la voz en ingles**.
- [ ] **C5** screenshots nuevas del sitio: las actuales son de la skin anime, que ya no es
      el look por defecto (T-56). Son tambien las que ve Paddle.
- [ ] **C6** `supabase functions deploy send-feedback --no-verify-jwt` (desde v1.5).
- [ ] **C7** privatizar el repo al lanzar (T-57).
