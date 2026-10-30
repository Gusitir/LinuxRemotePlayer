import asyncio
import os
import signal
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = str(ROOT / "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from backend import kiosk, main
sys.modules["kiosk"] = kiosk


@pytest.fixture(autouse=True)
def _reset_panel_cooldown(monkeypatch):
    """B34: el cooldown anti-tormenta del panel idle es estado global; aislarlo."""
    monkeypatch.setattr(main, "_last_panel_attempt", 0.0)
    monkeypatch.setattr(main, "_panel_fail_streak", 0)
    # D3: ningún test debe depender de procesos Firefox reales del host.
    monkeypatch.setattr(kiosk, "_firefox_kiosk_pids", lambda: [])
    monkeypatch.setattr(kiosk, "_profile_kiosk_pids", lambda: [])

INSTALLER = (ROOT / "scripts" / "install.sh").read_text()



def test_find_browser_accepts_only_executable_debian_path(monkeypatch):
    monkeypatch.setattr(kiosk.os.path, "isfile", lambda path: path == "/usr/bin/firefox-esr")
    monkeypatch.setattr(kiosk.os, "access", lambda path, mode: path == "/usr/bin/firefox-esr")
    assert kiosk.find_browser() == ("/usr/bin/firefox-esr", "firefox-esr")


def test_find_browser_reports_missing_esr(monkeypatch):
    monkeypatch.setattr(kiosk.os.path, "isfile", lambda _path: False)
    assert kiosk.find_browser() == (None, None)


def test_profile_arg_detection_requires_exact_profile_path(tmp_path):
    """D1: se exige el par `-profile <path>`, nunca un substring del cmdline."""
    profile = tmp_path / "lrp-kiosk-firefox"
    profile.mkdir()
    other = tmp_path / "firefox-normal"
    other.mkdir()
    profile_path = os.path.realpath(str(profile))

    assert kiosk._has_kiosk_profile_arg(
        ["/usr/bin/firefox-esr", "-profile", str(profile), "https://example.test"], profile_path
    ) is True
    assert kiosk._has_kiosk_profile_arg(
        ["/usr/bin/firefox-esr", "--profile", str(profile) + os.sep, "https://example.test"], profile_path
    ) is True
    # Un Firefox normal con otro perfil y "lrp-kiosk-firefox" en la URL no cuenta.
    assert kiosk._has_kiosk_profile_arg(
        ["/usr/bin/firefox-esr", "-profile", str(other), "https://lrp-kiosk-firefox.test"], profile_path
    ) is False
    # El path suelto, sin el flag, tampoco.
    assert kiosk._has_kiosk_profile_arg(
        ["/usr/bin/firefox-esr", str(profile), "https://example.test"], profile_path
    ) is False


def test_gui_env_is_xorg_only(monkeypatch):
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    monkeypatch.setenv("DISPLAY", ":7")
    monkeypatch.delenv("XDG_RUNTIME_DIR", raising=False)
    monkeypatch.setattr(kiosk.os, "getuid", lambda: 1001, raising=False)
    env = kiosk.gui_env()
    assert env["DISPLAY"] == ":7"
    assert env["XDG_RUNTIME_DIR"] == "/run/user/1001"
    assert env["HOME"] == os.path.expanduser("~")
    assert env["XAUTHORITY"] == os.path.join(env["HOME"], ".Xauthority")
    assert "WAYLAND_DISPLAY" not in env
    assert env["MOZ_CRASHREPORTER_DISABLE"] == "1"


def test_launch_rejects_non_http_url(monkeypatch):
    monkeypatch.setattr(kiosk, "kill_existing_kiosks", lambda: None)
    popen = pytest.MonkeyPatch()
    popen.setattr(kiosk.subprocess, "Popen", lambda *args, **kwargs: pytest.fail("Popen called"))
    try:
        assert kiosk.launch_kiosk("file:///tmp/player") is False
    finally:
        popen.undo()


def test_launch_uses_exact_esr_command_and_dedicated_profile(monkeypatch, tmp_path):
    calls = {}
    monkeypatch.setattr(kiosk, "kill_existing_kiosks", lambda: None)
    monkeypatch.setattr(kiosk, "find_browser", lambda: ("/usr/bin/firefox-esr", "firefox-esr"))
    monkeypatch.setattr(kiosk.os.path, "expanduser", lambda path: str(tmp_path) if path == "~/.config/lrp-kiosk-firefox" else path)
    monkeypatch.setattr(kiosk.subprocess, "Popen", lambda cmd, **kwargs: calls.update(cmd=cmd, kwargs=kwargs) or SimpleNamespace(poll=lambda: None, pid=1))
    modes = []
    monkeypatch.setattr(kiosk.os, "chmod", lambda path, mode: modes.append((path, mode)))
    assert kiosk.launch_kiosk("https://example.test") is True
    assert calls["cmd"] == ["/usr/bin/firefox-esr", "--kiosk", "--new-instance", "--no-remote", "-profile", str(tmp_path), "https://example.test"]
    assert calls["kwargs"]["start_new_session"] is True
    assert modes[0] == (str(tmp_path), 0o700)
    assert any(path.startswith(str(tmp_path)) and mode == 0o600 for path, mode in modes)
    prefs = (tmp_path / "user.js").read_text()
    assert "browser.sessionstore.resume_from_crash" in prefs
    assert "browser.startup.page" in prefs
    assert "browser.shell.checkDefaultBrowser" in prefs


def test_launch_removes_only_dedicated_session_artifacts(monkeypatch, tmp_path):
    profile = tmp_path / "profile"
    profile.mkdir()
    (profile / "sessionstore.jsonlz4").write_text("x")
    (profile / "sessionstore-backups").mkdir()
    monkeypatch.setattr(kiosk, "kill_existing_kiosks", lambda: None)
    monkeypatch.setattr(kiosk, "find_browser", lambda: ("/usr/bin/firefox-esr", "firefox-esr"))
    monkeypatch.setattr(kiosk.os.path, "expanduser", lambda path: str(profile) if path == "~/.config/lrp-kiosk-firefox" else path)
    monkeypatch.setattr(kiosk.subprocess, "Popen", lambda *args, **kwargs: SimpleNamespace(poll=lambda: None, pid=1))
    assert kiosk.launch_kiosk("https://example.test") is True
    assert not (profile / "sessionstore.jsonlz4").exists()
    assert not (profile / "sessionstore-backups").exists()


def test_launch_returns_false_when_popen_fails(monkeypatch):
    monkeypatch.setattr(kiosk, "kill_existing_kiosks", lambda: None)
    monkeypatch.setattr(kiosk, "find_browser", lambda: ("/usr/bin/firefox-esr", "firefox-esr"))
    monkeypatch.setattr(kiosk.subprocess, "Popen", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("boom")))
    assert kiosk.launch_kiosk("http://example.test") is False


