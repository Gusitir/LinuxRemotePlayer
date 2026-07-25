"""Genera los PNG del logo (app + web) a partir de la geometria de frontend/icon.svg.

Por que no rasterizamos el SVG: no hay cairosvg / inkscape / imagemagick en el
entorno de desarrollo, y PIL no lee SVG. Asi que la forma esta reimplementada
aca con primitivas de PIL. **Si tocas frontend/icon.svg hay que replicar el
cambio aca (y al reves).** La verificacion es comparar pixeles del PNG contra
el render nativo del SVG en un navegador.

Uso:  python scripts/dev/generate_png_icons.py
"""
import os

from PIL import Image, ImageChops, ImageDraw

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# --- paleta: la misma del sitio web (website/style.css, tema light) ---
CREAM = (246, 242, 234)   # --bg
INK = (41, 35, 25)        # --text
GREEN = (62, 158, 99)     # verde de marca aclarado para leerse sobre la tinta
# Punto del grid = crema al 20% sobre tinta, precalculado.
DOT = tuple(round(0.20 * c + 0.80 * i) for c, i in zip(CREAM, INK))

VB = 512   # viewBox del SVG
S = 4      # supersampling (se reduce con LANCZOS al final)
N = VB * S

TILE_R = 114                          # squircle del tile
PAD_XY, PAD_WH, PAD_R = 92, 328, 78   # el touchpad
DOT_STEP, DOT_R = 41, 5
TRI = [(323, 256), (205, 186), (205, 326)]   # triangulo de play
TRI_STROKE = 30                       # = stroke-width del SVG (centrado sobre el borde)


def build(rounded=True):
    """rounded=False -> tile cuadrado a sangre, para apple-touch-icon (iOS
    aplica su propia mascara y no quiere transparencia)."""
    base = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(base)

    tile = [0, 0, N - 1, N - 1]
    if rounded:
        d.rounded_rectangle(tile, radius=TILE_R * S, fill=CREAM + (255,))
    else:
        d.rectangle(tile, fill=CREAM + (255,))

    pad = [PAD_XY * S, PAD_XY * S,
           (PAD_XY + PAD_WH) * S - 1, (PAD_XY + PAD_WH) * S - 1]
    d.rounded_rectangle(pad, radius=PAD_R * S, fill=INK + (255,))

    # Grid de puntos recortado a la forma del pad: las esquinas redondeadas
    # dejarian escapar puntos sobre el crema.
    dots = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dots)
    step, r = DOT_STEP * S, DOT_R * S
    n_cells = PAD_WH // DOT_STEP       # 328 / 41 = 8 exacto -> grid simetrico
    for row in range(n_cells):
        for col in range(n_cells):
            cx = PAD_XY * S + col * step + step // 2
            cy = PAD_XY * S + row * step + step // 2
            dd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=DOT + (255,))
    pad_mask = Image.new("L", (N, N), 0)
    ImageDraw.Draw(pad_mask).rounded_rectangle(pad, radius=PAD_R * S, fill=255)
    dots.putalpha(ImageChops.multiply(dots.getchannel("A"), pad_mask))
    base = Image.alpha_composite(base, dots)

    # Triangulo con esquinas redondeadas = suma de Minkowski del triangulo con
    # un disco de radio stroke/2: relleno + una banda por arista + un disco por
    # vertice. (joint="curve" de PIL muerde el vertice agudo y deja un escalon.)
    d = ImageDraw.Draw(base)
    pts = [(x * S, y * S) for x, y in TRI]
    w = TRI_STROKE * S
    r = w // 2
    d.polygon(pts, fill=GREEN + (255,))
    for i in range(len(pts)):
        d.line([pts[i], pts[(i + 1) % len(pts)]], fill=GREEN + (255,), width=w)
    for x, y in pts:
        d.ellipse([x - r, y - r, x + r, y + r], fill=GREEN + (255,))
    return base


# (ruta relativa al repo, tamano, tile redondeado, modo)
TARGETS = [
    ("frontend/icon-192.png", 192, True, "RGBA"),
    ("frontend/icon-512.png", 512, True, "RGBA"),   # tambien el icono .desktop (build_deb.sh)
    ("frontend/apple-touch-icon.png", 180, False, "RGB"),
    ("website/icon-192.png", 192, True, "RGBA"),     # favicon + logo del header del sitio
    ("website/icon-512.png", 512, True, "RGBA"),
    ("website/favicon-32.png", 32, True, "RGBA"),
]


if __name__ == "__main__":
    cache = {}
    for rel, size, rounded, mode in TARGETS:
        if rounded not in cache:
            cache[rounded] = build(rounded=rounded)
        out = cache[rounded].resize((size, size), Image.LANCZOS)
        if mode == "RGB":
            flat = Image.new("RGB", (size, size), CREAM)
            flat.paste(out, (0, 0), out)
            out = flat
        path = os.path.join(ROOT_DIR, rel.replace("/", os.sep))
        out.save(path, "PNG", optimize=True)
        print("%-32s %3dx%-3d %-4s %6d bytes"
              % (rel, size, size, mode, os.path.getsize(path)))
