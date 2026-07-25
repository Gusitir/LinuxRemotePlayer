# TESTING — ciclo v1.8.9 (OTA desde 1.8.0)

```yaml
doc_id: TESTING_v1.8.9
date: 2026-07-24
author: Claude (arma la matriz) — EJECUTA EL DUEÑO en HTPC + teléfono; Gemini corrige
matriz_anterior: .agents/archive/TESTING_v1.7.md (ciclo v1.7.0, CERRADO — no reusar)
formato_resultado: marcar cada ítem [OK] / [FALLA: descripción] / [SKIP: motivo]
  y volcar los FALLA en RESULTADOS al final. Claude los tría y los convierte en tareas.
entorno_ref: HTPC Plasma Bigscreen (Wayland, Debian-based) + teléfono del dueño.
prioridad: ⛔ bloquea el lanzamiento v1.9.0 · ⚠️ importante · (sin marca) deseable
```

## QUÉ VA ACÁ Y QUÉ NO
- **Acá**: pruebas que se hacen EN EL DEVICE (HTPC + teléfono). Las ejecutás vos.
- **NO acá**: tareas operativas fuera del device (comprar el dominio, deployar una Edge
  Function, sacar screenshots). Esas viven en **CHECKLIST DEL DUEÑO** de `CURRENT.md`.
- **Por qué esta matriz es nueva**: la v1.7 quedó cerrada. Desde el 1.8.0 (lo último
  validado en device) entraron ai-proxy, licencia de 1 dispositivo, cuota 60, skins
  nuevas y logo nuevo. **Nada de eso se probó sobre un .deb publicado.**

---

## A. OTA Y ARRANQUE — hacer esto PRIMERO

- [ ] ⛔ **A1.** Ajustes → Buscar actualización → ofrece **1.8.9** → Actualizar → el
      servicio se reinicia y la app reconecta sola, sin tocar la terminal.
      (Es el pipeline que va a usar cada cliente que compre.)
- [ ] ⛔ **A2.** Tras el OTA, **cerrar y reabrir la PWA**: tiene que aparecer el logo
      nuevo y el tema claro. Si seguís viendo el logo viejo (el control remoto azul), el
      service worker no invalidó la caché → FALLA grave, anotarlo.
- [ ] **A3.** `curl -s https://linux-remote-player.vercel.app/latest.json`
      → `"version": "1.8.9"` y sha `890211c8...bf87c`.
- [ ] **A4.** El panel de la TV muestra la versión **1.8.9**.
- [ ] **A5.** `systemctl status linuxremoteplayer` → activo tras el update. Reboot →
      arranca solo.

## B. SKINS Y LOGO (T-58 — NUNCA se probó en device)

- [ ] ⛔ **B1. El notch del iPhone.** Abrir la PWA **instalada** (standalone, desde el
      icono, no desde Safari). La barra de estado NO debe tapar el engranaje de Ajustes
      ni el título, y no debe quedar una banda blanca rara arriba.
      *Por qué*: cambié `apple-mobile-web-app-status-bar-style` de `black-translucent` a
      `default`, porque con fondo crema el texto blanco de la barra quedaba invisible.
      **Es el único cambio de T-58 que no pude verificar sin hardware.**
- [ ] ⛔ **B2. Icono en la pantalla de inicio** = logo nuevo (cuadro oscuro con puntitos
      y triángulo verde). Si aparece una "R" o el control viejo: borrar la PWA,
      reinstalarla y volver a mirar. Anotar modelo + SO + navegador.
- [ ] ⚠️ **B3. Migración de tema.** Tras el OTA el tema debe quedar en **Day** (claro)
      **sin** que salte el aviso "requiere licencia pro". Con licencia Pro activa, el
      tema oscuro que tenías debe pasar a **Night** (navy), no a claro.
- [ ] **B4.** Cambiar entre Day / Night / Café / Anime → aplica al instante y **persiste**
      tras cerrar y reabrir la app.
- [ ] ⚠️ **B5. Probar de noche, con la luz apagada.** Usar la app 2 minutos con el tema
      Day mientras mirás algo en la TV. Esto es un mando a distancia: se usa a oscuras, y
      una pantalla crema a pantalla completa puede encandilar. Si molesta, decilo — se
      evalúa volver a Night por defecto o cambiar según la hora. **No es una falla de
      código, es una decisión de producto que solo se puede tomar usándola.**
- [ ] **B6.** En cada skin, que no haya texto ilegible: botones de acento (Enter, Done,
      Añadir, Activar), el estado "Conectado", y los textos de Ajustes.

## C. VOZ VÍA AI-PROXY (revalidar sobre el .deb publicado)

- [ ] ⛔ **C1.** Comando en **español**: "pon youtube" → transcribe y abre. Sin llaves de
      IA en el device (ahora pasa por el proxy).
- [ ] ⛔ **C2.** Comando en **INGLÉS**: "play youtube" → funciona.
      *Por qué es ⛔*: el prompt bilingüe (T-53d) nunca se confirmó, **y la web ya vende
      la voz en inglés** ("AI voice control in English and Spanish"). Si esto falla, hay
      una promesa publicada sin respaldo.
