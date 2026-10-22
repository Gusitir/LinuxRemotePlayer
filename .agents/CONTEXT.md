# CONTEXT — handoff entre sesiones

<!-- Última sesión completa arriba. Las anteriores se compactan; la historia exacta vive en git. -->

## 2026-08-11 · cambio de visión: LRP local, libre de premium y nube

El dueño decidió cambiar la tesis del producto después de evaluar Needle 2. **Destino aprobado:**
voz e interpretación 100% locales en el HTPC, sin Paddle, licencias, cuotas premium ni funciones
bloqueadas. Patreon será apoyo voluntario. LRP seguirá siendo la app multi-distro; una imagen
Debian HTPC será un proyecto hermano posterior.

La propuesta inicial `Silero → SenseVoice → Needle 2` tenía un bloqueo: SenseVoice-Small no
soporta español. El laboratorio comparará Whisper multilingüe `base` y `small` cuantizados;
`whisper.cpp` es la primera referencia y sherpa-onnx una abstracción alternativa. Needle 2
parece adecuado para tool calling restringido, pero sus cifras deben repetirse en Linux x86-64
y con órdenes reales de LRP. El Q8300 deja de ser objetivo; el piso provisional es AVX2 hasta
que los benchmarks definan el mínimo real.

La arquitectura acordada separa: audio → VAD → STT → Needle → validador Python → contexto
SQLite → adaptadores MPRIS/CDP/entrada. **La IA nunca ejecuta shell.** CDP/BiDi, si se usa,
escucha solo en `127.0.0.1`, con perfil aislado y capacidades por sitio. El historial local no
se promete universal: cada adaptador declara qué puede observar y reanudar.

Esta sesión solo reescribió `.agents/`; no modificó producto. **1.9.1 todavía es cloud/licensed**
y se conserva estable hasta demostrar el reemplazo. El próximo paso es que el dueño establezca
el flujo de trabajo; luego se crea un laboratorio aislado y se mide antes de implementar.

**Aclaración posterior del dueño:** toda la nueva visión es **LinuxRemotePlayer 2.0.0**. El
lanzamiento incluye también el rediseño de la web y la retirada de los servicios Supabase de
keys, licencias y proxy de IA. No son tareas post-2.0 ni releases intermedias.

**Workflow adoptado:** Arquitecto Codex (este chat) → un Ingeniero Codex nuevo por fase → un
Obrero Gemini 3.6 Flash High fresco por tarea mediante `agy.exe`. El Ingeniero audita tareas y
hace sus commits; el Arquitecto audita fases, integra y es el único que modifica `.agents`.
Contrato, gates, ramas, evidencia y comando verificado: `WORKFLOW.md`.

**PH21 abierta:** el Arquitecto fijó G0 en `PLAN_PH21.md`: benchmark STT reproducible, Whisper
base/small obligatorios, corpus ES/EN, licencias, métricas y separación estricta del producto
1.9.1. El Ingeniero debe producir G1 y un smoke test de `agy.exe` antes de lanzar Obreros.

## Sesiones anteriores — vigencia condensada

- **2026-07-31:** auditor externo descubrió B19: OTA root sin firma. Sigue abierto y bloquea
  cualquier siguiente release pública, aunque ya no exista venta. También nacieron USER.md y
  BUGS.md. El plan comercial Paddle/1.9.2/1.9.3 quedó **SUPERADO** por D16-D24.
- **2026-07-30:** 1.9.1 publicada y certificada 6/6. Regla durable: una prueba de device solo
  vale si `dpkg -V` confirma que el equipo representa el paquete. Solo el dueño hace push.
- **2026-07-24..30:** dominio, documentación, PWA, skins y updater fueron endurecidos. Mantener
  alias Vercel antiguo, comentarios de T-70/T-72/T-79 y verificación del `.deb` real.
- **2026-07-13..20:** nació el flujo ejecutor/auditor y se implementó la voz cloud. Esa
  implementación pasa a ser baseline de comparación, no arquitectura futura.

## INIT · 2026-06-24

PWA móvil controla una PC Linux por WebSocket. La premisa original decía que la IA pesada iba
a la nube; D16 reemplaza esa premisa, pero no cambia retroactivamente el código de 1.9.1.

## 2026-08-21 · adopción agents-workflow v3

MAINTAIN adoptó la semántica v3 en el plano de control. `AGENTS.md` es la autoridad de roles,
assurance `Standard`, reglas durables, gates, separación y orquestación; `CURRENT.md` solo mantiene
estado vivo; `INDEX.md` posee navegación; `TESTING.md` contiene únicamente checks humanos o no
disponibles; los planes poseen scope/tareas; `APPCORE.md` conserva arquitectura estable verificada.

Se corrigió D27: el workflow vigente usa dos Ingenieros persistentes `gpt-5.6 LUNA` con esfuerzo
`MAX`; TERRA/SOL están prohibidos; cada Ingeniero tiene hasta 2 slots LUNA-MAX y el total global
es 4, siempre con autorización del Arquitecto. DeepSeek V4 Flash High queda reservado al
Arquitecto para hasta 2 fixes diminutos posteriores a auditoría. No se usaron Obreros en MAINTAIN.

CAVEMAN queda durable para Arquitecto, Ingenieros y Obreros: sin saludos ni relleno; salida breve,
técnica, factual y accionable. PH21 permanece activa con G0 `APTO` y G1 `pendiente`; el siguiente
job es el global `REINDEX`. El snapshot histórico de TESTING queda en `archive/`.

## 2026-08-21 · D28 — betas opt-in y pruebas directas

El dueño reemplazó el laboratorio físico como gate previo por betas instalables. Stable 1.9.1 no
debe descubrirlas: conserva su manifiesto y botón actuales. La única inscripción beta será el
comando curl de una página pública mínima; una beta instalada persiste su canal, consulta un
manifiesto separado y recibe solo actualizaciones beta-a-beta.

Las versiones técnicas siguen `X.Y.Z`: `1.99.1`, `1.99.2`, etc.; `2.0.0` queda para estable. Cada
modelo se validará dentro de una beta con 18 comandos —12 ES y 6 EN— en lugar de exigir primero el
corpus físico de 60 audios. PH21 se conserva como tooling reutilizable, no como gate.

B19 es un riesgo aceptado por el dueño para estas betas opt-in sin publicidad porque no hay base de
usuarios anunciada. No se declara resuelto: firma, downgrade y rollback siguen bloqueando la
promoción estable 2.0.0. Needle 2 permanece previsto para sustituir la interpretación cloud tras
elegir STT; Python mantiene PolicyEngine y los modelos nunca ejecutan shell.

**Aprobación D28:** el dueño aprobó el plan beta y ordenó `RUN THE LOOP` el 2026-08-21. Diseño
canónico SHA-256: `2bc3ec3cfac39a205c4a16c0d1f06b85f388d040e34a0d2290e3dd0f9c552f7d`.
La aprobación habilita T-117; no autoriza push, deploy, release ni operaciones destructivas.

## 2026-08-22 · integración final beta opt-in

Registro operativo: `main` quedó en `8e27512` y `codex/beta-foundation` en `4bdf5da`; la cadena de
commits de producto fue `942fab2`, `afdcfd3`, `bedc94b`, `28be028` y el fix LF `8e27512` en main,
con equivalentes `298bb39`, `607bf04`, `be96e35`, `e838279` y `4bdf5da` en beta. Vercel reportó
status success para `8e27512` en `2026-08-23T04:48:12Z`.

Se verificaron los endpoints públicos: raíz ES y `/en/` muestran beta mínima; `/latest.json` sigue
stable `1.9.1` con SHA `82b6bc5286cdf197bb684ddc00f6c797aac498f2959b354cada83acaddd93d38`;
`/beta/latest.json` es `1.99.1` y `/beta/install.sh` responde. El `.deb` beta descargado de forma
independiente coincide con SHA `8d4a19834eca05eda0e3f8b9c77817e6baaa19fb1bd823e30b5a726b6cb9c894`.

El fix `.gitattributes` quedó incluido en `8e27512`; 29 tests pasaron después del arreglo de LF.
T-121 queda bloqueado únicamente por la evidencia HTPC del dueño (`TST-BETA-CHANNEL-001`). Los
clones externos `lrp-t118-build-3`, `lrp-t118-integrated-1` y `t120-native-20260822-5` quedan sin
cleanup autorizado. Este registro no emite veredicto humano.

## 2026-08-23 · HANDOFF session close

`main`/`origin/main` están sincronizados en `4c28d41`; `codex/beta-foundation`/origin en `4bdf5da`.
Vercel reportó `success` en `2026-08-23T05:07:01Z`. Stable `1.9.1` y beta `1.99.1` permanecen
verificadas; el beta `.deb` coincide con SHA
`8d4a19834eca05eda0e3f8b9c77817e6baaa19fb1bd823e30b5a726b6cb9c894`.

T-121 queda bloqueado por `TST-BETA-CHANNEL-001` automatizable con autorización del dueño y
`TST-BETA-HUMAN-001` humano. `TST-BETA-UPDATE-002` queda diferido y no bloquea. Persisten sin
cleanup autorizado los clones `lrp-t118-build-3`, `lrp-t118-integrated-1` y `t120-native-20260822-5`.
Sesiones persistentes: control `ses_fd89e5f9effeFg15Lq7OKDlxu3`, producto
`ses_fd89e2891ffePR5nRqlGsyeKHw`, Workers `ses_fd84c189dffeo3efi7lMZtZ6HS` y
`ses_fd82b70b4ffe1xKKtLCNow4QzW`, DeepSeek del Arquitecto `ses_fd31148adffeGMmtU9XqM9OYqG`.
Sin veredicto humano nuevo; el Arquitecto audita y decide después de recibir ambas capsules.

## 2026-08-23 · D29 T-121 evidence reconciliation

Se separó la evidencia de T-121: `TST-BETA-CHANNEL-001` conserva una cápsula técnica AI `[OK]`
con manifiestos, hash, instalación beta, canal persistente, servicio y endpoints verificados; AI no
ejecutó ni certifica browser/certificado, QR/PIN, onboarding PWA, kiosk, touchpad o media. El dueño
registró esos checks en `TST-BETA-HUMAN-001` como `[OK]` el 2026-08-23.

`TST-DEVICE-001` queda `[SKIP: offline/uninstall/upgrade not executed; owner accepts deferral and
trusts existing implementation]`. La prueba de campo con una instalación estable ya instalada
queda `[SKIP: no ejecutada; no aplicable por ausencia de usuarios]`. Stable isolation sigue siendo
requisito de producto; para BETA-FOUNDATION, los tests deterministas T-117 y el manifiesto público
stable `1.9.1` sustituyen esa evidencia de campo. T-121 queda en `audit` hasta la revisión
independiente del Arquitecto; no se emite `APTO`.

