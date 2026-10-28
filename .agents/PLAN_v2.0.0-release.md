# PLAN v2.0.0 — Integración y release estable

```yaml
status: approved
goal: publicar LRP 2.0.0 estable desde codex/debian-foundation, con la rama integrada en main, artefacto reconciliado y firmado, y nube/licencias retiradas del producto instalado y de la web
assurance: Standard
base_estable: 1.9.1
release_objetivo: 2.0.0
approval_digest: 2814bb3c3252c3a6435db1c6e3b127300f72df7db850f42479159233d5661a76
approval_actor: owner
approved_at: 2026-10-21T16:55:00-05:00
approval_decision_id: D51
approval_source: 2814bb3c3252c3a6435db1c6e3b127300f72df7db850f42479159233d5661a76
created_at: 2026-10-21T16:45:00-05:00
source_commit: 88cf2f6
```

Aprobado por el dueño (D51). Ninguna tarea de producto se despacha hasta `RUN THE LOOP`.

## Canonical design approved

Digest boundary: exact UTF-8/LF bytes between `CANONICAL-DESIGN-BEGIN` and
`CANONICAL-DESIGN-END`, excluding the marker lines.

<!-- CANONICAL-DESIGN-BEGIN -->
1. LRP 2.0.0 se publica desde `main` tras un merge `--no-ff` de `codex/debian-foundation` @ `50da3ca`, que preserva los 17 commits `[T-NN]`.
2. El artefacto beta `1.99.2` publicado (`a0b54c85…`) queda congelado; el rebuild de la rama (`25ea4173…`) no se publica bajo `1.99.2`.
3. `VERSION` pasa a `2.0.0`; el manifiesto estable 2.0.0 apunta al artefacto 2.0.0 firmado con archivo = sidecar = manifiesto.
4. PH24 retira licencia, proxy cloud, cuotas y activación del backend, frontend, web ES/EN y docs; el control y la voz local no consultan red.
5. El retiro de Supabase en producción lo ejecuta el dueño tras verificar el corte; el repo no puede demostrarlo.
6. `LICENSE` no se modifica en 2.0.0; cualquier relicenciamiento es una decisión separada.
7. Gates de release: instalación limpia, upgrade `1.9.1 -> 2.0.0` con rollback, operación sin red, desinstalación, `dpkg -V` y verificación física en HTPC.
8. Non-goals: multi-distro/CI (PH25), skins 2.0 (PH17) y port Windows.
<!-- CANONICAL-DESIGN-END -->

## Hechos verificados (2026-10-21)

- `main` @ `88cf2f6`; `codex/debian-foundation` @ `50da3ca`; merge-base `98bb9f1`.
- La rama aporta 46 archivos (`git diff --name-status main...codex/debian-foundation`) y 17 commits;
  `main` tiene 1 commit que la rama no tiene (`88cf2f6`).
- `main` no contiene `backend/ota_security.py`, `backend/local_intent.py`, `backend/local_stt.py`,
  `backend/system_platform.py` ni `scripts/debian/iso/`; todo eso existe solo en la rama.
- La rama recrea el artefacto beta `1.99.2` con SHA `25ea4173…` (331202 bytes) mientras el publicado
  en `main` es `a0b54c85…` (330280 bytes) y `website/beta/latest.json` de `main` sirve `a0b54c85…`.
  Reemplazar el archivo sin cambiar versión alteraría el artefacto de clientes beta ya instalados.
- La rama aún contiene superficies cloud/licencia: `backend/auth.py` (`LICENSE_API_URL`,
  `is_license_valid_cached_or_online`), `backend/ai_pipeline.py::proxy_license_action`,
  `backend/main.py::_autoenable_voice_for_existing_license`, `supabase/functions/*` (4),
  `backend/supabase_schema.sql`, `backend/.env.example`.
- `VERSION` es `1.99.2` en `main` y en la rama; no existe tag ni manifiesto `2.0.0`.
- Estable publicada: `1.9.1` SHA `82b6bc52…`. Beta publicada: `1.99.2` SHA `a0b54c85…`.
- G4 de fase v2.0 APTO (`PLAN_v2.0-appliance.md`), evidencia determinista registrada allí.

## Decisiones materiales pendientes (preflight)

- **D-R1 Estrategia de integración — APROBADA (owner, D51)**: merge `--no-ff` de la rama en `main`
  preservando los 17 commits `[T-NN]`.
- **D-R2 Deriva del artefacto `1.99.2` — APROBADA (owner, D51)**: `1.99.2` queda congelado en
  `a0b54c85…`; el rebuild `25ea4173…` se publica como `2.0.0`.
