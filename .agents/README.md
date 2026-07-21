# .agents — memoria de proyecto para IA

**EMPEZÁ ACÁ (sesión nueva, en orden):**
1. [`WORKFLOW.md`](WORKFLOW.md) — cómo trabajamos (roles, ciclo por tarea, entorno, release). **Estable.**
2. [`CURRENT.md`](CURRENT.md) — dónde estamos AHORA (versión, tarea activa, pendientes). **Cambia seguido.**

Con esos dos ya sabés todo. Después, según necesites:

| Archivo | Qué es |
|---|---|
| `PLAN.md` | Roadmap de alto nivel (milestones, v1.9 en adelante). |
| `PLAN_v1.8.md` | Plan maestro de la fase ACTIVA (limpieza/optimización pre-v1.9). |
| `APPCORE.md` | Mapa del código: rutas, endpoints, archivos clave, protocolo WS. |
| `TESTING.md` | Matriz de test intensivo (la corre el dueño en device + teléfono). |
| `AUDITS/` | Auditorías pesadas de versiones grandes (una por hito). |
| `archive/` | Planes/briefs de tareas ya cerradas. Referencia, NO resucitar. |
| `skills/manage_context/` | Skill `reindex` para re-sincronizar APPCORE contra el repo real. |

**Regla:** nunca escribir en estos .md lo no verificado. Tras cada release o si el índice
miente, re-sincronizar contra el repo REAL (grep de rutas/endpoints) y anotar la fecha.
