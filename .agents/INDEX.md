# INDEX - navegacion del repositorio

```yaml
last_reindexed_at: 2026-10-29T05:25:00-05:00
source_commit: dcd26f5
dirty: true
active_plan: PLAN_v1.0.0-public.md (D56; T-150 y T-151 aptos, T-152 en curso, T-153..T-155 pendientes, T-157 voz diferida)
state: "LRP OS 1.0.0 GPL-3.0: F1 (limpieza) y F2 (panel/onboarding) aptas; binarios irán a GitHub Releases y la web a Vercel por Git; rama legacy/2.0 archivada"
```

El estado activo pertenece a [`CURRENT.md`](CURRENT.md), no a este indice.

## CONTROL V3

- [`../AGENTS.md`](../AGENTS.md): shim raiz, origen importado y CAVEMAN.
- [`AGENTS.md`](AGENTS.md): roles, assurance, propiedad y gates.
- [`CURRENT.md`](CURRENT.md): estado vivo y proxima accion.
- [`CONTEXT.md`](CONTEXT.md): decisiones y handoffs append-only.
- [`INDEX.md`](INDEX.md): este mapa de navegacion.
- [`TESTING.md`](TESTING.md): checks vivos de DEBIAN-FOUNDATION, humanos o no disponibles.
- [`WORKFLOW.md`](WORKFLOW.md): extension subordinada de agents-workflow v3.

## PLANES Y EXTENSIONES

- [`PLAN_v1.0.0-public.md`](PLAN_v1.0.0-public.md): **plan activo** del release open source 1.0.0 (GPL-3.0, ISO-only, sin OTA), aprobado D56.
- [`PLAN_v2.0.0-release.md`](PLAN_v2.0.0-release.md): histórico del ciclo comercial 2.0.0 (D51); su código vive en `legacy/2.0`.
- [`PLAN_v2.0-appliance.md`](PLAN_v2.0-appliance.md): plan v3 completado (LRP OS Appliance & Local Voice, T-132..T-142 apto, G4 APTO).
- [`PLAN_v1.99.2-debian-htpc-foundation.md`](PLAN_v1.99.2-debian-htpc-foundation.md): plan cerrado DEBIAN-FOUNDATION, veredicto `APTO`.
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

- [`APPCORE.md`](APPCORE.md): mapa factual del codigo 1.99.2 / 2.0.0-dev (base 1.9.1).
- [`../AUDITORIA_ASTRA.md`](../AUDITORIA_ASTRA.md): auditoría de seguridad y resiliencia (ASTRA-01..04 remediados).
- [`../NEWUI.MD`](../NEWUI.MD): especificación de diseño canónico Mobile PWA 2.0 (Mantatomic Wheel).
- [`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md): forma del sistema y limites.
- [`docs/DEVELOPING.md`](../docs/DEVELOPING.md): desarrollo, gates y release.
- [`README.md`](../README.md): entrada publica del repositorio.

## PRODUCTO CLAVE

- `backend/run.py`, `backend/main.py`: entrypoint HTTPS/Uvicorn, REST, WebSocket y static mount.
- `backend/auth.py`: gestión de token de pairing (ASTRA-02 revocación inmediata).
- `backend/ota_security.py`: verificación criptográfica asimétrica Ed25519 y protección anti-downgrade (T-142).
- `backend/ai_pipeline.py`: orquestador de voz local (whisper.cpp AVX1 + local_intent), sin proxy cloud.
- `backend/local_intent.py`: motor NLU local Needle 2 (regex/pattern matching en CPU, <0.25ms).
- `backend/system_platform.py`: endpoints `/api/system/*` (audio PipeWire, Wi-Fi, BT, energía, display).
- `backend/input_emulator.py`, `backend/kiosk.py`, `backend/discovery.py`, `backend/audio.py`:
  input uinput, ventanas Firefox ESR Kiosk, apps y audio.
- `frontend/index.html`, `frontend/app.js`, `frontend/sw.js`, `frontend/skins.css`:
  PWA Mobile 2.0 (rueda Mantatomic SVG, App Hub, Quick Dock, scroll lateral independiente, temas Day/Night/Café/Anime).
- `scripts/install.sh`, `scripts/build_deb.sh`, `scripts/update.sh`, `scripts/uninstall.sh`,
  `scripts/lrp-cleanup.sh`: instalacion modo `htpc`, paquete, OTA con watchdog/rollback, desinstalacion y cleanup.
- `scripts/sign_ota_manifest.py`: herramienta offline para firmar digitalmente manifiestos OTA con clave Ed25519 (T-142).
- `scripts/debian/iso/build_iso.sh`: orquestador live-build para generar imagen ISO híbrida USB Debian 13 minimal (T-141).
- `scripts/debian/iso/config/`: assets de arranque inyectados por `includes.chroot` — `hosts` (B20),
  `default-grub` + `lrp-splash.png` (fondo GRUB y splash plymouth `lrp`), `zram-generator.conf`.
- `scripts/debian/preflight.sh`, `nvidia-bootstrap.sh`, `session-bootstrap.sh`,
  `platform-bootstrap.sh`, `bootstrap.sh`: baseline, driver/sesion/plataforma y orquestador resumible.
- `website/index.html`, `website/en/index.html`, `website/latest.json`, `website/install.sh`:
  landing, canal estable e instalador.
- `website/beta/latest.json`, `website/beta/install.sh`, `website/beta/downloads/`: manifiesto,
  instalador y artefacto `1.99.2` amd64.
- `supabase/functions/ai-proxy`, `validate-license`, `send-feedback`, `stripe-webhook`:
  funciones Edge legacy tracked; desacopladas del runtime del appliance.
- `backend/supabase_schema.sql`: tablas, RLS y RPC del backend cloud legacy.

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
- `tests/` existe con suites Debian/kiosk/release (`test_debian_*`, `test_kiosk_debian.py`, `test_t125_installer.py`, `test_beta_*`).
- `python -m pytest -q`; `bash -n` por cada script shell tocado.
