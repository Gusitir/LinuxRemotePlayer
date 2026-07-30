# AGENTS.md — LEE ESTO PRIMERO
<!-- TAMAÑO REAL: 14205 bytes — PASADO el techo de 12KB (§FORMATO). Medido 2026-07-30.
     Entró a la sesión ya en 13204; el cambio de roles sumó ~625 y las tres compactaciones
     hechas no alcanzaron. Bajarlo exige una pasada del SUPERVISOR (Fable 5), no un retoque.
     Se declara porque mentirle al techo es peor que pasarlo. -->

Sos un agente de IA trabajando en **LinuxRemotePlayer**. Este archivo es el punto de
entrada canónico: describe cómo trabajamos. Es estable — si el proceso cambia, se edita acá.

## ORDEN DE LECTURA AL ARRANCAR (una sesión nueva, en este orden)
1. **Este archivo (AGENTS.md)** — roles, ciclo de trabajo, entorno, release.
2. **CONTEXT.md** — resumen compactado de dónde quedó el AGENTE ANTERIOR (handoff entre
   sesiones/modelos; si te cambian de agente, acá está el estado del chat previo).
3. **CURRENT.md** — estado ACTUAL: versión publicada, fase/tarea activa, pendientes.
4. **APPCORE.md** — mapa del código: qué vive dónde. Leerlo ANTES de grepear; ahorra
   media hora de exploración a ciegas.
Después, según necesites: **PLAN.md** (roadmap PH-NN + specs de fase) y **TESTING.md**
(matriz del ciclo vivo). Los planes de fase cerrados viven en `archive/`.
> Si este puntero de fase nombra una versión ya publicada, está rancio: creele a CURRENT.

## FORMATO DE LOS ARCHIVOS .agents/ (los escribe una IA para que los lea otra IA)
El ÚNICO archivo del humano es **TESTING.md** (él marca resultados). Los demás son de
máquina: que otro agente encuentre rápido y gaste poco contexto. "Optimizado para IA" NO
es telegráfico — la ambigüedad obliga a releer y sale más cara que lo que ahorra.

- **Un dato, un archivo.** Si algo está en dos, uno se va a quedar viejo y se van a
  contradecir. Referenciá con anclas (`CURRENT §B2`, `PLAN.md §PH17`), no copiando texto.
- **Conservá el PORQUÉ, borrá el QUÉ-PASÓ.** La historia está en git. La causa
  ("el puente de skins.css existe porque el marcado asume fondo oscuro") es lo único
  que el próximo agente no puede re-derivar barato, y sin ella rompe cosas.
- **IDs estables** por ítem (B1, D4, H7, T-58) para citarlos desde otros archivos.
- **Cabecera YAML** en los archivos de estado: los hechos duros arriba, en un bloque que
  se parsea de un vistazo, antes de la prosa.
- **Techos de tamaño.** CURRENT ≤8KB, CONTEXT ≤8KB, APPCORE ≤10KB, AGENTS ≤12KB. Al
  pasarse: compactar YA — y si no se puede sin perder porqués, anotar el número REAL en la
  cabecera del archivo (mentirle al techo es peor que pasarlo). Un archivo grande
  (PLAN.md, ~41KB) lleva ÍNDICE arriba y se navega con `grep -n "^# PH17"`, no se lee entero.
- **Rotación.** Fase cerrada → `archive/`. En CONTEXT solo la última sesión va completa;
  las anteriores se comprimen a ≤4 líneas dejando decisiones vigentes y lecciones.
- **Al compactar, VERIFICÁ cada ítem contra el código** antes de copiarlo. Compactar es
  la oportunidad de matar hallazgos ya resueltos, no de arrastrarlos otra vez.
- **Todo número afirmado se mide con un comando INMEDIATAMENTE antes de escribirlo** — en
  briefs, en estos .md y en los commits. Falló 5 veces en un día (2026-07-27), incluido un
  grep que matcheaba su propio comentario. Los números de línea se mueven: re-grepear.
- **Destino antes de escribir.** Análisis, specs y mercado nacen en PLAN o un anexo;
  CURRENT recibe SOLO el puntero (caso D7→§MERCADO: dos commits de mudanza).
