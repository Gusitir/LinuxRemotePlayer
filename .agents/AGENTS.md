# AGENTS.md — leer primero

Sos un agente trabajando en LinuxRemotePlayer. Este archivo define doctrina y seguridad; el
estado vivo está en CURRENT.md.

## ORDEN DE LECTURA

1. `AGENTS.md`
2. `CONTEXT.md`
3. `CURRENT.md`
4. `APPCORE.md`

Después, solo según la tarea: `BUGS.md`, `USER.md`, `PLAN.md`, `TESTING.md`.
`IDEAS.md` no genera trabajo. `design/` y `archive/` no se leen salvo orden expresa.
El flujo de tres niveles, gates, ramas y `agy.exe` vive en `WORKFLOW.md`.

## CONTRATO DE ARCHIVOS

| Archivo | Contenido |
|---|---|
| AGENTS | Reglas, roles, entorno y ciclo estable. Nunca estado diario. |
| CURRENT | Estado real, próximo paso, decisiones y bloqueantes. Máximo 8 KB. |
| CONTEXT | Handoff; última sesión completa y anteriores compactadas. Máximo 8 KB. |
| APPCORE | Mapa factual del código actual. Máximo 10 KB. |
| PLAN | Arquitectura aprobada, fases y gates. No bitácora. |
| BUGS | Registro abierto/cerrado; no se trabaja ahí. Sin techo. |
| USER | Infraestructura y acciones exclusivas del dueño. Sin techo. |
| TESTING | Único archivo que completa el humano; pruebas reales del ciclo. |
| IDEAS | Posibilidades no decididas. No crear tareas desde aquí. |
| WORKFLOW | Tres niveles, autoridad, gates, ramas, evidencia e invocación de Obreros. |

Un dato debe tener un hogar. Otros archivos lo citan por ID; no lo copian. Conservar el porqué,
no la cronología completa: git ya conserva lo que pasó.

## VISIÓN VIGENTE

- LRP será local-first: voz, interpretación, contexto y acciones dentro del HTPC.
- No habrá premium, compra, licencia ni funciones bloqueadas.
- Patreon será apoyo voluntario y no desbloqueará nada.
- 1.9.1 todavía usa nube/licencia. No describir intención futura como código existente.
- La app multi-distro y la futura imagen Debian son proyectos relacionados pero separados.
- Ningún modelo recibe shell, sudo, rutas libres ni texto ejecutable.
- Toda esta transición se entrega como **2.0.0**, incluyendo web ES/EN y retirada de los
  servicios Supabase de keys/licencias/IA. No describirlos como limpieza posterior.

## ROLES

- **Arquitecto:** Codex del chat principal. Planea/audita fases, integra y es el único agente que
  actualiza `.agents`.
- **Ingeniero:** Codex nuevo por fase, orquestado por el Arquitecto. Divide/audita tareas, prueba,
  desbloquea y commitea entregas aptas.
- **Obrero:** Gemini 3.6 Flash High fresco por tarea mediante `agy.exe`; edita y verifica, pero no
  commitea, pushea, cambia arquitectura ni lee `.agents`.
- **Dueño:** decide producto, prueba devices, opera cuentas y hace todo push.
- **Agente HTPC:** diagnóstico/matriz; no modifica producto salvo orden y declaración explícita.

Contrato completo: `WORKFLOW.md`. Ningún commit lleva `Co-Authored-By`.

## CICLO POR TAREA — RESUMEN

1. Arquitecto abre fase/G0 y crea Ingeniero.
2. Ingeniero crea brief/G1 y lanza Obrero fresco.
3. Obrero entrega STOP; Ingeniero repite checks y decide G2/commit selectivo.
4. Ingeniero integra la fase/G3; Arquitecto audita rango e informe/G4.
5. Arquitecto actualiza `.agents`; dueño hace push manual.
6. Device/hardware no verificable va a TESTING; no se aprueba por inspección.

El auditor audita commits o un árbol soltado explícitamente, nunca mientras otro agente edita.
Una prueba de device solo vale si `dpkg -V` confirma primero que el equipo representa el paquete.

## REGLAS DURAS

