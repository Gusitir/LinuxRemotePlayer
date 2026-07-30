# INSTRUCCIONES PARA EL AGENTE DE PRUEBAS DEL HTPC — ciclo 1.8.12

Sos un agente con acceso a shell **en el HTPC de pruebas de LinuxRemotePlayer** (Debian con
systemd, Plasma Bigscreen). Tu trabajo es **ejecutar una matriz de pruebas y reportar lo que
pasa**. No sos quien arregla.

Este archivo es autocontenido: no necesitas leer nada mas del repositorio.

> **Ciclo anterior (1.8.11): 9 de 9.** El reporte fue bueno y encontro cosas que la matriz
> no pedia. Dos correcciones que salieron de ahi ya estan aplicadas en estas instrucciones.

---

## LAS 5 REGLAS. Romper una invalida el reporte.

1. **NO MODIFIQUES CODIGO NI ARCHIVOS DEL PRODUCTO.** Ni para arreglar algo roto, ni para
   probar una hipotesis. Este equipo recibe actualizaciones que **pisan cualquier cambio
   local**, asi que un arreglo tuyo desaparece *y* hace que la prueba siguiente mida algo
   que no existe en el producto. Si ves la causa de un fallo, **escribila en el reporte**:
   eso es lo valioso. No se toca nada bajo `/opt/linuxremoteplayer/`.
   **Si necesitas una excepcion, pedila y declarala en el reporte** — en el ciclo anterior
   se hizo asi y estuvo bien.

2. **Evidencia literal o no cuenta.** Pega la salida REAL, completa, tal como salio. Si no
   corriste el comando, no lo reportes. Nada de "deberia funcionar" ni resumenes.

3. **Ante un resultado inesperado, PARA y reporta.** Varias pruebas son destructivas y
   tienen un orden; improvisar puede dejar el equipo en un estado del que no sabes volver.

4. **Lo que no podes ver, lo declaras** (`[NO VERIFICABLE: motivo]`). Nunca lo des por
   bueno. Si una prueba quedo contaminada por algo previo, decilo — eso paso en el ciclo
   anterior y fue lo correcto.

5. **Respeta el orden: S1 → S2 → S3 → S4.** S3 desinstala el producto.

---

## Contexto minimo

- Servicio: `linuxremoteplayer.service` (systemd, a nivel sistema)
- Archivos: `/opt/linuxremoteplayer/`
- API local: `https://localhost:8000`, **certificado autofirmado** → todo `curl` lleva `-k`
- **El endpoint de salud es `/health`, NO `/api/health`** (eso daba 404 en el ciclo anterior;
  era un error de las instrucciones, no del producto).
- El token de acceso vive en **`/opt/linuxremoteplayer/backend/.pairing_token`**, no en el
  `.env` (correccion del ciclo anterior):

```bash
TOKEN=$(sudo cat /opt/linuxremoteplayer/backend/.pairing_token)
echo "token leido: ${TOKEN:0:6}…"
```

**Que se prueba:** el equipo tiene **1.8.11** y se publico **1.8.12**. La version 1.8.11 fue
la primera con el actualizador corregido, asi que **esta actualizacion es la primera que lo
ejecuta**. Ese es el objetivo del ciclo.

---

# S1 · ⛔ LA PRUEBA PRINCIPAL — el OTA tiene que reiniciar el servicio

```bash
cat /opt/linuxremoteplayer/VERSION
systemctl is-active linuxremoteplayer
sudo lrp-update
sleep 60
cat /opt/linuxremoteplayer/VERSION
systemctl is-active linuxremoteplayer
tail -30 /tmp/lrp-update.log
```

**Contexto que necesitas para interpretarlo:** el actualizador llama a `apt-get install`, y
ese paquete **reescribe el propio actualizador mientras corre**. Antes eso lo mataba antes
de reiniciar el servicio. La correccion envuelve todo en funciones para que el script se lea
entero en memoria antes de ejecutarse.

| Resultado | Que significa |
|---|---|
| `1.8.12` + **`active`** | **La correccion funciona.** Es el resultado que se busca |
| `1.8.12` + `inactive` | **FALLA REAL.** Pega el log completo y PARA. No sigas con S2 |
| la version no cambia | Otro problema. PARA y reporta |

> En el ciclo anterior este item fallo **a proposito** y estaba avisado, porque corria el
> script viejo. **Esta vez no.** Si queda `inactive`, es una falla y bloquea el lanzamiento.

Si quedo `inactive` y necesitas seguir para reportar mas cosas, levantalo a mano y decilo:
`sudo systemctl start linuxremoteplayer`

---

# S2 · ⛔ La actualizacion no debe haber borrado nada

Inmediatamente despues de S1, sin reiniciar ni tocar nada:

```bash
ls -l /etc/udev/rules.d/99-uinput.rules
sudo ufw status | grep 8000
systemctl is-enabled sleep.target
sudo ls -l /opt/linuxremoteplayer/backend/.env /opt/linuxremoteplayer/backend/.pairing_token
sudo ls -d /opt/linuxremoteplayer/backend/certs
```

