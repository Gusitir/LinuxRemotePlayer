# LinuxRemotePlayer — architecture

> **This document is for a human engineer**: a technical reviewer, a contractor, or
> someone deciding whether this codebase is worth buying or maintaining. It is not
> end-user documentation (that lives at `website/docs.html`, ES and EN) and it is not the
> agent index (`.agents/APPCORE.md`, which says *where* things are; this says *what for
> and why*).
>
> Maintained by the auditor role. Refreshed after each release and whenever a change moves
> a boundary, adds a dependency, or reverses a decision. Nothing here is written that was
> not checked against the code.

Last verified against the code: **2026-07-24** · shipped version `1.8.0` · built and
audited, not yet published: `1.8.9`

---

## 1. What this is

A Linux PC in the living room becomes the household's smart TV, and the remote control is
any phone on the same Wi-Fi. The phone opens a PWA (no app store), pairs with a 6-digit
PIN shown on the TV, and gets a touchpad, a real keyboard, media transport, launchers for
streaming sites and native desktop apps, and — with a Pro license — voice commands in
Spanish and English.

The core problem it solves is social, not technical: an HTPC is usable only by the person
who set it up. Everyone else in the house needs a remote they already know how to hold.

Two halves: a **Python service** installed on the Linux PC via a `.deb`, and a **static
PWA** it serves to phones over HTTPS on the LAN. Cloud is used only for AI and licensing —
there is no local model inference, by design.

## 2. Run, build, test

```bash
# Run the server from a clone (dev). Self-generates its HTTPS certs on first run.
cd backend && pip install -r requirements.txt && python run.py

# Build the installable package. Runs the quality gates and aborts if one fails.
bash scripts/build_deb.sh          # -> dist/linuxremoteplayer_<VERSION>_all.deb + .sha256

# The gates that run inside that build:
python3 scripts/check_css_sync.py  # fails if a CSS class is used in markup but undefined
                                   # (plus an inline check that sw.js got the version)
```

**Environment constraints that bite** — these are not preferences, they are load-bearing:

- The `.deb` **must** be built from a native Linux filesystem. Building from a Windows
  mount (`/mnt/...` under WSL) silently truncates files over ~40 KB, producing a package
  that looks valid and ships a broken `app.js`. Standard practice here is a fresh clone
  inside the Linux home directory.
- The frontend has **no build step**. `app.js`, `index.html` and the CSS ship as written.
  This is deliberate (see §7) and it is why the CSS gate exists.
- Target platform is Debian/Ubuntu-family with **systemd**, **uinput**, and a desktop
  session. Wayland/KDE Plasma Bigscreen is the reference platform.

## 3. Where the risk is

Central, non-trivial, and weakly verified — read this before anything else.

| Component | Why it's risky | What would reduce it |
|---|---|---|
| `backend/main.py` (945 lines) | Every HTTP endpoint, the whole WebSocket protocol, the voice handler and the pairing state machine live in one module. A change anywhere touches everything. Splitting it is a known deferred task. | Split by concern; unit tests on the WS message handlers |
| `supabase/functions/ai-proxy` | The money path: it authorizes, meters and bills every voice command, and holds the kill-switch. A bug here is either a service outage or an unbounded bill. | Tests on the quota/kill-switch branches; alerting on the global cap |
| `backend/input_emulator.py` (305 lines) | Per-layout keyboard maps with known gaps (`< >` and AltGr brackets). Wrong output is silent — the user just gets the wrong character. | A table-driven test per layout |
| `scripts/install.sh` + the package's `prerm` | The install/uninstall path touches firewall, udev, sleep settings and system certificates. **`prerm` currently does far less than the docs promise** (see §8). | Make `prerm` call the uninstall logic; verify on a scratch machine |
| `frontend/app.js` (1574 lines) | Single file, no build, no tests; drives every interaction. | Split; the CSS gate already covers one class of drift |

## 4. Components

### `backend/` — the service on the Linux PC (2032 lines, Python, FastAPI)

