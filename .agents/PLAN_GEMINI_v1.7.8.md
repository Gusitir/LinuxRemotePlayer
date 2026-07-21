# PLAN_GEMINI_v1.7.8 — Fix card "Comandos de voz" invisible en Ajustes

> Brief autocontenido para chat FRESCO de Gemini 3.5 Flash (ejecutor).
> Claude (Opus 4.8) planifica y AUDITA. Tú ejecutas. Una tarea = un commit = un
> checkpoint de auditoría. Lee TODO antes de tocar nada.

---

## 0. QUIÉN ERES Y QUÉ ES ESTO

Eres el ejecutor de código de **LinuxRemotePlayer**: una PWA (frontend vanilla JS,
sin build) que controla por WiFi un HTPC con Linux (backend FastAPI). Repo privado,
licencia Elastic 2.0. Versión publicada actual: **1.7.7**. Vamos a **1.7.8**.

Este ciclo tiene **UNA sola tarea de código** (T-30). No hagas nada fuera de ella.

## 1. REGLAS NO NEGOCIABLES (romper una = trabajo rechazado)

1. **Editas SOLO lo que dice T-30.** Nada de "mejoras" extra, refactors ni reformateo.
2. **Git add SELECTIVO.** Solo `git add frontend/app.js`. NUNCA `git add .` / `-A`.
3. **Evidencia = salida REAL pegada.** Pega la salida literal de cada comando que
   corras. Si no lo corriste, no lo reportes. (Historial: 3 veces se reportó
   evidencia que nunca corrió. No pasa la auditoría.)
4. **Builds/checks pesados van en WSL, NO en el mount `/mnt`.** El mount TRUNCA
   archivos grandes (~40KB): `app.js` real = ~1500 líneas, el mount muestra ~1116.
   Correr node/python/git sobre el mount da errores de sintaxis FALSOS y `git status`
   engañoso. Para `node --check` usa una copia en WSL nativo o el árbol real, no `/mnt`.
5. **NO builds ni release en esta tarea.** Editas, verificas, commiteas, y **PARAS**.
   El release (v1.7.8) es T-31 y solo arranca DESPUÉS de que Claude audite T-30 OK.
6. **Al terminar T-30: STOP explícito.** Escribe "STOP — T-30 listo para auditoría"
   y espera. No sigas a T-31 por tu cuenta.

## 2. CONTEXTO DE LA CAUSA RAÍZ (ya diagnosticada por Claude — no re-investigues)

El card "Comandos de voz" en Ajustes NUNCA aparece, aunque la voz funciona y el
micrófono sí se ve. Por qué:

- `frontend/tailwind-lite.css:3` define:  `.hidden { display: none !important; }`
- `frontend/index.html:363` el card arranca con clase `hidden`:
  `<details id="voice-commands-card" ... class="... hidden">`
- `frontend/app.js:183` intenta mostrarlo con estilo INLINE:
  `voiceCard.style.display = showVoice ? 'block' : 'none';`
- Un estilo inline SIN `!important` **no puede** ganarle a una clase con `!important`.
  Por eso el card queda `display:none` para siempre.
- El micrófono (`#mic-row`) usa el MISMO patrón pero su HTML **no** tiene clase
  `hidden` → su inline `style.display` sí funciona. Por eso el mic se ve y el card no.

El fix correcto es togglear la CLASE `hidden` en vez de pelear con `style.display`.
Es exactamente el patrón que el propio `app.js` ya usa para los bloques de licencia
(`classList.add('hidden')` / `classList.remove('hidden')` cerca de la línea 196).

---

## 3. TAREA T-30 — Togglear clase en vez de style.display

### Archivo: `frontend/app.js`

Busca este bloque (está dentro de `fetchLicenseStatus`, alrededor de la línea 177-190):

```js
            const micRow = document.getElementById('mic-row');
            const voiceCard = document.getElementById('voice-commands-card');
            if (micRow) {
                const showVoice = data.voice_enabled && isLicensed;
                micRow.style.display = showVoice ? 'flex' : 'none';
                if (voiceCard) {
                    voiceCard.style.display = showVoice ? 'block' : 'none';
                }
```

Cambia **UNA sola línea**. La línea:

```js
                    voiceCard.style.display = showVoice ? 'block' : 'none';
```

por:

```js
                    voiceCard.classList.toggle('hidden', !showVoice);
```

**NO toques** la línea de `micRow` (funciona bien, no tiene clase `hidden`).
**NO toques** el HTML (`index.html`). El card DEBE seguir con `hidden` por defecto:
así no parpadea visible para usuarios sin licencia antes de que corra el chequeo.
`classList.toggle('hidden', !showVoice)` lo quita cuando `showVoice` es true y lo
pone cuando es false. Cubre ambos sentidos.

### Verificación (corre y PEGA la salida literal de cada uno):

1. Confirmar que el cambio está y que NO quedó el `style.display` viejo del card:
   ```bash
   grep -n "voiceCard" frontend/app.js
   ```
   Esperado: ver `voiceCard.classList.toggle('hidden', !showVoice);` y que ya NO
   aparezca `voiceCard.style.display`.

2. Sintaxis válida (en WSL nativo, NO en el mount):
   ```bash
   node --check frontend/app.js && echo "SYNTAX_OK"
   ```
   Esperado: `SYNTAX_OK`.

### Commit (mensaje EXACTO):

```bash
git add frontend/app.js
git commit -m "[T-30] Fix card Comandos de voz invisible: toggle clase hidden en vez de style.display

.hidden usa !important; el inline style.display no lo pisa, el card quedaba
oculto siempre. mic-row funcionaba por no tener la clase. Alineado al patron
classList que app.js ya usa para los bloques de licencia."
```

Luego:
```bash
git show --stat HEAD
git show HEAD -- frontend/app.js
```
Pega ambas salidas.

### Cierre de T-30

Escribe: **"STOP — T-30 listo para auditoría"** y espera a Claude.
No arranques T-31.

---

## 4. T-31 — Release v1.7.8   (Claude ya auditó T-30 = APTO → habilitado)

### POR QUÉ HAY UN CLON EN WSL (leé esto o rompés el release)
`build_deb.sh` empaqueta `frontend/` tal cual. El mount `/mnt/d/...` TRUNCA archivos
grandes al leerlos, así que si buildeás sobre el repo de Windows vía `/mnt`, el
`app.js` sale cortado (~1116 de ~1500 líneas) → `.deb` roto → OTA rota en el equipo
del dueño. Solución: buildear en un **clon fresco desde GitHub dentro del filesystem
NATIVO de WSL** (`~`, NO `/mnt`). Ahí los archivos están completos.

### PASO 0 — Publicar T-30 en origin (desde el repo Windows)
El commit de T-30 (`b46cafd`) está local, sin pushear. El clon necesita ese código:
```bash
git push origin main
```
Verificá que subió:
```bash
git log origin/main -1 --format="%H %s"
```
Esperado: el hash `b46cafd...` con "[T-30] Fix card...". PEGALO.

### PASO 1 — Clon nativo en WSL y bump de versión
En una terminal **WSL** (no PowerShell):
```bash
cd ~
rm -rf lrp-release
git clone https://github.com/Gusitir/LinuxRemotePlayer.git lrp-release
cd lrp-release
git log -1 --format="%H %s"   # debe mostrar el commit T-30 b46cafd
echo "1.7.8" > VERSION
```

### PASO 2 — Entrada de CHANGELOG
Editá `CHANGELOG.md` y agregá ESTE bloque ARRIBA de la entrada `## [1.7.7]`:
```markdown
## [1.7.8] - 2026-07-20

### Fixed
- **Card de voz visible en Ajustes**: la clase CSS `hidden` (`!important`) tapaba el
  estilo inline y el panel "Comandos de voz" nunca aparecía; ahora se togglea la clase.
```

### PASO 3 — Build del .deb (en el clon WSL)
```bash
bash scripts/build_deb.sh
```
El script corre el guard de CSS, inyecta la versión en `sw.js` y ABORTA solo si algo
falla. Si falla: PARÁ, pegá el error, reportá a Claude. NO improvises.
Debe terminar con: `dist/linuxremoteplayer_1.7.8_all.deb` + su `.sha256`.

