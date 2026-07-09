# PLAN v1.2 — PIN pairing, license-status bug, lrp-setup user bug, Bigscreen integration (machine-optimized)

```yaml
document_type: implementation_plan
audience: AI coding agent (Gemini) — execute autonomously
baseline: v1.1.3 (deployed and field-tested on KDE Neon Plasma Bigscreen)
field_evidence:
  - log_instalacion_2 (repo root) — READ IT before coding. Key lines:
      L103: "[i] Added 'root' to 'input' group"  -> lrp-setup lost $SUDO_USER (bug F3)
      L117: pairing token "E6GGFXKtFflOkjK9ggyUnQ" -> contains F/f/l/O ambiguity; owner
            failed manual entry 3 times on the phone (motivates F1)
  - Owner field report:
      F1: QR opens the link, browser gets the token, PWA installs — but the INSTALLED app
          starts clean and demands a token. ROOT CAUSE (do not fight it, design around it):
          on iOS, home-screen web apps have STORAGE ISOLATED from Safari. localStorage/
          IndexedDB written in the browser NEVER reaches the installed PWA. The ?token=
          mechanism is structurally incapable of pairing an installed iOS PWA.
      F2: status panel shows "Licencia activa" on a fresh install with NO license ever
          activated — false positive, must be diagnosed and fixed.
      F3: see L103 — everything (input group, chown, likely systemd User=) was configured
          for root instead of the real user 'tv'.
      F4: no desktop shortcut appeared in KDE Plasma Bigscreen; panel never auto-opened
          after install; APPLIANCE_IDLE_PANEL wiring not evident in lrp-setup output.
orchestration_contract:
  - Self-audit first: read scripts/build_deb.sh (postinst heredocs: lrp-setup, lrp-update),
    scripts/install.sh, backend/main.py (/api/status, license endpoints, pairing endpoints),
    frontend/app.js (pairing screen), frontend/status.html. Map every item to exact lines.
    If a diagnosis conflicts with the code, trust the code and document it.
  - After each phase: python3 -m py_compile backend/*.py && node --check frontend/app.js
    && bash -n scripts/*.sh website/install.sh
  - End: independent review pass (subagent) over the full diff, then final report
    {id, estado, archivos, desviaciones, acciones-del-dueño}.
  - Keep: vanilla JS, no build step, Spanish UI, existing auth/whitelist gates.
  - Version: bump VERSION to 1.2.0 + CHANGELOG entry (packaging/publish is P6).
severity_scale: [CRITICAL, HIGH, MEDIUM, LOW]
```

---

## P1 — PIN PAIRING (CRITICAL — replaces manual token as the primary mechanic)

### P1-1 Backend: PIN manager + exchange endpoint
```yaml
files: [backend/main.py (or new backend/pairing.py)]
design: >
  The TV displays a short-lived 6-digit PIN on the status panel. The phone (inside the
  installed PWA, its own storage context) types the PIN. The backend exchanges PIN -> the
  real pairing token. This crosses the iOS storage boundary because the SECRET travels
  through the USER (6 digits), not through browser storage.
fix_spec:
  - PIN state (module-level): {pin: str|None, expires_at: float, failed_attempts: per-IP dict}.
  - generate_pin(): 6 random digits via secrets.randbelow(10) x6, TTL 120s, SINGLE-USE
    (invalidate on successful exchange). Regenerated lazily when expired/consumed.
  - GET /api/pairing-pin  [require_local ONLY]: returns current valid PIN (generating if
    needed) + remaining seconds: {"pin":"483921","expires_in":94}. Local-only because the
    status panel (rendered on the TV itself) is its only consumer.
  - POST /api/pair  [LAN-accessible, NO auth]: body {"pin":"483921"}.
      * brute-force guard: per-IP max 5 failed attempts / 60s -> 60s lockout for that IP;
        global cap 20 failed/min -> invalidate current PIN and regenerate.
      * compare with hmac.compare_digest.
      * success -> {"token": <PAIRING_TOKEN>} and consume the PIN.
      * failure -> 401 {"detail":"PIN incorrecto"}; expired/none -> 410
        {"detail":"PIN expirado — mira la TV"}; locked -> 429.
  - 6 digits + 120s TTL + 5/min/IP -> worst-case online guessing ≈ 0.001% per window;
    acceptable for a LAN pairing secret; document in a code comment.
acceptance:
  - Local curl /api/pairing-pin returns a pin; POST /api/pair with it returns the token;
    reusing the same pin -> 410; 6 rapid wrong attempts -> 429 lockout.
```

