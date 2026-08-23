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

`[SKIP: evidencia HTPC del dueño no ejecutada]` hasta completar este brief:

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

- `TST-BETA-HUMAN-001` `[SKIP: revisión del dueño no ejecutada]`: inspeccionar landing ES/EN en
  desktop y mobile; legibilidad de copy/comando; claridad de preguntas del instalador; certificado,
  QR/PIN y onboarding PWA; touchpad, teclado, media y kiosk reales; UI muestra beta/versión y estado
  sin update; registrar problemas subjetivos con `[OK]`, `[FAIL: reason]` o `[SKIP: reason]`.
- `TST-DEVICE-001` `[SKIP: experiencia de device humana no ejecutada]`: instalación limpia, upgrade,
  offline y desinstalación; requiere juicio y evidencia del dueño.

Los checks externos son requeridos, no opcionales. No se inventan resultados ni se reutiliza el
snapshot histórico para certificar 2.0.0.
