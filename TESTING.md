# Probar en tu TV / HTPC (con y sin IA)

Guía para instalar y probar el control remoto, incluyendo la activación de licencias comerciales, actualizaciones y desinstalación.

---

## 1. En el PC/TV (servidor)

```bash
git clone <tu-repo> linuxremoteplayer
cd linuxremoteplayer
sudo ./scripts/install.sh        # instala deps, permisos uinput, Chromium, cert HTTPS
```

El instalador:
- instala dependencias: `python3-venv`, `ufw`, `avahi-daemon`, **Chromium**;
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

---

## 2. En el teléfono (cliente)

1. Conéctate al **mismo WiFi** que el PC.
2. Abre la URL de emparejamiento con el token imprimida en la terminal al arrancar (ej. `https://<hostname>.local:8000/?token=<token>`).
3. Acepta el certificado autofirmado **una vez** (Avanzado → Continuar).
4. **Instala la PWA** siguiendo el tutorial en pantalla (Compartir → Añadir a inicio en iOS; menú ⋮ → Instalar en Android).
5. Abre la app **desde el icono** (no desde el navegador) para que se vea como app independiente.

---

## 3. Qué probar (todo funciona sin IA de forma gratuita)

- **Apps**: toca Netflix/YouTube/etc → debe abrir Chromium en kiosk en el PC. "Más apps" despliega el resto.
- **Touchpad**: arrastra en el recuadro → mueve el puntero del PC. Toque corto = clic izquierdo; pulsación larga (>500ms) = clic derecho con vibración.
- **Scroll**: arrastra en el lateral derecho del touchpad para deslizar verticalmente.
- **Multimedia**: ⏮ ⏯ ⏭, y **volumen +/−** y **mute**.
- **Teclado**: botón ⌨ abre el teclado del teléfono; lo que escribes se teclea en el PC; **Done** cierra el teclado.
- **Cerrar app**: botón Home.

---

## 4. Pruebas de Licenciamiento y Voz (Fase C2/C3)

Para realizar pruebas del flujo comercial y control por voz:

### 4.1 Simular activación de licencia
1. En tu celular, entra a la app y pulsa el icono de engranaje (**Ajustes**).
2. En la sección **Clave de licencia**, introduce una clave de prueba. (Para pruebas de desarrollo con la Edge Function local, introduce cualquier clave válida; para pruebas online, introduce la clave entregada por correo o generada en la base de datos).
3. Presiona **Activar**. Deberías ver la notificación "Licencia activada con éxito" y el estado de la licencia cambiará a "activa (lifetime)".
4. El botón del micrófono (módulo de voz) se hará visible de inmediato.

### 4.2 Probar control por voz
1. Asegúrate de tener configurado `ENABLE_VOICE=true` y las API keys correspondientes (`NVIDIA_NIM_API_KEY`, `OPENROUTER_API_KEY`) en tu archivo `backend/.env`.
2. Mantén presionado el botón del micrófono y di un comando en español (ej. "pon vídeos de gatitos en youtube").
3. Al soltar, la barra de estado mostrará la transcripción e intención analizada, y el PC HTPC abrirá la URL del kiosk correspondiente.

---

## 5. Pruebas de Actualización (Fase C2-4)

1. En **Ajustes**, dirígete a la sección **Actualización** (muestra la versión actual, ej. `Versión 1.0.0`).
2. Toca **Buscar actualización**. Si creaste un tag superior en tu repositorio de GitHub, el botón cambiará a **Actualizar a vX.Y.Z**.
3. Toca el botón de actualizar. La app lanzará el script `scripts/update.sh` en segundo plano en el PC y mostrará un toast indicando que se reconectará sola.
4. El servicio del PC se reiniciará automáticamente con el nuevo código. La app móvil se reconectará en unos segundos tras el reinicio del socket.

---

## 6. Pruebas de Desinstalación (Fase C2-5)

1. En la consola de tu PC HTPC, ejecuta el comando de desinstalación:
   ```bash
   sudo ./scripts/uninstall.sh
   ```
2. Confirma con `y` cuando te lo solicite.
3. El script removerá los servicios systemd (de usuario y de sistema), deshará las reglas udev para uinput, eliminará los puertos del cortafuegos y limpiará entornos virtuales y certificados.
4. Verifica que el servicio esté apagado e inactivo:
   ```bash
   systemctl status linuxremoteplayer.service
   ```

---

## 7. Diagnóstico

```bash
# ¿El backend ve uinput?  -> abre en el navegador:
https://<ip>:8000/api/debug      # {"evdev_available": true, "is_ui_created": true, ...}

# ¿Configuración general? -> /api/config
# Logs del servicio (Desktop mode):
journalctl --user -u linuxremoteplayer.service -f
```
