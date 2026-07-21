# PLAN v1.8 — FASE DE LIMPIEZA, OPTIMIZACIÓN Y PROFESIONALIZACIÓN (pre-lanzamiento)

> Documento MAESTRO de fase (mapa completo). Cada tarea T-NN recibe su brief
> spoon-fed para Gemini 3.5 Flash al ejecutarla (estilo T-30/T-31), auditada por
> Claude entre medio. Planifica/audita: Claude Opus 4.8. Ejecuta TODO: Gemini Flash.

## OBJETIVO
Dejar el proyecto 100% limpio, profesional y coherente ANTES de arrancar v1.9
(lanzamiento). Purga de legacy, limpieza de código moderada, docs/web factualmente
correctas, GitHub prolijo, y reestructura a fondo de `.agents/`. Cierra publicando un
**release v1.8** (con re-test OTA + regresión en device del dueño).

## DECISIONES BLOQUEADAS (2 rondas con el dueño, 2026-07-20)
1. **Multi-distro = FUERA de esta fase.** Va POST-v1.9 como desarrollo activo (junto a
   features premium: skins 2.0, voz 2.0, asistente). Aquí SOLO se documentan los puntos
   de acoplamiento a distro para ese milestone futuro; no se refactoriza para multi-distro.
2. **Release v1.8 = SÍ.** La fase termina publicando .deb v1.8 → rebuild + re-test OTA en
   vivo + pase de regresión completo de TESTING.md en el device.
3. **Web = solo corrección factual.** Versión, stack IA real (Together), instrucciones,
   screenshots reales, precio. Rebrand + rediseño + dominio propio = v1.9 (PH-WEB).
4. **Modo IA local = ELIMINAR** (incluye MOCK_AI y defaults NVIDIA/OpenRouter muertos).
5. **Refactor = MODERADO.** Borrar código muerto + estilo + docstrings + extracción de
   bajo riesgo. NADA de re-arquitectura riesgosa justo antes del lanzamiento.
6. **Legacy = podar superados, conservar `.agents/archive/`.** Borrar `docs/archive/`,
   reubicar scripts one-shot; git preserva el histórico.
7. **`.agents` = WORKFLOW.md canónico + consolidar.** Codificar el flujo real una vez.
8. **GitHub: hoy es PÚBLICO** (CURRENT.md decía "PRIVADO" — ERROR, se corrige). Se hará
   PRIVADO en el lanzamiento v1.9 (Elastic 2.0 permite repo privado; la visibilidad es
   ajuste de GitHub, no de licencia). Moat real = gating server-side + ai-proxy (v1.9),
   no el secreto del código. En esta fase se deja prolijo y LISTO para privatizar.

## SCOPE
- **IN:** auditoría de secretos, purga IA legacy, borrar pair.html muerto, reubicar
  scripts dev, borrar docs/archive, limpieza código backend+frontend (moderada), README
  factual, website factual, licencias/CHANGELOG, actualizar contenido `.agents`,
  reestructurar `.agents`, release v1.8 + regresión.
- **OUT (diferido):** multi-distro (post-v1.9), rebrand/rediseño/dominio (v1.9 PH-WEB),
  nuevas features premium (v1.9+), ai-proxy/anti-abuso/licencia-1-dispositivo (v1.9).

## REGLAS DE ESTA FASE (además de las operativas de siempre)
- Una tarea = un commit `[T-NN]` = un checkpoint de auditoría. `git add` SELECTIVO.
- Evidencia = salida real PEGADA. Flash PARA ante cualquier error y reporta a Claude.
- Builds SOLO en clon WSL nativo (el mount /mnt trunca; ver PASO release).
- Cambios que tocan runtime (T-33, T-34, T-37, T-38) → marcados "RE-TEST DEVICE": entran
  al pase de regresión de TESTING.md antes de declarar v1.8 estable.
- `.agents/` NO se empaqueta en el .deb (build_deb solo copia backend/frontend/scripts/
  VERSION) → T-43/T-44 tienen CERO riesgo de release.
- Orden pensado por riesgo: primero seguro (auditoría, purga behavior-neutral, docs),
  refactor moderado después, release al final.

---

# TAREAS

