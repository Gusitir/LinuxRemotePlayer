import hashlib
import json
import re
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="ascii").strip()
# D51: el canal beta queda congelado en 1.99.2; VERSION avanza a 2.0.0 (estable).
BETA_VERSION = "1.99.2"
PACKAGE = ROOT / "website" / "beta" / "downloads" / f"linuxremoteplayer_{BETA_VERSION}_amd64.deb"
SIDECAR = PACKAGE.with_name(PACKAGE.name + ".sha256")
MANIFEST = ROOT / "website" / "beta" / "latest.json"


def test_release_metadata_and_template_are_beta_only():
    assert VERSION == "2.0.0"
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert changelog.startswith("# Changelog")
    assert re.search(r"## \[2\.0\.0\] - 2026-10-21", changelog)
    top_entry = changelog.split("## [1.99.2]", 1)[0]
    assert "LRP OS Appliance 2.0" in top_entry

    template = json.loads((ROOT / "website" / "beta" / "latest.template.json").read_text())
    assert template["version"] == "__BETA_VERSION__"
    assert template["deb_url"] == (
        "https://www.linuxremoteplayer.com/beta/downloads/__BETA_DEB_FILENAME__"
    )
    assert template["sha256"] == "__BETA_SHA256__"


def test_live_beta_artifact_sidecar_and_manifest_cohere():
    assert MANIFEST.is_file()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest["sha256"] == "BUILD_REQUIRED":
        assert not PACKAGE.exists()
        assert not SIDECAR.exists()
        pytest.skip("prebuild beta manifest")
    assert re.fullmatch(r"[0-9a-f]{64}", manifest["sha256"])
    assert PACKAGE.is_file()
    assert SIDECAR.is_file()
    digest = hashlib.sha256(PACKAGE.read_bytes()).hexdigest()
    sidecar = SIDECAR.read_text(encoding="ascii").split()
    assert sidecar == [digest, PACKAGE.name]

    assert manifest["version"] == BETA_VERSION
    assert manifest["deb_url"] == (
        "https://www.linuxremoteplayer.com/beta/downloads/" + PACKAGE.name
    )
    assert manifest["sha256"] == digest


def _wsl_path(path):
    drive = path.drive.rstrip(":").lower()
    return f"/mnt/{drive}{path.as_posix()[2:]}"


def _dpkg_deb(arguments):
    executable = shutil.which("dpkg-deb")
    if executable:
        command = [executable, *arguments]
    else:
        native_arguments = [
            _wsl_path(Path(arg)) if Path(arg).is_absolute() else arg for arg in arguments
        ]
        command = ["wsl", "bash", "-lc", "dpkg-deb " + shlex.join(native_arguments)]
    return subprocess.run(command, check=True, capture_output=True, text=True)


def _package_control(field):
    return _dpkg_deb(["-f", str(PACKAGE), field]).stdout.strip()


def test_package_identity_and_stable_default_contract():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest["sha256"] == "BUILD_REQUIRED":
        assert not PACKAGE.exists()
        assert not SIDECAR.exists()
        pytest.skip("prebuild beta manifest")
    assert re.fullmatch(r"[0-9a-f]{64}", manifest["sha256"])
    assert _package_control("Version") == BETA_VERSION
    assert _package_control("Package") == "linuxremoteplayer"
    assert _package_control("Architecture") == "amd64"
    assert all(package in _package_control("Depends") for package in ("sudo", "curl", "ca-certificates"))
    listing = _dpkg_deb(["-c", str(PACKAGE)]).stdout
    assert not re.search(r"\./opt/linuxremoteplayer/backend/\.env\s", listing)
    assert "./opt/linuxremoteplayer/frontend/sw.js" in listing
    bootstrap_paths = {
        "./opt/linuxremoteplayer/scripts/debian/bootstrap.sh",
        "./opt/linuxremoteplayer/scripts/debian/platform-bootstrap.sh",
        "./opt/linuxremoteplayer/scripts/debian/session-bootstrap.sh",
        "./opt/linuxremoteplayer/scripts/debian/nvidia-bootstrap.sh",
        "./opt/linuxremoteplayer/scripts/debian/preflight.sh",
    }
    bootstrap_modes = {
        line.split()[-1]: line.split()[0]
        for line in listing.splitlines()
        if line.split() and line.split()[-1] in bootstrap_paths
    }
    assert bootstrap_modes == {path: "-rwxr-xr-x" for path in bootstrap_paths}
    with tempfile.TemporaryDirectory() as directory:
        _dpkg_deb(["-x", str(PACKAGE), directory])
        extracted = Path(directory) / "opt" / "linuxremoteplayer"
        assert (extracted / "VERSION").read_text(encoding="ascii").strip() == BETA_VERSION
        sw = (extracted / "frontend" / "sw.js").read_text(encoding="utf-8")
        assert "__LRP_VERSION__" not in sw
        assert f"lrp-{BETA_VERSION}" in sw
        control = Path(directory) / "control"
        _dpkg_deb(["--control", str(PACKAGE), str(control)])
        updater = (control / "postinst").read_text()
        assert 'https://www.linuxremoteplayer.com/latest.json' in updater
        assert 'https://www.linuxremoteplayer.com/beta/latest.json' in updater
        assert 'MANIFEST_URL="${UPDATE_MANIFEST_URL' not in updater
        assert not (extracted / "backend" / ".env").exists()
