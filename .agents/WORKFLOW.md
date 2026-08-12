# WORKFLOW — desarrollo de LinuxRemotePlayer 2.0

```yaml
niveles: 3
arquitecto: Codex, chat principal persistente
ingeniero: Codex nuevo por fase, orquestado por el Arquitecto
obrero: Gemini 3.6 Flash High, conversación fresca por tarea mediante agy.exe
push: solo el dueño
agents_write: solo el Arquitecto
```

## PROPÓSITO

Conservar el razonamiento estratégico en el nivel más capaz y aislar el ruido de implementación.
El ahorro desaparece si el Arquitecto vuelve a repetir toda auditoría de tarea. El Ingeniero
audita tareas; el Arquitecto audita fases, gates y excepciones de alto riesgo.

```text
Dueño
  └─ Arquitecto — visión, fases, gates, .agents, integración
       └─ Ingeniero de fase — tareas, Obreros, tests, commits, informe
            └─ Obrero por tarea — implementación y evidencia, sin commits
```

El Ingeniero es un subagente Codex creado por el Arquitecto. El Obrero **no** es otro subagente
Codex: es un proceso externo `agy.exe` lanzado por el Ingeniero. Los niveles no se saltan.

## NIVEL 1 — ARQUITECTO

Responsabilidades:

- Define arquitectura, fases, dependencias, interfaces, amenazas y fuera de alcance.
- Abre cada fase con una especificación y gates medibles.
- Crea un Ingeniero Codex nuevo por fase y le entrega contexto limitado.
- Es el único agente que modifica `.agents/` y hace commits de apertura/cierre de fase.
- Audita el rango de commits y el informe final de la fase.
- Reejecuta gates críticos o toma muestras; no repite mecánicamente cada auditoría de tarea.
- Decide APTO/NO APTO de fase e integración hacia la rama de 2.0.
- Audita release/artefacto; el dueño decide y ejecuta el push.

Escalamiento obligatorio al Arquitecto:

- Cambio de arquitectura, formato persistido, API o alcance de fase.
- Dependencia/modelo/licencia no aprobados.
- Privilegios, sudoers, OTA, firma, autenticación, secretos o migración Supabase.
- Mismo bloqueo después de dos intentos razonados del Ingeniero.
- Test que requiera cambiar su criterio para pasar.

## NIVEL 2 — INGENIERO DE FASE

Se crea uno nuevo por fase para evitar contexto acumulado. Trabaja en la rama/worktree de esa
fase y recibe: spec, gates, APPCORE relevante, bugs relacionados y límites de escritura.

Responsabilidades:

- Inspecciona el código real y divide la fase en tareas `[T-NN]` pequeñas y ordenadas.
- Define por tarea objetivo, archivos, prohibiciones, pruebas, aceptación y rollback.
- Lanza un Obrero fresco mediante `agy.exe`; no reutiliza conversación entre tareas.
- Audita cada STOP: árbol real, alcance, tests, errores, referencias y documentación.
- Desbloquea fallos rutinarios; devuelve una corrección autocontenida al Obrero.
- Hace el commit de cada tarea APTO con staging selectivo y sin `Co-Authored-By`.
- Ejecuta integración/build/benchmarks al cerrar la fase.
- Entrega `phase-report.md` condensado al Arquitecto.

No puede:

- Editar `.agents/`, cambiar arquitectura o redefinir gates.
- Pushear, desplegar, usar secretos o operar Supabase/Vercel/DNS.
- Aprobar su propio cambio manual no auditado. Si corrige código directamente, convoca otro
  Obrero/revisor o escala al Arquitecto según riesgo.

## NIVEL 3 — OBRERO

Modelo fijado: `gemini-3.6-flash-high`. Una ejecución/conversación nueva por tarea.

Puede:

- Leer solo el contexto y archivos necesarios.
- Editar el alcance autorizado.
- Ejecutar checks y devolver evidencia literal.

No puede:

- Leer o editar `.agents/`, `design/`, `archive/` ni secretos.
- Cambiar arquitectura, añadir dependencias o ampliar alcance sin STOP.
- Hacer commit, push, deploy o tocar infraestructura.
- Modificar tests/criterios para esconder un fallo.
- Ejecutar shell generado por un modelo local ni conceder privilegios nuevos.

Entrega obligatoria:

```text
STOP — T-NN listo para auditoría
Archivos tocados: ...
Pruebas ejecutadas: comando + salida/resumen verificable
No verificado: ...
Desvíos/hallazgos: ...
```

## INVOCACIÓN DE AGY

Binario verificado el 2026-08-11:

```text
C:\Users\OnlyH\AppData\Local\agy\bin\agy.exe
```

Plantilla PowerShell del Ingeniero:

