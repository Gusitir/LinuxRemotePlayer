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

## A. INSTALACIÓN (limpia e idempotente)

- [ ] A1. Instalación limpia: `curl -fsSL https://linux-remote-player.vercel.app/install.sh | sudo bash`
      termina sin errores. Preguntas: modo [S], suspensión [S], teclado [3 latam].
- [ ] A2. `which firefox || which firefox-esr` -> existe. `which chromium` -> VACÍO.
- [ ] A3. `cat /etc/firefox/policies/policies.json` -> contiene uBlock, Certificates
      con ruta real del ca.pem, EncryptedMediaExtensions.
- [ ] A4. `grep -E "LRP_MODE|KEYBOARD_LAYOUT" /opt/linuxremoteplayer/backend/.env`
      -> LRP_MODE=appliance y KEYBOARD_LAYOUT=latam.
- [ ] A5. `systemctl is-enabled sleep.target` -> masked (elegiste S en suspensión).
- [ ] A6. `ls /usr/local/share/ca-certificates/lrp-ca.crt` -> existe (CA en trust;
      requiere que el servicio arrancara y generara ca.pem en <30s).
- [ ] A7. Idempotencia: re-ejecutar el installer completo -> termina sin errores y sin
      duplicar (servicio, policies, .env sin líneas repetidas:
      `grep -c "^LRP_MODE" backend/.env` -> 1).
- [ ] A8. Dependencias: `which pactl wmctrl` y `which qdbus || which qdbus6` -> existen.
- [ ] A9. Reboot -> el servicio arranca solo: `systemctl status linuxremoteplayer` activo,
      panel de estado aparece en la TV tras ~45s de inactividad.

## B. SEGURIDAD / AUTH (desde OTRA máquina de la LAN, sin token)

- [ ] B1. `curl -k https://<IP>:8000/api/apps` -> 401/403 (require_token).
- [ ] B2. `curl -k -X POST https://<IP>:8000/api/kiosk/launch -H "Content-Type: application/json" -d '{"url":"https://example.com"}'`
      -> 401/403. NUNCA debe abrir nada en la TV.
- [ ] B3. `curl -k https://<IP>:8000/api/status` -> rechazado (require_local; solo 127.0.0.1).
- [ ] B4. `curl -k https://<IP>:8000/api/pairing-token` -> rechazado (require_local).
- [ ] B5. WS sin auth: conectar wss://<IP>:8000/ws sin frame de auth o token malo ->
      cierre con código 1008.
- [ ] B6. PIN brute-force: 6 intentos seguidos de PIN inválido en /api/pair ->
      bloqueado (límite 5/IP); el PIN expira a los 120s y es de un solo uso.
- [ ] B7. `curl -k https://<IP>:8000/health` y `/api/config` y `/api/ca` -> 200 (públicos
      por diseño; config NO debe filtrar el pairing token — inspeccionar respuesta).
- [ ] B8. Token en URL de emparejamiento: tras emparejar por PIN, verificar que la app
      funciona SIN mostrar nunca un campo de token manual (eliminado en G-02/C-02).

## C. INPUT / WS (teléfono emparejado)

- [ ] C1. Touchpad: mover, tap=click izq, long-press=click der (vibración), scroll lateral.
- [ ] C2. Teclado texto completo (layout latam): escribir en un editor del HTPC:
      `hola/mundo @correo.com (test) & "ok" ¿? ; : + * _ =` -> todo exacto.
      Anotar los que fallen (gap conocido: < > y corchetes AltGr — no soportados aún).
- [ ] C3. Texto largo: pegar/escribir >500 chars -> el backend lo trunca/rechaza sin
      crashear (límite del protocolo WS).
- [ ] C4. Media keys: volumen +/- y mute funcionan (audio.py vía wpctl/pactl);
      transporte ⏯ ⏮ ⏭ funciona en YouTube kiosk.
- [ ] C5. Atrás: en un video embebido de un sitio de terceros -> navega atrás, NO
      rebobina (BTN_SIDE). En página normal -> historia atrás.
- [ ] C6. Nav-mode (D-Pad): flechas + Enter + Esc funcionan en una app leanback.
- [ ] C7. Latencia bajo carga: abrir kiosk de página pesada con ads y, DURANTE la carga,
      mover el touchpad -> fluido, sin congelamientos (fix C-01). Repetir cambiando
      de app 3 veces seguidas.

## D. KIOSK / NAVEGADOR (Firefox)

- [ ] D1. Kiosk abre Firefox fullscreen (sin barra de URL). Perfil dedicado:
      `ls ~/.config/lrp-kiosk-ff` existe tras el primer launch.
- [ ] D2. uBlock activo: sitio con ads -> limpio. (Verificación fina: abrir kiosk a
      `about:support` y buscar uBlock en extensiones.)
- [ ] D3. Netflix/Max: reproduce (primer video puede tardar 1-2 min por Widevine).
- [ ] D4. Panel /status en el HTPC -> SIN advertencia de certificado.
- [ ] D5. Sesiones: login en un sitio -> cambiar de app 3 veces -> login conservado.
- [ ] D6. Apps nativas: lanzar una del drawer (detectadas .desktop) -> abre; el
      TERMINAL aparece en el drawer (G-18).
