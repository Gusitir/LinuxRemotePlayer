# TESTING INTENSIVO — v1.7.0 (Firefox)

```yaml
doc_id: TESTING_v1.7
date: 2026-07-17
author: Claude (plan de pruebas) — ejecuta el dueño en HTPC + teléfono; Gemini corrige
reemplaza: TESTING.md de la raíz (obsoleto: Chromium, install por git clone) — eliminado
formato_resultado: marcar cada ítem [OK] / [FALLA: descripción] / [SKIP: motivo]
  y volcar los FALLA en la sección RESULTADOS al final. Claude convierte los FALLA
  en tareas del siguiente plan.
entorno_ref: HTPC Plasma Bigscreen (Wayland, Debian-based) + teléfono del dueño.
  Comandos require_local: ejecutarlos EN el HTPC. Comandos LAN: desde otra máquina.
```

## A. INSTALACIÓN (limpia e idempotente) [VERIFICAR output_instalation.md]

- [OK] A1. Instalación limpia: `curl -fsSL https://linux-remote-player.vercel.app/install.sh | sudo bash`
      termina sin errores. Preguntas: modo [S], suspensión [S], teclado [3 latam].
- [OK] A2. `which firefox || which firefox-esr` -> existe. `which chromium` -> VACÍO.
- [FALLA: No se cargo ublock verificar output_instalation.md] A3. `cat /etc/firefox/policies/policies.json` -> contiene uBlock, Certificates
      con ruta real del ca.pem, EncryptedMediaExtensions.
- [OK: El comando lrp-setup no se auto ejecuta terminada la primera fase de instalacion, aun necesita input del comando de parte del usuario] A4. `grep -E "LRP_MODE|KEYBOARD_LAYOUT" /opt/linuxremoteplayer/backend/.env`
      -> LRP_MODE=appliance y KEYBOARD_LAYOUT=latam.
- [OK] A5. `systemctl is-enabled sleep.target` -> masked (elegiste S en suspensión).
- [FALLA: Al terminar de me da dos enlaces con token de certificado, pero me manda a una pantalla de "error", sin el token me manda al navegador normal con la advertencia de certificado que hay que saltar dandole clic a "continuar inseguro", en la consola pide el imput de algo pero no deja meter input y no llego a entender del todo esta funcionalidad] A6. `ls /usr/local/share/ca-certificates/lrp-ca.crt` -> existe (CA en trust;
      requiere que el servicio arrancara y generara ca.pem en <30s).
- [SKIP: para una actualizacion ejecuto el comando de reinstalar] A7. Idempotencia: re-ejecutar el installer completo -> termina sin errores y sin
      duplicar (servicio, policies, .env sin líneas repetidas:
      `grep -c "^LRP_MODE" backend/.env` -> 1).
- [SKIP: no se que debo verificar, consultar output_instalation.md] A8. Dependencias: `which pactl wmctrl` y `which qdbus || which qdbus6` -> existen.
- [OK] A9. Reboot -> el servicio arranca solo: `systemctl status linuxremoteplayer` activo,
      panel de estado aparece en la TV tras ~45s de inactividad.

## B. SEGURIDAD / AUTH (desde OTRA máquina de la LAN, sin token) [Se puede ejecutar con WSL?]

- [OK] B1. `curl -k https://<IP>:8000/api/apps` -> 401/403 (require_token).
- [OK] B2. `curl -k -X POST https://<IP>:8000/api/kiosk/launch -H "Content-Type: application/json" -d '{"url":"https://example.com"}'`
      -> 401/403. NUNCA debe abrir nada en la TV.
- [OK] B3. `curl -k https://<IP>:8000/api/status` -> rechazado (require_local; solo 127.0.0.1).
- [OK] B4. `curl -k https://<IP>:8000/api/pairing-token` -> rechazado (require_local).
- [OK] B5. WS sin auth: conectar wss://<IP>:8000/ws sin frame de auth o token malo ->
      cierre con código 1008.
- [OK] B6. PIN brute-force: 6 intentos seguidos de PIN inválido en /api/pair ->
      bloqueado (límite 5/IP); el PIN expira a los 120s y es de un solo uso.
- [OK] B7. `curl -k https://<IP>:8000/health` y `/api/config` y `/api/ca` -> 200 (públicos
      por diseño; config NO debe filtrar el pairing token — inspeccionar respuesta).
