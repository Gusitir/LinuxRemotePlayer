# LinuxRemotePlayer — COMMERCIALIZATION PLAN (machine-optimized)

```yaml
document_type: implementation_plan
audience: AI coding agent (Gemini) — execute autonomously, phase by phase
depends_on: AUDIT_REMEDIATION_PLAN.md + FIXES_ROUND2.md (both COMPLETED — do not redo)
companion_doc: WEB_DESIGN_SPEC.md   # full design brief for PHASE C4 (website)
goal: >
  Make the app sellable: purchase website (Vercel + Stripe), license key delivered by
  email, activation UX in the app, secure license validation (no secrets on customer
  devices), one-line install, updater + uninstaller, in-app menu (Update / Buy / Share),
  README, and a final careful repo cleanup.
execution_contract:
  - Phases MUST run in order C1 -> C2 -> C3 -> C4 -> C5 -> C6. C0 is human-only.
  - Items marked HUMAN_REQUIRED cannot be done by the agent: emit a clear TODO list for
    the owner (Agustin) and use placeholder env names; NEVER invent or hardcode real keys.
  - Preserve existing architecture: FastAPI backend, vanilla-JS PWA, no build step,
    Spanish UI strings, single-file frontend pages.
  - Every new script goes in scripts/, is idempotent, and starts with `set -e`.
  - Do not break the offline/no-cloud mode: the app must keep working WITHOUT any license
    server for basic remote control (pairing token path). The license gates ONLY voice/AI
    and future premium features.
severity_scale: [CRITICAL, HIGH, MEDIUM, LOW]
```

---

## SECRETS MATRIX (CRITICAL — read before any phase)

```yaml
rule: secrets NEVER ship to the customer's HTPC or the static website.
locations:
  stripe_secret_key:        ONLY in Supabase Edge Function secrets
  stripe_webhook_secret:    ONLY in Supabase Edge Function secrets
  resend_api_key:           ONLY in Supabase Edge Function secrets
  supabase_service_role:    ONLY in Supabase Edge Function runtime (automatic) — REMOVE from backend/.env
  supabase_anon_key:        allowed in backend/.env (it is public by design; RLS protects data)
  license_token:            customer device only (phone storage + backend/.env or .license file)
  pairing_token:            customer device only (backend/.pairing_token)
current_violation_to_fix: >
  backend/auth.py uses supabase-py with SUPABASE_KEY (service_role) directly on the HTPC.
  PHASE C2 replaces this with HTTPS calls to an Edge Function. This is the single most
  important security change in this plan.
```

---

## PHASE C0 — HUMAN_REQUIRED: accounts & configuration (owner checklist, no code)

```yaml
- id: C0-1
  task: Create/verify Stripe account. Create ONE Product "LinuxRemotePlayer Licencia"
        with a one-time Price (recommended to start; subscriptions can come later).
        Create a Payment Link for that price. Note the URL -> used as BUY_URL everywhere.
        In the Payment Link settings enable "collect customer email" (default) and set
        the after-payment redirect to https://<vercel-domain>/gracias.html.
- id: C0-2
  task: In Supabase dashboard note PROJECT_URL and ANON_KEY. Install supabase CLI locally
        (needed once to deploy Edge Functions: `supabase functions deploy`).
- id: C0-3
  task: Create a Resend account (resend.com, free tier 100 mails/day), verify a sending
        domain or use onboarding@resend.dev for testing. Note RESEND_API_KEY.
- id: C0-4
  task: In Stripe dashboard -> Developers -> Webhooks: add endpoint
        https://<PROJECT_REF>.functions.supabase.co/stripe-webhook
        with event `checkout.session.completed`. Note the signing secret (whsec_...).
- id: C0-5
  task: Set Edge Function secrets:
        supabase secrets set STRIPE_SECRET_KEY=... STRIPE_WEBHOOK_SECRET=... RESEND_API_KEY=... BUY_URL=...
- id: C0-6
  task: Create GitHub repo (public or private). Push. Create a Vercel project pointing at
        the /website directory (PHASE C4 creates it). Note the production domain.
- id: C0-7
  task: LEGAL decision: current LICENSE file appears to be GPL. GPL allows selling but
        obliges source distribution to buyers. If undesired, replace with a proprietary
        EULA before public release. (Owner decision; agent must NOT change LICENSE alone.)
```

---

## PHASE C1 — Supabase v2: schema + Edge Functions

