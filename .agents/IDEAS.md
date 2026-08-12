# IDEAS — posibilidades no decididas

Nada de este archivo crea tareas. Las decisiones local-first, sin premium y Patreon ya se
mudaron a CURRENT/PLAN y no se discuten aquí.

## 1 — ¿dos modos o una sola interfaz adaptativa?

### Hipótesis fuerte

No pensar “dedicado = más permisos” y “escritorio = menos permisos”. Son experiencias distintas:

- **Escritorio:** la computadora sigue siendo protagonista; LRP ofrece touchpad, teclado,
  shortcuts, apps del sistema y funciones power-user.
- **Dedicado:** la TV y el contenido son protagonistas; LRP guía hacia apps predeterminadas,
  reproducción y voz, mientras herramientas de sistema requieren intención deliberada.

La pregunta sin resolver es si necesitan modos separados o una misma arquitectura que cambie
jerarquía, onboarding y HUD según el objetivo. “Guiar sin prohibir” sigue siendo el principio.

### Requisitos que sobreviven a cualquier diseño

- Salida de emergencia antes de restringir.
- Todo cambio del sistema tiene desinstalación/reversión.
- Un power user conserva combinaciones y automatizaciones allowlist.
- Teclado/mouse son normales al instalar y excepcionales en uso diario.
- Si LRP falla en modo dedicado, no debe convertir la máquina en un ladrillo.
- La pantalla del HTPC puede ser informativa —QR, PIN, estado— sin competir con el teléfono.

## 2 — sesión dedicada

Una sesión propia es preferible a modificar agresivamente el escritorio habitual del usuario.
Puede tener autologin, navegador kiosk, panel informativo y políticas limitadas, mientras una
sesión de mantenimiento conserva escritorio/SSH. Firefox kiosk y políticas de escritorio son
capas complementarias, no alternativas.

Modelo de amenaza acordado:

- Defender al usuario sin conocimientos de errores accidentales.
- No intentar hacer invulnerable el equipo ante una persona local destructiva.
- Sí defender de atacante remoto, malware, navegador comprometido y cadena OTA.

## 3 — actualización que no empeora el equipo

“100% infalible” se traduce en una propiedad verificable: una actualización fallida no deja la
máquina peor que antes. Firma, staged install, health-check, rollback y recuperación. Para el
appliance puede evolucionar a sistema por imágenes/A-B; para la app, paquete anterior conocido.

## 4 — imagen Debian LRP

No es una distro nueva: sería una imagen reproducible sobre Debian estable con LRP y una sesión
HTPC opinada.

Flujo deseado:

```text
USB → instalación con confirmación de disco → arranque → panel QR/PIN → teléfono → uso diario
```

Arquitectura posible:

- Usuario TV: autologin, sin sudo, sin terminal visible.
- Usuario dueño: contraseña y acceso de mantenimiento/SSH.
- Cage u otra sesión ligera, PipeWire y navegador kiosk.
- LRP local preinstalado; datos y modelos en área mutable explícita.
- Parches de seguridad y LRP con mecanismos separados, firmados y recuperables.
- Una ISO por generación de Debian, no por versión de LRP.

Desafíos: instalación y particionado seguros, firmware/Wi-Fi, Secure Boot, DRM/VA-API, soporte de
hardware, hosting de imágenes, obligaciones de redistribución, recuperación y años de parches.
La decodificación de video puede ser el límite antes que la inferencia o el escritorio.

Secuencia correcta: motor local → modo dedicado → sesión dedicada → imagen. Una ISO no arregla
componentes inmaduros; solo los multiplica.

## 5 — Windows

Viable, no prioritario. Se reutilizan PWA, protocolo, pairing, intención y gran parte del backend;
se reescriben input, discovery, ventanas, audio, servicio, certificados, firewall, instalador,
desinstalador y updater. Considerarlo solo ante demanda sostenida después de consolidar Linux.

## 6 — extensiones del ecosistema

- Control de presentaciones y macros declarativas: mismo motor de input, HUD diferente.
- Gamepad multijugador desde teléfonos.
- Archivos locales y “reproducir en TV”, sin venderlo como NAS.
- Skins/layouts accesibles y temas visuales 2.0.
- Demo web sin backend que muestre el control de forma honesta.
- Adaptadores para Kodi/Jellyfin/VLC además de servicios web.

No priorizar ninguna hasta estabilizar la base local.

## 7 — preguntas abiertas para futuras conversaciones

- ¿Dos perfiles STT —ligero/preciso— o una única configuración recomendada?
- ¿Descargar el modelo al instalar o en el primer uso con verificación firmada?
- ¿VAD en el teléfono, el HTPC o ambos?
- ¿Qué historial es útil sin convertir LRP en un sistema de vigilancia doméstica?
- ¿Qué acciones requieren confirmación y cómo se expresa sin volver torpe la voz?
- ¿Elastic 2.0 y repo privado siguen alineados con una app gratuita financiada por Patreon?
- ¿El appliance usa Debian convencional con rollback propio o una base atómica?
