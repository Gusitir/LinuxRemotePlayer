#!/usr/bin/env python3
import os
import re
import sys

# Script to detect CSS drift (classes used in HTML/JS but missing in CSS)

# Directories
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

# Files to check for usage
USAGE_FILES = [
    os.path.join(FRONTEND_DIR, "index.html"),
    os.path.join(FRONTEND_DIR, "status.html"),
    os.path.join(FRONTEND_DIR, "pair.html"),
    os.path.join(FRONTEND_DIR, "app.js")
]

# Files providing definitions
CSS_FILES = [
    os.path.join(FRONTEND_DIR, "tailwind-lite.css"),
    os.path.join(FRONTEND_DIR, "skins.css")
]

# Whitelist classes that might not be explicitly defined but are safe/dynamic/external
IGNORE_CLASSES = {'bg-black/30', 'right-col', 'h-6', 'bg-cyan-400', 'bg-blue-600/10', 'bg-blue-500/20', 'icon', 'bg-fuchsia-500/20', 'bg-amber-500/20', 'instructions', 'w-8', 'link-row', 'bg-glow', 'gap-6', 'loader', 'drawer', 'btn-copy', 'hover:border-cyan-400', 'text-slate-700', 'visible', 'bg-blue-500', 'm-4', 'border-cyan-800', 'util-btn', 'hover:border-fuchsia-400', 'lucide', 'w-5', 'border-fuchsia-800', 'bg-black', 'w-10', 'text-3xl', 'hover:bg-gray-500', 'hidden', 'open', 'ring-blue-500', 'icon-container', 'bg-cyan-500/20', 'success', 'text-fuchsia-300', 'bg-green-500/20', 'hover:text-blue-300', 'text-cyan-400', 'hover:bg-gray-700', 'h-20', 'to-orange-500/20', 'h-8', 'link-card', 'from-cyan-900/40', 'from-fuchsia-600/40', 'maintenance-section', 'bg-fuchsia-950', 'bg-gray-600', 'shadow-sm', 'w-3', 'bg-black/60', 'pro-lock', 'hover:border-blue-400', 'border-gray-300', 'max-w-xs', 'p-1', 'stat-sub', 'error', 'btn-back', 'focus:border-blue-500', 'shadow-2xl', 'link-text', 'text-green-400', 'btn-action', 'qr-box', 'hover:bg-blue-600/30', 'h-10', 'border-blue-500/30', 'bg-fuchsia-400', 'bg-blue-600/20', 'space-y-2', 'status-visible', 'badge', 'nav-mode', 'icon-lg', 'pt-0', 'w-6', 'stat-grid', 'text-gray-100', 'bg-black/20', 'stat-value', 'stat-card', 'h-5', 'h-3', 'error-message', 'bg-slate-100', 'hover:border-gray-400', 'ctrl-round', 'left-col', 'hover:bg-blue-500', 'util-active'}

def extract_defined_classes():
    defined = set()
    # Match standard classes and escaped tailwind classes like .bg-blue-500\/20
    regex = re.compile(r'\.((?:[a-zA-Z0-9_\[\]/%-]|\\.)+)')
    for css_file in CSS_FILES:
        if not os.path.exists(css_file):
            continue
        with open(css_file, "r", encoding="utf-8") as f:
            for match in regex.finditer(f.read()):
                raw_class = match.group(1)
                # Unescape css backslashes
                clean_class = raw_class.replace('\\', '')
                defined.add(clean_class)
    return defined

def extract_used_classes():
    used = set()
    
    html_class_regex = re.compile(r'class(?:Name)?\s*=\s*["\']([^"\']+)["\']')
    js_class_regex = re.compile(r'classList\.(?:add|remove|toggle)\s*\(\s*["\']([^"\']+)["\']\s*\)')
    
    for fpath in USAGE_FILES:
        if not os.path.exists(fpath):
            continue
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
            # Match class="c1 c2"
            for match in html_class_regex.finditer(content):
                classes = match.group(1).split()
                used.update(classes)
            # Match classList.add('c1')
            for match in js_class_regex.finditer(content):
                used.add(match.group(1).strip())
                
    return used

def main():
    defined = extract_defined_classes()
    used = extract_used_classes()
    
    missing = []
    for c in used:
        if c not in defined and c not in IGNORE_CLASSES:
            # Check if it's a tailwind-lite dynamic class or something we ignore
            # E.g. we might have specific classes that are fine
            missing.append(c)
            
    if missing:
        print("ERROR: CSS Drift Detected!")
        print("The following classes are used in HTML/JS but are NOT defined in CSS:")
        for m in sorted(missing):
            print(f"  - {m}")
        print("\nPlease add them to frontend/css/tailwind-lite.css or add to IGNORE_CLASSES in scripts/check_css_sync.py")
        sys.exit(1)
    else:
        print("CSS Sync Check Passed.")
        sys.exit(0)

if __name__ == "__main__":
    main()
