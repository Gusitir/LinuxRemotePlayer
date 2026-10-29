# TESTING - checks v3

```yaml
assurance: Standard
device_owner: dueño
format: "[OK] / [FAIL: reason] / [SKIP: reason]"
```

## DEBIAN-FOUNDATION · T-122 baseline (automatizable por IA en HTPC)

Estas instrucciones están pensadas para que un agente IA autónomo las ejecute de forma segura sobre
el HTPC físico recién instalado. Van separadas de la parte humana. Las cápsulas completadas de
BETA-FOUNDATION están archivadas en `archive/TESTING_beta-foundation_1.99.1.md`.

### Resultado de baseline (T-122, cerrado)

- `TST-DEBIAN-BASE-001` `[OK]` — AI: Debian 13 trixie amd64 (UEFI), RTX 3060 PCI `10de:2504` con
  módulo `nouveau` activo, Secure Boot `disabled` (Setup Mode), fuentes apt oficiales
  `main`+`non-free-firmware` sin repositorios de terceros; contract de paquetes D32 verificado en
  sandbox aislado oficial. Evidencia cruda no persistida en el vivo.
- `TST-DEBIAN-BASE-HUMAN-001` `[OK]` — dueño: instalación netinst minimal sin desktop, login de
  consola y red confirmados, GPU RTX 3060 física y pantalla conectadas, backup/reinstalación
  disponibles.

### Protocolo IA (obligatorio, TST-DEBIAN-BASE-001)

- CAVEMAN: salida breve, técnica, literal y accionable.
- **Nunca** mutar el sistema, instalar, reiniciar ni pedir `sudo` durante esta baseline.
  `sudo` solo si una lectura de solo lectura lo exige de verdad y el dueño lo aprueba explícitamente.
- **Nunca** mostrar credenciales de `apt` (formato `user:pass@`), tokens, claves ni seriales.
- Si `apt update`/`apt install` aparecen en alguna instrucción: **no ejecutarlos**. La baseline no
  actualiza listas ni instala nada. Candidate se lee de las listas locales que ya existan.
- No ejecutar `hostname`, `whoami`, `dmesg`, volcado de `/etc/hostname`, UUIDs de disco ni comandos
  de identidad/privilegio.
- Todo comando debe ser read-only. Clasificar cada requisito en uno de:
  `ok` / `missing tool` / `missing data` / `fail` / `unknown` / `unresolved`.
    - `missing tool`: la herramienta no está instalada (p. ej. `mokutil`, `lspci`). **Válido**, no fallo.
    - `missing data`: la herramienta existe pero no devuelve el dato (p. ej. `candidate` `(none)`).
    - `fail`: dato presente pero no coincide con el objetivo (distro/arq/GPU/suite).
    - `unknown`: dato indeterminado por herramienta o fuente ausente.
    - `unresolved`: requisito sin entrada explícita.
- Registrar comandos literales con su exit code, salida decisiva, "no verificado", riesgos y
  recomendación. La recomendación puede ser `APTO`; el veredicto lo emite el Arquitecto.
- **STOP** inmediato ante: host no Debian, arq no amd64, GPU no NVIDIA esperada, repositorio de
  terceros con credenciales, comando que pida mutación durante el inventario, o rol de paquete
  sin resolver.

### Instalación previa (ejecuta el humano, ver abajo SOLO PARA HUMANO)

La baseline asume que el dueño ya instaló oficial Debian 13 amd64 minimal sin escritorio. El agente
IA verifica ese estado, no lo crea.

### TST-DEBIAN-BASE-001 · protocolo y campos a registrar

Campos esperados en Debian 13 minimal amd64 (registrar valor real):

