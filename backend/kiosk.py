import subprocess
import os

import shutil

def kill_existing_kiosks():
    try:
        # Use '--' to signify end of options so '--kiosk' is treated as a pattern by pkill
        subprocess.run(['pkill', '-f', '--', '--kiosk'], check=False)
        print("Killed existing kiosk instances.")
    except Exception as e:
        print(f"Error killing kiosk: {e}")

def launch_kiosk(url: str):
    kill_existing_kiosks()
    
    # URL Validation
    if not url.startswith("http://") and not url.startswith("https://"):
        print(f"Invalid URL: {url}")
        return False
        
    try:
        cmd = []
        if shutil.which('google-chrome'):
            cmd = ['google-chrome', f'--app={url}', '--kiosk', '--start-maximized', '--no-errdialogs', '--disable-infobars']
        elif shutil.which('chromium-browser'):
            cmd = ['chromium-browser', f'--app={url}', '--kiosk', '--start-maximized', '--no-errdialogs', '--disable-infobars']
        elif shutil.which('chromium'):
            cmd = ['chromium', f'--app={url}', '--kiosk', '--start-maximized', '--no-errdialogs', '--disable-infobars']
        elif shutil.which('firefox'):
            cmd = ['firefox', '--kiosk', url]
        else:
            print("Warning: No supported browser found (Chrome/Chromium/Firefox). Using default browser.")
            cmd = ['xdg-open', url]

        print(f"Launching kiosk: {' '.join(cmd)}")
        
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        return True
    except Exception as e:
        print(f"Failed to launch kiosk: {e}")
        return False