- [OK] B8. Token en URL de emparejamiento: tras emparejar por PIN, verificar que la app
      funciona SIN mostrar nunca un campo de token manual (eliminado en G-02/C-02).

## C. INPUT / WS (teléfono emparejado)

- [OK] C1. Touchpad: mover, tap=click izq, long-press=click der (vibración), scroll lateral.
- [OK] C2. Teclado texto completo (layout latam): escribir en un editor del HTPC:
      `hola/mundo @correo.com (test) & "ok" ¿? ; : + * _ =` -> todo exacto.
      Anotar los que fallen (gap conocido: < > y corchetes AltGr — no soportados aún).
- [SKIP: No lo probe no pense que es necesario testearlo] C3. Texto largo: pegar/escribir >500 chars -> el backend lo trunca/rechaza sin
      crashear (límite del protocolo WS).
- [OK] C4. Media keys: volumen +/- y mute funcionan (audio.py vía wpctl/pactl);
      transporte ⏯ ⏮ ⏭ funciona en YouTube kiosk.
- [OK] C5. Atrás: en un video embebido de un sitio de terceros -> navega atrás, NO
      rebobina (BTN_SIDE). En página normal -> historia atrás.
- [CAMBIO: En este momento solo se sobrepone una cruz de flechas, no es feedback entendible del todo, debe quitar el PAD y poner las flechas mas claro y que tambien indique visualmente que es deslizable y no clicleable, luego funciona correctamente] C6. Nav-mode (D-Pad): flechas + Enter + Esc funcionan en una app leanback.
- [SKIP: no funciona el ublock, pero en si no experimento baja de latencia en ningun momento, estaria bien añadir un marcador de latencia en el mismo HUD del telefono] C7. Latencia bajo carga: abrir kiosk de página pesada con ads y, DURANTE la carga,
      mover el touchpad -> fluido, sin congelamientos (fix C-01). Repetir cambiando
      de app 3 veces seguidas.

## D. KIOSK / NAVEGADOR (Firefox)

- [OK] D1. Kiosk abre Firefox fullscreen (sin barra de URL). Perfil dedicado:
      `ls ~/.config/lrp-kiosk-ff` existe tras el primer launch.
- [FALLA: Consultar output_instalation.md] D2. uBlock activo: sitio con ads -> limpio. (Verificación fina: abrir kiosk a
      `about:support` y buscar uBlock en extensiones.)
- [SKIP: no tengo suscripcion de netflix] D3. Netflix/Max: reproduce (primer video puede tardar 1-2 min por Widevine).
- [PARCIAL: en el panel que se despliega automaticamente despues de la instalacion (el que aparece cuando detecta inactividad) se abre sin advertencia de certificado, pero en si la URL con token de la consola de instalacion no funciona y al finalizar la instalacion tampoco lanza automaticamente el panel de estatus y ademas pide ese pin de verificacion que no deja ingresar tampoco y no entiendo del todo para que es] D4. Panel /status en el HTPC -> SIN advertencia de certificado.
- [OK] D5. Sesiones: login en un sitio -> cambiar de app 3 veces -> login conservado.
- [OK] D6. Apps nativas: lanzar una del drawer (detectadas .desktop) -> abre; el
      TERMINAL aparece en el drawer (G-18).
- [OK] D7. Home x2: con 1 kiosk + 1 app abierta A MANO -> Home limpia TODO el
      escritorio. Repetir Home otra vez con nuevas ventanas -> vuelve a funcionar
      (fix FC-01 del script KWin).
- [PARCIAL: el favicon a veces es erroneo no se si es por la misma pagina, en una ocacion añadi una app del sistema y le puso el logo de nuestra app (LRP)] D8. Custom app: añadir una web custom desde el móvil -> tile con favicon
      (o fallback), lanza en kiosk.

## E. PANEL DE ESTADO / IDLE

- [OK] E1. Panel muestra: versión 1.7.0, latencia en ms, modo "TV", clientes conectados,
      uinput OK, badge "uBlock (Firefox)", licencia correcta, QR escaneable.
- [OK] E2. Enlace de compra clicable con el puntero virtual.
- [OK] E3. Idle: sin clientes y sin audio -> panel aparece a los ~45s. Con video
      reproduciéndose en app abierta A MANO (VLC/navegador manual) y teléfono en
      reposo -> NO aparece (pactl). `journalctl -u linuxremoteplayer | grep -i pactl`
      -> sin warnings de pactl ausente.
