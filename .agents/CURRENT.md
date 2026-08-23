# CURRENT — estado vivo v3

```yaml
version: 3
updated_at: 2026-08-22T23:38:23-05:00
source_commit: 1999a8457b64eb7801df80fb69e7bda97456886c
product_branch_head: e838279
dirty: true
dirty_items:
  - .agents/AGENTS.md (MAINTAIN correction cycles 1-2)
  - .agents/CURRENT.md (MAINTAIN cycles 1-2; REINDEX)
  - .agents/TESTING.md (MAINTAIN correction cycle 1)
  - .agents/WORKFLOW.md (MAINTAIN correction cycle 1)
  - .agents/skills/manage_context/SKILL.md (MAINTAIN correction cycle 1)
  - .agents/CONTEXT.md (MAINTAIN cycle 1, preserved in correction cycle 1)
  - .agents/INDEX.md (MAINTAIN cycles 1-2; REINDEX)
  - .agents/APPCORE.md (REINDEX)
  - .agents/archive/TESTING_legacy_2026-08-21.md (MAINTAIN cycle 1)
  - .agents/PLAN_v2.0-ph21-stt.md (PLAN draft superseded before approval)
  - .agents/PLAN_PH21.md (legacy pointer added by PLAN)
  - .agents/PLAN.md (roadmap pointer updated by PLAN)
  - .agents/PLAN_v1.99-beta-foundation.md (new PLAN draft)
  - AGENTS.md (MAINTAIN cycle 2: placeholder convertido en shim de instrucciones; sin commit)
  - .agents/design/skins2/lochi.png (pre-existing untracked)
assurance: Standard
active_job: RUN THE LOOP
active_plan: PLAN_v1.99-beta-foundation.md
active_task: T-121
last_verdict: APTO
verdict_scope: T-120 independent model audit
next_action: Push main and codex/beta-foundation, deploy website beta to production, then owner executes TST-BETA-CHANNEL-001
```

## Blockers

- Checks de device, benchmark y release requieren entornos no disponibles.
- El despliegue real de Supabase Edge Functions y Vercel no es demostrable desde Git.
- `TST-BETA-CHANNEL-001` and deployed endpoint/install evidence are unavailable; T-121 remains blocked.

## Fresh evidence

- REINDEX global verifico entrypoints, REST, WebSocket, pairing, trust boundaries, persistencia,
  voz cloud, build/install/OTA, website/latest, Supabase, docs y superficies de referencia.
- El Arquitecto independiente reejecuto `git diff --check`, `node --check frontend/app.js` y
  `bash -n scripts/build_deb.sh scripts/install.sh scripts/update.sh scripts/uninstall.sh
  website/install.sh`: todos pasaron.
- El diff de producto backend/frontend/scripts/website/supabase fue vacio; el SHA verificado del
  `.deb` es `82b6bc5286cdf197bb684ddc00f6c797aac498f2959b354cada83acaddd93d38`.
- `git status --short --branch`: `main` ahead 10; cambios MAINTAIN y REINDEX sin commit; `lochi.png`
  permanece intacto y el shim raiz permanece untracked.
- `git diff --check`: sin errores; `git ls-files tests`: sin salida.
- Último commit y source commit: `1999a8457b64eb7801df80fb69e7bda97456886c`.
- `last_verdict: APTO` tiene scope T-120 independent model audit; no es una autoaprobacion del
  Ingeniero.
- Inspeccion read-only de PH21: `1999a845..580847e8`, 23 commits; 297 tests pasaron; producto
  runtime sin diff; `readiness.json` permanece `false` por cuatro prerrequisitos externos.

## Current facts

- El código publicado 1.9.1 es un servicio FastAPI/PWA con voz, licencia y actualización cloud.
- El plan activo pendiente se consulta en `PLAN_v1.99-beta-foundation.md`; sus tareas no se duplican.
- Stable 1.9.1 debe permanecer aislado; betas numéricas 1.99.x son opt-in por curl y beta-a-beta.
- La historia y decisiones durables pertenecen a `CONTEXT.md` y git.

## Open findings

- No hay tests automatizados tracked; los gates ejecutables y checks de device están documentados,
  pero los de campo permanecen sin ejecutar.
- Finding documental: `docs/ARCHITECTURE.md` declara version 1.8.0 y 1.8.9 (lineas 16-17), y
  `docs/DEVELOPING.md` declara version 1.8.0 (linea 9), anteriores a 1.9.1; docs no editados.
- El worktree PH21 tiene `INTRUCCIONES PARA DEEPSEEK.md` untracked; se preserva como trabajo ajeno.
- `codex/v2-integration` y `codex/PH21-stt` apuntan al mismo head; cualquier disposicion Git requiere
  autorización separada.
- El draft PH21 fue superseded antes de aprobación; sus 23 commits/tooling se preservan como
  evidencia reutilizable, no como gate del nuevo flujo beta.
