# PLAN DE TRABAJO — GEMINI (v1.7.1: correcciones del testing intensivo)

```yaml
plan_id: PLAN_GEMINI_v1.7.1
date: 2026-07-17
author: Claude — triaje del testing intensivo del dueño (.agents/TESTING.md +
  output_instalation.md + capturas en .agents/capturastesting/)
executor: Gemini 3.5 Pro
flujo: BACHE — T-01..T-10 seguidas, un commit por tarea, evidencia real de comandos;
  STOP al terminar -> auditoría Claude -> T-12 (release v1.7.1)
bonus: la release v1.7.1 sirve para probar el botón OTA end-to-end (ítem H3 pendiente)
reglas: las de siempre (ver planes anteriores) — alcance estricto, sin secretos,
  archivos grandes con lectura verificada, evidencia pegada en bitácora de CURRENT.md
```

## HALLAZGO RAÍZ DEL INSTALADOR (explica A3+A6+D2+D4-parcial de la matriz)
En el HTPC del dueño, `certutil -A` pidió password interactivo
(`Enter Password or Pin for "NSS Certificate DB":`, output_instalation.md:197) porque
su nssdb ya existía con contraseña. El install QUEDÓ COLGADO ahí. Todo lo que va
DESPUÉS de ese bloque en install.sh nunca corrió: escritura de policies.json (por eso
NO hay uBlock), lanzamiento del panel, mensajes finales. Un solo bug, cuatro síntomas.

---

## T-01 — [CRÍTICO] install.sh: certutil no-interactivo + reordenar bloques
1. REORDENAR: escribir `/etc/firefox/policies/policies.json` ANTES del bloque certutil
   (no depende de él en nada; uBlock/DRM/CA-policy no pueden quedar rehenes de NSS).
2. certutil SIEMPRE no-interactivo: crear pwfile temporal vacío
   (`PWFILE=$(mktemp); echo "" > "$PWFILE"`) y usar `-f "$PWFILE"` en TODAS las llamadas
   certutil, ademas de `< /dev/null` como cinturón. Si la importación falla (nssdb con
   contraseña real del usuario) -> `[!]` warning claro y CONTINUAR (el kiosk Firefox usa
   policies, no NSS; NSS solo cubre el fallback chromium/brave). rm del pwfile.
3. Verificar que el lanzamiento del panel y los mensajes finales queden DESPUÉS y se
   ejecuten siempre.
**Aceptación:** bash -n OK; simulación: nssdb preexistente con password -> install
termina SOLO sin pedir input, policies.json existe, warning visible.

## T-02 — [ALTO] Flujo final del instalador orientado a PIN + investigar "pantalla de error" del ?token=
1. Mensaje final del install: liderar con el flujo que SÍ funciona:
   "1) En tu teléfono abre https://<host>.local:8000  2) Acepta el certificado (una vez)
    3) Escribe el PIN que muestra el panel de tu TV". Los enlaces con ?token= quedan
   como alternativa avanzada, no como principal.
2. Investigar la "pantalla de error" al abrir la URL con ?token= (reporte A6/D4):
   app.js initToken() se ve correcto (guarda token y limpia URL). Hipótesis: interstitial
   de Safari por cert aún no aceptado. Revisar si el flujo con ?token= en un dispositivo
   SIN cert aceptado puede caer en un estado raro (p.ej. WS falla -> pantalla de error
   propia). Si no es reproducible en código, documentar pasos de repro para el dueño y
   dejar hallazgo anotado.
**Aceptación:** mensajes nuevos en install.sh (bash -n OK); análisis de ?token=
documentado en la bitácora con conclusión.

## T-03 — [MEDIO] Bootstrap encadena lrp-setup automáticamente
Hoy el .deb termina con "Ejecuta: sudo lrp-setup" y el dueño debe teclearlo (A4).
En el install.sh del WEBSITE (bootstrap): tras instalar el .deb con éxito, ejecutar
`lrp-setup` directamente (ya corre con sudo y con tty — usar el patrón
`exec < /dev/tty` existente). Mantener el mensaje como fallback si no hay tty.
**Aceptación:** bash -n del install.sh del website; flujo: curl|sudo bash -> preguntas
de lrp-setup aparecen sin paso manual.

## T-04 — [BAJO] UFW: perfil OpenSSH inexistente da ERROR feo
output_instalation.md:177. Cambiar a: `ufw allow OpenSSH 2>/dev/null || ufw allow 22/tcp || true`.
**Aceptación:** bash -n OK; en sistema sin perfil OpenSSH no imprime ERROR.

