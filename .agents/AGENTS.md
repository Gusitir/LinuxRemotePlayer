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

### Tríada persistente (D54)

- **Tres subagentes por fase**, con contexto propio y persistente: `coder` (implementa el brief),
  `auditor` (verifica diff, criterios y gates por su cuenta) y `asistente` (lecturas, recon, anclas,
  estado del equipo y ops por SSH). Sustituyen a los workers `flash` de D48 con los mismos límites y
  se terminan al cerrar la fase; la fase siguiente arranca con contextos limpios.
- **Recibo obligatorio**, ≤12 líneas y sin prosa ni logs crudos:
  `STATUS` (`OK|FAIL|BLOCKED`), `FILES` (`ruta:rango`, máx 6), `GATES` (`cmd=exit`, máx 4),
  `DIFFSTAT`, `RISK` y `NEXT`. La salida cruda vive en un archivo temporal referenciado por ruta.
- **Escritor único**: solo `coder` escribe producto, un archivo a la vez y dentro del write-set.
  `auditor` no corrige; `asistente` es read-only sobre el repo y solo muta el appliance por orden
  explícita de despliegue.
- **Independencia de auditoría**: el `auditor` recibe brief, diff y gates; nunca la conversación.
- **Ciclo acotado**: `NO APTO` regresa al `coder` con el defecto exacto; tres ciclos fallidos escalan
  al humano o fuerzan rediseño del brief.
- **Autoridad**: commits `[T-NN]`/`[STATE]`, veredictos y `.agents` son del Arquitecto/Ingeniero; el
  push es del dueño y todo commit requiere autorización explícita. Los checks visuales, de hardware y
  de Secure Boot los certifica únicamente el dueño.

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

- **Licencia GPL-3.0 (D56)**: todo el repositorio, la ISO y la rama legacy. Avisos de licencia y
  créditos de terceros obligatorios en la web y en la ISO (`NOTICE`, `THIRD_PARTY_LICENSES.md`).
- **Distribución ISO-only (D56)**: la web sirve ISO + APK + checksums y documentación. Sin OTA,
  auto-update, canal beta ni manifiestos firmados; las versiones se publican por tag/release. El `.deb`
  es artefacto interno de build.
- **Sin comercialización (D56)**: prohibido reintroducir licencia, premium, compra, cuotas, cuentas,
  telemetría o servicios cloud en el producto o en la web.
- **Archivo legacy**: `legacy/2.0` + `v2.0.0-legacy` conservan el desarrollo comercial previo; no se
  modifica salvo corrección legal.
- Plataforma objetivo única: Debian 13 stable amd64 minimal. LRP administrará una sesión
  Xorg/Openbox; no se garantiza otra distro, Plasma/Bigscreen, Wayland ni escritorio general.
- RTX 3060 es la GPU inicial a certificar. Drivers/firmware solo desde repositorios Debian; nunca
  NVIDIA `.run` ni repositorios externos. Paquetes exactos requieren evidencia física y D32.
- Releases salen de clon WSL nativo limpio bajo `~`, nunca `/mnt`; inspeccionar el `.deb` extraído
  y su SHA independiente.
- Windows es el único clon productor de commits. El workspace se referencia con rutas relativas al
  repo; usar Windows/PowerShell 5.1 y recordar el quirk de truncamiento WSL en `/mnt`.
- Workspace migrado de `D:` a `G:` el 2026-10-22 (cambio de computadora). Artefactos externos en
  `G:\AGUSTIN\Portafolio\Proyectos\lrp-iso` (ISOs) y `...\lrp-keys` (claves OTA). `.venv` y
  `node_modules` son replicables y no se copiaron.
- Ciclo de estabilización D53: los fixes se despliegan al HTPC de pruebas por SSH (`lrp`/`lrp`) y la
  ISO definitiva se construye una sola vez al final del ciclo. WSL `Debian` compila desde `/mnt/g/...`;
  QEMU (`qemu-system-x86`, `ovmf`) se instala aparte y no está presente por defecto.
- Versiones de release `X.Y.Z`; cada release se publica por tag y se instala desde la ISO.
- `PAIRING_TOKEN` puede estar en `.pairing_token`.
- La CA tiene sufijo por máquina. No volver a añadir `viewport-fit=cover`. Mantener el alias Vercel
  legado mientras clientes publicados lo tengan grabado.
- **OTA eliminada por D56**: updater, firma de manifiestos, rollback, canal beta y `latest.json` viven
  solo en `legacy/2.0`. No se reintroducen en 1.0.0.

## CICLO Y GATES

1. Arquitecto fija spec, write-set, riesgos y G0 delegando en `Arch-Flash`.
2. Ingeniero orquesta a `Eng-Flash-1` (Constructor) para implementar y a `Eng-Flash-2` (Inspector) para verificar `git diff`, criterios `archivo:línea` y micro-checks (<5s: `py_compile`, `node --check`, `bash -n`, greps). **Nunca la suite completa por tarea (D48/D57)**.
3. Arquitecto audita un bache de tareas cuando exista una frontera material; no hay audit por tarea.
4. **Gate de fase (D57)**: la suite completa se corre **una vez al cierre de cada fase** (G4), más una
   vez antes del release; los bugs se resuelven al final de la fase con testeo dirigido. La cobertura se
   poda (se borran tests de funciones retiradas) en vez de crecer.
5. Dueño autoriza y opera push/despliegue según el alcance concedido.

G0: fase lista. G1: tarea lista. G2: tarea apta. G3: integración. G4: fase apta.

## LECTURA

Leer `AGENTS.md`, `CONTEXT.md`, `CURRENT.md`, `APPCORE.md`; después solo lo requerido. `INDEX.md`
guía navegación. `archive/`, `design/` y capturas no tienen autoridad.
