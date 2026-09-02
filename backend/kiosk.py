"""Kiosk launcher and process management for Linux Remote Player."""
import subprocess
import os
import shutil
import signal
import time
import logging
import tempfile

logger = logging.getLogger("kiosk")

_kiosk_proc = None
_native_procs = []


def find_browser():
    """Return the Debian Firefox ESR executable, if it is installed."""
    browser = "/usr/bin/firefox-esr"
    if os.path.isfile(browser) and os.access(browser, os.X_OK):
        return browser, "firefox-esr"
    return None, None


def gui_env():
    """Build the Xorg environment used by the kiosk process."""
    env = {key: value for key, value in os.environ.items() if key != "WAY" + "LAND_DISPLAY"}
    env.setdefault("DISPLAY", ":0")
    uid = os.getuid() if hasattr(os, "getuid") else None
    env["XDG_RUNTIME_DIR"] = env.get("XDG_RUNTIME_DIR") or f"/run/user/{uid}" if uid is not None else ""
    env["HOME"] = os.path.expanduser("~")
    env["XAUTHORITY"] = os.path.join(env["HOME"], ".Xauthority")
    env["MOZ_CRASHREPORTER_DISABLE"] = "1"
    return env


def close_all():
    kill_existing_kiosks()
    for proc in _native_procs:
        if proc.poll() is None:
            try:
                pgid = os.getpgid(proc.pid)
                os.killpg(pgid, signal.SIGTERM)
            except Exception as e:
                logger.error(f"Error terminating native process group: {e}")
    _native_procs.clear()
    
    # Best-effort cleanup of extraneous X11 windows through wmctrl only.
    env = gui_env()
    try:
        if shutil.which("wmctrl"):
            out = subprocess.check_output(["wmctrl", "-l"], env=env, text=True, stderr=subprocess.DEVNULL)
            if out.strip():
                for line in out.strip().split("\n"):
                    if not line:
                        continue
                    parts = line.split(maxsplit=3)
                    if len(parts) >= 1:
                        wid = parts[0]
                        subprocess.run(["wmctrl", "-ic", wid], env=env, check=False, stderr=subprocess.DEVNULL)
    except Exception as e:
        logger.error(f"Error during window cleanup: {e}")



def kill_existing_kiosks():
    global _kiosk_proc
    
    # SEC-05: Process group kiosk termination
    if _kiosk_proc is not None and _kiosk_proc.poll() is None:
        try:
            pid = _kiosk_proc.pid
            pgid = os.getpgid(pid)
            logger.info(f"Terminating kiosk process group {pgid}...")
            os.killpg(pgid, signal.SIGTERM)
            
            for _ in range(100):
                if _kiosk_proc.poll() is not None:
                    break
                time.sleep(0.1)
                
            if _kiosk_proc.poll() is None:
                logger.warning(f"Kiosk process group {pgid} did not terminate after 10s, sending SIGKILL...")
                os.killpg(pgid, signal.SIGKILL)
                _kiosk_proc.wait()
            logger.info("Kiosk process group terminated.")
        except Exception as e:
            logger.error(f"Error terminating tracked kiosk process: {e}")
        _kiosk_proc = None
        return

    logger.info("No active tracked kiosk process found. Running Firefox ESR fallback cleanup...")
    try:
        profile = os.path.expanduser("~/.config/lrp-kiosk-firefox")
        subprocess.run(
            ["pkill", "-f", "--", f"/usr/bin/firefox-esr.*--kiosk.*-profile[ =]{profile}"],
            check=False,
        )
    except Exception as e:
        logger.error(f"Error running fallback pkill: {e}")


def adblock_status() -> str:
    _browser_path, browser_type = find_browser()
    if browser_type == "firefox-esr":
        if os.path.exists("/etc/firefox/policies/policies.json"):
            try:
                with open("/etc/firefox/policies/policies.json", "r") as f:
                    if "ublock" in f.read().lower():
                        return "ubo-firefox"
            except Exception:
                pass
        return "none"
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
        logger.error("Firefox ESR not found at /usr/bin/firefox-esr. Install it or re-run scripts/install.sh.")
        return False

    try:
        profile_dir = os.path.expanduser("~/.config/lrp-kiosk-firefox")
        os.makedirs(profile_dir, mode=0o700, exist_ok=True)
        os.chmod(profile_dir, 0o700)
        for artifact in ("sessionstore.jsonlz4", "sessionstore-backups"):
            path = os.path.join(profile_dir, artifact)
            if os.path.isdir(path):
                shutil.rmtree(path)
            elif os.path.exists(path):
                os.unlink(path)
        fd, prefs_tmp = tempfile.mkstemp(prefix=".user.js.", dir=profile_dir, text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write('user_pref("browser.sessionstore.resume_from_crash", false);\n')
                stream.write('user_pref("browser.startup.page", 0);\n')
                stream.write('user_pref("browser.shell.checkDefaultBrowser", false);\n')
            if hasattr(os, "chown") and hasattr(os, "getuid"):
                os.chown(prefs_tmp, os.getuid(), os.getgid())
            os.chmod(prefs_tmp, 0o600)
            os.replace(prefs_tmp, os.path.join(profile_dir, "user.js"))
        except Exception:
            try:
                os.unlink(prefs_tmp)
            except OSError:
                pass
            raise
        cmd = [browser_bin, "--kiosk", "--no-remote", "-profile", profile_dir, url]

        logger.info(f"Launching kiosk: {' '.join(cmd)}")
        _kiosk_proc = subprocess.Popen(
            cmd, env=gui_env(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True
        )
        return True
    except Exception as e:
        logger.error(f"Failed to launch kiosk: {e}")
        return False
