import base64
import json
import os
import sys
import tempfile
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts"))

import ota_security
import sign_ota_manifest

BUILD_DEB = ROOT / "scripts" / "build_deb.sh"
PUBKEY_FILE = ROOT / "scripts" / "debian" / "lrp-ota-pub.pem"


def test_ota_public_key_pem_file_and_default_constant():
    assert PUBKEY_FILE.is_file(), "lrp-ota-pub.pem must exist"
    content = PUBKEY_FILE.read_text(encoding="utf-8")
    assert "-----BEGIN PUBLIC KEY-----" in content
    assert "-----END PUBLIC KEY-----" in content
    assert ota_security.DEFAULT_OTA_PUBLIC_KEY_PEM.strip() == content.strip()


def test_key_generation_and_cli_signing():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        priv_path = tmp / "test_ota_priv.pem"
        pub_path = tmp / "test_ota_pub.pem"
        manifest_path = tmp / "latest.json"

        # 1. Generate keypair via CLI function
        sign_ota_manifest.generate_keypair(str(priv_path), str(pub_path))
        assert priv_path.is_file()
        assert pub_path.is_file()

        manifest_data = {
            "version": "2.0.0",
            "architecture": "amd64",
            "filename": "linuxremoteplayer_2.0.0_amd64.deb",
            "sha256": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "deb_url": "https://www.linuxremoteplayer.com/downloads/linuxremoteplayer_2.0.0_amd64.deb",
        }
        manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

        # 2. Sign manifest
        sign_ota_manifest.sign_manifest(str(manifest_path), str(priv_path), str(pub_path))

        signed = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert "signature" in signed
        assert len(signed["signature"]) > 40

        # 3. Verify via CLI
        rc = sign_ota_manifest.verify_manifest(str(manifest_path), str(pub_path))
        assert rc == 0


def test_signature_verification_and_tamper_detection():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        priv_path = tmp / "priv.pem"
        pub_path = tmp / "pub.pem"
        manifest_path = tmp / "latest.json"

        sign_ota_manifest.generate_keypair(str(priv_path), str(pub_path))
        manifest_data = {
            "version": "2.0.0",
            "architecture": "amd64",
            "deb_url": "https://www.linuxremoteplayer.com/downloads/linuxremoteplayer_2.0.0_amd64.deb",
            "sha256": "1111111111111111111111111111111111111111111111111111111111111111",
        }
        manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")
        sign_ota_manifest.sign_manifest(str(manifest_path), str(priv_path), str(pub_path))

        signed = json.loads(manifest_path.read_text(encoding="utf-8"))
        pub_pem = pub_path.read_text(encoding="utf-8")

        # Valid signature succeeds
        assert ota_security.verify_manifest_signature(signed, pub_pem) is True

        # Tampered sha256 fails
        tampered_sha = dict(signed)
        tampered_sha["sha256"] = "2222222222222222222222222222222222222222222222222222222222222222"
        assert ota_security.verify_manifest_signature(tampered_sha, pub_pem) is False

        # Tampered version fails
        tampered_ver = dict(signed)
        tampered_ver["version"] = "2.0.1"
        assert ota_security.verify_manifest_signature(tampered_ver, pub_pem) is False

        # Tampered URL fails
        tampered_url = dict(signed)
        tampered_url["deb_url"] = "https://malicious.com/evil.deb"
        assert ota_security.verify_manifest_signature(tampered_url, pub_pem) is False

        # Missing signature fails
        no_sig = dict(signed)
        del no_sig["signature"]
        assert ota_security.verify_manifest_signature(no_sig, pub_pem) is False

        # Corrupt signature fails
        bad_sig = dict(signed)
        bad_sig["signature"] = base64.b64encode(b"invalid_signature_bytes_length_64_padding_to_match_target_len!!").decode("ascii")
        assert ota_security.verify_manifest_signature(bad_sig, pub_pem) is False


def test_anti_downgrade_enforcement():
    # Strict inequality: remote must be strictly greater than local
    assert ota_security.is_version_newer("2.0.0", "1.99.2") is True
    assert ota_security.is_version_newer("1.99.3", "1.99.2") is True
    assert ota_security.is_version_newer("1.10.0", "1.9.0") is True

    # Same or lower version rejected
    assert ota_security.is_version_newer("1.99.2", "1.99.2") is False
    assert ota_security.is_version_newer("1.99.1", "1.99.2") is False
    assert ota_security.is_version_newer("1.8.0", "2.0.0") is False

    # Validation helper
    manifest = {
        "version": "1.99.1",
        "architecture": "amd64",
        "deb_url": "https://example.com/test.deb",
        "sha256": "abc",
        "signature": "dummy",
    }
    ok, reason = ota_security.validate_ota_manifest(manifest, "1.99.2")
    assert ok is False
    assert "anti-downgrade" in reason


def test_build_deb_updater_contracts():
    source = BUILD_DEB.read_text(encoding="utf-8")
    assert "verify_ed25519_signature" in source
    assert "check_anti_downgrade" in source
    assert 'dpkg --compare-versions "$REMOTE_VER" gt "$LOCAL_VER"' in source
    assert "rollback_ota" in source
    assert "45" in source, "Must have 45s watchdog loop"
    assert "lrp-ota-pub.pem" in source
    assert "openssl pkeyutl -verify -pubin -inkey" in source
    assert "/var/lib/linuxremoteplayer/ota-backup" in source
    assert 'main "$@"; exit $?' in source