## 2026-08-23 · D30 BETA-FOUNDATION milestone close

El Arquitecto cerró BETA-FOUNDATION con veredictos autoritativos `APTO` para T-117, T-118, T-119,
T-120 y T-121 bajo assurance `Standard` / independent model audit. El plan cerrado vive en
`archive/PLAN_v1.99-beta-foundation.md` y la cápsula completa en
`archive/TESTING_beta-foundation_1.99.1.md`; `TESTING.md` fue rotado al ciclo BETA-STT sin resultados
crudos del milestone cerrado.

Stable permanece en `1.9.1`; beta en `1.99.1`; el artefacto beta conserva SHA
`8d4a19834eca05eda0e3f8b9c77817e6baaa19fb1bd823e30b5a726b6cb9c894`. Push y deploy ya estaban
realizados. La disposición propuesta es conservar `codex/beta-foundation`. D29 sigue aceptado y
`TST-DEVICE-001` queda como residual `[SKIP]`; `TST-BETA-UPDATE-002` queda diferido y no bloquea.

`backup_state: pending`. El savepoint autorizado para Google Drive debe usar los nombres
`linuxremoteplayer-savepoint-beta-foundation-20260823.bundle` y
`linuxremoteplayer-savepoint-beta-foundation-20260823.zip`; no se persiste ruta absoluta. El siguiente
paso, tras registrar hashes del backup, es iniciar PLAN BETA-STT. El cleanup de clones WSL sigue sin
autorización.

## 2026-08-23 · D30 backup receipt correction

Corrección append-only del estado D30: `backup_state` pasa de `pending` a `complete` con recibo
verificado bajo autoridad del Arquitecto. El commit de cierre main es `407bb66`; la disposición de
branch permanece `keep codex/beta-foundation` y push/deploy ya estaban realizados.

Google Drive labels/names y hashes: `backups/linuxremoteplayer-savepoint-beta-foundation-20260823.bundle`,
size `13079844`, SHA256
`ebcf392cb5c521e1b07f4e9264c2838a994c14769d32e80906260ffb2ef5f0c4`; `git bundle verify` reporta
complete history y 14 refs. `backups/linuxremoteplayer-savepoint-beta-foundation-20260823.zip`, size
`4144496`, SHA256
`f78fdb421d355321596ef503c0ab59b2df3666f149f86a037e95de3f566eb1ec`; contiene todos los tracked
files en `407bb66` más el `lochi.png` preexistente, sin `.env` ni `.git`. No se persiste ruta absoluta
de Drive. El siguiente job es PLAN BETA-STT; quedan únicamente cleanup WSL no autorizado y decisiones
de inventario/diseño de modelos sin resolver.

## 2026-08-28 · D31 Debian-only HTPC direction

El dueño redefinió el alcance: LinuxRemotePlayer sigue siendo un solo producto y soportará únicamente
Debian 13 stable amd64 minimal con sesión gráfica Xorg/Openbox administrada por LRP. La imagen Debian
y un control remoto multidistro quedan diferidos; Plasma/Bigscreen, KDE Neon, Wayland y compatibilidad
multidistro salen del alcance activo. RTX 3060 12 GB será la GPU inicial certificada; drivers y
firmware deben provenir solo de repositorios Debian.

Rationale: Plasma Bigscreen no levantó en la máquina de pruebas tras instalar RTX 3060, mientras
Linux Mint instaló correctamente. La causa raíz no fue demostrada; el hecho solo justifica dejar de
depender de una plataforma HTPC inmadura, no afirmar incompatibilidad universal Plasma/NVIDIA.
Antes de código privilegiado, T-122 verifica paquetes/repositorios/Secure Boot/GPU en Debian real y
D32 fija display manager y paquetes exactos. STT/Needle se posponen hasta cerrar esta fundación.

## 2026-08-28 · D31 approval receipt and run authorization

El Arquitecto GPT aceptó el diseño canónico del plan `PLAN_v1.99.2-debian-htpc-foundation.md` con
SHA-256 `678ac5c9119312529ec1b5fe3b054c77a595b03dbe82c8319d669327fd17002a`, registró
`approval_decision_id: D31` y ordenó `RUN THE LOOP`. La aprobación habilita únicamente T-122
(`ready`); el resto de tareas permanece bloqueado hasta T-122 `APTO` y la decisión D32.

Topología vigente: el Arquitecto GPT posee `design`, `.agents` y el veredicto final; el asistente del
Arquitecto `ses_fd31148adffeGMmtU9XqM9OYqG` hace lecturas, preauditorías y escrituras focalizadas y
nunca se autoaudita; el único Ingeniero `ses_fd89e5f9effeFg15Lq7OKDlxu3` posee briefs, razonamiento
complejo, orquestación de Workers y veredictos de tarea; hay 2 Workers Ingeniero DeepSeek V4 Flash
para escribir, buscar y testear; el Auditor de fase `ses_fba664c9effeeQgXoQXg6zck60` audita solo
fases, sin código, fixes ni planificación. La entrega de cada Worker es auditada y veredictada por el
único Ingeniero; el asistente puede preauditar mecánicamente; tareas de alto riesgo o seleccionadas y
el milestone reciben revisión independiente del Arquitecto GPT; T-131 recibe revisión de fase del
Auditor más un veredicto final independiente del Arquitecto.

Se eliminaron todas las referencias Gemini y los rótulos de audit por tarea del Auditor en AGENTS,
WORKFLOW y el plan. La aprobación no autoriza push, deploy ni operaciones destructivas; el push sigue
siendo del dueño.

## 2026-08-28 · D32 package contract approved (T-122 apto)

El Arquitecto aprobó D32 tras la baseline física T-122. `TST-DEBIAN-BASE-001` `[OK]` (AI: Debian 13
trixie amd64 UEFI, RTX 3060 PCI `10de:2504`, módulo `nouveau` activo, Secure Boot `disabled` Setup
Mode, fuentes oficiales `main`+`non-free-firmware` sin terceros) y `TST-DEBIAN-BASE-HUMAN-001` `[OK]`
(dueño: netinst minimal sin desktop, consola/red, GPU y pantalla, backup/recovery). Código T-122
final `APTO` (33/33 T-122, 62/62 suite, bash/static/diff).

Contrato D32: componentes oficiales `main contrib non-free non-free-firmware`; display manager
`lightdm 1.32.0-6+b2`; `xserver-xorg 1:7.7+24+deb13u1`; `openbox 3.6.1-12+b2`; NVIDIA meta
`nvidia-driver 550.163.01-2` con deps `nvidia-kernel-dkms`/`xserver-xorg-video-nvidia 550.163.01-2`,
`firmware-nvidia-gsp 550.163.01-2`, `linux-headers-amd64 6.12.105-1`, `dkms 3.2.2-1~deb13u1`. No
instalar `nvidia-open-kernel-dkms` ni `firmware-misc-nonfree` salvo dependencia verificada; nunca
`.run`/third-party. Verificado por consulta `apt-cache` aislada en sandbox oficial; no se ejecutó
instalación. T-122 queda `APTO`; T-123 queda `ready`. El código T-122 sigue sin commit en
`codex/debian-foundation`.

## 2026-08-31 · T-123 apto — NVIDIA bootstrap and reboot resume

Código T-123 final `APTO` (47/47 T-123, 110/110 suite completa; auditorías posteriores verdes).
Evidencia física: Debian 13 legacy oficial, components `main contrib non-free non-free-firmware`,
paquetes/headers exactos; un apply interrumpido se recuperó vía `dpkg --configure -a`; apply final
exit 20 sin auto-reboot; reboot autorizado por el dueño; módulo `nvidia` vinculado a RTX 3060 con
`nouveau` ausente, `nvidia-smi` `550.163.01`, resume exit 0 estado `complete`. Interrupción de
energía residual recuperada; renderer diferido a T-124. `TST-NVIDIA-001` `[OK]`; `TST-SESSION-001`
`SKIP`. T-123 `APTO`; T-124 queda `ready`. Código T-122 y T-123 siguen sin commit en
`codex/debian-foundation`.

## 2026-08-31 · T-124 apto — managed Xorg/Openbox session

T-124 queda `APTO` por veredicto del Ingeniero. Código: 15/15 tests focales y 125/125 suite completa
antes de dos fixes físicos acotados, ambos con 15/15 focales y `bash -n` verde. El HTPC instaló los
siete paquetes Debian exactos y creó el usuario bloqueado no-root `lrp`. Un primer apply se detuvo de
forma segura con LightDM enmascarado por una expansión Bash incorrecta; el fix idempotente terminó
exit 20, desenmascaró y habilitó LightDM sin iniciarlo. Tras reboot autorizado, resume exit 0 verificó
LightDM activo, Xorg, Openbox propiedad de `lrp`, entorno X, renderer NVIDIA sin `llvmpipe`, paquetes
íntegros y estado `complete`. `TST-SESSION-001` `[OK]`; T-125 queda `ready`. Código T-122..T-124 sigue
sin commit en `codex/debian-foundation`.

## 2026-08-31 · T-125 apto — single Debian HTPC installer/service mode

T-125 queda `APTO` por veredicto del Ingeniero: 10/10 tests focales, 135/135 suite completa,
`bash -n` y diff verdes. `scripts/install.sh` exige el usuario T-124 `lrp`, normaliza
`LRP_MODE=htpc`, limpia de forma acotada unidades user legacy y genera un único servicio systemd
`User=lrp` ordenado tras display manager y red. `scripts/build_deb.sh` conserva únicamente lifecycle
del servicio system. La prueba física del backend se difiere hasta que exista el paquete 1.99.2;
no se ejecutó el instalador viejo sobre el HTPC. T-126 y T-127 quedan `ready`.

## 2026-08-31 · T-126 apto — Firefox ESR kiosk on Xorg/Openbox

T-126 queda `APTO` por veredicto del Ingeniero: 22/22 tests focales, 147/147 suite completa y gates
Python/shell/diff verdes. Runtime e instalador usan solo Firefox ESR sobre Xorg, con perfil dedicado,
`wmctrl` y cierre acotado del grupo rastreado; se retiraron fallbacks Brave/Chromium, Wayland,
KWin y qdbus. En el HTPC se instalaron desde Debian oficial `firefox-esr 140.14.0esr-1~deb13u1` y
`wmctrl 1.07+git20240228.1105759-1`; el smoke bajo `lrp` abrió una ventana kiosk, confirmó proceso y
ventana a los 10 segundos y cerró limpio con exit 0. T-127 queda como siguiente tarea.

## 2026-08-31 · T-127 apto — Debian platform services

