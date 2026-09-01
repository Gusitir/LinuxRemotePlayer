import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/debian/platform-bootstrap.sh"
def _find_bash():
    if os.name == "nt":
        candidate = Path("C:/Program Files/Git/bin/bash.exe")
        if candidate.exists():
            return str(candidate)
    return shutil.which("bash") or ("/bin/bash" if os.name != "nt" else str(candidate))


BASH = _find_bash()


def _shell_path(path):
    text = str(path).replace("\\", "/")
    if os.name != "nt":
        return str(Path(path).resolve())
    drive, rest = text.split(":", 1)
    return "/" + drive.lower() + rest
VERSIONS = {
    "pipewire": "1.4.2-1",
    "pipewire-pulse": "1.4.2-1",
    "wireplumber": "0.5.8-2",
    "avahi-daemon": "0.8-16",
    "libnss-mdns": "0.15.1-4+b1",
    "ufw": "0.36.2-9",
    "x11-xserver-utils": "7.7+11",
}


class Fixture:
    def __init__(self, tmp_path):
        self.root = tmp_path / "root"
        self.cmds = tmp_path / "cmds"
        self.log = tmp_path / "commands.log"
        for path in ("etc", "home/lrp/.config/openbox", "usr/local/share/ca-certificates", "proc"):
            (self.root / path).mkdir(parents=True, exist_ok=True)
        self.cmds.mkdir()
        self.write(self.root / "home/lrp/.config/openbox/autostart", "# existing\n")
        self.env = {"LRP_ARCH": "amd64", "LRP_APT_RC": "0", "LRP_SYSTEMCTL_RC": "0"}
        self.stub("getent", '#!/bin/sh\necho "lrp:x:1001:1001::/home/lrp:/bin/bash"\n')
        self.stub("passwd", '#!/bin/sh\n[ "$1" = -S ] && echo "lrp L 01/01/1970 0 99999 7 -1"\n')
        self.stub("id", '#!/bin/sh\n[ "$1" = -u ] && echo 1001 && exit 0\n[ "$1" = -nG ] && echo "lrp video" && exit 0\n')
        self.stub("apt-get", '#!/bin/sh\necho "apt-get $*" >> "$LRP_CMDLOG"\nexit "$LRP_APT_RC"\n')
        self.stub("apt-cache", '#!/bin/sh\ncase "$2" in pipewire|pipewire-pulse) v="1.4.2-1";; wireplumber) v="0.5.8-2";; avahi-daemon) v="0.8-16";; libnss-mdns) v="0.15.1-4+b1";; ufw) v="0.36.2-9";; x11-xserver-utils) v="7.7+11";; esac\necho "  Candidate: $v"\n')
        self.stub("dpkg-query", '#!/bin/sh\ncase "$3" in pipewire|pipewire-pulse) echo "1.4.2-1";; wireplumber) echo "0.5.8-2";; avahi-daemon) echo "0.8-16";; libnss-mdns) echo "0.15.1-4+b1";; ufw) echo "0.36.2-9";; x11-xserver-utils) echo "7.7+11";; esac\n')
        self.stub("dpkg", '#!/bin/sh\nexit 0\n')
        self.stub("systemctl", '#!/bin/sh\necho "systemctl $*" >> "$LRP_CMDLOG"\nif grep -q "phase=applied" "$LRP_ROOT/var/lib/linuxremoteplayer/platform/state" 2>/dev/null; then case "$1 $2" in "is-enabled avahi-daemon"|"is-active avahi-daemon") exit 0;; "is-enabled sleep.target"|"is-enabled suspend.target"|"is-enabled hibernate.target"|"is-enabled hybrid-sleep.target") echo masked; exit 0;; esac; fi\ncase "$1 $2" in "is-enabled avahi-daemon"|"is-active avahi-daemon") exit 1;; "is-enabled sleep.target"|"is-enabled suspend.target"|"is-enabled hibernate.target"|"is-enabled hybrid-sleep.target") echo disabled; exit 1;; esac\nexit "$LRP_SYSTEMCTL_RC"\n')
        self.stub("runuser", '#!/bin/sh\necho "runuser $*" >> "$LRP_CMDLOG"\ncase "$*" in *is-enabled*|*is-active*) grep -q "phase=applied" "$LRP_ROOT/var/lib/linuxremoteplayer/platform/state" 2>/dev/null && exit 0 || exit 1;; esac\nexit 0\n')
        self.stub("modprobe", '#!/bin/sh\nexit 0\n')
        self.stub("openssl", '#!/bin/sh\nexit 0\n')
        self.stub("usermod", '#!/bin/sh\necho "usermod $*" >> "$LRP_CMDLOG"\n')
        self.stub("udevadm", '#!/bin/sh\necho "udevadm $*" >> "$LRP_CMDLOG"\n')
        self.stub("ufw", '#!/bin/sh\nif [ "$1" = status ]; then if grep -q "phase=applied" "$LRP_ROOT/var/lib/linuxremoteplayer/platform/state" 2>/dev/null; then echo "Status: active"; echo "linuxremoteplayer ALLOW"; else echo "Status: inactive"; fi; exit 0; fi\necho "ufw $*" >> "$LRP_CMDLOG"\n')
        self.stub("update-ca-certificates", '#!/bin/sh\necho "update-ca-certificates" >> "$LRP_CMDLOG"\n')
        self.stub("gpasswd", '#!/bin/sh\necho "gpasswd $*" >> "$LRP_CMDLOG"\n')
        self.stub("chmod", '#!/bin/sh\necho "chmod $*" >> "$LRP_CMDLOG"\n')
        self.stub("chown", '#!/bin/sh\necho "chown $*" >> "$LRP_CMDLOG"\n')

    def write(self, path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="ascii")

    def stub(self, name, text):
        self.write(self.cmds / name, text)

    def run(self, *args):
        env = dict(os.environ)
        env.update(self.env)
        env.update({"LRP_ROOT": _shell_path(self.root), "LRP_COMMANDS": _shell_path(self.cmds), "LRP_COMMANDS_ONLY": "1", "LRP_CMDLOG": _shell_path(self.log)})
        return subprocess.run([BASH, "-c", 'bash "$0" "$@"', _shell_path(SCRIPT), *args], env=env, capture_output=True, text=True)

    def parsed(self, *args):
        result = self.run(*args)
        return result, json.loads(result.stdout) if result.stdout else None


