# CURRENT — estado vivo
<!-- Formato: AGENTS.md §FORMATO. IDs (B/N/D/H/C) son anclas: citalos, no copies el texto.
     Tamaño ~12.8KB, SOBRE el techo de 8KB. Esta inflado a proposito y de forma transitoria:
     el ciclo de correcciones de 1.8.10 tiene 6 bugs abiertos a la vez (§B9..B14) que se van
     TODOS cuando el device valide 1.8.11. Ya se movio a PLAN lo que era spec de tarea
     futura (T-57) y a comentarios del codigo el porque de B9/B14. Lo que queda es estado
     vivo. El detalle de cada auditoria esta en git log, no aca. -->

```yaml
version_publicada:   1.8.10   # LIVE desde 2026-07-29 (T-69). Build DE PRUEBA, no lanzamiento
version_en_curso:    1.9.0    # falta T-73, despues construir 1.8.11 y probar el OTA
dominio:             https://www.linuxremoteplayer.com  # sirviendo desde Vercel
alias_vercel:        linux-remote-player.vercel.app     # VIVO a proposito: canal OTA del parque 1.8.x
correo_soporte:      support@linuxremoteplayer.com      # buzon real (Namecheap Private Email)
fase_activa:         v1.9 -> PLAN_v1.9.md   # hechas T-46..T-66; faltan T-51/T-55/T-56/T-57
repo:                publico; se privatiza en T-57
licencia:            Elastic 2.0
ultima_sesion:       2026-07-28
pruebas_device:      TESTING.md — matriz del ciclo 1.8.9 SIN EJECUTAR TODAVIA
docs_humanos:        docs/ARCHITECTURE.md (la forma) + docs/DEVELOPING.md (como trabajar)
historia:            CONTEXT.md + git log
```

> **Lo mas importante que hay que entender al entrar:** la matriz de TESTING **YA SE CORRIO**
> sobre el build de prueba 1.8.10 (29/07) y encontro 6 bugs, uno de ellos catastrofico: el
> OTA dejaba el servicio muerto en todos los dispositivos. Cinco ya estan arreglados
> (T-70..T-72) y el sexto es T-73. **Ninguno de esos arreglos se probo en device todavia.**
> El proximo paso es un build 1.8.11 y volver a correr el OTA — ver §N.

## B — BLOQUEANTES

- **B1 · el correo de soporte no esta probado de punta a punta.** La web publica `support@`
  en 14 lugares. **Recibir funciona**; enviar rebotaba con `550-5.7.26` de Gmail, pero **esa
  causa ya no existe**: el DNS (SPF unico + DKIM + DMARC) se cargo despues y esta verificado
  contra 8.8.8.8 y 1.1.1.1, y las dos IPs que Gmail rechazo estan autorizadas por ese SPF.
  El 2do fallo fue **cache negativa** de Gmail. → Falta solo **reintentar el envio** (C8/C9).
  **NO tocar el DNS mientras tanto**: cada cambio reinicia el reloj del cache.
  *Leccion:* publicar una direccion no prueba que exista un buzon, y que el buzon exista no
  prueba que lo que mande llegue.
- **B2 · `apt remove` incumple la doc — ARREGLADO EN CODIGO (T-64), SIN PROBAR.**
  Sigue como bloqueante porque el fix **no esta verificado**: toca un script de mantenedor y
  eso necesita un Debian real. Se cierra con **TESTING §E**.
  *El fix:* `scripts/lrp-cleanup.sh` (no interactivo, sin `set -e`, siempre `exit 0`) con las
  4 acciones que promete la doc; lo llaman el `prerm` y `uninstall.sh`.
  **El riesgo que domina todo esto: la limpieza solo corre con `$1 = "remove"`.** dpkg invoca
  el prerm TAMBIEN en cada actualizacion con `upgrade`; sin ese guard, **cada OTA borraria las
  reglas udev y liberaria la licencia de todos los dispositivos**. Es T-19 otra vez, y es
  exactamente lo que mide **TESTING E1**.

## B9..B14 — LO QUE ENCONTRO EL TEST DE 1.8.10 EN DEVICE (2026-07-29)

El build de prueba encontro **un bug que habria golpeado a todos los clientes el dia del
lanzamiento**, y eso solo justifico la estrategia de probar antes de 1.9.0.
**Ninguno de los arreglos se probo en device todavia** — hace falta 1.8.11 (§N).