## T-05 — [ALTO] Frontend: layout desborda en pantallas cortas 16:9 (iPhone 8 Plus)
Evidencia: capturas app_barra_desplazamient_bajada.jpeg (fila de mute cortada abajo,
scrollbar vertical) y notas F2/F5. El alto total excede el viewport en pantallas 16:9
-> aparece scroll, los botones inferiores se cortan y el usuario percibe que la barra
de estado "tapa" el header al hacer scroll.
1. Media query por ALTURA (p.ej. `@media (max-height: 750px)`): reducir min-height del
   touchpad, paddings/gaps de las filas, tamaño de botones circulares.
2. El contenedor raíz NO debe scrollear: la app completa cabe en 100dvh (flex con
   shrink en el touchpad, que es el único elemento elástico).
3. Revisar clipping en Ajustes (captura panel_ajustes_premium.jpeg): botón "Buscar" y
   enlace "Descargar Certificado CA" se cortan en el borde de su card.
4. OJO deriva CSS: cualquier clase nueva pasa por check_css_sync.
**Aceptación:** en viewport 414x736 (iPhone 8 Plus, DevTools) TODAS las filas visibles
sin scroll y sin corte; check_css_sync exit 0; node --check OK.

## T-06 — [MEDIO] Coach marks: el tooltip tapa su propio objetivo
Evidencia: tutorial000_error_de_ubicacion_primer_aparicion.jpeg — el tooltip "Tus apps
favoritas" cubre la fila de apps que señala. Posicionar el tooltip para NUNCA solapar
el elemento destacado (arriba/abajo según espacio disponible; recalcular tras layout).
El dueño reporta que en segunda ejecución no pasa -> probable carrera con el layout
inicial: lanzar el tour tras `requestAnimationFrame`/load completo.
**Aceptación:** primera ejecución en viewport corto -> tooltip no tapa su objetivo.

## T-07 — [MEDIO] Nav-mode: overlay debe comunicar "desliza", no parecer botones
Reporte C6: la cruz de flechas superpuesta no se entiende (parece clickeable).
Rediseñar overlay: flechas en los 4 bordes + hint textual/animación breve "Desliza
para navegar · toca para OK" la primera vez; estética de guía, no de botonera.
**Aceptación:** juicio visual del dueño en el siguiente smoke; sin clases CSS sin definir.

## T-08 — [BAJO] Indicador de latencia en el HUD del teléfono (petición C7)
El heartbeat ya hace ping/pong cada 10s: medir RTT y mostrar "XX ms" discreto junto al
estado "Connected" (color: verde <60ms, ámbar <150, rojo resto).
**Aceptación:** visible en la app, se actualiza; node --check OK.

## T-09 — [MEDIO] Favicons de apps: basura y logo equivocado (D8)
Evidencia: captura ...animeav1_sin_favicon.jpeg (tile con imagen ilegible).
1. Apps del SISTEMA añadidas al menú: usar SIEMPRE /api/icon del backend (nunca la
   cadena google/ddg — eso causó el logo LRP en una app de sistema).
2. Webs custom: si el favicon resuelto no carga o es inválido -> fallback de LETRA
   (inicial del nombre sobre color derivado del nombre), NUNCA el logo LRP.
**Aceptación:** añadir web sin favicon válido -> tile con letra; app de sistema ->
icono correcto del sistema.

## T-10 — [BAJO] Icono PWA en iOS muestra letra "R" (F1; iPhone 8 Plus, iOS 18, Safari)
1. Verificar dimensiones reales de frontend/apple-touch-icon.png -> debe ser 180x180
   (regenerar desde icon-512 si no).
2. `<link rel="apple-touch-icon" sizes="180x180" href="apple-touch-icon.png">` en
   index.html Y en pair.html (iOS toma el icono de la página desde la que se instala).
**Aceptación:** `python -c "from PIL import Image; print(Image.open('frontend/apple-touch-icon.png').size)"`
-> (180,180) (o herramienta equivalente); links presentes en ambos HTML.

