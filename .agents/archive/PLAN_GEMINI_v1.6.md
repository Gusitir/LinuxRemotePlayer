# PLAN DE TRABAJO — GEMINI (v1.6.0: reporte de bugs HTPC + migración Brave + hardening)

```yaml
plan_id: PLAN_GEMINI_v1.6
date: 2026-07-13
author: Claude (planificador/auditor) — causas raíz verificadas en código real
executor: Gemini 3.5 Pro (programador)
supersedes: PLAN_GEMINI_v1.5.1 (absorbido: sus T1/T2/T3 son ahora G-09/G-10/G-12)
base: reporte de bugs del dueño (testing v1.5.0 en HTPC, 2026-07-13) + AUDIT_v1.5
flujo: BACHE (desde 2026-07-14, decisión del dueño para ahorrar tokens) — Gemini ejecuta
  C-03..C-09 + G-17 + G-18 SEGUIDAS (un commit por tarea, sin parar entre ellas),
  auto-verificando cada criterio de aceptación; STOP solo al terminar el bache completo
  -> Claude audita TODO el bache -> G-14.
release: TODO sale en un único .deb v1.6.0 (un solo ciclo de build WSL)
estado: AUDITADO 2026-07-14. C-01 (ce6149b) APTO. C-02 (8d91989) APTO.
  G-14 BLOQUEADO hasta auditoría del bache C-03..G-18.
```

## AUDITORÍA CLAUDE 2026-07-14 — VEREDICTOS G-01..G-13 (+2 commits extra)

| Tarea | Veredicto | Nota |
|---|---|---|
| G-01 fc52e44 | APTO | Import, QR, mode, buy-link OK. "mode" depende de C-06. |
| G-02 8453c18 | APTO CON CORRECCIÓN | Dejó `</div>` huérfano (index.html:90) + función muerta toggleManualToken (app.js:1287). -> C-02 |
| G-03 7417b67 | PARCIAL | KPSLASH OK. Mapa es/latam incompleto (@, &, parens) y AltGr IMPOSIBLE: KEY_RIGHTALT=100 no está en caps range(1,100). -> C-07 |
| G-04 c9291fe | APTO CON NOTA | Falta ack en rama browser_back. -> C-09 |
| [G-05] eb57191 | APTO (FUERA DE PLAN) | get_ips filtra ifaces virtuales — útil, display-only, aceptado. OJO: el G-05 real (iconos) NO se hizo -> renumerado G-17. |
| [G-06] a87287b | NO APTO PARCIAL | location.reload() en heartbeat = riesgo de bucle de recargas + pisa el backoff -> REVERTIR (C-03). Meta refresh 3600 del panel: aceptado. El G-06 real (terminales) NO se hizo -> renumerado G-18. |
| G-07 ef5a3b9+38ad7bf | APTO CON CORRECCIÓN | Brave+perfil dedicado+repo apt oficial OK. Falta escribir LRP_MODE en .env (-> C-06). |
| G-08 0a8cd0d | APTO CON CORRECCIÓN | 10s correcto PERO amplifica bloqueo del event loop (launch/close síncronos en handlers async) -> C-01 CRÍTICO. |
| G-09 1d05359 | APTO CON CORRECCIÓN | certutil/trust OK pero en fresh install ca.pem AÚN NO EXISTE cuando corre el bloque -> no-op silencioso. -> C-05 |
| G-10 e4646ca | APTO | wmctrl best-effort con exclusiones razonables. Sync -> cubierto por C-01. |
| G-11 bbb9330 | APTO CON CORRECCIÓN | pactl sin XDG_RUNTIME_DIR -> falla en Appliance (system service), justo donde importa. -> C-04 |
| G-12 095883e | APTO | Verificado: greps mock-link y `except:` a 0; deb 1.4.0 fuera. |
| G-13 0c846a4 | PARCIAL | Script funciona pero IGNORE_CLASSES gigante (incluye `hidden`!) anula el guard; no lee `<style>` inline de los HTML. sw.js ya bumpeado a lrp-v16 ✓. -> C-08 |
| b32101d ai_pipeline | ACEPTADO (FUERA DE PLAN) | Retrocompatible, sin secretos. PERO refuerza claves en dispositivo: ai-proxy sigue siendo obligatorio antes de vender voz. Violación de regla 3 (sin [G-NN], sin tarea) — no repetir. |
| 57f221a APK nota | OK | Evaluada -> FASE E. |

