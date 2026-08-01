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

# 4 · ISO propia con LRP preinstalado

**Aclaracion del dueño:** no habla de una distro de cero, sino de **una ISO personalizada
sobre bases existentes**, con lo justo y necesario, apuntada a que **un equipo viejo levante
un HTPC** y no se rompa con cada actualizacion.

## "Hacer una distro" esconde cuatro proyectos distintos
| nivel | que es | esfuerzo | quien mantiene el sistema |
|---|---|---|---|
| 1 | instalador automatizado (preseed de Debian) | dias | Debian |
| 2 | **ISO propia desde una base** (`live-build`, `archiso`) | semanas | el dueño las integraciones |
| 3 | **imagen inmutable, atomica, con reversion** | alto, pero hay frameworks | el dueño la imagen, upstream la base |
| 4 | distro de verdad: paqueteria, repos, kernel | equipo, años | **descartado** |

## La conexion que importa: el nivel 3 responde el problema del OTA
El dueño describio querer *"sin sorpresas, sin actualizaciones que rompan algo"*. **Eso es la
definicion de un sistema por imagenes e inmutable**: raiz de solo lectura, el sistema entero se
actualiza como unidad atomica, y si falla **revierte al reiniciar**. Es lo que hacen SteamOS,
Bazzite y ChimeraOS — que el propio dueño habia nombrado antes sin notar que ya respondian.

**Su idea de ISO y su meta de "OTA a prueba de fallos" (§3) son el MISMO problema con la misma
solucion.** Hay frameworks que construyen imagenes personalizadas sobre bases atomicas
definiendolas casi como un `Containerfile`, con la build en CI; Bazzite empezo asi. **Investigar
esa familia antes de pensar en algo propio.**

## La disyuntiva REAL de la base — hay que elegirla a conciencia
- **Debian** → maxima compatibilidad de hardware, **todavia soporta 32 bits**, ciclos largos,
  base gigante, y ya es su plataforma. **Pero actualizaciones convencionales: sin reversion.**
- **Familia atomica (Fedora Atomic / imagenes tipo uBlue)** → **da la reversion que quiere**,
  pero es **solo 64 bits** y su piso de hardware es mas nuevo.

**No se puede tener las dos cosas.** Maxima compatibilidad con equipos viejos y actualizaciones
atomicas tiran para lados opuestos. Decidir cual duele menos ANTES de construir nada.

## Restricciones tecnicas que ya fijan el terreno
LRP necesita **`uinput`, systemd, PipeWire/Pulse y Firefox**. Eso descarta de entrada Alpine y
similares con musl (rompe supuestos de Python y binarios) y cualquier base sin systemd (Devuan).
Las candidatas serias quedan en la **familia Debian** (incluidas MX, antiX, Q4OS, LMDE) o la
**familia atomica de Fedora**.

## El techo que NO lo pone el sistema operativo
**En un HTPC el cuello de botella suele ser la decodificacion de video, no la CPU.** Una maquina
sin decodificacion por hardware de h264/h265 va a trabarse con 1080p en el navegador **por mas
liviano que sea el sistema**. Un equipo de 2008 puede correr la interfaz de LRP perfecto y aun
asi no reproducir YouTube en 1080p. **Aligerar el sistema tiene un piso que no depende del
sistema.** Probar esto TEMPRANO, con el hardware objetivo real.

## Lo que hay que saber antes de meterse
- **Una ISO es superficie de SOPORTE, no una funcion.** Hoy, si a alguien no le anda el WiFi, el
  problema es de Debian. Con imagen propia, *"no me levanta en mi laptop vieja"* es un ticket
  propio. **Ironia:** el hardware viejo con pocos recursos es justo el de peor soporte de
  drivers. El publico objetivo es el peor caso de soporte.
- **Cambia lo que se vende.** De una app de $5 a proveedor de sistema. La gente espera parches de
  seguridad por años; abandonarlo deja gente con un aparato conectado y sin actualizar.