- [ ] D7. Home x2: con 1 kiosk + 1 app abierta A MANO -> Home limpia TODO el
      escritorio. Repetir Home otra vez con nuevas ventanas -> vuelve a funcionar
      (fix FC-01 del script KWin).
- [ ] D8. Custom app: añadir una web custom desde el móvil -> tile con favicon
      (o fallback), lanza en kiosk.

## E. PANEL DE ESTADO / IDLE

- [ ] E1. Panel muestra: versión 1.7.0, latencia en ms, modo "TV", clientes conectados,
      uinput OK, badge "uBlock (Firefox)", licencia correcta, QR escaneable.
- [ ] E2. Enlace de compra clicable con el puntero virtual.
- [ ] E3. Idle: sin clientes y sin audio -> panel aparece a los ~45s. Con video
      reproduciéndose en app abierta A MANO (VLC/navegador manual) y teléfono en
      reposo -> NO aparece (pactl). `journalctl -u linuxremoteplayer | grep -i pactl`
      -> sin warnings de pactl ausente.
- [ ] E4. Mantenimiento del panel: botón de actualización visible; tutorial de cambio
      de modo presente.

## F. PWA (teléfono)

- [ ] F1. Instalación fresca de la PWA (borrar la vieja primero) -> icono correcto en
      home screen (SI FALLA: anotar modelo+OS+navegador -> alimenta G-16).
- [ ] F2. Límites de pantalla: barra de estado del teléfono NO tapa el icono de
      Ajustes; sin scroll lateral; botones inferiores completos (SI FALLA: screenshot
      -> alimenta G-15).
- [ ] F3. Reconexión: apagar pantalla 2 min -> encender -> reconecta sola en <5s sin
      recargar la página; sin bucles de recarga (fix C-03).
- [ ] F4. Offline: modo avión -> la app abre (shell cacheado lrp-v16) y muestra estado
      de desconexión razonable, no pantalla blanca.
- [ ] F5. Onboarding: en un teléfono/navegador nuevo -> pantalla de PIN únicamente
      (sin opción de token manual); PIN del panel empareja correctamente.
- [ ] F6. Iconos nuevos: borrar texto = ⌫, nav = cruz de flechas, panel = pulso;
      estilo visual convive bien con el resto (juicio del dueño).
- [ ] F7. Skins: cambiar skin (con licencia Pro) -> aplica y persiste tras recargar.
- [ ] F8. Coach marks / tour de primera vez: se muestra una vez y no vuelve a molestar.

## G. LICENCIA / VOZ

- [ ] G1. Activar licencia desde el móvil -> "Licencia activada"; micrófono aparece;
      panel de la TV refleja "Activa (Pro)" sin reiniciar.
- [ ] G2. Gracia offline: desconectar internet del HTPC (no la LAN) -> la voz/skins
      siguen funcionando (cache 72h). Reconectar.
- [ ] G3. Voz cloud (Together.ai configurado): "pon videos de gatitos en youtube" ->
      transcripción + kiosk correcto. Probar también un comando inválido -> error
      claro, sin crash.
- [ ] G4. Sin licencia (otro teléfono/token regenerado): micrófono oculto; enviar
      audio por WS a mano -> rechazado.

## H. OTA / ACTUALIZACIÓN

- [ ] H1. Ajustes -> Buscar actualización -> "estás al día" (1.7.0 == 1.7.0).
- [ ] H2. `curl -s https://linux-remote-player.vercel.app/latest.json` -> 1.7.0,
      sha256 4fff1722...4833.
- [ ] H3. (Cuando exista 1.7.1+) flujo completo: Buscar -> Actualizar -> el servicio
      se reinicia y la app reconecta sola.

## I. ESTRÉS / RESILIENCIA

- [ ] I1. 2-3 teléfonos conectados a la vez -> input de todos funciona; contador de
      clientes del panel correcto; desconectar uno no afecta al resto.
- [ ] I2. 20 reconexiones seguidas (pantalla on/off del teléfono) -> sin degradación,
      sin procesos zombie: `pgrep -c firefox` estable tras Home.
- [ ] I3. Reinicio del servicio con la app abierta: `sudo systemctl restart
      linuxremoteplayer` -> la app reconecta sola con backoff, sin intervención.
- [ ] I4. Cambio de IP (reconectar WiFi del HTPC o DHCP nuevo) -> run.py regenera leaf,
      servicio se reinicia, `https://<hostname>.local:8000` sigue funcionando y el
      panel NO muestra advertencia de cert (CA estable).
- [ ] I5. Maratón: 2h de reproducción continua -> sin suspensión (A5), sin caída de
      WS, memoria del backend estable (`systemctl status` / `top`).

## J. DESINSTALACIÓN

- [ ] J1. `sudo ./scripts/uninstall.sh` -> servicios fuera, `systemctl is-enabled
      sleep.target` -> vuelve a normal (unmask), reglas udev y UFW limpias.
- [ ] J2. Re-instalar tras desinstalar -> todo vuelve a funcionar (A1-A9 rápido).

---

## RESULTADOS (dueño rellena)

```
Fecha ejecución:
Ítems OK:        /
FALLAS:
- <ID>: <descripción exacta + cómo reproducir>
SKIPS:
- <ID>: <motivo>
```

Claude triará las FALLAS -> tareas [T-NN] del siguiente plan (v1.7.1 o v1.8).
