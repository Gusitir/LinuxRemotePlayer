---
name: reindex
description: Audita y actualiza el índice del código (.agents/APPCORE.md) contra el repo REAL. Invocar tras cada release o cuando una búsqueda revele que APPCORE está desactualizado.
---

# `reindex` — mantenimiento del índice de código (APPCORE.md)

**Qué es APPCORE.md**: el mapa curado del proyecto (archivos críticos, endpoints y sus
gates de auth, protocolo WS, pipeline de venta). Ahorra miles de tokens de búsqueda —
PERO solo si dice la verdad. Esta skill lo re-sincroniza con la realidad.

**Cuándo invocar**: (a) después de cada release; (b) si al usar APPCORE encontraste
una entrada que ya no coincide con el código; (c) antes de planear un milestone grande.

**Protocolo** (verificar contra el repo real, no de memoria):

1. **Endpoints**: `grep -n "@app\.\(get\|post\)" backend/main.py` y comparar con la
   lista de APPCORE (ruta + gate require_token/require_local/require_local_or_token).
   Añadir faltantes, borrar muertos, corregir gates.
2. **Archivos críticos**: para cada archivo listado en APPCORE, confirmar que existe y
   que su descripción de 1-3 líneas sigue siendo cierta (funciones clave, flags .env).
   Archivos nuevos importantes (backend/, frontend/, scripts/) -> añadirlos.
3. **Protocolo WS**: comparar los `msg_type`/acciones del handler de websocket en
   main.py con la sección WS de APPCORE.
4. **Config**: variables de backend/.env.example vs las mencionadas en APPCORE.
5. **Reglas de edición**: entradas CORTAS (1-3 líneas por archivo, estilo actual);
   APPCORE es un mapa, no documentación; NUNCA pegar código; NUNCA inventar — si no se
   verificó con grep/lectura, no se escribe.
6. Al terminar: anotar en CURRENT.md "APPCORE re-sincronizado [fecha] (N cambios)".

**Costo estimado**: ~5-10k tokens por corrida (greps + lectura dirigida). Se recupera
en la primera búsqueda que el índice evita.