- **La critica a Plasma Bigscreen es correcta, la conclusion no se sigue.** Es cierto que arrastra
  medio KDE y no es apto para consumo masivo. Pero entre eso y "hago una distro" hay un escalon:
  **una sesion curada sobre una base existente** da el 90% del beneficio sin ser dueño del SO.
- **La comparacion con Firestick es una trampa.** Funciona porque Amazon subsidia hardware y tiene
  acuerdos de contenido. Competir ahi es competir en hardware, retail y contenido. **La ventaja
  propia es la opuesta y es mejor: ellos venden un aparato nuevo, LRP hace util el que ya esta
  tirado.**

## La version sana de la idea
> **Una imagen reproducible y opinada que convierte una PC vieja en un electrodomestico LRP**,
> construida sobre una base existente, con actualizaciones atomicas y reversion.

Encaja con el ecosistema: **LRP-para-cualquier-distro** (la app, que ya existe) y
**LRP-appliance** (la imagen llave en mano). Dos productos, un motor.

## SECUENCIA — importa
**Va DESPUES del modo dedicado (§1), no antes.** La sesion propia es el paso previo natural: si
esa sesion funciona bien sobre una base existente, la imagen es empaquetarla. **Si no funciona,
la imagen no la va a salvar.**

---

## Sesiones, contraseñas y "capar" el sistema

**El autologin es la parte facil.** Un unico usuario sin privilegios, sin sudo (salvo la regla
angosta de `lrp-update` que ya existe), y **el concepto de contraseña desaparece de la vista**.
*Consecuencia a decir en voz alta:* sin contraseña, **acceso fisico = acceso total**, y queda
descartado el cifrado de disco (pediria clave al arrancar). Un Firestick es igual. Es un
intercambio consciente.

**Capas para acotar el daño**, de la que mas rinde a la que menos: (1) **sin sudo** — la que mas
protege: sin escalada, el daño se limita a la carpeta personal · (2) sin terminal al alcance **y
deshabilitar el cambio de terminal virtual** (`Ctrl+Alt+F2`, el agujero que se olvida) ·
(3) **AppArmor**, que Debian ya trae, para acotar Firefox y el backend · (4) **raiz de solo
lectura**, que es *la* propiedad que hace sentir indestructible al AndroidTV.

**Tension:** la capa 4 es justo la que Debian NO da de fabrica (se aproxima con overlay sobre la
raiz, artesanal). Se eligio Debian por el hardware viejo, y la propiedad mas admirada del
AndroidTV viene de la inmutabilidad. **Ese pedazo hay que construirlo a mano en vez de heredarlo.**

**Reencuadre que ordena todo:** la simplicidad del Firestick **no viene de estar capado, viene de
que no hay nada que configurar**. El capado es consecuencia del modelo de producto, no la causa
de la simplicidad. **El objetivo no es quitar capacidades: es que no haga falta verlas nunca** —
"guiar sin guiar" aplicado al sistema operativo.

## Arquitectura: DOS usuarios, no uno
- **Usuario del televisor:** autologin, sin contraseña, sin sudo, sin terminal. Es el que arranca.
- **Usuario dueño:** con contraseña, alcanzable por SSH o terminal virtual. Solo para emergencias.

Da "mi mama no puede romperlo" **y** "el dueño puede arreglarlo" sin contradiccion. **Es la misma
forma que la salida de emergencia por token de emparejamiento: el que sabe tiene una puerta, el
que no sabe ni la ve.**

## MODELO DE AMENAZA — DECIDIDO por el dueño (31/07)
- **Nivel 1 · usuario sin conocimiento que rompe por accidente → SI se defiende.** Es el objetivo.
- **Nivel 2 · alguien con intencion destructiva → NO es responsabilidad del producto.** Tarde o
  temprano lo logra por mas trabas que se pongan; esa prevencion es del dueño del equipo.
