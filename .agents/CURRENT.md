# CURRENT — estado vivo v3

```yaml
version: 3
updated_at: 2026-08-23T23:52:55-05:00
source_commit: f65ea58
product_branch_head: 4bdf5da
dirty: true
dirty_items:
  - .agents/APPCORE.md (CLOSE release-surface refresh)
  - .agents/CONTEXT.md (append-only D30 milestone close)
  - .agents/CURRENT.md (CLOSE compact state)
  - .agents/INDEX.md (closed-plan navigation)
  - .agents/PLAN.md (closed-plan link)
  - .agents/PLAN_PH21.md (closed-plan link)
  - .agents/PLAN_v2.0-ph21-stt.md (closed-plan link)
  - .agents/TESTING.md (rotated BETA-STT matrix)
  - .agents/archive/PLAN_v1.99-beta-foundation.md (closed plan)
  - .agents/archive/TESTING_beta-foundation_1.99.1.md (completed testing snapshot)
  - .agents/design/skins2/lochi.png (pre-existing untracked)
assurance: Standard
active_job: CLOSE
active_plan: none
active_task: none
last_verdict: APTO
verdict_scope: BETA-FOUNDATION independent model audit
next_action: Architect commits close, creates the authorized Google Drive bundle/zip savepoint, records hashes, then starts PLAN BETA-STT
```

## Blockers

- Backup finalization remains pending: authorized Google Drive savepoint bundle and zip must be
  created and hashed.
- Cleanup of external WSL audit clones remains unauthorized.

## Fresh evidence

- T-117, T-118, T-119, T-120 and T-121 are `APTO` under independent model audit; milestone
  assurance is `Standard`.
- Stable `1.9.1` remains isolated; beta `1.99.1` is published with SHA
  `8d4a19834eca05eda0e3f8b9c77817e6baaa19fb1bd823e30b5a726b6cb9c894`.
- `main`/`origin/main` were synced at `f65ea58` before current dirty control edits; beta branch and
  origin remain at `4bdf5da`. Push/deploy are already done.
- Branch disposition proposal: keep `codex/beta-foundation`.

## Current facts

- Closed plan: `archive/PLAN_v1.99-beta-foundation.md`; archived completed testing:
  `archive/TESTING_beta-foundation_1.99.1.md`.
- Live `TESTING.md` is rotated for BETA-STT. `TST-BETA-UPDATE-002` is deferred until `1.99.2`;
  `TST-BETA-MODEL-001` is upcoming with 12 ES + 6 EN commands.
- Owner-accepted residuals: `TST-DEVICE-001`, `TST-STT-001` and `TST-OTA-001`.
- Backup state is `pending`; savepoint names are
  `linuxremoteplayer-savepoint-beta-foundation-20260823.bundle` and
  `linuxremoteplayer-savepoint-beta-foundation-20260823.zip`. No absolute path is persisted.

## Open findings

- Architect must finalize the close commit and authorized Google Drive savepoint before starting
  PLAN BETA-STT.
