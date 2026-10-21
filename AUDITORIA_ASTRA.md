# Auditoría Astra — código

Fecha: 2026-09-04.

## Alcance

Código de `.worktrees/debian-foundation`, rama `codex/debian-foundation`, commit base `95490ce`, incluidos los cambios locales sin commit de T-132 presentes durante la revisión.

Revisión de backend, PWA y rutas de instalación y actualización, con inspección adicional del código cloud. Los hallazgos corresponden a ese worktree; no constituyen una certificación del artefacto publicado ni del estado desplegado.

No se modificó código. Este documento registra los resultados; no implementa correcciones.

## Hallazgos

### ASTRA-01 — [P1] Escalada de `lrp` a root durante OTA

El instalador entrega todo `/opt/linuxremoteplayer` al usuario `lrp`, incluido el entorno virtual `.venv`. El `postinst` ejecuta como root `.venv/bin/pip`, que ese usuario puede modificar. El usuario `lrp` pertenece al grupo `input`, autorizado a invocar el actualizador mediante sudo sin contraseña.

Un proceso que ya ejecute como `lrp` puede alterar el ejecutable del entorno virtual y provocar su ejecución como root al invocar la OTA. El entorno virtual no forma parte del contenido empaquetado que la reinstalación reemplaza.

Evidencia:

- `.worktrees/debian-foundation/scripts/install.sh:83`: `chown -R` de la aplicación a `lrp`.
- `.worktrees/debian-foundation/scripts/build_deb.sh:82`: reutilización del entorno virtual existente.
- `.worktrees/debian-foundation/scripts/build_deb.sh:86`: ejecución de `.venv/bin/pip` desde `postinst`.
- `.worktrees/debian-foundation/scripts/build_deb.sh:234`: autorización sudo para `%input`.
- `.worktrees/debian-foundation/scripts/debian/platform-bootstrap.sh:35`: incorporación de `lrp` al grupo `input`.

Corrección recomendada: mantener código y entorno virtual bajo propiedad root; separar tokens, configuración, certificados y otros datos mutables en directorios específicos.

Validación: trazado estático de permisos y ejecución privilegiada. No se ejecutó una escalada ni una OTA.

### ASTRA-02 — [P1] Regenerar el token no revoca conexiones existentes

La regeneración sustituye `auth.PAIRING_TOKEN`, pero los WebSockets ya autenticados conservan `is_authenticated=True`. Las órdenes posteriores no vuelven a validar el token ni una generación de sesión.

Un cliente conectado antes de la rotación mantiene el control hasta que su conexión termine, aunque su token ya no permita abrir conexiones nuevas.

Evidencia:

- `.worktrees/debian-foundation/backend/main.py:397`: actualización del token global.
- `.worktrees/debian-foundation/backend/main.py:964`: establecimiento del estado autenticado.
- `.worktrees/debian-foundation/backend/main.py:974`: autorización posterior basada únicamente en el booleano de sesión.

Corrección recomendada: cerrar las sesiones existentes al rotar el token o comprobar una generación de autenticación antes de ejecutar cada mensaje.

Validación: se extrajo por AST la función real del WebSocket y se ejecutó en memoria con transporte y teclado simulados. Después de autenticar con el token anterior y cambiar el token vigente, la sesión ejecutó una orden de texto. Resultado: `old_session_actions = ['still accepted']`.

### ASTRA-03 — [P2] La voz lenta provoca desconexiones del control remoto

El backend espera `voice_command()` dentro del mismo bucle que recibe los mensajes WebSocket. Mientras espera el resultado de voz, no procesa los pings pendientes. El frontend envía heartbeat cada 10 segundos y evalúa su timeout 5 segundos después.

Una respuesta de voz suficientemente lenta provoca el cierre del WebSocket y la reconexión del control remoto. El procesamiento de voz puede seguir pendiente cuando el cliente cierra la conexión.

Evidencia:

