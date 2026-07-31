# TESTING — ciclo VIVO: 1.9.1

```yaml
doc_id:      TESTING_v1.9.1
estado:      SIN EJECUTAR
instalado:   el HTPC viene de 1.9.0 (PARCHEADO A MANO — ver M3)
publicado:   1.9.1 — LIVE, verificado contra el dominio el 30/07
ejecutan:    agente del HTPC (shell) + el dueño (iPhone)
agente:      .agents/TESTING_HTPC_AGENT.md — autocontenido, no lee este archivo
cerrados:    archive/TESTING_v1.9.0.md — NO reusar. Su L2 dio ✅ sobre un equipo
             parcheado a mano, no sobre un paquete: por eso existe este ciclo.
formato:     [OK] / [FALLA: descripcion] / [NO VERIFICABLE: motivo]
```

## POR QUE ESTE CICLO EXISTE

**El ciclo de 1.9.0 no certifico nada de iPhone.** Su L2 se probo sobre el HTPC con
`index.html` editado a mano, asi que midio codigo que no estaba en el paquete. El paquete
1.9.0 salio con el bug adentro.

1.9.1 lleva el arreglo de verdad (T-79) mas el del boton "Actualizar" (T-78). **Este ciclo
es corto: solo mide lo que 1.9.1 cambia, sobre el `.deb` REAL.**

---

## ⛔ M1 · El OTA lleva el equipo de 1.9.0 a 1.9.1  🤖 agente

```bash
cat /opt/linuxremoteplayer/VERSION
TOKEN=$(sudo cat /opt/linuxremoteplayer/backend/.pairing_token)
curl -sk -X POST -H "X-Auth-Token: $TOKEN" https://localhost:8000/api/update/apply
sleep 90
cat /opt/linuxremoteplayer/VERSION
systemctl is-active linuxremoteplayer
```

Esperado: **1.9.1 + `active`**.

> **Si devuelve error 500 o el boton falla, NO es una regresion: es B18**, el bug que 1.9.1
> viene a arreglar. La 1.9.0 instalada todavia lo tiene, asi que se manifiesta al
> actualizar DESDE ella. *Salida:* `sudo rm -f /tmp/lrp-update.log` y reintentar.
> **Anotalo si pasa** — confirma B18 en vivo. A partir de 1.9.1 no deberia repetirse.

- [ ] **M1**

## ⛔ M2 · B1 — el HUD ya no se corre en iPhone, AHORA sobre el paquete  📱 el dueño

**Es el unico item que decide algo.** Correr DESPUES de M1 (el equipo tiene que estar en
1.9.1) y **borrar la PWA del telefono y reinstalarla** antes de probar, para no arrastrar el
cache viejo.

1. Instalar la PWA desde el icono (standalone). Abrirla y mirar que el HUD arranque bien.
2. **Cerrarla del todo** (sacarla del selector de apps) y volver a abrirla. Repetir **4 o 5
   veces** — el bug no aparecia en el primer arranque sino tras varios.
3. Rotar el telefono y volver a vertical.

Esperado: **nunca** aparece una banda extra bajo la barra de estado, y **los botones de
abajo siguen accesibles**. En **los dos telefonos**: el 8+ ocultaba botones, el 12 solo
mostraba el espacio.

- [ ] **M2 · iPhone 8+**
- [ ] **M2 · iPhone 12**

## ⛔ M3 · El equipo ya no esta parcheado a mano  🤖 agente

**Sin esto, M2 no vale.** El HTPC quedo con `index.html` y `sw.js` editados durante el ciclo
anterior; el OTA de M1 tiene que haberlos pisado.

```bash
sudo dpkg -V linuxremoteplayer
grep -n viewport /opt/linuxremoteplayer/frontend/index.html
```

Esperado: `dpkg -V` **sin salida** (ningun archivo alterado), y el `grep` mostrando la
etiqueta viewport **sin `viewport-fit=cover`** — que ahora viene asi de fabrica, no
parcheada.

- [ ] **M3**

## M4 · El boton "Actualizar" ya no depende de `/tmp`  🤖 agente

```bash
grep -rn "/tmp/lrp-update.log" /opt/linuxremoteplayer/backend/ ; echo "salida: $?"
ls -l /var/log/lrp-update.log
```

Esperado: el `grep` **no encuentra nada** (T-78), y el log del actualizador vive en
`/var/log` con la salida del OTA de M1 (T-77).

- [ ] **M4**

## M5 · Regresion minima  🤖 agente + 📱 dueño

🤖 Por shell:

```bash
TOKEN=$(sudo cat /opt/linuxremoteplayer/backend/.pairing_token)
curl -sk https://localhost:8000/health
curl -sk -H "X-Auth-Token: $TOKEN" https://localhost:8000/api/config
curl -sk -H "X-Auth-Token: $TOKEN" https://localhost:8000/api/license/status
curl -sk -o /dev/null -w "docs: %{http_code}\n" https://localhost:8000/docs
```

Esperado: health OK, licencia activa, voz encendida, **docs 404**.

📱 El dueño, 5 minutos de uso normal: touchpad, teclado, lanzar una app, un comando de voz,
cambiar de tema. Solo se busca que nada se haya roto.

- [ ] **M5**

---

## NO SE PRUEBA ACA

- **H21 · el `theme-color` no refresca en vivo en iOS >=16** — conocido y aceptado. Si al
  cambiar de tema en el iPhone 12 la barra de estado no cambia hasta cerrar y reabrir, **es
  esto y NO es un fallo**. En iPhone 8+ si cambia en vivo.
- **H19 · el QR lleva a "Offline"** — sin arreglar, va a fallar igual.
- Todo lo validado en 1.9.0 que no cambio codigo (L1/L3/L5 dieron OK): no se repite.

---

## RESULTADOS

```
Fecha:  __/__/__     Version antes: 1.9.0   despues: 1.9.1
M1 __  M2(8+) __  M2(12) __  M3 __  M4 __  M5 __
¿B1 CERRADO?  (solo si M2 pasa en los DOS telefonos Y M3 dio sin salida)
```

Volcar cada **[FALLA]** con su salida literal. Claude confirma causa raiz en el codigo antes
de convertirla en tarea.
