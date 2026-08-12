# LinuxRemotePlayer — plan de transición local

```yaml
base_estable: 1.9.1
destino: voz e interpretación locales; sin premium, pagos ni dependencia operativa de nube
estado: arquitectura aprobada; implementación no iniciada
regla: ninguna fase se convierte en tareas T-NN antes de medir sus prerequisitos
```

## ÍNDICE

| Fase | Objetivo | Estado |
|---|---|---|
| PH1–PH20 | Historia hasta 1.9.1 | Cerrada o superada; detalle en git y archive/ |
| GATE-OTA | Firma y actualización recuperable | Obligatorio antes de publicar otra versión |
| PH21 | Laboratorio STT local | Siguiente |
| PH22 | Needle 2 y contrato de acciones | Pendiente de PH21 |
| PH23 | Pipeline local integrado | Pendiente |
| PH24 | Retirada coordinada de nube/licencias/pagos | Pendiente de equivalencia funcional |
| PH25 | Calidad, CI y soporte multi-distro | Pendiente |
| PH26 | Modos escritorio/dedicado completos | Diseño futuro |
| PH27 | Imagen Debian para HTPC | Proyecto hermano posterior |

## PRINCIPIOS DE ARQUITECTURA

1. **Local significa local en runtime.** El uso normal no depende de APIs, cuentas, cuotas ni
   conexión a internet. Herramientas cloud pueden usarse durante desarrollo para generar casos,
   pero no forman parte del producto instalado.
2. **Modelos sin autoridad.** STT produce texto; Needle produce una intención; solo código
   determinista permite y ejecuta acciones.
3. **Fail closed.** Baja confianza, herramienta inexistente, argumentos fuera de rango o
   ambigüedad producen rechazo o confirmación, nunca una suposición peligrosa.
4. **Capacidades explícitas.** MPRIS primero; entrada simulada después; CDP/BiDi únicamente
   para capacidades que no existan por vías estables.
5. **Main es producción.** Los experimentos viven en rama/laboratorio y no sustituyen 1.9.1
   hasta pasar gates automáticos y pruebas en campo.
6. **Medir antes de soportar.** Hardware mínimo, modelo y latencia se deciden con corpus y
   máquinas reales.

# GATE-OTA — actualizar sin entregar root al origen

**B19 sigue siendo el riesgo estructural principal.** El hash y el paquete provienen del mismo
servidor; un compromiso del origen puede instalar código hostil como root.

Antes de cualquier release nueva:

- [ ] Firma criptográfica separada del manifiesto/artefacto.
- [ ] Clave pública embebida en el paquete; clave privada offline y fuera de Vercel/GitHub.
- [ ] Rechazo probado de firma inválida, manifiesto alterado y downgrade.
- [ ] Descarga en directorio `mktemp` propiedad de root; cerrar B19b/TOCTOU.
- [ ] Health-check posterior y rollback al paquete anterior si el servicio no levanta.
- [ ] Regla sudoers limitada al ejecutable y usuario necesarios, no al grupo completo.
- [ ] Documentar rotación/revocación de clave.

Destino posterior: repositorio APT firmado. No hace falta esperar al appliance para usar la
maquinaria estándar de Debian.

# PH21 — laboratorio de voz a texto local

## Pregunta

¿Qué STT ofrece español e inglés suficientemente precisos y rápidos en el hardware mínimo?

## Candidatos iniciales

- Whisper multilingüe `base`, cuantizado, con `whisper.cpp`.
- Whisper multilingüe `small`, cuantizado, con `whisper.cpp`.
- Los mismos o un candidato equivalente mediante sherpa-onnx si mejora empaquetado/rendimiento.
- Parakeet multilingüe solo como comparación; 600M parámetros impiden asumirlo como baseline.
- SenseVoice-Small queda fuera: no soporta español.

## Corpus mínimo

- Español latino e inglés.
- Órdenes cortas, naturales y parafraseadas.
- Nombres de aplicaciones, plataformas, títulos y personas.
- TV de fondo, silencio, voz lejana y micrófonos de distinta calidad.
- Casos negativos: conversación de la TV, ruido, órdenes incompletas y frases no dirigidas a LRP.

## Métricas

- WER/CER y, más importante, exactitud de slots relevantes.
- Latencia desde fin de habla hasta texto.
- RAM máxima y residente, CPU, temperatura y tamaño instalado.
- Alucinaciones con silencio y falsas activaciones.
- Primera inferencia frente a inferencias calientes.

## Gate de salida

Elegir runtime, modelo recomendado, posible perfil ligero y hardware mínimo. No hay números
aceptados hasta obtener resultados reproducibles.

# PH22 — Needle 2 y contrato de acciones

## Objetivo

Convertir texto en JSON limitado, sin ejecutar acciones reales durante la primera evaluación.

## Catálogo inicial

