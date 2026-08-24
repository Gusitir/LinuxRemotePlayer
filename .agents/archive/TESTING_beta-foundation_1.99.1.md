# TESTING - checks v3

```yaml
assurance: Standard
device_owner: dueño
format: "[OK] / [FAIL: reason] / [SKIP: reason]"
```

## AUTOMATIZABLE POR IA EN HTPC

Estos checks requieren un HTPC real y siguen no disponibles hasta autorización explícita del dueño.
La IA inspecciona antes de ejecutar; no se autoaprueba ni edita control state, `/opt` o tests.

### Protocolo AI

- CAVEMAN: salida breve, técnica, literal y accionable.
- Pedir aprobación explícita antes de `sudo`, instalación, restart o acción destructiva.
- Nunca mostrar `.env`, tokens o licencias; solo puede imprimir `LRP_CHANNEL`.
- Ejecutar `dpkg -V` antes de declarar válido el paquete.
- STOP ante mismatch de hash, versión, canal o servicio.
- Registrar comandos literales, exit codes, salida decisiva, no verificado, riesgos y recomendación.
- La recomendación puede ser `APTO`; el veredicto lo emite el Arquitecto.

### TST-BETA-CHANNEL-001

`[OK]` cápsula técnica AI completada con autorización del dueño el 2026-08-23:

1. Verificar manifiestos públicos:
   - `curl -fsS https://www.linuxremoteplayer.com/latest.json` -> `version` `1.9.1`.
   - `curl -fsS https://www.linuxremoteplayer.com/beta/latest.json` -> `version` `1.99.1`.
   - `curl -fsSL https://www.linuxremoteplayer.com/beta/downloads/linuxremoteplayer_1.99.1_all.deb | sha256sum` ->
     `8d4a19834eca05eda0e3f8b9c77817e6baaa19fb1bd823e30b5a726b6cb9c894`.
2. Tras aprobación explícita del dueño, ejecutar una sola instalación pública:
   - `curl -fsSL https://www.linuxremoteplayer.com/beta/install.sh | sudo bash` -> exit 0 o
     salida literal de configuración requerida.
3. Validar paquete antes de reiniciar:
   - `dpkg -V linuxremoteplayer` -> sin salida.
   - `dpkg-query -W -f='${Version}\n' linuxremoteplayer` -> `1.99.1`.
   - `grep -E '^LRP_CHANNEL=beta$' /opt/linuxremoteplayer/backend/.env` -> solo
     `LRP_CHANNEL=beta`; no imprimir el archivo completo.
4. Reiniciar solo después de autorización del dueño y comprobar servicio:
   - `systemctl is-active linuxremoteplayer.service` -> `active`, o
     `systemctl --user is-active linuxremoteplayer.service` -> `active` para servicio de usuario.
   - `curl -kfsS https://127.0.0.1:8000/health` -> `{"status":"ok"}`.
5. Validar configuración sin secretos:
   - `curl -kfsS https://127.0.0.1:8000/api/config` -> versión `1.99.1`, canal `beta`.
   - `curl -kfsS https://127.0.0.1:8000/api/update/check` -> `current` y `latest` `1.99.1`,
     `update_available: false`.
6. Repetir el manifiesto estable y confirmar públicamente `1.9.1`; no probar todavía una beta
   `1.99.2`.

**Capsule obligatoria:** `environment`; `commands + exit`; `decisive output`; `not verified`;
`risks`; `recommendation`.

#### Resultados TST-BETA-CHANNEL-001 — 2026-08-23

Ejecutado por IA en HTPC del dueño con luz verde explícita. Pre-requisito cumplido: stable
`1.9.1` removida por completo (purge + residuos) y verificada antes de instalar.

1. Manifiestos públicos `[OK]`: `latest.json` -> `version` `1.9.1`; `beta/latest.json` ->
   `version` `1.99.1`; hash de `.deb` beta coincide con manifiesto (`8d4a19...c894`, exit 0).
2. Instalación pública `[OK]`: `curl -fsSL https://www.linuxremoteplayer.com/beta/install.sh |
   sudo bash` -> exit 0, instalador verifica suma (`La suma coincide`) y emite salida literal
   de configuración requerida (`FALTA UN PASO ... sudo lrp-setup`; setup interactivo sin TTY).
   Completado con `sudo lrp-setup` bajo pty aceptando defaults (usuario `gus`, dedicada `S`,
   suspensión `S`, layout detectado `es`) -> exit 0, servicio habilitado e iniciado.
3. Paquete pre-restart `[OK]`: `dpkg -V linuxremoteplayer` -> sin salida; `dpkg-query -W` ->
   `1.99.1`; `grep -E '^LRP_CHANNEL=beta$' /opt/linuxremoteplayer/backend/.env` (con sudo,
   solo línea del canal) -> `LRP_CHANNEL=beta`.
4. Servicio `[OK]`: `systemctl restart linuxremoteplayer.service` -> exit 0; `systemctl is-active` ->
   `active`; `curl -kfsS https://127.0.0.1:8000/health` -> `{"status":"ok"}`.
5. Configuración sin secretos `[OK]`: `/api/config` -> `version` `1.99.1`, `channel` `beta`;
   `/api/update/check` -> `current` y `latest` `1.99.1`, `update_available: false`.
6. Manifiesto estable re-verificado `[OK]`: público sigue `1.9.1`; beta sigue `1.99.1` (sin
   `1.99.2` que probar). Caso de campo con instalación estable ya instalada `[SKIP: no ejecutado;
   owner D29 lo declara no aplicable por ausencia de usuarios.]` La prueba técnica de manifiesto
   estable permanece `[OK]`.

**Not verified by AI:** certificado en browser real, QR/PIN y onboarding PWA, kiosk/touchpad/media;
owner los cubrió mediante `TST-BETA-HUMAN-001`.
**Risks:** el setup aceptó defaults que habilitan UFW y deshabilitan suspensión/DPMS del sistema
(modo appliance); autologin requiere configuración manual según DM; el instalador imprime token de
enlace directo en pantalla, no registrado aquí.
**Recommendation:** cápsula técnica completa; sin veredicto del Arquitecto.

### Deferred

- `TST-BETA-UPDATE-002` `[SKIP: requiere futura 1.99.2; debe probar 1.99.1->1.99.2 preservando
  canal/config/servicio; no bloquea BETA-FOUNDATION.]`
- `TST-BETA-MODEL-001` `[SKIP: milestone BETA-STT futuro; requiere 12 comandos ES + 6 EN con
  métricas, rechazo/fallo y estado offline.]`
- `TST-STT-001` `[SKIP: requiere hardware/laboratorio PH21 y autoridad del Arquitecto para decidir
  runtime/modelo.]`
- `TST-OTA-001` `[SKIP: requiere artefactos, entorno de campo y autoridad del Arquitecto/dueño para
  firmar, probar downgrade, interrupción y rollback.]`

## SOLO PARA HUMANO

- `TST-BETA-HUMAN-001` `[OK: owner 2026-08-23]`: certificado/browser, QR/PIN, onboarding PWA,
  kiosk, touchpad y media fueron probados manualmente y resultaron OK.
- `TST-DEVICE-001` `[SKIP: offline/uninstall/upgrade no ejecutados; owner acepta la deferral y
  confía en la implementación existente.]`

Los checks externos son requeridos, no opcionales. No se inventan resultados ni se reutiliza el
snapshot histórico para certificar 2.0.0.
