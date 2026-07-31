# TESTING — ciclo VIVO: 1.9.1

```yaml
doc_id:      TESTING_v1.9.1
estado:      COMPLETADO (30/07/26) — todos los items OK, ciclo cerrado
instalado:   1.9.1 (via OTA desde el boton de la app)
publicado:   1.9.1 — LIVE, verificado contra el dominio el 30/07
ejecutan:    agente del HTPC (shell) + el dueño (iPhone)
cerrados:    archive/TESTING_v1.9.0.md — NO reusar. Su L2 dio ✅ sobre un equipo
             parcheado a mano, no sobre un paquete: por eso existe este ciclo.
formato:     [OK] / [FALLA: descripcion] / [NO VERIFICABLE: motivo]
```

## COMO SE USA ESTE ARCHIVO

- **El dueño marca los resultados acá** (§MATRIZ y §RESULTADOS). Este es su archivo.
- **Al agente del HTPC se le entrega el §BLOQUE PARA EL AGENTE tal cual**, copiado entre sus
  marcas. Es autocontenido a proposito: ese agente **no lee el repo**.
- **Los comandos de shell viven UNICAMENTE en ese bloque.** La matriz de arriba dice que se
  prueba y que significa pasar, pero no repite ningun comando.
  *Antes eran dos archivos y el mismo id `L5` llego a significar cosas distintas en cada uno
  (el del agente corria dos chequeos extra). Por eso ahora es uno solo.*

## POR QUE ESTE CICLO EXISTE

**El ciclo de 1.9.0 no certifico nada de iPhone.** Su L2 se probo sobre el HTPC con
`index.html` editado a mano, asi que midio codigo que no estaba en el paquete. El paquete
1.9.0 salio con el bug adentro.

1.9.1 lleva el arreglo de verdad (T-79) mas el del boton "Actualizar" (T-78). **Este ciclo
es corto: solo mide lo que 1.9.1 cambia, sobre el `.deb` REAL.**

---

# MATRIZ

## ⛔ M1 · El OTA lleva el equipo de 1.9.0 a 1.9.1  🤖 agente
Pasa si: queda en **1.9.1** y el servicio sigue **active**.
> **Si da error 500, NO es una regresion: es B18**, el bug que 1.9.1 viene a arreglar. La
> 1.9.0 instalada todavia lo tiene, o sea que el equipo usa el actualizador roto para
> instalar su propia correccion. *Salida:* `sudo rm -f /tmp/lrp-update.log` y reintentar.
> **Anotalo si pasa** — confirma B18 en vivo. De 1.9.1 en adelante no deberia repetirse.

- [x] **M1** ✅ 1.9.1 + active — OTA desde el botón de la app, sin error 500 (B18 no se manifestó)

## ⛔ M2 · B1 — el HUD ya no se corre en iPhone, AHORA sobre el paquete  📱 el dueño

**Es el unico item que decide algo.** Correr **despues de M1** (el equipo tiene que estar en
1.9.1) y **borrar la PWA del telefono y reinstalarla** antes de probar: si no, el service
worker viejo puede servir el `index.html` cacheado y estarias midiendo el paquete anterior.

1. Instalar la PWA desde el icono (standalone). Abrirla y mirar que el HUD arranque bien.
2. **Cerrarla del todo** (sacarla del selector de apps) y volver a abrirla. Repetir **4 o 5
   veces** — el bug no aparecia en el primer arranque sino tras varios.
3. Rotar el telefono y volver a vertical.

Pasa si: **nunca** aparece una banda extra bajo la barra de estado y **los botones de abajo
siguen accesibles**. En **los dos telefonos**: el 8+ ocultaba botones, el 12 solo mostraba
el espacio.

- [x] **M2 · iPhone 8+**  ✅
- [x] **M2 · iPhone 12**  ✅

## ⛔ M3 · El equipo ya no esta parcheado a mano  🤖 agente
**Sin esto, M2 no vale** — habilita a M2, no es un tramite. El HTPC quedo con `index.html` y
`sw.js` editados en el ciclo anterior; el OTA de M1 tiene que haberlos pisado.
Pasa si: `dpkg -V` **no devuelve nada** y la etiqueta viewport viene **sin
`viewport-fit=cover` de fabrica**, no parcheada.

- [x] **M3** ✅ dpkg -V sin salida, viewport sin `viewport-fit=cover` (comentario del paquete)

## M4 · El boton "Actualizar" ya no depende de `/tmp`  🤖 agente
Pasa si: no queda ninguna referencia a `/tmp/lrp-update.log` en el backend (T-78) y el log
del actualizador vive en `/var/log` con la salida del OTA de M1 (T-77).

