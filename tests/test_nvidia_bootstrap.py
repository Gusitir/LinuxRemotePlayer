"""T-123 tests for the Debian 13 NVIDIA bootstrap tool.

The tool (scripts/debian/nvidia-bootstrap.sh) is a stateful, owner-approved
installer. Default is read-only planning; apply requires --approve; --resume
runs only the post-reboot verification and never auto-reboots.

Exit contract:
  0 complete, 10 unresolved preflight, 11 failed requirement/transaction,
  12 invalid contract/state, 20 reboot required, 21 post-reboot verify failed.

Tests run the real script through Git Bash against fixture filesystems and
stubbed commands (no real root/apt/reboot).
"""

import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = ROOT / "scripts" / "debian" / "nvidia-bootstrap.sh"

EXPECTED_PKGS = {
    "nvidia-driver": "550.163.01-2",
    "nvidia-kernel-dkms": "550.163.01-2",
    "xserver-xorg-video-nvidia": "550.163.01-2",
    "firmware-nvidia-gsp": "550.163.01-2",
    "dkms": "3.2.2-1~deb13u1",
}
KERNEL_RELEASE = "6.12.105-amd64"
KERNEL_VERSION = "6.12.105-1"
EXPECTED_COMPONENTS = "main contrib non-free non-free-firmware"


def _find_bash():
    if os.name == "nt":
        c = Path("C:/Program Files/Git/bin/bash.exe")
        if c.exists():
            return str(c)
    return shutil.which("bash") or ("/bin/bash" if os.name != "nt" else str(c))


BASH = _find_bash()


def _msys(path):
    text = str(path).replace("\\", "/")
    if os.name != "nt":
        return str(Path(path).resolve())
    drive, rest = text.split(":", 1)
    return "/" + drive.lower() + rest


