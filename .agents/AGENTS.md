# AGENTS.md — autoridad del plano de control

Este archivo define reglas durables. `CURRENT.md` contiene estado vivo; `CONTEXT.md` contiene
decisiones y handoffs append-only; `INDEX.md` contiene navegación.

## CAVEMAN

Regla obligatoria para Arquitecto, Ingenieros y Workers: sin saludos ni relleno; salida breve,
técnica, factual y accionable.

## PROPIEDAD V3 Y ROLES

- Assurance vigente: `Standard`.
- El Arquitecto posee `INIT`, `PLAN`, diseño y `CLOSE`; aprueba diseño, alcance, milestones,
  riesgos materiales, gates y decisiones irreversibles. No escribe producto.
- `INGENIERO-CONTROL` ejecuta `MAINTAIN`, `REINDEX`, `HANDOFF`, `COMPACT`, `AUDIT` y `EXPORT
  DOCUMENTATION` cuando están autorizados; puede escribir el plano de control dentro del scope.
- `INGENIERO-PRODUCTO` coordina y audita el plano de producto; no implementa producto directamente.
- Los Workers implementan producto dentro del write-set autorizado y entregan evidencia; no
  cambian arquitectura, controlan `.agents`, hacen commit ni push.
- Hay dos Ingenieros persistentes `gpt-5.6 LUNA` con esfuerzo `MAX`. `TERRA` y `SOL` están
  prohibidos para Ingenieros y Workers.
- Cada Ingeniero puede solicitar como máximo 2 Workers `LUNA-MAX`; el total global es 4. Cada slot
  requiere autorización previa del Arquitecto.
- Solo el Arquitecto puede usar hasta 2 Workers `DeepSeek V4 Flash High`, exclusivamente para
  fixes diminutos posteriores a una auditoría que el Arquitecto no escriba.
- El dueño hace push; nadie reescribe historia válida ni crea commits sin autorización.

## PROPIEDAD DE ARCHIVOS

| Archivo | Propiedad |
|---|---|
| `AGENTS.md` | autoridad, roles, assurance, entorno, gates y orquestación |
| `CURRENT.md` | estado, job, plan, tarea, veredicto, bloqueos y próxima acción |
| `CONTEXT.md` | decisiones y handoffs append-only desde la frontera v3 |
| `INDEX.md` | navegación, no estado activo duplicado |
| `TESTING.md` | checks humanos o no disponibles |
| `PLAN.md`, `PLAN_PH21.md` | scope, tareas, fases y gates |
| `APPCORE.md` | arquitectura estable verificada |
| `WORKFLOW.md` | extensión subordinada a este contrato y agents-workflow v3 |

Un hecho tiene un solo hogar. No copiar decisiones, diarios ni estado entre archivos.

## SEPARACIÓN, EVIDENCIA Y SEGURIDAD

- El plano de control no se mezcla con backend, frontend, website, scripts, Supabase, artefactos,
  worktrees ni otros archivos de producto.
- El modelo de inferencia del producto no recibe shell, sudo, rutas libres ni texto ejecutable; sus
  acciones son declaradas y validadas determinísticamente. Esto no limita herramientas autorizadas
  de Ingenieros o Workers.
- Inspeccionar antes de escribir. Evidencia o no ocurrió. Clasificar defectos como `missing`,
  `stale`, `contradictory`, `duplicate`, `misplaced`, `unsafe` o `broken reference`.
- Docs y marketing son código auditable. Renames y migraciones terminan cuando no quedan referencias
  antiguas en repo, sitio ni docs. Root-cause precede cualquier fix.
- Estado externo, deploys, servicios, otros clones y commits sin push se registran en `CURRENT.md`
  o `USER.md`.
- No implementar pipeline local antes de benchmark y contrato de seguridad aprobados.
- Un device solo vale tras `dpkg -V` confirmando que representa el paquete.

## RELEASE Y ENTORNO

- Releases salen de clon WSL nativo limpio bajo `~`, nunca `/mnt`; inspeccionar el `.deb` extraído
  y su SHA independiente.
- Windows es el único clon productor de commits. El workspace se referencia con rutas relativas al
  repo; usar Windows/PowerShell 5.1 y recordar el quirk de truncamiento WSL en `/mnt`.
- Versiones OTA son `X.Y.Z`.
- El updater conserva sus functions y `main "$@"; exit $?` durante self-rewrite.
- `prerm` limpia solo en `remove`, nunca en `upgrade`.
- `PAIRING_TOKEN` puede estar en `.pairing_token`.
- La CA tiene sufijo por máquina. No volver a añadir `viewport-fit=cover`. Mantener el alias Vercel
  legado mientras clientes publicados lo tengan grabado.
- B19, OTA sin firma independiente ni rollback probado, es riesgo aceptado por el dueño solo para
  betas opt-in sin publicidad; bloquea `2.0.0` estable y cualquier promoción al canal estable.
- Stable usa `latest.json` y no descubre betas. Beta se instala solo por curl, persiste su canal y
  consulta un manifiesto beta separado. Versiones beta son numéricas `1.99.x`; estable será `2.0.0`.

## CICLO Y GATES

1. Arquitecto fija spec, write-set, riesgos y G0.
2. Ingeniero coordina tareas, checks, rollback y G1; solicita slots antes de Workers.
3. Worker implementa y entrega STOP con archivos, comandos, evidencia, no verificado y desvíos.
4. Ingeniero repite gates, audita alcance e integra; Arquitecto decide G4.
5. Dueño opera push y despliegue.

G0: fase lista. G1: tarea lista. G2: tarea apta. G3: integración. G4: fase apta.

## LECTURA

Leer `AGENTS.md`, `CONTEXT.md`, `CURRENT.md`, `APPCORE.md`; después solo lo requerido. `INDEX.md`
guía navegación. `archive/`, `design/` y capturas no tienen autoridad.
