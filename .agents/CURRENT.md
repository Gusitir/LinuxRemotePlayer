# CURRENT — estado vivo
<!-- Formato: AGENTS.md §FORMATO. IDs (B/N/D/H/C) son anclas: citalos, no copies el texto.
     Limpieza profunda 2026-07-30: cerro el ciclo de correcciones (B9..B17) y todo eso
     salio de aca. El detalle de cada auditoria esta en git log. -->

```yaml
version_publicada:  1.8.12   # build de PRUEBA. La comercial es la 1.9.0, sin construir
dominio:            https://www.linuxremoteplayer.com
alias_vercel:       linux-remote-player.vercel.app   # VIVO a proposito: canal OTA del parque viejo
correo_soporte:     support@linuxremoteplayer.com    # buzon real; falta probar que envia (C9)
fase_activa:        v1.9 -> lanzamiento. Hechas T-46..T-76; faltan T-77, T-56, T-51, T-55, T-57
repo:               publico; se privatiza al lanzar (PLAN.md §T-57)
licencia:           Elastic 2.0
ultima_sesion:      2026-07-30
pruebas_device:     TESTING.md (ciclo 1.9.0, sin ejecutar)
docs_humanos:       docs/ARCHITECTURE.md + docs/DEVELOPING.md
historia:           CONTEXT.md + git log
```

> **Al entrar, lo que hay que saber:** el ciclo de correcciones **cerro completo** el 30/07.
> Se hicieron tres builds de prueba (1.8.10, 1.8.11, 1.8.12) y el ultimo valido en hardware
> **todo lo que bloqueaba la venta**, incluido el bug que dejaba el servicio muerto en cada
> actualizacion. **No quedan bloqueantes tecnicos.** Falta B1 (visual, iPhone) y despues es
> todo comercial.

## B — BLOQUEANTES

- **B1 · el HUD se corre y tapa botones en iPhone.** Al reabrir la PWA aparece un espacio
  extra bajo la barra de estado que desplaza el contenido; en iPhone 8+ oculta los botones
  de abajo, en 12 solo molesta. **Abierto desde T-58 y confirmado en los tres ciclos.**
  *Causa probable:* `--app-h` sale de `visualViewport.height` y **no se recalcula al reanudar
  la PWA** — faltan `visualViewport.resize` y `pageshow`. Al volver de segundo plano conserva
  un valor viejo en pixeles.
  *Dos caminos:* agregar los listeners, o eliminar `--app-h` y confiar en `100dvh` (ese
  mecanismo es anterior al soporte de `dvh` en iOS y hoy podrian estorbarse).
  **Decision del dueño (30/07): se arregla en 1.9.0.** Necesita ida y vuelta con los dos
  telefonos; si hace falta otra pasada, la definitiva seria 1.9.1.

## N — SIGUIENTE (orden estricto)

1. **N1 · T-77: arreglar B1** + el log del actualizador (H18). Es lo ultimo de codigo.
2. **N2 · T-56, el release v1.9.0.** Absorbe: las 6 lineas de la web que aun venden los temas
   como Pro (`website/index.html:148,254,299` + `website/en/index.html:148,256,301`) y el
   CHANGELOG. Sigue §PROCESO DE RELEASE de AGENTS.md. **Savepoint del proyecto.**
3. **N3 · probar 1.9.0 en device** (TESTING.md) y **privatizar** (PLAN.md §T-57).
4. **N4 · lo comercial:** C9 (que support@ ENVIE sin caer en spam) → C5 (capturas con la skin
   Day) → **T-51 Paddle** (alta, producto $5, webhook, compra real + refund; arrastra B1b y
   H11) → T-55 docs.

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

- **H18 · el log del actualizador queda mudo** si `/tmp/lrp-update.log` lo creo otro usuario.
  **Probado: NO es peligroso** — el script sobrevive (ese `exec` va antes del `set -e`) y
  systemd captura todo en el journal. Se pierde solo el log dedicado, que es justo el que se
  mira cuando un OTA falla. *Fix (T-77):* mover el log a **`/var/log/lrp-update.log`**,
  root-only y fuera del alcance de `PrivateTmp`. **NO usar el parche de `exec 3>>` que se
  probo en el device: verificado que no silencia el mensaje y complica un script critico.**
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
- **H6** `bootstrap.sh` es legacy y muere con el repo privado: borrarlo en T-57.
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
- [ ] **C7** privatizar el repo al lanzar — **que verificar antes: PLAN.md §T-57.**