- [ ] **C3.** Cold start: el primer comando tras varias horas de inactividad tarda unos
      segundos (hallazgo conocido: Edge Function dormida + Whisper frío). **Anotar cuántos
      segundos** — ese número decide si vale la pena un keep-alive.
- [ ] **C4.** Contabilidad: dar exactamente 3 comandos, después en Supabase
      `select commands_today from licenses where token = '<tu key>';` → subió exactamente 3.
- [ ] ⚠️ **C5. Kill-switch.** En el SQL editor:
      `update service_state set value = jsonb_set(value,'{enabled}','false') where key='voice';`
      → la voz responde con un error claro y la app NO se rompe.
      **Revertir a `true` al terminar** (si no, quedás sin voz).
- [ ] **C6.** `grep -iE "CLOUD_|TOGETHER" /opt/linuxremoteplayer/backend/.env`
      → **sin llaves de IA** (deben vivir solo en los secrets de Supabase).
- [ ] **C7.** Whisper con silencio: apretar el micro sin hablar → hoy inventa texto y
      ejecuta algo raro (hallazgo conocido, no es regresión). Confirmar que sigue igual
      para dimensionar el arreglo.

## D. LICENCIA DE 1 DISPOSITIVO

- [ ] ⛔ **D1.** Activar la licencia desde el móvil → "activada", aparece el micrófono,
      y el panel de la TV dice Pro sin reiniciar nada.
- [ ] ⚠️ **D2. Mudanza.** Activar la MISMA key en otra PC → debe preguntar "¿Mudar la key
      acá? El otro dispositivo perderá el premium" → confirmar → la primera PC pierde Pro.
- [ ] **D3.** Gracia offline: cortar internet del HTPC (no la LAN) → el estado Pro
      aguanta (cache 72h). La voz NO (necesita nube, es esperado).

## E. DESINSTALACIÓN — ⚠️ HAY UN BUG YA CONFIRMADO EN CÓDIGO

**No hace falta probar para saberlo** (verificado leyendo el `prerm` del .deb el
2026-07-24): `sudo apt remove linuxremoteplayer` **solo para y deshabilita el servicio**.
NO libera la licencia, NO borra la regla de UFW, NO borra la regla de udev y NO
desenmascara la suspensión. Las cuatro cosas sí las hace `scripts/uninstall.sh`, que
`apt remove` nunca ejecuta — y `website/docs.html` (ES y EN) promete las cuatro.
→ Ya está anotado como hallazgo en CURRENT.md; necesita tarea antes del lanzamiento.

- [ ] **E1.** *(Cuando esté el fix)* `sudo apt remove linuxremoteplayer` y después:
      `systemctl is-enabled sleep.target` → no masked ·
      `ufw status | grep 8000` → vacío ·
      `ls /etc/udev/rules.d/99-uinput.rules` → no existe ·
      y la key queda libre para activar en otra PC sin pasar por la mudanza.
- [ ] **E2.** Reinstalar tras desinstalar → todo vuelve a funcionar.

## F. REGRESIÓN DEL NÚCLEO (1.8.9 tocó TODO el frontend + la voz del backend)

- [ ] ⛔ **F1.** Emparejar por PIN desde un teléfono nuevo (o borrando datos del sitio).
- [ ] ⛔ **F2.** Touchpad: mover, tap = clic izq, long-press = clic der, scroll lateral.
- [ ] **F3.** Teclado latam, escribir en un editor del HTPC:
      `hola/mundo @correo.com (test) & "ok" ¿? ; : + * _ =` → exacto.
- [ ] **F4.** Volumen +/−, mute, y ⏯ ⏮ ⏭ en un kiosk de YouTube.
- [ ] **F5.** Apps: lanzar una nativa (Dolphin) y una web; abrir "Más apps".
- [ ] **F6.** Panel /status en el HTPC → SIN advertencia de certificado.
- [ ] **F7.** Reconexión: apagar la pantalla del teléfono 2 min → encender → reconecta
      sola en <5s, sin recargar.
- [ ] **F8.** Modo D-Pad: flechas + Enter + Esc en una app leanback.

## G. ARRASTRES DE LA MATRIZ v1.7 (siguen sin cerrar)

- [ ] **G1.** 2-3 teléfonos conectados a la vez (faltaba un segundo dispositivo).
- [ ] **G2.** Cambio de IP del HTPC → el certificado y el panel siguen sin advertencia.
- [ ] **G3.** ¿Sigue el favicon basura al añadir una app web, y el logo de LRP colándose
      en una app del sistema?
- [ ] **G4.** Backlog visual: el header dice "Remote Linux Player" (orden invertido) y
      "Okular" aparece duplicado en las apps detectadas.

---

## RESULTADOS

```
Fecha ejecución: __/__/__  |  Balance: __ OK · __ FALLA · __ SKIP
Veredicto del dueño:
```

Volcar acá cada **[FALLA]** con su descripción. Claude las tría (causa raíz confirmada en
código ANTES de crear tarea — regla 10) y las convierte en tareas del plan de la fase.
