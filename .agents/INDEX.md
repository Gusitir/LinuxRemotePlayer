# INDEX - navegacion del repositorio

```yaml
last_reindexed_at: 2026-08-21T22:28:50-05:00 (historical; no new reindex claim)
source_commit: 407bb66
dirty: true
active_plan: none
dirty_state: "backup receipt control edits: APPCORE.md, CONTEXT.md, CURRENT.md, INDEX.md; lochi.png preexistente intacto; no reindex claim"
```

El estado activo pertenece a [`CURRENT.md`](CURRENT.md), no a este indice.

## CONTROL V3

- [`../AGENTS.md`](../AGENTS.md): shim raiz, origen importado y CAVEMAN.
- [`AGENTS.md`](AGENTS.md): roles, assurance, propiedad y gates.
- [`CURRENT.md`](CURRENT.md): estado vivo y proxima accion.
- [`CONTEXT.md`](CONTEXT.md): decisiones y handoffs append-only.
- [`INDEX.md`](INDEX.md): este mapa de navegacion.
- [`TESTING.md`](TESTING.md): checks vivos del ciclo BETA-STT, humanos o no disponibles.
- [`WORKFLOW.md`](WORKFLOW.md): extension subordinada de agents-workflow v3.

## PLANES Y EXTENSIONES

- [`archive/PLAN_v1.99-beta-foundation.md`](archive/PLAN_v1.99-beta-foundation.md): plan cerrado
  BETA-FOUNDATION, veredicto `APTO`.
- [`PLAN_v2.0-ph21-stt.md`](PLAN_v2.0-ph21-stt.md): draft superseded antes de aprobación.
- [`PLAN_PH21.md`](PLAN_PH21.md): fuente legacy de G0, sin autoridad activa.
- [`PLAN.md`](PLAN.md): roadmap y alcance de transicion.
- [`BUGS.md`](BUGS.md): registro de bugs, sin autoridad de scope.
- [`USER.md`](USER.md): operaciones y decisiones exclusivas del dueño.
- [`IDEAS.md`](IDEAS.md): ideas no decididas.
- [`skills/manage_context/SKILL.md`](skills/manage_context/SKILL.md): suplemento local de REINDEX.

## MAPAS Y DOCUMENTACION

- [`APPCORE.md`](APPCORE.md): mapa factual de arquitectura estable 1.9.1 y superficies beta 1.99.1.
- [`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md): forma del sistema y limites.
- [`docs/DEVELOPING.md`](../docs/DEVELOPING.md): desarrollo, gates y release.
- [`README.md`](../README.md): entrada publica del repositorio.

## PRODUCTO CLAVE

- `backend/run.py`, `backend/main.py`: entrypoint HTTPS/Uvicorn, REST, WebSocket y static mount.
- `backend/auth.py`, `backend/ai_pipeline.py`: pairing, licencia cacheada y proxy de voz.
- `backend/input_emulator.py`, `backend/kiosk.py`, `backend/discovery.py`, `backend/audio.py`:
  input, ventanas, apps y audio.
- `frontend/index.html`, `frontend/app.js`, `frontend/sw.js`, `frontend/skins.css`:
  PWA, cliente WS, cache y temas.
- `scripts/install.sh`, `scripts/build_deb.sh`, `scripts/update.sh`, `scripts/uninstall.sh`:
  instalacion, paquete, OTA y desinstalacion.
- `website/index.html`, `website/en/index.html`, `website/latest.json`, `website/install.sh`:
  landing, canal de release e instalador.
- `supabase/functions/ai-proxy`, `validate-license`, `send-feedback`, `stripe-webhook`:
  funciones Edge tracked; el despliegue no se afirma desde Git.
- `backend/supabase_schema.sql`: tablas, RLS y RPC del backend cloud.

## HISTORICO Y ASSETS

- [`archive/`](archive/): historico; no es autoridad operativa ni se reescribe durante REINDEX.
- [`archive/TESTING_legacy_2026-08-21.md`](archive/TESTING_legacy_2026-08-21.md): snapshot de
  testing previo a v3.
- [`archive/TESTING_beta-foundation_1.99.1.md`](archive/TESTING_beta-foundation_1.99.1.md): snapshot
  exacto de testing completado para BETA-FOUNDATION.
- [`design/`](design/): diseño no operativo; no es fuente de arquitectura.
- `design/skins2/lochi.png`: asset untracked preexistente; preservado, no es navegación operativa.
- `.work/`: evidencia efimera si existe; no se inventa ni se indexa como producto.

## COMANDOS VERIFICADOS U OBSERVADOS

- `git status --short --branch`, `git rev-parse HEAD`, `git ls-files`.
- `git diff --check`.
- `python3 scripts/check_css_sync.py`.
- `node --check frontend/app.js`.
- `python -m py_compile backend/*.py`.
- `bash scripts/build_deb.sh`.
- `bash scripts/install.sh`, `bash scripts/update.sh`, `bash scripts/uninstall.sh`.
- `git ls-files tests` confirma que no hay directorio de tests tracked.
