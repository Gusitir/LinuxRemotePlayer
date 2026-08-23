# PLAN v1.99 - beta opt-in foundation

```yaml
status: active
goal: entregar una beta numerica 1.99.1 instalable solo por curl, invisible para clientes estables 1.9.1 y capaz de recibir actualizaciones exclusivas del canal beta
assurance: Standard
approval_digest: 2bc3ec3cfac39a205c4a16c0d1f06b85f388d040e34a0d2290e3dd0f9c552f7d
approval_actor: owner
approval_request_ref: none
approved_at: 2026-08-21T23:16:59-05:00
approval_decision_id: D28
approval_source: design SHA-256 2bc3ec3cfac39a205c4a16c0d1f06b85f388d040e34a0d2290e3dd0f9c552f7d
```

No task enters `in-progress` before owner approval and digest registration. Approval does not
authorize push, deploy, release, destructive cleanup or `RUN THE LOOP`; each remains explicit.

## Canonical design approved

Digest boundary: exact UTF-8/LF bytes between `CANONICAL-DESIGN-BEGIN` and
`CANONICAL-DESIGN-END`, excluding marker lines.

<!-- CANONICAL-DESIGN-BEGIN -->
1. Stable installations remain on `1.9.1`, keep their current update behavior and read only the
   stable manifest. The stable manifest is not advanced to a beta version.
2. Beta enrollment is explicit and only occurs through the command shown on the minimal public
   page. No existing stable update button offers or discovers a beta.
3. The beta installer writes a durable beta-channel marker. Beta builds read only the beta
   manifest and may update to later beta builds through their update UI.
4. Technical versions remain numeric `X.Y.Z`: betas use `1.99.1`, `1.99.2`, and so on; stable
   local-first release remains `2.0.0`. Beta identity comes from channel metadata and UI, not a
   version suffix.
5. The public website becomes a minimal beta notice plus one curl installation command. Stable
   manifests, installers and artifacts required by existing installations remain reachable but
   are not advertised as beta.
6. B19 is an owner-accepted residual risk for the unadvertised opt-in beta channel. It remains a
   blocking gate for stable `2.0.0`; channel isolation does not claim to solve signature, downgrade
   or rollback security.
7. This milestone changes distribution/channel behavior only. It does not integrate local STT,
   Needle 2, remove cloud/licensing, select models or change LinuxRemotePlayer runtime features.
8. The next milestone tests models directly in installable betas with a fixed 18-command checklist
   per model: 12 Spanish and 6 English. The old 60-audio laboratory is reusable tooling, not a gate.
<!-- CANONICAL-DESIGN-END -->

## Scope

- In scope: stable/beta channel contract, numeric beta versioning, beta installer/manifest,
  minimal website, beta artifact, channel-isolation tests and owner field validation.
- Non-goals: STT/Needle integration, model selection, cloud/license removal, B19 remediation for
  beta, stable manifest bump, automatic stable-to-beta migration, merge, push or deploy.
- Development method: smallest vertical channel slice; deterministic gates before owner field test.
- Closure evidence: stable manifest unchanged, beta manifest/artifact coherent, stable update check
  cannot see beta, curl enrolls beta, beta update check reads beta channel, package SHA matches and
  `TST-BETA-CHANNEL-001` is fresh.

## Workspace and orchestration

- Product work uses an isolated worktree approved before dispatch; do not write in dirty `main`.
- `INGENIERO-PRODUCTO` coordinates and audits; Workers implement bounded product tasks.
- Each Engineer may use at most 2 LUNA-MAX Workers; global total is 4. Product roster: 2/2 sessions
  registered, active 0; global roster: 2/4, active 0. No new Product Workers are permitted; existing
  sessions may be reused.
- Architect-only DeepSeek slots are not planned for this milestone.
- INGENIERO-CONTROL updates `main` control state only from accepted capsules while product writers
  are stopped. Product branches never write or import `.agents`.
- CAVEMAN applies to every brief, capsule and report.

## Tasks

### T-117 - Implement the stable/beta channel contract

