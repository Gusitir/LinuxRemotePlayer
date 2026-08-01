# IDEAS.md — pensamiento de diseño, NADA decidido

<!-- QUE ES: el espacio para pensar el producto sin comprometer versiones. Nace de una
     conversacion del 31/07/26 entre el dueño y Claude Opus 5.

     QUE NO ES: un plan. Nada de aca esta agendado, ni entra en CURRENT, ni en PLAN, ni
     genera tareas. **La app HOY esta bien como esta** — esto es explorar posibilidades.

     LA REGLA QUE LO MANTIENE SANO: cuando una idea se DECIDE, se muda a PLAN.md con fecha
     y **se borra de aca**. Si vive en los dos lados, uno se va a quedar viejo (AGENTS
     §FORMATO). Este archivo solo contiene lo que sigue SIN decidir.

     SIN TECHO de tamaño. -->

---

# 1 · Los dos modos: ¿que es de verdad un "modo dedicado"?

## El diagnostico del dueño
Hoy el modo dedicado es **escritorio con permisos**: servicio a nivel sistema en vez de
usuario, panel de inactividad a los 45 s, y `LRP_NOSLEEP` enmascarando la suspension. Nada
mas. Un modo dedicado de verdad deberia **cambiar el comportamiento del entorno**, no solo
los permisos del servicio.

## La taxonomia — la idea mas fuerte de la conversacion
**No hay un solo "modo dedicado", porque no hay un solo tipo de maquina objetivo.**

**(a) Distros que YA son electrodomestico** — Plasma Bigscreen, Batocera, Bazzite, ChimeraOS,
RetroArch. El sistema ya arranca en una interfaz de TV y ya esta acotado. **El trabajo pesado
lo hizo la distro**; LRP se integra, no bloquea.

**(b) Escritorios con una sesion de TV** — Mint y compañia: una sesion normal para trabajar y
otra "modo TV". Aca LRP **aporta su propia sesion**.

## Sesion propia > modificar el escritorio del usuario
Idea del dueño, y es arquitectonicamente superior a lo que se habia propuesto antes
(restringir el escritorio existente con el framework Kiosk de KDE). Por que:
- No toca la configuracion del escritorio diario de nadie.
- **La salida de emergencia viene incorporada:** cerrar sesion y entrar a la normal.
- Desinstalar = borrar una entrada de sesion, no revertir veinte ajustes del sistema.
- Se puede bloquear todo lo que se quiera **porque la sesion es propia**.

Convierte "modificar el comportamiento de la distro" —fragil y especifico de cada entorno— en
**"ofrecer un entorno propio"**, que es limpio y portable.

## La pantalla del televisor: INFORMATIVA, no interactiva
Como la interaccion vive en el telefono, la pantalla no necesita ser navegable. **Ahorra
construir una interfaz de TV entera**, que es donde se hunden estos proyectos. El panel de
inactividad que ya existe es el germen de esto.

## El principio de diseño que salio (y ordena todo lo demas)
> **Guiar sin guiar.** Una buena decision de diseño no necesita ocultar opciones: lleva al
> usuario a las que le convienen, sin castigar al que sabe lo que hace.

Formulado por el dueño. **Prohibir es la salida perezosa**; guiar es la cara.

## Tension real, sin resolver
**Un power user necesita atajos de teclado y acceso a comandos.** Eso empuja en direccion
contraria a esconder. Cualquier diseño tiene que servir a los dos usuarios **sin dos productos
distintos**.

## El HUD diferenciado
Los dos modos quieren cosas opuestas en un lugar donde hoy hay una sola. Ejemplo concreto: en
**T-25 se saco el filtro de categorias de `discovery.py`** a proposito, porque el power user
queria ver Dolphin y Konsole. **En modo dedicado se quiere justo lo contrario.** Mismo codigo,
dos politicas.

Boceto: *dedicado* pone adelante las apps de streaming y la reproduccion, y entierra "añadir
app web" y "apps del sistema" detras de un gesto deliberado. *Escritorio* pone adelante el
touchpad y el teclado.

> **Correccion del dueño, anotada porque cambia el encuadre:** que esto sea tecnicamente
> accesible NO lo convierte en "algo barato para hacer ya". **Es una decision de diseño y se
> lanza COMPLETA**, no como atajo. Claude lo habia planteado como la version reducida y
> barata; el dueño lo corrigio, con razon.

## LO QUE SIGUE SIN DECIDIR
**¿Separar los dos modos agresivamente, o solo rediseñar el HUD para delimitar suavemente al
usuario objetivo?** Sin resolver, y a proposito.

## Restricciones que cualquier version tiene que respetar
1. **La salida de emergencia se diseña ANTES que el bloqueo.** Si el usuario pierde el control
   y algo se rompe, no tiene teclado util ni terminal. *Precedente propio:* cuando el
   actualizador dejaba el servicio muerto, la unica recuperacion era por SSH. (La sesion
   aparte resuelve esto casi solo.)