| Campo | Comando | Esperado | Estado si falta |
|---|---|---|---|
| `os-release` ID / VERSION_ID / VERSION_CODENAME | cat `/etc/os-release` (o `/usr/lib/os-release`) | `debian` / `13` / `trixie` | `missing data` |
| Arquitectura dpkg | `dpkg --print-architecture` | `amd64` | `missing tool`/`missing data` |
| Kernel / máquina uname | `uname -r`, `uname -m` | `m` = `x86_64` | `missing data` |
| Modo de arranque | `test -d /sys/firmware/efi` | `UEFI` o `legacy` | `unknown` |
| Secure Boot | `mokutil --sb-state` | `enabled`/`disabled`; ausente = válido | `unknown` si `mokutil` falta |
| GPU PCI vendor/device | `lspci -nn` (clase 0300/0302/0380) | NVIDIA `10de` RTX 3060 | `unknown` si `lspci` falta |
| Módulos cargados | `cat /proc/modules` | busca `nvidia`/`nouveau`/`i915`/`amdgpu` | `missing data` |
| Fuentes apt (sanitizadas) | `find /etc/apt/sources.list.d -maxdepth 1 -type f` + `cat` de `sources.list` y `.list`/`.sources` locales | `deb.debian.org`/`security.debian.org`, components `main` (+`non-free-firmware`) | `missing data` |
| Candidate de paquetes (local, sin `apt update`) | `apt-cache policy <pkg>` | ver lista | `missing data`/`(none)` |

Paquetes a consultar por `apt-cache policy` (local, **sin** `apt update`) para candidate/installed:
`xorg`, `xserver-xorg`, `openbox`, `lightdm`, `gdm3`, `sddm`, `nvidia-driver`,
`nvidia-kernel-dkms`, `linux-headers-amd64`, `firmware-misc-nonfree`, `firefox-esr`, `pipewire`,
`wireplumber`, `avahi-daemon`, `ufw`, `xdg-utils`, `dbus`.

Al leer fuentes apt, **sanitizar**: nunca volcar credenciales embebidas en URIs
(`user:pass@host`); mostrar solo host y components.

### Bloque de comandos seguro (manual, si `preflight.sh` aún no está transferido)

Si el script del repo aún no está presente en el HTPC, ejecutar estos comandos read-only de forma
manual (no instalan, no actualizan, no vuelcan identidad/secretos):

```bash
cat /etc/os-release 2>/dev/null; echo "---"; cat /usr/lib/os-release 2>/dev/null
dpkg --print-architecture 2>/dev/null
uname -r; uname -m
test -d /sys/firmware/efi && echo UEFI || echo legacy
command -v mokutil >/dev/null && mokutil --sb-state 2>/dev/null || echo "Secure Boot unknown (mokutil missing)"
command -v lspci >/dev/null && lspci -nn 2>/dev/null | grep -Ei 'vga|3d|display' || echo "GPU unknown (lspci missing)"
cat /proc/modules 2>/dev/null
echo "--- apt sources (sanitized) ---"
for f in /etc/apt/sources.list /etc/apt/sources.list.d/*; do [ -f "$f" ] || continue; echo "### $f"; sed -E 's|//[^/:@]*:[^/:@]*@|//|g; s|//[^/:@]*@|//|g' "$f"; done
echo "--- candidates (local, no update) ---"
for p in xorg xserver-xorg openbox lightdm gdm3 sddm nvidia-driver nvidia-kernel-dkms \
  linux-headers-amd64 firmware-misc-nonfree firefox-esr pipewire wireplumber avahi-daemon ufw \
  xdg-utils dbus; do printf "%s: " "$p"; apt-cache policy "$p" 2>/dev/null | grep -i candidate || echo "(none)"; done
```

Estado del script preferido: una vez `scripts/debian/preflight.sh` esté transferido al HTPC, usarlo
en lugar del bloque manual. El código está **pendiente de commit** en la rama `codex/debian-foundation`
del repo; no se publica una URL pública de descarga. No inventar enlaces.

### Esquema exacto de cápsula (TST-DEBIAN-BASE-001)

```
environment: {host: HTPC-fisico, role: T-122-baseline}
commands: [{cmd: "<literal>", exit_code: <n>}, ...]
status: ok|unknown|missing_tool|missing_data|fail|unresolved
decisive_output:
  os_release: {id, version_id, codename}
  architecture: {dpkg, uname}
  boot_mode, secure_boot, gpu: {vendor_id, device_id, driver}, modules: [...]
  apt: {sources_count, sources_sanitized: [...], has_third_party, components, candidates: {pkg: {installed, candidate}}}
not_verified: [<checks no realizados y por qué>]
risks: [<supuestos o incógnitas>]
recommendation: APTO | NO APTO | BLOCKED
stop_conditions: [<STOP disparados o no>]
```

