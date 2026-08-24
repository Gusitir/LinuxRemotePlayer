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
