# CURRENT — estado vivo v3

```yaml
version: 3
updated_at: 2026-10-21T16:35:00-05:00
source_commit: 88cf2f6
product_branch: codex/debian-foundation
product_branch_head: d3495ab
product_branch_state: 24 commits ahead of main, 1 main-only commit, not merged; merge-tree exit 0 (tree 8068b59)
dirty: true
dirty_items:
  - control-plane MAINTAIN edits pending `[STATE]` commit (AGENTS, APPCORE, BUGS, CONTEXT, CURRENT, INDEX, PLAN)
  - .agents/PLAN_v2.0.0-release.md untracked (aprobado D51)
assurance: Standard
active_job: RUN THE LOOP
active_plan: PLAN_v2.0.0-release.md (approved, digest 2814bb3c…, D51)
active_task: T-143 audit (delta ISO)
last_verdict: APTO
verdict_scope: APTO otorgado por auditor independiente sobre `9d60785` (merge --no-ff + push autorizados; publicación de manifiesto estable excluida). Delta posterior `d3495ab` corrige el arranque de la ISO (enlaces `live/vmlinuz` e `initrd.img`); re-auditoría del delta en curso.
next_action: Con APTO del delta `d3495ab`: commit `[STATE]` del control plane, merge `--no-ff` en `main` y push. Publicación de `website/latest.json` 2.0.0 queda para T-146 (gate PH24).
```

## Blockers

- Merge y push de `codex/debian-foundation` BLOQUEADOS: auditoría pre-merge `NO APTO` (AUD-001..003
  en `BUGS.md`). No se integra ni publica hasta un veredicto APTO sobre el head corregido.
- Push, merge y deploy adicionales requieren autorización explícita del dueño; el commit `[STATE]`
  `88cf2f6` ya está en `origin/main`.
- `2.0.0` no es publicable: `main` no contiene ninguno de los 18 commits de producto de
  `codex/debian-foundation`; falta además bump de `VERSION`, firma de manifiestos y `TST-OTA-001`.
- Cleanup of external WSL audit clones remains unauthorized.
- One abrupt physical reset occurred after launching Netflix. Journal ended without orderly
  shutdown, panic, OOM, thermal event, NVIDIA Xid or pstore evidence; a 90-second monitored
  retry did not reproduce.

## Fresh evidence

- `main`/`origin/main` at `88cf2f6` (`[STATE] Cierra v2.0 appliance`), árbol limpio;
  `git rev-list --left-right --count origin/main...main` = `0 0`.
- Published beta artifact `website/beta/downloads/linuxremoteplayer_1.99.2_amd64.deb` rehashes to
  `a0b54c85fff7842a25676546c8d105455c603fb202eb53510fbff622442a83e9`, equal to manifest and
  sidecar. Stable manifest remains `1.9.1` SHA `82b6bc5286cdf197bb684ddc00f6c797aac498f2959b354cada83acaddd93d38`.
- T-131 artifact/manifest mismatch is resolved: no `dist/` sidecar exists in
  `.worktrees/debian-foundation` and no `25ea41…` reference remains in the repo.
- ISO 2.0.0 vigente, head `d3495ab`: `lrp-os_2.0.0_amd64.iso`, 2036561920 bytes, SHA256
  `c1e191330be3eef64ad2ded14a5ddb2ff09cce844e40880066873906dbfad2e0` (copia en
  `D:\AGUSTIN\Portafolio\Proyectos\lrp-iso\`). Montada y verificada: `/live/vmlinuz` e
  `/live/initrd.img` resuelven al kernel 6.12.113+deb13-amd64. ISO anterior `cb846984…` y
  `f8611e13…` quedan obsoletas (fallaban con `file '/live/vmlinuz' not found`).
- Correcciones `c484274`/`f229e5b`/`bad230f`: venv limpio `IMPORT_OK 47.0.0`; VERSION 2.0.0;
  `.deb` 2.0.0 SHA256 `4783af823dab1d4b3c8ffda82c8f6521cbf1dd1a0bb1c18342f6e96d2c4b69c1`;
  manifiesto beta 1.99.2 firmado Ed25519 y verificado; pytest 282 passed + 2 fallos por root.
- Ancla OTA rotada: clave privada Ed25519 en `D:\AGUSTIN\Portafolio\Proyectos\lrp-keys\lrp-ota-priv.pem`
  (fuera del repo, nunca versionada); pública en `scripts/debian/lrp-ota-pub.pem` y en
  `backend/ota_security.py:15`.
- Auditoría pre-merge (agente independiente, head `7d95326`): pytest 284 passed exit 0 (398 s),
  `check_css_sync` 0, `node --check` 0, `bash -n` 15 scripts 0, `merge-tree 98bb9f1 main 7d95326`
  exit 0, 16 tests OTA/seguridad/resiliencia passed. Veredicto NO APTO por AUD-001..003.
- Savepoint receipt: bundle `backups/linuxremoteplayer-savepoint-beta-foundation-20260823.bundle`
  SHA256 `ebcf392c…`, zip SHA256 `f78fdb42…`, both verified complete; no absolute Drive path.
- Task statuses, commit IDs and closure evidence are owned by
  [`PLAN_v2.0-appliance.md`](PLAN_v2.0-appliance.md); not duplicated here.

## Current facts

- Closed plan: `PLAN_v2.0-appliance.md` (G4 APTO). Archived: `archive/PLAN_v1.99-beta-foundation.md`.
- Owner-accepted residuals: `TST-DEVICE-001`, `TST-STT-001`, `TST-OTA-001`; `TESTING.md` owns them.
- Backup state is `complete`; receipt detail is in `CONTEXT.md`.
- Stable `1.9.1` remains isolated; beta `1.99.2` is opt-in and does not discover stable.
- D48/D49/D50 remain in force: Zero-IO en modelos pesados, workers flash persistentes, briefs
  guiados unitarios.
