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
_panel_window_id = None
_panel_launched_at = 0.0
_last_launch_at = 0.0
_panel_miss_logged = False
_wmctrl_warned = False


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


def _pids_matching(binary_needle: str, flag_needle: str) -> list:
    """PIDs whose command line contains both needles (/proc, pgrep/ps fallback).

    /proc se consulta primero: no depende de pgrep ni de un subproceso cronometrado
    (el sondeo corre cada 100 ms y no debe pagar un fork por vuelta).
    """
    pids = []
    try:
        entries = os.listdir("/proc")
    except OSError:
        entries = []
    if entries:
        for entry in entries:
            if not entry.isdigit():
                continue
            try:
                with open(f"/proc/{entry}/cmdline", "rb") as stream:
                    args = stream.read().replace(b"\x00", b" ").decode("utf-8", "ignore")
            except OSError:
                continue
            if binary_needle in args and flag_needle in args:
                pids.append(int(entry))
        return pids
    if os.name != "posix":
        return []

    pattern = f"{binary_needle}.*{flag_needle}"
    try:
        if shutil.which("pgrep"):
            out = subprocess.check_output(
                ["pgrep", "-f", pattern],
                text=True,
                stderr=subprocess.DEVNULL,
                timeout=2.0,
            )
            return [int(value) for value in out.split() if value.isdigit()]
        out = subprocess.check_output(
            ["ps", "-eo", "pid=,args="],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=2.0,
        )
        for line in out.splitlines():
            pid, _, args = line.strip().partition(" ")
            if pid.isdigit() and binary_needle in args and flag_needle in args:
                pids.append(int(pid))
        return pids
    except Exception:
        return []


def _firefox_kiosk_pids() -> list:
    """Live `firefox-esr --kiosk` processes owned by the kiosk profile."""
    return _pids_matching("/usr/bin/firefox-esr", "--kiosk")


def _kiosk_profile_path() -> str:
    """Normalized path of the dedicated LRP kiosk profile."""
    return os.path.realpath(os.path.expanduser("~/.config/lrp-kiosk-firefox"))


def _has_kiosk_profile_arg(args: list, profile_path: str) -> bool:
    """True only if `-profile`/`--profile` is followed by exactly the kiosk profile.

    D1: comparar argumentos, no substrings: un Firefox normal cuya URL contenga
    "lrp-kiosk-firefox" no debe contar como el panel del kiosk.
    """
    for index, arg in enumerate(args):
        if arg in ("-profile", "--profile") and index + 1 < len(args):
            if os.path.realpath(args[index + 1]) == profile_path:
                return True
    return False


def _profile_kiosk_pids() -> list:
    """Live Firefox processes started with the LRP kiosk profile (exact arg match)."""
    profile_path = _kiosk_profile_path()
    pids = []
    try:
        entries = os.listdir("/proc")
    except OSError:
        entries = []
    if entries:
        for entry in entries:
            if not entry.isdigit():
                continue
            try:
                with open(f"/proc/{entry}/cmdline", "rb") as stream:
                    raw = stream.read()
            except OSError:
                continue
            args = [piece.decode("utf-8", "ignore") for piece in raw.split(b"\x00") if piece]
            if _has_kiosk_profile_arg(args, profile_path):
                pids.append(int(entry))
        return pids
    if os.name != "posix":
        return []
    try:
        out = subprocess.check_output(
            ["ps", "-eo", "pid=,args="],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=2.0,
        )
    except Exception:
        return []
    for line in out.splitlines():
        pid, _, rest = line.strip().partition(" ")
        if pid.isdigit() and _has_kiosk_profile_arg(rest.split(), profile_path):
            pids.append(int(pid))
    return pids


