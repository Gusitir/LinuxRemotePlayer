# PLAN v1.0.0 — LRP OS open source (GPL-3.0)

```yaml
status: approved
goal: publicar LRP OS 1.0.0 como appliance ISO de código abierto (GPL-3.0), sin licencia/premium, sin OTA, sin nube ni telemetría, servido desde la web junto al APK Android y con documentación de build
assurance: Standard
base_estable: legacy/2.0 (v2.0.0-legacy, archivado)
release_objetivo: 1.0.0
approval_decision_id: D56
approved_at: 2026-10-29T03:00:00-05:00
approval_actor: owner
created_at: 2026-10-29T03:00:00-05:00
source_commit: f698e18
```

Aprobado por el dueño (D56). El desarrollo previo vive en `legacy/2.0` + tag `v2.0.0-legacy`
(licencia GPL-3.0 también), como archivo consultable.

## Diseño canónico aprobado

<!-- CANONICAL-DESIGN-BEGIN -->
1. Producto: ISO Debian 13 que arranca al panel; el móvil controla cursor, teclado, apps, volumen y
   energía. Voz local diferida a T-157 (Needle 3 / voice-to-text); hasta entonces se oculta.
2. Licencia **GPL-3.0** para el repo completo, la ISO y la rama legacy. Avisos de licencia y créditos
   de terceros visibles en la web y en la ISO.
3. Sin licencia, premium, compra, cuotas, cuentas ni telemetría. Sin OTA ni auto-update: las versiones
   se publican por release del repositorio.
4. Sin Supabase ni servicios cloud en el producto ni en la web.
5. La web sirve ISO + APK + checksums, tutoriales de instalación y documentación de arquitectura/build.
6. Android: APK **TWA** firmada, servida aparte (sideload, sin Play Store) con `assetlinks.json` en el
   dominio. iOS: PWA instalada desde Safari con tutorial guiado. Desktop: instrucciones neutras.
7. Versión **1.0.0**. Todo lo comercial previo (2.0.0) queda archivado en `legacy/2.0`.
8. Non-goals de 1.0.0: Windows, multi-distro, Play Store, auto-update, skins 2.0, voz (T-157).
<!-- CANONICAL-DESIGN-END -->

## Scope

- In scope: limpieza de licencia/modo/OTA/Supabase; panel compacto; onboarding QR iOS/Android; APK TWA;
  web de descarga con avisos GPL; docs de build y arquitectura; ISO 1.0.0 reproducible; publicación.
- Non-goals: los del punto 8 del diseño.

## Tasks

### T-150 — F1: limpieza comercial, modo appliance, OTA y Supabase

- Status: **apto** (2026-10-29) — commits `ee93f4c` (GPL/NOTICE), `30dbd69` (frontend),
  `180f717` (backend), `d5b75f7` (OTA backend/panel), `878d948` (OTA scripts/web), `3cf38ed`
  (Supabase), `6df950e` (modo). Gate de fase: `pytest tests/` = 250 passed; HTPC verificado por
  captura y sin referencias legacy en runtime.
- Objective: eliminar del producto toda superficie comercial (licencia/premium/compra), el modo
  appliance/`lrp-setup`, la OTA completa (updater, firma, manifiestos, canal beta) y Supabase.
- Sub-tareas:
  - **T-150a frontend**: fuera tarjeta Licencia, textos “Pro”, voz/micrófono (oculto hasta T-157),
    toggle “TV o Escritorio” y llamadas a `/api/license/*`, `/api/voice/toggle`, `buy_url`.
  - **T-150b backend**: fuera stubs `/api/license/*`, `buy_url`, `/api/voice/toggle` y `LRP_MODE`.
  - **T-150c OTA**: fuera `ota_security.py`, `/api/update/*`, `lrp-update`, `sign_ota_manifest.py`,
    manifiestos `website/*/latest.json`, canal beta y sus tests.
  - **T-150d Supabase**: fuera `supabase/`, `backend/supabase_schema.sql`, referencias en `.env.example`
    y el log `SUPABASE_*` de `run.py`.
- Allowed scope: `backend/`, `frontend/`, `scripts/`, `website/`, `tests/`, `.env.example`.
- Acceptance: `grep` sin referencias ejecutables a licencia/premium/OTA/Supabase; el panel y el control
  funcionan sin ninguna de esas superficies; tests adaptados al contrato nuevo.
- Gates: `py_compile backend/*.py`; `node --check frontend/app.js`; `check_css_sync.py`;
  `pytest -q tests/`.