- `set_playback(action)`
- `seek_playback(direction, seconds)`
- `set_volume(action, value)`
- `open_application(app_id)`
- `search_media(service, query)`
- `open_media_result(position)`
- `resume_recent_media(timeframe, media_type)`
- `navigate_interface(action)`
- `send_shortcut(shortcut_id)`

Enums, rangos y patrones deben formar parte del esquema. Nada de `command`, `shell`, rutas
arbitrarias o código generado.

## Evaluación

- Corpus gold en español e inglés, incluidos off-topic y ambigüedad.
- Exactitud de herramienta y argumentos por separado.
- Umbral de confianza calibrado para minimizar acciones incorrectas.
- Pruebas de salida imposible, prompt injection hablado y frases adversariales.
- Validar soporte real de Linux x86-64, empaquetado, licencia MIT y actualizaciones del modelo.
- Fine-tuning LoRA solo si el modelo base no alcanza el gate y el dataset es reproducible.

# PH23 — pipeline local integrado

```text
PWA → audio LAN autenticado → VAD → STT → Needle → PolicyEngine
    → ContextStore(SQLite) → AdapterRegistry → MPRIS/CDP/entrada
```

- [ ] Servicio local con modelos precargados y límites de recursos.
- [ ] Política de confirmación/rechazo centralizada.
- [ ] Fast path determinista para acciones inequívocas si reduce latencia sin duplicar reglas.
- [ ] SQLite con migraciones, retención configurable y borrado desde la interfaz.
- [ ] Adaptadores que declaran capacidades; no prometer reanudación universal.
- [ ] CDP/BiDi ligado a `127.0.0.1`, perfil aislado y apagado cuando no se necesita.
- [ ] Descarga de modelos autenticada por checksum/firma y compatible con operación offline.
- [ ] Degradación clara: si el modelo falla, touchpad/teclado/control siguen funcionando.

Gate: superar al baseline 1.9.1 en privacidad y autonomía sin degradación inaceptable de
precisión/latencia en el hardware mínimo.

# PH24 — retirar nube, licencias y pagos

Una sola migración coordinada; no dejar estados híbridos invisibles.

- [ ] Backend: retirar validación de licencia, proxy cloud, cuotas y activación.
- [ ] Frontend: retirar compra, clave, plan, takeover y gates; voz disponible localmente.
- [ ] Supabase: archivar funciones/esquema de IA/licencias; el dueño realiza deploy/retirada.
- [ ] Website ES/EN: retirar Paddle, precio, premium y términos de venta; explicar privacidad local.
- [ ] Añadir Patreon como apoyo voluntario sin beneficios funcionales.
- [ ] README, docs, changelog, uninstall y `.env.example` coherentes.
- [ ] Definir licencia futura del proyecto en una decisión separada; “sin premium” no implica
  automáticamente cambiar Elastic 2.0 ni hacer público el repo.
- [ ] Política para usuarios de 1.9.1 con claves existentes: migración automática, sin perder
  configuración ni exigir intervención.

# PH25 — calidad y multi-distro

- [ ] Un comando local ejecuta lint, pruebas unitarias, contratos, build y auditoría de artefacto.
- [ ] CI en rama; `main` solo recibe entregas auditadas.
- [ ] Matriz de VM para Debian/Ubuntu primero; Fedora/Arch después de abstraer empaquetado.
- [ ] Pruebas de instalación limpia, upgrade, rollback, desinstalación y ausencia de red.
- [ ] Corpus STT/intents versionado sin audio privado del dueño.
- [ ] Benchmarks reproducibles por clase de CPU.

# PH26 — modos escritorio y dedicado

No decidido todavía si se separan agresivamente o mediante jerarquía visual. Principios ya
aceptados: guiar sin prohibir, salida de emergencia antes del bloqueo, sesión dedicada separada,
HUD adaptado al objetivo y acceso deliberado a funciones power-user. Diseño en IDEAS.md.

# PH27 — imagen Debian para HTPC

Proyecto hermano posterior: Debian estable, sesión dedicada, autologin de usuario sin sudo,
panel informativo con QR/PIN, navegador kiosk, PipeWire y LRP local. Debe heredar componentes
probados, actualizaciones firmadas y recuperación. La ISO instala; no reemplaza el mantenimiento
del sistema ya instalado. Ver IDEAS.md.

# PH17 — Skins 2.0 (diferida)

Ancla histórica conservada porque `design/skins2/` la referencia. Las propuestas siguen siendo
material de diseño, no trabajo activo. Cuando vuelva esta fase se replanteará sin gates Pro:
accesibilidad, layouts y temas estarán disponibles para todos. No leer ni implementar `design/`
hasta una decisión expresa del dueño.

## FUERA DEL PLAN ACTIVO

- Port de Windows: viable, solo ante demanda sostenida.
- Skins 2.0, gamepad, archivos y demo web: ideas válidas, sin prioridad hasta estabilizar la
  nueva base local.
- El antiguo roadmap Paddle/Pro/1.9.2/1.9.3 queda superado. La historia permanece en git.
