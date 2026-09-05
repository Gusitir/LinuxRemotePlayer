import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "debian" / "session-bootstrap.sh"
def _find_bash():
    if os.name == "nt":
        candidate = Path("C:/Program Files/Git/bin/bash.exe")
        if candidate.exists():
            return str(candidate)
    return shutil.which("bash") or ("/bin/bash" if os.name != "nt" else str(candidate))


BASH = _find_bash()
PACKAGES = {
    "lightdm": "1.32.0-6+b2",
    "xserver-xorg": "1:7.7+24+deb13u1",
    "openbox": "3.6.1-12+b2",
    "dbus-x11": "1.16.2-2",
    "xauth": "1:1.1.2-1.1",
    "mesa-utils": "9.0.0-2+b2",
    "lightdm-gtk-greeter": "2.0.9-1",
}


def msys(path):
    text = str(path).replace("\\", "/")
    if os.name != "nt":
        return str(Path(path).resolve())
    drive, rest = text.split(":", 1)
    return "/" + drive.lower() + rest


class Fixture:
    def __init__(self, tmp_path):
        self.base = tmp_path
        self.root = tmp_path / "root"
        self.cmds = tmp_path / "cmds"
        self.log = tmp_path / "commands.log"
        for d in (
            "etc/apt/sources.list.d",
            "etc/lightdm/lightdm.conf.d",
            "usr/share/xsessions",
            "home/lrp",
            "sys/firmware/efi",
            "sys/bus/pci/devices/dev0",
            "proc",
        ):
            (self.root / d).mkdir(parents=True, exist_ok=True)
        self.cmds.mkdir()
        self.write(self.root / "etc/os-release", 'ID=debian\nVERSION_ID="13"\nVERSION_CODENAME=trixie\n')
        self.write(self.root / "etc/apt/sources.list.d/debian.sources",
                   "Types: deb\nURIs: http://deb.debian.org/debian\n"
                   "Suites: trixie\nComponents: main contrib non-free non-free-firmware\n"
                   "Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg\n")
        self.write(self.root / "sys/bus/pci/devices/dev0/vendor", "0x10de\n")
        self.write(self.root / "sys/bus/pci/devices/dev0/device", "0x2504\n")
        self.write(self.root / "sys/bus/pci/devices/dev0/driver", "nvidia\n")
        self.modules("nvidia 1 1 live\nnvidia_modeset 1 1 live\n"
                     "nvidia_drm 1 1 live\nnvidia_uvm 1 1 live\n")
        self.env = {
            "LRP_ARCH": "amd64",
            "LRP_KERNEL": "6.12.105-amd64",
            "LRP_SB": "disabled",
             "LRP_APT_RC": "0",
             "LRP_USER_RC": "0",
            "LRP_SYSTEMCTL_RC": "0",
            "LRP_SMI_RC": "0",
            "LRP_GLX": "OpenGL renderer string: NVIDIA GeForce RTX 3060/PCIe/SSE2",
            "LRP_KERNEL_VERSION": "6.12.105-1",
            "LRP_DISPLAY": ":0",
            "LRP_XAUTHORITY": "/home/lrp/.Xauthority",
        }
        self.stub("dpkg", '#!/bin/sh\n[ "$1" = --print-architecture ] && echo "$LRP_ARCH"\nexit 0\n')
        self.stub("dpkg-query", '#!/bin/sh\ncase "$3" in linux-image-*) printf "install ok installed\\t%s\\n" "$LRP_KERNEL_VERSION";; linux-headers-*) echo "$LRP_KERNEL_VERSION";; lightdm) echo "1.32.0-6+b2";; xserver-xorg) echo "1:7.7+24+deb13u1";; openbox) echo "3.6.1-12+b2";; dbus-x11) echo "1.16.2-2";; xauth) echo "1:1.1.2-1.1";; mesa-utils) echo "9.0.0-2+b2";; lightdm-gtk-greeter) echo "2.0.9-1";; esac\n')
        self.stub("apt-cache", '#!/bin/sh\necho "apt-cache-locale=$LC_ALL/$LANG" >> "$LRP_CMDLOG"\ncase "$2" in lightdm) v="1.32.0-6+b2";; xserver-xorg) v="1:7.7+24+deb13u1";; openbox) v="3.6.1-12+b2";; dbus-x11) v="1.16.2-2";; xauth) v="1:1.1.2-1.1";; mesa-utils) v="9.0.0-2+b2";; lightdm-gtk-greeter) v="2.0.9-1";; *) v="(none)";; esac\necho "  Candidate: $v"\n')
        self.stub("uname", '#!/bin/sh\n[ "$1" = -r ] && echo "$LRP_KERNEL"\n[ "$1" = -m ] && echo x86_64\n')
        self.stub("mokutil", '#!/bin/sh\necho "SecureBoot $LRP_SB"\n')
        self.stub("useradd", '#!/bin/sh\necho "useradd $*" >> "$LRP_CMDLOG"\nexit "$LRP_USER_RC"\n')
        self.stub("passwd", '#!/bin/sh\nexit 0\n')
        self.stub("id", '#!/bin/sh\nexit 1\n')
        self.stub("ps", '#!/bin/sh\nprintf "1 root Xorg\\n2 lrp openbox-session\\n"\n')
        self.stub("apt-get", '#!/bin/sh\necho "apt-get $* frontend=$DEBIAN_FRONTEND" >> "$LRP_CMDLOG"\nexit "$LRP_APT_RC"\n')
        self.stub("systemctl", '#!/bin/sh\necho "systemctl $*" >> "$LRP_CMDLOG"\nexit "$LRP_SYSTEMCTL_RC"\n')
        self.stub("nvidia-smi", '#!/bin/sh\nexit "$LRP_SMI_RC"\n')
        self.stub("glxinfo", '#!/bin/sh\necho "$LRP_GLX"\n')
        self.stub("lightdm", "#!/bin/sh\nexit 0\n")
        self.stub("Xorg", "#!/bin/sh\nexit 0\n")
        self.stub("openbox-session", "#!/bin/sh\nexit 0\n")
        self.stub("stat", '#!/bin/sh\ncase "$3" in */home/lrp|*/home/lrp/*) echo lrp;; *) echo root;; esac\n')
        self.stub("chmod", '#!/bin/sh\necho "chmod $*" >> "$LRP_CMDLOG"\nexit 0\n')
        self.stub("chown", '#!/bin/sh\necho "chown $*" >> "$LRP_CMDLOG"\nexit 0\n')

    def write(self, path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("ascii"))

    def stub(self, name, text):
        self.write(self.cmds / name, text)

    def modules(self, text):
        self.write(self.root / "proc/modules", text)

    def session_files(self):
        self.write(self.root / "etc/lightdm/lightdm.conf.d/50-linuxremoteplayer.conf", "[Seat:*]\nautologin-user=lrp\nuser-session=linuxremoteplayer\n")
        self.write(self.root / "usr/share/xsessions/linuxremoteplayer.desktop", "[Desktop Entry]\nExec=openbox-session\n")
        self.write(self.root / "home/lrp/.config/openbox/rc.xml", "<openbox_config></openbox_config>\n")
        self.write(self.root / "home/lrp/.config/openbox/autostart", "# LinuxRemotePlayer session marker\n")
        return self

    def env_for_run(self):
        env = dict(os.environ)
        env.update(self.env)
        env.update({
            "LRP_ROOT": msys(self.root),
            "LRP_COMMANDS": msys(self.cmds),
            "LRP_COMMANDS_ONLY": "1",
            "LRP_CMDLOG": msys(self.log),
            "PATH": msys(self.cmds) + ":" + env.get("PATH", ""),
        })
        return env

    def run(self, *args):
        return subprocess.run(
            [BASH, "-c", 'bash "$0" "$@"', msys(SCRIPT), *args],
            env=self.env_for_run(), capture_output=True, text=True,
        )

    def parsed(self, *args):
        proc = self.run(*args)
        if not proc.stdout:
            return proc, None
        return proc, json.loads(proc.stdout)

    def state(self):
        return self.root / "var/lib/linuxremoteplayer/session/state"

    def source(self):
        return self.root / "etc/apt/sources.list.d/debian.sources"

    def write_state(self, text):
        path = self.state()
        path.parent.mkdir(parents=True, exist_ok=True)
        self.write(path, text)