### C1-1 — Schema migration
```yaml
severity: CRITICAL
file: backend/supabase_schema.sql (append a clearly marked "-- v2 MIGRATION" section)
fix_spec: |
  alter table licenses add column if not exists email text;
  alter table licenses add column if not exists active boolean not null default true;
  alter table licenses add column if not exists plan text not null default 'lifetime';
  alter table licenses add column if not exists stripe_customer_id text;
  alter table licenses add column if not exists stripe_session_id text unique;  -- idempotency
  -- consume_command(): add `and active` to the WHERE clause (deny revoked licenses).
  -- New helper for validation without increment:
  create or replace function check_license(p_token text) returns json ...
  -- returns {"valid": bool, "active": bool, "plan": text, "remaining_today": int}
notes: stripe_session_id unique => webhook retries cannot create duplicate licenses.
acceptance: SQL runs clean twice in a row (idempotent) in the Supabase SQL editor.
```

### C1-2 — Edge Function `stripe-webhook`
```yaml
severity: CRITICAL
file: supabase/functions/stripe-webhook/index.ts   (new; Deno/TypeScript)
behavior:
  1. Verify Stripe signature with STRIPE_WEBHOOK_SECRET (constructEventAsync). 400 on fail.
  2. Handle checkout.session.completed:
     a. Idempotency: if a license with this stripe_session_id exists -> 200 return.
     b. Generate token: crypto random, format 'LRP-XXXX-XXXX-XXXX' (A-Z0-9, no 0/O/1/I).
     c. Insert license row (token, email from session.customer_details.email, plan,
        stripe_customer_id, stripe_session_id) using service_role client (built-in env).
     d. Send email via Resend API: subject "Tu licencia de LinuxRemotePlayer",
        HTML body containing: the key in large monospace, activation steps (3 lines:
        abre la app -> Ajustes -> Código de licencia -> pega la clave), a deep link
        block "o desde el navegador del teléfono en tu red local:
        https://TU-TV.local:8000/?license=LRP-...", and a support mailto.
     e. Return 200 even if the email send fails (log it) — the license row is the truth;
        the /gracias page also shows recovery instructions.
  3. Any other event -> 200 no-op.
acceptance: `stripe listen --forward-to` test event creates exactly one row + one email;
            replaying the same event creates nothing new.
```

### C1-3 — Edge Function `validate-license`
```yaml
severity: CRITICAL
file: supabase/functions/validate-license/index.ts   (new)
api_contract:
  request:  POST {"token": "LRP-....", "consume": true|false}
  response: 200 {"valid": true, "active": true, "plan": "lifetime", "remaining_today": 57}
            200 {"valid": false}                       # unknown/revoked -> still HTTP 200
            429 {"valid": true, "active": true, "remaining_today": 0}   # daily cap hit
behavior:
  - consume=true  -> call consume_command RPC (atomic, respects active + 60/day).
  - consume=false -> call check_license (no increment) — used at app boot.
  - CORS: allow all origins (called from customer LAN backends).
  - Rate-limit abuse guard: max 10 req/min per token (in-function memory Map is fine).
acceptance: curl tests for the 3 response shapes pass.
```

---

## PHASE C2 — Backend: secure licensing client + versioning + updater + uninstaller

### C2-1 — Remove service_role from the device (auth.py refactor)
```yaml
severity: CRITICAL
files: [backend/auth.py, backend/requirements.txt, backend/.env.example]
fix_spec:
  - DELETE supabase-py usage and the `supabase` dependency from requirements.txt.
  - New envs in .env.example: LICENSE_API_URL (default
    https://<PROJECT_REF>.functions.supabase.co/validate-license), LICENSE_TOKEN (empty).
    REMOVE SUPABASE_URL / SUPABASE_KEY entries entirely.
  - auth.py becomes two independent gates:
      verify_access(token)          -> UNCHANGED semantics: local PAIRING_TOKEN check.
                                       (Remote control never depends on the cloud.)
      validate_license_and_increment(license_token) -> httpx POST to LICENSE_API_URL
                                       {"token":..., "consume": true}; 3s timeout.
  - OFFLINE GRACE: cache last successful validation timestamp in backend/.license_cache
    (json: {token_hash, last_ok_iso}). If the API is unreachable AND last_ok < 72h ago,
    allow. If never validated or >72h, deny with message "Sin conexión con el servidor
    de licencias".
  - The license token is stored server-side in backend/.env as LICENSE_TOKEN when the
    user activates from the phone (see C2-2). chmod 600 on write.
acceptance:
  - grep -r "SUPABASE" backend/ returns nothing.
  - With no network, a license validated <72h ago still allows voice; >72h denies.
```

