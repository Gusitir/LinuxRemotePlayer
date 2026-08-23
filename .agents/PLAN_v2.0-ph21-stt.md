# PLAN v2.0 - PH21 STT local

> Draft superseded before approval by [`PLAN_v1.99-beta-foundation.md`](PLAN_v1.99-beta-foundation.md).
> No task in this draft was dispatched. Its laboratory evidence remains reusable, not gating.

```yaml
status: blocked
goal: comparar whisper.cpp base-q5_0 y small-q5_0 con 60 audios ES/EN reales en Linux HTPC y emitir una decision reproducible sin modificar el runtime 1.9.1
assurance: Standard
approval_digest: pending
approval_actor: owner
approval_request_ref: none
approved_at: pending
approval_decision_id: pending
approval_source: pending
```

No task may enter `in-progress` until the owner approves this exact design and its digest is
recorded. Approval does not authorize merge, push, deploy, release, destructive cleanup or product
integration.

## Canonical design pending approval

Digest boundary: exact UTF-8/LF bytes between `CANONICAL-DESIGN-BEGIN` and
`CANONICAL-DESIGN-END`, excluding the marker lines.

<!-- CANONICAL-DESIGN-BEGIN -->
1. Preserve `main` as the factual 1.9.1 product and keep PH21 restricted to `lab/` plus its
   laboratory documentation.
2. Treat `codex/PH21-stt` commits T-88 through T-110 as an existing pre-v3 baseline not yet
   audited under this plan. Audit them before requesting corrections; do not reimplement passing
   work.
3. The v3 control plane on `main` is authoritative. Legacy `.agents` changes from the PH21 branch
   must not overwrite it during future integration.
4. External binary, model weights, human audio and benchmark results remain outside Git. Exact
   origin, version, license and checksum are required before they count as evidence.
5. Compare multilingual whisper.cpp `base-q5_0` and `small-q5_0` on the same 60-case ES/EN corpus
   and the same physical Linux HTPC. Fixtures and synthetic observations never select a winner.
6. A decision may select one candidate, select profiles by hardware, or return no winner. Missing
   evidence remains `BLOCKED`; gates are not relaxed to force a result.
7. PH21 does not integrate STT into backend/frontend, remove cloud/licensing, alter packaging or
   publish hardware claims. Those require later approved phases.
8. Branch integration and any control-plane reconciliation occur only after task evidence and a
   separate explicit Git authorization.
<!-- CANONICAL-DESIGN-END -->

## Existing baseline

- Base/head: `1999a845` -> `580847e8`, 23 commits `T-88` through `T-110`.
- Product runtime diff: none under `backend/`, `frontend/`, `scripts/`, `website/`, `supabase/`,
  `VERSION`, `CHANGELOG.md` or `README.md`.
- Laboratory: 60-case textual corpus, inventory, metrics, whisper.cpp adapter, decision logic,
  HTTPS recorder and physical benchmark kit.
- Fresh read-only gate: 297 tests passed on Windows; this validates code behavior, not Linux/HTPC
  performance or a candidate decision.
- Readiness: `false`; binary, weights, human audio and target HTPC inventory are absent.
- Dirty worktree item: `INTRUCCIONES PARA DEEPSEEK.md`, untracked and owner-controlled.
- Git risk: `codex/v2-integration` and `codex/PH21-stt` currently point to the same head.

## Scope

- In scope: audit the existing laboratory, pin external assets, capture/validate the external
  corpus, benchmark both candidates on target hardware, produce a decision and audit PH21.
- Non-goals: production STT integration, Needle/actions, backend/frontend changes, cloud/license
  removal, OTA B19, packaging, website claims, merge, push, deploy or release.
- Development method: evidence-first; reuse existing tested work, then smallest corrections only.
- Closure evidence: clean task diffs, 297+ tests, external asset manifest, 60 validated WAVs,
  Linux inventory, comparable base/small reports, deterministic decision, reference sweep and
  `TST-STT-001`.

## Dependencies and workspace

- Writable product workspace: `.worktrees/PH21-stt`, branch `codex/PH21-stt`.
- `main` control-plane dirty state is unrelated and must not be staged or copied into PH21.
- PH21 never writes `.agents`. After each completed audit, INGENIERO-CONTROL may update the v3
  control state on `main` from the accepted capsule while all product writers are stopped.
- Tasks are serialized unless the Engineer proves disjoint write-sets and receives worker slots.
- Each Engineer may use at most 2 LUNA-MAX Workers; global total is 4. No slots are allocated yet.
- Architect-only DeepSeek slots are unavailable to Engineers and are not planned for PH21.
- CAVEMAN applies to all briefs, capsules and reports.

