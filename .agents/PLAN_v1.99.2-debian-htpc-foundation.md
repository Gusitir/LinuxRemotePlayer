# PLAN v1.99.2 - Debian HTPC Foundation

```yaml
status: closed
goal: entregar beta 1.99.2 instalable por OTA sobre Debian 13 minimal amd64, con sesion Xorg/Openbox administrada por LRP y RTX 3060 certificada inicialmente, sin dependencias Plasma/Bigscreen ni promesas multidistro
assurance: Standard
approval_digest: 678ac5c9119312529ec1b5fe3b054c77a595b03dbe82c8319d669327fd17002a
approval_actor: owner
approval_request_ref: none
approved_at: 2026-08-28T00:24:48-05:00
approval_decision_id: D31
approval_source: 678ac5c9119312529ec1b5fe3b054c77a595b03dbe82c8319d669327fd17002a
```

Aprobado por el dueño (D31). La aprobación habilita únicamente T-122, que queda `ready`; el resto
permanece bloqueado. Exact display-manager and Debian/NVIDIA package choices require D32 after
physical Debian evidence; dependent tasks remain blocked until that decision.

## Canonical design approved

Digest boundary: exact UTF-8/LF bytes between `CANONICAL-DESIGN-BEGIN` and
`CANONICAL-DESIGN-END`, excluding marker lines.

<!-- CANONICAL-DESIGN-BEGIN -->
1. LinuxRemotePlayer remains one product. Its only supported platform is Debian 13 stable amd64;
   other distributions may work accidentally but receive no compatibility guarantee.
2. The supported host starts from Debian minimal. LRP installs and owns one dedicated HTPC session
   based on Xorg and Openbox; Plasma, Plasma Bigscreen, KDE Neon and Wayland are not supported
   runtime targets for this milestone.
3. RTX 3060 12 GB is the initial certified GPU. NVIDIA drivers, firmware and dependencies come
   only from enabled Debian repositories; NVIDIA `.run`, third-party driver repositories and
   silently downloaded executables are forbidden.
4. T-122 verifies Debian package names/versions, repository components, Secure Boot, GPU identity
   and display-manager options on the physical test machine. D32 binds the exact package/session
   contract before driver or session implementation begins.
5. Installation is a resumable state machine: preflight, driver, reboot, driver verification,
   graphical session, platform services, application. Every privileged mutation has evidence,
   rollback and a STOP condition.
6. LRP runs as a dedicated non-root user. Root authority is limited to apt, driver/kernel setup,
   systemd, display manager, UFW, udev, certificates and owned system configuration.
7. Firefox ESR is the only supported browser. KWin DBus, qdbus, Wayland/XWayland workarounds,
   Brave/Chromium fallbacks and Desktop/Appliance dual mode are removed only after replacement
   behavior and rollback are verified.
8. systemd, uinput, MPRIS, PipeWire/WirePlumber, Avahi, local HTTPS, pairing and beta channel
   isolation remain required Debian mechanisms.
9. Beta 1.99.2 proves clean Debian install, driver/reboot recovery, managed session, autologin,
   kiosk, input, audio, pairing, OTA from 1.99.1 and uninstall/rollback on the physical HTPC.
10. Local STT, Needle 2, Debian image generation and a general multidistro remote are explicit
    non-goals. Voice/cloud/licensing behavior remains factual until a later approved milestone.
11. The RTX 3060/Plasma Bigscreen failure and Linux Mint success are architectural rationale only;
    root cause is unknown and no universal NVIDIA/Plasma claim is made.
<!-- CANONICAL-DESIGN-END -->

## Existing baseline

- Stable channel: `1.9.1`; beta channel: deployed `1.99.1`.
- Current installer supports Debian/Ubuntu-family and Desktop/Appliance modes.
- Current kiosk prefers Firefox but falls back to Brave/Chromium and KWin DBus.
- Current package is `Architecture: all`; no Xorg/Openbox/NVIDIA bootstrap exists.
- Current tests cover beta channel/distribution/landing/release, not managed Debian session.
- Physical test machine has RTX 3060; Debian 13 minimal evidence is not yet available.
- BETA-FOUNDATION is closed and archived; beta branch `codex/beta-foundation` is retained.

## Scope

- In scope: Debian-only contract, package inventory, NVIDIA preflight/bootstrap, reboot-resume,
  Xorg/Openbox managed session, single HTPC mode, Firefox-only kiosk, Debian platform services,
  uninstall/rollback, documentation cleanup and beta 1.99.2.