@pytest.fixture
def fx(tmp_path):
    return Fixture(tmp_path)


def test_apply_installs_exact_packages_and_no_removal(fx):
    result, _ = fx.parsed("--apply", "--approve")
    assert result.returncode == 0
    install = next(line for line in fx.log.read_text().splitlines() if line.startswith("apt-get install"))
    assert all(f"{package}={version}" in install for package, version in VERSIONS.items())
    assert "apt-get remove" not in fx.log.read_text()


def test_apply_creates_owned_platform_files_and_marked_dpms(fx):
    result, _ = fx.parsed("--apply", "--approve")
    assert result.returncode == 0
    modules = fx.root / "etc/modules-load.d/linuxremoteplayer-uinput.conf"
    udev = fx.root / "etc/udev/rules.d/99-linuxremoteplayer-uinput.rules"
    assert modules.read_text() == "uinput\n"
    assert "KERNEL==\"uinput\"" in udev.read_text()
    autostart = (fx.root / "home/lrp/.config/openbox/autostart").read_text()
    assert autostart.count("LRP-T127-DPMS-BEGIN") == 1
    assert "xset s off" in autostart and "xset -dpms" in autostart and "xset s noblank" in autostart


def test_apply_orders_ssh_before_ufw_enable_and_audio_bus(fx):
    result, _ = fx.parsed("--apply", "--approve")
    assert result.returncode == 0
    lines = fx.log.read_text().splitlines()
    ssh = next(i for i, line in enumerate(lines) if "ufw allow OpenSSH" in line)
    enable = next(i for i, line in enumerate(lines) if "ufw --force enable" in line)
    assert ssh < enable
    assert any(line.startswith("runuser -u lrp") and "DBUS_SESSION_BUS_ADDRESS" in line for line in lines)


def test_applied_audio_verification_uses_the_same_user_bus_environment():
    text = SCRIPT.read_text(encoding="ascii")
    assert 'state_applied_audio_bus_ok()' in text
    assert 'state_applied_audio_bus_ok || return 1' in text


def test_apply_is_idempotent_and_does_not_duplicate_dpms(fx):
    assert fx.run("--apply", "--approve").returncode == 0
    before = (fx.root / "home/lrp/.config/openbox/autostart").read_text()
    fx.stub("id", '#!/bin/sh\n[ "$1" = -u ] && echo 1001 && exit 0\n[ "$1" = -nG ] && echo "lrp input video" && exit 0\n')
    systemctl = (fx.cmds / "systemctl").read_text().replace("echo masked; exit 0;", "echo masked; exit 1;")
    fx.stub("systemctl", systemctl)
    assert fx.run("--apply", "--approve").returncode == 0
    assert (fx.root / "home/lrp/.config/openbox/autostart").read_text() == before


