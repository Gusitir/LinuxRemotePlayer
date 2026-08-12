# APPCORE — mapa factual del código 1.9.1

```yaml
reindexado: 2026-08-11
estado: código publicado cloud/licensed; destino local todavía no implementado
release_destino: 2.0.0
backend_main: 1013 líneas
frontend_app: 1583 líneas
```

## DIRECTORIOS

- `backend/`: FastAPI, autenticación, pairing, input, kiosk y cliente de IA cloud.
- `frontend/`: PWA vanilla JS/CSS, sin build de framework.
- `scripts/`: instalación, empaquetado, actualización, desinstalación y guards.
- `website/`: Vercel, landing ES/EN, instalador, `.deb` y `latest.json`.
- `supabase/functions/`: `ai-proxy`, `validate-license`, `stripe-webhook` legacy y feedback.
  Editar repo no despliega funciones.
- `docs/`: documentación humana. `.agents/`: coordinación. `archive/` no se reactiva.

## BACKEND ACTUAL

- `main.py`: endpoints FastAPI, WebSocket, PinManager, apps, kiosk, OTA, licencia y voz.
- Pairing: PIN local de 6 dígitos/TTL y token compartido; QR apunta a HTTPS local.
- Control mutante exige token; rutas locales de status/QR/update usan gates locales explícitos.
- WebSocket: auth inicial, ping, pointer, text, combos, gamepad y audio binario.
- Audio: `main.py` llama `ai_pipeline.voice_command`; intents actuales:
  `launch_kiosk`, `media_control`, `search`.
- `ai_pipeline.py` envía audio a Supabase `ai-proxy`; allí Together hace Whisper/Qwen.
- `auth.py` valida licencia mediante Supabase y caché de gracia.
- Licencia: activate/status/takeover; activar persiste clave y habilita voz.
- OTA: check/apply; apply termina en `sudo lrp-update`. **B19 abierto: sin firma independiente.**
- Docs FastAPI solo con `LRP_DEV=true`.

## FRONTEND ACTUAL

- `app.js`: pairing, WebSocket/reconexión, touchpad, teclado, apps, skins, OTA, licencia y
  push-to-talk de hasta 8 s.
- La voz y sus tarjetas están gateadas por licencia en 1.9.1.
- `index.html`: onboarding PIN, HUD, ajustes, compra/licencia y ayuda.
- `sw.js`: cache versionado en build. Query `?token=` no coincide con shell precacheado (H19).
- `skins.css`: cuatro skins y puente para marcado históricamente oscuro.
- `tailwind-lite.css`: subset manual; `check_css_sync.py` evita usadas-sin-definir.

## SISTEMA E INSTALACIÓN

- `input_emulator.py`: uinput, teclado us/es/latam, pointer y media keys allowlist.
- `discovery.py`: `.desktop`, incluidos Flatpak/Snap/local; respeta Hidden/NoDisplay.
- `kiosk.py`: Firefox primero; fallback Brave/Chromium; cierre gradual.
- `run.py`: HTTPS self-healing, CA por máquina y hoja por IP/FQDN.
- `install.sh`: modo desktop/dedicated, systemd, Firefox, CA/NSS, UFW y suspensión.
- `build_deb.sh`: inyecta versión del SW, ejecuta guard CSS y genera scripts maintainer.
- `lrp-cleanup.sh`: cleanup best-effort, siempre exit 0; lee configuración antes de borrarla.
- `website/install.sh`: `curl | sudo bash`; no reemplazar stdin con `/dev/tty`.

## NUBE/COMERCIAL QUE 2.0.0 DEBE RETIRAR COORDINADAMENTE

- Backend: `auth.py`, `ai_pipeline.py`, endpoints/estado de licencia, BUY_URL y flags de voz.
- Frontend: IndexedDB/localStorage de licencia, UI de compra/activación/takeover y gates.
- Supabase: esquema de licencias/cuotas y funciones `ai-proxy`/`validate-license`/webhook.
- Website/docs ES+EN: Paddle, precio, Pro, cuotas, privacidad cloud y términos de venta.
- Configuración/desinstalador: LICENSE_*, AI_PROXY_URL, BUY_URL y cachés.

No borrar una sola capa y dejar las demás: produciría UI, migraciones o documentación falsas.
El rediseño de `website/` y la retirada en producción de los servicios Supabase de keys/IA son
gates del lanzamiento 2.0.0, no mantenimiento posterior.

## FRONTERAS DEL DESTINO LOCAL — NO EXISTEN AÚN

Componentes previstos, nombres no contractuales hasta PH21-PH23:

- `LocalSpeechEngine`: VAD + STT multilingüe intercambiable.
- `IntentEngine`: Needle 2, solo JSON restringido y confianza.
- `PolicyEngine`: validación, confirmación y rechazo deterministas.
- `ContextStore`: SQLite local, retención y borrado.
- `AdapterRegistry`: MPRIS, entrada y automatización por aplicación.

Un agente no debe buscar estos componentes ni afirmar que están implementados.

## ACOPLAMIENTOS QUE NO SE DEBEN ROMPER

- Versión: `VERSION` → build → service worker → paquete → `latest.json`.
- Pairing token: `.env` o `.pairing_token` según instalación.
- CA: `run.py`, instalador, Firefox/NSS, trust del sistema y cleanup.
- Update: backend → sudoers → `lrp-update` → maintainer scripts → health del servicio.
- Skin: tabla JS, `data-skin`, CSS, assets y precache del SW.

Reindexar tras cada fase que retire nube o añada componentes locales; verificar con repo real.