- Non-goals: STT, Needle 2, model delivery, cloud/license removal, Debian image/ISO, general remote,
  non-Debian support, Wayland migration and B19 remediation.
- Development method: evidence-first replacement; add Debian behavior and gates before deleting
  compatibility code; one focused task/commit at a time.
- Closure evidence: package inventory/D32, clean Debian install, NVIDIA reboot recovery,
  Xorg/Openbox autologin, service non-root, kiosk/input/audio/pairing, OTA 1.99.1->1.99.2,
  uninstall/rollback, artifact audit, docs sweep and required TESTING IDs.

## Workspace and orchestration

- Product branch/worktree: `codex/debian-foundation` / `.worktrees/debian-foundation`. Worktree HEAD is
  `7f6375d` (D35 one-command + legacy migration); only the rebuilt `1.99.2` artifact/sidecar remain uncommitted there.
- Architect owns design, `.agents`, D32 and the final verdict; never writes product.
- Sole Engineer: `fdfc68b2-8383-4854-8f61-737c6e0c101b`; direct product implementation, corrections,
  deterministic gates and evidence integration. No Workers or implementation subagents.
- Architect audits batches of tasks, not individual tasks, and owns all control-plane verdicts.
- Phase Auditor: `ae7b054f-900d-4285-87c0-f2cdd49e7888`; one final phase audit, no code, fixes or planning.
- Tasks are serialized unless Engineer proves disjoint writes. Docs T-129 may overlap only after
  platform contracts are frozen and never while another task edits the same references.
- No commit, push, deploy, cleanup or destructive host operation without explicit authorization.

## Tasks

### T-122 - Verify Debian baseline and package contract

- Status: apto (D32 package contract approved)
- Architect: principal Architect; records D32.
- Engineer: sole Engineer; prepares physical preflight brief.
- Worker: DeepSeek V4 Flash Worker 1 for bounded preflight/tests after slot authorization.
- Depends on: owner approval digest.
- Objective: verify Debian 13 minimal amd64, RTX 3060, repository components and exact package
  candidates before any privileged platform implementation.
- Non-goals: install driver/session, change host, remove existing code or publish package claims.
- Allowed scope: `scripts/debian/preflight.sh`, `tests/test_debian_preflight.py`, focused Debian
  setup documentation; HTPC commands are read-only until owner authorizes each privileged action.
- Acceptance: evidence records `/etc/os-release`, architecture, kernel, PCI GPU, Secure Boot,
  current modules, apt sources and `apt-cache policy` for Xorg, Openbox, candidate display manager,
  NVIDIA driver/firmware, headers/DKMS, Firefox ESR, PipeWire, Avahi, UFW and session dependencies.
- Evidence: sanitized host capsule with exact package candidates/versions and unresolved items.
  Recorded final: code APTO plus gates (33/33 T-122, 62/62 full suite, bash/static/diff); physical
  Debian 13 trixie amd64 UEFI, RTX 3060 PCI `10de:2504`, module `nouveau` active, Secure Boot disabled
  (Setup Mode), apt sources oficiales `main`+`non-free-firmware` sin terceros. D32 contract approved on
  isolated official Debian sandbox.
- Gates: preflight unit fixtures; shell syntax; Debian 13 physical output; no host mutation.
- Human checks: `TST-DEBIAN-BASE-HUMAN-001` owner confirms target install and hardware identity.
- External required check: `TST-DEBIAN-BASE-001` AI read-only baseline evidence.
- Audit: Engineer code verdict APTO; Architect assistant preaudit finding resolved; Architect approves
  D32; T-122 `APTO`.
- Worker result: DONE_WITH_CONCERNS accepted (physical Debian evidence now available and D32 approved;
  Worker1 `ses_fb9282115fferi6Gzz4NVmDL74` final STOP cycle2; Worker2 `ses_fb928209dffeG7DcXFSfRcCvaL`
  idle). Exact files: `scripts/debian/preflight.sh`, `tests/test_debian_preflight.py`.
- Risks: wrong Debian suite/components, Secure Boot, unavailable firmware, package drift.
- STOP conditions: non-Debian host, non-amd64, GPU mismatch, third-party repo required, package
  identity unresolved or command requests mutation during inventory.
- Invalidated by: Debian suite, architecture, GPU or repository policy change.

### T-123 - Implement NVIDIA bootstrap and reboot resume

