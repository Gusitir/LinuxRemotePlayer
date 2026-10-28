# WORKFLOW — extensión subordinada a agents-workflow v3

`AGENTS.md` es la autoridad. CAVEMAN aplica siempre: sin saludos ni relleno; salida breve, técnica,
factual y accionable.

## ROLES

- **Protocolo Cero-IO en modelos pesados (D48)**: Arquitecto (`42a6a909-29da-4d4c-8f81-4e7bafff4cb8`),
  Ingeniero (`fdfc68b2-8383-4854-8f61-737c6e0c101b`) y Auditor (`ae7b054f-900d-4285-87c0-f2cdd49e7888`)
  NUNCA ejecutan lecturas completas, escrituras, búsquedas ni comandos directos; delegan todo a workers
  persistentes con `Model: "flash"` (`Arch-Flash` para Arquitecto; `Eng-Flash-1` Constructor y `Eng-Flash-2`
  Inspector para Ingeniero; `Aud-Flash` para Auditor), los cuales se mantienen vivos toda la fase y se
  terminan (`kill`) al cerrar la fase. Lectura directa en modelos pesados solo permitida por rango
  quirúrgico (`StartLine`/`EndLine` <= 25 líneas) ante duda crítica.
- **Workers Flash y recibos**: respuestas de workers `flash` limitadas a <150 palabras (recibo determinista:
  `git status -s`, `git diff --stat`, `archivo:línea`, exit code de 1 línea).
- Arquitecto (`42a6a909-29da-4d4c-8f81-4e7bafff4cb8`): posee INIT, PLAN, diseño, `.agents`, veredictos y commits
  autorizados; orquesta a Ingeniero y Auditor a través de su worker persistente `Arch-Flash`; audita baches
  de tareas y no escribe producto.
- Ingeniero persistente (`fdfc68b2-8383-4854-8f61-737c6e0c101b`): coordina producto en worktree, redacta
  briefs y orquesta a `Eng-Flash-1` (Constructor) y `Eng-Flash-2` (Inspector); no corre comandos pesados
  ni escribe código directo en su contexto; no se autoaudita ni cambia diseño.
- Verificación Constructor/Inspector (D48): `Eng-Flash-1` implementa según brief; `Eng-Flash-2` (contexto
  `flash` independiente) audita `git diff`, verifica cada criterio con `archivo:línea` y corre micro-checks
  rápidos (<2s: `bash -n`, `py_compile`, `node --check`).
- Auditor (`ae7b054f-900d-4285-87c0-f2cdd49e7888`): búsquedas exhaustivas, resolución de problemas complejos y
  auditoría de cierre de fase completa (`G4`) delegando en `Aud-Flash`; autorizado a usar `/boost` y
  `/teamwork-preview`; sin código ni planificación.
- **Briefs Guiados por Contexto y Tareas Unitarias (D49)**: Arquitecto e Ingeniero NUNCA envían un plan
  completo en one-shot ni delegan búsquedas a ciegas; despachan 1 tarea acotada a la vez (p. ej. primero
  `T-141`, validar recibo, luego `T-142`) e incluyen siempre las rutas exactas, líneas/funciones ancla y
  extracto de contexto de `APPCORE.md`/`INDEX.md` para que el worker `flash` vaya directo al punto sin
  quemar tokens explorando el repo.

## TRÍADA PERSISTENTE (D54, 2026-10-22)

Sustituye los nombres de D48 por tres subagentes con la misma disciplina:

| Rol D54 | Rol D48 | Alcance |
|---|---|---|
| `coder` | `Eng-Flash-1` | Único escritor de producto; write-set cerrado; no commitea ni edita `.agents` |
| `auditor` | `Eng-Flash-2` / `Aud-Flash` | Corre gates propios, verifica `archivo:línea`, dicta `APTO`/`NO APTO`; no corrige |
| `asistente` | `Arch-Flash` | Lecturas, recon, anclas y ops por SSH; read-only sobre el repo |

- Recibo fijo ≤12 líneas: `STATUS`, `FILES`, `GATES`, `DIFFSTAT`, `RISK`, `NEXT`; lo crudo va a archivo.
- Independencia: el auditor recibe brief + diff + gates, nunca la conversación.
- Rotación por fase: los tres se terminan al cerrar (`G4`) y la fase siguiente arranca limpia.
- Tres ciclos `NO APTO` escalan al humano o fuerzan rediseño del brief.

## GATES

1. Arquitecto fija spec, write-set, rutas exactas, anclas y G0 delegando en `Arch-Flash` (D49).
2. Ingeniero redacta brief unitario con coordenadas exactas (D49), `Eng-Flash-1` implementa y `Eng-Flash-2` audita diff y micro-checks deterministas (<2s). Cero suites pesadas ni auditorías por tarea (D48).
3. Arquitecto audita bloques/baches de tareas cuando existe una frontera material.
4. Auditor revisa hallazgos complejos, detección de bugs y la suite completa de pruebas en la auditoría final de fase (`G4`) delegando en `Aud-Flash`; Arquitecto decide G4.
5. Dueño autoriza y opera push/despliegue.

Assurance: `Standard`. G0 fase lista, G1 tarea lista, G2 tarea apta, G3 integración, G4 fase apta.

## POLÍTICA DE USO DE `/boost`

`/boost` realiza razonamiento profundo y multi-perspectiva con alto consumo de tokens. Su uso se rige por:
- **Obreros (Gemini)**: **PROHIBIDO**. No usar en tareas de código rutinarias ni búsquedas mecánicas.
- **Ingeniero**: **DESACONSEJADO**. Solo utilizable como excepción ante bugs inexplicables que bloqueen la tarea tras fallar el flujo normal.
- **Auditor**: **AUTORIZADO bajo demanda**. Reservado para auditorías de cierre de fase completa (G4), análisis de vectores de seguridad (OTA/B19) o detección forense de condiciones de carrera.
- **Arquitecto**: **RESERVADO**. Únicamente para dilemas de arquitectura mayor o diseño de protocolos criptográficos.
- **Regla de disparo único**: `/boost` nunca se mantiene activo de forma continua. Se invoca puntualmente por orden explícita para una consulta delimitada y se retorna al flujo ordinario.
