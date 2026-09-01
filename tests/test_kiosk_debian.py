import os
import signal
from pathlib import Path
from types import SimpleNamespace

import pytest

from backend import kiosk


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = (ROOT / "scripts" / "install.sh").read_text()


def test_find_browser_accepts_only_executable_debian_path(monkeypatch):
    monkeypatch.setattr(kiosk.os.path, "isfile", lambda path: path == "/usr/bin/firefox-esr")
    monkeypatch.setattr(kiosk.os, "access", lambda path, mode: path == "/usr/bin/firefox-esr")
    assert kiosk.find_browser() == ("/usr/bin/firefox-esr", "firefox-esr")


def test_find_browser_reports_missing_esr(monkeypatch):
    monkeypatch.setattr(kiosk.os.path, "isfile", lambda _path: False)
    assert kiosk.find_browser() == (None, None)


def test_gui_env_is_xorg_only(monkeypatch):
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    monkeypatch.setenv("DISPLAY", ":7")
    monkeypatch.setattr(kiosk.os, "getuid", lambda: 1001, raising=False)
    env = kiosk.gui_env()
    assert env["DISPLAY"] == ":7"
    assert env["XDG_RUNTIME_DIR"] == "/run/user/1001"
    assert env["HOME"] == os.path.expanduser("~")
    assert env["XAUTHORITY"] == os.path.join(env["HOME"], ".Xauthority")
    assert "WAYLAND_DISPLAY" not in env


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
    assert calls["cmd"] == ["/usr/bin/firefox-esr", "--kiosk", "--no-remote", "-profile", str(tmp_path), "https://example.test"]
    assert calls["kwargs"]["start_new_session"] is True
    assert modes == [(str(tmp_path), 0o700)]


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
    policy.write_text('{"uBlock": true}')
    monkeypatch.setattr(kiosk, "find_browser", lambda: ("/usr/bin/firefox-esr", "firefox-esr"))
    monkeypatch.setattr(kiosk.os.path, "exists", lambda path: path == "/etc/firefox/policies/policies.json")
    monkeypatch.setattr(kiosk, "open", lambda *args, **kwargs: policy.open(*args[1:], **kwargs), raising=False)
    assert kiosk.adblock_status() == "ubo-firefox"


def test_runtime_has_no_forbidden_browser_or_desktop_paths():
    source = (ROOT / "backend" / "kiosk.py").read_text()
    for forbidden in ("brave", "chromium", "/snap/", "qdbus", "KWin", "tempfile", "WAYLAND_DISPLAY", "gdm", "plasma", "krunner"):
        assert forbidden not in source


def test_installer_requires_esr_and_removes_browser_fallbacks():
    assert "apt-get install -y" in INSTALLER
    assert "firefox-esr" in INSTALLER
    assert "apt-get install -y firefox-esr ||" not in INSTALLER
    for forbidden in ("qdbus", "kwriteconfig", "kbuildsycoca", "certutil", "xdg-open", "chromium"):
        assert forbidden not in INSTALLER
    assert "/etc/firefox/policies/policies.json" in INSTALLER
    assert "platform-bootstrap.sh" in INSTALLER
