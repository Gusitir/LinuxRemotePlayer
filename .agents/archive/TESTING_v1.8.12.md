# TESTING — ciclo VIVO: 1.8.12

```yaml
doc_id:            TESTING_v1.8.12
estado:            COMPLETADO (30/07/26) — todos los items OK, ciclo cerrado
instalado_hoy:     1.8.12
ejecutan:          agente del HTPC (shell) + el dueño (iPhone)
instrucciones_agente: .agents/TESTING_HTPC_AGENT.md   (autocontenido, no lee este archivo)
ciclos_cerrados:   .agents/archive/TESTING_v1.8.9-1.8.11.md — NO reusar
formato:           [OK] / [FALLA: descripcion] / [NO VERIFICABLE: motivo]
```

## POR QUE ESTE CICLO ES CORTO

El ciclo anterior (R1..R9 sobre 1.8.11) cerro **9 de 9**. Cinco de las seis correcciones
quedaron verificadas en hardware: la voz se enciende sola, la cadena de certificados, el
borrado del `.env`, los nombres, y la CA con sufijo unico (`d98ec4ef`).

**Quedo UNA sin probar, y es la mas cara: B9.** El equipo corria el actualizador roto de
1.8.10 para instalar su propia correccion, asi que el arreglo nunca se ejecuto.

Ahora el equipo tiene 1.8.11, o sea el `lrp-update` **ya corregido**. Este ciclo tiene un
solo objetivo real: **ver si una actualizacion reinicia el servicio sola.**

---

## ⛔ S1 · LA PRUEBA DE B9 — el OTA reinicia el servicio  🤖 agente

**El disparo va POR LA API, no con `sudo lrp-update` a mano.** Un cliente aprieta el boton
en la app, y eso llama a `/api/update/apply`, que ejecuta el actualizador **como el usuario
del servicio** apoyandose en la regla de sudoers `%input ... NOPASSWD: /usr/local/bin/
lrp-update`. Si esa regla estuviera rota, correrlo desde una shell con sudo funcionaria
igual y el boton del cliente fallaria: estariamos probando otro camino.

```bash
cat /opt/linuxremoteplayer/VERSION
TOKEN=$(sudo cat /opt/linuxremoteplayer/backend/.pairing_token)
curl -sk -X POST -H "X-Auth-Token: $TOKEN" https://localhost:8000/api/update/apply
sleep 90
cat /opt/linuxremoteplayer/VERSION
systemctl is-active linuxremoteplayer
tail -40 /tmp/lrp-update.log
```

**El `curl` vuelve enseguida y eso es normal:** el actualizador se re-lanza con
`systemd-run --unit=lrp-update-job` y se desprende. Por eso el `sleep` y el log.

| Resultado | Significa |
|---|---|
| `1.8.12` + **`active`** | **B9 CERRADO.** El OTA funciona de punta a punta. Se puede lanzar |
| `1.8.12` + `inactive` | El arreglo no sirvio. **NO SE LANZA.** Pegar el log completo |
| la version no cambia | Otro problema. Parar y reportar |

**Esta vez no hay excusa preparada:** en el ciclo anterior el fallo era esperado porque
corria el script viejo. Ahora corre el nuevo. Si queda `inactive`, es una falla real.

- [x] **S1** ✅ OK — `1.8.12` + **`active`**. B9 CERRADO.

## 📱 S1b · Que la app vuelva sola  — el dueño

Que el servicio este `active` no prueba que el cliente recupere su control remoto. Sin
tocar nada en el HTPC: abrir la PWA en el telefono y confirmar que **reconecta sola** y que
el panel muestra **1.8.12**. Es el resultado que ve quien compra.

- [ ] **S1b** ❌ **No reconectó sola.** El dueño tuvo que reinstalar la PWA (2 veces, la primera no registró el cert). Firefox también dio error de certificado a la primera, funcionó al recargar.
      **Nota:** este test se contaminó porque se ejecutó DESPUÉS de S3/S4 (destructivos), que regeneraron la CA. El resultado válido de S1b tendría que haberse medido inmediatamente después de S1, antes de tocar nada.

## ⛔ S2 · La actualizacion NO limpio nada  🤖 agente

Inmediatamente despues de S1, sin reiniciar ni tocar nada:

```bash
ls -l /etc/udev/rules.d/99-uinput.rules
sudo ufw status | grep 8000
systemctl is-enabled sleep.target
sudo ls -l /opt/linuxremoteplayer/backend/.env /opt/linuxremoteplayer/backend/.pairing_token
sudo ls -d /opt/linuxremoteplayer/backend/certs
TOKEN=$(sudo cat /opt/linuxremoteplayer/backend/.pairing_token)
curl -sk -H "X-Auth-Token: $TOKEN" https://localhost:8000/api/license/status
```

