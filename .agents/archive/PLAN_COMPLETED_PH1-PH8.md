# PLAN — fases COMPLETADAS (archivado 2026-07-30)

<!-- PH1..PH8.8: scaffold, kiosk, IA cloud, installer, auditoria de seguridad, HTTPS+PWA,
     rediseño de la UI y remediacion. Todo entregado antes de la v1.8.
     Se archiva porque PLAN.md lo marcaba 'DONE - saltar' y nadie lo leia: era peso muerto
     en un archivo que cargan los agentes. El roadmap vivo esta en .agents/PLAN.md. -->

## ✅ COMPLETED

# PH1: SCAFFOLD & CORE (FastAPI + evdev) — DONE
- [x] FastAPI app, WebSocket router, static file serving
- [x] evdev/UInput virtual keyboard-gamepad (input_emulator.py)

# PH2: KIOSK & DISCOVERY — DONE
- [x] .desktop app discovery (discovery.py)
- [x] Kiosk launcher with multi-browser fallback (kiosk.py)

# PH3: CLOUD AI — DONE
- [x] STT (NVIDIA NIM) + LLM intent parsing (OpenRouter)

# PH4: INSTALLER & DEPLOY — DONE
- [x] install.sh (Appliance vs Desktop)
- [x] systemd service configs

# PH5: LOCAL AI & NETWORK CONFIG — DONE
- [x] Local Ollama + Whisper fallback
- [x] Bind 0.0.0.0, serve PWA at /
- [x] Keyboard keys mapped to virtual device

# PH6: BUGFIXING & TESTING — DONE
- [x] /dev/uinput permissions fixed in installer (modprobe + udev rule + input group)

# PH7: SECURITY AUDIT REMEDIATION — DONE
- [x] Auth gate on WebSocket + kiosk/app REST endpoints (PAIRING_TOKEN / Supabase)
- [x] CORS credentials disabled (stop reflecting any origin)
- [x] media_control wired to evdev (volume up/down, mute, play-pause)
- [x] Daily reset for rate-limit counter (last_reset column)
- [x] LLM target_id sanitization + URL encoding
- [x] Audio payload size guard (5 MB)
- [x] requirements.txt pinned

# PH8: HTTPS + PWA — DONE (current iteration)
- [x] backend/run.py: automatic self-healing HTTPS (self-signed cert auto-generated +
      regenerated when the LAN IP changes) — mic works out-of-the-box, zero manual steps
- [x] scripts/gen_cert.sh: manual cert generator (fallback; run.py does this automatically)
- [x] Insecure-context banner: guides phones from http:// to the https:// URL (accept once)
- [x] Installer is non-interactive for HTTPS (no prompt)
- [x] manifest.json + sw.js + icon.svg: installable PWA shell
- [x] 'search' voice intent handler
- [x] ?token= URL pairing (enables link/QR onboarding)
- [x] backend/supabase_schema.sql
- [x] Browser-vs-app detection: install tutorial with iOS/Android SVG diagrams when not installed
- [x] No-zoom hardening (double-tap + pinch) + chromeless standalone meta tags
- [x] Kiosk uses Chromium only (Brave/Firefox dropped); installer auto-detects/installs Chromium

# PH8.5: REMOTE UI REDESIGN — DONE
- [x] Virtual mouse pointer (touchpad: move, tap=left-click, long-press=right-click) + scroll strip
- [x] Free SVG icons (Lucide-style) on all control buttons; app tiles use site favicons (letter fallback)
- [x] Transport uses ordinary keys (Space / Left / Right) so it hits the FOREGROUND kiosk, not the system media session; volume/mute stay as global media keys
- [x] D-pad removed (touchpad replaces it); media transport occupies that space
- [x] System keyboard bridge with Done + Enter/Search; backspace (delete) button
- [x] App drawer (slide-up): suggested + custom web apps (+ add) + detected system apps (.desktop) pinnable to the menu
- [x] Settings drawer (placeholders only): general, app info, web link, share-control QR (local IP), buy premium, skins (premium)
- [x] Browser-vs-installed-app detection fixed (style.display, not the hidden attr that Tailwind flex/grid overrides); desktop browsers show the remote directly for testing
- [x] Toast feedback on launch; safe-area (notch) padding

# PH8.8: AUDIT & REMEDIATION PLAN — DONE
- [x] Stable mDNS hostname resolution (avahi-daemon) + DNS certificate SANs
- [x] Two-tier certificate authority (ca.pem + leaf certs) preventing trust breakage
- [x] Reconnection exponential backoff, WS heartbeat liveness, and offline tailwind-lite.css
- [x] Resilient IndexedDB + LocalStorage pairing token storage & settings entry UI
- [x] Late/lazy initialization of uinput devices to handle installation startup races
- [x] Security: auto-generated pairing token, Same-Origin CORS, and whitelist for evdev keys
- [x] DOM-based XSS protection for dynamic UI tiles & whitelist for voice intent domains
- [x] Atomic rate-limiting via Supabase RPC functions
- [x] Correctness: X11/Xauthority kiosk launch, standard python logging, and IME input diffing
- [x] Round 2 post-implementation review fixes: bootstrap mobile detection, delete custom apps, and toast alerts

