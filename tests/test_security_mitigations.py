"""Unit tests for ASTRA-01 and ASTRA-02 security mitigations (T-134).

ASTRA-01:
- /opt/linuxremoteplayer and .venv strictly owned by root:root (0755/0644).
- Mutable state (.env, .pairing_token, certs/) isolated in /var/lib/linuxremoteplayer (lrp:lrp 0700).
- Config module resolves /var/lib/linuxremoteplayer in appliance mode and backend/ in dev.

PH24:
- No license exists in the backend: no remote check, no gate, no cloud proxy.
- /api/license/* endpoints are local inert stubs that never touch the network.

ASTRA-02:
- Rotating pairing token immediately terminates and revokes all active authenticated WebSocket sessions.
- Clients must re-authenticate with the newly generated token.
"""
import os
import sys
from pathlib import Path
import pytest
from starlette.websockets import WebSocketDisconnect
from starlette.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import config
import auth
import ai_pipeline
from main import app, active_authenticated_websockets


def test_config_paths_with_lrp_data_dir(tmp_path, monkeypatch):
    custom_dir = tmp_path / "var_lib_lrp"
    monkeypatch.setenv("LRP_DATA_DIR", str(custom_dir))

    data_dir = config.get_data_dir()
    assert data_dir == custom_dir
    assert custom_dir.is_dir()

    assert config.get_token_file() == custom_dir / ".pairing_token"
    assert config.get_env_file() == custom_dir / ".env"
    # PH24: licensing state no longer exists in the configuration surface.
    assert not hasattr(config, "get_license_cache_file")
    assert config.get_certs_dir() == custom_dir / "certs"
    assert config.get_ca_key_file() == custom_dir / "certs" / "ca.key"
    assert config.get_ca_cert_file() == custom_dir / "certs" / "ca.pem"


def test_config_legacy_fallback_when_file_exists_in_backend(monkeypatch):
    monkeypatch.delenv("LRP_DATA_DIR", raising=False)

    # In dev mode without LRP_DATA_DIR and without /var/lib/linuxremoteplayer
    data_dir = config.get_data_dir()
    if data_dir == BACKEND_DIR:
        legacy_token = BACKEND_DIR / ".pairing_token"
        if legacy_token.is_file():
            assert config.get_token_file() == legacy_token


def test_scripts_enforce_astra01_root_isolation():
    installer = (ROOT / "scripts" / "install.sh").read_text(encoding="utf-8")
    builder = (ROOT / "scripts" / "build_deb.sh").read_text(encoding="utf-8")
    uninstall = (ROOT / "scripts" / "uninstall.sh").read_text(encoding="utf-8")

    # install.sh enforces root:root on /opt/linuxremoteplayer and lrp:lrp 0700 on /var/lib/linuxremoteplayer
    assert 'chown -R "$TARGET_USER":"$TARGET_USER" /opt/linuxremoteplayer' not in installer
    assert "chown -R root:root /opt/linuxremoteplayer" in installer
    assert "mkdir -p /var/lib/linuxremoteplayer" in installer
    assert 'chown "$TARGET_USER":"$TARGET_USER" /var/lib/linuxremoteplayer' in installer
    assert "chmod 0700 /var/lib/linuxremoteplayer" in installer

    # postinst enforces root:root on /opt/linuxremoteplayer and lrp:lrp 0700 on /var/lib/linuxremoteplayer
    assert "chown -R root:root /opt/linuxremoteplayer" in builder
    assert "mkdir -p /var/lib/linuxremoteplayer" in builder
    assert "chown -R lrp:lrp /var/lib/linuxremoteplayer" in builder
    assert "chmod 0700 /var/lib/linuxremoteplayer" in builder

    # lrp-update checks /var/lib/linuxremoteplayer/.env
    assert "ENV_FILE=/var/lib/linuxremoteplayer/.env" in builder

    # uninstall retains /var/lib/linuxremoteplayer
    assert "/var/lib/linuxremoteplayer" in uninstall