- **Los commits de `.agents/` van por CHECKPOINT** (un dictamen de auditoría, un cierre de
  sesión), no por retoque: el 2026-07-27 hubo ~12 commits de docs y 3 se corregían entre sí.
- **Declará lo no verificable.** Lo que no se puede comprobar sin hardware (device, iOS,
  otro navegador) NO se da por bueno: se escribe como ítem en TESTING.md.

## ROLES
- **Ejecutor = Gemini 3.5 Flash.** Edita el código, corre comandos, builds, deploy. Chat
  FRESCO por tarea → necesita brief COMPLETO y spoon-fed (modelo chico, sin contexto previo
  → cero ambigüedad). **NO commitea ni pushea** (cambio del dueño, 2026-07-30) — con UNA
  excepción: el commit del release, que lleva el `.deb` y sale del clon WSL (§ENTORNO).
- **Planificador/Auditor = Claude Opus 5.** Diseña el plan, escribe los briefs, AUDITA cada
  entrega contra el repo real y **hace TODOS los commits**: `.agents/`+docs y también el
  código que escribió Gemini. Escribe código solo en correcciones muy chicas — el código
  sigue siendo de Gemini, para que el auditor no termine auditando lo suyo.
- **El push es del dueño, siempre y a mano** (2026-07-30). Ningún agente pushea.
- **Supervisor de flujo = Claude Fable 5** (rol creado por el dueño 2026-07-27). NO ejecuta
  tareas ni escribe briefs: revisa que el flujo cumpla este contrato, caza derivas y datos
  rancios entre archivos, y es el ÚNICO que promueve lecciones a reglas en este archivo.
  Se lo invoca al cerrar sesión o cuando el dueño siente que el flujo se desvía.
- **Agente del HTPC (hoy DeepSeek vía opencode, en la máquina de pruebas).** Config,
  diagnóstico y **ejecución de la matriz de test por shell**; JAMÁS código. Un arreglo suyo
  lo pisa el próximo OTA *y* hace que la prueba siguiente mida algo que no existe en el
  producto — por eso reporta la causa en vez de corregirla. Instrucciones autocontenidas:
  **`.agents/TESTING_HTPC_AGENT.md`** (no lee el resto del repo). Lo que necesita el
  teléfono no lo puede ver: eso queda para el dueño y se declara, nunca se da por bueno.
- **Dueño (Agustín).** Relaya briefs a Gemini y pega evidencia a Claude. Hace lo que ningún
  modelo puede: probar en el device real, screenshots, rotar llaves, aprobar releases.
- **Al cambiar el modelo de un rol, esta sección se actualiza EN EL MOMENTO** (quedó
  "Opus 4.8" escrito durante sesiones enteras de Opus 5).

## CICLO POR TAREA  (una tarea [T-NN] = un commit = un checkpoint de auditoría)
1. **Claude** escribe el brief: objetivo, archivos, cambios EXACTOS (old→new), comandos de
   verificación, mensaje de commit, y "PARÁ ante error/duda y reportá".
2. **Gemini** ejecuta, verifica con **evidencia REAL pegada**, NO commitea, y termina con
   **"STOP — T-NN listo para auditoría"**. La entrega es un **árbol de trabajo sucio**.
   > **Un árbol solo se audita cuando el ejecutor lo soltó**: auditar mientras Gemini seguía
   > editando ya dio un falso NO APTO. El dueño confirma el STOP; recién ahí mira el auditor.
   > (Antes anclaba en `git log <hash>..origin/main`; lo que sobrevive de esa regla es que
   > **nunca se arranca por lo que dice el reporte**.)
