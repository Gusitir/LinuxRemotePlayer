# Política de seguridad

LRP OS es un producto que se ejecuta en la red local del usuario: la PC de la TV y los teléfonos
emparejados. Esta política describe cómo reportar problemas y qué se considera parte del alcance.

## Cómo reportar una vulnerabilidad

Usá un **GitHub Security Advisory privado** del repositorio:

<https://github.com/Gusitir/LinuxRemotePlayer/security/advisories/new>

No abras un issue público con detalles explotables: un advisory privado permite coordinar la
corrección y la publicación.

Incluí:

- versión de LRP OS (`cat /VERSION`) y método de instalación (ISO o desarrollo),
- hardware y distro base,
- pasos para reproducir y el impacto esperado,
- logs o capturas sin datos personales.

La respuesta es best-effort; no hay un SLA contractual.

## Alcance

- Backend FastAPI (`backend/`) y su API/WebSocket.
- PWA del teléfono (`frontend/`) y el panel de la TV.
- Pairing (PIN, token, QR) y la CA local.
- Instalador de la ISO, hook de chroot y unidad systemd.
- Scripts de empaquetado e instalación del repositorio.

Fuera de alcance:

- Acceso físico a la PC o al teléfono.
- Paquetes de Debian, Firefox ESR, PipeWire o el kernel: se reportan aguas arriba.
- Configuraciones de red del usuario (router, Wi-Fi de invitados).
- Ingeniería social.

## Reglas para reportes

- No publiques exploits ni pruebas de concepto funcionales en issues públicos.
- No hagas pruebas contra instalaciones de terceros sin permiso.
- No incluyas datos personales, tokens de pairing ni claves de la CA en el reporte.

## Secretos en el repositorio

- El repo no contiene `.env`, tokens de pairing, claves privadas de la CA ni credenciales de
  servicios.
- El `.env` es local y está en `.gitignore`; el token de pairing se genera en la PC.
- Si un secreto se filtra: rotá el token de pairing (invalida las sesiones activas), regenerá la CA
  local y revocá cualquier credencial expuesta.
- Cualquier secreto commiteado se considera un incidente y se rota, no solo se borra del historial.

## Versiones soportadas

Solo la última release estable de la serie 1.0.x recibe correcciones de seguridad.