## T-32 — Auditoría de secretos del historial git  [CRÍTICA, PRIMERO · sin cambio de código]
**Por qué:** el repo está/estuvo público. Un secreto commiteado alguna vez sigue en el
historial aunque hoy esté gitignored.
**Alcance:** escanear TODO el historial (no solo el árbol actual) buscando llaves/tokens:
Together, Supabase (service_role), Stripe (sk_live/sk_test), PAIRING_TOKEN, LICENSE_TOKEN,
contenido de `.env`, `.pairing_token`, certs.
- Herramienta: `gitleaks detect --source . --log-opts="--all"` (o `git log -p --all | grep`
  con patrones si no hay gitleaks). Revisar también `git log --all -- backend/.env` etc.
**Verificación:** listado de hallazgos (idealmente 0). Reportar a Claude.
**Si hay filtración:** Claude decide → ROTAR la llave afectada (dueño lo hace en el panel
del proveedor) + documentar. NO reescribir historia sin acordar (rompe clones/forks).
**Riesgo:** nulo (read-only). **Re-test device:** no.

## T-33 — Purga del modo IA legacy + config honesta  [RE-TEST DEVICE]
**Por qué:** `ai_pipeline.py` tiene 3 capas muertas: (a) `USE_LOCAL_AI` (Whisper/Ollama
local, testing), (b) `MOCK_AI` (respuestas falsas), (c) defaults NVIDIA/OpenRouter que
CRASHEABAN (nemotron-asr, llama-3.1 → 400). Producción anda solo porque el `.env` del HTPC
pisa todo con Together. Los defaults mienten.
**Alcance:**
- `backend/ai_pipeline.py`: eliminar ramas `USE_LOCAL_AI` (transcribe_audio, parse_intent),
  vars LOCAL_WHISPER_URL/LOCAL_OLLAMA_URL/OLLAMA_MODEL, y `MOCK_AI` (líneas 30,87-89,169-171).
  Poner defaults HONESTOS = stack Together validado (o dejar URL/KEY/MODEL sin default y
  requerir .env). Quitar fallbacks NVIDIA_NIM_API_KEY/OPENROUTER_API_KEY/nemotron.
- `backend/main.py:49`: quitar la referencia `if ai_pipeline.USE_LOCAL_AI:` (log de arranque).
- `backend/.env.example`: reescribir la sección IA → Together como el ejemplo principal
  (Whisper-large-v3 + Qwen2.5-7B-Instruct-Turbo), borrar NVIDIA/OpenRouter/local/mock.
**Verificación:** `grep -rn "USE_LOCAL_AI\|MOCK_AI\|OLLAMA\|nemotron\|OPENROUTER" backend/`
→ 0 hits. `python3 -m py_compile backend/ai_pipeline.py backend/main.py` OK.
**Riesgo:** bajo (en prod los flags eran false → behavior-neutral). **Re-test device:** SÍ
(confirmar que la voz por Together sigue OK tras quitar las ramas).

## T-34 — Eliminar pair.html (muerto)  [RE-TEST DEVICE leve]
**Por qué:** `status.html` reemplazó a `pair.html`. Se sirve por el static mount (línea 926)
pero probablemente ya nada lo enlaza.
**Alcance:** confirmar sin links (`grep -rn "pair.html\|pair\b" frontend/ website/` — que no
haya href/redirect vivo). Si confirmado muerto: borrar `frontend/pair.html`, quitarlo de
`scripts/check_css_sync.py` (lista FRONTEND) y de `scripts/apply_reicons.py`.
**Verificación:** `grep -rn "pair.html" .` → solo en archive/docs (no en código vivo).
build_deb corre el guard CSS sin pair.html y no aborta.
**Riesgo:** bajo. **Re-test device:** verificar que pairing/onboarding sigue OK.

## T-35 — Reubicar scripts one-shot a scripts/dev/ + adelgazar el .deb  [sin runtime]
**Por qué:** `apply_reicons.py`, `gen_reicon_map.py`, `generate_png_icons.py`,
`download_fonts.py` son herramientas de dev ya ejecutadas (iconos/fuentes ya commiteados).
Hoy `build_deb.sh` copia `scripts/` entero → viajan al .deb sin necesidad.
**Alcance:** mover esos 4 a `scripts/dev/`. Ajustar `build_deb.sh` para NO empaquetar
`scripts/dev/` (ni `build_deb.sh`/`check_css_sync.py`) en el .deb — solo install/update/
uninstall que el paquete necesita. Actualizar rutas si algo los referencia.
**Verificación:** extraer el .deb de prueba y confirmar que `scripts/dev/` NO está dentro;
que install/update/uninstall SÍ están.
**Riesgo:** bajo. **Re-test device:** cubierto por el build/regresión de T-45.

