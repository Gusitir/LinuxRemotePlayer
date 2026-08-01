# LinuxRemotePlayer — Development Plan
<!-- Archivo GRANDE (43 KB al 2026-07-30). NO leerlo entero: usá el indice y saltá con `grep -n "^# PH17"`.
     Estado vivo -> CURRENT.md. Ciclo de pruebas vivo -> TESTING.md. -->

## INDICE (fase · estado · dónde)

| Fase | Qué es | Estado |
|---|---|---|
| PH1..PH9 | scaffold, kiosk, IA cloud, installer, seguridad, HTTPS+PWA, rediseño UI, licencias backend | ✅ DONE — **saltar** |
| PH10 | monetización (Stripe) | ⚠️ obsoleta: se migró a **Paddle**, ver CURRENT §D1 |
| PH11 | polish | parcial / vigente |
| PH12 | distribución (.deb, install.sh, landing) | ✅ DONE — **saltar** |
| PH13 | anti-clon | ✅ lo esencial hecho: repo PRIVADO (T-57) + Elastic 2.0 + ai-proxy |
| PH14..PH14e | ciclos v1.6/v1.7 y su testing | ✅ DONE — **saltar** |
| PH-WEB | rediseño del sitio | ✅ hecho en T-53 (v1.9) |
| PH-LICENCIAS | activación por dispositivo | ✅ hecho en T-46..T-49 |
| PH-ANTIABUSO | cap 512KB, kill-switch, cuota | ✅ hecho en T-46..T-48 |
| PH-PRICING | modelo de precio | decidido, ver CURRENT §D3 |
| **PH17** | **Theme Packs / Skins 2.0** | **v2.0 · un PREVIEW PRO sale en v1.9.3** |
| **PH20** | **Demo interactiva en la web** | **v1.9.2 — reemplaza al video, cancelado** |
| PH19 | Voz 2.0 (asistente ampliado) | v2.0 — diseñada |
| PH15 | APK Android | v2.1 |
| PH16 | Archivos / disco virtual | v2.2 |
| PH18 | Modo gamepad | v2.3 |
| MERCADO | proyectos vecinos (LinuxPlay) + colision de nombre | contexto, decision en CURRENT §D7 |
| **PH0** | **superficie de verificacion (un comando = todos los gates)** | **✅ ADOPTADA 31/07** |

Orden comercial vigente (31/07): **v1.9.1 LANZADA → alta en Paddle → v1.9.2 (firma del OTA
§OTA-FIRMA + paddle-webhook + correcciones; ES LA QUE HABILITA COBRAR) → v1.9.3 skin PREVIEW
PRO → v2.0 skins Pro + accesibilidad + multi-distro + Voz 2.0 → v2.1 APK → v2.2 archivos**.
PH20 depende de PH17 (ver PH20 §DEPENDENCIA): si la demo sale primero, hereda la deuda.

## ✅ FASES COMPLETADAS — archivadas

PH1..PH8.8 (scaffold, kiosk, IA cloud, installer, auditoria de seguridad, HTTPS+PWA,
rediseño de la UI, remediacion) se entregaron antes de la v1.8 y viven en
**`archive/PLAN_COMPLETED_PH1-PH8.md`**. No hace falta leerlas para trabajar hoy.

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

# PH12: DISTRIBUTION — ✅ DONE (entregada en v1.8/v1.9; se deja el porque, no el checklist)
<!-- El .deb, el one-liner `curl | sudo bash` desde el dominio propio y la landing en Vercel
     estan vivos y auditados. Vigente de esta fase: NO empaquetar en Flatpak/Snap — su
     sandbox bloquea uinput/systemd/lanzar navegadores, que es exactamente lo que hace LRP. -->

# PH13: CODE PROTECTION / ANTI-CLONE — ✅ lo esencial HECHO (2026-07-30)
<!-- Repo PRIVADO (T-57), LICENSE = Elastic 2.0, y la voz pasa por ai-proxy: el device no
     tiene llaves. Compilar el backend y ofuscar el JS siguen SIN hacer y son deterrentes,
     no proteccion. La proteccion real es server-side y ya esta: copiar el cliente da una
     cascara inutil sin la nube. -->

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

