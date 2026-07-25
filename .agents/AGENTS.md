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
3. **Claude** RE-EJECUTA los checks contra el repo/commit real (NO confía en el paste — ya
   pasó 3 veces que se reportó evidencia que nunca corrió) y dictamina **APTO** o **NO APTO
   con causa raíz**. Recién con APTO se avanza.

## REGLAS DE ORO
- Evidencia = salida literal pegada. Si no lo corriste, no lo reportes. El auditor re-corre.
- `git add` selectivo. Un commit por tarea `[T-NN]`. Gemini PARA ante duda/error y reporta;
  NO improvisa en código que corre en el device. Nada se cierra hasta que Claude audita.
- Al cerrar una sesión (o antes de quedarte sin tokens): actualizá **CONTEXT.md** con un
  resumen compactado, para que el próximo agente sepa dónde quedó todo.

## ENTORNO (crítico — romper esto = builds/edits corruptos)
- **El mount WSL `/mnt/...` TRUNCA archivos grandes (~40KB):** app.js (~1500 líneas) y main.py
  salen CORTADOS si se leen/editan por `/mnt` → falsos errores, `git status` engañoso, .deb
  ROTO. Editar/leer archivos grandes con herramientas NATIVAS (harness / Windows), nunca `/mnt`.
- `py_compile` / `node --check` / `pyflakes` con python/node de **Windows** (nativo) = OK.
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