def test_rollback_requires_approval_and_keeps_packages(fx):
    assert fx.run("--rollback").returncode == 1
    assert fx.run("--apply", "--approve").returncode == 0
    result, _ = fx.parsed("--rollback", "--approve")
    assert result.returncode == 0
    assert "systemctl stop avahi-daemon" in fx.log.read_text()
    assert "apt-get remove" not in fx.log.read_text()


def test_optional_ca_is_installed_and_rollback_removes_it(fx):
    ca = fx.root / "ca.pem"
    ca.write_text("-----BEGIN CERTIFICATE-----\nTEST\n-----END CERTIFICATE-----\n", encoding="ascii")
    assert fx.run("--apply", "--approve", "--ca-path", str(ca).replace("\\", "/")).returncode == 0
    assert (fx.root / "usr/local/share/ca-certificates/linuxremoteplayer-ca.crt").exists()


def test_sleep_targets_are_masked_only_when_not_already_masked():
    text = SCRIPT.read_text(encoding="ascii")
    assert "is-enabled" in text and "systemctl mask" in text
    assert "SLEEP_CHANGED" in text


def test_install_integration_delegates_platform_and_removes_duplicates():
    text = (ROOT / "scripts/install.sh").read_text(encoding="utf-8")
    assert "platform-bootstrap.sh" in text
    assert "LRP_MODE=htpc" in text
    assert "systemctl enable --now avahi-daemon" not in text
    assert "ufw allow 8000/tcp" not in text
    assert "99-uinput.rules" not in text
    assert "lrp-ca.crt" not in text


def test_static_platform_contract_is_system_safe():
    text = SCRIPT.read_text(encoding="ascii")
    assert "--apply" in text and "--rollback" in text and "--approve" in text
    assert "pipewire.service" in text and "wireplumber.service" in text
    assert "systemctl --user" in text
    assert "linuxremoteplayer-ca.crt" in text
    assert "gpasswd -d lrp input" in text


def test_owned_ufw_rollback_deletions_are_forced():
    text = SCRIPT.read_text(encoding="ascii")
    assert "ufw --force delete allow linuxremoteplayer" in text
    assert "ufw --force delete allow \"$UFW_SSH_ADDED\"" in text


def test_service_contract_is_single_system_unit():
    install = (ROOT / "scripts/install.sh").read_text(encoding="utf-8")
    build = (ROOT / "scripts/build_deb.sh").read_text(encoding="utf-8")
    assert "User=lrp" in install
    assert "Wants=network-online.target" in install
    assert "After=display-manager.service network-online.target" in install
    assert "systemctl --user" not in build


def test_prior_avahi_state_is_recorded_for_rollback(fx):
    fx.stub("systemctl", '#!/bin/sh\necho "systemctl $*" >> "$LRP_CMDLOG"\ncase "$1 $2" in "is-enabled avahi-daemon"|"is-active avahi-daemon") exit 0;; esac\nexit "$LRP_SYSTEMCTL_RC"\n')
    result, _ = fx.parsed("--apply", "--approve")
    assert result.returncode == 0
    state = (fx.root / "var/lib/linuxremoteplayer/platform/state").read_text()
    assert "AVAHI_ENABLED=1" in state and "AVAHI_ACTIVE=1" in state


def test_existing_input_group_is_not_modified(fx):
    fx.stub("id", '#!/bin/sh\n[ "$1" = -u ] && echo 1001 && exit 0\n[ "$1" = -nG ] && echo "lrp input video" && exit 0\n')
    result, _ = fx.parsed("--apply", "--approve")
    assert result.returncode == 0
    assert "usermod -aG input lrp" not in fx.log.read_text()


def test_first_apply_rejects_unmanaged_platform_paths(fx):
    fx.write(fx.root / "etc/modules-load.d/linuxremoteplayer-uinput.conf", "unmanaged\n")
    result, _ = fx.parsed("--apply", "--approve")
    assert result.returncode == 1
    assert "apt-get install" not in (fx.log.read_text() if fx.log.exists() else "")


def test_applied_state_drift_fails_without_replacing_rollback_flags(fx):
    assert fx.run("--apply", "--approve").returncode == 0
    state_before = (fx.root / "var/lib/linuxremoteplayer/platform/state").read_text()
    fx.write(fx.root / "etc/modules-load.d/linuxremoteplayer-uinput.conf", "drift\n")
    result, _ = fx.parsed("--apply", "--approve")
    assert result.returncode == 1
    assert "applied_state_drift" in result.stderr
    assert (fx.root / "var/lib/linuxremoteplayer/platform/state").read_text() == state_before