**Resueltos (T-70..T-72). El porque tecnico esta COMENTADO EN EL CODIGO**, que es donde lo
va a leer quien intente "ordenarlo"; el detalle de cada auditoria, en git log:
- **B9 ⛔⛔ el OTA dejaba el servicio MUERTO** — `lrp-update` se reescribia a si mismo al
  correr `apt-get install`. Ver la cabecera del heredoc en `scripts/build_deb.sh`.
  **Al planificar: el fix NO repara la actualizacion que lo entrega** — un equipo en <=1.8.10
  sufre el bug una vez mas. El OTA que tiene que verse verde es **1.8.11 → 1.9.0**.
- **B10 ⛔ la voz no se encendia si ya eras Pro** — ahora tambien al arrancar, y **nunca pisa
  un `false` explicito** (eso es D10, y hay test que lo cubre).
- **B11 ⛔ faltaba mandar la cadena de certificados** — `ensure_full_chain()`, idempotente y
  llamada donde se configura uvicorn, NO dentro de `ensure_cert` (que retorna temprano y ahi
  adentro no repararia una instalacion rota).
- **B14 una reinstalacion rompia los telefonos emparejados** — la CA renacia con el MISMO
  nombre y otra llave: el navegador tenia el dato VIEJO, no le faltaba uno; por eso decia
  "firma invalida" y la cadena de B11 no lo arreglaba. **No repara lo ya roto: hay que borrar
  la CA vieja a mano del sistema y del iPhone, una vez.**

**Pendientes** — ya no: **B12 y B13 se cerraron en T-73** (`6ac5d2d`). Ese commit toco 5
archivos y no 3: mi brief decia "3 archivos" pero su propio check exigia cero ocurrencias
del nombre en TODO el repo, asi que el ejecutor siguio la verificacion, que era la spec
estricta. Aparecio ademas el nombre invertido en **el correo que recibe el cliente con su
clave** (`stripe-webhook`). **OJO: ese cambio no surte efecto hasta redesplegar la Edge
Function** — va con T-51. Lo que decian era:
- **B12 · `apt remove` deja credenciales en disco.** El `.env` conserva `LICENSE_TOKEN` y
  `PAIRING_TOKEN`, y al reinstalar re-reclama la licencia sola. *Fix:* borrarlo **al final**
  de `lrp-cleanup.sh` — el paso que libera la licencia lee ese mismo archivo.
- **B13 · el `.desktop` dice "Remote Linux Player"** (`build_deb.sh:40`). T-66 no lo cazo
  porque **el brief acoto la busqueda a `frontend/` y `website/`**: la leccion de "auditar
  REFERENCIAS" incumplida al escribir el alcance.

## N — SIGUIENTE (orden estricto)

1. **N1 · T-77: el log del actualizador a `/var/log`** (H18). Una linea, y es lo ultimo de
   codigo. Se puede plegar dentro de T-56 si se prefiere no gastar una tarea.
2. **N2 · T-56, el release v1.9.0. YA NO HAY BLOQUEANTES TECNICOS.** Absorbe N4 (las 6
   lineas de la web que aun venden los temas como Pro) y el `CHANGELOG`. El ciclo de 1.8.12
   cerro B9, T-75 y la reconexion de la PWA: **lo que falta para vender ya no es codigo.**
   Sigue §PROCESO DE RELEASE de AGENTS.md.
3. **N3 · lo comercial:** C8/C9 (probar el correo), C5 (capturas con la skin Day), T-51
   (alta de Paddle, arrastra B1b y H11), T-55 docs, T-57 privatizar (PLAN.md §T-57).
4. **N4 · corregir la web AL PUBLICAR v1.9.0, no antes.** La web vende los temas como Pro y
   T-62 ya los libero en codigo; cambiarlas antes haria mentir a la web al reves.
   Lineas: `website/index.html:148,254,299` + `website/en/index.html:148,256,301`.
5. **N5 · T-56, el release v1.9.0.** Absorbe N4. Sigue §PROCESO DE RELEASE de AGENTS.md.
6. **N6** → T-51 Paddle (alta, producto $5, webhook, compra real + refund; arrastra H11) →
   T-55 docs (absorbe T-43/T-44) → T-57 privatizar.

## HECHO (fase v1.9 — todas auditadas APTO; evidencia en git log)

**T-46..T-50** ai-proxy + anti-abuso + licencia 1-dispositivo · **T-50b, T-53a..d** sitio
ES+EN LIVE · **T-58** identidad app↔web · **T-59+T-60** release 1.8.9 publicado ·
**T-61** dominio + `support@` en la web · **T-62** skins liberadas · **T-63** doc de FastAPI
oculta · **T-64** apt remove limpia · **T-65** URLs de maquina al dominio · **T-66** pulido
pre-Paddle (cierra H7, H8a, B1b) · **T-67** (`21f552a`) instalador · **T-68**
(`c2df1b3`+`6dea973`) voz automatica y enlace de compra (cierra B4, B7, B8) ·
**T-69** (`f36bee9`) **release 1.8.10 de prueba, PUBLICADO** · **T-70** (`2f2b6b2`)
`lrp-update` a prueba de auto-reescritura (cierra B9) · **T-71** (`168259c`) voz al arrancar
+ cadena de certificados (cierra B10, B11) · **T-72** (`0238bb0`) CA con nombre unico
(cierra B14).

