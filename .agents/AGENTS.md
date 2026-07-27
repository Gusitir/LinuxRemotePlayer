# AGENTS.md — LEE ESTO PRIMERO

Sos un agente de IA trabajando en **LinuxRemotePlayer**. Este archivo es el punto de
entrada canónico: describe cómo trabajamos. Es estable — si el proceso cambia, se edita acá.

## ORDEN DE LECTURA AL ARRANCAR (una sesión nueva, en este orden)
1. **Este archivo (AGENTS.md)** — roles, ciclo de trabajo, entorno, release.
2. **CONTEXT.md** — resumen compactado de dónde quedó el AGENTE ANTERIOR (handoff entre
   sesiones/modelos; si te cambian de agente, acá está el estado del chat previo).
3. **CURRENT.md** — estado ACTUAL: versión publicada, fase/tarea activa, pendientes.
4. **APPCORE.md** — mapa del código: qué vive dónde. Leerlo ANTES de grepear; ahorra
   media hora de exploración a ciegas.
Con eso ya sabés todo. Después, según necesites: PLAN.md (roadmap + fases futuras
PH-NN), **PLAN_v1.9.md (plan de la fase ACTIVA)**, TESTING.md (matriz de test del device).
> El puntero a la fase activa se actualiza al abrir cada fase nueva. Si acá dice una
> versión que ya salió, está rancio: creele a CURRENT.md, no a esta línea.

## FORMATO DE LOS ARCHIVOS .agents/ (los escribe una IA para que los lea otra IA)
El ÚNICO archivo que lee y escribe el humano es **TESTING.md** (él marca los resultados).
Los demás son de máquina: optimizalos para que otro agente encuentre rápido y gaste poco
contexto. "Optimizado para IA" NO es telegráfico ni abreviado — la ambigüedad obliga a
releer y sale más cara que las palabras que ahorra.

- **Un dato, un archivo.** Si algo está en dos, uno se va a quedar viejo y se van a
  contradecir. Referenciá con anclas (`CURRENT §B2`, `PLAN.md §PH17`), no copiando texto.
- **Conservá el PORQUÉ, borrá el QUÉ-PASÓ.** La historia está en git. La causa
  ("el puente de skins.css existe porque el marcado asume fondo oscuro") es lo único
  que el próximo agente no puede re-derivar barato, y sin ella rompe cosas.
- **IDs estables** por ítem (B1, D4, H7, T-58) para citarlos desde otros archivos.
- **Cabecera YAML** en los archivos de estado: los hechos duros arriba, en un bloque que
  se parsea de un vistazo, antes de la prosa.
- **Techos de tamaño.** CURRENT ≤8KB, CONTEXT ≤8KB, APPCORE ≤10KB. Al pasarse: compactar
  YA. Un archivo grande (PLAN.md, ~33KB) lleva ÍNDICE arriba y se navega con
  `grep -n "^# PH17"`, no se lee entero.
- **Rotación.** Fase cerrada → `archive/`. En CONTEXT solo la última sesión va completa;
  las anteriores se comprimen a ≤4 líneas dejando decisiones vigentes y lecciones.
- **Al compactar, VERIFICÁ cada ítem contra el código** antes de copiarlo. Compactar es
  la oportunidad de matar hallazgos ya resueltos, no de arrastrarlos otra vez.
- **Los números y las rutas de un brief salen de un comando corrido, no de la memoria ni
  de un .md.** Pasó tres veces el 2026-07-27: un conteo de ocurrencias mal (`isLicensed`
  eran 4, no 3), un `grep "set -e"` que matcheaba el propio comentario del archivo y habría
  reprobado código correcto, y B2 afirmando que `uninstall.sh` no iba en el `.deb` cuando sí
  va. Los números de línea además se mueven con cada tarea: re-grepear siempre.
- **Declará lo no verificable.** Lo que no se puede comprobar sin hardware (device, iOS,
  otro navegador) NO se da por bueno: se escribe como ítem en TESTING.md.

## ROLES
- **Ejecutor = Gemini 3.5 Flash.** Hace TODO lo operativo: editar código, correr comandos,
  commits, push, builds, releases, deploy. Chat FRESCO por tarea → necesita brief COMPLETO
  y spoon-fed (modelo chico, sin contexto previo → cero ambigüedad).
- **Planificador/Auditor = Claude Opus 4.8.** Diseña el plan, escribe los briefs para Gemini,
  AUDITA cada entrega contra el repo real. Casi no ejecuta (solo correcciones muy chicas, por
  tokens). Se agotó Fable5 (antes auditaba).