### C2-2 — License activation endpoint (how the user "puts the key in")
```yaml
severity: HIGH
files: [backend/main.py, frontend/app.js]
design: >
  Two tokens exist and must not be confused in UI or code:
    pairing token  = connects PHONE <-> HTPC (already working, stays as-is).
    license key    = LRP-XXXX-... unlocks voice/AI/premium (NEW).
fix_spec:
  - POST /api/license/activate  (dependencies=[Depends(require_token)])
      body {"key": "LRP-..."} -> backend calls validate-license (consume=false);
      if valid: persist LICENSE_TOKEN into backend/.env (python-dotenv set_key),
      update in-memory value, return {"status":"success","plan":...}.
      if invalid: 400 {"detail":"Clave no válida"}.
  - GET /api/license/status (auth) -> {"licensed": bool, "plan": str|null, "voice_enabled": bool}.
  - Frontend Ajustes: new row "Clave de licencia" (input + Activar button) placed ABOVE
    the pairing row; on success show toast "Licencia activada" and re-run loadConfig so
    the mic button appears. Support deep link ?license=LRP-... in initToken(): if param
    present and connected, auto-call activate, then clean URL (mirrors ?token= handling).
acceptance: activating a valid key from the phone persists across backend restart;
            /api/license/status flips to licensed:true; mic row becomes visible.
```

### C2-3 — Versioning
```yaml
severity: HIGH
files: [VERSION (new, repo root, content "1.0.0"), backend/main.py]
fix_spec:
  - /api/config adds: "version": <content of VERSION file, read once at startup>.
  - GET /api/update/check (auth): fetch
    https://api.github.com/repos/<OWNER>/<REPO>/releases/latest (5s timeout, httpx),
    compare tag_name (strip leading 'v') vs local semver ->
    {"current":"1.0.0","latest":"1.1.0","update_available":true}.
    On network failure: {"current":..., "latest":null, "update_available":false}.
  - OWNER/REPO from env GITHUB_REPO in .env.example (e.g. "agustin/linuxremoteplayer").
acceptance: endpoint returns coherent JSON online and offline.
```

### C2-4 — scripts/update.sh + self-update endpoint
```yaml
severity: HIGH
files: [scripts/update.sh (new), backend/main.py]
fix_spec:
  - scripts/update.sh: set -e; cd repo root (relative to script); `git fetch --tags &&
    git checkout $(git describe --tags $(git rev-list --tags --max-count=1))` if tags
    exist else `git pull --ff-only`; venv pip install -r requirements.txt;
    restart service: try `systemctl --user restart linuxremoteplayer` then fall back to
    `sudo systemctl restart linuxremoteplayer` (document that Appliance mode may need a
    sudoers NOPASSWD line for this exact command — write the exact line in a comment).
  - POST /api/update/apply (auth): launch update.sh DETACHED
    (subprocess.Popen(start_new_session=True, stdout->/tmp/lrp-update.log)) and return
    {"status":"started"} immediately — the service will die and be restarted by the
    script/systemd; the phone shows "Actualizando..." and reconnects via the existing
    heartbeat/backoff logic (no new client code needed for the wait).
  - RELEASE PROCESS documented at top of update.sh as a comment: bump VERSION, update
    CHANGELOG.md, `git tag vX.Y.Z && git push --tags`, create GitHub Release.
acceptance: with a newer tag available, apply -> service restarts on the new tag; VERSION
            reported by /api/config changes.
```

### C2-5 — scripts/uninstall.sh
```yaml
severity: HIGH
file: scripts/uninstall.sh (new)
fix_spec: mirror install.sh exactly, in reverse, with a confirm prompt ("Esto eliminará
  LinuxRemotePlayer. ¿Continuar? [y/N]"):
  - stop+disable+rm BOTH possible units (system /etc/systemd/system/linuxremoteplayer.service
    and user ~/.config/systemd/user/...), daemon-reload.
  - rm /etc/udev/rules.d/99-uinput.rules and /etc/modules-load.d/uinput.conf; udevadm reload.
  - ufw delete allow 8000/tcp (ignore failure).
  - rm -rf backend/.venv backend/certs backend/.pairing_token backend/.license_cache
    backend/__pycache__.
  - PRINT (do not execute): optional manual steps — remove user from input group
    (`sudo gpasswd -d $USER input`), delete the cloned repo folder, uninstall avahi/chromium
    (may be used by other software — never auto-remove).
acceptance: after run, `systemctl status linuxremoteplayer` (both scopes) -> not-found;
            re-running install.sh afterwards works cleanly.
```

