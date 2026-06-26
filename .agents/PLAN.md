# LinuxRemotePlayer — Development Plan

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
- [x] Integrate virtual mouse pointer + keyboard text entry via WebSocket
- [x] Redesign layout with media apps row, touchpad area, mic button, D-pad + OK, and keyboard bridge

## ⬜ REMAINING

# PH9: PAIRING UX & LICENSING BACKEND
- [ ] Backend endpoint to issue/persist a device token
- [ ] /pair page that renders a QR encoding https://<ip>:<port>/?token=<token>
- [ ] Apply supabase_schema.sql to the project; add RLS policies
- [ ] First-run onboarding in PWA (no token -> show pairing prompt instead of 'guest')

# PH10: MONETIZATION (Stripe)
- [ ] Stripe checkout ($4.99 lifetime)
- [ ] Supabase Edge Function / webhook -> issue license token on successful payment
- [ ] Bind purchased token to licenses table

# PH11: FEATURE COMPLETENESS & POLISH
- [ ] Gamepad UI in PWA (A/B/X/Y, Start/Select) — backend already supports the codes
- [ ] Smarter voice->app mapping (multi-word targets, not just {name}.com)
- [ ] Discovery: filter by category (AudioVideo / Network / Game)
- [ ] Appliance autologin auto-detect (SDDM / LightDM injection)
- [ ] Add backend/certs/ to .gitignore
- [ ] Tests (pytest) + on-hardware evdev injection test

## NOTES / MANUAL ACTIONS
- HTTPS is automatic: run.py self-generates and self-heals the cert. The only manual
  step is each phone accepting the self-signed cert once (browser warning -> proceed).
  To remove that warning entirely you need a trusted cert (PH-future, Plex-style).
- Set PAIRING_TOKEN in backend/.env, else control endpoints are open in dev mode.
- Create the 'licenses' table in Supabase (backend/supabase_schema.sql) + set SUPABASE_URL/KEY.
- Verify the real NVIDIA NIM ASR model id (NVIDIA_ASR_MODEL); current default is unverified.
