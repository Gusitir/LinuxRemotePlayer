# CURRENT — estado vivo v3

```yaml
version: 3
updated_at: 2026-10-17T07:35:00-05:00
source_commit: 98bb9f1
product_branch_head: 50da3ca
dirty: true
dirty_items:
  - AGENTS.md (control-plane shim neutral header)
  - .agents/AGENTS.md (D48 Zero-IO protocol, flash workers, test priority, D49 guided briefs)
  - .agents/APPCORE.md (REINDEX to 2.0.0-dev appliance & ISO/OTA components)
  - .agents/BUGS.md (H22, L1, L2, ASTRA-01..04, BUG-WS-HEARTBEAT resolved)
  - .agents/WORKFLOW.md (D48 Zero-IO protocol, flash workers, gates, D49 guided briefs)
  - .agents/PLAN.md (roadmap updated: LRP-OS-APPLIANCE, ISO-FACTORY, GATE-OTA Cerrado APTO)
  - .agents/PLAN_PH21.md (neutral engineer role)
  - .agents/PLAN_v1.99.2-debian-htpc-foundation.md (closed plan)
  - .agents/PLAN_v2.0-appliance.md (completed plan: T-132..T-142 APTO, G4 APTO)
  - .agents/CONTEXT.md (append-only through D50)
  - .agents/CURRENT.md (phase closure state)
  - .agents/INDEX.md (navigation updated to active state)
  - .agents/TESTING.md (checks updated with verified appliance v2.0 IDs)
  - AUDITORIA_ASTRA.md (resolution summary for ASTRA-01..04 appended)
  - NEWUI.MD (Section 12 appended with final D43 implementation details)
  - docs/ARCHITECTURE.md (updated with local CPU voice and system platform)
  - docs/DEVELOPING.md (updated with 272-test automated pytest suite)
  - .agents/design/skins2/lochi.png (pre-existing untracked)
assurance: Standard
active_job: CLOSE
active_plan: PLAN_v2.0-appliance.md
active_task: none (PLAN_v2.0-appliance.md G4 APTO)
last_verdict: APTO
verdict_scope: PLAN_v2.0-appliance.md cerrado formalmente con G4 APTO (T-132..T-142 APTO; T-140 PWA 2.0 y CSS sync exit 0, T-141 ISO factory live-build exit 0, T-142 Ed25519 OTA + 45s rollback exit 0; 59/59 tests v2.0 passing; check_css_sync.py exit 0, node --check exit 0, bash -n limpio)
next_action: Arquitecto reporta cierre de fase G4 APTO al dueño; en espera de autorización de commit de control y push/deploy.
```

## Blockers

- Cleanup of external WSL audit clones remains unauthorized.
- T-130 pushed to `origin/main` as `98bb9f1` with Vercel success; no further push/deploy without owner authorization.
- T-131 needs artifact/manifest reconciliation (worktree sidecar `25ea41…` vs manifest `a0b54…`), owner visual rollback confirmation and final phase audit.
- Public OTA 1.99.1->1.99.2 passed with channel/config/token/CA retained; legacy uinput migration verified on HTPC.
- One abrupt physical reset occurred after launching Netflix. Journal ended without orderly shutdown,
  panic, OOM, thermal event, NVIDIA Xid or pstore evidence; a 90-second monitored retry did not reproduce.

## Fresh evidence

- T-117, T-118, T-119, T-120 and T-121 are `APTO` under independent model audit; milestone
  assurance is `Standard`.
- Stable `1.9.1` remains isolated; beta `1.99.1` is published with SHA
  `8d4a19834eca05eda0e3f8b9c77817e6baaa19fb1bd823e30b5a726b6cb9c894`.
- `main`/`origin/main` are at `98bb9f1` (T-130 rebuild with physical fixes); Vercel reported success and public beta serves `1.99.2` amd64.
- Branch disposition proposal: keep `codex/beta-foundation`.
- Google Drive receipt: bundle `backups/linuxremoteplayer-savepoint-beta-foundation-20260823.bundle`,
  size `13079844`, SHA256 `ebcf392cb5c521e1b07f4e9264c2838a994c14769d32e80906260ffb2ef5f0c4`;
  `git bundle verify` reports complete history and 14 refs. Zip
  `backups/linuxremoteplayer-savepoint-beta-foundation-20260823.zip`, size `4144496`, SHA256
  `f78fdb421d355321596ef503c0ab59b2df3666f149f86a037e95de3f566eb1ec`; contains all tracked files
  at `407bb66` plus pre-existing `lochi.png`, with no `.env` or `.git`. No absolute Drive path is
  persisted.

## Current facts

- Closed plan: `archive/PLAN_v1.99-beta-foundation.md`; archived completed testing:
  `archive/TESTING_beta-foundation_1.99.1.md`.
