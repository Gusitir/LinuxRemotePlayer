# TESTING — checks v3

```yaml
assurance: Standard
historical_snapshot: archive/TESTING_legacy_2026-08-21.md
device_owner: dueño
format: "[OK] / [FAIL: reason] / [SKIP: reason]"
```

## REQUIRED CHECKS

- TST-BETA-CHANNEL-001 [SKIP: requiere evidencia del dueño en HTPC: curl instala 1.99.1,
  `dpkg -V`, VERSION 1.99.1, `LRP_CHANNEL=beta`, restart/health, `/api/config` channel beta,
  `/api/update/check` current/latest 1.99.1 sin update y stable `/latest.json` 1.9.1.]
- TST-BETA-UPDATE-002 [SKIP: requiere futura beta 1.99.2 para probar 1.99.1->1.99.2 preservando
  canal/config/servicio; diferido y no bloquea BETA-FOUNDATION porque el plan exige lectura del
  manifiesto beta, no una build futura.]
- TST-BETA-MODEL-001 [SKIP: milestone BETA-STT no iniciado; cada beta/modelo requiere 12 comandos
  ES y 6 EN con resultado, latencia percibida, fallo/rechazo y estado offline.]
- TST-DEVICE-001 [SKIP: device real no disponible; bloquea validación de instalación limpia,
  upgrade, operación offline y desinstalación.]
- TST-STT-001 [SKIP: hardware y laboratorio PH21 no disponibles; bloquea selección de runtime,
  benchmark y decisión de pipeline local.]
- TST-OTA-001 [SKIP: artefactos y entorno de campo no disponibles; firma, downgrade, interrupción y
  rollback bloquean 2.0.0 estable, no la beta opt-in cuyo riesgo aceptó el dueño.]
Estos checks son requeridos, no opcionales. No se inventan resultados frescos ni se usa el snapshot
histórico para certificar 2.0.0.