def test_tracked_process_group_escalates_term_to_kill(monkeypatch):
    signals = []
    proc = SimpleNamespace(pid=42, poll=lambda: None, wait=lambda: None)
    kiosk._kiosk_proc = proc
    monkeypatch.setattr(kiosk.os, "getpgid", lambda pid: 99, raising=False)
    monkeypatch.setattr(kiosk.os, "killpg", lambda pgid, sig: signals.append((pgid, sig)), raising=False)
    monkeypatch.setattr(kiosk.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(signal, "SIGKILL", 9, raising=False)
    kiosk.kill_existing_kiosks()
    assert signals == [(99, signal.SIGTERM), (99, signal.SIGKILL)]
    assert kiosk._kiosk_proc is None


def test_orphan_cleanup_targets_only_esr_dedicated_profile(monkeypatch):
    calls = []
    monkeypatch.setattr(kiosk, "_kiosk_proc", None)
    monkeypatch.setattr(kiosk.subprocess, "run", lambda *args, **kwargs: calls.append(args[0]))
    kiosk.kill_existing_kiosks()
    assert len(calls) == 1
    assert calls[0][:3] == ["pkill", "-f", "--"]
    assert "lrp-kiosk-firefox" in calls[0][3]
    assert all(browser not in calls[0][3] for browser in ("brave", "chromium", "firefox.*"))


def test_window_cleanup_uses_wmctrl_without_desktop_fallback(monkeypatch):
    calls = []
    monkeypatch.setattr(kiosk, "kill_existing_kiosks", lambda: None)
    monkeypatch.setattr(kiosk.shutil, "which", lambda name: "/usr/bin/wmctrl" if name == "wmctrl" else None)
    monkeypatch.setattr(kiosk.subprocess, "check_output", lambda *args, **kwargs: "0x1  0 host Player\n")
    monkeypatch.setattr(kiosk.subprocess, "run", lambda *args, **kwargs: calls.append(args[0]))
    kiosk.close_all()
    assert calls == [["wmctrl", "-ic", "0x1"]]


def test_adblock_status_reports_firefox_policy_only(monkeypatch, tmp_path):
    policy = tmp_path / "policies.json"
    policy.write_text('{"ExtensionSettings": {"uBlock0@raymondhill.net": {"installation_mode": "force_installed"}}}')
    monkeypatch.setattr(kiosk, "find_browser", lambda: ("/usr/bin/firefox-esr", "firefox-esr"))
    monkeypatch.setattr(kiosk.os.path, "exists", lambda path: path == "/etc/firefox/policies/policies.json")
    monkeypatch.setattr(kiosk, "open", lambda *args, **kwargs: policy.open(*args[1:], **kwargs), raising=False)
    assert kiosk.adblock_status() == "ublock"


def _mock_wmctrl(monkeypatch, output, calls):
    monkeypatch.setattr(kiosk.os, "name", "posix")
    monkeypatch.setattr(kiosk.shutil, "which", lambda name: "/usr/bin/wmctrl" if name == "wmctrl" else None)
    monkeypatch.setattr(kiosk.subprocess, "check_output", lambda *args, **kwargs: output)
    monkeypatch.setattr(kiosk.subprocess, "run", lambda *args, **kwargs: calls.append(args[0]))


def test_watchdog_does_nothing_without_registered_panel(monkeypatch):
    calls = []
    _mock_wmctrl(monkeypatch, "0x2  0 Navigator.Firefox host Popup\n", calls)
    monkeypatch.setattr(kiosk, "_panel_window_id", None)
    monkeypatch.setattr(kiosk, "_last_launch_at", 0.0)
    assert kiosk.enforce_panel_window() is True
    assert calls == []


def test_watchdog_returns_false_when_panel_is_missing(monkeypatch):
    calls = []
    _mock_wmctrl(monkeypatch, "0x2  0 Navigator.Firefox host Popup\n", calls)
    monkeypatch.setattr(kiosk, "_panel_window_id", "0x1")
    monkeypatch.setattr(kiosk, "_last_launch_at", 0.0)
    assert kiosk.enforce_panel_window() is False
    assert calls == []


def test_watchdog_closes_intruder_and_refocuses_panel(monkeypatch):
    calls = []
    windows = (
        "0x1  0 Navigator.Firefox host Estado del Sistema — LinuxRemotePlayer\n"
        "0x2  0 Navigator.Firefox host Popup\n"
    )
    _mock_wmctrl(monkeypatch, windows, calls)
    monkeypatch.setattr(kiosk, "_panel_window_id", "0x1")
    monkeypatch.setattr(kiosk, "_last_launch_at", 0.0)
    assert kiosk.enforce_panel_window() is True
    assert calls == [["wmctrl", "-ic", "0x2"], ["wmctrl", "-ia", "0x1"]]


def test_watchdog_grace_blocks_enforcement_after_launch(monkeypatch):
    calls = []
    windows = (
        "0x1  0 Navigator.Firefox host Estado del Sistema — LinuxRemotePlayer\n"
        "0x2  0 Navigator.Firefox host Popup\n"
    )
    _mock_wmctrl(monkeypatch, windows, calls)
    monkeypatch.setattr(kiosk, "_panel_window_id", "0x1")
    monkeypatch.setattr(kiosk, "_last_launch_at", time.time())
    assert kiosk.enforce_panel_window() is True
    assert calls == []


def test_watchdog_self_heals_missing_panel_registration(monkeypatch):
    calls = []
    windows = (
        "0x1  0 Navigator.Firefox host Estado del Sistema — LinuxRemotePlayer\n"
        "0x2  0 Navigator.Firefox host Popup\n"
    )
    _mock_wmctrl(monkeypatch, windows, calls)
    monkeypatch.setattr(kiosk, "_panel_window_id", None)
    monkeypatch.setattr(kiosk, "_panel_miss_logged", False)
    monkeypatch.setattr(kiosk, "_last_launch_at", 0.0)
    assert kiosk.enforce_panel_window() is True
    assert kiosk._panel_window_id == "0x1"
    assert calls == [["wmctrl", "-ic", "0x2"], ["wmctrl", "-ia", "0x1"]]


def test_runtime_has_no_forbidden_browser_or_desktop_paths():
    source = (ROOT / "backend" / "kiosk.py").read_text()
    for forbidden in ("brave", "chromium", "/snap/", "qdbus", "KWin", "WAYLAND_DISPLAY", "gdm", "plasma", "krunner"):
        assert forbidden not in source


def test_installer_requires_esr_and_removes_browser_fallbacks():
    assert "apt-get install -y" in INSTALLER
    assert "firefox-esr" in INSTALLER
    assert "apt-get install -y firefox-esr ||" not in INSTALLER
    for forbidden in ("qdbus", "kwriteconfig", "kbuildsycoca", "certutil", "xdg-open", "chromium"):
        assert forbidden not in INSTALLER
    assert "/etc/firefox/policies/policies.json" in INSTALLER
    assert "platform-bootstrap.sh" in INSTALLER


def test_tv_cursor_scaling_default_and_4k(monkeypatch):
    monkeypatch.setattr(kiosk.shutil, "which", lambda name: None)
    assert kiosk.get_tv_cursor_size() == 48

    monkeypatch.setattr(kiosk.shutil, "which", lambda name: "/usr/bin/xrandr" if name == "xrandr" else None)
    monkeypatch.setattr(kiosk.subprocess, "check_output", lambda *a, **k: "Screen 0: ...\nHDMI-1 connected 1920x1080+0+0\n   1920x1080     60.00*+  50.00\n")
    assert kiosk.get_tv_cursor_size() == 48

    monkeypatch.setattr(kiosk.subprocess, "check_output", lambda *a, **k: "Screen 0: ...\nHDMI-1 connected 3840x2160+0+0\n   3840x2160     60.00*+  30.00\n")
    assert kiosk.get_tv_cursor_size() == 96


def test_gui_env_includes_tv_cursor():
    env = kiosk.gui_env()
    assert env.get("XCURSOR_SIZE") in ("48", "96")
    assert env.get("XCURSOR_THEME") == "DMZ-White"


def test_status_panel_and_media_kiosk_detection(monkeypatch):
    kiosk._kiosk_proc = None
    kiosk._kiosk_url = None
    assert kiosk.is_kiosk_running() is False
    assert kiosk.is_status_panel_running() is False
    assert kiosk.is_media_kiosk_running() is False

    # B34b: sin handle (_kiosk_proc None) un Firefox del perfil kiosk implica panel vivo.
    monkeypatch.setattr(kiosk, "_profile_kiosk_pids", lambda: [4242])
    assert kiosk.is_status_panel_running() is True
    monkeypatch.setattr(kiosk, "_profile_kiosk_pids", lambda: [])
    assert kiosk.is_status_panel_running() is False

    kiosk._kiosk_proc = SimpleNamespace(poll=lambda: None)
    kiosk._kiosk_url = "https://127.0.0.1:8000/status"
    assert kiosk.is_kiosk_running() is True
    assert kiosk.is_status_panel_running() is True
    assert kiosk.is_media_kiosk_running() is False

    kiosk._kiosk_url = "https://youtube.com"
    assert kiosk.is_status_panel_running() is False
    assert kiosk.is_media_kiosk_running() is True

    kiosk._kiosk_proc = SimpleNamespace(poll=lambda: 0)
    assert kiosk.is_kiosk_running() is False
    assert kiosk.is_status_panel_running() is False
    assert kiosk.is_media_kiosk_running() is False
    kiosk._kiosk_proc = None
    kiosk._kiosk_url = None


def test_audio_playing_detection(monkeypatch):
    monkeypatch.setattr(kiosk.shutil, "which", lambda name: "/usr/bin/pactl" if name == "pactl" else None)
    monkeypatch.setattr(kiosk.subprocess, "check_output", lambda *a, **k: "1   42  PipeWire    s16le 2ch 48000Hz\n")
    assert kiosk.is_audio_playing() is True

    monkeypatch.setattr(kiosk.subprocess, "check_output", lambda *a, **k: "   \n")
    assert kiosk.is_audio_playing() is False


def test_has_user_windows_detection(monkeypatch):
    monkeypatch.setattr(kiosk.shutil, "which", lambda name: "/usr/bin/wmctrl" if name == "wmctrl" else None)
    monkeypatch.setattr(kiosk.subprocess, "check_output", lambda *a, **k: "0x01  0 host Linux Remote Player Status\n")
    assert kiosk.has_user_windows() is False

    monkeypatch.setattr(kiosk.subprocess, "check_output", lambda *a, **k: "0x02  0 host VLC media player\n")
    assert kiosk.has_user_windows() is True


def test_is_media_active_composite(monkeypatch):
    kiosk._kiosk_proc = None
    kiosk._kiosk_url = None
    kiosk._native_procs.clear()
    monkeypatch.setattr(kiosk, "is_audio_playing", lambda: False)
    monkeypatch.setattr(kiosk, "has_user_windows", lambda: False)

    assert kiosk.is_media_active() is False

    kiosk._kiosk_proc = SimpleNamespace(poll=lambda: None)
    kiosk._kiosk_url = "https://netflix.com"
    assert kiosk.is_media_active() is True
    kiosk._kiosk_proc = None
    kiosk._kiosk_url = None

    proc = SimpleNamespace(poll=lambda: None)
    kiosk._native_procs.append(proc)
    assert kiosk.is_media_active() is True
    kiosk._native_procs.clear()

    monkeypatch.setattr(kiosk, "is_audio_playing", lambda: True)
    assert kiosk.is_media_active() is True


@pytest.mark.asyncio
async def test_idle_panel_disabled_by_default(monkeypatch):
    monkeypatch.delenv("APPLIANCE_IDLE_PANEL", raising=False)
    launched = []
    monkeypatch.setattr(kiosk, "launch_kiosk", lambda url: launched.append(url) or True)
    res = await main.check_and_launch_status_panel()
    assert res is False
    assert launched == []


@pytest.mark.asyncio
async def test_idle_panel_immediate_launch_on_empty_desktop(monkeypatch):
    monkeypatch.setenv("APPLIANCE_IDLE_PANEL", "true")
    monkeypatch.setattr(kiosk, "is_status_panel_running", lambda: False)
    monkeypatch.setattr(kiosk, "is_media_active", lambda: False)
    main.connected_clients = 0
    main.client_disconnected_during_media_time = 0.0

    launched = []
    monkeypatch.setattr(kiosk, "launch_kiosk", lambda url: launched.append(url) or True)

    res = await main.check_and_launch_status_panel()
    assert res is True
    assert len(launched) == 1
    assert launched[0].startswith(f"https://127.0.0.1:{os.getenv('PORT', '8000')}/status?v=")
    assert launched[0].rsplit("?v=", 1)[1].isdigit()


@pytest.mark.asyncio
async def test_idle_panel_skips_when_status_panel_already_running(monkeypatch):
    monkeypatch.setenv("APPLIANCE_IDLE_PANEL", "true")
    monkeypatch.setattr(kiosk, "is_status_panel_running", lambda: True)
    monkeypatch.setattr(kiosk, "is_media_active", lambda: False)

    launched = []
    monkeypatch.setattr(kiosk, "launch_kiosk", lambda url: launched.append(url) or True)

    res = await main.check_and_launch_status_panel()
    assert res is False
    assert launched == []


@pytest.mark.asyncio
async def test_idle_panel_never_interrupts_active_media(monkeypatch):
    monkeypatch.setenv("APPLIANCE_IDLE_PANEL", "true")
    monkeypatch.setattr(kiosk, "is_status_panel_running", lambda: False)
    monkeypatch.setattr(kiosk, "is_media_active", lambda: True)
    main.connected_clients = 0
    main.client_disconnected_during_media_time = 0.0

    launched = []
    monkeypatch.setattr(kiosk, "launch_kiosk", lambda url: launched.append(url) or True)

    res = await main.check_and_launch_status_panel()
    assert res is False
    assert launched == []


@pytest.mark.asyncio
async def test_idle_panel_respects_45s_safety_delay_after_disconnect_during_media(monkeypatch):
    monkeypatch.setenv("APPLIANCE_IDLE_PANEL", "true")
    monkeypatch.setattr(kiosk, "is_status_panel_running", lambda: False)
    monkeypatch.setattr(kiosk, "is_media_active", lambda: False)
    main.connected_clients = 0

    # Disconnected 10 seconds ago during media
    main.client_disconnected_during_media_time = time.time() - 10.0

    launched = []
    monkeypatch.setattr(kiosk, "launch_kiosk", lambda url: launched.append(url) or True)

    # Within 45s: must not launch
    res = await main.check_and_launch_status_panel()
    assert res is False
    assert launched == []

    # After 45s (e.g. 50s ago): must launch
    main.client_disconnected_during_media_time = time.time() - 50.0
    res = await main.check_and_launch_status_panel()
    assert res is True
    assert len(launched) == 1
    assert launched[0].startswith(f"https://127.0.0.1:{os.getenv('PORT', '8000')}/status?v=")
    assert launched[0].rsplit("?v=", 1)[1].isdigit()


@pytest.mark.asyncio
async def test_stop_kiosk_resets_safety_delay_and_launches_status(monkeypatch):
    monkeypatch.setenv("APPLIANCE_IDLE_PANEL", "true")
    monkeypatch.setattr(kiosk, "is_status_panel_running", lambda: False)
    monkeypatch.setattr(kiosk, "is_media_active", lambda: False)
    monkeypatch.setattr(kiosk, "close_all", lambda: None)
    main.connected_clients = 0
    main.client_disconnected_during_media_time = time.time() - 5.0

    launched = []
    monkeypatch.setattr(kiosk, "launch_kiosk", lambda url: launched.append(url) or True)

    res = await main.stop_kiosk()
    assert res == {"status": "success"}
    assert main.client_disconnected_during_media_time == 0.0

    await asyncio.sleep(0.05)
    assert len(launched) == 1
    assert launched[0].startswith(f"https://127.0.0.1:{os.getenv('PORT', '8000')}/status?v=")
    assert launched[0].rsplit("?v=", 1)[1].isdigit()


class _FakeClock:
    """Reloj controlado para verificar los limites exactos del backoff (D2)."""

    def __init__(self, start: float = 1000.0):
        self.now = start

    def time(self) -> float:
        return self.now


@pytest.mark.asyncio
async def test_idle_panel_cooldown_30s_exact_boundaries(monkeypatch):
    """D2: limite de 30 s exacto: 29 s bloqueado, 31 s permitido."""
    monkeypatch.setenv("APPLIANCE_IDLE_PANEL", "true")
    monkeypatch.setattr(kiosk, "is_status_panel_running", lambda: False)
    monkeypatch.setattr(kiosk, "is_media_active", lambda: False)
    main.connected_clients = 0
    main.client_disconnected_during_media_time = 0.0

    clock = _FakeClock()
    monkeypatch.setattr(main, "time", clock)

    launched = []
    monkeypatch.setattr(kiosk, "launch_kiosk", lambda url: launched.append(url) or False)

    t0 = clock.now
    assert await main.check_and_launch_status_panel() is False
    assert len(launched) == 1
    assert main._panel_fail_streak == 1
    assert main._last_panel_attempt == t0

    clock.now = t0 + 29.0
    assert await main.check_and_launch_status_panel() is False
    assert len(launched) == 1

    clock.now = t0 + 31.0
    assert await main.check_and_launch_status_panel() is False
    assert len(launched) == 2
    assert main._panel_fail_streak == 2


@pytest.mark.asyncio
async def test_idle_panel_success_does_not_block_relaunch(monkeypatch):
    """D4: un lanzamiento exitoso no abre ventana de bloqueo (p. ej. tras stop_kiosk)."""
    monkeypatch.setenv("APPLIANCE_IDLE_PANEL", "true")
    monkeypatch.setattr(kiosk, "is_status_panel_running", lambda: False)
    monkeypatch.setattr(kiosk, "is_media_active", lambda: False)
    main.connected_clients = 0
    main.client_disconnected_during_media_time = 0.0

    clock = _FakeClock()
    monkeypatch.setattr(main, "time", clock)

    launched = []
    monkeypatch.setattr(kiosk, "launch_kiosk", lambda url: launched.append(url) or True)

    assert await main.check_and_launch_status_panel() is True
    assert main._panel_fail_streak == 0
    # Sin avanzar el reloj: el exito no debe bloquear el siguiente intento.
    assert await main.check_and_launch_status_panel() is True
    assert len(launched) == 2


@pytest.mark.asyncio
async def test_idle_panel_backoff_120s_exact_boundaries(monkeypatch):
    """D2: tras 3 fallos, 119 s bloqueado y 121 s permitido."""
    monkeypatch.setenv("APPLIANCE_IDLE_PANEL", "true")
    monkeypatch.setattr(kiosk, "is_status_panel_running", lambda: False)
    monkeypatch.setattr(kiosk, "is_media_active", lambda: False)
    main.connected_clients = 0
    main.client_disconnected_during_media_time = 0.0

    clock = _FakeClock()
    monkeypatch.setattr(main, "time", clock)

    launched = []
    monkeypatch.setattr(kiosk, "launch_kiosk", lambda url: launched.append(url) or False)

    for offset in (0.0, 40.0, 80.0):
        clock.now = offset
        await main.check_and_launch_status_panel()
    assert len(launched) == 3
    assert main._panel_fail_streak == 3
    t3 = clock.now

    clock.now = t3 + 119.0
    assert await main.check_and_launch_status_panel() is False
    assert len(launched) == 3

    clock.now = t3 + 121.0
    await main.check_and_launch_status_panel()
    assert len(launched) == 4
    assert main._panel_fail_streak == 4


def test_is_display_ready_and_wait_for_display(monkeypatch):
    monkeypatch.setattr(kiosk.os, "name", "posix")
    monkeypatch.setattr(kiosk.os.path, "exists", lambda p: True)
    monkeypatch.setattr(kiosk.shutil, "which", lambda cmd: "/usr/bin/xset" if cmd == "xset" else None)
    
    # 1. Success case: xset q succeeds
    monkeypatch.setattr(kiosk.subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=0))
    assert kiosk.is_display_ready() is True
    assert kiosk.wait_for_display(timeout=1.0) is True

    # 2. Failure case: xset q fails
    monkeypatch.setattr(kiosk.subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=1))
    assert kiosk.is_display_ready() is False


