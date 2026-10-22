"""Unit tests for system platform abstractions (/api/system/*) and Kiosk VA-API optimization.
Verifies PipeWire audio control, NetworkManager Wi-Fi, bluetoothctl, xrandr display,
and Firefox kiosk user.js hardware acceleration settings.
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace
import pytest
from starlette.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import system_platform
import kiosk
from main import app


@pytest.fixture
def client():
    return TestClient(app, client=("127.0.0.1", 50000))


WPCTL_SAMPLE_STATUS = """
Audio
 ├─ Devices:
 │      41. Built-in Audio                      [alsa]
 │      42. GA106 High Definition Audio         [alsa]
 │
 ├─ Sinks:
 │  *   49. Built-in Audio Analog Stereo        [vol: 0.65]
 │      50. GA106 High Definition Audio Digital Stereo (HDMI) [vol: 1.00 MUTED]
 │
 ├─ Sink endpoints:
 │
 ├─ Sources:
 │  *   51. Built-in Audio Analog Stereo        [vol: 0.80]
 │
 ├─ Filters:
 │
 └─ Streams:
"""


def test_get_audio_fallback_and_stub(client, monkeypatch):
    # 1. Fallback when wpctl is not available
    monkeypatch.setattr(shutil, "which", lambda cmd: None)
    resp = client.get("/api/system/audio")
    assert resp.status_code == 200
    data = resp.json()
    assert data["backend"] == "none"
    assert data["active_sink"] == "dummy"
    assert len(data["sinks"]) >= 1

    # 2. Parsing with wpctl status stub
    def mock_which(cmd):
        return "/usr/bin/wpctl" if cmd == "wpctl" else None

    def mock_subprocess_run(cmd, *args, **kwargs):
        if "status" in cmd:
            return SimpleNamespace(returncode=0, stdout=WPCTL_SAMPLE_STATUS, stderr="")
        if "get-volume" in cmd:
            return SimpleNamespace(returncode=0, stdout="Volume: 0.65\n", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(shutil, "which", mock_which)
    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)

    resp = client.get("/api/system/audio")
    assert resp.status_code == 200
    data = resp.json()
    assert data["backend"] == "pipewire"
    assert data["active_sink"] == "49"
    assert data["volume"] == 65
    assert data["muted"] is False
    assert len(data["sinks"]) == 2
    assert data["sinks"][0]["id"] == "49"
    assert data["sinks"][0]["active"] is True
    assert data["sinks"][1]["id"] == "50"
    assert data["sinks"][1]["muted"] is True


def test_set_audio_sink_and_volume(client, monkeypatch):
    recorded_cmds = []

    def mock_which(cmd):
        return "/usr/bin/wpctl" if cmd == "wpctl" else None

    def mock_run(cmd, *args, **kwargs):
        recorded_cmds.append(cmd)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(shutil, "which", mock_which)
    monkeypatch.setattr(subprocess, "run", mock_run)

    # Set default sink
    resp = client.post("/api/system/audio/sink", json={"sink_id": "50"})
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    assert recorded_cmds[-1] == ["/usr/bin/wpctl", "set-default", "50"]

    # Set volume
    resp = client.post("/api/system/audio/volume", json={"sink_id": "50", "volume": 80})
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    assert recorded_cmds[-1] == ["/usr/bin/wpctl", "set-volume", "50", "80%"]

    # Invalid volume validation (<0 or >150)
    resp = client.post("/api/system/audio/volume", json={"sink_id": "50", "volume": 200})
    assert resp.status_code == 422


NMCLI_SAMPLE_OUTPUT = """
HomeFiber_5G:88:WPA2:*
CoffeeShop_Guest:45:OPEN:
--:30:WPA2:
HomeFiber_5G:60:WPA2:
"""


def test_get_wifi_and_connect(client, monkeypatch):
    # 1. Fallback when nmcli is absent
    monkeypatch.setattr(shutil, "which", lambda cmd: None)
    resp = client.get("/api/system/wifi")
    assert resp.status_code == 200
    assert resp.json()["available"] is False

    # 2. Stubbed nmcli scan
    recorded_cmds = []

    def mock_which(cmd):
        return "/usr/bin/nmcli" if cmd == "nmcli" else None

    def mock_run(cmd, *args, **kwargs):
        recorded_cmds.append(cmd)
        if "list" in cmd:
            return SimpleNamespace(returncode=0, stdout=NMCLI_SAMPLE_OUTPUT, stderr="")
        if "connect" in cmd:
            return SimpleNamespace(returncode=0, stdout="Device 'wlan0' successfully activated", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(shutil, "which", mock_which)
    monkeypatch.setattr(subprocess, "run", mock_run)

    resp = client.get("/api/system/wifi")
    assert resp.status_code == 200
    data = resp.json()
    assert data["available"] is True
    assert data["connected"] == "HomeFiber_5G"
    assert len(data["networks"]) == 2  # Deduplicated, empty SSID excluded
    assert data["networks"][0]["ssid"] == "HomeFiber_5G"
    assert data["networks"][0]["signal"] == 88
    assert data["networks"][0]["connected"] is True

    # 3. Connect to Wi-Fi
    resp = client.post("/api/system/wifi/connect", json={"ssid": "HomeFiber_5G", "password": "SecretPassword123"})
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    assert recorded_cmds[-1] == [
        "/usr/bin/nmcli", "device", "wifi", "connect", "HomeFiber_5G", "password", "SecretPassword123"
    ]


BT_SHOW_SAMPLE = """
Controller 00:1A:7D:DA:71:10 HTPC-BT [default]
	Name: HTPC-BT
	Alias: HTPC-BT
	Class: 0x000c010c
	Powered: yes
	Discoverable: no
	Pairable: yes