Lo unico que el proximo agente no puede re-derivar de git:
- **T-46..T-50 se validaron sobre un build de prueba, NO sobre un .deb publicado** →
  revalidar en TESTING §C/§D. De T-53 falta el video demo. Placeholders vivos en la web:
  PADDLE / KOFI / VIDEO.
- **T-62 y T-64 no llegan a ningun device hasta el release v1.9.0.**
- **T-64 traia un defecto que ninguna verificacion de sintaxis caza**: `lrp-cleanup.sh`
  commiteado sin bit de ejecucion. En el `.deb` no se veia (`build_deb.sh:61` hace `chmod +x`),
  pero en un clon de git el guard `[ -x ]` de `uninstall.sh` daba falso y el desinstalador
  manual dejaba de hacer sus 4 acciones **en silencio**. Corregido.

## D — DECISIONES VIGENTES (no re-litigar)

- **D1 · pagos: PADDLE.** Stripe no opera para vendedores en Ecuador; PayPal plan B;
  donaciones por Ko-fi. Validacion = compra real $5 + refund. **Paddle REVISA el sitio antes
  de aprobar** → por eso web, dominio y capturas van ANTES del alta.
- **D2 · nombre comercial: LinuxRemotePlayer** (rebrand cancelado); **"LRP" marca corta**.
- **D3 · precio:** Pro unico $5 lifetime al lanzar. Suscripcion recien con Voz 2.0.
- **D4 · las 7 skins planeadas van GRATIS**, son el gancho; el Pro se vendera con skins
  ADICIONALES en v2.0. Roster y spec: **PLAN.md §PH17** (v1.9.1); mockups en
  `.agents/design/skins2/`. Falta del dueño: wallpapers (C3).
  **Codigo: las 4 que existen ya estan libres (T-62); las otras 3 son PH17.**
- **D5 · Voz 2.0 repriorizada a v2.0** (PLAN.md §PH19). Meta: que "pon video de gatos"
  REPRODUZCA, no que se quede en la busqueda.
- **D6 · demo interactiva en la web** (minijuego con control simulado + "TV"), spec en
  **PLAN.md §PH20** (v1.9.1). Dos reglas que NO se negocian: etiqueta de SIMULACION visible
  y CERO red. Va con PH17 o despues, nunca antes. No bloquea Paddle.
- **D7 · `Techlm77/LinuxPlay` NO es competencia: otra categoria** (GPL-2.0, streaming de
  escritorio; LRP no transmite video). **NO se rebrandea.** Analisis: **PLAN.md §MERCADO**.
  Su codigo no entra acá: **AGENTS.md §CÓDIGO DE TERCEROS**.
- **D8 · PENDIENTE de decidir, se aplica en T-56 · `manifest.json` `short_name`.** Quedo en
  `"RemoteLinux"`, una TERCERA variante del nombre (T-66 arreglo las otras 8; esta no estaba
  en su alcance). Es el rotulo bajo el icono en Android y el campo existe para ser CORTO, asi
  que "LinuxRemotePlayer" (17 chars) no sirve. **Recomendacion: `"LRP"`** (D2).

## RESULTADO DEL TEST DE 1.8.11 EN DEVICE (2026-07-30, agente del HTPC + dueño)

**5 de las 6 correcciones quedaron VERIFICADAS en hardware:** B10 (la voz se enciende sola:
se borro `ENABLE_VOICE` del `.env`, se reinicio y el backend lo repuso), B11 (`cert.pem` con
2 certificados y `openssl verify` OK), B12 (el `.env` desaparece con `apt remove`), B13/D8
(`Name=LinuxRemotePlayer`, `short_name=LRP`, confirmado tambien en el iPhone) y **B14 (CA
regenerada como `CN=LinuxRemotePlayer CA d98ec4ef`, CON sufijo)**.

