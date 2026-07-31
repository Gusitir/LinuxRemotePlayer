# CURRENT — estado vivo
<!-- Formato: AGENTS.md §FORMATO. IDs (B/N/D/H/C) son anclas: citalos, no copies el texto.
     Limpieza profunda 2026-07-30: cerro el ciclo de correcciones (B9..B17) y todo eso
     salio de aca. El detalle de cada auditoria esta en git log. -->

```yaml
version_publicada:  1.9.1    # COMERCIAL. Publicada 2026-07-30, auditada contra el .deb real
                             # y verificada VIVA: el dominio sirve latest.json con su sha256
dominio:            https://www.linuxremoteplayer.com
alias_vercel:       linux-remote-player.vercel.app   # VIVO a proposito: canal OTA del parque viejo
correo_soporte:     support@linuxremoteplayer.com    # buzon real; falta probar que envia (C9)
fase_activa:        v1.9 CERRADA en codigo (T-46..T-81). Falta probar 1.9.1 en device y lo comercial
repo:               publico; se privatiza al lanzar (PLAN.md §T-57)
licencia:           Elastic 2.0
ultima_sesion:      2026-07-30
pruebas_device:     TESTING.md (ciclo 1.9.1, SIN EJECUTAR — M2 es el unico que decide)
docs_humanos:       docs/ARCHITECTURE.md + docs/DEVELOPING.md
historia:           CONTEXT.md + git log
```

> **Al entrar, lo que hay que saber:** **la 1.9.1 esta PUBLICADA, VIVA y CERTIFICADA EN
> DEVICE** (30/07, 6/6 en TESTING). El repo ya es PRIVADO y T-57 cerro entero. **No queda
> NINGUN bloqueante tecnico ni codigo pendiente en la fase v1.9.** Todo lo que sigue es
> comercial: que `support@` envie, capturas, y el alta de Paddle.

## B — BLOQUEANTES

**NINGUNO.** B1 y B18 cerraron el 30/07 con la 1.9.1, certificada en device (TESTING 6/6).

Lo unico que no se re-deriva de git, en una linea cada uno:
- **B1 era `viewport-fit=cover`**, no la altura que re-leia T-77. El porque completo esta
  **comentado en `frontend/index.html`**, que es donde lo va a leer quien quiera "ordenarlo"
  y volver a ponerlo. Detalle y radio de impacto: **PLAN.md §T-79**.
- **B18 era menos grave de lo que creiamos:** solo dispara si `/tmp/lrp-update.log` ya existe
  y no es escribible por el usuario del servicio (alguien corrio `sudo lrp-update` a mano
  antes de T-77). **En una instalacion nueva nunca habria fallado.** Analisis: **TESTING
  §NOTA DEL AUDITOR**. Salida en un equipo aun en 1.9.0: `sudo rm -f /tmp/lrp-update.log`.
- **La regla que salio de todo esto:** una prueba de device solo vale si ANTES se probo que
  el equipo ES el paquete — el ciclo 1.9.0 dio ✅ sobre un equipo parcheado a mano. Hoy eso
  es un item con `dpkg -V` (TESTING §M3), no un recordatorio.

## N — SIGUIENTE (orden estricto)

1. ~~**N1 · probar 1.9.1 en device**~~ **HECHO 30/07: 6/6 OK, ciclo cerrado y auditado.**
   **No queda NADA de ingenieria en la fase v1.9.** Lo que sigue es todo comercial.
2. **N2 · el repo YA ES PRIVADO (30/07) — deuda de PLAN.md §T-57, casi cerrada:**
   **(a) Vercel ✅ CERRADO 30/07** — deployo sin problema tras privatizar. El canal OTA vive.
   **(b) el clon WSL ✅ CERRADO 30/07.** Era una trampa: el helper estaba solo en el config
   LOCAL de `~/lrp-release`, asi que el clon viejo andaba y el FRESCO del paso 2 fallaba con
   `fatal: could not read Username for 'https://github.com'`. Se puso el helper en el
   **global** de WSL (apunta al GCM de Windows; no guarda secretos nuevos). **Verificado
   reproduciendo el paso 2:** `git clone --depth 1` fresco entro sin pedir credenciales.
   **(c) `bootstrap.sh` ✅ CERRADO 30/07** (T-80): borrado junto con su mencion en el README y
   la variable muerta `GITHUB_REPO`. **T-57 queda cerrado entero.**
