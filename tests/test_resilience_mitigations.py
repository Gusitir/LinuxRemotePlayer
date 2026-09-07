"""Deterministic unit tests for resilience mitigations:
- ASTRA-03: Asynchronous voice processing decoupled from main WebSocket receive loop.
- ASTRA-04: HTTPS certificate expiration checking (notAfter), automatic renewal (<48h), and RTC safeguard.
"""
import os
import sys
import time
import asyncio
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest
from starlette.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import run as run_module
import auth
import main
from main import app, voice_enabled


def test_cert_date_parsing_and_expiration(tmp_path, monkeypatch):
    """ASTRA-04: Tests parse_cert_dates and is_cert_expiring_or_invalid with varied time vectors."""
    cert_dir = tmp_path / "certs"
    cert_dir.mkdir(parents=True, exist_ok=True)
    key_file = cert_dir / "test.key"
    cert_file = cert_dir / "test.crt"

    # Generate a certificate valid for 10 days
    openssl_bin = run_module.OPENSSL_BIN
    subprocess.run(
        [openssl_bin, "req", "-x509", "-newkey", "rsa:2048", "-keyout", str(key_file),
         "-out", str(cert_file), "-days", "10", "-nodes", "-subj", "/CN=127.0.0.1"],
        check=True, capture_output=True
    )

    # 1. Verify parse_cert_dates
    nb, na = run_module.parse_cert_dates(str(cert_file))
    assert nb is not None
    assert na is not None
    assert na > nb
    diff = na - nb
    assert 9 <= diff.days <= 11

    # 2. Currently valid cert (tested at issue time + 1 hour)
    t_valid = nb + timedelta(hours=1)
    assert run_module.is_cert_expiring_or_invalid(str(cert_file), min_hours=48.0, current_time=t_valid) is False

    # 3. Expiring cert (tested 24 hours before expiration, min_hours=48h)
    t_expiring = na - timedelta(hours=24)
    assert run_module.is_cert_expiring_or_invalid(str(cert_file), min_hours=48.0, current_time=t_expiring) is True

    # 4. Expired cert (tested 1 hour after expiration)
    t_expired = na + timedelta(hours=1)
    assert run_module.is_cert_expiring_or_invalid(str(cert_file), min_hours=48.0, current_time=t_expired) is True

    # 5. RTC Safeguard: system clock desynchronized / dead CMOS battery (e.g. year 1970 or 2000)
    t_rtc_dead = datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert run_module.is_cert_expiring_or_invalid(str(cert_file), min_hours=48.0, current_time=t_rtc_dead) is False

    # 6. Corrupt / nonexistent file
    assert run_module.is_cert_expiring_or_invalid(str(cert_dir / "nonexistent.crt")) is True


def test_ensure_cert_regeneration_and_rtc_safeguard(tmp_path, monkeypatch):
    """ASTRA-04: Test ensure_cert automatically renews expired certs and preserves valid certs under RTC drift."""
    cert_dir = tmp_path / "app_certs"
    cert_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(run_module, "CERT_DIR", str(cert_dir))
    monkeypatch.setattr(run_module, "CA_KEY_FILE", str(cert_dir / "ca.key"))
    monkeypatch.setattr(run_module, "CA_CERT_FILE", str(cert_dir / "ca.pem"))
    monkeypatch.setattr(run_module, "KEY_FILE", str(cert_dir / "cert.key"))
    monkeypatch.setattr(run_module, "CERT_FILE", str(cert_dir / "cert.pem"))

    ip = "127.0.0.1"
    fqdn = "htpc.local"

    # 1. First run generates CA and Leaf cert
    ok = run_module.ensure_cert(ip, fqdn)
    assert ok is True
    assert (cert_dir / "ca.pem").is_file()
    assert (cert_dir / "cert.pem").is_file()
    original_leaf_content = (cert_dir / "cert.pem").read_text()

    # 2. Re-running with valid cert and same identity returns True without modifying leaf cert
    ok = run_module.ensure_cert(ip, fqdn)
    assert ok is True
    assert (cert_dir / "cert.pem").read_text() == original_leaf_content

    # 3. Simulate certificate expired: mock is_cert_expiring_or_invalid to return True
    monkeypatch.setattr(run_module, "is_cert_expiring_or_invalid", lambda cert_file, min_hours=48.0: True)
    ok = run_module.ensure_cert(ip, fqdn)
    assert ok is True
    # Leaf cert must be regenerated (content differs)
    renewed_content = (cert_dir / "cert.pem").read_text()
    assert renewed_content != original_leaf_content

    # 4. Under RTC desynchronization (clock in 1970 prior to notBefore), ensure_cert preserves existing cert
    monkeypatch.undo()
    monkeypatch.setattr(run_module, "CERT_DIR", str(cert_dir))
    monkeypatch.setattr(run_module, "CA_KEY_FILE", str(cert_dir / "ca.key"))
    monkeypatch.setattr(run_module, "CA_CERT_FILE", str(cert_dir / "ca.pem"))
    monkeypatch.setattr(run_module, "KEY_FILE", str(cert_dir / "cert.key"))
    monkeypatch.setattr(run_module, "CERT_FILE", str(cert_dir / "cert.pem"))

    class MockDatetime:
        @classmethod
        def now(cls, tz=None):
            return datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        @classmethod
        def strptime(cls, *args, **kwargs):
            return datetime.strptime(*args, **kwargs)

    monkeypatch.setattr(run_module, "datetime", MockDatetime)
    ok = run_module.ensure_cert(ip, fqdn)
    assert ok is True
    # Leaf cert must be preserved without regeneration
    assert (cert_dir / "cert.pem").read_text() == renewed_content


