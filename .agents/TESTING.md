# TESTING — ciclo VIVO: 1.8.12

```yaml
doc_id:            TESTING_v1.8.12
estado:            esperando el .deb de 1.8.12 (T-76, bloqueada hasta que entre T-75)
instalado_hoy:     1.8.11
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

- [ ] **S1**

## 📱 S1b · Que la app vuelva sola  — el dueño

Que el servicio este `active` no prueba que el cliente recupere su control remoto. Sin
tocar nada en el HTPC: abrir la PWA en el telefono y confirmar que **reconecta sola** y que
el panel muestra **1.8.12**. Es el resultado que ve quien compra.

- [ ] **S1b**

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

- [ ] **S2**

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

- [ ] **S3**

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

- [ ] **S4**

---

## LO QUE NO SE PRUEBA ACA

- **B1** (espacio extra en iPhone al reabrir la PWA) — sin arreglo todavia, va a fallar
  igual. No hace falta reportarlo.
- **R9 / cambio de IP** — cerrado por inspeccion de codigo en el ciclo anterior:
  `ensure_cert()` regenera solo la hoja y nunca la CA. No se puede forzar sin perder el
  acceso remoto al equipo. Delegado a reportes de clientes.
- Todo lo demas del ciclo anterior (voz, skins, touchpad, teclado, licencia) **ya paso** y
  no cambio codigo que lo afecte: no se vuelve a correr.

---

## RESULTADOS

```
Fecha:  __/__/__     Version antes: ____   despues: ____
S1 ____  S2 ____  S3 ____  S4 ____
Veredicto: ¿se puede lanzar 1.9.0?  SI / NO
```

Volcar cada **[FALLA]** con su salida literal. Claude confirma causa raiz en el codigo
antes de convertirla en tarea.
