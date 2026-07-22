# PLAN v1.9 — LANZAMIENTO (ai-proxy + licencias 1-dispositivo + Stripe LIVE + web + privatizar)

> Documento MAESTRO de fase (mapa completo). Cada tarea T-NN recibe su brief
> spoon-fed para Gemini al ejecutarla, auditada por Claude entre medio.
> Planifica/audita: Claude (Fable 5). Ejecuta TODO: Gemini. Flujo: AGENTS.md.

## OBJETIVO
Lanzar comercialmente: llaves de IA fuera del device (ai-proxy), anti-abuso real,
licencia atada a 1 dispositivo con mudanza autoservicio, Stripe LIVE a $5 USD,
dominio propio + rebrand + web rediseñada, repo privado. Cierra con release v1.9.0
validado en device.

## ARQUITECTURA DECIDIDA (diseño de esta fase — leer antes de cualquier T)

### ai-proxy (pieza central)
- **Hoy:** el backend del HTPC llama a Together DIRECTO con `CLOUD_STT_KEY`/`CLOUD_LLM_KEY`
  en su `.env`. Cualquier comprador extrae las llaves y consume sin límite.
- **Destino:** nueva Edge Function `supabase/functions/ai-proxy/`. El backend del device
  manda `{license_token, device_id, valid_targets, audio}` (multipart) → el proxy hace
  TODO server-side: kill-switch → cap global → licencia+activación+cuota (RPC atómico
  `consume_voice`) → cap 512KB → Together STT → Together LLM (intent) → log de métricas →
  devuelve el intent JSON. **Las llaves Together viven SOLO en secrets de Supabase.**
- STT+LLM en UNA llamada al proxy (1 round-trip, métrica por comando completa).
- `ai_pipeline.py` del device queda reducido a: empaquetar audio + llamar al proxy +
  devolver intent. Sin llaves Together en el device NUNCA MÁS.
- **Consecuencia aceptada:** la voz REQUIERE internet (ya lo requería — Together es cloud).
  La gracia offline 72h queda solo para el ESTADO premium (card/skins), no para voz.
- `validate-license` (función existente) QUEDA para checks de estado sin consumo
  (`is_license_valid_cached_or_online`). El camino de consumo migra al proxy; el
  parámetro `consume` de validate-license queda deprecado (no se borra en esta fase).

### Licencia = 1 dispositivo simultáneo (PH-LICENCIAS, diseño 2026-07-19 en PLAN.md)
- `device_id` = **sha256 de `/etc/machine-id`** (hasheado: no mandamos el id crudo).
- Tabla `activations` (1 fila por key): device_id, activated_at, last_seen.
- Claim: sin dueño / mismo device / last_seen>72h → activa. Otro device activo →
  `in_use_elsewhere` → la PWA pregunta "¿Mudar la key aquí? El otro dispositivo
  perderá el premium" → confirmar → claim con `force=true` (takeover).
- `uninstall.sh` llama release best-effort. Heartbeat: cada validación/consumo
  actualiza last_seen.
- Edge case aceptado: device expulsado conserva premium ≤72h (cache de gracia).
- Rotación por robo: v1 MANUAL (procedimiento documentado, T-55); autoservicio = post-lanzamiento.

### Anti-abuso (PH-ANTIABUSO — obligatorio, va DENTRO del proxy)
- Cap de tamaño REAL server-side: **512 KB** (~60s Opus) en el WS handler del device
  Y en el proxy (hoy 5MB = ~40min de audio facturable, y el límite de 8s es solo client-side).
- Kill-switch global: tabla `service_state` clave `voice` → `{enabled, daily_global_cap}`.
  `enabled=false` (manual, dueño en SQL editor) o cap global diario superado → voz off
  para todos. Seguro contra factura sorpresa. Alerta por email = opcional post-dominio (Resend).
- Cuota por plan: tabla `plan_quotas` (`lifetime`=60/día); `check_license` y `consume_voice`
  la leen (fuera el 60 hardcodeado).
- Métricas: tabla `usage_log` (token, device_id, ts, audio_bytes, ok) → base real de
  costos para decidir precios de Voz 2.0.

### Web / monetización
- Stripe LIVE: producto único **$5 USD lifetime** (hoy el link es TEST 9.99 EUR).
- Dominio propio + rebrand (nombre comercial lo decide el dueño AL COMPRAR el dominio —
  un solo cambio de infra). Email soporte → soporte@<dominio> (hoy correo test).
- PH-WEB: rediseño completo con identidad propia + capturas reales + video + tutoriales.
- Repo → PRIVADO al final. bootstrap.sh (instala por git-clone) muere: instalación
  SOLO por .deb desde la web.