- Status: apto
- Architect: principal Architect; owns channel design and persistent-format approval.
- Engineer: INGENIERO-PRODUCTO.
- Worker: one LUNA-MAX Worker after slot authorization.
- Depends on: none; dispatch was blocked until the approval digest was current.
- Objective: make beta channel selection explicit and persistent without changing installed 1.9.1.
- Non-goals: website redesign, artifact publication, model integration or stable update behavior.
- Allowed scope: `backend/main.py`, `frontend/app.js`, `backend/.env.example`, focused tests/docs;
  exact files must be reduced by the Engineer after inspection.
- Acceptance: stable/default resolves only stable manifest; beta marker resolves only beta manifest;
  API/UI expose channel honestly; unknown values fail to stable or closed per approved threat review;
  existing 1.9.1 binaries require no change and cannot discover beta.
- Approved channel contract: `LRP_CHANNEL=stable|beta`; absent/empty/invalid normalizes to `stable`
  and invalid values log a warning. Stable reads `UPDATE_MANIFEST_URL` or
  `https://www.linuxremoteplayer.com/latest.json`. Beta ignores the stable override and reads
  `BETA_UPDATE_MANIFEST_URL` or `https://www.linuxremoteplayer.com/beta/latest.json`.
- Evidence: protocol round trip, config persistence test, focused diff and audit capsule. Verdict:
  APTO. Fresh gates after final change: system Python pytest 15 passed; full runtime round trips
  stable->stable, beta->beta, invalid->stable PASS; `node --check` PASS; CSS sync PASS; `git diff
  --check` PASS. Changed exactly `backend/main.py`, `frontend/app.js`, `backend/.env.example` and
  `tests/test_beta_channel.py` in `codex/beta-foundation`; commit `298bb39`.
- Gates: Python syntax/tests added for channel selection; `node --check frontend/app.js`;
  `git diff --check`; reference sweep for manifest URLs and update labels.
- Human checks: none.
- Audit: independent model audit by principal Architect, separate model/context from execution.
- Worker result: `DONE_WITH_CONCERNS` from `ses_fd84c189dffeo3efi7lMZtZ6HS` (`gpt-5.6 LUNA MAX`),
  accepted by independent model audit. Concern resolved by Architect full runtime import using the
  root backend venv with `PAIRING_TOKEN` guard. Product Worker slot released (Product 0/2, global
  0/4).
- Risks: channel crossover, stale config, hidden fallback to beta and UI mislabeling.
- STOP conditions: change to stable manifest contract, destructive migration, ambiguous persistence or
  any path allowing stable clients to select beta without curl enrollment.
- Invalidated by: channel marker or manifest contract change.

### T-118 - Build the beta installer and manifest

- Status: apto
- Architect: principal Architect.
- Engineer: INGENIERO-PRODUCTO.
- Worker: one LUNA-MAX Worker after slot authorization.
- Depends on: T-117 apto.
- Objective: create an explicit beta installer and beta manifest isolated from stable distribution.
- Non-goals: deploy, stable manifest edit, signature/rollback remediation or model payload.
- Allowed scope: `website/beta/install.sh`, `website/beta/latest.template.json`,
  `scripts/build_deb.sh`, `tests/test_beta_distribution.py`,
  `tests/fixtures/beta-manifest.json`; stable `website/latest.json` is read-only.
- Acceptance: beta installer contract validates numeric version/SHA and writes the channel marker;
  generated root updater parses only `LRP_CHANNEL` as a literal enum without source/eval, uses only
  hardcoded official stable/beta URLs and preserves beta across upgrade. No live beta manifest is
  created before T-120; stable manifest remains byte-identical.
- Evidence: template/fixture checks, generated updater extraction, native WSL test package,
  updater channel matrix, stable-manifest hash and diff. Verdict: APTO after correction cycle 1.
  Integrated T-117+T-118 package was built/extracted in a native WSL clone. Installer marker precedes
  `lrp-setup`; `scripts/install.sh` `chown -R` precedes service restart. Device validation remains
  required by T-121, not T-118. Fresh gates: 21 pytest PASS; full runtime import PASS; node PASS; CSS
  PASS; `bash -n` installer/build PASS on Windows+WSL; distribution parser/dedup 6 tests PASS;
  stable `website/latest.json` unchanged with hash/blob `700a8878a2dd743ea7ca4ff73b8c592b3bb92727`;
  no live beta latest; integrated `.deb` SHA `026669a8d853c624c10ea1b991a78ecbe391401a132f1a67fafcb5c7445178f2`
  matched sidecar; control postinst/updater syntax and hardcoded URLs PASS; package excludes `.env`.
  Changed exactly `website/beta/install.sh`, `website/beta/latest.template.json`,
  `scripts/build_deb.sh`, `tests/test_beta_distribution.py` and `tests/fixtures/beta-manifest.json`;
  commit `607bf04`.