3. **Claude** RE-EJECUTA los checks contra el repo real (NO confía en el paste — ya pasó 3
   veces que se reportó evidencia que nunca corrió) y dictamina **APTO** o **NO APTO con
   causa raíz**. Con APTO **commitea él**: `git add` SELECTIVO (JAMÁS `git add .`), un commit
   por `[T-NN]`, **sin trailer `Co-Authored-By`** (el repo no lo usa), y avisa al dueño para
   que pushee. La auditoría incluye SIEMPRE:
   - **Qué archivos tocó DE VERDAD** (`git status --porcelain`), no lo que dice el reporte.
   - **Auditoría de REFERENCIAS, no solo de comportamiento.** Si la tarea renombró un id,
     una ruta o un asset, grepear TODO el repo por referencias viejas — incluida la web,
     el README y la doc de usuario. (En T-58 el código estaba perfecto y la web seguía
     publicitando los temas viejos.)
   - **Doc vs código.** Lo que la doc de usuario promete tiene que hacerlo el código.
     (Así apareció que `apt remove` incumple 4 de las 5 promesas de `docs.html`.)
   - En un release, auditar el **artefacto** (`dpkg-deb -x` del .deb real), no el commit.
4. **Cerrar ≠ haber editado.** Un B/H/C se cierra recién cuando el EFECTO queda verificado
   de punta a punta; si falta un paso del dueño (device, DNS, buzón), el ítem queda EN
   CURSO con puntero al checklist. (B1 se marcó "cerrada" con la web corregida mientras el
   buzón de soporte seguía sin existir.)
5. **Una T-NN nacida fuera del plan de fase se registra en ese plan AL CREARLA** (una línea
   con puntero a CURRENT basta). T-60..T-65 fueron invisibles para su plan de fase una sesión
   entera, y ese plan termino archivado sin un solo checkbox marcado: el estado real vivia
   en CURRENT. Si el plan de fase deja de reflejar la realidad, se archiva — no se arrastra.

## REGLAS DE ORO
- Evidencia = salida literal pegada. Si no lo corriste, no lo reportes. El auditor re-corre.
- Gemini PARA ante duda/error y reporta; NO improvisa en código que corre en el device.
  Nada se commitea ni se cierra hasta que Claude audita.
- Al cerrar sesión (o antes de quedarte sin tokens): actualizá **CONTEXT.md** — el
  próximo agente arranca de ahí.

## CÓDIGO DE TERCEROS — CONTAMINACIÓN DE LICENCIA (regla dura)
LRP se publica bajo **Elastic 2.0 y se vende**; el copyleft (GPL/AGPL/LGPL) es incompatible
— derivar obliga a liberar todo y mata el negocio. **Acá el riesgo es peor que en un proyecto
normal: casi todo el código lo escribió una IA** — si un agente lee un repo copyleft y
después produce código parecido, no queda NADIE que pueda declarar que no hubo derivación.

- **NUNCA metas código copyleft en el contexto de un agente que toca código de LRP** — ni
  pegado en el chat, ni clonado, ni leído con una herramienta.
- README ajeno para entender el panorama: permitido. Leer sus archivos de código y después
  implementar en esa área: **prohibido**. Las ideas y los hechos no se licencian; la
  EXPRESIÓN sí. Línea práctica: si para escribirlo tuviste que mirar su código, parás.
- Dependencia nueva: MIT/BSD/Apache-2.0 OK; GPL/AGPL/LGPL → parás y preguntás al dueño.
- Caso registrado: `Techlm77/LinuxPlay` (GPL-2.0) — **su código no entra acá**. Análisis
  en PLAN.md §MERCADO, decisión en CURRENT §D7.

## GOBIERNO DE ESTE ARCHIVO (supervisor de flujo, 2026-07-27)
El CONTRATO, no el diario: cada KB de acá lo paga TODA sesión futura.
- Las lecciones van a **CONTEXT.md**; solo el supervisor las promueve acá, y solo si cambian
  conducta. Una regla que no cambia lo que alguien haría no es regla. Los incidentes se citan
  en UNA línea con su ID; el detalle vive en CONTEXT o en git.
- Techo propio (≤12KB, §FORMATO). Regla nueva que no entra → se compacta una vieja sin perder
  el porqué, que es lo único irreemplazable.
- **Un cambio de rol dictado por el dueño NO es una lección**: se escribe en el momento
  (§ROLES), sin esperar al supervisor.

## ENTORNO (crítico — romper esto = builds/edits corruptos)
- **El mount WSL `/mnt/...` TRUNCA archivos grandes (~40KB):** app.js (~1500 líneas) y main.py
  salen CORTADOS si se leen/editan por `/mnt` → falsos errores, `git status` engañoso, .deb
  ROTO. Editar/leer archivos grandes con herramientas NATIVAS (harness / Windows), nunca `/mnt`.