2. **Todo lo que se toca hay que destocarlo.** Es donde viven los bugs de este proyecto:
   `lrp-cleanup.sh` existe porque desinstalar dejaba basura.
3. **Sube las apuestas de la confiabilidad.** Hoy, si LRP falla, el usuario tiene una
   computadora que funciona. En modo dedicado tiene **un ladrillo con una tele conectada**.

## Dato de campo del dueño
En un HTPC, el teclado y el mouse se usan **para instalar**, y despues se prescinde de ellos
en un ~95% — salvo emergencias. **El diseño deberia asumir ese ciclo de vida:** se necesitan al
principio, estorban despues, y tienen que volver a estar disponibles cuando algo falla.

## Aclaracion tecnica que resolvio una duda
**Firefox kiosk y el framework Kiosk de KDE NO compiten: son capas distintas.** KDE restringe
el *escritorio* (abrir terminal, cerrar sesion, editar iconos); Firefox corre la *aplicacion*
a pantalla completa. **La eleccion de Firefox fue correcta y no se revisa:** dio compatibilidad,
bloqueador de anuncios y sobre todo **acceso al DOM para controlar apps por voz**, que es
funcionalidad de producto. KDE Kiosk nunca habria dado eso.

---

# 2 · ¿Portar a Windows?

**Disparador real:** el dueño compartio la app en un grupo de Facebook y **le preguntaron por
Windows**. Nunca lo habia considerado: son entornos de uso distintos. Su lectura: la
competencia en Windows **lo hace mal** — el es cliente de ese tipo de apps y ninguna le
resolvia lo que necesitaba, hasta que hizo la suya.

**Veredicto de la conversacion: viable, NO urgente. Se considera si los clientes lo piden.**

**Se porta gratis:** la PWA entera (~1583 lineas de `app.js`, no le importa que hay del otro
lado), el protocolo WS, el ruteo de FastAPI, la autenticacion, el emparejamiento, `ai_pipeline`,
el `ai-proxy`, la licencia, Paddle y el sitio. Es una porcion enorme del valor acumulado.

**Hay que reescribir casi todo lo que toca la maquina:** `input_emulator` (`uinput` → `SendInput`;
**ahi Windows es MAS facil**: sin grupo `input`, sin udev, sin reboot) · `discovery` (`.desktop`
→ accesos del Menu Inicio y apps de la Store) · `kiosk` (manejo de ventanas Win32) · `audio`
(Core Audio) · el servicio · la CA local · el firewall.

**Y lo mas caro, que no se ve:** el `.deb`, `install.sh`, `uninstall.sh`, `lrp-cleanup.sh`,
`lrp-update`, `postinst`, `prerm` y el canal OTA entero. **Cada leccion que costo un ciclo de
pruebas** —el actualizador que se reescribia a si mismo, el `prerm` que solo limpia en
`remove`, la CA que colisionaba— **no sirve en Windows**. Esperan sus equivalentes, todas nuevas.

**La objecion que no es tecnica:** la tesis de producto se debilita. Todo lo que vende LRP es
*"el problema no es armar el HTPC, es que despues nadie mas en la casa sabe usarlo"*. En Windows
ese dolor es mas chico y hay competidores establecidos hace una decada. Se pasa de **ser la
mejor opcion de un nicho desatendido** a **una opcion mas en un mercado saturado**.

**Alternativa mas rentable por peso: multi-distro.** Reutiliza todo menos el empaquetado
(`uinput`, `.desktop`, systemd y PipeWire son los mismos en Fedora o Arch), ya esta en v2.0, y
aprovecha el laboratorio de VMs que ya se queria montar.

---

# 3 · OTA a prueba de fallos

**Meta del dueño:** un OTA 100% antifallos.

**Reencuadre propuesto, porque el objetivo original no es alcanzable y este es mejor:** no "que
nunca falle", sino **"que nunca deje la maquina peor que antes"**. Atomicidad y reversion, no
perfeccion.

Mecanismo concreto: guardar el paquete anterior · verificar la **salud del servicio** despues
de actualizar · **si no levanta en N segundos, reinstalar el anterior solo**. El `trap` que ya
reinicia pase lo que pase es una version primitiva de esa idea.

*Pista:* la familia de Bazzite —que el dueño nombro por otro motivo— usa **actualizaciones
transaccionales con reversion**. Es el modelo a mirar.

**Requisito que el dueño puso, y es el correcto:** esto no se logra con parches sueltos.
Necesita un sistema de desarrollo integro — **gates, pruebas en rama, y `main` solo para
produccion probada**. Eso ya empezo: PH0 quedo adoptada.

---

# 4 · Posicionamiento

**El modo dedicado de verdad es probablemente el mejor diferenciador comercial**, porque es
exactamente lo que las apps de control remoto NO hacen: ellas asumen que hay alguien manejando
una computadora. LRP estaria vendiendo **"convertí esa PC en un electrodomestico"**.

Si algun dia se justifica subir el precio, va a ser por ahi — **no por mas botones**.
