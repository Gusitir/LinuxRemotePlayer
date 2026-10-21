# AGENTS.md — autoridad del plano de control

Este archivo define reglas durables. `CURRENT.md` contiene estado vivo; `CONTEXT.md` contiene
decisiones y handoffs append-only; `INDEX.md` contiene navegación.

## CAVEMAN

Regla obligatoria para Arquitecto, Ingeniero y Auditor de fase: sin saludos ni relleno; salida breve,
técnica, factual y accionable.

## PROPIEDAD V3 Y ROLES

- Assurance vigente: `Standard`.
- **Protocolo Cero-IO en modelos pesados (D48)**: Arquitecto (`42a6a909-29da-4d4c-8f81-4e7bafff4cb8`),
  Ingeniero (`fdfc68b2-8383-4854-8f61-737c6e0c101b`) y Auditor (`ae7b054f-900d-4285-87c0-f2cdd49e7888`)
  NUNCA ejecutan lecturas completas, escrituras, búsquedas ni comandos directos; delegan todo a workers
  persistentes con `Model: "flash"` (`Arch-Flash` para Arquitecto; `Eng-Flash-1` Constructor y `Eng-Flash-2`
  Inspector para Ingeniero; `Aud-Flash` para Auditor), los cuales se mantienen vivos toda la fase y se
  terminan (`kill`) al cerrar la fase. Lectura directa en modelos pesados solo permitida por rango
  quirúrgico (`StartLine`/`EndLine` <= 25 líneas) ante duda crítica.
- **Workers Flash y recibos**: respuestas de workers `flash` limitadas estrictamente a <150 palabras
  (recibo determinista: `git status -s`, `git diff --stat`, `archivo:línea`, exit code de 1 línea).
- **El Arquitecto** posee `INIT`, `PLAN`, diseño, `.agents`, commits de control/integración y el veredicto final;
  orquesta a Ingeniero y Auditor a través de su worker persistente `Arch-Flash`. Audita baches de tareas y no escribe producto.
- **El Ingeniero** coordina producto en worktree y orquesta a `Eng-Flash-1` (Constructor) y `Eng-Flash-2` (Inspector);
  no escribe código directo ni corre comandos pesados en su contexto.
- **Verificación Constructor/Inspector (D48)**: `Eng-Flash-1` implementa y `Eng-Flash-2` (contexto `flash`
  independiente) audita `git diff`, verifica cada criterio con `archivo:línea` y corre micro-checks
  rápidos (<2s: `bash -n`, `py_compile`, `node --check`).
- **El Auditor** persistente ejecuta búsquedas exhaustivas, detección de bugs y la auditoría final de fase
  a solicitud del Arquitecto delegando en `Aud-Flash`; autorizado a usar `/boost` y `/teamwork-preview`
  según convenga; no escribe código, fixes ni planificación.
- **Prioridad producto y gates de tests (D48)**: prioridad producto sobre cobertura de tests durante ejecución
  de tareas; se eliminan suites pesadas y auditorías por tarea. Los bugs y la suite completa se cubren
  únicamente en la auditoría final de fase (`G4`) con dictamen del Auditor.
- **Briefs Guiados por Contexto y Tareas Unitarias (D49)**: Arquitecto e Ingeniero NUNCA envían un plan
  completo en one-shot ni delegan búsquedas a ciegas; despachan 1 tarea acotada a la vez (p. ej. primero
  `T-141`, validar recibo, luego `T-142`) e incluyen siempre las rutas exactas, líneas/funciones ancla y
  extracto de contexto de `APPCORE.md`/`INDEX.md` para que el worker `flash` vaya directo al punto sin
  quemar tokens explorando el repo.
- La evidencia determinista avanza tareas; el Arquitecto agrupa revisiones en baches y emite sus veredictos.
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
  del Ingeniero.
- Inspeccionar antes de escribir. Evidencia o no ocurrió. Clasificar defectos como `missing`,
  `stale`, `contradictory`, `duplicate`, `misplaced`, `unsafe` o `broken reference`.
- Docs y marketing son código auditable. Renames y migraciones terminan cuando no quedan referencias
  antiguas en repo, sitio ni docs. Root-cause precede cualquier fix.
- Estado externo, deploys, servicios, otros clones y commits sin push se registran en `CURRENT.md`
  o `USER.md`.
- No implementar pipeline local antes de benchmark y contrato de seguridad aprobados.
- Un device solo vale tras `dpkg -V` confirmando que representa el paquete.

## RELEASE Y ENTORNO

- Plataforma objetivo única: Debian 13 stable amd64 minimal. LRP administrará una sesión
  Xorg/Openbox; no se garantiza otra distro, Plasma/Bigscreen, Wayland ni escritorio general.
- RTX 3060 es la GPU inicial a certificar. Drivers/firmware solo desde repositorios Debian; nunca
  NVIDIA `.run` ni repositorios externos. Paquetes exactos requieren evidencia física y D32.
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
- El instalador beta público puede reiniciar automáticamente solo en modo unattended autorizado por
  el comando inicial. Usa un servicio systemd temporal, máximo dos reboots esperados, contador
  anti-loop, STOP fail-closed y recuperación TTY; cualquier otro flujo conserva no-auto-reboot.

## CICLO Y GATES

1. Arquitecto fija spec, write-set, riesgos y G0 delegando en `Arch-Flash`.
2. Ingeniero orquesta a `Eng-Flash-1` (Constructor) para implementar y a `Eng-Flash-2` (Inspector) para verificar `git diff`, criterios `archivo:línea` y micro-checks (<2s). Cero suites pesadas ni auditorías por tarea (D48).
3. Arquitecto audita un bache de tareas cuando exista una frontera material; no hay audit por tarea.
4. Auditor de fase revisa el conjunto, bugs y la suite completa únicamente al cierre de fase (`G4`) delegando en `Aud-Flash`; Arquitecto decide G4.
5. Dueño autoriza y opera push/despliegue según el alcance concedido.

G0: fase lista. G1: tarea lista. G2: tarea apta. G3: integración. G4: fase apta.

## LECTURA

Leer `AGENTS.md`, `CONTEXT.md`, `CURRENT.md`, `APPCORE.md`; después solo lo requerido. `INDEX.md`
guía navegación. `archive/`, `design/` y capturas no tienen autoridad.