## T-36 — Borrar docs/archive/  [sin runtime]
**Por qué:** planes/auditorías v1.1–v1.4 superados; git conserva el histórico.
**Alcance:** `git rm -r docs/archive/` (9 archivos). Si `docs/` queda vacío, quitarla.
Verificar que nada vivo (README, scripts) linkea a esos paths.
**Verificación:** `git status`; `grep -rn "docs/archive" .` → 0 en código/README.
**Riesgo:** nulo. **Re-test device:** no.

## T-37 — Limpieza código backend (moderada)  [RE-TEST DEVICE]
**Alcance:** imports muertos, ramas/vars sin uso, `print`/logs de debug olvidados, código
comentado, TODOs resueltos. Docstrings de módulo + de funciones públicas. Estilo consistente
(nombres, comillas, orden imports). SIN cambios de comportamiento ni de arquitectura.
Archivos: main.py, run.py, auth.py, discovery.py, kiosk.py, input_emulator.py, audio.py,
ai_pipeline.py (post T-33). Idealmente en 2-3 commits chicos por área, no uno gigante.
**Verificación:** `py_compile` de cada archivo OK; diff revisado (nada de lógica cambiada);
`grep` de los símbolos borrados = 0 refs.
**Riesgo:** medio (fácil romper sin querer) → auditoría estricta + re-test. **Re-test:** SÍ.

## T-38 — Limpieza código frontend (moderada)  [RE-TEST DEVICE]
**Alcance:** `app.js` — `console.log` de debug, código muerto, comentarios obsoletos, estilo.
index.html/status.html — markup muerto, comentarios. NO tocar el fix T-30 ni la lógica del SW.
El guard CSS (check_css_sync) debe seguir pasando.
**Verificación:** `node --check frontend/app.js` OK; guard CSS OK; diff sin cambios de lógica.
**Riesgo:** medio. **Re-test:** SÍ (toda la app corre sobre esto).

## T-39 — (OPCIONAL) Extracción de bajo riesgo en main.py  [RE-TEST DEVICE]
**Solo si** reduce complejidad SIN cambiar comportamiento (ej: mover constantes
SUGGESTED_KIOSKS/MEDIA_KEYS a un módulo, o aislar el handler de voz). Si hay cualquier duda
de riesgo → SE DIFIERE a v1.9. Claude decide tras ver el tamaño/enredo real de main.py.
**Riesgo:** medio-alto → por eso es opcional. **Re-test:** SÍ si se hace.

## T-40 — Reescribir README.md (factual)  [sin runtime]
**Corregir:** stack IA (línea 24 dice NVIDIA NIM/OpenRouter/Ollama → es Together:
Whisper-large-v3 + Qwen2.5-7B). Screenshot placeholder → screenshots REALES (las provee el
dueño). Layout del repo completo y correcto (ai_pipeline, kiosk, discovery, input_emulator,
audio, send-feedback). Instalación: Debian/Ubuntu (+ nota "otras distros = roadmap futuro").
Features al día. Troubleshooting revisado. Precio/licencia coherentes.
**Verificación:** revisión de Claude contra el código real. Links válidos.
**Riesgo:** nulo. **Depende de:** screenshots del dueño (acción externa).

## T-41 — Website factual (index.html + gracias.html)  [deploy Vercel]
**Corregir:** versión, stack IA real, precio ($5 único al lanzar), sin NVIDIA, screenshots
reales, textos coherentes con README. SIN rediseño ni rebrand (eso es v1.9).
**Verificación:** `curl` a Vercel tras deploy; revisión visual del dueño.
**Riesgo:** bajo (contenido). **Re-test device:** no (pero sí revisar la web en vivo).

## T-42 — Licencias + CHANGELOG  [sin runtime]
**Alcance:** verificar `THIRD_PARTY_LICENSES.md` (deps reales: FastAPI, httpx, segno,
Space Grotesk, Lucide, uBlock refs, etc.) y `LICENSE`. Entrada `## [1.8.0]` en CHANGELOG
resumiendo esta fase.
**Verificación:** Claude cruza deps de requirements.txt + assets vs THIRD_PARTY.
**Riesgo:** nulo.

