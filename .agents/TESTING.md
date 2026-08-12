# TESTING — baseline y próximo ciclo

```yaml
baseline: 1.9.1
baseline_estado: APTO 6/6 en campo, 2026-07-30
proximo_ciclo: no abierto; espera selección de STT y flujo de trabajo
release_objetivo: 2.0.0
ejecuta_device: dueño; un agente puede diagnosticar por shell pero no sustituir experiencia
formato: "[OK] / [FALLA: descripción] / [NO VERIFICABLE: motivo]"
```

## BASELINE 1.9.1 — CERRADO

- [x] OTA 1.9.0 → 1.9.1; servicio quedó activo.
- [x] HUD correcto al cerrar/reabrir repetidamente en iPhone 8+ y 12.
- [x] `dpkg -V linuxremoteplayer` sin salida: se probó el paquete, no un parche local.
- [x] Actualizador sin dependencia de `/tmp/lrp-update.log`.
- [x] Health, licencia, voz cloud, docs 404, suspensión, CA y uso general correctos.

Resultado histórico completo disponible en git. No reutilizar esta matriz para certificar la
nueva arquitectura: mide nube/licencia y una actualización sobre un equipo existente.

## REGLAS DE CAMPO

1. El dueño ejecuta instalación limpia y experiencia desde el teléfono sin ayuda de agente.
2. El agente del HTPC no modifica archivos bajo `/opt/linuxremoteplayer`. Si el dueño se lo
   ordena, debe declarar cada cambio y adjuntar `sudo dpkg -V linuxremoteplayer`.
3. Evidencia literal o no cuenta. Ante un resultado inesperado se detiene y reporta.
4. Una prueba de device solo vale si antes `dpkg -V` confirma que el equipo es el paquete.
5. El auditor convierte fallas en bugs únicamente después de confirmar causa raíz.

## MATRIZ QUE DEBERÁ APROBAR LINUXREMOTEPLAYER 2.0.0

### TST-L1 — benchmark STT

- Español latino e inglés.
- Órdenes cortas, nombres propios, ruido de TV, silencio y micrófonos distintos.
- Whisper base/small: latencia fría/caliente, RAM, CPU, error y alucinación.
- Cada resultado incluye modelo exacto, cuantización, runtime, CPU e instrucciones disponibles.

### TST-L2 — Needle sin efectos

- Corpus gold de herramienta y argumentos.
- Off-topic, ambigüedad, negación, prompt injection hablado y valores fuera de rango.
- Umbral de confianza medido; ninguna salida de baja confianza se ejecuta.

### TST-L3 — pipeline local

- Audio del teléfono → texto → intención → acción permitida.
- Funciona con internet desconectado.
- Fallo del modelo no rompe touchpad, teclado, pairing ni control normal.
- CDP/BiDi, si existe, no escucha en LAN y no controla perfiles ajenos.

### TST-L4 — migración de usuario

- Instalación limpia sin cuenta, licencia ni clave.
- Upgrade desde 1.9.1 conserva pairing, apps, skins y configuración.
- Clave vieja no bloquea ni exige acción.
- Web ES/EN no ofrece compra, licencia ni servicio cloud y presenta correctamente Patreon.
- Las funciones Supabase de keys/licencias/IA ya no son necesarias ni reciben tráfico de 2.0.0.
- Desinstalación completa retira servicio, permisos, modelos, cachés y certificados propios.

### TST-L5 — OTA seguro

- Firma válida instala.
- Firma inválida, manifiesto modificado y downgrade abortan sin tocar el sistema instalado.
- Interrupción de red/energía no deja el servicio peor; health-check dispara rollback.
- Artefacto, manifiesto y versión coinciden con el commit auditado.

### TST-L6 — instalación limpia como usuario real

Sin agente asistente: instalar → certificado/QR/PIN → PWA → primer comando local. Anotar tiempo,
dudas, mensajes confusos, ruido, espera y recuperación. Este camino es obligatorio antes de una
release pública.

## NO ESCRIBIR TODAVÍA

Los comandos exactos y casillas de resultado se generan cuando existan una rama, modelos y
criterios aprobados. Escribirlos ahora produciría una matriz ficticia contra código inexistente.