3. **N3 · lo comercial:** C9 (que support@ ENVIE sin caer en spam) → C5 (capturas de 1.9.0,
   las que ve Paddle) → **T-51 Paddle** (alta, producto $5, webhook, compra real + refund;
   arrastra B1b y H11) → T-55 docs.
4. **N4 · lo que NO entra en 1.9.1** (sale despues; 1.9.1 es solo T-78+T-79): PH17 skins ·
   PH20 demo web · D11 boton de modo oscuro · D12 iconos borrosos · H19 el QR "Offline" ·
   H21 el `theme-color` de iOS 16+.

## HECHO — fase v1.9 (todo auditado APTO; evidencia en git log)

**T-78** el boton de actualizar no depende de `/tmp` · **T-79** B1: fuera `viewport-fit=cover`
(la causa real) · **T-80** muere `bootstrap.sh` + `GITHUB_REPO` · **T-81** release 1.9.1 ·
**T-46..T-50** ai-proxy, anti-abuso y licencia de 1 dispositivo · **T-53** sitio ES+EN ·
**T-58** identidad app↔web · **T-59..T-61** release 1.8.9 publicado + dominio propio ·
**T-62** skins gratis · **T-63** doc de FastAPI cerrada · **T-64** apt remove limpia ·
**T-65** URLs al dominio · **T-66** pulido de nombres · **T-67** instalador · **T-68** voz
automatica + buy_url · **T-69/T-74/T-76** builds de prueba 1.8.10/11/12 · **T-70** el OTA ya
no deja el servicio muerto · **T-71** voz al arrancar + cadena de certs · **T-72** CA con
nombre unico · **T-73** nombres y `.env` · **T-75** apt remove borra claves y CA del sistema.

Lo unico que el proximo agente no puede re-derivar de git:
- **De T-46..T-50 falta el video demo.** Placeholders vivos en la web: PADDLE / KOFI / VIDEO.
- **Los porques tecnicos de T-70 y T-72 estan COMENTADOS EN EL CODIGO**, que es donde los va
  a leer quien intente "ordenarlo". No los repitas aca.
- **Tres builds de prueba antes de la comercial fue la decision correcta**: el primero
  destapo que cada actualizacion dejaba el servicio muerto. Si 1.8.10 hubiera sido el
  lanzamiento, cada comprador lo habria sufrido en su primera actualizacion.

## D — DECISIONES VIGENTES (no re-litigar)

- **D1 · pagos: PADDLE.** Stripe no opera para vendedores en Ecuador; PayPal plan B; Ko-fi
  para donaciones. Validacion = compra real $5 + refund. **Paddle REVISA el sitio antes de
  aprobar** → web, dominio y capturas van ANTES del alta.
- **D2 · nombre: LinuxRemotePlayer**; **"LRP"** marca corta (es el `short_name` del manifest).
- **D3 · precio:** Pro unico $5 lifetime. Suscripcion recien con Voz 2.0.
- **D4 · las 7 skins van GRATIS**, son el gancho; el Pro se vendera con skins ADICIONALES en
  v2.0. Las 4 que existen ya estan libres; las otras 3 son PH17. Falta del dueño: wallpapers.
- **D5 · Voz 2.0 a v2.0** (PLAN.md §PH19).
- **D6 · demo interactiva en la web** (PLAN.md §PH20, v1.9.1). Dos reglas duras: etiqueta de
  SIMULACION visible y CERO red.
- **D7 · `Techlm77/LinuxPlay` no es competencia** (GPL-2.0, streaming de escritorio; LRP no
  transmite video). NO se rebrandea. Analisis: PLAN.md §MERCADO. Su codigo no entra acá:
  AGENTS.md §CÓDIGO DE TERCEROS.
- **D9/D10 · la voz se enciende sola al activar la licencia** y el usuario puede apagarla.
  El arranque **nunca** pisa un `false` explicito.
- **D11/D12 · boton de modo oscuro en el HUD e iconos de apps borrosos → v1.9.1.**

## H — HALLAZGOS ABIERTOS (no bloquean)

- **H18 · el log del actualizador — CERRADO en T-77 + T-78, pero la lectura inicial fue MALA.**
  Se declaro "no peligroso" mirando solo el `exec` del script. **Lo era:** `backend/main.py`
  abria ESE MISMO `/tmp/lrp-update.log` antes de lanzar el actualizador, y si el archivo era
  de otro usuario el `open()` lanzaba, el endpoint devolvia 500 y **el boton "Actualizar" de
  la app fallaba sin lanzar nada**. Lo reporto el dueño usando el producto, no el testing.
  *Leccion:* un mismo recurso tocado desde dos lados solo se entiende mirando los dos.
  T-77 movio el log del script a `/var/log`; T-78 saco la apertura del backend (usa
  `DEVNULL`, porque el script ya redirige su propia salida). **Gemini encontro que
  `system_apply_update` —el panel de la TV— tenia el bug identico**, fuera del alcance del
  brief.