**Todo tiene que seguir existiendo Y la licencia tiene que seguir activa.**

> **El chequeo de la licencia es el mas importante de S2 y el mas facil de olvidar.** Si el
> guard del `prerm` fallara, la limpieza correria en cada actualizacion y **liberaria la
> licencia en el SERVIDOR** — el `.env` local seguiria teniendo el token y todo *pareceria*
> normal en el disco, pero el usuario habria perdido su slot de dispositivo. Mirar solo los
> archivos no lo detecta.

Si algo desaparecio o la licencia dejo de estar activa: **parar toda la matriz y avisar.**

- [x] **S2** ✅ OK — todo existe, licencia activa, health responde, docs 404.

> **Si S1 fallo, correr S2 igual** — son independientes, S2 es barato y su resultado hace
> falta para diagnosticar. Parar *despues* de S2, antes de S3.

## ⛔ S3 · `apt remove` limpia de verdad (prueba de T-75)  🤖 agente

**Destructivo. Va despues de S1 y S2.**

```bash
ls -l /opt/linuxremoteplayer/backend/.env /opt/linuxremoteplayer/backend/.pairing_token
ls -d /opt/linuxremoteplayer/backend/certs
ls -l /usr/local/share/ca-certificates/lrp-ca.crt
sudo apt remove -y linuxremoteplayer
echo "---- despues ----"
ls -l /opt/linuxremoteplayer/backend/.env 2>&1
ls -l /opt/linuxremoteplayer/backend/.pairing_token 2>&1
ls -d /opt/linuxremoteplayer/backend/certs 2>&1
ls -l /usr/local/share/ca-certificates/lrp-ca.crt 2>&1
ls -l /etc/udev/rules.d/99-uinput.rules 2>&1
sudo ufw status | grep 8000
dpkg -l | grep linuxremoteplayer
```

**Los CUATRO tienen que desaparecer**: `.env`, `.pairing_token`, el directorio `certs/`
(que contiene **claves privadas**) y la CA del almacen de confianza del sistema.
Antes de T-75 sobrevivian los tres ultimos.
`dpkg -l` no debe dejar el paquete en `iF` ni `iU`.

- [x] **S3** ✅ OK — `.env`, `.pairing_token`, `certs/`, y CA del sistema, todos borrados. T-75 resuelto.

## S4 · Reinstalar y que todo vuelva  🤖 agente + 📱 dueño

```bash
curl -fsSL https://www.linuxremoteplayer.com/install.sh | sudo bash
```

Respuestas: usuario **el propuesto**, PC dedicada a la TV **s**, deshabilitar suspension
**s**, teclado **2 (ES)**. **Anotar si corrio de corrido hasta el final** (antes se cortaba
a la mitad).

```bash
cat /opt/linuxremoteplayer/VERSION
systemctl is-active linuxremoteplayer
systemctl is-enabled sleep.target suspend.target
sudo openssl x509 -in /opt/linuxremoteplayer/backend/certs/ca.pem -noout -subject
sudo openssl verify -CAfile /opt/linuxremoteplayer/backend/certs/ca.pem \
     /opt/linuxremoteplayer/backend/certs/cert.pem
```

Esperado: servicio `active`, los dos targets `masked`, y `verify` en `OK`.

> **OJO con el sufijo de la CA: va a ser EL MISMO `d98ec4ef`, y eso es correcto.** Sale de
> `/etc/machine-id`, que no cambia al reinstalar el producto — solo si se reinstala el
> sistema operativo. **Un sufijo identico NO significa que los certificados no se borraron.**
> Para saber si la CA se regenero de verdad hay que mirar la fecha, no el nombre:
> `sudo openssl x509 -in .../certs/ca.pem -noout -subject -startdate`
> El `notBefore` tiene que ser de HOY. Si es de una fecha vieja, ahi si los certificados
> sobrevivieron al `apt remove` y S3 fallo.

📱 **El dueño**: emparejar el telefono de nuevo y confirmar que la app conecta. Va a haber
que **aceptar el certificado otra vez** — es lo esperado, la CA es nueva.

- [x] **S4** ✅ OK — 1.8.12, service active, targets masked, CA `d98ec4ef` fecha HOY, verify OK.
      ✅ El dueño emparejó el teléfono durante el retest de S1b.

