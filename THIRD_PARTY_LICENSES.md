# Third-Party Licenses / Licencias de terceros

LRP OS 1.0.0 incluye y usa el siguiente software y recursos de terceros. Las licencias completas
de cada paquete están disponibles en el sistema instalado (`/usr/share/doc/<paquete>/copyright`)
y en los repositorios oficiales.

## Sistema base

### Debian 13 (trixie)

- Licencias: varias (GPL, LGPL, BSD, MIT, Apache-2.0 y otras), según el paquete.
- Uso: distribución base de la ISO; los textos de copyright de cada paquete están en
  `/usr/share/doc/*/copyright`.
- https://www.debian.org/legal/licenses/

## Navegador y multimedia

### Firefox ESR

- Licencia: Mozilla Public License 2.0 (MPL-2.0).
- Uso: navegador en modo kiosk para el panel y las apps web.
- https://www.mozilla.org/MPL/2.0/

### PipeWire

- Licencia: MIT.
- Uso: audio del sistema (salidas, volumen y mute vía `pactl`/`wpctl`).
- https://gitlab.freedesktop.org/pipewire/pipewire

### whisper.cpp

- Licencia: MIT.
- Uso: transcripción de voz local en la PC.
- https://github.com/ggerganov/whisper.cpp

## Dependencias Python

- FastAPI — MIT — https://github.com/fastapi/fastapi
- Uvicorn — BSD-3-Clause — https://github.com/encode/uvicorn
- python-dotenv — BSD-3-Clause — https://github.com/theskumar/python-dotenv
- python-evdev — BSD-3-Clause — https://github.com/gvalkov/python-evdev
- segno — BSD-3-Clause — https://github.com/heuer/segno

## Extensiones del navegador

### uBlock Origin

- Autor: Raymond Hill (gorhill) — https://github.com/gorhill/uBlock
- Licencia: GNU General Public License v3.0 (GPLv3).
- Uso: NO se distribuye con el producto. `scripts/install.sh` configura Firefox para instalarlo
  desde el sitio oficial de addons de Mozilla en la máquina del usuario; el código y la licencia
  están en el repositorio oficial.

## Recursos visuales

### Space Grotesk

- Autor: Florian Karsten.
- Licencia: SIL Open Font License 1.1 (OFL).
- Uso: tipografía del sitio web (`website/fonts/`).

### Iconos de la aplicación

- Autoría propia del proyecto (Agustín / Gusitir), publicados bajo la licencia del repositorio
  (GNU GPL v3.0) salvo que se indique otra cosa.
- Algunos SVG de interfaz se basan en Reicon (MIT, Dev Chauhan — https://github.com/dqev/reicon).

## Marcas

Los nombres y logotipos de Debian, Mozilla/Firefox y los servicios de streaming mencionados en la
web pertenecen a sus respectivos titulares y se usan solo de forma descriptiva.
