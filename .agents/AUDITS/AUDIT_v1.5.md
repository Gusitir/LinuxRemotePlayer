# AUDITORÍA PESADA — v1.5.0 (Cozy Media)

```yaml
audit_id: AUDIT_v1.5
date: 2026-07-09
auditor: Claude (Opus) — harness Read/Grep sobre archivos reales (Windows), NO bash (ver nota)
scope: exhaustiva — backend, frontend, scripts, supabase, website, config/deploy
verdict: APTO PARA VENTA tras aplicar los BLOQUEANTES (todos ya corregidos o con acción git pendiente)
method_note: >
  El mount de bash (/mnt) TRUNCA archivos grandes (app.js real=1402 líneas, mount=1116).
  Toda esta auditoría se hizo con las herramientas del harness (Read/Grep) que leen la ruta
  Windows real y completa. La validación de sintaxis (node --check / py_compile) debe correrse
  en WSL — el mount NO sirve para eso. Regla permanente para futuras auditorías en este entorno.
```

## RESUMEN
Base v1.5.0 sólida. Cero vulnerabilidades graves de código. Los problemas encontrados fueron
de **configuración/despliegue** (dominio incorrecto en el manifest de actualización) y de
**deriva de CSS** (clase faltante), ambos ya corregidos. Modelo de autenticación coherente.

---

## BLOQUEANTES (corregidos en esta sesión; requieren commit+push+deploy)
```yaml
- id: B1
  sev: CRITICAL
  area: deploy
  file: website/latest.json
  problem: >
    deb_url apuntaba a https://linuxremoteplayer.com (dominio NO poseído) en vez de
    linux-remote-player.vercel.app. Rompía el OTA por completo (descarga 404). Además
    version="v1.5.0" (con prefijo v inconsistente) y archivo con relleno de bytes nulos
    (visto en el mount).
  fix: reescrito limpio -> dominio Vercel, version "1.5.0", sha256 real verificado
       (3b3b97c8...), campo notes. HECHO. Falta: git commit+push (Vercel republica).
- id: B2
  sev: HIGH
  area: config
  file: supabase/functions/send-feedback/index.ts
  problem: correo destino fallback = soporte@linuxremoteplayer.com (inexistente).
  fix: -> Deno.env SUPPORT_EMAIL || aeciminer02@gmail.com. HECHO. Falta:
       `supabase functions deploy send-feedback --no-verify-jwt`.
- id: B3
  sev: MEDIUM
  area: repo-hygiene
  path: pkg/
  problem: la carpeta de staging del .deb (37 archivos, duplica backend/frontend/scripts)
    quedó RASTREADA en git tras el build de Gemini. Bloat + confusión.
  fix: añadida a .gitignore. HECHO. Falta: `git rm -r --cached pkg/` + commit.
```

## HALLAZGOS DE CÓDIGO (no bloqueantes)
```yaml
- id: C1
  sev: SYSTEMIC (RIESGO RECURRENTE)
  area: frontend/tailwind-lite.css
  problem: >
    tailwind-lite.css se compila a mano y se DESINCRONIZA del markup. Ya causó 2 bugs
    (`.hidden` faltante -> redundancia de licencia + overlay nav siempre visible; utilidades
    de overflow/max-w faltantes -> scroll horizontal en Ajustes). Cada vez que se añaden
    clases nuevas al HTML sin añadirlas al CSS, se rompe algo EN SILENCIO.
  status: los casos conocidos ya parcheados manualmente.
  recommendation: >
    Añadir un check en build_deb.sh (o pre-commit) que extraiga las clases usadas en
    index.html/app.js/status.html y avise de las que falten en tailwind-lite.css. Alternativa
    de fondo: generar el CSS con el CLI real de Tailwind en el build (mantiene "sin build" en
    runtime pero elimina la deriva). Es la deuda técnica #1 del frontend.
- id: C2
  sev: LOW
  area: backend/main.py:352
  problem: un `except:` desnudo (captura SystemExit/KeyboardInterrupt).
  fix: cambiar a `except Exception:`.
- id: C3
  sev: LOW
  area: frontend/app.js:61,226
  problem: buyUrl fallback hardcodeado 'https://buy.stripe.com/mock-link' (placeholder muerto).
    El backend siempre devuelve buy_url real en /api/config, así que no se usa; limpiar.
- id: C4
  sev: INFO (defensa en profundidad)
  area: backend/main.py /api/icon
  problem: si un .desktop de confianza tuviera Icon=/ruta/absoluta, se serviría ese archivo.
    NO explotable por red (app_id se valida contra apps instaladas; icon_val viene de
    .desktop del sistema). Aceptable. Opcional: restringir a dirs de iconos conocidos.
- id: C5
  sev: INFO
  area: repo
  file: reicon_map.json (raíz)
  problem: verificar si es artefacto del build de iconos Reicon; si no se usa en runtime,
    considerar moverlo a docs/ o gitignore. (No revisado a fondo.)
```

