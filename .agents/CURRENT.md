# CURRENT — estado vivo

```yaml
version_publicada: 1.9.1
estado_codigo: estable y certificado en campo; todavía usa nube, licencia y Supabase
vision_aprobada: inferencia 100% local, sin premium ni pagos
version_objetivo: 2.0.0
transicion: toda la nueva visión se entrega junta en 2.0.0; todavía no implementada
fase_activa: preparación del flujo de desarrollo de 2.0.0
repo: privado; main local está 6 commits por delante de origin/main
dominio: https://www.linuxremoteplayer.com
pruebas_publicadas: TESTING.md — ciclo 1.9.1 cerrado 6/6
ultima_actualizacion_docs: 2026-08-11
```

## VERDAD OPERATIVA

Hay dos estados que no deben mezclarse:

1. **LRP 1.9.1 real:** voz por Together/Supabase, licencia Pro, BUY_URL y textos comerciales.
2. **Destino aprobado:** voz e interpretación locales, todas las funciones libres, sin Paddle,
   sin activación y con Patreon únicamente como apoyo voluntario.

Hasta que una tarea auditada cambie el código, la primera descripción sigue siendo la verdad
del producto instalado. Ningún documento de usuario se actualiza como si la migración ya existiera.

## SIGUIENTE

1. El dueño establece el nuevo flujo de trabajo y los roles.
2. Crear una rama/laboratorio separado; `main` conserva 1.9.1 estable.
3. Medir STT local en español e inglés: Whisper multilingüe `base` y `small` cuantizados,
   con `whisper.cpp` como primera referencia y sherpa-onnx como alternativa.
4. Validar Needle 2 en Linux x86-64: runtime, licencia, memoria, latencia, confianza y precisión
   con un corpus propio de órdenes LRP.
5. Elegir hardware mínimo a partir de evidencia; candidato provisional: x86-64 + AVX2.
6. Diseñar la migración sin nube y recién entonces trocearla en tareas.
7. Corregir B19 dentro de 2.0.0 antes de publicarla: el OTA actual sigue sin firma.
8. Rediseñar la web ES/EN para 2.0.0 y retirar Paddle/Pro/licencias en el mismo lanzamiento.
9. Retirar los servicios Supabase de keys, validación y proxy de IA antes de publicar 2.0.0.

## DECISIONES VIGENTES

- **D16 — local-first:** audio, STT, interpretación, historial y acciones permanecen en el HTPC.
- **D17 — sin premium:** no habrá funciones bloqueadas, licencias, cuotas comerciales ni compras.
- **D18 — financiación:** Patreon será apoyo voluntario y nunca desbloqueará funciones.
- **D19 — seguridad:** ningún modelo obtiene Bash, sudo ni comandos libres. Solo emite acciones
  declaradas; Python valida esquema, confianza, permisos y contexto antes de ejecutar.
- **D20 — idioma:** el STT inicial debe funcionar en español; inglés también forma parte del
  producto objetivo. SenseVoice-Small queda descartado porque no soporta español.
- **D21 — hardware:** se abandona el Core2Quad Q8300 como objetivo. El mínimo definitivo sale
  de benchmarks, no de una generación o cifra imaginada.
- **D22 — dos productos:** LRP seguirá instalable en distribuciones Linux. La imagen HTPC sobre
  Debian será un proyecto hermano posterior, no el laboratorio de la voz local.
- **D23 — estabilidad:** no se elimina la nube de 1.9.1 antes de demostrar que el pipeline local
  iguala el flujo actual en precisión, latencia y recuperación ante fallos.
- **D24 — datos:** sin telemetría remota obligatoria. Historial y diagnósticos serán locales;
  cualquier exportación futura requerirá una acción explícita del usuario.
- **D25 — versión:** la nueva arquitectura completa se publica como **2.0.0**. No habrá una
  release intermedia que anuncie la nueva visión con piezas cloud/comerciales todavía activas.
- **D26 — corte coordinado:** web, aplicación, documentación y servicios Supabase de
  keys/licencias/IA cambian juntos al lanzar 2.0.0. Hasta entonces, 1.9.1 permanece factual.

## BLOQUEANTES Y RIESGOS

- **B19:** el actualizador instala como root y confía en un hash servido por el mismo origen.
  La gratuidad no reduce el riesgo. Ver BUGS.md y PLAN §GATE-OTA.
- **A1:** aún no existe benchmark del pipeline completo en hardware objetivo.
- **A2:** Needle 2 es muy nuevo; sus métricas publicadas por el autor no sustituyen pruebas LRP.
- **A3:** automatizar sitios mediante CDP/BiDi es frágil y expone sesiones si el puerto sale de
  localhost. MPRIS y acciones deterministas tienen prioridad.
- **A4:** la distribución y actualización de modelos añade tamaño, compatibilidad y licencias.

## NO HACER TODAVÍA

- No borrar Paddle, Supabase, Together, licencias ni términos del código por partes.
- No prometer públicamente “100% local” antes de una release que lo cumpla.
- No elegir un modelo por una tabla de Gemini o por benchmarks de otro hardware.
- No comenzar la ISO antes de validar modo dedicado, motor local y actualización firmada.
- No leer `design/` ni convertir IDEAS en tareas sin decisión expresa del dueño.