- **H11 · `.env.example` traia un link de Stripe TEST** → ya vacio (PLACEHOLDER-PADDLE). Se
  completa en T-51 con la URL real de Paddle. `grep -rn PLACEHOLDER-PADDLE` lista lo pendiente.
- **B1b · `gracias.html` publica el gmail personal del dueño.** La ve un procesador de pagos.
  Se rehace en T-51.
- **H19 · el QR lleva a una pagina "Offline".** El QR trae `?token=…` y `caches.match` compara
  la URL completa, asi que no matchea el precache de `/` y el service worker devuelve texto
  plano 503. *Fix:* `{ ignoreSearch: true }`. **Y en el mismo bloque falta un `else` tras el
  timeout de 3s: si el cache falla ahi, la promesa nunca se resuelve.**
- **H21 · el `theme-color` no se actualiza en vivo en iOS >=16** (iPhone 12): al cambiar de
  tema hay que cerrar y reabrir la PWA. En iPhone 8+ (iOS <16) si funciona. Lo reescribe
  `app.js:174`; Safari 16+ no re-evalua ese meta. Sin workaround conocido. **Aparecio al
  sacar `viewport-fit=cover`** (T-79): sin `cover`, el `theme-color` pasa a pintar la barra
  de estado, asi que recien ahi se nota. Marginal, NO bloquea el lanzamiento.
- **H12** el numero de version sale del backend y la interfaz del cache del SW: pueden
  discrepar sin aviso. Prioridad baja.
- **H1** cold-start de voz: dejo de reproducirse, no se hace keep-alive.
- **H2** Whisper alucina con silencio → descartar audios <~1s antes de facturar.
- **H3** el OTA actualiza al cerrar/reabrir la PWA, no sola. Aceptado.
- **H4** falta intent "volumen al maximo" (hoy sube 1 paso).
- **H5** `showInstallScreen` usa `hidden` pero `#app-ui` tiene `.flex` (gana el autor);
  `showPairingScreen` lo esquiva con `style.display`. Unificar.
- ~~**H6** `bootstrap.sh`~~ **CERRADO en T-80 (30/07)**: borrado con su mencion en el README y
  con `GITHUB_REPO`. *Dato que aparecio al auditarlo:* se venia empaquetando en el `.deb`
  (`build_deb.sh` copia `scripts/` entera y su lista de exclusiones nunca lo incluyo), asi
  que vivia en `/opt/linuxremoteplayer/scripts/` de cada usuario. `dpkg` lo borra al
  actualizar a 1.9.1.
- **H20 · el correo del cliente con su clave** (`stripe-webhook`) ya dice el nombre correcto,
  pero **eso no surte efecto hasta redesplegar la Edge Function**. Va con T-51.

## C — CHECKLIST DEL DUEÑO

- [x] **C1** push de 1.8.9 · [x] **C2** dominio + `support@` en la web · [x] **C8** el buzon
      RECIBE (probado)
- [ ] **C9** que support@ **ENVIE** sin caer en spam: mandar uno a un gmail y ver
      "Mostrar original" con **SPF y DKIM en PASS**. El DNS ya esta cargado y verificado.
      **Cuando entre Resend (T-51), su include va en el MISMO registro SPF** — dos registros
      SPF fallan en ambos y ahi se pierde el correo de licencias.
- [ ] **C5** capturas nuevas — **de v1.9.0**, o fotografian el producto viejo. Las ve Paddle.
- [ ] **C6** `supabase functions deploy send-feedback --no-verify-jwt` (desde v1.5).
- [ ] **C3** wallpapers de las skins nuevas (PH17/v1.9.1, no bloquea). Para Gato/Perro mandar
      **el TILE** (~400x400), no el pantallazo: tilear ya esta soportado y pesa ~30KB vs ~170KB.
- [x] **C7** repo privatizado el 30/07 y **CERRADO ENTERO** el mismo dia: (a) Vercel sigue
      desplegando, (b) el clon fresco de WSL autentica, (c) `bootstrap.sh` borrado (T-80).
