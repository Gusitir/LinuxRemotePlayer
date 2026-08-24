# CURRENT — estado vivo v3

```yaml
version: 3
updated_at: 2026-08-23T23:59:01-05:00
source_commit: 407bb66
product_branch_head: 4bdf5da
dirty: true
dirty_items:
  - .agents/APPCORE.md (backup receipt metadata)
  - .agents/CONTEXT.md (append-only backup receipt correction)
  - .agents/CURRENT.md (backup receipt state)
  - .agents/INDEX.md (backup receipt metadata)
  - .agents/design/skins2/lochi.png (pre-existing untracked)
assurance: Standard
active_job: PLAN
active_plan: none
active_task: none
last_verdict: APTO
verdict_scope: BETA-FOUNDATION independent model audit
next_action: Architect plans BETA-STT direct model beta
```

## Blockers

- Cleanup of external WSL audit clones remains unauthorized.
- Model inventory and design choices remain unresolved before BETA-STT planning.

## Fresh evidence

- T-117, T-118, T-119, T-120 and T-121 are `APTO` under independent model audit; milestone
  assurance is `Standard`.
- Stable `1.9.1` remains isolated; beta `1.99.1` is published with SHA
  `8d4a19834eca05eda0e3f8b9c77817e6baaa19fb1bd823e30b5a726b6cb9c894`.
- `main`/`origin/main` are at verified close commit `407bb66`; beta branch and
  origin remain at `4bdf5da`. Push/deploy are already done.
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
- Live `TESTING.md` is rotated for BETA-STT. `TST-BETA-UPDATE-002` is deferred until `1.99.2`;
  `TST-BETA-MODEL-001` is upcoming with 12 ES + 6 EN commands.
- Owner-accepted residuals: `TST-DEVICE-001`, `TST-STT-001` and `TST-OTA-001`.
- Backup state is `complete`; receipt and hashes are recorded in `CONTEXT.md`.

## Open findings

- Architect plans BETA-STT direct model beta after resolving model inventory and design choices.
