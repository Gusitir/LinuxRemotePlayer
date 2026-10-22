# CURRENT — estado vivo v3

```yaml
version: 3
updated_at: 2026-10-21T19:20:00-05:00
source_commit: db97991
product_branch: codex/debian-foundation (integrada en main)
product_branch_head: d3495ab
product_branch_state: merged into main via --no-ff (ad30b95); main == origin/main
dirty: false
assurance: Standard
active_job: RUN THE LOOP
active_plan: PLAN_v2.0.0-release.md (approved, digest 2814bb3c…, D51)
active_task: T-143 apto; T-144 ready
last_verdict: APTO
verdict_scope: T-143 apto. Auditor independiente dio APTO en `9d60785` y APTO final en `d3495ab` (delta ISO). Merge `--no-ff` en `ad30b95`, corrección de beta congelado `db97991`, push a origin/main (`0 0`). `VERSION` 2.0.0 en main; 20/20 tests de release/OTA/ISO pasan sobre el merge.
next_action: Ejecutar T-144 (PH24 backend sin licencia ni proxy cloud) sobre main limpio; luego T-145 frontend, T-146 web/docs con publicación del manifiesto estable, T-147 Supabase y T-148 gates.
```

## Blockers

- Merge y push de `codex/debian-foundation` BLOQUEADOS: auditoría pre-merge `NO APTO` (AUD-001..003
  en `BUGS.md`). No se integra ni publica hasta un veredicto APTO sobre el head corregido.
- Merge y push de v2.0 ejecutados con APTO del auditor (`d3495ab`); no hay bloqueo de integración.
- Push, merge y deploy adicionales requieren autorización explícita del dueño; `main` está en
  `db97991` y sincronizado con `origin/main`.
- Publicación del manifiesto estable `2.0.0` bloqueada por el gate PH24: requiere T-144, T-145 y
  T-146 antes de servir `website/latest.json` 2.0.0.
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
- ISO 2.0.0 vigente, head `be39761`: `lrp-os_2.0.0_amd64.iso`, SHA256
  `816bd924c973e522c08433119cb0284a6eca58756d5eb1bd27ee087fa96e6f9c` (copia en
  `D:\AGUSTIN\Portafolio\Proyectos\lrp-iso\`). Arranque verificado en QEMU UEFI (OVMF): autologin
  `lrp` en tty1, `startx`/Openbox, backend activo y panel de emparejamiento con PIN y QR a pantalla
  completa (captura `lrp-iso/boot_e.png`). Correcciones de arranque: `isofs` en initramfs, MBR
  isohybrid (modo DD), `.deb` fuera de `/tmp`, autologin sin greeter y política Firefox con la CA
  local. Obsoletas todas las ISO previas (`f8611e13…` a `b76a44af…`).
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