- Status: apto (D32 package contract approved)
- Architect: approves D32 package contract and trust boundary.
- Engineer: sole Engineer.
- Worker: DeepSeek V4 Flash Worker 1.
- Depends on: T-122 apto; D32 approved.
- Objective: install verified Debian NVIDIA dependencies through a resumable, auditable state machine.
- Non-goals: session UI, third-party NVIDIA installer, GPU overclocking or support claims beyond RTX 3060.
- Allowed scope: Debian installer/preflight scripts, state markers, package tests and focused docs.
- Acceptance: preflight fails closed; apt sources are explicit; driver install requests owner approval;
  reboot resumes safely; module/renderer verification passes; failure leaves actionable rollback.
- D32 contract (approved): enable official components `main contrib non-free non-free-firmware`;
  display manager `lightdm 1.32.0-6+b2`; `xserver-xorg 1:7.7+24+deb13u1`; `openbox 3.6.1-12+b2`; NVIDIA
  meta `nvidia-driver 550.163.01-2` with dependencies `nvidia-kernel-dkms`/`xserver-xorg-video-nvidia`
  `550.163.01-2`, `firmware-nvidia-gsp 550.163.01-2`, `linux-headers-amd64 6.12.105-1`, `dkms
  3.2.2-1~deb13u1`. Do not install `nvidia-open-kernel-dkms` or `firmware-misc-nonfree` unless a later
  verified dependency requires it. No `.run`/third-party repositories.
- Evidence: package transaction, state transitions, reboot capsule, `nvidia-smi`/module/renderer output.
  Recorded final: code gates latest 47/47 T-123 and 110/110 full suite (subsequent audits green);
  physical Debian 13 with official legacy sources, components `main contrib non-free non-free-firmware`,
  exact packages/header; an interrupted apply was recovered via `dpkg --configure -a`; final apply exit 20
  without auto-reboot; owner-authorized reboot; `nvidia` module bound to RTX 3060, `nouveau` absent,
  `nvidia-smi` `550.163.01`, resume exit 0 with state `complete`. Residual power-interruption recovered;
  renderer deferred to T-124.
- Gates: state-machine tests; shell syntax; failure fixtures; `TST-NVIDIA-001` physical check.
- Human checks: owner authorizes apt/reboot and confirms display returns.
- Audit: Engineer code verdict APTO; Architect assistant preaudit mechanical; Architect approves;
  T-123 `APTO`.
- Worker result: DONE_WITH_CONCERNS accepted (physical apply/recovery completed; renderer deferred to
  T-124; Worker1 `ses_fb9282115fferi6Gzz4NVmDL74`; Worker2 `ses_fb928209dffeG7DcXFSfRcCvaL` idle).
- Risks: Secure Boot/DKMS failure, black screen, kernel mismatch, nonrecoverable display.
- STOP conditions: external repo or `.run`, unsigned/unloadable module, no rollback path, reboot cannot
  resume, or system loses recoverable console.
- Invalidated by: D32 or kernel/driver contract change.

### T-124 - Create the managed Xorg/Openbox session

- Status: apto
- Architect: owns session and privilege design.
- Engineer: sole Engineer.
- Worker: DeepSeek V4 Flash Worker 1.
- Depends on: T-123 apto.
- Objective: boot into a dedicated non-root LRP Xorg/Openbox session with verified autologin and escape path.
- Non-goals: Plasma/KWin, Wayland, general desktop support or image generation.
- Allowed scope: session scripts/config, selected display-manager config, systemd units, installer
  integration and tests.
- Acceptance: boot/reboot enters session; LRP service starts after display/network; no root GUI;
  display failure returns to recoverable console; explicit owner-access escape path exists.
- Evidence: 15/15 focused tests and 125/125 full suite; physical apply installed the exact seven
  Debian packages, created locked non-root `lrp`, enabled LightDM without starting it, and requested
  reboot. After the owner-authorized reboot, resume exit 0 verified active LightDM, Xorg, Openbox
  owned by `lrp`, NVIDIA renderer, package integrity and state `complete`.
- Gates: config syntax; systemd verify; Xorg/Openbox smoke; `TST-SESSION-001`.
- Human checks: `TST-DEBIAN-UX-001` boot/autologin/recovery portion.
- Audit: sole Engineer verdict `APTO`; physical evidence accepted by the Architect.
- Worker result: Worker 1 implementation accepted after two bounded physical-parser/ownership fixes.
- Risks: autologin security, display loop, environment/DBus errors, unrecoverable kiosk.
- STOP conditions: root session, hidden escape, boot loop, missing rollback or display manager drift.
- Invalidated by: D32 display-manager/session contract change.