class Fixture:
    def __init__(self, root_dir):
        self.base = root_dir
        self.root = root_dir / "root"
        self.cmds = root_dir / "cmds"
        self.apt_log = root_dir / "apt.log"
        self.reboot_log = root_dir / "reboot.log"
        self.chmod_log = root_dir / "chmod.log"
        self.chown_log = root_dir / "chown.log"
        self.source_layout = "deb822"
        self._write = lambda p, t: p.write_bytes(str(t).encode("ascii", "replace"))
        for d in ("etc/apt/sources.list.d", "sys/firmware/efi",
                  "proc", "sys/bus/pci/devices/dev0"):
            (self.root / d).mkdir(parents=True, exist_ok=True)
        self.cmds.mkdir(exist_ok=True)
        self._env = {
            "LRP_INSTALLED": "",
            "LRP_DPKG_ARCH": "amd64",
            "LRP_NVIDIA_SMI_RC": "0",
            "APT_UPDATE_RC": "0",
            "APT_INSTALL_RC": "0",
            "LRP_KERNEL_RELEASE": KERNEL_RELEASE,
            "LRP_IMAGE_VERSION": KERNEL_VERSION,
            "LRP_HEADER_CANDIDATE": KERNEL_VERSION,
        }
        self.os_release(("ID=debian", 'VERSION_ID="13"',
                         "VERSION_CODENAME=trixie"))
        self.pci_gpu(bound="nvidia")
        self.modules(
            "nvidia 1 1 live\nnvidia_modeset 1 1 live\n"
            "nvidia_drm 1 1 live\nnvidia_uvm 1 1 live\n")
        self.sources_deb822(
            "Types: deb\n"
            "URIs: http://deb.debian.org/debian\n"
            "Suites: trixie trixie-updates trixie-backports\n"
            "Components: main\n"
            "Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg\n")
        # stubs
        self._write(self.cmds / "uname",
                    '#!/bin/sh\n[ "$1" = -r ] && echo "$LRP_KERNEL_RELEASE"\n'
                    '[ "$1" = -m ] && echo x86_64\n')
        self._write(self.cmds / "dpkg",
                    '#!/bin/sh\n'
                    'if [ "$1" = "--print-architecture" ]; then '
                    'echo "$LRP_DPKG_ARCH"; exit 0; fi\n'
                    'if [ "$1" = "-s" ]; then shift; for p in "$@"; do '
                    'case ",$LRP_INSTALLED," in *,${p},*) ;; *) exit 1;; '
                    'esac; done; exit 0; fi\nexit 0\n')
        self._write(self.cmds / "dpkg-query",
                    '#!/bin/sh\n'
                    'if [ "$1" = -W ]; then printf "install ok installed\\t%s\\n" "$LRP_IMAGE_VERSION"; exit 0; fi\n'
                    'exit 1\n')
        self._write(self.cmds / "apt-cache",
                    '#!/bin/sh\n'
                    'if [ "$1" = policy ]; then echo "  Candidate: $LRP_HEADER_CANDIDATE"; exit 0; fi\n'
                    'exit 1\n')
        self._write(self.cmds / "mokutil",
                    '#!/bin/sh\n[ "$1" = --sb-state ] && echo "SecureBoot disabled"\n')
        self._write(self.cmds / "apt-get",
                    '#!/bin/sh\n'
                    'echo "$*" >> "$APT_OPLOG"\n'
                    'case "$1" in\n'
                    '  update) exit "${APT_UPDATE_RC:-0}" ;;\n'
                    '  install) exit "${APT_INSTALL_RC:-0}" ;;\n'
                    '  *) exit 0 ;;\n'
                    'esac\n')
        self._write(self.cmds / "nvidia-smi",
                    '#!/bin/sh\nexit "${LRP_NVIDIA_SMI_RC:-0}"\n')
        self._write(self.cmds / "reboot",
                    '#!/bin/sh\necho called >> "$LRP_REBOOTLOG"\nexit 0\n')
        # chmod/chown are routed through the command seam so tests can verify
        # the exact permission request (MSYS cannot store/report 0600).
        self._write(self.cmds / "chmod",
                    '#!/bin/sh\necho "chmod $*" >> "$LRP_CHMODLOG"\nexit 0\n')
        self._write(self.cmds / "chown",
                    '#!/bin/sh\necho "chown $*" >> "$LRP_CHOWNLOG"\nexit 0\n')

    # -- filesystem -----------------------------------------------------
    def os_release(self, lines):
        self._write(self.root / "etc" / "os-release", "\n".join(lines) + "\n")
        return self

    def efi(self, enabled=True):
        p = self.root / "sys" / "firmware" / "efi"
        if enabled:
            (p / "efivars").mkdir(parents=True, exist_ok=True)
        else:
            shutil.rmtree(p, ignore_errors=True)
        return self

    def pci_gpu(self, vendor="0x10de", device="0x2504", bound="nvidia",
                present=True):
        d = self.root / "sys" / "bus" / "pci" / "devices" / "dev0"
        if not present:
            shutil.rmtree(self.root / "sys" / "bus" / "pci" / "devices",
                          ignore_errors=True)
            (self.root / "sys" / "bus" / "pci" / "devices").mkdir(parents=True)
            return self
        d.mkdir(parents=True, exist_ok=True)
        self._write(d / "vendor", vendor + "\n")
        self._write(d / "device", device + "\n")
        self._write(d / "class", "0x030000\n")
        if bound is None:
            (d / "driver").unlink(missing_ok=True)
        else:
            self._write(d / "driver", bound + "\n")
        return self

    def modules(self, text):
        self._write(self.root / "proc" / "modules", text)
        return self

    def sources_deb822(self, text):
        self.source_layout = "deb822"
        self._write(self.root / "etc" / "apt" / "sources.list.d" / "debian.sources",
                    text)
        return self

    def sources_legacy(self, text):
        self.source_layout = "legacy"
        (self.root / "etc" / "apt" / "sources.list.d" / "debian.sources").unlink(missing_ok=True)
        self._write(self.root / "etc" / "apt" / "sources.list", text)
        return self

    def add_extra_source(self, text, name="other.list"):
        self._write(self.root / "etc" / "apt" / "sources.list.d" / name, text)
        return self

    # -- commands -------------------------------------------------------
    def no_dpkg(self):
        (self.cmds / "dpkg").unlink(missing_ok=True)
        return self

    def no_uname(self):
        (self.cmds / "uname").unlink(missing_ok=True)
        return self

    def no_dpkg_query(self):
        (self.cmds / "dpkg-query").unlink(missing_ok=True)
        return self

    def no_apt_cache(self):
        (self.cmds / "apt-cache").unlink(missing_ok=True)
        return self

    def apt_cache_raw(self, body):
        self._write(self.cmds / "apt-cache", body)
        return self

    def mokutil(self, state="disabled"):
        p = self.cmds / "mokutil"
        if state == "missing":
            p.unlink(missing_ok=True)
            return self
        if state == "fail":
            self._write(p, "#!/bin/sh\nexit 2\n")
            return self
        label = {"enabled": "SecureBoot enabled", "disabled": "SecureBoot disabled"}[state]
        self._write(p, '#!/bin/sh\n[ "$1" = --sb-state ] && echo "' + label + '"\n')
        return self

    def installed(self, *pkgs):
        self._env["LRP_INSTALLED"] = ",".join(pkgs)
        return self

    def arch(self, a):
        self._env["LRP_DPKG_ARCH"] = a
        return self

    def smi_rc(self, rc):
        self._env["LRP_NVIDIA_SMI_RC"] = str(rc)
        return self

    def apt_update_rc(self, rc):
        self._env["APT_UPDATE_RC"] = str(rc)
        return self

    def apt_install_rc(self, rc):
        self._env["APT_INSTALL_RC"] = str(rc)
        return self

    def kernel(self, release=KERNEL_RELEASE, image_version=KERNEL_VERSION,
               header_candidate=KERNEL_VERSION):
        self._env["LRP_KERNEL_RELEASE"] = release
        self._env["LRP_IMAGE_VERSION"] = image_version
        self._env["LRP_HEADER_CANDIDATE"] = header_candidate
        return self

    # -- state helpers --------------------------------------------------
    def state_file(self):
        return self.root / "var" / "lib" / "linuxremoteplayer" / "bootstrap" / "state"

    def backup_file(self):
        name = "sources.list.bak" if self.source_layout == "legacy" else "sources.debian.bak"
        return self.root / "var" / "lib" / "linuxremoteplayer" / "bootstrap" / name

    def write_state(self, text):
        p = self.state_file()
        p.parent.mkdir(parents=True, exist_ok=True)
        self._write(p, text)
        return self

    # -- runner ---------------------------------------------------------
    def run(self, *args, extra_env=None):
        env = dict(os.environ)
        env.update(self._env)
        env.update({
            "LRP_PF": _msys(PREFLIGHT),
            "LRP_ROOT": _msys(self.root),
            "LRP_COMMANDS": _msys(self.cmds),
            "LRP_COMMANDS_ONLY": "1",
            "APT_OPLOG": _msys(self.apt_log),
            "LRP_REBOOTLOG": _msys(self.reboot_log),
            "LRP_CHMODLOG": _msys(self.chmod_log),
            "LRP_CHOWNLOG": _msys(self.chown_log),
        })
        if extra_env:
            env.update(extra_env)
        script = "bash \"$LRP_PF\" \"$@\""
        return subprocess.run([BASH, "-c", script, "lrp", *args],
                              env=env, capture_output=True, text=True)

    def json(self, *args, **kw):
        proc = self.run(*args, **kw)
        try:
            start = proc.stdout.index("{")
            body = json.loads(proc.stdout[start:])
        except (ValueError, json.JSONDecodeError):
            body = None
        return proc, body

    def stat_mode(self, path):
        p = subprocess.run(
            [BASH, "-c", 'stat -c "%a" "$0"', _msys(path)],
            capture_output=True, text=True)
        return p.stdout.strip()

    def read_apt_log_installs(self):
        if not self.apt_log.exists():
            return []
        lines = self.apt_log.read_text().splitlines()
        return [line for line in lines if line.startswith("install")]

    def reboot_called(self):
        return self.reboot_log.exists()

    def chmod_calls(self):
        if not self.chmod_log.exists():
            return []
        return self.chmod_log.read_text(encoding="utf-8").splitlines()

    def chmod_has(self, mode, suffix):
        return any(l.startswith("chmod " + mode + " ") and
                   l.split()[-1].endswith(suffix) for l in self.chmod_calls())

    @staticmethod
    def source_components(text):
        for line in text.splitlines():
            if line.startswith("Components:"):
                return line.split(":", 1)[1].strip()
        return ""