T-127 queda `APTO` por veredicto del Ingeniero. Gates: 17/17 plataforma, 36/36 combinado y full previo
159/159. Apply físico exit 0 y reboot verificaron usuario `lrp` con grupo input, `/dev/uinput` rw,
PipeWire/Pulse/WirePlumber activos, Avahi activo, UFW activo con reglas OpenSSH y
`linuxremoteplayer`, cuatro targets sleep masked, screensaver timeout 0, DPMS disabled y `dpkg -V`
limpio. Un check repeat detectó correctamente un falso drift por semántica rc=1 de `masked`; el fix
focal quedó 14/14 y repeat físico terminó exit 0. El attach tardío de CA real quedó cubierto 17/17;
la evidencia HTTPS se completa cuando el backend/paquete genere su CA, sin CA temporal falsa. T-128
y T-129 quedan `ready`.

## 2026-08-31 · T-128 apto — uninstall/rollback round trip

T-128 queda `APTO` por veredicto del Ingeniero. Gates finales: rollback/plataforma 37/37, archivo
rollback 15/15 y full previo 178/178. En el HTPC, dry-run root listó platform/session y datos
retenidos; apply estricto exit 0 dejó consola segura, retiró únicamente estado administrado y
restauró Avahi/UFW/sleep/input. Se conservaron usuario/home `lrp`, todos los paquetes, NVIDIA RTX
3060/driver 550 y datos del backend. El round trip reaplicó sesión y plataforma, ejecutó dos reboots
y terminó con session `complete`, platform `applied`, audio/uinput/UFW/DPMS/NVIDIA correctos. Falta
solo confirmación visual humana de consola para cerrar `TST-DEBIAN-ROLLBACK-001`. T-129 queda activo.

## 2026-08-31 · T-129 apto — Debian-only product truth

T-129 queda `APTO` por veredicto del Ingeniero: docs/landing 8/8, suite completa 187/187 y sweep de
referencias activas limpio. README, arquitectura/desarrollo, website/docs/términos ES/EN y
`.env.example` declaran Debian 13 stable amd64 minimal, sesión Xorg/Openbox administrada, Firefox ESR
y RTX 3060 12 GB como GPU inicialmente certificada; otras plataformas no tienen garantía. Changelogs
y archivos históricos quedaron intactos. T-130 queda `ready`; commit, push y deploy siguen sin
autorización explícita.

## 2026-09-01 · T-130 prebuild ready — commit authorization required

T-130 preparó VERSION 1.99.2, changelog, builder/control/updater amd64, manifest beta con
`BUILD_REQUIRED` y tests release. Gates prebuild: 190 passed, 2 skips esperados por ausencia de
artefacto; diff y aislamiento stable verdes. No se construyó artefacto ni se hizo commit, push o
deploy. El build obligatorio desde clon WSL nativo limpio requiere primero un commit productor en
Windows; queda bloqueado hasta autorización explícita del dueño. Push/deploy siguen separados.

## 2026-09-01 · D33 — two-level Architect/Engineer workflow

El dueño reemplazó la topología de tres niveles por dos niveles para esta fase. El Arquitecto
conserva diseño, `.agents`, alcance, auditorías por baches y veredicto final. El único Ingeniero
`ses_fd89e5f9effeFg15Lq7OKDlxu3` implementa producto directamente, corrige, ejecuta gates e integra
evidencia. No se orquestan Workers, asistentes ni subagentes de implementación. No hay auditoría ni
veredicto por tarea. El Auditor `ses_fba664c9effeeQgXoQXg6zck60` interviene una sola vez al cierre de
fase, antes del veredicto final del Arquitecto. Resultados históricos de Workers permanecen como
evidencia pasada y no describen la topología vigente.

## 2026-09-01 · D34 — audio output selector deferred to app redesign

El dueño exige que el rediseño general de la app/control remoto incluya detección y selección de
salida de audio. La UI deberá enumerar sinks PipeWire, mostrar/cambiar/persistir el activo y manejar
mute, volumen, hotplug, reboot y ausencia de HDMI. Para la fundación Debian actual se corrige la
selección automática del HDMI certificado; esa automatización no cierra ni reemplaza el requisito UI
de PH26.

## 2026-09-01 · T-130 physical candidate evidence

El candidato local `98bb9f1` / artefacto SHA
`a0b54c85fff7842a25676546c8d105455c603fb202eb53510fbff622442a83e9` pasa 205/205 en Windows y
clon WSL nativo limpio. El HTPC instaló/reinstaló 1.99.2 amd64 con `dpkg -V` limpio, servicio no-root,
HTTPS/CA, beta channel, pairing, apps, controles, Firefox ESR y plataforma activos. Se corrigieron
tres defectos físicos: no se imprime el token de pairing, UFW recarga mDNS 5353/udp además de
8000/tcp y PipeWire selecciona/desmutea HDMI NVIDIA al 100%; Firefox elimina solo recovery state del
perfil kiosk y desactiva restore-from-crash. El token expuesto durante diagnóstico fue rotado sin
mostrar el reemplazo. Un hard reset tras Netflix no dejó shutdown/panic/OOM/thermal/Xid/pstore y no
se reprodujo durante 90 segundos monitorizados; permanece como finding de estabilidad. Sin push/deploy.

## 2026-09-01 · T-130 apto — public beta 1.99.2

El Arquitecto cerró el audit de bache T-122..T-130 después de resolver orquestación de instalación
limpia, dependencias runtime, exposición de pairing token, mDNS efectivo, salida HDMI y recuperación
Firefox. `main` avanzó por fast-forward a `98bb9f1` y fue pusheado con autorización explícita; Vercel
reportó success. Manifest/installer/copy ES/EN públicos declaran 1.99.2 Debian amd64 y el artefacto
descargado independientemente coincide con SHA
`a0b54c85fff7842a25676546c8d105455c603fb202eb53510fbff622442a83e9`; stable permanece 1.9.1.
Windows y WSL nativo pasan 205/205. El dueño confirmó pairing, apps, controles y audio HDMI; el
soak de 3 minutos mantuvo health/GPU/servicio sin reset. T-130 queda `APTO`; T-131 queda `ready`.

## 2026-09-01 · D35 — one-command unattended Debian install

El dueño reemplazó el flujo manual de dos resumes por una instalación pública de un solo comando.
La invocación inicial autoriza apt y hasta dos reboots automáticos. Un servicio systemd temporal
persiste la continuación NVIDIA -> sesión -> app/plataforma, limita intentos para impedir boot loops,
falla cerrado, conserva recuperación por TTY y se elimina tras health exitoso. Fuera del modo
unattended, los bootstraps mantienen no-auto-reboot. La OTA pública 1.99.1 -> 1.99.2 pasó y conservó
channel/config/token/CA, pero reveló los dos archivos uinput legacy exactos; D35 incluye su migración
segura antes del cierre T-131.

## 2026-09-02 · MAINTAIN — reconciliación de estado tras cambio de modelo y limpieza de `%TEMP%`

Correcciones clasificadas contra Git verificado (`main`/`origin/main` `98bb9f1`; worktree `7f6375d`):
`CURRENT.md` tenía `source_commit`, `product_branch_head`, `dirty_items`, `next_action`, blockers
(push/deploy) y evidencia (`407bb66`, `205/205`) `stale`/`contradictory`; el plan activo decía
T-131 `ready` con alcance solo read-only pese al commit D35; `TESTING.md` aún bloqueaba el comando
beta hasta T-122/D32 y daba la migración legacy por pendiente; `INDEX.md` seguía en reindex de
agosto (plan pendiente, sin `tests/`). Reparado cada archivo dueño sin tocar producto ni reescribir
historia. Estado real: OTA pública `1.99.1->1.99.2` pasada con estado retenido, migración legacy
verificada en HTPC, suite `207/207`, sandbox D35 y audio HDMI humano `[OK]`; pendiente reconciliar el
artefacto reconstruido (sidecar `25ea41…`) con el manifiesto (`a0b54…`), confirmación visual de
rollback y auditoría final. Limpieza de `%TEMP%` invalida cachés/fixtures previos: regenerarlos al
correr gates. Siguiente harness: reconciliar artefacto/manifiesto, reruns deterministas, sin
push/deploy sin autorización del dueño.

## 2026-09-02 · REINDEX + deuda — APPCORE/INDEX/BUGS al día

`APPCORE.md` reindexado contra `98bb9f1` verificado en repo: mapa 1.99.2 Debian-only
(amd64, Xorg/Openbox, Firefox ESR solo `lrp`, servicio único, bootstraps, beta amd64 con SHA
`a0b54…`, `tests/` existentes). `INDEX.md` reconstruido con rutas `scripts/debian/*`,
`website/beta/*` y comandos `pytest`/`bash -n`. `BUGS.md`: token-print marcado resuelto en
1.99.2; registrada deuda `state_applied_ok()` duplicado (líneas 55/57, sin efecto runtime).
Digest canónico intacto. Pendiente solo T-131: reconciliar artefacto, reruns, confirmación
visual, auditoría final; sin push/commit sin autorización.

## 2026-09-03 · D36 — revised multi-tier topology and role contracts

El dueño estableció la topología refinada del proyecto:
- Arquitecto (`42a6a909-29da-4d4c-8f81-4e7bafff4cb8`): diseño, planificación, pensamiento estratégico,
  auditoría de baches, commits del plano de control e integración autorizada, veredictos. Orquestación
  principal de los chats persistentes Ingeniero y Auditor. Autorizado para orquestar un único asistente
  para tareas quirúrgicas puntuales y lecturas/búsquedas de ahorro de contexto (sin tareas extensas).
- Ingeniero (`fdfc68b2-8383-4854-8f61-737c6e0c101b`): implementación de producto en worktree, redacción
  de briefs, ejecución de gates deterministas, tests y verificación técnica. Autorizado para orquestar
  hasta 2 Obreros Gemini concurrentes para escribir código y hacer búsquedas. Invariante estricto: inspección
  directa obligatoria en código y diffs antes de avanzar; nunca aceptar ciegamente por reporte.
- Obreros (Gemini): orquestados exclusivamente por el Ingeniero para código y búsquedas acotadas.
- Auditor (`ae7b054f-900d-4285-87c0-f2cdd49e7888`): búsquedas exhaustivas, detección de bugs complejos,
  auditorías de fases y auditorías completas a solicitud del Arquitecto. Autorizado a usar `/boost` y
  `/teamwork-preview` (notando que `/boost` presenta fallo transitorio en Antigravity).

## 2026-09-03 · D37 — Debian HTPC Foundation Phase closure (T-122..T-131 APTO)

Cierre formal de la fase `PLAN_v1.99.2-debian-htpc-foundation.md`:
- T-131 verificado y cerrado como `APTO`. Reconciliación determinista completada: paquete `.deb`, sidecar
  `.sha256` y manifiesto `latest.json` coinciden exactamente en SHA256
  `25ea41735a5e3b8b35d8f9e718700ff54195d976950360ddd050f8ea855fea46`.
