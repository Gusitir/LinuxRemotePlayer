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