> ### ✅ B9 CERRADO EN DEVICE — 2026-07-30, ciclo 1.8.12
> El OTA de 1.8.11 → 1.8.12, **disparado por la API igual que lo haria un cliente**, dejo el
> servicio en **`active`** sin intervencion. Era la unica correccion que faltaba validar y
> **la que bloqueaba el lanzamiento**. Tambien quedaron verificados: T-75 (el `apt remove`
> borra `.env`, `.pairing_token`, `certs/` y la CA del sistema), que la actualizacion NO
> toca nada ni libera la licencia, y —en un retest limpio— que **la PWA reconecta sola**.
> **Veredicto del ciclo: se puede lanzar 1.9.0.**
>
> *Nota de metodo:* el primer S1b dio FALLA pero estaba **contaminado** (se midio despues de
> los items destructivos, que regeneran la CA). El agente lo detecto, lo declaro, y armo un
> retest limpio reinstalando el mismo `.deb` para simular un OTA sin cambiar certificados.
> Esa distincion es la diferencia entre un bug inventado y un dato.

> ### ~~⛔ LO UNICO QUE SIGUE SIN PROBARSE ES LO MAS IMPORTANTE: B9~~ (historico)
> R1 fallo **como estaba previsto** — el equipo corria el `lrp-update` roto de 1.8.10 para
> instalar su propia correccion, y el servicio quedo `inactive`. O sea que **el arreglo que
> hace que una actualizacion reinicie el servicio NUNCA se ejecuto todavia.**
> **El OTA de 1.8.11 → 1.9.0 ES la prueba de B9, y es tambien el lanzamiento.** Si falla
> ahi, cada cliente pierde el control remoto en su primera actualizacion y hay que
> levantarlo por SSH. Es el riesgo numero uno del lanzamiento: **publicar 1.9.0 y NO
> actualizar el HTPC de inmediato para verificarlo seria lanzar a ciegas.**

Dos cosas mas del reporte:
- **R9 (cambio de IP) quedo verificado SOLO POR INSPECCION de codigo**, no de punta a punta:
  no se puede forzar sin perder el acceso remoto al equipo. Aceptado como declarado.
- El agente **declaro una excepcion a su propia regla de no tocar nada** (borro
  `backend/certs/` con permiso del dueño para forzar la regeneracion de la CA) en vez de
  ocultarla, y **construyo una prueba mejor que la del guion** para B10. Es la conducta que
  se le pidio.

## H — HALLAZGOS ABIERTOS (no bloquean)

- **H18 · el log del actualizador queda mudo si `/tmp/lrp-update.log` es de otro usuario.**
  Lo encontro el agente del HTPC (30/07): `exec >>/tmp/lrp-update.log 2>&1` falla con
  "Permiso denegado" cuando el archivo lo creo otro usuario en una corrida previa.
  **NO es peligroso — verificado empiricamente:** el script sobrevive (bash imprime el error
  y sigue) porque ese `exec` va ANTES del `set -e`, y systemd captura toda la salida en el
  journal igual. El costo es solo perder el log dedicado, que es justo el que se mira cuando
  un OTA sale mal.
  **NO adoptar el parche que probo el agente** (`exec 3>>` dentro de un `if`): probado, no
  silencia el mensaje —el `2>/dev/null` no alcanza al error que bash emite por la
  redireccion— y agrega complejidad a un script critico sin resolver el sintoma.
  *Fix correcto, va en 1.9.0:* mover el log a **`/var/log/lrp-update.log`**. Es root-only,
  asi que ningun usuario puede dejar ahi un archivo ajeno, y queda fuera de `/tmp`, que es lo
  que aislaria `PrivateTmp` si algun dia se activa.
  *Ojo:* el agente aplico su parche **en vivo sobre el equipo** — una excepcion a su regla de
  no tocar codigo. Lo declaro, y advirtio que el proximo `apt` lo pisa. Esta bien que lo
  dijera; el arreglo de verdad tiene que viajar en el `.deb`.

- **B16 · `apt remove` deja CLAVES y CREDENCIALES en el disco.** `uninstall.sh` borra
  `certs/` y `.pairing_token`, pero **`lrp-cleanup.sh` —el camino de `apt remove`, que es el
  que recomienda la doc— solo borra el `.env`**. Sobreviven: el directorio `certs/` con
  `ca.key` y `key.pem` (**claves privadas**) y el `.pairing_token`. Lo destapo el agente al
  ver que la CA no se regeneraba con sufijo.
  **CORRECCION 2026-07-30:** B12 decia que el `PAIRING_TOKEN` vivia en el `.env`. **Es
  inexacto**: `auth.py:17-25` lo lee del entorno y si no esta cae a
  `backend/.pairing_token`, que es lo que escribe `install.sh:293`. O sea que borrar el
  `.env` no alcanzaba para llevarse esa credencial. Lo caza T-75.
