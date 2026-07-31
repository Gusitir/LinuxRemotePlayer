# CONTEXT — handoff entre sesiones
<!-- APPEND-ONLY arriba. Politica de rotacion (AGENTS.md §FORMATO): la sesion mas
     reciente va completa; las anteriores se comprimen a <=4 lineas dejando SOLO
     decisiones vigentes y lecciones de proceso. Lo operativo del dia vive en CURRENT.md;
     el detalle esta en git log. Techo del archivo: ~8KB. -->

## 2026-07-30 (b) · Claude Opus 5 — la fase v1.9 CIERRA: 1.9.1 publicada y certificada

**Se termino la ingenieria del lanzamiento.** Lo unico pendiente para vender es Paddle.

**Cambio de contrato (decision del dueño):** **Gemini ya no commitea ni pushea.** Edita
codigo y para en STOP con el arbol sucio; **Claude audita y commitea**; **el push es del
dueño, a mano**. Unica excepcion: el commit del release, que lleva el `.deb` y sale del clon
WSL. Eso obligo a reemplazar el ancla de auditoria: antes se auditaban COMMITS
(`git log <hash>..origin/main`), ahora se audita el **arbol**, y por eso el dueño confirma el
STOP antes de que el auditor mire — auditar un arbol que el ejecutor sigue tocando ya produjo
un falso NO APTO. Lo que sobrevive de la regla vieja: **nunca se arranca por lo que dice el
reporte**. *El ejecutor paso a Gemini 3.6 Flash.*

**El hallazgo mas caro del dia, y la razon de que exista TESTING §M3.** El ciclo de pruebas
de 1.9.0 dio 6/6 con B1 ✅ en los dos iPhone. **Era falso.** El agente del HTPC habia
encontrado la causa real de B1 —`viewport-fit=cover`, no la altura que re-leia T-77—, la
**aplico al equipo** y anoto la solucion, pero **no declaro que habia editado el producto**.
El auditor lo cazo **abriendo el `.deb` publicado** en vez de creerle al reporte: el atributo
seguia ahi. *El arreglo era bueno; lo que faltaba era una linea diciendo que existia.*
**Consecuencias permanentes:** el formato del reporte tiene ahora un campo OBLIGATORIO
("¿tocaste algun archivo del producto? SI/NO" + `dpkg -V`), y la matriz tiene **M3**, que
verifica con `dpkg -V` que el equipo ES el paquete **antes** de que la prueba de iPhone
cuente. Sin eso, un ✅ miente sin que nadie mienta.

**Correccion de un analisis del agente que quedaba en el registro:** atribuyo que B18 no se
disparara a que el log de `/tmp` era de root. Es al reves — el backend corre como usuario
normal (`User=$TARGET_USER`) y abria en modo append, que exige ESCRITURA; si fuera de root
habria fallado. **B18 solo dispara si el archivo YA existe y no es escribible por el usuario
del servicio**, o sea si alguien corrio `sudo lrp-update` a mano antes de T-77. **En una
instalacion nueva nunca habria fallado: ningun comprador lo habria visto.**

**Repo PRIVADO, T-57 cerrado entero.** (a) Vercel siguio desplegando. (b) *La trampa:* el
`credential.helper` existia solo en el config **LOCAL** de `~/lrp-release`, con el global
vacio — el clon viejo funcionaba y tapaba el problema, mientras que el clon **fresco** que
manda el paso 2 del release fallaba con `could not read Username`. Se puso el helper en el
global de WSL (reusa el GCM de Windows, sin secretos nuevos) y se verifico **reproduciendo un
`git clone` fresco**. *Leccion: un config local que funciona puede tapar un global que no
existe.* (c) murio `bootstrap.sh` — y al auditarlo aparecio que **se venia empaquetando en el
`.deb`** y vivia en el equipo de cada usuario.

**Los dos archivos de testing se fusionaron en uno.** Tenian el mismo id (`L5`) significando
cosas distintas: es la regla de "un dato, un archivo" materializandose. Ahora los comandos
viven SOLO en el §BLOQUE PARA EL AGENTE, que se le entrega tal cual porque ese agente no lee
el repo. El reporte del ciclo va FUERA de ese bloque: adentro, el ciclo siguiente le
entregaria los resultados del anterior como si fueran su guion.

**T-82 y T-83 dejaron el sitio listo para Paddle** (no se tocaba desde 1.8.0). Se saco la
promesa de "video de demostracion en camino" —cancelado, la demo va a 1.9.2— y nacieron los
terminos de venta. El README decia que el control basico es **open source**: no lo es, es
source-available bajo Elastic 2.0. *Metodologico:* **WebFetch no ejecuta JavaScript**, asi
que mostro un fallback estatico y me hizo declarar un 404 en vivo que no existia — para
verificar una pagina con JS, navegador.

