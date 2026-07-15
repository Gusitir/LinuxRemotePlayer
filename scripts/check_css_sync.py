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
IGNORE_CLASSES = {'lucide', 'loader', 'pro-lock', 'maintenance-section'}

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
                clean_class = raw_class.replace('\\', '')
                defined.add(clean_class)
                
    # Extract from inline <style> in HTML files
    style_regex = re.compile(r'<style[^>]*>(.*?)</style>', re.DOTALL | re.IGNORECASE)
    for fpath in USAGE_FILES:
        if not fpath.endswith('.html') or not os.path.exists(fpath):
            continue
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
            for style_match in style_regex.finditer(content):
                for match in regex.finditer(style_match.group(1)):
                    raw_class = match.group(1)
                    clean_class = raw_class.replace('\\', '')
                    defined.add(clean_class)
                    
    return defined

def extract_used_classes():
    used = set()
    
    html_class_regex = re.compile(r'class(?:Name)?\s*=\s*["\']([^"\']+)["\']')
    js_class_regex = re.compile(r'classList\.(?:add|remove|toggle)\s*\(([^)]+)\)')
    string_regex = re.compile(r'["\']([^"\']+)["\']')
    
    for fpath in USAGE_FILES:
        if not os.path.exists(fpath):
            continue
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
            # Match class="c1 c2"
            for match in html_class_regex.finditer(content):
                classes = match.group(1).split()
                used.update(classes)
            # Match classList.add('c1', 'c2')
            for match in js_class_regex.finditer(content):
                args_str = match.group(1)
                for str_match in string_regex.finditer(args_str):
                    used.add(str_match.group(1).strip())
                
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
        print("\nPlease add them to frontend/tailwind-lite.css or add to IGNORE_CLASSES in scripts/check_css_sync.py")
        sys.exit(1)
    else:
        print("CSS Sync Check Passed.")
        sys.exit(0)

if __name__ == "__main__":
    main()
