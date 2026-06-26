# Probar en tu TV / HTPC (sin IA)

Guía para instalar y probar el control en un PC Linux real **sin configurar nada de IA**
(sin Supabase, sin claves NVIDIA/OpenRouter, sin Stripe). El botón de micrófono queda
oculto automáticamente mientras `ENABLE_VOICE=false`.

## 1. En el PC/TV (servidor)

```bash
git clone <tu-repo> linuxremoteplayer
cd linuxremoteplayer
sudo ./scripts/install.sh        # instala deps, permisos uinput, Chromium, cert HTTPS
```

El instalador:
- instala dependencias, `python3-venv`, `ufw`, **Chromium**;
- configura permisos de `/dev/uinput` (teclado/ratón virtual) — **requiere reiniciar o re-login una vez**;
- genera el certificado HTTPS automáticamente;
- crea el servicio (Appliance = arranque dedicado / Desktop = servicio de usuario).

> Tras la primera instalación, **reinicia** (o cierra y reabre sesión) para que el grupo
> `input` y el módulo `uinput` queden activos.

Arranque manual para depurar (en vez del servicio):

```bash
cd backend
source .venv/bin/activate
python run.py        # sirve en https://<ip>:8000
```

## 2. En el teléfono (cliente)

1. Conéctate al **mismo WiFi** que el PC.
2. Abre `https://<IP-del-PC>:8000` en el navegador.
3. Acepta el certificado autofirmado **una vez** (Avanzado → Continuar).
4. **Instala la PWA** siguiendo el tutorial en pantalla (Compartir → Añadir a inicio en iOS; menú ⋮ → Instalar en Android).
5. Abre la app **desde el icono** (no desde el navegador) para que se vea como app.

## 3. Qué probar (todo funciona sin IA)

- **Apps**: toca Netflix/YouTube/etc → debe abrir Chromium en kiosk en el PC. "Más apps" despliega el resto.
- **Touchpad**: arrastra en el recuadro → mueve el puntero del PC. Toque corto = clic.
- **D-pad + OK**: flechas y Enter (navegación / avanzar-retroceder video).
- **Home**: cierra la app kiosk. **Atrás**: Esc.
- **Multimedia**: ⏮ ⏯ ⏭, y **volumen +/−** y **mute**.
- **Teclado**: botón ⌨ abre el teclado del teléfono; lo que escribes se teclea en el PC; **Done** cierra el teclado.
- **Cerrar app**: botón Home.

## 4. Diagnóstico

```bash
# ¿El backend ve uinput?  -> abre en el navegador:
https://<ip>:8000/api/debug      # {"evdev_available": true, "is_ui_created": true, ...}

# ¿Config de voz?  -> /api/config  => {"voice_enabled": false}  (correcto sin IA)

# Logs del servicio (Desktop mode):
journalctl --user -u linuxremoteplayer.service -f
```

Si `is_ui_created` es `false`: faltan permisos uinput → reinicia tras el install, o revisa
que tu usuario esté en el grupo `input` (`id | grep input`).

Si una app NO abre ventana al tocarla: el servicio no tiene sesión gráfica. Para pruebas,
arranca el backend manualmente (`python run.py`) dentro de tu sesión de escritorio.

## 5. Cuando quieras activar la voz (más adelante)

En `backend/.env`: pon `ENABLE_VOICE=true` y configura STT/LLM (NVIDIA/OpenRouter o local).
El botón de micrófono reaparece solo. Hasta entonces, déjalo en `false`.