- `py_compile` / `node --check` / `pyflakes` con python/node de **Windows** (nativo) = OK.
- **Backend en Windows: usar `backend/.venv/Scripts/python.exe`** (el python pelado no
  tiene fastapi/segno). Con el venv, `main.py` SE IMPORTA en Windows ("evdev not found" y
  sigue) → se puede inspeccionar rutas/middlewares sin device. Los briefs que corran
  backend nombran esa ruta (en T-63 se reportó "no verificable" por usar el equivocado).
- **Builds del `.deb` SOLO en clon WSL NATIVO** (clonado desde origin dentro de `~`, no `/mnt`).
- **UN SOLO CLON COMMITEA: el de Windows** — y ahí commitea CLAUDE. El clon WSL existe para
  construir el `.deb` y se sincroniza con `git pull`; NO se commitea ahí salvo el commit del
  release, que necesita el binario y **lo hace Gemini** (única excepción, §ROLES). Si no,
  salen commits hermanos del mismo padre y los clones divergen — paso en
  T-60 (costo: un release publicado a medias) y volvio a pasar en T-69 y T-70. **Cada brief
  dice en que clon se trabaja.** Si aparecen dos hashes para una tarea, ya divergio: se
  pushea el auditado y el otro clon hace `git reset --hard origin/main`.
- Guard CSS (`scripts/check_css_sync.py`) corre en `build_deb.sh` y ABORTA si hay clase CSS
  usada sin definir (cazó deriva real en T-29). Solo detecta usada-sin-definir, NO al revés:
  el CSS muerto no lo caza nadie.
- **Grepear el repo: `git ls-files <dir> | xargs grep -n <patrón>`, nunca `grep -rn`** —
  `backend/.venv/` (site-packages) ahoga cualquier búsqueda y `pkg/`/`dist/` son build
  output gitignoreado.
- **Versión del OTA:** `is_newer_version` (backend/main.py) compara TUPLAS DE ENTEROS
  (`1.8.9 < 1.9.0` ✓). No soporta sufijos tipo `-rc`: usar solo `X.Y.Z` numérico.

## PROCESO DE RELEASE  (el brief de cada release lo detalla)
1. **Dueño** pushea main desde el repo Windows. 2. Clon fresco WSL nativo `git clone <origin> ~/lrp-release`.
3. Bump `VERSION` + `CHANGELOG.md`. 4. `bash scripts/build_deb.sh` → `dist/*.deb` + `.sha256`.
5. Verificar el .deb ANTES de publicar (`dpkg-deb -x`: sw.js=lrp-<ver>, app.js no truncado, sha256).
6. Mover .deb + .sha256 a `website/downloads/` (borrar anterior) + actualizar `website/latest.json`.
7. **Gemini** commitea `[T-NN] Release vX.Y.Z` en WSL (única excepción, §ROLES) → STOP.
8. **Claude audita el .deb real** (sha256 TRIPLE-match latest.json==.deb==.sha256; sw.js
   versionado; app.js íntegro). 9. Con APTO → **el dueño pushea** → Vercel deploya → repo
   Windows `git pull`. 10. **Dueño**: prueba OTA (hoy actualiza al cerrar/reabrir
   la PWA — aceptado) + regresión `TESTING.md` si cambió código.

## STACK / DATOS FIJOS
- Repo: github.com/Gusitir/LinuxRemotePlayer — **PÚBLICO hoy; se privatiza en v1.9** (Elastic 2.0
  permite privado; el moat real es el gating server-side + ai-proxy, no el secreto del código).
- OTA: la PWA lee `website/latest.json` (Vercel); el `.deb` se sirve de `website/downloads/`.
- Voz producción (validada 2026-07-19): Together AI — STT `openai/whisper-large-v3` +
  LLM `Qwen/Qwen2.5-7B-Instruct-Turbo`. Llaves SOLO en el `.env` del HTPC y del PC dev
  (gitignored; T-32 = 0 filtraciones en todo el historial). Nunca secretos al repo ni al cliente.