## T-11 — [DUEÑO, config — NO es bug] El micrófono "desaparecido" (G1/G3/G4)
La captura panel_ajustes_premium.jpeg lo dice: "Voz con IA: se activará al configurar
el servicio". El HTPC recién formateado tiene ENABLE_VOICE=false (las llaves de
Together.ai quedaron en el .env del PC de desarrollo, no del HTPC).
DUEÑO: en el HTPC editar /opt/linuxremoteplayer/backend/.env ->
ENABLE_VOICE=true + CLOUD_STT_URL/KEY/MODEL + CLOUD_LLM_URL/KEY/MODEL, y
`sudo systemctl restart linuxremoteplayer`. Después re-probar G1/G3/G4.
(Solución definitiva sin llaves en dispositivo = ai-proxy, v1.9.)

## T-13 — [ALTO] Voz: condición de carrera deja grabaciones huérfanas en iOS (añadida 2026-07-17)
**Causa raíz confirmada (app.js:577-616):** startVoice() es async (await getUserMedia
tarda 200-500ms en iOS); si el pointerup llega ANTES de que resuelva, stopVoice() no
encuentra recorder activo -> la grabación arranca DESPUÉS con el dedo fuera y nadie la
detiene -> pastilla de mic de iOS queda encendida y el usuario debe matarla desde el
sistema. Además navigator.vibrate NO existe en iOS Safari (feedback actual invisible).
**Fix:**
1. Bandera `micHeld`: pointerdown=true, pointerup/pointercancel=false. Tras el await de
   getUserMedia: si !micHeld -> stream.getTracks().forEach(stop) y NO iniciar recorder.
2. Failsafe: setTimeout de 8s tras start() -> auto-stop y envío (limpiar el timer en
   el stop normal).
3. Overlay de grabación prominente (no solo el texto de status): mic pulsando + contador
   + "Suelta para enviar". Ocultar al parar.
4. Toque corto (<250ms entre down y up): cancelar SIN enviar + toast "Mantén pulsado
   para hablar".
5. pointerleave con el dedo fuera del botón -> cancelar sin enviar (patrón WhatsApp).
6. Sin clases CSS sin definir (check_css_sync).
**Aceptación:** en iOS: toque corto -> no graba, hint visible; mantener 3s y soltar ->
envía y la pastilla del sistema se APAGA sola; overlay visible durante la grabación;
grabación jamás supera 8s; node --check OK; check_css_sync exit 0.

## CORRECCIONES DE AUDITORÍA [Claude 2026-07-17] — antes de T-12

### TC-01 — [MEDIO] T-03: `exec` mata el fallback
En website/install.sh se cambió la llamada a lrp-setup por `exec lrp-setup || echo...`.
Si lrp-setup no existe/no es ejecutable, un bash NO-interactivo TERMINA en el exec
fallido y el `|| echo` jamás corre (fallback muerto, exit 127 silencioso). Además el
exec era innecesario: la llamada normal ya entregaba el tty.
**Fix:** volver a la llamada directa: `/usr/local/bin/lrp-setup || echo -e "..."`.
**Aceptación:** bash -n OK; sin `exec` en esa línea.

### TC-02 — [BAJO] T-10 quedó a medias (commit vacío solo "verificó")
El PNG sí es 180x180 (verificado por Claude leyendo el header). Pero la spec pedía
además: (1) `sizes="180x180"` en el link de index.html; (2) añadir el link
apple-touch-icon TAMBIÉN en frontend/pair.html (iOS toma el icono de la página desde
la que se instala). Nada de eso se hizo.
**Fix:** `<link rel="apple-touch-icon" sizes="180x180" href="apple-touch-icon.png">`
en index.html (reemplazar el actual) y pair.html (añadir).
**Aceptación:** grep apple-touch-icon -> presente en ambos HTML con sizes.

## T-14 — [CRÍTICO] OTA se suicida: el updater muere en el cgroup del servicio (H3 FALLA, 2026-07-18)
**Evidencia:** logs del dueño (lrp-update.log cortado en "Preparando para desempaquetar";
status: servicio detenido 23:51:23 y jamás reiniciado; sudo session closed en el MISMO
segundo del stop).
**Causa raíz (confirmada en build_deb.sh):** el backend corre como servicio systemd de
SISTEMA. /api/update/apply lanza `sudo lrp-update` con start_new_session=True — pero
setsid NO saca al proceso del CGROUP del servicio. lrp-update ejecuta apt-get sobre el
.deb; el prerm del paquete hace `systemctl stop linuxremoteplayer` -> systemd mata TODO
el cgroup (KillMode=control-group por defecto) -> dpkg muere a mitad de desempaquetado,
asesinado por el stop que él mismo provocó. (La hipótesis SSH del análisis de DeepSeek
es incorrecta: no hubo SSH; y nohup/screen NO escapan del cgroup — no usar.)
**Fix (en el lrp-update embebido en build_deb.sh):**
1. Al inicio del script: si `$LRP_DETACHED` no está definido y `systemd-run` existe:
   `exec systemd-run --collect --unit=lrp-update-job --setenv=LRP_DETACHED=1 \
    /usr/local/bin/lrp-update` -> re-ejecuta como UNIT TRANSITORIA (cgroup propio,
   sobrevive al stop del servicio). El script ya corre como root: no toca sudoers.
   Fallback sin systemd-run: continuar como hoy + warning en el log.
