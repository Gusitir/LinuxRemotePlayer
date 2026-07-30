# CONTEXT — handoff entre sesiones
<!-- APPEND-ONLY arriba. Politica de rotacion (AGENTS.md §FORMATO): la sesion mas
     reciente va completa; las anteriores se comprimen a <=4 lineas dejando SOLO
     decisiones vigentes y lecciones de proceso. Lo operativo del dia vive en CURRENT.md;
     el detalle esta en git log. Techo del archivo: ~8KB. -->

## 2026-07-30 · Claude Opus 5 — el ciclo de correcciones cerro; no quedan bloqueantes tecnicos

**Arranca aca el chat nuevo.** `.agents` quedo limpio a proposito para esto: se archivo todo
lo cerrado y CURRENT bajo de 18.6KB a 8.3KB.

**Lo que paso, en una linea:** se sacaron TRES builds de prueba (1.8.10, 1.8.11, 1.8.12)
antes de la comercial, y **esa decision del dueño salvo el lanzamiento**.

**Por que.** El primer build de prueba destapo que **cada actualizacion dejaba el servicio
MUERTO**. El actualizador llama a `apt-get install`, y el paquete **reescribe ese mismo
archivo mientras corre**; bash lee por posicion de byte, retomaba en el archivo nuevo a mitad
de palabra y moria antes del `systemctl restart`. Si 1.8.10 hubiera sido el lanzamiento,
**cada comprador habria perdido el control remoto en su primera actualizacion**, y solo se
recuperaba por SSH. Se arreglo envolviendo el script en funciones (bash lo parsea entero
antes de ejecutar) con `main "$@"; exit $?` en la MISMA linea.
*El porque completo esta comentado en el codigo, no lo repitas en los .md.*

**El fix no podia probarse solo:** el equipo usaba el actualizador roto para instalar su
propia correccion, asi que hicieron falta dos builds mas. **Cerro verde el 30/07.**

**Auditadas APTO en esta sesion:** T-67 instalador · T-68 voz automatica + enlace de compra ·
T-70 el OTA ya no mata el servicio · T-71 voz al arrancar + cadena de certificados · T-72 CA
con nombre unico · T-73 nombres y `.env` · T-75 apt remove borra claves y CA del sistema ·
T-69/T-74/T-76 los tres builds de prueba.

**Lecciones de proceso — las tres ya son reglas en AGENTS.md:**
1. *Un guard en un brief vale lo que cuesta escribirlo.* El paso 0 de un release paro a
   Gemini cuando su requisito no estaba mergeado, y evito publicar un build a medias.
2. *Auditar reproduciendo, no leyendo.* El bug del actualizador se confirmo simulando un
   script que se reescribe a si mismo: el patron viejo **se detiene en silencio y devuelve
   exit 0**. Leer el diff nunca habria mostrado eso.
3. *Un plan de fase que deja de reflejar la realidad se archiva.* `PLAN_v1.9.md` termino con
   18 tareas abiertas y 0 cerradas mientras 30 estaban hechas: el estado real vivia en
   CURRENT. Arrastrarlo era peor que no tenerlo.

**Errores propios que valen mas que los aciertos:**
- Se dio B12 por cerrado creyendo que el `PAIRING_TOKEN` vivia en el `.env`. **Vive en
  `.pairing_token`**, asi que la credencial seguia en disco tras desinstalar. Lo destapo el
  agente del HTPC.
- Se diagnostico el error de certificado como "falta la cadena". Era otra cosa: al
  desinstalar se **destruia la CA** y al reinstalar nacia otra con **el mismo nombre**; el
  navegador tenia el dato viejo, no le faltaba uno. Mandar la cadena no lo arreglaba.
- Un brief acoto una busqueda a dos carpetas y dejo el nombre invertido en `scripts/` y en
  **el correo que recibe el cliente con su clave**.

**El agente del HTPC (DeepSeek via opencode) funciono muy bien:** declaro sus excepciones en
vez de ocultarlas, marco como contaminada una prueba propia en lugar de darla por buena, y
construyo un retest mejor que el del guion. Sus instrucciones estan en
`TESTING_HTPC_AGENT.md`, autocontenidas.

**Estado al cerrar:** falta **B1** (el HUD se corre en iPhone, decidido arreglarlo en 1.9.0)
y el log del actualizador → **T-77**. Despues **T-56, el release 1.9.0**, que es el savepoint
del proyecto y absorbe las 6 lineas de la web que aun venden los temas como Pro. Luego
privatizar (PLAN.md §T-57) y lo comercial: correo, capturas, Paddle.

## Sesiones anteriores (comprimidas)

