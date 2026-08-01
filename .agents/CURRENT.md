# CURRENT — estado vivo
<!-- Formato: AGENTS.md §FORMATO. IDs son anclas: citalos, no copies el texto.
     ESTE archivo = estado de la version en curso. Los bugs viven en BUGS.md y las tareas
     del dueño en USER.md; aca solo se los CITA. Lo cerrado esta en git log y en PLAN.md. -->

```yaml
version_publicada:  1.9.1    # COMERCIAL. Auditada contra el .deb real y verificada VIVA
                             # (el dominio sirve latest.json con su sha256) + 6/6 en device
dominio:            https://www.linuxremoteplayer.com
alias_vercel:       linux-remote-player.vercel.app   # VIVO a proposito: canal OTA del parque viejo
correo_soporte:     support@linuxremoteplayer.com    # recibe y ENVIA; cae en spam (C9)
fase_activa:        v1.9.1 LANZADA. **v1.9.2 = la que habilita COBRAR** (B19 + paddle-webhook)
repo:               PRIVADO desde el 30/07; T-57 cerrado entero
licencia:           Elastic 2.0 (source-available, NO open source — dicho asi en el README)
ultima_sesion:      2026-07-31
pruebas_device:     TESTING.md — ciclo 1.9.1 EJECUTADO Y APTO (6/6)
docs_humanos:       docs/ARCHITECTURE.md + docs/DEVELOPING.md
bugs:               BUGS.md — abiertos y cerrados, SIN techo
tareas_del_dueño:   USER.md — infra, cuentas, comandos y el contrato de quien hace que
historia:           CONTEXT.md + git log
```

> **Al entrar: NO SE COBRA hasta cerrar B19** (el OTA da root sin firma; lo hallo una
> auditoria externa el 31/07). El alta en Paddle se puede PEDIR ya —el sitio esta listo: 1.9.1
> publicada y certificada en device, repo privado, capturas reales, terminos en dos idiomas—
> pero **la primera venta espera a la 1.9.2**, que es la que firma el OTA.

## B — BLOQUEANTES

- **B19 · el OTA da root sin firma. NO cobrar antes de cerrarlo.** El sha256 sale del MISMO
  origen que el `.deb`, asi que detecta corrupcion pero no hostilidad: quien tome Vercel, el
  registrador o el DNS ejecuta **root** en la maquina de cada cliente. *Calibracion: no hay
  timer, hace falta que el usuario toque "Actualizar" — pero la app le avisa que hay version
  nueva.* **Analisis y las tres capas del arreglo: PLAN.md §OTA-FIRMA.** Va en 1.9.2.
  *Lo hallo el auditor externo; no estaba en ninguna lista.*

## N — SIGUIENTE (orden estricto)

1. **N1 · T-51 Paddle** — alta y revision. El sitio ya esta listo (T-82/T-83). **Ojo: el alta
   se puede pedir ya, pero NO se cobra hasta cerrar B19.** Arrastra **H11** y **H20**.
2. **N2 · v1.9.2 — la version que habilita cobrar.** Lleva: **B19 (firma del OTA)** ·
   **`paddle-webhook`** (se escribe cuando Paddle apruebe: se limpio el de Stripe a proposito,
   NO es un olvido) · **H23** (el texto de "Temas Pro") · **C9** · **C6** · **H12** · **H19** ·
   **H5** · **H22** · **D6** demo web · pagina de gracias en INGLES (los terminos en ingles ya
   existen: `website/en/terms.html`).
   **Su ciclo de pruebas es el mas grande hasta hoy:** instalacion LIMPIA + OTA +
   desinstalacion completa (TESTING §CICLO 1.9.2).
3. **N3 · T-55** — doc de usuario, con el flujo de compra real.
4. **N4 · PH0 ADOPTADA (31/07): la superficie de verificacion.** Cuatro capas + rama y CI —
   **detalle en PLAN.md §PH0**. Arrancar por las dos primeras: son horas y matan la clase de
   error que ya mordio. **Hoy no hay UN SOLO test automatico.**
5. **N5 · v1.9.3:** una skin **PREVIEW PRO** tomada de `design/skins2`, como anticipo de v2.0.
   Recien ahi vuelve a ser cierto el texto de "Temas Pro" en la app (H23).
6. **N6 · v2.0 NO se empieza hasta ver clientes** (D13): skins Pro + skins de ACCESIBILIDAD +
   soporte multi-distro + voz ampliada.

## HECHO — fase v1.9

**T-46..T-83, todo auditado APTO.** Detalle en `git log`; lecciones en CONTEXT (30/07).
**Los porques de T-70, T-72 y T-79 estan COMENTADOS EN EL CODIGO** — ahi los lee quien
intente "ordenarlo" y revertirlos. No los copies aca.

## D — DECISIONES VIGENTES (no re-litigar)

- **D1 · pagos: PADDLE.** Stripe no opera en Ecuador; PayPal plan B; Ko-fi donaciones.
  Validacion = compra real $5 + refund. **Paddle REVISA el sitio antes de aprobar.**
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
- **D13 · v2.0 NO arranca hasta ver clientes** (31/07); mientras, SOLO 1.9.x. *Por que:* junta
  skins (ingreso), multi-distro (alcance) y voz (retencion), y en un solo release la matriz se
  multiplica; la 1.9.0, mas chica, necesito TRES builds. **Por pistas, skins primero.**
- **D14 · el feedback va a TABLA de Supabase, NO por correo** (31/07). 1/dia **por dispositivo**
  (por IP no: una casa comparte IP) y **server-side**. *Por que:* del mismo dominio que las
  claves, **una queja de spam degrada la entrega de las claves**, de la que depende la venta.
- **D15 · nada de subdominios de correo** (decision del dueño, 31/07): no tiene acceso ni los
  quiere. Si algun dia hace falta aislar reputacion, se crea **otra cuenta de correo**.

## H — HALLAZGOS

**Se mudaron a `BUGS.md`** (31/07), que no tiene techo y registra abiertos y cerrados con su
resolucion. Aca no se duplican: se citan por id.

**Agendados a v1.9.2:** B19 + B19b (firma del OTA) · H23 (el texto de "Temas Pro") · H24 ·
H25 · H19 · H12 · H5 · H22. **Sin fecha:** H21 y los menores. **Con Paddle:** H11, H20.

## C — CHECKLIST DEL DUEÑO

**Se mudo a `USER.md`** (31/07), junto con los comandos y el contrato de quien puede hacer que.
Pendiente ahi: **U1** capa 0 de B19 (2FA y bloqueo del dominio, ~20 min, sin codigo) · **U2**
alta en Paddle · **U3** C9 el correo fuera de spam · **U4** desplegar `send-feedback` ·
**U5** wallpapers.
