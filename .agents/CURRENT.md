# CURRENT — estado vivo
<!-- Formato: AGENTS.md §FORMATO. IDs (B/N/D/H/C) son anclas: citalos, no copies el texto.
     Compactado 2026-07-28: 11.2KB -> ~9.4KB. Queda ~1.4KB SOBRE el techo de 8KB; lo que
     sobra es el porque de B1, B2, D4-D8 y H11-H12, y podarlo mas costaba informacion que
     el proximo agente no puede re-derivar. Se recupera CERRANDO items: B2 se lleva ~0.5KB
     el dia que TESTING §E pase. El detalle de cada auditoria esta en git log, no aca. -->

```yaml
version_publicada:   1.8.9    # LIVE desde 2026-07-26 (T-60). sha 890211c8…bf87c
version_en_curso:    1.9.0    # CODIGO COMPLETO Y AUDITADO, sin construir ni publicar
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

> **Lo mas importante que hay que entender al entrar:** el codigo de v1.9.0 esta terminado
> y auditado, pero **no existe ningun `.deb` de 1.9.0 y la matriz de TESTING nunca se corrio**.
> Todo lo pendiente cuelga de eso, no de escribir mas codigo.

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

## B9..B13 — LO QUE ENCONTRO EL TEST DE 1.8.10 EN DEVICE (2026-07-29)

El release de prueba 1.8.10 se publico y se probo por OTA. **Encontro un bug que habria
golpeado a TODOS los clientes el dia del lanzamiento** — esa sola razon justifico la
estrategia de sacar un build de prueba antes de 1.9.0.

- **B9 ⛔⛔ · el OTA dejaba el servicio MUERTO. ARREGLADO en T-70, sin probar en device.**
  *Causa (no era la obvia):* `lrp-update` llama a `apt-get install --reinstall`, y el
  postinst de ese paquete **reescribe `/usr/local/bin/lrp-update`** — el archivo que bash
  esta leyendo. Bash lee por posicion de byte: retoma en un offset del archivo NUEVO, cae a
  mitad de palabra, ejecuta el fragmento `start`, y `set -e` lo mata ANTES del
  `systemctl restart`. *Fix:* todo el cuerpo en funciones + `main "$@"; exit $?` en la
  MISMA linea (bash parsea el archivo entero antes de ejecutar) + `trap` que reinicia el
  servicio en toda salida. **Probado empiricamente**: el patron viejo se detiene en silencio
  y devuelve exit 0; el nuevo llega al final.
  **OJO al planificar: el fix NO puede reparar la actualizacion que lo entrega.** Un equipo
  en <=1.8.10 usa su `lrp-update` roto para instalar la siguiente version, asi que sufre el
  bug una vez mas. El OTA que tiene que verse verde antes de lanzar es **1.8.11 → 1.9.0**.
- **B10 ⛔ · la voz no se enciende si la licencia ya estaba activa antes del update.**
  `ENABLE_VOICE` solo se escribe dentro de `activate_license`; quien ya era Pro nunca pasa
  por ese flujo. *Fix:* al arrancar el backend, si hay `LICENSE_TOKEN` valido y
  `ENABLE_VOICE` **no existe** en el `.env`, ponerlo en true. **No debe pisar un `false`
  explicito** o se rompe D10 (el usuario no podria apagar la voz nunca).
- **B11 ⛔ · cadena de certificados incompleta.** `run.py:210` pasa `ssl_certfile=CERT_FILE`
  (la hoja sola) y nunca concatena `ca.pem` ni usa `ssl_ca_certs`. Funcionaba porque
  `install.sh` mete el CA en el trust store; al regenerar certs (uninstall→reinstall) deja
  de coincidir y Firefox tira `SEC_ERROR_BAD_SIGNATURE`.
- **B12 · `apt remove` deja las credenciales en disco.** `lrp-cleanup.sh` libera la licencia
  en el servidor pero el `.env` conserva el `LICENSE_TOKEN` **y el `PAIRING_TOKEN`**: al
  reinstalar re-reclama la key sola y no se puede probar la mudanza. *Fix:* borrar el `.env`.
- **B13 · el `.desktop` dice "Remote Linux Player"** (`build_deb.sh:40`). T-66 no lo cazo
  porque **el brief acoto la busqueda a `frontend/` y `website/`** — el nombre tambien vivia
  en `scripts/`. Es la leccion de "auditar REFERENCIAS" incumplida al escribir el alcance.

## N — SIGUIENTE (orden estricto)

1. **N1 · el dueño ejecuta TESTING.md sobre 1.8.9** (§A §B §C §D §F §G; §E necesita 1.9.0).
   Nada lo bloquea y es el camino critico: lo que falle tiene que entrar en el MISMO .deb.
   Antes: poner el HTPC en el 1.8.9 **publicado** (el que tiene es un build de prueba).
2. **N2 · corregir la web AL PUBLICAR v1.9.0, no antes** (parte de T-56). La web vende los
   temas como Pro y T-62 ya los libero en codigo: cambiarlas antes haria mentir a la web al
   reves para todo el que tenga 1.8.9.
   Lineas: `website/index.html:148,254,299` + `website/en/index.html:148,256,301`.
3. **N3 · T-56, armar el release v1.9.0.** Absorbe N2 y la decision de `short_name` (ver D8).
   Sigue §PROCESO DE RELEASE de AGENTS.md. **Ojo: el clon WSL nativo esta desactualizado** —
   hay que traerle T-62..T-66 antes de construir.
4. **N4** → T-51 Paddle (alta, producto $5, webhook, compra real + refund; arrastra H11) →
   T-55 docs (absorbe T-43/T-44) → T-57 privatizar.

## HECHO (fase v1.9 — todas auditadas APTO; evidencia en git log)

**T-46..T-50** ai-proxy + anti-abuso + licencia 1-dispositivo · **T-50b, T-53a..d** sitio
ES+EN LIVE · **T-58** identidad app↔web · **T-59+T-60** release 1.8.9 publicado ·
**T-61** dominio + `support@` en la web · **T-62** skins liberadas · **T-63** doc de FastAPI
oculta · **T-64** apt remove limpia · **T-65** URLs de maquina al dominio · **T-66** pulido
pre-Paddle (cierra H7, H8a, B1b) · **T-67** (`21f552a`) instalador · **T-68**
(`c2df1b3`+`6dea973`) voz automatica y enlace de compra (cierra B4, B7, B8).

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

## PRIVATIZAR EL REPO (T-57) — que hay que hacer ANTES de apretar el boton

Verificado 2026-07-29. **El OTA NO se rompe**: `latest.json` y el `.deb` se sirven de Vercel,
no de GitHub. Pero hay tres cosas que si:
1. **Vercel tiene que seguir desplegando desde un repo privado.** Soporta privados, pero la
   integracion con GitHub debe conservar el acceso. **Verificar asi:** privatizar → hacer un
   commit trivial en `website/` → confirmar que Vercel lo despliega. Si no lo hace, se
   re-autoriza la app de GitHub. **Si esto falla y no se nota, el canal OTA se congela.**
2. **El clon WSL del release** (`git clone <origin> ~/lrp-release`, §PROCESO DE RELEASE paso 2)
   va a pedir credenciales. Resolverlo ANTES, no en medio de un release.
3. **`scripts/bootstrap.sh` muere** (H6): clona desde GitHub y va a dar 404 para todos.
   Borrarlo en la misma tarea, no dejarlo publicado roto.
- Dato menor: `backend/.env.example:15` trae `GITHUB_REPO=Gusitir/LinuxRemotePlayer` y
  **ningun codigo lo lee** — variable muerta, sacarla de paso.
- **4. El push pasa a ser del dueño A PARTIR de 1.9.0, no antes.** Durante 1.8.x sigue
  vigente §CICLO paso 2 tal cual: Gemini commitea Y pushea. Cuando cambie hay que editar
  ese paso: Gemini termina con el **hash del commit local**, el auditor audita ESE commit
  (nunca el working tree — trampa de T-64) y recien con APTO pushea el dueño.
  *(Los briefs de T-69 y T-70 pidieron "no pushear" por adelantado; fue un error de tiempo
  del auditor, no un cambio de contrato.)*

## H — HALLAZGOS ABIERTOS (no bloquean)

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
- [ ] **C7** privatizar el repo al lanzar (T-57).