# PH14d: v1.7.1 — ✅ CERRADA (los T-01..T-12 se entregaron en el ciclo v1.7.1..v1.7.7)
<!-- Los checkboxes de abajo quedaron sin marcar y son RUIDO: el estado real de ese ciclo
     esta en CONTEXT (2026-07-17..20) y en git. Detalle: archive/PLAN_GEMINI_v1.7.1.md. -->

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

# PH19: VOZ 2.0 — ASISTENTE AMPLIADO [v2.0] (consulta del dueño 2026-07-19;
#       REPRIORIZADA a v2.0 por el dueño 2026-07-24, junto con el paquete de skins Pro)
## Objetivo concreto que puso el dueño: que "pon video de gatos" REPRODUZCA
Hoy ese comando termina en la página de RESULTADOS de búsqueda y el usuario tiene que
elegir a mano. La meta de v2.0 es que arranque el primer resultado solo.
**El "equivalente a las DevTools" que preguntaba el dueño es `WebDriver BiDi`**, servido
por el Remote Agent de Firefox (`--remote-debugging-port`); el protocolo viejo
equivalente es `Marionette`. CDP es de Chromium y NO aplica: el kiosk es Firefox.
Ya estaba anotado abajo como Fase 3 — se mantiene el orden 1→2→3 por dos razones:
- **Fase 2 (keymaps) resuelve gran parte sin DOM.** En YouTube, `/` enfoca la búsqueda
  y una secuencia de teclas reproduce el primer resultado: eso es uinput, que ya
  funciona, cero dependencias nuevas, y no se rompe cuando el sitio cambia el HTML.
- **SEGURIDAD (evaluar antes de la Fase 3):** abrir un puerto de depuración en el
  Firefox del HTPC deja que CUALQUIER proceso local maneje el navegador con la sesión
  del usuario (sesiones de Netflix, correo, lo que haya). El proyecto hoy cuida esto
  (token, HTTPS, llaves fuera del device). Si se activa: bind SOLO a 127.0.0.1, y
  encenderlo/apagarlo por comando en vez de dejarlo abierto siempre.

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

# T-79: B1 — sacar `viewport-fit=cover` ✅ HECHO Y AUDITADO APTO (2026-07-30, `5371086`)

<!-- Cerrado en codigo. B1 NO se cierra hasta que 1.9.1 este publicada y §L2 se repita sobre
     el .deb: lo probado en campo fue un equipo parcheado a mano. Estado vivo: CURRENT §B1.
     Auditoria: diff de 8+/1-, archivo integro (71514->72060 bytes, cierra en </html>, el
     mount /mnt no lo trunco), meta byte a byte identico menos el atributo, los 5 usos de
     safe-area intactos, y ninguna otra referencia a viewport-fit en el repo. -->


Un solo atributo en `frontend/index.html:6`. **La causa y el arreglo ya estan validados en
campo** (iPhone 8+ y 12, TESTING §L2) — lo que falta es embarcarlo: se probo sobre el HTPC
parcheado a mano y nunca entro al repo.

**Alcance CONFIRMADO con `dpkg -V linuxremoteplayer` (30/07), no de memoria.** Salieron DOS
archivos alterados en el HTPC: `frontend/index.html` **y `frontend/sw.js`**. El segundo **NO
entra en T-79**: era el cache-bust necesario para que el iPhone dejara de recibir el
`index.html` cacheado y la prueba midiera algo. `sw.js:1` es `const CACHE = 'lrp-__LRP_VERSION__'`
y `build_deb.sh:52` lo sustituye al construir (`:53` aborta si queda sin versionar), asi que
**el bump a 1.9.1 lo regenera solo**. Replicarlo a mano seria un error.

Linea final verificada en el equipo donde funciono:
`<meta name="viewport" content="width=device-width, initial-scale=1.0, minimum-scale=1.0, maximum-scale=1.0, user-scalable=no">`

**Radio de impacto auditado el 30/07** — sin `cover`, `env(safe-area-inset-*)` pasa a 0.
Los cinco usos degradan limpio, por eso el cambio es de bajo riesgo:
- `index.html:23` `body padding: env(R/B/L)` → 0. Correcto: sin `cover` iOS ya insetea el
  viewport, y sumar padding encima es JUSTO lo que duplicaba el inset.