def test_websocket_immediate_revocation_on_token_regenerate(tmp_path, monkeypatch):
    custom_dir = tmp_path / "lrp_state"
    custom_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("LRP_DATA_DIR", str(custom_dir))

    # Initialize pairing token
    initial_token = "valid_initial_token_12345"
    token_file = custom_dir / ".pairing_token"
    token_file.write_text(initial_token, encoding="ascii")
    auth.PAIRING_TOKEN = initial_token

    client = TestClient(app, client=("127.0.0.1", 50000))

    # 1. Connect WebSocket with current valid token
    with client.websocket_connect(f"/ws?token={initial_token}") as ws:
        # Ping/pong to verify active communication
        ws.send_json({"type": "ping"})
        data = ws.receive_json()
        assert data.get("type") == "pong"

        # 2. Call local regenerate endpoint
        resp = client.post("/api/pairing-token/regenerate")
        assert resp.status_code == 200
        new_token = resp.json()["token"]
        assert new_token != initial_token
        assert auth.PAIRING_TOKEN == new_token

        # 3. ASTRA-02: Existing WebSocket must be forcibly closed
        with pytest.raises(Exception):
            ws.send_json({"type": "ping"})
            # Should raise WebSocketDisconnect or receive close code 1008
            ws.receive_json()

    # 4. Connecting with old token is rejected upon attempting command
    with client.websocket_connect(f"/ws?token={initial_token}") as ws_old:
        ws_old.send_json({"type": "ping"})
        err_msg = ws_old.receive_json()
        assert err_msg.get("status") == "error"
        assert err_msg.get("message") == "Unauthorized"
        with pytest.raises(WebSocketDisconnect) as exc_info:
            ws_old.receive_json()
        assert exc_info.value.code == 1008

    # 5. Connecting with newly rotated token succeeds
    with client.websocket_connect(f"/ws?token={new_token}") as ws_new:
        ws_new.send_json({"type": "ping"})
        data = ws_new.receive_json()
        assert data.get("type") == "pong"


def test_token_regenerate_alias_endpoint(tmp_path, monkeypatch):
    custom_dir = tmp_path / "lrp_state"
    custom_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("LRP_DATA_DIR", str(custom_dir))

    initial_token = "alias_initial_token_9999"
    token_file = custom_dir / ".pairing_token"
    token_file.write_text(initial_token, encoding="ascii")
    auth.PAIRING_TOKEN = initial_token

    client = TestClient(app, client=("127.0.0.1", 50000))

    # Test /api/token/regenerate alias
    resp = client.post("/api/token/regenerate")
    assert resp.status_code == 200
    new_token = resp.json()["token"]
    assert new_token != initial_token
    assert auth.PAIRING_TOKEN == new_token

    # Test /api/token alias
    resp_get = client.get("/api/token")
    assert resp_get.status_code == 200
    assert resp_get.json()["token"] == new_token


def test_ph24_license_routes_are_local_and_inert(tmp_path, monkeypatch):
    """PH24: no remote license check, no gate and no cloud proxy anywhere."""
    custom_dir = tmp_path / "lrp_state_ph24"
    custom_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("LRP_DATA_DIR", str(custom_dir))

    token = "ph24_local_token_123456"
    (custom_dir / ".pairing_token").write_text(token, encoding="ascii")
    monkeypatch.setattr(auth, "PAIRING_TOKEN", token)

    # License code cannot reach the network: no HTTP client, cloud URL or remote check.
    for module in (auth, ai_pipeline):
        source = Path(module.__file__).read_text(encoding="utf-8").lower()
        assert "httpx" not in source
        assert "supabase" not in source
        assert "license_api_url" not in source
        assert "proxy_license_action" not in source
        assert "is_license_valid_cached_or_online" not in source

    client = TestClient(app, client=("127.0.0.1", 50000))
    headers = {"X-Auth-Token": token}

    status = client.get("/api/license/status", headers=headers)
    assert status.status_code == 200
    body = status.json()
    assert body["licensed"] is True
    assert body["source"] == "local"
    assert body["plan"] == "appliance"
    assert "voice_enabled" in body

    activated = client.post("/api/license/activate", headers=headers, json={"key": "ANY-KEY"})
    assert activated.status_code == 200
    assert activated.json()["status"] == "not_required"
    assert activated.json()["licensed"] is True

    takeover = client.post("/api/license/takeover", headers=headers)
    assert takeover.status_code == 200
    assert takeover.json()["status"] == "not_required"
