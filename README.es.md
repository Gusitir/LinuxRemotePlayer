# LRP OS

[English](README.md) | **Español**

LRP OS 1.0.1 es una ISO de Debian 13 que convierte una PC x86_64 en un equipo de TV. La PC arranca directamente en un panel kiosk y tu teléfono pasa a ser el control remoto. El control se queda en la red local: sin dependencia de la nube, sin cuentas, sin claves de licencia, sin telemetría y sin actualizaciones OTA.

LinuxRemotePlayer es software libre bajo la GNU General Public License v3.0.

![Panel de emparejamiento de LRP OS 1.0.1 en una TV](website/screenshots/panel_pairing.webp)

## Qué es y qué no es

| Es | No es |
| --- | --- |
| Una ISO de Debian 13 (`trixie`, amd64) creada con live-build e instalada en disco. | Un servicio de streaming ni un paquete de contenidos. |
| Un equipo kiosk: Xorg + Openbox + Firefox ESR + un backend FastAPI. | Un escritorio de uso general. |
| Un control remoto por la red local: APK para Android o PWA para iOS. | Un dispositivo en la nube, un sistema de cuentas o un producto por suscripción. |
| Software libre bajo GPL-3.0. | Android TV/Google TV; además, la APK no es el sistema operativo. |

La APK de Android es la **aplicación de control remoto**. LRP OS es el sistema Debian de la PC; iOS usa la PWA en lugar de una APK.

## Cómo funciona

```
Teléfono (APK de Android / PWA de iOS)
  │  HTTPS + WSS en la LAN, emparejamiento con PIN de 6 dígitos
  ▼
Backend FastAPI, usuario lrp
  ├─ uinput/evdev ──► Xorg / Openbox
  ├─ audio PipeWire
  ├─ información de pantalla por xrandr
  ├─ Wi-Fi por nmcli / Bluetooth por bluetoothctl
  └─ kiosk de Firefox ESR ──► TV
```

Secuencia de arranque:

1. UEFI carga el shim firmado y GRUB desde la ESP (`LRP-BOOT`), o el respaldo `EFI/BOOT/BOOTX64.EFI`.
2. systemd inicia sesión automáticamente como `lrp` en tty1; `.bash_profile` ejecuta `startx` y arranca Openbox.
3. `linuxremoteplayer.service` inicia el backend FastAPI como `lrp` en HTTPS por el puerto 8000, con una CA local y un certificado hoja para la IP de la LAN y `<hostname>.local`.
4. El backend lanza el kiosk de Firefox ESR en `https://127.0.0.1:8000/status`.
5. El panel de la TV muestra un PIN de 6 dígitos y un código QR; el teléfono se empareja y conecta.