- **D-R3 Licencia — APROBADA (owner, D51)**: `LICENSE` no se modifica en 2.0.0.

## Scope

- In scope:
  - Integración de `codex/debian-foundation` en `main` y bump `VERSION` a `2.0.0`.
  - Reconciliación de artefacto: un solo build 2.0.0, firma Ed25519 y triple match
    (archivo = sidecar = manifiesto).
  - PH24 backend: retirar validación de licencia, proxy cloud, cuotas y activación.
  - PH24 frontend: retirar compra, clave, plan, takeover y gates; voz disponible localmente.
  - PH24 website ES/EN: landing 2.0, retirar Paddle/precio/premium/términos de venta, Patreon
    voluntario, `latest.json` 2.0.0.
  - PH24 documentación: README, `docs/`, changelog, `uninstall`, `.env.example`.
  - Supabase de producción: retiro operado por el dueño tras verificar el corte.
  - Gates de release: instalación limpia, upgrade `1.9.1 -> 2.0.0`, operación sin red, desinstalación.
- Non-goals: multi-distro y CI (PH25), skins 2.0 (PH17), port Windows, alias Vercel legado nuevo.

## Tasks

### T-143 — Integración de rama y reconciliación de artefacto

- Status: apto (merge `--no-ff` `ad30b95`, beta congelado `db97991`, push `0 0`, auditoría APTO `d3495ab`;
  verificado además en hierro el 2026-10-22 con la ISO `720fc8…`: instalación y arranque UEFI desde
  disco OK tras corregir el `BootOrder` del firmware — D53)
- Depends on: aprobación D51 vigente; auditoría APTO.
- Objective: integrar `codex/debian-foundation` en `main` según D-R1; resolver la deriva `25ea41…` vs
  `a0b54c85…` según D-R2; bump `VERSION` a `2.0.0` y actualizar `frontend/sw.js`/manifiestos.
- Allowed scope: historia Git, `VERSION`, `frontend/sw.js`, `website/*/latest.json`, artefactos.
- Acceptance: `main` contiene los 17 commits; `VERSION` = `2.0.0`; un único artefacto 2.0.0 con SHA
  reproducible; ningún cliente beta recibe bytes distintos bajo `1.99.2`.
- Gates: `git merge-base --is-ancestor`, `git status`, `python3 scripts/check_css_sync.py`.
- Evidence: commits, `git log --oneline`, hashes de artefacto.

### T-144 — PH24 backend sin licencia ni proxy cloud

- Status: apto — auditor independiente **APTO** el 2026-10-22 (7/7 criterios, defectos none); backend
  desplegado y verificado en el HTPC (`licensed=true, license_source=local`, stubs locales sin red,
  audio 200, 0 referencias legacy). Commiteado el 2026-10-27 en `5cd1eeb`. Residuo fuera de scope:
  `.env` local y `scripts/*` mencionan `.license_cache` (inertes; limpia T-145/T-147).
- Objective: eliminar `LICENSE_API_URL`/`is_license_valid_cached_or_online`, `proxy_license_action`,
  `_autoenable_voice_for_existing_license` y sus llamadas; la voz local no consulta cuota.
- Allowed scope: `backend/auth.py`, `backend/ai_pipeline.py`, `backend/main.py`, `backend/config.py`,
  `backend/.env.example`, tests asociados.
- Acceptance: ninguna ruta instalada exige licencia para operar; voz funciona offline sin token;
  arranque sin `LICENSE_TOKEN`.
- Gates: `python -m py_compile backend/*.py`; `python -m pytest -q tests/test_local_intent.py tests/test_local_stt.py`.
- Evidence: `archivo:línea` sin referencias a licencia; exit codes.

### T-145 — PH24 frontend sin compra, plan ni takeover

- Status: ready (T-144 apto y commiteado en `5cd1eeb`)
- Objective: retirar de la PWA compra, clave, plan, takeover y gates; mantener control, voz y ajustes.
- Allowed scope: `frontend/index.html`, `frontend/app.js`, `frontend/skins.css`, `frontend/status.html`.
- Acceptance: PWA opera completa sin estado de licencia; invariante B1/T-79 intacta (sin
  `viewport-fit=cover`); contraste multi-skin conservado.
- Gates: `node --check frontend/app.js`; `python3 scripts/check_css_sync.py`.
- Evidence: diff, exit codes.

### T-146 — PH24 website, docs y manifiesto estable 2.0.0