## LO QUE ESTÁ BIEN (verificado)
```yaml
security:
  - subprocess: siempre con listas de args, sin shell=True. app/launch usa shlex.split sobre
    Exec de .desktop de confianza (app_id validado). pkill con patrón estrecho chromium.*--kiosk.
  - CORS: allow_origins=[] (solo mismo origen).
  - Auth model COHERENTE:
      require_token (PAIRING_TOKEN): apps, kiosk launch/kill, app/launch, debug, license*,
        update/apply, panel/show, ws.
      require_local (solo 127.0.0.1/::1/localhost): pairing-pin, pairing-token(+regen),
        pairing-qr, status, /status, system/update.
      require_local_or_token: update/check (teléfono con token O panel local).
      sin auth por diseño: health, config, ca, pair(PIN LAN), icon(<img>).
  - /api/system/update: require_local interno -> NO expuesto a la LAN. OK.
  - Sin secretos en código commiteado: Edge Functions usan Deno.env; backend usa .env
    (gitignored) y .env.example sin valores reales. supabase/.temp gitignored.
  - XSS: tiles/listas construidas con DOM (createElement/textContent), no innerHTML con datos.
  - Licencia: validación vía Edge Function; sin service_role en el dispositivo; gracia 72h.
correctness:
  - QR de emparejamiento: dark=#000 sobre light=#fff, border=4 (quiet zone) -> escaneable.
  - Home: close_all() ya NO relanza el panel (APPLIANCE_IDLE_PANEL removido de ahí) -> deja
    escritorio limpio; el panel vuelve por el monitor de inactividad (45s).
  - PinManager: PIN 6 dígitos, TTL 120s, un solo uso, anti-fuerza-bruta (5/IP + 20 global).
  - uBOL: URL resuelta dinámicamente vía API de GitHub (asset .chromium.zip versionado);
    instalado en $HOME (snap Chromium no lee /opt); flatten de subcarpeta.
```

## VERIFICACIÓN PENDIENTE (WSL — no factible en este entorno por truncado del mount)
```
node --check frontend/app.js         # confirmar sintaxis (real=1402 líneas)
node --check frontend/status.html?   # (es HTML; validar manualmente)
python3 -m py_compile backend/*.py
bash -n scripts/*.sh website/install.sh
grep -ri "linuxremoteplayer\.com" --include=*.json --include=*.ts .   # esperado: 0
```

## ACCIONES GIT/DEPLOY PENDIENTES (dueño / Gemini)
```
git rm -r --cached pkg/
git add -A && git commit -m "fix: latest.json domain/version, feedback email, status-panel links, ignore pkg/"
git push
supabase functions deploy send-feedback --no-verify-jwt
# verificar en vivo: latest.json (dominio vercel + 1.5.0), deb 200, sha256 match
```

## DEUDA TÉCNICA PRIORIZADA (para próximas versiones grandes)
1. C1 — deriva tailwind-lite.css (check automatizado o CLI de Tailwind en build). ALTA.
2. ai-proxy Edge Function para voz (mover claves NVIDIA/OpenRouter fuera del dispositivo). ALTA (bloquea venta de la función de voz).
3. Stripe modo LIVE + dominio propio + verificación de dominio en Resend. ALTA (bloquea venta real).
4. Limpieza: buyUrl mock-link (C3), except: desnudo (C2), reicon_map.json (C5). BAJA.
```