### C2-6 — scripts/bootstrap.sh (one-line install)
```yaml
severity: MEDIUM
file: scripts/bootstrap.sh (new)
fix_spec: |
  #!/bin/bash — set -e; require root; apt-get install -y git (if missing);
  INSTALL_DIR=/opt/linuxremoteplayer; if dir exists -> git pull, else git clone <REPO_URL>;
  exec bash "$INSTALL_DIR/scripts/install.sh"
  REPO_URL from a variable at the top (placeholder https://github.com/<OWNER>/<REPO>.git).
usage_line_for_website: curl -fsSL https://raw.githubusercontent.com/<OWNER>/<REPO>/main/scripts/bootstrap.sh | sudo bash
acceptance: line works on a clean Debian/Ubuntu VM.
```

---

## PHASE C3 — Frontend app: menu (Actualizar / Comprar / Compartir)

### C3-1 — Settings drawer rework
```yaml
severity: HIGH
files: [frontend/index.html, frontend/app.js]
fix_spec: replace the placeholder rows (comingSoon) with, in this order:
  1. "Clave de licencia"  -> input + Activar (from C2-2). Show current status line under
     it: "Licencia: activa (lifetime)" or "Sin licencia — funciones de voz bloqueadas".
  2. "Código de emparejamiento" (existing row, unchanged).
  3. "Buscar actualizaciones" -> row shows "Versión 1.0.0"; on tap: GET /api/update/check;
     if update_available -> button text becomes "Actualizar a v1.1.0"; tap again ->
     POST /api/update/apply + toast "Actualizando… la app se reconectará sola" (the
     existing reconnect/backoff UI handles the restart window).
  4. "Comprar licencia" -> window.open(BUY_URL, '_blank'). BUY_URL delivered by the
     backend in /api/config as "buy_url" (env BUY_URL in .env.example) so it is
     changeable without shipping a frontend update.
  5. "Compartir app" -> Web Share API:
       navigator.share({
         title: 'LinuxRemotePlayer',
         text: '🎬 Convertí mi PC Linux en una Smart TV con control remoto desde el
                móvil. Touchpad, teclado, apps y voz. Mirá:',
         url: BUY_URL (website)
       })
     Fallback if !navigator.share: copy `${text} ${url}` to clipboard + toast
     "Enlace copiado — pégalo donde quieras".
  6. "Descargar Certificado CA" (existing, keep).
  7. Remove: "Comprar Premium", "Skins / Temas", "Página web", "Ajustes generales",
     "Información de la app" placeholders. Keep the version footer, now dynamic.
acceptance: all 6 rows functional; zero comingSoon() references left in index.html.
```

---

## PHASE C4 — Purchase website (Vercel)

```yaml
severity: HIGH
directory: website/   (new, repo root; deployed as a Vercel static project)
instruction: >
  Build EXACTLY per companion doc WEB_DESIGN_SPEC.md (layout, palette, copy, sections).
  Read that file fully before writing any HTML.
files:
  - website/index.html      # single file, inline CSS, no frameworks, no build step
  - website/gracias.html    # post-purchase page (Stripe redirect target)
  - website/icon-192.png / icon-512.png (copy from frontend/)
  - website/vercel.json     # {"cleanUrls": true}
functional_requirements:
  - Buy buttons -> BUY_URL (Stripe Payment Link) — plain <a>, no JS needed.
  - Install section shows the C2-6 one-liner with a copy-to-clipboard button.
  - gracias.html: "Revisa tu correo — tu clave llega en 1-2 minutos" + activation steps +
    spam-folder note + support mailto. NO license data is ever rendered client-side
    (the key travels only by email).
  - SEO: title/description/OG tags in Spanish; og:image can reuse icon-512.png.
acceptance: Lighthouse (mobile) >= 90 performance & accessibility; total page weight
            < 300KB; renders correctly at 360px and 1440px.
```

---

## PHASE C5 — Documentation