### T-125 - Collapse installer and service to one HTPC mode

- Status: apto
- Architect: owns migration behavior.
- Engineer: sole Engineer.
- Worker: DeepSeek V4 Flash Worker 1.
- Depends on: T-124 apto.
- Objective: replace Desktop/Appliance branching with one Debian HTPC installation and service contract.
- Non-goals: unrelated UI changes, voice pipeline or format-breaking config cleanup without migration.
- Allowed scope: `scripts/install.sh`, generated service/package templates, config migration and tests.
- Acceptance: existing beta configuration migrates deterministically; service/user/paths are singular;
  repeated setup is idempotent; restart/IP-change behavior remains correct.
- Evidence: 10/10 focused tests, 135/135 full suite, shell syntax and generated-unit inspection.
  Installer fixes target `lrp`, migrates `LRP_MODE=htpc`, removes bounded legacy user units and emits
  one system service ordered after display manager and network online; updater lifecycle is system-only.
- Gates: shell/config tests; systemd unit checks; protocol health smoke.
- Human checks: none beyond dependent physical session gate.
- Audit: sole Engineer verdict `APTO`; Architect accepts the bounded installer/service migration.
- Worker result: Worker 1 delivery accepted after passwd-field and legacy-cleanup correction.
- Risks: orphan user service, duplicate units, lost pairing/config, ownership regression.
- STOP conditions: destructive migration, token/cert loss, dual active services or non-idempotent setup.
- Invalidated by: session/service contract change.

### T-126 - Make kiosk and runtime Debian-only

- Status: apto
- Architect: owns supported capability boundary.
- Engineer: sole Engineer.
- Worker: DeepSeek V4 Flash Worker 2.
- Depends on: T-125 apto.
- Objective: support Firefox ESR on Xorg/Openbox and remove unsupported KWin/Wayland/Brave/Chromium paths.
- Non-goals: website redesign, browser extensions redesign or general desktop compatibility.
- Allowed scope: `backend/kiosk.py`, related backend/config tests, installer browser policy and docs.
- Acceptance: Firefox ESR launch/kill/recovery work; no KWin/qdbus/Wayland/Brave/Chromium runtime
  reference remains; failure is explicit; production control functions remain isolated.
- Evidence: 22/22 focused tests, 147/147 full suite and clean forbidden-reference sweep. Physical
  Debian smoke installed Firefox ESR and wmctrl from official repositories, launched one kiosk window
  under `lrp`, confirmed the tracked process after 10 seconds and closed its process group cleanly.
- Gates: focused Python tests; full beta suite; Firefox/Xorg process round trip.
- Human checks: `TST-DEBIAN-UX-001` kiosk/media portion.
- Audit: sole Engineer verdict `APTO`; Architect accepts code and physical kiosk evidence.
- Worker result: Worker 2 delivery accepted after removal of one residual desktop-shell filter.
- Risks: orphan Firefox, profile corruption, focus/fullscreen loss, stale policy.
- STOP conditions: browser fallback reintroduced, arbitrary process kill, user profile touched or kiosk cannot exit.
- Invalidated by: session/browser contract change.

### T-127 - Standardize Debian platform services

- Status: apto
- Architect: owns system mutation and rollback policy.
- Engineer: sole Engineer.
- Worker: DeepSeek V4 Flash Worker 1.
- Depends on: T-125 apto.
- Objective: make uinput, PipeWire, Avahi, UFW, sleep/DPMS and certificates deterministic for Debian HTPC.
- Non-goals: driver/session replacement, OTA signing or broad security hardening outside touched services.
- Allowed scope: installer/cleanup scripts, service rules, configuration templates and tests.
- Acceptance: every mutation has ownership marker and inverse cleanup; no KDE setting remains; audio,
  input, discovery, firewall and local HTTPS survive reboot; previous host state is not silently destroyed.
- Evidence: final platform tests 17/17, combined gates 36/36 and prior full suite 159/159. Physical
  apply/reboot verified uinput permissions, PipeWire/WirePlumber, Avahi, UFW SSH+LRP rules, four
  sleep masks, DPMS disabled, package integrity and repeat apply exit 0.