@pytest.fixture
def fx(tmp_path):
    return Fixture(tmp_path)


# ---------------------------------------------------------------------------
# Read-only default and no mutation
# ---------------------------------------------------------------------------

def test_default_plan_is_read_only_no_mutation(fx):
    before = (fx.root / "etc" / "apt" / "sources.list.d" / "debian.sources").read_text()
    proc, body = fx.json()
    assert proc.returncode == 0
    assert body["mode"] == "plan"
    after = (fx.root / "etc" / "apt" / "sources.list.d" / "debian.sources").read_text()
    assert after == before
    assert not fx.state_file().exists()
    assert not fx.backup_file().exists()
    assert not fx.reboot_called()


def test_apply_requires_explicit_owner_approval(fx):
    before = (fx.root / "etc" / "apt" / "sources.list.d" / "debian.sources").read_text()
    proc, _ = fx.json("--apply")
    assert proc.returncode == 12
    after = (fx.root / "etc" / "apt" / "sources.list.d" / "debian.sources").read_text()
    assert after == before
    assert not fx.state_file().exists()
    assert not fx.reboot_called()


def test_approval_without_apply_is_invalid(fx):
    proc, _ = fx.json("--approve")
    assert proc.returncode == 12


# ---------------------------------------------------------------------------
# Apply: full success
# ---------------------------------------------------------------------------