- D28 y el plan beta fueron aprobados por el dueño con digest
  `2bc3ec3cfac39a205c4a16c0d1f06b85f388d040e34a0d2290e3dd0f9c552f7d`.
- `RUN THE LOOP` state integration stops at T-121. Owner authorized selective commits, push and
  production deployment; cleanup remains unauthorized.
- T-117 verdict `APTO`: Worker `ses_fd84c189dffeo3efi7lMZtZ6HS` (`gpt-5.6 LUNA MAX`) returned
  `DONE_WITH_CONCERNS`; Architect resolved the concern with full runtime import using the root
  backend venv and `PAIRING_TOKEN` guard.
- Fresh T-117 gates: system Python pytest 15 passed; stable->stable, beta->beta and invalid->stable
  full runtime round trips PASS; `node --check` PASS; CSS sync PASS; `git diff --check` PASS.
- T-117 changed exactly `backend/main.py`, `frontend/app.js`, `backend/.env.example` and
  `tests/test_beta_channel.py`; commit `298bb39`. Product Worker slots released:
  Product 0/2, global 0/4.
- T-118 verdict `APTO` after correction cycle 1: Worker `ses_fd82b70b4ffe1xKKtLCNow4QzW`
  (`gpt-5.6 LUNA MAX`) returned `DONE_WITH_CONCERNS`; concerns resolved with integrated T-117+T-118
  package built/extracted in native WSL, installer marker before `lrp-setup`, and `chown -R` before
  service restart. Device validation remains required by T-121, not T-118.
- Fresh T-118 gates: 21 pytest PASS; full runtime import PASS; node PASS; CSS PASS; `bash -n`
  installer/build PASS on Windows+WSL; distribution parser/dedup 6 tests PASS; stable
  `website/latest.json` unchanged hash/blob `700a8878a2dd743ea7ca4ff73b8c592b3bb92727`; no live
  beta latest; integrated `.deb` SHA `026669a8d853c624c10ea1b991a78ecbe391401a132f1a67fafcb5c7445178f2`
  matched sidecar; control postinst/updater syntax and hardcoded URLs PASS; package excludes `.env`.
- T-118 changed exactly `website/beta/install.sh`, `website/beta/latest.template.json`,
  `scripts/build_deb.sh`, `tests/test_beta_distribution.py` and `tests/fixtures/beta-manifest.json`;
  commit `607bf04`. Product roster 2/2 sessions registered, active 0;
  global roster 2/4, active 0; no new Product Workers permitted, existing sessions may be reused.
- T-119 verdict `APTO` after correction cycles 1-2: Worker `ses_fd82b70b4ffe1xKKtLCNow4QzW`
  (`gpt-5.6 LUNA MAX`) final result `DONE`; no Worker nuevo.
- Fresh T-119 gates: 26 cumulative pytest PASS; node site/app PASS; CSS sync PASS; `git diff --check`
  PASS; protected stable manifests/installers/downloads/JS/Vercel unchanged; no inline CSS;
  namespaced beta-landing CSS; exactly one command and one language link; Edge/CDP desktop 1440x900
  and mobile 390x844 with `mobile=true`, `touch=true`, `scale=3`, `scrollWidth==innerWidth`;
  screenshots external temp.
- T-119 changed exactly `website/index.html`, `website/en/index.html`, `website/style.css` and
  `tests/test_beta_landing.py`; commit `be96e35`. Product roster 2/2 sessions registered, active 0;
  global roster 2/4, active 0; existing Product Workers may be reused, no new ones permitted.
- T-120 verdict `APTO` after correction cycle 1: Worker `ses_fd82b70b4ffe1xKKtLCNow4QzW`
  (`gpt-5.6 LUNA MAX`) final result `DONE`; no new Worker.
- Fresh T-120 gates: VERSION/package `1.99.1`; 29 tests PASS; node/bash/CSS/diff PASS; source
  service-worker placeholder unchanged and package stamped `lrp-1.99.1`; stable latest/downloads/
  install byte-identical; package metadata `linuxremoteplayer`/`all`; `.env` absent; exact manifest
  URL; artifact/sidecar/manifest SHA `8d4a19834eca05eda0e3f8b9c77817e6baaa19fb1bd823e30b5a726b6cb9c894`
  matched; control postinst/updater syntax and hardcoded URLs PASS; commit `e838279`; push/deploy
  pending.
- T-120 files: `VERSION`, `CHANGELOG.md`, beta template/live manifest, beta `.deb`+sidecar,
  `tests/test_beta_release.py`, expanded `tests/test_beta_distribution.py`; source `frontend/sw.js`
  remained read-only.
- External WSL audit clones: `lrp-t118-build-3`, `lrp-t118-integrated-1`,
  `t120-native-20260822-5`; cleanup not authorized. Product roster 2/2 sessions registered, active 0;
  global roster 2/4, active 0; existing sessions may be reused, no new Product Workers permitted.