- [x] **M4** ✅ sin referencias a /tmp en backend, log en /var/log con salida del OTA

## M5 · Regresion minima  🤖 agente + 📱 dueño
🤖 Pasa si: health OK, licencia **activa**, voz **encendida**, **docs 404**, los dos targets
de suspension **masked**, la CA con sufijo y `verify` en **OK**.

📱 El dueño, 5 minutos de uso normal: touchpad, teclado, lanzar una app, un comando de voz,
cambiar de tema. Solo se busca que nada se haya roto.

- [x] **M5** ✅ shell: health OK, licencia activa, voz true, docs 404, targets masked, CA d98ec4ef, verify OK
  ✅ Dueño: 5 minutos de uso normal, todo OK

---

## NO SE PRUEBA ACA

- **H21 · el `theme-color` no refresca en vivo en iOS >=16** — conocido y aceptado. Si al
  cambiar de tema en el iPhone 12 la barra de estado no cambia hasta cerrar y reabrir, **es
  esto y NO es un fallo**. En iPhone 8+ si cambia en vivo.
- **H19 · el QR lleva a "Offline"** — sin arreglar, va a fallar igual.
- Todo lo validado en 1.9.0 que no cambio codigo (L1/L3/L5 dieron OK): no se repite.
- **Cambio de IP** — cerrado por inspeccion; no se puede forzar sin perder el acceso remoto.

---

## RESULTADOS

```
Fecha:  30/07/26     Version antes: 1.9.0   despues: 1.9.1
M1 ✅  M2(8+) ✅  M2(12) ✅  M3 ✅  M4 ✅  M5 ✅
¿B1 CERRADO?  SI — M2 pasó en los DOS telefonos y M3 dio sin salida
Veredicto: 1.9.1 certificado — B1 cerrado sobre el paquete REAL
```

Volcar cada **[FALLA]** con su salida literal. Claude confirma causa raiz en el codigo antes
de convertirla en tarea.

## REPORTE DEL AGENTE DEL HTPC (30/07/26)

<!-- Va ACA, FUERA del bloque que se le copia al agente: si vive adentro, el ciclo
     siguiente le entrega los resultados del anterior como si fueran su guion. -->

```
### RESUMEN — ciclo 1.9.1, cerrado
Version antes: 1.9.0  despues: 1.9.1
M1 OK  M2(8+) OK  M2(12) OK  M3 OK  M4 OK  M5 OK
¿El servicio se reinicio SOLO tras el OTA?  SI — journalctl mostro el mensaje del
    updater y el servicio quedo active sin intervencion
¿Hubo error 500 en M1 (bug conocido de 1.9.0)?  NO — el OTA se disparo desde el
    boton de la app en el iPhone y completo sin incidentes
¿TOCASTE algun archivo del producto?  NO
  (las ediciones manuales de `index.html`/`sw.js` del ciclo 1.9.0 las piso el OTA
   de M1 — M3 lo confirma: dpkg -V sin salida, el equipo vuelve a ser el paquete)
Hallazgos fuera de la matriz:
  - B18 no se manifesto en este OTA. (La explicacion que dio el agente estaba
    invertida; la correcta esta abajo, en la NOTA DEL AUDITOR.)
  - El boton "Actualizar" de la app mostro "Actualizando" y la app se desconecto y
    reconecto sola tras el reinicio — flujo de cliente completo OK, sin B18.
  - Desvio declarado: el OTA de M1 se disparo desde el boton de la app, no con el
    `curl` de la matriz. Es el mismo endpoint y ademas probo el camino real del
    cliente de punta a punta.
```

> ### NOTA DEL AUDITOR (30/07) — por que B18 no se disparo
> El agente lo atribuyo a que `/tmp/lrp-update.log` era **root-owned** y por eso el backend
> "pudo abrirlo". **Es al reves**, y conviene dejarlo derecho porque cambia la gravedad:
> - El backend corre como **usuario normal** (`install.sh`: `User=$TARGET_USER`), no root.
> - La 1.9.0 hacia `open("/tmp/lrp-update.log", "a")` — **append exige ESCRITURA**.
> - Un archivo de root en modo 0644 **no** es escribible por ese usuario: si hubiera sido de
>   root, el `open()` habria lanzado y **el 500 SI habria ocurrido**. Que no ocurriera prueba
>   lo contrario: el archivo era del usuario del servicio, o no existia.
> - Y con el archivo **inexistente** `open(...,"a")` lo **crea** y funciona (`/tmp` es
>   escribible por todos), asi que en un equipo nuevo B18 **nunca** se habria manifestado.
>
> **Conclusion: B18 solo se dispara si el archivo YA existe y no es escribible por el
> usuario del servicio** — tipicamente porque alguien corrio `sudo lrp-update` a mano
> ANTES de T-77, cuando el script escribia ese log como root. Eso explica de una que el
> dueño lo sufriera y el HTPC no. **El resto del reporte es solido**: declaro el campo
> obligatorio, declaro el desvio, y M3 sostiene a M2.