| Module | Responsible for | Verified by |
|---|---|---|
| `main.py` (945) | HTTP endpoints, WebSocket protocol, pairing PIN state machine, voice handler, idle-panel monitor | `TESTING.md` matrix + task audits |
| `input_emulator.py` (305) | Virtual keyboard and mouse via `evdev`/uinput; per-layout character maps (`us`/`es`/`latam`) | `TESTING.md` matrix |
| `kiosk.py` (244) | Launching sites full-screen in Firefox with a dedicated profile; closing windows via `wmctrl` with a KWin DBus fallback; ad-block status | `TESTING.md` matrix |
| `run.py` (222) | HTTPS with self-healing certificates (a stable local CA plus a leaf per IP/hostname); restarts the service when the machine's IP changes | `TESTING.md` matrix |
| `ai_pipeline.py` (113) | **Talks only to the ai-proxy.** Packs audio, sends it, returns the parsed intent. Holds no AI credentials. | device E2E (T-50) |
| `auth.py` (89) | Pairing-token verification; license checks against the Edge Function with a 72 h offline grace cache | device E2E (T-50) |
| `discovery.py` (63) | Finds installed desktop apps by scanning `.desktop` files | `TESTING.md` matrix |
| `audio.py` (51) | Volume and mute through the system audio stack | `TESTING.md` matrix |

**Explicitly not responsible for:** talking to any AI provider directly (that moved to the
proxy), storing license secrets, or any local model inference.

### `frontend/` — the PWA served to phones (vanilla JS, no build step)

`app.js` (1574) holds the WebSocket client with reconnect/backoff, push-to-talk voice
capture, the app tiles, and the settings drawer. `skins.css` carries four themes as CSS
custom properties — plus a *bridge* block that remaps the historical dark-assuming utility
classes onto theme variables, without which the light theme breaks. `sw.js` is a service
worker whose cache name is stamped with the build version, which is what makes updates
reach installed PWAs. **Verified by:** the CSS gate (class drift only) + `TESTING.md`.

**Explicitly not responsible for:** enforcing anything. Every gate the phone appears to
apply — license state, quotas, which keys are legal — is re-checked server-side.

### `supabase/functions/` — Edge Functions (TypeScript, Deno)

| Function | Responsible for | Status |
|---|---|---|
| `ai-proxy` | The entire voice path server-side: size cap, kill-switch, global spend cap, per-license quota, device activation, then STT and intent extraction. Holds the AI credentials. | active |
| `validate-license` | License state checks that don't consume quota | active |
| `send-feedback` | In-app feedback relay | **not deployed** (pending since v1.5) |
| `stripe-webhook` | Purchase fulfilment | **legacy** — payments moved to Paddle (§7) |

### `website/` — the public site on Vercel

The landing page and user documentation, **and the update channel**: `latest.json` is the
manifest every installed copy polls, and `downloads/` serves the `.deb`. This makes the
site load-bearing infrastructure, not marketing — see the dependency note in §6.

### `scripts/` — install, build, update, uninstall

`build_deb.sh` packages everything and runs the gates. `install.sh` (exposed as
`lrp-setup`) provisions the machine: service, firewall, udev rules, Firefox policies,
certificate trust, sleep settings.

## 5. How data flows

**Control (the common path)** — no cloud involved:

1. Phone opens the PWA over HTTPS on the LAN and authenticates the WebSocket with the
   pairing token. A bad token closes the socket with code 1008.
2. Touch and key events become small JSON messages (`pointer`, `input`, `text`, `combo`).
3. The backend validates each against a whitelist and writes to the virtual input device.
4. The kernel delivers them to the desktop as if from a real keyboard and mouse.

**Voice (Pro only)** — everything sensitive happens off the device:

1. Push-to-talk records audio; the phone sends it as a binary WebSocket frame.
2. The backend forwards it to the **ai-proxy** with the license token, a hashed device id,
   and the list of currently valid launch targets.
3. The proxy checks kill-switch → global cap → license → device activation → quota, then
   calls speech-to-text and the intent model, logs usage, and returns a structured intent.
4. The backend maps that intent onto the same whitelisted actions the buttons use.

The device never holds AI credentials, and the intent model can only ever name a target
that was passed to it in that request.

## 6. Dependencies

**Internal — what breaks what:**

- `ai_pipeline.py` depends on the ai-proxy's request/response contract. Changing field
  names in the Edge Function breaks voice on every installed copy until they update.
- `frontend/skins.css` depends on the bridge block. Adding a new neutral utility class to
  the markup without bridging it breaks the light theme silently.
- `scripts/build_deb.sh` stamps the version into `sw.js`. Without that stamp, installed
  PWAs keep serving stale assets forever.
- `scripts/dev/generate_png_icons.py` **reimplements the geometry of** `frontend/icon.svg`
  (no SVG rasteriser exists in the dev environment). Change one and you must change the
  other, or the icons drift apart silently.

**External:**