**Los cinco tienen que SEGUIR EXISTIENDO.**

> Si algo desaparecio: **PARA TODA LA MATRIZ Y REPORTA YA**. Significaria que una
> actualizacion normal borra la configuracion del sistema y las credenciales del usuario.
> Es el peor fallo posible del producto.

Comproba tambien que el servicio responde:

```bash
curl -sk https://localhost:8000/health
TOKEN=$(sudo cat /opt/linuxremoteplayer/backend/.pairing_token)
curl -sk -H "X-Auth-Token: $TOKEN" https://localhost:8000/api/config
curl -sk -o /dev/null -w "docs: %{http_code}\n" https://localhost:8000/docs
```

`/docs` tiene que dar **404**: un 200 expondria el mapa de la API en la red local.

---

# S3 · ⛔ DESTRUCTIVO — `apt remove` tiene que limpiar de verdad

**No empieces si S1 o S2 quedaron con algo pendiente.**

Antes de desinstalar, dejá constancia de que existen:

```bash
sudo ls -l /opt/linuxremoteplayer/backend/.env /opt/linuxremoteplayer/backend/.pairing_token
sudo ls -d /opt/linuxremoteplayer/backend/certs
ls -l /usr/local/share/ca-certificates/lrp-ca.crt
```

Desinstala y comproba:

```bash
sudo apt remove -y linuxremoteplayer
echo "---- despues ----"
sudo ls -l /opt/linuxremoteplayer/backend/.env 2>&1
sudo ls -l /opt/linuxremoteplayer/backend/.pairing_token 2>&1
sudo ls -d /opt/linuxremoteplayer/backend/certs 2>&1
ls -l /usr/local/share/ca-certificates/lrp-ca.crt 2>&1
ls -l /etc/udev/rules.d/99-uinput.rules 2>&1
sudo ufw status | grep 8000
systemctl is-enabled sleep.target 2>&1
dpkg -l | grep linuxremoteplayer
```

**Los CUATRO primeros tienen que DESAPARECER**: `.env`, `.pairing_token`, el directorio
`certs/` (contiene **claves privadas**) y la CA del almacen de confianza del sistema.
Hasta esta version sobrevivian los tres ultimos — ese es justo el arreglo que se prueba.

Tambien: la regla udev borrada, `ufw` sin la regla 8000, `sleep.target` ya no `masked`, y
`dpkg -l` sin dejar el paquete en `iF` ni `iU`.

**No borres nada a mano en este paso.** Si algo sobrevive, es el hallazgo.

---

# S4 · Reinstalar y que todo vuelva

```bash
curl -fsSL https://www.linuxremoteplayer.com/install.sh | sudo bash
```

Es interactivo. Responde: usuario **el que propone**, PC dedicada a la TV **s**,
deshabilitar suspension **s**, teclado **2 (ES)**.

**Anota si se ejecuto de corrido hasta el final** — en una version anterior se cortaba a la
mitad y dejaba al usuario ante un cursor mudo.

```bash
cat /opt/linuxremoteplayer/VERSION
systemctl is-active linuxremoteplayer
systemctl is-enabled sleep.target suspend.target
sudo openssl x509 -in /opt/linuxremoteplayer/backend/certs/ca.pem -noout -subject
sudo grep -c "BEGIN CERTIFICATE" /opt/linuxremoteplayer/backend/certs/cert.pem
sudo openssl verify -CAfile /opt/linuxremoteplayer/backend/certs/ca.pem \
     /opt/linuxremoteplayer/backend/certs/cert.pem
```

**Esperado:** servicio `active`, los dos targets `masked`, `cert.pem` con **2** certificados,
`verify` en `OK`, y la CA con un sufijo **NUEVO y distinto de `d98ec4ef`** (el del ciclo
anterior). Como S3 borro los certificados, tiene que nacer una CA nueva — si sale el mismo
sufijo, los certificados no se borraron y hay que reportarlo.

---

# FORMATO DEL REPORTE

Un bloque por item:

```
### S_  —  [OK] | [FALLA] | [NO VERIFICABLE: motivo]
Comando:
<tal cual>
Salida REAL:
<pegada completa, sin editar>
Observacion: <solo si hay algo que decir>
```

Y al cerrar:

```
### RESUMEN
Version antes: ____  despues: ____
S1 ____  S2 ____  S3 ____  S4 ____
¿El servicio se reinicio SOLO tras el OTA?  SI / NO   <-- lo que decide si se lanza
Hallazgos fuera de la matriz:
```

**Si algo te resulta ambiguo, reportalo como ambiguo.** Vale mas que una conjetura prolija:
quien lee esto no puede ver la maquina.

---

# LO QUE NO PODES PROBAR — no lo intentes

Necesitan el iPhone del dueño y los hace el:

- que el **microfono** aparezca en la app
- el **icono y el rotulo "LRP"** en la pantalla de inicio
- el **espacio extra bajo la barra de estado** al reabrir la app (falla conocida, sin
  arreglo — no hace falta reportarla)
- que el navegador **acepte el certificado** tras reinstalar
- la **prueba de voz real** (hablarle al microfono)
