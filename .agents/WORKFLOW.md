# WORKFLOW — extensión subordinada a agents-workflow v3

`AGENTS.md` es la autoridad. CAVEMAN aplica siempre: sin saludos ni relleno; salida breve, técnica,
factual y accionable.

## ROLES

- Arquitecto: posee INIT, PLAN, diseño y CLOSE; aprueba alcance, arquitectura, riesgos y gates; no
  escribe producto.
- INGENIERO-CONTROL: ejecuta jobs de control autorizados y escribe `.agents` dentro de su scope.
- INGENIERO-PRODUCTO: coordina tareas, repite gates y audita el plano de producto; no implementa
  producto directamente.
- Worker: implementa producto en el write-set autorizado y entrega evidencia; no cambia arquitectura,
  `.agents`, commits ni push.
- Dos Ingenieros persistentes: `gpt-5.6 LUNA` con esfuerzo `MAX`. TERRA y SOL están prohibidos.
- Cada Ingeniero puede solicitar 2 Workers `LUNA-MAX`; máximo global 4; slots autorizados por el
  Arquitecto. El Arquitecto puede usar hasta 2 Workers `DeepSeek V4 Flash High` para fixes diminutos
  posteriores a auditoría que no escriba él mismo.

## GATES

1. Arquitecto fija spec, write-set, riesgos y G0.
2. Ingeniero prepara tareas, checks, rollback y G1; solicita slots.
3. Worker implementa y entrega STOP con archivos, comandos, evidencia, no verificado y desvíos.
4. Ingeniero repite checks, audita diff y alcance, integra y entrega informe.
5. Arquitecto decide G4; dueño hace push y despliegue.

Assurance: `Standard`. G0 fase lista, G1 tarea lista, G2 tarea apta, G3 integración, G4 fase apta.
