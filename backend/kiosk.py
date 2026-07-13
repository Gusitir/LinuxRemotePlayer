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


def find_browser():
    """Return a Brave or Chromium executable path, and its type.

    Covers distro naming differences and snap cases. Brave is preferred.
    """
    for name in ("brave-browser", "brave-browser-stable", "brave"):
        path = shutil.which(name)
        if path:
            return path, "brave"
    for path in ("/usr/bin/brave-browser", "/opt/brave.com/brave/brave-browser"):
        if os.path.exists(path):
            return path, "brave"

    for name in ("chromium", "chromium-browser"):
        path = shutil.which(name)
        if path:
            return path, "chromium"
    for path in ("/usr/bin/chromium", "/usr/bin/chromium-browser", "/snap/bin/chromium"):
        if os.path.exists(path):
            return path, "chromium"
    return None, None


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
        subprocess.run(['pkill', '-f', '--', 'brave.*--kiosk'], check=False)
        subprocess.run(['pkill', '-f', '--', 'chromium.*--kiosk'], check=False)
        subprocess.run(['pkill', '-f', '--', 'chromium-browser.*--kiosk'], check=False)
    except Exception as e:
        logger.error(f"Error running fallback pkill: {e}")


def adblock_status() -> str:
    browser_path, browser_type = find_browser()
    if browser_type == "brave":
        return "shields"
    home_ext = os.path.expanduser("~/lrp-extensions/ubol")
    opt_ext = "/opt/linuxremoteplayer/extensions/ubol"
    if os.path.exists(os.path.join(home_ext, "manifest.json")) or os.path.exists(os.path.join(opt_ext, "manifest.json")):
        return "ubol"
    return "none"

def launch_kiosk(url: str) -> bool:
    global _kiosk_proc
    kill_existing_kiosks()

    # URL Validation
    if not url.startswith("http://") and not url.startswith("https://"):
        logger.warning(f"Invalid URL: {url}")
        return False

    browser_bin, browser_type = find_browser()
    if not browser_bin:
        logger.error("Brave/Chromium not found. Install it or re-run scripts/install.sh.")
        return False

    try:
        user_data_dir = os.path.expanduser("~/.config/lrp-kiosk")
        cmd = [browser_bin, f'--app={url}', '--kiosk', '--start-maximized', '--noerrdialogs', '--disable-infobars', f'--user-data-dir={user_data_dir}']

        # uBOL path: prefer the user's HOME (snap-packaged Chromium on Ubuntu/KDE Neon
        # CANNOT read /opt due to confinement); /opt kept as fallback for non-snap builds.
        home_ext = os.path.expanduser("~/lrp-extensions/ubol")
        opt_ext = "/opt/linuxremoteplayer/extensions/ubol"
        ext_path = home_ext if os.path.exists(os.path.join(home_ext, "manifest.json")) else opt_ext

        if browser_type == "chromium":
            if os.path.exists(os.path.join(ext_path, "manifest.json")):
                cmd.append(f'--load-extension={ext_path}')
                logger.info(f"Loaded uBOL extension from {ext_path}")
            else:
                logger.warning(f"uBOL no encontrado en {home_ext} o {opt_ext} — kiosk sin bloqueador")

        logger.info(f"Launching kiosk: {' '.join(cmd)}")
        _kiosk_proc = subprocess.Popen(
            cmd, env=gui_env(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True
        )
        return True
    except Exception as e:
        logger.error(f"Failed to launch kiosk: {e}")
        return False
