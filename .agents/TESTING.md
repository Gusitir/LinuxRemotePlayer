# TESTING — ciclo v1.8.9/1.8.10 · CERRADO. El proximo ciclo es 1.8.11 (ver arriba de todo)

> ## ⏭ CICLO SIGUIENTE — QUE RE-TESTEAR SOBRE 1.8.11
> El ciclo de abajo YA SE EJECUTO (29/07, sobre 1.8.10) y produjo B9..B14. **Seis arreglos
> criticos (T-70..T-73) no tocaron hardware todavia.** 1.8.11 ya esta publicada (T-74,
> auditada contra el `.deb` real). Re-correr SOLO esto — lo demas del ciclo viejo sigue
> valiendo:
>
> ### QUIEN EJECUTA CADA ITEM (2026-07-30)
> El testeo del HTPC se delega a un agente con shell en esa maquina; sus instrucciones
> autocontenidas estan en **`.agents/TESTING_HTPC_AGENT.md`** (no lee este archivo).
> - 🤖 **agente del HTPC** — todo lo que se comprueba por shell. Incluye R4 y R9, que antes
>   figuraban como manuales y son automatizables via API y `nmcli`.
> - 📱 **el dueño** — lo que necesita el iPhone: no hay forma de que el agente lo vea.
> - **El agente NO toca codigo** (AGENTS.md §ROLES): un arreglo suyo lo pisa el proximo OTA
>   y encima hace que la prueba siguiente mida algo que no existe en el producto.
>
> **BORRAR LA CA VIEJA ANTES DE REINSTALAR** — no al principio, o el Firefox del propio HTPC
> queda sin CA durante el resto de las pruebas y ensucia los resultados.
> - 🤖 la del HTPC la borra **el agente**, en su seccion D-2 (ya esta en sus instrucciones).
> - 📱 el **perfil del iPhone lo borra el dueño**, antes de volver a conectar el telefono
>   tras la reinstalacion. Sin eso, el `SEC_ERROR_BAD_SIGNATURE` persiste aunque T-72 este
>   perfecto, y pareceria que el arreglo no sirvio.
>
> - [ ] ⛔ **R1 · el OTA reinicia el servicio.** Actualizar y comprobar
>       `systemctl status linuxremoteplayer` → **active**, sin tocar la terminal.
>       **ESPERADO QUE FALLE ESTA VEZ:** el equipo esta en 1.8.10 y usa su `lrp-update` roto
>       para instalar; el arreglo de B9 recien corre en el OTA SIGUIENTE. Levantarlo a mano
>       (`sudo systemctl start linuxremoteplayer`) y seguir. **El que tiene que verse verde
>       es 1.8.11 → 1.9.0.**
> - [ ] ⛔ **R2 · un OTA NO limpia nada** (era E1). Tras actualizar:
>       `ls /etc/udev/rules.d/99-uinput.rules` existe · `ufw status | grep 8000` con la regla ·
>       `systemctl is-enabled sleep.target` masked · y la app **sigue diciendo Pro**.
> - [ ] ⛔ **R3 · la voz aparece sola.** Con la licencia YA activada de antes, tras el OTA el
>       microfono tiene que estar **sin tocar el `.env` a mano** (era el bug B10).
> - [ ] **R4 · apagar y volver a encender la voz** desde la app. Al apagarla, el `.env` queda
>       en `ENABLE_VOICE=false` y **un reinicio del servicio NO debe volver a prenderla**.
> - [ ] ⛔ **R5 · `apt remove` borra el `.env`** (era E2). Despues:
>       `ls /opt/linuxremoteplayer/backend/.env` → **no existe**, y al reinstalar tiene que
>       pedir emparejar de nuevo y NO reclamar la licencia sola.
> - [ ] **R6 · certificado tras reinstalar** (era F6/B14). **ANTES de probar, borrar a mano la
>       CA vieja**: en el HTPC `sudo rm /usr/local/share/ca-certificates/lrp-ca.crt &&
>       sudo update-ca-certificates --fresh`, y en el iPhone borrar el perfil viejo. Sin eso
>       el `SEC_ERROR_BAD_SIGNATURE` persiste aunque T-72 este bien.
>       Comprobar tambien que la CA nueva tenga sufijo:
>       `openssl x509 -in /opt/linuxremoteplayer/backend/certs/ca.pem -noout -subject`
>       → tiene que decir `CN=LinuxRemotePlayer CA <8 caracteres>`.
> - [ ] **R7 · el nombre en el menu de aplicaciones** dice **LinuxRemotePlayer** (era G4/B13).
> - [ ] **R8 · el icono de la PWA**, tras borrarla y volver a agregarla, muestra el logo y el
>       rotulo **LRP** (era B2/D8).
> - [ ] **R9 · G2, cambio de IP** — se puede provocar: reservar otra IP en el DHCP del router
>       y reiniciar la red (`sudo nmcli con down <nombre> && sudo nmcli con up <nombre>`) o el
>       equipo. `monitor_ip` deberia regenerar la hoja **sin** regenerar la CA, y el panel
>       tiene que abrir sin advertencia en la IP nueva.
>
> **Sigue sin arreglo y va a fallar igual: B1** (el espacio extra en iPhone tras abrir y
> cerrar la PWA). Es esperado, no hace falta volver a reportarlo.

