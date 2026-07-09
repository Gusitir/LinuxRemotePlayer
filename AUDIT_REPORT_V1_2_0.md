# Reporte de Auditoría y Ejecución: Plan v1.2.0

## Contexto del Desarrollo
El usuario solicitó implementar el `PLAN_V1_2.md` con mejoras significativas en el proceso de emparejamiento (PIN en pantalla), robustez del instalador, y compatibilidad nativa con KDE Plasma Bigscreen. 

## Cambios Implementados (v1.2.0)

### 1. P1: Nuevo Flujo de Emparejamiento (PIN de 6 dígitos)
- **Backend (`main.py`)**: 
  - Se implementó la clase `PinManager` que genera un PIN seguro de 6 dígitos, con un TTL de 120 segundos.
  - Se agregaron los endpoints `/api/pairing-pin` (restringido a `localhost` para la TV) y `/api/pair` (público en la LAN).
  - Se incluyó protección contra fuerza bruta: limitación global (20 intentos fallidos / minuto) y limitación por IP (bloqueo de 60s tras 5 intentos fallidos).
- **Frontend (`index.html` y `app.js`)**: 
  - Se rediseñó el prompt inicial en el móvil (`#pairing-prompt-ui`) para pedir el PIN en lugar del antiguo token manual (el cual quedó como *fallback* oculto).
  - Se añadió la lógica en JS para enviar el PIN y almacenar el token automáticamente.
  - **Panel de Estado (`status.html`)**: Ahora muestra el PIN en texto enorme y realiza un *polling* cada 5s para refrescarlo, incluyendo un temporizador en vivo.

### 2. P2: Corrección del Bug de "Licencia Activa"
- **Bug**: En instalaciones limpias, la UI mostraba "Activa" por defecto porque el estado en `/api/status` estaba _hardcodeado_ a `True`.
- **Solución**: En `main.py`, la respuesta de `licensed` ahora evalúa de forma asíncrona la caché o el endpoint online (`auth.is_license_valid_cached_or_online`). La UI en `status.html` fue actualizada para renderizar "Sin licencia", "Activa (Pro)", o "Error al verificar".

### 3. P3 y P5: Robustez del Instalador y Manejo de Usuarios
- Se modificó `scripts/install.sh` para usar técnicas avanzadas de resolución del usuario activo (`TARGET_USER`) a través de `logname` y `loginctl`, evitando la dependencia frágil de `$SUDO_USER` en sesiones `su`.
- **Protección UFW (P5)**: Antes de aplicar un `ufw --force enable`, el instalador ahora asegura que el acceso SSH (puerto 22) esté permitido (`ufw allow OpenSSH || ufw allow 22/tcp`), previniendo aislar máquinas remotas.
- **Validación del `venv`**: Se añadió una comprobación estricta post-pip en `build_deb.sh` (`touch .deps_incomplete`). El `lrp-setup` aborta proactivamente y muestra instrucciones claras si el entorno de Python falla.

### 4. P4: Compatibilidad con KDE Plasma Bigscreen
- Se empaquetó el archivo `linuxremoteplayer-panel.desktop` y su ícono dentro de `/usr/share/applications/` de forma nativa en el `.deb`.
- Al finalizar `lrp-setup`, el instalador actualiza los cachés (`kbuildsycoca6/5`, `update-desktop-database`) y abre automáticamente el navegador en la URL del Panel de Estado para que el usuario pueda ver el PIN de inmediato.

### 5. P6: Empaquetado y Publicación
- Se compiló con éxito el paquete `linuxremoteplayer_1.2.0_all.deb` en el subsistema WSL (preservando permisos Linux).
- El binario fue verificado correctamente por `dpkg-deb`, copiado a la carpeta `/website/downloads/`, y el archivo `latest.json` fue actualizado con su respectivo `sha256`.
- Los cambios han sido subidos a la rama principal.

## Próximos Pasos (Validación del Cliente)
El paquete v1.2.0 ya está publicado y disponible para ser descargado e instalado.
El usuario procederá a validar la actualización en su HTPC con KDE Neon.
