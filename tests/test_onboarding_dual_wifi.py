"""Unit tests for T-137: TV Kiosk OSD Settings tab and Dual Wi-Fi Onboarding logic.
Validates keyboard detection, network evaluation, hotspot auto-creation,
state transitions, and OSD panel elements.
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
from main import app


@pytest.fixture
def client():
    return TestClient(app, client=("127.0.0.1", 50000))


def test_keyboard_detection_filters_virtual(monkeypatch):
    """Certify keyboard detection distinguishes real physical hardware from virtual uinput/LRP."""
    # Virtual uinput only
    virtual_devices = """
I: Bus=0003 Vendor=1234 Product=5678 Version=0111
N: Name="LinuxRemotePlayer Emulated Gamepad"
P: Phys=
S: Sysfs=/devices/virtual/input/input20
U: Uniq=
H: Handlers=event20 kbd
B: PROP=0
B: EV=120013
B: KEY=10000 0 0 0 0

I: Bus=0003 Vendor=0001 Product=0001 Version=0100
N: Name="py-evdev-uinput"
H: Handlers=event21 kbd
"""
    monkeypatch.delenv("LRP_MOCK_KEYBOARD", raising=False)
    monkeypatch.setattr(os.path, "exists", lambda p: p == "/proc/bus/input/devices")

    import builtins
    orig_open = builtins.open

    def mock_open(path, *args, **kwargs):
        if str(path) == "/proc/bus/input/devices":
            from io import StringIO
            return StringIO(virtual_devices)
        return orig_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", mock_open)
    # With only virtual uinput keyboards, should return False
    assert system_platform.is_physical_keyboard_connected() is False

    # Now add real USB keyboard
    real_devices = virtual_devices + """
I: Bus=0003 Vendor=046d Product=c31c Version=0111
N: Name="Logitech USB Keyboard"
H: Handlers=sysrq kbd event5
"""

    def mock_open_real(path, *args, **kwargs):
        if str(path) == "/proc/bus/input/devices":
            from io import StringIO
            return StringIO(real_devices)
        return orig_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", mock_open_real)
    assert system_platform.is_physical_keyboard_connected() is True


def test_dual_onboarding_modes(client, monkeypatch):
    """Certify the three dual onboarding state paths:
    1. Network active -> 'normal'
    2. Network inactive + keyboard attached -> 'wifi_keyboard'
    3. Network inactive + no keyboard -> 'wifi_hotspot'
    """
    # 1. Normal mode (connected to LAN/Wi-Fi)
    monkeypatch.setenv("LRP_MOCK_NETWORK", "1")
    monkeypatch.setenv("LRP_MOCK_KEYBOARD", "0")
    resp = client.get("/api/system/onboarding")
    assert resp.status_code == 200
    assert resp.json()["mode"] == "normal"
    assert resp.json()["has_network"] is True

    # 2. Case A: No network, but keyboard attached
    monkeypatch.setenv("LRP_MOCK_NETWORK", "0")
    monkeypatch.setenv("LRP_MOCK_KEYBOARD", "1")
    resp = client.get("/api/system/onboarding")
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "wifi_keyboard"
    assert data["has_network"] is False
    assert data["keyboard_detected"] is True

    # 3. Case B: No network, and NO keyboard attached (Appliance headless first-boot)
    monkeypatch.setenv("LRP_MOCK_NETWORK", "0")
    monkeypatch.setenv("LRP_MOCK_KEYBOARD", "0")
    resp = client.get("/api/system/onboarding")
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "wifi_hotspot"
    assert data["has_network"] is False
    assert data["keyboard_detected"] is False


def test_hotspot_lifecycle_and_auto_termination_on_wifi_connect(client, monkeypatch):
    """Certify starting hotspot creates LRP-Setup-XXXX and connecting to Wi-Fi terminates hotspot."""
    # 1. Start Hotspot
    resp = client.post("/api/system/onboarding/hotspot/start")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert "LRP-Setup-" in data["hotspot"]["ssid"]
    assert system_platform._hotspot_state["active"] is True

    # 2. Verify onboarding reflects active hotspot
    status = client.get("/api/system/onboarding").json()
    assert status["hotspot_active"] is True
    assert status["hotspot_ssid"] == data["hotspot"]["ssid"]

    # 3. Mock Wi-Fi connection success
    monkeypatch.setattr(shutil, "which", lambda cmd: "/usr/bin/nmcli" if cmd == "nmcli" else None)
    monkeypatch.setattr(
        subprocess, "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="Successfully activated", stderr="")
    )

    connect_resp = client.post("/api/system/wifi/connect", json={"ssid": "HomeNetwork", "password": "MyPassword123"})
    assert connect_resp.status_code == 200
    assert connect_resp.json()["ok"] is True

    # Hotspot MUST be automatically stopped upon successful connection
    assert system_platform._hotspot_state["active"] is False
    status_after = client.get("/api/system/onboarding").json()
    assert status_after["hotspot_active"] is False


def test_status_html_contains_settings_tab_and_tv_accessibility():
    """Certify frontend/status.html contains TV settings tab, audio/wifi/display elements, and keyboard listeners."""
    status_file = ROOT / "frontend" / "status.html"
    assert status_file.is_file()
    content = status_file.read_text(encoding="utf-8")

    # Tab navigation
    assert 'tab-btn-pairing' in content
    assert 'tab-btn-settings' in content
    assert 'pane-pairing' in content
    assert 'pane-settings' in content

    # Settings elements for Audio, Wi-Fi, Display
    assert 'setting-audio-sink' in content
    assert 'setting-audio-vol-slider' in content
    assert 'wifi-networks-list' in content
    assert 'wifi-connect-box' in content
    assert 'display-output-name' in content
    assert 'display-resolution' in content

    # Onboarding banner
    assert 'onboarding-banner' in content
    assert 'checkOnboarding' in content

    # TV Accessibility: High-contrast focus outline & Keyboard listener
    assert ':focus' in content
    assert 'keydown' in content