- **Nivel 3 · acceso fisico → NO preocupa** (hasta un Firestick cae). **Pero SI preocupa el
  atacante REMOTO o un virus.**

**Consecuencia del nivel 3, y es la que mas manda:** la superficie remota real es **Firefox
navegando la web** en una maquina que emula teclado a nivel kernel, y **el canal de
actualizacion** — que es literalmente B19. *Un aparato que vive años en una sala con un
navegador sin parchear es exactamente como te comprometen de forma remota.* Esto **choca de
frente con la idea de "ISO versionada sin OTA"** (ver abajo).

---

# 5 · ISO: esfuerzo, desafios y como se actualiza

## El esfuerzo real, con calibracion honesta
El dueño pidio no pensar en tiempos de desarrollo humano porque se usan herramientas con IA.
**Justo: la IA comprime la parte MAS CHICA de este trabajo.** Un proyecto de ISO casi no es
escribir codigo; es **integracion, arranque y hardware**: grabar USB, bootear, observar, corregir
— ciclos que requieren **una persona frente a la maquina** y no se paralelizan.

*Precedente propio:* el bug del actualizador necesito **tres builds de prueba** y un humano en el
HTPC. Una ISO tiene MAS de eso, no menos.

**Forma realista del esfuerzo:**
- **Primera ISO booteable con LRP preinstalado:** rapido, dias con `live-build`. **Es la parte
  engañosa: el primer 80% sale volando.**
- **Autologin + sesion dedicada + cero teclado despues de instalar:** mas, pero tratable.
- **Que ande en hardware que no tenes:** *la cola larga, y no termina nunca.*

## Desafios concretos
1. **Instalar EXIGE teclado y mouse, y no se puede evitar.** No se particiona un disco desde el
   telefono. *Pero encaja con la observacion de campo del propio dueño:* se necesitan al
   instalar y despues estorban. **Aceptarlo en vez de pelearlo.** Se minimiza con un instalador
   automatizado (preseed) que tome el disco entero sin preguntas.
2. **Nunca borrar un disco en silencio.** Hace falta UNA confirmacion explicita, si o si.
3. **Secure Boot:** una ISO propia con modulos propios puede no arrancar donde este activado.
   Irrelevante en el Q8300 (pre-UEFI), relevante en maquinas mas nuevas.
4. **Firmware no libre**, sobre todo WiFi. Los instaladores actuales de Debian ya lo incluyen,
   lo que resuelve la mayor parte.
5. **Obligaciones de redistribucion.** Distribuir una ISO derivada de Debian **es distribuir
   binarios GPL**: aparecen obligaciones de disponibilidad de fuentes. Para paquetes sin
   modificar, apuntar a los repos de Debian suele alcanzar; **si se MODIFICA un paquete GPL, hay
   que publicar su fuente.** LRP sigue siendo Elastic 2.0 como paquete aparte — **agregar no es
   derivar** —, pero la obligacion existe y hay que conocerla (AGENTS §CÓDIGO DE TERCEROS).
6. **Peso y hosting.** Una ISO son ~1-2 GB. **Vercel no sirve para eso.** Hace falta hosting real,
   espejos o torrent. Es infraestructura nueva y costo recurrente.

## ACTUALIZACION: el voto del dueño (ISO versionada SIN OTA) tiene un problema
**No son alternativas: responden preguntas distintas.**
- **ISO versionada = como se OBTIENE el sistema la primera vez.** Correcto, y va.
- **OTA = como se mantiene al dia una maquina YA instalada.**

**Si fuera solo ISO:** cada actualizacion exige presencia fisica, un USB y reinstalar → **nadie
actualiza jamas** → Firefox sin parchear durante años en la sala → **que es exactamente el
nivel 3 que el dueño dijo que SI le preocupa**. Y ademas LRP perderia el canal para arreglar lo
que ya construyo.

**Propuesta: TRES NIVELES, y el mas importante NO tiene boton.**

