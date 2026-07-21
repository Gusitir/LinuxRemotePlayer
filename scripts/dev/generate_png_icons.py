import os
from PIL import Image, ImageDraw

# Root directory of the project
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

def draw_icon(size):
    # Canvas
    image = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Background rect: fill #111827, rx=96
    draw.rounded_rectangle([0, 0, 512, 512], radius=96, fill="#111827")

    # Remote body rect: fill #1f2937, stroke #3b82f6, width 12, rx=56
    # x="176" y="80" width="160" height="352"
    draw.rounded_rectangle([176, 80, 336, 432], radius=56, fill="#1f2937", outline="#3b82f6", width=12)

    # Green circle: cx=256, cy=156, r=30, fill #22c55e
    draw.ellipse([256-30, 156-30, 256+30, 156+30], fill="#22c55e")

    # Blue circles: r=18, fill #3b82f6
    blue_centers = [
        (212, 248), (256, 248), (300, 248),
        (212, 304), (256, 304), (300, 304)
    ]
    for cx, cy in blue_centers:
        draw.ellipse([cx-18, cy-18, cx+18, cy+18], fill="#3b82f6")

    # Red rect: x="228" y="356" width="56" height="40" rx=12, fill #ef4444
    draw.rounded_rectangle([228, 356, 284, 396], radius=12, fill="#ef4444")

    # Resize to target size if needed
    if size != 512:
        image = image.resize((size, size), Image.Resampling.LANCZOS)
    return image

if __name__ == "__main__":
    os.makedirs(FRONTEND_DIR, exist_ok=True)
    
    icon_512 = draw_icon(512)
    icon_512.save(os.path.join(FRONTEND_DIR, "icon-512.png"))
    print("Generated icon-512.png")

    icon_192 = draw_icon(192)
    icon_192.save(os.path.join(FRONTEND_DIR, "icon-192.png"))
    print("Generated icon-192.png")
