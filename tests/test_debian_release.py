import json
import hashlib
import re
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
BUILD = ROOT / "scripts" / "build_deb.sh"
MANIFEST = ROOT / "website" / "beta" / "latest.json"
STABLE_MANIFEST = ROOT / "website" / "latest.json"
SERVICE_WORKER = ROOT / "frontend" / "sw.js"
PACKAGE = ROOT / "website" / "beta" / "downloads" / "linuxremoteplayer_1.99.2_amd64.deb"
SIDECAR = PACKAGE.with_name(PACKAGE.name + ".sha256")


def test_debian_release_source_contract():
    source = BUILD.read_text(encoding="utf-8")
    assert (ROOT / "VERSION").read_text(encoding="ascii").strip() == "1.99.2"
    assert "Architecture: amd64" in source
    assert "chmod 0755 pkg/opt/linuxremoteplayer/scripts/debian/*.sh" in source
    assert "exec ./debian/bootstrap.sh \"$@\"" in source
    assert "sudo lrp-setup --apply --approve" in source
    assert "exec ./debian/bootstrap.sh \"$@\"" in source
    assert "exec ./install.sh" not in source
    assert "linuxremoteplayer_${VERSION}_amd64.deb" in source
    assert "linuxremoteplayer_${VERSION}_amd64.deb.sha256" in source
    assert "firefox-esr | firefox" not in source
    assert "Recommends: firefox-esr," in source
    assert "Depends: python3, python3-venv, python3-dev, build-essential, openssl, sudo, curl, ca-certificates" in source
    assert "avahi-daemon" not in source
    assert "modprobe uinput" not in source
    assert "99-linuxremoteplayer-uinput.rules" not in source
    assert "systemd-run --unit=\"linuxremoteplayer-bootstrap-ota-$$\"" in source
    assert "--resume --unattended" in source
    assert "main \"$@\"; exit $?" in source
    assert 'if [ "$1" = "remove" ]; then' in source


def test_updater_uses_architecture_neutral_temp_filename():
    source = BUILD.read_text(encoding="utf-8")
    updater = source[source.index("cat <<'INNEREOF' > /usr/local/bin/lrp-update") :]
    assert 'linuxremoteplayer_${VERSION}.deb' in updater
    assert "_all.deb" not in updater


def test_beta_manifest_is_prebuild_only_and_stable_is_isolated():
    beta = json.loads(MANIFEST.read_text(encoding="utf-8"))
    stable = json.loads(STABLE_MANIFEST.read_text(encoding="utf-8"))
    assert beta["version"] == "1.99.2"
    assert beta["architecture"] == "amd64"
    assert beta["deb_url"].endswith("linuxremoteplayer_1.99.2_amd64.deb")
    if not PACKAGE.exists():
        assert not SIDECAR.exists()
        assert beta["sha256"] == "BUILD_REQUIRED"
    else:
        assert SIDECAR.is_file()
        digest = hashlib.sha256(PACKAGE.read_bytes()).hexdigest()
        assert re.fullmatch(r"[0-9a-f]{64}", beta["sha256"])
        assert beta["sha256"] == digest
        assert SIDECAR.read_text(encoding="ascii").split() == [digest, PACKAGE.name]
    assert stable["version"] != beta["version"]
    assert "beta/" not in stable["deb_url"]


def _assert_manifest_ready(manifest, final_build):
    if final_build:
        assert re.fullmatch(r"[0-9a-f]{64}", manifest["sha256"])
    else:
        assert manifest["sha256"] == "BUILD_REQUIRED"


def test_manifest_placeholder_is_allowed_prebuild_but_forbidden_final_build():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if PACKAGE.exists():
        _assert_manifest_ready(manifest, final_build=True)
    else:
        _assert_manifest_ready(manifest, final_build=False)
        with pytest.raises(AssertionError):
            _assert_manifest_ready(manifest, final_build=True)


def test_service_worker_source_remains_unstamped():
    assert "__LRP_VERSION__" in SERVICE_WORKER.read_text(encoding="utf-8")