- `index.html:24` y `:26` `.app-header padding-top: max(env(top), 8px|20px)` → cae al `max()`.
- `index.html:38` `.drawer` (`fixed; inset:0`) → 0, ya queda dentro del area segura.
- `index.html:162` `calc(1rem + env(bottom))` → `1rem`.

Va en **1.9.1 junto con T-78**. Al cerrar: **repetir §L2 sobre el `.deb`**, no sobre el HTPC.
Efecto colateral conocido y aceptado: **H21** (el `theme-color` no refresca en vivo en iOS 16+).

# T-57: PRIVATIZAR EL REPO — YA SE APRETO EL BOTON (2026-07-30)
<!-- Estado vivo y decision: CURRENT §C7. Aca esta el detalle operativo. -->

> **EL REPO YA ES PRIVADO** (el dueño lo privatizo el 2026-07-30, ANTES de correr estos
> chequeos). Lo de abajo dejo de ser "que verificar antes" y paso a ser **deuda a verificar
> AHORA**. Comprobado el mismo dia: `git ls-remote origin` responde desde el clon Windows,
> asi que las credenciales locales (Git Credential Manager) siguen sirviendo.

Verificado 2026-07-29. **El OTA NO se rompe**: `latest.json` y el `.deb` se sirven de Vercel,
no de GitHub. Pero hay tres cosas que si:
1. **Vercel — ✅ CERRADO 30/07.** Deployo sin problema con el repo ya privado; el canal OTA
   no se congelo. (Cualquier push sirve de prueba: `website/vercel.json` es solo `cleanUrls`,
   sin Ignored Build Step, asi que todo push dispara build.)
2. **El clon WSL del release — ✅ CERRADO 30/07.** Era una TRAMPA y por eso vale como leccion:
   el helper existia **solo en el config LOCAL de `~/lrp-release`**, con el global vacio. El
   clon viejo funcionaba y daba falsa sensacion de resuelto, mientras que **§PROCESO paso 2
   manda clon FRESCO, que nace sin config y falla** con
   `fatal: could not read Username for 'https://github.com'` — y en interactivo se cuelga
   esperando una contraseña que GitHub ya no acepta, en medio de un release.
   **Aplicado:** en WSL, `git config --global credential.helper` apuntando al
   `git-credential-manager.exe` de Windows (reusa el GCM; no guarda secretos nuevos).
   **Verificado reproduciendo el paso 2**, no leyendo: `git clone --depth 1` fresco entro sin
   pedir nada. *Leccion: un config local que funciona puede tapar un global que no existe.*
3. **`scripts/bootstrap.sh` — ✅ BORRADO en T-80** (junto con su mencion en el README y la
   variable muerta `GITHUB_REPO`). Clonaba desde GitHub, asi que al privatizar quedaba en 404.
   *Dato que aparecio al auditarlo:* **se venia empaquetando en el `.deb`** — `build_deb.sh`
   copia `scripts/` entera y su lista de exclusiones nunca lo incluyo —, o sea que vivia en
   `/opt/linuxremoteplayer/scripts/` de cada usuario. `dpkg` lo borra al actualizar a 1.9.1.
- **4. El push del dueño YA RIGE, y el reparto quedo distinto al previsto aca.** Lo que se
  planeaba —Gemini commitea local y el auditor audita ESE commit— **no es lo que se
  decidio**: Gemini no commitea nada y entrega arbol sucio. **El contrato vigente esta en
  AGENTS.md §ROLES y §CICLO; no lo repitas aca.**

# OTA-FIRMA: cerrar B19 (analisis 2026-07-31; estado vivo en CURRENT §B19)

**El problema en una frase:** el sha256 y el `.deb` vienen del MISMO origen. Verificar uno
contra el otro solo prueba que la descarga no se corrompio en transito; si alguien controla
que sirve el dominio, controla los dos. Quien tome la cuenta de Vercel, la del registrador o
el DNS, ejecuta **root** en la maquina de cada cliente.

*Calibracion:* **no hay timer ni cron** (verificado). Hace falta que el usuario toque
"Actualizar" — pero la app le avisa que hay version nueva, asi que lo va a tocar. No es
"toda la flota al instante"; es "todos los que actualicen despues del compromiso".

