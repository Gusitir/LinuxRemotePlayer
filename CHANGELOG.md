# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.8.0] - 2026-07-20

### Changed
- Release de limpieza y profesionalización pre-lanzamiento. Voz simplificada a solo cloud
  (Together: Whisper-large-v3 + Qwen2.5). README y sitio web corregidos. Paquete .deb más liviano.

### Removed
- Modo de IA local (Whisper/Ollama) y mock de testing; defaults obsoletos NVIDIA/OpenRouter.
- Página pair.html (reemplazada por status.html).

### Fixed
- Limpieza de imports y variables muertas en el backend (sin cambios de comportamiento).

## [1.7.8] - 2026-07-20

### Fixed
- **Card de voz visible en Ajustes**: la clase CSS `hidden` (`!important`) tapaba el
  estilo inline y el panel "Comandos de voz" nunca aparecía; ahora se togglea la clase.

## [1.7.7] - 2026-07-19

### Changed
- **Mejoras finales**: detector de apps abierto, voz robusta con prompt dinámico y errores claros, guía de comandos de voz, PWA auto-actualizable.

## [1.7.6] - 2026-07-19

### Fixed
- **Voz reparada**: crash con ENABLE_VOICE activo (variables obsoletas), soporte de micrófono en iOS (audio/mp4 dinámico), errores de micrófono visibles en la UI, log de audio recibido en el backend.

## [1.7.5] - 2026-07-19

### Changed
- **PWA**: Versionado dinámico del cache del Service Worker (sw.js auto-versionado en build). Las PWAs instaladas recibirán los assets (CSS/íconos) frescos automáticamente en cada release.
- **PWA / iOS**: Nota de actualización: iOS hornea las metas del PWA al instalar — tras updates que toquen manifest o metas apple-*, reinstalar la app en el teléfono.

## [1.7.4] - 2026-07-18

### Fixed
- **OTA**: El servicio se re-habilita y reinicia correctamente tras actualizar (prerm distingue upgrade de remove; updater decide por existencia del unit).

## [1.7.3] - 2026-07-18

### Fixed
- **Frontend/iOS**: Determinismo de viewport en iOS (black-translucent y padding gestionado por variables CSS según entorno).
- **Frontend/Favicons**: Restaurados los favicons de las aplicaciones sugeridas (diferenciando por origen `is_native` en lugar de por prefijo de ID).
- **Frontend/Ancladas**: Restaurado el botón de eliminar para las aplicaciones nativas ancladas.

## [1.7.2] - 2026-07-18

### Fixed
- **OTA Updater**: Solucionado fallo crítico que mataba el proceso de actualización en curso (el script interno se re-ejecuta como unit transitoria aislando su `cgroup` y preservando sus logs en `/tmp/lrp-update.log`).

## [1.7.1] - 2026-07-17

### Added
- **Latencia HUD**: Indicador de ping (RTT) en tiempo real en la barra de estado.

### Changed
- **Installer Robusto**: `certutil` ahora es no-interactivo para evitar bloqueos por contraseñas preexistentes de NSS. Políticas inyectadas tempranamente.
- **Flujo PIN-first**: Los mensajes post-instalación priorizan emparejar vía red local con PIN en vez del token en URL.
- **Nav-mode Rediseñado**: Overlay sutil con flechas direccionales e hint que desaparece.

### Fixed
- **Voz en iOS**: Solucionada condición de carrera que dejaba micrófonos abiertos; incorporado failsafe de 8s y overlay de estado prominente.
- **Layout Adaptativo**: Corrección de desbordamiento en pantallas 16:9 cortas (iPhone 8 Plus).
- **Favicons**: Corrección en cadena de íconos (API local, DDG, Google S2 y fallbacks).
- **Icono PWA iOS**: Actualizado `apple-touch-icon.png` a 180x180 opaco y referenciado en todos los flujos.
- **UFW**: Suprimidos falsos errores en sistemas sin perfiles de app (ej. OpenSSH).

