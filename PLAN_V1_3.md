# PLAN v1.3 — Phase 10: panel bugs, mobile UI, control redesign, catalog, ad-blocking (machine-optimized)

```yaml
document_type: implementation_plan
audience: AI coding agent (Gemini) — execute autonomously
baseline: v1.2.1 (deployed; OTA update button verified working)
source: owner field-test report "Fase 10" + independent code verification
verified_facts (already confirmed against code — trust these):
  - backend/main.py L467: /api/update/check has Depends(require_token) -> the local status
    panel fetches it WITHOUT a token -> 401 -> "vundefined" + broken polling. CONFIRMED.
  - frontend/app.js L553: kiosk tile icons use logo.clearbit.com. CONFIRMED.
  - backend/kiosk.py L79-82: close_all() relaunches the status panel IMMEDIATELY when
    APPLIANCE_IDLE_PANEL=true -> this is why Home feels disruptive. CONFIRMED.
critical_corrections_to_the_report (apply THESE, not the report's literal proposals):
  - C1: do NOT replace require_token with require_local on /api/update/check — the PHONE
    also calls it (Ajustes -> Buscar actualizaciones) from a REMOTE IP with a token.
    Implement DUAL acceptance: allow if (request is local) OR (X-Auth-Token valid).
  - C2: Home should not need Super+D tricks: simply REMOVE the immediate panel relaunch
    from close_all(); the existing 45s idle monitor (monitor_idle_panel) already brings
    the panel back when the TV is truly idle. Home -> clean close, panel arrives later.
  - C3: uBlock Origin classic is Manifest V2 (being phased out of Chromium). Use
    uBlock Origin LITE (MV3). Do NOT bundle it inside the .deb (GPL bundling + package
    bloat + snap confinement issues): download it during lrp-setup instead. SNAP CAVEAT:
    on KDE Neon/Ubuntu, chromium is a SNAP and CANNOT read /opt — the extension MUST live
    in a snap-readable path (the target user's real $HOME, non-hidden dir).
orchestration_contract:
  - Self-audit first; map items to exact lines; trust code over report when they differ.
  - After each phase: python3 -m py_compile backend/*.py && node --check frontend/app.js
    && bash -n scripts/*.sh website/install.sh
  - End: independent subagent review of the diff; report {id, estado, archivos,
    desviaciones, acciones-del-dueño}. Bump VERSION 1.3.0 + CHANGELOG; publish via the
    WSL .deb pipeline (same as v1.2.x) + latest.json + push.
severity_scale: [CRITICAL, HIGH, MEDIUM, LOW]
```

---

## P1 — STATUS PANEL BUGS (CRITICAL)

### P1-1 "vundefined" / frozen data — dual-auth for update check
```yaml
files: [backend/main.py, frontend/status.html]
fix_spec:
  - New dependency helper `require_local_or_token(request, x_auth_token)`: passes if
    require_local() succeeds OR verify_access(x_auth_token) is True; else 401.
  - Apply it to /api/update/check (REPLACES require_token). Phone keeps sending its
    header (no frontend change); panel needs none.
  - status.html hardening: every polling function (updateStatus, checkForUpdates, PIN
    poll) must be try/catch-isolated so one failing endpoint can NEVER freeze the others;
    on fetch failure render explicit fallbacks ("—", "Sin conexión") instead of stale
    "Verificando...". Never interpolate undefined into the DOM (`v${data.latest ?? '?'}`).
acceptance: panel opened at https://127.0.0.1:8000/status shows real version, client
  count, latency and license state; phone's "Buscar actualizaciones" still works.
```

