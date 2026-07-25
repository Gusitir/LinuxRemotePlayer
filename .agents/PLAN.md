# LinuxRemotePlayer — Development Plan

## ✅ COMPLETED

# PH1: SCAFFOLD & CORE (FastAPI + evdev) — DONE
- [x] FastAPI app, WebSocket router, static file serving
- [x] evdev/UInput virtual keyboard-gamepad (input_emulator.py)

# PH2: KIOSK & DISCOVERY — DONE
- [x] .desktop app discovery (discovery.py)
- [x] Kiosk launcher with multi-browser fallback (kiosk.py)

# PH3: CLOUD AI — DONE
- [x] STT (NVIDIA NIM) + LLM intent parsing (OpenRouter)

# PH4: INSTALLER & DEPLOY — DONE
- [x] install.sh (Appliance vs Desktop)
- [x] systemd service configs

# PH5: LOCAL AI & NETWORK CONFIG — DONE
- [x] Local Ollama + Whisper fallback
- [x] Bind 0.0.0.0, serve PWA at /
- [x] Keyboard keys mapped to virtual device

# PH6: BUGFIXING & TESTING — DONE
- [x] /dev/uinput permissions fixed in installer (modprobe + udev rule + input group)

# PH7: SECURITY AUDIT REMEDIATION — DONE
- [x] Auth gate on WebSocket + kiosk/app REST endpoints (PAIRING_TOKEN / Supabase)
- [x] CORS credentials disabled (stop reflecting any origin)
- [x] media_control wired to evdev (volume up/down, mute, play-pause)
- [x] Daily reset for rate-limit counter (last_reset column)
- [x] LLM target_id sanitization + URL encoding
- [x] Audio payload size guard (5 MB)
- [x] requirements.txt pinned

# PH8: HTTPS + PWA — DONE (current iteration)
- [x] backend/run.py: automatic self-healing HTTPS (self-signed cert auto-generated +
      regenerated when the LAN IP changes) — mic works out-of-the-box, zero manual steps
- [x] scripts/gen_cert.sh: manual cert generator (fallback; run.py does this automatically)
- [x] Insecure-context banner: guides phones from http:// to the https:// URL (accept once)
- [x] Installer is non-interactive for HTTPS (no prompt)
- [x] manifest.json + sw.js + icon.svg: installable PWA shell
- [x] 'search' voice intent handler
- [x] ?token= URL pairing (enables link/QR onboarding)
- [x] backend/supabase_schema.sql
- [x] Browser-vs-app detection: install tutorial with iOS/Android SVG diagrams when not installed
- [x] No-zoom hardening (double-tap + pinch) + chromeless standalone meta tags
- [x] Kiosk uses Chromium only (Brave/Firefox dropped); installer auto-detects/installs Chromium

# PH8.5: REMOTE UI REDESIGN — DONE
- [x] Virtual mouse pointer (touchpad: move, tap=left-click, long-press=right-click) + scroll strip
- [x] Free SVG icons (Lucide-style) on all control buttons; app tiles use site favicons (letter fallback)
- [x] Transport uses ordinary keys (Space / Left / Right) so it hits the FOREGROUND kiosk, not the system media session; volume/mute stay as global media keys
- [x] D-pad removed (touchpad replaces it); media transport occupies that space
- [x] System keyboard bridge with Done + Enter/Search; backspace (delete) button
- [x] App drawer (slide-up): suggested + custom web apps (+ add) + detected system apps (.desktop) pinnable to the menu
- [x] Settings drawer (placeholders only): general, app info, web link, share-control QR (local IP), buy premium, skins (premium)
- [x] Browser-vs-installed-app detection fixed (style.display, not the hidden attr that Tailwind flex/grid overrides); desktop browsers show the remote directly for testing
- [x] Toast feedback on launch; safe-area (notch) padding

