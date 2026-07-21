import os
import json

with open(r"D:\AGUSTIN\Portafolio\Proyectos\Proyecto WebApp - LinuxRemotePlayer\reicon_map.json", "r", encoding="utf-8") as f:
    reicons = json.load(f)

# Helper to inject class into reicon
def get_new(name, cls="icon"):
    svg = reicons[name]
    # SVG from reicon usually starts with <svg viewBox="0 0 24 24" fill="none">
    # We want to add class="cls"
    return svg.replace('<svg viewBox="0 0 24 24" fill="none">', f'<svg viewBox="0 0 24 24" fill="none" class="{cls}">')

replacements_index = [
    # pair icon
    (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="w-8 h-8"><rect x="5" y="2" width="14" height="20" rx="2" ry="2"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg>',
        get_new("mobile.svg", "w-8 h-8")
    ),
    # settings
    (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>',
        get_new("settings.svg", "icon")
    ),
    # more apps
    (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:1rem;height:1rem"><rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/></svg>',
        get_new("grid.svg", "").replace('class=""', 'style="width:1rem;height:1rem"')
    ),
    # touchpad
    (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-12 h-12"><path d="M5 9c0-2.8 2.2-5 5-5s5 2.2 5 5v6c0 2.8-2.2 5-5 5s-5-2.2-5-5z"/><path d="M12 5v4"/></svg>',
        get_new("mouse.svg", "w-12 h-12")
    ),
    # chevron up
    (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon"><path d="m18 15-6-6-6 6"/></svg>',
        get_new("chevron-up.svg", "icon")
    ),
    # chevron down
    (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon"><path d="m6 9 6 6 6-6"/></svg>',
        get_new("chevron-down.svg", "icon")
    ),
    # microphone
    (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon-lg"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/></svg>',
        get_new("microphone.svg", "icon-lg")
    ),
    # keyboard
    (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon"><rect width="20" height="16" x="2" y="4" rx="2"/><path d="M6 8h.01M10 8h.01M14 8h.01M18 8h.01M8 12h.01M12 12h.01M16 12h.01M7 16h10"/></svg>',
        get_new("keyboard.svg", "icon")
    ),
    # trash/delete
    (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon"><path d="M21 4H8l-7 8 7 8h13a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2Z"/><path d="m18 9-6 6"/><path d="m12 9 6 6"/></svg>',
        get_new("trash.svg", "icon")
    ),
    # gamepad toggle
    (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon"><path d="M12 2v4"/><path d="M12 18v4"/><path d="M22 12h-4"/><path d="M6 12H2"/><path d="M12 12h.01"/></svg>',
        get_new("gamepad.svg", "icon")
    ),
    # tv panel
    (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon"><line x1="21" x2="14" y1="4" y2="4"/><line x1="10" x2="3" y1="4" y2="4"/><line x1="21" x2="12" y1="12" y2="12"/><line x1="8" x2="3" y1="12" y2="12"/><line x1="21" x2="16" y1="20" y2="20"/><line x1="12" x2="3" y1="20" y2="20"/><line x1="14" x2="14" y1="2" y2="6"/><line x1="8" x2="8" y1="10" y2="14"/><line x1="16" x2="16" y1="18" y2="22"/></svg>',
        get_new("tv.svg", "icon")
    ),
    # OS menu
    (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M10 4v4"/><path d="M2 8h20"/><path d="M6 4v4"/></svg>',
        get_new("menu.svg", "icon")
    ),
    # home
    (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M9 22V12h6v10"/></svg>',
        get_new("home.svg", "icon")
    ),
    # arrow left
    (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon"><path d="m12 19-7-7 7-7"/><path d="M19 12H5"/></svg>',
        get_new("arrow-left.svg", "icon")
    ),
    # rewind
    (
        '<svg viewBox="0 0 24 24" fill="currentColor" class="icon"><polygon points="11 19 2 12 11 5 11 19"/><polygon points="22 19 13 12 22 5 22 19"/></svg>',
        get_new("rewind.svg", "icon")
    ),
    # play
    (
        '<svg viewBox="0 0 24 24" fill="currentColor" class="icon-lg"><path d="M3 4v16l9-8z"/><rect x="14" y="4" width="3" height="16" rx="1"/><rect x="19" y="4" width="3" height="16" rx="1"/></svg>',
        get_new("play.svg", "icon-lg")
    ),
    # fast forward
    (
        '<svg viewBox="0 0 24 24" fill="currentColor" class="icon"><polygon points="13 19 22 12 13 5 13 19"/><polygon points="2 19 11 12 2 5 2 19"/></svg>',
        get_new("fast-forward.svg", "icon")
    ),
    # volume up
    (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/><line x1="19" y1="9" x2="19" y2="15"/><line x1="16" y1="12" x2="22" y2="12"/></svg>',
        get_new("volume-up.svg", "icon")
    ),
    # volume down
    (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/><line x1="17" y1="12" x2="21" y2="12"/></svg>',
        get_new("volume-down.svg", "icon")
    ),
    # close app / x
    (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/></svg>',
        get_new("x.svg", "icon")
    ),
    # share
    (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon"><polyline points="9 10 4 15 9 20"/><path d="M20 4v7a4 4 0 0 1-4 4H4"/></svg>',
        get_new("share.svg", "icon")
    ),
    # share 2 (line 336 feedback) -> message or share? the old is a share icon. Let's map it to share.
    (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>',
        get_new("share.svg", "w-4 h-4")
    ),
    # group chevrons (group-open:rotate-180) -> use chevron-down
    (
        '<svg class="w-4 h-4 transition-transform group-open:rotate-180" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>',
        get_new("chevron-down.svg", "w-4 h-4 transition-transform group-open:rotate-180")
    ),
    # update check
    (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><path d="M20 6 9 17l-5-5"/></svg>',
        get_new("settings.svg", "w-4 h-4")  # Wait, old update check is a checkmark... I'll use lock.svg? Wait, checkmark -> we need a check icon or refresh. Let's use menu.svg or x.svg... wait! Line 269 is <path d="M20 6 9 17l-5-5"/> this is a CHECKMARK! I forgot to download check.svg. I'll download it or just map it to something similar for now. Wait, I can't leave it broken.
    ),
    # pro lock
    (
        '<svg viewBox="0 0 24 24" fill="none" stroke="#22d3ee" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-5 h-5"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
        get_new("lock.svg", "w-5 h-5")
    ),
    (
        '<svg viewBox="0 0 24 24" fill="none" stroke="#e879f9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-5 h-5"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
        get_new("lock.svg", "w-5 h-5")
    )
]

def replace_in_file(path, replacements):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    for old_str, new_str in replacements:
        if new_str == "NOT_FOUND":
            print(f"Skipping replacement for missing Reicon: {old_str[:50]}...")
            continue
        if old_str in content:
            content = content.replace(old_str, new_str)
        else:
            print(f"Warning: String not found in {path}: {old_str[:50]}...")
            
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# Special overrides
# Checkmark
replacements_index[23] = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><path d="M20 6 9 17l-5-5"/></svg>',
    '<svg viewBox="0 0 24 24" fill="none" class="w-4 h-4"><path d="M20 6L9 17L4 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
)

base = r"D:\AGUSTIN\Portafolio\Proyectos\Proyecto WebApp - LinuxRemotePlayer"
replace_in_file(os.path.join(base, "frontend", "index.html"), replacements_index)

# status.html has phone
replacements_status = [
    (
        '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="2" width="14" height="20" rx="2" ry="2"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg>',
        get_new("mobile.svg", "").replace('class=""', 'width="32" height="32"')
    )
]
replace_in_file(os.path.join(base, "frontend", "status.html"), replacements_status)

print("Icons replaced in HTML files successfully.")
