# NEWUI.md — Especificación Técnica del Rediseño Mobile PWA 2.0

Documento de extracción de diseño y especificación técnica de interfaz a partir de la maqueta ergonómica para HTPC (*Mantatomic Ergonomic Radial Arc Wheel System*).

---

## 1. Filosofía de Diseño y Concepto

- **Paradigma**: Operación con una sola mano (Thumb-first ergonomics) desde el sofá.
- **Estética**: *Dark Obsidian Glassmorphism* con acentos de neón difuso (Cyberpunk minimalista).
- **Estructura espacial**: División vertical modular en 5 zonas:
  1. Header de Estado y Conectividad.
  2. Dock de Lanzamiento Rápido de Aplicaciones (Quick Apps).
  3. Trackpad Háptico Masivo con Franja de Scroll Independiente.
  4. Barra de Herramientas del Sistema (5 accesos directos).
  5. Controlador Radial Ergonómico en Arco ("Mantatomic Wheel").

---

## 2. Sistema de Diseño y Tokens Visuales

### 2.1. Paleta de Colores

| Token | Hex / RGBA | Uso |
|---|---|---|
| `bg-app` | `#070A0E` | Fondo exterior / viewport global |
| `bg-chassis` | `#0D1117` | Fondo del contenedor principal |
| `surface-glass` | `rgba(255, 255, 255, 0.04)` | Superficies secundarias (dock, trackpad, botones) |
| `surface-glass-active` | `rgba(255, 255, 255, 0.08)` | Estados hover / pressed |
| `border-subtle` | `rgba(255, 255, 255, 0.08)` | Bordes de tarjetas y separadores (1px) |
| `border-highlight` | `rgba(255, 255, 255, 0.15)` | Resaltes de bisel superior (inner highlight) |
| `text-primary` | `#F3F4F6` | Títulos principales e iconos activos |
| `text-secondary` | `#9CA3AF` | Etiquetas secundarias y descripciones |
| `text-muted` | `#6B7280` | Indicadores terciarios y latencia |
| `accent-green` | `#10B981` / `#00E676` | Estado de conexión estable y Botón Hero Mic |
| `accent-green-glow` | `rgba(16, 185, 129, 0.35)` | Halo difuso de voz y conexión |
| `accent-blue` | `#3B82F6` / `#00D2FF` | Botón Hero Play/Pause |
| `accent-blue-glow` | `rgba(59, 130, 246, 0.40)` | Halo difuso de reproducción activa |
| `accent-red` | `#EF4444` | Botón flotante 'X' (Cerrar Kiosk) |
| `accent-red-glow` | `rgba(239, 68, 68, 0.35)` | Halo difuso de cierre de ventana |

### 2.2. Sombras y Efectos

- **Chassis Border**: `border: 1px solid rgba(255, 255, 255, 0.08)` con radio de curvatura de `36px`.
- **Glassmorphism Backdrop**: `backdrop-filter: blur(20px) saturate(180%)`.
- **Inner Bevel**: `box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.12), 0 8px 24px rgba(0, 0, 0, 0.5)`.
- **Glow Buttons**:
  - Micrófono: `box-shadow: 0 0 18px rgba(16, 185, 129, 0.45), inset 0 0 8px rgba(16, 185, 129, 0.2)`.
  - Play/Pause: `box-shadow: 0 0 18px rgba(59, 130, 246, 0.45), inset 0 0 8px rgba(59, 130, 246, 0.2)`.
  - Close 'X': `box-shadow: 0 0 12px rgba(239, 68, 68, 0.35)`.

### 2.3. Tipografía

- **Familia**: `system-ui, -apple-system, 'SF Pro Display', 'Inter', Roboto, sans-serif`.
- **Pesos**: Regular (`400`), Medium (`500`), SemiBold (`600`).
- **Escala**:
  - Header Title: `16px`, weight `600`, tracking `-0.01em`.
  - Connection status: `12px`, weight `500`.
  - Latency: `10px`, weight `400`.
  - Utility labels: `10px - 11px`, weight `500`, line-height `1.1`.

---

## 3. Desglose Detallado de Componentes

### 3.1. Header de Estado y Conectividad
- **Layout**: Fila horizontal (`display: flex; justify-content: space-between; align-items: center`).
- **Botón Settings (Izquierda)**:
  - Botón circular (~40px × 40px), fondo `surface-glass`, borde `1px solid border-subtle`.
  - Icono de engranaje minimalista centrado.