- Deuda técnica eliminada en `scripts/debian/platform-bootstrap.sh` (duplicado `state_applied_ok()` removido).
- Gates deterministas: suite completa `pytest` 207/207 passed, `bash -n` limpio en todos los scripts de Debian.
- Verificación física en hardware objetivo: Debian 13 minimal amd64 + RTX 3060, driver oficial 550, sesión
  Xorg/Openbox no-root (`lrp`), Firefox ESR kiosk a pantalla completa, PipeWire con salida HDMI seleccionada al 100%,
  UFW 8000/tcp+5353/udp, Avahi y uinput operativos. Flujo de instalación unattended D35 verificado en HTPC.
  Confirmación visual del dueño del código QR y panel de estado en pantalla (`TST-DEBIAN-ROLLBACK-001` [OK]).
- Auditoría de cierre: LRP AUDITOR emitió recomendación técnica favorable (APTO). LRP ARQUITECTO emitió veredicto
  G4 APTO. Commit de producto registrado en `codex/debian-foundation` como `95490ce`.
- Canal estable 1.9.1 permanece estrictamente aislado; B19 permanece documentado como bloqueante para 2.0.0 estable.
- Plan cerrado y archivado. Próxima fase del roadmap: BETA-STT / PH21 (laboratorio de voz a texto local).

## 2026-09-03 · D38 — LRP OS v2.0 Appliance & Local Voice Plan Approval

El dueño aprobó la visión estratégica integral y el plan maestro `PLAN_v2.0-appliance.md`:
- Digest de aprobación canónica: `3af7f03777efc59794d3c485267c010c39dba010cb4e9a2cf195b4a3309b0667`.
- Definición de producto: Se prioriza LRP OS (Appliance Debian 13 minimal listo para USB) como producto
  principal para hardware de bajos recursos/dedicado, antes de portar la app a otras distros.
- Hardware mínimo certificado: Intel Core i5-3470 (Ivy Bridge, 4 núcleos, 3.2 GHz, SSE4.2 + AVX 1.0, sin AVX2
  ni FMA3), 8 GB RAM, y GPU integrada Intel (HD 2500/4000). Inferencia de voz 100% en CPU sin dGPU.
- Arquitectura desacoplada: El Core universal de LRP se separa de los módulos de control del sistema operativo
  (Audio PipeWire, Wi-Fi NetworkManager, Bluetooth BlueZ, Display Xrandr).
- Panel de TV (OSD): Extendido con pestaña de Ajustes de Sistema para visualización y control directo en TV.
- T-132 habilitada como primera tarea (`ready`):
  1. Arranque inmediato del panel OSD si no hay medios reproduciéndose (elimina el delay de 45s tras el boot).
  2. Apertura inmediata del panel de status cuando el escritorio quede sin ventanas de aplicaciones (`wmctrl -l`).
  3. Preservación del delay de 45s únicamente cuando haya streaming o audio activo ante caída de cliente.
  4. Escalado de cursor a 48px para 1080p (y regla para 4K) en Openbox / X11 para visibilidad desde el sofá.

## 2026-09-03 · D39 — /boost Command Governance Policy

Se define la política formal de uso para el comando `/boost`:
- Característica: Razonamiento profundo y multi-perspectiva de alto consumo de tokens.
- Restricciones por rol:
  * Obreros (Gemini): PROHIBIDO. Tareas rutinarias no justifican saturación de tokens.
  * LRP Ingeniero: DESACONSEJADO. Excepción única ante bugs bloqueantes inexplicables.
  * LRP Auditor: AUTORIZADO bajo demanda para auditorías forenses G4 y vectores críticos (B19/OTA).
  * LRP Arquitecto: RESERVADO para dilemas de arquitectura mayor o protocolos criptográficos.
- Regla operativa: Invocación puntual por orden explícita (disparo único); nunca activo de forma continua.

## 2026-09-04 · D40 — LRP OS Master Plan Regeneration (Bare-Metal Baseline, Network Resiliency & Astra Remediation)

El dueño ordenó regenerar el plan de acción para integrar la línea base física real, el blindaje de red y los hallazgos de `AUDITORIA_ASTRA.md`:
- Digest de aprobación canónica: `4e04a30856692a4c22b9fea1f2e017045c4923311ff72298e4f7a31d6aa80975`.
- Línea base de hardware bare-metal: Intel Core i5-3470, 16 GB DDR3, Intel HD Graphics 2500 (`8086:0152`), sin GPU dedicada (RTX 3060 retirada físicamente). Verificado arranque normal en Onboard IGD con salida HDMI y conexión Ethernet `enp2s0` a `192.168.0.246`.
- T-132 cerrada como `APTO` (arranque inmediato de OSD en <3s y cursor TV de 48px/96px; 220/220 tests pasando).
- T-133 habilitada como `ready` (Blindaje de red y GPU):
  1. Configuración de red agnóstica de hardware mediante regla comodín (`Name=en* eth*` DHCP) en `systemd-networkd` / udev.
  2. Watchdog de autorrecuperación de enlace cableado (`carrier == 1`).
  3. Carga dinámica de módulos NVIDIA mediante udev condicionado al PCI Vendor `0x10de`, eliminando `/etc/modules-load.d/nvidia*.conf`.
- Planificación de remediación de `AUDITORIA_ASTRA.md`:
  - T-134 (Seguridad crítica): ASTRA-01 (propiedad root de `/opt` y `.venv`, aislamiento de mutables) y ASTRA-02 (cierre de WebSockets autenticados al rotar pairing token).
  - T-135 (Resiliencia): ASTRA-03 (procesamiento de voz asíncrono desacoplado del heartbeat WS) y ASTRA-04 (verificación de caducidad `notAfter` y renovación automática de certificados HTTPS locales).

## 2026-09-05 · D41 — LRP OS Master Plan v2.0 Final Approval (Dual-Mode Wi-Fi & T-140 Hold Point)

El dueño fijó las directrices finales para el plan maestro `PLAN_v2.0-appliance.md`:
- Digest de aprobación canónica: `2120e72d1c9cc58361276c92d394a358cfecaaba9a61a01476d4965bd775b534`.
- Onboarding Wi-Fi dual de primer arranque:
  * Si se detecta teclado físico conectado: el panel OSD de la TV muestra el menú interactivo para seleccionar red y escribir contraseña mediante teclado.
  * Si NO se detecta teclado y no hay red cableada: LRP OS levanta automáticamente un hotspot Wi-Fi temporal (`LRP-Setup-XXXX`) mostrando un código QR en TV para que el usuario ingrese las credenciales desde su teléfono móvil.
  * En la futura LRP App para distros de escritorio, la configuración de red permanece desacoplada y opcional durante `lrp-setup`.
- Parada obligatoria antes de T-140:
  * El flujo de trabajo se detendrá estrictamente al concluir T-139. La tarea T-140 (Rediseño Móvil PWA 2.0) requerirá supervisión, alineación y dirección visual directa del dueño antes de iniciarse.
- T-132 commiteado en `codex/debian-foundation` como `faafd39` tras verificación determinista completa.
- T-133 implementado por LRP INGENIERO, verificado y cerrado como `APTO`:
  * Red comodín universal `/etc/systemd/network/10-wired-default.network` (`Name=en* eth* enx*`, `DHCP=yes`).
  * Sanitización de `/etc/network/interfaces` eliminando interfaces cableadas fijas.
  * Watchdog de auto-recuperación de carrier en `/usr/local/bin/lrp-network-watchdog` con timer systemd y regla udev.
  * Carga dinámica de módulos NVIDIA mediante `/etc/udev/rules.d/71-nvidia.rules` en vendor `0x10de`; eliminado `/etc/modules-load.d/nvidia*.conf`.
  * Resiliencia en hardware Intel/AMD: `nvidia-bootstrap.sh` y `session-bootstrap.sh` toleran ausencia de dGPU NVIDIA, verifican aceleración DRI/Mesa y descartan llvmpipe; paquete `i965-va-driver-shaders` agregado; DPMS inhabilitado.
  * Gates: 227/227 tests pytest passing, `bash -n` limpio; commit de producto `9898f6a`. Habilita T-134.
- T-134 implementado por LRP INGENIERO, verificado y cerrado como `APTO`:
  * ASTRA-01: `/opt/linuxremoteplayer` y `.venv` asegurados con propiedad `root:root` (0755/0644) en `install.sh` y `build_deb.sh`. Aislamiento de mutables (`.env`, `.pairing_token`, `.license_cache`, `certs/`) en `/var/lib/linuxremoteplayer/` (`lrp:lrp`, 0700). Módulo `backend/config.py` centraliza resolución de rutas seguras.
  * ASTRA-02: Revocación forzada y cierre inmediato de todas las conexiones WebSocket autenticadas (`code=1008`) al regenerar el pairing token en `/api/pairing-token/regenerate` y `/api/token/regenerate`.
  * Gates: 232/232 tests pytest passing (5 nuevos en `tests/test_security_mitigations.py`), `bash -n` limpio; commit de producto `610194e`. Habilita T-135.
- T-135 implementado por LRP INGENIERO, verificado y cerrado como `APTO`:
  * ASTRA-03: Desacoplamiento asíncrono de procesamiento de voz en WebSocket mediante `asyncio.create_task()` con tracking por conexión, cancelación en cleanup y `ws_send_lock` para evitar colisiones de frames. Pings/pongs y frames de control se responden concurrentemente.
  * ASTRA-04: Parseo de vigencia `notBefore` y `notAfter` en `backend/run.py`. Auto-renovación de certificados con caducidad <= 48h y salvaguarda RTC para preservar certificados válidos cuando el reloj del sistema esté descalibrado al año 1970/2000 por CMOS agotada.
  * Gates: 235/235 tests pytest passing (3 nuevos en `tests/test_resilience_mitigations.py`), `bash -n` limpio; commit de producto `ebfdf82`. Habilita T-136.
- T-136 implementado por LRP INGENIERO, verificado y cerrado como `APTO`:
  * Módulo desacoplado `backend/system_platform.py` con endpoints `/api/system/*` para PipeWire audio sinks y volumen (`wpctl`), Wi-Fi (`nmcli`), Bluetooth (`bluetoothctl`) y Display (`xrandr`), con degradación elegante en modo dev/no-Linux.
  * Optimización Kiosk VA-API en `backend/kiosk.py`: inhabilitación de VP9 y AV1 en `user.js` forzando streams H.264 por aceleración de hardware Intel HD 2500 (`i965-va-driver-shaders`).
  * Gates: 241/241 tests pytest passing (6 nuevos en `tests/test_system_platform.py`), `bash -n` limpio; commit de producto `b988882`. Habilita T-137.