**PARA EL SUPERVISOR — AGENTS.md sigue fuera de techo (13923 vs 12288).** Se hizo la poda
MECANICA (redundancia, sin tocar reglas) y quedo declarado en su cabecera. Lo que falta es un
juicio que el auditor no deberia tomar solo, porque es sobre el proceso del que forma parte:
**decidir que reglas ya no cambian conducta.** Candidatas que dejo marcadas, sin borrar:
- §CICLO paso 2, el parentesis que explica el ancla VIEJA (`git log <hash>..origin/main`).
  Es arqueologia de una regla que ya no existe; sobrevive solo la frase que importa.
- §ENTORNO, `py_compile` / `node --check` con python de Windows, y la nota de
  `is_newer_version`: **ambas se vuelven redundantes cuando aterrice PH0** (capa 1 y capa 2
  las convierten en un comando y en un test). Borrar DESPUES de que exista `verify.sh`.
- §CICLO paso 5 (registrar una T-NN en su plan de fase): los planes de fase estan archivados
  y el estado vive en CURRENT; verificar si todavia le cambia la vida a alguien.

## Sesiones anteriores (comprimidas)

- **2026-07-30 (a) · el ciclo de correcciones cerro y se publico 1.9.0.** Tres builds de
  prueba antes de la comercial **salvaron el lanzamiento**: el primero destapo que cada
  actualizacion dejaba el servicio MUERTO (el paquete reescribia el script mientras corria;
  bash lee por posicion de byte). Se arreglo envolviendolo en funciones. **Vigente:** el
  `PAIRING_TOKEN` vive en `.pairing_token`, NO en el `.env`; y una CA reinstalada con el
  mismo nombre confunde al navegador — no era falta de cadena.
- **2026-07-28 · dominio, correo y pulido pre-Paddle.** T-66 corrigio el nombre del producto,
  INVERTIDO en 8 lugares. De ahi el orden: *pulir → release → capturas → Paddle*. Publicar
  una direccion no prueba que exista buzon, y que el buzon exista no prueba que lo que mande
  llegue. **iOS ignora los iconos del manifest**: solo lee `apple-touch-icon`, PNG sin alfa.
- **2026-07-27 · se publico 1.8.9 y se cerro el codigo de v1.9.0.** Llevaba tres dias
  construido y auditado **sin pushear**, con dos clones divergidos. **Vigente:** el alias
  `vercel.app` **no se apaga nunca** (los 1.8.x lo tienen grabado); `LRP_DEV` y no `LRP_MODE`.
- **2026-07-24 (b) · documentacion para humanos.** Nacen `docs/ARCHITECTURE.md` y
  `docs/DEVELOPING.md`. **Leccion:** cuando la mayoria del codigo lo escribio una IA, NADIE
  tiene el diseño en la cabeza; un colaborador humano es un TERCER ROL bajo el mismo contrato.
- **2026-07-24 · identidad visual + spec Skins 2.0.** **Vigente:** el marcado historico asume
  fondo OSCURO — hay un bloque PUENTE en `skins.css` y **toda clase neutra nueva hay que
  puentearla** o el tema claro se rompe. Verificar en un motor no es verificar (`<symbol>`
  bajo `display:none` rompe `<use>` en WebKit, y la PWA corre en Safari iOS). PH17: NO son
  paletas, cambian que botones existen y donde.
- **2026-07-20 · v1.7.8 + fase v1.8.** Limpieza pre-lanzamiento cerrada: T-32 auditoria de
  secretos (0 fugas en 145 commits), purga de IA legacy, README+web factuales, 1.8.0 LIVE.
  T-39 (partir `main.py`) DIFERIDO. **Leccion del dueño:** el README a actualizar es el de la
  RAIZ (GitHub), no uno dentro de `.agents`.
- **2026-07-17..20 · ciclo v1.7.1..v1.7.7.** 29 tareas y 8 releases verificadas en vivo.
  Sagas cerradas: OTA, voz end-to-end, PWA auto-actualizable, viewport iOS. Stack de voz
  ratificado: whisper-large-v3 + Qwen2.5-7B-Turbo (Together). **Incidentes → reglas:** falso
  NO APTO por auditar mientras el ejecutor editaba; 3 veces se reporto evidencia sin correr
  el comando (→ el auditor re-ejecuta SIEMPRE). Nacio el contrato de archivos `.agents`.
- **2026-07-13 · planificacion.** Nacio el formato "Gemini programa / Claude planifica y
  audita" con criterios de aceptacion por tarea.

## INIT · 2026-06-24
PC con Linux controlada por una PWA movil via WebSocket. La IA pesada va a la nube; nada
de inferencia local. Repo inicializado, scaffolding fase 1.