2. El logging debe sobrevivir al re-exec: dentro del script, redirigir su propia
   salida a /tmp/lrp-update.log (exec >>/tmp/lrp-update.log 2>&1 tras el re-exec),
   porque la unit transitoria escribe al journal, no al log del Popen.
3. Al final: `systemctl restart linuxremoteplayer` explícito (garantía de re-arranque).
**Aceptación:** disparar la actualización DESDE EL ENDPOINT (curl con token a
/api/update/apply, no desde terminal) -> dpkg completa, servicio vuelve activo,
/tmp/lrp-update.log completo hasta el final. `journalctl -u lrp-update-job` visible.
**⚠ HUEVO-GALLINA para el dueño:** el lrp-update INSTALADO (v1.7.x) sigue siendo el
buggy; la subida 1.7.1 -> 1.7.2 vía botón fallaría igual. Esa se hace con
`sudo lrp-update` desde terminal del HTPC. El botón (H3) se valida recién en la
actualización 1.7.2 -> 1.7.3 (o la siguiente que exista).

## T-12 — Release v1.7.1 (WSL) — SOLO tras APTO de Claude a TC-01 y TC-02
Procedimiento estándar (clon fresco, sha256 real, verificación en vivo con salidas).
EXTRA: el dueño probará la actualización 1.7.0 -> 1.7.1 CON EL BOTÓN de la app
(ítem H3 de la matriz) — NO reinstalar a mano esta vez.

---

## BUGS POST-RELEASE v1.7.2 (smoke del dueño en iPhone 8 Plus + iPhone 12, 2026-07-18)

### T-16 — [ALTO] Viewport iOS no determinista: layout distinto en frío vs relanzado
**Síntomas (capturas del dueño):**
- iPhone 12 (notch), 1er arranque: header ENTERO cortado por arriba (sin acceso a
  Ajustes) + hueco muerto abajo (HUD corrido hacia arriba). Al cerrar/reabrir: correcto.
- iPhone 8 Plus (sin notch), 1er arranque: barra de estado SUPERPUESTA al header
  (visualmente aceptable). Al cerrar/reabrir: la barra pasa a ocupar espacio físico,
  desplaza el HUD hacia abajo y recorta los botones inferiores.
**Diagnóstico:** bug clásico de PWA standalone en iOS: `window.innerHeight`/`100vh` y
los env(safe-area-inset-*) reportan valores distintos entre arranque frío y relanzado;
nuestro layout usa alturas fijas de viewport (body h-screen=100vh + overflow-hidden de
T-05) medidas UNA vez -> queda congelado con el valor que tocó. La meta
apple-mobile-web-app-status-bar-style="black" (barra opaca que ocupa espacio) se aplica
de forma inconsistente entre lanzamientos (iOS 18).
**Fix (dos capas, determinismo por diseño):**
1. Meta status-bar-style -> `black-translucent` (la barra SIEMPRE superpone, mismo
   comportamiento en todo lanzamiento) y compensar SIEMPRE:
   header padding-top: max(env(safe-area-inset-top), 20px) SOLO en modo standalone
   (media (display-mode: standalone)); en navegador mantener el actual.
2. Altura por JS en vez de 100vh congelado: setear una CSS var
   `--app-h = window.innerHeight px` en load + resize + orientationchange + pageshow
   (visualViewport.height si existe), y el contenedor raíz usa
   `height: var(--app-h, 100dvh)`. Así frío y relanzado convergen al valor real.
3. Verificar padding-bottom con env(safe-area-inset-bottom) para el home-indicator
   del iPhone 12 (el hueco de abajo debe desaparecer al corregir la altura).
**Aceptación:** en AMBOS iPhones: arranque frío y relanzado se ven IGUALES; Ajustes
accesible; sin recortes arriba/abajo; sin scroll; node --check + check_css_sync OK.