# PH8.8: AUDIT & REMEDIATION PLAN — DONE
- [x] Stable mDNS hostname resolution (avahi-daemon) + DNS certificate SANs
- [x] Two-tier certificate authority (ca.pem + leaf certs) preventing trust breakage
- [x] Reconnection exponential backoff, WS heartbeat liveness, and offline tailwind-lite.css
- [x] Resilient IndexedDB + LocalStorage pairing token storage & settings entry UI
- [x] Late/lazy initialization of uinput devices to handle installation startup races
- [x] Security: auto-generated pairing token, Same-Origin CORS, and whitelist for evdev keys
- [x] DOM-based XSS protection for dynamic UI tiles & whitelist for voice intent domains
- [x] Atomic rate-limiting via Supabase RPC functions
- [x] Correctness: X11/Xauthority kiosk launch, standard python logging, and IME input diffing
- [x] Round 2 post-implementation review fixes: bootstrap mobile detection, delete custom apps, and toast alerts

## ⬜ REMAINING

# PH9: PAIRING UX & LICENSING BACKEND — DONE
- [x] Backend endpoint to issue/persist a device token
- [x] /pair page that renders a QR encoding https://<ip>:<port>/?token=<token>
- [x] Apply supabase_schema.sql to the project; add RLS policies
- [x] First-run onboarding in PWA (no token -> show pairing prompt instead of 'guest')

# PH10: MONETIZATION (Stripe)
- [ ] Stripe checkout ($4.99 lifetime)
- [ ] Supabase Edge Function / webhook -> issue license token on successful payment
- [ ] Bind purchased token to licenses table

