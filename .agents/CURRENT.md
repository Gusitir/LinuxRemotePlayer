# CURRENT — estado vivo
<!-- Formato: AGENTS.md §FORMATO. IDs (D/H/C) son anclas: citalos, no copies el texto.
     Lo cerrado NO vive aca: esta en git log, en PLAN.md y en comentarios del codigo. -->

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

> **Al entrar:** **no queda ingenieria que BLOQUEE la venta** — si quedan hallazgos abiertos,
> todos agendados a v1.9.2 (§N2, §H). 1.9.1 publicada, viva y certificada en device; repo
> privado; sitio, README y terminos al dia (T-82/T-83). **Lo unico que falta para vender es
> el alta en Paddle** (§N1).

## B — BLOQUEANTES

**NINGUNO.**

## N — SIGUIENTE (orden estricto)

1. **N1 · T-51 Paddle — LO UNICO que falta para vender.** Alta, producto $5, webhook, compra
   real + refund. Arrastra **H11** y **H20**. *El sitio ya esta listo:* T-82 lo puso al dia y
   T-83 sumo los terminos, que era la unica objecion previsible.
2. **N2 · v1.9.2 — correcciones. Nada de esto bloquea a Paddle:** C9 · C6 · H12 · H19 · H5 ·
   H22 · D6 (demo web).
3. **N3 · T-55** — doc de usuario, con el flujo de compra real.
4. **N4 · PH0 ADOPTADA (31/07): la superficie de verificacion.** Cuatro capas + rama y CI —
   **detalle en PLAN.md §PH0**. Arrancar por las dos primeras: son horas y matan la clase de
   error que ya mordio. **Hoy no hay UN SOLO test automatico.**
5. **N5 · v2.0 NO se empieza hasta ver clientes** (D13).

## HECHO — fase v1.9

**T-46..T-82, todo auditado APTO.** El detalle esta en `git log`; no se repite aca.
Lo unico que el proximo agente NO puede re-derivar:

- **Tres builds de prueba antes de la comercial salvaron el lanzamiento:** el primero destapo
  que cada actualizacion dejaba el servicio muerto.
- **Los porques de T-70, T-72 y T-79 estan COMENTADOS EN EL CODIGO**, que es donde los lee
  quien intente "ordenarlo" y revertirlos. No los copies aca.
- **Una prueba de device solo vale si ANTES se probo que el equipo ES el paquete** (el ciclo
  1.9.0 dio ✅ sobre uno parcheado a mano). Hoy es un item con `dpkg -V`: TESTING §M3.

## D — DECISIONES VIGENTES (no re-litigar)

- **D1 · pagos: PADDLE.** Stripe no opera para vendedores en Ecuador; PayPal plan B; Ko-fi
  para donaciones. Validacion = compra real $5 + refund. **Paddle REVISA el sitio antes de
  aprobar** → web, dominio, capturas y terminos van ANTES del alta.
- **D2 · nombre: LinuxRemotePlayer**; **"LRP"** es el `short_name` del manifest. · **D3 ·
  precio:** Pro unico $5 lifetime; suscripcion recien con Voz 2.0.
- **D4 · las 7 skins van GRATIS**, son el gancho; el Pro se vendera con skins ADICIONALES en
  v2.0. Las 4 que existen ya estan libres; las otras 3 son PH17. Falta del dueño: wallpapers.
- **D5 · Voz 2.0 a v2.0** (PLAN.md §PH19).
- **D6 · demo interactiva** (PLAN.md §PH20) — **a v1.9.2**; reemplaza al video, cancelado.
  Reglas duras: etiqueta de SIMULACION visible y CERO red.
- **D7 · `Techlm77/LinuxPlay` no es competencia** (GPL-2.0, streaming de escritorio; LRP no
  transmite video). NO se rebrandea. Analisis: PLAN.md §MERCADO. Su codigo NO entra aca.
- **D9/D10 · la voz se enciende sola al activar la licencia** y se puede apagar; el arranque
  **nunca** pisa un `false` explicito.
- **D11/D12 · boton de modo oscuro en el HUD e iconos de apps borrosos → v2.0** (estetica).
- **D13 · v2.0 NO arranca hasta ver clientes reales** (31/07); mientras, SOLO correcciones
  1.9.x. *Por que:* junta tres apuestas distintas —skins (ingreso), multi-distro (alcance),
  voz (retencion)— y en un solo release la matriz de prueba se multiplica; la 1.9.0, mucho
  mas chica, necesito TRES builds. **Se entrega por pistas, empezando por skins, que cobra.**