def _wait_until_kiosk_gone(timeout: float = 4.0) -> bool:
    """Poll up to `timeout` until no `firefox-esr --kiosk` process is alive."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not _firefox_kiosk_pids():
            return True
        time.sleep(0.1)
    return not _firefox_kiosk_pids()


def is_kiosk_running() -> bool:
    global _kiosk_proc
    return _kiosk_proc is not None and _kiosk_proc.poll() is None


def is_status_panel_running() -> bool:
    global _kiosk_proc, _kiosk_url
    if is_kiosk_running():
        return bool(_kiosk_url and ("/status" in _kiosk_url or _kiosk_url.endswith("/status")))
    if _kiosk_proc is None:
        # B34: tras un restart del servicio se pierde el handle; si el Firefox del
        # perfil kiosk sigue vivo, el panel ya esta abierto y no hay que relanzarlo.
        return bool(_profile_kiosk_pids())
    return False


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
    global _kiosk_proc, _kiosk_url, _panel_window_id
    
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
        _panel_window_id = None
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
    _panel_window_id = None


def adblock_status() -> str:
    _browser_path, browser_type = find_browser()
    if browser_type == "firefox-esr":
        if os.path.exists("/etc/firefox/policies/policies.json"):
            try:
                with open("/etc/firefox/policies/policies.json", "r") as f:
                    if "ublock0@raymondhill.net" in f.read().lower():
                        return "ublock"
            except Exception:
                pass
        return "none"
    return "none"


# --- T-156: watchdog de ventanas del panel (anti-popunder) ---

def _panel_window_title(title: str) -> bool:
    lower = title.lower()
    return "estado del sistema" in lower or "lrp os" in lower


def _wmctrl_windows() -> list:
    """Return [(window_id, wm_class, title)] using wmctrl -lx (2s timeout)."""
    if os.name != "posix" or not shutil.which("wmctrl"):
        return []
    try:
        out = subprocess.check_output(
            ["wmctrl", "-lx"],
            env=gui_env(),
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=2.0,
        )
    except Exception:
        return []
    windows = []
    for line in out.splitlines():
        parts = line.split(None, 4)
        if len(parts) >= 5 and parts[0].startswith("0x"):
            windows.append((parts[0], parts[2], parts[4]))
        elif len(parts) >= 4 and parts[0].startswith("0x"):
            windows.append((parts[0], "", parts[3]))
    return windows


def record_panel_window() -> str:
    """Registra SOLO la ventana cuyo titulo es el panel; sin adivinar por Firefox."""
    global _panel_window_id, _panel_launched_at, _panel_miss_logged
    _panel_launched_at = time.time()
    panel_id = ""
    for wid, _wm_class, title in _wmctrl_windows():
        if _panel_window_title(title):
            panel_id = wid
            break
    _panel_window_id = panel_id or None
    if _panel_window_id:
        _panel_miss_logged = False
        logger.debug(f"Panel window tracked: {_panel_window_id}")
    elif not _panel_miss_logged:
        logger.debug("Panel window not found yet; watchdog disabled until it appears.")
        _panel_miss_logged = True
    return _panel_window_id or ""


def enforce_panel_window(max_seconds: float = 20.0) -> bool:
    """Cierra ventanas de Firefox ajenas al panel; False si el panel desaparecio.

    Conservador a proposito: sin identidad confirmada no toca nada y espera una
    gracia de `max_seconds` desde el ultimo launch_kiosk para no matar el panel
    recien abierto.
    """
    global _panel_window_id, _wmctrl_warned
    if os.name != "posix":
        return True
    if _panel_window_id is None:
        return True
    if not shutil.which("wmctrl"):
        if not _wmctrl_warned:
            logger.warning("wmctrl no disponible: anti-popunder deshabilitado")
            _wmctrl_warned = True
        return True
    if _last_launch_at and (time.time() - _last_launch_at) < max_seconds:
        return True
    windows = _wmctrl_windows()
    if not any(wid == _panel_window_id for wid, _cls, _title in windows):
        return False
    for wid, wm_class, _title in windows:
        if wid == _panel_window_id:
            continue
        if "firefox" in wm_class.lower() or "navigator" in wm_class.lower():
            try:
                subprocess.run(
                    ["wmctrl", "-ic", wid],
                    env=gui_env(),
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=2.0,
                )
                logger.info(f"Cerrada ventana emergente del kiosk: {wid}")
            except Exception as e:
                logger.debug(f"No se pudo cerrar la ventana {wid}: {e}")
    try:
        subprocess.run(
            ["wmctrl", "-ia", _panel_window_id],
            env=gui_env(),
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2.0,
        )
    except Exception as e:
        logger.debug(f"No se pudo reenfocar el panel {_panel_window_id}: {e}")
    return True

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
    global _kiosk_proc, _kiosk_url, _last_launch_at
    _last_launch_at = time.time()
    kill_existing_kiosks()
    # B34: no lanzar encima de un Firefox que aun esta muriendo. Si sigue vivo se
    # degrada el log y se continua (el perfil puede estar en mal estado).
    if not _wait_until_kiosk_gone(timeout=4.0):
        logger.warning("A firefox-esr --kiosk process is still alive after 4s; launching anyway.")

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
        # B34: artefactos de un arranque fallido (lock, crash-restore) dejan el perfil
        # corrupto y Firefox arranca en 10x10 en bucle. Se limpian antes de lanzar.
        for artifact in (
            "lock",
            ".parentlock",
            ".startup-incomplete",
            "sessionstore.jsonlz4",
            "sessionstore-backups",
        ):
            path = os.path.join(profile_dir, artifact)
            if os.path.isdir(path):
                shutil.rmtree(path)
            elif os.path.lexists(path):
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
        # B34: --new-instance evita adjuntarse a una instancia zombi del mismo perfil.
        cmd = [browser_bin, "--kiosk", "--new-instance", "--no-remote", "-profile", profile_dir, url]

        logger.info(f"Launching kiosk: {' '.join(cmd)}")
        _kiosk_proc = subprocess.Popen(
            cmd, env=gui_env(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True
        )
        # B34: 1.8 s alcanza para detectar el crash de arranque (10x10 / perfil roto);
        # con 0.2 s el fallo pasaba inadvertido y el watchdog relanzaba en bucle.
        time.sleep(1.8)
        if _kiosk_proc.poll() is not None:
            logger.error(f"Kiosk process exited during startup with code {_kiosk_proc.poll()}")
            _kiosk_proc = None
            return False
        _kiosk_url = url
        # T-156: recordar que ventana es el panel para el watchdog anti-popunder.
        record_panel_window()
        return True
    except Exception as e:
        logger.error(f"Failed to launch kiosk: {e}")
        return False
