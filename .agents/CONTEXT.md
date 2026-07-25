# CONTEXT — handoff entre sesiones
<!-- APPEND-ONLY arriba. Politica de rotacion (AGENTS.md §FORMATO): la sesion mas
     reciente va completa; las anteriores se comprimen a <=4 lineas dejando SOLO
     decisiones vigentes y lecciones de proceso. Lo operativo del dia vive en CURRENT.md;
     el detalle esta en git log. Techo del archivo: ~8KB. -->

## 2026-07-24 · Claude Opus 5 — identidad visual, release 1.8.9, spec Skins 2.0

**T-58** skins de la app alineadas 1:1 con la paleta del sitio: day (clara) por defecto y
gratis, night, cafe, anime; ids viejos migran en `setSkin()` (free `dark`→`day` SIN toast,
Pro `dark`/`neon`→`night`). Logo rehecho ("Touchpad"), `icon.svg` + 6 PNG de app y web;
`scripts/dev/generate_png_icons.py` reescrito y con su `ROOT_DIR` arreglado (roto desde T-35).

**Leccion tecnica reusable:** el marcado historico asumia fondo OSCURO, asi que la skin
clara lo rompia. Se resolvio con un bloque PUENTE en `skins.css` que reasigna las
utilidades neutras de tailwind-lite a variables de skin. Toda clase neutra nueva hay que
puentearla o el tema claro se rompe de nuevo.

**Lecciones de auditoria (las 3 se incorporaron a AGENTS.md y a la skill):**
1. *Auditar comportamiento no alcanza: hay que auditar REFERENCIAS.* Verifique que las
   skins funcionaban, el dueño pregunto por referencias, y aparecio que la web publicitaba
   los temas viejos "Dark, Day, Neon" en ES y EN.
2. *La doc y el marketing son parte del radio de impacto.* Verificando un item de TESTING
   salio que `apt remove` solo para el servicio mientras `docs.html` promete 4 cosas
   (ver CURRENT §B2).
3. *Verificar en un motor no es verificar.* Cace un riesgo propio: `<symbol>` bajo
   `display:none` rompe `<use>` en WebKit y la PWA corre en Safari iOS. Lo que no se puede
   verificar sin hardware se DECLARA y va a TESTING, no se da por bueno.

**T-59 release 1.8.9** — Gemini ejecuto, Claude auditó APTO contra el .deb REAL via WSL
(cuadruple match de sha256, contenido identico al arbol del commit, y se verifico QUE
archivos toca el commit, no solo que exista). Commiteada en el clon WSL, SIN PUSHEAR.

**Decisiones del dueño:** las 7 skins van GRATIS como gancho (el Pro se vendera con skins
adicionales en v2.0); roster Day/Night/Cafe/Cozy(ex-anime)/Cyberpunk/Gato/Perro con
etiqueta "Accesibilidad" en las 2 ultimas; Voz 2.0 repriorizada a v2.0. Dominio aplazado.

**PH17 (Theme Packs) especificada** para v1.9.1 con los 4 mockups en `.agents/design/skins2/`.
Clave: NO son paletas — cambian posicion de botones, cuales existen, y agregan etiquetas de
texto que no estan en el DOM. Diseño: `data-layout` independiente de `data-skin`, cada skin
fijada a un layout para que la matriz de QA quede en N. Criticas aceptadas: el D-Pad SE QUEDA
en el layout accesible (para quien no controla un puntero es mas facil que un cursor libre);
"INICIO" se saca porque es `killKiosk()` y mata la app en curso; el engranaje se queda (sin
el, el usuario queda atrapado); "Edgerunners" no se usa (marca de CD Projekt/Trigger).

**Mantenimiento .agents:** CURRENT compactado 10.2KB→8KB y pasado a esquema con IDs;
TESTING reconstruido para el ciclo 1.8.9 (la matriz v1.7 quedo en archive/); PLAN_v1.8
archivado; APPCORE re-sincronizado; AGENTS.md corregido (apuntaba a PLAN_v1.8 como fase
activa) + §FORMATO nueva.

## Sesiones anteriores (comprimidas)

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
