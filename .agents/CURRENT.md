# CURRENT — estado vivo
<!-- Formato: AGENTS.md §FORMATO. IDs (B/N/D/H/C) son anclas: citalos, no copies el texto.
     Ronda el techo de 8KB y a veces lo pasa. El espacio se recupera CERRANDO items
     (B1, B2, H11, H12), no borrando el porque. El detalle de cada auditoria esta en git. -->

```yaml
version_publicada:   1.8.9    # LIVE desde 2026-07-26 (T-60). sha 890211c8…bf87c
dominio:             https://www.linuxremoteplayer.com  # comprado y sirviendo desde Vercel
alias_vercel:        linux-remote-player.vercel.app     # VIVO a proposito: es el canal OTA
correo_soporte:      support@linuxremoteplayer.com      # el viejo soporte@ NO existia
fase_activa:         v1.9 -> PLAN_v1.9.md   # ejecutadas T-46..T-65; faltan T-51/T-55/T-56/T-57
repo:                publico; se privatiza en T-57
licencia:            Elastic 2.0
ultima_sesion:       2026-07-27
pruebas_device:      TESTING.md (matriz ciclo 1.8.9; DESBLOQUEADA por T-60)
docs_humanos:        docs/ARCHITECTURE.md (la forma) + docs/DEVELOPING.md (como trabajar)
historia:            CONTEXT.md + git log
```

## B — BLOQUEANTES (rotos AHORA, en produccion)

- **B1 · EN CURSO: el buzon `support@` ya existe; falta confirmar que RECIBE y arreglar SPF.**
  T-61 puso la direccion en la web (14 lugares) cuando no habia buzon detras (C8 reboto con
  `554 Relay access denied`). El dueño migro a un buzon REAL: **verificado 2026-07-27 que los
  MX ahora son `mx1/mx2.privateemail.com`** (Namecheap Private Email) y ya no el reenvio
  gratuito — o sea que support@ tambien puede ENVIAR, no solo recibir. Falta C8.
  **HUECO NUEVO (verificado contra 8.8.8.8 y 1.1.1.1): el dominio NO tiene NINGUN registro
  TXT.** Se perdio el SPF que existia con el reenvio, y no hay DKIM ni DMARC. Efecto: lo que
  SALGA de support@ tiene alta chance de caer en spam en Gmail/Outlook. **Importa ya**: T-51
  manda las claves de licencia por correo y la correspondencia con Paddle va por ahi.
  Fix (ver C9). *Leccion:* que la web publique una direccion no prueba que exista un buzon,
  y que el buzon exista no prueba que lo que mande llegue.
- **B1b · `website/gracias.html:226` publica el gmail PERSONAL del dueño**
  (`aeciminer02@gmail.com`). La pagina de "gracias por comprar" es de las que MIRA un
  procesador de pagos: un gmail personal ahi resta credibilidad. Se rehace en T-51.
- **B2 · `apt remove` incumple la doc — ARREGLADO EN CODIGO (T-64), SIN PROBAR EN DEVICE.**
  Sigue listado como bloqueante porque el fix **no esta verificado**: toca un script de
  mantenedor y eso no se puede probar sin un Debian real. Se cierra recien con **TESTING §E**.
  *Que hace el fix:* nace `scripts/lrp-cleanup.sh` (no interactivo, sin `set -e`, siempre
  `exit 0`) con las 4 acciones que la doc promete; lo llaman el `prerm` y `uninstall.sh`.
  **El riesgo que domina esto: la limpieza solo corre con `$1 = "remove"`.** dpkg invoca el
  prerm TAMBIEN en cada actualizacion con `upgrade`; sin ese guard, cada OTA borraria las
  reglas udev y liberaria la licencia de todos los dispositivos. Es T-19 otra vez, y es lo
  que prueba **TESTING E1**.

## N — SIGUIENTE (orden estricto)

1. **N1 · el dueño ejecuta TESTING.md** (empezar por los ⛔). Nada lo bloquea.
2. **N2 · corregir la web AL PUBLICAR v1.9.0, no antes** (parte de T-56). La web vende los
   temas como Pro y T-62 ya los libero en el codigo: hasta que el `.deb` nuevo este
   publicado, cambiarlas haria mentir a la web al reves para todo el que tenga 1.8.9.
   Lineas: `website/index.html:148,254,299` + `website/en/index.html:148,256,301`.
3. **N3 · T-56, armar el release v1.9.0.** El CODIGO YA ESTA COMPLETO (T-62 skins libres,
   T-63 doc FastAPI, T-64 apt remove, T-65 dominio). El brief de T-56 tiene que absorber N2
   y seguir §PROCESO DE RELEASE de AGENTS.md. **Ojo: el .deb se construye en el clon WSL
   nativo, que hoy esta desactualizado** — hay que traer todos los commits de T-62..T-65.
