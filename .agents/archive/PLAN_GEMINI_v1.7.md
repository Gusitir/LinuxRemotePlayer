# PLAN DE TRABAJO — GEMINI (v1.7.0: Firefox + fixes del smoke-test v1.6)

```yaml
plan_id: PLAN_GEMINI_v1.7
date: 2026-07-14
author: Claude (causas raíz verificadas en repo + smoke-test del dueño en HTPC limpio)
executor: Gemini 3.5 Pro
base: smoke-test v1.6.0 (7/7 funcional) + decisión del dueño: FIREFOX como navegador
  por defecto (Brave/Chromium tienen bugs con Plasma Bigscreen recién lanzado; Firefox
  viene en prácticamente todas las distros).
flujo: BACHE — F-01..F-06 seguidas, un commit por tarea, evidencia de comandos en la
  bitácora; STOP al terminar -> auditoría Claude -> F-07 (release v1.7.0).
contexto_smoke_test: panel/teclado/latencia/sesiones/atrás OK. Fallan: Home no cierra
  apps de sistema (Wayland), audio externo no detectado (¿pactl ausente?), advertencia
  de cert en panel, chromium se reinstala (Recommends del .deb), suspensión de la
  distro interrumpe reproducción.
```

## REGLAS (las de siempre, obligatorias)
1. Leer CURRENT.md y APPCORE.md antes de empezar. Un commit por tarea [F-NN].
2. Nada fuera de alcance; hallazgos a HALLAZGOS GEMINI sin código.
3. Criterio de aceptación verificado con SALIDA REAL de comando pegada en bitácora.
4. Archivos grandes: verificar lectura completa (wc -l). Secretos: backend/.env NI TOCARLO.
5. bash -n / py_compile / node --check antes de cada commit.

---

### F-01 — Migración del kiosk a FIREFOX (decisión del dueño)
**backend/kiosk.py:**
1. `find_browser()`: buscar PRIMERO firefox (`firefox`, `firefox-esr`, `/usr/bin/firefox`,
   `/usr/bin/firefox-esr`, `/snap/bin/firefox`), devolver ("...", "firefox"). Brave y
   chromium quedan como fallback (en ese orden). NO instalar brave/chromium nunca.
2. Comando firefox: `[bin, '--kiosk', '--no-remote', '-profile', PROFILE_DIR, url]`
   con PROFILE_DIR = `~/.config/lrp-kiosk-ff` (crear con os.makedirs si no existe;
   perfil dedicado = mismo diseño de aislamiento/persistencia que con Brave).
   Los flags --app/--noerrdialogs/--user-data-dir son SOLO para la rama chromium/brave.
3. pkill fallback: añadir patrón `firefox.*--kiosk`.
4. `adblock_status()`: si browser=firefox y existe /etc/firefox/policies/policies.json
   con "ublock" dentro -> "ubo-firefox". Mantener "shields"/"ubol"/"none" para fallbacks.
   status.html: mostrar "uBlock (Firefox)" para el nuevo estado.
**scripts/install.sh:**
5. QUITAR el bloque de instalación de Brave (repo apt + keyring). No desinstalar el
   Brave del usuario si ya existe — solo dejamos de instalarlo.
6. Instalar firefox: `apt-get install -y firefox-esr || apt-get install -y firefox`
   (Debian usa firefox-esr; Ubuntu usa firefox/snap). Si ya existe, no hacer nada.
7. Crear `/etc/firefox/policies/policies.json` (mkdir -p; idempotente) con:
   ```json
   {
     "policies": {
       "ExtensionSettings": {
         "uBlock0@raymondhill.net": {
           "installation_mode": "force_installed",
           "install_url": "https://addons.mozilla.org/firefox/downloads/latest/ublock-origin/latest.xpi"
         }
       },
       "Certificates": {
         "ImportEnterpriseRoots": true,
         "Install": ["/opt/linuxremoteplayer/backend/certs/ca.pem"]
       },
       "EncryptedMediaExtensions": { "Enabled": true },
       "DisableFirefoxStudies": true,
       "OverrideFirstRunPage": "",
       "NoDefaultBookmarks": true
     }
   }
   ```
   NOTA: la política Certificates.Install hace que Firefox confíe nuestra CA -> esto
   REEMPLAZA a certutil/NSS para el kiosk (Firefox no lee ~/.pki/nssdb). El bloque
   certutil existente se queda (sirve para el fallback chromium/brave).
   NOTA 2: ruta del ca.pem = instalación real (/opt/linuxremoteplayer/backend/certs/
   ca.pem) — verificar contra el layout del .deb; si el backend corre desde otra ruta,
   usar esa. La política se escribe DESPUÉS de que exista ca.pem (junto al bloque
   certutil movido en C-05).
