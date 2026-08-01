# BUGS.md — registro de bugs y hallazgos

<!-- SIN TECHO DE TAMAÑO: este archivo crece a proposito, es el historial.
     QUE ES: el registro de que bugs existen, si estan abiertos o cerrados, y como se
     resolvieron. NO se trabaja aca. La planificacion vive en PLAN.md y el estado de la
     version en CURRENT.md, que solo apunta a los IDs que tiene agendados.
     ARRANQUE: 2026-07-31, desde la 1.9.x. Lo cerrado ANTES de 1.9.0 no se registra —
     esta en git log y en archive/. Se empieza limpio a proposito.
     IDs: se conservan los historicos (B/H) porque los citan commits, codigo y PLAN. -->

**Formato de cada entrada:** id · titulo · estado · version · y despues, si esta **ABIERTO**,
la descripcion y como se manifiesta; si esta **CERRADO**, como se resolvio.

---

# 🔴 ABIERTOS

## B19 · El OTA da root sin firma
**BLOQUEA COBRAR · agendado a v1.9.2 · lo hallo el auditor externo (31/07)**

**Es el primer bug de este registro y el primero que vamos a trabajar.**

`lrp-update` corre como **root** (sudoers `%input ALL=(root) NOPASSWD`), baja el `.deb` desde
el dominio y lo instala. Verifica un sha256 — **pero ese sha256 sale del MISMO origen que el
`.deb`**. Eso detecta que la descarga no se corrompio; no detecta que la descarga sea hostil.

**Como se manifiesta:** quien tome la cuenta de Vercel, la del registrador de dominio o el
DNS, **ejecuta codigo como root en la maquina de cada cliente**. No hay firma, no hay clave
publica embebida, no hay repositorio firmado. Y no hay ninguna señal de que ocurrio.

**Calibracion (verificada 31/07, corrige al reporte del auditor):** **no hay timer ni cron.**
El `systemd-run` de `build_deb.sh:151` es solo el auto-desprendimiento del actualizador ya
lanzado. Hace falta que el usuario toque "Actualizar" — pero la app le avisa que hay version
nueva, asi que lo va a tocar. No es "toda la flota al instante": es "todos los que actualicen
despues del compromiso".

**Plan del arreglo, en tres capas: PLAN.md §OTA-FIRMA.** Resumen: capa 0 endurecer el origen
(USER §U1, sin codigo, hoy) · capa 1 firma separada sobre `latest.json` con la clave privada
**offline**, en 1.9.2 · capa 2 repositorio APT firmado, en v2.0.

## B19b · Ventana TOCTOU en el actualizador
**abierto · va con B19 · auditor externo**

`lrp-update` hace `cd /tmp` y escribe `linuxremoteplayer_${VERSION}_all.deb`: nombre
**predecible** en directorio compartido, con una ventana entre `sha256sum -c` y
`apt-get install`. `systemd-run --collect` **no** activa `PrivateTmp` por defecto (el
comentario de H18 en el script sugiere que se creyo lo contrario).
*Fix:* `mktemp -d` con permisos de root. Escalada local; en un HTPC de un solo usuario el
impacto practico es bajo, pero se arregla junto con B19 porque es el mismo archivo.

## H23 · La app promete "Temas Pro" que hoy no existen
**abierto · v1.9.2 (quitar) y v1.9.3 (volver a poner) · auditor externo**

`frontend/index.html:408` dice que pegar la clave *"desbloquea Temas Pro y control por Voz con
IA"*. **Contradice los terminos publicados**, que declaran los cuatro temas gratis. Verificado:
`isLicensed` (`app.js:185-226`) solo gatea la voz y el bloque de licencia; **no toca el
selector de skins**.

**Como se manifiesta:** el comprador paga $5, lee que desbloqueo temas Pro, y no encuentra
ninguno. Es el producto contradiciendo por escrito el contrato de venta que Paddle intermedia.
Viaja dentro de cada instalacion.

**Decision del dueño (31/07):** quitar la mencion en **1.9.2** y **volver a ponerla en 1.9.3**,
cuando salga la skin PREVIEW PRO. El texto tiene que decir la verdad de cada momento.

## H24 · El boton de compra de la app contradice el diseño declarado
**abierto · v1.9.2 · auditor externo**

`backend/main.py:453` y `backend/.env.example:16` dicen que `buy_url` vacio significa *"la app
no ofrece compra"*. Pero `frontend/app.js:239` tiene fallback duro
`buy_url || 'https://www.linuxremoteplayer.com/'`, y `#buy-license-btn` no se oculta nunca
(`grep buy-license-btn frontend/app.js` → cero coincidencias).
`frontend/status.html:449-457` **si** respeta la regla.
**Como se manifiesta:** hoy el boton lleva a la home, donde el boton de compra esta
deshabilitado con "Compra disponible muy pronto". Callejon sin salida.

