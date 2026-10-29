# CURRENT — estado vivo v3

```yaml
version: 3
updated_at: 2026-10-29T03:10:00-05:00
source_commit: f698e18
workspace_root: "G:/AGUSTIN/Portafolio/Proyectos/Proyecto WebApp - LinuxRemotePlayer"
product_branch: main (1.0.0 open source)
product_branch_state: "legacy/2.0 + v2.0.0-legacy archivados y publicados; main inicia 1.0.0 con LICENSE GPL-3.0"
dirty: true
assurance: Standard
active_job: RUN THE LOOP
active_plan: PLAN_v1.0.0-public.md (approved, D56)
active_task: T-150a frontend (limpieza comercial, voz oculta y modo appliance) en ejecución
last_verdict: APTO (T-149) — ciclo legacy cerrado; F1 no tiene veredicto todavía
verdict_scope: "T-149 quedó APTO y publicado (cde09c8, 3a385c2) con panel y kiosk verificados por captura y auditoría de 289 tests. D56 cambia el producto a ISO open source 1.0.0; desde acá rige PLAN_v1.0.0-public.md."
next_action: "cerrar T-150 (a frontend, b backend, c OTA, d Supabase), luego T-151 (panel compacto + onboarding QR iOS/Android + B37 + Bluetooth acotado); la ISO se reconstruye recién en T-154."
```

## Blockers

- **Repo público desde el inicio (D56)** exige antes de la primera release: auditoría de secretos en
  toda la historia y revisión de assets de terceros (logos de apps, fondos de skins, fuentes). Se hace
  en T-152, no al final.
- **TWA/APK** requiere dominio propio con `assetlinks.json`; si el dominio cambia, la APK deja de
  verificar. Decisión de dominio pendiente para T-153.
- **Hosting de la ISO (~2 GB)** por definir antes de T-155.
- **Sin OTA (D56)**: no hay auto-update; cualquier fix futuro se publica como release nueva y se
  reinstala. Documentado como decisión, no como deuda.
- Checks de dispositivo aún abiertos: `TST-LRP-SPLASH-001` (splash GRUB/plymouth) y
  `TST-LRP-POINTER-001` (cursor visible). El resto de D53 se cerró por captura.
- `dpkg -V` divergente en el HTPC por despliegue SSH; se normaliza al instalar la ISO 1.0.0 (T-154).

## Fresh evidence

- `legacy/2.0` + tag `v2.0.0-legacy` publicados en `origin`, con `LICENSE` GPL-3.0 y `NOTICE` en el
  commit `e452c9a`. `main` parte de `f698e18`.
- `LICENSE` de `main` reemplazado por GPL-3.0 (553 líneas) + `NOTICE` con copyright 2026 Gusitir y
  acreditación de terceros; pendiente de commit (T-150).
- T-149 cerrado y publicado: `pytest tests/` = 289 passed, capturas reales del panel (Emparejamiento y
  Ajustes 2x2 con datos), kiosk robusto (B34) y HTPC sano en `192.168.0.246` (UEFI, backend activo,
  audio HDMI, `HDMI-1 1920x1080@60`, Bluetooth on, 5 redes Wi-Fi).
- Voz/micrófono: quedan ocultos y desactivados hasta T-157 (Needle 3 / voice-to-text), sin borrar el
  backend de voz.

## Current facts

- Plan vigente: `PLAN_v1.0.0-public.md` (D56). `PLAN_v2.0.0-release.md` es histórico del ciclo anterior.
- Producto 1.0.0: ISO Debian → panel → control por móvil; Android APK TWA (sideload), iOS PWA con
  tutorial; sin nube, licencia, premium, cuentas, telemetría ni OTA.
- Licencia GPL-3.0 en ambos planos (main y legacy). La web deberá mostrar avisos de licencia y créditos.
- El HTPC de pruebas (`192.168.0.246`, `lrp`/`lrp`) sigue operativo con el código 2.0.0 desplegado; es
  banco de pruebas hasta que exista la ISO 1.0.0.
- `.worktrees/` siguen apuntando a `D:` (prunable); `lrp-iso/run-vm.sh` usa `/mnt/d`; QEMU no está en
  WSL. No bloquean F1.
- Tríada D54 (`coder`/`auditor`/`asistente`) activa; D48/D49/D50 siguen en vigor.