- Evidence: diffs, greps en 0, exit codes, captura del panel sin tarjetas retiradas.

### T-151 — F2: panel compacto y onboarding de instalación

- Status: pending (depende de T-150)
- Objective: barra de estado corta (dispositivos, latencia, versión) y espacio para el tutorial de
  instalación; QR que detecta plataforma (iOS → PWA, Android → APK, desktop → neutro); B37
  (Wi-Fi “Desconectado” con cable) y Bluetooth limitado a encendido/apagado + lista.
- Allowed scope: `frontend/status.html`, `frontend/index.html`, `backend/main.py`,
  `backend/system_platform.py`, `tests/`.
- Acceptance: panel sin tarjetas retiradas, tutorial visible y correcto en las tres plataformas,
  Wi-Fi honesto, Bluetooth sin promesas que no cumple.
- Gates: `node --check`, `check_css_sync.py`, `pytest -q tests/test_system_platform.py tests/test_onboarding_dual_wifi.py`.
- Evidence: capturas reales de los tres estados de onboarding y del panel final.

### T-152 — F3: web ISO + APK y documentación

- Status: pending (depende de T-151)
- Objective: web que sirve ISO y APK con checksums, avisos GPL y créditos; README, arquitectura, build
  reproducible, `SECURITY.md`, `THIRD_PARTY_LICENSES.md` y auditoría de assets de terceros.
- Allowed scope: `website/`, `docs/`, `README.md`, `CHANGELOG`, `THIRD_PARTY_LICENSES.md`, `NOTICE`.
- Acceptance: sin precios/Paddle/premium; descarga de ISO y APK con SHA256; avisos de licencia
  visibles; assets de terceros reemplazados o acreditados.
- Gates: enlaces locales, `grep` de términos retirados, verificación de checksums.
- Evidence: capturas, greps en 0, manifiesto de release.

### T-153 — F4: APK Android (TWA)

- Status: pending (depende de T-152)
- Objective: APK TWA firmada contra el dominio, `assetlinks.json`, build reproducible documentado.
- Allowed scope: nuevo directorio `android/`, `website/`, docs.
- Acceptance: APK instala en Android, abre el panel, no requiere Play Store; firma custodiada fuera
  del repo.
- Gates: build reproducible + instalación en dispositivo físico.
- Evidence: hash de APK, captura en móvil, docs.

### T-154 — F5: ISO 1.0.0 y gates de release

- Status: pending (depende de T-153)
- Objective: reconstruir la ISO una sola vez con todos los deltas y verificar instalación limpia,
  operación sin red, `dpkg -V` y prueba física.
- Acceptance: ISO instala en UEFI, arranca al panel, control y ajustes sin red, `dpkg -V` limpio.
- Gates: build reproducible, checksum, instalación limpia, suite completa.
- Evidence: cápsula de auditoría de fase, SHA256, capturas.

### T-155 — F6: publicación

- Status: pending (depende de T-154)
- Objective: tag `v1.0.0`, release con ISO + APK + checksums, repo público con avisos GPL.
- Acceptance: release descargable, repo público sin secretos, licencia y créditos correctos.
- Evidence: release, auditoría de secretos, enlaces.

### T-157 — Voz local (diferida)

- Status: blocked (después de la base 1.0.0)
- Objective: evaluar Needle 3 (github.com/cactus-compute/needle) y voice-to-text
  (cactuscompute.com/blog/whistle) para dictado en el campo de texto y comandos locales.
- Nota: hasta entonces todo lo de micrófono queda desactivado y oculto en la UI.

## Riesgos

- La TWA depende de dominio propio y `assetlinks.json`; si cambia el dominio, la APK deja de verificar.
- iOS no permite forzar la instalación de la PWA: el tutorial es la única vía.
- Publicar el repo expone assets de terceros (logos de apps, fondos de skins) y requiere auditoría legal.
- Una ISO de ~2 GB necesita hosting con cuotas; definir antes de F6.
- El alcance puede inflarse: la ISO definitiva se construye una sola vez, al final (F5).

## Closure gate

- [ ] T-150 APTO (limpieza completa).
- [ ] T-151 APTO (panel + onboarding, capturas).
- [ ] T-152 APTO (web/docs/licencia).
- [ ] T-153 APTO (APK en dispositivo físico).
- [ ] T-154 APTO (ISO 1.0.0 + gates).
- [ ] T-155 publicado (release + repo público).
