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
active_task: T-152 apto; T-154 (ISO 1.0.0 + gates) siguiente; T-153 APK y T-155 publicación después
last_verdict: APTO (T-150, T-151 y T-152)
verdict_scope: "T-150 (F1) apto: GPL-3.0, sin licencia/voz/modo, sin OTA ni Supabase; gate de fase 250 passed. T-151 (F2) apto: panel compacto, Bluetooth on/off real, B37 y onboarding web por plataforma. T-152 (F3) apto: web 1.0.0 desplegada y verificada en producción (`e9c67c7`, Vercel, 0 rastros comerciales) y documentación completa (`f152331`: README, arquitectura, build, DEPLOY, SECURITY, terceros)."
next_action: "T-154: medir/construir la ISO 1.0.0 en WSL (clon nativo bajo ~), verificar instalación limpia en el HTPC y `dpkg -V`; en paralelo o después T-153 (APK TWA); cerrar con T-155 (release + repo público + B38/B39)."
```

## Blockers

- **B38 bloquea la publicación**: las capturas de la web y del README muestran logos de Netflix/
  YouTube/Spotify/TikTok y el botón de micrófono del control viejo. Hay que reemplazarlas por capturas
  1.0.0 reales antes de T-155.
- **B39**: revisión legal de `terminos`/`terms`, `SECURITY.md` y `THIRD_PARTY_LICENSES.md` antes de
  publicar.
- **Repo público desde el inicio (D56)** exige antes de la primera release: auditoría de secretos en
  toda la historia. Se hace en T-155.
- **TWA/APK**: dominio decidido `www.linuxremoteplayer.com` (Vercel, `linux-remote-player.vercel.app`
  como alias). `assetlinks.json` se sirve desde ese dominio en T-153.
- **Hosting de binarios (decidido 2026-10-29)**: **ISO + APK + `SHA256SUMS` en GitHub Releases** (repo
  público, límite 2 GiB/asset; medir la ISO en T-154 y partirla si excede). **Web en Vercel por
  integración Git** (push a `main`), documentada en T-152; sin CI ni `vercel` CLI. Plan B si la ISO
  supera 2 GiB: Cloudflare R2 con subdominio propio.
- **Sin OTA (D56)**: no hay auto-update; cualquier fix futuro se publica como release nueva y se
  reinstala. Documentado como decisión, no como deuda.
- Checks de dispositivo aún abiertos: `TST-LRP-SPLASH-001` (splash GRUB/plymouth) y
  `TST-LRP-POINTER-001` (cursor visible). El resto de D53 se cerró por captura.
- `dpkg -V` divergente en el HTPC por despliegue SSH; se normaliza al instalar la ISO 1.0.0 (T-154).

## Fresh evidence

- **T-152 apto (F3)**: `e9c67c7` publica la web 1.0.0 (ES/EN) y Vercel la sirve con deploy nuevo
  (`x-vercel-id` distinto, `age: 0`, `last-modified` = `date`): HTTP 200, “1.0.0”, “GPL”, enlaces a
  Releases y **0** rastros de Paddle/premium/latest.json/.deb/install.sh en home y `/en/`.
  `f152331` añade README, `docs/ARCHITECTURE.md`, `docs/DEVELOPING.md`, `docs/DEPLOY.md`,
  `SECURITY.md` y `THIRD_PARTY_LICENSES.md`, sin términos comerciales y con links relativos en 0 roto.

- **F1 cerrada (T-150)**: gate de fase `pytest tests/` = **250 passed** (376 s) tras la poda de tests de
  licencia/OTA/Supabase; commits `ee93f4c`, `30dbd69`, `180f717`, `d5b75f7`, `878d948`, `3cf38ed`,
  `6df950e`. HTPC desplegado (main.py, run.py, status.html, index.html, app.js): unit activa, kiosk
  único con `--new-instance`, `/api/status` con 8 claves, `/api/update/check` 404, `ota_security`
  ausente, 0 referencias Supabase/update en runtime. Captura final sin licencia, voz ni actualización.
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
