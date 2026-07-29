# CONTEXT — handoff entre sesiones
<!-- APPEND-ONLY arriba. Politica de rotacion (AGENTS.md §FORMATO): la sesion mas
     reciente va completa; las anteriores se comprimen a <=4 lineas dejando SOLO
     decisiones vigentes y lecciones de proceso. Lo operativo del dia vive en CURRENT.md;
     el detalle esta en git log. Techo del archivo: ~8KB. -->

## 2026-07-28 · Claude Opus 5 — correo real, pulido pre-Paddle, revision de la skill

**Arranca aca el chat nuevo.** El codigo de v1.9.0 esta COMPLETO y auditado (T-60..T-66).
No falta programar: falta **construir el .deb y correr la matriz de TESTING**, que sigue
sin ejecutarse desde que se publico 1.8.9.

**T-66 (APTO)** cerro tres cosas de golpe: el nombre del producto estaba **invertido**
("Remote Linux Player") en 8 lugares incluido el `<title>` y el manifest, `gracias.html`
publicaba el **gmail personal** del dueño, y sobrevivian 13 reglas CSS muertas. Se descubrio
al preparar C5: **las capturas para Paddle iban a fotografiar el nombre mal**. De ahi la
regla de orden: *pulir → release → capturas → Paddle*, nunca al reves.

**La saga del correo, que valio por tres lecciones.** La web publicaba `support@` desde
T-61 y el buzon NO EXISTIA (rebote `554 Relay access denied`). El dueño migro del reenvio
gratuito a un buzon real (Namecheap Private Email, MX `mx1/mx2.privateemail.com`), pero al
migrar **se perdio el SPF** y el dominio quedo sin ningun TXT. Los envios rebotaban con
`550-5.7.26` de Gmail. Se cargaron SPF+DKIM+DMARC y se verificaron contra 8.8.8.8 y 1.1.1.1.
**El segundo rebote, ya con el DNS puesto, fue cache negativa**: Gmail habia guardado "este
dominio no tiene SPF" de la consulta anterior. Falta solo reintentar (C8/C9).
- *Leccion 1:* publicar una direccion no prueba que exista un buzon, y que el buzon exista
  no prueba que lo que mande llegue. **Un item se cierra con el efecto verificado.**
- *Leccion 2:* en el panel de Namecheap, MAIL SETTINGS (los MX) y HOST RECORDS (los TXT) son
  bloques SEPARADOS. El desplegable es excluyente solo entre formas de configurar MX.
- *Leccion 3:* cuando entre Resend (T-51), su include va en el **MISMO** registro SPF. Dos
  registros SPF fallan en ambos y ahi se pierde el correo de licencias.

**Icono en iOS (TESTING B2), diagnosticado sin poder cerrarlo.** iOS **ignora los iconos del
`manifest.json`**: solo lee `<link rel="apple-touch-icon">`. El archivo del repo es correcto
(PNG 180x180, **sin canal alfa**, etiqueta presente) y los 12 assets del precache existen.
Si igual sale la letra, el sospechoso es el **certificado autofirmado**: aceptar la
advertencia de Safari sirve para navegar, pero la descarga del icono no hereda esa excepcion.
Hay que instalar la CA **y activar la confianza total** (Ajustes → General → Informacion →
Ajustes de confianza del certificado), y recien ahi borrar y re-agregar la PWA.

**Skin `agents-workflow` revisada (repo aparte, NO se implemento nada).** Crecio a 45KB y
**todas sus war stories son de este proyecto**. Veredicto para LRP:
- **Adoptar:** la *verification surface* de PH0 — UN comando que corre todos los gates y sale
  distinto de cero. Hoy los gates estan desperdigados (`check_css_sync.py` dentro de
  `build_deb.sh`; `py_compile`/`node --check`/`bash -n` escritos A MANO en cada brief), y esa
  redaccion manual ya produjo un check erroneo. Es la mejora con mejor retorno.
- **Adoptar, cuesta cero:** las 5 preguntas del dueño y el checklist de integridad de release
  (sus 8 items son agujeros que este proyecto ya tuvo) → al hito T-56.
- **NO adoptar ahora:** la ejecucion delegada (el auditor invocando al ejecutor por CLI).
  Exige la verification surface como precondicion dura, y sobre todo **multiplica las
  entregas sin multiplicar la matriz de test** — que es justo el cuello de botella real de
  LRP hoy. Aceleraria lo que ya no damos abasto para verificar.

**Decision pendiente del dueño:** `manifest.json` `short_name` quedo en `"RemoteLinux"`, una
tercera variante del nombre. Recomendacion: **`"LRP"`** (D2). Se aplica en T-56.

## Sesiones anteriores (comprimidas)

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