"""

BT_DEVICES_SAMPLE = """
Device 00:1A:7D:DA:71:13 Xbox Wireless Controller
Device E4:50:EB:8F:22:11 Sony WH-1000XM4
"""

BT_PAIRED_SAMPLE = """
Device 00:1A:7D:DA:71:13 Xbox Wireless Controller
"""


def test_get_bluetooth(client, monkeypatch):
    def mock_which(cmd):
        return "/usr/bin/bluetoothctl" if cmd == "bluetoothctl" else None

    def mock_run(cmd, *args, **kwargs):
        if "show" in cmd:
            return SimpleNamespace(returncode=0, stdout=BT_SHOW_SAMPLE, stderr="")
        if "Paired" in cmd:
            return SimpleNamespace(returncode=0, stdout=BT_PAIRED_SAMPLE, stderr="")
        if "devices" in cmd:
            return SimpleNamespace(returncode=0, stdout=BT_DEVICES_SAMPLE, stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(shutil, "which", mock_which)
    monkeypatch.setattr(subprocess, "run", mock_run)

    resp = client.get("/api/system/bluetooth")
    assert resp.status_code == 200
    data = resp.json()
    assert data["available"] is True
    assert data["powered"] is True
    assert len(data["devices"]) == 2
    assert data["devices"][0]["name"] == "Xbox Wireless Controller"
    assert data["devices"][0]["paired"] is True
    assert data["devices"][1]["name"] == "Sony WH-1000XM4"
    assert data["devices"][1]["paired"] is False


XRANDR_SAMPLE_OUTPUT = """
Screen 0: minimum 320 x 200, current 1920 x 1080, maximum 16384 x 16384
HDMI-1 connected primary 1920x1080+0+0 (normal left inverted right x axis y axis) 1150mm x 650mm
   1920x1080     60.00*+  50.00    59.94  
   1280x720      60.00    50.00  
