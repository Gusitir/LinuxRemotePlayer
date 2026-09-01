import json
import re
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
BUILD = ROOT / "scripts" / "build_deb.sh"
MANIFEST = ROOT / "website" / "beta" / "latest.json"
STABLE_MANIFEST = ROOT / "website" / "latest.json"
SERVICE_WORKER = ROOT / "frontend" / "sw.js"


def test_debian_release_source_contract():
    source = BUILD.read_text(encoding="utf-8")
    assert (ROOT / "VERSION").read_text(encoding="ascii").strip() == "1.99.2"
    assert "Architecture: amd64" in source
    assert "linuxremoteplayer_${VERSION}_amd64.deb" in source
    assert "linuxremoteplayer_${VERSION}_amd64.deb.sha256" in source
    assert "firefox-esr | firefox" not in source
    assert "Recommends: firefox-esr," in source
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
    assert beta["sha256"] == "BUILD_REQUIRED"
    assert stable["version"] != beta["version"]
    assert "beta/" not in stable["deb_url"]


def _assert_manifest_ready(manifest, final_build):
    if final_build:
        assert re.fullmatch(r"[0-9a-f]{64}", manifest["sha256"])
    else:
        assert manifest["sha256"] == "BUILD_REQUIRED"


def test_manifest_placeholder_is_allowed_prebuild_but_forbidden_final_build():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    _assert_manifest_ready(manifest, final_build=False)
    with pytest.raises(AssertionError):
        _assert_manifest_ready(manifest, final_build=True)


def test_service_worker_source_remains_unstamped():
    assert "__LRP_VERSION__" in SERVICE_WORKER.read_text(encoding="utf-8")