4. **N4** → T-51 Paddle (alta, producto $5, webhook, compra real + refund; arrastra B1b y
   H11) → T-55 docs (absorbe T-43/T-44) → T-57 privatizar.

## HECHO (fase v1.9 — todas auditadas APTO; la evidencia esta en git log)

**T-46..T-50** ai-proxy + anti-abuso + licencia 1-dispositivo · **T-50b, T-53a..d** sitio
ES+EN LIVE · **T-58** identidad app↔web (`ae27a31`) · **T-59+T-60** release 1.8.9 construido
y PUBLICADO · **T-61** (`014269f`) dominio + `support@` en la web · **T-62** (`4c52165`)
skins liberadas · **T-63** (`03581cc`) doc de FastAPI oculta · **T-64** (`21e7d09`+`82a84c9`)
apt remove limpia · **T-65** (`4f35c0d`) URLs de maquina al dominio.

Lo unico de ahi que el proximo agente no puede re-derivar de git:
- **T-46..T-50 se validaron sobre un build de prueba, NO sobre un .deb publicado** →
  revalidar en TESTING §C/§D. Falta de T-53: video demo y `gracias.html`.
  Placeholders vivos en la web: PADDLE / KOFI / VIDEO.
- **T-62 y T-64 todavia NO llegan a ningun device**: necesitan el release v1.9.0.
- **T-64 se entrego SIN reporte** y traia un defecto que ninguna verificacion de sintaxis
  caza: `lrp-cleanup.sh` commiteado en modo `100644`. En el `.deb` no se veia porque
  `build_deb.sh:61` le hace `chmod +x`, pero en un clon de git el guard `[ -x ]` de
  `uninstall.sh` daba falso y el desinstalador manual dejaba de hacer las 4 acciones **en
  silencio**. Corregido. La leccion esta en AGENTS.md §CICLO.

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
  **PLAN.md §MERCADO**. Su codigo no entra acá: **AGENTS.md §CÓDIGO DE TERCEROS**.

## H — HALLAZGOS ABIERTOS (no bloquean)

- **H12 · el numero de version que muestra la app NO describe la interfaz que corre.** Sale
  de `/api/status` (BACKEND) mientras el HTML/JS los sirve el service worker desde su cache:
  pueden discrepar sin que nada avise, y un cliente diria "actualice y no cambio nada" con
  el propio producto dandole la razon. Suma a H3. **Bajado de prioridad** (dueño 2026-07-27):
  el caso que lo destapo era un build de prueba nunca anotado, no una instalacion normal.
  *Fix si algun dia molesta:* que el frontend exponga SU version (la que `build_deb` inyecta
  en `sw.js`) y el panel avise cuando no coincide.
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
- [ ] **C8** correo de prueba a `support@linuxremoteplayer.com` desde una cuenta de fuera
      (gmail) y confirmar que LLEGA al buzon. Los MX ya apuntan a Private Email. Cierra
      la mitad de B1 y es prerrequisito de Paddle.
- [ ] **C9** cargar los TXT que faltan en el DNS (hoy el dominio no tiene NINGUNO):
      SPF `v=spf1 include:spf.privateemail.com ~all` · DKIM desde el panel de Private Email
      (lo autogenera) · DMARC `_dmarc` con `v=DMARC1; p=none; rua=mailto:support@...`.
      Despues mandar un correo DESDE support@ a un gmail y ver que no caiga en spam.
      **Cuando entre Resend para las claves de licencia (T-51), su include va en el MISMO
      SPF** — un dominio no puede tener dos registros SPF.
- [ ] **C3** wallpapers de las skins nuevas. Para Gato/Perro mandar **el TILE** (~400x400),
      no el pantallazo: son patrones sin costura, tilear ya esta soportado
      (`--bg-repeat`/`--bg-size`) y un tile pesa ~30KB vs ~170KB del full-screen.
- [ ] **C4** redeployar ai-proxy con el prompt bilingue si no se hizo (T-53d). ⛔ en
      TESTING C2 porque **la web ya vende la voz en ingles**.
- [ ] **C5** screenshots nuevas del sitio: las actuales son de la skin anime, que ya no es
      el look por defecto (T-56). Son tambien las que ve Paddle.
- [ ] **C6** `supabase functions deploy send-feedback --no-verify-jwt` (desde v1.5).
- [ ] **C7** privatizar el repo al lanzar (T-57).