## [1.7.0] - 2026-07-14

### Added
- **Firefox Kiosk**: Migrado el navegador por defecto de Brave/Chromium a Firefox con políticas empresariales inyectadas.
- **Wayland Window Management**: Soporte nativo para cerrar ventanas en KDE Wayland usando KWin Scripting por DBus.
- **Sleep Management**: Nueva opción en `lrp-setup` para deshabilitar completamente la suspensión/apagado de pantalla a nivel del sistema (ideal para modo Appliance).

### Changed
- **uBlock Origin**: Ahora instalado automáticamente en Firefox vía `policies.json`, eliminando la necesidad de empaquetar uBOL internamente.
- **Build Hygiene**: Erradicadas las dependencias y rastros residuales de Chromium y uBOL en los scripts de construcción de .deb.
- **Idle Audio Detection**: Ahora se advierte proactivamente si `pulseaudio-utils` falta en el sistema anfitrión.

## [1.6.0] - 2026-07-15

### Added
- **Brave Browser**: Brave with Shields active is now the default kiosk browser for better ad blocking and performance.
- **Keyboard Layouts**: Added support for es/latam keyboard layouts, including AltGr mapped keys.
- **CSS Safeguard**: Added anti-drift check for CSS utilities to ensure layout stability.

### Changed
- **Home Behavior**: The Home button now cleanly closes all desktop windows (via wmctrl/KWin), not just our own apps.
- **TV Panel Trigger**: The idle panel now properly detects active audio (via pactl) to prevent interrupting media played outside the app.
- **Navigation Back**: The 'back' combo now correctly simulates browser back without rewinding media players.
- **Certificates**: Local CA is now automatically trusted at the system level and NSS db, eliminating browser warnings on the HTPC.
- **Event Loop Performance**: Significantly reduced latency spikes by running blocking system calls in asynchronous threads.

### Fixed
- Fixed an issue where the TV panel would break due to a missing internal import.
- Simplified system icons using inline Lucide SVGs for better visual consistency.

## [1.5.0] - 2026-07-09

### Added
- **Design Line**: Introduced "Cozy Media" as the default design language with self-hosted Space Grotesk fonts.
- **KDE Bigscreen Support**: The installer now automatically disables `kscreenlocker` and DPMS screen blanking when installed in Appliance Mode to prevent disconnections.

### Changed
- **Website Compactness**: Simplified the website to focus purely on value proposition, demo, and direct installation.

### Fixed
- **QR Contrast**: Fixed an issue where the pairing QR code would be invisible on some phones by enforcing a white background with a quiet zone.
- **Home Button**: Fixed an issue where pressing the Home button would not correctly leave a clean desktop if no other screens were open.
- **App Updates**: Fixed an issue where the "Actualizar" button in the app failed to trigger the system-level updater script due to permissions.
- **Custom Apps Icons**: Custom web apps added locally now properly fall back to the default app icon if their favicon fails to load.
- **iOS Safe Area**: Fixed an issue where the UI could clip behind the notch or dynamic island on iPhones in landscape mode.

## [1.4.0] - 2026-07-09

### Added
- **Settings Categories**: Redesigned settings drawer with accordion categories for better UX.
- **Nav Mode**: Touchpad now supports a D-Pad mode (Up, Down, Left, Right, Enter, Esc) for easier navigation on Bigscreen.
- **App Tour**: Added a first-run tutorial highlighting UI elements.
- **Feedback Module**: Built-in support form linked to a new Supabase Edge Function to securely send suggestions to the owner.

### Changed
- **Favicons**: Implemented an automatic favicon resolution chain (Google -> DDG -> Domain) for custom apps and missing suggested apps.
- **Default Apps**: Default suggested apps can now be hidden/restored by the user.

### Fixed
- **Ad-block Hardening**: uBlock Origin Lite zip is now robustly flattened during installation, ensuring the Chromium kiosk correctly loads the manifest.
- **Meta Key Bug**: Restored OS Menu key functionality by correctly injecting the LEFTMETA capability requirement in the UInput emulator.
- **UI Overflow**: Fixed horizontal scroll issues in the settings panel by changing the skin carousel to a responsive grid.

