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

> **Nota del dueño**: Se hizo instalación limpia en lugar de OTA, por lo que A1 y A2
> no aplican. Tema claro, logo nuevo OK.

- [SKIP: instalación limpia, pendiente para test OTA] ⛔ **A1.** Ajustes → Buscar actualización → ofrece **1.8.9** → Actualizar → el
      servicio se reinicia y la app reconecta sola, sin tocar la terminal.
      (Es el pipeline que va a usar cada cliente que compre.)
- [SKIP: instalación limpia, sin OTA. El icono nuevo no aparece ni con certificados
  instalados ni en ventana de navegación privada. ↓ Ver Hallazgo 4.] ⛔ **A2.** Tras el OTA, **cerrar y reabrir la PWA**: tiene que aparecer el logo
      nuevo y el tema claro. Si seguís viendo el logo viejo (el control remoto azul), el
      service worker no invalidó la caché → FALLA grave, anotarlo.
- [OK] **A3.** `latest.json` responde igual en los DOS hosts y con el mismo sha:
      `curl -s https://www.linuxremoteplayer.com/latest.json`
      `curl -s https://linux-remote-player.vercel.app/latest.json`
      *Por qué los dos*: T-65 migró el canal al dominio propio, pero los equipos con 1.8.x
      tienen la URL de `vercel.app` grabada en su código y la van a consultar para siempre.
      Ese alias no se apaga nunca; si alguna vez deja de responder, el OTA de todo el parque
      instalado muere.
- [OK] **A4.** El panel de la TV muestra la versión **1.8.9**.
- [OK] **A5.** `systemctl status linuxremoteplayer` → activo tras el update. Reboot →
      arranca solo.

## B. SKINS Y LOGO (T-58 — NUNCA se probó en device)

- [FALLA: en la primera instalación se ve correcto, pero tras abrir/cerrar varias
  veces aparece un espacio extra debajo de la barra de estado que desplaza el HUD
  hacia abajo ocultando botones inferiores. Sucede en iPhone 8+. En iPhone 12 no
  oculta botones pero igual tiene ese espacio extra arriba.] ⛔ **B1. El notch del iPhone.** Abrir la PWA **instalada** (standalone, desde el
      icono, no desde Safari). La barra de estado NO debe tapar el engranaje de Ajustes
      ni el título, y no debe quedar una banda blanca rara arriba.
      *Por qué*: cambié `apple-mobile-web-app-status-bar-style` de `black-translucent` a
      `default`, porque con fondo crema el texto blanco de la barra quedaba invisible.
      **Es el único cambio de T-58 que no pude verificar sin hardware.**