## SCOPE
- **IN:** schema v3 Supabase, ai-proxy, backend→proxy, cap 512KB, activación 1-device +
  mudanza PWA, release en uninstall, cuota unificada 60, Stripe LIVE, dominio/rebrand/
  email, rediseño web, matar bootstrap.sh, docs de rotación, release v1.9.0, privatizar.
- **OUT (post-lanzamiento):** T-39 partir main.py (sigue diferido), rotación autoservicio
  (magic link), compilar backend (Nuitka), multi-distro, Skins 2.0, APK, Gamepad, Voz 2.0,
  OTA auto-reload seamless (HALLAZGOS; entra solo si sobra tiempo al final).

## REGLAS DE ESTA FASE
- Una tarea = un commit `[T-NN]` = un checkpoint de auditoría. `git add` SELECTIVO.
- Evidencia real pegada. Gemini PARA ante error/duda y reporta.
- SQL de Supabase: Gemini escribe el archivo; el DUEÑO lo aplica en el SQL editor y pega
  el resultado (o CLI `supabase db push` solo si el dueño lo aprueba explícito).
- Deploys de Edge Functions: `supabase functions deploy <fn>` — los corre el dueño (CLI
  autenticada). Aprovechar la sesión para el pendiente `send-feedback` (desde v1.5).
- Llaves Together: se CARGAN como secrets de Supabase (dueño) y luego se BORRAN del
  `.env` del HTPC (tras validar E2E). Nunca en el repo.
- Cambios de runtime → RE-TEST DEVICE antes de declarar estable. Release al final.
- Orden: primero infra server-side (T-46..T-49), checkpoint E2E device (T-50), luego
  monetización/web (T-51..T-54, algunas BLOCKED por dueño), cierre (T-55..T-58).

---

# TAREAS

## BLOQUE A — INFRA IA SEGURA (código, sin bloqueos de dueño)

### T-46 — Schema v3 Supabase  [sin runtime device; dueño aplica SQL]
Extender `backend/supabase_schema.sql` con la sección "v3 MIGRATION":
- Tablas nuevas: `plan_quotas` (seed lifetime=60), `activations`, `usage_log` (+índice ts),
  `service_state` (seed voice: enabled=true, daily_global_cap=2000). RLS service_role en todas.
- RPCs nuevos: `claim_device(token, device_id, force)` → activated/in_use_elsewhere/invalid
  (con auto-takeover si last_seen>72h); `release_device(token, device_id)`;
  `consume_voice(token, device_id, audio_bytes)` → chequeo ATÓMICO completo:
  kill-switch → cap global → licencia activa → activación device (heartbeat/auto-takeover
  72h) → cuota por plan → incrementa + loguea → `{ok, remaining_today, plan}` o
  `{ok:false, reason}`.
- Modificar `check_license` para leer cuota de `plan_quotas` (no 60 hardcodeado).
- Grants: revoke public/anon/authenticated + grant service_role en los 3 RPCs nuevos.
**Verificación:** dueño aplica en SQL editor → 0 errores; `select * from plan_quotas /
service_state` pegado. **Riesgo:** bajo (aditivo; no rompe validate-license actual).

### T-47 — Edge Function ai-proxy  [dueño deploya + carga secrets]
Nueva `supabase/functions/ai-proxy/index.ts`:
- POST multipart: campos `token`, `device_id`, `targets` (JSON array), archivo `audio`.
- Pipeline: cap 512KB (413 si excede) → RPC `consume_voice` (mapear reasons a HTTP:
  service_disabled/global_cap→503, invalid_license→403, in_use_elsewhere→409,
  quota_exceeded→429) → Together STT (whisper-large-v3) → Together LLM (Qwen2.5-7B,
  mismo system prompt de intents que hoy tiene ai_pipeline.py, con targets dinámicos) →
  valida action ∈ {launch_kiosk, media_control, search} → responde
  `{ok, text, intent, remaining_today}`.
- Endpoints hermanos en la misma función (por `action` en el body o rutas): `activate`
  (claim_device, con force opcional) y `release` (release_device).
- Secrets: `TOGETHER_API_KEY` (+ URLs/modelos con defaults). Rate limit en memoria
  10 req/min por token (como validate-license).
**Verificación:** deploy OK + `curl` de prueba con licencia dev (activate + voz con un
audio corto real) pegados. **Dueño:** deploy ai-proxy + send-feedback pendiente + cargar
secret Together. **Riesgo:** medio (código nuevo server-side; no toca el device aún).

