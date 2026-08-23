---
name: reindex
description: Suplemento project-local del job global REINDEX para auditar APPCORE e INDEX contra el repo real.
---

# `reindex` — suplemento local

El job global `REINDEX` es la autoridad. Actualiza `APPCORE.md` e `INDEX.md` con evidencia del repo
real; esta skill no crea otro propietario ni registra bitácora en `CURRENT.md`.

## PROCEDIMIENTO

1. Confirmar source commit y dirty state.
2. Comparar endpoints, gates, archivos críticos, WebSocket y configuración contra `APPCORE.md`.
3. Verificar rutas de navegación y referencias contra el repo; corregir `INDEX.md` con hechos reales.
4. Registrar solo hechos verificados, en entradas cortas; no pegar código ni inventar componentes.
5. Entregar evidencia al job global, que decide y aplica ambos cambios.

No actualizar `CURRENT.md` como diario. No modificar producto fuera del alcance del job global.
