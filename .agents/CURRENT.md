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
active_task: T-149 apto (cde09c8); T-144 apto (5cd1eeb); T-145 ready
last_verdict: APTO (T-149 y T-144)
verdict_scope: "T-149: B20–B26 corregidos, auditoría determinística y despliegue verificado en el HTPC el 2026-10-22. T-144: auditor independiente APTO (7/7, defectos none), `pytest tests/` 285 passed y backend desplegado/verificado en el HTPC el mismo día. Ambos commiteados el 2026-10-27; los checks visuales del dueño siguen pendientes."
next_action: "T-145 (PH24 frontend: sin compra, clave, plan ni takeover) y, cuando el HTPC vuelva a estar en red, cerrar los [pendiente] de TESTING.md (splash, panel, audio, Wi-Fi/Pantalla/Bluetooth, puntero) antes de reconstruir la ISO definitiva."
```

## Blockers

- **HTPC de pruebas no alcanzable** desde el 2026-10-27: `192.168.0.246:22` responde
  `No route to host` (equipo apagado o fuera de la red). Toda verificación de dispositivo posterior
  requiere que el dueño lo encienda y confirme la IP; las evidencias de dispositivo son del 2026-10-22.
- Publicación del manifiesto estable `2.0.0` bloqueada por PH24: requiere T-145 y T-146 (y T-147 del
  dueño) antes de servir `website/latest.json` 2.0.0.
- **La ISO definitiva no se reconstruye hasta cerrar el ciclo** (D53): debe incluir los deltas de
  `[T-149]`/`[T-144]` ya commiteados y repetir instalación limpia y arranque.
- Checks visuales/humanos pendientes del dueño: `TST-LRP-SPLASH-001`, `TST-LRP-PANEL-001`,
  `TST-LRP-AUDIO-001`, `TST-LRP-WIFI-DISPLAY-BT-001`, `TST-LRP-POINTER-001` (`TESTING.md`, D53).
- Secure Boot en hierro sin confirmar: el arranque verificado fue UEFI con ESP firmado ya escrito.
- Cleanup of external WSL audit clones remains unauthorized.

## Fresh evidence

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