---

## CICLO EJECUTADO — v1.8.9 → 1.8.10 (resultados del 29/07, ya triados)

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

> **Nota**: OTA real de 1.8.9→1.8.10 ejecutada desde la app (reporte completo al final).
> Tema claro, logo nuevo OK.

- [OK] ⛔ **A1.** Ajustes → Buscar actualización → ofrece **1.8.10** → Actualizar → el
      servicio se reinicia y la app reconecta sola, sin tocar la terminal.
      (Es el pipeline que va a usar cada cliente que compre.)
- [OK] ⛔ **A2.** Tras el OTA, **cerrar y reabrir la PWA**: tiene que aparecer el logo
      nuevo y el tema claro. Si seguís viendo el logo viejo (el control remoto azul), el
      service worker no invalidó la caché → FALLA grave, anotarlo.  
      NOTA: El icono de app aun es una letra, aunque no entra en este item cabe mencionarlo
- [OK] **A3.** `latest.json` responde igual en los DOS hosts y con el mismo sha:
      `curl -s https://www.linuxremoteplayer.com/latest.json`
      `curl -s https://linux-remote-player.vercel.app/latest.json`
      *Por qué los dos*: T-65 migró el canal al dominio propio, pero los equipos con 1.8.x
      tienen la URL de `vercel.app` grabada en su código y la van a consultar para siempre.
      Ese alias no se apaga nunca; si alguna vez deja de responder, el OTA de todo el parque
      instalado muere.
- [OK] **A4.** El panel de la TV muestra la versión **1.8.10**.
- [OK] **A5.** `systemctl status linuxremoteplayer` → activo tras el update. Reboot →
      arranca solo.

## B. SKINS Y LOGO (T-58 — NUNCA se probó en device)

- [FALLA: Aun esta el espacio superior que desplaza el HUD hacia abajo cuando se abre la PWA por segunda vez, la primera vez no muestra el error] ⛔ **B1. El notch del iPhone.** Abrir la PWA **instalada** (standalone, desde el
      icono, no desde Safari). La barra de estado NO debe tapar el engranaje de Ajustes
      ni el título, y no debe quedar una banda blanca rara arriba.
      *Por qué*: cambié `apple-mobile-web-app-status-bar-style` de `black-translucent` a
      `default`, porque con fondo crema el texto blanco de la barra quedaba invisible.
      **Es el único cambio de T-58 que no pude verificar sin hardware.**
- [OK: Solo al reinstalar, comportamiento esperado, ya no reconecta al instalar el certificado descargable] ⛔ **B2. Icono en la pantalla de inicio** = logo nuevo (cuadro oscuro con puntitos
      y triángulo verde). Si aparece una "R" o el control viejo: borrar la PWA,
      reinstalarla y volver a mirar. Anotar modelo + SO + navegador.