- **Título de la Aplicación (Centro)**:
  - Texto: `Linux Remote Player` (blanco plateado, centrado).
- **Badge de Conexión (Derecha)**:
  - Disposición vertical en 2 líneas:
    1. Icono de rayo `⚡` + `Connection:` en blanco/gris, seguido de `Stable` en `accent-green`.
    2. `Latency: 12ms` en tipografía reducida monocromática verde/gris.

### 3.2. Dock de Lanzamiento Rápido (Quick Apps)
- **Contenedor**: Tarjeta horizontal tipo cápsula con bordes redondeados (`border-radius: 20px`), fondo `surface-glass`.
- **Grid / Distribución**: 4 accesos rápidos equidistantes:
  1. **Netflix**: Fondo negro mate, isotipo clásico "N" rojo de alto contraste.
  2. **YouTube**: Fondo oscuro/grafito con isotipo rojo rectangular y triángulo de reproducción blanco.
  3. **Spotify**: Fondo oscuro con isotipo verde circular y ondas sonoras negras.
  4. **Más Apps**: Botón launcher del drawer de aplicaciones. Icono superior con tres puntos horizontales `...` y texto inferior `Más Apps`.

### 3.3. Trackpad Háptico Masivo
- **Propósito**: Superficie táctil maximizada para control de cursor en TV sin levantar el pulgar.
- **Geometría**: Rectángulo con bordes redondeados (`border-radius: 18px`), altura aprox. del 22-26% del viewport.
- **Textura**: Malla / matriz de puntos micropunteados (*dotted grid pattern*) de bajo contraste para feedback visual de desplazamiento.
- **Guía Central**: Cruceta de cuatro flechas tenues (Up, Down, Left, Right) en el centro geométrico.
- **Scroll Strip (Lateral Derecho)**:
  - Canal vertical independiente en el margen derecho interior.
  - Píldora deslizante indicadora de scroll vertical para navegación rápida por listas, páginas web y menús de streaming.

### 3.4. Barra de Accesos Rápidos del Sistema
- **Layout**: Fila horizontal de 5 botones de acción con icono superior y etiqueta inferior:
  1. **Virtual Keyboard**: Icono de teclado + etiqueta "Virtual Keyboard".
  2. **Backspace**: Icono `[⌫]` + etiqueta "Backspace".
  3. **D-Pad Toggle**: Icono de 5 puntos en cruceta + etiqueta "D-Pad Toggle" (alterna entre modo ratón libre y cruceta direccional TV).
  4. **Panel TV**: Icono de monitor de TV + etiqueta "Panel TV" (abre el Kiosk OSD de ajustes en pantalla grande).
  5. **OS Meta Menu**: Icono de cuadrícula 3x3 + etiqueta "OS Meta Menu" (emula tecla Super / lanzador de sistema operativo).

### 3.5. Botón Flotante 'X' (Close App)
- **Ubicación**: Esquina superior derecha de la zona de control radial, flotando justo debajo de "OS Meta Menu".
- **Visual**: Círculo de ~36px con borde rojo fino, icono `✕` rojo brillante y halo `accent-red-glow`.
- **Acción**: Cierre instantáneo de la aplicación en primer plano o retorno al escritorio/launcher.

### 3.6. Sistema de Rueda Radial en Arco ("Mantatomic")
El elemento central del diseño: una distribución geométrica concéntrica basada en arcos de circunferencia (sectores polares) optimizada para el movimiento pendular del pulgar.

#### A. Botón Hero Central - Play / Pause (Azul)
- **Ubicación**: Vértice superior del arco central.
- **Forma**: Botón circular grande (~54px × 54px).
- **Estilo**: Fondo azul medianoche con borde azul neón (`#3B82F6`), icono `⏯` blanco/celeste y brillo difuso periférico.

#### B. Botón Hero Inferior - Micrófono / Voz (Verde)
- **Ubicación**: Centro absoluto del borde inferior (fácil alcance sin estirar la mano).
- **Forma**: Botón circular grande (~56px × 56px).
- **Estilo**: Fondo oscuro con anillo verde neón (`#10B981`), icono de micrófono central y glow verde expansivo cuando está activo.