---
---

# ═══════ BLOQUE PARA EL AGENTE DEL HTPC — copiar DESDE ACA ═══════

Sos un agente con acceso a shell **en el HTPC de pruebas de LinuxRemotePlayer** (Debian con
systemd, Plasma Bigscreen). Ejecutas una matriz de pruebas y reportas lo que pasa.
**No sos quien arregla.** Esto es autocontenido: no necesitas leer nada mas.

> **Ciclos anteriores: 9/9, 4/4 y el de 1.9.0.** Los reportes fueron buenos: encontraron
> cosas fuera de la matriz y **detectaron cuando una prueba propia habia quedado
> contaminada** en vez de darla por buena. Eso es exactamente lo que se busca.

## LAS 5 REGLAS

1. **NO MODIFIQUES CODIGO NI ARCHIVOS DEL PRODUCTO.** Ni para arreglar algo roto ni para
   probar una hipotesis. Este equipo recibe actualizaciones que **pisan cualquier cambio
   local**, asi que un parche tuyo desaparece *y* hace que la prueba siguiente mida algo que
   no existe en el producto. Si ves la causa de un fallo, **escribila en el reporte**: eso
   vale mas que el parche. Nada bajo `/opt/linuxremoteplayer/`.
   **Si el dueño te pide expresamente que arregles algo, hacelo — pero DECLARALO**, en el
   campo obligatorio del §RESUMEN. Un arreglo sin declarar convierte cada ✅ posterior en un
   resultado falso, porque el equipo deja de ser el producto. Ya paso (ver ese campo).
2. **Evidencia literal o no cuenta.** Salida REAL, completa. Si no lo corriste, no lo
   reportes.
3. **Ante un resultado inesperado, PARA y reporta.** No improvises pasos que no estan aca.
4. **Lo que no podes ver, lo declaras** (`[NO VERIFICABLE: motivo]`).
5. **Orden: M1 → M3 → M4 → M5.** Este ciclo NO tiene pasos destructivos.

## Contexto minimo

- Servicio: `linuxremoteplayer.service` (systemd, a nivel sistema)
- API local `https://localhost:8000`, **certificado autofirmado** → todo `curl` con `-k`
- Endpoint de salud: **`/health`** (no `/api/health`)
- Token: **`/opt/linuxremoteplayer/backend/.pairing_token`** (no esta en el `.env`)

**Que se prueba:** el equipo tiene **1.9.0** y se publico **1.9.1**. Los arreglos grandes ya
se validaron en ciclos anteriores; aca se confirma que entraron los dos cambios nuevos y que
nada se rompio.

---

## M1 · ⛔ El OTA lleva el equipo a 1.9.1

**Dispara por la API, no con `sudo lrp-update`.** Un cliente aprieta un boton en la app, y
eso ejecuta el actualizador **como el usuario del servicio** via una regla de sudoers.
Correrlo desde tu shell con sudo probaria otro camino.

```bash
cat /opt/linuxremoteplayer/VERSION
systemctl is-active linuxremoteplayer
TOKEN=$(sudo cat /opt/linuxremoteplayer/backend/.pairing_token)
curl -sk -X POST -H "X-Auth-Token: $TOKEN" https://localhost:8000/api/update/apply
sleep 90
cat /opt/linuxremoteplayer/VERSION
systemctl is-active linuxremoteplayer
```

**El `curl` vuelve enseguida y eso es normal:** el actualizador se re-lanza con
`systemd-run --unit=lrp-update-job` y se desprende. Por eso el `sleep`.
Para seguirlo en vivo: `journalctl -u lrp-update-job -f`

Esperado: **`1.9.1` + `active`**.

> **Si el `curl` devuelve un error 500, NO es una regresion.** Es un bug conocido de la
> 1.9.0 instalada: el backend abria un archivo de log en `/tmp` y fallaba si lo habia creado
> otro usuario. La 1.9.1 lo arregla, pero el equipo usa el actualizador viejo para
> instalarla. **Salida:** `sudo rm -f /tmp/lrp-update.log` y volve a lanzar el `curl`.
> **Anota si te paso** — es informacion valiosa, confirma el bug en vivo.