- Gates: shell syntax; focused distribution tests; generated updater channel matrix; package build
  and extraction in native WSL clone; stable-manifest equality; `git diff --check`.
- Human checks: none.
- Audit: independent model audit by principal Architect, separate model/context from execution.
- Worker result: `DONE_WITH_CONCERNS` from `ses_fd82b70b4ffe1xKKtLCNow4QzW` (`gpt-5.6 LUNA MAX`),
  accepted by independent model audit. Concerns resolved by the integrated package/runtime checks
  above. Product roster remains 2/2 sessions registered, active 0; global roster 2/4, active 0.
- Risks: root installer supply chain, wrong package channel, filename/version drift and WSL build.
- STOP conditions: stable manifest modification, live beta manifest before T-120, source/eval or URL
  override read by root updater, unsigned risk presented as solved, checksum mismatch, package
  version outside `X.Y.Z` or build outside native Linux filesystem.
- Invalidated by: T-117 NO APTO or version/channel contract change.

### T-119 - Reduce the public website to beta enrollment

- Status: apto
- Architect: principal Architect; approves public wording.
- Engineer: INGENIERO-PRODUCTO.
- Worker: one LUNA-MAX Worker after slot authorization.
- Depends on: T-118 apto.
- Objective: show only a concise beta notice and the explicit curl enrollment command.
- Non-goals: remove required artifacts/manifests, claim stable readiness or advertise model results.
- Allowed scope: `website/index.html`, `website/en/index.html`, `tests/test_beta_landing.py`.
- Acceptance: ES/EN landing surfaces show beta status, risk/expectation and one installer command;
  no purchase/premium claims remain visible; stable and beta distribution URLs remain reachable.
- Evidence: rendered desktop/mobile screenshots, DOM/link sweep and text/reference audit. Verdict:
  APTO after correction cycles 1-2. Fresh gates: 26 cumulative pytest PASS; node site/app PASS; CSS
  sync PASS; `git diff --check` PASS; protected stable manifests/installers/downloads/JS/Vercel
  unchanged; no inline CSS; namespaced beta-landing CSS; exactly one command and one language link;
  Edge/CDP desktop 1440x900 and mobile 390x844 with `mobile=true`, `touch=true`, `scale=3`,
  `scrollWidth==innerWidth`; screenshots external temp. Changed exactly `website/index.html`,
  `website/en/index.html`, `website/style.css` and `tests/test_beta_landing.py`; commit `be96e35`.
- Gates: static link/path checks; HTML/JS syntax where available; mobile/desktop render inspection;
  `git diff --check`.
- Human checks: owner wording approval before deploy.
- Audit: independent model audit by principal Architect, separate model/context from execution.
- Worker result: `DONE` from reused Product Worker `ses_fd82b70b4ffe1xKKtLCNow4QzW` (`gpt-5.6 LUNA
  MAX`); accepted by independent model audit. Product roster 2/2 sessions registered, active 0;
  global roster 2/4, active 0; no new Product Workers permitted.
- Risks: accidental deletion of OTA assets, stale localized page and misleading public status.
- STOP conditions: installer/manifests become unreachable, hidden purchase path remains or public copy
  claims local functionality not yet implemented.
- Invalidated by: installer URL or beta disclosure change.

### T-120 - Produce and audit beta 1.99.1

- Status: apto
- Architect: principal Architect.
- Engineer: INGENIERO-PRODUCTO.
- Worker: one LUNA-MAX Worker for release preparation after slot authorization.
- Depends on: T-117 apto; T-118 apto; T-119 apto.
- Objective: build an internally coherent 1.99.1 beta artifact without publishing it automatically.
- Non-goals: deploy, push, stable release, local AI or model testing.
- Allowed scope: `VERSION`, `CHANGELOG.md`, `website/beta/latest.template.json`,
  `website/beta/latest.json`, `website/beta/downloads/linuxremoteplayer_1.99.1_all.deb`,
  its `.sha256` sidecar and `tests/test_beta_release.py`; source `frontend/sw.js` is read-only.