### P1-2 Panel layout/responsive
```yaml
files: [frontend/status.html]
fix_spec:
  - body { overflow: hidden } — a TV panel must NEVER scroll. Fit content to viewport:
    CSS grid/flex with flex-wrap, relative units (vw/vh/clamp), remove rigid min-widths.
  - Test targets: 1920x1080 and 1280x720 (TV), plus 1024x768 fallback. No collisions,
    no scrollbars, PIN remains couch-readable.
  - Remove the manual activation block "https://TU-TV:8000/?license=..." (broken/confusing;
    activation happens on the phone).
  - Replace the clickable "Comprar licencia" button with a NON-interactive line: small
    text "Compra tu licencia en: linux-remote-player.vercel.app" (a TV kiosk can't
    usefully click it; clicking currently just reloads the page).
acceptance: no scrollbars at any target resolution; removed blocks gone.
```

---

## P2 — MOBILE APP UI (HIGH)

### P2-1 iOS safe areas (notch + gesture bar)
```yaml
files: [frontend/index.html]
fix_spec:
  - Verify meta viewport includes viewport-fit=cover (present historically — confirm).
  - Top header: padding-top: max(env(safe-area-inset-top), 8px) on the header container
    (not only body). Bottom control panel: padding-bottom:
    calc(1rem + env(safe-area-inset-bottom)) — verify it survived the redesigns.
  - Drawers (#app-drawer, #settings-drawer, #kb-bar) also need both insets.
  - Test in iOS standalone mode: gear icon fully tappable, volume buttons above the
    gesture bar.
acceptance: no UI element under the notch/status bar or gesture bar on iPhone standalone.
```

### P2-2 Settings cleanup: pairing token field out, license states
```yaml
files: [frontend/index.html, frontend/app.js]
fix_spec:
  - REMOVE the "Código de emparejamiento" row from the settings drawer (PIN flow owns
    pairing now; the collapsed manual fallback in the PAIRING SCREEN stays as-is).
    Remove associated saveNewToken UI wiring (keep the function only if the pairing-screen
    fallback uses it).
  - License row states: after successful activation (or when /api/license/status returns
    licensed:true at boot): input.disabled = true, input shows the key masked, button
    replaced by a static green badge "✓ Activada". 
  - "Comprar licencia" row: hidden whenever licensed === true (evaluate at boot AND after
    activation — single render function, not two code paths).
acceptance: fresh unlicensed -> buy row visible, license input editable; after activation
  (and after reload) -> input locked, green badge, buy row gone; pairing row absent.
```

### P2-3 Skins: modal with visual previews
```yaml
files: [frontend/index.html, frontend/app.js, frontend/tailwind-lite.css or skins.css]
fix_spec:
  - Settings row becomes a single button "Personalizar tema" -> opens a modal (same
    drawer/overlay pattern as existing UI, DOM-built, no innerHTML with data).
  - Modal shows one card per skin (dark, day, neon, anime): a mini-mockup preview
    rendered with CSS using that skin's variables (small rectangle with bg, a fake
    button, accent dot — pure CSS, no screenshots; anime card may use the real bg image
    thumbnail via CSS background) + name + active-state ring.
  - Unlicensed: cards visible but locked (padlock overlay); tap -> toast + buy_url.
  - Keep persistence + license gating logic exactly as-is (setSkin).
acceptance: modal opens, previews reflect each skin's palette, selection applies live,
  lock behavior for unlicensed users unchanged.
```

### P2-4 Mic button visibility after licensing
```yaml
files: [frontend/app.js, frontend/index.html]
fix_spec:
  - Audit the mic-row display logic: it must re-evaluate after license activation
    (activateLicenseKey already calls fetchConfig — verify fetchConfig actually toggles
    mic-row from voice_enabled) and the row must have position/z-index that keeps it
    above the touchpad/scroll strip (z-index >= 30; verify no overlap at small heights).
  - If ENABLE_VOICE=false server-side, mic stays hidden regardless of license (document:
    voice requires BOTH license and server voice config).
acceptance: with ENABLE_VOICE=true + licensed, mic visible and tappable immediately after
  activation without reload; never buried under other elements.
```

---

## P3 — CONTROL/BUTTON REDESIGN (HIGH)