@pytest.fixture
def fx(tmp_path):
    return Fixture(tmp_path)


def test_default_read_only_and_approval(fx):
    before = fx.source().read_bytes()
    proc, body = fx.parsed()
    assert proc.returncode == 0
    assert body["mode"] == "plan"
    assert fx.source().read_bytes() == before
    assert not fx.state().exists()
    assert "apt-cache-locale=C/C" in fx.log.read_text()
    assert fx.parsed("--apply")[0].returncode == 12
    assert fx.source().read_bytes() == before


def test_apply_exact_packages_configs_and_no_auto_start(fx):
    proc, body = fx.parsed("--apply", "--approve")
    assert proc.returncode == 20
    assert body["state"]["phase"] == "reboot_required"
    source = fx.source().read_text()
    assert "Components: main contrib non-free non-free-firmware" in source
    assert (fx.root / "etc/lightdm/lightdm.conf.d/50-linuxremoteplayer.conf").read_text() == "[Seat:*]\ngreeter-session=lightdm-gtk-greeter\nautologin-user=lrp\nautologin-user-timeout=0\nuser-session=linuxremoteplayer\n"
    assert (fx.root / "usr/share/xsessions/linuxremoteplayer.desktop").is_file()
    autostart = (fx.root / "home/lrp/.config/openbox/autostart").read_text()
    assert autostart.strip() == "# LinuxRemotePlayer session marker"
    assert "xset" not in autostart and "xrandr" not in autostart
    log = fx.log.read_text().splitlines()
    assert "systemctl enable lightdm" in log
    assert f"chown lrp:lrp {msys(fx.root / 'home/lrp/.config/openbox/rc.xml')} {msys(fx.root / 'home/lrp/.config/openbox/autostart')}" in log
    assert not any("systemctl start" in line or "systemctl restart" in line for line in log)
    assert not any(line.startswith("reboot") for line in log)
    install = [line for line in log if line.startswith("apt-get install")]
    assert len(install) == 1
    assert all(f"{p}={v}" in install[0] for p, v in PACKAGES.items())
    assert "xinit" not in install[0] and "policykit-1" not in install[0]


