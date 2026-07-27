# Developing LinuxRemotePlayer

> **Start here if you've just joined the project.** This is how to get running, how to make
> a change safely, and what will bite you. For the shape of the system — components,
> boundaries, data flow, why things are the way they are — read
> [`ARCHITECTURE.md`](ARCHITECTURE.md) first; it's a 15-minute read and it will save you
> from "fixing" something load-bearing.

Verified against the code: **2026-07-24** · version `1.8.0`

---

## 1. Day one: get it running

You need a Linux machine with a desktop session — this project writes to the kernel's
virtual input device, so it cannot be meaningfully developed on Windows or macOS. A VM with
a desktop works. Debian/Ubuntu family with systemd is the target.

```bash
git clone <repo> && cd linuxremoteplayer
cd backend
pip install -r requirements.txt
python run.py
```

`run.py` generates its own HTTPS certificates on first run (a local CA plus a leaf for your
IP) and serves the PWA. Open the printed URL on a phone on the same network, accept the
certificate warning once, and pair with the 6-digit PIN shown on the PC.

**If input does nothing:** your user needs access to `/dev/uinput`. The installer creates a
udev rule for this; in a dev clone you may need to add it yourself or run with elevated
privileges once to confirm that's the cause.

**Environment variables** live in `backend/.env` (never committed — `.env.example` shows
the shape). The ones that matter in dev: `PAIRING_TOKEN`, `KEYBOARD_LAYOUT`
(`us` / `es` / `latam`), `ENABLE_VOICE`, `LRP_MODE`.

## 2. Three things that will bite you

These are not style preferences. Each one has cost someone real time.

**The `.deb` must be built from a native Linux filesystem.** Building from a Windows mount
(`/mnt/...` under WSL) silently truncates files over ~40 KB. The package looks valid, passes
its checks, and ships a broken `app.js`. Build from a fresh clone inside the Linux home
directory — nowhere else.

**The frontend has no build step.** `app.js`, `index.html` and the CSS ship exactly as
written. Don't reach for a bundler; the tooling absence is deliberate (see ARCHITECTURE §7).

**`frontend/skins.css` has a bridge block at the bottom** that remaps Tailwind-ish neutral
utility classes (`border-gray-700`, `text-gray-300`, `bg-blue-600`…) onto theme variables.
The markup predates theming and assumes a dark background. **If you add a neutral utility
class to the markup, bridge it too**, or the light theme — which is the default — breaks
silently for that element.

## 3. How to make a change

This project runs an executor/auditor workflow: **one task, one commit, evidence, stop.**
It applies to human contributors exactly as it does to the AI agents. The rules live in
[`.agents/AGENTS.md`](../.agents/AGENTS.md); the short version:

1. **Read `.agents/CURRENT.md` first.** It's the live state: what's shipped, what's next,
   what's known broken. Don't start from the code.
2. **One task per commit**, prefixed `[T-NN]`. Never mix two concerns in one commit.
3. **`git add` the task's files explicitly.** Never `git add -A` — it sweeps up unrelated
   work in progress.
4. **Evidence or it didn't happen.** Paste the real output of the command that proves your
   change works. "Verified" without output is the one thing that will get a change rejected
   outright.
5. **Say what you did NOT verify.** If you couldn't test something (no hardware, another OS,
   another browser), say so — it becomes an item in `.agents/TESTING.md`. Claiming it works
   is worse than saying you didn't check.
6. **Out-of-scope findings go to `CURRENT.md`, not into your commit.** Noticed a bug next to
   your change? Write it down; don't fix it in the same commit.

Before pushing, run what the build runs:

```bash
python3 scripts/check_css_sync.py    # fails if a CSS class is used but never defined
node --check frontend/app.js         # syntax
python -m py_compile backend/*.py    # syntax
```

There is **no automated test suite** (see ARCHITECTURE §8 — it's the project's largest gap).
Verification is `.agents/TESTING.md`, executed on real hardware. If your change touches
anything a user can see or feel, add a matrix item for it.

## 4. Common changes, and where they go

### Add a streaming site to the launcher

`backend/main.py` → `SUGGESTED_KIOSKS` (~line 117):

```python
{"id": "twitch", "name": "Twitch", "url": "https://twitch.tv", "color": "#9146FF"},
```

`SUGGESTED_KIOSKS_MAP` derives from it automatically, and so does the list of valid targets
handed to the voice model — **the intent model can only ever name a target from this list**,
which is why it can't be tricked into launching arbitrary URLs. Adding an entry here is all
that's needed for both the button and the voice command.

### Add or fix a media key

`backend/main.py` → `MEDIA_KEYS` (~line 138). This is a whitelist: anything not in it is
rejected before reaching the input layer, from both the buttons and the voice path.

### Add or fix a keyboard layout

`backend/input_emulator.py` → `_build_char_keys()` (~line 28). Layouts branch on
`KEYBOARD_LAYOUT`; `es` and `latam` share most of the map and diverge at ~line 74.
Known gaps: `< >` and AltGr bracket characters.

**Test it properly:** open a text editor on the machine and type, from the phone, at
minimum: `hola/mundo @correo.com (test) & "ok" ¿? ; : + * _ =`. Wrong characters fail
silently — nothing errors, the user just gets the wrong letter.

### Change the phone UI

`frontend/index.html` + `frontend/app.js`. No build step, no framework. Mind the bridge
block (§2). Re-run `check_css_sync.py`.

### Change the voice behaviour

The device holds **no AI credentials**. `backend/ai_pipeline.py` only packages audio and
calls the proxy. The actual pipeline — size cap, kill-switch, quota, speech-to-text, intent
extraction — lives in `supabase/functions/ai-proxy/index.ts` and is deployed separately from
the `.deb`. Changing the prompt or the model means deploying that function, not shipping a
release.

## 5. Releasing

Full procedure in [`.agents/AGENTS.md`](../.agents/AGENTS.md). The shape of it: build from a
fresh native clone, verify the artifact by extracting it (not by trusting the build output),
publish the `.deb` plus its checksum to `website/downloads/`, and update `website/latest.json`
— that manifest is what every installed copy polls, so **the checksum must match in all
three places** or clients refuse the update.

`scripts/build_deb.sh` stamps the version into `sw.js`. Without that stamp, installed PWAs
serve stale assets forever. The build aborts if the stamp is missing.

## 6. Where to look things up

| You want | Read |
|---|---|
| The shape of the system, and why | [`ARCHITECTURE.md`](ARCHITECTURE.md) |
| What file holds what (terse index) | [`.agents/APPCORE.md`](../.agents/APPCORE.md) |
| Current state: shipped, next, known broken | [`.agents/CURRENT.md`](../.agents/CURRENT.md) |
| The rules of working here | [`.agents/AGENTS.md`](../.agents/AGENTS.md) |
| What gets tested on real hardware | [`.agents/TESTING.md`](../.agents/TESTING.md) |
| Endpoint reference | the running server's `/docs` — only with `LRP_DEV=true` in `backend/.env`; it is off by default so installations do not publish their API surface on the LAN |
| Why a past decision was made | `ARCHITECTURE.md` §7, then `.agents/CONTEXT.md` |