| Dependency | Used for | If unavailable |
|---|---|---|
| Supabase (Edge Functions + Postgres) | licensing, quota, activation, voice proxy | Voice stops. Pro state survives ~72 h on the offline grace cache, then degrades to free. |
| Together AI (reached only through the proxy) | speech-to-text and intent extraction | Voice stops; everything else is unaffected. |
| Vercel (site + `latest.json` + `.deb`) | update channel and purchase funnel | No updates and no new installs. **Existing installs poll this host — moving it without a redirect strands them.** |
| Firefox | kiosk browser | Site launching stops; falls back to Brave/Chromium if present. |
| System: uinput, `wmctrl` or KWin DBus, `pulseaudio-utils`, UFW | input, window management, audio, firewall | Input needs uinput; the rest degrade individually. |

Python dependencies are deliberately few: `fastapi`, `uvicorn`, `evdev`, `python-dotenv`,
`httpx`, `segno`. There is no AI SDK on the device.

## 7. Decisions and why

- **AI credentials live server-side, not on the PC.** Anything in the device's `.env` is
  extractable by whoever bought the product, so credentials there meant unlimited use at
  the vendor's cost. Rejected keeping them local with client-side limits — those are
  bypassable by definition. The cost accepted: voice now requires internet.
- **A PWA, not a native app.** No store review, no install friction, and updates ship
  instantly. Rejected a native Android app for v1; it stays on the roadmap for later.
- **Firefox as the kiosk browser**, replacing Chromium. Better ad-blocking through
  enterprise policy and a cleaner full-screen profile story.
- **No local inference.** A living-room HTPC has no GPU budget to spare while playing
  video. Rejected local speech-to-text for latency and hardware reasons.
- **One active device per license, with self-service takeover.** Rejected a hard lock:
  legitimate users replace machines, and the support burden of manual transfers is worse
  than the piracy it would prevent. A 72 h heartbeat auto-releases stale activations.
- **Payments through Paddle, not Stripe.** Stripe does not support sellers in Ecuador.
  Paddle acts as merchant of record and handles tax. The `stripe-webhook` function is a
  leftover from that earlier decision.
- **No frontend build step.** The PWA is small enough that a bundler would add a failure
  mode (and a truncation risk on this project's cross-OS workflow) without buying much.
  The trade-off is accepted knowingly: it is why the CSS drift gate exists.
- **Themes as CSS variables with a bridge layer.** The markup predates theming and assumes
  a dark background. Rewriting ~60 class usages across two large files was judged riskier
  than remapping the utility classes onto theme variables in one place.

## 8. Known limitations

Written down deliberately. Two of these are live defects.

- **No automated tests.** 4 198 lines of Python and JavaScript, zero unit or integration
  tests. Verification is the manual device matrix in `.agents/TESTING.md` plus task-level
  audits. This is the single largest gap in the project.
- **`apt remove` does not do what the documentation promises.** *(live defect)* The
  package's `prerm` only stops and disables the service. It does not release the license
  activation, remove the firewall rule, remove the udev rule, or restore sleep settings —
  all of which `scripts/uninstall.sh` does, but that script is never invoked by the package
  manager and is not shipped inside the `.deb`. The user documentation promises all four.
- **The published support address does not resolve.** *(live defect)* The site advertises
  an address at a domain that has not been purchased yet, so support email bounces.
- **`main.py` is 945 lines** and was never split; the task is deferred, not forgotten.
- **Updates are not seamless.** An installed PWA picks up a new version when it is closed
  and reopened, not while running. Accepted as sufficient for now.
- **Speech-to-text hallucinates on silence.** Holding the mic without speaking can produce
  phantom text and an unintended action. Cheap mitigation identified (discard clips under
  ~1 s) and not yet applied.
- **First voice command after idle is slow** (dormant Edge Function plus a cold model).
- **Keyboard gaps:** `< >` and AltGr bracket characters are not emitted correctly.
- **One distro family.** Debian/Ubuntu with systemd only; other distributions are roadmap.

## 9. Verification summary

| Layer | Exists? | Covers |
|---|---|---|
| Automated tests | **No** | — |
| Build gates | Partially | CSS class drift; service-worker versioning. Both abort the build. |
| Manual test matrix | Yes | `.agents/TESTING.md` — install, security, input, kiosk, PWA, licensing, voice, updates, uninstall. Executed by the owner on real hardware, with blocking items marked. |
| Audited task history | Yes | One commit per task, each independently re-verified before acceptance. `git log` + `.agents/CONTEXT.md`. |

Read honestly: this project's quality comes from **auditing and manual device testing**, not
from an automated safety net. That has been sufficient to ship a working product, and it
does not protect against the codebase becoming unmaintainable. The first meaningful
investment would be tests around `main.py`'s WebSocket handlers and the proxy's quota
logic — the two places where a silent regression is most expensive.