## H25 · La app muestra el token de emparejamiento como si fuera la licencia
**abierto · v1.9.2 · auditor externo**

`frontend/app.js:217-218` arma `Clave: LRP-xxxx••••••••xxxx` con la variable `token`, que es
el **token de emparejamiento** (`app.js:59`, usado como `X-Auth-Token` en `:181`), no la clave
de licencia — esa se manda en `activateLicenseKey()` y nunca se guarda en el cliente.
**Como se manifiesta:** (1) quien quiera confirmar "¿guarde bien mi clave?" ve un valor que no
se parece al que le llego por correo, y escribe a soporte; (2) se renderizan 8 caracteres del
secreto de emparejamiento sin motivo.

## H19 · El QR lleva a una pagina "Offline"
**abierto · v1.9.2 · re-verificado en codigo el 31/07 (se lo creia corregido)**

El QR codifica `https://<ip>:<port>/?token=<TOKEN>` (`backend/main.py:372`) y **ninguna de las
tres `caches.match` de `frontend/sw.js` usa `ignoreSearch`**, asi que la URL con query no
matchea el precache de `/`.

**Por que PARECE arreglado:** con red buena, el `fetch` resuelve antes del timeout de 3 s y el
service worker nunca toca el cache. **Falla solo con el backend lento o caido** — justo cuando
el usuario necesita que funcione.

*Fix:* `{ ignoreSearch: true }` **+ el `else` que falta en `sw.js:34`**: hoy, si el timeout
salta y el cache falla, la promesa **nunca resuelve** y la pagina queda colgada. La rama del
`catch` (`:51`) si tiene su `else` y devuelve el 503 "Offline".

## H12 · La version del backend y la de la interfaz divergen sin aviso
**abierto · v1.9.2**

El numero sale del backend por un lado y del nombre de cache del service worker por otro.
Divergen cuando la PWA nunca se cierra: el OTA actualiza el backend y el telefono sigue con el
`app.js` viejo. *Fix propuesto:* al conectar, comparar ambas y si difieren forzar
`skipWaiting` + recarga — **de paso cierra H3 casi entero**.

## H5 · Dos mecanismos distintos para ocultar pantallas
**abierto · v1.9.2**

`showInstallScreen` usa `hidden`, pero `#app-ui` tiene `.flex` (gana el autor);
`showPairingScreen` lo esquiva con `style.display`. Uno de los dos va a fallar en algun estado.

## H22 · La «×» de borrar esta siempre visible en cada icono
**abierto · v1.9.2**

`frontend/app.js:788-802` agrega el boton de borrar u ocultar **sin modo edicion**: cada icono
lo lleva permanentemente. Sale en todas las capturas del sitio. Ruido visual en la primera
impresion del producto; no bloquea nada funcional.

## H21 · El `theme-color` no refresca en vivo en iOS ≥16
**abierto · sin fecha — sin workaround conocido**

En iPhone 12 hay que cerrar y reabrir la PWA para que la barra de estado cambie de color; en
iPhone 8+ (iOS <16) si funciona en vivo. Lo reescribe `app.js:174` y Safari 16+ no re-evalua
ese meta. **Aparecio al sacar `viewport-fit=cover`** (T-79): sin `cover`, el `theme-color`
pasa a pintar la barra de estado y recien ahi se nota.

## H11 · `PLACEHOLDER-PADDLE` sin completar
**abierto · se cierra con el alta en Paddle (USER §U2)**
`grep -rn PLACEHOLDER-PADDLE` lista lo pendiente. Los valores estan vacios **a proposito**,
con fallback seguro: sin URL configurada no se anuncia compra.

## H20 · El correo con la clave no toma el nombre corregido
**abierto · va con Paddle**
`stripe-webhook` ya dice el nombre correcto en el repo, pero **no surte efecto hasta
redesplegar la Edge Function** (USER §CONTRATO: editarlas en el repo no las despliega).

## Menores, sin fecha
- **H1** cold-start de voz: deja de reproducirse, no se hace keep-alive.
- **H2** Whisper alucina con silencio → descartar audios <~1 s **antes de facturar**.
- **H3** el OTA actualiza al cerrar/reabrir la PWA, no sola. Aceptado; lo aliviaria H12.
- **H4** falta el intent "volumen al maximo" (hoy sube un paso).
- **auth.py:89** `verify_access` compara con `==` y no con `hmac.compare_digest`, mientras que
  `/api/pair` (`main.py:327`) si lo usa. Canal temporal en LAN, riesgo remoto muy bajo, pero
  es una inconsistencia entre dos comparaciones de secreto en el mismo servicio. *Auditor.*
