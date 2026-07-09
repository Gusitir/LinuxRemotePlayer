# PLAN v1.4 — Final polish for sale (machine-optimized)

```yaml
document_type: implementation_plan
audience: AI coding agent (Gemini)
baseline: v1.3.1 deployed; owner field-tested (KDE Neon Bigscreen + iPhone)
pre_diagnosed_facts (verified by reviewer — trust these):
  - F1: KEY_LEFTMETA (code 125) is in ALLOWED_KEYS but NOT in the UInput capability list
    (range(1,100) + named list exclude it) -> write silently dropped -> Meta button dead.
  - F2: uBOL adblock: the release zip most likely extracts a NESTED folder, so
    manifest.json is not at $UBOL_DIR/manifest.json -> kiosk.py never appends
    --load-extension. Diagnose and flatten.
  - F3: mic button absent is CORRECT (server ENABLE_VOICE=false; AI phase pending).
    v1.4 only surfaces this state in UI text, does not force the button.
owner_decisions: settings redesign in categories; hideable default apps; KEEP top-row +
  drawer hybrid; touchpad navigation-mode toggle (Apple-TV style); first-run coach marks.
orchestration_contract:
  - Self-audit first; map to exact lines; trust code over plan on conflict.
  - Per phase: py_compile backend/*.py && node --check frontend/app.js && bash -n scripts.
  - End: subagent diff review; report {id, estado, archivos, desviaciones, acciones-dueño}.
  - VERSION 1.4.0 + CHANGELOG; publish via WSL pipeline (fresh clone) + latest.json + push.
```

---

## P1 — INPUT FIXES (CRITICAL)

### P1-1 Meta key dead + duplicated icon
```yaml
files: [backend/input_emulator.py, frontend/index.html]
fix:
  - Add e.KEY_LEFTMETA to the UInput capability keys list. Then add a startup guard:
    log an ERROR for any ALLOWED_KEYS/COMBOS key missing from device caps (never let this
    class of bug be silent again).
  - Menú/OS button icon currently duplicates "Más apps" grid icon -> replace with a
    distinct SVG (app-window style), same stroke family.
accept: Meta opens KDE launcher; startup log shows 0 missing caps; icons distinct.
```

### P1-2 Touchpad NAVIGATION MODE (D-pad for Bigscreen)
```yaml
files: [frontend/app.js, frontend/index.html]
design: toggle button in utility row (d-pad cross icon) switches pad mode
  pointer <-> navigation; persist in localStorage.
navigation_mode:
  - swipe >=40px (dominant axis) -> KEY_UP/DOWN/LEFT/RIGHT once; finger held past
    threshold -> repeat every 300ms (hold-to-repeat).
  - tap (<10px, <250ms) -> KEY_ENTER. long-press (>=500ms, still) -> KEY_ESC.
  - visuals: 4 faint accent chevrons + center dot overlaid on the pad (CSS only);
    toggle button shows active state. Pointer mode unchanged.
backend: none (keys already whitelisted).
accept: full KDE Bigscreen navigation from the pad; pointer mode intact after toggle back.
```

### P1-3 "Cerrar app" placement
```yaml
files: [frontend/index.html, frontend/app.js]
problem: full-width bottom bar looks wrong and collides with iPhone gesture bar.
fix: remove the bar; add a normal round button (red accent, X-window icon) in the control
  cluster (e.g. under Volumen- or next to Atrás). Keep long-press-only trigger + toast
  hint on short tap. Container must respect env(safe-area-inset-bottom).
accept: no element under the gesture bar; long-press closes; short tap only hints.
```

---

## P2 — ICONS & APPS (HIGH)

### P2-1 Favicon fallback chain (suggested + custom apps)
```yaml
files: [frontend/app.js]
problem: several tiles (Kick, TikTok, Instagram, Stremio, Plex, Max) still letter-only;
  custom-added web apps get NO favicon at all (logic only applied to suggested list).
fix:
  - Single helper setTileFavicon(img, domain) used by suggested AND custom tiles.
  - Fallback chain via img.onerror: google s2 sz=128 -> https://icons.duckduckgo.com/ip3/
    <domain>.ico -> https://<domain>/favicon.ico -> remove img (letter shows).
  - Treat s2's 16x16 "globe" default as failure when detectable (naturalWidth<=16 -> next
    source).
accept: custom app added with URL shows an icon; the listed apps resolve real logos online.
```

### P2-2 Hideable/restorable default apps
```yaml
files: [frontend/app.js, frontend/index.html]
fix:
  - localStorage 'hidden_apps' (array of suggested ids). Drawer tiles for suggested apps
    get the same × affordance as custom ones but action = hide (adds to hidden_apps).
  - renderApps filters hidden ids from row + drawer.
  - Drawer bottom: link "Restablecer apps ocultas (N)" visible when N>0 -> clears list.
accept: hide Plex -> gone from row/drawer, survives reload; restore brings all back.
```

---

## P3 — ADBLOCK NOT WORKING (HIGH)

```yaml
files: [scripts/install.sh, scripts/build_deb.sh (lrp-update heredoc), backend/kiosk.py]
diagnose_first: on the packaged zip, inspect structure: if it extracts a nested folder
  (e.g. uBOLite.chromium.mv3/), manifest.json is NOT at $UBOL_DIR/manifest.json and the
  --load-extension flag is never appended (F2).
fix:
  - After unzip in BOTH install.sh and lrp-update: if manifest.json is not at the root of
    $UBOL_DIR, find it one level down and move that folder's contents up (flatten).
  - kiosk.py: when the flag IS appended, logger.info the final path; when NOT, logger
    .warning "uBOL no encontrado en <path> — kiosk sin bloqueador" (make failure loud).
  - Add "ubol_active": bool to /api/status so the TV panel shows adblock state.
accept: ad-heavy site in kiosk shows no popups; /api/status reports ubol_active true;
  journalctl shows the load-extension line.
```

