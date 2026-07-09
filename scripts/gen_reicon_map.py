import json
import os
import re

base_path = r"D:\AGUSTIN\Portafolio\Proyectos\Proyecto WebApp - LinuxRemotePlayer\reicon-icons\outline"
icons_to_fetch = [
    "mobile.svg", "settings.svg", "grid.svg", "mouse.svg", "gamepad.svg",
    "chevron-up.svg", "chevron-down.svg", "chevron-left.svg", "chevron-right.svg",
    "microphone.svg", "keyboard.svg", "trash.svg", "tv.svg", "menu.svg", "x.svg",
    "arrow-left.svg", "volume-down.svg", "volume-up.svg", "home.svg",
    "rewind.svg", "play.svg", "fast-forward.svg", "share.svg", "lock.svg"
]

out = {}
for icon in icons_to_fetch:
    path = os.path.join(base_path, icon)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            # Clean up the SVG
            content = content.replace('\n', '').replace('\r', '')
            content = re.sub(r'xmlns="[^"]+"\s*', '', content)
            content = re.sub(r'width="24"\s*height="24"\s*', '', content)
            content = content.replace('fill="#000000"', 'fill="currentColor"')
            content = content.replace(' stroke="#000000"', ' stroke="currentColor"')
            out[icon] = content
    else:
        # try to find alternatives if not exact match
        alt = [f for f in os.listdir(base_path) if f.startswith(icon.split('.')[0])]
        if alt:
            path = os.path.join(base_path, alt[0])
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                content = content.replace('\n', '').replace('\r', '')
                content = re.sub(r'xmlns="[^"]+"\s*', '', content)
                content = re.sub(r'width="24"\s*height="24"\s*', '', content)
                content = content.replace('fill="#000000"', 'fill="currentColor"')
                content = content.replace(' stroke="#000000"', ' stroke="currentColor"')
                out[icon] = content
        else:
            out[icon] = "NOT_FOUND"

with open(r"D:\AGUSTIN\Portafolio\Proyectos\Proyecto WebApp - LinuxRemotePlayer\reicon_map.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2)

print("Done generating map.")
