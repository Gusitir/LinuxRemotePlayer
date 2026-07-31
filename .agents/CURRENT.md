# CURRENT — estado vivo
<!-- Formato: AGENTS.md §FORMATO. IDs (D/H/C) son anclas: citalos, no copies el texto.
     Limpieza 2026-07-30 (2da): cerro la fase v1.9 entera. Todo lo cerrado salio de aca;
     el detalle vive en git log, en PLAN.md y en los comentarios del codigo. -->

```yaml
version_publicada:  1.9.1    # COMERCIAL. Auditada contra el .deb real y verificada VIVA
                             # (el dominio sirve latest.json con su sha256) + 6/6 en device
dominio:            https://www.linuxremoteplayer.com
alias_vercel:       linux-remote-player.vercel.app   # VIVO a proposito: canal OTA del parque viejo
correo_soporte:     support@linuxremoteplayer.com    # recibe y ENVIA; cae en spam (C9)
fase_activa:        v1.9 CERRADA (T-46..T-82). Solo queda lo COMERCIAL: Paddle
repo:               PRIVADO desde el 30/07; T-57 cerrado entero
licencia:           Elastic 2.0 (source-available, NO open source — dicho asi en el README)
ultima_sesion:      2026-07-30
pruebas_device:     TESTING.md — ciclo 1.9.1 EJECUTADO Y APTO (6/6)
docs_humanos:       docs/ARCHITECTURE.md + docs/DEVELOPING.md
historia:           CONTEXT.md + git log
```

> **Al entrar:** **no queda ingenieria pendiente.** La 1.9.1 esta publicada, viva y
> certificada en device; el repo es privado; el sitio y el README quedaron al dia con el
> producto real (T-82). **Lo unico que falta para vender es el alta en Paddle** (§N).

## B — BLOQUEANTES

**NINGUNO.**

## N — SIGUIENTE (orden estricto)

1. **N1 · C9: sacar `support@` de la carpeta de spam.** Ya ENVIA y llega — probado con un
   correo real —, pero **cae en spam**. Falta SPF/DKIM en PASS y reputacion. *Trampa
   registrada:* **cuando entre Resend (T-51) su include va en el MISMO registro SPF** — dos
   registros SPF fallan en ambos, y ahi se pierde el correo que lleva la clave al cliente.
2. **N2 · T-51 Paddle** — alta, producto $5, webhook, compra real + refund. Arrastra **H11**
   (poner la URL real donde hoy dice PLACEHOLDER-PADDLE) y **H20** (redesplegar la Edge
   Function para que el correo al cliente salga con el nombre corregido).
3. **N3 · T-55** — la doc de usuario, con el flujo de compra ya real.
4. **N4 · fuera de alcance ahora (v1.9.2 en adelante):** demo interactiva (D6) · PH17 skins ·
   D11 boton de modo oscuro · D12 iconos borrosos · H19 el QR "Offline" · H21 `theme-color`.

## HECHO — fase v1.9

**T-46..T-82, todo auditado APTO.** El detalle esta en `git log`; no se repite aca.
Lo unico que el proximo agente NO puede re-derivar:

- **Tres builds de prueba antes de la comercial salvaron el lanzamiento.** El primero destapo
  que cada actualizacion dejaba el servicio muerto: si 1.8.10 hubiera sido el lanzamiento,
  cada comprador lo habria sufrido en su primera actualizacion.
- **Los porques tecnicos de T-70, T-72 y T-79 estan COMENTADOS EN EL CODIGO**, que es donde
  los va a leer quien intente "ordenarlo" y revertirlos. No los copies aca.
- **Una prueba de device solo vale si ANTES se probo que el equipo ES el paquete.** El ciclo
  1.9.0 dio ✅ sobre un equipo parcheado a mano. Hoy eso es un item con `dpkg -V`
  (TESTING §M3), no un recordatorio.

## D — DECISIONES VIGENTES (no re-litigar)

- **D1 · pagos: PADDLE.** Stripe no opera para vendedores en Ecuador; PayPal plan B; Ko-fi
  para donaciones. Validacion = compra real $5 + refund. **Paddle REVISA el sitio antes de
  aprobar** → web, dominio y capturas van ANTES del alta.
