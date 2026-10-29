# CURRENT — estado vivo v3

```yaml
version: 3
updated_at: 2026-10-27T21:40:00-05:00
source_commit: 5cd1eeb
workspace_root: "G:/AGUSTIN/Portafolio/Proyectos/Proyecto WebApp - LinuxRemotePlayer (migrado desde D: el 2026-10-22)"
product_branch: main
product_branch_head: 5cd1eeb
product_branch_state: "main == origin/main tras el push del 2026-10-27; T-149 y T-144 integrados"
dirty: false
assurance: Standard
active_job: RUN THE LOOP
active_plan: PLAN_v2.0.0-release.md (approved, D51) + T-149 estabilización (D53)
active_task: T-149 (panel + kiosk `3a385c2`, sin push); T-144 apto (`5cd1eeb`); T-145 ready
last_verdict: APTO (T-143, T-144, T-149 inventario y T-149 UI/kiosk)
verdict_scope: "T-149: B20–B26 y luego B27–B36 (panes, caché, grilla, `?tab`, voz `open_settings`, robustez de kiosk con D1–D4) corregidos; auditor independiente APTO con `pytest tests/` = 289 passed y verificación en el HTPC por capturas reales y ciclos kill/launch idempotentes. T-144: APTO (7/7) con backend desplegado. Commits locales `cde09c8`, `5cd1eeb`, `3a385c2`; push pendiente del dueño. Quedan splash y puntero como checks del dueño."
next_action: "push de `3a385c2` cuando el dueño lo autorice; luego T-145 (PH24 frontend, incluido B37 Wi-Fi/cable) y reconstruir la ISO definitiva con todos los deltas antes de T-148."
```

## Blockers

- **Commit local `3a385c2` sin push**: `[T-149]` panel + kiosk queda en `main` local; el dueño
  autoriza el push.
- **El appliance ya no coincide con el `.deb` instalado**: `dpkg -V linuxremoteplayer` reporta checksums
  divergentes (módulos de backend de T-144, `frontend/status.html` y ahora `kiosk.py`/`main.py`), porque
  el ciclo D53 despliega por SSH. Es esperado; se resuelve empaquetando 2.0.0 y reinstalando en T-148.
  Mientras tanto el equipo no es representante válido del paquete (regla de `AGENTS.md`).
- Publicación del manifiesto estable `2.0.0` bloqueada por PH24: requiere T-145 y T-146 (y T-147 del
  dueño) antes de servir `website/latest.json` 2.0.0.
- **La ISO definitiva no se reconstruye hasta cerrar el ciclo** (D53): debe incluir los deltas de
  `[T-149]`/`[T-144]` ya commiteados y repetir instalación limpia y arranque.
- Checks del dueño pendientes: `TST-LRP-SPLASH-001` (splash GRUB/plymouth) y `TST-LRP-POINTER-001`
  (cursor visible con mouse). Panel, audio y Wi-Fi/Pantalla/Bluetooth ya cerrados por captura
  (`TESTING.md`, D53).
- Secure Boot en hierro sin confirmar: el arranque verificado fue UEFI con ESP firmado ya escrito.
- Cleanup of external WSL audit clones remains unauthorized.

## Fresh evidence

- Lote UI/kiosk del 2026-10-29 (`[T-149]`, commit `3a385c2`; auditor APTO, 289 tests): panes
  exclusivos (B27), grilla 2x2 en Ajustes con `align-items:start` (B32/B36), `?tab=` (B31),
  `Cache-Control: no-store` (B29) y `?v=<epoch>` (B30), voz `open_settings` a `?tab=settings` (B33) y
  kiosk robusto (B34: espera de salida, limpieza de `lock`/`.parentlock`/`.startup-incomplete`,
  `--new-instance`, detección por `-profile`+`realpath`, cooldown 30/120 s). Capturas reales:
  Emparejamiento limpio y Ajustes con audio HDMI 40 %, 5 redes Wi-Fi, `HDMI-1 1920x1080@60` y
  Bluetooth encendido.
- Kiosk recuperado en el HTPC: perfil corrupto movido a `~/.config/lrp-kiosk-firefox.broken-*`,
  perfil nuevo recreado por el backend, un único Firefox con `--new-instance`, sin bucle en 30 s ni
  tras dos ciclos kill/launch.