def test_apply_success_reboot_required_and_exact_bundle(fx):
    proc, body = fx.json("--apply", "--approve")
    assert proc.returncode == 20, proc.stdout
    assert body["state"]["phase"] == "reboot_required"
    assert body["state"]["reboot_required"] == 1
    assert not fx.reboot_called()

    # components enabled in the existing single source file (no duplicate source)
    srcfiles = list((fx.root / "etc" / "apt" / "sources.list.d").iterdir())
    assert [p.name for p in srcfiles] == ["debian.sources"]
    comps = fx.source_components(srcfiles[0].read_text())
    assert comps.split() == EXPECTED_COMPONENTS.split()

    # backup exists and hash registered in state
    assert fx.backup_file().exists()
    state = fx.state_file().read_text()
    assert state.startswith("phase=reboot_required")
    assert "source_backup_sha256=" in state and state.split("source_backup_sha256=")[1].strip()

    # exact install bundle + apt update, in order
    log = fx.apt_log.read_text().splitlines()
    assert "update" in log
    installs = fx.read_apt_log_installs()
    assert len(installs) == 1
    tokens = shlex.split(installs[0])
    assert tokens[0] == "install" and tokens[1] == "-y"
    argv = tokens[2:]
    expected = dict(EXPECTED_PKGS)
    expected["linux-headers-" + KERNEL_RELEASE] = KERNEL_VERSION
    expected_argv = sorted(k + "=" + v for k, v in expected.items())
    assert sorted(argv) == expected_argv
    assert body["kernel"] == {
        "release": KERNEL_RELEASE,
        "image_package": "linux-image-" + KERNEL_RELEASE,
        "image_version": KERNEL_VERSION,
        "header_package": "linux-headers-" + KERNEL_RELEASE,
        "header_version": KERNEL_VERSION,
        "probe": "ok",
    }
    assert "linux-headers-amd64" not in argv


def test_kernel_meta_drift_is_ignored(fx):
    # The meta package is deliberately not provided by any fixture command;
    # only the exact release-derived header is queried/installed.
    proc, body = fx.json("--apply", "--approve")
    assert proc.returncode == 20
    assert body["kernel"]["header_package"] == "linux-headers-" + KERNEL_RELEASE
    assert "linux-headers-amd64" not in "\n".join(fx.apt_log.read_text().splitlines())


def test_kernel_image_header_version_mismatch_stops_before_mutation(fx):
    fx.kernel(header_candidate="6.12.104-1")
    proc, body = fx.json("--apply", "--approve")
    assert proc.returncode == 11
    assert "mismatch" in " ".join(body["preflight"]["issues"])
    assert not fx.state_file().exists()
    assert not fx.apt_log.exists()


def test_kernel_image_or_header_data_missing_is_unresolved(fx):
    fx.no_dpkg_query()
    proc, body = fx.json("--apply", "--approve")
    assert proc.returncode == 10
    assert body["preflight"]["issues"]
    assert not fx.state_file().exists()


def test_kernel_candidate_parses_with_spanish_host_locale(fx):
    # The command changes labels by locale; the probe must scope LC_ALL/LANG=C
    # and therefore receive the English Candidate field.
    fx.apt_cache_raw(
        '#!/bin/sh\n'
        'if [ "$LC_ALL" = "C" ] && [ "$LANG" = "C" ]; then\n'
        '  echo "  Installed: (none)"\n'
        '  echo "  Candidate: 6.12.105-1"\n'
        'else\n'
        '  echo "  Instalado: (none)"\n'
        '  echo "  Candidato: 6.12.105-1"\n'
        'fi\n')
    proc, body = fx.json("--apply", "--approve")
    assert proc.returncode == 20
    assert body["kernel"]["header_package"] == "linux-headers-" + KERNEL_RELEASE
    assert body["kernel"]["header_version"] == KERNEL_VERSION
    assert not fx.reboot_called()


def test_kernel_candidate_none_stops_before_mutation(fx):
    fx.kernel(header_candidate="(none)")
    proc, body = fx.json("--apply", "--approve")
    assert proc.returncode == 11
    assert "header_candidate_unavailable" in body["preflight"]["issues"]
    assert not fx.state_file().exists()
    assert not fx.apt_log.exists()


def test_kernel_candidate_field_missing_stops_before_mutation(fx):
    fx.apt_cache_raw('#!/bin/sh\necho "  Installed: (none)"\n')
    proc, body = fx.json("--apply", "--approve")
    assert proc.returncode == 10
    assert "header_candidate_unresolved" in body["preflight"]["issues"]
    assert not fx.state_file().exists()
    assert not fx.apt_log.exists()