#### C. Anillo Interior (Controles de Navegación Básica)
- **Lado Izquierdo**:
  - Botón Home (`🏠`): Retorno a pantalla inicial / status OSD.
  - Botón Flecha Izquierda (`<`): Navegación lateral izquierda.
- **Lado Derecho**:
  - Botón Retorno / Volver (`↩`): Tecla Escape / Back en aplicaciones de TV.

#### D. Anillo Exterior (Arco Periférico Semicircular)
Dividido en cuñas curvadas (*curved wedge segments*) con ranuras de separación de 2px a 3px:
- **Flanco Izquierdo (Control Multimedia)**:
  - Cuña Superior: Avance Rápido / Siguiente (`⏩` / `⏭`).
  - Cuña Central: Rebobinar / Retroceso (`⏪`).
  - Cuña Inferior: Pista / Contenido Anterior (`⏮`).
- **Flanco Derecho (Control de Volumen y Salida)**:
  - Cuña Superior: Botón Secundario de Retorno (`↩`).
  - Cuña Central: Subir Volumen (`🔊+` / `+`).
  - Cuña Inferior: Bajar Volumen (`-`) / Mute (`🔇`).

---

## 4. Geometría Matemática del Controlador Radial

Para una replicación exacta en HTML5/CSS (SVG o `conic-gradient` / `clip-path`):

1. **Punto de Origen Polar (Centro Virtual)**:
   - Coordenadas: `(X: 50%, Y: 88%)` relativo a la base de la pantalla.
2. **Radios Concéntricos**:
   - Radio 0 (Hub Voz): `0px` a `28px` (Círculo de `56px`).
   - Radio 1 (Anillo Interior): `34px` a `68px` (Arco de botones Home/Back).
   - Radio 2 (Hero Play/Pause): Centrado en ángulo `90°` (arriba), radio orbital `85px`.
   - Radio 3 (Anillo Exterior): `74px` a `125px` (Sectores polares multimedia y volumen).
3. **Ángulos de Segmentación**:
   - Arco Izquierdo (Media): de `105°` a `195°` (distribuido en 3 cuñas de ~28° con gap de 2°).
   - Arco Derecho (Volumen): de `-15°` a `75°` (distribuido en 3 cuñas de ~28° con gap de 2°).

---

## 5. Matriz de Estados e Interactividad

| Elemento | Reposo (Default) | Activo / Pulsado (Active) | Estado Especial |
|---|---|---|---|
| **Botón Micrófono** | Anillo verde estático | Escala `0.95`, resplandor pulsante verde | Pulso continuo durante inferencia Whisper |
| **Botón Play/Pause** | Anillo azul estático | Escala `0.95`, resplandor azul intenso | Alterna icono Play / Pause según MPRIS |
| **Cuñas Radiales** | Superficie grafito mate | Fondo `rgba(255,255,255,0.15)`, feedback háptico | Inset shadow pronunciado |
| **Trackpad** | Malla de puntos estática | Flecha directiva iluminada bajo el punto táctil | Scroll strip se ensancha al tocar el borde |
| **Quick Apps** | Icono original saturado | Elevación / escala `1.05` | Indicador led inferior si la app está corriendo |
| **Botón 'X'** | Círculo rojo oscuro | Rojo brillante con halo `accent-red-glow` | Inactivo si no hay kiosk abierto |

---

## 6. Recomendaciones de Implementación Web (PWA 2.0)

1. **Contenedor Responsivo**:
   - `max-width: 440px; margin: 0 auto; height: 100dvh; display: flex; flex-direction: column; justify-content: space-between;`
   - Uso obligatorio de `env(safe-area-inset-top)` y `env(safe-area-inset-bottom)`.
2. **Construcción del Sistema Radial**:
   - Recomendado: Elementos `<svg>` con paths `<path d="M... A..." />` para los arcos polares, permitiendo targets táctiles exactos sin solapamiento de bounding boxes rectangulares.
3. **Optimización Táctil**:
   - `touch-action: none;` en la zona del trackpad y rueda radial para prevenir scroll accidental del navegador.
   - `navigator.vibrate([10])` en cada pulsación de botón radial para sensación de control físico.

---

## 7. Auditoría Exhaustiva de Controles: LRP Actual vs. Maqueta