Regla: el veredicto lo emite el Arquitecto; la IA solo recomienda y registra evidencia.

## SOLO PARA HUMANO (dueño)

### TST-DEBIAN-BASE-HUMAN-001 · confirmación de baseline

- Instalar **Debian 13 amd64 netinst oficial minimal**.
- Seleccionar **solo** "SSH server" (opcional/recomendado) + "standard system utilities"; **no**
  instalar escritorio.
- Arrancar en consola (texto) y confirmar login y red.
- **No** instalar NVIDIA, LRP, Xorg ni Openbox; **no** ejecutar `apt update`/`apt install` antes de
  la baseline.
- Confirmar físicamente GPU RTX 3060 y pantalla conectada.
- Confirmar disponibilidad de backup/recovery antes de cualquier paso siguiente.

Resultado esperado: `[OK]` cuando el HTPC esté en Debian 13 minimal sin desktop, sin paquetes
extra y listo para la baseline read-only de T-122.

### IDs futuros (diferidos hasta fundación Debian cerrada)

- `TST-NVIDIA-001` `[OK]` — NVIDIA bootstrap/recovery; driver `550.163.01` activo en RTX 3060,
  `nouveau` ausente, reinicio resumido exit 0; renderer diferido a T-124. (Evidencia concisa; crudo
  fuera del vivo.)
- `TST-SESSION-001` `[OK]` — reboot físico con LightDM/autologin, Xorg y Openbox bajo `lrp`; renderer
  NVIDIA activo, sin `llvmpipe`, package integrity y resume exit 0 estado `complete`.
- `TST-DEBIAN-SERVICES-001` `[OK]` — physical reboot verifies uinput, PipeWire/WirePlumber, Avahi,
  UFW 8000/tcp+5353/udp IPv4/IPv6, sleep/DPMS, local HTTPS CA attachment and NVIDIA HDMI selection.
- `TST-BETA-UPDATE-002` `[OK: public 1.99.1 -> 1.99.2 updater installed amd64, retained beta channel,
  config, pairing token and CA; legacy-uinput migration verified on HTPC; D35 rebuilt artifact/manifest
  reconciliation remains before closure.]`
- `TST-DEBIAN-UX-001` `[OK]` — owner paired the remote and verified apps, controls and audible HDMI;
  AI verified boot/autologin, kiosk panel recovery, input routing and service health.
- `TST-DEBIAN-ROLLBACK-001` `[OK: AI physical dry-run, strict rollback, retained-state sweep and
  full reapply/reboot passed; owner visually confirmed text console and subsequent QR pairing panel on screen.]`
- `TST-STT-001` `[OK: whisper.cpp AVX1 en Intel Core i5-3470 bare-metal verificado; base-q5_1 seleccionado con 2.6s latencia, 136.9 MB RAM pico, 0 SIGILL, 100% precisión en corpus gold; 254 tests pass (commits fad6e33, 45ab922)]`
- `TST-SECURITY-ASTRA-001` `[OK: ASTRA-01 root ownership en /opt y ASTRA-02 revocación inmediata de WebSockets al regenerar token; 232 tests pass (commit 610194e)]`
- `TST-RESILIENCE-ASTRA-001` `[OK: ASTRA-03 procesamiento asíncrono de voz en WS y ASTRA-04 renovación de certificados HTTPS caducados con chequeo RTC timesyncd; 235 tests pass (commit ebfdf82)]`
- `TST-SYSTEM-PLATFORM-001` `[OK: endpoints /api/system/* para PipeWire sinks, Wi-Fi, BT, energía y display; Firefox VA-API forzado en H.264; 241 tests pass (commit b988882)]`
- `TST-NLU-INTENT-001` `[OK: motor Needle 2 en backend/local_intent.py con latencia <0.25ms en CPU, allowlist, normalización fonética y filtro anti-inyección; desconexión total de Supabase ai-proxy; 263 tests pass (commit 6099d50)]`
- `TST-MOBILE-PWA-001` `[OK: PWA Mobile 2.0 Mantatomic SVG, 10.8px clearance botón Play, franja scroll lateral independiente, Quick Dock dinámico 450ms long-press, ajustes en columna única, skins Day/Anime, catálogo AnimeAV1, corrección heartbeat WS 15s; 272 tests pass (commits 348113b, 024cd8b, 6258b7a y D43)]`
- `TST-OTA-001` `[SKIP: requires field artifacts and Architect/owner authority for signing, downgrade, interruption and rollback (T-142).]`