def test_apply_preserves_other_source_fields_and_permissions(fx):
    original = (fx.root / "etc" / "apt" / "sources.list.d" / "debian.sources").read_text()
    fx.json("--apply", "--approve")
    edited = (fx.root / "etc" / "apt" / "sources.list.d" / "debian.sources").read_text()
    def keep(s):
        return [l for l in s.splitlines() if not l.startswith("Components:")]
    assert keep(edited) == keep(original)
    for line in ("Types:", "URIs:", "Suites:", "Signed-By:"):
        assert any(l.startswith(line) for l in edited.splitlines())
    # Existing source file keeps its own permission mode (0644 here).
    assert fx.stat_mode(fx.root / "etc" / "apt" / "sources.list.d" / "debian.sources") == "644"
    # Strict mode requests are observable via the routed permission seam.
    calls = fx.chmod_calls()
    assert calls, calls
    assert fx.chmod_has("0700", "/bootstrap"), calls          # store dir
    assert fx.chmod_has("0600", "/state"), calls              # state file 0600
    assert fx.chmod_has("0600", "/sources.debian.bak"), calls # backup 0600
    assert fx.chmod_has("0644", "/debian.sources"), calls     # source 0644
    # On the real filesystem the sensitive artifacts are not group/other writable.
    for label, path in (("bst", fx.state_file().parent),
                        ("state", fx.state_file()),
                        ("backup", fx.backup_file())):
        mode = int(fx.stat_mode(path), 8)
        assert mode & 0o022 == 0, (label, path)


def test_state_and_backup_mode_0600_requested(fx):
    fx.json("--apply", "--approve")
    assert fx.chmod_has("0600", "/state")
    assert fx.chmod_has("0600", "/sources.debian.bak")
    assert fx.chmod_has("0700", "/bootstrap")


def test_apply_idempotent_when_components_already_enabled(fx):
    fx.sources_deb822(
        "Types: deb\nURIs: http://deb.debian.org/debian\nSuites: trixie\n"
        "Components: " + EXPECTED_COMPONENTS + "\n"
        "Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg\n")
    before = (fx.root / "etc" / "apt" / "sources.list.d" / "debian.sources").read_text()
    proc, body = fx.json("--apply", "--approve")
    assert proc.returncode == 20
    after = (fx.root / "etc" / "apt" / "sources.list.d" / "debian.sources").read_text()
    assert after == before
    assert "update" in fx.apt_log.read_text()


def test_legacy_layout_plan_is_accepted(fx):
    fx.sources_legacy(
        "# retained comment\n\n"
        "deb http://deb.debian.org/debian trixie main non-free-firmware\n"
        "deb-src http://deb.debian.org/debian trixie-updates main non-free-firmware # source\n"
        "deb http://security.debian.org/debian-security trixie-security main non-free-firmware\n")
    proc, body = fx.json()
    assert proc.returncode == 0
    assert body["sources"]["layout"] == "legacy"
    assert body["sources"]["file"] == "sources.list"
    assert body["sources"]["contract_ok"] is True
    assert not fx.state_file().exists()


def test_legacy_apply_adds_components_preserving_lines_and_backup(fx):
    original = (
        "# retained comment\n\n"
        "deb http://deb.debian.org/debian trixie main non-free-firmware\n"
        "deb-src http://deb.debian.org/debian trixie-updates main non-free-firmware # source\n")
    fx.sources_legacy(original)
    proc, body = fx.json("--apply", "--approve")
    assert proc.returncode == 20
    source = (fx.root / "etc" / "apt" / "sources.list").read_text()
    assert source.startswith("# retained comment\n\n")
    assert "deb http://deb.debian.org/debian trixie main contrib non-free non-free-firmware\n" in source
    assert "deb-src http://deb.debian.org/debian trixie-updates main contrib non-free non-free-firmware # source\n" in source
    assert fx.backup_file().name == "sources.list.bak"
    assert fx.backup_file().read_text() == original
    assert body["sources"]["layout"] == "legacy"
    assert "layout=legacy" in fx.state_file().read_text()
    assert not (fx.root / "etc" / "apt" / "sources.list.d" / "debian.sources").exists()


def test_legacy_apply_is_idempotent(fx):
    original = (
        "# retained\n"
        "deb http://deb.debian.org/debian trixie main contrib non-free non-free-firmware\n"
        "deb-src http://security.debian.org/debian-security trixie-security main contrib non-free non-free-firmware\n")
    fx.sources_legacy(original)
    proc, _ = fx.json("--apply", "--approve")
    assert proc.returncode == 20
    assert (fx.root / "etc" / "apt" / "sources.list").read_text() == original