### 7.1. Matriz de Cobertura de Controles

| Control / Función | En LRP v1.99 Actual | En Maqueta Imagen | Estado / Dictamen |
|---|---|---|---|
| **Trackpad Ratón** | Sí (`#touchpad`) | Sí (*Massive trackpad*) | ✅ **Cubierto** (Mejorado con textura dotted mesh y cruceta guía) |
| **Scroll Vertical** | Sí (`#scroll-strip`) | Sí (*Scroll strip*) | ✅ **Cubierto** (Integrado como canal derecho en trackpad) |
| **Comando por Voz** | Sí (`#mic-btn`) | Sí (*Hero Mic button*) | ✅ **Cubierto** (Posición inferior ergonómica con halo verde) |
| **Play / Pause** | Sí (`KEY_SPACE`) | Sí (*Hero Play/Pause*) | ✅ **Cubierto** (Posición cenital prominente con halo azul) |
| **Lanzador de Apps** | Sí (`#apps-row` + drawer) | Sí (*Quick Apps* + *Más Apps*) | ✅ **Cubierto** (Dock superior compacto de 4 accesos directos) |
| **Teclado Virtual** | Sí (`openKeyboard()`) | Sí (*Virtual Keyboard*) | ✅ **Cubierto** en barra de utilidades |
| **Borrar Texto** | Sí (`KEY_BACKSPACE`) | Sí (*Backspace*) | ✅ **Cubierto** en barra de utilidades |
| **Modo D-Pad / Ratón** | Sí (`toggleNavMode()`) | Sí (*D-Pad Toggle*) | ✅ **Cubierto** en barra de utilidades |
| **Panel TV OSD** | Sí (`showPanel()`) | Sí (*Panel TV*) | ✅ **Cubierto** en barra de utilidades |
| **Menú OS (Super)** | Sí (`KEY_LEFTMETA`) | Sí (*OS Meta Menu*) | ✅ **Cubierto** en barra de utilidades |
| **Cerrar App (Kill)** | Sí (`btn-close-app`) | Sí (*Close App 'X'*) | ✅ **Cubierto** (Glow rojo de alta visibilidad) |
| **Volumen +** | Sí (`KEY_VOLUMEUP`) | Sí (*Volume +*) | ✅ **Cubierto** en anillo exterior derecho |
| **Volumen -** | Sí (`KEY_VOLUMEDOWN`) | Parcial (compartido con Mute) | ⚠️ **Gap**: Requiere botón o cuña independiente de `Vol -` |
| **Silenciar (Mute)** | Sí (`KEY_MUTE`) | Parcial (icono mute) | ⚠️ **Gap**: Debe estar separado de `Vol -` para evitar disparos accidentales |
| **Seek Adelante (10s)** | Sí (`KEY_RIGHT`) | Sí (`⏩` Seek Forward) | ✅ **Cubierto** en anillo exterior izquierdo |
| **Seek Atrás (10s)** | Sí (`KEY_LEFT`) | Sí (`⏪` Seek Rewind) | ✅ **Cubierto** en anillo exterior izquierdo |
| **Pista Anterior / Siguiente** | No dedicado | Sí (`⏮` en flanco izquierdo) | 🚀 **Ganancia** en maqueta |
| **Home (Escritorio)** | Sí (`killKiosk()`) | Sí (`🏠` en anillo interior) | ✅ **Cubierto** |
| **Atrás (Browser Back)** | Sí (`sendCombo`) | Sí (`↩` flecha curva) | ✅ **Cubierto** |
| **Ajustes (Settings)** | Sí (`btn-settings`) | Sí (Engranaje superior) | ✅ **Cubierto** |
| **Estado y Latencia** | Sí (`#status`, `#latency`) | Sí (*Connection: Stable, 12ms*) | ✅ **Cubierto** (Diseño muy superior en header) |

---

## 8. Análisis de Gaps Críticos: Lo que FALTA para LRP OS Appliance

Al analizar las necesidades operativas de **LRP OS v2.0** como sistema operativo *turnkey* para TV (sin teclado ni ratón físico en el salón), se identifican **6 controles esenciales que NO están en la maqueta**:

### 8.1. GAP-01: Botón "OK / Select / Enter" para Navegación TV
- **Problema**: En la maqueta, el botón azul central superior es `Play/Pause`. Cuando el usuario activa `D-Pad Toggle` para navegar por menús de Netflix, YouTube, Stremio o el sistema OSD mediante flechas, pulsar `Play/Pause` **NO selecciona** elementos en la mayoría de interfaces de TV; se requiere estrictamente `KEY_ENTER`.
- **Riesgo**: El usuario queda atrapado en menús sin poder confirmar selecciones salvo cambiando al ratón.
- **Solución recomendada**: El botón central debe operar en modo dual o conmutar dinámicamente entre `OK / Enter` (cuando se está en modo D-Pad o navegando listas) y `Play/Pause` (cuando hay reproducción de medios activa). Adicionalmente, el tap en el trackpad debe disparar `Enter` en modo D-Pad.

### 8.2. GAP-02: Selector de Salida de Audio PipeWire (Ubicación: Dentro de Settings)
- **Decisión de Diseño**: La salida de audio se aloja **dentro del panel de Settings** para mantener la pantalla principal del control remoto 100% limpia y fiel a la maqueta visual.
- **Implementación en Settings**:
  - Tarjeta interactiva "Salida de Audio" que consulta y conmuta los sinks detectados vía `/api/system/audio/sinks`:
    * `[ 📺 HDMI TV ]` (Salida de audio digital a través del televisor).
    * `[ 🔈 Analógico ]` (Jack 3.5mm / Barra de sonido conectada al HTPC).
    * `[ 🎧 Bluetooth ]` (Auriculares o altavoces inalámbricos vinculados).
  - Slider de volumen independiente y sincronizado con PipeWire (`wpctl`).

### 8.3. GAP-03: Menú de Energía del HTPC (Ubicación: Dentro de Settings)
- **Decisión de Diseño**: El control de energía del HTPC se aloja **dentro del panel de Settings** para prevenir apagados o suspensiones accidentales desde la interfaz principal mientras se usa el mando.
- **Implementación en Settings**:
  - Módulo "Gestión de Energía" con botones claros y confirmación de seguridad rápida (modal de 2 pasos):
    * `Suspender`: Entra en suspensión de bajo consumo o apaga la señal de vídeo (DPMS off).
    * `Apagar HTPC`: Apagado limpio del sistema operativo (`systemctl poweroff`).
    * `Reiniciar HTPC`: Reinicio completo del host (`systemctl reboot`).
    * `Reiniciar Interfaz`: Reinicia el servicio `linuxremoteplayer` sin reiniciar el equipo físico.

### 8.4. GAP-04: Clic Derecho (Right-Click / Context Menu)
- **Problema**: En navegación web en TV o reproductores multimedia, el clic secundario es necesario para abrir menús contextuales, cambiar pistas de subtítulos, copiar o inspeccionar. El doble toque en pantallas móviles táctiles para simular clic derecho es propenso a errores.
- **Solución recomendada**: Gesto inequívoco de pulsación prolongada (long-press de 500ms) en el trackpad con feedback háptico, o botón secundario en la barra de utilidades.

### 8.5. GAP-05: Conmutador de Pantalla Completa (F11 / Fullscreen)
- **Problema**: Si una ventana de streaming pierde el foco o se abre fuera de pantalla completa en Firefox kiosk / Openbox, el usuario necesita forzar pantalla completa sin reiniciar la aplicación.
- **Solución recomendada**: Atajo de pantalla completa (`F11` / `Alt+Enter`) ubicado en la cuña superior derecha del anillo radial exterior (sustituyendo al botón `↩` redundante de la maqueta).

### 8.6. GAP-06: Asimetría y Redundancia en el Anillo Radial de la Maqueta
- **Defecto en la maqueta original**:
  - En el flanco derecho hay **dos botones de retorno idénticos (`↩`)**: uno en el anillo interior y otro en la cuña superior del anillo exterior.
  - En el anillo interior izquierdo hay una flecha izquierda (`<`), pero no existe la flecha derecha (`>`).
- **Optimización ergonómica**:
  - Eliminar el botón `↩` duplicado del anillo exterior y asignar esa cuña a **Pantalla Completa (`⛶`)**.
  - En el anillo interior: unificar la tríada de control del sistema: `Home` (`🏠`), `Escape / Back` (`↩`), y `Menu Contextual / Info` (`ℹ`).

---