- [OK] E4. Mantenimiento del panel: botón de actualización visible; tutorial de cambio
      de modo presente.

## F. PWA (teléfono)

- [PARCIAL: aun muestra una letra R en ios18 con safari iphone8plus, no probe en android] F1. Instalación fresca de la PWA (borrar la vieja primero) -> icono correcto en
      home screen (SI FALLA: anotar modelo+OS+navegador -> alimenta G-16).
- [FALLA: ver screenshot] F2. Límites de pantalla: barra de estado del teléfono NO tapa el icono de
      Ajustes; sin scroll lateral; botones inferiores completos (SI FALLA: screenshot
      -> alimenta G-15).
- [OK] F3. Reconexión: apagar pantalla 2 min -> encender -> reconecta sola en <5s sin
      recargar la página; sin bucles de recarga (fix C-03).
- [SKIP: no lo vi necesario] F4. Offline: modo avión -> la app abre (shell cacheado lrp-v16) y muestra estado
      de desconexión razonable, no pantalla blanca.
- [OK: pero tiene barra lateral de desplazamiento, sospecho que por un error universal con la barra de estado] F5. Onboarding: en un teléfono/navegador nuevo -> pantalla de PIN únicamente
      (sin opción de token manual); PIN del panel empareja correctamente.
- [OK] F6. Iconos nuevos: borrar texto = ⌫, nav = cruz de flechas, panel = pulso;
      estilo visual convive bien con el resto (juicio del dueño).
- [OK] F7. Skins: cambiar skin (con licencia Pro) -> aplica y persiste tras recargar.
- [PARCIAL: Funciona correctamente, pero mira una screenshot, el primer mensaje tapa el recuadro que quiere mostrar (el de las apps) esto pasa en primera ejecucion, sospecho que por el error con la barra de estado, porque en segunda ejecucion no pasa este error] F8. Coach marks / tour de primera vez: se muestra una vez y no vuelve a molestar.

## G. LICENCIA / VOZ

- [PARCIAL: el micronofo no aparece, creo que esta oculto tras la capa de los botones] G1. Activar licencia desde el móvil -> "Licencia activada"; micrófono aparece;
      panel de la TV refleja "Activa (Pro)" sin reiniciar.
- [SKIP: no crei necesario] G2. Gracia offline: desconectar internet del HTPC (no la LAN) -> la voz/skins
      siguen funcionando (cache 72h). Reconectar.
- [FALLO: sin el boton de micro no puedo probar esta feacture] G3. Voz cloud (Together.ai configurado): "pon videos de gatitos en youtube" ->
      transcripción + kiosk correcto. Probar también un comando inválido -> error
      claro, sin crash.
- [SKIP: Sin boton de microfono] G4. Sin licencia (otro teléfono/token regenerado): micrófono oculto; enviar
      audio por WS a mano -> rechazado.

## H. OTA / ACTUALIZACIÓN

- [OK] H1. Ajustes -> Buscar actualización -> "estás al día" (1.7.0 == 1.7.0).
- [SKIP: no vi necesario probar] H2. `curl -s https://linux-remote-player.vercel.app/latest.json` -> 1.7.0,
      sha256 4fff1722...4833.
- [OK ✓ DEFINITIVO 2026-07-19: boton 1.7.4->1.7.5 limpio — encontro, instalo,
  desconecto/reconecto "muy rapido", sin comandos. Costo 3 bugs encontrados y
  matados en el camino: cgroup suicide (T-14), prerm disable (T-19), gate
  is-enabled (T-19). El pipeline OTA que usara cada cliente esta VALIDADO.] H3.
      Flujo completo: Buscar -> Actualizar -> el servicio se reinicia y la app
      reconecta sola.

## I. ESTRÉS / RESILIENCIA

- [PENDIENTE: por el momento no dispongo de segundo dispositivo movil, quiza mas tarde] I1. 2-3 teléfonos conectados a la vez -> input de todos funciona; contador de
      clientes del panel correcto; desconectar uno no afecta al resto.
- [SKIP: no crei necesario] I2. 20 reconexiones seguidas (pantalla on/off del teléfono) -> sin degradación,
      sin procesos zombie: `pgrep -c firefox` estable tras Home.
- [SKIP: no crei necesario] I3. Reinicio del servicio con la app abierta: `sudo systemctl restart
      linuxremoteplayer` -> la app reconecta sola con backoff, sin intervención.