| que | como | quien lo ve |
|---|---|---|
| **Seguridad del sistema** | automatico, silencioso, en segundo plano (`unattended-upgrades` limitado al repo de SEGURIDAD) | **nadie** |
| **LRP** | el boton que ya existe, con la firma de B19 puesta | el usuario, si quiere |
| **Salto de version de Debian** | nunca automatico, nunca desde el boton | solo con ISO nueva |

**La propiedad Firestick no viene de que el boton haga todo: viene de que no hace falta boton.**
El usuario nunca se entera de que su navegador se parcho anoche. Y el nivel 1 es literalmente lo
que el dueño pidio —"actualizaciones estables de sistema criticas"—: el repo de seguridad no
trae cambios de funcionalidad, asi que "sin sorpresas" se conserva.

## Por que NO acoplar "un solo boton" que actualice LRP + sistema
Idea que el dueño propuso y se descarto tras analizarla:
- **Radios de daño incomparables.** LRP = reinstalar UN paquete propio y probado. `apt upgrade`
  completo = kernel, systemd, drivers y Firefox de una. Si sale mal, la maquina puede no
  arrancar — **y la usuaria no tiene teclado**. *Precedente: el OTA que dejaba el servicio
  muerto era UN paquete; el mismo modo de falla con un kernel adentro es otra cosa.*
- **Ritmos distintos.** Un LRP del martes no debe arrastrar un kernel; un parche de Firefox no
  debe esperar al proximo release de LRP.
- **Tiempo percibido.** El boton se espera en segundos. Un upgrade completo son cientos de MB y
  varios minutos — en el Q8300 con disco mecanico, bastantes — con la tele sin responder.
- **Lo mas grave: la reversion.** Volver atras un `.deb` es viable (se guarda el anterior).
  **Revertir un `apt upgrade` completo en Debian, en la practica, no se puede.**

## Malentendido que libera la mitad del problema
*"Actualizar LRP deberia llamar a actualizar dependencias"* — **eso YA pasa**:
`apt install ./paquete.deb` resuelve e instala lo declarado en `Depends:`.
**Actualizar dependencias NO es actualizar el sistema.** Lo primero ya esta; lo segundo es lo que
no conviene atar al boton.
*(Relacionado: el `.deb` declara `build-essential`, o sea que le mete un compilador entero a cada
usuario. En un electrodomestico pesa mas que en un escritorio. Anotado en BUGS §menores.)*

## Correccion a "una sola ISO siempre"
**Una ISO por GENERACION de Debian, no una por version de LRP** — o sea, una **cada ~2 años**,
cuando sale una Debian mayor. Con eso:
- **Casi no se mantienen ISOs.**
- **Las instalaciones existentes NUNCA hacen el salto grande en caliente**, que es el que rompe
  maquinas: siguen recibiendo parches de seguridad durante los ~5 años de soporte de esa Debian.
- **Cambiar de base = ISO nueva**, instalacion limpia, sin migracion riesgosa.

**Ahi las ISOs versionadas ganan su lugar: no como canal de actualizacion, sino como GENERACIONES
DE PRODUCTO.**

---

# 6 · El brazo mas barato del ecosistema, que casi se pasa por alto

El dueño menciono al pasar **control profesional: diapositivas y comandos programables**.
**Eso es la misma emulacion de entrada que ya existe, con otro HUD y un modo de macros.** Cero
sistema operativo, cero soporte de hardware nuevo, cero distro.

Y le habla a un publico que **paga mas que el usuario de sala**. Puede ser el brazo mas rentable
del ecosistema y el mas barato de construir. **Pensarlo en paralelo, no despues.**

---

# 6 · Posicionamiento

**El modo dedicado de verdad es probablemente el mejor diferenciador comercial**, porque es
exactamente lo que las apps de control remoto NO hacen: ellas asumen que hay alguien manejando
una computadora. LRP estaria vendiendo **"convertí esa PC en un electrodomestico"**.

Si algun dia se justifica subir el precio, va a ser por ahi — **no por mas botones**.