## REGLAS PARA GEMINI (obligatorias)

1. Leer PRIMERO `.agents/CURRENT.md` y `.agents/APPCORE.md`. No re-descubrir arquitectura.
2. **Una tarea = un commit** con prefijo `[G-NN]`. No mezclar tareas.
3. **No tocar nada fuera del alcance.** Hallazgos ajenos -> anotarlos en CURRENT.md
   (sección HALLAZGOS GEMINI) y seguir. NO arreglarlos.
4. **Archivos grandes** (`frontend/app.js` ~1400 líneas, `frontend/index.html` ~80KB,
   `backend/main.py` ~880 líneas): verificar que tu herramienta lee el archivo COMPLETO
   (`wc -l` real vs lo que ves). Este repo ya sufrió truncado silencioso.
5. Sintaxis/builds (`py_compile`, `node --check`, `build_deb.sh`): SOLO en WSL.
6. NUNCA commitear secretos. `.env.example` sin valores reales.
7. Al cerrar cada tarea: actualizar CURRENT.md y DETENERSE para auditoría.
8. El modelo de auth NO se toca: require_token / require_local / require_local_or_token
   (ver APPCORE.md). Cualquier endpoint nuevo debe declarar su gate explícitamente.

---

## FASE A — BUGFIXES DE CÓDIGO (causa raíz confirmada)

### G-01 — Panel de estado muerto: import inexistente rompe /api/status [CRÍTICO]
**Causa raíz confirmada:** `backend/main.py:362` hace
`from input_emulator import mouse_ui_created`, pero ese símbolo NO existe en
`input_emulator.py` (solo exporta `gamepad` y `mouse`). ImportError en cada request ->
/api/status devuelve 500 -> el panel entero queda sin datos (latencia vacía, kiosk "Idle",
licencia "Verificando..." eterno). Es la causa de casi todo el bug del panel.
**Fix:**
1. Sustituir por `from input_emulator import mouse` y reportar `"uinput_ok": mouse.ui is not None`
   (o exponer un helper `is_ready()` en input_emulator; elegir lo más limpio).
