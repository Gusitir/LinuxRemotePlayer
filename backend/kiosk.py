import subprocess
import os
import shutil
import glob
import signal
import time
import logging

logger = logging.getLogger("kiosk")

_kiosk_proc = None
_native_procs = []


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


def gui_env():
    """Build an environment so the browser can open even when launched from a
    systemd service, which lacks the graphical-session variables.

    DISPLAY=:0 works for X11 and for Wayland via XWayland; WAYLAND_DISPLAY is set
    when a native Wayland socket is found.
    """
    env = os.environ.copy()
    env.setdefault("DISPLAY", ":0")
    
    uid = None
    if hasattr(os, "getuid"):
        uid = os.getuid()
        runtime = env.get("XDG_RUNTIME_DIR") or f"/run/user/{uid}"
        env["XDG_RUNTIME_DIR"] = runtime
        if "WAYLAND_DISPLAY" not in env and os.path.exists(os.path.join(runtime, "wayland-0")):
            env["WAYLAND_DISPLAY"] = "wayland-0"

    # COR-04: probe Xauthority paths
    if "XAUTHORITY" not in env:
        home = os.path.expanduser("~")
        xauth_user = os.path.join(home, ".Xauthority")
        if os.path.exists(xauth_user):
            env["XAUTHORITY"] = xauth_user
        elif uid is not None:
            xauth_gdm = f"/run/user/{uid}/gdm/Xauthority"
            if os.path.exists(xauth_gdm):
                env["XAUTHORITY"] = xauth_gdm
            else:
                xauth_globs = glob.glob(f"/run/user/{uid}/xauth_*")
                if xauth_globs:
                    env["XAUTHORITY"] = xauth_globs[0]
                    
    return env


def close_all():
    kill_existing_kiosks()
    global _native_procs
    for proc in _native_procs:
        if proc.poll() is None:
            try:
                pgid = os.getpgid(proc.pid)
                os.killpg(pgid, signal.SIGTERM)
            except Exception as e:
                logger.error(f"Error terminating native process group: {e}")
    _native_procs.clear()

    if os.getenv("APPLIANCE_IDLE_PANEL", "").lower() == "true":
        port = os.getenv("PORT", "8000")
        url = f"https://127.0.0.1:{port}/status"
        launch_kiosk(url)


def kill_existing_kiosks():
    global _kiosk_proc
    
    # SEC-05: Process group kiosk termination
    if _kiosk_proc is not None and _kiosk_proc.poll() is None:
        try:
            pid = _kiosk_proc.pid
            pgid = os.getpgid(pid)
            logger.info(f"Terminating kiosk process group {pgid}...")
            os.killpg(pgid, signal.SIGTERM)
            
            for _ in range(30):
                if _kiosk_proc.poll() is not None:
                    break
                time.sleep(0.1)
                
            if _kiosk_proc.poll() is None:
                logger.warning(f"Kiosk process group {pgid} did not terminate, sending SIGKILL...")
                os.killpg(pgid, signal.SIGKILL)
                _kiosk_proc.wait()
            logger.info("Kiosk process group terminated.")
        except Exception as e:
            logger.error(f"Error terminating tracked kiosk process: {e}")
        _kiosk_proc = None
        return

    logger.info("No active tracked kiosk process found. Running fallback pkill with narrow patterns...")
    try:
        subprocess.run(['pkill', '-f', '--', 'chromium.*--kiosk'], check=False)
        subprocess.run(['pkill', '-f', '--', 'chromium-browser.*--kiosk'], check=False)
    except Exception as e:
        logger.error(f"Error running fallback pkill: {e}")


def launch_kiosk(url: str) -> bool:
    global _kiosk_proc
    kill_existing_kiosks()

    # URL Validation
    if not url.startswith("http://") and not url.startswith("https://"):
        logger.warning(f"Invalid URL: {url}")
        return False

    chromium = find_chromium()
    if not chromium:
        logger.error("Chromium not found. Install it or re-run scripts/install.sh.")
        return False

    try:
        cmd = [chromium, f'--app={url}', '--kiosk', '--start-maximized', '--no-errdialogs', '--disable-infobars']
        logger.info(f"Launching kiosk: {' '.join(cmd)}")
        _kiosk_proc = subprocess.Popen(
            cmd, env=gui_env(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True
        )
        return True
    except Exception as e:
        logger.error(f"Failed to launch kiosk: {e}")
        return False