- Acceptance: source, Debian version, service-worker cache, beta manifest, artifact name/metadata and
  SHA agree; stable latest remains 1.9.1; artifact identifies beta channel in UI/config.
- Evidence: fresh-clone build capsule, extracted artifact inventory and independent SHA. Verdict:
  APTO after correction cycle 1. VERSION/package are `1.99.1`; 29 tests PASS; node/bash/CSS/diff
  PASS; source service-worker placeholder unchanged and package service worker stamped `lrp-1.99.1`;
  stable latest/downloads/install byte-identical; package metadata is `linuxremoteplayer`/`all`;
  `.env` absent; manifest URL exact; artifact/sidecar/manifest SHA all
  `8d4a19834eca05eda0e3f8b9c77817e6baaa19fb1bd823e30b5a726b6cb9c894`; commit `e838279`; no push,
  deploy or release at audit time. Files: `VERSION`, `CHANGELOG.md`, beta template/live manifest, beta `.deb`+sidecar,
  `tests/test_beta_release.py` and expanded `tests/test_beta_distribution.py`.
- Gates: full available syntax/CSS gates; native WSL build; artifact/source comparison;
  beta/stable manifest assertions; `git diff --check`.
- Human checks: none until owner installs.
- Audit: independent model audit by principal Architect, separate model/context from execution.
- Worker result: `DONE` from reused Product Worker `ses_fd82b70b4ffe1xKKtLCNow4QzW` (`gpt-5.6 LUNA
  MAX`); accepted by independent model audit. Product roster 2/2 sessions registered, active 0;
  global roster 2/4, active 0; no new Product Workers permitted.
- Risks: version coupling, stale service worker and accidental stable-channel publication.
- STOP conditions: any stable manifest bump, dirty release clone, artifact mismatch or missing beta mark.
- Invalidated by: upstream task NO APTO or release metadata drift.

### T-121 - Validate opt-in and channel isolation

- Status: blocked
- Architect: principal Architect; issues milestone verdict.
- Engineer: INGENIERO-PRODUCTO; prepares G3 capsule.
- Worker: none unless an audited correction brief is authorized.
- Depends on: T-120 apto.
- Objective: prove stable cannot discover beta and an explicitly enrolled beta reads beta updates.
- Non-goals: advertise, deploy beyond owner action, model testing or close B19.
- Allowed scope: installed test systems and distribution endpoints read-only; corrections require a
  new bounded task.
- Acceptance: existing 1.9.1 reports no beta update; curl installs 1.99.1; installed beta persists
  channel after restart; beta check reads beta manifest; stable manifest remains 1.9.1.
- Evidence: literal endpoint responses, installed package/version/channel, service health and UI.
- Gates: protocol round trip stable->stable and beta->beta; package verification; endpoint/link sweep.
- Human checks: `TST-BETA-CHANNEL-001` must be `[OK]`.
- Audit: independent model audit by principal Architect, separate model/context from execution.
- Worker result: none; not dispatched.
- Risks: cache leakage, wrong manifest, beta marker loss and owner-accepted B19 exposure.
- STOP conditions: stable sees beta, beta falls back silently to stable, field package differs from
  artifact or required human evidence is unavailable.
- Invalidated by: delayed upstream NO APTO, endpoint drift or deployment mismatch.

## Closure gate

- [ ] Owner approval digest is current and T-117..T-121 have required verdicts.
- [ ] Stable `latest.json` still advertises 1.9.1 and stable clients cannot discover beta.
- [ ] Curl is the only enrollment path and beta channel persists across restart/update.
- [ ] Beta manifest, package, VERSION, service worker and SHA agree.
- [ ] Website is minimal and distribution assets remain reachable.
- [ ] `TST-BETA-CHANNEL-001` is fresh.
- [ ] B19 is recorded as accepted beta risk and remains a stable 2.0.0 blocker.
- [ ] Main v3 control state agrees with accepted capsules, repository, artifact and Git.
- [ ] Push, deploy and branch disposition remain separate owner actions.