- **Fuentes duplicadas:** `space-grotesk-bold.woff2` y `-regular.woff2` son **el mismo
  archivo** (mismo sha256). Google Fonts devuelve una variable font para ambos pesos. Efecto
  seguro: ~19 KB descargados dos veces y precacheados dos veces. **Sin verificar** si ademas
  rompe el peso 700 — hace falta un navegador. *Auditor.*
- **`Depends: build-essential`** en el `.deb`: arrastra un toolchain de compilacion completo a
  un electrodomestico de usuario final. *Auditor.*
- **`install.sh` imprime el token de emparejamiento en claro** en el mensaje final; queda en el
  scrollback de la terminal. *Auditor.*

---

# ✅ CERRADOS (desde 1.9.x)

## B1 · El HUD se corria en iPhone al reabrir la app
**CERRADO en 1.9.1 (T-79) · certificado en device, iPhone 8+ y 12**

**Causa real:** `viewport-fit=cover` en el meta viewport. Con `cover` + `theme-color`, iOS
**duplica `safe-area-inset-top` al REABRIR** la PWA — por eso no salia en el primer arranque
sino tras varios. En iPhone 8+ tapaba los botones de abajo; en el 12 solo dejaba una banda.

**Resuelto** sacando el atributo. Los cinco usos de `env(safe-area-inset-*)` degradan limpio:
dos tienen `max()` con fallback y en los otros tres el 0 es el valor correcto, porque sumar
padding sobre un viewport que iOS ya inseteo era justamente lo que duplicaba el inset.
**El porque completo esta comentado en `frontend/index.html`**, que es donde lo va a leer quien
intente "ordenarlo" y volver a ponerlo.

**T-77 no era el arreglo:** re-leia la altura tres veces al volver del segundo plano
(`updateAppHeightSettled`, nacio ahi). Viajo en 1.9.0 y no alcanzo porque atacaba el sintoma.
Se dejo: no molesta y cubre otros casos.

**Efecto colateral aceptado:** H21.

**La leccion, que costo un ciclo entero:** el arreglo lo encontro el agente del HTPC, **lo
aplico al equipo de pruebas y no declaro que habia editado el producto**. El ciclo dio 6/6 con
B1 en verde — sobre un equipo parcheado a mano, mientras el paquete publicado seguia con el
bug. Se detecto **abriendo el `.deb`** en vez de creerle al reporte. De ahi salieron dos
guardas permanentes: el campo obligatorio "¿tocaste algun archivo del producto?" en el reporte,
y **TESTING §M3**, que verifica con `dpkg -V` que el equipo ES el paquete **antes** de que la
prueba de iPhone cuente.

## B18 · El boton "Actualizar" fallaba con un log ajeno en /tmp
**CERRADO en 1.9.1 (T-78)**

`backend/main.py` abria `/tmp/lrp-update.log` en modo **append** antes de lanzar el
actualizador. Si el archivo pertenecia a otro usuario, el `open()` lanzaba, el endpoint
devolvia 500 y **el boton fallaba sin lanzar nada**.

**Resuelto** usando `subprocess.DEVNULL`: el script del actualizador ya redirige su propia
salida, asi que el backend no necesitaba abrir nada. Gemini encontro que el endpoint del panel
de la TV tenia el bug identico, fuera del alcance del brief.

**Menos grave de lo que se creyo, y conviene dejarlo derecho:** el backend corre como usuario
normal (`install.sh`: `User=$TARGET_USER`) y abria en modo append, que exige **escritura**. O
sea que **solo disparaba si el archivo YA existia y no era escribible por ese usuario** —
tipicamente porque alguien corrio `sudo lrp-update` a mano antes de T-77, cuando el script
escribia ese log como root. **En una instalacion nueva el archivo no existe, `open` lo crea y
nunca falla: ningun comprador lo habria visto.**

**La leccion:** se declaro "no peligroso" mirando solo el `exec` del script. Un mismo recurso
tocado desde dos lados solo se entiende mirando los dos.

## H6 · `bootstrap.sh` quedo roto al privatizar el repo
**CERRADO en 1.9.1 (T-80)**

Instalaba clonando desde GitHub; al privatizar, esa URL da 404 para cualquiera.
**Resuelto** borrandolo, junto con su mencion en el README y la variable muerta `GITHUB_REPO`.
*Dato que aparecio al auditarlo:* **se venia empaquetando en el `.deb`** — `build_deb.sh` copia
`scripts/` entera y su lista de exclusiones nunca lo incluyo —, o sea que vivia en
`/opt/linuxremoteplayer/scripts/` de cada usuario. `dpkg` lo borra al actualizar.

## B1b · `gracias.html` publicaba el gmail personal del dueño
**CERRADO — ya usaba `support@linuxremoteplayer.com` cuando se fue a verificar (31/07)**
Se arreglo en algun punto sin registrarlo. Queda como recordatorio de que **un item cerrado
sin anotarlo se sigue arrastrando como abierto** y consume atencion en cada revision.
