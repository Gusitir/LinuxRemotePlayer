# TESTING — ciclo VIVO: 1.9.0 (el LANZAMIENTO)

```yaml
doc_id:      TESTING_v1.9.0
estado:      esperando el .deb de 1.9.0
instalado:   1.8.12 (build de prueba)
ejecutan:    agente del HTPC (shell) + el dueño (iPhone)
agente:      .agents/TESTING_HTPC_AGENT.md — autocontenido, no lee este archivo
cerrados:    archive/TESTING_v1.8.9-1.8.11.md · archive/TESTING_v1.8.12.md — NO reusar
formato:     [OK] / [FALLA: descripcion] / [NO VERIFICABLE: motivo]
```

## POR QUE ESTE CICLO ES CORTO

Tres ciclos previos ya validaron en hardware lo que importaba: **el OTA reinicia el
servicio**, la desinstalacion limpia de verdad, la voz se enciende sola, la CA no colisiona,
la PWA reconecta. Nada de eso cambio.

**Lo nuevo de 1.9.0 es: el arreglo de B1 (iPhone), el log del actualizador, y la web
corregida.** Eso es lo que hay que mirar — mas una regresion minima de que nada se rompio.

---

## ⛔ L1 · El OTA sigue funcionando  🤖 agente

Disparado **por la API**, como lo haria un cliente:

```bash
cat /opt/linuxremoteplayer/VERSION
TOKEN=$(sudo cat /opt/linuxremoteplayer/backend/.pairing_token)
curl -sk -X POST -H "X-Auth-Token: $TOKEN" https://localhost:8000/api/update/apply
sleep 90
cat /opt/linuxremoteplayer/VERSION
systemctl is-active linuxremoteplayer
```

Esperado: **1.9.0 + `active`**. Ya paso en el ciclo anterior; aca solo se confirma que no
hubo regresion.

- [ ] **L1**

## ⛔ L2 · B1 — el HUD ya no se corre en iPhone  📱 el dueño

**Es el motivo principal de este ciclo.** Con la PWA instalada (standalone, desde el icono):

1. Abrirla. Mirar que el HUD arranque bien.
2. **Cerrarla del todo** (sacarla del selector de apps) y volver a abrirla. Repetir **4 o 5
   veces** — el bug no aparecia en el primer arranque sino tras varios.
3. Rotar el telefono y volver a vertical.

Esperado: **nunca** aparece una banda extra bajo la barra de estado, y **los botones de
abajo siguen accesibles**. Probar en **los dos telefonos** (iPhone 8+ y 12): el 8+ ocultaba
botones, el 12 solo mostraba el espacio.

- [ ] **L2 · iPhone 8+**
- [ ] **L2 · iPhone 12**

## L3 · El log del actualizador ya no queda mudo  🤖 agente

```bash
ls -l /var/log/lrp-update.log
sudo tail -20 /var/log/lrp-update.log
```

Esperado: el archivo existe y tiene la salida del OTA de L1. (Antes se escribia en `/tmp` y
quedaba mudo si otro usuario habia creado el archivo.)

- [ ] **L3**

## L4 · La web ya no vende como Pro lo que es gratis  📱 el dueño

En `https://www.linuxremoteplayer.com` y en `/en/`: la seccion de temas y la de precios **no
deben decir que Night, Café o Anime son Pro**. Son gratis desde T-62.

- [ ] **L4**

## L5 · Regresion minima  🤖 agente + 📱 dueño

🤖 Por shell:

```bash
TOKEN=$(sudo cat /opt/linuxremoteplayer/backend/.pairing_token)
curl -sk https://localhost:8000/health
curl -sk -H "X-Auth-Token: $TOKEN" https://localhost:8000/api/config
curl -sk -H "X-Auth-Token: $TOKEN" https://localhost:8000/api/license/status
curl -sk -o /dev/null -w "docs: %{http_code}\n" https://localhost:8000/docs
sudo openssl verify -CAfile /opt/linuxremoteplayer/backend/certs/ca.pem \
     /opt/linuxremoteplayer/backend/certs/cert.pem
```

Esperado: health OK, licencia activa, voz encendida, **docs 404**, verify OK.

📱 El dueño, 5 minutos de uso normal: touchpad, teclado, lanzar una app, un comando de voz,
cambiar de tema. Solo se busca que nada se haya roto.

- [ ] **L5**

---

## NO SE PRUEBA ACA

- **H19 · el QR lleva a una pagina "Offline"** — sin arreglar, va a fallar igual.
- **Cambio de IP** — cerrado por inspeccion en un ciclo anterior; no se puede forzar sin
  perder el acceso remoto.
- Todo lo validado en los ciclos 1.8.11 y 1.8.12 que no cambio codigo: no se repite.

---

## RESULTADOS

```
Fecha:  __/__/__     Version antes: 1.8.12   despues: ____
L1 ____  L2(8+) ____  L2(12) ____  L3 ____  L4 ____  L5 ____
Veredicto: ¿1.9.0 queda como version comercial?  SI / NO
```

Volcar cada **[FALLA]** con su salida literal. Claude confirma causa raiz en el codigo antes
de convertirla en tarea.