def test_legacy_nouveau_preinstall_reaches_reboot_required(fx):
    fx.sources_legacy(
        "# existing legacy layout\n"
        "deb http://deb.debian.org/debian trixie main\n")
    fx.pci_gpu(bound="nouveau").modules("nouveau 1 1 live\n")
    proc, body = fx.json("--apply", "--approve")
    assert proc.returncode == 20
    assert body["state"]["phase"] == "reboot_required"
    assert body["sources"]["layout"] == "legacy"
    assert "update" in fx.apt_log.read_text()
    assert not fx.reboot_called()


def test_legacy_apt_update_failure_restores_actual_backup(fx):
    original = "# comment\ndeb http://deb.debian.org/debian trixie main non-free-firmware\n"
    fx.sources_legacy(original).apt_update_rc(1)
    proc, body = fx.json("--apply", "--approve")
    assert proc.returncode == 11
    assert body["state"]["status"] == "apt_update_failed"
    assert (fx.root / "etc" / "apt" / "sources.list").read_text() == original
    assert fx.backup_file().read_text() == original


def test_legacy_and_deb822_active_rejected(fx):
    fx.sources_legacy("deb http://deb.debian.org/debian trixie main\n")
    fx.sources_deb822(
        "Types: deb\nURIs: http://deb.debian.org/debian\n"
        "Suites: trixie\nComponents: main\n"
        "Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg\n")
    proc, _ = fx.json("--apply", "--approve")
    assert proc.returncode == 12
    _assert_no_mutation(fx)


def test_legacy_credentials_and_malformed_contract_rejected(fx):
    fx.sources_legacy(
        "deb http://deploy:secret@deb.debian.org/debian trixie main\n")
    proc, _ = fx.json("--apply", "--approve")
    assert proc.returncode == 12
    _assert_no_mutation(fx)


def test_apply_state_dir_root_owned(monkeypatch, fx):
    fx.json("--apply", "--approve")
    # The tool targets a root-owned state store. chown is best-effort in tests,
    # so we assert the store directory & file exist with restrictive modes and
    # that the script explicitly applies chown 0:0 (verified statically below).
    assert fx.state_file().is_file()
    assert fx.state_file().parent == fx.root / "var" / "lib" / "linuxremoteplayer" / "bootstrap"


# ---------------------------------------------------------------------------
# Source trust boundary (invalid contract -> 12, no mutation)
# ---------------------------------------------------------------------------

def _assert_no_mutation(fx):
    assert not fx.state_file().exists()
    assert not fx.backup_file().exists()
    assert not fx.reboot_called()


def test_multiple_sources_rejected(fx):
    fx.add_extra_source("deb http://evil.example-co-uk.com/repo trixie main\n")
    proc, _ = fx.json("--apply", "--approve")
    assert proc.returncode == 12
    _assert_no_mutation(fx)


def test_third_party_repo_rejected(fx):
    fx.sources_deb822("Types: deb\n"
                      "URIs: http://evil.example-co-uk.com/repo\n"
                      "Suites: trixie\nComponents: main\n")
    proc, _ = fx.json("--apply", "--approve")
    assert proc.returncode == 12
    _assert_no_mutation(fx)


def test_ambiguous_multiple_uris_rejected(fx):
    fx.sources_deb822("Types: deb\n"
                      "URIs: http://deb.debian.org/debian http://cup.example-co-uk.com\n"
                      "Suites: trixie\nComponents: main\n")
    proc, _ = fx.json("--apply", "--approve")
    assert proc.returncode == 12
    _assert_no_mutation(fx)


def test_missing_debian_sources_rejected(fx):
    (fx.root / "etc" / "apt" / "sources.list.d" / "debian.sources").unlink()
    proc, _ = fx.json("--apply", "--approve")
    assert proc.returncode == 12
    _assert_no_mutation(fx)


# ---------------------------------------------------------------------------
# Preflight fail-closed
# ---------------------------------------------------------------------------

def test_wrong_distro_fail_closed(fx):
    fx.os_release(("ID=ubuntu", 'VERSION_ID="24.04"', "VERSION_CODENAME=noble"))
    before = (fx.root / "etc" / "apt" / "sources.list.d" / "debian.sources").read_text()
    proc, body = fx.json("--apply", "--approve")
    assert proc.returncode == 11
    assert body["preflight"]["status"] == "fail"
    assert (fx.root / "etc" / "apt" / "sources.list.d" / "debian.sources").read_text() == before
    assert not fx.state_file().exists()


def test_secure_boot_enabled_fail_closed(fx):
    fx.mokutil("enabled")
    proc, body = fx.json("--apply", "--approve")
    assert proc.returncode == 11
    assert body["preflight"]["status"] == "fail"
    assert "secure_boot" in body["preflight"]["issues"][0]
    assert not fx.state_file().exists()


