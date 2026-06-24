import os
import configparser

def get_installed_apps():
    apps = []
    paths = ['/usr/share/applications', os.path.expanduser('~/.local/share/applications')]
    
    for path in paths:
        if not os.path.exists(path):
            continue
        for filename in os.listdir(path):
            if filename.endswith('.desktop'):
                filepath = os.path.join(path, filename)
                try:
                    parser = configparser.ConfigParser(interpolation=None, strict=False)
                    parser.optionxform = str  # Preserve casing for Name, Icon, Exec
                    
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if '[Desktop Entry]' not in content:
                            continue
                    
                    parser.read_string(content)
                    if 'Desktop Entry' in parser:
                        entry = parser['Desktop Entry']
                        if entry.get('NoDisplay', 'false').lower() == 'true':
                            continue
                            
                        name = entry.get('Name', filename.replace('.desktop', ''))
                        icon = entry.get('Icon', 'application-x-executable')
                        exec_cmd = entry.get('Exec', '')
                        
                        apps.append({
                            "id": filename.replace('.desktop', ''),
                            "name": name,
                            "icon": icon,
                            "type": "native",
                            "exec": exec_cmd
                        })
                except Exception as e:
                    pass
    
    return sorted(apps, key=lambda x: x['name'])
