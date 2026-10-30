# uBlock Origin (vendorizado)

Extensión empaquetada para el navegador de LRP OS (Firefox ESR del kiosk).

| Campo | Valor |
|---|---|
| Asset | `uBlock0_1.75.0.firefox.signed.xpi` |
| Versión | 1.75.0 |
| Origen | https://github.com/gorhill/uBlock/releases/download/1.75.0/uBlock0_1.75.0.firefox.signed.xpi |
| Release | https://github.com/gorhill/uBlock/releases/tag/1.75.0 |
| SHA256 | `5b74415860456370644bd80f16125e865b0e6c356bb5dfcfb84069967eaa5287` |
| Tamaño | 4.650.100 bytes |
| Licencia | GPL-3.0 (uBlock Origin, © Raymond Hill y contribuyentes) |
| Fecha de vendorización | 2026-10-29 |

## Verificación

- XPI = ZIP válido (661 entradas), `manifest.json` presente.
- `manifest.json`: `version = 1.75.0`, `manifest_version = 2`.
- ID de extensión: `uBlock0@raymondhill.net` (declarado en `browser_specific_settings.gecko.id`).

```bash
python3 - <<'PY'
import zipfile, json, hashlib
p = "uBlock0.xpi"
print(hashlib.sha256(open(p,'rb').read()).hexdigest())
z = zipfile.ZipFile(p)
m = json.loads(z.read("manifest.json"))
print(m["version"], m["browser_specific_settings"]["gecko"]["id"])
PY
```

Archivo local: `scripts/debian/iso/vendor/uBlock0.xpi`