Los resultados crudos de BETA-FOUNDATION son históricos; no copiar ni usarlos para certificar
`2.0.0`.

## COMANDO LRP — SOLO CON AUTORIZACIÓN EXPLÍCITA

```bash
curl -fsSL https://www.linuxremoteplayer.com/beta/install.sh | sudo bash
```

Este comando instala la beta pública `1.99.2` amd64 con flujo unattended D35 (hasta dos reboots automáticos) y **requiere privilegios elevados**. **No ejecutarlo** sin autorización explícita del dueño; el cierre T-131 sigue pendiente.

## D53 · Estabilización sobre appliance instalado (2.0.0, 2026-10-22)

Checks humanos o no disponibles del ciclo que corrige sobre el HTPC ya instalado (ISO `720fc8…`),
antes de reconstruir la ISO definitiva.

**Nota D56 (2026-10-29)**: el ciclo comercial 2.0.0 se archivó en `legacy/2.0`; estos checks se
conservan porque splash y puntero siguen vigentes para la ISO 1.0.0.

**Estado 2026-10-29**: equipo encendido y alcanzable en `192.168.0.246`; barrido por SSH OK (unidades,
API, audio, pantalla, Bluetooth, Wi-Fi y fixes persistidos tras reboot). `dpkg -V` divergente en 5
archivos por despliegue fuera del paquete: se corrige al empaquetar 2.0.0 en T-148. Tres checks se
cerraron por **captura real del panel** (`scrot`, 1920x1080) en vez de confirmación ocular; splash y
puntero siguen pendientes del dueño.

- `TST-LRP-IRON-BOOT-001` `[OK]` — dueño: la ISO instala y el disco arranca en UEFI; el fallo previo
  era el `BootOrder` del firmware priorizando la entrada legacy, no la escritura del instalador.
  Evidencia AI: `efibootmgr -v` (`Boot0002` → `\EFI\BOOT\BOOTX64.EFI`) y `/var/log/lrp-install-report.txt`.
- `TST-LRP-PAIR-001` `[OK]` — dueño: PIN + QR emparejan el móvil; panel y control responden
  (`Connection: Stable`, latencia 6–10 ms, 1 teléfono conectado).
- `TST-LRP-SPLASH-001` `[pendiente]` — splash de arranque: GRUB y plymouth en verde `#10B981` con el
  icono LRP, sin artwork de Debian, y arranque posterior al panel.
- `TST-LRP-PANEL-001` `[OK: captura 2026-10-29]` — panel a `min(1500px, 94vw)` en TV 1080p; un pane
  por vez (B27), Ajustes en grilla 2x2 (B32) y sin recorte.
- `TST-LRP-AUDIO-001` `[OK: captura 2026-10-29]` — Ajustes muestra `Built-in Audio Digital Stereo
  (HDMI)` con volumen 40 %; sin “Cargando salidas…”.
- `TST-LRP-WIFI-DISPLAY-BT-001` `[OK: captura 2026-10-29]` — Wi-Fi lista 5 redes con señal, Pantalla
  `HDMI-1 1920x1080 @ 60.00 Hz` con modos, Bluetooth “Encendido (0 dispositivos)”.
- `TST-LRP-POINTER-001` `[pendiente]` — con mouse 2.4G conectado, el puntero se ve y se mueve sobre el
  panel tras el fix B26 (`startx` sin `-nocursor`). Si no aparece, revisar tema/cursor de Openbox antes
  que el flag de Xorg.
