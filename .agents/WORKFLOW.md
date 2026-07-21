# WORKFLOW — cómo trabajamos en LinuxRemotePlayer

> Documento CANÓNICO y estable del proceso. Una sesión nueva lee ESTO una vez y ya sabe
> el flujo completo — no hay que re-explicarlo cada vez. Si el proceso cambia, se edita acá.

## ROLES
- **Ejecutor = Gemini 3.5 Flash.** Hace TODO lo operativo: editar código, correr comandos,
  commits, push, builds, releases, deploy. Trabaja en chat FRESCO por tarea → necesita un
  brief COMPLETO y spoon-fed (no tiene contexto previo; es un modelo chico → cero ambigüedad).
- **Planificador/Auditor = Claude Opus 4.8.** Diseña el plan, escribe los briefs para Gemini,
  y AUDITA cada entrega contra el repo real. Casi no ejecuta (solo correcciones puntuales muy
  chicas, para ahorrar tokens). Se agotó Fable5; antes auditaba Fable5.
- **DeepSeek (asistente en el HTPC del dueño).** Solo config/diagnóstico en el equipo, JAMÁS
  código. Sus hotfixes de emergencia se PORTAN al repo o el próximo OTA los pisa.
- **Dueño (Agustín).** Relaya los briefs a Gemini y pega la evidencia de vuelta a Claude.
  Hace lo que ningún modelo puede: probar en el device real, sacar screenshots, rotar llaves,
  aprobar releases. Los subagentes Sonnet se usan solo si el dueño lo pide explícitamente.

## CICLO POR TAREA  (una tarea [T-NN] = un commit = un checkpoint de auditoría)
1. **Claude** escribe el brief: objetivo, archivos, cambios EXACTOS (old→new si aplica),
   comandos de verificación, mensaje de commit, y "PARÁ ante error/duda y reportá".
2. **Gemini** ejecuta, verifica con **evidencia REAL pegada**, hace `git add` SELECTIVO
   (JAMÁS `git add .`), commitea, pushea, y termina con: **"STOP — T-NN listo para auditoría"**.
3. **Claude** RE-EJECUTA los checks contra el repo/commit real (NO confía en el paste — ya
   pasó 3 veces que se reportó evidencia que nunca corrió) y dictamina **APTO** o **NO APTO
   con causa raíz**. Recién con APTO se avanza a la próxima tarea.

## REGLAS DE ORO
- Evidencia = salida literal pegada. Si no lo corriste, no lo reportes. El auditor re-corre.
- `git add` selectivo siempre. Un commit por tarea. Mensajes claros `[T-NN] ...`.
- Gemini PARA ante cualquier error/duda y reporta; NO improvisa en código que corre en el
  device del dueño. Claude (más inteligente) resuelve y le indica cómo.
- Nada se declara "cerrado" hasta que Claude audita. Nada llega al device hasta el release.

## ENTORNO (crítico — romper esto = builds/edits corruptos)
- **El mount WSL `/mnt/...` TRUNCA archivos grandes (~40KB):** app.js (~1500 líneas) y
  main.py salen CORTADOS si se leen/editan por `/mnt` → falsos errores de sintaxis, `git
  status` engañoso, y **.deb roto**. Editar/leer archivos grandes con herramientas NATIVAS
  (harness, o herramientas de Windows), nunca vía `/mnt`.
- `py_compile` / `node --check` / `pyflakes` con **python/node de Windows** (nativo) = OK.
- **Builds del `.deb` SOLO en clon WSL NATIVO** (clonado desde origin dentro de `~`, NO `/mnt`).
- Guard CSS (`scripts/check_css_sync.py`) corre en `build_deb.sh` y ABORTA si hay una clase
  CSS usada sin definir. Ya cazó deriva real (T-29).

## PROCESO DE RELEASE  (resumen; el brief de cada release lo detalla)
1. En el repo Windows: `git push origin main` (subir el código de la versión).
2. Clon fresco en WSL nativo: `git clone <origin> ~/lrp-release` (NO `/mnt`).
3. Bump `VERSION` + entrada en `CHANGELOG.md`.
4. `bash scripts/build_deb.sh` → genera `dist/linuxremoteplayer_<ver>_all.deb` + `.sha256`.
5. **Verificar el .deb ANTES de publicar:** extraer con `dpkg-deb -x`, confirmar
   `sw.js = lrp-<ver>`, `app.js` NO truncado (~1500 líneas), y el `sha256`.
6. Mover `.deb` + `.sha256` a `website/downloads/` (borrar el anterior), actualizar
   `website/latest.json` (version + deb_url + sha256 real).
7. Commit `[T-NN] Release vX.Y.Z` → **STOP**.
8. **Claude audita el .deb real** (vía `wsl` al clon): sha256 TRIPLE-match
   (latest.json == .deb == .sha256), sw.js versionado, app.js íntegro.
9. Con APTO → `git push origin main` → Vercel deploya. Repo Windows: `git pull` para sincronizar.
10. **Dueño en el device:** prueba OTA (idealmente auto-recarga; hoy se actualiza al
    cerrar/reabrir la PWA — aceptado como suficiente) + regresión de `TESTING.md` si cambió código.

## STACK / DATOS FIJOS
- Repo: github.com/Gusitir/LinuxRemotePlayer — **PÚBLICO hoy; se privatiza en el lanzamiento
  v1.9** (Elastic 2.0 permite privado; el moat real es el gating server-side + ai-proxy).
- OTA: la PWA lee `website/latest.json` en Vercel; el `.deb` se sirve de `website/downloads/`.
- Voz (producción, validada 2026-07-19): Together AI — STT `openai/whisper-large-v3` +
  LLM `Qwen/Qwen2.5-7B-Instruct-Turbo`. Llaves SOLO en el `.env` del HTPC y del PC dev
  (gitignored; auditoría de secretos T-32 = 0 filtraciones en todo el historial).
- Builds: WSL. Edición/lectura: harness nativo. Nunca secretos al repo ni al cliente.