- T-137 implementado por LRP INGENIERO, verificado y cerrado como `APTO`:
  * Interfaz Kiosk TV OSD en `frontend/status.html`: pestaña de ajustes del sistema ("Ajustes de Sistema") navegable con teclado físico y control remoto, feedback de foco de alto contraste para TV, selector interactivo de salida de audio PipeWire, selector de redes Wi-Fi e indicador de estado de red.
  * Onboarding Wi-Fi dual en `backend/system_platform.py`: detección automática de teclado físico conectado (`/dev/input/by-id/*kbd*` / `sysfs`). Si hay teclado, presenta menú de configuración interactivo en TV; si no hay teclado y no hay enlace cableado, activa automáticamente hotspot temporal `LRP-Setup-XXXX` con QR en pantalla para aprovisionamiento móvil.
  * Auto-desactivación de hotspot al conectarse exitosamente a red Wi-Fi y persistencia de configuración.
  * Gates: 245/245 tests pytest passing (4 nuevos en `tests/test_onboarding_dual_wifi.py`), `bash -n` limpio; commit de producto `415524b`. Habilita T-138.
- T-138 implementado por LRP INGENIERO, verificado y cerrado como `APTO`:
  * Infraestructura local STT en `backend/local_stt.py`: transcodificación in-memory WebM/MP4 -> WAV PCM 16kHz mono 16-bit vía pipes `ffmpeg` (sin escrituras en disco), VAD por umbral RMS (`threshold_rms=100.0`, `padding_ms=350`) con descarte instantáneo de silencios (0 ms) y runner `whisper.cpp` AVX1 con soporte tmpfs (`/dev/shm`).
  * Script de compilación `scripts/debian/build_whisper_avx1.sh` con flags estrictos CMake (`-DGGML_AVX=ON -DGGML_AVX2=OFF -DGGML_FMA=OFF -DGGML_AVX512=OFF -DGGML_CUDA=OFF`) garantizando compatibilidad con procesadores Ivy Bridge sin SIGILL.
  * Harness comparativo `scripts/benchmark_stt.py` ejecutado en bare-metal físico HTPC (Intel Core i5-3470, 4 cores AVX 1.0, 14GB RAM):
    - `ggml-base-q5_1.bin` seleccionado como modelo óptimo de producción: 2617 ms latencia promedio, RTF 2.107, 136.9 MB RAM pico, 100% precisión en comandos canónicos de TV en español ("abrir netflix", "pausar", "subir volumen", "buscar blade runner").
    - Modelo small (`ggml-small-q5_1.bin`) descartado para CPU mínima por latencia excesiva (~9.4s, RTF 7.567).
  * Gates: 254/254 tests pytest passing (9 nuevos en `tests/test_local_stt.py`), `bash -n` limpio; commits de producto `fad6e33` y `45ab922`. Habilita T-139.