- Gates: script tests; generated config validation; `TST-DEBIAN-SERVICES-001`.
- Human checks: owner approves sleep/firewall policy and validates media/input.
- Audit: sole Engineer verdict `APTO`; Architect accepts code and physical platform evidence.
- Worker result: Worker 1 delivery accepted after physical masked-status and late-CA fixes.
- Risks: firewall lockout, input permissions, sleep policy damage, certificate residue.
- STOP conditions: no rollback, unmanaged global overwrite, secret exposure or device mismatch.
- Invalidated by: platform policy change.

### T-128 - Complete uninstall and rollback

- Status: apto
- Architect: owns destructive acceptance.
- Engineer: sole Engineer.
- Worker: DeepSeek V4 Flash Worker 1.
- Depends on: T-126 apto; T-127 apto.
- Objective: remove LRP-owned Debian session/platform state and restore recorded host state safely.
- Non-goals: remove Debian/NVIDIA driver by default or delete owner data without explicit choice.
- Allowed scope: uninstall/cleanup scripts, ownership manifest, rollback tests and docs.
- Acceptance: services/session/autologin/UFW/udev/certs/cache are removed or restored; NVIDIA driver
  remains unless separately authorized; dry-run/report exists; repeated uninstall is safe.
- Evidence: rollback/platform focused 37/37, rollback file 15/15 and prior full suite 178/178.
  Physical dry-run, strict rollback, residual sweep and complete reapply/reboot round trip passed;
  NVIDIA, packages, `lrp` and owner data were retained.
- Gates: cleanup fixtures; shell syntax; `TST-DEBIAN-ROLLBACK-001`.
- Human checks: owner verifies login/console and expected retained data.
- Audit: sole Engineer verdict `APTO`; Architect accepts automated physical rollback evidence.
- Worker result: Worker 1 delivery accepted after strict propagation, UFW force and root dry-run fixes.
- Risks: loss of login, network, display or user configuration.
- STOP conditions: destructive ambiguity, no ownership record, driver removal, or rollback cannot be proven.
- Invalidated by: any upstream ownership/installation contract drift.

### T-129 - Publish Debian-only product truth

- Status: apto
- Architect: approves product wording.
- Engineer: sole Engineer.
- Worker: DeepSeek V4 Flash Worker 2.
- Depends on: T-125 apto; T-126 apto; D32 approved.
- Objective: remove active multidistro/Plasma/Bigscreen claims and document only verified Debian support.
- Non-goals: rewrite historical changelog/archive, claim untested GPUs or advertise future voice.
- Allowed scope: `README.md`, `docs/**`, active website docs/terms/changelog references,
  `backend/.env.example` and reference tests. APPCORE remains control-plane owned.
- Acceptance: active docs say Debian 13 amd64 required; RTX 3060 is initial certified GPU; other
  distros/GPUs are not guaranteed; no active Plasma/Bigscreen/KDE Neon/Desktop/Appliance claim remains.
- Evidence: focused docs/landing 8/8, full suite 187/187 and clean active-reference sweep; ES/EN
  active copy agrees on Debian 13 amd64 minimal, Xorg/Openbox, Firefox ESR and RTX 3060 certification.
- Gates: link/text tests; render desktop/mobile; history/archive exclusions.
- Human checks: owner copy approval.
- Audit: sole Engineer verdict `APTO`; Architect accepts factual ES/EN copy.
- Worker result: Worker 2 delivery accepted after one stale landing-test correction.
- Risks: deleting historical rationale, overclaiming GPU support, stale localized copy.
- STOP conditions: product claim lacks physical evidence or historical files are rewritten.
- Invalidated by: platform/package evidence change.

### T-130 - Build and deploy beta 1.99.2

- Status: apto
- Architect: owns release gate.
- Engineer: sole Engineer; implements release corrections directly.
- Implementation: direct Engineer work under the two-level workflow.
- Depends on: T-126 apto; T-127 apto; T-128 apto; T-129 apto.
- Objective: publish audited beta 1.99.2 and preserve stable 1.9.1 isolation.
- Non-goals: stable promotion, model/Needle delivery, B19 closure or branch deletion.
- Allowed scope: `VERSION`, `CHANGELOG.md`, beta manifest/artifact/sidecar and
  `tests/test_debian_release.py`; source `frontend/sw.js` is read-only and stamped only in package.
- Acceptance: cumulative source/package/SW/manifest/SHA agree; package is `amd64`; source and artifact
  contain Debian-only contracts; stable manifest/download remain byte-identical. Fresh public install
  is one command: a guarded transient service resumes across at most two automatic reboots and removes
  itself after health succeeds; TTY recovery and anti-loop failure remain explicit.