- [OK] ⚠️ **B3. Migración de tema.** Tras el OTA el tema debe quedar en **Day** (claro).
      Con 1.8.9: si NO tenés Pro y elegís otro tema, salta "requiere licencia pro" — es lo
      esperado en esa versión. **Con 1.9.0 ese aviso NO debe existir más** (T-62 liberó las
      4 skins); si aparece, es una falla.
- [OK] **B4.** Cambiar entre Day / Night / Café / Anime → aplica al instante y **persiste**
      tras cerrar y reabrir la app. **En 1.9.0, las 4 sin candado y sin licencia.**
- [OK] ⚠️ **B5. Probar de noche, con la luz apagada.** Usar la app 2 minutos con el tema
      Day mientras mirás algo en la TV. Esto es un mando a distancia: se usa a oscuras, y
      una pantalla crema a pantalla completa puede encandilar. Si molesta, decilo — se
      evalúa volver a Night por defecto o cambiar según la hora. **No es una falla de
      código, es una decisión de producto que solo se puede tomar usándola.**
      *→ Propuesta del dueño: añadir en 1.9.0 un botón de acceso rápido al modo oscuro*
      *desde el HUD principal.*
- [OK] **B6.** En cada skin, que no haya texto ilegible: botones de acento (Enter, Done,
      Añadir, Activar), el estado "Conectado", y los textos de Ajustes.

## C. VOZ VÍA AI-PROXY (revalidar sobre el .deb publicado)

- [OK] ⛔ **C1.** Comando en **español**: "pon youtube" → transcribe y abre. Sin llaves de
      IA en el device (ahora pasa por el proxy).
- [OK] ⛔ **C2.** Comando en **INGLÉS**: "play youtube" → funciona.
      *Por qué es ⛔*: el prompt bilingüe (T-53d) nunca se confirmó, **y la web ya vende
      la voz en inglés** ("AI voice control in English and Spanish"). Si esto falla, hay
      una promesa publicada sin respaldo.
- [OK: Sin necesidad de un Keepalive, antes era lento ahora es rapido, desconozco la causa] **C3.** Cold start: el primer comando tras varias horas de inactividad tarda unos
      segundos (hallazgo conocido: Edge Function dormida + Whisper frío). **Anotar cuántos
      segundos** — ese número decide si vale la pena un keep-alive.
- [SKIP: hice varios comandos, queda comprobar en supabase o dejarlo pendiente de verificacion] **C4.** Contabilidad: dar exactamente 3 comandos, después en Supabase
      `select commands_today from licenses where token = '<tu key>';` → subió exactamente 3.
- [SKIP: Pendiente para ver en supabase] ⚠️ **C5. Kill-switch.** En el SQL editor:
      `update service_state set value = jsonb_set(value,'{enabled}','false') where key='voice';`
      → la voz responde con un error claro y la app NO se rompe.
      **Revertir a `true` al terminar** (si no, quedás sin voz).
- [OK] **C6.** `grep -iE "CLOUD_|TOGETHER" /opt/linuxremoteplayer/backend/.env`
      → **sin llaves de IA** (deben vivir solo en los secrets de Supabase).
- [OK: Sigue igual, aunque a veces da error de LLM] **C7.** Whisper con silencio: apretar el micro sin hablar → hoy inventa texto y
      ejecuta algo raro (hallazgo conocido, no es regresión). Confirmar que sigue igual
      para dimensionar el arreglo.

## D. LICENCIA DE 1 DISPOSITIVO

- [OK] ⛔ **D1.** Activar la licencia desde el móvil → "activada", aparece el micrófono,
      y el panel de la TV dice Pro sin reiniciar nada.
- [OK] ⚠️ **D2. Mudanza.** Activar la MISMA key en otra PC → debe preguntar "¿Mudar la key
      acá? El otro dispositivo perderá el premium" → confirmar → la primera PC pierde Pro.