## Capa 0 — hoy, sin codigo
2FA en Vercel Y en el registrador · bloqueo de transferencia + renovacion automatica del
dominio · borrar tokens de despliegue sin usar. No arregla el diseño; baja la probabilidad a
casi cero mientras llega el arreglo.

## Capa 1 — v1.9.2: firma separada sobre `latest.json`
La propiedad que hace falta es UNA: **la clave privada nunca toca Vercel ni el repo.** Vive
offline. Asi, comprometer el hosting deja de alcanzar para falsificar una version.
1. Par **ed25519** generado una vez. La publica se empaqueta en el `.deb`; la privada se queda
   en la maquina del dueño.
2. En cada release se firma `latest.json` offline y se publica `latest.json.sig` al lado.
3. `lrp-update` **verifica la firma ANTES de descargar nada**. Si no valida, aborta.

Se usa `openssl` porque **ya es dependencia** del instalador (certificados); `minisign` es mas
limpio pero suma un binario en la maquina del cliente.
**CAVEAT:** los flags de firma raw ed25519 cambiaron entre OpenSSL 1.1.1 (Debian 11) y 3.x
(Debian 12+). **Probar en la distro objetivo antes de embarcar** — es justo la clase de
comando que "parece bien" y falla en silencio.
**RIESGO QUE INTRODUCE, aceptado a ojos abiertos:** si se pierde la clave privada, **no se
pueden volver a publicar actualizaciones** para el parque instalado; recuperarse exige que
cada usuario instale a mano un `.deb` con la clave nueva. Copia offline en DOS lugares, y
ninguno es el repo ni el proveedor de nube.

## Capa 2 — el destino: repositorio APT firmado
La respuesta canonica de Debian: publicar un repo APT con su `Release` firmado con GPG. `apt`
hace toda la verificacion con maquinaria probada y **no se escribe una linea de cripto
propia**; el usuario actualiza con `apt upgrade`. Un repo APT son **archivos estaticos**, asi
que Vercel puede servirlo igual que hoy. Costo: reestructurar la publicacion (`aptly` o
`reprepro`) y cambiar el flujo del OTA. **Cuando haya volumen, no antes.**

## Endurecimientos baratos que van con la capa 1
- **Angostar el sudoers:** hoy es `%input ALL=(root) NOPASSWD`, o sea CUALQUIER miembro del
  grupo `input`. Debe ser el usuario del servicio.
- **`mktemp -d`** en vez de `/tmp/linuxremoteplayer_<ver>_all.deb`: el nombre predecible en
  directorio compartido habilita la ventana TOCTOU entre `sha256sum -c` y `apt-get install`.
  (`systemd-run --collect` **no** activa `PrivateTmp` por defecto.)
- **Verificar el nombre del paquete** en los campos de control antes de instalar, para que un
  `.deb` legitimo pero DISTINTO no se cuele.

# CORREO: sacar `support@` de spam (analisis 2026-07-31; estado vivo en CURRENT §C9)

