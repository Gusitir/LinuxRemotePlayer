# PH21 — laboratorio STT local

```yaml
fase: PH21
release: 2.0.0
owner: Arquitecto
ejecucion: un Ingeniero Codex de fase
estado: ABIERTA — G0 aprobado; G1-G3 a cargo del Ingeniero
producto: no integrar STT al backend en esta fase
```

## OBJETIVO

Elegir con evidencia el runtime, modelo/perfil y hardware mínimo para transcribir órdenes LRP
en español e inglés localmente. PH21 produce un laboratorio reproducible y una decisión; no
modifica todavía el pipeline de producción 1.9.1.

## ALCANCE

- Inventariar CPU/instrucciones, memoria, SO y runtimes de cada máquina medida.
- Auditar licencias y redistribución del runtime y de cada peso exacto.
- Construir un corpus versionado de intención/texto y un formato para audios de prueba.
- Crear un harness reproducible que mida calidad, latencia fría/caliente, RAM y CPU.
- Evaluar como mínimo Whisper multilingüe `base` y `small` cuantizados con `whisper.cpp`.
- Evaluar sherpa-onnx solo si puede ejecutar un candidato comparable sin contaminar la matriz.
- Registrar fallos con silencio, ruido de TV, nombres propios y comandos fuera de dominio.
- Recomendar modelo por defecto, perfil ligero opcional o justificar un único perfil.
- Proponer hardware mínimo y recomendado a partir de resultados, no de marketing.

## FUERA DE ALCANCE

- Integrar STT en `backend/main.py` o retirar Together/Supabase.
- Implementar Needle 2, acciones, SQLite, CDP/BiDi o UI final.
- Descargar modelos durante instalación del producto.
- Publicar requisitos de hardware en README/web.
- Soportar el Q8300 como gate. Puede medirse solo como dato exploratorio.
- Introducir modelos/pesos al `.deb` de producción.

## CANDIDATOS OBLIGATORIOS

1. Whisper `base` multilingüe, cuantización elegida y registrada por el Ingeniero.
2. Whisper `small` multilingüe, la misma política de cuantización cuando exista.

SenseVoice-Small está descartado: no soporta español. Parakeet multilingüe puede figurar como
comparación opcional, nunca desplazar los dos candidatos obligatorios sin decisión del Arquitecto.

## CONTRATO DEL CORPUS

El corpus debe tener un manifiesto UTF-8 versionado con IDs estables y, por caso:

- idioma y locale;
- texto esperado normalizado;
- clase: playback, volume, app, search, navigation, negative;
- slots relevantes;
- condición: limpia, TV de fondo, lejana, silencio u otra declarada;
- hablante/dispositivo con alias anónimo, nunca nombre personal;
- archivo de audio relativo y checksum;
- permiso/origen del audio.

Conjunto mínimo de textos: 60 casos únicos —30 ES y 30 EN— equilibrados entre clases, incluidos
10 negativos por idioma. Los audios humanos reales no se commitean hasta decidir licencia,
privacidad y tamaño; el harness debe aceptar una carpeta externa gitignored.

La métrica primaria no es WER aislado: es **exactitud de texto/slots suficiente para que PH22
elija la intención correcta**. Conservar además WER/CER para diagnóstico.

## MÉTRICAS REQUERIDAS

- Identidad exacta: runtime/commit o versión, modelo, checksum y cuantización.
- Hardware: CPU, flags SIMD, núcleos/hilos, RAM, SO y backend de cómputo.
- Latencia end-to-end por archivo, p50/p95; separar primera inferencia y caliente.
- Real-time factor por duración de audio.
- RSS inicial y máximo; CPU máxima/promedio cuando la plataforma lo permita.
- WER/CER, exactitud de frase normalizada y exactitud de slots.
- Falsos positivos en silencio/ruido y alucinaciones observadas.
- Tamaño en disco del runtime y pesos.

## GATES

### G0 — fase lista — APTO

Objetivo, candidatos, corpus, métricas, límites y entregables definidos en este archivo.

### G1 — plan de tareas del Ingeniero

Antes de lanzar Obreros, el Ingeniero entrega en `.work/PH21/phase-task-plan.md`:

- tareas ordenadas con write-set disjunto o secuencial;
- comando exacto de cada verificación;
- dependencias/licencias a revisar;
- política de descarga y caché de modelos fuera de Git;
- smoke test real de `agy.exe` en modo no mutante.

### G2 — tarea

Cada Obrero entrega STOP; el Ingeniero repite pruebas, audita diff y hace un commit selectivo.

### G3 — integración de fase

- Harness corre desde clon/worktree limpio sin rutas personales codificadas.
- Resultados contienen todos los metadatos exigidos y son reproducibles.
- Ambos candidatos obligatorios tienen la misma matriz válida.
- Fallos y resultados ausentes no se convierten en cero ni se ocultan.
- Suite existente de LRP no empeora; esta fase no altera producto runtime.
- Informe `phase-report.md` recomienda o declara que la evidencia no alcanza.

### G4 — auditoría del Arquitecto

El Arquitecto revisa commits, licencias, reproducibilidad, comparabilidad y una muestra de datos;
repite el harness en una muestra cuando el entorno lo permita. Solo entonces fija el STT de PH23.

## UMBRALES DE DECISIÓN

No se inventa un porcentaje absoluto antes de escuchar el corpus. La fase usa una regla comparativa:

- cero aceptación de alucinaciones peligrosas en silencio dentro de la muestra medida;
- p95 caliente menor que la duración del audio en hardware mínimo candidato;
- ninguna clase crítica con exactitud de slots inferior al promedio por más de 10 puntos;
- si `base` y `small` quedan dentro de 2 puntos de exactitud de slots, gana el menor consumo;
- si ningún candidato cumple, PH21 termina NO APTO y propone ampliar candidatos/hardware.

Estos umbrales pueden endurecerse tras el primer piloto, pero no relajarse para declarar ganador
sin una decisión registrada por el Arquitecto.

## ENTREGABLES DE LA RAMA

- Harness y pruebas automatizadas bajo un directorio de laboratorio que el Ingeniero definirá
  siguiendo patrones reales del repo.
- Corpus textual/manifiesto sin datos privados.
- Instrucciones reproducibles sin secretos ni rutas personales.
- Resultados estructurados por máquina/modelo; binarios, pesos y audios externos gitignored.
- Informe de fase efímero en `.work/PH21/phase-report.md`.
- Commits de tarea atómicos, sin cambios de producción no autorizados.

## INFORMACIÓN QUE REQUIERE AL DUEÑO — NO BLOQUEA EL ARRANQUE

- Grabar/proporcionar audios humanos ES/EN cuando el harness esté listo.
- Ejecutar el benchmark en el HTPC objetivo siguiendo un brief sin ayuda interpretativa.
- Confirmar la máquina AVX2 que representará el mínimo candidato.

El Ingeniero puede completar inventario, licencias, corpus textual, harness y piloto en la máquina
disponible antes de esas acciones.
