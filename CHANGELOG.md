# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
