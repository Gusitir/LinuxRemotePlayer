# Reporte de Error: Instalación de LinuxRemotePlayer v1.1.1

## Resumen

El instalador `curl -fsSL https://linux-remote-player.vercel.app/install.sh | sudo bash` falla porque el script `postinst` del paquete `.deb` no logra completar su ejecución, dejando el paquete en estado **`half-configured`** y sin crear el binario `/usr/local/bin/lrp-setup` que el instalador espera ejecutar al final.

---

## Estado Actual del Sistema

```
dpkg --status linuxremoteplayer
  Package: linuxremoteplayer
  Status: install ok half-configured
  Version: 1.1.1
```

- El venv `/opt/linuxremoteplayer/backend/.venv/` sí fue creado.
- `/usr/local/bin/lrp-setup` **NO existe**.
- No hay ningún servicio systemd configurado (ni de sistema ni de usuario).

---

## Cadena de Error (Paso a Paso)

### 1. El instalador online (`install.sh` en Vercel)

```bash
# Descarga el .deb, lo instala con apt-get, luego ejecuta:
/usr/local/bin/lrp-setup   # ← ESTO FALLA: el archivo no existe
```

### 2. El `.deb` ejecuta `postinst` al instalarse

El script `DEBIAN/postinst` (generado por `build_deb.sh`) hace esto en orden:

1. Carga el módulo `uinput` y configura udev
2. Crea el venv: `python3 -m venv .venv` ← **OK**
3. Instala dependencias: `.venv/bin/pip install -r requirements.txt` ← **FALLA**
4. Crea `/usr/local/bin/lrp-setup` ← **NUNCA SE EJECUTA**
5. Crea `/usr/local/bin/lrp-update` ← **NUNCA SE EJECUTA**

### 3. Causa raíz del fallo

El requirements.txt incluye `evdev>=1.6,<2.0`, un paquete con extensión C que necesita compilarse:

```
Building wheel for evdev (pyproject.toml): finished with status 'error'
  error: command 'x86_64-linux-gnu-gcc' failed: No such file or directory
```

**El sistema no tiene `gcc` instalado.** Los paquetes que faltan son:

| Paquete | Propósito |
|---------|-----------|
| `build-essential` | Proporciona `gcc`, `make` y herramientas de compilación |
| `python3-dev` | Proporciona los headers de Python (`Python.h`) |

### 4. El `set -e` mata el script

El `postinst` tiene `set -e` (línea 54 de `build_deb.sh`). Apenas `pip install` devuelve exit code != 0, el script termina inmediatamente. Todo lo que estaba después (crear `lrp-setup`, `lrp-update`) jamás se ejecuta.

---

## Problemas en `build_deb.sh`

### Problema 1: Falta dependencia de compilación

**Archivo:** `build_deb.sh`
**Línea:** 41-48

```bash
# DEBIAN/control
cat <<EOF > pkg/DEBIAN/control
Package: linuxremoteplayer
Version: ${VERSION}
Architecture: all
Maintainer: LinuxRemotePlayer
Description: Remote Linux Player API and web interface
Depends: python3, python3-venv, openssl, avahi-daemon        # ← FALTA build-essential y python3-dev
Recommends: chromium | chromium-browser, ufw
EOF
```

`python3-venv` y `python3-dev` existen, pero el compilador `gcc` solo viene con `build-essential`. En Ubuntu 24.04, `python3-dev` instala los headers pero no necesariamente `gcc`.

### Problema 2: `postinst` no tolera fallos parciales

**Archivo:** `build_deb.sh`
**Línea:** 52-125

El `postinst` entero tiene `set -e`. Si falla `pip install`, se pierde todo el resto del setup (incluyendo la creación de `lrp-setup` y `lrp-update`). Sería mejor:
- Mover `pip install` a `lrp-setup` para que sea un paso separado y no bloquee la instalación del paquete.
- O mitigar el error con `|| true` y un mensaje de advertencia.

---

## Diferencias entre el instalador online y el postinst del .deb

El `install.sh` de Vercel y el `postinst` en `build_deb.sh` hacen cosas similares pero están desincronizados:

| Acción | `install.sh` (Vercel) | `postinst` (build_deb.sh) |
|--------|----------------------|---------------------------|
| Instalar `python3-dev`, `python3-venv`, `ufw`, `avahi-daemon` | ✅ Sí | ❌ No (solo en Depends) |
| Instalar `build-essential` / `gcc` | ❌ No | ❌ No |
| Configurar uinput/udev | ✅ Sí | ✅ Sí |
| Crear venv + pip install | ❌ No (lo delega en `lrp-setup`) | ✅ Sí (pero falla) |
| Crear `/usr/local/bin/lrp-setup` | ❌ No (espera que exista) | ✅ Sí (pero nunca llega) |
| Configurar systemd service | ✅ Sí (en `lrp-setup`) | ❌ No (delegado a `lrp-setup`) |

---

## Archivos Relevantes

| Archivo | Propósito |
|---------|-----------|
| `scripts/build_deb.sh` | Genera el `.deb` (control, postinst, prerm) |
| `scripts/install.sh` | Setup completo (venv, systemd, firewall) - corre en máquina destino |
| `backend/requirements.txt` | Dependencias Python (`evdev` requiere compilación) |
| `https://linux-remote-player.vercel.app/install.sh` | Instalador online (descarga .deb, lo instala, corre `lrp-setup`) |

---

## Soluciones Propuestas (para implementar en `build_deb.sh`)

### Opción A (Recomendada): Añadir `build-essential` a Depends

```bash
Depends: python3, python3-venv, python3-dev, build-essential, openssl, avahi-daemon
```

Esto asegura que `gcc` esté disponible cuando `pip install` compile `evdev`.

### Opción B: Mover `pip install` fuera del postinst

Que el `postinst` solo cree los binarios `lrp-setup` y `lrp-update`, y delegar la instalación de dependencias Python a `lrp-setup` (que ya ejecuta `scripts/install.sh`). Esto hace que la instalación del `.deb` nunca falle por dependencias Python.

### Opción C: Hacer el pip install tolerante a fallos

```bash
.venv/bin/pip install -r requirements.txt || echo "[!] pip install failed, run 'sudo lrp-setup' to retry"
```

Sin `set -e` o con `|| true`, para que aunque falle `pip install`, el resto del `postinst` se ejecute y al menos se creen los binarios.

---

## Comandos de Verificación

```bash
# Ver estado del paquete
dpkg --status linuxremoteplayer

# Verificar si existe lrp-setup
ls -la /usr/local/bin/lrp-setup

# Ver si gcc está instalado
which gcc

# Reconfigurar el paquete (para reintentar el postinst después de instalar gcc)
apt-get install -y build-essential
dpkg --configure linuxremoteplayer
```
