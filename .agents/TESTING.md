# TESTING - checks v3

```yaml
assurance: Standard
device_owner: dueño
format: "[OK] / [FAIL: reason] / [SKIP: reason]"
```

## AUTOMATIZABLE POR IA EN HTPC

Checks vivos para el siguiente ciclo. Las cápsulas completadas de BETA-FOUNDATION están archivadas
en [`archive/TESTING_beta-foundation_1.99.1.md`](archive/TESTING_beta-foundation_1.99.1.md).

### Protocolo AI

- CAVEMAN: salida breve, técnica, literal y accionable.
- Pedir aprobación explícita antes de `sudo`, instalación, restart o acción destructiva.
- Nunca mostrar `.env`, tokens o licencias; solo puede imprimir `LRP_CHANNEL`.
- Ejecutar `dpkg -V` antes de declarar válido el paquete.
- STOP ante mismatch de hash, versión, canal o servicio.
- Registrar comandos literales, exit codes, salida decisiva, no verificado, riesgos y recomendación.
- La recomendación puede ser `APTO`; el veredicto lo emite el Arquitecto.

### BETA-STT

- `TST-BETA-UPDATE-002` `[SKIP: deferred until beta 1.99.2; nonblocking residual from closed
  BETA-FOUNDATION.]`
- `TST-BETA-MODEL-001` `[SKIP: upcoming BETA-STT; execute 12 comandos ES + 6 EN with metrics,
  rejection/failure and offline state.]`

## SOLO PARA HUMANO

- `TST-STT-001` `[SKIP: requires PH21 hardware/lab and Architect authority for runtime/model
  decision.]`
- `TST-OTA-001` `[SKIP: requires field artifacts and Architect/owner authority for signing,
  downgrade, interruption and rollback.]`
- `TST-DEVICE-001` `[SKIP: offline/uninstall/upgrade deferred by owner acceptance from
  BETA-FOUNDATION.]`

Completed beta channel and human evidence are historical; do not copy their raw results into this
live matrix or use them to certify `2.0.0`.
