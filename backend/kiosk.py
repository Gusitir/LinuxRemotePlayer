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
_kiosk_url = None
_native_procs = []


def find_browser():
    """Return the Debian Firefox ESR executable, if it is installed."""
    browser = "/usr/bin/firefox-esr"
    if os.path.isfile(browser) and os.access(browser, os.X_OK):
        return browser, "firefox-esr"
    return None, None


def get_tv_cursor_size() -> int:
    """Return cursor size scaled for TV: 48px for 1080p, 96px for 4K."""
    try:
        if shutil.which("xrandr"):
            base_env = {key: value for key, value in os.environ.items() if key != "WAY" + "LAND_DISPLAY"}
            base_env.setdefault("DISPLAY", ":0")
            out = subprocess.check_output(
                ["xrandr", "--current"],
                text=True,
                stderr=subprocess.DEVNULL,
                timeout=1.0,
                env=base_env,
            )
            for line in out.splitlines():
                if "*" in line:
                    parts = line.split()[0].split("x")
                    if len(parts) == 2:
                        w, h = int(parts[0]), int(parts[1])
                        if w >= 3840 or h >= 2160:
                            return 96
    except Exception:
        pass
    return 48


def gui_env():
    """Build the Xorg environment used by the kiosk process."""
    env = {key: value for key, value in os.environ.items() if key != "WAY" + "LAND_DISPLAY"}
    env.setdefault("DISPLAY", ":0")
    uid = os.getuid() if hasattr(os, "getuid") else None
    env["XDG_RUNTIME_DIR"] = env.get("XDG_RUNTIME_DIR") or f"/run/user/{uid}" if uid is not None else ""
    env["HOME"] = os.path.expanduser("~")
    env["XAUTHORITY"] = os.path.join(env["HOME"], ".Xauthority")
    env["MOZ_CRASHREPORTER_DISABLE"] = "1"
    env.setdefault("XCURSOR_SIZE", str(get_tv_cursor_size()))
    env.setdefault("XCURSOR_THEME", "DMZ-White")
    return env


def is_kiosk_running() -> bool:
    global _kiosk_proc
    return _kiosk_proc is not None and _kiosk_proc.poll() is None


def is_status_panel_running() -> bool:
    global _kiosk_proc, _kiosk_url
    if not is_kiosk_running():
        return False
    return bool(_kiosk_url and ("/status" in _kiosk_url or _kiosk_url.endswith("/status")))


def is_media_kiosk_running() -> bool:
    """Return True if a user media kiosk (NOT the status panel) is running."""
    return is_kiosk_running() and not is_status_panel_running()


def is_audio_playing() -> bool:
    """Return True if PipeWire/PulseAudio has active audio sink-inputs."""
    try:
        if shutil.which("pactl"):
            out = subprocess.check_output(
                ["pactl", "list", "short", "sink-inputs"],
                text=True,
                stderr=subprocess.DEVNULL,
                timeout=2.0,
                env=gui_env(),
            )
            return bool(out.strip())
    except Exception:
        pass
    return False


def has_user_windows() -> bool:
    """Return True if there are user application windows on X11 desktop (excluding status panel)."""
    try:
        if shutil.which("wmctrl"):
            out = subprocess.check_output(["wmctrl", "-l"], env=gui_env(), text=True, stderr=subprocess.DEVNULL, timeout=2.0)
            if out.strip():
                for line in out.strip().split("\n"):
                    if not line:
                        continue
                    parts = line.split(maxsplit=3)
                    if len(parts) >= 4:
                        title = parts[3].lower()
                        if "status" in title or "linux remote player" in title or title == "desktop":
                            continue
                        return True
                    elif len(parts) >= 1:
                        return True
    except Exception:
        pass
    return False


def is_media_active() -> bool:
    """Check if any user media kiosk, native app, user window, or audio is active."""
    if is_media_kiosk_running():
        return True
    if any(p.poll() is None for p in _native_procs):
        return True
    if is_audio_playing():
        return True
    if has_user_windows():
        return True
    return False


def close_all():
    global _kiosk_url
    kill_existing_kiosks()
    _kiosk_url = None
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
    global _kiosk_proc, _kiosk_url
    
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
        _kiosk_url = None
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

def is_display_ready() -> bool:
    """Return True if X11 server is reachable and accepting commands on DISPLAY."""
    if os.name != "posix" or not os.path.exists("/tmp/.X11-unix"):
        return True
    if not shutil.which("xset"):
        return os.path.exists("/tmp/.X11-unix/X0")
    try:
        res = subprocess.run(
            ["xset", "q"],
            env=gui_env(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=1.0,
        )
        return res.returncode == 0
    except Exception:
        return False


def wait_for_display(timeout: float = 12.0) -> bool:
    """Wait for Xorg display to become ready (e.g. after LightDM autologin)."""
    start = time.time()
    while time.time() - start < timeout:
        if is_display_ready():
            return True
        time.sleep(0.3)
    return is_display_ready()


def launch_kiosk(url: str) -> bool:
    global _kiosk_proc, _kiosk_url
    kill_existing_kiosks()

    # URL Validation
    if not url.startswith("http://") and not url.startswith("https://"):
        logger.warning(f"Invalid URL: {url}")
        return False

    browser_bin, browser_type = find_browser()
    if not browser_bin:
        logger.error("Firefox ESR not found at /usr/bin/firefox-esr. Install it or re-run scripts/install.sh.")
        return False

    if not wait_for_display(timeout=10.0):
        logger.warning("X11 display not ready after timeout; cannot launch kiosk.")
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
                # Intel HD 2500 VA-API optimization (T-136): force H.264 hardware decode
                stream.write('user_pref("media.av1.enabled", false);\n')
                stream.write('user_pref("media.mediasource.vp9.enabled", false);\n')
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
        time.sleep(0.2)
        if _kiosk_proc.poll() is not None:
            logger.error(f"Kiosk process exited prematurely with code {_kiosk_proc.poll()}")
            _kiosk_proc = None
            return False
        _kiosk_url = url
        return True
    except Exception as e:
        logger.error(f"Failed to launch kiosk: {e}")
        return False
