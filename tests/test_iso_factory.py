import os
import shutil
import subprocess
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
ISO_DIR = ROOT / "scripts" / "debian" / "iso"
BUILD_ISO = ISO_DIR / "build_iso.sh"
INSTALLER_TARGET = ISO_DIR / "installer" / "lrp-install-target.sh"
PRESEED = ISO_DIR / "preseed.cfg"
ZRAM_CONF = ISO_DIR / "config" / "zram-generator.conf"
HOOK_SETUP = ISO_DIR / "hooks" / "99-lrp-setup.chroot"
GRUB_CFG = ISO_DIR / "config" / "grub.cfg"
ISOLINUX_CFG = ISO_DIR / "config" / "isolinux.cfg"
PKG_LIST = ISO_DIR / "package-lists" / "lrp-appliance.list.chroot"


def _find_bash():
    if os.name == "nt":
        candidate = Path("C:/Program Files/Git/bin/bash.exe")
        if candidate.exists():
            return str(candidate)
    found = shutil.which("bash")
    if found and "wsl" not in found.lower():
        return found
    return "bash"


BASH = _find_bash()


def test_build_iso_script_contracts():
    assert BUILD_ISO.is_file(), "build_iso.sh must exist"
    content = BUILD_ISO.read_text(encoding="utf-8")
    assert b"\r" not in BUILD_ISO.read_bytes(), "build_iso.sh must use LF line endings"

    # Contract checks
    assert "--binary-images iso-hybrid" in content
    assert "--architectures amd64" in content
    assert "--distribution trixie" in content
    assert "--debian-installer live" in content
    assert "/mnt/*" in content, "Must detect /mnt/* to reject WSL/9p mounts"
    assert "--dry-run" in content
    assert "--deb" in content
    assert "--output" in content
    assert "--workdir" in content
    assert "sha256sum" in content, "Must generate .sha256 sidecar"
    assert "99-lrp-setup.chroot" in content
    assert "lrp-install-target.sh" in content
    assert "zram-generator.conf" in content
    assert "preseed.cfg" in content


def test_build_iso_rejection_of_mnt_path():
    content = BUILD_ISO.read_text(encoding="utf-8")
    # Verify the check logic explicitly forbids /mnt/* when DRY_RUN=0
    assert '[[ "$CHECK_DIR" == /mnt/* ]] && [ "$DRY_RUN" -eq 0 ]' in content


def test_build_iso_dry_run_execution():
    if not shutil.which(BASH) and not Path(BASH).exists():
        pytest.skip("Bash executable not available")
    res = subprocess.run([BASH, str(BUILD_ISO), "--dry-run"], capture_output=True, text=True)
    assert res.returncode == 0, f"Dry-run failed: {res.stderr}"
    assert "[LRP-ISO] MODO DRY-RUN" in res.stdout
    assert "trixie amd64" in res.stdout
    assert "DRY-RUN exitoso" in res.stdout


def test_fail_closed_usb_exclusion_installer():
    target_sh = INSTALLER_TARGET.read_text(encoding="utf-8")
    # Must check mountpoints
    assert "/run/live/medium" in target_sh
    assert "/cdrom" in target_sh
    assert "/live/image" in target_sh
    # Must check USB transport
    assert 'TRAN="usb"' in target_sh or 'TRAN:-}' in target_sh or '"$TRAN" = "usb"' in target_sh or '[ "${TRAN:-}" = "usb" ]' in target_sh
    assert "MEDIO_LIVE_ACTIVO" in target_sh
    assert "TRANSPORTE_USB" in target_sh


def test_fail_closed_usb_exclusion_preseed():
    preseed = PRESEED.read_text(encoding="utf-8")
    assert "/run/live/medium" in preseed
    assert "/cdrom" in preseed
    assert "/live/image" in preseed
    assert "ID_BUS=usb" in preseed
    assert "partman-auto/disk" in preseed
    assert "partman/early_command" in preseed


def test_zram_and_offline_boot_configs():
    zram = ZRAM_CONF.read_text(encoding="utf-8")
    assert "[zram0]" in zram
    assert "compression-algorithm = zstd" in zram
    assert "swap-priority = 100" in zram

    hook = HOOK_SETUP.read_text(encoding="utf-8")
    assert "autologin-user=lrp" in hook
    assert "user-session=openbox" in hook
    assert "linuxremoteplayer.service" in hook
    assert "zram-generator.conf" in hook


def test_iso_bash_syntax_checks():
    if not shutil.which(BASH) and not Path(BASH).exists():
        pytest.skip("Bash executable not available")
    scripts = [BUILD_ISO, INSTALLER_TARGET, HOOK_SETUP]
    for script in scripts:
        res = subprocess.run([BASH, "-n", str(script)], capture_output=True, text=True)
        assert res.returncode == 0, f"Syntax error in {script}: {res.stderr}"