## Tasks

### T-111 - Audit existing PH21 baseline

- Status: blocked
- Architect: principal Architect; owns design and dispositions.
- Engineer: INGENIERO-PRODUCTO; owns orchestration and independent audit preparation.
- Worker: none unless a correction brief is approved after findings.
- Depends on: none; dispatch remains blocked until the owner approval digest is current.
- Objective: audit T-88..T-110 as delivered baseline and classify every blocking defect.
- Non-goals: reimplementation, merge, control-plane rewrite or physical benchmark.
- Allowed scope: `lab/**`, `docs/superpowers/specs/2026-08-14-stt-kit-minimal.md`, Git range
  `1999a845..580847e8` read-only; corrections require a new bounded write-set.
- Acceptance: commit/task map, diff review, license/provenance review, isolation proof and finding
  dispositions exist; no production path depends on `lab/`.
- Evidence: audit capsule with base/head, changed files, diff, gates, risks and open questions.
- Gates: `python -m pytest -p no:cacheprovider lab/stt/tests lab/stt/kit/test_kit.py`;
  `git diff --check`; product-path diff against `main` must be empty.
- Human checks: none.
- Audit: independent model audit by the principal Architect, separate model/context from execution.
- Worker result: none; not dispatched.
- Risks: 23 pre-v3 commits and mixed legacy `.agents` changes in the branch.
- STOP conditions: product runtime diff, unverifiable provenance, unsafe path or design drift.
- Invalidated by: canonical design or source range change.

### T-112 - Pin runtime, weights and licenses

- Status: blocked
- Architect: principal Architect.
- Engineer: INGENIERO-PRODUCTO.
- Worker: one LUNA-MAX Worker after slot authorization.
- Depends on: T-111 apto.
- Objective: make external whisper.cpp base/small assets identifiable and reproducible.
- Non-goals: commit binaries/weights, alter product installer or select a winner.
- Allowed scope: `lab/stt/WHISPER_CPP_SETUP.md`, `lab/stt/licenses.json`,
  `lab/stt/kit/prepare.sh`, focused tests; external asset directory is evidence only.
- Acceptance: runtime commit/version, base/small model identity, q5_0 process, license,
  redistribution status and SHA-256 are recorded; no implicit product download exists.
- Evidence: external manifest plus command/output and focused test capsule.
- Gates: focused prepare/whisper tests; full PH21 Python suite; `git diff --check`.
- Human checks: none.
- Audit: independent model audit by the principal Architect, separate model/context from execution.
- Worker result: none; not dispatched.
- Risks: upstream drift, code/weight license mismatch and large external downloads.
- STOP conditions: copyleft/non-commercial ambiguity, checksum mismatch, network side effect outside
  explicit preparation or product-path write.
- Invalidated by: T-111 NO APTO or runtime/model identity change.

### T-113 - Capture and validate the real corpus

- Status: blocked
- Architect: principal Architect.
- Engineer: INGENIERO-PRODUCTO.
- Worker: one LUNA-MAX Worker for bounded kit corrections only; owner records audio.
- Depends on: T-112 apto.
- Objective: obtain 60 valid external WAV files matching the canonical ES/EN manifest.
- Non-goals: commit human audio, infer consent or alter corpus labels after seeing results.
- Allowed scope: `lab/stt/corpus/**`, `lab/stt/kit/**`, focused tests; external audio is owner data.
- Acceptance: every ID has one PCM mono 16 kHz WAV, checksum, anonymous speaker/device alias,
  permission/origin and declared condition; missing/duplicate IDs fail closed.
- Evidence: validation output and sanitized manifest/checksum report; no audio committed.
- Gates: corpus and kit tests; validator over all 60 IDs; `git status` proves audio remains external.
- Human checks: `TST-STT-001` owner recording portion.
- Audit: independent model audit by the principal Architect, separate model/context from execution.
- Worker result: none; not dispatched.
- Risks: privacy, inconsistent microphone distance, clipping and prompt-reading bias.
- STOP conditions: absent consent, personal identifiers, invalid format or fewer than 60 valid WAVs.
- Invalidated by: corpus schema or canonical prompt change.

### T-114 - Benchmark base and small on target HTPC