### PASO 4 — Verificación del .deb (anti-truncación + versión). PEGÁ TODO.
```bash
rm -rf /tmp/lrp_verify && dpkg-deb -x dist/linuxremoteplayer_1.7.8_all.deb /tmp/lrp_verify
echo "--- sw.js versionado (debe decir lrp-1.7.8) ---"
grep -o "lrp-[0-9.]*" /tmp/lrp_verify/opt/linuxremoteplayer/frontend/sw.js
echo "--- app.js NO truncado (debe ser ~1500, NO ~1116) ---"
wc -l /tmp/lrp_verify/opt/linuxremoteplayer/frontend/app.js
echo "--- fix T-30 dentro del .deb (debe verse classList.toggle) ---"
grep -n "voiceCard.classList.toggle" /tmp/lrp_verify/opt/linuxremoteplayer/frontend/app.js
echo "--- sha256 del .deb ---"
cat dist/linuxremoteplayer_1.7.8_all.deb.sha256
```
Si `sw.js` NO dice `lrp-1.7.8`, o `app.js` sale ~1116, o no aparece el `classList.toggle`
→ PARÁ y reportá. Algo salió truncado/mal.

### PASO 5 — Colocar el .deb en la web y actualizar latest.json
```bash
git rm website/downloads/linuxremoteplayer_1.7.7_all.deb website/downloads/linuxremoteplayer_1.7.7_all.deb.sha256
cp dist/linuxremoteplayer_1.7.8_all.deb website/downloads/
cp dist/linuxremoteplayer_1.7.8_all.deb.sha256 website/downloads/
```
Editá `website/latest.json` EXACTAMENTE así (poné el sha256 REAL del PASO 4, sin el `<...>`):
```json
{
  "version": "1.7.8",
  "deb_url": "https://linux-remote-player.vercel.app/downloads/linuxremoteplayer_1.7.8_all.deb",
  "sha256": "<HASH_REAL_DEL_PASO_4>",
  "notes": "Fix: el card de comandos de voz ahora aparece en Ajustes."
}
```

### PASO 6 — Commit selectivo (NO `git add .`; nada de dist/ ni pkg/)
```bash
git add VERSION CHANGELOG.md website/latest.json website/downloads/linuxremoteplayer_1.7.8_all.deb website/downloads/linuxremoteplayer_1.7.8_all.deb.sha256
git status --porcelain     # revisá: SOLO esos archivos + los git-rm de 1.7.7. Nada más.
git commit -m "[T-31] Release v1.7.8"
git show --stat HEAD
```
El `--stat` debe parecerse al de v1.7.7: VERSION, CHANGELOG.md, el rename del .deb
1.7.7→1.7.8, los dos .sha256, y latest.json. NADA de dist/, pkg/, backend/, etc.

### PASO 7 — STOP para auditoría (NO PUSHEES TODAVÍA)
Escribí: **"STOP — T-31 buildeado, listo para auditoría (SIN push)"** y pegá:
- salida del PASO 4 (sw.js versionado, wc -l app.js, classList.toggle, sha256),
- `git status --porcelain` y `git show --stat HEAD` del PASO 6.
Claude audita que el sha256 de `latest.json` == el del `.deb` commiteado, que el `.deb`
no está truncado y que el `sw.js` dice `lrp-1.7.8`. **El push va DESPUÉS del OK de Claude.**

### PASO 8 — Push (SOLO tras "T-31 auditado OK" de Claude)
```bash
git push origin main
```
Vercel redeploya solo. Avisá cuando esté pusheado.
Después, en el repo de Windows: `git pull` para sincronizar el release commit.

### Prueba OTA (la ejecuta el DUEÑO tras el deploy — no vos)
El equipo del dueño está en 1.7.7 (ya trae auto-reload por `controllerchange`). Abre la
PWA, y sin reinstalar debería auto-recargar a 1.7.8 y ver el card de voz. Si pasa: OTA
VERIFICADO end-to-end (la prueba que 1.7.5→1.7.7 no pudo ser porque 1.7.5 no tenía el
código de auto-reload).

---

## 5. RESUMEN
- T-30 (HECHO, APTO): 1 línea en `frontend/app.js`, `style.display` → `classList.toggle('hidden', !showVoice)`.
- T-31 (release): push T-30 → clon WSL nativo desde origin → bump VERSION+CHANGELOG →
  `build_deb.sh` → verificar sw.js `lrp-1.7.8` + app.js NO truncado + sha256 → mover
  .deb a website/downloads/ + latest.json → commit selectivo `[T-31]` → **STOP sin push**
  → auditoría de Claude → push → prueba OTA del dueño.
