# USER.md — acciones exclusivas del dueño

**Dueño:** Agustín (Gusitir), Ecuador.

Este archivo guarda infraestructura, cuentas, gastos y operaciones manuales. Un agente puede
preparar instrucciones y commits, pero no sustituye al dueño en estas acciones.

## CONTRATO

| Solo el dueño | Regla |
|---|---|
| `git push` | Los agentes no pushean. Tampoco añaden `Co-Authored-By`. |
| Supabase desplegado | Solo el dueño ejecuta SQL, despliega o retira Edge Functions y secretos. |
| Cuentas y llaves | Nunca pegar tokens, contraseñas o llaves en chat, brief o repo. |
| DNS, dominio y Vercel | Cambios únicamente con instrucciones verificadas y rollback claro. |
| Patreon | Crear/configurar cuenta, URL, pagos e información fiscal. |
| Dispositivos | Instalación limpia, iPhone, HTPC y hardware de benchmark real. |
| Releases | Aprobar publicación, compatibilidad anunciada y hardware mínimo. |
| Compras | Ningún agente contrata servicios ni gasta dinero. |

Si una tarea depende de una acción de esta tabla, queda **EN CURSO** hasta recibir evidencia.

## PENDIENTE

### U1 — endurecer el origen del OTA

No corrige B19, pero reduce exposición mientras se implementa la firma.

- [ ] 2FA en Vercel.
- [ ] 2FA en Namecheap.
- [ ] Registrar lock y renovación automática del dominio.
- [ ] Revocar tokens de despliegue no usados.
- [ ] Guardar la futura clave privada de firma **offline**, nunca en Vercel/GitHub/Supabase.

### U2 — Patreon

- [ ] Crear o confirmar la página del proyecto/desarrollador.
- [ ] Entregar la URL pública definitiva cuando el sitio esté listo para migrar.
- [ ] Decidir texto de presentación y niveles de apoyo.
- [ ] Confirmar que ningún nivel promete desbloquear funciones de LRP.

### U3 — laboratorio de hardware

- [ ] Elegir al menos una máquina AVX2 modesta y una recomendada.
- [ ] El Q8300 puede usarse como dato exploratorio, pero no como objetivo ni gate.
- [ ] Ejecutar personalmente las pruebas de percepción: ruido de TV, espera, errores y recuperación.

### U4 — corte de servicios para el lanzamiento 2.0.0

Solo después de que PH23 sea APTO y siguiendo el brief de PH24:

- [ ] Retirar/desplegar cambios de Supabase según el brief auditado.
- [ ] Revocar llaves de Together y otros proveedores que ya no se necesiten.
- [ ] Retirar los servicios Supabase de keys, licencias, activaciones y proxy de IA.
- [ ] Cancelar o cerrar Paddle si se creó alguna cuenta/configuración.
- [ ] Verificar que no queden cobros, webhooks ni datos de clientes pendientes.
- [ ] Confirmar el corte después de desplegar la web 2.0; no apagar antes los servicios que
  todavía necesite la 1.9.1 durante la transición.

### U5 — soporte por correo

`support@linuxremoteplayer.com` seguirá siendo soporte aunque ya no entregue licencias.

- [ ] Probar un mensaje realista; no asunto/cuerpo `test`.
- [ ] Verificar SPF y DKIM en “Mostrar original”.
- [ ] Añadir DMARC inicialmente con `p=none` si falta.
- [ ] No crear dos registros SPF ni subdominios de correo.

## COMANDOS RECURRENTES

```bash
git push origin main
```

Verificar que un HTPC representa el paquete instalado:

```bash
sudo dpkg -V linuxremoteplayer
```

Desplegar una Edge Function — solo cuando un brief futuro lo ordene:

```bash
supabase functions deploy <nombre> --no-verify-jwt
```

## DATOS FIJOS

- Dominio: `https://www.linuxremoteplayer.com`
- Alias legado: `linux-remote-player.vercel.app` — mantener mientras versiones antiguas lo usen.
- Correo: `support@linuxremoteplayer.com`
- Repo: `github.com/Gusitir/LinuxRemotePlayer`, privado.
- Estado publicado 1.9.1: Together + Supabase siguen activos en el código hasta PH24.