### T-48 — Backend device → proxy  [RE-TEST DEVICE]
- `ai_pipeline.py`: reescribir a cliente del proxy — `AI_PROXY_URL` (default a la función
  desplegada), manda multipart con token de licencia + device_id + targets + audio.
  ELIMINAR `CLOUD_STT_KEY`/`CLOUD_LLM_KEY` y toda llamada directa a Together.
- Nuevo helper `device_id()`: sha256 de `/etc/machine-id` (fallback: hash de hostname+mac).
- `main.py`: cap de audio 5MB → **512_000 bytes** (mismo límite que el proxy); el handler
  de voz ya no llama `validate_license_and_increment` (el proxy valida/consume — quitar
  la doble validación); manejar respuestas del proxy: 429→"cuota agotada", 409→disparar
  flujo de mudanza (T-49), 503→"voz temporalmente deshabilitada".
- `.env.example`: fuera CLOUD_*; documentar `AI_PROXY_URL` (opcional) y `LICENSE_TOKEN`.
**Verificación:** py_compile + pyflakes; grep 0 refs a CLOUD_STT_KEY/CLOUD_LLM_KEY;
voz E2E en dev. **Riesgo:** alto (camino crítico de voz) → auditoría estricta.

### T-49 — Activación 1-device + mudanza en PWA + cuota 60  [RE-TEST DEVICE]
- Backend: al validar licencia en startup/status → claim (`activate`); endpoint local
  `/api/license/takeover` (auth pairing) → claim force=true; `uninstall.sh` → release
  best-effort (curl con timeout corto, nunca bloquea la desinstalación).
- PWA (`app.js`): ante `in_use_elsewhere` → diálogo "¿Mudar la key aquí? El otro
  dispositivo perderá el premium" → confirmar → `/api/license/takeover` → reintenta.
- Quick fix incluido: card de voz `app.js:204` "100 cmds/día" → "60 comandos/día"
  (unificado con web y cuota real).
**Verificación:** node --check + guard CSS; flujo simulado (claim con device_id falso →
409 → takeover → OK) con curl pegado. **Riesgo:** medio.

## BLOQUE B — CHECKPOINT DEVICE

### T-50 — E2E en device del dueño  [checkpoint obligatorio]
Guion para el dueño (Claude lo escribe al llegar acá): voz completa vía proxy (latencia
comparable), cuota real decrementa, card correcta, mudanza simulada (claim desde otro
device_id → prompt → takeover), kill-switch manual (enabled=false → voz off → true),
`.env` del HTPC SIN llaves Together (borradas tras validar). Solo con TODO verde se
avanza al bloque C.

## BLOQUE C — MONETIZACIÓN + WEB  [dependencias del dueño marcadas]

### T-51 — Stripe LIVE $5 USD  [BLOCKED: dueño crea producto]
- Dueño: producto "LinuxRemotePlayer Pro" $5 USD pago único en Stripe LIVE + payment
  link + webhook LIVE apuntando a `stripe-webhook` + secrets LIVE en Supabase
  (`STRIPE_WEBHOOK_SECRET`, key). Prueba de compra real (refund después).
- Gemini: `website/index.html` link de checkout TEST→LIVE; revisar `stripe-webhook/index.ts`
  (que emita licencia con el evento LIVE; ajustes si hacen falta); precio coherente en toda la web.
**Verificación:** compra de prueba → licencia emitida en Supabase → email recibido.

### T-52 — Dominio + rebrand + email  [BLOCKED: dueño compra dominio y decide nombre]
- Dueño: decide nombre comercial + compra dominio + lo conecta a Vercel + crea
  soporte@<dominio> (o forwarding) + Resend con el dominio (para emails de licencia).
- Gemini: reemplazar aeciminer02@gmail.com (index.html:870/887, gracias.html:226/7) por
  soporte@<dominio>; nombre comercial en web/README/PWA donde aplique ("linuxremoteplayer"
  queda como nombre técnico); URLs latest.json/downloads si cambia el host del OTA
  (¡OJO: la PWA vieja consulta la URL vieja — mantener la URL Vercel vieja respondiendo
  o redirect, si no los 1.8.0 no ven más OTA!).

### T-53 — PH-WEB: rediseño completo  [necesita T-52 (identidad) + capturas del dueño]
Matar el diseño "IA genérico": identidad propia, capturas REALES device (TV+teléfono),
video de la app en acción, tutoriales (instalar / actualizar OTA / reinstalar PWA),
sección premium clara (qué incluye la Pro lifetime: voz IA con 60/día, skins, futuro APK),
precio $5, FAQ, requisitos (Debian/Ubuntu+systemd), soporte. Puede partirse en 2-3 commits.