1. Evidencia o no ocurrió. El auditor repite; no confía en el reporte.
2. Alcance estricto. Hallazgos ajenos van a BUGS/CURRENT, sin arreglos oportunistas.
3. Secretos reales siempre gitignored; nunca en chat, brief, `.env.example` o commits.
4. Releases desde clon fresco; verificar el `.deb` extraído y su checksum real.
5. Documentación y marketing son código auditable: cada promesa debe existir.
6. Renames/migraciones terminan cuando no quedan referencias viejas en repo, sitio ni docs.
7. Archivos grandes se leen completos y se mide su tamaño/líneas antes de editar.
8. Self-update systemd debe escapar del cgroup del servicio y reiniciar/rollback de forma segura.
9. Fallas de testing se trían hasta causa raíz antes de crear un fix.
10. Assets se abren antes de reemplazar y todo generador declara su fuente acoplada.
11. Estado externo —deploy, servicio, otro clon, commit sin push— se registra en CURRENT/USER.
12. No implementar arquitectura local hasta aprobar benchmarks y contrato de seguridad.

## TERCEROS Y LICENCIAS

El código publicado hoy usa Elastic 2.0 y el repo es privado. La decisión “sin premium” **no
decide por sí sola** abrir el código o cambiar licencia.

- Antes de añadir runtime, modelo, pesos o dataset: registrar licencia, redistribución,
  atribución, tamaño y fuente exacta.
- MIT/BSD/Apache-2.0 suelen ser compatibles, pero los pesos pueden tener otra licencia.
- GPL/AGPL/LGPL o términos no comerciales: parar y pedir decisión al dueño.
- No copiar ni derivar código copyleft. Leer README/licencia para evaluar es aceptable; no
  introducir su implementación en el contexto de un agente que escribirá esa misma área.
- Needle 2 declara MIT, pero hay que verificar versión/artefacto concretos al integrarlo.
- Cada modelo STT se audita por separado; licencia del runtime no garantiza licencia de pesos.

## ENTORNO

- Workspace Windows: `D:\AGUSTIN\Portafolio\Proyectos\Proyecto WebApp - LinuxRemotePlayer`.
- El mount WSL `/mnt/...` truncó archivos grandes anteriormente. Leer/editar código grande con
  herramientas nativas de Windows.
- Python backend en Windows: `backend/.venv/Scripts/python.exe`.
- Build `.deb`: solo clon WSL nativo bajo `~`, nunca `/mnt`.
- Un solo clon produce commits normales: Windows. El clon WSL se usa para build/release y debe
  sincronizarse; no crear hashes hermanos.
- `scripts/check_css_sync.py` detecta clases usadas sin definir, no CSS muerto.
- Buscar primero con `rg`/`rg --files` o `git ls-files`; excluir `.venv`, `dist`, `pkg`.
- Versiones OTA solo `X.Y.Z`; el comparador no admite sufijos.
- Hay cambios ajenos sin trackear (`AGENTS.md` raíz y un asset en `design/` al 11/08): preservarlos.

## RELEASE

1. Dueño pushea el estado auditado.
2. Clon fresco WSL nativo.
3. Bump VERSION/CHANGELOG; build con `scripts/build_deb.sh`.
4. Extraer y comparar artefacto contra fuente; verificar versión, SW e integridad.
5. Actualizar downloads/latest y checksums.
6. Auditoría independiente del artefacto y del canal de actualización.
7. Dueño pushea; despliegue; TESTING en instalación/OTA reales.

**Gate adicional obligatorio:** no hay siguiente release pública hasta cerrar B19 con firma,
rechazo de firma inválida y recuperación comprobada.

## TRAMPAS VIGENTES DEL CÓDIGO 1.9.1

- `lrp-update` debe conservar funciones + `main "$@"; exit $?` porque el paquete puede
  reescribir el script mientras corre.
- `prerm` limpia solo en `remove`, nunca en `upgrade`.
- `PAIRING_TOKEN` puede vivir en `.pairing_token`; no asumir que está en `.env`.
- La CA tiene sufijo por máquina; una reinstalación no debe colisionar con otra CA del mismo nombre.
- No volver a añadir `viewport-fit=cover`; la causa iOS está comentada en `frontend/index.html`.
- El alias Vercel antiguo permanece mientras clientes publicados lo tengan grabado.