## [1.3.1] - 2026-07-09

### Fixed
- curl/wget fallback en updater, uBlock en ruta legible por snap, catálogo completo, YouTube URL.

## [1.3.0] - 2026-07-09

### Added
- **Ad-blocking**: Integrated uBlock Origin Lite by default in Appliance Mode kiosk for an ad-free streaming experience.
- **Key Combos**: Backend now supports executing key combinations (e.g., Alt+F4, Alt+Left) securely.
- **Mobile UI Fixes**: Added proper padding for iOS devices with notches and gesture bars, ensuring the UI remains accessible.
- **Themes Modal**: Replaced simple skin buttons with a rich horizontal scrolling carousel showing previews for each theme.
- **New Buttons**: Added "Panel" (opens TV Status Panel), "OS Menu" (triggers the Linux app launcher), and "Close App" (Alt+F4).

### Changed
- **Catalog Update**: Added Stremio, Crunchyroll, and Apple TV+ to the default app list. Replaced Hulu.
- **Favicons**: Replaced Clearbit icon engine with Google's native favicon service to avoid ad-blocker domain restrictions.
- **Home Button Behavior**: The Home button now cleanly closes the active app instead of immediately relaunching the status panel in Appliance mode.

### Fixed
- **Status Freeze Bug**: Resolved "vundefined" issue and frozen polling data where the `/api/update/check` endpoint blocked non-authenticated local requests.
- **License View Fix**: Once a license is activated, the token entry fields are now securely hidden, showing only a green "Activa" badge.

## [1.2.1] - 2026-07-09

### Improved
- **Installer UX**: `lrp-setup` is now automatically invoked after `apt-get install` finishes via the web installer script.
- **Setup UX**: The interactive installer now simply asks "¿Esta PC está dedicada a la TV? [S/n]" rather than showing a numbered menu.
- **Idempotency**: Changing the mode of operation via `lrp-setup` will securely disable and teardown the systemd services of the previous mode.

## [1.2.0] - 2026-07-09

### Added
- **PIN Pairing**: Replaced manual token entry with an intuitive 6-digit TV PIN mechanism.
- **Bigscreen Integration**: Native app icon and desktop entry specifically targeted for KDE Plasma Bigscreen.
- **Auto-Launch Status Panel**: The panel now opens automatically on the TV at the end of the installation process.

### Fixed
- **License Status Bug**: Corrected a bug where the UI would report the license as active on a fresh install.
- **Installer User Binding**: Setup script now robustly identifies the active user (e.g. `tv`) instead of mistakenly binding permissions to `root`.
- **UFW Robustness**: UFW is only forcibly enabled in Appliance mode, and guarantees SSH access (port 22) is kept open to avoid customer lockouts.

## [1.0.0] - 2026-07-04

### Added
- **Licensing System**: Secure client-side activation and status endpoints (`/api/license/activate` and `/api/license/status`).
- **Supabase Integration v2**: Database schema migration for licensing tracking, active plans, Stripe customer mapping, and transactional records.
- **Supabase Edge Functions**: Added `validate-license` and `stripe-webhook` serverless handlers.
- **Offline Grace Cache**: Cache system permitting voice commands for up to 72 hours if the central licensing API is unreachable.
- **One-Command Bootstrapper**: Added `scripts/bootstrap.sh` script for rapid single-command installation.
- **Detached Auto-Updater**: Implemented client-triggered self-updating process through `scripts/update.sh` detached daemon launch.
- **System Uninstaller**: Added `scripts/uninstall.sh` to fully revert installation steps, directories, services, and configs.
- **Marketing Landing Page**: Completed beautiful, responsive Stripe-integrated index page (`website/index.html` and `website/gracias.html`) ready for Vercel.
- **Share/Web Share API**: Native sheet recommendation triggers with fallback copying options.