- Barrido post-reinicio del 2026-10-29 (`asistente`, solo lectura): equipo encendido en
  `192.168.0.246`, `up 1 minute`, 0 unidades fallidas, backend y SSH activos, `/api/status` con
  `version=2.0.0 licensed=true license_source=local network_ips=[enp2s0: 192.168.0.246] kiosk_active=true`,
  audio con 1 sink HDMI activo, pantalla `HDMI-1 1920x1080@60`, Bluetooth encendido, 27 redes Wi-Fi.
  Fixes persistidos tras reboot: `/etc/hosts` (3 líneas), `zramswap` masked, drop-in de sesión
  (`XDG_RUNTIME_DIR`+`DBUS_SESSION_BUS_ADDRESS`), `grep 'startx -- -nocursor'` = 0, tema plymouth `lrp`
  en el initramfs (4 entradas) y `lrp-splash.png` en `grub.cfg` (2 referencias). Xorg corre `:0 vt1`
  sin `-nocursor`. `dpkg -V` divergente (5 checksums) por despliegue fuera del paquete.
- `main` en `5cd1eeb` (`[T-144] PH24 backend sin licencia ni proxy cloud`), precedido por `cde09c8`
  (`[T-149] Estabiliza appliance: hosts, zram, NVRAM, audio, splash y puntero`) y `8fb13e9`; tras el
  `[STATE]` del 2026-10-27 el árbol queda limpio y `git rev-list --left-right --count origin/main...main`
  = `0 0`.
- Gates del 2026-10-27 sobre el árbol commiteado: `python -m py_compile` de los cuatro módulos del
  backend = 0; `pytest -q tests/test_iso_factory.py tests/test_t125_installer.py
  tests/test_security_mitigations.py tests/test_local_intent.py tests/test_local_stt.py` = 42 passed.
  Auditoría T-144 previa: `pytest tests/` = 285 passed y greps de licencia en `backend/` = 0 matches.
- Appliance (verificado el 2026-10-22, hoy inalcanzable): UEFI con `Boot0002` →
  `\EFI\BOOT\BOOTX64.EFI`, `VERSION` 2.0.0, `dpkg -V linuxremoteplayer` limpio, backend activo en
  `0.0.0.0:8000`, SSH activo, autologin `lrp` en tty1, kiosk 1920x1080, audio PipeWire con sink HDMI
  (vol 40 %), `network_ips: ["enp2s0: 192.168.0.246"]` y Xorg `:0 vt1` **sin** `-nocursor` tras B26.
- ISO 2.0.0 vigente (pre-PH24, no reutilizable para el release):
  `G:\AGUSTIN\Portafolio\Proyectos\lrp-iso\lrp-os_2.0.0_amd64.iso`, SHA256
  `720fc8370f83344a982d77ba48f2c63fb2cfc882f5e2296ea57ad7639843fbfb`.
- Savepoint y backups previos siguen válidos; `lrp-keys/` y `lrp-iso/` viven en
  `G:\AGUSTIN\Portafolio\Proyectos\`.

## Current facts

- Plan activo: `PLAN_v2.0.0-release.md`; T-143, T-149 y T-144 aptos; T-145 ready; T-146..T-148 pendientes.
- Tríada persistente D54 operativa (`coder`/`auditor`/`asistente`); `CONTEXT.md` D53/D54 registran la
  decisión, el cambio de disco `D:`→`G:` y el contrato de recibos.
- `.worktrees/` siguen apuntando a `D:` (prunable) y `lrp-iso/run-vm.sh` usa `/mnt/d`; ambos fuera de
  alcance hasta nuevo aviso. WSL `Debian` conserva `live-build`/`xorriso`; QEMU no está instalado.
- `backend/.venv` y `node_modules` no se copiaron (replicables). Los gates corren con Python 3.14 global.
- Residuo inocuo de PH24 fuera de backend: `scripts/install.sh`, `build_deb.sh` y `uninstall.sh` aún
  mencionan `.license_cache`, y el `.env` local (gitignored) conserva `LICENSE_*` sin lector.
- D48/D49/D50 y D54 siguen en vigor: Zero-IO en modelos pesados, briefs unitarios con anclas y tríada
  persistente con recibos deterministas.