def test_apply_idempotent_and_state_permissions(fx):
    first, _ = fx.parsed("--apply", "--approve")
    assert first.returncode == 20
    second, body = fx.parsed("--apply", "--approve")
    assert second.returncode == 20
    assert not (fx.root / "var/lib/linuxremoteplayer/session/sources.debian.bak").exists()
    assert body["state"]["phase"] == "reboot_required"
    calls = fx.log.read_text()
    assert "chmod 0600" in calls
    assert "chmod 0700" in calls


def test_resume_success_verifies_session_nvidia_and_renderer(fx):
    fx.session_files()
    fx.write_state("phase=reboot_required\nlayout=deb822\n")
    proc, body = fx.parsed("--resume")
    assert proc.returncode == 0
    assert body["state"]["phase"] == "complete"
    assert body["post_reboot"]["issues"] == []
    assert "renderer" not in json.dumps(body).lower()


def test_resume_rejects_llvmpipe_and_nouveau(fx):
    fx.session_files()
    fx.write_state("phase=reboot_required\nlayout=deb822\n")
    fx.env["LRP_GLX"] = "OpenGL renderer string: llvmpipe (LLVM 17.0.6, 256 bits)"
    fx.modules("nvidia 1 1 live\nnvidia_modeset 1 1 live\nnvidia_drm 1 1 live\nnvidia_uvm 1 1 live\nnouveau 1 0 live\n")
    proc, body = fx.parsed("--resume")
    assert proc.returncode == 21
    assert "nouveau_present" in body["post_reboot"]["issues"]


def test_preflight_fail_closed_and_state_recovery_tty(fx):
    fx.env["LRP_ARCH"] = "arm64"
    proc, body = fx.parsed("--apply", "--approve")
    assert proc.returncode == 11
    assert body["preflight"]["issues"]
    assert not fx.state().exists()
    assert "TTY" in body["recovery"]["tty"]


def test_source_and_package_sanitization(fx):
    secret = "TOP_SECRET_TOKEN"
    fx.write(fx.source(), "Types: deb\nURIs: http://user:" + secret + "@deb.debian.org/debian\nSuites: trixie\nComponents: main\nSigned-By: /key\n")
    proc = fx.run()
    assert secret not in proc.stdout and "user:" not in proc.stdout and "://" not in proc.stdout
    assert "policykit-1" not in SCRIPT.read_text()


def test_static_scope_and_write_set():
    source = SCRIPT.read_text()
    code = "\n".join(line for line in source.splitlines() if not line.lstrip().startswith("#"))
    for forbidden in ("systemctl start", "systemctl restart", "reboot ", "xset ", "xset:", "apt-get upgrade", "xinit"):
        assert forbidden not in code
    assert "autologin-user=lrp" in source
    assert "linuxremoteplayer" in source
    assert "policykit-1" not in source
    for relative in ("scripts/debian/session-bootstrap.sh",
                     "tests/test_session_bootstrap.py"):
        assert (ROOT / relative).is_file()
        assert subprocess.run(
            ["git", "ls-files", "--error-unmatch", relative], cwd=ROOT,
            capture_output=True, text=True).returncode == 0