- [PENDIENTE] **D3.** Gracia offline: cortar internet del HTPC (no la LAN) → el estado Pro
      aguanta (cache 72h). La voz NO (necesita nube, es esperado).

## E. DESINSTALACIÓN — probado en 1.8.10

El bug de B2 se arregló el 2026-07-27: nació `scripts/lrp-cleanup.sh` (no interactivo) y el
`prerm` lo llama.

> **E1 ES EL ÍTEM MÁS PELIGROSO DE TODA LA MATRIZ.** Si sale mal, el daño no es "no limpia":
> es que **cada actualización futura borre las reglas del sistema y libere la licencia de
> todos los dispositivos**. Hacelo ANTES que E2, y si falla, parás y avisás.

- [OK] ⛔ **E1. Que un OTA NO limpie nada.** Con 1.8.10 instalado y funcionando, se ejecutó
      actualización (o reinstalar el mismo `.deb` con `apt install --reinstall`). Después:
      `ls /etc/udev/rules.d/99-uinput.rules` → **TIENE que seguir existiendo** ·
      `ufw status | grep 8000` → **la regla sigue** ·
      `systemctl is-enabled sleep.target` → **sigue masked** (si instalaste con LRP_NOSLEEP) ·
      y el estado **Pro sigue activo** en la app (la licencia NO se liberó).
      *Por qué*: dpkg corre el `prerm` también al actualizar, con `$1="upgrade"`. El fix trae
      un guard `if [ "$1" = "remove" ]` justo para esto. Es la trampa de T-19 otra vez.
- [FALLO: en .env queda aun la key, al reinstalar reutiliza la key en .env, asi que no puedo testear en el mismo equipo si salta la mudanza, en el servidor si se libero efectivamente, pero que la key se haya quedado en el dispositivo local impide un OK en este item] ⛔ **E2. Que `apt remove` SÍ limpie.** `sudo apt remove linuxremoteplayer` y después:
      `ls /etc/udev/rules.d/99-uinput.rules` → no existe ·
      `ufw status | grep 8000` → vacío ·
      `systemctl is-enabled sleep.target` → **no** masked ·
      y la key queda libre para activar en otra PC **sin** pasar por la pantalla de mudanza.
- [OK] ⛔ **E3. Que `apt remove` termine bien pase lo que pase.** Repetir E2 **con el HTPC sin
      internet** (la liberación de licencia es una llamada de red con timeout de 5s).
      El `apt remove` tiene que **completar igual**, sin colgarse ni dejar el paquete en
      estado roto. Comprobar con `dpkg -l | grep linuxremoteplayer` → no debe quedar en `iF`
      ni `iU`. *Por qué*: un fallo de la limpieza JAMÁS puede abortar una desinstalación.
- [OK] **E4.** El desinstalador manual: `sudo /opt/linuxremoteplayer/scripts/uninstall.sh`
      → hace las mismas 4 cosas y NO imprime "se omite la limpieza de sistema".
      *Por qué está acá*: en la auditoría de T-64 el script nuevo se había commiteado sin
      permiso de ejecución y este camino quedaba silenciosamente sin hacer nada. Se corrigió,
      pero es exactamente la clase de fallo que solo se ve corriéndolo.
- [OK] **E5.** Reinstalar tras desinstalar → todo vuelve a funcionar.

## F. REGRESIÓN DEL NÚCLEO (1.8.9 tocó TODO el frontend + la voz del backend)

- [OK] ⛔ **F1.** Emparejar por PIN desde un teléfono nuevo (o borrando datos del sitio).
- [OK] ⛔ **F2.** Touchpad: mover, tap = clic izq, long-press = clic der, scroll lateral.
- [PARCIAL: teclado ES probado y funciona correctamente. No se probó con teclado
  LATAM.] **F3.** Teclado latam, escribir en un editor del HTPC:
      `hola/mundo @correo.com (test) & "ok" ¿? ; : + * _ =` → exacto.
