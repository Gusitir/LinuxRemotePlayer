# CURRENT — estado vivo
<!-- Formato: AGENTS.md §FORMATO. IDs (B/N/D/H/C) son anclas: citalos, no copies el texto.
     Limpieza profunda 2026-07-30: cerro el ciclo de correcciones (B9..B17) y todo eso
     salio de aca. El detalle de cada auditoria esta en git log. -->

```yaml
version_publicada:  1.9.0    # COMERCIAL. Publicada 2026-07-30, auditada contra el .deb real
dominio:            https://www.linuxremoteplayer.com
alias_vercel:       linux-remote-player.vercel.app   # VIVO a proposito: canal OTA del parque viejo
correo_soporte:     support@linuxremoteplayer.com    # buzon real; falta probar que envia (C9)
fase_activa:        v1.9 CERRADA en codigo (T-46..T-77 + T-56). Falta probar 1.9.0 y lo comercial
repo:               publico; se privatiza al lanzar (PLAN.md §T-57)
licencia:           Elastic 2.0
ultima_sesion:      2026-07-30
pruebas_device:     TESTING.md (ciclo 1.9.0, SIN EJECUTAR — L2 es el que importa)
docs_humanos:       docs/ARCHITECTURE.md + docs/DEVELOPING.md
historia:           CONTEXT.md + git log
```

> **Al entrar, lo que hay que saber:** **la 1.9.0 esta PUBLICADA** (30/07) y es la version
> comercial. El ciclo de correcciones cerro completo tras tres builds de prueba, y el codigo
> de la fase v1.9 esta terminado. **Lo que falta no es programar:** probar 1.9.0 en device
> (§TESTING, sobre todo L2 = B1 en los dos iPhone), privatizar el repo, y lo comercial.

## B — BLOQUEANTES

- **B18 · la 1.9.0 PUBLICADA tiene el bug del boton "Actualizar"** (H18). Se arreglo en
  **T-78, que NO viajo en ese `.deb`**. Un equipo con 1.9.0 y un `/tmp/lrp-update.log` ajeno
  vera "Error al aplicar actualización" y no podra actualizarse desde la app.
  *Salida manual mientras tanto:* `sudo rm -f /tmp/lrp-update.log`, o `sudo lrp-update`.
  **Se cierra publicando 1.9.1**, que es la primera tarea de la sesion siguiente.


- **B1 · el HUD se corre en iPhone — ARREGLADO en T-77, SIN PROBAR en device.** Sigue aca
  porque el arreglo no esta verificado. *Causa:* al volver del segundo plano iOS reporta la
  altura ANTERIOR en el instante en que disparan `pageshow`/`visibilitychange`; los listeners
  ya estaban, lo que faltaba era **no leer el valor de inmediato**. Ahora se re-lee tres
  veces (ya, al frame, a los 300ms).
  **Si tras probarlo el espacio sigue:** el siguiente paso es eliminar `--app-h` y confiar en
  `100dvh` — mas limpio, pero puede reabrir el problema de viewport que ese mecanismo vino a
  resolver en el ciclo v1.7. **Decision del dueño: si hace falta otra pasada, la definitiva
  es la 1.9.1.** Se cierra con **TESTING §L2**, en iPhone 8+ Y 12 (se comportaban distinto).

## N — SIGUIENTE (orden estricto)

1. **N1 · probar 1.9.0 en device** — `TESTING.md`, ciclo L1..L5. **L2 es el unico que decide
   algo**: si B1 quedo resuelto. El agente del HTPC cubre L1/L3/L5; L2 y L4 son del dueño.
2. **N2 · el repo YA ES PRIVADO (30/07) — falta cerrar la deuda de PLAN.md §T-57**, que se
   iba a verificar ANTES y quedo para despues. Pendiente y en orden de riesgo:
   **(a) que Vercel siga desplegando.** Si dejo de hacerlo y no se nota, **el canal OTA se
   congela**. *Test gratis:* el proximo push (aunque solo toque `.agents/`) dispara deploy —
   `website/vercel.json` es solo `cleanUrls`, sin Ignored Build Step. Mirar el dashboard.
   **(b) el clon WSL del release** va a pedir credenciales: resolverlo ANTES de un release,
   no en medio. En Windows ya andan (Git Credential Manager, probado con `git ls-remote`).
   **(c) `scripts/bootstrap.sh` ya da 404** — pero no lo ofrece la web (H6), daño real cero.
3. **N3 · lo comercial:** C9 (que support@ ENVIE sin caer en spam) → C5 (capturas de 1.9.0,
   las que ve Paddle) → **T-51 Paddle** (alta, producto $5, webhook, compra real + refund;
   arrastra B1b y H11) → T-55 docs.
4. **N4 · v1.9.1:** PH17 skins · PH20 demo web · D11 boton de modo oscuro · D12 iconos
   borrosos · H19 el QR que lleva a "Offline".

## HECHO — fase v1.9 (todo auditado APTO; evidencia en git log)

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
- **H12** el numero de version sale del backend y la interfaz del cache del SW: pueden
  discrepar sin aviso. Prioridad baja.
- **H1** cold-start de voz: dejo de reproducirse, no se hace keep-alive.
- **H2** Whisper alucina con silencio → descartar audios <~1s antes de facturar.
- **H3** el OTA actualiza al cerrar/reabrir la PWA, no sola. Aceptado.
- **H4** falta intent "volumen al maximo" (hoy sube 1 paso).
- **H5** `showInstallScreen` usa `hidden` pero `#app-ui` tiene `.flex` (gana el autor);
  `showPairingScreen` lo esquiva con `style.display`. Unificar.
- **H6** `bootstrap.sh` YA murio (repo privado desde el 30/07): su `REPO_URL` da 404. No lo
  ofrece `website/` —solo lo nombran README y CHANGELOG—, asi que no rompe a nadie. Borrarlo
  con su mencion en el README. Va en T-57 §(c).
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
- [~] **C7** repo privatizado el 30/07 — **el boton se apreto, la verificacion no.** Sigue
      abierto por §CICLO regla 4 (cerrar ≠ haber editado): se cierra cuando (a) Vercel
      demuestre que sigue desplegando, (b) el clon WSL clone sin trabarse y (c) muera
      `bootstrap.sh`. Detalle en **N2**.