```yaml
- id: C5-1
  files: [README.md]
  action: update the README (a solid base already exists) — add: buy/licensing section,
          one-liner install, update & uninstall commands, website link, screenshots
          placeholders, repo layout tree including website/ and supabase/. Remove the
          local file:/// link to TESTING.md (relative link instead). English keeps.
- id: C5-2
  files: [CHANGELOG.md (new)]
  action: Keep-a-Changelog format; entry [1.0.0] summarizing the audit hardening +
          commercialization features. Every future release adds an entry (tie to C2-4
          release process).
- id: C5-3
  files: [TESTING.md]
  action: add sections: license activation test, update test, uninstall test.
```

---

## PHASE C6 — FINAL: careful repo cleanup (READ RULES FIRST)

```yaml
severity: HIGH (destructive if careless)
rules_for_agent:
  R1: SAFETY SNAPSHOT FIRST: `git tag pre-cleanup && git branch backup/pre-cleanup`.
      Never proceed without a clean `git status` (commit pending work first).
  R2: Use `git rm` (tracked) — never delete via OS for tracked files, so everything is
      recoverable. One single cleanup commit at the end with the full file list in the
      commit message.
  R3: BEFORE deleting any file, grep the whole repo for references to its name
      (imports, links in .md, script paths). A referenced file is NOT deleted — fix the
      reference or keep the file.
  R4: NEVER touch (hard blocklist): .git/, .gitignore, LICENSE, backend/.env,
      backend/.env.example, backend/.pairing_token, backend/certs/, backend/.license_cache,
      anything under website/ or supabase/ created in this plan, VERSION, CHANGELOG.md.
  R5: When in doubt -> move to docs/archive/ instead of deleting.
dispositions:
  - geminireport.md, geminireport2.md            -> git rm (session artifacts, no value in repo)
  - AUDIT_REMEDIATION_PLAN.md, FIXES_ROUND2.md,
    PLAN_COMERCIALIZACION.md, WEB_DESIGN_SPEC.md -> git mv into docs/archive/ (historical
    record, keep out of root; verify no README links break)
  - .agents/                                     -> ASK OWNER (agent-tooling context; if owner
    approves: add to .gitignore and git rm -r --cached, keep on disk)
  - backend/__pycache__/                         -> ensure untracked (git rm -r --cached if
    tracked); it is already gitignored
  - scripts/generate_png_icons.py                -> KEEP (icon regeneration tool)
  - scripts/gen_cert.sh                          -> verify already deleted in round 1; if a
    stray copy exists, git rm
  - TESTING.md                                   -> KEEP (referenced by README)
  - repo-wide sweeps: remove *.pyc, .DS_Store, Thumbs.db, editor swap files; verify with
    `git status --ignored` that ignores are healthy
final_step: run full VERIFICATION below, then commit "chore: repo cleanup (see list)" and
            `git tag v1.0.0`.
```

---

## VERIFICATION (end-to-end, after all phases)

```bash
# Syntax / boot
python3 -m py_compile backend/*.py && node --check frontend/app.js
cd backend && .venv/bin/python -c "import main" && cd ..

# Licensing (needs deployed Edge Functions)
curl -s -X POST $LICENSE_API_URL -d '{"token":"LRP-FAKE","consume":false}' | grep '"valid": *false'
# Real flow: Stripe test-mode payment -> email arrives -> activate key in app ->
#            /api/license/status licensed:true -> mic visible -> voice command works.

# Update flow
curl -sk -H "X-Auth-Token: $(cat backend/.pairing_token)" https://127.0.0.1:8000/api/update/check
# Tag a test release -> app Ajustes shows "Actualizar a vX" -> apply -> reconnects on new VERSION.

# Uninstall / reinstall
sudo scripts/uninstall.sh && sudo scripts/install.sh   # both clean

# Website
# Vercel deploy preview: buy button opens Stripe checkout (test mode); gracias.html reachable;
# install one-liner copyable; Lighthouse >= 90 / 90.

# Cleanup sanity
git log --oneline -3 && git tag --list 'v*' 'pre-cleanup'
grep -rn "geminireport" . --include="*.md" | wc -l   # 0
```

## EXECUTION ORDER (flat)
C1-1, C1-2, C1-3, C2-1, C2-2, C2-3, C2-4, C2-5, C2-6, C3-1, C4 (read WEB_DESIGN_SPEC.md first), C5-1..C5-3, C6, VERIFICATION.