def test_launch_fails_when_display_not_ready(monkeypatch):
    monkeypatch.setattr(kiosk, "kill_existing_kiosks", lambda: None)
    monkeypatch.setattr(kiosk, "find_browser", lambda: ("/usr/bin/firefox-esr", "firefox-esr"))
    monkeypatch.setattr(kiosk, "wait_for_display", lambda timeout=10.0: False)
    assert kiosk.launch_kiosk("https://example.test") is False


def test_launch_detects_immediate_process_crash(monkeypatch, tmp_path):
    monkeypatch.setattr(kiosk, "kill_existing_kiosks", lambda: None)
    monkeypatch.setattr(kiosk, "find_browser", lambda: ("/usr/bin/firefox-esr", "firefox-esr"))
    monkeypatch.setattr(kiosk, "wait_for_display", lambda timeout=10.0: True)
    monkeypatch.setattr(kiosk.os.path, "expanduser", lambda path: str(tmp_path))
    # Mock process that dies immediately (poll returns 1)
    monkeypatch.setattr(kiosk.subprocess, "Popen", lambda *a, **kw: SimpleNamespace(poll=lambda: 1, pid=999))
    assert kiosk.launch_kiosk("https://example.test") is False
    assert kiosk._kiosk_proc is None


@pytest.mark.asyncio
async def test_api_panel_show_allows_local_access(monkeypatch):
    launched = []
    monkeypatch.setattr(main, "launch_kiosk", lambda url: launched.append(url) or True)
    from starlette.testclient import TestClient
    client = TestClient(main.app, client=("127.0.0.1", 50000))
    resp = client.post("/api/panel/show")
    assert resp.status_code == 200
    assert resp.json() == {"status": "success"}
    assert len(launched) == 1
    # /api/panel/show NO agrega cache-busting (B30 solo aplica al auto-lanzamiento).
    assert launched[0].endswith("/status")