## 9. Arquitectura del Panel de Ajustes (Settings Drawer PWA 2.0)

Al pulsar el botón `[⚙ Settings]` en la esquina superior izquierda de la pantalla principal, se despliega el drawer con los módulos del sistema agrupados:

```text
+-------------------------------------------------------------+
|                      AJUSTES LRP OS                         |
+-------------------------------------------------------------+
| 1. SALIDA DE AUDIO (PipeWire)                               |
|    (*) HDMI TV   ( ) Analógico (Jack)   ( ) Bluetooth       |
|    Volumen Master: [====|-----------] 65%                   |
+-------------------------------------------------------------+
| 2. GESTIÓN DE ENERGÍA                                       |
|    [ 🌙 Suspender ]    [ 🔄 Reiniciar ]    [ ⏻ Apagar ]      |
+-------------------------------------------------------------+
| 3. RED Y CONECTIVIDAD                                       |
|    Wi-Fi: "MiFibra-5G" (192.168.0.246) · [Cambiar red]      |
|    Bluetooth: Activo · [Emparejar dispositivo]              |
+-------------------------------------------------------------+
| 4. PREFERENCIAS DEL CONTROL                                 |
|    Sensibilidad Trackpad:  ( ) 1x   (*) 1.5x   ( ) 2x       |
|    Vibración Háptica:      [Activada]                       |
+-------------------------------------------------------------+
| 5. SISTEMA Y ACTUALIZACIONES                                |
|    Versión: 2.0.0 (Canal Beta) · [Buscar actualización]    |
|    Certificado HTTPS: [Descargar Certificado CA]            |
+-------------------------------------------------------------+
```

---

## 10. Arquitectura de Mapeo Definitiva (Plano de Replicación para T-140)

```text
+-------------------------------------------------------------+
|  [⚙ Settings]             Linux Remote Player   [⚡ Stable] |
|                                                   [ 12ms ]  |
+-------------------------------------------------------------+
|  +-------------------------------------------------------+  |
|  | [N Netflix]  [▶ YouTube]  [♫ Spotify]  [··· Más Apps] |  |
|  +-------------------------------------------------------+  |
+-------------------------------------------------------------+
|  +-------------------------------------------------------+  |
|  |                      ▲                                |  |
|  |             TRACKPAD HÁPTICO MASIVO                   |S |
|  |           (Dotted Mesh + Smooth Inertia)              |C |
|  |             ◄       [OK]       ►                      |R |
|  |                      ▼                                |O |
|  |                                                       |L |
|  +-------------------------------------------------------+L |
+-------------------------------------------------------------+
| [⌨ Teclado] [⌫ Borrar] [🎛 D-Pad] [📺 Panel TV] [▦ Menú OS]  |
+-------------------------------------------------------------+
|                                                   (✕ Cerrar)|
|                     ( ⏯ Play / OK )                         |
|                 /                     \                     |
|           (⏩ Seek+)                 (⛶ Fullscr)            |
|          /                             \                    |
|    (⏪ Seek-)     [🏠 Home]    [↩ Back]   (🔊 Vol +)         |
|        |                                    |               |
|    (⏮ Prev)             (( 🎙 ))           (🔉 Vol - / 🔇)  |
|                         Voz Local                           |
+-------------------------------------------------------------+
```

### 10.1. Mapeo de Teclas Físicas y Señales Backend

