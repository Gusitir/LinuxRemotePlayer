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

Con 1.8.11 instalado y funcionando:

```bash
cat /opt/linuxremoteplayer/VERSION
sudo lrp-update
sleep 60
cat /opt/linuxremoteplayer/VERSION
systemctl is-active linuxremoteplayer
tail -30 /tmp/lrp-update.log
```

| Resultado | Significa |
|---|---|
| `1.8.12` + **`active`** | **B9 CERRADO.** El OTA funciona de punta a punta. Se puede lanzar |
| `1.8.12` + `inactive` | El arreglo no sirvio. **NO SE LANZA.** Pegar el log completo y parar |
| la version no cambia | Otro problema. Parar y reportar |

**Esta vez no hay excusa preparada:** en el ciclo anterior el fallo era esperado porque
corria el script viejo. Ahora corre el nuevo. Si queda `inactive`, es una falla real.

- [ ] **S1**

## ⛔ S2 · La actualizacion NO limpio nada  🤖 agente

Inmediatamente despues de S1, sin reiniciar ni tocar nada:

```bash
ls -l /etc/udev/rules.d/99-uinput.rules
sudo ufw status | grep 8000
systemctl is-enabled sleep.target
ls -l /opt/linuxremoteplayer/backend/.env /opt/linuxremoteplayer/backend/.pairing_token
ls -d /opt/linuxremoteplayer/backend/certs
```

**Todo tiene que seguir existiendo.** Si algo desaparecio, el guard del `prerm` fallo:
**parar toda la matriz y avisar** — significaria que cada actualizacion rompe la
configuracion de todos los equipos.

- [ ] **S2**

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

Esperado: servicio `active`, los dos targets `masked`, la CA con **sufijo nuevo y distinto
de `d98ec4ef`** (los certificados se borraron en S3, asi que nace una CA nueva), y
`verify` en `OK`.

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