### P3-1 Key combos support (backend)
```yaml
files: [backend/input_emulator.py, backend/main.py]
fix_spec:
  - input_emulator: new async press_combo(combo_name). PREDEFINED whitelist only (never
    arbitrary key arrays from the client):
      COMBOS = {
        "browser_back":  ["KEY_LEFTALT", "KEY_LEFT"],
        "close_window":  ["KEY_LEFTALT", "KEY_F4"],
      }
    Implementation: press modifiers down -> key down -> syn -> key up -> modifiers up.
    Ensure KEY_F4 and KEY_LEFTALT are in the UInput key capability list (range 1..99
    covers them — verify: KEY_F4=62, KEY_LEFTALT=56 ✔).
  - ALLOWED_KEYS: add "KEY_LEFTMETA" (single-press for the OS app launcher).
  - main.py WS: new msg {"type":"combo","name":"browser_back"} -> validate against
    COMBOS keys -> press_combo; unknown name -> error reply. Rate-limited by the
    existing slow bucket.
acceptance: WS combo browser_back navigates back inside a kiosk page; close_window closes
  the focused window; arbitrary combo names rejected.
```

### P3-2 Button remap + new buttons (frontend)
```yaml
files: [frontend/index.html, frontend/app.js]
layout_spec (keep current visual structure; adjust contents):
  - Volume: replace +/- line icons with conventional speaker SVGs (speaker + waves and
    a small +; speaker with a small −), same stroke style as the rest.
  - "Atrás": now sends {"type":"combo","name":"browser_back"} (was KEY_ESC).
  - "Home": now ONLY calls the existing /api/kiosk/kill (killKiosk) — with C2 applied the
    TV returns to a clean desktop; the idle monitor shows the panel after 45s if idle.
  - NEW "Panel": icon = monitor/dashboard SVG; calls new POST /api/panel/show
    (dependencies require_token) which backend-side launches the status panel kiosk
    (launch_kiosk of the local /status URL). Place it in the utility row.
  - NEW "Menú" (OS launcher): sends KEY_LEFTMETA. Icon: grid/rocket SVG.
  - NEW "Cerrar app": sends combo close_window. Icon: X-in-window SVG. Place with a
    distinct color (red-ish) and require a long-press OR double-tap to avoid accidental
    Alt+F4 (implement with the existing pointer-event patterns; toast hint on short tap:
    "Mantén pulsado para cerrar la app").
  - Rebalance the grid so rows stay thumb-reachable; do not remove existing transport/
    volume controls.
files_backend: [backend/main.py]  # /api/panel/show endpoint
acceptance: all 3 new buttons work end-to-end; Atrás navigates history in kiosk; Home
  leaves clean desktop (no immediate panel); accidental single-tap does not Alt+F4.
```

### P3-3 close_all(): remove immediate panel relaunch (correction C2)
```yaml
files: [backend/kiosk.py]
fix_spec: delete the APPLIANCE_IDLE_PANEL relaunch block inside close_all() (L79-82).
  The idle monitor in main.py remains the ONLY mechanism that (re)opens the panel
  (idle + no clients + 45s). /api/panel/show (P3-2) is the on-demand mechanism.
acceptance: Home closes everything -> desktop stays clean; panel appears by itself only
  after the idle conditions; "Panel" button opens it instantly on demand.
```

---

## P4 — CATALOG & ICONS (MEDIUM)

### P4-1 Icons: clearbit -> Google favicons
```yaml
files: [frontend/app.js (L553 area)]
fix_spec: img.src = `https://www.google.com/s2/favicons?domain=${domain}&sz=128`;
  keep the existing onerror -> letter-tile fallback. Also apply to drawer tiles if the
  code path differs.
acceptance: Netflix/YouTube/etc. tiles show real logos online; offline falls back to
  letters without broken-image icons.