- [PENDIENTE: no tuve oportunidad de probar esto, quiza cuando se cambie la IP en algun momento de desarrollo lo vemos, mientras en pendientes] I4. Cambio de IP (reconectar WiFi del HTPC o DHCP nuevo) -> run.py regenera leaf,
      servicio se reinicia, `https://<hostname>.local:8000` sigue funcionando y el
      panel NO muestra advertencia de cert (CA estable).
- [OK] I5. Maratón: 2h de reproducción continua -> sin suspensión (A5), sin caída de
      WS, memoria del backend estable (`systemctl status` / `top`).

## J. DESINSTALACIÓN

- [PENDIENTE: antes probaremos el boton de actualizar] J1. `sudo ./scripts/uninstall.sh` -> servicios fuera, `systemctl is-enabled
      sleep.target` -> vuelve a normal (unmask), reglas udev y UFW limpias.
- [PENDIENTE] J2. Re-instalar tras desinstalar -> todo vuelve a funcionar (A1-A9 rápido).

---

## RESULTADOS — TRIADOS POR CLAUDE [2026-07-17]

```
Fecha ejecución: 17/07/26 | Balance: 28 OK · 4 FALLA · 4 PARCIAL · 1 CAMBIO · resto SKIP/PENDIENTE
Veredicto global: núcleo SÓLIDO (seguridad 8/8, input, kiosk, panel, idle, Home, sesiones).
Todas las fallas tienen causa raíz identificada -> plan .agents/PLAN_GEMINI_v1.7.1.md
```

MAPEO FALLA -> TAREA (detalle en PLAN_GEMINI_v1.7.1.md):
- A3 + A6 + D2 + D4(parcial) -> T-01 [CRÍTICO]. CAUSA RAÍZ ÚNICA confirmada en
  output_instalation.md:197: certutil pidió password del NSS db (tu nssdb ya tenía
  contraseña) y el install QUEDÓ COLGADO ahí — ese era el "input que no deja meter".
  Todo lo posterior nunca corrió: policies.json (por eso NO uBlock), lanzamiento del
  panel, mensajes finales. Fix: certutil no-interactivo + policies ANTES de certutil.
- A6/D4 (enlaces ?token= -> "pantalla de error") -> T-02: mensaje final orientado a
  PIN + investigación (el código de ?token= en app.js es correcto; hipótesis:
  interstitial de cert de Safari). El "pin de verificación que no deja ingresar" de la
  consola era el MISMO prompt de certutil de T-01.
- A4 (lrp-setup manual) -> T-03: bootstrap lo encadena automáticamente.
- Output línea 177 (ERROR perfil OpenSSH de UFW) -> T-04.
- F2 + F5 + F8(parcial) -> T-05 [ALTO]: el layout DESBORDA verticalmente en pantallas
  16:9 (iPhone 8 Plus 414x736): fila de mute cortada + scrollbar (capturas). No es la
  barra de estado: es alto total > viewport. + clipping en cards de Ajustes.
- F8 (tooltip tapa las apps que señala, captura tutorial000) -> T-06.
- C6 (cruz de nav-mode no comunica "desliza") -> T-07.
- C7 (petición: indicador de latencia en HUD) -> T-08.
- D8 (favicon basura en animeav1; logo LRP en app de sistema) -> T-09.
- F1 (icono "R" en iOS 18 / iPhone 8 Plus / Safari) -> T-10: apple-touch-icon 180x180
  + sizes + link también en pair.html.
- G1/G3/G4 (micrófono ausente) -> T-11 [NO ES BUG]: el HTPC formateado tiene
  ENABLE_VOICE=false — la captura lo dice: "Voz con IA: se activará al configurar el
  servicio". Las llaves quedaron en el .env del PC de desarrollo. Acción del dueño.
- E1 nota de Claude: el badge "uBlock (Firefox)" no pudo estar OK con A3 en falla —
  re-verificar badge tras T-01 (probablemente decía "Inactivo").

PENDIENTES DE MATRIZ (no-código): H3 se prueba con el release v1.7.1 usando EL BOTÓN
de la app (no reinstalar); luego J1/J2. I1 con segundo teléfono; I4 oportunista.
C3/F4/G2/I2/I3 recomendados, a criterio del dueño.
Respuesta a tu pregunta en B: SÍ, esos curl se pueden correr desde WSL (misma LAN).
