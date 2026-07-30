# INSTRUCCIONES PARA EL AGENTE DE PRUEBAS DEL HTPC

Sos un agente con acceso a shell **en el HTPC de pruebas de LinuxRemotePlayer** (Debian con
systemd, Plasma Bigscreen). Tu trabajo es **ejecutar una matriz de pruebas y reportar lo que
pasa**. No sos quien arregla.

Este archivo es autocontenido: no necesitas leer el resto del repositorio.

---

## LAS 5 REGLAS. Romper una invalida todo el reporte.

1. **NO MODIFIQUES CODIGO. NUNCA.** Ni para arreglar algo que veas roto, ni para "probar
   una hipotesis". Este equipo recibe actualizaciones automaticas que **pisan cualquier
   cambio local**, asi que un arreglo tuyo desaparece sin dejar rastro y ademas hace que la
   proxima prueba mida algo que no existe en el producto. Si ves la causa de un fallo,
   **escribila en el reporte**. Eso es lo valioso.
   Archivos que NO se tocan: cualquier cosa bajo `/opt/linuxremoteplayer/`.

2. **Evidencia literal o no cuenta.** Pega la salida REAL de cada comando, completa, tal
   como salio. Si un comando no lo corriste, no lo reportes. Nada de "deberia funcionar",
   "parece que anda" ni resumenes de lo que esperabas ver.

3. **Ante un resultado inesperado, PARA y reporta.** No improvises pasos que no estan aca.
   Muchas de estas pruebas son destructivas y en cierto orden; salirse del guion puede
   dejar el equipo en un estado del que no sabes volver.

4. **Lo que no podes ver, lo declaras.** Varios items necesitan un iPhone que no controlas.
   Marcalos `[NO VERIFICABLE: necesita el telefono]`. **Jamas los des por buenos.**

5. **Respeta el orden.** La seccion D destruye la instalacion. Todo lo demas va antes.

---

## Contexto minimo

- Servicio: `linuxremoteplayer.service` (systemd, a nivel sistema)
- Archivos: `/opt/linuxremoteplayer/` — backend, frontend, scripts, certificados
- API local: `https://localhost:8000` con **certificado autofirmado** → todos los `curl`
  llevan `-k`
- Los endpoints protegidos piden la cabecera `X-Auth-Token`. El token esta en el `.env`:

```bash
TOKEN=$(grep -E '^PAIRING_TOKEN=' /opt/linuxremoteplayer/backend/.env | cut -d= -f2- | tr -d "\"'")
echo "token leido: ${TOKEN:0:6}…"
```

**Que se esta probando:** la version instalada es **1.8.10** y tiene seis fallas conocidas.
Se publico **1.8.11** con las correcciones. Esta matriz comprueba que funcionaron.

---

# SECCION A — Antes de tocar nada: foto del estado actual

Corre esto y pega la salida. Es la linea de base contra la que se compara todo despues.

```bash
cat /opt/linuxremoteplayer/VERSION
systemctl is-active linuxremoteplayer
ls -l /etc/udev/rules.d/99-uinput.rules
sudo ufw status | grep 8000
systemctl is-enabled sleep.target
ls -l /opt/linuxremoteplayer/backend/.env
grep -c '^ENABLE_VOICE' /opt/linuxremoteplayer/backend/.env
sudo openssl x509 -in /opt/linuxremoteplayer/backend/certs/ca.pem -noout -subject
```

**Esperado:** version `1.8.10`, servicio `active`, la regla udev existe, UFW muestra
`8000/tcp`, `sleep.target` dice `masked`, el `.env` existe.
El `subject` de la CA probablemente diga `CN=LinuxRemotePlayer CA` **sin sufijo** — eso es
correcto para 1.8.10 y es justo lo que tiene que cambiar despues.

---

# SECCION B — La actualizacion (lo mas importante de toda la matriz)

## B-1 · Lanzar el OTA

