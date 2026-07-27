# CONTEXT — handoff entre sesiones
<!-- APPEND-ONLY arriba. Politica de rotacion (AGENTS.md §FORMATO): la sesion mas
     reciente va completa; las anteriores se comprimen a <=4 lineas dejando SOLO
     decisiones vigentes y lecciones de proceso. Lo operativo del dia vive en CURRENT.md;
     el detalle esta en git log. Techo del archivo: ~8KB. -->

## 2026-07-27 · Claude Opus 5 — 1.8.9 publicada, dominio propio, codigo de v1.9.0 cerrado

**Lo que se publico:** el release 1.8.9 estaba construido y auditado desde el 24 pero
**nunca se habia pusheado**. Se reunieron los dos clones divergidos (T-60) y quedo LIVE.
Eso cerro B3 (la voz estaba muerta para toda instalacion nueva: el 1.8.0 publicado llamaba
a Together con llaves revocadas). El dominio `www.linuxremoteplayer.com` ya sirve el sitio.

**Tareas auditadas APTO:** T-60 push del release · T-61 dominio + `support@` en la web ·
T-62 skins liberadas (implementa D4) · T-63 doc de FastAPI oculta (cierra H9) · T-64
`apt remove` limpia de verdad (arregla B2 en codigo) · T-65 URLs de maquina al dominio.
**Con eso el CODIGO de v1.9.0 esta completo**; lo que falta para el release no es codigo.

**Lo que NO esta verificado y es lo mas peligroso que hay abierto:** T-64 toca el `prerm`
del `.deb`. Si el guard `$1 = "remove"` fallara, **cada actualizacion OTA borraria las
reglas del sistema y liberaria la licencia de todos los dispositivos**. No se puede probar
sin un Debian real → **TESTING §E, E1 primero**.

**Lecciones de proceso (las tres ya estan en AGENTS.md):**
1. *Un push sin el bloque STOP no es una entrega.* T-64 —el cambio mas riesgoso— se
   commiteo y pusheo sin una linea de evidencia. Se descubrio solo porque el push de la
   tarea siguiente arrancaba en un hash desconocido. **El auditor arranca siempre por
   `git log <ultimo-auditado>..origin/main`, no por el reporte.**
2. *Los numeros de un brief salen de un comando corrido, no de la memoria ni de un .md.*
   Fallaron tres veces el mismo dia: un conteo de `isLicensed` (eran 4, no 3), un
   `grep "set -e"` que matcheaba el comentario del propio archivo y habria reprobado codigo
   correcto, y una nota de CURRENT que afirmaba que `uninstall.sh` no viajaba en el `.deb`
   cuando si viaja. Los numeros de linea ademas se mueven con cada tarea.
3. *Hay defectos que ninguna verificacion de sintaxis caza.* `lrp-cleanup.sh` se commiteo
   sin bit de ejecucion: perfecto para `bash -n`, y silenciosamente rompia el desinstalador
   manual mientras el camino del `.deb` seguia bien porque `build_deb.sh` le hace `chmod`.

**Decisiones nuevas:** las URLs de maquina se migraron al dominio propio **pero el alias
`vercel.app` no se apaga NUNCA** — los equipos con 1.8.x lo tienen grabado en su codigo.
`LRP_DEV` en vez de `LRP_MODE` para la doc de FastAPI (`desktop` es un modo de usuario
real, no de desarrollo). La web sigue vendiendo los temas como Pro a proposito: esas 6
lineas se corrigen **el dia del release**, no antes, o mentiria al reves para quien tiene
1.8.9 (CURRENT §N2). Nace **PH20**, la demo interactiva del sitio, con dos reglas duras:
etiqueta de simulacion visible y cero red.

**Regla nueva de licencias (AGENTS.md §CÓDIGO DE TERCEROS):** aparecio `Techlm77/LinuxPlay`
(GPL-2.0). No es competencia —ellos hacen streaming de escritorio, LRP no transmite video—
pero su codigo no entra al contexto de ningun agente. **El porque es propio de este
proyecto: como casi todo lo escribio una IA, si un agente lee copyleft y produce algo
parecido, no queda nadie que pueda declarar que no hubo derivacion.** Analisis en
PLAN.md §MERCADO.

**Abierto al cerrar:** B1 (el buzon `support@` todavia no recibia; el dueño agrego los DNS
del Webmail y falta repetir la prueba de C8) · B2 pendiente de TESTING §E · H11 (link de
Stripe TEST en `.env.example`) · H12 (el numero de version que muestra la app sale del
backend y la interfaz del cache del SW: pueden discrepar. Bajado de prioridad — el 1.8.9
raro del device era un build de prueba de una sesion que nunca se anoto. *Leccion: si se
toca el device, se anota, o reaparece meses despues como un bug fantasma*).

## 2026-07-24 (b) · Claude Opus 5 — documentacion humana + skill como paquete

Nacen `docs/ARCHITECTURE.md` y `docs/DEVELOPING.md`, verificados contra el codigo.
**Leccion:** `APPCORE.md` es un indice para agentes y vive donde ningun humano mira, asi
que un colaborador contratado no tenia nada — y pesa mas aca que en un proyecto normal:
cuando la mayoria del codigo lo escribio una IA, NADIE tiene el diseño en la cabeza. Un
colaborador humano es un TERCER ROL bajo el mismo contrato que los agentes.
**Formato:** se sigue en Markdown, NO se migra a HTML (GitHub no lo renderiza desde el
repo, es impuesto de tokens y ensucia los diffs; los grafos ya salen con Mermaid).
**Skill aparte** (`markdawnproyectstructure`, repo propio): el flujo es LIVE -> repo, nunca
al reves; correr su install.sh sobrescribiria la version LIVE.

## Sesiones anteriores (comprimidas)

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