- Status: blocked
- Architect: principal Architect.
- Engineer: INGENIERO-PRODUCTO.
- Worker: one LUNA-MAX Worker to execute the approved brief on the target environment.
- Depends on: T-112 apto; T-113 apto.
- Objective: produce comparable physical Linux results for both required candidates.
- Non-goals: tune thresholds after results, use Windows as target evidence or integrate production.
- Allowed scope: `lab/stt/**`, focused tests and external results directory; no product paths.
- Acceptance: Linux inventory includes CPU flags/RAM; both candidates cover all 60 IDs with cold/hot
  latency, RTF, RAM/CPU, WER/CER, phrase/slot accuracy, failures and hallucinations.
- Evidence: inventory JSON, immutable asset manifest and raw/derived result JSON with checksums.
- Gates: readiness passes; benchmark exits 0; decision input validation accepts both reports;
  full PH21 suite passes.
- Human checks: `TST-STT-001` benchmark/hardware portion.
- Audit: independent model audit by the principal Architect, separate model/context from execution.
- Worker result: none; not dispatched.
- Risks: thermal variance, background noise, CPU flags, measurement bias and incomplete runs.
- STOP conditions: synthetic input, different corpus/assets/hardware between candidates, missing
  metrics, hidden failures or non-Linux target.
- Invalidated by: asset/corpus/benchmark schema change.

### T-115 - Produce the PH21 decision and report

- Status: blocked
- Architect: principal Architect.
- Engineer: INGENIERO-PRODUCTO.
- Worker: one LUNA-MAX Worker for deterministic report generation; no discretionary winner.
- Depends on: T-114 apto.
- Objective: apply the fixed gates and emit winner, profiles or insufficient evidence.
- Non-goals: relax thresholds, publish hardware requirements or modify production.
- Allowed scope: `lab/stt/decision.py`, `lab/stt/DECISION.md`, `lab/stt/readiness.json`, tests and
  external result inputs; phase report remains ephemeral.
- Acceptance: decision is reproducible from checksummed inputs; every gate is explicit; ties use
  the approved rule; `winner: null` is retained when evidence is insufficient.
- Evidence: decision output, phase report, commands and input/output checksums.
- Gates: decision tests; full PH21 suite; rerun decision from clean checkout plus external inputs.
- Human checks: `TST-STT-001` result review.
- Audit: independent model audit by the principal Architect, separate model/context from execution.
- Worker result: none; not dispatched.
- Risks: report drift, accidental fixture acceptance and unsupported hardware generalization.
- STOP conditions: missing raw evidence, manual result edits, threshold change or ambiguous license.
- Invalidated by: any upstream NO APTO or changed decision contract.

### T-116 - Audit and close PH21 evidence

- Status: blocked
- Architect: principal Architect; performs phase verdict.
- Engineer: INGENIERO-PRODUCTO; prepares G3 capsule.
- Worker: none unless an audited correction brief is authorized.
- Depends on: T-115 apto.
- Objective: prove PH21 met its laboratory goal without contaminating product or v3 control state.
- Non-goals: merge, push, release, PH22 or runtime integration.
- Allowed scope: PH21 Git range and evidence read-only; corrections require separate scope.
- Acceptance: required tasks are apto, human evidence is current, full suite passes, product diff is
  empty, control-plane branch changes are excluded from future integration, and risks are explicit.
- Evidence: G3 audit capsule, task verdicts, source range, test output and branch disposition proposal.
- Gates: full PH21 suite; reference sweep; product isolation diff; phase coherence check.
- Human checks: `TST-STT-001` must be `[OK]` for closure.
- Audit: independent model audit by the principal Architect, separate model/context from execution.
- Worker result: none; not dispatched.
- Risks: branch/control conflicts and evidence existing only outside repository.
- STOP conditions: required human check unavailable, dirty evidence, product contamination, missing
  authority for branch disposition or any unresolved blocker.
- Invalidated by: delayed NO APTO in T-111..T-115 or canonical design drift.

## Closure gate

- [ ] Owner approval digest is current and all tasks have required verdicts.
- [ ] External binary, weights, audio, inventory and result checksums are recorded without secrets.
- [ ] Required deterministic evidence and `TST-STT-001` are fresh.
- [ ] Both candidates used identical corpus, hardware, runtime policy and metrics.
- [ ] No fixture/synthetic observation selected a winner.
- [ ] Production paths remain unchanged and `lab/` is absent from the package/runtime graph.
- [ ] Legacy branch `.agents` changes cannot overwrite the v3 control plane.
- [ ] Main v3 CURRENT, APPCORE, INDEX and TESTING agree with accepted task capsules, repository,
  worktree and Git; legacy PH21 `.agents` changes were not copied or integrated.
- [ ] Merge/push/branch disposition remains a separate explicit owner action.