- ~~**B17 · `sleep.target` en `static`.**~~ **CERRADO 2026-07-30, no era un bug.** Tras la
  reinstalacion de D-2 quedo `masked` en `sleep.target` y `suspend.target`: el `static` que
  vio el agente era residuo del ciclo anterior, donde la desinstalacion lo desenmascaro y no
  hubo reinstalacion despues. `install.sh:79` funciona.
- **H15 · desinstalar deja la CA en el almacen de confianza del sistema.** `install.sh:353`
  copia el `ca.pem` a `/usr/local/share/ca-certificates/lrp-ca.crt`, y ningun script lo saca.
  Queda una raiz de confianza instalada tras desinstalar el producto. *No se pudo confirmar
  en este ciclo* (la CA ya se habia borrado a mano para D-2), pero esta claro en el codigo.
  **B16, B17 y H15 van juntos en una sola tarea**: los tres son "la desinstalacion no hace lo
  que promete", que es la tercera vez que aparece despues de B2 y B12.

- **H11** `backend/.env.example:20` trae `BUY_URL=https://buy.stripe.com/test_...`: Stripe en
  modo TEST cuando los pagos ya son Paddle (D1). Es la plantilla del `.env` real → el boton
  "comprar" de un device apuntaria a un checkout de prueba. Se arregla en T-51.
- **H12** el numero de version que muestra la app **no describe la interfaz que corre**: sale
  de `/api/status` (backend) mientras el HTML/JS los sirve el service worker desde su cache.
  Un cliente diria "actualice y no cambio nada" con el producto dandole la razon. Prioridad
  baja. *Fix si molesta:* que el frontend exponga SU version (la de `sw.js`) y el panel avise.
- **H1** cold-start de voz: el 1er comando tras inactividad tarda segundos (Edge Function
  dormida + Whisper frio). Medir en TESTING C3 antes de decidir un keep-alive.
- **H2** Whisper alucina con silencio → texto fantasma. Arreglo: descartar audios <~1s.
- **H3** el OTA no es transparente: actualiza al cerrar/reabrir la PWA. Aceptado.
- **H4** falta intent "volumen al maximo" (hoy sube 1 paso).
- **H5** `showInstallScreen` usa `appUI.hidden=true` pero `#app-ui` tiene `.flex` (el autor le
  gana al `[hidden]` del UA); `showPairingScreen` lo esquiva con `style.display`. Unificar.
- **H6** `bootstrap.sh` (instala por git-clone) es legacy y muere con el repo privado (T-54).
- **H8b** "Okular" DUPLICADO en las apps detectadas (`backend/discovery.py` escanea `.desktop`;
  causa probable: mismo id en dos rutas sin deduplicar). **No se reproduce sin el HTPC.**
- Cerradas: **H7**, **H8a** (T-66) · **H9** (T-63) · **H10** (docs/DEVELOPING.md).

## C — CHECKLIST DEL DUEÑO (lo del device esta en TESTING.md)

- [x] **C1** push de 1.8.9 · [x] **C2** dominio + `support@` en la web
- [ ] **C8** correo de prueba HACIA `support@` desde gmail → confirmar que llega.
- [ ] **C9** correo DESDE `support@` hacia gmail → "Mostrar original" con **SPF y DKIM PASS**.
      El DNS ya esta cargado y verificado; esto solo espera que expire el cache de Gmail.
      **Cuando entre Resend (T-51), su include va en el MISMO registro SPF** — un dominio con
      dos registros SPF falla en ambos y ahi se pierde el correo de licencias.
- [~] **C4 · probablemente HECHO**: el dueño reporto dos veces que **los comandos en INGLES
      funcionan** — es lo que habilita el prompt bilingue (T-53d) y lo que mide TESTING C2.
      Falta marcarlo formalmente ahi.
- [ ] **C5** capturas nuevas — **tienen que salir de v1.9.0**, o fotografian el nombre viejo
      y las skins bloqueadas. Son las que ve Paddle.
- [ ] **C6** `supabase functions deploy send-feedback --no-verify-jwt` (desde v1.5).
- [ ] **C3** wallpapers de las skins nuevas (PH17/v1.9.1, no bloquea el lanzamiento). Para
      Gato/Perro mandar **el TILE** (~400x400), no el pantallazo: son patrones sin costura,
      tilear ya esta soportado y un tile pesa ~30KB vs ~170KB del full-screen.
- [ ] **C7** privatizar el repo al lanzar. **Que verificar antes: PLAN.md §T-57** — el OTA
      no se rompe (lo sirve Vercel), pero si Vercel deja de desplegar y no se nota, el canal
      de actualizacion se congela en silencio.