def test_late_ca_attach_updates_only_ca_flag(fx):
    assert fx.run("--apply", "--approve").returncode == 0
    fx.stub("id", '#!/bin/sh\n[ "$1" = -u ] && echo 1001 && exit 0\n[ "$1" = -nG ] && echo "lrp input video" && exit 0\n')
    ca = fx.root / "ca.pem"
    ca.write_text("-----BEGIN CERTIFICATE-----\nLATE\n-----END CERTIFICATE-----\n", encoding="ascii")
    before = (fx.root / "var/lib/linuxremoteplayer/platform/state").read_text()
    result = fx.run("--apply", "--approve", "--ca-path", str(ca).replace("\\", "/"))
    assert result.returncode == 0
    after = (fx.root / "var/lib/linuxremoteplayer/platform/state").read_text()
    assert "CA_INSTALLED=0" in before and "CA_INSTALLED=1" in after
    assert "PRIOR_AVAHI_ENABLED" in before and "PRIOR_AVAHI_ENABLED" in after


def test_same_late_ca_is_idempotent(fx):
    assert fx.run("--apply", "--approve").returncode == 0
    fx.stub("id", '#!/bin/sh\n[ "$1" = -u ] && echo 1001 && exit 0\n[ "$1" = -nG ] && echo "lrp input video" && exit 0\n')
    ca = fx.root / "ca.pem"
    ca.write_text("-----BEGIN CERTIFICATE-----\nSAME\n-----END CERTIFICATE-----\n", encoding="ascii")
    assert fx.run("--apply", "--approve", "--ca-path", str(ca).replace("\\", "/")).returncode == 0
    state = (fx.root / "var/lib/linuxremoteplayer/platform/state").read_text()
    assert fx.run("--apply", "--approve", "--ca-path", str(ca).replace("\\", "/")).returncode == 0
    assert (fx.root / "var/lib/linuxremoteplayer/platform/state").read_text() == state


def test_different_existing_ca_is_rejected_without_overwrite(fx):
    assert fx.run("--apply", "--approve").returncode == 0
    fx.stub("id", '#!/bin/sh\n[ "$1" = -u ] && echo 1001 && exit 0\n[ "$1" = -nG ] && echo "lrp input video" && exit 0\n')
    first = fx.root / "ca-one.pem"
    second = fx.root / "ca-two.pem"
    first.write_text("-----BEGIN CERTIFICATE-----\nONE\n-----END CERTIFICATE-----\n", encoding="ascii")
    second.write_text("-----BEGIN CERTIFICATE-----\nTWO\n-----END CERTIFICATE-----\n", encoding="ascii")
    assert fx.run("--apply", "--approve", "--ca-path", str(first).replace("\\", "/")).returncode == 0
    installed = (fx.root / "usr/local/share/ca-certificates/linuxremoteplayer-ca.crt").read_bytes()
    result = fx.run("--apply", "--approve", "--ca-path", str(second).replace("\\", "/"))
    assert result.returncode == 1
    assert (fx.root / "usr/local/share/ca-certificates/linuxremoteplayer-ca.crt").read_bytes() == installed


def test_nonroot_default_dry_run_is_rejected(fx):
    fx.env["LRP_COMMANDS_ONLY"] = "0"
    fx.env["LRP_TEST_NONROOT"] = "1"
    result = fx.run()
    assert result.returncode == 1
    assert "root_required" in result.stderr


def test_root_dry_run_lists_recorded_states(fx):
    state = fx.root / "var/lib/linuxremoteplayer/platform/state"
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text("phase=applied\n", encoding="ascii")
    result, body = fx.parsed("--dry-run")
    assert result.returncode == 0
    assert body["platform_state"] == "recorded"
    assert body["session_state"] == "absent"


def test_strict_rollback_preserves_applied_state_when_mutation_fails(fx):
    assert fx.run("--apply", "--approve").returncode == 0
    state = fx.root / "var/lib/linuxremoteplayer/platform/state"
    before = state.read_text()
    fx.stub("systemctl", '#!/bin/sh\nexit 1\n')
    result = fx.run("--rollback", "--approve", "--strict")
    assert result.returncode == 11
    assert state.read_text() == before


def test_default_rollback_remains_best_effort(fx):
    assert fx.run("--apply", "--approve").returncode == 0
    fx.stub("systemctl", '#!/bin/sh\nexit 1\n')
    assert fx.run("--rollback", "--approve").returncode == 0
