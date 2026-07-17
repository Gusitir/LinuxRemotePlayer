# ESTADO ACTUAL

VERSION commiteada y PUBLICADA: 1.7.0 (Firefox). Repo PRIVADO. Licencia: Elastic 2.0.
Fase activa: TESTING INTENSIVO v1.7.0 (matriz en .agents/TESTING.md). PH14c en PLAN.md.
Modelos: Gemini 3.5 Pro ejecuta; Claude (tier "Fable5 Alto" desde 2026-07-17) planifica
y audita — toda afirmación con salida real de comando.

## RESUMEN v1.6/v1.7 (cerrados; detalle en .agents/archive/ y git log)
- v1.6.0 (2026-07-14): bugs del HTPC + hardening. G-01..G-18 + C-01..C-10 auditados.
  Smoke-test 7/7 funcional. Release verificado en vivo (sha256 match).
- v1.7.0 (2026-07-14): migración a Firefox + uBlock Origin vía policies.json, CA por
  política, Home en Wayland (KWin DBus), pactl deps, opción no-suspensión, higiene .deb.
  F-01..F-07 + FC-01..FC-03 auditados APTO. Release verificado en vivo:
  sha256 4fff17226f3d451a64b68eabf904445b93b1e81a38941f627d8b03538a434833 == manifest.
- Llaves reales de Together.ai viven en backend/.env (NO trackeado, verificado) con
  ENABLE_VOICE=true — solo para pruebas del dueño.

## PRÓXIMO PASO
1. DUEÑO: ejecutar la matriz A-J de .agents/TESTING.md en HTPC limpio + teléfono;
   registrar [OK]/[FALLA]/[SKIP] y volcar FALLAS en la sección RESULTADOS.
2. CLAUDE: triar FALLAS -> tareas [T-NN] del plan v1.7.1/v1.8.
3. GEMINI: ejecutar esas tareas (mismo protocolo: un commit por tarea + evidencia).
Los ítems F1/F2 de la matriz alimentan G-15 (safe-area) y G-16 (icono PWA) — pendientes
desde v1.5 por falta de modelo/screenshots del teléfono.

## LIMPIEZA 2026-07-17 (esta sesión)
- TESTING.md de raíz ELIMINADO (obsoleto: Chromium, install por git clone). Sustituido
  por .agents/TESTING.md. README actualizado (2 referencias).
- Archivados en .agents/archive/: PLAN_GEMINI_v1.6.md, PLAN_GEMINI_v1.7.md,
  AUDIT_G07_G13_Report.md. CURRENT.md compactado (histórico en git).
- AGENTS.md: registrados TESTING.md, archive/ y el cambio de modelo.

## HALLAZGOS GEMINI
(Gemini: anota aquí lo que encuentres fuera del alcance de tu tarea. NO lo arregles.)

## ⚠ ENTORNO — regla permanente
El mount de bash (/mnt) TRUNCA archivos grandes (app.js real ~1400 líneas). Leer/editar/
auditar SOLO con herramientas del harness; builds .deb SOLO en WSL con clon fresco.
py_compile/node --check sobre la ruta real (Windows) es válido. Aplica también a Gemini:
verificar `wc -l` vs lo que su herramienta lee antes de editar archivos grandes.

## CHECKLIST DEL DUEÑO (pendiente)
- [ ] Ejecutar matriz de testing (.agents/TESTING.md) y traer RESULTADOS.
- [ ] `supabase functions deploy send-feedback --no-verify-jwt` (sin confirmar desde v1.5).
- [ ] Commit+push de esta limpieza (.agents reorganizado + TESTING.md raíz eliminado).

## PENDIENTES GRANDES ANTES DE VENDER
- [ ] ai-proxy Edge Function (claves fuera del dispositivo). Bloquea venta de voz;
      prerrequisito del APK v2.0 (FASE E en archive/PLAN_GEMINI_v1.6.md; PH15 en PLAN.md).
- [ ] Stripe modo LIVE + dominio propio + verificación de dominio en Resend.
- [ ] Deuda conocida teclado: < > (KEY_102ND) y corchetes AltGr en es/latam.

## HISTORIAL DE FASES (resumen)
- F1-8 MVP+seguridad; C1-C6 comercialización; F9 emparejamiento PIN; F10 (v1.4) pulido;
  F11 (v1.5) Cozy Media; F12 (v1.6) bugs HTPC+hardening; F13 (v1.7) Firefox.
- F14 (actual): testing intensivo v1.7.0 -> correcciones -> luego ai-proxy / APK v2.0.
