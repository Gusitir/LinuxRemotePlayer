# CURRENT — estado vivo v3

```yaml
version: 3
updated_at: 2026-08-22T23:52:24-05:00
source_commit: 8e27512
product_branch_head: 4bdf5da
dirty: true
dirty_items:
  - .agents/CURRENT.md (RUN THE LOOP control correction)
  - .agents/TESTING.md (TST-BETA checks correction)
  - .agents/design/skins2/lochi.png (pre-existing untracked)
assurance: Standard
active_job: RUN THE LOOP
active_plan: PLAN_v1.99-beta-foundation.md
active_task: T-121
last_verdict: APTO
verdict_scope: T-120 independent model audit
next_action: Owner runs public curl on HTPC and records TST-BETA-CHANNEL-001
```

## Blockers

- T-121 remains blocked on owner HTPC evidence for TST-BETA-CHANNEL-001.
- TST-BETA-UPDATE-002 is deferred until 1.99.2 and does not block BETA-FOUNDATION closure because
  the plan requires beta-manifest reading, not a future beta build.
- Cleanup of external WSL audit clones is not authorized.

## Fresh evidence

- `main` head/pushed: `8e27512`; beta branch head/pushed: `4bdf5da`.
- Product commits on main: `942fab2`, `afdcfd3`, `bedc94b`, `28be028`, LF fix `8e27512`; beta
  equivalents: `298bb39`, `607bf04`, `be96e35`, `e838279`, `4bdf5da`.
- Vercel status `success` for main `8e27512` at `2026-08-23T04:48:12Z`.
- Public endpoints verified: ES root and `/en/` beta pages; stable `/latest.json` 1.9.1;
  `/beta/latest.json` 1.99.1; `/beta/install.sh` reachable.
- Independently downloaded beta `.deb` SHA matches manifest:
  `8d4a19834eca05eda0e3f8b9c77817e6baaa19fb1bd823e30b5a726b6cb9c894`.
- 29 tests PASS after `.gitattributes` LF fix in `8e27512`.
- T-121 remains blocked only by `TST-BETA-CHANNEL-001`; no human field verdict recorded.
- External WSL audit clones: `lrp-t118-build-3`, `lrp-t118-integrated-1`, `t120-native-20260822-5`.

## Current facts

- Stable channel remains LinuxRemotePlayer `1.9.1`; beta channel is deployed as numeric `1.99.1`.
- Stable and beta manifests/installers are separate; stable `/latest.json` remains unchanged.
- Main and beta branch changes are pushed and website deployment succeeded.
- `lochi.png` is the only pre-existing untracked item; cleanup remains unauthorized.

## Open findings

- Owner must execute and record `TST-BETA-CHANNEL-001` on the HTPC. `TST-BETA-UPDATE-002` is
  deferred and not a BETA-FOUNDATION blocker.