### T-17 — [MEDIO] Regresión de T-09: iconos de las apps SUGERIDAS rotos
**Evidencia:** capturas — Netflix/YouTube/Pluto/Kick/TikTok muestran todos el icono
genérico LRP. **Causa confirmada (app.js:724):** la condición
`!app.id.startsWith('custom_')` manda a las sugeridas a /api/icon/{id}; el backend
solo resuelve apps .desktop instaladas -> 404 -> onerror -> icon.svg.
**Fix:** decidir por TIPO, no por prefijo:
- app de sistema (viene de installed_apps / type 'native') -> /api/icon/{id}
- app con url (sugeridas Y customs) -> setTileFavicon (DDG -> S2 -> letra)
- resto -> letra. NUNCA icon.svg como fallback de marca (la letra es el fallback).
**Aceptación:** sugeridas muestran su favicon de marca de nuevo; apps de sistema
siguen con /api/icon; customs sin cambio; node --check OK.

### TC-03 — [BAJO] T-17 dejó las apps nativas ancladas SIN forma de quitarse
Auditoría Claude: los nativos anclados viven en custom_apps (renderApps:787) pero tras
T-17 no caen en ninguna rama de botón (762 exige prefijo 'custom_'; 769 excluye
is_native) -> quedan permanentes salvo borrar localStorage. (El botón "ocultar" que
tenían antes tampoco funcionaba: el filtro hidden solo aplica a kiosks, no a customs.)
**Fix (1 línea + verificación):** en createAppTile, la rama del botón ELIMINAR
(app.js:762) pasa a: `if (app.id && (app.id.startsWith('custom_') || app.is_native))`
— los nativos están en custom_apps, así que el handler de dataset.remove existente los
elimina igual que a las webs custom. VERIFICAR que ese handler filtra custom_apps por
id sin asumir prefijo.
**Aceptación:** anclar app de sistema -> tile con ×; × la quita y no reaparece tras
recargar; node --check OK.

### T-18 — Release v1.7.3 (tras APTO de T-16/T-17/TC-03) — ¡ESTA valida el BOTÓN OTA (H3)!
Procedimiento estándar. El dueño actualiza 1.7.2 -> 1.7.3 CON EL BOTÓN de la app:
primera prueba real del updater arreglado (T-14). Si el botón funciona, H3 queda OK
y el ciclo de testing intensivo se cierra.

### T-19 — [CRÍTICO] OTA parte 2: el prerm deshabilita el servicio y el restart final se salta (H3 PARCIAL, 2026-07-18)
**Evidencia (journal lrp-update-job del dueño):** T-14 FUNCIONÓ (dpkg completó, job
terminó limpio, ii 1.7.3). Pero al final: el prerm del .deb hizo `systemctl stop` +
`systemctl DISABLE`; lrp-update decide el restart con `if systemctl is-enabled...` ->
gate falso -> salta el restart de sistema -> cae a la rama --user -> "Unit not found"
(Appliance no tiene user service) -> servicio queda muerto y disabled.
**Fix (build_deb.sh, DOS capas):**
1. **prerm consciente del upgrade** (lo canónico Debian): dpkg pasa `$1`. Solo hacer
   stop+disable cuando `$1 = "remove"`. En upgrade: SOLO stop (dpkg lo necesita para
   reemplazar archivos), NUNCA disable. Aplicar a ambas variantes (system y --user).
2. **lrp-update decide por EXISTENCIA, no por is-enabled** (cinturón): tras el apt,
   `systemctl daemon-reload`; si existe /etc/systemd/system/linuxremoteplayer.service
   -> `systemctl enable linuxremoteplayer || true; systemctl restart
   linuxremoteplayer || true`; si no, buscar el user unit por archivo y hacer lo
   análogo con --user. El enable repara instalaciones ya dañadas por el prerm viejo.
**Aceptación:** extraer prerm y lrp-update de los heredocs -> bash -n OK; revisión de
flujo: upgrade NO deshabilita; restart incondicional por existencia + enable.
**HUEVO-GALLINA (documentar al dueño):** el update 1.7.3 -> 1.7.4 vía botón usará el
lrp-update DE 1.7.3 (cgroup bien, restart mal) -> dpkg completará pero el servicio
quedará caído: recuperar con `sudo systemctl enable --now linuxremoteplayer` (1
comando). El ciclo OTA 100% limpio se valida recién en 1.7.4 -> 1.7.5.

### T-20 — Release v1.7.4 (tras APTO de T-19). Procedimiento estándar.