- [OK] **F4.** Volumen +/−, mute, y ⏯ ⏮ ⏭ en un kiosk de YouTube.
      *→ Anotación: el volumen afecta globalmente al sistema, funciona en cualquier app.*
      *Control de reproducción funciona correctamente.*
- [OK] **F5.** Apps: lanzar una nativa (Dolphin) y una web; abrir "Más apps".
- [OK] **F6.** Panel /status en el HTPC → SIN advertencia de certificado.
- [OK] **F7.** Reconexión: apagar la pantalla del teléfono 2 min → encender → reconecta
      sola en <5s, sin recargar.
- [PARCIAL: en el escritorio funciona como control D-Pad correctamente. En YouTube
  se comporta como flechas, no como D-Pad de TV (por la naturaleza de YouTube, no
  de la app). Se revisará al hacer compatibles los kiosks. No tengo botón Esc ni
  Enter en el D-Pad.] **F8.** Modo D-Pad: flechas + Enter + Esc en una app leanback.

## G. ARRASTRES DE LA MATRIZ v1.7 (siguen sin cerrar)

- [PARCIAL: 2 dispositivos conectados a la vez sin problemas ni latencia. Faltó
  probar con 3.] **G1.** 2-3 teléfonos conectados a la vez (faltaba un segundo dispositivo).
- [SKIP: el ISP no otorga IP dinámica nueva. Si se refiere a cambio de IP local del
  HTPC, no está claro cómo provocarlo.] **G2.** Cambio de IP del HTPC → el certificado y el panel siguen sin advertencia.
- [OK] **G3.** ¿Sigue el favicon basura al añadir una app web, y el logo de LRP colándose
      en una app del sistema?
      *→ Anotación: ya no hay logo basura. Los iconos de apps cargan correctamente*
      *(aunque se ven un poco borrosos / baja calidad).*
- [OK: ahora dice LinuxRemotePlayer]
  **G4.** Backlog visual: el header dice "Remote Linux Player" (orden invertido) y NOTA: LA APP EN PLASMABIGSCREEN SE INSTALA CON NOMBRE REMOTE LINUX PLAYER, DEBE SER IGUALMENTE LINUX REMOTE PLAYER, LA APP INSTALADA DICE "REMOTELINUX" Y NO LRP COMO DEBE SER

---

## RESULTADOS

```
Fecha ejecución: 29/07/26  |  Balance: 29 OK · 2 FALLA · 3 PARCIAL · 3 SKIP · 1 PENDIENTE
Veredicto del dueño: La mayoría de ítems están correctos, solo tienen detalles.
```

### FALLAS reportadas

**B1 — Espacio extra en iPhone con notch (regresión T-58)**
: En la primera instalación se ve correcto, pero tras abrir/cerrar varias veces
aparece un espacio extra debajo de la barra de estado que desplaza el HUD hacia
abajo ocultando botones inferiores. Sucede en iPhone 8+. En iPhone 12 no oculta
botones pero igual tiene el espacio extra arriba.
: `apple-mobile-web-app-status-bar-style` cambiado de `black-translucent` a `default`.
: Habría que evaluar una solución que funcione en ambos modelos.

**E2 — La licencia no se limpia del .env local al desinstalar**
: `lrp-cleanup.sh` libera la licencia vía proxy (servidor), pero el `.env` local
sigue teniendo el token. La app en el teléfono muestra "activa" aunque en el
servidor ya está libre.
: `dpkg` no borra el `.env` porque no es parte del paquete (lo crea `install.sh`).
: El dueño considera que no es una limpieza completa si la key persiste en el equipo.

## ANOTACIONES DEL DUEÑO — no bloquean la matriz

- **Instalador**: El `.deb` no ejecuta `lrp-setup` automáticamente al finalizar la
  instalación. Pero si muestra un aviso de  "FALTA UN PASO. Para configurar el servicio ejecuta:
     sudo lrp-setup"