- **DeepSeek (en el HTPC del dueño).** Solo config/diagnóstico, JAMÁS código; sus hotfixes se
  PORTAN al repo o el próximo OTA los pisa.
- **Dueño (Agustín).** Relaya briefs a Gemini y pega evidencia a Claude. Hace lo que ningún
  modelo puede: probar en el device real, screenshots, rotar llaves, aprobar releases.

## CICLO POR TAREA  (una tarea [T-NN] = un commit = un checkpoint de auditoría)
1. **Claude** escribe el brief: objetivo, archivos, cambios EXACTOS (old→new), comandos de
   verificación, mensaje de commit, y "PARÁ ante error/duda y reportá".
2. **Gemini** ejecuta, verifica con **evidencia REAL pegada**, hace `git add` SELECTIVO
   (JAMÁS `git add .`), commitea, pushea, y termina con **"STOP — T-NN listo para auditoría"**.
   > **Un push sin ese bloque NO es una entrega.** En T-64 (2026-07-27) se commiteó y pusheó
   > el cambio más riesgoso de la sesión sin una sola línea de evidencia; se descubrió solo
   > porque el push de la tarea siguiente arrancaba en un hash desconocido. **Por eso el
   > auditor empieza SIEMPRE por `git log <ultimo-hash-auditado>..origin/main`**, nunca por
   > lo que dice el reporte: si hay commits que nadie reportó, aparecen ahí.
3. **Claude** RE-EJECUTA los checks contra el repo/commit real (NO confía en el paste — ya
   pasó 3 veces que se reportó evidencia que nunca corrió) y dictamina **APTO** o **NO APTO
   con causa raíz**. Recién con APTO se avanza. La auditoría incluye SIEMPRE:
   - **Qué archivos toca el commit** (`git show --stat`), no solo que el commit exista.
   - **Auditoría de REFERENCIAS, no solo de comportamiento.** Si la tarea renombró un id,
     una ruta o un asset, grepear TODO el repo por referencias viejas — incluida la web,
     el README y la doc de usuario. (En T-58 el código estaba perfecto y la web seguía
     publicitando los temas viejos.)
   - **Doc vs código.** Lo que la doc de usuario promete tiene que hacerlo el código.
     (Así apareció que `apt remove` incumple 4 de las 5 promesas de `docs.html`.)
   - En un release, auditar el **artefacto** (`dpkg-deb -x` del .deb real), no el commit.

## REGLAS DE ORO
- Evidencia = salida literal pegada. Si no lo corriste, no lo reportes. El auditor re-corre.
- `git add` selectivo. Un commit por tarea `[T-NN]`. Gemini PARA ante duda/error y reporta;
  NO improvisa en código que corre en el device. Nada se cierra hasta que Claude audita.
- Al cerrar una sesión (o antes de quedarte sin tokens): actualizá **CONTEXT.md** con un
  resumen compactado, para que el próximo agente sepa dónde quedó todo.

## CÓDIGO DE TERCEROS — CONTAMINACIÓN DE LICENCIA (regla dura)
LinuxRemotePlayer se publica bajo **Elastic 2.0 y se vende**. El código copyleft
(GPL/AGPL/LGPL en sus variantes) es **incompatible**: derivar de él obligaría a liberar
todo el producto bajo esa licencia. No es un tecnicismo, mata el modelo de negocio.

**Acá el riesgo es peor que en un proyecto normal, y por eso la regla es más estricta:
la mayoría de este código lo escribió una IA.** Si un agente lee un repo copyleft y
después produce código parecido en esa misma área, NO existe forma de demostrar después
que no hubo derivación — no hay un humano que pueda declarar qué tenía en la cabeza.

- **NUNCA metas código copyleft en el contexto de un agente que va a tocar código de LRP.**
  Ni pegado en el chat, ni clonado en el repo, ni leído con una herramienta.
- Leer el **README** de un proyecto ajeno para entender el panorama: permitido. Leer sus
  archivos de código y después implementar una feature en esa área: **prohibido**.
- Las ideas de alto nivel y los hechos no se pueden licenciar (que UDP conviene sobre TCP
  para input, qué puertos usa alguien). La EXPRESIÓN sí. La línea práctica: si para
  escribirlo tuviste que mirar su código, parás.
