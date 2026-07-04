# DIRECTORIES
- /backend/: FastAPI server, Python logic.
- /frontend/: PWA static files.
- /scripts/: Bash setup scripts.

# CRITICAL FILES
- /backend/main.py: FastAPI entrypoint. WS router (input keys / pointer move+click+scroll / text typing / media). REST: /api/apps, /api/kiosk/launch|kill, /api/app/launch, /api/config, /api/debug. Auth gate (verify_access) + static mount. VOICE_ENABLED gate on audio.
- /backend/run.py: launcher with automatic self-healing HTTPS (self-signed cert per current LAN IP).
- /backend/input_emulator.py: evdev UInput. VirtualGamepad (keys + free text typing via CHAR_KEYS) + VirtualMouse (move / click / scroll).
- /backend/kiosk.py: Chromium-only kiosk launcher + gui_env() (DISPLAY / WAYLAND_DISPLAY / XDG_RUNTIME_DIR so it opens from a systemd service).
- /backend/discovery.py: .desktop scanner (usr/local + flatpak + snap paths; filters NoDisplay/Hidden + Settings/System categories).
- /backend/ai_pipeline.py: STT + LLM (cloud NVIDIA/OpenRouter or local Whisper/Ollama). Used only when ENABLE_VOICE=true.
- /backend/auth.py: verify_access (PAIRING_TOKEN / Supabase) + validate_license_and_increment (daily rate-limit).
- /backend/supabase_schema.sql: 'licenses' table schema (token, commands_today, last_reset).
- /backend/.env.example: ENABLE_VOICE (default false), PAIRING_TOKEN, SUPABASE_*, NVIDIA_ASR_MODEL, USE_LOCAL_AI, local URLs.
- /scripts/install.sh: deps + uinput perms + Chromium install + systemd service (Appliance/Desktop).
- /scripts/gen_cert.sh: manual self-signed cert generator (run.py does this automatically).
- /frontend/index.html: PWA UI — remote (apps row, touchpad+scroll, mic, transport/home/back/volume), app drawer, settings drawer, install tutorial.
- /frontend/app.js: WS client, touchpad/scroll/keyboard bridge, app + custom-app + drawer logic, install/desktop detection, toast.
- /frontend/sw.js: service worker (cache lrp-v10).
- /frontend/manifest.json + icon.svg: PWA manifest + icon.

# WS MESSAGE PROTOCOL (frontend -> backend)
- {"type":"input","device":"gamepad","action":"press","key":"KEY_*"}  -> key press
- {"type":"pointer","dx":N,"dy":N}                                      -> mouse move
- {"type":"pointer","click":"left"|"right"}                            -> mouse click
- {"type":"pointer","scroll":N}                                        -> mouse wheel
- {"type":"text","text":"..."}                                         -> type text
- {"action":"media_control","parameters":{"key":"KEY_*"}}              -> media key
- binary audio frame                                                  -> STT/LLM (only if ENABLE_VOICE)

# DISTRIBUTION (planned, PH12)
- Client = PWA (no app store). Server = .deb (fpm) for the Linux HTPC. Landing on Vercel.

# CODE PROTECTION (planned, PH13)
- Private repo + proprietary license + compiled backend (Nuitka) + server-side license/AI proxy.
- Never ship API keys in the client.