---

## P4 — SETTINGS REDESIGN: CATEGORIES (HIGH)

```yaml
files: [frontend/index.html, frontend/app.js, supabase/functions/send-feedback/index.ts (new)]
layout: replace the flat settings list with a 2-col grid of category cards (1-col under
  380px). Drawer gets overflow-x: hidden; every card max-width: 100%; the current
  horizontal scrollbar must be impossible (root cause: skin carousel with fixed widths —
  convert to grid). Tapping a card expands it (accordion) or opens a sub-view.
categories:
  licencia:
    - unlicensed: input clave + Activar + "Comprar licencia" CTA (one card, one flow).
    - licensed: single green block "✓ Licencia activa (lifetime)" + useful info: key
      masked (LRP-••••-••••-1234), plan, "Voz con IA: se activará al configurar el
      servicio" when voice_enabled=false (F3), remaining daily voice commands when true.
    - buy CTA hidden entirely when licensed.
  temas:
    - grid 2x2 of skin cards, each a CSS mockup (bg + fake button + accent dot using that
      skin's variables; anime uses the real bg image as thumbnail). Active ring on the
      selected one; padlock overlay on Pro skins when unlicensed (tap -> toast + buy).
  actualizacion:
    - version row + update button (existing check/apply logic).
    - "Novedades": show the `notes` field from the update manifest (or current CHANGELOG
      top entry bundled at build time) so users see what changed.
    - "Descargar Certificado CA" moves here.
  social:
    - "Compartir app" (existing share flow).
    - "Enviar sugerencia": textarea (max 500 chars) + optional email field -> POST to new
      Edge Function send-feedback.
  tutoriales:
    - static collapsible guides (details/summary): usar el control, modo navegación,
      emparejar un teléfono, activar licencia, solucionar conexión, cambiar de modo TV.
    - last entry: "Volver a ver la guía inicial" -> clears the coach-marks flag and
      relaunches it (P5).
feedback_edge_function (send-feedback):
  - POST {message, email?, version} -> sends via Resend to the support address
    (RESEND secrets already configured). SILENT rate limit: max 3/day per IP+token hash;
    beyond that return 200 without sending (anti-spam, invisible to user). Max 500 chars,
    strip HTML. Deploy note for owner in the report.
accept: no horizontal scroll at 320-430px widths; all five categories functional;
  feedback arrives to the support inbox; 4th message same day is silently dropped.
```

---

## P5 — FIRST-RUN COACH MARKS (MEDIUM)

```yaml
files: [frontend/app.js, frontend/index.html]
design (approved): after first successful pairing (token saved AND first Connected), if
  localStorage 'tour_done' unset -> overlay tour, 4 steps, each highlights one zone
  (dimmed backdrop with a cutout via box-shadow trick, tooltip bubble, Siguiente/Saltar):
  1. apps row: "Tus apps favoritas — un toque y se abren en la TV"
  2. touchpad: "Desliza para mover el puntero. El botón cruceta lo convierte en flechas"
  3. control cluster: "Multimedia, volumen, Atrás y Home"
  4. gear: "Todo lo demás vive en Ajustes — incluidos los tutoriales"
  On finish/skip -> set tour_done. Pure DOM/CSS, no libraries. Re-launchable from
  Ajustes -> Tutoriales (P4).
accept: fresh pairing shows the tour once; skippable at any step; never reappears; can be
  relaunched from Tutoriales.
```

---

## P6 — SMALL UI FIXES (MEDIUM)

```yaml
files: [frontend/index.html]
fixes:
  - Settings button: replace the current out-of-place icon with a gear/cog SVG from the
    same lucide-style stroke family used everywhere else.
  - Audit all header/util icons for visual consistency (stroke-width 2, round caps).
accept: gear icon in place; icon set visually homogeneous.
```

---

## P7 — BUILD & PUBLISH v1.4.0

```yaml
steps: VERSION 1.4.0 + CHANGELOG -> commit/push -> deploy send-feedback Edge Function
  (supabase functions deploy send-feedback --no-verify-jwt; report as owner action if CLI
  unavailable) -> WSL fresh-clone build -> dpkg-deb validate (Version 1.4.0; grep the
  packaged main.py for a v1.4 marker) -> copy deb to website/downloads/ (remove 1.3.x)
  -> latest.json (version/url/REAL sha256/notes) -> push -> verify live latest.json,
  deb URL 200, sha256 match.
acceptance_final: the owner's TV panel offers "Actualizar a v1.4.0" and applies it OTA.
```

## EXECUTION ORDER
P1-1, P3, P1-3, P2-1, P2-2, P1-2, P4, P5, P6, P7.

## OWNER VERIFICATION (after OTA to 1.4.0)
```
Meta abre el lanzador KDE · modo navegación recorre Bigscreen con swipes · Cerrar app es
botón normal (long-press) sin chocar con la barra iOS · adblock bloquea popups y el panel
dice ubol_active · iconos en Kick/TikTok/Stremio y en apps custom · ocultar Plex y
restablecer · Ajustes sin scroll horizontal, 5 categorías, feedback llega al correo ·
tour inicial aparece una vez tras emparejar · tuerca como icono de config.
```
