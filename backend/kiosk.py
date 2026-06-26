import subprocess
import os
import shutil


def find_chromium():
    """Return a Chromium executable path, or None.

    Covers distro naming differences (chromium vs chromium-browser) and the snap
    case, where /snap/bin is often missing from a systemd service's PATH.
    """
    for name in ("chromium", "chromium-browser"):
        path = shutil.which(name)
        if path:
            return path
    for path in ("/usr/bin/chromium", "/usr/bin/chromium-browser", "/snap/bin/chromium"):
        if os.path.exists(path):
            return path
    return None


def kill_existing_kiosks():
    try:
        # Use '--' so '--kiosk' is treated as a pattern by pkill, not an option.
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

    # Chromium only — Brave/Firefox proved unreliable in kiosk mode.
    chromium = find_chromium()
    if not chromium:
        print("Error: Chromium not found. Install it (e.g. 'sudo apt install chromium') "
              "or re-run scripts/install.sh.")
        return False

    try:
        cmd = [chromium, f'--app={url}', '--kiosk', '--start-maximized', '--no-errdialogs', '--disable-infobars']
        print(f"Launching kiosk: {' '.join(cmd)}")
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        return True
    except Exception as e:
        print(f"Failed to launch kiosk: {e}")
        return False
