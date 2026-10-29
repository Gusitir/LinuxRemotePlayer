# LRP Remote (Android)

Wrapper WebView de LRP OS. No es una TWA: el panel vive en `https://<IP>:8000` dentro de la red
local, no en un dominio público.

## Compilar

Requiere JDK 17 y Android SDK 35. Con Gradle instalado, desde `android/`:

```bash
gradle wrapper          # una sola vez: genera ./gradlew
./gradlew assembleRelease
```

El APK queda en `app/build/outputs/apk/release/`. Si no hay configuración de firma, el archivo se
llama `app-release-unsigned.apk`.

## Firma

La firma **no vive en el repo**. Para firmar, creá `android/keystore.properties` (ignorado por git):

```properties
storeFile=/ruta/absoluta/lrp-release.jks
storePassword=...
keyAlias=lrp
keyPassword=...
```

Sin ese archivo el build de release compila sin firmar; CI/ops firma aparte. Un APK sin firmar no
se instala en un dispositivo normal.

## Certificado TLS

El backend de LRP OS usa una CA local que el teléfono no conoce. La app **acepta cualquier
certificado** (`onReceivedSslError` → `proceed()`) para poder abrir el panel, y lo advierte en la
pantalla inicial: *“Esta app acepta el certificado del equipo sin validarlo. Usala solo en tu red
local.”* Es una decisión explícita para un producto LAN-only; no se usa para tráfico de internet.

## Distribución

No se publica en Play Store. El APK se adjunta a las releases de GitHub
(`https://github.com/Gusitir/LinuxRemotePlayer/releases`).

## Alcance

- Solo `INTERNET`; tráfico en claro deshabilitado (`usesCleartextTraffic=false`).
- Sin telemetría, sin cuentas y sin red más allá de la URL que el usuario ingresa.
- La última URL se guarda en `SharedPreferences` del dispositivo.
