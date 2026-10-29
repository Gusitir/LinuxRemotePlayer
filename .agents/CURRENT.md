# CURRENT — estado vivo v3

```yaml
version: 3
updated_at: 2026-10-29T17:25:00-05:00
source_commit: ae658a9
workspace_root: "G:/AGUSTIN/Portafolio/Proyectos/Proyecto WebApp - LinuxRemotePlayer"
product_branch: main (1.0.0)
product_branch_state: "público en GitHub; release v1.0.0 publicado como latest; árbol limpio"
dirty: false
assurance: Standard
active_job: PAUSED (esperando checks del dueño; retomable con T-154c)
active_plan: PLAN_v1.0.0-public.md (D56; T-150..T-153 y T-155 aptos, T-154 con gate QEMU y física pendiente)
active_task: T-154 pendiente solo de instalación física; T-157 (voz) diferida
last_verdict: APTO (T-150, T-151, T-152, T-153, T-155) + gate QEMU de T-154
verdict_scope: "LRP OS 1.0.0 publicado: repo público, release v1.0.0 con ISO/APK/SHA256SUMS, web 1.0.0 en producción, documentación GPL-3.0. Quedan como checks exclusivos del dueño la instalación física de la ISO, el APK en un Android real y la revisión legal de términos (B39)."
next_action: "cuando el dueño retome: instalar lrp-os_1.0.0_amd64.iso en el HTPC, correr `dpkg -V` y los checks de TESTING (splash, puntero, audio, red, pantalla, BT), probar lrp-1.0.0.apk en Android, y luego cerrar T-154 y el plan (CLOSE)."
```

## Blockers

- **T-154c pendiente (dueño)**: instalación física de la ISO 1.0.0 en el HTPC — borra el disco y
  requiere al dueño delante. Incluye `dpkg -V` y los checks de `TESTING.md` (`1.0.0 · release público`).
- **TST-APK-001 pendiente (dueño)**: el APK no se probó en hardware Android real; solo se verificó
  compilación, firma (`apksigner`, CN=LRP OS) y descarga (200/24 400 B).
- **B39 abierto**: revisión legal de `terminos`/`terms`, `SECURITY.md` y `THIRD_PARTY_LICENSES.md`.
- No hay OTA (D56): cada release se instala desde la ISO; no reintroducir updater.

## Fresh evidence

- **Release público `v1.0.0`** (`https://github.com/Gusitir/LinuxRemotePlayer/releases/tag/v1.0.0`,
  *latest*): ISO `5cc67f101bb507b590085183817ac87f8b1ccd04e2becb1c5e4d5d8972c9f5b2` (2 093 056 000 B),
  APK `fcfb76e0383f5e3e7b72d7805618143945fd24a608ad4dd42df3d159b19c0bef` (24 400 B) y
  `SHA256SUMS` (171 B). Los tres responden 200 y los digests de la API coinciden con los locales.
- **Repo público** `Gusitir/LinuxRemotePlayer` (main); auditoría de secretos previa: sin `.env`,
  claves privadas ni keystores versionados (solo fixtures y una clave pública ya eliminada).
- **Web 1.0.0 en producción** (`www.linuxremoteplayer.com`, Vercel): ISO/APK, avisos GPL, docs; el APK
  se sirve desde el sitio (`/downloads/lrp.apk`, 200/24 400 B) y desde el equipo
  (`https://<IP>:8000/downloads/lrp.apk`, verificado en el HTPC).
- **ISO final** validada en QEMU UEFI: instalación sin intervención, reinicio automático
  (boot_count=2) y arranque desde `Boot0004 LRP-OS` con panel 1.0.0; APK presente en el rootfs.
- **HTPC de pruebas** (`192.168.0.246`, `lrp`/`lrp`): corre el frontend nuevo con `VERSION` 1.0.0,
  kiosk único con `--new-instance`, APK servido localmente.

## Current facts

- Licencia **GPL-3.0** en `main` y en `legacy/2.0` (tag `v2.0.0-legacy`), que archiva el desarrollo
  comercial previo (licencias, OTA, Supabase, web de venta).
- Build reproducible: `.deb` con `scripts/build_deb.sh` y ISO con `scripts/debian/iso/build_iso.sh`
  en clon WSL nativo; el método está en `docs/DEVELOPING.md`. Deploy web: `docs/DEPLOY.md` (Vercel
  por integración Git).
- Artefactos locales: `G:\AGUSTIN\Portafolio\Proyectos\lrp-iso\` (ISO final + `.prev-b2ada72` +
  `.prev-575d82`); claves y keystore en `G:\AGUSTIN\Portafolio\Proyectos\lrp-keys\`
  (`android-release.jks`, `android-release.pass`, `lrp-ota-priv.pem` heredada del ciclo 2.0).
- Worktrees viejos siguen apuntando a `D:` (prunable) y `lrp-iso/run-vm.sh` usa `/mnt/d`: residuos sin
  impacto en 1.0.0.
- Tríada D54 y reglas D48/D49/D50/D57 siguen en vigor; voz/micrófono ocultos hasta T-157 (Needle 3 y
  voice-to-text anotados allí).