### T-21 — [ALTO] PWAs instaladas no reciben los fixes: cache del SW congelado (hallazgo del dueño, 2026-07-18)
**Causa confirmada:** sw.js:1 = 'lrp-v16' SIN CAMBIOS desde v1.6. El SW sirve assets
(tailwind-lite.css, skins.css, iconos) cache-first: solo se refrescan si el NOMBRE del
cache cambia. Releases 1.7.1-1.7.4 cambiaron CSS sin bump -> PWAs instaladas quedan con
HTML nuevo + CSS viejo (Frankenstein): los fixes de layout "no llegan".
**Fix (automatizar, no depender de memoria humana):**
1. frontend/sw.js: `const CACHE = 'lrp-__LRP_VERSION__';` (placeholder).
2. scripts/build_deb.sh: tras copiar frontend/ al staging, reemplazar el placeholder
   con la versión real: `sed -i "s/__LRP_VERSION__/${VERSION}/" <staging>/frontend/sw.js`.
   Así CADA release cambia sw.js -> el navegador reinstala el SW -> assets frescos ->
   activate borra caches viejos (ya implementado).
3. Guard en build_deb.sh: tras el sed, `grep -q "lrp-${VERSION}" sw.js || exit 1`.
4. Dev sin build: el placeholder actúa como nombre constante — aceptable.
**Aceptación:** extraer el sw.js del staging de un build de prueba -> contiene
lrp-<VERSION>; guard falla si el placeholder no se reemplaza; node --check no aplica
(sw.js no es módulo, basta el grep).
**DOC (añadir nota en CHANGELOG/GUIA):** en iOS, los cambios de meta/manifest
(status-bar-style, iconos) se hornean AL INSTALAR la PWA -> tras updates que los
toquen, REINSTALAR la app en el teléfono (borrar + añadir a inicio).

### T-22 — Release v1.7.5 (tras APTO de T-21) — LA release de cierre total
Con el updater 1.7.4 ya sano instalado: esta actualización por botón debe completar
SIN intervención (H3 ✓ DEFINITIVO) y, con T-21, las PWAs instaladas recibirán los
assets frescos solos. Cierra el ciclo de testing intensivo.

### T-23 — [CRÍTICO] VOZ rota de punta a punta (reporte DeepSeek + diagnóstico Claude, 2026-07-19)
**23a — main.py:53 crashea el servicio con ENABLE_VOICE=true** (confirmado en repo):
referencia `ai_pipeline.NVIDIA_KEY`/`OPENROUTER_KEY`, inexistentes desde el refactor
b32101d (renombradas CLOUD_STT_KEY/CLOUD_LLM_KEY). DeepSeek lo hotfixeó SOLO en el
HTPC -> el próximo OTA lo revertiría. Fix en repo:
`if not ai_pipeline.CLOUD_STT_KEY or not ai_pipeline.CLOUD_LLM_KEY:` (grep confirma
que es el único sitio con nombres viejos).
**23b — iOS no soporta audio/webm** (causa raíz del "audio nunca llega"):
app.js:581 `new MediaRecorder(stream,{mimeType:'audio/webm'})` lanza NotSupportedError
en Safari/iOS -> catch silencioso (solo console.error) -> sin overlay ni grabación.
Fix frontend:
1. Detección: si `MediaRecorder.isTypeSupported('audio/webm')` -> webm; si no,
   probar 'audio/mp4'; si ninguno -> constructor SIN options (default del navegador).
   Guardar el mime elegido y usarlo en el Blob.
2. El catch de startVoice DEBE mostrar toast con el error (adiós fallos silenciosos).
Fix backend (ai_pipeline.py:57): dejar de hardcodear webm — detectar formato por
magic bytes del audio recibido (EBML 0x1A45DFA3 -> audio.webm/audio/webm; 'ftyp' en
offset 4 -> audio.m4a/audio/mp4; default webm) y armar el tuple files acorde
(Together/Whisper aceptan m4a).
**23c — observabilidad**: en main.py, al recibir mensaje binario por WS: logger.info
con el tamaño en bytes (la ausencia de este log costó una sesión de diagnóstico).
**Aceptación:** py_compile + node --check; grep NVIDIA_KEY|OPENROUTER_KEY en backend/
= 0; revisión del flujo mime en ambos lados.
**NOTA:** reconexiones WS cada 30-60s observadas por DeepSeek -> NO atacar aún
(probable pantalla del teléfono apagándose durante el monitoreo); vigilar en retest.

