# Arquitectura de LRP OS

LRP OS 1.0.0 es una imagen Debian 13 (`trixie`, amd64) armada con `live-build` que se instala en
disco y arranca directamente en el panel de LinuxRemotePlayer. El teléfono controla la PC por la
red local; no hay servicios en la nube, cuentas ni telemetría.

## Componentes

### ISO (`scripts/debian/iso/`)

- `build_iso.sh` orquesta `live-build`: lista de paquetes (`lrp-appliance.list.chroot`), preseed,
  configuración de GRUB/ISOLINUX, splash de Plymouth, zram y el hook de chroot.
- `hooks/99-lrp-appliance.chroot` prepara el sistema dentro del chroot: crea el usuario `lrp`,
  enmascara `lightdm` y `live-config`, deja autologin de `getty@tty1`, escribe el `.bash_profile`
  con `startx`, instala la política de Firefox que confía en la CA local y conecta la unidad del
  backend si encuentra el venv.
- `hooks/99-lrp-live-links.binary` enlaza los binarios del entorno live para que el instalador
  pueda ejecutarse antes del primer arranque.
- `installer/lrp-install-target.sh` particiona el disco, copia el sistema, instala GRUB para UEFI
  (con shim; fallback `--removable`), crea la entrada NVRAM `LRP-OS` con `efibootmgr` y la deja
  primera en `BootOrder`, configura zram y el autologin.
- `config/` contiene preseed, GRUB/ISOLINUX, splash y zram; `package-lists/` la selección mínima
  de Debian.

### Arranque

1. UEFI carga el shim firmado y GRUB desde la ESP (o el fallback `BOOTX64.EFI`).
2. systemd arranca; `getty@tty1` hace autologin como `lrp`.
3. `.bash_profile` ejecuta `startx`; Openbox levanta la sesión mínima.
4. La sesión lanza el kiosk de Firefox ESR apuntando al panel local (`https://127.0.0.1:8000/status`).
5. La unidad `linuxremoteplayer.service` corre el backend FastAPI; el panel muestra PIN y QR.

### Backend (`backend/`, Python + FastAPI)

- `main.py`: aplicación, router de sistema, endpoints de pairing (`/api/pairing-pin`, `/api/pair`,
  `/api/pairing-token`, `/api/pairing-qr`), panel (`/status`), estado (`/api/status`), apps,
  kiosk, panel y WebSocket `/ws`.
- `system_platform.py` (router `/api/system`): audio por PipeWire (`pactl`), Wi-Fi (`nmcli`),
  Bluetooth (`bluetoothctl`), pantalla (`xrandr`), energía y onboarding. Todo local.
- `kiosk.py`: lanza y vigila Firefox ESR en modo kiosk; limpia el perfil dedicado y evita
  instancias zombi.
- `input_emulator.py`: teclado, mouse y gamepad virtuales vía `uinput` (requiere el grupo `input`).
- `audio.py`: control de volumen/mute con fallback a teclas multimedia.
- `discovery.py`: detecta apps nativas desde archivos `.desktop`.
- `config.py`: resuelve rutas mutables en `/var/lib/linuxremoteplayer` (0700) y el código en
  `/opt/linuxremoteplayer` (root:root).
- `run.py`: arranque HTTPS, generación/renovación de la CA local y del certificado de la IP y
  `hostname.local`.
- `auth.py`: token de pairing persistido en `.pairing_token`.

### Control (`frontend/`)

PWA sin paso de build. `index.html` + `app.js` implementan touchpad, teclado, apps y navegación;
`status.html` es el panel de la TV (pairing, estado, ajustes). El WebSocket `/ws` autentica con
`{"type":"auth","token":...}` en los primeros 3 segundos, aplica rate limiting y envía eventos de
puntero, teclado, combos y multimedia.

### Web (`website/`)

Sitio estático ES/EN desplegado en Vercel. No participa del runtime del producto.

## Flujo de datos

```
Teléfono (PWA) --HTTPS/WSS LAN--> backend FastAPI --uinput--> Xorg
                                        |--PipeWire (audio)
                                        |--bluetoothctl
                                        |--xrandr
                                        '--Firefox ESR (kiosk) --> TV
```

El QR entrega la URL con el token de pairing; el PIN de 6 dígitos permite emparejar un teléfono
sin conocer el token.

## Trust boundaries

- **Red local:** el control viaja cifrado con el certificado de la CA local. Nada sale a internet.
- **Pairing:** sin token válido el WebSocket se cierra a los 3 segundos (código 1008). El token se
  genera en la PC y se puede rotar.
- **Endpoints locales:** `/api/status`, `/status` y el panel exigen acceso desde loopback. Los
  endpoints de sistema aceptan peticiones locales o con `X-Auth-Token` válido.
- **Privilegios:** el backend corre como `lrp`; el acceso a `uinput` viene del grupo `input`. La
  escritura en `/opt` y la unidad systemd son de root.
- **CA local:** la clave privada y los certificados viven en `/var/lib/linuxremoteplayer/certs`
  (0700) y solo los usa el backend.

## Decisiones

- **Sin display manager:** autologin de `getty` + `startx`/Openbox evita un greeter y reduce el
  tiempo hasta el panel.
- **Firefox ESR kiosk:** un único perfil dedicado, con política de confianza en la CA local.
- **Voz local:** el pipeline de STT/NLU corre en la PC; no hay proveedor externo ni cuota.
- **Sin actualizador remoto en 1.0.0:** la versión se instala desde la ISO publicada.

## Limitaciones conocidas

- El certificado es de una CA propia: la primera visita en el teléfono pide aceptar la excepción.
- El control requiere que el teléfono y la PC estén en la misma red local.
- La GPU certificada es NVIDIA RTX 3060 12 GB; otras GPUs pueden funcionar sin soporte declarado.
- El APK de Android todavía no se publica.