```bash
sudo lrp-update
sleep 45
cat /opt/linuxremoteplayer/VERSION
systemctl is-active linuxremoteplayer
tail -40 /tmp/lrp-update.log
```

**Que esperar — LEELO ANTES DE ALARMARTE:**

- La version **tiene que pasar a 1.8.11**.
- **Es MUY PROBABLE que el servicio quede `inactive`, y eso NO es una falla nueva.** El
  equipo corre el actualizador de 1.8.10, que tiene un defecto conocido: se sobrescribe a
  si mismo mientras corre y muere antes de reiniciar el servicio. La correccion viaja
  DENTRO de 1.8.11, o sea que recien se aplica en la actualizacion siguiente.
- Anota exactamente **cual de los dos casos ocurrio**. Los dos son resultados validos:
  - servicio `active` → el arreglo se aplico antes de lo previsto, excelente
  - servicio `inactive` → esperado; levantalo y segui:

```bash
sudo systemctl start linuxremoteplayer
systemctl is-active linuxremoteplayer
```

**Si la version NO cambio a 1.8.11: PARA.** Es otro problema y hay que reportarlo antes de
seguir.

## B-2 · ⛔ La actualizacion NO debe haber borrado nada

**Este es el item mas critico de la matriz.** Corre exactamente los mismos comandos de la
seccion A:

```bash
ls -l /etc/udev/rules.d/99-uinput.rules
sudo ufw status | grep 8000
systemctl is-enabled sleep.target
ls -l /opt/linuxremoteplayer/backend/.env
grep -E '^LICENSE_TOKEN' /opt/linuxremoteplayer/backend/.env | cut -c1-25
```

**Los cinco tienen que seguir IGUAL que en la seccion A.**

> **Si alguno desaparecio, PARA TODA LA MATRIZ Y REPORTA INMEDIATAMENTE.** Significaria que
> una actualizacion normal borra la configuracion del sistema y libera la licencia del
> usuario. Es el peor fallo posible del producto y no tiene sentido seguir probando.

---

# SECCION C — Voz y certificados (no destructivo)

## C-1 · ⛔ La voz se enciende sola

En 1.8.10 habia que editar el `.env` a mano. Ahora el backend deberia encenderla al
arrancar si ya hay una licencia.

```bash
grep -E '^ENABLE_VOICE|^LICENSE_TOKEN' /opt/linuxremoteplayer/backend/.env | cut -c1-25
TOKEN=$(grep -E '^PAIRING_TOKEN=' /opt/linuxremoteplayer/backend/.env | cut -d= -f2- | tr -d "\"'")
curl -sk -H "X-Auth-Token: $TOKEN" https://localhost:8000/api/config
```

**Esperado:** hay `LICENSE_TOKEN`, aparece `ENABLE_VOICE=true` en el `.env` **sin que nadie
lo haya escrito a mano**, y el JSON trae `"voice_enabled": true`.

## C-2 · Apagar la voz y que siga apagada tras reiniciar

El usuario tiene que poder desactivarla, y un reinicio **no debe volver a prenderla**.

```bash
TOKEN=$(grep -E '^PAIRING_TOKEN=' /opt/linuxremoteplayer/backend/.env | cut -d= -f2- | tr -d "\"'")
curl -sk -X POST -H "X-Auth-Token: $TOKEN" -H "Content-Type: application/json" \
     -d '{"enabled": false}' https://localhost:8000/api/voice/toggle
grep -E '^ENABLE_VOICE' /opt/linuxremoteplayer/backend/.env
sudo systemctl restart linuxremoteplayer && sleep 8
grep -E '^ENABLE_VOICE' /opt/linuxremoteplayer/backend/.env
curl -sk -H "X-Auth-Token: $TOKEN" https://localhost:8000/api/config
```

