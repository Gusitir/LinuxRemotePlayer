# INSTRUCCIONES PARA EL AGENTE DE PRUEBAS DEL HTPC — ciclo 1.9.0

Sos un agente con acceso a shell **en el HTPC de pruebas de LinuxRemotePlayer** (Debian con
systemd, Plasma Bigscreen). Ejecutas una matriz de pruebas y reportas lo que pasa.
**No sos quien arregla.** Este archivo es autocontenido.

> **Ciclos anteriores: 9/9 y 4/4.** Los reportes fueron buenos: encontraron cosas fuera de la
> matriz y, sobre todo, **detectaron cuando una prueba propia habia quedado contaminada** en
> vez de dar el resultado por bueno. Eso es exactamente lo que se busca.

---

## LAS 5 REGLAS

1. **NO MODIFIQUES CODIGO NI ARCHIVOS DEL PRODUCTO.** Ni para arreglar algo roto ni para
   probar una hipotesis. Este equipo recibe actualizaciones que **pisan cualquier cambio
   local**, asi que un parche tuyo desaparece *y* hace que la prueba siguiente mida algo que
   no existe en el producto. Si ves la causa de un fallo, **escribila en el reporte**: eso
   vale mas que el parche. Nada bajo `/opt/linuxremoteplayer/`.
   **Si necesitas una excepcion, pedila y declarala** — en ciclos anteriores se hizo asi.
2. **Evidencia literal o no cuenta.** Salida REAL, completa. Si no lo corriste, no lo
   reportes.
3. **Ante un resultado inesperado, PARA y reporta.** No improvises pasos que no estan aca.
4. **Lo que no podes ver, lo declaras** (`[NO VERIFICABLE: motivo]`). Y si una prueba quedo
   contaminada por algo previo, **decilo** — eso ya paso y fue lo correcto.
5. **Orden: L1 → L3 → L5.** Este ciclo NO tiene pasos destructivos.

---

## Contexto minimo

- Servicio: `linuxremoteplayer.service` (systemd, a nivel sistema)
- API local `https://localhost:8000`, **certificado autofirmado** → todo `curl` con `-k`
- Endpoint de salud: **`/health`** (no `/api/health`)
- Token: **`/opt/linuxremoteplayer/backend/.pairing_token`** (no esta en el `.env`)

```bash
TOKEN=$(sudo cat /opt/linuxremoteplayer/backend/.pairing_token)
```

**Que se prueba:** el equipo tiene **1.8.12** y se publico **1.9.0**, que es la **version
comercial**. Los arreglos grandes ya se validaron en ciclos anteriores; aca se confirma que
nada se rompio y que entraron los tres cambios nuevos.

---

# L1 · ⛔ El OTA sigue funcionando

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

Esperado: **`1.9.0` + `active`**. Esto ya funciono en el ciclo anterior; si ahora falla, es
una **regresion** y bloquea el lanzamiento — pega el log y PARA.

---

# L3 · El log del actualizador ya no queda mudo

Hasta 1.8.12 el log iba a `/tmp/lrp-update.log` y quedaba mudo si ese archivo lo habia
creado otro usuario. Ahora deberia estar en `/var/log`, que es root-only.

```bash
ls -l /var/log/lrp-update.log
sudo tail -20 /var/log/lrp-update.log
ls -l /tmp/lrp-update.log 2>&1
```

Esperado: `/var/log/lrp-update.log` **existe y tiene la salida del OTA de L1**. El de `/tmp`
puede seguir ahi de antes; solo anota si quedo o no.

---

# L5 · Regresion minima

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

# FORMATO DEL REPORTE

```
### L_  —  [OK] | [FALLA] | [NO VERIFICABLE: motivo]
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
L1 ____  L3 ____  L5 ____
¿El servicio se reinicio SOLO tras el OTA?  SI / NO
Hallazgos fuera de la matriz:
```

**Si algo te resulta ambiguo, reportalo como ambiguo.** Quien lee esto no puede ver la
maquina y decide con lo que escribas.

---

# LO QUE NO PODES PROBAR — es del dueño, con el iPhone

- **El arreglo del HUD (L2), que es el motivo principal de este ciclo**: hay que abrir y
  cerrar la PWA varias veces y ver si aparece una banda extra bajo la barra de estado.
- El texto de la web sobre los temas (L4).
- La prueba de voz real y el uso general de 5 minutos.