### P1-2 Frontend: PIN-first pairing screen (PWA)
```yaml
files: [frontend/app.js, frontend/index.html]
fix_spec:
  - Rework #pairing-prompt-ui: headline "Conecta con tu TV", subline "Escribe el PIN de 6
    dígitos que aparece en la pantalla de tu TV", ONE large input
    (inputmode="numeric" pattern="[0-9]*" maxlength="6", auto-submit at 6 digits, huge
    centered monospace). On submit -> POST /api/pair; success: store token via the existing
    localStorage + IndexedDB helpers, toast "¡Emparejado!", then the normal boot path
    (fetchConfig -> connect -> fetchApps; reuse saveOnboardingToken plumbing INCLUDING
    pending_license handling).
  - Errors: 401 -> clear input + "PIN incorrecto, revisa la TV"; 410 -> "El PIN expiró, en
    la TV aparecerá uno nuevo"; 429 -> "Demasiados intentos, espera un minuto"; network ->
    existing trouble-banner logic.
  - Manual token entry becomes a COLLAPSED fallback: link "¿Problemas? Usar código manual"
    toggles the old token input (functionality kept, hidden by default).
  - Helper line: "¿No ves el PIN? Abre el Panel de LinuxRemotePlayer en tu TV".
  - Keep the ?token= URL flow working (still valid for Android/desktop browsers).
acceptance: fresh PWA (cleared storage) pairs end-to-end typing only the 6 digits shown on
  the TV; wrong/expired/locked PIN show their distinct messages.
```

### P1-3 Status panel: display the PIN
```yaml
files: [frontend/status.html]
fix_spec:
  - New PRIMARY block above the QR: "PIN de emparejamiento" + the 6 digits ENORMOUS
    (couch-readable, ~10vw monospace, grouped "483 921") + countdown of remaining seconds;
    poll /api/pairing-pin every 5s and refresh when it rotates.
  - QR stays as secondary ("o escanea para abrir la app en tu teléfono") — the QR is still
    the best path to REACH the install page; the PIN authorizes the installed app.
acceptance: panel shows live PIN + countdown; rotates visibly on expiry/consumption.
```

---

## P2 — FALSE "LICENCIA ACTIVA" ON FRESH INSTALL (HIGH)

```yaml
id: P2
files: [backend/main.py (/api/status), frontend/status.html, backend/auth.py if needed]
symptom: fresh install, LICENSE_TOKEN never set, status panel says license ACTIVE.
diagnosis_required: >
  Find the real defect — candidates (verify in code): /api/status computing "licensed"
  from the wrong source (bool of a default, voice_enabled, inverted truthiness);
  status.html rendering "Activa" when the JSON field is falsy/undefined (wrong key name,
  inverted ternary); or is_license_valid_cached_or_online returning True on an empty token
  via a stale .license_cache branch.
fix_spec:
  - /api/status "licensed" MUST equal is_license_valid_cached_or_online(os.getenv(
    "LICENSE_TOKEN","")) run in a thread; verify auth.py short-circuits empty token -> False.
  - status.html renders three explicit states: "Sin licencia" (gray), "Activa (<plan>)"
    (green), "Error al verificar" (amber on exception) — NEVER defaults to active.
acceptance: fresh install (no LICENSE_TOKEN) -> panel shows "Sin licencia" and
  curl /api/status shows "licensed": false; after real activation -> "Activa".
```

---

## P3 — lrp-setup CONFIGURES root INSTEAD OF THE REAL USER (CRITICAL)

