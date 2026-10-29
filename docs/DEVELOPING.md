# Desarrollo de LRP OS

Guía para trabajar en LRP OS 1.0.0: entorno, build del paquete y de la ISO, y política de pruebas
por fase.

## 1. Entorno

Se desarrolla en Debian 13 (o WSL con Debian 13). El código se ejecuta en Linux: `evdev`/`uinput`
y `pactl` no existen en Windows.

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-dev build-essential git \
    ffmpeg curl ca-certificates openssl wmctrl pulseaudio-utils firefox-esr

python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt
```

Para desarrollo del panel y de la PWA:

```bash
cd backend
LRP_DEV=true .venv/bin/python run.py     # HTTPS en https://127.0.0.1:8000
```

`LRP_DEV=true` habilita `/docs` y `/openapi.json`. Nunca se deja activo en una instalación real.

## 2. Pruebas (D57: micro-gates por fase)

La suite completa **no** se corre en cada tarea. Cada tarea valida solo lo que toca:

| Cambio | Micro-gates |
| --- | --- |
| Python del backend | `python -m py_compile backend/*.py` y los tests del área |
| Frontend | `node --check frontend/app.js`, parse del JS inline, `python scripts/check_css_sync.py` |
| Scripts shell | `bash -n scripts/<archivo>.sh` |
| Sitio | chequeo de links relativos y grep de términos prohibidos |

Al **cierre de fase** se corre la suite completa:

```bash
python -m pytest -q tests/
```

Los tests por área más usados:

```bash
python -m pytest -q tests/test_local_intent.py tests/test_local_stt.py
python -m pytest -q tests/test_security_mitigations.py tests/test_system_platform.py
python -m pytest -q tests/test_kiosk_debian.py
```

## 3. Build del paquete `.deb`

```bash
./scripts/build_deb.sh
```

Deja `dist/linuxremoteplayer_<VERSION>_amd64.deb` y su `.sha256`. El script corre el chequeo de CSS
y falla si el empaquetado queda inconsistente.

## 4. Build de la ISO

Requiere `live-build` y un filesystem Linux nativo: `/mnt/*` (WSL/DrvFs) no sirve porque
`live-build` necesita `mknod` y `chroot`.

```bash
sudo apt install -y live-build
./scripts/debian/iso/build_iso.sh \
    --deb dist/linuxremoteplayer_<VERSION>_amd64.deb \
    --output dist/lrp-os_<VERSION>_amd64.iso
```

Para validar la configuración sin construir:

```bash
./scripts/debian/iso/build_iso.sh --dry-run --deb dist/linuxremoteplayer_<VERSION>_amd64.deb
```

La ISO arranca en BIOS y UEFI (híbrida), pero la instalación a disco está soportada solo en UEFI:
el instalador crea GPT con ESP y no crea una partición BIOS Boot. Escribe GRUB con shim, crea la
entrada NVRAM `LRP-OS`, deja el autologin de `tty1` y el arranque al panel.

## 5. Convenciones

- **Commits:** `[T-NN] descripción corta` para una tarea; `[STATE] descripción` para cambios de
  estado del proyecto. Sin commits gigantes mezclando tareas.
- **Ramas/worktrees:** una rama por fase o tarea grande; no se commitea desde un worktree ajeno.
- **Secretos:** prohibido commitear `.env`, tokens de pairing, claves privadas de la CA o cualquier
  credencial. `.env` está en `.gitignore`; el token se genera en la PC.
- **Agentes:** los workers no editan `.agents/` ni commitean. El plano de control vive en `.agents`.
- **Frontend:** no se agrega `viewport-fit=cover` (rompe el layout de iOS al reabrir la PWA).

## 6. Trampas conocidas

- El grupo `input` recién aplica después de reiniciar (teclado/mouse virtuales).
- El certificado local se regenera cuando cambia la IP: el teléfono debe volver a aceptarlo.
- Rotar el token de pairing cierra todos los WebSocket activos (código 1008).
- Firefox ESR kiosk usa un perfil dedicado (`~/.config/lrp-kiosk-firefox`): no lo bloquees con
  otra instancia del mismo perfil.
- La voz es 100% local; si `whisper-cli` o el modelo no están, el pipeline devuelve error sin
  bloquear el resto del control.
- El driver NVIDIA no forma parte de la ISO ni del instalador: se instala aparte con
  `scripts/debian/bootstrap.sh` (`nvidia-bootstrap.sh`) y el script exige Secure Boot desactivado.