---

## M3 · ⛔ El equipo ya no esta parcheado a mano

En el ciclo anterior se editaron a mano dos archivos del producto en este equipo. El OTA de
M1 tiene que haberlos reemplazado. **Si no, todas las pruebas de iPhone que siguen no valen.**

```bash
sudo dpkg -V linuxremoteplayer
grep -n viewport /opt/linuxremoteplayer/frontend/index.html
```

Esperado: `dpkg -V` **sin ninguna salida** (ningun archivo alterado respecto al paquete), y
el `grep` mostrando una etiqueta `<meta name="viewport" ...>` que **NO** contiene
`viewport-fit=cover`.

Si `dpkg -V` lista archivos, **PARA y reporta cuales**: significa que el OTA no piso los
parches y hay que resolver eso antes de seguir.

---

## M4 · El boton "Actualizar" ya no depende de `/tmp`

```bash
grep -rn "/tmp/lrp-update.log" /opt/linuxremoteplayer/backend/
ls -l /var/log/lrp-update.log
sudo tail -20 /var/log/lrp-update.log
```

Esperado: el `grep` **no encuentra nada**, y `/var/log/lrp-update.log` existe con la salida
del OTA de M1.

---

## M5 · Regresion minima

```bash
TOKEN=$(sudo cat /opt/linuxremoteplayer/backend/.pairing_token)
curl -sk https://localhost:8000/health
curl -sk -H "X-Auth-Token: $TOKEN" https://localhost:8000/api/config
curl -sk -H "X-Auth-Token: $TOKEN" https://localhost:8000/api/license/status
curl -sk -o /dev/null -w "docs: %{http_code}\n" https://localhost:8000/docs
systemctl is-enabled sleep.target suspend.target
sudo openssl x509 -in /opt/linuxremoteplayer/backend/certs/ca.pem -noout -subject
sudo openssl verify -CAfile /opt/linuxremoteplayer/backend/certs/ca.pem \
     /opt/linuxremoteplayer/backend/certs/cert.pem
```

Esperado: health responde · licencia **activa** · `voice_enabled` **true** · **docs 404**
(un 200 expondria el mapa de la API en la red local) · los dos targets `masked` · la CA con
sufijo · `verify` en **OK**.

> El sufijo de la CA va a ser el mismo de siempre y **eso es correcto**: sale de
> `/etc/machine-id`, que no cambia. Un OTA no regenera certificados.

---

## FORMATO DEL REPORTE

```
### M_  —  [OK] | [FALLA] | [NO VERIFICABLE: motivo]
Comando:
<tal cual>
Salida REAL:
<pegada completa, sin editar>
Observacion: <solo si hay algo que decir>
```

Y al cerrar:

```
### RESUMEN
Version antes: 1.9.0  despues: 1.9.1
M1 __  M3 __  M4 __  M5 __
¿El servicio se reinicio SOLO tras el OTA?  __
¿Hubo error 500 en M1 (bug conocido de 1.9.0)?  __

¿TOCASTE algun archivo del producto?  SI / NO      <-- OBLIGATORIO, aunque sea NO
  Si es SI, uno por linea: <ruta> — <que cambiaste> — <por que>
  Y pega la salida de:  sudo dpkg -V linuxremoteplayer

Hallazgos fuera de la matriz:
  - ...
```

> **Por que ese campo existe** (paso el 30/07/26, ciclo 1.9.0): se pidio buscar la causa de
> un bug de iPhone; el agente la encontro, **la corrigio en el equipo** y anoto la solucion —
> correcta, y validada despues en los dos telefonos. Pero **no dijo que habia editado el
> producto**, asi que el resultado se leyo como si certificara el paquete publicado, cuando
> media un equipo parcheado a mano. El auditor lo cazo abriendo el `.deb`. **El arreglo era
> bueno; lo que faltaba era una linea diciendo que existia.** Sin ese dato, un ✅ miente sin
> que nadie mienta.

---

## LO QUE NO PODES PROBAR — es del dueño, con el iPhone

- **El arreglo del HUD, que es el motivo principal de este ciclo**: hay que abrir y cerrar la
  PWA varias veces y ver si aparece una banda extra bajo la barra de estado.
- La prueba de voz real y el uso general de 5 minutos.

**Si algo te resulta ambiguo, reportalo como ambiguo.** Quien lee esto no puede ver la
maquina y decide con lo que escribas.

# ═══════ HASTA ACA ═══════