- **D2 · nombre: LinuxRemotePlayer**; **"LRP"** marca corta (es el `short_name` del manifest).
- **D3 · precio:** Pro unico $5 lifetime. Suscripcion recien con Voz 2.0.
- **D4 · las 7 skins van GRATIS**, son el gancho; el Pro se vendera con skins ADICIONALES en
  v2.0. Las 4 que existen ya estan libres; las otras 3 son PH17. Falta del dueño: wallpapers.
- **D5 · Voz 2.0 a v2.0** (PLAN.md §PH19).
- **D6 · demo interactiva en la web** (PLAN.md §PH20) — **a v1.9.2** por decision del dueño;
  reemplaza al video, que se cancelo. Dos reglas duras: etiqueta de SIMULACION visible y CERO red.
- **D7 · `Techlm77/LinuxPlay` no es competencia** (GPL-2.0, streaming de escritorio; LRP no
  transmite video). NO se rebrandea. Analisis: PLAN.md §MERCADO. Su codigo no entra aca:
  AGENTS.md §CÓDIGO DE TERCEROS.
- **D9/D10 · la voz se enciende sola al activar la licencia** y el usuario puede apagarla.
  El arranque **nunca** pisa un `false` explicito.
- **D11/D12 · boton de modo oscuro en el HUD e iconos de apps borrosos → post 1.9.1.**

## H — HALLAZGOS ABIERTOS (no bloquean)

- **H11 · `PLACEHOLDER-PADDLE`** vive en `.env.example` y en los botones de compra del sitio.
  `grep -rn PLACEHOLDER-PADDLE` lista lo pendiente. Se completa en T-51.
- **H20 · el correo del cliente con su clave** (`stripe-webhook`) ya dice el nombre correcto,
  pero **no surte efecto hasta redesplegar la Edge Function**. Va con T-51.
- **H19 · el QR lleva a una pagina "Offline".** El QR trae `?token=…` y `caches.match` compara
  la URL completa, asi que no matchea el precache de `/` y el service worker devuelve texto
  plano 503. *Fix:* `{ ignoreSearch: true }`. **Y en el mismo bloque falta un `else` tras el
  timeout de 3s: si el cache falla ahi, la promesa nunca se resuelve.**
- **H21 · el `theme-color` no se actualiza en vivo en iOS >=16** (iPhone 12): al cambiar de
  tema hay que cerrar y reabrir la PWA. En iPhone 8+ (iOS <16) si funciona. Lo reescribe
  `app.js:174`; Safari 16+ no re-evalua ese meta. **Aparecio al sacar `viewport-fit=cover`**
  (T-79): sin `cover` el `theme-color` pinta la barra de estado, y recien ahi se nota.
- **H12** el numero de version sale del backend y la interfaz del cache del SW: pueden
  discrepar sin aviso. Prioridad baja.
- **H1** cold-start de voz: dejo de reproducirse, no se hace keep-alive.
- **H2** Whisper alucina con silencio → descartar audios <~1s antes de facturar.
- **H3** el OTA actualiza al cerrar/reabrir la PWA, no sola. Aceptado.
- **H4** falta intent "volumen al maximo" (hoy sube 1 paso).
- **H5** `showInstallScreen` usa `hidden` pero `#app-ui` tiene `.flex` (gana el autor);
  `showPairingScreen` lo esquiva con `style.display`. Unificar.
- **H22 · la «×» de borrar/ocultar esta SIEMPRE visible** en cada icono de app
  (`app.js:788-802`, sin modo edicion). Sale en todas las capturas del sitio. Es ruido
  visual en la primera impresion del producto; conviene esconderla tras un modo edicion.

## C — CHECKLIST DEL DUEÑO

- [~] **C9** `support@` **ENVIA y llega, pero cae en SPAM.** Falta ver "Mostrar original" con
      **SPF y DKIM en PASS** y ganar reputacion. Ojo con el registro SPF unico (§N1).
- [ ] **C6** `supabase functions deploy send-feedback --no-verify-jwt` (desde v1.5).
- [ ] **C3** wallpapers de las skins nuevas (PH17, no bloquea). Para Gato/Perro mandar
      **el TILE** (~400x400), no el pantallazo: tilear ya esta soportado y pesa ~30KB vs ~170KB.
- [x] **C1** push 1.8.9 · [x] **C2** dominio + `support@` · [x] **C8** el buzon RECIBE ·
      [x] **C7** repo privado + T-57 cerrado · [x] **C5** capturas de 1.9.1 ya publicadas (T-82)