**Aceptación:** kiosk abre Firefox fullscreen con uBlock activo (about:policies del
perfil muestra la política); panel /status SIN advertencia de cert; Netflix reproduce
(Widevine se descarga en el primer uso — puede tardar 1-2 min con internet);
bash -n + py_compile OK.

### F-02 — Higiene del .deb: erradicar chromium/uBOL de build_deb.sh [causa raíz confirmada]
1. `build_deb.sh:66`: `Recommends: chromium | chromium-browser` -> `firefox-esr | firefox`.
   (Esto era lo que REINSTALABA chromium en cada install del .deb.)
2. `build_deb.sh:42` (.desktop del panel embebido en el .deb): Exec con chromium ->
   `xdg-open https://127.0.0.1:8000/status` (respeta navegador por defecto; el panel
   NO necesita kiosk).
3. Bloque uBOL dentro del lrp-update embebido (build_deb.sh:146-156): ELIMINARLO.
4. Revisar el resto de build_deb.sh por más referencias a chromium/brave/ubol (grep).
**Aceptación:** `grep -in "chromium\|brave\|ubol" scripts/build_deb.sh` -> 0 resultados
(o solo comentarios); bash -n OK.

### F-03 — Home cierra TODO también en Wayland/KDE (Plasma Bigscreen) [fallo confirmado en smoke-test]
wmctrl no funciona en Wayland (por eso Home solo cerraba lo nuestro). Implementar el
fallback KWin prometido en G-10:
1. En kiosk.close_all(), tras el intento wmctrl: si no hay DISPLAY X11 útil o wmctrl
   no listó ventanas, usar KWin Scripting por DBus:
   - Escribir script JS temporal (tempfile): compatible KWin5/KWin6:
     ```js
     var list = (typeof workspace.windowList === 'function')
       ? workspace.windowList() : workspace.clientList();
     for (var i = 0; i < list.length; i++) {
       var c = list[i];
       if (!c.specialWindow && !c.skipTaskbar) { c.closeWindow(); }
     }
     ```
   - Cargar/ejecutar: `qdbus org.kde.KWin /Scripting loadScript <file> lrpCloseAll`
     + `qdbus org.kde.KWin /Scripting/Script<N> run` (o `org.kde.kwin.Scripting.start`).
     Usar `qdbus` o `qdbus6` según exista (shutil.which). env=gui_env() + DBUS de sesión:
     para DBus de sesión hace falta DBUS_SESSION_BUS_ADDRESS — derivarlo:
     `unix:path=$XDG_RUNTIME_DIR/bus` si existe ese socket (estándar en systemd).
   - Timeout 3s, best-effort, log claro si falla. Ejecutar dentro del to_thread ya
     existente (C-01) — no bloquear el loop.
2. install.sh: qdbus está en `qdbus-qt5 | qdbus-qt6 | qt6-tools` según distro — instalar
   con `apt-get install -y qdbus-qt6 || apt-get install -y qdbus-qt5 || true` y loggear.
**Aceptación:** en Plasma Bigscreen (Wayland), con 1 app kiosk + 1 app abierta a mano,
Home deja el escritorio sin ventanas. py_compile OK.

### F-04 — Detección de audio: pactl ausente en la distro [fallo confirmado en smoke-test]
El monitor idle solo detectaba audio de apps propias -> casi seguro `shutil.which("pactl")`
da None en Plasma Bigscreen (el código lo salta EN SILENCIO — solo warnea excepciones).
1. main.py monitor_idle_panel: si pactl NO existe -> logger.warning UNA VEZ
   ("pactl no encontrado: instala pulseaudio-utils para detección de audio").
2. install.sh deps: añadir `pulseaudio-utils` (cliente pactl; funciona contra
   PipeWire vía pipewire-pulse y contra PulseAudio clásico).
3. build_deb.sh Depends/Recommends: añadir pulseaudio-utils en Recommends.
4. Además, DBUS no hace falta para pactl, pero sí XDG_RUNTIME_DIR (ya resuelto C-04).
**Aceptación:** con pulseaudio-utils instalado y VLC abierto A MANO reproduciendo,
`pactl list short sink-inputs` no vacío y el panel NO aparece (validación final en HTPC).

### F-05 — Opción de deshabilitar suspensión en lrp-setup [pedido del dueño]
En install.sh, tras elegir modo Appliance: preguntar
"¿Deshabilitar suspensión/apagado de pantalla del sistema? [S/n]" (default S en
Appliance; en Desktop default n). Si sí:
`systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target`
(DE-agnóstico; el bloqueo de kscreenlocker/DPMS de v1.5 se mantiene aparte).
Soportar no-interactivo: env LRP_NOSLEEP=1|0. En scripts/uninstall.sh: unmask de los
4 targets (revertir).
**Aceptación:** bash -n OK; con LRP_NOSLEEP=1, `systemctl is-enabled sleep.target`
-> masked; uninstall revierte a estado normal.