- T-139 implementado por LRP INGENIERO, verificado y cerrado como `APTO`:
  * Motor NLU local de intenciones en `backend/local_intent.py`: analizador semántico determinista ultra-rápido (latencia 0.01ms - 0.25ms, superando límite <50ms por 200x) sin dependencias de librerías Torch ni instrucciones AVX2.
  * Catálogo de intenciones strictly allowlisted: `launch_kiosk` (netflix, youtube, primevideo, spotify, etc.), `media_control` (teclas de reproducción, volumen y mute en Linux uinput), `search` (queries sanitizadas) y `system_control` (toggle_osd, open_settings, close_kiosk).
  * Normalización fonética y corrección de alucinaciones/transcripciones fonéticas de whisper ("posar" -> KEY_PLAYPAUSE, "buscar blader anero" -> "blade runner", "yutup" -> youtube, etc.).
  * Filtro de seguridad activo: rechazo inmediato de inyecciones de shell (`;`, `&`, `|`, `` ` ``, `$`, `>`, `<`, `\`) y path traversal.
  * Desconexión definitiva de Supabase `ai-proxy`: `backend/ai_pipeline.py` orquesta la voz de forma 100% local y offline (audio -> ffmpeg in-memory -> VAD -> whisper.cpp AVX1 en thread asíncrono -> local_intent -> backend dispatch). Eliminada dependencia de `LICENSE_TOKEN`.
  * Gates: 263/263 tests pytest passing (9 nuevos en `tests/test_local_intent.py`), `bash -n` limpio; commit de producto `6099d50`.
  * PARADA DE CONTROL PREVIA A T-140 ALCANZADA: flujo detenido conforme al mandato del dueño para dirección visual de la PWA 2.0.
- T-140 diseño visual y plan técnico aprobados por el dueño:
  * Extracción de maqueta completada en `NEWUI.MD`: sistema ergonómico radial Mantatomic para control desde el sofá con una sola mano, trackpad háptico masivo y dock de Quick Apps.
  * Título canónico fijado a `Linux Remote Player`.
  * Salida de audio PipeWire y menú de energía alojados dentro de `Settings Drawer` para preservar la pantalla principal ultra limpia.
  * Remodelación completa del launcher de apps ("Más Apps") a `LRP App Hub` (estilo Apple TV / Google TV): tarjetas squircle de 72px, live indicator, búsqueda en tiempo real, chips de categoría y catálogo "1-Tap Add".
  * Plan técnico formal `implementation_plan.md` aprobado por el dueño; T-140 marcado `ready` y despachado brief a LRP INGENIERO.
- T-140 implementado por LRP INGENIERO, verificado y cerrado como `APTO`:
  * Backend: endpoints `/api/system/power/*` (`suspend`, `reboot`, `poweroff`, `restart-service`) con protección por token y fallback transparente `LRP_MOCK_POWER`. Cobertura unitaria en `tests/test_system_platform.py` (8/8 PASSED).
  * Sistema de Diseño: `frontend/skins.css` con tokens Dark Obsidian Glassmorphism (`#070A0E`, `#0D1117`, surface glass), halos difusos neón (`glow-green`, `glow-blue`, `glow-red`), textura micropunteada de trackpad, tarjetas squircle de 72px con live indicators pulsantes, sectores polares de rueda radial y chips de categoría.
  * Marcado HTML: `frontend/index.html` con cabecera minimalista (Settings, título canónico `Linux Remote Player`, badge de estado y latencia), Quick Dock de 4 accesos rápidos, trackpad masivo con canal de scroll lateral, barra de utilidades de 5 accesos, botón flotante 'X' de cierre, rueda radial Mantatomic con geometrías polares SVG exactas sin solapamientos táctiles, Settings Drawer con selector de sinks PipeWire y slider maestro, y LRP App Hub con buscador reactivo, chips, catálogo 1-Tap Add y modal de confirmación en 2 pasos para energía.
  * Invariante móvil B1/T-79: preservada estrictamente sin `viewport-fit=cover`.
  * Lógica de cliente: `frontend/app.js` con soporte contextual Hero Center (`KEY_ENTER` en modo D-Pad vs `KEY_SPACE` en multimedia), conmutación reactiva de sinks de audio PipeWire, gestión de energía en 2 pasos y motor de búsqueda para el hub de apps.
  * Gates: 254/254 tests pytest passing, `bash -n` limpio; commit de producto `348113b`.
  * T-140 queda `APTO`; T-141 (LRP OS bootable USB ISO factory) queda `ready`.
- T-140 Remediación visual y funcional completada conforme a validación humana interactiva:
  * Scroll lateral independiente: `#scroll-strip` posicionado como columna flex derecha `w-7 shrink-0` fuera de `#touchpad`, eliminando la invasión central del trackpad.
  * Header: corregida duplicación visual `Connection: Stable Stable` a `Connection: Stable`.
  * Quick Dock dinámico & Long-Press: interacción táctil de pulsación prolongada (450ms con vibración háptica y supresión de click de 800ms) para pinear/despinear apps desde el App Hub hacia el Quick Dock superior (`lrp_pinned_apps` en `localStorage`), retiro de botones `×` permanentes de tarjetas y sustitución por indicador de pin.
  * Ajustes LRP OS: reorganizado a layout de columna única completa (cards legibles de ancho completo), retiro total de sección obsoleta `Social & Feedback` y desacople de voz offline (`showVoice = true`), eliminando el bloque comercial "Comprar licencia (Voz IA)".
  * Skin "Day" por defecto: fijada como predeterminada con calibración de alto contraste (fondo claro cálido `#f4f0e6`, textos `#1f2937`, bordes tenues y vectores SVG contrastados en `#374151`).
  * Skin "Anime": transparencia total de `.app-chassis` y `#touchpad` (`background-color: transparent !important`), con gradiente suave que permite apreciar nítidamente la ilustración de fondo `anime-bg.webp`.
  * Catálogo de apps enriquecido: integración oficial de AnimeAV1 (`https://animeav1.com`, color `#7C3AED`, badge `AV1`) y 14 presets populares (Stremio, AnimeFLV, Crunchyroll, YouTube TV, Netflix, Disney+, Prime Video, Pluto TV, Twitch, Kick, Spotify, Apple TV+, Kodi, RetroArch).
  * Invariante B1/T-79: preservada estrictamente (`user-scalable=no` sin `viewport-fit=cover`).
  * Gates: 8/8 tests en `test_system_platform.py`, 15/15 en `test_beta_channel.py`, 254/254 suite completa, 14 scripts shell validados con `bash -n`; commit de producto `024cd8b`.
  * T-140 formalmente `APTO`; T-141 (LRP OS bootable USB ISO factory) queda `ready`.
- Diagnóstico y resolución de arranque físico TV / panel de estado diferido:
  * Evidencia física en HTPC (192.168.0.246): `systemctl show linuxremoteplayer.service` confirmó `NRestarts=1` con reinicio forzado a los ~70s del arranque (`sep 6 22:03`).
  * Causa raíz 1 (DHCP Race & Lockout de 60s en `backend/run.py`): al arrancar, `detect_ip()` ejecutaba una sola vez mientras DHCP de `enp2s0` estaba en vuelo, devolviendo `127.0.0.1`. `monitor_ip` dormía 60s incondicionalmente antes de detectar el cambio de IP y disparar `os._exit(3)`.
  * Causa raíz 2 (X11 Display Race en `backend/kiosk.py` y `backend/main.py`): `linuxremoteplayer.service` iniciaba con LightDM pero antes de que el servidor Xorg `:0` y `.Xauthority` aceptaran conexiones de usuario `lrp`; Firefox ESR crasheaba inmediatamente al fallar la conexión a pantalla.
  * Causa raíz 3 (Ventana raíz negra Openbox y firmware TV): Openbox no pintaba fondo (`xsetroot`), manteniendo pantalla negra por >60s, lo que activaba en Smart TVs HDMI el diálogo *"Detección automática de dispositivos no conectados"*.
  * Remediación aplicada:
    1. `backend/run.py`: nueva función `get_initial_ip(timeout=8.0)` para sondear DHCP en los primeros segundos de arranque sin caer en loopback; sondeo rápido de 2.0s en `monitor_ip` si la IP inicial fuera loopback.
    2. `backend/kiosk.py`: funciones `is_display_ready()` y `wait_for_display(timeout=10.0)` con comprobación `xset q` previo al lanzamiento de Firefox, y verificación de supervivencia de proceso (`poll()`) post-spawn.
    3. `backend/main.py`: `/api/panel/show` adaptado a `require_local_or_token` para permitir invocación local por scripts de sesión sin requerir token dinámico.
- Remediación integral de UI Mobile 2.0 PWA (Testing de usabilidad previo a LRP OS ISO):
  * Retiro definitivo de Licencia: eliminado el bloque `<details>` de Licencia en Ajustes y el ítem de FAQ correspondiente en `frontend/index.html`; la voz y temas en v2.0 operan en modo local y offline sin Supabase ni claves de activación.
  * Indicador visual de skin activa: incorporados badges de selección `.skin-swatch.active` con bordes acentuados, halos difusos y checkmark `✓` (`.skin-swatch-check`); `setSkin()` se invoca de forma síncrona inmediata al cargar el script, evitando pantallas oscuras no sincronizadas.
  * Reconstrucción semántica de temas: variables CSS dedicadas (`--wedge-bg`, `--wedge-border`, `--wheel-icon-fill`, `--wheel-icon-stroke`, `--hero-*-bg`, `--scroll-strip-*`, `--scroll-thumb-*`) para `day`, `night`, `cafe` y `anime` en `frontend/skins.css`.
  * Barra de scroll lateral de alta visibilidad: `#scroll-strip` y `#scroll-thumb` estilizados con píldora acentuada de 32px, brillo sutil y contraste impecable tanto en fondos claros ("Day") como oscuros ("Night", "Café", "Anime").
  * Rediseño radial Mantatomic continuo: reemplazo de polígonos irregulares por sectores anulares matemáticamente simétricos con líneas frontera compartidas (`stroke-width: 1.5px`); radio exterior ampliado a $R_{out} = 202$ con `viewBox="-15 0 390 250"`, eliminando espacios muertos y ajustando el margen con el botón flotante 'X' a 16px exactos.
  * Corrección de cuelgue táctil y estabilidad de WebSocket:
    1. `scratch/simulate_lrp_ui.py`: manejo de frame `ping` con respuesta inmediata `pong` para evitar timeouts de heartbeat cada 15s; respuesta de autenticación homologada a `{"status": "success", "message": "Authenticated"}`.
    2. `frontend/app.js`: `togglePinApp()` ahora actualiza los pins visuales en el App Hub mediante `updateAppPinBadges()` manipulando exclusivamente los badges sin destruir el árbol DOM mientras el usuario mantiene el dedo presionado; límites establecidos a 4 apps máximo y 1 mínimo.
  * Verificación determinista: 272/272 tests pytest passing, `bash -n` limpio, 0 advertencias críticas.
- D43: Refinamiento ergonómico, visual y de conectividad en Mobile 2.0 PWA:
  * Rueda radial Mantatomic y botón Play: apertura angular simétrica de 30° (75° a 105°) en los anillos exterior e interior, creando un canal de separación limpio y uniforme de 10.8px en ambos costados del botón central Play/Pausa (r=28 en cx=180, cy=65) sin colisiones de cuñas.
  * Vector de navegación Atrás: icono SVG rediseñado con flecha curva de retorno de trazo nítido (2.4px) con fill="none" y stroke="currentColor"; selector CSS en frontend/skins.css actualizado para prevenir que trazados con fill="none" se rellenen con polígonos sólidos.
  * Captura de puntero y robustez en botón de Micrófono: #mic-btn ahora usa setPointerCapture / releasePointerCapture y previene contextmenu; retirado el listener destructivo pointerleave que reseteaba micHeld antes de que getUserMedia resolviera.
  * Simulación de voz WebSocket: simulate_lrp_ui.py ahora recibe mensajes mixtos (text y binary bytes), permitiendo el flujo de blobs de audio sin emitir excepciones WebSocketDisconnect ni cerrar la sesión.
  * Causa raíz del cuelgue Cliente PWA desconectado: corregido el temporizador de heartbeat en frontend/app.js donde heartbeatTimeoutId nunca se cancelaba al recibir pong, lo que provocaba que cada 15 segundos el cliente cerrara su propio socket por falso timeout; ahora se cancela de inmediato al llegar pong y la tolerancia se amplió a 8s.
  * Apps por defecto y unpinning en App Hub: renderApps() integra obligatoriamente todas las apps predeterminadas y del catálogo base (BUILTIN_APPS_MAP) en appMap, asegurando que Netflix, YouTube y Spotify siempre figuren en MIS APLICACIONES del App Hub con su pin badge y puedan desanclarse con pulsación prolongada.
  * Iconos consistentes y prevención de duplicados: función unificada getAppIconElement() que provee SVGs y badges oficiales de alta resolución para todas las marcas (Netflix, YouTube, Spotify, AnimeAV1, Stremio, AnimeFLV, Crunchyroll, etc.) tanto en Quick Dock como en las tarjetas squircle del App Hub; renderCatalogGrid() excluye apps ya existentes por URL/ID, eliminando entradas dobles al añadir desde el catálogo 1-Tap; deduplicación de lrp_pinned_apps con Set.
  * Barra de scroll en categorías: #hub-chips configurado con scrollbar-width: none; ::-webkit-scrollbar { display: none; } para ocultar la barra horizontal mientras conserva el desplazamiento táctil fluido.

## 2026-09-07 · D44 — Play Button Tactile/Visual Feedback, App Hub Edit Mode & Voice Category

Conforme a las solicitudes de usabilidad del dueño para la Mobile App 2.0 PWA:
- Feedback integral en botón central Play:
  * Feedback táctil y de pulsación (`:active` / `.pressed`): escala `scale(0.90)`, halo difuso azul brillante `#2563EB` (`filter: drop-shadow(0 0 16px rgba(59, 130, 246, 0.95))`), vibración háptica de 35ms y registro de eventos `pointerdown`/`pointerup`/`pointercancel` en `frontend/app.js` para respuesta táctil instantánea sin lag en pantallas móviles.
  * Estado activado / reproducción en curso (`.is-playing`): animación keyframe `pulse-play-glow` con respiración de halo azul vivo, toggle dinámico entre vectores SVG `#hero-vector-play` (`▶`) y `#hero-vector-pause` (`⏸`), y actualización de tooltip contextual. En modo navegación (`navMode`), conmuta a `#hero-vector-ok` y emite `KEY_ENTER`.
- Eliminación de catálogo redundante y modo edición de apps:
  * Retiro definitivo de la sección redundante `Disponibles para añadir (1-Tap)` (`#catalog-grid`); todas las plataformas preconfiguradas residen directamente en `BUILTIN_APPS_MAP` y en la biblioteca principal ("Aplicaciones Disponibles").
  * Botón `Editar` (`#btn-edit-apps`) en la cabecera del App Hub con toggle a `Listo` (azul activo) y bloqueo de aperturas accidentales durante edición.
  * Contrato estricto Ocultar vs Borrar:
    1. Apps predeterminadas / de sistema: solo pueden ocultarse (`toggleHideApp`), persistiendo sus IDs en `localStorage.hidden_apps`; nunca se eliminan. Muestran botón de acción ámbar `—` (ocultar).
    2. Apps personalizadas añadidas por el usuario (`custom_apps`): muestran botón de acción rojo `✕` (`deleteCustomApp`) que las elimina definitivamente de `localStorage` y del Quick Dock.
    3. Apps ocultas en modo edición: se muestran semi-transparentes (`is-hidden-app`, opacidad 0.42, escala de grises) con botón verde `+` (mostrar/desocultar) para restaurarlas en cualquier momento, además del botón inferior de restauración masiva.
- Categoría "Con Voz" y badge de comandos por voz:
  * Chip de filtro `🎙 Con Voz` (`data-category="voice"`) en `#hub-chips`.
  * Propiedad `hasVoice: true` asignada a YouTube y YouTube TV en `BUILTIN_APPS_MAP`.
  * Filtro dinámico en `renderApps()` y banner de ayuda superior (`#hub-voice-tip`): indica el comando por voz especial *"Buscar [canción o película]"* al mantener presionado el micrófono.
  * Badge visual `voice-badge` anclado en la esquina superior izquierda de las tarjetas (`top: 3px; left: 5px;`), eliminando cualquier solapamiento sobre el icono central de la app.
  * Integración visual limpia del botón `Editar`: reubicado en la cabecera del App Hub a la derecha junto al botón cerrar con píldora simétrica, icono SVG, hover y estado activo azul.
  * Banner de consejos por voz (`#hub-voice-tip`): desacoplado de la grilla de 4 columnas a un contenedor superior de ancho completo (100%) bajo los chips de categoría, con badge de "Voz 100% Local" y comando formateado en caja monoespaciada.
- Verificación: 261/261 tests pytest passing, `test_system_platform.py` 8/8 passing, 14 scripts shell validados con `bash -n`, `node --check frontend/app.js` exit 0, simulador UI respondiendo 200 OK en `http://localhost:8000/`.

## 2026-09-07 · D45 — Multi-Skin Contrast Calibration, Universal Deduplication & Quality Brand Icons/Favicons

Conforme a las observaciones del dueño sobre contraste en skins, apps repetidas y calidad de iconos:
- Calibración integral de contraste y botones radiales en todas las skins:
  * Causa raíz: `#mic-btn` y `#btn-close-app` carecían de reglas CSS base en SVG `<circle>` y trazados, provocando que los navegadores aplicaran el valor por defecto de SVG `fill: black; stroke: none` en fondos oscuros (Night, Café, Anime), renderizándolos como círculos negros sólidos sin icono interior.
  * Solución CSS & SVG: atributos nativos de respaldo `fill="rgba(16,185,129,0.16)" stroke="#10B981"` en `#mic-btn` y `fill="rgba(239,68,68,0.16)" stroke="#EF4444"` en `#btn-close-app`. Reglas base y animaciones `:active`/`.recording` agregadas en `frontend/skins.css`.
  * Calibración temática dedicada: overrides para `[data-skin="cafe"]` (tonos cálidos madera `#cd8b62`, trazos ámbar `#e0a35c` en cuñas, iconos `#f4ecdf`) y `[data-skin="anime"]` (magenta/violeta neón `#9333ea`, trazos `#c084fc`, iconos `#f5d0fe`, tarjetas de vidrio translúcido).
- Deduplicación universal de aplicaciones y saneamiento automático:
  * Causa raíz: las aplicaciones añadidas previamente en `localStorage.custom_apps` o sugeridas por backend con IDs divergentes (ej. `disney` vs `disneyplus`, o `custom_17...` para apps ya catalogadas) no colisionaban con las claves de `BUILTIN_APPS_MAP`, resultando en múltiples entradas para la misma plataforma.
  * Solución determinista: funciones `normalizeUrl()` y `getCanonicalAppKey(app)` en `frontend/app.js` que resuelven alias (`disney` -> `disneyplus`, `youtube_tv` -> `youtubetv`, `max` -> `hbomax`), normalizan dominios y comparan nombres fonéticos/canónicos.
  * Saneamiento reactivo: `renderApps()` consolida duplicados preexistentes en `localStorage.custom_apps` hacia su entrada canónica y purga registros duplicados del almacenamiento del navegador. `addCustomApp()` detecta colisiones antes de insertar y desoculta si la app ya existía.
- Motor unificado de iconos de alta calidad (Brand SVGs & Favicons):
  * Causa raíz: el selector `if (app.color)` antecedía a `if (app.url)`, forzando que todas las apps con color asignado mostraran cuadros planos con iniciales en lugar de vectores de marca o favicons; además, el dock y el hub divergían en su resolución de metadatos.
  * Solución unificada: `getAppIconElement(app, size)` implementa una jerarquía estricta para dock (`size === 'dock'`) y tarjetas del hub (`size === 'card'`):
    1. Iconos vectoriales oficiales SVGs de alta definición para plataformas reconocidas: Netflix, YouTube, YouTube TV, Spotify, Disney+, Prime Video, Twitch, Crunchyroll, Apple TV+, Kodi, RetroArch, Stremio, Pluto TV, Kick, AnimeAV1, AnimeFLV, TikTok y Max (HBOMax).
    2. Aplicaciones del sistema Linux: `/api/icon/${app.id}`.
    3. Plataformas web / URLs personalizadas: extracción de hostname y descarga de favicons de alta resolución (128px) vía DuckDuckGo / Google s2 (`setTileFavicon`).
    4. Fallback: monograma tipográfico con fondo de acento.
- Verificación: `node --check frontend/app.js` exit 0, `pytest tests/test_system_platform.py -v` 8/8 passed, simulador UI respondiendo 200 OK en `http://localhost:8000/`.

## 2026-09-07 · D46 — Multi-Skin SVG Contrast Remediation & Button Legibility Guarantee

Conforme a las pruebas de contraste en diferentes skins reportadas por el dueño:
- Causa raíz de iconos negros en skins oscuras e ilustradas (Anime/Night/Café):
  * En la especificación SVG de W3C, cualquier figura vectorial (`polygon`, `rect`, `path`) sin atributo `fill` definido ni regla CSS aplicable adopta por omisión `fill: #000000` (negro absoluto).
  * En `frontend/skins.css`, los selectores de tema dependían de atributos literales `[fill="#F3F4F6" i]` y `[stroke="#F3F4F6" i]`. Dado que el marcado de `frontend/index.html` no contenía tales cadenas, ninguna de las reglas de skin se activaba sobre las figuras de la rueda Mantatomic, provocando que los botones de salto (`>>`, `<<`), pista anterior (`|<<`), cuerpo de altavoces de volumen e icono Home se dibujaran en negro sólido (invisible sobre fondos oscuros o fondos de anime con sombras).
- Remediación sistemática en SVG y CSS:
  1. `frontend/index.html`: inyección de `fill="currentColor"` en todos los vectores sólidos de la rueda radial (`.wedge-btn`) y en `#hero-vector-play polygon`.
  2. `frontend/skins.css`:
     - `.wedge-btn` propaga `color: var(--wheel-icon-color, #F3F4F6)`.
     - `.icon-group` hereda `color: inherit` y aplica `fill: currentColor` a `polygon`, `rect` y `path:not([fill="none"])`, y `stroke: currentColor` a `polyline` y trazos.
     - Skin "Day": cuñas calibradas con fondos tenues `rgba(0, 0, 0, 0.04)` y trazos `0.14`; figuras vectoriales en `#374151 !important`; agregado selector para `#hero-vector-pause rect` en `#2563EB` (previamente ausente, lo que dejaba el icono de pausa blanco sobre círculo celeste); feedback visual al pulsar donde el icono pasa a blanco `#FFFFFF` al oscurecer el círculo a `#2563EB`; barra de utilidades `.util-btn` con texto y vectores oscuros en `#1F2937`.
     - Skin "Café": completadas variables de tokens `--surface-glass`, `--border-subtle`, `--text-primary`; cuñas en `rgba(224, 163, 92, 0.10)`, iconos en crema cálido `#F4ECDF !important`.
     - Skin "Anime": reconstrucción completa para contraste sobre ilustración viva:
       * Cuñas de rueda Mantatomic con vidrio violeta enriquecido (`rgba(76, 29, 149, 0.48)`, trazo `rgba(216, 180, 254, 0.55)`, `backdrop-filter: blur(8px)`).
       * Iconos de cuña forzados a blanco puro `#FFFFFF !important` con `filter: drop-shadow(0 1px 3px rgba(0, 0, 0, 0.90))`.
       * Botón de voz (`#mic-btn`) con fondo más brillante `rgba(16, 185, 129, 0.38)`, trazo `#34D399` e icono blanco nítido.
       * Botón de cierre (`#btn-close-app`) con fondo `rgba(244, 63, 94, 0.38)`, trazo `#FB7185` y cruz blanca `#FFFFFF` de trazo 2.4px con drop-shadow.
       * Barra utilitaria (`.util-btn`) con texto `#FFFFFF` y sombras `text-shadow: 0 1px 3px rgba(0, 0, 0, 0.85)`.
       * Quick Dock con vidrio de 12px de desenfoque y etiquetas de texto contrastadas con sombra.
- Verificación determinista:
  * `node --check frontend/app.js`: exit 0.
  * `pytest tests/test_system_platform.py -v`: 8/8 passed.
  * `bash -n` en la totalidad de scripts shell: 0 errores.
  * Servidor simulador en vivo sirviendo las nuevas reglas de contraste.

## 2026-09-07 · D47 — Full-Size Authentic Squircle App Cards & Proportional Icon Hierarchy (T-140)

Conforme a la solicitud del dueño de hacer los iconos del tamaño completo de su cuadro en el App Hub ("Aplicaciones Disponibles"), eliminando el efecto de tarjeta anidada / marco doble con icono reducido:
- Causa raíz del doble marco / icono miniatura:
  * `createAppTile()` creaba un contenedor externo `.squircle-card` (68x68 px, padding 8px) y dentro incrustaba `iconBox = getAppIconElement(app, 'card')` que tenía dimensiones fijas de 40x40 px (`w-10 h-10`) con su propio fondo y borde, y dentro un SVG de 24x24 px.
  * El resultado visual era un icono diminuto (24px) flotando en un cuadro de 40px dentro de un marco de 68px. En la skin Day, `.squircle-card` recibía un fondo beige claro que creaba un marco visible alrededor de los cuadros negros de Netflix, YouTube, Spotify, etc., dando apariencia de 'estampilla enmarcada' con pérdida de distinción visual.
- Arquitectura de tarjeta squircle auténtica y jerarquía proporcional:
  1. Contenedor unificado: `card = getAppIconElement(app, 'card')` retorna directamente el elemento `.squircle-card` (68x68 px con border-radius de 18px), sin caja anidada redundante. El cuadro de la app ES la tarjeta squircle de la marca.
  2. Escalado vectorial de marca:
     - Logotipos cuadrados (Netflix, YouTube, Spotify, Prime Video, Twitch, Crunchyroll, Kodi, RetroArch, Stremio, Pluto TV, Kick, AnimeAV1, AnimeFLV, TikTok, Max): escalados a 44x44 px (`w-11 h-11`), ocupando ~65% de la tarjeta de 68px con proporciones idénticas a los launchers nativos de iOS/Android/tvOS.
     - Logotipos anchos (Disney+, Apple TV+, YouTube TV): adaptados a 52x36 px (`w-13 h-9` / `w-13 h-10`) para máxima visibilidad sin cortes.
     - Aplicaciones nativas de sistema y web favicons: escalados a 44–48 px (`object-contain`).
     - Tipografía inicial de fallback: escalada de `text-xs` a `text-xl font-bold tracking-tight`.
  3. Quick Dock: mantiene dimensiones proporcionales 44x44 px (`w-11 h-11 rounded-xl`) con SVGs de 28x28 px (`w-7 h-7`), alineado con `#more-btn` (actualizado a `w-11 h-11` con SVG `w-6 h-6`).
  4. Protección de fondos de marca en temas Day, Café y Anime:
     - En `frontend/skins.css`, los selectores de tema para `.squircle-card` se acotaron exclusivamente a `.squircle-card.surface-glass`. Las tarjetas con fondos oficiales de marca (`bg-black`, `bg-[#1A1D24]`, `bg-[#FFDA00]`, etc.) conservan su estética original pura sin ser sobreescritas por el tinte beige de Day o el marrón de Café.
  5. Contención de badges y modo edición:
     - Badges de voz (`voice-badge`) y anclaje (`pin-badge`) anclados directamente en las esquinas internas de `card` (`top: 3px; left: 5px` y `top: 3px; right: 5px`).
     - Botones de acción en modo edición (`actionBtn`) montados en `cardWrapper` (`relative shrink-0`) anclados a `top: -4px; right: -4px` para evitar ser recortados por el `overflow: hidden` del squircle.
  6. Utilidades de dimensión en `frontend/tailwind-lite.css`: agregadas clases `.w-11`, `.h-11`, `.w-13`, `.h-9`, `.h-10` requeridas para el nuevo escalado.
- Verificación determinista:
  * `node --check frontend/app.js`: exit 0.
  * `py -3.14 -m pytest tests/test_system_platform.py -v`: 8/8 passed.
  * `wsl -e bash -c 'for f in scripts/*.sh scripts/debian/*.sh; do [ -f "$f" ] && bash -n "$f"; done'`: 0 errores.
  * Servidor simulador UI en vivo (`task-2905`) sirviendo las tarjetas squircle auténticas.

## 2026-09-07 · HANDOFF — Cierre de Sesión Mobile App 2.0 (T-140 APTO, T-141 READY)

- **Estado de entrega**: T-140 (Rediseño Mobile App 2.0 PWA) completamente implementado, auditado y verificado (APTO).
  * Refinamientos cerrados: D43 (rueda radial simétrica 30°, botón play con canal 10.8px, vector curvo de retorno, captura de micro, heartbeat fix), D44 (feedback táctil y halo play, modo edición de apps con ocultar vs borrar, categoría "Con Voz"), D45 (calibración de contrastes, deduplicación canónica, iconos oficiales), D46 (remediación multi-skin SVG fill currentColor y drop-shadows), D47 (tarjetas squircle 68x68 auténticas sin marco doble, iconos a tamaño completo 44x44 / 52x36).
- **Evidencia verificada**:
  * 261/261 tests pytest passing (0 fallos, 0 regresiones).
  * `test_system_platform.py` 8/8 passed.
  * `node --check frontend/app.js`: exit 0.
  * 12 scripts shell validados con `bash -n`: 0 errores.
  * Invariante móvil B1/T-79 (`user-scalable=no` sin `viewport-fit=cover`) intacta.
- **Archivos modificados en worktree (`codex/debian-foundation`)**:
  * `frontend/app.js`
  * `frontend/index.html`
  * `frontend/skins.css`
  * `frontend/tailwind-lite.css`
- **Plano de control**:
  * `.agents/PLAN_v2.0-appliance.md` actualizado (T-140 APTO, T-141 READY).
  * `.agents/CURRENT.md` actualizado con `active_job: HANDOFF` y `active_task: T-141`.
- **Próxima acción para la siguiente sesión**: Despachar brief de implementación para T-141 (LRP OS bootable USB ISO factory con live-build en Debian 13 minimal).

## 2026-10-17 · D48 — Product priority over task test suites, Zero-IO protocol and Flash worker topology

Decisión del dueño para optimizar la velocidad y el consumo de contexto en el plano de control:
1. **Prioridad producto sobre cobertura de tests durante tareas**:
   - Se eliminan suites de prueba pesadas y auditorías exhaustivas por tarea individual.
   - La verificación en tarea se enfoca en el cumplimiento funcional del producto.
   - La detección de bugs, regresiones y la ejecución de la suite completa de pruebas se concentran exclusivamente en la auditoría final de fase (`G4`) con dictamen del Auditor.
2. **Protocolo Cero-IO en modelos pesados**:
   - Arquitecto (`42a6a909...`), Ingeniero (`fdfc68b2...`) y Auditor (`ae7b054f...`) NUNCA ejecutan lecturas completas de archivos, escrituras, búsquedas de código ni comandos directos en sus propios contextos.
   - Delegan todo el trabajo operativo a subagentes/workers persistentes con `Model: "flash"`:
     * Arquitecto: `Arch-Flash` (asistente persistente de control).
     * Ingeniero: `Eng-Flash-1` (Constructor) y `Eng-Flash-2` (Inspector).
     * Auditor: `Aud-Flash` (ejecutor persistente de auditoría y pruebas).
   - Los workers `flash` se mantienen vivos durante toda la fase y solo se terminan (`kill`) al cerrar la fase.
   - La lectura directa en modelos pesados se restringe estrictamente a rangos quirúrgicos (`StartLine`/`EndLine` <= 25 líneas) ante dudas críticas puntuales.
3. **Verificación desacoplada Constructor / Inspector**:
   - `Eng-Flash-1` (Constructor) implementa el código según el brief del Ingeniero.
   - `Eng-Flash-2` (Inspector, contexto `flash` independiente) audita `git diff`, verifica cada criterio de aceptación con referencias `archivo:línea` y corre micro-checks deterministas ultrarrápidos (<2s: `bash -n`, `py_compile`, `node --check`).
4. **Respuestas de workers Flash concisas**:
   - Límite estricto de <150 palabras por mensaje de worker flash. Formato de recibo determinista: `git status -s`, `git diff --stat`, `archivo:línea`, exit code de 1 línea.

## 2026-10-17 · D49 — Context-Guided Briefs and Single-Task Flow

Decisión del dueño para eliminar el consumo innecesario de tokens y prevenir extravíos de contexto en workers:
1. **Despacho unitario de tareas**: Arquitecto e Ingeniero nunca despachan un plan completo en one-shot ni asignan múltiples tareas concurrentes a ciegas. Se despacha estrictamente una tarea acotada a la vez (ej. `T-141`), se valida y registra el recibo determinista (`git status -s`, `git diff --stat`, `archivo:línea`, exit code), y solo tras aprobación se procede a la siguiente (`T-142`).
2. **Contexto guiado obligatorio en briefs**: Todo brief a workers `flash` debe incluir rutas de archivo absolutas o relativas exactas, números de línea o nombres de funciones ancla, y extractos pertinentes de `APPCORE.md` o `INDEX.md`, garantizando que el worker ejecute su tarea sin realizar búsquedas exploratorias no guiadas.

## 2026-10-17 · D50 — Milestone Closure PLAN_v2.0-appliance.md (T-140..T-142 APTO, G4: APTO)

Entrega y cierre de fase auditada y aprobada:
1. **T-140 APTO (commit `964f66f`)**:
   - Refinamientos finales Mobile 2.0 PWA (D43..D47): tarjetas squircle de 68x68 a tamaño completo (iconos 44x44 / 52x36), contraste multi-skin SVG (fill currentColor y drop-shadows), modo edición (ocultar vs borrar), chip y categoría 'Con Voz', scrollbar lateral independiente y resolución de CSS sync (Gate B: `check_css_sync.py` exit 0).
2. **T-141 APTO (commit `b1f8d65`)**:
   - LRP OS bootable USB ISO factory: receta `live-build` (`scripts/debian/iso/build_iso.sh`) para Debian 13 minimal con instalador target desatendido (`lrp-install-target.sh`) con salvaguarda fail-closed contra instalación en el USB de arranque, swap zram al 50% (`zram-generator.conf`), y suite `tests/test_iso_factory.py` (5/5 passed, `bash -n` exit 0).
3. **T-142 APTO (commit `50da3ca`)**:
   - Firma criptográfica asimétrica Ed25519 en manifiestos OTA (`backend/ota_security.py`), clave pública embebida (`scripts/debian/lrp-ota-pub.pem`), herramienta de firma offline (`scripts/sign_ota_manifest.py`), protección anti-downgrade y watchdog de auto-rollback transaccional de 45 segundos en `/usr/local/bin/lrp-update`. Cierre definitivo del riesgo estructural B19. Validado con `tests/test_ota_signing_rollback.py` (6/6 passed).
 4. **Veredicto de Fase G4: APTO**:
   - Auditor de fase (`ae7b054f...`) emitió dictamen verde unánime: `check_css_sync.py` exit 0, `node --check frontend/app.js` exit 0, `bash -n` en todos los scripts shell exit 0, y 59/59 tests passed en las 9 suites de Appliance v2.0.
   - Arquitecto ratifica cierre completo de `PLAN_v2.0-appliance.md`.

## 2026-10-21 · MAINTAIN — Reconciliación de control tras `[STATE]` 88cf2f6

Correcciones de estado contra repo verificado (no cambia alcance ni producto):

1. `CURRENT.md`: `source_commit` `98bb9f1` → `88cf2f6`; `dirty` true → false; `next_action` consumido
   (autorización de commit/push ya ejecutada) reemplazado por PLAN del release 2.0.0; lista duplicada
   de estados T-132..T-142 retirada porque el plan es su único hogar.
2. `INDEX.md`: `source_commit` y estado reindexados; retirada la cifra "283 tests passing" del índice.
3. `PLAN.md`: PH27/T-141 deja de figurar como "Activo/READY"; la cabecera refleja plan cerrado y
   pendiente release 2.0.0.
4. `AGENTS.md`: B19 se declara cerrado por T-142 en `codex/debian-foundation`, con bloqueo de
   promoción vigente mientras `main` no integre la rama.
5. `APPCORE.md`: la superficie beta ya no describe el rebuild D35 como "uncommitted"; aclara que los
   módulos v2.0 existen solo en `codex/debian-foundation` @ `50da3ca` y que el conteo de tests
   pertenece al plan.

Evidencia: artefacto beta rehash `a0b54c85…` = manifiesto = sidecar; sin `dist/` ni referencias
`25ea41…`; `git rev-list --left-right --count origin/main...main` = `0 0`; `main` @ `88cf2f6`.

Corrección (2026-10-21, misma fecha): la frase "sin referencias `25ea41…`" vale solo para `main` y
el worktree. La rama `codex/debian-foundation` sí contiene `25ea4173…` como artefacto
`website/beta/downloads/linuxremoteplayer_1.99.2_amd64.deb` (331202 bytes) y como SHA en su
`latest.json`/sidecar; ese rebuild es el que D51 resuelve publicándolo como `2.0.0`.

## 2026-10-21 · D51 — Aprobación del plan de release 2.0.0

Decisión del dueño sobre el preflight de `PLAN_v2.0.0-release.md`:

1. **D-R1**: merge `--no-ff` de `codex/debian-foundation` @ `50da3ca` en `main`, preservando los 17
   commits `[T-NN]`.
2. **D-R2**: congelar el artefacto beta `1.99.2` en `a0b54c85…`; el rebuild `25ea4173…` se publica
   como `2.0.0` firmado.
3. **D-R3**: `LICENSE` no se modifica en 2.0.0; cualquier relicenciamiento es decisión separada.

Digest del diseño canónico: `2814bb3c3252c3a6435db1c6e3b127300f72df7db850f42479159233d5661a76`
(992 bytes UTF-8/LF, verificado contra el archivo). Con esto el plan queda `approved` y CURRENT pasa
a `RUN THE LOOP` con `T-143` ready.

## 2026-10-21 · D52 — Rotación del ancla de confianza OTA

El dueño informó que no localiza la clave privada Ed25519 de la ancla vigente
(`scripts/debian/lrp-ota-pub.pem`, introducida por T-142). Búsqueda en el host: 133 archivos de clave,
62 con material privado, ninguna coincidencia; `~/.ssh/prod_rsa_private.pem` es RSA 2048 y no
corresponde. Los manifiestos publicados (`1.9.1`, `1.99.2`) nunca tuvieron firma, así que no existía
cadena firmada válida que preservar. Decisión: rotar el ancla.

- Par Ed25519 nuevo generado con `scripts/sign_ota_manifest.py --generate-key`.
- Privada: `D:\AGUSTIN\Portafolio\Proyectos\lrp-keys\lrp-ota-priv.pem`, fuera del repo; nunca se
  versiona. Pública replicada en `scripts/debian/lrp-ota-pub.pem` y
  `backend/ota_security.py::DEFAULT_OTA_PUBLIC_KEY_PEM`.
- `website/beta/latest.json` firmado y verificado con la nueva pública.
- Riesgo aceptado: los clientes `1.9.1`/`1.99.2` ya instalados llevan la pública anterior y no
  podrán verificar releases futuros por OTA; 2.0.0 se distribuye por instalador/ISO. Si la privada
  antigua aparece, se puede reintroducir como ancla secundaria.