### T-24 — Release v1.7.6 (tras APTO de T-23). El dueño actualiza 1.7.4 -> 1.7.6 por
botón (valida OTA limpio de paso) y re-prueba la voz (el hotfix de DeepSeek en el
HTPC será reemplazado por el fix oficial idéntico — sin conflicto).

### T-26 — [ALTO] Voz fase final: el LLM inventa valores (reporte DeepSeek v1.7.6, 2026-07-19)
**Estado validado en vivo:** audio->backend ✓, magic bytes ✓, STT ✓ (whisper-large-v3),
LLM ✓ (Qwen2.5-7B-Instruct-Turbo — stack NUEVO ratificado, ya en .env/.env.example;
nemotron-streaming y los Llama-3.1 dan 400 en Together). FALLA: "Abre Netflix" ->
"App no reconocida"; "Sube el volumen" -> "Invalid media key". Causa: system_prompt
de ai_pipeline (~:111) no enumera valores válidos -> el LLM inventa.
**Fix (MEJORA sobre la propuesta de DeepSeek — no hardcodear la lista de apps en el
prompt: es la lección de la deriva CSS aplicada a prompts; se desincronizaría del
catálogo):**
1. parse_intent(transcription) -> parse_intent(transcription, valid_targets=None):
   main.py le pasa [k["id"] for k in SUGGESTED_KIOSKS] en el handler de voz.
   El system_prompt se construye DINÁMICO inyectando esa lista.
2. Prompt nuevo (base la de DeepSeek, con estos añadidos): lista dinámica de
   target_id; lista EXACTA de keys de media (KEY_VOLUMEUP, KEY_VOLUMEDOWN, KEY_MUTE,
   KEY_PLAYPAUSE, KEY_PLAY, KEY_PAUSE, KEY_STOP, KEY_NEXTSONG, KEY_PREVIOUSSONG,
   KEY_FASTFORWARD, KEY_REWIND); nota "user speaks Spanish; map synonyms
   (sube/baja volumen, pausa, silencio, adelanta...)"; los 5 ejemplos de DeepSeek.
3. DEFENSA server-side (por si el LLM igual alucina): en el handler de voz de
   main.py: target_id -> .lower().strip() antes de matchear; media key -> upper() y
   si no empieza con KEY_, anteponer KEY_ y validar contra whitelist. Si sigue sin
   matchear -> error claro.
4. UX de errores (pedido DeepSeek): los mensajes de error de voz al WS incluyen
   etapa: "Voz: error STT (400)" / "Voz: error LLM (400)" / "Voz: app 'X' no
   reconocida" — el usuario ve QUÉ falló.
**Aceptación:** py_compile; simulación textual del prompt generado pegada en
bitácora; revisión de las 3 defensas.

### T-25 (recordatorio, ya en PLAN.md PH14e) — Detector de apps abierto
discovery.py: eliminar SKIP_CATEGORIES (y la excepción TerminalEmulator, obsoleta);
MANTENER NoDisplay/Hidden. Dolphin y apps de sistema visibles.
**Aceptación:** py_compile; grep SKIP_CATEGORIES -> 0.

### T-28 — [ALTO] T-21 fase 2: la PWA no se auto-recarga al llegar el SW nuevo (dueño, 2026-07-19)
**Evidencia:** subida 1.7.5->1.7.6: el SW nuevo se instaló (cache versionado OK) pero
la página corriente siguió con assets viejos — el dueño tuvo que reinstalar la webapp.
Falta el eslabón estándar del patrón skipWaiting+claim: nadie recarga la página cuando
el SW nuevo toma control.
**Fix (en el script de registro del SW en index.html):**
1. Tras registrar: guardar `reg`; en `visibilitychange`->visible y en `pageshow`,
   llamar `reg.update()` (fuerza el chequeo del sw.js en cada vuelta al primer plano —
   crítico en iOS, que resume de snapshot sin navegación).
2. `navigator.serviceWorker.addEventListener('controllerchange', ...)`: recargar UNA
   vez con guard anti-bucle:
   `if (!window.__swReloaded) { window.__swReloaded = true; location.reload(); }`
3. Sin clases CSS ni cambios de layout.
**Aceptación:** node --check no aplica (script inline) -> revisión manual del bloque +
prueba negativa mental del guard. NOTA DE EXPECTATIVA para el dueño: la subida
1.7.6->1.7.7 AÚN mostrará el síntoma una última vez (la página corriente es la 1.7.6,
sin el listener) — basta CERRAR del multitarea y reabrir 1 vez (sin reinstalar).
Desde 1.7.7 en adelante: seamless total.