| Componente UI | Acción Primaria | Código uinput / Backend | Ubicación |
|---|---|---|---|
| **Hero Micrófono** | Grabación de voz (Push-to-Talk) | `backend/ai_pipeline.py` (Local STT + NLU) | Pantalla Principal (Centro Inferior) |
| **Hero Play / Pause** | Play/Pause / OK en menús | `KEY_SPACE` / `KEY_ENTER` | Pantalla Principal (Centro Superior Arco) |
| **Seek + (⏩)** | Avanzar 10 segundos | `KEY_RIGHT` | Pantalla Principal (Flanco Izquierdo) |
| **Seek - (⏪)** | Retroceder 10 segundos | `KEY_LEFT` | Pantalla Principal (Flanco Izquierdo) |
| **Track Prev (⏮)** | Pista / vídeo anterior | `KEY_PREVIOUSSONG` | Pantalla Principal (Flanco Izquierdo) |
| **Fullscreen (⛶)** | Alternar pantalla completa | `KEY_F11` | Pantalla Principal (Flanco Derecho) |
| **Volumen +** | Aumentar volumen +5% | `wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%+` | Pantalla Principal (Flanco Derecho) |
| **Volumen - / Mute** | Bajar volumen / Silenciar | `wpctl set-volume 5%-` / `toggle-mute` | Pantalla Principal (Flanco Derecho) |
| **Home (🏠)** | Retorno al escritorio LRP | Minimiza/cierra ventanas activas | Pantalla Principal (Anillo Interior) |
| **Back (↩)** | Volver / Cancelar | `KEY_ESC` / `browser_back` (Alt+Left) | Pantalla Principal (Anillo Interior) |
| **Cerrar (✕)** | Cerrar aplicación actual | `backend/kiosk.py close_kiosk()` | Pantalla Principal (Flotante Rojo) |
| **Settings (⚙)** | Abrir panel de ajustes | Abre Settings Drawer | Pantalla Principal (Header Izquierdo) |
| **Audio Sinks** | Selector de salida de audio | `/api/system/audio/sink` | **Dentro de Settings Drawer** |
| **Power Menu** | Suspender / Reiniciar / Apagar | `/api/system/power/*` | **Dentro de Settings Drawer** |

---

## 11. Remodelación del Launcher de Aplicaciones ("Más Apps" → LRP App Hub)

### 11.1. Diagnóstico del Diseño Actual ("Look Nerd / Problemático")
- **Iconos circulares diminutos (48px)**: Los favicons web se escalan pixelados o muestran letras iniciales toscas sobre fondos oscuros planos.
- **Formulario de desarrollador expuesto**: Campos crudos de texto para escribir a mano "Nombre" y "URL (https://...)" ocupando espacio permanente en pantalla.
- **Volcado de paquetes Linux**: Lista vertical tipo depuración ("Apps del sistema detectadas") con nombres crudos del sistema operativo.
- **Cero jerarquía ni filtros**: No hay categorización ni buscador para encontrar apps cuando la lista crece.

### 11.2. Nuevo Concepto: LRP App Hub (Estética Apple TV / Google TV)
Se transforma el drawer tosco en una **experiencia de catálogo de entretenimiento premium**:

1. **Grid de Tarjetas Squircle (72px × 72px)**:
   - Tarjetas tipo squircle (`border-radius: 20px`) con fondo `rgba(255, 255, 255, 0.05)`, borde sutil `1px solid rgba(255, 255, 255, 0.08)` y sombras profundas.
   - Logos oficiales vectoriales / PNG de alta resolución con relación de aspecto completa (no recortados en círculos).
   - Indicador de estado activo (*Live Indicator*): Si la app está abierta en la TV, la tarjeta muestra un punto verde brillante y un sutil borde pulsante.
2. **Buscador y Chips de Categoría**:
   - Barra de búsqueda superior: `[ 🔍 Buscar en catálogo... ]` con filtrado en tiempo real al escribir.
   - Chips horizontales deslizables para filtrar instantáneamente:
     * `[ Todos ]`
     * `[ 🎬 Cine y Series ]` (Netflix, YouTube, Prime Video, Disney+, Stremio, Plex, Crunchyroll)
     * `[ 🎵 Música ]` (Spotify, YouTube Music, Radio)
     * `[ 🌐 Web y TV ]` (Twitch, Kick, TikTok, Navegador Web libre)
3. **Catálogo "1-Tap Add" (Reemplazo del formulario URL manual)**:
   - En lugar de pedir al usuario que escriba URLs largas en el móvil, se presenta una galería visual de "Plataformas Populares Listas para Activar":
     * Cada servicio tiene su tarjeta con un botón `[+ Añadir]`.
     * Al tocarlo, se instala instantáneamente con el user-agent y flags VA-API optimizados para TV.
   - Para URLs arbitrarias, un único botón minimalista al final: `[+ Añadir enlace web personalizado]` que abre un modal limpio solo cuando se solicita.
4. **Gestión de Favoritos en el Dock Principal**:
   - Al mantener presionada cualquier app (long-press), aparece la opción de:
     * `★ Fijar en Quick Apps` (para sustituir o reordenar los 3 accesos rápidos de la pantalla principal).
     * `Ocultar app`.