### F-06 — Limpieza menor acumulada
1. main.py:24: quitar import muerto `kill_existing_kiosks` (nota de auditoría C-01).
2. tailwind-lite.css: dedupe de `.hidden` (definida 2 veces; dejar la de `!important`).
3. CHANGELOG/README: actualizar mención de Brave->Firefox y uBlock Origin.
**Aceptación:** py_compile OK; `python scripts/check_css_sync.py` sigue en exit 0.

## CORRECCIONES DE AUDITORÍA DEL BACHE [Claude 2026-07-14] — antes de F-07

### FC-01 — [MEDIO] F-03: Home solo funcionará UNA vez por sesión de KWin
`loadScript(path, "lrpCloseAll")` devuelve -1 si ya existe un script con ese nombre
(cargado en el Home anterior) -> `out.isdigit()` falla con "-1" -> el run se salta y
los Home siguientes no cierran nada.
**Fix:** en kiosk.close_all(), ANTES del loadScript llamar
`qdbus org.kde.KWin /Scripting unloadScript lrpCloseAll` (ignorar error si no existe,
timeout 3s). Así cada Home carga y ejecuta fresco.
**Aceptación:** py_compile OK; revisión de flujo: unload -> load -> run.

### FC-02 — [BAJO] F-06 quedó incompleto (2 de 3 puntos sin hacer)
1. main.py:24 AÚN importa `kill_existing_kiosks` (muerto). Quitarlo del import.
2. `.hidden` AÚN está definida 2 veces en tailwind-lite.css (verificado por Claude:
   grep '^\.hidden' = 2). Dejar SOLO la de `display: none !important;`.
3. README.md: sigue mencionando Chromium como navegador del kiosk (Features y
   Troubleshooting). Actualizar a Firefox + uBlock Origin. Grep de control:
   `grep -in "chromium\|brave" README.md` -> solo menciones históricas/changelog si las hay.
**Aceptación:** greps + py_compile + `python scripts/check_css_sync.py` exit 0.

### FC-03 — [BAJO] Robustez Firefox (2 detalles del diseño F-01)
1. policies.json está DENTRO del `if [ -f ca.pem ]` -> si el cert tarda >30s, uBlock y
   DRM tampoco se configuran. Mover la escritura de policies.json FUERA del if (siempre
   se escribe); la clave "Install" puede apuntar a la ruta del ca.pem aunque el archivo
   aparezca después (Firefox la lee en cada arranque; si falta, la ignora con un log).
2. Snap Firefox (Ubuntu): no puede leer perfiles en dirs ocultos de $HOME
   (~/.config/...). En kiosk.py, si el binario es /snap/bin/firefox, usar
   `~/snap/firefox/common/lrp-kiosk` como profile_dir.
**Aceptación:** bash -n + py_compile OK; grep del nuevo path snap en kiosk.py.

### F-07 — Release v1.7.0 (WSL) — SOLO tras APTO de Claude a FC-01..FC-03
Mismo procedimiento que G-14 (clon fresco, sha256 real, verificación EN VIVO con
salidas pegadas). VERSION 1.7.0. Borrar .deb 1.6.0 de website/downloads/.
Smoke-test del dueño: los 7 puntos de v1.6 + (a) Firefox+uBlock en kiosk, (b) panel
sin advertencia de cert, (c) Home cierra apps manuales en Bigscreen, (d) panel idle
respeta video de apps manuales, (e) suspensión deshabilitada si se eligió.

---

## NOTAS PARA EL DUEÑO
- Perfil secundario del navegador: ES INTENCIONAL (aislamiento + persistencia de
  logins — tu punto 6 del smoke-test funciona gracias a eso). Con Firefox igual.
- uBlock Origin elegido sobre "AdBlock/ABP" (más popular en Firefox, sin "anuncios
  aceptables"). Cambiar = 1 URL en policies.json.
- Netflix en Firefox: el primer video puede tardar (descarga de Widevine). Es una vez.
- Brave instalado en tu HTPC por la v1.6: puedes desinstalarlo a mano si quieres
  (`sudo apt remove brave-browser`); el installer ya no lo tocará.
- PENDIENTES sin cambio: G-15/G-16 (necesito modelo de teléfono + screenshots),
  deploy send-feedback, ai-proxy antes de vender voz, Stripe LIVE.
