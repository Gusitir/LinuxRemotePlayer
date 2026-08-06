# USER.md — lo que SOLO puede hacer el dueño

<!-- Este archivo existe para sacar del chat los comandos y las credenciales de acceso.
     Si una tarea necesita una cuenta, una tarjeta, un telefono o una decision comercial,
     vive ACA y ningun agente la ejecuta. Sin techo de tamaño. -->

**Dueño: Agustín (Gusitir), Ecuador.**

---

## CONTRATO — quien puede hacer que

Esto no es burocracia: cada linea nacio de un incidente real.

| Solo el dueño | Por que |
|---|---|
| **`git push`** | Ningun agente pushea. El auditor commitea; el push es un acto deliberado del dueño. |
| **Escribir en Supabase** — desplegar Edge Functions, correr SQL, tocar tablas | Editarlas en el repo **NO las despliega**. Un agente que "arregla" una funcion en el repo cree haber resuelto algo que sigue roto en produccion. |
| **Las llaves de proveedores** (Together, Supabase, Resend, Paddle) | Viven en el entorno de Supabase y en el `.env` del HTPC. **Nunca en el repo, nunca en el chat, nunca en un brief.** |
| **DNS y dominio** (Namecheap) | Un registro mal puesto tumba el correo de licencias o el sitio entero. |
| **Cuenta de Vercel** | Es el canal OTA. Quien la controla, controla lo que se instala en cada cliente (ver BUGS §B19). |
| **Probar en device** — iPhone, HTPC, instalacion limpia | Ningun agente ve la advertencia del certificado ni espera el PIN en la TV. |
| **Aprobar releases y precios** | Decision comercial. |
| **Comprar cualquier cosa** | Ningun agente gasta plata. |

**Corolario para los agentes:** si una tarea depende de algo de esta tabla, **no se marca como cerrada** — queda EN CURSO con puntero acá. (AGENTS §CICLO regla 4.)

---

## PENDIENTE AHORA

### U1 · Capa 0 de B19 — endurecer el origen  ⏱️ ~20 min · **SIN CODIGO**
Es lo mas barato que existe contra el riesgo mas grave abierto. No arregla el diseño; baja la
probabilidad a casi cero mientras llega la firma en 1.9.2.

- [ ] **2FA en Vercel.**
- [ ] **2FA en el registrador del dominio** (Namecheap).
- [ ] **Bloqueo de transferencia** del dominio (*registrar lock*).
- [ ] **Renovacion automatica** del dominio activada.
- [ ] **Borrar tokens de despliegue de Vercel** que no se usen.

> El dominio vencido o la cuenta tomada = root en la maquina de cada cliente. Ver BUGS §B19.

### U2 · Alta en Paddle (T-51)
- [ ] Crear cuenta, dar de alta el producto **$5 pago unico**.
- [ ] Pasar la revision del sitio. **Ya esta listo:** dominio propio, capturas de 1.9.1,
      terminos en los dos idiomas, precio claro y politica de reembolso publicada.
- [ ] Cuando aprueben: pasar la **URL real de checkout** → reemplaza `PLACEHOLDER-PADDLE`.
- [ ] Compra real de $5 + refund, de punta a punta.

> **NO cobrarle a nadie hasta cerrar B19.** El alta y la revision se pueden pedir ya; la
> primera venta espera a que la 1.9.2 firme el OTA.

### U2b · Plugin de Paddle para Claude Code — **NO INSTALADO** (intento fallido 31/07)
Se intento y **NO se pudo**: el cliente respondio `"/plugin isn't available in this
environment"`. **No asumas que existe tooling de Paddle.**

```
/plugin marketplace add anthropics/claude-plugins-community
/plugin install paddle@claude-community
```

> Se escriben en el **PROMPT de Claude Code**, no en la terminal — ningun agente puede
> ejecutarlos. En esta superficie el comando no existe; **reintentar desde una sesion
> interactiva de `claude` en terminal**, que es donde suele estar disponible.

**Si algun dia queda activo, para el agente que tome T-51:** verifica que expone ANTES de
asumir capacidades. **Precaucion:** el marketplace lo hospeda Anthropic pero **los plugins son
de la comunidad**, y este proyecto maneja webhooks de pago y claves de licencia — revisarlo
antes de darle credenciales reales (§CONTRATO: las llaves son del dueño, nunca del chat).

### U3 · C9 — sacar `support@` de spam  (a 1.9.2)
- [ ] **Repetir la prueba primero.** La que detecto el problema tenia asunto `test` y cuerpo
      `test`: eso ya es patron de spam. Probar con un correo realista (asunto tipo "Tu clave
      de LinuxRemotePlayer", saludo, clave, enlace al dominio, firma).
- [ ] Ver "Mostrar original" en Gmail: **SPF y DKIM en PASS**.
- [ ] **Agregar DMARC** — probablemente es lo que falta. Empezar con `p=none`.
- [ ] Medir con **mail-tester.com**.

> **Trampa:** cuando entre Resend, su `include` va en el **MISMO** registro SPF. Dos registros
> SPF fallan en ambos y ahi se pierde el correo que lleva la clave al cliente.
> **Descartado (D15):** subdominios. Si hace falta aislar, se crea otra cuenta de correo.

### U4 · Desplegar `send-feedback` (C6)
Pendiente **desde v1.5**: el boton de feedback lleva cuatro versiones muerto y nadie lo noto.

```bash
supabase functions deploy send-feedback --no-verify-jwt
```

> En 1.9.2 cambia de forma: el feedback ira a una **tabla**, no a correo (CURRENT §D14).
> Cuando eso se implemente, este deploy se rehace.

### U5 · Wallpapers de las skins nuevas (C3, no bloquea)
- [ ] Para **Gato** y **Perro**: mandar **el TILE** (~400x400), no el pantallazo. Tilear ya
      esta soportado y pesa ~30 KB contra ~170 KB.

---

## COMANDOS QUE USA EL DUEÑO

```bash
git push origin main
```

Release — el clon fresco de WSL (§PROCESO DE RELEASE en AGENTS.md):
```bash
rm -rf ~/lrp-release && git clone https://github.com/Gusitir/LinuxRemotePlayer.git ~/lrp-release
```

Desplegar una Edge Function de Supabase:
```bash
supabase functions deploy <nombre> --no-verify-jwt
```

Diagnostico en el HTPC — verificar que el equipo ES el paquete (TESTING §M3):
```bash
sudo dpkg -V linuxremoteplayer
```

Salida manual si el boton "Actualizar" falla en un equipo aun en 1.9.0:
```bash
sudo rm -f /tmp/lrp-update.log
```

---

## DATOS FIJOS

- **Dominio:** https://www.linuxremoteplayer.com
- **Alias Vercel:** `linux-remote-player.vercel.app` — **VIVO a proposito**: es el canal OTA
  del parque viejo (los 1.8.x lo tienen grabado). **Nunca apagarlo.**
- **Correo:** support@linuxremoteplayer.com
- **Repo:** github.com/Gusitir/LinuxRemotePlayer — **PRIVADO** desde el 30/07.
- **Voz en produccion:** Together AI — `openai/whisper-large-v3` + `Qwen/Qwen2.5-7B-Instruct-Turbo`.
- **Credenciales de WSL:** el `credential.helper` global apunta al GCM de Windows. Sin eso, el
  clon fresco del release se cuelga pidiendo usuario.
