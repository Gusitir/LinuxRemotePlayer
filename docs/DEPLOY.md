# Despliegue

Este documento cubre los dos canales de publicación de LRP OS 1.0.0: el sitio estático en Vercel y
los binarios (ISO/APK/SHA256SUMS) en GitHub Releases.

## 1. Sitio web (Vercel)

El sitio es estático: `website/` se publica tal cual, sin build. La configuración de
`website/vercel.json` (`cleanUrls`) no se toca.

### Integración Git (recomendada)

1. En Vercel, **Add New → Project** e importá `Gusitir/LinuxRemotePlayer`.
2. Configurá:
   - **Root Directory:** `website`
   - **Framework Preset:** Other (sin build command, sin output directory)
3. Cada push a `main` genera un **deployment de producción**; las ramas y PRs generan previews.
4. No subas binarios al repo: el sitio solo contiene HTML/CSS/JS, fuentes, iconos y capturas.

### Verificar un deploy

```bash
curl -sI https://www.linuxremoteplayer.com | grep -iE 'x-vercel-id|last-modified|age'
```

El `x-vercel-id` cambia en cada deployment y `last-modified` refleja el momento de publicación. Si
el HTML nuevo no aparece, revisá la CDN/caché y el deployment en el dashboard.

### Rollback

En el dashboard de Vercel: **Project → Deployments**, elegí un deployment anterior y usá
**Promote to Production** (o **Instant Rollback**). El rollback no requiere rebuild.

### Dominios

- Producción: `www.linuxremoteplayer.com` (dominio principal del proyecto).
- Alias: `linux-remote-player.vercel.app`.
- Si el DNS no está en Vercel, apuntá `www` con un `CNAME` al destino que indique Vercel y
  verificá el dominio desde **Project → Settings → Domains**.

## 2. Binarios (GitHub Releases)

La ISO y el APK se publican como assets de un release. Los checksums van siempre con el binario.

```bash
# Generar checksums
sha256sum dist/lrp-os_1.0.0_amd64.iso dist/lrp-1.0.0.apk > dist/SHA256SUMS

# Publicar el release
gh release create v1.0.0 \
  dist/lrp-os_1.0.0_amd64.iso \
  dist/lrp-1.0.0.apk \
  dist/SHA256SUMS \
  --repo Gusitir/LinuxRemotePlayer \
  --title "LRP OS 1.0.0" \
  --notes "LRP OS 1.0.0 — ISO Debian para x86_64 (UEFI). Verificar con SHA256SUMS."
```

El botón de descarga del sitio apunta a `https://github.com/Gusitir/LinuxRemotePlayer/releases/latest`.

### Límite de 2 GiB por asset

GitHub Releases acepta como máximo **2 GiB por archivo**. Si la ISO se acerca o supera ese límite:

1. Comprimí la imagen (`xz -T0 -9`) y publicá el archivo comprimido junto a `SHA256SUMS`.
2. Reducí paquetes de la lista (`scripts/debian/iso/package-lists/lrp-appliance.list.chroot`) y
   volvé a construir.
3. Si aun así excede el límite, alojá la ISO en un espejo estable (por ejemplo archive.org o un
   servidor propio) y publicá en el release solo los checksums y el enlace al espejo, dejando
   claro en las notas de la release dónde está el binario.

### APK

El APK de Android (`lrp-1.0.0.apk`) se adjunta al release v1.0.0. No se publica en Google Play; la
descarga se hace desde el release y el teléfono debe permitir apps de origen desconocido.

## 3. Reglas

- Nunca commitear binarios (`dist/` no se versiona).
- Publicar siempre `SHA256SUMS` junto al binario.
- No incluir secretos ni claves privadas en assets, notas de release ni en el sitio.