**Antes de diagnosticar, repetir la prueba.** La que detecto el problema tenia asunto `test`
y cuerpo `test`: eso **es** un patron de spam y lo marcan filtros mucho mas laxos que Gmail.
Puede estar menos roto de lo que parece. Reprobar con un correo realista (asunto tipo "Tu
clave de LinuxRemotePlayer", saludo, clave, enlace al dominio propio, firma).

Lo que Gmail pesa, en orden:
1. **Autenticacion.** SPF y DKIM ya estan. **Lo que probablemente falta es DMARC** — desde
   2024 Gmail lo exige en serio. Un `_dmarc` con `p=none` ya mejora y ademas manda reportes.
2. **Alineacion.** El `From:` visible tiene que coincidir con el dominio que firma DKIM. Si
   el proveedor firma con el suyo y se muestra `@linuxremoteplayer.com`, no alinea.
3. **Reputacion.** El dominio es nuevo, sin historial. Se gana con volumen bajo y constante y
   con interaccion positiva: que abran, respondan y marquen "No es spam".
4. **Contenido.** Texto + HTML, pocos enlaces, sin acortadores, sin mayusculas gritadas.

Herramienta: **mail-tester.com** da puntaje y dice exactamente que falta.

**Descartado por el dueño (D15): subdominios.** La recomendacion tecnica habitual es mandar
lo transaccional desde un subdominio para aislar la reputacion del correo humano. No hay
acceso ni interes. **Alternativa si algun dia hace falta aislar: otra cuenta de correo.**

**Lo ya hecho:** `gracias.html` avisa de revisar spam y de marcar "No es spam" (T-83). Es
mitigacion honesta, no arreglo: un porcentaje real de compradores no va a buscar en spam.

# PH0: SUPERFICIE DE VERIFICACION — ✅ ADOPTADA 2026-07-31

**Cuatro capas, de barata a cara.** El orden importa: lo que fallo de verdad (el actualizador
que se reescribia a si mismo, un archivo truncado por `/mnt`, un 6/6 falso sobre un equipo
parcheado, la web anunciando 1.8.0) **no lo hubiera cazado ninguna VM**. Son errores baratos
de detectar y carisimos de sufrir.

1. **Gates (horas).** `scripts/verify.sh`: `py_compile`, `node --check`, `bash -n`, el guard
   de CSS **+ asserts propios**: `sw.js` versionado, `latest.json` == `VERSION`, que no
   reaparezca `viewport-fit=cover`, que no quede ningun `PLACEHOLDER` en un build de release.
2. **Unitarios de logica pura (un dia).** `is_newer_version` es el caso testigo: compara
   tuplas, no soporta sufijos, y **decide si cada cliente recibe cada actualizacion**. Se
   prueba en cinco lineas. Idem cuota y licencia.
3. **Smoke del paquete en contenedor (un dia).** Docker/Debian: instalar el `.deb`, verificar
   que el postinst corre, que el servicio queda instalado y que los archivos estan. Caza
   regresiones de empaquetado en segundos, sin VM.
4. **Laboratorio de VMs (idea del dueño).** Lo unico que prueba systemd real, `uinput`,
   sesion grafica y Plasma. **Ahi vive la cobertura multi-distro: construirlo cuando arranque
   esa pista (v2.0), no antes.**

**Rama + CI.** Dejar de trabajar directo sobre `main`: rama de desarrollo, PR, y CI corriendo
las capas 1 y 2 en cada push. Elimina el modo de falla "alguien tenia que acordarse".
*Verificar el cupo de minutos vigente para repos privados antes de dimensionarlo.*

## Lo que decia la propuesta original (2026-07-28)

Viene de revisar la skill `agents-workflow` (repo aparte). **Nada de esto se implemento**;
queda registrado para que la evaluacion no se pierda con el chat.

## El hueco real que tenemos
Los gates de LRP estan DESPERDIGADOS: `check_css_sync.py` corre dentro de `build_deb.sh`, y
`py_compile` / `node --check` / `bash -n` los escribe **a mano el auditor en cada brief**.
Esa redaccion manual ya produjo un check equivocado (un `grep "set -e"` que matcheaba el
comentario del propio archivo y habria reprobado codigo correcto). **Un archivo versionado
elimina esa clase entera de error**: se corrige una vez y sirve para siempre.

## Que seria
- [ ] `scripts/verify.sh`: UN comando que corre todos los gates y **sale distinto de cero**
      si algo falla. Dia uno puede ser solo los chequeos de sintaxis que ya usamos.
- [ ] Registrar en AGENTS.md **que cubre y que NO cubre**. Lo que no cubre es exactamente lo
      que justifica TESTING.md — no es un hueco a esconder.
- [ ] Cada incidente nuevo que revele una clase de bug agrega un gate (el ciclo de las war
      stories, automatizado).

## Adoptar tambien, cuesta cero
- **Las 5 preguntas del dueño** (no requieren leer codigo): "pega la salida del comando",
  "que archivos toco el commit", "que NO verificaste", "cambio de significado algo fuera del
  codigo", "que pasa con quien ya instalo la version anterior".
- **Checklist de integridad de release** → va al hito **T-56**. Sus 8 items son, uno por uno,
  agujeros que ESTE proyecto ya tuvo: direcciones de soporte muertas, doc prometiendo lo que
  el script no hace, un build publicado roto mientras las maquinas de dev funcionan, renames
  que no llegaron al marketing, instalaciones existentes huerfanas por un cambio de dominio,
  capturas de tres releases atras.

## NO adoptar ahora: la ejecucion delegada (auditor invocando al ejecutor por CLI)
Suena a la solucion obvia —el dueño es hoy el transporte entre Gemini y Claude— pero:
1. Exige la superficie de verificacion como **precondicion dura**: un auditor sin humano solo
   puede aprobar lo que puede chequear, y hoy no existe ese comando.
2. **Multiplica las entregas sin multiplicar la matriz de test**, que sigue siendo una persona
   con hardware real. Ese es el cuello de botella REAL de LRP hoy: T-60..T-66 auditadas y
   TESTING sin correr. Delegar aceleraria justo lo que ya no damos abasto para verificar.
Revisar recien cuando PH0 exista y la matriz este al dia.

# MERCADO: PROYECTOS VECINOS (revisado 2026-07-26) — decision viva en CURRENT §D7

## Techlm77/LinuxPlay — GPL-2.0, 622 estrellas, 12 forks, ultimo push 2025-11-10
**No es competencia: es otra categoria de producto.** Capturan la pantalla del host con
FFmpeg, la codifican H.264/H.265 y la mandan por UDP a un cliente Qt en OTRA PC — familia
Moonlight/Sunshine/Parsec. Resuelven "quiero ver y usar mi PC Linux desde otra computadora".
LRP no transmite video: el HTPC ya esta enchufado a la TV, la TV ES la pantalla y el
telefono es el mando. Resolvemos "estoy en el sillon y necesito un control remoto".
Se tocan en un solo punto: ambos inyectan input en un host Linux y hacen handshake por PIN.

**Lectura de traccion:** 622 estrellas con 12 forks (2%), 10 watchers y 1 issue abierto es
el patron "le di estrella, nunca lo instale". Dormido hace 8 meses, un solo mantenedor, y el
propio README dice que no es un producto pulido. Conclusion: hay demanda de herramientas de
control remoto en Linux, y nadie ocupo el nicho del sillon. Eso juega a favor.

**Riesgo real #1 — licencia.** GPL-2.0 contra nuestro Elastic 2.0 comercial. La regla dura
y el POR QUE (codigo mayoritariamente escrito por IA = imposible probar no-derivacion
despues) viven en **AGENTS.md §CÓDIGO DE TERCEROS**. Su codigo no se lee ni se pega en el
contexto de ningun agente que toque LRP.

**Riesgo real #2 — colision de nombre.** "LinuxPlay" vs "LinuxRemotePlayer". Su repo es de
feb-2025 con SEO acumulado; el nuestro **ya es privado** (T-57) y arranca de cero. NO se
rebrandea (D2 cerrado, dominio ya comprado, reabrirlo cuesta mas de lo que rinde). Se
mitiga: apoyarse en el dominio propio y en "LRP", y que la web hable del problema del
sillon/HTPC y no de "remote player" generico — ahi no competimos por la misma busqueda.

**Diferenciador factual usable en la web:** su README avisa que NO cifra el trafico de media
ni de control, y manda a tunelizar por WireGuard/OpenVPN/SSH en redes no confiables. LRP
hace HTTPS con CA propia y pairing por PIN desde el minuto uno. Decirlo SIN nombrarlos:
comparar de frente con un proyecto ajeno es ruido legal que no compra nada.

**Lo unico aprovechable de su diseño** (del README, no del codigo): usan UDP y no TCP para
input y gamepad. Dato a tener en cuenta al medir latencia en PH18.

# PH20: DEMO INTERACTIVA EN LA WEB ("live test") [v1.9.1] (pedido del dueño 2026-07-26)
Un minijuego en el sitio: el visitante usa un control remoto SIMULADO y ve, al lado, una
"pantalla de TV" que reacciona al comando. Objetivo comercial: que se entienda el producto
sin instalar nada. Corre con las 4 skins actuales (day/night/cafe/anime).

## POR QUÉ ES MÁS CARO DE LO QUE PARECE
Es una SEGUNDA implementación de la botonera. El día que PH17 cambie layouts o renombre
`anime`→`Cozy`, la demo queda mintiendo y NADIE se va a acordar de tocarla — el sitio y la
app viven en carpetas distintas y no comparten build. Ese es el riesgo real, no el juego.

## DECISIÓN DE ARQUITECTURA A TOMAR ANTES DE CODIFICAR (bloquea el troceado)
- **Opción A — reusar los assets reales.** La demo importa `frontend/skins.css` (copiado a
  `website/` por un script) y reusa el marcado real de la botonera. Un guard tipo
  `scripts/check_css_sync.py` aborta si la copia divergió del original. Caro de montar,
  barato de mantener, y la demo nunca miente.
- **Opción B — maqueta a mano.** HTML/CSS propios del sitio, sin relación con la app.
  Rápido ahora, deriva garantizada después.
- Recomendación: **A**. El precedente ya existe (el guard CSS cazó deriva real en T-29) y
  PH17 va a mover justo estas piezas.
- La lista de skins de la demo se DERIVA de una sola fuente (misma const que `SKINS` en
  app.js), nunca se escribe dos veces. Si no, PH17 la rompe en silencio.

## ALCANCE FUNCIONAL v1 (sin backend; todo client-side, cero red)
- [ ] Touchpad: arrastrar mueve un cursor en la "TV". Tap = clic.
- [ ] D-pad + OK: navega una grilla falsa de apps (Netflix/YouTube/Spotify ficticios).
- [ ] Teclas de media: play/pausa/siguiente cambian el estado visible de la TV.
- [ ] Lanzar kiosko: elegir una app "abre" una pantalla falsa dentro de la TV.
- [ ] Selector de skin visible: las 4 skins aplicadas EN VIVO (es el argumento visual).
- [ ] Objetivo de juego (lo que lo vuelve "minijuego"): una tarea corta y guiada
      —"poné a reproducir el video"— con un tick al completarla. Sin puntaje ni timer:
      la meta es que entienda el producto, no que juegue 10 minutos.

## REGLAS NO NEGOCIABLES
- **Etiquetarla como SIMULACIÓN, visible, no en letra chica.** Un visitante (o un revisor
  de Paddle) tiene que entender que no está controlando una máquina real. Una demo que
  parece real y no lo es, es publicidad engañosa y es exactamente lo que hunde una cuenta
  de pagos.
- **NO simular la voz como si funcionara.** La voz real necesita el ai-proxy y cuesta
  dinero por request. Si se muestra voz, va con guion enlatado y cartel de "ejemplo
  grabado". Alternativa preferida: para la voz, un video (ya pendiente en T-53).
- **Sin red.** Cero llamadas a la API real desde el sitio público: sería un endpoint
  abierto y gratis para cualquiera.
- **Móvil primero, pero el desktop no puede quedar roto.** Un tercio de las visitas de un
  producto de PC llegan desde una PC: el touchpad necesita fallback de mouse (mousedown/
  mousemove), no solo eventos touch.
- Presupuesto: la demo NO puede engordar el `.deb`. Vive SOLO en `website/`, nunca en
  `frontend/` (que sí se empaqueta). Ver PH17 §PRESUPUESTO DE ASSETS.

## TROCEADO SUGERIDO
1. Decidir A vs B + montar la fuente única de skins y el guard (si es A).
2. Maqueta estática: control + TV + selector de skins, sin lógica.
3. Lógica de interacción (touchpad, d-pad, media) + estados de la TV.
4. La tarea guiada + el tick + los textos ES/EN.
5. Instrumentar: cuántos la usan y cuántos de esos van a comprar (si no se mide, no se
   sabe si valió la pena).

## DEPENDENCIA CON PH17
Si PH17 sale primero, la demo nace ya con los layouts nuevos y se ahorra una reescritura.
Si sale la demo primero, PH17 hereda la deuda de actualizarla. **Recomendación: PH17 antes
que PH20**, o los dos en la misma tanda con la Opción A de arriba.

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
- **C6 — gating. RESUELTA (dueño, 2026-07-24): TODAS estas skins van GRATIS.** Son el
  gancho; el Pro se vende con MÁS skins más adelante (v2.0). Ver roster abajo.

## DECISIONES DEL DUEÑO (2026-07-24) — todas las críticas aceptadas
Roster final de skins, **las 7 gratuitas**:
| skin | layout | etiqueta | notas |
|---|---|---|---|
| **Day** | classic | — | por defecto (ya existe, T-58) |
| **Night** | classic | — | ya existe (T-58) |
| **Cafe** | classic | — | ya existe (T-58) |
| **Cozy** | classic | — | **RENOMBRAR desde `anime`** (ver abajo) |
| **Cyberpunk** | radial | — | sin NINGUNA referencia a Edgerunners (C5) |
| **Gato** | senior | Accesibilidad | |
| **Perro** | senior | Accesibilidad | |
- El Pro pasa a venderse por skins ADICIONALES (v2.0), no por estas.
- **Etiqueta "Accesibilidad"** visible en el selector de Temas para Gato/Perro, para que
  se entienda que recortan botones a propósito y no que están "incompletas".
- Arte de Cyberpunk: ilustraciones IA de personaje cyberpunk genérico, sin nombrar ni
  aludir a la serie ni al personaje. (Zanja C5 en lo comercial; el arte igual debe ser
  original y no una copia reconocible.)

### Coste de código de estas decisiones (ojo, no son gratis)
- **Renombrar `anime` → `cozy`** toca 4 sitios: id en `SKINS`, entrada
  `LEGACY_SKINS = { anime: 'cozy' }` en `setSkin()` (o los usuarios actuales pierden su
  skin), el asset `frontend/skins/anime-bg.webp` (renombrar + la URL dentro de
  `--bg-image`), y la lista `ASSETS` de `frontend/sw.js`. Es una migración, no un
  find&replace.
- **Todo gratis** simplifica: `FREE_SKIN` (constante única) pasa a ser un CONJUNTO de
  skins libres, y el gate Pro de skins queda inactivo pero NO se borra — v2.0 lo
  reactiva con el roster ampliado. Los `.pro-lock` del selector quedan sin uso por ahora.

## SET DE BOTONES DEL LAYOUT "senior" (recomendación pedida por el dueño)
De los 17 controles actuales, **quedan 8 + micrófono**; se ocultan 7.

**QUEDAN (8):** ▶‖ Play/Pausa · Vol+ · Vol− · Silenciar · Atrás · Teclado ·
**D-Pad** (`#btn-nav-mode`) · el micrófono, agrandado y protagonista.
- El **D-Pad se queda y va ENCENDIDO por defecto** (crítica C2): para quien no controla
  bien un puntero, navegar con flechas es más fácil que arrastrar un cursor.
- **Teclado se queda**: es el plan B cuando la voz falla; sin él no puede escribir nada.
- **Atrás se queda**: es el "deshacer" del usuario perdido, y no es destructivo.

**SE OCULTAN (7):** Borrar · Panel TV · Menú OS · X (cerrar app) · ◀◀ · ▶▶ · Inicio.
- **Borrar**: solo sirve tecleando; que viva dentro del cajón del teclado.
- **Panel TV** y **Menú OS**: diagnóstico y escritorio del sistema. Puro riesgo de
  confusión, cero uso diario.
- **X**: es long-press (mala interacción para este usuario) Y destructivo.
- **◀◀ / ▶▶**: son `KEY_LEFT`/`KEY_RIGHT`, redundantes con el D-Pad encendido.
- **Inicio**: es `killKiosk()`, MATA la app en curso (crítica C3). Se saca del layout.
  **VERIFICAR ANTES DE IMPLEMENTAR:** que lanzar una app desde `#apps-row` REEMPLACE
  el kiosk en curso. Si no lo hace, el usuario queda sin forma de salir de una app y
  el layout senior necesita UN botón seguro "Volver al inicio" con confirmación.
- Ocultar también `#latency` (ruido) y redactar `#status` en palabras, no en jerga
  ("Disconnected" no le dice nada a este usuario).
- El engranaje de Ajustes **se queda visible** (crítica C4: sin él no hay forma de salir
  del modo accesible).

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
  mercado nuevo. Resolver antes las CRITICAS DE DISEÑO C2/C3/C4/C6 **de esta misma seccion**
  — no confundir con el checklist del dueño de CURRENT §C, que es otro espacio de nombres.
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
