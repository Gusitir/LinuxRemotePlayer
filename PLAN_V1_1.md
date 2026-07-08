# PLAN v1.1 — Field-test fixes, Status Panel, Skins Premium, .deb packaging (machine-optimized)

```yaml
document_type: implementation_plan
audience: AI coding agent (Gemini) — execute autonomously
source: real-hardware field test by the owner (HTPC + iPhone Safari PWA), 2026-07-07
baseline: main @ e5f0411 (v1.0.0) — all prior plans completed; do NOT redo them
orchestration_contract:
  - BEFORE coding: run a self-audit pass — read backend/main.py, backend/input_emulator.py,
    backend/kiosk.py, frontend/app.js, frontend/index.html end-to-end and map each finding
    below to the exact lines you will touch. If a diagnosis below conflicts with what you
    find in code, TRUST THE CODE and document the discrepancy in your report.
  - AFTER each phase: run `python3 -m py_compile backend/*.py && node --check frontend/app.js`
    plus the phase's acceptance checks. At the END: spawn/perform an independent code-review
    pass (subagent if available) over the full diff before writing the final report.
  - IMAGE GENERATION REQUIRED in P6 (anime skin background) — see exact prompt constraints there.
  - Bump sw.js CACHE version once at the end (single bump).
  - Keep: vanilla JS, no build step, Spanish UI, existing security gates (whitelists, auth).
severity_scale: [CRITICAL, HIGH, MEDIUM, LOW]
```

---

## PHASE P1 — INPUT BUGS (CRITICAL — the product's core)

### P1-1 Touchpad completely dead
```yaml
id: P1-1
severity: CRITICAL
files: [backend/main.py, backend/input_emulator.py]
diagnosis (verify in code first):
  A) PRIME SUSPECT — the WS TokenBucket (main.py ~line 195, rate=60/s, capacity=120)
     throttles ALL text messages. The touchpad streams pointer deltas at requestAnimationFrame
     rate (60–120 msg/s on modern phones) PLUS pings PLUS key presses. The bucket drains and
     pointer messages are silently dropped (log line "WS message dropped due to rate limit").
     On a 120Hz phone the touchpad loses >50% of frames or starves entirely.
  B) SECONDARY — /api/debug only reports gamepad.ui; VirtualMouse.ui could be None
     (silent failure) and nobody would know.
fix_spec:
  - Rate limiting redesign: pointer + ping messages are lightweight and MUST NOT starve.
    Implement two buckets: fast_bucket (rate=240, cap=480) consumed by msg_type in
    {"pointer","ping"}; slow_bucket (rate=30, cap=60) for everything else. Drop silently
    only from fast_bucket; keep warning log for slow_bucket.
  - /api/debug: add "mouse_ui_created": input_emulator.mouse.ui is not None, and
    "dropped_msgs_last_min" counters for both buckets (simple counters on the WS handler).
  - input_emulator: on VirtualMouse init failure, logger.error (not warning) with the
    exception text — this must be loud in journalctl.
acceptance:
  - Sustained pointer stream at 120 msg/s for 10s: zero drops, pointer moves on screen.
  - /api/debug shows both ui flags.
```

### P1-2 Certain keys don't work (volume/mute/media)
```yaml
id: P1-2
severity: CRITICAL
files: [backend/main.py, backend/input_emulator.py (new module function or backend/audio.py)]
diagnosis: >
  uinput media keys (KEY_VOLUMEUP/DOWN/MUTE/PLAYPAUSE) are just key events — SOMETHING on the
  desktop must handle them (a DE daemon). On a kiosk/appliance HTPC without a full desktop
  environment nobody listens, so volume/mute/playpause do nothing. Navigation keys work
  because Chromium itself handles them. This matches the field report exactly.
fix_spec:
  - New backend module audio.py with set_volume(delta_percent) and toggle_mute():
      try in order: `wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%+` (PipeWire),
      `pactl set-sink-volume @DEFAULT_SINK@ +5%` (PulseAudio),
      `amixer -q sset Master 5%+` (ALSA). First binary found via shutil.which wins.
      Mute: wpctl toggle / pactl toggle / amixer toggle. All via subprocess with gui_env().
  - main.py media_control handler: intercept KEY_VOLUMEUP/KEY_VOLUMEDOWN/KEY_MUTE ->
    audio.py functions (uinput fallback ONLY if no mixer binary found).
    KEY_PLAYPAUSE -> if a kiosk is tracked as running, send KEY_SPACE via uinput instead
    (Chromium/streaming sites universally bind space); else send KEY_PLAYPAUSE as before.
  - Log which audio backend was selected at startup.
acceptance: on a system with pipewire OR pulse OR alsa, volume +/- and mute work from the
  phone with no desktop environment running; play/pause works inside Netflix/YouTube kiosk.
```

---

## PHASE P2 — FUNCTIONAL REGRESSIONS & BEHAVIOR (HIGH)

### P2-1 Restore "add native app to favorites"
```yaml
id: P2-1
severity: HIGH
files: [frontend/app.js, frontend/index.html]
problem: native list rows only have "Abrir"; the old "+ Añadir" (pin to app grid) was lost.
fix_spec:
  - renderNativeList: each row gets TWO buttons (DOM-built, no innerHTML with data):
    "Abrir" (launch) and "+ Añadir" (pin). Pin saves into custom_apps as
    {id: 'native-'+nativeId, name, kind:'native', nativeId, color: palette rotation}.
  - createAppTile + handleAppLaunchClick: if app.kind==='native' -> POST /api/app/launch
    with nativeId instead of kiosk launch. Tile removable (custom_ OR native- prefix).
  - Duplicate pin -> toast "ya está en el menú".
acceptance: pin a native app -> tile appears in grid + drawer, launches it, can be deleted.
```

### P2-2 Home must close EVERYTHING (single-app HTPC model)
```yaml
id: P2-2
severity: HIGH
files: [backend/kiosk.py, backend/main.py]
problem: >
  /api/kiosk/kill only kills Chromium kiosks. Native apps launched from the remote stay
  running forever in the background — unreachable from the remote, wasting RAM on old PCs.
fix_spec:
  - kiosk.py: module list _native_procs. main.py /api/app/launch appends its Popen there
    (it already uses start_new_session=True -> each is a process-group leader).
  - New kiosk.py function close_all(): kills the tracked kiosk (existing logic) AND iterates
    _native_procs -> os.killpg(SIGTERM), 3s grace, SIGKILL; prune dead entries.
  - /api/kiosk/kill calls close_all(). (Home button = "close everything, back to idle".)
  - Do NOT add pkill patterns for native apps (too dangerous); tracked-only is correct.
acceptance: launch Kodi/native app + a kiosk from the phone, press Home once -> both gone,
  `ps` shows no leftovers from tracked launches.
```

### P2-3 App icons (native + streaming)
```yaml
id: P2-3
severity: MEDIUM
files: [backend/main.py or backend/icons.py (new), backend/discovery.py, frontend/app.js]
fix_spec:
  - New endpoint GET /api/icon/{app_id} (auth): resolve the .desktop Icon value:
    if absolute path and exists -> serve; else search, in order:
    /usr/share/icons/hicolor/{256x256,128x128,512x512,64x64,48x48}/apps/{icon}.{png,svg},
    /usr/share/pixmaps/{icon}.{png,svg}, flatpak exports share/icons (same pattern).
    Cache resolution in a dict. 404 if not found. Correct media type per extension.
  - frontend tiles: native tiles -> <img src=`${apiUrl}/icon/${nativeId}`> layered over the
    letter (letter stays as fallback via img.onerror -> img.remove()). NOTE: <img> can't send
    the X-Auth-Token header — so EXEMPT /api/icon from auth OR accept ?token= query param on
    this endpoint only (icons are not sensitive; exempting is acceptable — document choice).
  - Streaming kiosk tiles: restore favicon overlay
    `https://www.google.com/s2/favicons?sz=64&domain={hostname}` with onerror fallback to
    the colored letter (this is how it worked pre-rewrite).
acceptance: Firefox/Kodi tiles show their real icons; Netflix tile shows the N favicon;
  no broken-image squares when offline (fallback letter visible).
```

---

## PHASE P3 — MOBILE UI & BRANDING (HIGH)

### P3-1 Status-bar overlap / bottom buttons pushed off-screen (PWA)
```yaml
id: P3-1
severity: HIGH
files: [frontend/index.html]
diagnosis: >
  Two stacked problems: (1) apple-mobile-web-app-status-bar-style=black-translucent makes
  iOS draw the clock OVER the app; padding-top:env(safe-area-inset-top) on body then pushes
  content but (2) body uses h-screen (100vh) which on mobile Safari includes the URL-bar
  area -> total height exceeds the visual viewport and the bottom control panel drifts off.
fix_spec:
  - <meta name="apple-mobile-web-app-status-bar-style" content="black"> (opaque bar, own space,
    zero overlap — simplest robust fix).
  - body: replace h-screen with style height:100dvh (dynamic viewport height) with 100vh
    fallback: `height:100vh; height:100dvh;` in the <style> block; keep flex column.
  - Keep padding-top:env(safe-area-inset-top) (harmless with opaque bar) and existing
    bottom safe-area padding on the control panel.
  - Verify #app-ui uses min-h-0 + flex-1 so the touchpad flexes, not the buttons.
acceptance: in standalone mode on a notched phone: settings gear fully visible/tappable,
  volume buttons fully visible above the home indicator, no scrolling of the shell.
```

### P3-2 Rename "Remote Kiosk" -> "Remote Linux Player"
```yaml
id: P3-2
severity: MEDIUM
files: [frontend/manifest.json, frontend/index.html, frontend/app.js, frontend/pair.html,
        supabase/functions/stripe-webhook/index.ts, website/*.html, README.md, TESTING.md]
fix_spec:
  - manifest: "name":"Remote Linux Player", "short_name":"RemoteLinux" (<=12 chars for launcher).
  - index.html: <title>, apple-mobile-web-app-title, header label, install screens copy.
  - Email template in stripe-webhook: "Abre la aplicación Remote Linux Player…" -> NOTE in the
    final report that the owner must redeploy: `supabase functions deploy stripe-webhook --no-verify-jwt`.
  - Website gracias.html activation card + any "Remote Kiosk" mention repo-wide (grep).
  - WARNING to include in report: manifest name/icon changes only apply to NEW installs —
    the owner must remove + re-add the PWA once on each phone.
acceptance: grep -ri "remote kiosk" over repo returns 0 hits (excluding docs/archive/).
```

### P3-3 One icon everywhere (the website one)
```yaml
id: P3-3
severity: MEDIUM
files: [frontend/icon-192.png, frontend/icon-512.png, frontend/index.html, frontend/manifest.json,
        website/index.html, website/gracias.html]
problem: owner reports the installed PWA shows NO icon on the phone; wants the website icon as
  the single brand icon everywhere.
fix_spec:
  - website/icon-512.png is the master. Regenerate from it: frontend/icon-192.png,
    frontend/icon-512.png, frontend/apple-touch-icon.png (180x180, NO transparency — iOS
    renders transparent as black; composite over the theme bg color #111827),
    website/favicon-32.png.
  - index.html: <link rel="apple-touch-icon" sizes="180x180" href="apple-touch-icon.png">
    (iOS ignores manifest icons; this tag is what fixes the "no icon" report).
  - manifest icons: 192 + 512 (purpose any) + 512 maskable entry.
  - Add all icon files to sw.js ASSETS.
acceptance: fresh PWA install on iOS shows the brand icon (not a screenshot/letter tile).
```

---

## PHASE P4 — STATUS PANEL ON THE PC ("like Unified Remote") (HIGH)

```yaml
id: P4
severity: HIGH
files: [frontend/status.html (new — evolve/replace pair.html), backend/main.py, scripts/install.sh]
design_decision: >
  Web-based panel served by the backend itself (NO Qt/GTK — zero new system deps, works on
  every distro, reuses the design system). It doubles as the TV's IDLE SCREEN in appliance
  mode: when no kiosk is running, the TV shows the panel with the pairing QR — this ALSO
  solves the pairing-friction complaint (P10 of the field report): the user just points the
  camera at the TV.
fix_spec:
  - GET /status (require_local, like /api/pairing-qr): dark cinematic page (reuse pair.html
    styles) showing live via polling /api/status every 2s:
      * connection state: number of connected phone clients (track a counter in the WS
        handler: +1 on successful auth, -1 on disconnect) and last-input timestamp
      * latency: measured client-side by the panel against /health (fetch timing)
      * system status: uinput keyboard/mouse OK (from /api/debug fields), audio backend,
        voice enabled, license status (licensed/plan), version + update available
      * pairing QR (existing /api/pairing-qr) + the .local URL in text
      * buy link button (buy_url from /api/config) + support email
  - New GET /api/status (require_local): JSON aggregating the above server-side facts.
  - install.sh Desktop mode: install a .desktop launcher
    (~/.local/share/applications/linuxremoteplayer-panel.desktop) that opens
    `chromium --app=https://127.0.0.1:8000/status` — the "server app" experience.
  - Appliance idle screen: in kiosk.py close_all()/kill success path, if APPLIANCE_IDLE_PANEL
    env is true (default false; installer sets true in Appliance mode .service Environment=),
    relaunch chromium kiosk on https://127.0.0.1:8000/status. Pressing Home therefore returns
    the TV to the status/QR screen instead of a bare desktop.
acceptance: opening /status on the HTPC shows QR + live client count + latency; from a
  non-local IP it returns 403; in appliance mode, Home returns the TV to the panel.
```

### P4-B Auto-launch the panel when no remote is connected (owner request)
```yaml
id: P4-B
severity: HIGH
files: [backend/main.py, backend/kiosk.py]
goal: >
  If the phone cannot connect (e.g. the HTPC IP changed), the TV must AUTOMATICALLY show the
  status panel with the pairing QR — the user just scans it and is reconnected. Zero terminal.
fix_spec:
  - main.py: background asyncio task (started on startup via lifespan/startup event), tick
    every 15s. Launch the panel when ALL of:
      * connected_clients == 0 continuously for >= 45s (debounce — track the timestamp of the
        last disconnect / last failed period; avoids flashing the panel during brief phone
        sleep/reconnect cycles)
      * no tracked kiosk running AND no tracked native app running (NEVER interrupt playing
        media just because the phone dropped)
      * the panel is not already the active kiosk (track a flag/marker when launching it,
        e.g. remember the launched URL)
      * AUTO_STATUS_PANEL env is true — installer sets true for Appliance mode; default false
        in Desktop mode (popping a fullscreen window on someone's desktop is intrusive;
        document that desktop users can enable it in .env)
  - Launch via the existing kiosk launcher: launch_kiosk("https://127.0.0.1:8000/status")
    but WITHOUT counting it as user media (Home/idle logic must treat panel-kiosk as idle).
  - When a phone client authenticates while the panel is open: keep the panel (it is the idle
    screen); it gets replaced naturally when the user launches an app.
  - The QR endpoint already resolves the CURRENT LAN IP per request — verify it is not cached.
acceptance: with the service running and no client connected for ~1 min, the TV shows the
  panel by itself; while Netflix kiosk is playing, disconnecting the phone does NOT interrupt
  playback; scanning the QR pairs and the remote works.
```

### P4-C Self-heal on IP change (completes the QR story)
```yaml
id: P4-C
severity: HIGH
files: [backend/run.py]
problem: >
  run.py monitor_ip() currently only LOGS a warning on IP change. The TLS leaf cert keeps the
  OLD IP in its SAN, so a phone scanning the new QR would hit a cert mismatch. Without this
  fix, P4-B's "scan and it works" promise breaks exactly in the IP-change scenario it was
  built for.
fix_spec:
  - monitor_ip(): on detected change (stable for 2 consecutive checks to avoid DHCP flapping):
    log clearly, then exit the process with os._exit(3). systemd (Restart=always, RestartSec=5)
    brings it back up; startup regenerates the leaf cert for the new IP + rebinds; P4-B then
    auto-shows the panel with a QR pointing at the new IP. Full loop with zero human steps on
    the HTPC.
  - Guard: only self-restart when running under systemd (env INVOCATION_ID present) — when run
    manually (python run.py) keep today's warning-only behavior so debugging sessions don't
    self-kill.
acceptance: change the HTPC IP (or simulate: reassign DHCP lease) -> within ~2 min the service
  restarts itself, serves a cert valid for the new IP, TV shows the panel, scanning the QR
  from the phone connects without any certificate error beyond the usual first-accept.
```

---

### P3-4 Silent fast-resume on screen wake (owner report)
```yaml
id: P3-4
severity: MEDIUM
files: [frontend/app.js]
problem: >
  Phones kill the WebSocket when the screen turns off (OS behavior — cannot be prevented).
  On wake, the app flashes red "Reconnecting..." for ~2s before recovering. Functionally fine,
  but feels broken to the user every single time they wake the phone.
fix_spec:
  - Reconnect-on-wake already exists (visibilitychange -> connect()). Improve PERCEIVED UX:
    on visibilitychange->visible with a dead socket, set status to a neutral gray
    "Conectando…" (not red) and attempt an IMMEDIATE reconnect (reset connectAttempts=0 and
    skip any pending backoff timer so wake never waits on a previous backoff).
  - Only show the red "Reconectando..." state if the wake reconnect has not succeeded within
    3s (timer set on wake, cleared in onopen). Success within 3s -> straight to green
    "Connected" with no red flash.
  - Do NOT show the troubleshooting banner for wake-induced retries (reset its counter on
    successful wake reconnect, as today).
  - P4-B interaction (verify, no code change expected): screen-off disconnects put
    connected_clients at 0 — the 45s idle debounce plus the "never over running media" rule
    already prevent the TV panel from popping during normal phone sleep. Add a unit note in
    the report confirming this path was reviewed.
acceptance: waking the phone shows green "Connected" in under ~1s on LAN with no red flash;
  TV panel does not appear when the phone screen is off for short periods while media plays.
```

## PHASE P5 — INSTALLER: interactive prompt dies under `curl | sudo bash` (CRITICAL)

```yaml
id: P5
severity: CRITICAL
files: [scripts/install.sh, scripts/bootstrap.sh]
diagnosis: confirmed by owner — `read -p` consumes the PIPE (the script itself) as stdin, so
  the mode prompt aborts. Classic curl|bash pitfall.
fix_spec:
  - install.sh, before the mode prompt:
      if [ ! -t 0 ] && [ -e /dev/tty ]; then exec < /dev/tty; fi
    (rebinds stdin to the real terminal when piped).
  - Support non-interactive: env LRP_MODE=1|2 skips the prompt entirely (document in README).
  - bootstrap.sh: pass LRP_MODE through if set. Also `git fetch --all && git reset --hard
    origin/main` instead of bare `git pull` in the existing-dir path (avoids merge conflicts
    on re-runs / detached HEAD from update.sh tags).
acceptance: `curl -fsSL .../bootstrap.sh | sudo bash` reaches and answers the 1/2 prompt
  interactively on a clean VM; `curl ... | sudo LRP_MODE=2 bash` installs with no prompt.
```

---

## PHASE P6 — PREMIUM FEATURE: SKINS (license-gated) + IMAGE GENERATION

```yaml
id: P6
severity: MEDIUM
files: [frontend/index.html, frontend/app.js, frontend/skins.css (new),
        frontend/skins/anime-bg.webp (new — GENERATED IMAGE), frontend/sw.js]
architecture:
  - Convert the hardcoded gray palette to CSS custom properties on :root in a new skins.css:
    --bg-base, --bg-panel, --bg-btn, --bg-btn-active, --text-main, --text-dim, --accent,
    --accent-green, --touchpad-bg, --touchpad-dot, --bg-image (default: none).
    Replace color literals in index.html <style> AND tailwind-lite.css classes ONLY where the
    theme must change (keep utility classes; override via [data-skin] selectors — do not
    rewrite tailwind-lite).
  - <html data-skin="dark"> default. Skins:
      dark  = current look (no visual change — regression-free baseline)
      day   = light theme: bg #f1f5f9, panels #ffffff, text #0f172a, accent #2563eb —
              VERIFY 4.5:1 contrast on all text/buttons
      anime = cozy kawaii: bg-image url('skins/anime-bg.webp') cover + dark overlay
              rgba(11,18,32,0.55) behind controls so buttons stay legible; accent #ec4899;
              panels rgba(17,24,39,0.75) with backdrop-filter: blur(6px)
  - Ajustes row "Skins / Temas (Premium)": on tap -> if /api/license/status licensed ->
    picker with 3 preview swatches (DOM-built); else toast "Función premium — compra tu
    licencia" + open buy_url. Persist choice in localStorage ('skin'), apply on boot BEFORE
    first paint (inline script in <head> reading localStorage to avoid flash).
  - Free users are always forced to 'dark' on boot even if localStorage was tampered
    (cosmetic-only enforcement is acceptable; note it).
image_generation_task (MANDATORY — generate, do not stub):
  file: frontend/skins/anime-bg.webp
  spec: vertical phone wallpaper ~1080x2340, anime illustration style: cozy/kawaii scene —
    anime girl relaxing on a couch in a warm dim living room, TV glow, plants, plushies,
    night window. STRICTLY SFW and tasteful (fully clothed, wholesome mood — this ships in a
    commercial product). Composition: main subject in the UPPER third; lower two thirds
    low-detail/darker so touchpad and buttons remain readable. Muted palette that harmonizes
    with #0b1220 and pink accent #ec4899.
  constraints: convert/compress to webp <= 400KB. Add to sw.js ASSETS.
acceptance: switching skins is instant and persists across reloads; dark skin is pixel-
  equivalent to current UI; day skin passes contrast; anime bg loads offline (SW cached);
  unlicensed user cannot activate skins.
```

---

## PHASE P7 — .deb PACKAGING & PRIVATE DISTRIBUTION (code off public GitHub)

```yaml
id: P7
severity: HIGH
context: owner will make the GitHub repo PRIVATE and distribute a .deb from the website.
legal_prereq_for_report: >
  Remind the owner: relicense to Elastic License 2.0 BEFORE going private (he is sole author);
  the already-published AGPL snapshot remains AGPL for anyone who cloned it — closing applies
  forward only.
fix_spec:
  - scripts/build_deb.sh (new, runs on any Debian/Ubuntu with dpkg-deb):
      staging: pkg/opt/linuxremoteplayer/{backend,frontend,scripts,VERSION}
               (EXCLUDE: .venv, certs, .pairing_token, .env, __pycache__, website, supabase,
                docs, .git)
      pkg/DEBIAN/control: Package linuxremoteplayer, Version from VERSION file, Arch all,
               Depends: python3, python3-venv, openssl, avahi-daemon; Recommends: chromium | chromium-browser, ufw
      pkg/DEBIAN/postinst: create venv + pip install -r requirements.txt; uinput
               modprobe/udev rule/group (reuse install.sh logic — factor shared steps into
               scripts/setup_common.sh sourced by both); install /usr/local/bin/lrp-setup
               (mode picker = current interactive part of install.sh) and print
               "Ejecuta: sudo lrp-setup" as the final line; install root-owned
               /usr/local/bin/lrp-update (see below).
      pkg/DEBIAN/prerm: stop/disable both service scopes (reuse uninstall.sh logic).
      output: dist/linuxremoteplayer_<VERSION>_all.deb + sha256 file.
  - UPDATE PIPELINE v2 (no GitHub API — repo will be private):
      * website/latest.json (new): {"version":"1.1.0","deb_url":"https://linux-remote-player.vercel.app/downloads/linuxremoteplayer_1.1.0_all.deb","sha256":"..."}
      * website/downloads/ folder holds the .deb (Vercel serves static files; the package is
        ~1MB, far under limits).
      * backend /api/update/check: fetch website latest.json (env UPDATE_MANIFEST_URL,
        default https://linux-remote-player.vercel.app/latest.json) instead of GitHub API.
      * /usr/local/bin/lrp-update (root, 0755, installed by postinst): downloads deb_url to
        /tmp, verifies sha256, `apt-get install -y --reinstall /tmp/pkg.deb`, restarts service.
        postinst adds sudoers drop-in /etc/sudoers.d/linuxremoteplayer:
        `%input ALL=(root) NOPASSWD: /usr/local/bin/lrp-update` (fixed path, no args).
      * scripts/update.sh becomes a thin wrapper: `sudo /usr/local/bin/lrp-update`.
        /api/update/apply launches that wrapper (unchanged endpoint contract).
  - website install section: replace the git-based one-liner with:
      `curl -fsSL https://linux-remote-player.vercel.app/install.sh | sudo bash`
      where website/install.sh (new) = downloads latest .deb per latest.json, sha256-checks,
      apt-get installs it, then runs lrp-setup (with the /dev/tty fix from P5).
  - README: update install/update instructions; remove references to cloning for end users
    (developers section may keep git instructions).
release_process_doc (top comment of build_deb.sh):
  1) bump VERSION + CHANGELOG  2) ./scripts/build_deb.sh  3) copy dist/*.deb to
  website/downloads/ + update website/latest.json (version, url, sha256)  4) commit+push ->
  Vercel publishes  5) phones/HTPCs see the update via /api/update/check.
acceptance: build_deb.sh produces an installable .deb on a clean VM (install -> lrp-setup ->
  service runs); latest.json flow: /api/update/check reports the new version; lrp-update
  upgrades and restarts; website one-liner works end to end without GitHub access.
```

---

## PHASE P8 — FINAL VERIFICATION (run all)

```bash
python3 -m py_compile backend/*.py && node --check frontend/app.js
grep -ri "remote kiosk" --include="*.html" --include="*.js" --include="*.json" --include="*.ts" . | grep -v docs/archive | wc -l   # 0
curl -sk https://127.0.0.1:8000/api/debug    # gamepad + mouse ui flags true
curl -sk https://127.0.0.1:8000/api/status   # 403 remote / JSON local
bash -n scripts/*.sh website/install.sh
# Manual matrix (owner): touchpad drag 10s continuous · volume/mute on HTPC w/o DE ·
# Home closes kiosk+native · pin native app · skins switch (licensed) · status panel QR pair ·
# curl|bash reaches mode prompt · PWA reinstall shows new name+icon · update via latest.json
```

## EXECUTION ORDER
P1-1, P1-2, P5, P2-1, P2-2, P3-1, P2-3, P3-2, P3-3, P4, P6, P7, P8.
Report format: per-item {id, status, files touched, deviations, owner-actions-required}.
```