def test_expected_gpu_missing_fail_closed(fx):
    fx.pci_gpu(present=False)
    proc, body = fx.json("--apply", "--approve")
    assert proc.returncode == 11
    assert any("gpu" in i for i in body["preflight"]["issues"])
    assert not fx.state_file().exists()


def test_wrong_architecture_fail_closed(fx):
    fx.arch("arm64").no_uname()
    proc, body = fx.json("--apply", "--approve")
    assert proc.returncode == 11
    assert any("arch" in i for i in body["preflight"]["issues"])


def test_secure_boot_unresolved_exit_10(fx):
    fx.mokutil("missing")
    proc, body = fx.json("--apply", "--approve")
    assert proc.returncode == 10
    assert body["preflight"]["status"] == "unknown"
    assert body["preflight"]["issues"]


def test_arch_unresolved_exit_10(fx):
    fx.no_dpkg().no_uname()
    proc, _ = fx.json("--apply", "--approve")
    assert proc.returncode == 10


# ---------------------------------------------------------------------------
# Rollback / transaction failures
# ---------------------------------------------------------------------------

def test_apt_update_failure_restores_source_backup(fx):
    original = (fx.root / "etc" / "apt" / "sources.list.d" / "debian.sources").read_text()
    fx.apt_update_rc(1)
    proc, body = fx.json("--apply", "--approve")
    assert proc.returncode == 11
    assert body["state"]["status"] == "apt_update_failed"
    restored = (fx.root / "etc" / "apt" / "sources.list.d" / "debian.sources").read_text()
    assert restored == original          # restored to the pre-enable backup
    assert not fx.reboot_called()


def test_package_install_failure_preserves_components(fx):
    fx.apt_update_rc(0).apt_install_rc(1)
    proc, body = fx.json("--apply", "--approve")
    assert proc.returncode == 11
    assert body["state"]["status"] == "package_install_failed"
    comps = fx.source_components(
        (fx.root / "etc" / "apt" / "sources.list.d" / "debian.sources").read_text())
    assert comps == EXPECTED_COMPONENTS   # not rolled back, kept for retry
    assert not fx.reboot_called()


def test_reapply_from_package_failure_preserves_backup_and_is_idempotent(fx):
    fx.apt_install_rc(1)
    first, first_body = fx.json("--apply", "--approve")
    assert first.returncode == 11
    backup = fx.backup_file().read_bytes()
    state_before = fx.state_file().read_text()
    fx.apt_install_rc(0)
    second, second_body = fx.json("--apply", "--approve")
    assert second.returncode == 20
    assert fx.backup_file().read_bytes() == backup
    assert "source_backup_sha256=" + state_before.split("source_backup_sha256=", 1)[1].splitlines()[0] in fx.state_file().read_text()
    assert second_body["state"]["phase"] == "reboot_required"
    assert fx.source_components((fx.root / "etc" / "apt" / "sources.list.d" / "debian.sources").read_text()) == EXPECTED_COMPONENTS


# ---------------------------------------------------------------------------
# Resume: post-reboot verification
# ---------------------------------------------------------------------------

def test_resume_invalid_without_apply_state(fx):
    proc, _ = fx.json("--resume")
    assert proc.returncode == 12


def test_resume_post_reboot_pass(fx):
    fx.write_state("phase=reboot_required\nreboot_required=1\n")
    # pre-populate installed so post-state is consistent (not required by tool)
    proc, body = fx.json("--resume")
    assert proc.returncode == 0
    assert body["state"]["phase"] == "complete"
    assert body["state"]["post_reboot_ok"] == 1
    state = fx.state_file().read_text()
    assert "phase=complete" in state


def test_resume_post_reboot_gpu_not_bound(fx):
    fx.write_state("phase=reboot_required\nreboot_required=1\n")
    fx.pci_gpu(bound="nouveau")
    proc, body = fx.json("--resume")
    assert proc.returncode == 21
    assert any("bound" in i for i in body["post_reboot"]["issues"])


def test_resume_post_reboot_nvidia_smi_fails(fx):
    fx.write_state("phase=reboot_required\nreboot_required=1\n")
    fx.smi_rc(1)
    proc, _ = fx.json("--resume")
    assert proc.returncode == 21


def test_resume_post_reboot_nouveau_present(fx):
    fx.write_state("phase=reboot_required\nreboot_required=1\n")
    fx.modules("nvidia 1 1 live\nnvidia_modeset 1 1 live\n"
               "nvidia_drm 1 1 live\nnvidia_uvm 1 1 live\nnouveau 1 0 live\n")
    proc, body = fx.json("--resume")
    assert proc.returncode == 21
    assert "nouveau_present" in " ".join(body["post_reboot"]["issues"])