2. `frontend/status.html:245`: `<img src="/api/qr">` -> endpoint real `/api/pairing-qr`
   (verificar que el panel se abre vía https://127.0.0.1:8000/status => require_local pasa).
3. Añadir a la respuesta de /api/status: `"mode"` (appliance|desktop) — el installer debe
   exportar `LRP_MODE` en el unit systemd (coordinar con G-07) y el backend leerlo de env.
4. Latencia: el panel la mide client-side (RTT del fetch a /api/status, mostrar ms).
   No inventar campo de latencia server-side.
5. Licencia en panel: la activación desde el móvil escribe LICENSE_TOKEN en backend/.env y
   os.environ (main.py:461-476), así que tras el fix del import el panel YA la verá.
   Además: el texto estático "Compra tu licencia en: linux-remote-player.vercel.app"
   (status.html:313) -> convertir en enlace/botón clicable (el usuario tiene puntero
   virtual en la TV) usando buy_url de /api/status.
**Aceptación:** `curl -k https://127.0.0.1:8000/api/status` -> 200 JSON completo (probar
en HTPC o WSL con backend corriendo); panel muestra versión, modo, licencia activada,
latencia en ms, QR visible; py_compile OK.

### G-02 — Quitar TODO el UI de token manual del móvil (petición repetida del dueño)
**Contexto:** el onboarding aún tiene `#manual-token-ui` + `#onboarding-token-input`
(index.html:93-94) y probablemente un enlace "usar token" que lo muestra, más una entrada
de token en Ajustes. El emparejamiento oficial es PIN de 6 dígitos (+link QR con ?token=).
**Fix:** eliminar el bloque manual-token-ui del onboarding y cualquier input de token en
Ajustes; buscar en app.js TODAS las referencias (mostrar/ocultar/leer ese input) y
eliminarlas. El token SIGUE existiendo por debajo (localStorage/IndexedDB + ?token= del QR
+ PIN que lo entrega vía /api/pair) — solo desaparece el INGRESO MANUAL visible.
**Aceptación:** grep de `manual-token-ui|onboarding-token-input` -> 0; onboarding muestra
SOLO PIN + instrucción de QR; flujo PIN completo sigue funcionando; node --check OK.

### G-03 — Teclado: "/" escribe "-" (layout hardcodeado US) [afecta a todo usuario ES]
**Causa raíz confirmada:** `input_emulator.py` `_build_char_keys()` mapea chars a keycodes
asumiendo layout US (línea 49: "/" -> KEY_SLASH). En layouts es/latam esa tecla física
produce "-". Afecta también a ; : ' " etc.
**Fix (dos capas):**
1. Inmediato y universal: "/" -> `KEY_KPSLASH` (el slash del numpad es independiente del
   layout y de NumLock). Añadir KEY_KPSLASH a las capabilities del UInput si hiciera falta
   (ya está: range(1,100) incluye el código 98).
2. General: soportar `KEYBOARD_LAYOUT` en backend/.env (valores: us|es|latam, default us).
   `_build_char_keys()` genera el mapa según layout (añadir diccionarios de diferencias
   es/latam para símbolos comunes: signos, acentos NO — solo ASCII imprimible).
   El installer (G-07) detecta el layout del sistema (`localectl status` -> XKBLAYOUT) y
   lo escribe en .env.
**Aceptación:** con KEYBOARD_LAYOUT=latam, escribir desde el móvil `hola/mundo: "ok!"` en
un editor del HTPC reproduce exactamente esos caracteres; py_compile OK.

### G-04 — Botón "atrás" actúa como rebobinar en reproductores
**Causa raíz:** combo browser_back = Alt+Left (input_emulator.py:164). Los reproductores
HTML5 capturan las flechas (Left = seek) y en algunos casos el Alt no llega/se ignora.
**Fix:** añadir `BTN_SIDE` (botón "atrás" del mouse) a las capabilities de VirtualMouse y
usar eso para "atrás": los navegadores lo interpretan como history-back a nivel global y
los reproductores NO lo capturan. Nuevo mensaje WS `{"type":"pointer","click":"back"}` (o
reutilizar combo -> mouse). Mantener Alt+Left como fallback si BTN_SIDE no disponible.
**Aceptación:** "atrás" navega en un reproductor embebido sin rebobinar; en páginas
normales sigue navegando atrás.

### G-05 [RENUMERADA -> G-17: Gemini usó este número para otra cosa] — Iconos confusos
**Fix (frontend/index.html, set Reicon/Lucide inline):**
1. Borrar texto: bote de basura -> icono BACKSPACE estándar (⌫: flecha-caja apuntando a
   la izquierda con X dentro; en Lucide es "delete").
2. Modo navegación: gamepad -> cruz de 4 flechas direccionales (Lucide "move" o 4 chevrons
   en cruz). Debe leerse como "navegación direccional", no juego.
3. Panel de estado: televisión -> icono de actividad/estado (Lucide "activity" — línea de
   pulso). 
**Aceptación:** los 3 SVG reemplazados inline, mismo tamaño/clase que los actuales, sin
clases CSS nuevas sin definir (¡deriva tailwind-lite!).

### G-06 [RENUMERADA -> G-18: Gemini usó este número para otra cosa] — Detector de apps: incluir terminales
**Causa raíz confirmada:** `discovery.py:16` SKIP_CATEGORIES={'Settings','System',
'Screensaver'}; konsole/gnome-terminal declaran `Categories=System;TerminalEmulator;` ->
quedan filtrados.
**Fix:** excepción ANTES del filtro: si `'TerminalEmulator' in cats` -> NO filtrar.
**Aceptación:** en HTPC con konsole instalado, /api/apps lo lista; el resto del ruido
System/Settings sigue oculto.

---

## FASE B — MIGRACIÓN A BRAVE + ESTABILIDAD DE SESIÓN

### G-07 — Brave como navegador kiosk por defecto (pedido explícito del dueño)
**Contexto:** Chromium sin adblock integrado; 2 intentos de preinstalar adblock fallaron
(uBOL actual funciona a medias). Brave (gratis en Linux, Chromium-based) trae Shields.
NOTA histórica: Brave se descartó en PH8 por simplificar a un solo navegador — el dueño
revierte esa decisión conscientemente.
**Fix:**
1. `backend/kiosk.py`: `find_browser()` busca brave primero (`brave-browser`,
   `brave-browser-stable`, `brave` + rutas /usr/bin, /opt/brave.com/brave/), chromium como
   fallback. Flags iguales (--app, --kiosk...) + CORRECCIÓN: el flag real es
   `--noerrdialogs` (el actual `--no-errdialogs` está mal escrito y se ignora).
2. **Perfil dedicado y persistente**: añadir `--user-data-dir=$HOME/.config/lrp-kiosk`
   al comando. Esto aísla el kiosk del perfil personal Y hace persistentes las sesiones
   de las páginas (ver G-08).
3. `--load-extension` uBOL: mantener SOLO si el navegador es chromium (fallback);
   con Brave no se carga (Shields lo cubre). `is_ubol_active()` -> renombrar/ampliar a
   `adblock_status()` que devuelva "shields" | "ubol" | "none" (status panel lo muestra).
4. pkill fallback (kiosk.py:109-110): añadir patrones brave (`brave.*--kiosk`).
5. `scripts/install.sh`: QUITAR instalación de chromium y TODO el bloque de descarga/
   flatten de uBOL. AÑADIR instalación de Brave por el repo apt oficial
   (keyring + sources.list.d según docs de Brave; NO el script curl|sh de terceros dentro
   del installer sin verificación: usar los pasos apt documentados). Idempotente.
6. `scripts/install.sh`: escribir `LRP_MODE=appliance|desktop` (G-01.3) y
   `KEYBOARD_LAYOUT` detectado (G-03.2) en backend/.env si no existen.
**Aceptación:** en HTPC limpio, install.sh deja Brave instalado; kiosk abre con Brave y
Shields activo (probar página con ads); bash -n install.sh OK; Chromium ya no se instala.

### G-08 — Pérdida de credenciales/sesión y picos de latencia [GRAVE según dueño]
**Diagnóstico (hipótesis fuerte, verificar en HTPC):**
- kiosk.py mata el kiosk con SIGTERM y a los 3s SIGKILL (kill_existing_kiosks). Con páginas
  pesadas (anime+ads) el navegador no cierra en 3s -> SIGKILL -> perfil sin flush ->
  cookies de sesión/estado perdidos ("credenciales reseteadas"). YouTube no lo sufre porque
  cierra rápido y su sesión es más robusta.
- Los picos de latencia: las páginas con ads saturan CPU del HTPC -> el backend (mismo
  equipo) responde lento al WS. Brave Shields mitiga la causa.
**Fix:**
1. Subir la espera de SIGTERM->SIGKILL de 3s a 10s (kiosk.py:92, range(30) de 0.1s ->
   range(100)).
2. Perfil dedicado persistente (ya en G-07.2) — las sesiones sobreviven entre lanzamientos.
3. Log de diagnóstico: si hay que SIGKILL, loggear WARNING con el tiempo esperado (para
   confirmar la hipótesis en journalctl).
**Aceptación:** lanzar página pesada, cambiar de app 3 veces -> login de la página se
conserva; journalctl sin SIGKILL en cierres normales.

### G-09 — Certificado "se pierde" en el navegador del HTPC
**Diagnóstico:** run.py regenera el cert leaf cuando cambia la IP. El navegador del HTPC
no confía en nuestra CA -> cada regeneración vuelve el interstitial de cert en el panel
(127.0.0.1). En el TELÉFONO no pasa si instalaron la CA.
**Fix:** en install.sh, instalar `backend/certs/ca.pem` en el trust del sistema
(`/usr/local/share/ca-certificates/lrp-ca.crt` + `update-ca-certificates`) Y en el NSS db
del usuario (`certutil -d sql:$HOME/.pki/nssdb -A -t "C,," -n "LRP CA"` — chromium/brave
leen NSS). Instalar `libnss3-tools` como dependencia. La CA es estable (solo el leaf rota),
así que es una operación de una vez. Idempotente.
**Aceptación:** tras install, abrir https://127.0.0.1:8000/status en Brave del HTPC ->
sin advertencia; regenerar leaf (cambiar IP o borrar certs) -> sigue sin advertencia.

### G-10 — Home debe dejar el escritorio limpio (cerrar TODAS las ventanas)
**Causa raíz confirmada:** kiosk.close_all() solo mata el kiosk propio + procesos nativos
lanzados por NUESTRA app (_native_procs). Ventanas abiertas por otros medios quedan vivas.
**Fix:** best-effort de cierre de ventanas ajenas tras close_all():
- X11/XWayland: `wmctrl -l` + `wmctrl -ic <id>` sobre cada ventana (cierre educado, no kill).
  Añadir wmctrl a deps del installer.
- KDE Wayland (Bigscreen): fallback vía KWin DBus si wmctrl no ve ventanas
  (`qdbus org.kde.KWin ...` / kdotool si disponible). Si ninguno disponible: loggear y
  mantener comportamiento actual — NO matar procesos por nombre a ciegas.
- Excluir de cierre: el propio panel de estado si está por relanzarse, y plasmashell/krunner
  (ventanas de shell del escritorio).
**Aceptación:** con 1 app nuestra + 1 ventana abierta a mano, Home deja escritorio sin
ventanas (X11); en Wayland al menos las nuestras + las que KWin permita.

### G-11 — Salvaguarda del panel idle: detectar media REAL, no solo procesos propios
**Causa raíz confirmada:** monitor_idle_panel (main.py:81-98) considera "media_running"
SOLO sus propios procesos. Si el usuario abre otra app/navegador a mano y el teléfono se
desconecta (reposo), a los 45s el panel se lanza ENCIMA del contenido.
**Fix — nueva señal primaria: audio activo.** media_running = (procesos propios vivos)
OR (hay streams de audio activos: `pactl list short sink-inputs` no vacío — funciona en
PipeWire vía pipewire-pulse y en PulseAudio; ejecutar con asyncio.to_thread y timeout).
Mantener el resto de la lógica (45s + connected_clients==0). Si pactl no existe -> señal
desactivada, comportamiento actual + WARNING una sola vez.
**Aceptación:** reproducir video en un navegador abierto A MANO, teléfono en reposo ->
el panel NO aparece; pausar el video y esperar >60s -> el panel aparece.

---

## FASE C — HARDENING HEREDADO (ex-plan v1.5.1) + RELEASE

### G-12 — Limpieza de código [ex-T1; AUDIT_v1.5 C2+C3]
1. `backend/main.py:352` — `except:` desnudo -> `except Exception:`.
2. `frontend/app.js:61,226` — placeholder muerto `'https://buy.stripe.com/mock-link'` ->
   `'https://linux-remote-player.vercel.app/'` (solo se usa en buyLicense(), línea ~1084).
3. `git rm` de `website/downloads/linuxremoteplayer_1.4.0_all.deb` y su `.sha256`.
**Aceptación:** greps a 0 (mock-link, `except:`); py_compile + node --check OK en WSL.

### G-13 — Guard anti-deriva tailwind-lite.css [ex-T2; AUDIT_v1.5 C1, deuda #1]
Crear `scripts/check_css_sync.py` (Python 3 stdlib): extrae clases usadas en
index.html/status.html/pair.html + app.js (classList.add/toggle/remove, className=,
class= en template literals) y las compara con las definidas en tailwind-lite.css +
skins.css. Lista faltantes -> exit 1. Whitelist IGNORE comentada en el script.
Integrar en build_deb.sh ANTES de empaquetar (abortar si falla).
**Relación con bug de límites de pantalla (G-15):** si el check detecta clases faltantes
reales, repararlas aquí — el scroll lateral del móvil huele a esta deriva.
**Aceptación:** check limpio en repo actual (o faltantes reparadas y anotadas); prueba
negativa con clase inventada -> exit 1; build_deb.sh aborta si falla.

## FASE A-BIS — CORRECCIONES DE AUDITORÍA (2026-07-14; BLOQUEAN G-14; en orden)

### C-01 — [CRÍTICO] El event loop se congela hasta 10s al lanzar/cerrar kiosk
`launch_kiosk`, `close_all` y `kill_existing_kiosks` hacen sleeps/subprocess SÍNCRONOS
(hasta 10s tras G-08, más wmctrl de G-10) y se llaman DIRECTO desde handlers `async` de
main.py -> todo el backend (WS incluido) se congela mientras tanto. Esto es parte de los
"picos de latencia" reportados por el dueño.
**Fix:** en main.py, envolver TODAS las llamadas a kiosk.* en `await asyncio.to_thread(...)`:
/api/kiosk/launch, /api/kiosk/kill, /api/app/launch, /api/panel/show y cualquier ruta del
WS que las invoque (buscar TODAS las referencias; monitor_idle_panel ya usa to_thread).
**Aceptación:** con un launch en curso de página pesada, un ping WS responde <200ms.

### C-02 — [ALTO] Restos de G-02: `</div>` huérfano + función muerta
1. `frontend/index.html:90`: eliminar el `</div>` huérfano que quedó al quitar el bloque
   de token manual (desbalancea el DOM: cierra #pairing-prompt-ui antes de tiempo).
2. `frontend/app.js:1287`: eliminar `toggleManualToken()` (referencia a un nodo que ya
   no existe).
**Aceptación:** conteo de `<div`/`</div>` balanceado en el bloque onboarding; grep
toggleManualToken -> 0; node --check OK.

### C-03 — [ALTO] Revertir location.reload() del heartbeat (commit a87287b, parte app.js)
Si el backend está caído, recarga la PWA cada 10s en bucle (batería, flashes, pierde
estado) y pisa el backoff exponencial existente. La reconexión debe ser SILENCIOSA:
ws.onclose ya reintenta con backoff; el banner solo tras varios fallos visibles.
**Fix:** quitar el `else if (!ws || ws.readyState === WebSocket.CLOSED) location.reload()`.
El meta refresh de status.html (panel TV) SE QUEDA.
**Aceptación:** con backend apagado y app abierta, NO hay recargas (observar 60s);
al volver el backend, reconecta solo.

### C-04 — [ALTO] G-11: pactl necesita el entorno de la sesión de usuario
En Appliance (system service) no hay XDG_RUNTIME_DIR -> pactl no encuentra
PipeWire/Pulse -> excepción silenciosa -> la señal de audio NUNCA funciona justo en el
modo para el que se creó.
**Fix:** pasar `env=kiosk.gui_env()` al subprocess de pactl; sustituir el `except: pass`
por un `logger.warning` UNA sola vez (flag de módulo) si pactl falla o no existe.
**Aceptación:** en Appliance mode con audio sonando (VLC manual), journalctl muestra
detección y el panel NO se lanza.

### C-05 — [ALTO] G-09: el trust del CA corre antes de que exista ca.pem
En fresh install, run.py genera certs/ca.pem al PRIMER arranque del backend; el bloque
de certutil corre antes -> `if [ -f ca.pem ]` falso -> no-op silencioso.
**Fix:** mover el bloque de trust DESPUÉS del arranque del servicio en install.sh, con
espera activa de hasta 30s a que aparezca ca.pem (bucle con sleep 2). Si no aparece:
`[!]` warning claro y continuar.
**Aceptación:** fresh install (o simulación borrando certs/) termina con lrp-ca.crt en
/usr/local/share/ca-certificates/ y la entrada "LRP CA" en el nssdb del usuario.

### C-06 — [MEDIO] Escribir LRP_MODE en backend/.env
El backend ya lee LRP_MODE (G-01) pero NADIE lo escribe -> el panel dirá siempre "TV".
**Fix:** en install.sh, tras decidir el modo (variable `mode`), persistirlo en
backend/.env con la misma técnica grep/sed usada para KEYBOARD_LAYOUT.
**Aceptación:** install en modo Desktop -> .env contiene LRP_MODE=desktop y el panel
muestra "Escritorio".

### C-07 — [MEDIO] Completar G-03: AltGr + tabla es/latam completa
1. **Bug bloqueante:** KEY_RIGHTALT=100 NO está en las capabilities del UInput
   (range(1,100) llega a 99). Añadirlo explícito a la lista de keys.
2. Extender el formato del mapa a (key, shift, altgr) o dict, y `type_text` para pulsar
   KEY_RIGHTALT cuando toque.
3. Completar overrides es/latam: `@` (latam: AltGr+Q; es: AltGr+2), `&` (Shift+6),
   `(` (Shift+8), `)` (Shift+9), `+` y `*` según layout. Documentar en .env.example los
   valores válidos de KEYBOARD_LAYOUT y los símbolos no soportados.
**Aceptación:** con KEYBOARD_LAYOUT=latam, escribir `usuario@mail.com (test) & "ok"`
reproduce exactamente eso en el HTPC; py_compile OK.

### C-08 — [MEDIO] G-13: el guard se anula a sí mismo con IGNORE_CLASSES gigante
El script no extrae las clases definidas en los bloques `<style>` INLINE de
index/status/pair.html -> decenas de clases legítimas (stat-card, qr-box...) acabaron en
IGNORE_CLASSES junto con utilidades REALES como `hidden` (¡la clase del bug original!),
`max-w-xs`, `w-8`... Con eso, la próxima deriva de esas clases pasa en silencio otra vez.
**Fix:**
1. extract_defined_classes(): extraer también selectores de los `<style>...</style>`
   de los HTML de USAGE_FILES.
2. Reducir IGNORE_CLASSES al mínimo real (solo clases generadas por JS externo o estados
   dinámicos), cada una con comentario de justificación. PROHIBIDO ignorar utilidades
   tailwind reales.
3. Soportar `classList.add('a','b')` multi-argumento.
4. Mensaje de error: la ruta correcta es frontend/tailwind-lite.css (no frontend/css/).
5. Cosmético: dedupe de `.hidden` (definida en línea 3 y ~246 de tailwind-lite.css).
**Aceptación:** check pasa con IGNORE <15 entradas justificadas; prueba negativa: quitar
`.hidden` del CSS -> el check FALLA (antes pasaba en silencio).

### C-09 — [BAJO] G-04: ack faltante en browser_back
La rama `if name == "browser_back"` no envía `{"status":"received"}` (las demás sí).
Unificar.

### C-10 — [ALTO] Definir las 60 utilidades que el guard destapó (audit del bache 2026-07-14)
El check C-08 ahora FUNCIONA y falla con 60 clases usadas pero sin definir (bg-black/30,
max-w-xs, space-y-2, w-8/h-8, focus:border-blue-500, hover:*, etc. — lista exacta:
ejecutar `python scripts/check_css_sync.py`). Son deriva REAL que G-13 escondió en el
IGNORE viejo en vez de definir; incluye clases del onboarding (posible causa parcial de
G-15). **Fix:** compilar/añadir las 60 definiciones a frontend/tailwind-lite.css (mismo
método del binario standalone de Tailwind usado en G-13, o a mano — son utilidades
estándar). PROHIBIDO volver a meterlas en IGNORE_CLASSES.
**Aceptación:** `python scripts/check_css_sync.py` -> exit 0 con IGNORE_CLASSES = 4
entradas actuales; sw.js CACHE bump si no se hizo ya en este ciclo (está en lrp-v16, OK).

### C-07-bis — [BAJO] Documentación pendiente de C-07
En backend/.env.example: documentar KEYBOARD_LAYOUT (us|es|latam, default us) y los
símbolos NO soportados en es/latam (`<` `>` requieren KEY_102ND; corchetes/llaves vía
AltGr no cubiertos). 5 minutos.

### G-17 — Iconos confusos (ex G-05 del plan, NO ejecutada)
Ver especificación en la sección G-05 renumerada de FASE A (borrar=⌫ "delete" Lucide,
nav=cruz de 4 flechas, panel estado="activity"). Sin clases CSS nuevas sin definir.

### G-18 — Detector de apps: incluir terminales (ex G-06 del plan, NO ejecutada)
Ver especificación en la sección G-06 renumerada de FASE A (excepción TerminalEmulator
antes del filtro SKIP_CATEGORIES en discovery.py:16).

---

### G-14 — Release v1.6.0 (WSL) — SOLO tras auditoría OK de C-01..C-09 + G-17 + G-18
1. VERSION -> 1.6.0; CHANGELOG.md con todo lo anterior.
2. WSL, clon fresco: build_deb.sh; .deb + .sha256 a website/downloads/; borrar el 1.5.0.
3. website/latest.json: version "1.6.0" (sin prefijo v), deb_url nuevo, sha256 REAL
   (sha256sum, no inventado), notes.
4. Commit + push. Verificar EN VIVO: curl latest.json -> 1.6.0; deb -> 200; sha256 match.
5. Instalar en HTPC y smoke-test: panel completo, Brave+Shields, PIN, teclado "/",
   atrás, Home, idle panel con video manual.

---

## FASE D — REQUIERE INFO DEL DISPOSITIVO (no arrancar sin datos del dueño)

### G-15 — Límites de pantalla en móvil (barra de estado tapa UI + scroll lateral)
El safe-area YA existe (index.html:6 viewport-fit=cover; :20 body padding env(); :102
header max(env,8px)) y aun así falla en el teléfono del dueño. NO adivinar.
**Necesito del dueño:** modelo de teléfono + OS + navegador de instalación + screenshot.
Hipótesis a validar: (a) clase CSS faltante (deriva -> G-13 puede destaparlo), (b) elemento
más ancho que viewport que fuerza scroll lateral y desplaza el layout, (c) PWA instalada
antes del fix v1.5 conserva shell viejo (sw.js cache) -> reinstalar.

### G-16 — PWA se instala sin icono
manifest.json correcto (192/512 any+maskable) y apple-touch-icon presente (index.html:10).
Hipótesis principal: en Android, la instalación desde origen con cert self-signed NO
genera WebAPK (Google no puede validar el manifest de un host LAN) -> Chrome cae a
shortcut con icono genérico. En iOS debería funcionar (apple-touch-icon).
**Necesito del dueño:** ¿en qué teléfono/navegador falta el icono? Si es Android+Chrome,
es limitación de WebAPK con cert local: documentar y mitigar (icono monocromo? shortcut
igual usa apple-touch-icon en algunos launchers). Evaluar y decidir con evidencia.

---

## FASE E — ROADMAP V2.0: APK ANDROID (evaluación de Claude, 2026-07-14)

Idea del dueño (anotada por Gemini en CURRENT.md): APK Android con las funciones
complejas (voz, botones físicos de volumen, auto-conexión) dejando la PWA como "Lite".

**Veredicto: APROBADA para roadmap v2.0.** La idea ataca limitaciones REALES e
irresolubles de la PWA: getUserMedia bloqueado en orígenes no confiables, WS suspendido
en reposo, sin acceso a botones de volumen, sin mDNS.

**Matiz de seguridad IMPORTANTE (corregido 2026-07-14):** NO usar `ws://` plano como
bypass. OJO: networkSecurityConfig estático NO sirve — la CA se genera POR HTPC en el
primer arranque (cada cliente tiene una distinta). Diseño correcto: **TOFU pinning** —
al emparejar, la app descarga ca.pem del HTPC (/api/ca ya existe) y lo persiste; el
WebView valida TLS en onReceivedSslError aceptando SOLO certs que encadenen a esa CA.
WSS cifrado, sin interstitials, sin instalación manual, sin claro en la LAN.
Stack decidido: Capacitor (frontend actual EMBEBIDO en el APK; origen https://localhost
= contexto seguro -> getUserMedia funciona con permiso RECORD_AUDIO nativo).
Extra HTPC: publicar _lrp._tcp en avahi (archivo en /etc/avahi/services/ vía install.sh)
para NSD discovery. Fases: F0 prerrequisitos (v1.6 estable + ai-proxy) -> F1 esqueleto
Capacitor+WSS TOFU+PIN -> F2 nativo (NSD, volumen físico, foreground service, mic) ->
F3 voz vía ai-proxy -> F4 distribución (APK firmado en web + apk_url en latest.json;
keystore FUERA del repo con backup) -> F5 Play Store opcional. iOS sigue con PWA Lite.

**Alcance estimado (wrapper, NO reescritura):**
- Capacitor sobre la PWA existente (misma base de código frontend).
- Plugins nativos: NSD/mDNS (autodescubrimiento del HTPC), RECORD_AUDIO (voz sin
  restricciones), volumen físico -> media keys, foreground service (WS persistente:
  adiós al problema de reposo... en Android; iOS se queda con la PWA Lite).
- Distribución: APK directo desde la web (sideload) o Play Store (revisar políticas).

**Prerrequisitos (en orden):** 1) v1.6.0 estable en el HTPC del dueño; 2) ai-proxy
Edge Function (T4 heredada — sin ella el APK con voz embarca claves); 3) plan detallado
propio (PLAN_GEMINI_v2.0.md) auditado antes de escribir código.

---

## CHECKLIST DEL DUEÑO (no-código, hacer YA — desbloquea G-14 y explica B-07)

- [ ] `git push` — CRÍTICO: el fix de latest.json (commits 165cf4b/e0865f1) está commiteado
      pero si no llegó a Vercel, el botón "Actualizar" del móvil seguirá muerto: el backend
      lee https://linux-remote-player.vercel.app/latest.json y el deployado estaba roto.
- [ ] `supabase functions deploy send-feedback --no-verify-jwt` (aún sin confirmar).
- [ ] Para G-15/G-16: modelo de teléfono, OS, navegador y screenshots del problema de
      pantalla y del icono faltante.
- [ ] Probar tras el push: Ajustes -> Buscar actualización (debe decir "estás al día", ya
      no fallar en silencio).

## PROTOCOLO DE AUDITORÍA (Claude)
Tras cada tarea: alcance respetado, criterios con EVIDENCIA (salida de comandos), sin
secretos ni binarios inesperados, sin regresión del modelo de auth, CURRENT.md al día.
Veredicto APTO -> siguiente. NO APTO -> correcciones.