def test_legacy_sources_are_supported_and_backup_extensions_ignored(fx):
    fx.source().unlink()
    fx.write(fx.root / "etc/apt/sources.list", "deb http://deb.debian.org/debian trixie main contrib\n"
             "deb http://deb.debian.org/debian-security trixie-security non-free non-free-firmware\n")
    fx.write(fx.root / "etc/apt/sources.list.d/vendor.list.bak", "deb http://evil.example trixie main\n")
    proc, body = fx.parsed()
    assert proc.returncode == 0
    assert body["sources"]["layout"] == "legacy"


def test_candidate_drift_is_before_any_mutation(fx):
    fx.stub("apt-cache", "#!/bin/sh\necho '  Candidate: wrong'\n")
    proc, body = fx.parsed("--apply", "--approve")
    assert proc.returncode == 11
    assert not fx.log.exists() or "apt-get" not in fx.log.read_text()
    assert not fx.state().exists()
    assert "candidate_drift" in body["preflight"]["issues"]


def test_existing_user_is_validated_and_repeat_apply_skips_useradd(fx):
    fx.stub("id", '#!/bin/sh\n[ "$1" = -u ] && { echo 1001; exit 0; }; [ "$1" = -nG ] && { echo "lrp video"; exit 0; }; exit 1\n')
    fx.stub("getent", '#!/bin/sh\necho "lrp:x:1001:1001::/home/lrp:/bin/bash"\n')
    fx.stub("passwd", '#!/bin/sh\n[ "$1" = -S ] && echo "lrp L 01/01/1970 0 99999 7 -1"\n')
    first, _ = fx.parsed("--apply", "--approve")
    second, _ = fx.parsed("--apply", "--approve")
    assert first.returncode == second.returncode == 20
    assert "useradd" not in fx.log.read_text()


def test_lightdm_mask_install_unmask_enable_order(fx):
    proc, _ = fx.parsed("--apply", "--approve")
    assert proc.returncode == 20
    calls = fx.log.read_text().splitlines()
    mask = calls.index("systemctl mask lightdm")
    install = next(i for i, line in enumerate(calls) if line.startswith("apt-get install"))
    unmask = calls.index("systemctl unmask lightdm")
    enable = calls.index("systemctl enable lightdm")
    assert mask < install < unmask < enable
    assert "frontend=noninteractive" in calls[install]
    assert not any(" start " in line or " restart " in line or line.startswith("reboot") for line in calls)


def test_resume_rejects_llvmpipe_without_leaking_renderer_text(fx):
    fx.session_files()
    fx.write_state("phase=reboot_required\n")
    fx.env["LRP_GLX"] = "OpenGL renderer string: llvmpipe (LLVM)"
    proc, body = fx.parsed("--resume")
    assert proc.returncode == 21
    assert "llvmpipe_renderer" in body["post_reboot"]["issues"]
    assert "OpenGL renderer string" not in json.dumps(body)


def test_every_deb822_stanza_is_required_to_be_complete(fx):
    fx.write(fx.source(), "Types: deb\nURIs: http://deb.debian.org/debian\nSuites: trixie\n"
             "Components: main contrib non-free non-free-firmware\n"
             "Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg\n\n"
             "Types: deb\nURIs: http://deb.debian.org/debian-security\nSuites: trixie-security\n"
             "Components: main\n")
    proc, body = fx.parsed()
    assert proc.returncode == 11
    assert "sources" in body["preflight"]["issues"]


def test_apply_writes_valid_openbox_34_xml(fx):
    proc, _ = fx.parsed("--apply", "--approve")
    assert proc.returncode == 20
    xml = (fx.root / "home/lrp/.config/openbox/rc.xml").read_text()
    assert xml == '<openbox_config xmlns="http://openbox.org/3.4"></openbox_config>\n'


def test_apply_configures_tv_cursor_and_scaling_environment(fx):
    proc, _ = fx.parsed("--apply", "--approve")
    assert proc.returncode == 20
    xresources = (fx.root / "home/lrp/.Xresources").read_text()
    assert "Xcursor.size: 48" in xresources
    assert "Xcursor.theme: DMZ-White" in xresources
    index_theme = (fx.root / "home/lrp/.icons/default/index.theme").read_text()
    assert "Inherits=DMZ-White" in index_theme
    env_script = (fx.root / "home/lrp/.config/openbox/environment").read_text()
    assert 'export XCURSOR_THEME="DMZ-White"' in env_script
    assert "export XCURSOR_SIZE=48" in env_script
    assert "export XCURSOR_SIZE=96" in env_script
    assert "xrdb -merge" in env_script