Implementación: [`lrp-install-target.sh`](scripts/debian/iso/installer/lrp-install-target.sh), [`99-lrp-appliance.chroot:153`](scripts/debian/iso/hooks/99-lrp-appliance.chroot#L153), [`backend/kiosk.py:431`](backend/kiosk.py#L431), [`backend/run.py:199`](backend/run.py#L199).

## Requisitos

| Componente | Requisito | Verificado en |
| --- | --- | --- |
| CPU | x86_64 (`amd64`). No se compila para x86 de 32 bits. | [`build_iso.sh:183`](scripts/debian/iso/build_iso.sh#L183) |
| Firmware | UEFI. Secure Boot es compatible mediante un shim firmado + GRUB. La instalación en BIOS legacy no está soportada. | [`lrp-install-target.sh:236`](scripts/debian/iso/installer/lrp-install-target.sh#L236), [`lrp-install-target.sh:347`](scripts/debian/iso/installer/lrp-install-target.sh#L347) |
| RAM | **4 GB mínimo**; 8 GB recomendado. El instalador no impone un mínimo de RAM. | requisito del autor; no hay comprobación de RAM en el código |
| Disco | Disco fijo interno de **al menos 8 GiB**. Se borra todo el disco. | [`lrp-install-target.sh:121`](scripts/debian/iso/installer/lrp-install-target.sh#L121) |
| GPU | Intel HD 2500 (validada por el autor), u otra GPU Intel/AMD mediante Mesa. NVIDIA RTX 3060 12 GB está certificada, pero requiere el controlador opcional que se describe abajo. | [`backend/kiosk.py:417`](backend/kiosk.py#L417), [`nvidia-bootstrap.sh:50`](scripts/debian/nvidia-bootstrap.sh#L50) |
| Pantalla | TV o monitor conectado por HDMI/DisplayPort. |  |
| Red | PC y teléfono en la misma red local (Ethernet o Wi-Fi). Internet solo hace falta para los sitios de streaming que abras. |  |
| Sistema base | Debian 13 `trixie` amd64 mínimo, Xorg/Openbox, Firefox ESR y PipeWire. | [`build_iso.sh:182`](scripts/debian/iso/build_iso.sh#L182) |

### Detalles de disco y firmware

El instalador solo acepta un disco fijo que no sea USB ni extraíble, que no sea de solo lectura y que tenga al menos 8 GiB; además excluye el medio de arranque live. Prefiere un disco NVMe; si no hay, toma el primer candidato fijo. El disco se reparticiona como GPT con dos particiones:

- `LRP-BOOT`: 512 MiB, FAT32, partición de sistema EFI.
- `LRP-ROOT`: ext4, el resto del disco.

`/etc/fstab` monta ambas por etiqueta; la swap zram se configura como `min(ram / 2, 4096)` con zstd. No hay arranque dual, ni cifrado de disco, ni `/home` separado: los datos que existan en el disco se pierden. GRUB se instala para UEFI con shim; el instalador crea la entrada NVRAM `LRP-OS`, intenta dejarla primera en `BootOrder` y también escribe el respaldo extraíble `EFI/BOOT/BOOTX64.EFI`. El informe de instalación se escribe en `/var/log/lrp-install-report.txt` en el destino y en `/run/lrp-install-report.txt` en la sesión live.

### NVIDIA: no se instala por defecto

**La ISO no incluye ni instala un controlador propietario de NVIDIA.** El instalador y la lista de paquetes de la ISO usan la pila gráfica genérica de Debian (Mesa, `xserver-xorg-video-all`); el firmware de NVIDIA y `nvidia-driver` no están en la imagen. Por eso una RTX 3060 se inicia con la pila genérica hasta que el operador ejecuta el bootstrap opcional.

La ruta certificada es la RTX 3060 12 GB (PCI `10de:2504`). En un sistema Debian 13 `trixie` amd64 verificado y con **Secure Boot desactivado**, [`scripts/debian/nvidia-bootstrap.sh`](scripts/debian/nvidia-bootstrap.sh) instala este conjunto exacto de paquetes desde los repositorios oficiales de Debian (`main contrib non-free non-free-firmware`):

- `nvidia-driver=550.163.01-2`
- `nvidia-kernel-dkms=550.163.01-2`
- `xserver-xorg-video-nvidia=550.163.01-2`
- `firmware-nvidia-gsp=550.163.01-2`
- `linux-headers-$(uname -r)` con la versión correspondiente a la imagen del kernel
- `dkms=3.2.2-1~deb13u1`

El script es de solo lectura por defecto; para aplicarlo hay que usar `--apply --approve`, nunca reinicia solo y pide `--resume` después del reinicio. Rechaza Secure Boot en estado `enabled`. Otras GPU NVIDIA y otras tarjetas no están certificadas. Consulta [`nvidia-bootstrap.sh:58`](scripts/debian/nvidia-bootstrap.sh#L58) y [`nvidia-bootstrap.sh:510`](scripts/debian/nvidia-bootstrap.sh#L510).

## Descarga y verificación

Obtén la versión desde [GitHub Releases v1.0.0](https://github.com/Gusitir/LinuxRemotePlayer/releases/tag/v1.0.0):

| Archivo | Notas |
| --- | --- |
| `lrp-os_1.0.0_amd64.iso` | ISO híbrida, aproximadamente 1,95 GiB. |
| `lrp-1.0.0.apk` | Aplicación de control remoto para Android, 24.400 bytes. |
| `SHA256SUMS` | Sumas de verificación de ambos archivos. |

Coloca los archivos en un mismo directorio y verifica:

```bash
sha256sum -c SHA256SUMS
```

Si solo descargaste la ISO:

```bash
sha256sum lrp-os_1.0.0_amd64.iso
```

Para 1.0.0 los valores esperados son:

```
5cc67f101bb507b590085183817ac87f8b1ccd04e2becb1c5e4d5d8972c9f5b2  lrp-os_1.0.0_amd64.iso
fcfb76e0383f5e3e7b72d7805618143945fd24a608ad4dd42df3d159b19c0bef  lrp-1.0.0.apk
```

En Windows:

```powershell
Get-FileHash .\lrp-os_1.0.0_amd64.iso -Algorithm SHA256
```

## Instalación

> **Advertencia: la entrada de arranque por defecto es el instalador automático.** Arranca con `lrp_auto_install`, elige el primer disco interno apto (NVMe primero) y borra todo el disco sin pedir confirmación. El menú de GRUB espera 3 segundos. En este modo reinicia automáticamente 15 segundos después de terminar. Para probar LRP OS sin instalar, elige **LRP OS Live (Probar en memoria sin instalar)** en el menú de arranque. Haz una copia de seguridad del disco destino antes de arrancar.

1. Descarga y verifica la ISO y `SHA256SUMS`.
2. Escribe la ISO en un pendrive con Rufus (usa el modo DD si lo pregunta), Ventoy o `dd`:

   ```bash
   sudo dd if=lrp-os_1.0.0_amd64.iso of=/dev/sdX bs=4M status=progress oflag=sync
   ```

   `/dev/sdX` es el dispositivo USB completo, no una partición. Si escribes en el dispositivo equivocado, destruyes sus datos.
3. Arranca la PC en modo UEFI. La entrada por defecto instala automáticamente; la entrada Live arranca la sesión live sin instalar.
4. Para elegir un disco manualmente, arranca la entrada Live y ejecuta:

   ```bash
   sudo /usr/local/sbin/lrp-install-target.sh --list-disks
   sudo /usr/local/sbin/lrp-install-target.sh --target /dev/nvme0n1
   ```

   El instalador valida que el destino sea un disco fijo y rechaza dispositivos USB, extraíbles, de solo lectura, live y de menos de 8 GiB. `--dry-run` simula la operación.
5. El instalador borra y formatea el disco, copia el sistema live, instala el gestor de arranque UEFI firmado y escribe la entrada NVRAM `LRP-OS` y el respaldo `EFI/BOOT/BOOTX64.EFI`. Consulta el informe en `/var/log/lrp-install-report.txt` en el sistema instalado.
6. Retira el USB y reinicia. La PC debería arrancar en el panel con un PIN y un código QR.
7. Empareja el teléfono (siguiente sección).

### Qué pasa con el disco

El instalador ejecuta `wipefs` y `sgdisk --zap-all`, crea una GPT nueva, formatea la ESP y la raíz, y copia el sistema de archivos live. Se eliminan todas las particiones y todos los archivos del disco destino. No hay confirmación en la ruta automática ni forma de deshacer.

## Control desde el teléfono

### Android: la APK es la aplicación de control remoto

1. Descarga `lrp-1.0.0.apk` desde la release.
2. Permite la instalación desde el navegador o el gestor de archivos que uses (**Instalar apps de origen desconocido**). La APK no se distribuye por Google Play.
3. Abre **LRP Remote**, escribe la IP o el nombre de host de la PC (el valor por defecto es `lrp.local`) y conecta. Si omites el puerto, la app usa HTTPS en el puerto 8000.
4. La app abre el control web en un WebView. Escribe el PIN de 6 dígitos que aparece en la TV.

La app acepta el certificado de la PC **sin validarlo** y muestra un aviso en su primera pantalla. Guarda la última URL en `SharedPreferences`; el WebView mantiene el almacenamiento local del panel (token de emparejamiento y preferencias de interfaz) en el teléfono. Solicita únicamente el permiso `INTERNET` y desactiva el tráfico en texto claro. Usa la app solo en una red local de confianza.

### iOS: la PWA

1. Abre Safari y ve a `https://<IP-LAN-DE-LA-PC>:8000` (o `https://lrp.local:8000`).
2. Acepta el aviso del certificado. Si quieres confiar explícitamente en la CA local, descárgala desde `/api/ca` e instálala en iOS.
3. Toca **Compartir → Añadir a pantalla de inicio**. La PWA se abre en modo independiente; no hay APK para iOS.

### El control en el teléfono

![Control remoto de LRP OS en un teléfono](website/screenshots/remote_control.webp)

La pantalla de control muestra el touchpad con su franja de desplazamiento, el teclado/D-pad y la rueda multimedia.
En Android se usa la APK; en iOS se añade la PWA a la pantalla de inicio.

### Emparejamiento

El panel de la TV muestra un PIN aleatorio de 6 dígitos que caduca a los 120 segundos, además de un código QR. El QR contiene la URL del teléfono con el token de emparejamiento; al escanearlo se empareja sin escribir el PIN. Un intercambio correcto del PIN devuelve el mismo token, que se guarda en la PC en `/var/lib/linuxremoteplayer/.pairing_token` (modo 0600). El token se puede regenerar mediante la API local; eso cierra las sesiones WebSocket activas.

Referencias: [`backend/main.py:337`](backend/main.py#L337) (PIN), [`backend/main.py:343`](backend/main.py#L343) (emparejamiento), [`backend/main.py:413`](backend/main.py#L413) (QR), [`backend/auth.py:33`](backend/auth.py#L33) (token).

## Qué puedes controlar

| Área | Qué expone 1.0.1 | Código |
| --- | --- | --- |
| Touchpad | Puntero relativo, clic izquierdo/derecho y franja de desplazamiento; eventos de puntero por `/ws`. | [`frontend/index.html:177`](frontend/index.html#L177), [`backend/main.py:901`](backend/main.py#L901) |
| Teclado | Inyección de texto y teclas (Retroceso, Intro, Meta, flechas, espacio); el texto se limita a 500 caracteres. | [`frontend/index.html:222`](frontend/index.html#L222), [`backend/main.py:909`](backend/main.py#L909) |
| Navegación | D-pad, atrás del navegador, reproducir/pausar y cerrar la app. | [`frontend/index.html:245`](frontend/index.html#L245), [`backend/main.py:916`](backend/main.py#L916) |
| Apps | Servicios de streaming sugeridos, apps con URL personalizada, apps nativas `.desktop`, búsqueda y fijación de apps. | [`backend/main.py:202`](backend/main.py#L202), [`backend/main.py:567`](backend/main.py#L567), [`backend/main.py:627`](backend/main.py#L627) |
| Multimedia | Reproducir/pausar, detener, siguiente/anterior, avance/retroceso, volumen y silencio por uinput; el volumen usa PipeWire cuando está disponible. | [`backend/main.py:222`](backend/main.py#L222), [`backend/main.py:928`](backend/main.py#L928) |
| Volumen y salida de audio | Selecciona la salida (sink) de PipeWire, ajusta el volumen (0-150 en el teléfono, 0-100 en el panel de la TV) y silencia. | [`backend/system_platform.py:173`](backend/system_platform.py#L173), [`backend/system_platform.py:178`](backend/system_platform.py#L178), [`backend/system_platform.py:196`](backend/system_platform.py#L196) |
| Pantalla | Lee la salida activa, la resolución y la frecuencia actuales y los modos disponibles por xrandr. **Cambiar el modo no está expuesto en 1.0.1.** | [`backend/system_platform.py:512`](backend/system_platform.py#L512), [`frontend/status.html:495`](frontend/status.html#L495) |
| Wi-Fi | Escanea y conecta mediante NetworkManager (`nmcli`); el punto de acceso de configuración se informa en el panel y tiene endpoints de API, pero la interfaz de 1.0.1 no tiene un botón para iniciarlo o detenerlo. | [`backend/system_platform.py:308`](backend/system_platform.py#L308), [`backend/system_platform.py:313`](backend/system_platform.py#L313), [`backend/system_platform.py:691`](backend/system_platform.py#L691) |
| Bluetooth | Enciende y apaga el adaptador desde el panel de la TV; la API también lista dispositivos y estado de emparejamiento con `bluetoothctl`, pero 1.0.1 no tiene lista de dispositivos ni interfaz de emparejamiento. | [`backend/system_platform.py:402`](backend/system_platform.py#L402), [`backend/system_platform.py:433`](backend/system_platform.py#L433) |
| Energía | Suspender, reiniciar, apagar y reiniciar el servicio `linuxremoteplayer` desde los ajustes del teléfono. | [`backend/system_platform.py:736`](backend/system_platform.py#L736), [`frontend/index.html:492`](frontend/index.html#L492) |
| Panel de la TV | PIN/QR de emparejamiento, ajustes del sistema (audio, Wi-Fi, pantalla, Bluetooth) y estado de clientes, latencia y versión. | [`frontend/status.html:397`](frontend/status.html#L397) |

- **Bloqueo de anuncios y protección contra ventanas emergentes:** uBlock Origin viene incluido
  y forzado por política, así que funciona sin red; las listas de filtros se actualizan cuando la
  PC tiene internet. Las ventanas emergentes inesperadas se cierran automáticamente y el panel
  conserva el foco.

## Actualizaciones

No hay OTA ni canal de autoactualización en 1.0.1. Cada versión se instala desde su ISO. La ruta soportada es arrancar la ISO nueva y reinstalar; el instalador borra el disco destino, así que los ajustes y los datos no se conservan. Planifica una copia de seguridad antes de actualizar. No hay una actualización de paquetes en el lugar desde la TV ni desde el teléfono.

## Privacidad

- **Sin cuentas, sin claves de licencia y sin telemetría.** El backend y el frontend no incluyen analítica ni cliente de nube. La única credencial es el token de emparejamiento local.
- **El control se queda en la LAN.** La API HTTPS/WSS escucha en el puerto 8000 y autentica con el token de emparejamiento. El panel y los endpoints del token exigen loopback.
- **Datos en la PC:** el estado mutable (`.env`, `.pairing_token`, `certs/`) vive en `/var/lib/linuxremoteplayer` con permisos `0700`. La clave privada de la CA nunca sale de la PC.
- **Datos en el teléfono:** la app de Android guarda la última URL en `SharedPreferences` y el WebView mantiene el almacenamiento local de la PWA (token y preferencias de interfaz); la PWA en Safari hace lo mismo en su propio almacenamiento. Ninguna envía datos de uso.
- **Tráfico saliente:** LRP OS no llama a casa. El navegador kiosk puede abrir los sitios de streaming que elijas, y descargar la APK desde la web es una petición web normal. No hay actualizaciones automáticas configuradas.

## Limitaciones conocidas

- **APK de Android no probada en hardware físico.** Compila y se publica, pero el autor no la ha validado en un dispositivo físico.
- **Instalación física pendiente de validación por el autor.** La ISO, el instalador y la ruta de arranque están implementados, pero una instalación completa en hardware real sigue pendiente de la validación del autor.
- **La voz y el micrófono están ocultos en 1.0.1.** El backend contiene un pipeline local de STT/NLU, pero la interfaz del teléfono no expone micrófono; está previsto para una versión posterior.
- **Los ajustes de pantalla son de solo lectura.** El panel informa la salida de xrandr; no cambia la resolución ni la disposición.
- **El emparejamiento Bluetooth no está expuesto.** La interfaz solo permite encender y apagar el adaptador; no hay lista de dispositivos ni pantalla de emparejamiento.
- **El botón de pantalla completa de la rueda no funciona en 1.0.1.** Envía `KEY_F11` ([`frontend/index.html:296`](frontend/index.html#L296)), que no está en la lista blanca de teclas del backend ([`input_emulator.py:16`](backend/input_emulator.py#L16)); el kiosk ya se ejecuta en pantalla completa.
- **No hay controlador NVIDIA en la ISO.** El soporte de RTX 3060 es el bootstrap opcional descrito arriba y requiere Secure Boot desactivado.
- **No hay OTA.** Reinstalar desde una ISO nueva borra el disco.
- **La APK de Android omite a propósito la validación del certificado TLS.** Es una decisión de diseño para LAN, no apta para redes no confiables.
- **iOS requiere aceptar el aviso del certificado** (o confiar en la CA local) en el primer uso.
- **La instalación en BIOS legacy no está soportada.** Usa UEFI.

## Compilar desde el código

Compila en Debian 13 (o WSL con Debian 13) sobre un sistema de archivos Linux nativo. `live-build` necesita `mknod` y `chroot`; `/mnt/*` (WSL/DrvFs) no sirve.

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-dev build-essential git \
  ffmpeg curl ca-certificates openssl wmctrl pulseaudio-utils firefox-esr live-build

# 1. Paquete .deb -> dist/linuxremoteplayer_1.0.1_amd64.deb
./scripts/build_deb.sh

# 2. ISO híbrida con el .deb dentro
./scripts/debian/iso/build_iso.sh \
  --deb dist/linuxremoteplayer_1.0.1_amd64.deb \
  --output dist/lrp-os_1.0.1_amd64.iso

# Validar la configuración de la ISO sin construir
./scripts/debian/iso/build_iso.sh --dry-run \
  --deb dist/linuxremoteplayer_1.0.1_amd64.deb

# Pruebas
python -m pytest -q tests/
```

El build del `.deb` ejecuta `scripts/check_css_sync.py`, prepara backend y frontend en `/opt/linuxremoteplayer` y escribe `dist/linuxremoteplayer_<VERSION>_amd64.deb`. El build de la ISO ejecuta `lb config` con `iso-hybrid`, amd64, `trixie`, `main contrib non-free non-free-firmware`, luego `lb build` y escribe un sidecar `.sha256`.

Para compilar la aplicación de control remoto de Android (opcional):

```bash
cd android
gradle wrapper
./gradlew assembleRelease
```

Requiere JDK 17 y Android SDK 35. La APK queda en `android/app/build/outputs/apk/release/`; sin configuración de firma, no está firmada. Consulta [`android/README.md`](android/README.md).

Más detalle: [docs/DEVELOPING.md](docs/DEVELOPING.md) y [docs/DEPLOY.md](docs/DEPLOY.md).

## Estructura del repositorio

| Ruta | Contenido |
| --- | --- |
| `backend/` | Servicio FastAPI: emparejamiento, control REST/WS, audio, Wi-Fi, Bluetooth, pantalla, energía, CA local y kiosk. |
| `frontend/` | PWA sin build: control del teléfono y panel de estado de la TV; incluye una copia de la APK en `downloads/`. |
| `android/` | Wrapper WebView de Android que produce la APK de control remoto. |
| `scripts/` | Instalación, empaquetado `.deb`, bootstrap de Debian y de NVIDIA, e ISO. |
| `scripts/debian/iso/` | Configuración de `live-build`, hook de chroot, instalador, menú de arranque y lista de paquetes. |
| `tests/` | Pruebas por fase y contratos de seguridad y empaquetado. |
| `docs/` | Arquitectura, desarrollo y despliegue. |
| `website/` | Sitio estático ES/EN desplegado en Vercel; no forma parte del runtime. |

## Licencia

Copyright © 2026 Agustín (Gusitir) y contribuyentes.

LinuxRemotePlayer se distribuye bajo la **GNU General Public License v3.0**. Consulta [LICENSE](LICENSE), [NOTICE](NOTICE) y [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md). Los componentes de terceros (Debian, Firefox ESR, PipeWire, whisper.cpp y otros) conservan sus propias licencias; los textos completos están en `/usr/share/doc/<paquete>/copyright` en un sistema instalado.

## Reportar errores

Usa los [issues del repositorio](https://github.com/Gusitir/LinuxRemotePlayer/issues) e incluye:

- versión de LRP OS (`cat /VERSION`);
- método de instalación (ISO o código);
- hardware (CPU, GPU, modo de firmware, disco) y si Secure Boot estaba activado;
- pasos para reproducir y comportamiento esperado/obtenido;
- logs, sin tokens, claves de la CA ni datos personales.

Para fallos de instalación, adjunta `/var/log/lrp-install-report.txt` y `/var/log/lrp-install-grub.log`. Para fallos en ejecución, incluye `journalctl -u linuxremoteplayer`.

Reporta vulnerabilidades de forma privada mediante un [GitHub Security Advisory](https://github.com/Gusitir/LinuxRemotePlayer/security/advisories/new) y sigue [SECURITY.md](SECURITY.md). No abras un issue público con detalles de explotación.

## Solución de problemas

### La PC no arranca LRP OS

- Entra al menú de arranque del firmware y selecciona **LRP-OS**. El instalador crea esa entrada NVRAM e intenta dejarla primera en `BootOrder`.
- Asegúrate de que el firmware esté en modo **UEFI**, no CSM/legacy. El instalador crea una partición de sistema EFI en un disco GPT y no crea una partición BIOS Boot.
- Si el firmware ignora la entrada NVRAM, el respaldo `EFI/BOOT/BOOTX64.EFI` de la ESP debería arrancar igual.
- Con Secure Boot activado se necesita la ruta firmada shim + GRUB. Revisa `secure_boot_efi` y `nvram_entry` en el informe de instalación; si la ruta firmada falló, reinstala con el gestor de arranque firmado o desactiva Secure Boot para el bootstrap de NVIDIA.
- El informe del instalador está en `/var/log/lrp-install-report.txt` en el sistema instalado y en `/run/lrp-install-report.txt` en la sesión live.

### La ISO empezó a instalar sin preguntar

Es la entrada de arranque por defecto (`lrp_auto_install`). Esa entrada elige el primer disco fijo apto y lo borra. Usa la entrada **Live** para probar sin instalar y haz siempre una copia de seguridad del disco.

### La APK no se instala

- Android bloquea por defecto las apps de orígenes desconocidos. Permite que el navegador o el gestor de archivos que uses instale apps desconocidas y vuelve a abrir la APK.
- Verifica el hash de la APK con `SHA256SUMS`; una descarga truncada no se instala.
- La app no está en Google Play, así que Play Protect puede pedir confirmación.

### El certificado no es válido

- LRP OS usa una CA local, no un certificado público. Safari en iOS te pide aceptarlo; la APK de Android lo acepta por diseño y te avisa.
- Asegúrate de abrir `https://<IP-DE-LA-PC>:8000` en la misma LAN, no un nombre público ni otra red.
- Si la IP de la PC cambió, el certificado hoja se regenera para la nueva IP; acepta el nuevo certificado en el teléfono.
- Para confiar explícitamente en la CA, descarga `https://<IP-DE-LA-PC>:8000/api/ca` e instálala en el teléfono.

### El panel no carga o el teléfono no conecta

- Revisa el servicio: `systemctl status linuxremoteplayer` y `journalctl -u linuxremoteplayer -n 100`.
- Confirma que el backend escucha en el puerto 8000 y que el firewall lo permite (`ufw status`).
- Usa la IP LAN de la PC; `lrp.local` depende de mDNS/Avahi.
- Reinicia el servicio después de cambiar de red: `sudo systemctl restart linuxremoteplayer`.

### No hay audio

- Abre el panel de la TV → **Ajustes de Sistema → Audio** y selecciona la salida HDMI/PipeWire.
- Revisa el volumen y el silencio en el mismo panel.
- Si la lista de salidas está vacía, verifica que PipeWire/WirePlumber estén ejecutándose para el usuario `lrp`.