```

### P4-2 Catalog update
```yaml
files: [backend/main.py SUGGESTED_KIOSKS]
fix_spec:
  - Change youtube url: https://youtube.com/tv -> https://youtube.com (tv variant now
    blocks non-certified browsers). Keep the voice-search special-case working (it
    builds /results URLs — verify unaffected).
  - ADD entries (id, name, url, brand color):
      plutotv     Pluto TV      https://pluto.tv                  #FAD000
      kick        Kick          https://kick.com                  #53FC18
      tiktok      TikTok        https://www.tiktok.com            #FE2C55
      instagram   Instagram     https://www.instagram.com         #E4405F
      facebook    Facebook      https://www.facebook.com          #1877F2
      crunchyroll Crunchyroll   https://www.crunchyroll.com       #F47521
      stremio     Stremio Web   https://web.stremio.com           #7B5BF5
  - The main row shows top-5 by usage — verify the grid/drawer handle 16 entries cleanly.
acceptance: new tiles present in drawer with colors/favicons; YouTube opens desktop site.
```

---

## P5 — AD-BLOCKING IN KIOSK (HIGH — apply correction C3, not the report's proposal)

```yaml
files: [scripts/install.sh (lrp-setup path), backend/kiosk.py, scripts/build_deb.sh (only
        if needed for shared helpers), docs]
design (corrected):
  - Extension: uBlock Origin LITE (MV3, actively supported by modern Chromium). Source:
    official GitHub releases (uBlockOrigin/uBOL-home) — download the chromium zip release
    at SETUP time (lrp-setup), NOT bundled in the .deb (avoids GPL-bundling questions,
    keeps the package small, always fetches a current version).
  - Install location (SNAP CAVEAT): chromium on Ubuntu/KDE Neon is a snap and cannot read
    /opt. Unzip to a snap-readable path in the TARGET_USER's real home:
    $USER_HOME/lrp-extensions/ublock-lite/   (non-hidden dir; chown TARGET_USER).
  - kiosk.py launch flags: append
    --load-extension=<resolved path>  (only if the dir exists — feature-detect)
    and --disable-features=Translate. Keep all existing flags.
  - lrp-setup: download step with sha256 logging, graceful skip on network failure
    ("[!] No se pudo descargar el bloqueador de anuncios; el kiosk funcionará sin él").
  - Re-run safety: idempotent (overwrite dir on re-setup to update the extension).
  - NOTE for report: --load-extension may show an infobar in some Chromium builds; the
    existing --disable-infobars/--no-errdialogs flags should suppress it — verify on Neon.
acceptance: after lrp-setup, launching an ad-heavy site in kiosk shows no popups/ads;
  if the extension dir is absent, kiosk launches normally without the flag.
```

---

## P6 — BUILD & PUBLISH v1.3.0
```yaml
steps: VERSION 1.3.0 + CHANGELOG -> commit/push -> WSL build (never /mnt) -> dpkg-deb
  validate -> copy deb to website/downloads/ -> latest.json (version/url/REAL sha256) ->
  push -> verify live latest.json + deb URL 200 + sha256 match.
note: after publish, the owner's TV panel should offer "Actualizar a v1.3.0" (OTA path
  proven in v1.2.1) — that is the acceptance test for the whole release.
```

## EXECUTION ORDER
P1-1, P1-2, P3-3, P3-1, P3-2, P2-1, P2-2, P2-3, P2-4, P4-1, P4-2, P5, P6.

## FINAL VERIFICATION (owner, on HTPC + phone)
```
Panel: version real (no vundefined), datos vivos, sin scroll, sin bloques eliminados.
Phone: sin campo de token en Ajustes; licencia bloqueada en verde tras activar; botón
  comprar oculto; modal de skins con previews; mic visible tras activar.
Control: Atrás retrocede historial; Home deja escritorio limpio; Panel abre el panel;
  Menú abre el lanzador; Cerrar app requiere pulsación larga y cierra con Alt+F4.
Kiosk: youtube.com abre; nuevos tiles presentes con logos; sitio con ads -> sin popups.
OTA: panel ofrece y aplica v1.3.0.
```