**Esperado:** tras el reinicio el `.env` **sigue en `false`** y el JSON dice
`"voice_enabled": false`.
**Si volvio a `true`, es una FALLA:** el usuario no podria apagar la voz nunca.

Dejala como estaba al terminar:

```bash
curl -sk -X POST -H "X-Auth-Token: $TOKEN" -H "Content-Type: application/json" \
     -d '{"enabled": true}' https://localhost:8000/api/voice/toggle
```

## C-3 · El certificado ahora lleva sufijo y la cadena esta completa

```bash
sudo openssl x509 -in /opt/linuxremoteplayer/backend/certs/ca.pem -noout -subject
sudo grep -c "BEGIN CERTIFICATE" /opt/linuxremoteplayer/backend/certs/cert.pem
sudo openssl verify -CAfile /opt/linuxremoteplayer/backend/certs/ca.pem \
     /opt/linuxremoteplayer/backend/certs/cert.pem
```

**Ojo:** los certificados solo se regeneran si no existen o si cambio la IP. Como este
equipo ya los tiene, **es esperado que el `subject` siga SIN sufijo** — la CA no se rehace
en una actualizacion. Eso se prueba de verdad en la seccion D, tras reinstalar.
Lo que **si** tiene que cumplirse ya: `cert.pem` con **2** certificados y `verify` diciendo
`OK`.

## C-4 · El nombre en el menu de aplicaciones

```bash
grep -E '^Name=|^Comment=' /usr/share/applications/linuxremoteplayer-panel.desktop
grep -E '"name"|"short_name"' /opt/linuxremoteplayer/frontend/manifest.json
```

**Esperado:** `Name=LinuxRemotePlayer` (una sola palabra, en ese orden),
`"name": "LinuxRemotePlayer"` y `"short_name": "LRP"`.

## C-5 · Regresion basica del servicio

```bash
curl -sk https://localhost:8000/api/health
curl -sk https://localhost:8000/api/status | head -c 400
sudo systemctl status linuxremoteplayer --no-pager | head -12
```

## C-6 · La documentacion tecnica NO debe estar publica

```bash
curl -sk -o /dev/null -w "%{http_code}\n" https://localhost:8000/docs
curl -sk -o /dev/null -w "%{http_code}\n" https://localhost:8000/openapi.json
```

**Esperado: 404 en los dos.** Un `200` es una FALLA: expondria el mapa completo de la API a
cualquiera en la red local.

---

# SECCION D — DESTRUCTIVA. Va al final, y solo si A/B/C terminaron.

> A partir de aca **se desinstala el producto**. No empieces esta seccion si quedo algo
> pendiente arriba.

## D-1 · ⛔ Desinstalar tiene que limpiar de verdad

```bash
grep -E '^LICENSE_TOKEN|^PAIRING_TOKEN' /opt/linuxremoteplayer/backend/.env | cut -c1-25
sudo apt remove -y linuxremoteplayer
echo "---- estado despues ----"
ls -l /etc/udev/rules.d/99-uinput.rules 2>&1
sudo ufw status | grep 8000
systemctl is-enabled sleep.target 2>&1
ls -l /opt/linuxremoteplayer/backend/.env 2>&1
dpkg -l | grep linuxremoteplayer
```

**Esperado:**
- la regla udev **no existe**
- `ufw status | grep 8000` **vacio**
- `sleep.target` **ya no** dice `masked`
- el `.env` **no existe** ← esto es nuevo en 1.8.11; en 1.8.10 sobrevivia con las credenciales
- `dpkg -l` **no** debe mostrar el paquete en estado `iF` ni `iU` (medio roto)

**Ademas comproba esto, que es un hallazgo conocido sin arreglo todavia** — reportá lo que
salga, no lo corrijas:

```bash
ls -l /usr/local/share/ca-certificates/lrp-ca.crt 2>&1
```

