import subprocess
import os

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
        browser_cmd = "chromium-browser"
        if subprocess.run(['which', 'chromium'], capture_output=True).returncode == 0:
            browser_cmd = "chromium"
            
        cmd = [browser_cmd, f'--app={url}', '--kiosk', '--start-maximized', '--no-errdialogs', '--disable-infobars']
        print(f"Launching kiosk: {' '.join(cmd)}")
        
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        return True
    except Exception as e:
        print(f"Failed to launch kiosk: {e}")
        return False