- `.worktrees/debian-foundation/backend/main.py:827`: recepción secuencial de mensajes.
- `.worktrees/debian-foundation/backend/main.py:851`: espera del resultado de voz dentro de ese bucle.
- `.worktrees/debian-foundation/frontend/app.js:402`: timeout del heartbeat.
- `.worktrees/debian-foundation/frontend/app.js:409`: intervalo de 10 segundos.

Corrección recomendada: procesar la voz sin detener la recepción del WebSocket, con concurrencia limitada y gestión explícita de cancelación y desconexión.

Validación: ejecución del heartbeat real en un contexto JavaScript aislado con reloj y temporizadores simulados. Sin respuesta pong, el socket se cerró a los 15 segundos. No se realizaron llamadas a proveedores de voz.

### ASTRA-04 — [P2] HTTPS reutiliza certificados caducados

`ensure_cert()` acepta el certificado existente si están presentes los archivos y coinciden IP y hostname. No comprueba su vigencia. El certificado de hoja se emite por 825 días; después de caducar, reiniciar el servicio no fuerza su renovación si la identidad permanece igual.

Evidencia:

- `.worktrees/debian-foundation/backend/run.py:159`: retorno anticipado basado en existencia e identidad.
- `.worktrees/debian-foundation/backend/run.py:186`: emisión de la hoja con duración de 825 días.

Corrección recomendada: verificar la vigencia del certificado y de la CA, y renovar la hoja anticipadamente cuando corresponda.

Validación: ejecución aislada de la función extraída por AST, simulando archivos existentes e identidad coincidente. Devolvió `True` sin ejecutar verificaciones de vigencia ni renovación. No se generaron ni modificaron certificados reales.

## Validación y límites

- Compilación en memoria de los 8 módulos Python del backend: correcta, sin importar el runtime ni escribir bytecode.
- `node --check` sobre `frontend/app.js` y `frontend/sw.js`: correcto.
- Reproducciones aisladas de revocación de sesión, timeout del heartbeat y ruta de reutilización del certificado.
- No se ejecutó la suite completa, instalación, OTA, explotación de privilegios ni pruebas en el HTPC.
- No se verificó el estado desplegado de los servicios cloud.
- La ausencia de otros hallazgos no demuestra ausencia de defectos.

Las referencias de línea corresponden al código observado durante esta revisión y pueden desplazarse con cambios posteriores.

---

## Estado de Resolución (Remediación Verificada)

Todos los hallazgos de esta auditoría fueron formalmente remediados, probados con suites automáticas dedicadas y verificados por el Arquitecto bajo garantía Standard:

| Hallazgo | Severidad | Tarea | Commit | Estado | Evidencia |
|---|---|---|---|---|---|
| **ASTRA-01** (Root escalation en `/opt`) | **P1** | T-134 | `610194e` | **Cerrado APTO** | Permisos `root:root` en `/opt/linuxremoteplayer` y `.venv`; mutables en `/var/lib/linuxremoteplayer/`; 232/232 tests pass. |
| **ASTRA-02** (Sesiones WS sin revocación al regenerar token) | **P1** | T-134 | `610194e` | **Cerrado APTO** | Cierre inmediato de WebSockets autenticados en `regenerate_pairing_token()`; pruebas de revocación activa en `test_security_mitigations.py`. |
| **ASTRA-03** (Desconexión de WS por bloqueo en voz) | **P2** | T-135 | `ebfdf82` | **Cerrado APTO** | Procesamiento de voz desacoplado en background task asíncrona; recepción de heartbeat ping/pong continua y fluida; 235/235 tests pass. |
| **ASTRA-04** (Certificados HTTPS caducados reutilizados) | **P2** | T-135 | `ebfdf82` | **Cerrado APTO** | Verificación `notAfter` en `backend/run.py` con regeneración automática ante caducidad y verificación RTC vía `systemd-timesyncd`. |