def test_websocket_voice_async_decoupling(tmp_path, monkeypatch):
    """ASTRA-03: Binary audio processing is decoupled from the main WebSocket loop,
    ensuring ping/pong heartbeats respond promptly during long-running voice inference."""
    custom_dir = tmp_path / "lrp_data"
    custom_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("LRP_DATA_DIR", str(custom_dir))

    token = "voice_test_token_999"
    token_file = custom_dir / ".pairing_token"
    token_file.write_text(token, encoding="ascii")
    monkeypatch.setattr(auth, "PAIRING_TOKEN", token)
    monkeypatch.setattr(main, "voice_enabled", lambda: True)

    voice_command_can_finish = asyncio.Event()

    async def mock_voice_command(audio_data, valid_targets=None):
        # Simulate long-running STT/LLM inference
        await voice_command_can_finish.wait()
        return {
            "ok": True,
            "text": "play music",
            "intent": {
                "action": "media_control",
                "parameters": {"key": "KEY_PLAY"}
            }
        }

    monkeypatch.setattr(main, "voice_command", mock_voice_command)

    client = TestClient(app, client=("127.0.0.1", 50000))

    with client.websocket_connect(f"/ws?token={token}") as ws:
        # Send binary voice audio data
        ws.send_bytes(b"dummy_audio_bytes_123456789")

        # Immediately send ping while voice_command is running in the background
        ws.send_json({"type": "ping"})

        # The client should receive messages:
        # 1. {"status": "processing", "message": "Listening..."} from voice task
        # 2. {"type": "pong"} from main receive loop responding to ping concurrently!
        received_types = []
        for _ in range(2):
            msg = ws.receive_json()
            if msg.get("type") == "pong":
                received_types.append("pong")
            elif msg.get("status") == "processing":
                received_types.append("processing")

        assert "pong" in received_types
        assert "processing" in received_types

        # Release voice inference to finish
        voice_command_can_finish.set()

        # Next messages should be Intent and Media success
        intent_msg = ws.receive_json()
        assert intent_msg.get("status") == "processing"
        assert "Intent" in intent_msg.get("message", "")

        result_msg = ws.receive_json()
        assert result_msg.get("status") == "success"


def test_get_initial_ip_acquires_dhcp_during_polling(monkeypatch):
    calls = 0

    def mock_detect_ip():
        nonlocal calls
        calls += 1
        # First 2 calls return loopback (DHCP in flight), 3rd call returns LAN IP
        if calls < 3:
            return "127.0.0.1"
        return "192.168.0.246"

    monkeypatch.setattr(run_module, "detect_ip", mock_detect_ip)
    monkeypatch.setattr(run_module.time, "sleep", lambda s: None)

    ip = run_module.get_initial_ip(timeout=5.0)
    assert ip == "192.168.0.246"
    assert calls == 3


def test_get_initial_ip_falls_back_to_loopback_on_timeout(monkeypatch):
    monkeypatch.setattr(run_module, "detect_ip", lambda: "127.0.0.1")
    ip = run_module.get_initial_ip(timeout=0.1)
    assert ip == "127.0.0.1"


def test_monitor_ip_fast_polling_on_loopback(monkeypatch):
    sleeps = []
    monkeypatch.setattr(run_module.time, "sleep", lambda s: sleeps.append(s) or (_ for _ in ()).throw(KeyboardInterrupt("stop")))
    
    # 1. On loopback initial_ip: sleep should be 2.0s
    with pytest.raises(KeyboardInterrupt):
        run_module.monitor_ip("127.0.0.1")
    assert sleeps == [2.0]

    # 2. On LAN initial_ip: sleep should be 60.0s
    sleeps.clear()
    with pytest.raises(KeyboardInterrupt):
        run_module.monitor_ip("192.168.0.246")
    assert sleeps == [60.0]