### T-54 — Instalación sin repo público  [RE-TEST DEVICE leve]
`bootstrap.sh` clona el repo → MUERE con repo privado. Matar/reescribir: instalación
canónica = descargar .deb desde la web (`curl -L <url>/downloads/latest.deb && apt install`).
Revisar README/website/TESTING.md para que NINGUNA instrucción dependa de git clone.
**Verificación:** grep 0 refs a bootstrap/git-clone en instrucciones de usuario final.

## BLOQUE D — CIERRE

### T-55 — Docs operativas + .agents  [sin runtime]
- GUIA_AGUSTIN (o doc nuevo): procedimiento MANUAL de rotación de key robada (responder
  SOLO al correo registrado en la licencia → active=false a la vieja + key nueva por
  el mismo correo; ladrón muere en ≤72h), y cómo operar kill-switch/cuotas/métricas
  (queries SQL listas para pegar).
- Carryover T-43/T-44 (quedó colgado de v1.8): WORKFLOW.md canónico + .agents/README.md
  índice + archivar briefs cerrados. CHANGELOG entrada 1.9.0.

### T-56 — Release v1.9.0 + regresión  [publica a producción]
Proceso estándar (AGENTS.md): clon WSL nativo → bump VERSION 1.9.0 → CHANGELOG →
build_deb → verificar (sw.js=lrp-1.9.0, app.js íntegro, sha256 triple-match) →
downloads/ + latest.json → commit → STOP → auditoría Claude → push → Vercel →
regresión COMPLETA TESTING.md en device + OTA 1.8.0→1.9.0 + voz vía proxy.

### T-57 — Privatizar repo + verificación post  [dueño ejecuta]
- ANTES de privatizar, verificar: Vercel con acceso GitHub app al repo privado (si el
  deploy es por integración GitHub, debe seguir deployando); OTA/downloads servidos por
  Vercel (no por GitHub raw — confirmar 0 URLs a raw.githubusercontent/github.com en
  código/web).
- Dueño privatiza → push de prueba → Vercel deploya → OTA sigue OK → LANZADO.

---

# DEFINITION OF DONE (fase v1.9)
- [ ] Llaves Together SOLO en Supabase secrets; `.env` del HTPC sin llaves de IA.
- [ ] Voz E2E vía ai-proxy en device (latencia aceptable para el dueño).
- [ ] Cap 512KB server-side (proxy Y device); kill-switch + cap global operativos.
- [ ] Licencia = 1 dispositivo con mudanza autoservicio validada; release en uninstall.
- [ ] Cuota 60/día por plan (tabla), unificada en app+web; métricas registrándose.
- [ ] Stripe LIVE $5 USD con compra de prueba real → licencia emitida.
- [ ] Dominio propio + soporte@dominio + rebrand aplicado; web rediseñada con capturas/video.
- [ ] Instalación 100% por .deb (bootstrap.sh muerto); docs sin git-clone.
- [ ] Rotación manual de keys documentada; .agents con WORKFLOW.md.
- [ ] Release v1.9.0 LIVE + regresión device verde + OTA verificado.
- [ ] Repo PRIVADO con Vercel/OTA funcionando.

# ACCIONES DEL DUEÑO (fuera de código)
- [ ] Aplicar SQL v3 en Supabase (T-46) y pegar resultado.
- [ ] Deploy ai-proxy + send-feedback (pendiente v1.5) + secret TOGETHER_API_KEY (T-47).
- [ ] E2E device (T-50) + borrar llaves Together del `.env` del HTPC al validar.
- [ ] Stripe LIVE: producto $5, webhook, compra de prueba (T-51).
- [ ] Decidir nombre comercial + comprar dominio + email soporte + Resend (T-52).
- [ ] Screenshots reales (TV + teléfono) + video (T-53) — pendiente desde v1.8.
- [ ] Regresión TESTING.md + OTA tras release (T-56). Privatizar repo (T-57).

# NOTAS DE RIESGO
- T-48 toca el camino crítico de voz → no se borran las llaves del `.env` del HTPC hasta
  que T-50 valide E2E (rollback instantáneo posible mientras tanto).
- Cambio de dominio: mantener la URL Vercel vieja viva (o redirect) hasta que la base
  instalada migre — las PWA 1.8.0 consultan latest.json en la URL vieja.
- Latencia de voz: proxy agrega 1 hop (device→Supabase→Together). Se mide en T-50; si
  degrada feo, opción B = proxy devuelve solo llaves efímeras (NO preferida; evaluar solo
  si duele).
- Todo lo BLOCKED por dueño (T-51/52/53) puede solaparse: mientras espera, Gemini avanza
  T-54/T-55.
