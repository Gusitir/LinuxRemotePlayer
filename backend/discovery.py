import os
import configparser

# Scan the standard FreeDesktop locations PLUS Flatpak/Snap/local so apps installed
# by any method (.deb, flatpak, snap, AppImage with a .desktop) are detected.
SCAN_PATHS = [
    '/usr/share/applications',
    '/usr/local/share/applications',
    os.path.expanduser('~/.local/share/applications'),
    '/var/lib/flatpak/exports/share/applications',
    os.path.expanduser('~/.local/share/flatpak/exports/share/applications'),
    '/var/lib/snapd/desktop/applications',
]

# Hide system/settings noise (e.g. "Login Window", control-panel entries).
SKIP_CATEGORIES = {'Settings', 'System', 'Screensaver'}


def get_installed_apps():
    apps = {}
    for path in SCAN_PATHS:
        if not os.path.isdir(path):
            continue
        try:
            filenames = os.listdir(path)
        except Exception:
            continue
        for filename in filenames:
            if not filename.endswith('.desktop'):
                continue
            filepath = os.path.join(path, filename)
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                if '[Desktop Entry]' not in content:
                    continue
                parser = configparser.ConfigParser(interpolation=None, strict=False)
                parser.optionxform = str  # preserve key casing
                parser.read_string(content)
                if 'Desktop Entry' not in parser:
                    continue
                entry = parser['Desktop Entry']

                if entry.get('Type', 'Application') != 'Application':
                    continue
                if entry.get('NoDisplay', 'false').lower() == 'true':
                    continue
                if entry.get('Hidden', 'false').lower() == 'true':
                    continue
                cats = set((entry.get('Categories', '') or '').split(';'))
                if cats & SKIP_CATEGORIES:
                    continue

                app_id = filename[:-len('.desktop')]
                apps[app_id] = {
                    'id': app_id,
                    'name': entry.get('Name', app_id),
                    'icon': entry.get('Icon', 'application-x-executable'),
                    'type': 'native',
                    'exec': entry.get('Exec', ''),
                }
            except Exception:
                continue

    return sorted(apps.values(), key=lambda x: x['name'].lower())