```powershell
& 'C:\Users\OnlyH\AppData\Local\agy\bin\agy.exe' `
  --model gemini-3.6-flash-high `
  --mode accept-edits `
  --sandbox `
  --disable-slash-commands `
  --output-format json `
  --print-timeout 20m `
  --print (Get-Content -Raw -Encoding utf8 '<brief>')
```

Reglas:

- Ejecutar primero un smoke test no mutante para confirmar modelo, cwd, salida y timeout.
- Preferir `--sandbox`; ampliar permisos solo con causa concreta y autorización del Ingeniero.
- **Prohibido `--dangerously-skip-permissions`.**
- No usar `--continue` ni `--conversation` entre tareas. Una corrección de la misma tarea puede
  continuar solo si el Ingeniero necesita preservar el diagnóstico; debe registrarlo.
- El prompt viaja en un archivo temporal gitignored para evitar problemas de escape y mantener
  un brief auditable. No contiene secretos.
- El Ingeniero captura stdout/stderr y código de salida en `.work/<fase>/<tarea>/`.
- Si JSON estructurado demuestra ser estable, añadir `--json-schema`; no asumirlo sin smoke test.

## RAMAS Y WORKTREES

```text
main                       producción 1.9.1
└─ codex/v2-integration    integración de fases aprobadas
   ├─ codex/PH21-stt
   ├─ codex/PH22-needle
   └─ codex/PHxx-...
```

- Una rama y worktree por fase; un solo Ingeniero escribe allí.
- Obreros de la misma fase trabajan secuencialmente en ese árbol.
- Paralelismo solo con tareas independientes y worktrees separados; nunca dos escritores sobre
  los mismos archivos o migración.
- `main` no recibe trabajo parcial de 2.0.
- El Ingeniero commitea tareas; el Arquitecto integra/cierra fases; solo el dueño pushea.

## GATES

### G0 — fase lista, Arquitecto

Objetivo, alcance, interfaces, amenazas, dependencias, evidencia y salida definidos.

### G1 — tarea lista, Ingeniero

Brief autocontenido, archivos permitidos, aceptación reproducible y rollback conocido.

### G2 — tarea apta, Ingeniero

STOP recibido; diff/alcance/referencias auditados; pruebas repetidas; commit único y limpio.

### G3 — integración de fase, Ingeniero

Suite completa, build/artefacto, pruebas cruzadas, deuda y no-verificables documentados.

### G4 — fase apta, Arquitecto

Spec cumplida; rango de commits coherente; invariantes y próximas fases protegidas; gates críticos
repetidos. Riesgos altos pueden recibir auditoría adicional aunque G2 haya pasado.

### G5 — release 2.0, Arquitecto + dueño

Clon fresco, firma válida/inválida, rollback, instalación limpia, upgrade 1.9.1→2.0.0, offline,
desinstalación, web ES/EN, Supabase retirado y testing de device. Dueño aprueba y pushea.

## EVIDENCIA Y AHORRO DE CONTEXTO

Trabajo efímero gitignored:

```text
.work/<fase>/<tarea>/brief.md
.work/<fase>/<tarea>/worker.json
.work/<fase>/<tarea>/tests.log
.work/<fase>/phase-report.md
```

El Arquitecto recibe solo `phase-report.md`, rango de commits, gates y excepciones. Consulta logs
de tarea únicamente al muestrear o investigar un riesgo. `.agents` conserva decisiones durables,
no transcripciones ni dumps.

Informe de fase mínimo:

```text
Fase / objetivo
Rango de commits y tareas
Gates: resultado + comandos
Tests/build/benchmarks
Cambios de interfaces y datos
Deuda, riesgos y no verificables
Archivos/documentos afectados
Recomendación: APTO / NO APTO
```

## CALIDAD DE VIBECODING

- Refactor y funcionalidad en tareas separadas.
- Dependencia nueva requiere licencia de código/pesos, mantenimiento, tamaño y desinstalación.
- Todo comportamiento tiene prueba proporcional: unidad, contrato, integración, benchmark o campo.
- Probar éxito y rechazo: firma inválida, intent desconocido, baja confianza, downgrade y puerto LAN.
- Interfaces tipadas; errores estructurados; configuración validada; logs sin secretos.
- Sin fallbacks silenciosos, strings mágicos duplicados, TODO oculto ni “ya que estamos”.
- Definition of Done de tarea: código + tests + errores + docs/referencias + evidencia + commit.
- Definition of Done de fase: integración + artefacto + informe + G4 + actualización `.agents`.

## POLÍTICA DE REINTENTOS

1. Primer fallo: Obrero corrige con diagnóstico concreto del Ingeniero.
2. Segundo fallo de la misma causa: el Ingeniero investiga y reduce/reformula la tarea.
3. Tercer bloqueo o implicación arquitectónica: STOP y escalamiento al Arquitecto.

Nunca iterar prompts a ciegas ni relajar tests para terminar.