- Antes de traer una dependencia nueva, mirá su licencia. MIT/BSD/Apache-2.0: OK.
  GPL/AGPL/LGPL: parás y preguntás al dueño.
- Caso concreto registrado (2026-07-26): `github.com/Techlm77/LinuxPlay`, GPL-2.0, mismo
  vecindario (control remoto de Linux) pero otro producto — ellos hacen streaming de
  escritorio con FFmpeg, nosotros no transmitimos video. Contexto de mercado en
  CURRENT §D7. **Su código no entra acá.**

## ENTORNO (crítico — romper esto = builds/edits corruptos)
- **El mount WSL `/mnt/...` TRUNCA archivos grandes (~40KB):** app.js (~1500 líneas) y main.py
  salen CORTADOS si se leen/editan por `/mnt` → falsos errores, `git status` engañoso, .deb
  ROTO. Editar/leer archivos grandes con herramientas NATIVAS (harness / Windows), nunca `/mnt`.
- `py_compile` / `node --check` / `pyflakes` con python/node de **Windows** (nativo) = OK.
- **Para EJECUTAR el backend, el python de Windows NO sirve** (le faltan fastapi, segno…):
  las dependencias viven en `backend/.venv/Scripts/python.exe`. Con ese intérprete
  `backend/main.py` SE PUEDE importar en Windows — avisa "evdev not found" y sigue, así que
  se puede inspeccionar la app FastAPI (rutas, middlewares) sin device. En T-63 se reportó
  "no verificable" solo por haber usado el python equivocado. Los briefs que pidan correr
  algo del backend deben nombrar la ruta del venv.
- **Builds del `.deb` SOLO en clon WSL NATIVO** (clonado desde origin dentro de `~`, no `/mnt`).
- Guard CSS (`scripts/check_css_sync.py`) corre en `build_deb.sh` y ABORTA si hay clase CSS
  usada sin definir (cazó deriva real en T-29). Solo detecta usada-sin-definir, NO al revés:
  el CSS muerto no lo caza nadie.
- **Trampa al grepear todo el repo:** `backend/.venv/` tiene site-packages y ahoga
  cualquier búsqueda (una búsqueda de "skin|icon|theme" devolvió 161KB de ruido). `pkg/`
  y `dist/` son build output gitignoreado. Para buscar en el repo REAL:
  `git ls-files <dir> | xargs grep -n <patrón>` en vez de `grep -rn`.
- **Versión del OTA:** `is_newer_version` (backend/main.py) compara TUPLAS DE ENTEROS
  (`1.8.9 < 1.9.0` ✓). No soporta sufijos tipo `-rc`: usar solo `X.Y.Z` numérico.

## PROCESO DE RELEASE  (el brief de cada release lo detalla)
1. Repo Windows: `git push origin main`. 2. Clon fresco WSL nativo `git clone <origin> ~/lrp-release`.
3. Bump `VERSION` + `CHANGELOG.md`. 4. `bash scripts/build_deb.sh` → `dist/*.deb` + `.sha256`.
5. Verificar el .deb ANTES de publicar (`dpkg-deb -x`: sw.js=lrp-<ver>, app.js no truncado, sha256).
6. Mover .deb + .sha256 a `website/downloads/` (borrar anterior) + actualizar `website/latest.json`.
7. Commit `[T-NN] Release vX.Y.Z` → STOP. 8. **Claude audita el .deb real** (sha256 TRIPLE-match
   latest.json==.deb==.sha256; sw.js versionado; app.js íntegro). 9. Con APTO → push → Vercel
   deploya → repo Windows `git pull`. 10. **Dueño**: prueba OTA (hoy actualiza al cerrar/reabrir
   la PWA — aceptado) + regresión `TESTING.md` si cambió código.

## STACK / DATOS FIJOS
- Repo: github.com/Gusitir/LinuxRemotePlayer — **PÚBLICO hoy; se privatiza en v1.9** (Elastic 2.0
  permite privado; el moat real es el gating server-side + ai-proxy, no el secreto del código).
- OTA: la PWA lee `website/latest.json` (Vercel); el `.deb` se sirve de `website/downloads/`.
- Voz producción (validada 2026-07-19): Together AI — STT `openai/whisper-large-v3` +
  LLM `Qwen/Qwen2.5-7B-Instruct-Turbo`. Llaves SOLO en el `.env` del HTPC y del PC dev
  (gitignored; T-32 = 0 filtraciones en todo el historial). Nunca secretos al repo ni al cliente.
