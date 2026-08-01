# CONTEXT — handoff entre sesiones
<!-- APPEND-ONLY arriba. Politica de rotacion (AGENTS.md §FORMATO): la sesion mas
     reciente va completa; las anteriores se comprimen a <=4 lineas dejando SOLO
     decisiones vigentes y lecciones de proceso. Lo operativo del dia vive en CURRENT.md;
     el detalle esta en git log. Techo del archivo: ~8KB. -->

## 2026-07-31 · Claude Opus 5 — auditoria externa: aparece B19 y cambia el plan

**Lo que hay que saber al entrar: NO SE COBRA hasta cerrar B19.** El alta en Paddle se puede
pedir ya (el sitio esta listo), pero la primera venta espera a la 1.9.2.

**Se lanzo un auditor externo** (Opus 5, sin contexto de la sesion, solo lectura) y **valio la
pena**: encontro tres cosas que no estaban en ninguna lista. La grave es **B19 — el OTA da
root sin firma**: `lrp-update` corre como root y verifica el `.deb` contra un sha256 que sale
del MISMO origen, o sea que detecta corrupcion pero no hostilidad. Quien tome Vercel, el
registrador o el DNS ejecuta root en la maquina de cada cliente. *Calibracion propia sobre su
reporte: dijo "desatendido" y verifique que **no hay timer ni cron**; hace falta que el usuario
toque "Actualizar" — pero la app le avisa que hay version nueva.* Plan en **PLAN §OTA-FIRMA**.
Tambien H23 (la app promete "Temas Pro" que no existen y **contradice los terminos
publicados**), H24 y H25. Todo en **BUGS.md**.

**Dos archivos nuevos, por decision del dueño.** **`USER.md`**: lo que solo puede hacer el
dueño —infra, cuentas, comandos— y el contrato de quien hace que ("solo yo pusheo, solo yo
escribo en Supabase"). **`BUGS.md`**: registro de bugs abiertos y cerrados con su resolucion,
**sin techo**, arrancando desde 1.9.x. *Efecto lateral que importa:* §H y §C salieron de
CURRENT, que bajo de 9703 a 6446 y volvio a entrar en su techo sin perder un solo porque.
**Regla implicita: los registros no se duplican, se citan por id.**

**Plan de versiones nuevo:** **1.9.2 es la que habilita cobrar** (firma del OTA +
`paddle-webhook` + las correcciones) · **1.9.3** skin PREVIEW PRO, y recien ahi vuelve a ser
cierto el texto de "Temas Pro" · **v2.0** skins Pro, accesibilidad, multi-distro, Voz 2.0 y
**registrar la app en un repositorio APT firmado**, que ademas resuelve B19 con maquinaria
estandar. **PH0 ADOPTADA**: hoy no hay un solo test automatico.

**T-82 y T-83** dejaron el sitio listo para Paddle (no se tocaba desde 1.8.0): capturas reales
de 1.9.1, changelog al dia, terminos de venta en los dos idiomas, y **fuera la promesa de
"video de demostracion en camino"** — el video se cancelo. El README decia que el control
basico es **open source**: no lo es, es source-available bajo Elastic 2.0.

**Limpieza a fondo de `.agents`,** con hallazgos que valen como leccion: los **diez conteos de
lineas de APPCORE estaban mal**, y dos archivos distintos declaraban el mismo numero — o sea
que se copio en vez de medirse. PLAN afirmaba que `bootstrap.sh` esta roto cuando ya se habia
borrado, y que el repo "se privatiza" cuando ya era privado.

**Tres errores propios, que valen mas que los aciertos:**
1. Declare un **404 en vivo** en el boton de descarga que no existia: **WebFetch no ejecuta
   JavaScript**, asi que vi el fallback estatico. *Para verificar una pagina con JS, navegador.*
2. Corregi diez conteos de APPCORE y **se me escapo un undecimo**, porque el regex exigia el
   parentesis pegado. Peor: **verifique con un grep con la misma forma que el arreglo**, asi
   que me confirmo solo lo que ya habia cambiado. *Un check moldeado sobre el propio fix no
   verifica nada.* Lo encontro el auditor.
3. El primer auditor **murio sin entregar informe** por quedarse sin presupuesto. El segundo
   llevo instruccion explicita: si te queda poco margen, para y escribi con lo que tengas.

## Sesiones anteriores (comprimidas)

- **2026-07-30 (b) · cierra la fase v1.9: se publico 1.9.1 y quedo certificada en device.**
  **Cambio de contrato:** Gemini ya no commitea ni pushea (entrega arbol sucio), Claude audita
  y commitea, el push es del dueño. **La leccion mas cara:** el ciclo de 1.9.0 dio 6/6 con B1
  en verde sobre un equipo **parcheado a mano** por el agente de pruebas, que no declaro haber
  editado el producto; se detecto abriendo el `.deb`. De ahi el campo obligatorio del reporte y
  **TESTING §M3**. **Vigente:** un config LOCAL que funciona puede tapar un global que no
  existe (credenciales de WSL); el detalle de B1 y B18 esta en BUGS.md.
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
de inferencia local.