### TC-05 — [MEDIO] T-26 borró la acción 'search' sin autorización (auditoría 2026-07-19)
El diff de 66abb99 eliminó la rama `elif action == "search"` del handler de voz de
main.py Y quitó 'search' de las acciones permitidas del prompt. La spec pedía las 3
acciones + el ejemplo de search. Consecuencia: "busca X" (sin nombrar app) pierde su
camino directo.
**Fix:** restaurar la rama search del handler (la que estaba: quote_plus + kiosk a
youtube/results, con sus mensajes de éxito/error) y en el prompt: añadir 'search' a
Allowed actions + el ejemplo
`"busca recetas de cocina" -> {{"action": "search", "parameters": {{"search_query": "recetas de cocina"}}}}`.
**Aceptación:** py_compile; grep '"search"' presente en prompt y handler.

### T-29 — [MEDIO] Descubribilidad de comandos de voz (pedido del dueño 2026-07-19)
Problema: el usuario no sabe QUÉ se puede decir -> pide imposibles -> concluye que la
voz está rota. Fix en 3 capas (frontend):
1. OVERLAY del mic: debajo de "Suelta para enviar", línea pequeña de ejemplos:
   «Abre Netflix» · «Sube el volumen» · «Busca ...» (estática, gris, discreta).
2. AJUSTES: nueva card "Comandos de voz" (visible SOLO cuando el mic está visible,
   es decir voice habilitado + licencia). Contenido DINÁMICO — jamás hardcodear apps:
   - "Abrir apps:" + nombres desde lastSuggestedKiosks (fuente de verdad en memoria)
   - "Controles: subir/bajar volumen, silencio, pausa, siguiente, anterior,
     adelantar, rebobinar"
   - "Buscar: di 'busca ...' y lo que quieras (abre YouTube)"
3. PRIMERA VEZ que el mic aparece: toast único "Consejo: mantén pulsado el micrófono
   y di 'abre youtube'" (flag en localStorage).
Regla de siempre: cero clases CSS sin definir (check_css_sync).
**Aceptación:** node --check OK; check_css_sync exit 0; card usa lista dinámica
(grep: NO debe haber nombres de apps hardcodeados en el HTML de la card).

### TC-06 — [ALTO] T-29 NO APTO: 3 defectos (auditoría 2026-07-19)
1. app.js:188 llama showToast() — la función es toast() (app.js:65) -> ReferenceError
   en runtime al disparar el hint. Corregir la llamada.
2. Deriva CSS: leading-relaxed y max-w-[280px] usadas sin definir (el guard
   check_css_sync FALLÓ y la evidencia no se corrió). Definirlas en tailwind-lite.css
   (leading-relaxed: line-height 1.625; max-w-[280px] con selector escapado) — NO
   meterlas en IGNORE.
3. app.js: la inyección de #voice-apps-list usa allKiosks (customs+nativas que la voz
   NO reconoce) -> usar lastSuggestedKiosks (y moverla fuera de renderApps si hace
   falta: puede poblarse en loadApps tras recibir suggested_kiosks).
**Aceptación:** node --check OK; check_css_sync EXIT 0 (salida pegada); grep
showToast -> 0; la lista usa lastSuggestedKiosks.

### T-27 — Release v1.7.7 (T-25+T-26+TC-05+T-28+T-29+TC-06; tras APTO de TC-06). Estándar.
El dueño actualiza por botón y re-prueba los comandos que fallaron:
"Abre Netflix", "Abre Stremio"(*), "Sube el volumen", "Pausa".
(*) stremio solo funcionará si está en SUGGESTED_KIOSKS del backend.
CON ESO: TESTING INTENSIVO CERRADO.

## ÍTEMS DE MATRIZ QUE QUEDAN PENDIENTES (no son tareas de código)
- H3 se prueba con esta release (botón Actualizar).
- J1/J2 (desinstalación) tras probar H3.
- I1 (multi-teléfono) cuando haya segundo dispositivo; I4 (cambio IP) oportunista.
- C3/F4/G2/I2/I3: recomendados pero no bloqueantes; el dueño decide.
- Pregunta del dueño en sección B: SÍ — los curl de seguridad se pueden correr desde
  WSL del PC de trabajo (misma LAN). Ya quedaron [OK] igualmente.
```
