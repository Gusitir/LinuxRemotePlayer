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
active_task: T-156 apto; T-154 pendiente solo de instalación física sobre la ISO 1.0.1; T-157 voz diferida
last_verdict: APTO (T-150..T-153, T-155 y T-156) + gate QEMU de T-154 sobre la ISO 1.0.1
verdict_scope: "LRP OS 1.0.1 publicado con adblock real y anti-popunder: uBlock Origin 1.75.0 vendorizado y forzado por política (offline), prefs anti-popup, watchdog que cierra ventanas ajenas y devuelve el foco, y wmctrl en la ISO. ISO `affcb651…` (1,95 GiB) verificada en QEMU UEFI con panel v1.0.1 desde disco; APK 1.0.1 (`a5624561…`, versionCode 2) dentro del rootfs y publicada. Quedan checks del dueño (instalación física, APK en Android) y B39 legal."
next_action: "con el dueño: instalar `lrp-os_1.0.1_amd64.iso` en el HTPC, `dpkg -V` y checks de TESTING; probar `lrp-1.0.1.apk` en Android; luego CLOSE del plan."
```

## Blockers

- **T-154c pendiente (dueño)**: instalación física de la ISO 1.0.0 en el HTPC — borra el disco y
  requiere al dueño delante. Incluye `dpkg -V` y los checks de `TESTING.md` (`1.0.0 · release público`).
- **TST-APK-001 pendiente (dueño)**: el APK no se probó en hardware Android real; solo se verificó
  compilación, firma (`apksigner`, CN=LRP OS) y descarga (200/24 400 B).
- **B39 abierto**: revisión legal de `terminos`/`terms`, `SECURITY.md` y `THIRD_PARTY_LICENSES.md`.
- No hay OTA (D56): cada release se instala desde la ISO; no reintroducir updater.

## Fresh evidence

- **LRP OS 1.0.1 (adblock + anti-popunder)**: ISO `affcb6517e389fea2269e538de09364f745bdb4f33ba430ee4e95adeb5931d71`
  (2 097 152 000 B, 1,95 GiB) construida desde `3baa610`; dentro del rootfs: `VERSION` 1.0.1,
  `wmctrl`, `uBlock0.xpi` (4 650 100 B) y `frontend/downloads/lrp.apk` con sha `a5624561…`. Gate QEMU
  UEFI: instalación sin intervención, auto-reboot (boot_count=2) y panel **v1.0.1** desde disco.
  Release `v1.0.1` (latest) con ISO, APK `a5624561…` (24 404 B, versionCode 2) y `SHA256SUMS`
  recalculado; los tres assets responden 200.
- **Adblock verificado en hierro**: `adblock_status=ublock`, `extensions.json` con
  `uBlock0@raymondhill.net` activo (1.75.0) y popups cerrados en 3 s y 3 s sin perder el panel.
- **Documentación y web 1.0.1**: README EN/ES, landings y docs apuntan a `v1.0.1` con los hashes
  nuevos (`affcb651…`, `a5624561…`); 0 referencias a artefactos 1.0.0.

- **Documentación y web 1.0.0 (2026-10-29)**: `README.md` reescrito en inglés (principal) con
  `README.es.md` en español neutro y enlace cruzado; `docs/GITHUB_ABOUT.md` con descripción, topics y
  homepage **aplicados al repo** (`gh repo edit`: descripción de una línea, homepage
  `https://www.linuxremoteplayer.com`, 10 topics, visibilidad pública). Hechos verificados contra el
  código: 4 GB RAM mínimo (dato del autor, el instalador no impone mínimo), disco fijo ≥8 GiB que se
  borra completo (GPT: 512 MiB `LRP-BOOT` + resto `LRP-ROOT`), NVIDIA **sin driver por defecto**
  (`nvidia-bootstrap.sh` instala 550.163.01-2 desde Debian 13, opt-in, rechaza Secure Boot), APK =
  app de control Android y PWA para iOS.
- **Web**: hero SVG rehecho (monitor con panel + teléfono), 16 iconos SVG inline (sin emoji), sección
  “El control en tu teléfono” con captura real `website/screenshots/remote_control.webp` (390x699,
  recortada para excluir logos de terceros), requisitos 4 GB/x86_64/UEFI/HD 2500, copy ES neutro y
  EN, espaciado/tap-target/contraste corregidos, header mobile sin desborde, `gracias.html` eliminada.
  Verificado en producción (`7d20bb6`, `5dc1216`): HTTP 200 ES/EN y hechos presentes (4 GB, UEFI,
  HD 2500, GPL, APK, PWA).

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
