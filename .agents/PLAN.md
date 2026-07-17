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

## ⬜ REMAINING

# PH9: PAIRING UX & LICENSING BACKEND — DONE
- [x] Backend endpoint to issue/persist a device token
- [x] /pair page that renders a QR encoding https://<ip>:<port>/?token=<token>
- [x] Apply supabase_schema.sql to the project; add RLS policies
- [x] First-run onboarding in PWA (no token -> show pairing prompt instead of 'guest')

# PH10: MONETIZATION (Stripe)
- [ ] Stripe checkout ($4.99 lifetime)
- [ ] Supabase Edge Function / webhook -> issue license token on successful payment
- [ ] Bind purchased token to licenses table

# PH11: FEATURE COMPLETENESS & POLISH
- [x] Voice/AI optional (ENABLE_VOICE flag; /api/config; mic hidden + audio rejected when off) — remote works with NO AI setup
- [x] Kiosk launches with graphical-session env (DISPLAY/Wayland/XDG_RUNTIME_DIR) so Chromium opens from the systemd service
- [x] TESTING.md: install + on-TV test guide (no AI)
- [x] Discovery widened to Flatpak/Snap/local paths + Type/category filtering (hide Settings/System noise)
- [ ] On-hardware test pass on the real TV (evdev keyboard+mouse, kiosk launch, PWA install)
- [ ] Appliance autologin auto-detect (SDDM / LightDM) + enable-linger for the user service
- [ ] "TV navigation mode" toggle (re-enable arrows + OK for leanback apps that don't use a pointer)
- [ ] Develop the Settings sections (currently placeholders): share-control QR, app info, web link
- [ ] Smarter voice->app mapping (multi-word targets, not just {name}.com)
- [ ] Add backend/certs/ to .gitignore
- [ ] Tests (pytest) + on-hardware evdev injection test

# PH12: DISTRIBUTION
- [ ] Build a .deb (use fpm) with a postinst that runs the install.sh logic (venv, systemd, uinput, cert); declare deps (python3-venv, chromium, ufw, openssl)
- [ ] Install-from-web one-liner: host install.sh and run via `curl -fsSL <url> | bash`
- [ ] Landing page on Vercel (download .deb + install command + docs; LATER Stripe checkout)
- [ ] The phone client needs NO app store (PWA "add to home screen"); the .deb only installs the SERVER on the Linux HTPC
- [ ] Avoid Flatpak/Snap: their sandbox blocks uinput / systemd / launching browsers (bad fit for this app)

# PH13: CODE PROTECTION / ANTI-CLONE
- [ ] Make the GitHub repo PRIVATE; distribute the built artifact (.deb), not the source repo
- [ ] Replace LICENSE with a proprietary/commercial license (current one may be open/GPL — revisit before selling)
- [ ] Compile the Python backend (Nuitka -> binary, or PyInstaller) and ship the binary in the .deb instead of .py
- [ ] Minify/obfuscate frontend JS (deterrent only — PWA JS is always visible in the browser)
- [ ] NEVER ship API keys (NVIDIA/OpenRouter/Supabase service) in the client; route AI through a proxy server you control
- [ ] REAL protection is server-side: license activation against your server + AI/premium gated by license. Copying the client yields a useless shell without your cloud.
- [ ] Reality: client-side code can't be fully hidden; move the value (AI, premium, license) to your server.

# PH14: v1.6.0 — BUGS HTPC + BRAVE + HARDENING — ✅ RELEASED 2026-07-14
- [x] G-01..G-13 + correcciones C-01..C-10 + G-17/G-18 (auditadas por Claude)
- [x] G-14 Release v1.6.0 publicado y verificado en vivo (sha256 match, OTA operativo)
- [x] Smoke-test 7/7 funcional en HTPC limpio (Plasma Bigscreen)
- [ ] G-15/G-16 (siguen esperando info del dispositivo del dueño)

# PH14b: v1.7.0 — FIREFOX + FIXES — ✅ RELEASED 2026-07-14 (plan: .agents/archive/PLAN_GEMINI_v1.7.md)
- [x] F-01..F-06 + FC-01..FC-03 (auditadas por Claude, verificación independiente)
- [x] F-07 Release v1.7.0 publicado y verificado en vivo (sha256 4fff1722... match)

# PH14c: TESTING INTENSIVO v1.7.0 (plan: .agents/TESTING.md) — EN CURSO 2026-07-17
- [ ] Dueño ejecuta la matriz A-J (instalación, seguridad, input, kiosk, panel, PWA,
      licencia/voz, OTA, estrés, desinstalación) y registra FALLAS
- [ ] Claude tría las FALLAS -> tareas del plan v1.7.1/v1.8 -> Gemini corrige
- [ ] G-15/G-16 se resuelven con los ítems F1/F2 de la matriz (icono PWA + safe-area)
- [ ] (dueño) deploy send-feedback; Stripe LIVE; dominio + Resend

# PH15: V2.0 — APK ANDROID (aprobado en evaluación; ver PLAN_GEMINI_v1.6.md FASE E)
- [ ] Prerrequisitos: v1.6.0 estable + ai-proxy Edge Function (claves fuera del dispositivo)
- [ ] Capacitor wrapper + NSD/mDNS + RECORD_AUDIO + volumen físico + foreground service
- [ ] WSS con networkSecurityConfig (CA propia embebida) — NO ws:// plano

## NOTES / MANUAL ACTIONS
- HTTPS is automatic: run.py self-generates and self-heals the cert. The only manual
  step is each phone accepting the self-signed cert once (browser warning -> proceed).
  To remove that warning entirely you need a trusted cert (PH-future, Plex-style).
- Set PAIRING_TOKEN in backend/.env, else control endpoints are open in dev mode.
- Create the 'licenses' table in Supabase (backend/supabase_schema.sql) + set SUPABASE_URL/KEY.
- Verify the real NVIDIA NIM ASR model id (NVIDIA_ASR_MODEL); current default is unverified.
- Owner deferred Supabase + Stripe + AI; current focus is on-TV testing of the control without AI.
- Distribution model: PWA client (no store) + a SERVER package (.deb) for the Linux HTPC. See PH12.
- Anti-clone: legal (private repo + proprietary license) + compiled backend + server-side license/AI proxy. See PH13.