### 11.3. Wireframe del Nuevo LRP App Hub (Modal Slide-Up)

```text
+-------------------------------------------------------------+
|                      APLICACIONES Y TV              [✕ Cerrar]
+-------------------------------------------------------------+
| [ 🔍 Buscar aplicación o streaming...                     ] |
+-------------------------------------------------------------+
| (• Todas)   ( Cine & Series )   ( Música )   ( En vivo / Web ) |
+-------------------------------------------------------------+
| MIS APLICACIONES INSTALADAS                                 |
|                                                             |
|  +---------+   +---------+   +---------+   +---------+      |
|  |    N    |   |    ▶    |   |    ♫    |   | Disney+ |      |
|  | Netflix |   | YouTube |   | Spotify |   | Disney+ |      |
|  +---------+   +---------+   +---------+   +---------+      |
|    • Activa                                                 |
|                                                             |
|  +---------+   +---------+   +---------+   +---------+      |
|  |  Prime  |   | Stremio |   | Twitch  |   | Crunchy |      |
|  |  Video  |   | Stremio |   | Twitch  |   |  roll   |      |
|  +---------+   +---------+   +---------+   +---------+      |
+-------------------------------------------------------------+
| DISPONIBLES PARA AÑADIR (1-TAP)                             |
|                                                             |
|  [ + Plex ]   [ + Apple TV+ ]   [ + Pluto TV ]   [ + Kick ] |
|                                                             |
|  [ ＋ Añadir URL personalizada... ]                         |
+-------------------------------------------------------------+
```

---

## 12. Implementación Final y Remediación (D43 / T-140)

La implementación en código (`frontend/index.html`, `frontend/skins.css`, `frontend/app.js`) materializó la especificación con los siguientes refinamientos físicos y ergonómicos:

1. **Rueda Radial Mantatomic SVG**:
   - Apertura angular simétrica de 30° ($75^\circ$ a $105^\circ$) en el arco exterior, generando una ranura de separación de 10.8px de despeje alrededor del botón Hero Play central ($r=28$ en $cx=180, cy=65$).
   - Cuñas de `Vol -` y `Mute` completamente independientes con trazados frontera limpios (`stroke-width: 1.5px`).
   - Vector de retorno 'Atrás' con flecha curva de 2.4px (`fill="none"`, `stroke="currentColor"`).
2. **Trackpad y Franja de Scroll Independiente**:
   - `#scroll-strip` posicionado en columna flex derecha `w-7 shrink-0` fuera de `#touchpad`, eliminando cualquier invasión central y proveyendo scroll vertical con cápsula acentuada de 32px.
3. **Quick Dock Dinámico y Long-Press**:
   - Persistencia en `localStorage` (`lrp_pinned_apps`); pulsación prolongada de 450ms con feedback háptico en tarjetas del App Hub para anclar/desanclar.
   - Apps base (Netflix, YouTube, Spotify) registradas en `BUILTIN_APPS_MAP` para permitir su desanclado; iconos vectoriales de marca unificados y prevención de duplicados en catálogo.
4. **Pantalla de Ajustes LRP OS**:
   - Layout de columna única completa (estilo iOS/Android Settings), retiro total de sección obsoleta `Social & Feedback` y eliminación de bloques comerciales de compra de licencia.
5. **Calibración de Temas**:
   - `Day`: tema por defecto de alto contraste (textos `#1f2937`, bordes sutiles y vectores en `#374151` sobre base `#f4f0e6`).
   - `Anime`: chasis y trackpad transparentes (`background-color: transparent !important`) para visualización directa de la ilustración `skins/anime-bg.webp`.
6. **Catálogo de Streaming Enriquecido**:
   - Incorporación oficial de **AnimeAV1** (`https://animeav1.com`, color `#7C3AED`, badge `AV1`) y 14 presets populares con flags optimizados para TV y VA-API.
   - Chips de categoría con scrollbar horizontal oculta (`scrollbar-width: none`).
7. **Estabilidad WebSocket**:
   - Cancelación inmediata del temporizador de timeout de heartbeat al recibir `pong` con tolerancia de 8 segundos, erradicando desconexiones periódicas cada 15 segundos.
   - Captura de puntero en micrófono con `setPointerCapture` / `releasePointerCapture` y prevención de menú contextual.