```yaml
id: P3
files: [scripts/build_deb.sh (lrp-setup heredoc), scripts/install.sh (shared logic)]
evidence: log_instalacion_2 L103 "[i] Added 'root' to 'input' group" — executed via
  `sudo lrp-setup` by user 'tv', so $SUDO_USER was lost in the heredoc/nesting chain.
consequences_if_unfixed: service runs as root (bad security), token/venv owned by root,
  desktop entry installed for the wrong user, group change useless for 'tv'.
fix_spec:
  - lrp-setup resolves TARGET_USER robustly, in order:
      1. $SUDO_USER if set and != "root"
      2. logname 2>/dev/null if != "root"
      3. owner of the active graphical session:
         loginctl list-sessions --no-legend | awk '$3!="root"{print $3; exit}'
      4. interactive prompt "¿Qué usuario usará la TV? [<detected>]" (respect /dev/tty fix)
      5. still root/empty -> ABORT with a clear red message. NEVER configure root.
  - Use TARGET_USER consistently: usermod -aG input, chown /opt/linuxremoteplayer,
    systemd unit User= (Appliance) / user-scope service (Desktop), .desktop entry,
    kbuildsycoca invocation (P4).
  - Echo before acting: "[i] Configurando para el usuario: <TARGET_USER>" (permanent field
    diagnostic), and print the REBOOT/re-login reminder in a loud block at the end.
  - CAREFUL with heredoc quoting in build_deb.sh: the lrp-setup body is nested inside
    postinst's heredoc — verify variable escaping survives both levels (this is exactly
    where $SUDO_USER got lost). Add `bash -n` of the GENERATED lrp-setup to build_deb.sh
    itself (extract from staging and lint during build).
acceptance: `curl | sudo bash` + `sudo lrp-setup` on a box logged in as 'tv' -> unit shows
  User=tv, `id tv` includes input, /opt owned by tv, log line names the user.
```

---

## P4 — POST-INSTALL WIRING: auto-launch panel + KDE Plasma Bigscreen entry (HIGH)

```yaml
id: P4
files: [scripts/build_deb.sh (lrp-setup + package staging), scripts/install.sh]
fix_spec:
  A) Launch the panel at the end of lrp-setup:
     - Poll https://127.0.0.1:8000/health (curl -k, max 15s) until the service is up.
     - Run AS TARGET_USER with display env (bash equivalent of gui_env: DISPLAY=:0,
       XDG_RUNTIME_DIR=/run/user/<uid>, XAUTHORITY probe ~/.Xauthority then
       /run/user/<uid>/gdm/Xauthority then /run/user/<uid>/xauth_*):
         sudo -u $TARGET_USER <env> xdg-open "https://127.0.0.1:8000/status"
         || sudo -u $TARGET_USER <env> chromium --app="https://127.0.0.1:8000/status"
     - No display detected -> print the /status URL + https://<hostname>.local:8000/status.
  B) Desktop entry visible in KDE Plasma Bigscreen:
     technical_context: >
       Plasma Bigscreen populates its launcher from standard freedesktop .desktop entries
       through KService's sycoca cache. To appear reliably: install a SYSTEM-WIDE entry
       (/usr/share/applications/), reference an icon installed in the hicolor theme (not a
       file path in $HOME), give it a media category, and refresh caches. Bigscreen runs on
       Wayland — prefer generic Exec that works on both.
     steps:
       - Package staging (build_deb.sh): ship the icon at
         pkg/usr/share/icons/hicolor/512x512/apps/linuxremoteplayer.png (copy of
         frontend/icon-512.png) and the entry at
         pkg/usr/share/applications/linuxremoteplayer-panel.desktop:
           [Desktop Entry]
           Type=Application
           Name=Remote Linux Player
           Comment=Panel de estado y emparejamiento
           Exec=sh -c 'chromium --app=https://127.0.0.1:8000/status || chromium-browser --app=https://127.0.0.1:8000/status'
           Icon=linuxremoteplayer
           Categories=AudioVideo;Video;Player;
           Terminal=false
       - postinst/lrp-setup: run `update-desktop-database /usr/share/applications || true`,
         `gtk-update-icon-cache /usr/share/icons/hicolor || true`, and refresh KDE's cache
         AS TARGET_USER: `sudo -u $TARGET_USER kbuildsycoca6 --noincremental 2>/dev/null ||
         sudo -u $TARGET_USER kbuildsycoca5 2>/dev/null || true`.
       - prerm: remove the .desktop + icon on uninstall.
  C) APPLIANCE_IDLE_PANEL wiring: verify lrp-setup (Appliance mode) writes
     Environment="APPLIANCE_IDLE_PANEL=true" into the unit — field log shows no evidence;
     if missing in the deb path, add it (install.sh already has it at ~L103).
acceptance: after lrp-setup on KDE Neon: panel opens automatically; "Remote Linux Player"
  appears in the Bigscreen launcher with its icon and opens the panel; Appliance unit
  contains APPLIANCE_IDLE_PANEL=true.
```