- Live `TESTING.md` is rotated for DEBIAN-FOUNDATION. STT/Needle checks are deferred.
- Owner-accepted residuals: `TST-DEVICE-001`, `TST-STT-001` and `TST-OTA-001`.
- Backup state is `complete`; receipt and hashes are recorded in `CONTEXT.md`.

- T-122 preflight, T-123 NVIDIA bootstrap and T-124 managed Xorg/Openbox session are `APTO` on
  `codex/debian-foundation`. T-124 physical resume exit 0 verified LightDM, non-root Openbox and the
  NVIDIA renderer. T-125 installer/service migration is `APTO` (10/10 focused, 135/135 full); T-126
  Firefox ESR kiosk is `APTO`; T-127 platform services are `APTO` after physical reboot and repeat
  apply. T-128 rollback/reapply round trip is `APTO`; real CA attachment and local HTTPS now pass on
  the HTPC. T-129 active truth is `APTO`. T-130 local package install, setup, pairing, apps, CA and
  service pass. Latest Windows and native WSL suites are 205/205; package `dpkg -V` passes. UFW
  materializes 8000/tcp+5353/udp, Firefox suppresses crash restore and HDMI is selected at 100%.
  Vercel deploy for `98bb9f1` is success; public artifact independently matches SHA `a0b54c85...`;
  stable manifest remains 1.9.1.
- D35 one-command unattended flow, legacy uinput migration, debt removal and rebuilt artifact SHA reconciliation committed in worktree `95490ce`; full suite `207/207` passed, triple-match SHA256 verified, G4 approved.
- D41 master plan `PLAN_v2.0-appliance.md` finalizado y aprobado (digest `2120e72d...`); línea base Core i5-3470 / Intel HD 2500 (bare-metal HTPC online en 192.168.0.246); onboarding Wi-Fi dual (teclado / hotspot automático); parada obligatoria previa a T-140; T-132 APTO; T-133 READY.
- `AUDITORIA_ASTRA.md` mapped into plan: T-134 (ASTRA-01 root ownership & ASTRA-02 WS token revocation) and T-135 (ASTRA-03 async voice WS & ASTRA-04 cert expiry).

## Open findings

- Debian HTPC Foundation closed (T-122..T-131 APTO).
- T-132 APTO: Immediate status panel launch + TV cursor scaling verified (commit `faafd39`).
- T-133 APTO: Hardware-agnostic network (wildcard DHCP, watchdog) & dynamic GPU udev loader verified (227/227 tests, commit `9898f6a`).
- T-134 APTO: Critical security mitigation (ASTRA-01 root ownership / /var/lib isolation & ASTRA-02 WS token revocation) verified (232/232 tests, commit `610194e`).
- T-135 APTO: Resilience mitigation (ASTRA-03 async voice WS & ASTRA-04 cert expiry / RTC safeguard) verified (235/235 tests, commit `ebfdf82`).
- T-136 APTO: System settings platform API module (`/api/system/*`) & Kiosk VA-API optimization verified (241/241 tests, commit `b988882`).
- T-137 APTO: Kiosk TV OSD system settings tab & dual-mode Wi-Fi onboarding verified (245/245 tests, commit `415524b`).
- T-138 APTO: Local STT benchmark on minimum CPU (whisper.cpp AVX1) verified on bare-metal i5-3470 (ggml-base-q5_1, 2.6s latency, 136.9 MB RAM peak; 254/254 tests, commits `fad6e33`, `45ab922`).
- T-139 APTO: Local NLU intent engine (`backend/local_intent.py`, latencia 0.01-0.25ms, allowlist estricta) & Supabase proxy removal verified (263/263 tests, commit `6099d50`).
- T-140 APTO: Rediseño Mobile App 2.0 PWA y remediación UI completada (tarjetas squircle 68x68 full-size, contraste multi-skin SVG, modo edición, chip 'Con Voz', CSS sync; commit `964f66f`).
- T-141 APTO: LRP OS bootable USB ISO factory (receta live-build Debian 13 minimal, exclusión de USB y zram; commit `b1f8d65`).
- T-142 APTO: Firma criptográfica OTA Ed25519 en manifiestos, protección anti-downgrade y auto-rollback transaccional de 45s; riesgo B19 cerrado (commit `50da3ca`).
- G4 APTO: Dictamen unánime del Auditor de fase (`ae7b054f...`) y ratificación del Arquitecto; 59/59 tests passing en las 9 suites v2.0; check_css_sync.py exit 0, node --check exit 0, bash -n exit 0; milestone PLAN_v2.0-appliance.md cerrado con éxito.
- D48/D49/D50 active: Zero-IO en modelos pesados, workers flash persistentes, briefs guiados unitarios y cierre formal de appliance v2.0.
