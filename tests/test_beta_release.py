import hashlib
import json
import re
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).parents[1]
VERSION = "1.99.1"
PACKAGE = ROOT / "website" / "beta" / "downloads" / f"linuxremoteplayer_{VERSION}_all.deb"
SIDECAR = PACKAGE.with_name(PACKAGE.name + ".sha256")
MANIFEST = ROOT / "website" / "beta" / "latest.json"


def test_release_metadata_and_template_are_beta_only():
    assert (ROOT / "VERSION").read_text(encoding="ascii").strip() == VERSION
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert changelog.startswith("# Changelog")
    top_entry = changelog.split("## [1.9.1]", 1)[0]
    assert re.search(r"## \[1\.99\.1\] - 2026-08-22\n\n### Added\n- .*Canal beta opt-in", top_entry)
    assert not re.search(r"STT|Needle|IA local|AI local|capacidad|capability", top_entry, re.I)

    template = json.loads((ROOT / "website" / "beta" / "latest.template.json").read_text())
    assert template["version"] == "__BETA_VERSION__"
    assert template["deb_url"] == (
        "https://www.linuxremoteplayer.com/beta/downloads/__BETA_DEB_FILENAME__"
    )
    assert template["sha256"] == "__BETA_SHA256__"


def test_live_beta_artifact_sidecar_and_manifest_cohere():
    assert PACKAGE.is_file()
    assert SIDECAR.is_file()
    assert MANIFEST.is_file()
    digest = hashlib.sha256(PACKAGE.read_bytes()).hexdigest()
    sidecar = SIDECAR.read_text(encoding="ascii").split()
    assert sidecar == [digest, PACKAGE.name]

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["version"] == VERSION
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
    assert _package_control("Version") == VERSION
    assert _package_control("Package") == "linuxremoteplayer"
    listing = _dpkg_deb(["-c", str(PACKAGE)]).stdout
    assert not re.search(r"\./opt/linuxremoteplayer/backend/\.env\s", listing)
    assert "./opt/linuxremoteplayer/frontend/sw.js" in listing

    with tempfile.TemporaryDirectory() as directory:
        _dpkg_deb(["-x", str(PACKAGE), directory])
        extracted = Path(directory) / "opt" / "linuxremoteplayer"
        assert (extracted / "VERSION").read_text(encoding="ascii").strip() == VERSION
        sw = (extracted / "frontend" / "sw.js").read_text(encoding="utf-8")
        assert "__LRP_VERSION__" not in sw
        assert f"lrp-{VERSION}" in sw
        control = Path(directory) / "control"
        _dpkg_deb(["--control", str(PACKAGE), str(control)])
        updater = (control / "postinst").read_text()
        assert 'https://www.linuxremoteplayer.com/latest.json' in updater
        assert 'https://www.linuxremoteplayer.com/beta/latest.json' in updater
        assert 'MANIFEST_URL="${UPDATE_MANIFEST_URL' not in updater
        assert not (extracted / "backend" / ".env").exists()