## T-43 — Actualizar CONTENIDO de .agents  [sin runtime, sin release]
**Alcance:** APPCORE.md refleja las remociones (sin local AI/mock/pair.html, scripts/dev/).
CURRENT.md: corregir "Repo PRIVADO" → "PÚBLICO (privatizar en v1.9)"; estado a v1.8.
HALLAZGOS/roadmap al día.
**Riesgo:** nulo.

## T-44 — REESTRUCTURA .agents (WORKFLOW canónico + consolidar)  [sin runtime, sin release]
**Por qué:** el dueño tuvo que repetir el flujo "Gemini implementa todo, Claude planifica/
audita". AGENTS.md describe un flujo `invoke_subagent` OBSOLETO. Hay que codificarlo una vez.
**Estructura destino:**
- **WORKFLOW.md** (NUEVO, reemplaza AGENTS.md): flujo REAL, estable, se lee 1 vez por sesión.
  Roles (Gemini Flash ejecuta TODO: código/commits/push/builds; Claude Opus planifica+audita),
  disciplina STOP-y-auditar, evidencia pegada, una-tarea-un-commit-una-auditoría, proceso de
  release por clon WSL nativo, reglas de entorno (mount trunca), modelos vigentes.
- **.agents/README.md** (NUEVO): índice de 10 líneas — "empezá acá: leé WORKFLOW.md, después
  CURRENT.md" + qué es cada archivo.
- Consolidar: retirar CONTEXT.md (dumps de sesión rancios; git+CURRENT alcanzan) o reducirlo.
  Archivar briefs de tareas cerradas (PLAN_GEMINI_v1.7.8.md → archive/ tras cerrar v1.8).
- Mantener: CURRENT.md, PLAN.md, APPCORE.md, TESTING.md, AUDITS/, archive/, skills/.
**Verificación:** una sesión fresca leyendo WORKFLOW.md + CURRENT.md entiende TODO sin repetir
nada. Claude valida que no queda referencia al flujo viejo.
**Riesgo:** nulo (no va al .deb).

## T-45 — RELEASE v1.8 + regresión  [publica a producción]
**Precondición:** T-32..T-44 auditadas OK.
**Pasos (clon WSL nativo desde origin, NO /mnt):** bump VERSION `1.8.0` → entrada CHANGELOG →
`build_deb.sh` → verificar sw.js `lrp-1.8.0` + app.js no truncado + sha256 → mover .deb a
website/downloads/ (borrar 1.7.7) + latest.json → commit `[T-45] Release v1.8.0` → STOP →
auditoría del .deb por Claude (sha256 triple-match, extracción) → push → Vercel deploy.
**Regresión (dueño en device):** pase COMPLETO de la matriz TESTING.md (porque cambió código:
T-33/34/37/38) + prueba OTA (1.7.8→1.8.0 auto-reload sin reinstalar).
**Cierre:** TODO OK → declarar v1.8 estable + testing cerrado → **arrancar v1.9**.

---

# DEFINITION OF DONE (fase v1.8)
- [ ] T-32 secretos: 0 filtraciones (o rotadas).
- [ ] IA legacy purgada; voz Together OK en device.
- [ ] pair.html fuera; onboarding OK.
- [ ] scripts dev reubicados; .deb más magro.
- [ ] docs/archive borrado.
- [ ] código backend+frontend limpio; regresión TESTING.md verde.
- [ ] README + website factualmente correctos (con screenshots reales).
- [ ] licencias + CHANGELOG al día.
- [ ] `.agents` reestructurado (WORKFLOW.md + README índice); el flujo NO se repite más.
- [ ] Release v1.8.0 LIVE + OTA verificado.
- [ ] Repo prolijo y LISTO para privatizar en v1.9.

# ACCIONES DEL DUEÑO (fuera de código)
- [ ] Tomar screenshots reales del device (para README/website — T-40/T-41).
- [ ] Rotar llaves si T-32 encuentra filtración.
- [ ] Pase de regresión TESTING.md en device tras el release (T-45).
- [ ] (v1.9) privatizar el repo en el lanzamiento.

# NOTAS DE RIESGO
- v1.8 SÍ toca código que corre en el device → cada tarea "RE-TEST DEVICE" se valida antes
  de declarar estable. Hay backup del dueño.
- Si el refactor moderado destapa algo grande → se DIFIERE a v1.9, no se fuerza pre-lanzamiento.