- [FALLA: no aparece el icono nuevo ni instalando el certificado. Al instalar el
  certificado nuevo la app se desconecta y se queda trabada reconectando. Hay que
  instalar otra PWA y aceptar el certificado (el que bloquea la página, no el de
  descarga). Ambas (antigua y nueva) se reconectan. Posible problema con el
  certificado de instalación que afecta al icono y al proceso de reinstalación.] ⛔ **B2. Icono en la pantalla de inicio** = logo nuevo (cuadro oscuro con puntitos
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

> **Nota del dueño**: Los comandos de voz están desactivados en 1.8.9, se probarán
> cuando estén habilitados. Toda la sección queda pendiente.

- [SKIP: comandos de voz desactivados en 1.8.9] ⛔ **C1.** Comando en **español**: "pon youtube" → transcribe y abre. Sin llaves de
      IA en el device (ahora pasa por el proxy).
- [SKIP: comandos de voz desactivados en 1.8.9] ⛔ **C2.** Comando en **INGLÉS**: "play youtube" → funciona.
      *Por qué es ⛔*: el prompt bilingüe (T-53d) nunca se confirmó, **y la web ya vende
      la voz en inglés** ("AI voice control in English and Spanish"). Si esto falla, hay
      una promesa publicada sin respaldo.
- [SKIP: comandos de voz desactivados en 1.8.9] **C3.** Cold start: el primer comando tras varias horas de inactividad tarda unos
      segundos (hallazgo conocido: Edge Function dormida + Whisper frío). **Anotar cuántos
      segundos** — ese número decide si vale la pena un keep-alive.
- [SKIP: comandos de voz desactivados en 1.8.9] **C4.** Contabilidad: dar exactamente 3 comandos, después en Supabase
      `select commands_today from licenses where token = '<tu key>';` → subió exactamente 3.
- [SKIP: comandos de voz desactivados en 1.8.9] ⚠️ **C5. Kill-switch.** En el SQL editor:
      `update service_state set value = jsonb_set(value,'{enabled}','false') where key='voice';`
      → la voz responde con un error claro y la app NO se rompe.
      **Revertir a `true` al terminar** (si no, quedás sin voz).
- [SKIP: comandos de voz desactivados en 1.8.9] **C6.** `grep -iE "CLOUD_|TOGETHER" /opt/linuxremoteplayer/backend/.env`
      → **sin llaves de IA** (deben vivir solo en los secrets de Supabase).
- [SKIP: comandos de voz desactivados en 1.8.9] **C7.** Whisper con silencio: apretar el micro sin hablar → hoy inventa texto y
      ejecuta algo raro (hallazgo conocido, no es regresión). Confirmar que sigue igual
      para dimensionar el arreglo.

## D. LICENCIA DE 1 DISPOSITIVO

- [PARCIAL: la skin premium se activa y el panel muestra Pro correctamente, pero no
  aparece el micrófono (comandos de voz desactivados en 1.8.9)] ⛔ **D1.** Activar la licencia desde el móvil → "activada", aparece el micrófono,
      y el panel de la TV dice Pro sin reiniciar nada.
- [OK] ⚠️ **D2. Mudanza.** Activar la MISMA key en otra PC → debe preguntar "¿Mudar la key
      acá? El otro dispositivo perderá el premium" → confirmar → la primera PC pierde Pro.
- [PENDIENTE] **D3.** Gracia offline: cortar internet del HTPC (no la LAN) → el estado Pro
      aguanta (cache 72h). La voz NO (necesita nube, es esperado).

## E. DESINSTALACIÓN — el fix ya está en código (T-64), FALTA PROBARLO

> **Nota del dueño**: Pendiente de un .deb de 1.9.0. Con 1.8.9 instalado no aplica.

El bug de B2 se arregló el 2026-07-27: nació `scripts/lrp-cleanup.sh` (no interactivo) y el
`prerm` lo llama. **Nada de esto se pudo probar sin un Debian real: es la verificación más
importante del ciclo.** Requiere un `.deb` de **1.9.0**; con el 1.8.9 instalado no aplica.

> **E1 ES EL ÍTEM MÁS PELIGROSO DE TODA LA MATRIZ.** Si sale mal, el daño no es "no limpia":
> es que **cada actualización futura borre las reglas del sistema y libere la licencia de
> todos los dispositivos**. Hacelo ANTES que E2, y si falla, parás y avisás.

- [SKIP: requiere .deb 1.9.0] ⛔ **E1. Que un OTA NO limpie nada.** Con 1.9.0 instalado y funcionando, disparar una
      actualización (o reinstalar el mismo `.deb` con `apt install --reinstall`). Después:
      `ls /etc/udev/rules.d/99-uinput.rules` → **TIENE que seguir existiendo** ·
      `ufw status | grep 8000` → **la regla sigue** ·
      `systemctl is-enabled sleep.target` → **sigue masked** (si instalaste con LRP_NOSLEEP) ·
      y el estado **Pro sigue activo** en la app (la licencia NO se liberó).
      *Por qué*: dpkg corre el `prerm` también al actualizar, con `$1="upgrade"`. El fix trae
      un guard `if [ "$1" = "remove" ]` justo para esto. Es la trampa de T-19 otra vez.
- [SKIP: requiere .deb 1.9.0] ⛔ **E2. Que `apt remove` SÍ limpie.** `sudo apt remove linuxremoteplayer` y después:
      `ls /etc/udev/rules.d/99-uinput.rules` → no existe ·
      `ufw status | grep 8000` → vacío ·
      `systemctl is-enabled sleep.target` → **no** masked ·
      y la key queda libre para activar en otra PC **sin** pasar por la pantalla de mudanza.
- [SKIP: requiere .deb 1.9.0] ⛔ **E3. Que `apt remove` termine bien pase lo que pase.** Repetir E2 **con el HTPC sin
      internet** (la liberación de licencia es una llamada de red con timeout de 5s).
      El `apt remove` tiene que **completar igual**, sin colgarse ni dejar el paquete en
      estado roto. Comprobar con `dpkg -l | grep linuxremoteplayer` → no debe quedar en `iF`
      ni `iU`. *Por qué*: un fallo de la limpieza JAMÁS puede abortar una desinstalación.
- [SKIP: requiere .deb 1.9.0] **E4.** El desinstalador manual: `sudo /opt/linuxremoteplayer/scripts/uninstall.sh`
      → hace las mismas 4 cosas y NO imprime "se omite la limpieza de sistema".
      *Por qué está acá*: en la auditoría de T-64 el script nuevo se había commiteado sin
      permiso de ejecución y este camino quedaba silenciosamente sin hacer nada. Se corrigió,
      pero es exactamente la clase de fallo que solo se ve corriéndolo.
- [SKIP: requiere .deb 1.9.0] **E5.** Reinstalar tras desinstalar → todo vuelve a funcionar.

## F. REGRESIÓN DEL NÚCLEO (1.8.9 tocó TODO el frontend + la voz del backend)

> **Hallazgo**: El QR escaneado da la URL con el token pero la página muestra solo
> un texto plano "offline" y no sucede nada. Investigar.

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
- [PARCIAL: el header sigue diciendo "Remote Linux Player" (orden invertido). G4a.]
  **G4.** Backlog visual: el header dice "Remote Linux Player" (orden invertido) y
      "Okular" aparece duplicado en las apps detectadas.
      *→ Okular aparece 2 veces porque Plasma BigScreen tiene dos versiones de Okular*
      *(lector y abre-archivos). No es error de detección de la app. Ignorar.*
      *→ Propuesta del dueño: usar ese espacio para banners de consejos/novedades de la*
      *app (feature para el plan).*

---

## RESULTADOS

```
Fecha ejecución: 29/07/26  |  Balance: 15 OK · 2 FALLA · 5 PARCIAL · 16 SKIP
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

**B2 — Icono nuevo no aparece y certificado causa desconexión**
: El logo nuevo no se muestra ni instalando el certificado. Al instalar el
certificado descargado, la app se desconecta y se queda trabada intentando
reconectar. La solución temporal es instalar otra PWA y aceptar el certificado
desde la advertencia del navegador (no el de descarga). Ambas PWA (antigua y
nueva) se reconectan después de eso.
: Posible problema con el certificado de instalación que afecta al icono y al
proceso de reinstalación.

### Hallazgos adicionales (no bloquean, pero se dejan asentados)

1. **QR muestra "offline"**: El QR escanea bien y da la URL con el token, pero la
   página solo muestra texto plano "offline" y no avanza.
2. **Volumen global del sistema**: Se confirma que el control de volumen afecta al
   sistema completo, no solo a la app activa. Se estableció que es el
   comportamiento esperado.
3. **D-Pad en YouTube**: Se comporta como flechas de navegación web, no como D-Pad
   de TV. Es inherente a YouTube, se revisará en la fase de compatibilidad de
   kiosks.
4. **Icono nuevo PWA**: El icono nuevo no se despliega en la PWA instalada ni con
   certificados ni en navegación privada. Puede estar relacionado con el service
   worker o el manifiesto.
5. **Gráficos de apps borrosos**: Los iconos de apps detectadas se ven de baja
   calidad. Posible mejora futura.

---

## ANOTACIONES DEL DUEÑO (hallazgos visuales/de instalación — no bloquean la matriz)

- **Instalador**: El `.deb` no ejecuta `lrp-setup` automáticamente al finalizar la
  instalación. Hay que correrlo a mano. Tampoco hay un mensaje que diga "Ejecute
  `lrp-setup` para iniciar la configuración". Si en otra distro tampoco corre
  automáticamente, el usuario se queda sin saber cómo continuar.
  (Output del instalador guardado en Downloads para el developer.)
- **Título de la app en el teléfono**: La PWA instalada muestra "Remote Linux Player"
  como encabezado. Debería decir "Linux Remote Player" (orden invertido, mismo bug
  que G4).
- **Nombre por defecto al instalar**: La app asigna "remote linux" como nombre de
  dispositivo. Debería ser "LRP" o al menos "Linux Remote Player" correctamente
  ordenado.