- **Nombre por defecto al instalar**: La app asigna "remote linux" como nombre de
  dispositivo. Debería ser "LRP" o al menos "Linux Remote Player" correctamente ordenado.
- **Cadena de certificados incompleta al regenerar certs**: Si se borra `/opt/linuxremoteplayer/backend/certs/`
  (ej: al ejecutar `uninstall.sh` — E4), el backend regenera solo el `cert.pem` (hoja)
  sin concatenar el `ca.pem`. Firefox reporta `SEC_ERROR_BAD_SIGNATURE` porque no recibe
  la cadena completa. Solución: `cat ca.pem >> cert.pem` y reiniciar el servicio.
  Tarea para el developer: `ensure_cert()` en `run.py` debería concatenar `ca.pem` al
  `cert.pem` automáticamente, o bien uvicorn debería usar `ssl_ca_certs`.

---

## OTA REAL 1.8.9 → 1.8.10 — FALLA (reporte de Claude)

### Qué pasó

El 29/07 a las 18:48 se ejecutó una actualización desde la app del teléfono (A1).
El proceso completo fue:

1. App chequeó → `latest.json` devolvió versión **1.8.10**
2. El usuario aplicó el OTA → `POST /api/update/apply`
3. `lrp-update` se lanzó via `systemd-run --unit=lrp-update-job`
4. Descargó el `.deb`, verificó SHA, instaló con `apt-get install --reinstall`
5. El paquete 1.8.10 quedó instalado correctamente
6. **El servicio NUNCA reinició.** Quedó `inactive (dead)`.

### Causa raíz

```
lrp-update-job.service: /usr/local/bin/lrp-update: línea 33: start: orden no encontrada
```

El script `lrp-update` tiene `set -e` (line 9). Encuentra un comando `start` que no
existe en systemd y falla con `status 127`, **antes** de llegar a
`systemctl restart linuxremoteplayer.service`.

El `start` viene del `.deb` 1.8.10 — posiblemente del postinst o del reemplazo en
caliente del propio `lrp-update` durante el `apt-get install`. Como el script se
reemplazó a sí mismo en disco, bash sigue ejecutando el código en memoria, pero al
llegar a la línea 33 de la *nueva versión* se topa con `start` y muere.

### Estado tras la falla

| Componente | Estado |
|---|---|
| Versión instalada | 1.8.10 ✓ |
| Servicio | `inactive (dead)` |
| systemd unit | intacto, `enabled` |
| .venv/python | intacto |
| Puerto 8000 | caído |

**El servicio arranca bien manualmente** (`systemctl start linuxremoteplayer` → active
en 2s). El bug es solo del script de update, no del paquete en sí.

### Acción requerida para el developer

- Revisar `lrp-update` (o `install.sh`): reemplazar el comando `start` por
  `systemctl start` o `systemctl restart`.
- Evaluar si conviene sacar `set -e` en la sección de restart, o al menos usar
  `|| true` para que un fallo menor no deje el servicio caído.
- Probar OTA real de 1.8.10 → 1.8.11 (o la que sigue) para verificar que el fix
  funciona de punta a punta.

**Anotación del dueño (activación manual de voz)**
: Tras el OTA el micrófono no se activó. El código de 1.8.10 activa la voz
  (`ENABLE_VOICE=true`) solo durante el flujo de activación de licencia
  (`POST /api/license/activate`, línea 535 de `main.py`). Si la licencia ya estaba
  activada antes del update, `ENABLE_VOICE` nunca se escribe en `.env`.
: **Solución aplicada**: se agregó `ENABLE_VOICE=true` al final de
  `/opt/linuxremoteplayer/backend/.env` y se reinició el servicio con
  `systemctl restart linuxremoteplayer`. `voice_enabled` ahora responde `true`.
: **Tarea para el developer**: en el arranque del backend, detectar si ya hay un
  `LICENSE_TOKEN` válido y setear `ENABLE_VOICE=true` automáticamente, en lugar de
  depender solo del flujo de activación.