- **2026-07-28 · dominio, correo y pulido pre-Paddle.** T-66 corrigio el nombre del producto,
  que estaba INVERTIDO en 8 lugares — se descubrio al preparar las capturas para Paddle, que
  lo iban a fotografiar. De ahi la regla de orden: *pulir → release → capturas → Paddle*.
  **Saga del correo, tres lecciones:** publicar una direccion no prueba que exista un buzon,
  y que el buzon exista no prueba que lo que mande llegue; en Namecheap los MX y los TXT son
  bloques SEPARADOS; y cuando entre Resend su include va en el MISMO registro SPF — dos
  registros fallan en ambos. **iOS ignora los iconos del manifest**: solo lee
  `apple-touch-icon`, y necesita PNG sin canal alfa.
  **Skill `agents-workflow` revisada (repo aparte, sin implementar):** adoptar la superficie
  de verificacion de PH0 (un comando = todos los gates); NO adoptar la ejecucion delegada,
  porque multiplica las entregas sin multiplicar la matriz de test, que es el cuello real.

- **2026-07-27 · se publico 1.8.9 y se cerro el codigo de v1.9.0** (T-60..T-65). Llevaba tres
  dias construido y auditado **sin pushear**, con dos clones divergidos. **Vigente:** el alias
  `vercel.app` **no se apaga nunca** (los 1.8.x lo tienen grabado); `LRP_DEV` y no `LRP_MODE`
  para la doc de FastAPI. Nace PH20. Las lecciones del dia estan en **AGENTS.md** (§CICLO,
  §FORMATO y §CÓDIGO DE TERCEROS), que es donde se aplican.
- **2026-07-24 (b) · documentacion para humanos.** Nacen `docs/ARCHITECTURE.md` y
  `docs/DEVELOPING.md`. **Leccion:** `APPCORE.md` es un indice de agentes y vive donde ningun
  humano mira; cuando la mayoria del codigo lo escribio una IA, NADIE tiene el diseño en la
  cabeza, asi que un colaborador humano es un TERCER ROL bajo el mismo contrato.
  **Formato:** se sigue en Markdown, NO se migra a HTML. **Skill** (repo aparte): el flujo es
  LIVE -> repo, nunca al reves; correr su install.sh pisaria la version LIVE.

- **2026-07-24 · identidad visual + release 1.8.9 + spec Skins 2.0.** T-58 alineo las skins
  con la paleta del sitio y rehizo el logo. **Leccion tecnica que sigue viva:** el marcado
  historico asume fondo OSCURO, asi que la skin clara lo rompia; se resolvio con un bloque
  PUENTE en `skins.css` — toda clase neutra nueva hay que puentearla o el tema claro se
  rompe otra vez. **Lecciones de auditoria (ya en AGENTS.md):** auditar REFERENCIAS y no
  solo comportamiento (la web seguia publicitando los temas viejos); la doc y el marketing
  entran en el radio de impacto (asi salio B2); y verificar en un motor no es verificar
  (`<symbol>` bajo `display:none` rompe `<use>` en WebKit y la PWA corre en Safari iOS) —
  lo que no se puede probar sin hardware se DECLARA y va a TESTING.
  PH17 (Theme Packs, v1.9.1) especificada: NO son paletas, cambian que botones existen y
  donde; `data-layout` separado de `data-skin` para que la matriz de QA no explote.

- **2026-07-20 · v1.7.8 + fase v1.8.** v1.7.8 aceptada por el dueño como "vendible". Fase
  v1.8 (limpieza pre-lanzamiento) CERRADA: T-32 auditoria de secretos (0 fugas en 145
  commits), T-33 purga IA legacy, T-34..T-37 limpieza, T-40/T-41 README+web factuales,
  T-45 release 1.8.0 LIVE y validado en device. T-39 (partir main.py) DIFERIDO.
  **Leccion del dueño:** NO borrar AGENTS.md ni CONTEXT.md; el README a actualizar es el
  de la RAIZ (GitHub), no uno dentro de .agents.
- **2026-07-17..20 · ciclo v1.7.1..v1.7.7.** Testing intensivo triado → 29 tareas y 8
  releases verificadas en vivo. Sagas cerradas: OTA (cgroup suicide / prerm / gate),
  voz end-to-end, PWA auto-actualizable (SW versionado por build), viewport iOS.
  Stack de voz ratificado: whisper-large-v3 + Qwen2.5-7B-Turbo (Together).
  **Incidentes de proceso → reglas:** falso NO APTO por auditar el working tree mientras
  el ejecutor editaba (→ auditar COMMITS tras el STOP, regla 11); 3 veces se reporto
  evidencia sin correr el comando (→ el auditor re-ejecuta siempre). El guard CSS cazo su
  primera deriva real. Nacio la skill global `agents-workflow` + el contrato de archivos.
- **2026-07-17 · reanudacion.** v1.7.0 (Firefox) publicada. Se elimino el TESTING.md de la
  raiz (obsoleto: Chromium + git clone) y nacio `.agents/TESTING.md`. Planes cerrados →
  `archive/`. Se identifico ai-proxy como el bloqueante de la venta de voz.
- **2026-07-13 · planificacion.** Auditoria del v1.5 contra git; nacio el formato
  "Gemini programa / Claude planifica y audita" con criterios de aceptacion por tarea.

## INIT · 2026-06-24
PC con Linux controlada por una PWA movil via WebSocket. La IA pesada va a la nube; nada
de inferencia local. Repo inicializado, scaffolding fase 1.