# PH11: FEATURE COMPLETENESS & POLISH
- [x] Voice/AI optional (ENABLE_VOICE flag; /api/config; mic hidden + audio rejected when off) — remote works with NO AI setup
- [x] Kiosk launches with graphical-session env (DISPLAY/Wayland/XDG_RUNTIME_DIR) so Chromium opens from the systemd service
- [x] TESTING.md: install + on-TV test guide (no AI)
- [x] Discovery widened to Flatpak/Snap/local paths + Type/category filtering (hide Settings/System noise)
- [ ] On-hardware test pass on the real TV (evdev keyboard+mouse, kiosk launch, PWA install)
- [ ] Appliance autologin auto-detect (SDDM / LightDM) + enable-linger for the user service
- [ ] "TV navigation mode" toggle (re-enable arrows + OK for leanback apps that don't use a pointer)
- [ ] Develop the Settings sections (currently placeholders): share-control QR, app info, web link
- [ ] Smarter voice->app mapping (multi-word targets, not just {name}.com)
- [ ] Add backend/certs/ to .gitignore
- [ ] Tests (pytest) + on-hardware evdev injection test

# PH12: DISTRIBUTION
- [ ] Build a .deb (use fpm) with a postinst that runs the install.sh logic (venv, systemd, uinput, cert); declare deps (python3-venv, chromium, ufw, openssl)
- [ ] Install-from-web one-liner: host install.sh and run via `curl -fsSL <url> | bash`
- [ ] Landing page on Vercel (download .deb + install command + docs; LATER Stripe checkout)
- [ ] The phone client needs NO app store (PWA "add to home screen"); the .deb only installs the SERVER on the Linux HTPC
- [ ] Avoid Flatpak/Snap: their sandbox blocks uinput / systemd / launching browsers (bad fit for this app)

# PH13: CODE PROTECTION / ANTI-CLONE
- [ ] Make the GitHub repo PRIVATE; distribute the built artifact (.deb), not the source repo
- [ ] Replace LICENSE with a proprietary/commercial license (current one may be open/GPL — revisit before selling)
- [ ] Compile the Python backend (Nuitka -> binary, or PyInstaller) and ship the binary in the .deb instead of .py
- [ ] Minify/obfuscate frontend JS (deterrent only — PWA JS is always visible in the browser)
- [ ] NEVER ship API keys (NVIDIA/OpenRouter/Supabase service) in the client; route AI through a proxy server you control
- [ ] REAL protection is server-side: license activation against your server + AI/premium gated by license. Copying the client yields a useless shell without your cloud.
- [ ] Reality: client-side code can't be fully hidden; move the value (AI, premium, license) to your server.

# PH14: v1.6.0 — BUGS HTPC + BRAVE + HARDENING — ✅ RELEASED 2026-07-14
- [x] G-01..G-13 + correcciones C-01..C-10 + G-17/G-18 (auditadas por Claude)
- [x] G-14 Release v1.6.0 publicado y verificado en vivo (sha256 match, OTA operativo)
- [x] Smoke-test 7/7 funcional en HTPC limpio (Plasma Bigscreen)
- [ ] G-15/G-16 (siguen esperando info del dispositivo del dueño)

# PH14b: v1.7.0 — FIREFOX + FIXES — ✅ RELEASED 2026-07-14 (plan: .agents/archive/PLAN_GEMINI_v1.7.md)
- [x] F-01..F-06 + FC-01..FC-03 (auditadas por Claude, verificación independiente)
- [x] F-07 Release v1.7.0 publicado y verificado en vivo (sha256 4fff1722... match)

# PH14c: TESTING INTENSIVO v1.7.0 — ✅ EJECUTADO Y TRIADO 2026-07-17
- [x] Matriz A-J ejecutada por el dueño: 28 OK (seguridad 8/8, input, kiosk, panel ✓)
- [x] Claude triado con causa raíz: 1 bug crítico de installer (certutil colgado =
      A3+A6+D2+D4), layout 16:9, tooltip, favicons, icono iOS, UX nav-mode
- [x] G-15/G-16 por fin diagnosticados (iPhone 8 Plus iOS18 Safari + capturas)

# PH14d: v1.7.1 — CORRECCIONES DEL TESTING (plan: .agents/PLAN_GEMINI_v1.7.1.md)
- [ ] T-01 [CRÍTICO] certutil no-interactivo + policies.json antes del bloque NSS
- [ ] T-02 flujo final del install orientado a PIN + investigar ?token=
- [ ] T-03 bootstrap encadena lrp-setup | T-04 UFW OpenSSH fallback
- [ ] T-05 [ALTO] layout pantallas cortas 16:9 | T-06 tooltip tour | T-07 nav-mode UX
- [ ] T-08 latencia en HUD | T-09 favicons | T-10 apple-touch-icon 180x180
- [ ] T-11 (dueño) activar voz en HTPC (config, no bug)
- [ ] T-12 Release v1.7.1 -> prueba REAL del botón OTA (H3) -> luego J1/J2
- [ ] (dueño) deploy send-feedback; Stripe LIVE; dominio + Resend

# ROADMAP COMERCIAL (decidido con el dueño 2026-07-17)
# Monetización: UNA licencia Pro lifetime cubre TODO lo premium (voz, APK, archivos,
# skins pro). Sin tiers. Precio puede subir al acumular features; compradores previos
# conservan todo. Free tier (touchpad/teclado/kiosk) se mantiene genuinamente bueno.
# Orden: v1.8 fixes testing -> v1.9 ai-proxy+Stripe LIVE+dominio (LANZAMIENTO+rebrand)
#        -> v2.0 Skins 2.0 -> v2.1 APK premium -> v2.2 Archivos/disco virtual.
# REBRAND: "linuxremoteplayer" se queda como nombre técnico; nombre comercial se decide
# al comprar el dominio propio (un solo cambio de infra, no dos).

# PH14e: PRÓXIMO CICLO MENOR [v1.7.7+] (decisiones del dueño 2026-07-19)
- [ ] T-25 Detector de apps ABIERTO: quitar SKIP_CATEGORIES de discovery.py (el dueño
      quiere Dolphin y apps de sistema; conviven usuarios normales y power users).
      MANTENER los filtros NoDisplay/Hidden (esos son "oculto" por spec freedesktop).
      La excepción TerminalEmulator queda obsoleta al quitar el filtro.
- [ ] (+ lo que salga del retest de voz en v1.7.6)

# PH-WEB: REDISEÑO DE LA PÁGINA [va con v1.9/lanzamiento + rebrand] (anotado 2026-07-19)
- [ ] Actualizar TODA la información (versiones, Firefox, features reales)
- [ ] Matar el diseño "IA genérico" — identidad propia (coordinar con el rebrand/dominio)
- [ ] Tutoriales: instalación, actualización (botón OTA), reinstalación de la PWA
- [ ] Capturas de pantalla reales (pendientes desde siempre) + VIDEO de la app en acción
- [ ] Sección premium clara: voz IA, skins, APK (cuando exista) — qué incluye la
      licencia Pro única lifetime
- [ ] Precio actualizado: $5 USD
- [ ] Revisar: FAQ, requisitos (Debian/Ubuntu+systemd), enlace de soporte/feedback

# PH-LICENCIAS: ACTIVACIONES POR DISPOSITIVO [va DENTRO de v1.9/ai-proxy] (diseño 2026-07-19)
Estado actual VERIFICADO en código: la key NO se liga a hardware; activa dispositivos
ILIMITADOS; único freno compartido = cuota de 60 comandos de voz/día POR KEY.
DECISIÓN DEL DUEÑO [2026-07-19]: **1 DISPOSITIVO SIMULTÁNEO** con mudanza autoservicio.
Regla: la key funciona en UNA sola PC a la vez; se puede "mudar" cuando la anterior
queda inactiva. Mecánica (3 piezas — el formateo NO puede avisar al servidor, por eso
no basta la liberación explícita):
- [ ] Tabla activations: 1 fila por key (device_id, last_seen, activated_at).
      device_id = /etc/machine-id del HTPC.
- [ ] Claim en /api/license/activate (+ai-proxy): si sin dueño, mismo device_id, o
      last_seen >72h -> activa/renueva. Si activa en OTRO device -> respuesta
      "in_use_elsewhere".
- [ ] MUDANZA (takeover confirmado): ante "in_use_elsewhere" la app pregunta
      "¿Mudar la key aquí? El otro dispositivo perderá el premium" -> confirmar ->
      la nueva PC se la queda (formateo = mudanza instantánea, sin soporte).
      El dispositivo expulsado falla su próxima validación -> premium off.
- [ ] Liberación explícita: uninstall.sh llama /release best-effort (mudanza limpia
      en el caso desinstalar->reinstalar).
- [ ] Heartbeat: toda validación hace upsert de last_seen (red de seguridad).
- [ ] EDGE CASE aceptado: la PC expulsada conserva premium hasta agotar su cache de
      gracia offline (<=72h) — ventana breve de doble uso, tolerable; alinear la
      gracia con el lease si se quiere apretar.

ROBO/ROTACIÓN DE KEY (decidido 2026-07-19; ancla = correo de compra Stripe en licenses):
- [ ] v1 MANUAL (lanzamiento): ticket -> el dueño RESPONDE al correo REGISTRADO en la
      licencia (no al remitente) -> confirmación = acceso al buzón -> en Supabase:
      active=false a la vieja + key nueva enviada al mismo correo. El ladrón muere
      en <=72h (gracia). Documentar el procedimiento en GUIA_AGUSTIN.
- [ ] v2 AUTOSERVICIO (post-lanzamiento): página "Recuperar mi licencia" + Edge
      Function: busca por correo -> magic link firmado un-solo-uso (TTL 15min) vía
      Resend al correo registrado -> clic = rotación automática. SIEMPRE respuesta
      genérica (no confirmar si el correo es cliente) + rate limit 3/día por
      correo/IP.
- [ ] Fallback extremo (buzón perdido): prueba de compra contra Stripe dashboard
      (recibo / últimos 4 dígitos), manual.

# PH15: APK ANDROID **PREMIUM** [v2.1] (diseño: archive/PLAN_GEMINI_v1.6.md FASE E)
- [ ] Prerrequisito: ai-proxy Edge Function (claves fuera del dispositivo)
- [ ] Capacitor wrapper + NSD/mDNS + RECORD_AUDIO + volumen físico + foreground service
- [ ] WSS con TOFU pinning del CA obtenido en pairing (NO ws:// plano)
- [ ] Gate premium: el VALOR se gatea con licencia server-side (no el archivo .apk);
      enlace de descarga en Ajustes al activar Pro
- [ ] Share-sheet Android "Enviar a TV" (sinergia con PH16)

# PH16: ARCHIVOS / DISCO VIRTUAL **PREMIUM** [v2.2] (aprobado 2026-07-17)
Caso de uso del dueño: mandar multimedia desde PC de trabajo o teléfono al HTPC;
guardar fotos/videos del teléfono y verlos en la TV.
- [ ] Fase 1 — WebDAV embebido en el backend (wsgidav, puro Python): montable como
      unidad de red en Windows/macOS/iOS Files/Android. Reusa HTTPS+CA+gate licencia.
- [ ] Seguridad: UNA carpeta raíz configurable (~/LRP-Share o disco elegido en Ajustes),
      guards de path-traversal, symlinks fuera del root prohibidos, credenciales
      dedicadas (user/pass generados, visibles en panel TV), solo LAN, opción read-only
- [ ] Fase 2 — pestaña "Archivos" en la PWA: navegar, subir fotos/videos del teléfono,
      descargar, y botón "REPRODUCIR EN TV" (kiosk/mpv sobre el archivo local) — el
      diferenciador vs un NAS normal
- [ ] Marketing honesto: "comparte y reproduce en tu TV", NO "NAS"

# PH19: VOZ 2.0 — ASISTENTE AMPLIADO [v2.4] (consulta del dueño 2026-07-19)
DECISIÓN: NO app separada — misma app, motor de intents MODULAR en backend (registry
de acciones). Latencia NO es impedimento (voz=async+nube, aislada del input desde
C-01; validado 12ms con voz activa). Diferenciador de mercado real: nadie hace
"asistente LLM para HTPC Linux desde el teléfono".
- [ ] Fase 1 (robusta): intents de control local — apagar/suspender HTPC, timers
      ("apágate en 30min"), abrir apps nativas por voz, volumen a %, Home
- [ ] Fase 2 (robusta): keymaps por sitio vía uinput (YouTube k/f/n, Netflix s=skip
      intro...) — "pantalla completa", "siguiente episodio" SIN tocar el DOM
- [ ] Fase 3 (investigación): DOM control vía WebDriver BiDi (Firefox; CDP es de
      Chromium) — frágil tipo scraping, solo si fase 1+2 saben corto
- [ ] MONETIZACIÓN: premium única = voz básica + cap diario (seguro de costos);
      suscripción "Voz Pro" ($1.99-2.99/mes tentativo) = asistente ampliado + cuota
      mayor. Costo medido por comando ≈ $0.0002-0.0005 (Whisper+Qwen en Together).
      NÚMEROS FINALES: decidir con datos reales de uso del ai-proxy (v1.9) tras beta.
      La columna `plan` de licenses ya soporta tiers.
PRERREQUISITO ABSOLUTO: ai-proxy (v1.9). Orden en roadmap: tras Gamepad o intercambiable
según demanda comercial.

# PH-ANTIABUSO: PROTECCIONES DEL SERVICIO DE IA [OBLIGATORIO en v1.9/ai-proxy] (2026-07-19)
Auditoría de protecciones actuales: cuota 60/día por key ✓ (DB atómica); 10 req/min ✓
(memoria). AGUJEROS confirmados:
- [ ] Cap de TAMAÑO server-side real: hoy acepta 5MB/mensaje = ~40 MIN de audio Opus
      (los 8s son solo client-side, bypasseables) -> bajar a ~512KB (~60s) en el WS
      handler Y en el ai-proxy. Un blob de 5MB factura ~40x por request en Whisper.
- [ ] Llaves fuera del dispositivo = el ai-proxy mismo (sin él, cualquier comprador
      extrae las keys del .env y consume sin cuota).
- [ ] KILL-SWITCH de gasto global en el ai-proxy: si el gasto diario en Together
      supera $X -> voz off + alerta al dueño (seguro contra factura sorpresa).
- [ ] Cuota por PLAN (columna plan ya existe): lifetime=30-60/día; futura sub mayor.
- [ ] Métrica de uso por key/dispositivo en el proxy (base de datos de costos ->
      decide precios con datos).

# PH-PRICING: DECISIÓN DE MODELO [2026-07-19, consulta del dueño sobre sub-only $3/mes]
RECOMENDACIÓN REGISTRADA (Claude): NO sub-only al lanzamiento. Razones: audiencia
self-hoster anti-subs; solo la voz tiene costo recurrente (~$0.05-0.15/mes usuario
real, ~$0.90/mes el peor con cap 60/día — el CAP protege, no hace falta sub); subs =
carga operativa (dunning/cancelaciones) para fundador solo; $5 único = compra impulso
que construye base sin reputación previa.
PLAN SECUENCIADO: v1.9 lanza Pro único $5 lifetime (todo premium + voz con cap
diario). La SUSCRIPCIÓN nace con Voz 2.0 [v2.4] como "Voz Pro" ~$2.99/mes (asistente
ampliado + cuota mayor) — atada a la feature de costo recurrente, sin traicionar a
compradores previos. Números finales de cap/precio: con datos reales del proxy.
(Decisión final del dueño pendiente de ratificar en v1.9.)

# PH18: MODO GAMEPAD **PREMIUM** [v2.3] (propuesto 2026-07-17; latencia validada por el dueño)
Posicionamiento: "retro y multijugador casual instantáneo" — NUNCA "reemplaza tu mando BT".
Killer feature: multijugador — cada teléfono conectado = un mando (sin hardware extra).
- [ ] Backend: uinput con IDENTIDAD de gamepad real (EV_ABS + BTN_GAMEPAD) para que
      RetroArch/emuladores lo detecten como mando; base ya existe (BTN_A/B/X/Y/START/
      SELECT/DPAD en caps desde PH1)
- [ ] Backend: UN dispositivo virtual POR cliente WS (hoy gamepad/mouse son singletons
      globales — cambio mayor); mando 1..4 asignado por orden de conexión
- [ ] PWA fase 1: layout landscape multitouch (D-pad + ABXY + Start/Select + L/R),
      háptica al pulsar; SIN sticks analógicos en v1 (táctiles son mediocres)
- [ ] Se implementa como theme pack de PH17 (reusa infraestructura de layouts)
- [ ] APK fase 2: háptica/multitouch nativos + menor latencia -> argumento de venta
      extra del APK premium
- [ ] Gate: misma licencia Pro única

# PH17: THEME PACKS / SKINS 2.0 [v1.9.1] (4 propuestas del dueño, 2026-07-24)
Evolución: de paletas CSS a THEME PACKS = paleta + **layout de botonera** + **set de
botones** + wallpaper. Mockups guardados en `.agents/design/skins2/`:
`alt1-radial.webp`, `alt2-cyber-anime.webp`, `alt3-senior-gatos.webp`,
`alt4-senior-perros.webp`. (Las rutas originales eran temporales de Gemini; se
convirtieron a WebP: 2.6 MB → 335 KB.)

## POR QUÉ ESTO NO ES "UNA SKIN MÁS"
Tras T-58 una skin es SOLO custom properties: `data-skin` en `<html>` + variables de
color. Estas propuestas mueven tres ejes que las variables NO alcanzan:
1. **Posición** de los botones (radial vs filas).
2. **Qué botones existen** (senior recorta 7 de 17).
3. **Etiquetas de texto** ("SUBIR VOL."), que hoy no están en el DOM — los botones son
   solo icono + `title=`. Eso es marcado, no CSS.

Inventario real de controles hoy (`frontend/index.html`, para dimensionar):
- Fila utilitaria (`grid-cols-5`): Teclado, Borrar, **D-Pad** (`#btn-nav-mode`),
  Panel TV, Menú OS (`KEY_LEFTMETA`).
- `#control-cluster` en 3 columnas: [Home `killKiosk()`, Atrás, X `#btn-close-app`] ·
  [◀◀ `KEY_LEFT`, ▶‖ `KEY_SPACE`, ▶▶ `KEY_RIGHT`] · [Vol+, Vol−, Mute `#btn-mute`].
- Aparte: `#mic-row`/`#mic-btn`, `#apps-row` + `#more-btn`, touchpad + `#scroll-strip`,
  header (`#btn-settings`, título, `#status`, `#latency`).

## ARQUITECTURA: separar PALETA de LAYOUT (decisión de diseño clave)
Añadir un segundo atributo independiente: `data-layout="classic|radial|senior"` en
`<html>`, junto al `data-skin` que ya existe. Cada skin declara UN layout; el usuario
NO combina libremente. Por qué importa:
- alt3 y alt4 son **el mismo layout** con otra ilustración → 1 layout, 2 skins.
- alt1 y alt2 comparten la idea radial → 1 layout (ver crítica C1), 2 skins.
- Fijar skin→layout mantiene la matriz de QA en N (una por skin) en vez de
  layouts × skins. Sin esto el coste de test explota.
`setSkin()` pasa a aplicar los DOS atributos desde una tabla `SKIN_LAYOUT`.

## LAYOUT "radial" (alt 1 y 2) — el caro
- Técnica recomendada: **posicionado polar por transform**, NO SVG.
  `position:absolute; left:50%; top:50%; transform: rotate(θ) translateY(-R) rotate(-θ)`
  por botón. Conserva el marcado y TODOS los `onclick` existentes; el riesgo del radial
  está en re-cablear handlers, no en dibujar. Cuñas de arco reales (SVG `path` +
  `foreignObject`) solo si el dueño exige los segmentos exactos del mockup: obliga a
  rehacer áreas táctiles, foco e iconos, y tira a la basura `.util-btn`/`.ctrl-round`.
- **RIESGO PRINCIPAL — presupuesto vertical.** El cluster radial es mucho más alto que
  las 2 filas actuales. El touchpad es `flex-1 min-h-0`: absorbe el déficit y puede
  colapsar a cero en teléfonos chicos. Necesita `min-height` de piso en el touchpad +
  tope/escalado del disco. Probar con `--app-h` en el teléfono más chico soportado; no
  regresar el trabajo de "viewport iOS determinista" de v1.7.x.
- **Bloqueador de código a resolver ANTES:** `app.js` hace
  `micRow.style.display = showVoice ? 'flex' : 'none'`. Si el mic se mete al centro del
  disco, ese `style.display='flex'` inline rompe el layout. Convertir a toggle de clase
  primero (cambio behavior-neutral, va en el sub-paso de infra).
- alt2 reutiliza plomería que YA existe: `--bg-image` + `--panel-backdrop: blur()` es
  exactamente lo que hace la skin `anime` → el fondo ilustrado con panel translúcido
  sale casi gratis.
- Paleta amarillo/verde ácido de alt2: el amarillo exige `--accent-contrast` OSCURO
  (blanco sobre amarillo no pasa contraste). El sistema de T-58 ya lo soporta.

## LAYOUT "senior" (alt 3 y 4) — el barato y el de más valor
- Recorte de botones = `display:none` por CSS. **Cero cambios de JS.** Se ocultan 7:
  Borrar, D-Pad, Panel TV, Menú OS, X, ◀◀, ▶▶. Quedan 7 + mic: ▶‖, Vol+, Vol−, Mute,
  Inicio, Volver, Teclado.
- Botones grandes = CSS (objetivo ~64-72 px de alto; el mínimo iOS de 44 px ya se supera).
- **Etiquetas**: agregar `<span class="btn-label">` PERMANENTE a cada botón de control,
  visible solo en `senior` y `sr-only` en el resto. Beneficio extra: hoy los botones son
  icono + `title=`, que es débil para lectores de pantalla — esto arregla un hueco real
  de accesibilidad en TODAS las skins.
- El touchpad sin textura de puntos del mockup = `--touchpad-dot` casi transparente. Gratis.

## CRÍTICAS DE DISEÑO A RESOLVER ANTES DE CODIFICAR
- **C1 — alt1 y alt2 NO son el mismo layout.** alt1 = semiarco + fila utilitaria plana
  encima. alt2 = anillo doble completo. Recomiendo unificar en el **semiarco de alt1**:
  el anillo completo pone la mitad de los botones ARRIBA del cluster, más lejos del pulgar
  que una fila plana, o sea contradice el objetivo ergonómico declarado; y desperdicia el
  interior del anillo. Si el dueño quiere las dos, son 2 layouts y 2 veces el QA.
- **C2 — en senior, quitar el D-Pad va probablemente al revés.** `toggleNavMode()` +
  `#nav-overlay` dan navegación por flechas. Para alguien que no controla bien un puntero,
  un D-Pad es MÁS fácil que un cursor libre: los mockups conservan el touchpad de puntero
  y eliminan justo la ayuda. Propuesta: en `senior`, modo navegación ENCENDIDO por
  defecto, y si hay que sacrificar algo, sacrificar el puntero libre, no el D-Pad.
- **C3 — "INICIO" es peligroso tal cual.** El botón Home es `killKiosk()`, titulado
  "Home (cierra app)": MATA la app en curso. Etiquetarlo "INICIO" para una persona mayor
  invita a cerrar la película sin querer. Hay que relabelarlo ("Cerrar app"), o remapear
  el Home de senior a algo no destructivo, o pedir confirmación.
- **C4 — vía de escape.** El mockup de gatos no muestra el engranaje de Ajustes. Si se
  oculta, el usuario NO puede volver a Ajustes para salir del modo senior: queda atrapado.
  El acceso a Ajustes tiene que seguir alcanzable (engranaje visible o long-press).
- **C5 — legal, "Edgerunners".** Es marca de CD Projekt / Trigger y el personaje del
  mockup se lee como Lucy. No se puede publicar con ese nombre ni con arte parecido en un
  producto DE PAGO. Renombrar (p. ej. "Neon") y usar ilustración original o licenciada.
- **C6 — gating.** Las skins senior son un modo de ACCESIBILIDAD. Cobrarlas como Pro se
  ve mal y probablemente vende peor: son justo el relato de "que la tele la use toda la
  familia" que ya vende el sitio. Recomiendo senior GRATIS; radial/cyber sí Pro.
  **Decisión del dueño.**

## PRESUPUESTO DE ASSETS (el .deb hoy pesa 281 KB; `anime-bg.webp` solo, 172 KB)
- Gatos y perros son **patrones sin costura** → NO mandar un pantallazo full-screen:
  mandar el **TILE** (p. ej. 400×400) y repetirlo. El sistema de skins ya tiene
  `--bg-repeat`, `--bg-size` y `--bg-position`, así que tilear no cuesta código. Un tile
  así ronda ~30 KB en vez de ~170 KB.
- La ilustración cyberpunk NO es tileable (personaje único a sangre) → sí necesita el
  archivo grande. Techo sugerido: ≤120 KB en WebP.
- alt1 no lleva imagen de fondo → 0 KB.
- Objetivo total: .deb ≤ 600 KB. Si se pasa, la alternativa es servir los wallpapers
  desde la web y cachearlos en el SW al elegir la skin (mantiene el .deb magro, pero mete
  dependencia de red en un cambio de tema).
- **Todo asset nuevo va agregado a `ASSETS` en `frontend/sw.js`** o la skin no funciona
  offline y el OTA no la precachea.

## TROCEADO SUGERIDO (no meter todo en una tarea)
- **v1.9.1a — infra, sin cambio visible:** `data-layout` + tabla `SKIN_LAYOUT` en
  `setSkin()`, `<span class="btn-label">` en todos los controles (ocultas), `#mic-row`
  a toggle de clase. Behavior-neutral y auditable por separado.
- **v1.9.1b — layout `senior` + skins gatos y perros.** Barato, riesgo bajo, abre un
  mercado nuevo. Resolver C2/C3/C4/C6 antes.
- **v1.9.2 — layout `radial` + skin neon/cyber.** Es un motor de layout con el riesgo
  del presupuesto vertical; no debe compartir release con senior.

## VERIFICACIÓN OBLIGATORIA POR SKIN NUEVA
- `scripts/check_css_sync.py` (toda clase nueva definida) + `node --check`.
- Auditoría de contraste con el arnés de T-58 (recorre el texto visible y marca <3.0:1)
  para CADA combinación skin+layout. Pastel sobre crema y amarillo sobre oscuro son los
  casos peligrosos.
- Filas nuevas en `TESTING.md` por layout (el touchpad y el D-Pad cambian de tamaño y
  posición: hay que re-probar arrastre, scroll y long-press del botón X donde exista).

## PENDIENTE DEL DUEÑO
- [ ] Wallpapers definitivos: alt2 ilustración a sangre; alt3/alt4 **el tile**, no el
      pantallazo; alt1 sin fondo.
- [ ] Decidir C1 (¿semiarco, anillo, o los dos?), C6 (gating de senior) y el nombre de alt2.
- [ ] Wins baratos que sobreviven del PH17 viejo: wallpaper propio del usuario
      (IndexedDB, cero servidor) y reordenar webapps por drag & drop (localStorage).

## NOTES / MANUAL ACTIONS
- HTTPS is automatic: run.py self-generates and self-heals the cert. The only manual
  step is each phone accepting the self-signed cert once (browser warning -> proceed).
  To remove that warning entirely you need a trusted cert (PH-future, Plex-style).
- Set PAIRING_TOKEN in backend/.env, else control endpoints are open in dev mode.
- Create the 'licenses' table in Supabase (backend/supabase_schema.sql) + set SUPABASE_URL/KEY.
- Verify the real NVIDIA NIM ASR model id (NVIDIA_ASR_MODEL); current default is unverified.
- Owner deferred Supabase + Stripe + AI; current focus is on-TV testing of the control without AI.
- Distribution model: PWA client (no store) + a SERVER package (.deb) for the Linux HTPC. See PH12.
- Anti-clone: legal (private repo + proprietary license) + compiled backend + server-side license/AI proxy. See PH13.