- Evidence: Windows and native WSL clean-clone suites 205/205; local artifact SHA
  `a0b54c85fff7842a25676546c8d105455c603fb202eb53510fbff622442a83e9`. Local amd64 package
  install/setup, service, CA, pairing, apps, controls and `dpkg -V` pass. Effective UFW rules include
  8000/tcp and 5353/udp on IPv4/IPv6; Firefox recovery suppression and NVIDIA HDMI default are active.
  Public manifest/installer/pages and independently downloaded artifact pass; Vercel status is success
  at `98bb9f1`, while stable 1.9.1 remains unchanged. OTA is deferred to T-131. One abrupt reset is
  not reproduced/root-caused after a 3-minute health/GPU soak.
- Gates: full suite; Debian package audit; reference sweep; `TST-BETA-UPDATE-002` prepared.
- Human checks: owner authorizes push/deploy and later HTPC OTA.
- Audit: Architect batch audit T-122..T-130 resolved clean-install orchestration, runtime dependencies,
  token exposure, mDNS runtime, HDMI selection and Firefox recovery findings; T-130 `APTO`.
- Historical delivery: pre-workflow Worker 2 prepared the initial prebuild; Engineer owns all work now.
- Risks: package architecture/dependency errors, stable crossover, failed OTA.
- STOP conditions: dirty build, stable mutation, missing physical prerequisites, package mismatch or unsupported claim.
- Invalidated by: upstream NO APTO or package/session contract drift.

### T-131 - Validate Debian HTPC foundation

- Status: apto (G4 phase audit and owner approval passed; commit 95490ce in codex/debian-foundation)
- Architect: issues milestone verdict.
- Engineer: prepares G3 capsule.
- Implementation: sole Engineer direct; no Workers or subagents.
- Depends on: T-130 apto.
- Objective: prove beta 1.99.2 installs/updates and operates as a clean Debian-managed HTPC.
- Non-goals: STT/Needle testing, stable release or image certification.
- Allowed scope: physical HTPC and public endpoints read-only; corrections require new task scope.
- Acceptance: clean Debian install and 1.99.1->1.99.2 OTA pass; NVIDIA/reboot/session/autologin,
  service, pairing, PWA, kiosk, input, audio, firewall, uninstall and rollback meet required checks.
  The one-command unattended path, two reboot continuations, anti-loop STOP and cleanup are physical gates.
- Evidence: AI automatic capsules plus owner-only visual/UX/recovery capsule. Active D35 evidence: full suite `207/207`, unattended sandbox and legacy migration verified on HTPC; rebuilt artifact/sidecar (`25ea41…`) still disagree with manifest (`a0b54…`).
- Gates: phase coherence, package/device verification, public endpoint sweep, all required TESTING IDs.
- Human checks: `TST-DEBIAN-UX-001`, `TST-DEBIAN-ROLLBACK-001` must be `[OK]`.
- External required checks: `TST-DEBIAN-BASE-001`, `TST-NVIDIA-001`, `TST-SESSION-001`,
  `TST-DEBIAN-SERVICES-001`, `TST-BETA-UPDATE-002` must be `[OK]`.
- Audit: one final phase review by Auditor, then final Architect verdict.
- Risks: device-only defects, driver regressions, rollback gaps and accepted B19 exposure.
- STOP conditions: missing required evidence, package mismatch, non-Debian host or unrecoverable system state.
- Invalidated by: delayed upstream NO APTO, endpoint drift or device mismatch.

## Closure gate

- [x] Owner approval and D32 package/session decision are current.
- [x] T-122..T-131 have required verdicts and dependency coherence.
- [x] Debian 13 minimal amd64 and RTX 3060 evidence is fresh.
- [x] Driver install/reboot, Xorg/Openbox session and non-root service are reproducible.
- [x] Plasma/Bigscreen/KWin/Wayland/multidistro active references are removed or explicitly historical.
- [x] Firefox ESR, input, audio, pairing, kiosk, firewall and cleanup pass physical checks.
- [x] Beta 1.99.2 artifact/manifest/SHA and 1.99.1->1.99.2 OTA are verified.
- [x] Stable 1.9.1 remains isolated and B19 remains a stable-release blocker.
- [x] CURRENT, APPCORE, INDEX, TESTING, repository, device and Git agree.
- [x] Branch disposition, backup and cleanup state are explicit.
