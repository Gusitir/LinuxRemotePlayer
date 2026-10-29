from pathlib import Path


ROOT = Path(__file__).parents[1]
BUILD = ROOT / "scripts" / "build_deb.sh"
SERVICE_WORKER = ROOT / "frontend" / "sw.js"


def test_debian_release_source_contract():
    source = BUILD.read_text(encoding="utf-8")
    assert (ROOT / "VERSION").read_text(encoding="ascii").strip() == "1.0.0"
    assert "Architecture: amd64" in source
    assert "chmod 0755 pkg/opt/linuxremoteplayer/scripts/debian/*.sh" in source
    assert "/opt/linuxremoteplayer/scripts/debian/bootstrap.sh --resume --unattended" in source
    assert "sudo /opt/linuxremoteplayer/scripts/debian/bootstrap.sh --apply --approve" in source
    assert "exec ./install.sh" not in source
    assert "linuxremoteplayer_${VERSION}_amd64.deb" in source
    assert "linuxremoteplayer_${VERSION}_amd64.deb.sha256" in source
    assert "firefox-esr | firefox" not in source
    assert "Recommends: firefox-esr," in source
    assert "Depends: python3, python3-venv, python3-dev, build-essential, openssl, sudo, curl, ca-certificates, python3-cryptography" in source
    assert "avahi-daemon" not in source
    assert "modprobe uinput" not in source
    assert "99-linuxremoteplayer-uinput.rules" not in source
    assert "systemd-run --unit=\"linuxremoteplayer-bootstrap-ota-$$\"" in source
    assert "--resume --unattended" in source
    assert 'if [ "$1" = "remove" ]; then' in source


def test_service_worker_source_remains_unstamped():
    assert "__LRP_VERSION__" in SERVICE_WORKER.read_text(encoding="utf-8")