**Se espera que SIGA EXISTIENDO.** La desinstalacion no lo borra: `install.sh` copia la CA
al almacen de confianza del sistema y ningun script la saca despues. Confirmalo y anotalo.

## D-2 · Borrar la CA vieja y reinstalar

**Este paso va ANTES de reinstalar y es imprescindible.** Si no se hace, el equipo se queda
con la CA de la instalacion anterior y no se puede saber si la correccion funciono:
cualquier error de certificado seria atribuible a la CA vieja y no al codigo nuevo.

```bash
sudo rm -f /usr/local/share/ca-certificates/lrp-ca.crt
sudo update-ca-certificates --fresh
ls -l /usr/local/share/ca-certificates/lrp-ca.crt 2>&1
```

**Esperado:** el `ls` final tiene que decir que **no existe**.

Recien ahora, reinstalar:

```bash
curl -fsSL https://www.linuxremoteplayer.com/install.sh | sudo bash
```

El instalador es interactivo y va a hacer preguntas. Respondelas asi: usuario **el que
propone por defecto**, PC dedicada a la TV **s**, deshabilitar suspension **s**, teclado
**2 (ES)**.

**Anota si el instalador se ejecuto de corrido hasta el final.** En una version anterior se
cortaba a la mitad y dejaba al usuario ante un cursor mudo; deberia estar corregido.

Cuando termine:

```bash
cat /opt/linuxremoteplayer/VERSION
systemctl is-active linuxremoteplayer
sudo openssl x509 -in /opt/linuxremoteplayer/backend/certs/ca.pem -noout -subject
sudo grep -c "BEGIN CERTIFICATE" /opt/linuxremoteplayer/backend/certs/cert.pem
sudo openssl verify -CAfile /opt/linuxremoteplayer/backend/certs/ca.pem \
     /opt/linuxremoteplayer/backend/certs/cert.pem
```

**Esperado — este es el objetivo de la seccion:** el `subject` de la CA ahora tiene que ser
`CN=LinuxRemotePlayer CA <8 caracteres>`, **con sufijo**. Si sigue sin sufijo, la correccion
no funciono y hay que reportarlo.
Ademas: `cert.pem` con 2 certificados y `verify` en `OK`.

## D-3 · El desinstalador manual

```bash
sudo /opt/linuxremoteplayer/scripts/uninstall.sh
```

Responde **y** a la confirmacion. **No debe imprimir** "se omite la limpieza de sistema" —
ese mensaje significaria que el script de limpieza no se pudo ejecutar.

Despues volve a instalar con el mismo comando de D-2 y deja el equipo funcionando.

---

# FORMATO DEL REPORTE

Un bloque por item, en el orden en que los corriste:

```
### <ID del item>  —  [OK] | [FALLA] | [NO VERIFICABLE: motivo]

Comando:
<lo que ejecutaste, tal cual>

Salida REAL:
<pegada completa, sin editar>

Observacion: <solo si hay algo que decir>
```

Y al final:

```
### RESUMEN
Version antes: ____   Version despues: ____
Balance: __ OK · __ FALLA · __ NO VERIFICABLE
El servicio quedo: active / inactive
Fallas encontradas, en una linea cada una:
```

**Si algo te resulta ambiguo, reportalo como ambiguo.** Vale mucho mas que una conjetura
prolija: quien lee este reporte no puede ver la maquina y va a decidir en base a lo que
escribas.

---

# LO QUE VOS **NO** PODES PROBAR — no lo intentes, ya esta cubierto

Estos items necesitan el iPhone del dueño y los hace el:

- que el **microfono aparezca** en la app tras la actualizacion
- el **icono y el rotulo "LRP"** en la pantalla de inicio del telefono
- el **espacio extra bajo la barra de estado** al reabrir la app (falla conocida, sin
  arreglo todavia — no hace falta reportarla)
- que **Firefox deje de mostrar el error de certificado** tras reinstalar
- la **prueba de voz real** (hablarle al microfono)