- Status: ready (bloqueada por T-145)
- Objective: rediseñar ES/EN para 2.0 (voz local, requisitos reales, privacidad, Patreon), retirar
  Paddle/precio/premium/términos de venta, publicar `latest.json` 2.0.0 y actualizar README, `docs/`,
  changelog, `uninstall` y `.env.example`.
- Allowed scope: `website/`, `README.md`, `docs/`, `CHANGELOG`, `scripts/uninstall.sh`.
- Acceptance: ninguna página pública menciona precio, Paddle o plan; el manifiesto 2.0.0 apunta al
  artefacto de T-143 con SHA correcto; stable no descubre beta.
- Gates: enlaces locales, `grep` de términos retirados en `website/` y `README.md`.
- Evidence: grep vacío, manifiesto, diff.

### T-147 — Retiro de Supabase en producción (dueño)

- Status: blocked (requiere operación del dueño)
- Depends on: T-144, T-145, T-146.
- Objective: retirar servicios de keys, validación, activaciones, cuotas, voice y proxy IA; revocar
  secretos tras verificar el corte.
- Acceptance: ninguna URL del sitio ni del producto apunta a `functions.supabase.co`; secretos revocados.
- Evidence: salida del panel/Supabase y grep del repo; el Arquitecto no ejecuta la operación.

### T-148 — Gates de release y cierre 2.0.0

- Status: blocked (depende de T-143..T-147)
- Objective: verificar instalación limpia, upgrade `1.9.1 -> 2.0.0` con rollback, operación sin
  internet, desinstalación y artefacto triple-match firmado; emitir G4.
- Acceptance: todas las rutas pasan; `dpkg -V` limpio; sin red el control, la voz y los ajustes operan.
- Gates: suite completa, `bash -n`, `node --check`, `check_css_sync.py`, verificación física en HTPC.
- Evidence: cápsula de auditoría de fase y dictamen.

### T-149 — Estabilización sobre appliance instalado (D53)

- Status: implementado y commiteado en `cde09c8` (`[T-149]`); B20–B26 corregidos, desplegados y
  verificados en el appliance el 2026-10-22. Cierre pendiente de los checks visuales del dueño
  (`TESTING.md`, D53) y, con el HTPC inalcanzable desde el 2026-10-27, de re-verificación cuando vuelva
  a la red
- Depends on: T-143 apto.
- Objective: corregir bugs críticos y de interfaz sobre el HTPC ya instalado con la ISO `720fc8…`,
  desplegando cada fix repo → SSH → servicio, y dejar la reconstrucción de la ISO para el cierre del
  ciclo (una sola vez, seguida de instalación limpia y gates de T-148).
- Allowed scope: `scripts/debian/iso/**` (hooks, instalador, package-lists, config), `frontend/status.html`,
  `frontend/index.html` si el bug lo exige, `backend/main.py` y unit del backend, `tests/` asociados y
  evidencia en `.agents`.
- Acceptance: B20–B25 corregidos en repo y verificados en el appliance; sin unidades fallidas al
  arranque; panel con audio, Wi-Fi, pantalla y Bluetooth renderizados; splash LRP en GRUB y plymouth;
  instalador con entrada NVRAM `LRP-OS` y report honesto.
- Gates: `bash -n` sobre instalador/hook/`build_iso.sh`; `pytest tests/test_iso_factory.py
  tests/test_t125_installer.py tests/test_debian_release.py`; `python -m py_compile backend/*.py`;
  verificación en appliance por SSH (`/api/status`, `/api/system/*`, `systemctl --failed`).
- Evidence: `BUGS.md` B20–B25, `CURRENT.md` fresh evidence, `TESTING.md` D53 y capturas del dueño.

## Riesgos

- Reemplazar el artefacto `1.99.2` rompe integridad de clientes beta (D-R2).
- El retiro de licencia puede dejar referencias muertas en frontend/config si se hace parcial.
- Supabase y Vercel son estado externo; su corte no se demuestra desde el repo.
- La ISO 2.0.0 debe reconstruirse tras el retiro de licencia y no reutilizar artefactos previos.

## Closure gate

- [ ] D-R1, D-R2 y D-R3 aprobadas por el dueño con digest.
- [ ] T-143..T-146 APTO.
- [ ] T-149 APTO (estabilización sobre el appliance instalado, D53).
- [ ] T-147 ejecutada por el dueño y verificada.
- [ ] T-148 APTO con dictamen de fase.
- [ ] `latest.json` estable sirve `2.0.0` y `1.9.1` deja de ser promovida.