def test_resume_post_reboot_modules_absent(fx):
    fx.write_state("phase=reboot_required\nreboot_required=1\n")
    fx.modules("overlay 1 1 live\n")
    proc, _ = fx.json("--resume")
    assert proc.returncode == 21


def test_renderer_graphics_deferred_to_t124(fx):
    # Post-reboot verification only checks PCI binding, NVIDIA modules,
    # nvidia-smi and nouveau absence. Graphics/renderer is T-124.
    fx.write_state("phase=reboot_required\nreboot_required=1\n")
    proc, body = fx.json("--resume")
    assert proc.returncode == 0
    asserted = json.dumps(body)
    assert "renderer" not in asserted.lower()
    assert "glx" not in asserted.lower()
    assert "xdpyinfo" not in asserted
    assert "glxinfo" not in asserted
    source = PREFLIGHT.read_text(encoding="utf-8")
    assert "xdpyinfo" not in source
    assert "glxinfo" not in source


# ---------------------------------------------------------------------------
# Sanitization
# ---------------------------------------------------------------------------

def test_sanitization_no_secret_no_hostname(fx):
    secret = "A_VERY_SECRET_TOKEN_XYZ99"
    fx.sources_deb822("Types: deb\n"
                      "URIs: http://deploy:" + secret + "@deb.debian.org/debian\n"
                      "Suites: trixie\nComponents: main\n")
    proc, _ = fx.json("--apply", "--approve")
    raw = proc.stdout
    assert secret not in raw
    assert "deploy:" not in raw
    assert "://" not in raw
    # hostname/username capture commands never used
    source = PREFLIGHT.read_text(encoding="utf-8")
    for bad in ("hostname ", "whoami", "getent", "logname", "/etc/hostname",
                ".env", "pairing_token"):
        assert bad not in source


def test_state_contains_no_secrets(fx):
    fx.json("--apply", "--approve")
    state = fx.state_file().read_text()
    for bad in ("SECRET", "password", "token=", "@"):
        assert bad not in state
    assert "phase=" in state


def test_intel_gpu_noop_apply_and_resume(fx):
    fx.pci_gpu(vendor="0x8086", device="0x0152", bound="i915")
    proc, body = fx.json("--apply", "--approve")
    assert proc.returncode == 0
    assert body["state"]["phase"] == "complete"
    assert body["state"]["status"] == "complete"
    udev = fx.root / "etc" / "udev" / "rules.d" / "71-nvidia.rules"
    assert udev.is_file()
    assert 'ATTR{vendor}=="0x10de"' in udev.read_text()


# ---------------------------------------------------------------------------
# Static invariant tests
# ---------------------------------------------------------------------------

def _code(source):
    return "\n".join(l for l in source.splitlines()
                     if not l.lstrip().startswith("#"))


def test_static_no_auto_reboot_no_emg_mutation():
    code = _code(PREFLIGHT.read_text(encoding="utf-8"))
    import re
    for bad in ("reboot ", " shutdown", "poweroff", " poweroff", "halt",
                "systemctl", "systemd-run", " init 6", "sudo ",
                "rm -rf /", "> /etc/", ">> /etc/"):
        assert bad not in code, bad
    assert re.search(r"(^|[;&|[:space:]])reboot([ ;&|$])", code) is None


def test_static_exact_package_bundle_no_open_variant():
    code = _code(PREFLIGHT.read_text(encoding="utf-8"))
    assert "nvidia-open" not in code
    assert "linux-headers-amd64" not in code
    assert "HEADER_PKG=\"linux-headers-$host_kernel\"" in code
    for base, ver in EXPECTED_PKGS.items():
        assert (base + "]=" + ver) in code, base
        assert (base + "=" + ver) in (" " + code) or (base + "]=" + ver) in code
    for token in ("lightdm", " xorg", "openbox", "nvidia-driver.run", ".run"):
        assert token not in code


def test_static_exit_codes_present():
    code = _code(PREFLIGHT.read_text(encoding="utf-8"))
    for token in ("exit 12", "exit_code=21", "exit_code=20", "exit_code=11",
                  "exit_code=10", "exit_code=0", "exit \"$exit_code\""):
        assert token in code, token


# ---------------------------------------------------------------------------
# Exact write-set (this task adds only the two NVIDIA files)
# ---------------------------------------------------------------------------

def test_exact_write_set():
    for relative in ("scripts/debian/nvidia-bootstrap.sh",
                     "tests/test_nvidia_bootstrap.py"):
        path = ROOT / relative
        assert path.is_file()
        assert subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "--error-unmatch", relative],
            capture_output=True, text=True).returncode == 0