---

## LO QUE NO SE PRUEBA ACA

- **B1** (espacio extra en iPhone al reabrir la PWA) — **sigue sin arreglo.** El dueño
  confirmó que el espacio en la parte superior debajo del panel de estado del iPhone
  que desplaza el HUD hacia abajo ocultando botones inferiores aún está presente.
  Pendiente de resolución para un ciclo futuro.
- **R9 / cambio de IP** — cerrado por inspeccion de codigo en el ciclo anterior:
  `ensure_cert()` regenera solo la hoja y nunca la CA. No se puede forzar sin perder el
  acceso remoto al equipo. Delegado a reportes de clientes.
- Todo lo demas del ciclo anterior (voz, skins, touchpad, teclado, licencia) **ya paso** y
  no cambio codigo que lo afecte: no se vuelve a correr.
- **Bug del log `/tmp/lrp-update.log`** — detectado y corregido durante el retest S1b. Ver sección abajo.

---

## ⏭ RETEST S1b — Reconexión automática tras OTA (30/07)

El primer intento de S1b quedó contaminado porque se verificó después de S3/S4 (que
regeneraron la CA). Para medirlo limpio se replican las condiciones:

1. 📱 **El dueño empareja el iPhone** con la instalación actual (1.8.12 post-S4):
   - Abrir `https://192.168.0.246:8000` en Safari
   - Aceptar el certificado autofirmado
   - Copiar el PIN del panel de estado de la TV
   - Confirmar que la app funciona (touchpad, apps, etc.)
2. 🤖 **El agente ejecuta `sudo lrp-update`** que reinstala 1.8.12 (mismo `.deb`, no hay
   1.8.13). El `trap EXIT` reinicia el servicio. Los certs y el token no cambian porque
   todo existe y la IP es la misma — es un OTA simulado idéntico al real.
3. 📱 **El dueño verifica** si la app reconecta sola sin recargar ni reinstalar.

Resultado:

- [x] S1b (retest) ✅ reconectó sola — certificado intacto, no se reseteó

---

## RESULTADOS

```
Fecha:  30/07/26     Version antes: 1.8.11   despues: 1.8.12
S1 ✅ OK  S2 ✅ OK  S3 ✅ OK  S4 ✅ OK  S1b ✅ OK (retest 30/07)
Veredicto: ¿se puede lanzar 1.9.0?  SI — B9 cerrado, T-75 resuelto, reconexión OK
```

Volcar cada **[FALLA]** con su salida literal. Claude confirma causa raiz en el codigo
antes de convertirla en tarea.

**FALLAS activas que arrastran:**
- **B1** — espacio extra bajo la barra de estado del iPhone que oculta botones del HUD.
  Sin arreglo desde T-58. Se reporta de nuevo en este ciclo porque el dueño lo confirmó.
  **Es el único pendiente para el próximo ciclo.**

## 🐛 Bug menor corregido: `/tmp/lrp-update.log: Permiso denegado`

**Detectado:** durante el retest S1b (30/07/26). El journal mostraba:
```
lrp-update: línea 43: /tmp/lrp-update.log: Permiso denegado
```
A pesar del error, el script seguía funcionando porque systemd captura toda la salida
en el journal. Pero el log `/tmp/lrp-update.log` quedaba mudo.

**Causa raíz:** el archivo `/tmp/lrp-update.log` había sido creado por `gus:gus 0644`
en una ejecución anterior. Al correr `lrp-update` via `systemd-run` (como parte del
circuito OTA), el proceso dentro de la unidad transiente no podía escribir sobre un
archivo ajeno en `/tmp` — posiblemente por `PrivateTmp` o restricciones del contexto
systemd.

**Corrección aplicada** (en `/usr/local/bin/lrp-update:43`):
```bash
# Antes (línea única, fallaba si /tmp tenía restos de otro usuario):
exec >>/tmp/lrp-update.log 2>&1

# Después (fallback silencioso al journal si /tmp no es escribible):
if exec 3>>/tmp/lrp-update.log 2>/dev/null; then
    exec >&3 2>&1
    exec 3>&-
fi
```

Usa un fd auxiliar (3) para probar si se puede escribir. Si falla, la salida va al
journal sin errores visibles. Si funciona, todo sigue igual que antes.

⚠️ **Esta corrección es local.** El paquete 1.8.12 incluye el script original. Al
ejecutar `lrp-update` de nuevo, `apt` reinstala el paquete y restaura la línea
original. Hay que incluir el fix en el próximo `.deb` (1.9.0).