- **D14 · el feedback va a una TABLA de Supabase, NO por correo** (31/07). 1 por dia **por
  dispositivo** (por IP no: una casa comparte IP) y **server-side**, que el cliente se saltea.
  *Por que no correo:* si sale del mismo dominio que las claves, **una queja de spam degrada
  la entrega de las claves**, que es el correo del que depende la venta.
- **D15 · nada de subdominios de correo** (decision del dueño, 31/07): no tiene acceso ni los
  quiere. Si algun dia hace falta aislar reputacion, se crea **otra cuenta de correo**.

## H — HALLAZGOS ABIERTOS (no bloquean)

- **H11** `grep -rn PLACEHOLDER-PADDLE` lista lo pendiente. Se llena en T-51.
- **H20 · el correo con la clave** (`stripe-webhook`) ya dice el nombre correcto, pero **no
  surte efecto hasta redesplegar la Edge Function**. Va con T-51.
- **H19 · el QR "Offline" — SIGUE ABIERTO** (re-verificado en codigo 31/07; se lo creia
  corregido). El QR codifica `…/?token=…` (`main.py:370`) y **ninguna `caches.match` de
  `sw.js` usa `ignoreSearch`**. *Parece arreglado porque con red buena el `fetch` gana al
  timeout de 3s y el SW nunca toca el cache; falla solo con el backend caido.* Fix:
  `ignoreSearch: true` **+ el `else` que falta en `sw.js:34`** (hoy la promesa no resuelve
  nunca y la pagina queda colgada; la rama del `catch`, :51, si lo tiene).
- **H21 · el `theme-color` no refresca en vivo en iOS >=16** (iPhone 12; en 8+ si): hay que
  cerrar y reabrir la PWA. Lo reescribe `app.js:174` y Safari 16+ no re-evalua ese meta.
  Aparecio al sacar `viewport-fit=cover` (T-79), que es cuando el `theme-color` pasa a pintar
  la barra de estado.
- **H12 · a v1.9.2.** La version sale del backend y la interfaz del cache del SW: divergen
  sin aviso cuando la PWA nunca se cierra. *Fix propuesto:* al conectar, comparar ambas y si
  difieren forzar `skipWaiting` + recarga — de paso cierra H3 casi entero.
- **H1** cold-start de voz: dejo de reproducirse, no se hace keep-alive. · **H2** Whisper
  alucina con silencio → descartar audios <~1s antes de facturar. · **H3** el OTA actualiza al
  cerrar/reabrir la PWA (aceptado; lo aliviaria H12). · **H4** falta "volumen al maximo".
- **H5 · a v1.9.2.** `showInstallScreen` usa `hidden` pero `#app-ui` tiene `.flex` (gana el
  autor); `showPairingScreen` lo esquiva con `style.display`. Dos mecanismos para lo mismo:
  uno va a fallar en algun estado.
- **H22 · a v1.9.2.** La «×» de borrar/ocultar esta SIEMPRE visible en cada icono
  (`app.js:788-802`, sin modo edicion). Sale en todas las capturas. Ruido visual en la
  primera impresion; no bloquea Paddle.

## C — CHECKLIST DEL DUEÑO

- [~] **C9 · a v1.9.2.** `support@` ENVIA y llega, pero **cae en spam**. *Empezar por repetir
      la prueba: la que lo detecto tenia asunto y cuerpo `test`, que ya es patron de spam.*
      **Analisis completo y que mirar: PLAN.md §CORREO.** Trampa: cuando entre Resend su
      include va en el MISMO registro SPF — dos registros fallan en ambos.
- [ ] **C6 · a v1.9.2**, y cambia de forma: el feedback va a **tabla de Supabase**, no a
      correo (D14). El deploy sigue pendiente desde v1.5: **el boton lleva cuatro versiones
      muerto** sin que nadie lo notara — lo que pasa con lo que solo vive en un checklist.
- [ ] **C3** wallpapers de las skins nuevas (PH17, no bloquea). Para Gato/Perro mandar
      **el TILE** (~400x400), no el pantallazo: tilear ya esta soportado y pesa ~30KB vs ~170KB.
- [x] **C1** push 1.8.9 · [x] **C2** dominio + `support@` · [x] **C8** el buzon RECIBE ·
      [x] **C7** repo privado + T-57 cerrado · [x] **C5** capturas de 1.9.1 ya publicadas (T-82)
