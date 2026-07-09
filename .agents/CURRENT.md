# ESTADO ACTUAL

VERSION commiteada: 1.5.0 (Cozy Media). Repo PRIVADO. Licencia: Elastic License 2.0.
Última auditoría pesada: .agents/AUDITS/AUDIT_v1.5.md (2026-07-09) -> APTO tras bloqueantes.

## ⚠ ENTORNO — regla permanente
El mount de bash (/mnt) TRUNCA archivos grandes (app.js real=1402, mount=1116). Para leer/
editar/auditar usar SIEMPRE las herramientas del harness (Read/Grep/Edit), NUNCA bash para
archivos grandes. Validación de sintaxis (node/py_compile): SOLO en WSL.

## CAMBIOS ACUMULADOS SIN COMMIT (aplicados a archivos reales; pendientes de git+deploy)
- website/latest.json: dominio corregido a linux-remote-player.vercel.app, version "1.5.0",
  sha256 real (3b3b97c8...), notes. [BLOQUEANTE B1 — sin esto el OTA está roto]
- supabase/functions/send-feedback/index.ts: correo -> SUPPORT_EMAIL || aeciminer02@gmail.com. [B2]
- .gitignore: +pkg/ (staging del .deb quedó rastreado por error). [B3]
- scripts/install.sh: al final imprime enlaces del Panel de Estado
  (https://localhost:8000/status y https://127.0.0.1:8000/status), siempre visibles aunque
  el navegador no abra solo. [va dentro del .deb -> requiere rebuild v1.5.1]

## ACCIONES PARA CERRAR (git/deploy/WSL — no factibles en este entorno)
1. git rm -r --cached pkg/
2. git add -A && git commit -m "fix: latest.json, feedback email, status-panel links, ignore pkg/" && git push
3. supabase functions deploy send-feedback --no-verify-jwt
4. (opcional ahora / acumulable) rebuild v1.5.1 en WSL con el cambio de install.sh:
   VERSION 1.5.1 + CHANGELOG -> build_deb en WSL (clon fresco) -> copiar .deb a website/downloads/,
   borrar el 1.5.0 -> latest.json (1.5.1 + sha256 real) -> commit + push.
5. Verificar en vivo: curl latest.json (dominio vercel + versión), deb 200, sha256 match.

## PENDIENTES GRANDES ANTES DE VENDER (ver GUIA_AGUSTIN.md)
- [ ] ai-proxy Edge Function: mover claves NVIDIA/OpenRouter fuera del dispositivo (voz).
- [ ] Stripe modo LIVE + dominio propio + verificación de dominio en Resend.
- [ ] Deuda técnica #1: deriva de tailwind-lite.css (ver AUDIT_v1.5 C1).

## HISTORIAL DE FASES (resumen)
- F1-8: MVP + control sin IA + endurecimiento de seguridad (auditorías tempranas).
- F C1-C6: comercialización (Supabase Edge Functions, Stripe test, licencias, .deb, web).
- F9: emparejamiento (PIN de 6 dígitos, panel de estado TV, QR).
- F10 (v1.4): pulido para venta (categorías de Ajustes, skins, adblock, coach marks, Reicon).
- F11 (v1.5): Cozy Media UI + web compacta + fixes (QR contraste, Home escritorio, safe-area).