---

## P5 — INSTALLER ROBUSTNESS (MEDIUM — from the v1.1.3 review)

```yaml
id: P5
files: [scripts/build_deb.sh (postinst + lrp-setup), scripts/install.sh]
fix_spec:
  - UFW safety: BEFORE any `ufw --force enable`, run `ufw allow OpenSSH || ufw allow
    22/tcp` — enabling a firewall on a customer machine must never cut their SSH access.
    Only auto-enable UFW in Appliance mode; in Desktop mode just add the 8000 rule and
    print whether the firewall is active.
  - venv validation in lrp-setup (postinst uses `pip install || true`, so a broken venv can
    slip through silently): check `/opt/linuxremoteplayer/backend/.venv/bin/python -c
    "import fastapi, evdev, segno"` — on failure print a RED actionable block:
    "Dependencias incompletas. Ejecuta: sudo /opt/linuxremoteplayer/backend/.venv/bin/pip
    install -r /opt/linuxremoteplayer/backend/requirements.txt" and abort before
    configuring the service.
  - postinst: on pip failure write /opt/linuxremoteplayer/.deps_incomplete marker; lrp-setup
    checks/clears it as part of the validation above.
acceptance: simulating a pip failure yields the red message and no half-configured service;
  fresh install on a machine with active SSH keeps SSH reachable after UFW enable.
```

---

## P6 — BUILD & PUBLISH v1.2.0 (same WSL pipeline as v1.1.x)

```yaml
id: P6
steps:
  1. VERSION -> 1.2.0; CHANGELOG.md entry (PIN pairing, license-status fix, setup user fix,
     Bigscreen entry, installer hardening).
  2. Commit + push (release: v1.2.0).
  3. WSL build (NEVER from /mnt/*): wsl -e bash -c "cd ~ && rm -rf LinuxRemotePlayer &&
     git clone https://github.com/Gusitir/LinuxRemotePlayer.git && cd LinuxRemotePlayer &&
     chmod +x scripts/build_deb.sh && ./scripts/build_deb.sh"
  4. Validate: dpkg-deb --info + --contents (Version 1.2.0; includes usr/share/applications
     + hicolor icon; excludes .venv/certs/.env/.pairing_token/__pycache__).
  5. Copy .deb to website/downloads/, update website/latest.json (version, url, REAL sha256).
  6. Commit + push (release: publish v1.2.0 .deb).
  7. Post-deploy: curl -sI the deb URL -> 200; curl latest.json -> 1.2.0 + real hash;
     download and sha256sum-verify.
```

---

## P7 — VERIFICATION (owner runs on the HTPC after `sudo lrp-update` or fresh install)

```bash
curl -sk https://127.0.0.1:8000/api/config | grep '"version": "1.2.0"'
curl -sk https://127.0.0.1:8000/api/status               # licensed:false on fresh install (P2)
curl -sk https://127.0.0.1:8000/api/pairing-pin           # PIN JSON (local only)
curl -sk -X POST https://127.0.0.1:8000/api/pair -H 'Content-Type: application/json' -d '{"pin":"000000"}'   # 401
grep User= /etc/systemd/system/linuxremoteplayer.service  # User=tv (P3)
id tv | grep input                                        # (P3)
ls /usr/share/applications/ | grep linuxremoteplayer      # (P4)
# Manual: TV shows panel with giant PIN -> phone PWA (storage cleared) pairs with the PIN
# in <30s; Bigscreen launcher shows "Remote Linux Player" with icon; SSH still reachable.
```

## EXECUTION ORDER
P3, P1-1, P1-2, P1-3, P2, P4, P5, P6, P7.
(P3 first: every later test depends on a correctly-configured service user.)
```