DP-1 disconnected (normal left inverted right x axis y axis)
"""


def test_get_display(client, monkeypatch):
    def mock_which(cmd):
        return "/usr/bin/xrandr" if cmd == "xrandr" else None

    def mock_run(cmd, *args, **kwargs):
        if "--current" in cmd:
            return SimpleNamespace(returncode=0, stdout=XRANDR_SAMPLE_OUTPUT, stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(shutil, "which", mock_which)
    monkeypatch.setattr(subprocess, "run", mock_run)

    resp = client.get("/api/system/display")
    assert resp.status_code == 200
    data = resp.json()
    assert data["available"] is True
    displays = data["displays"]
    assert len(displays) == 2
    assert displays[0]["output"] == "HDMI-1"
    assert displays[0]["connected"] is True
    assert displays[0]["primary"] is True
    assert displays[0]["current_mode"] == "1920x1080"
    assert displays[0]["refresh_rate"] == "60.00"
    assert "1920x1080" in displays[0]["modes"]
    assert displays[1]["output"] == "DP-1"
    assert displays[1]["connected"] is False


def test_kiosk_user_js_vaapi_optimization(tmp_path, monkeypatch):
    """Certify that launch_kiosk writes VA-API hardware decode preferences into user.js (Intel HD 2500 optimization)."""
    monkeypatch.setattr(kiosk, "kill_existing_kiosks", lambda: None)
    monkeypatch.setattr(kiosk, "find_browser", lambda: ("/usr/bin/firefox-esr", "firefox-esr"))
    monkeypatch.setattr(kiosk.os.path, "expanduser", lambda path: str(tmp_path) if path == "~/.config/lrp-kiosk-firefox" else path)
    monkeypatch.setattr(kiosk.subprocess, "Popen", lambda cmd, **kwargs: SimpleNamespace(poll=lambda: None, pid=1234))

    assert kiosk.launch_kiosk("https://youtube.com") is True

    user_js = tmp_path / "user.js"
    assert user_js.is_file()
    content = user_js.read_text(encoding="utf-8")

    # VA-API H.264 forcing preferences must be present
    assert 'user_pref("media.av1.enabled", false);' in content
    assert 'user_pref("media.mediasource.vp9.enabled", false);' in content
    # Session restore suppression must still be preserved
    assert 'user_pref("browser.sessionstore.resume_from_crash", false);' in content


def test_power_actions_mock_and_validation(client, monkeypatch):
    """Verify mock power actions and validation for suspend, reboot, poweroff, restart-service."""
    monkeypatch.setenv("LRP_MOCK_POWER", "true")

    for action in ["suspend", "reboot", "poweroff", "restart-service"]:
        resp = client.post(f"/api/system/power/{action}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["action"] == action
        assert data["mock"] is True

    # Invalid action
    resp = client.post("/api/system/power/invalid-action")
    assert resp.status_code == 400
    assert "Invalid power action" in resp.json()["detail"]


def test_power_actions_subprocess_dispatch(client, monkeypatch):
    """Verify actual subprocess dispatch for systemctl power actions when mock is off."""
    monkeypatch.setenv("LRP_MOCK_POWER", "false")
    monkeypatch.setattr(shutil, "which", lambda cmd: "/bin/systemctl" if cmd == "systemctl" else None)

    dispatched = []

    def mock_popen(cmd, *args, **kwargs):
        dispatched.append(cmd)
        return SimpleNamespace(pid=9999)

    monkeypatch.setattr(subprocess, "Popen", mock_popen)

    expected_cmds = {
        "suspend": ["systemctl", "suspend"],
        "reboot": ["systemctl", "reboot"],
        "poweroff": ["systemctl", "poweroff"],
        "restart-service": ["systemctl", "restart", "linuxremoteplayer.service"],
    }

    for action, expected_cmd in expected_cmds.items():
        resp = client.post(f"/api/system/power/{action}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["action"] == action
        assert data["mock"] is False

    assert dispatched == list(expected_cmds.values())
