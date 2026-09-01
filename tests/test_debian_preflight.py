"""T-122 tests for the Debian 13 foundation preflight tool.

The preflight tool is a read-only bash probe (scripts/debian/preflight.sh). It
emits a single sanitized JSON document and uses deterministic exit codes:
  0  success, 10 missing data/tool, 11 failed requirement, 12 invalid contract.

These tests run the real script through Git Bash against fixture filesystems,
plus static source checks for forbidden behavior and sanitization.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = ROOT / "scripts" / "debian" / "preflight.sh"


def _find_bash():
    if os.name == "nt":
        candidate = Path("C:/Program Files/Git/bin/bash.exe")
        if candidate.exists():
            return str(candidate)
    return shutil.which("bash") or ("/bin/bash" if os.name != "nt" else str(candidate))


BASH = _find_bash()

FORBIDDEN_MUTATORS = (
    "sudo",
    "apt-get update",
    "apt-get install",
    "apt update",
    "apt install",
    "dpkg --install",
    "dpkg -i ",
    "dpkg --configure",
    "dpkg --purge",
    "dpkg --remove",
    "modprobe",
    "systemctl",
    "shutdown",
    "reboot",
    "mktemp",
    "mkdir -p /",
    "/etc/modules-load.d",
    "lrp-cleanup",
    "nvidia-smi --generate",
)


def _msys(path):
    text = str(path).replace("\\", "/")
    if os.name != "nt":
        return str(Path(path).resolve())
    drive, rest = text.split(":", 1)
    return "/" + drive.lower() + rest


class Fixture:
    """Builds a fake Debian filesystem + fake command stubs in tmp_path."""

    def __init__(self, root_dir):
        self.base = root_dir
        self.root = root_dir / "root"
        self.cmds = root_dir / "cmds"
        self.manifest = root_dir / "manifest.txt"
        for d in ("etc/apt/sources.list.d", "proc", "sys/firmware/efi"):
            (self.root / d).mkdir(parents=True, exist_ok=True)
        self.cmds.mkdir(exist_ok=True)
        self._env_extra = {}
        self.uname_added = False
        self.dpkg_added = False
        self.os_release(("ID=debian", 'VERSION_ID="13"',
                         "VERSION_CODENAME=trixie"))

    # -- low-level write (ASCII/LF, no CRLF translation) -----------------
    @staticmethod
    def _write(path, text):
        path.write_bytes(str(text).encode("ascii", "replace"))
        return path

    # -- filesystem -----------------------------------------------------
    def os_release(self, lines):
        self._write(self.root / "etc" / "os-release",
                    "\n".join(lines) + "\n")
        return self

    def efi(self, enabled=True):
        if enabled:
            (self.root / "sys" / "firmware" / "efi").mkdir(
                parents=True, exist_ok=True)
            (self.root / "sys" / "firmware" / "efi" / "efivars").mkdir(
                exist_ok=True)
        else:
            shutil.rmtree(self.root / "sys" / "firmware" / "efi",
                          ignore_errors=True)
        return self

    def pci_gpu(self, vendor="0x10de", device="0x2504", cls="0x030000",
                name="dev0"):
        d = self.root / "sys" / "bus" / "pci" / "devices" / name
        d.mkdir(parents=True, exist_ok=True)
        self._write(d / "class", cls + "\n")
        self._write(d / "vendor", vendor + "\n")
        self._write(d / "device", device + "\n")
        return self

    def modules(self, text):
        self._write(self.root / "proc" / "modules", text)
        return self

    def apt_sources(self, lines, sources_d=None):
        self._write(self.root / "etc" / "apt" / "sources.list",
                    "\n".join(lines) + "\n")
        if sources_d:
            self._write(self.root / "etc" / "apt" / "sources.list.d" / "custom.list",
                        "\n".join(sources_d) + "\n")
        return self

    def apt_sources_deb822(self, text, name="custom.sources"):
        self._write(self.root / "etc" / "apt" / "sources.list.d" / name,
                    text)
        return self

    # -- commands -------------------------------------------------------
    def _stub(self, name, body, present=True):
        p = self.cmds / name
        if not present:
            p.unlink(missing_ok=True)
            return self
        self._write(p, body)
        return self

    def cmd_uname(self, kernel="6.1.0-21-amd64", machine="x86_64", fail=False):
        body = (
            "#!/bin/sh\n"
            "case \"$1\" in\n"
            "  -r) echo " + kernel + " ;;\n"
            "  *) echo " + machine + " ;;\n"
            "esac\n"
        )
        if fail:
            body = "#!/bin/sh\nexit 1\n"
        self._stub("uname", body)
        self.uname_added = True
        return self

    def cmd_dpkg(self, arch="amd64", present=True):
        self._stub("dpkg", "#!/bin/sh\necho " + arch + "\n", present=present)
        self.dpkg_added = True
        return self

    def cmd_mokutil(self, state="disabled", fail=False, present=True):
        if state == "unknown" or not present or fail:
            present = False if state in ("missing", None) else present
        if state == "missing" or not present:
            self._stub("mokutil", "#!/bin/sh\nexit 127\n", present=False)
            return self
        if fail:
            self._stub("mokutil", "#!/bin/sh\nexit 3\n")
            return self
        label = {
            "enabled": "SecureBoot enabled",
            "disabled": "SecureBoot disabled",
        }[state]
        self._stub("mokutil", '#!/bin/sh\n[ "$1" = --sb-state ] && echo "' +
                   label + '"\n')
        return self

    def cmd_apt_cache(self, policy=None, fail=False, present=True):
        if not present:
            self._stub("apt-cache", "#!/bin/sh\nexit 127\n", present=False)
            return self
        if fail:
            self._stub("apt-cache", "#!/bin/sh\nexit 2\n")
            return self
        body = "#!/bin/sh\nif [ \"$1\" = policy ]; then\ncase \"$2\" in\n"
        for pkg in (policy or {}):
            info = policy[pkg]
            inst = info.get("installed") or "(none)"
            cand = info.get("candidate") or "(none)"
            body += "  {p}) echo \"{p}:\" ; echo \"  Installed: {i}\" ; " \
                    "echo \"  Candidate: {c}\" ;;\n".format(
                        p=pkg, i=inst, c=cand)
        body += "esac\nfi\n"
        self._stub("apt-cache", body)
        return self

    def cmd_apt_cache_raw(self, body):
        self._stub("apt-cache", body)
        return self

    def cmd_binary(self, name, present=True):
        self._stub(name, "#!/bin/sh\nexit 0\n", present=present)
        return self

    # -- manifest -------------------------------------------------------
    def write_manifest(self, lines):
        self._write(self.manifest, "\n".join(lines) + "\n")
        return self

    def default_manifest(self):
        return self.write_manifest([
            "distro.id=debian", "distro.version=13", "distro.codename=trixie",
            "distro.arch=amd64", "secure_boot=disabled",
            "role.id=xorg", "role.bin=Xorg", "role.pkg=xserver-xorg",
            "role.id=openbox", "role.bin=openbox", "role.pkg=openbox",
            "role.id=display_manager", "role.bin=lightdm,gdm3,sddm,lightdm",
            "role.one_of=1",
            "role.id=nvidia", "role.gpu=nvidia", "role.pkg=nvidia-driver",
            "role.id=firefox_esr", "role.bin=firefox-esr",
            "role.pkg=firefox-esr",
            "role.id=pipewire", "role.bin=pipewire,wireplumber",
            "role.pkg=pipewire,wireplumber",
            "role.id=avahi", "role.bin=avahi-daemon", "role.pkg=avahi-daemon",
            "role.id=ufw", "role.bin=ufw", "role.pkg=ufw",
            "role.id=session", "role.bin=xdg-open,dbus-run-session",
        ])

    def satisfied_roles(self):
        """Adds stubs so every role in default_manifest() reports ok."""
        policy = {pkg: {"installed": "1:1.2", "candidate": "1:1.3"}
                  for pkg in ("xserver-xorg", "openbox", "nvidia-driver",
                              "firefox-esr", "pipewire", "wireplumber",
                              "avahi-daemon", "ufw")}
        self.cmd_apt_cache(policy)
        for binary in ("Xorg", "openbox", "lightdm", "firefox-esr", "pipewire",
                       "wireplumber", "avahi-daemon", "ufw", "xdg-open",
                       "dbus-run-session"):
            self.cmd_binary(binary)
        return self

    # -- runner ---------------------------------------------------------
    def run(self, argv=None, manifest_override=None):
        env = dict(os.environ)
        env.update({
            "LRP_PF": _msys(PREFLIGHT),
            "LRP_MF": _msys((manifest_override or self.manifest)),
            "LRP_ROOT": _msys(self.root),
            "LRP_COMMANDS": _msys(self.cmds),
            "LRP_COMMANDS_ONLY": "1",
        })
        env.update(self._env_extra)
        script = "bash \"$LRP_PF\" --manifest \"$LRP_MF\""
        if argv is not None:
            script = "bash \"$LRP_PF\" " + argv
        result = subprocess.run([BASH, "-c", script], env=env,
                                capture_output=True, text=True)
        return result

    def json(self, argv=None, manifest_override=None):
        proc = self.run(argv=argv, manifest_override=manifest_override)
        return proc, json.loads(proc.stdout[proc.stdout.index("{"):])


@pytest.fixture
def fx(tmp_path):
    return Fixture(tmp_path)


# ---------------------------------------------------------------------------
# Success / identity
# ---------------------------------------------------------------------------

def test_debian13_success(fx):
    fx.efi().pci_gpu().modules("nvidia 4096 1 live\novl 100 1 live\n")
    fx.apt_sources(
        ["deb http://deb.debian.org/debian trixie main non-free-firmware"],
        sources_d=["deb http://mirror.example-co-uk.com/apt trixie-stage main"])
    fx.cmd_uname().cmd_dpkg().cmd_mokutil("disabled")
    fx.satisfied_roles().default_manifest()
    proc = fx.run()
    body = json.loads(proc.stdout[proc.stdout.index("{"):])
    assert proc.returncode == 0
    assert body["contract_valid"] is True
    assert body["identity"]["id"] == "debian"
    assert body["identity"]["codename"] == "trixie"
    assert body["identity"]["architecture"]["effective"] == "amd64"
    assert body["identity"]["kernel"] == "6.1.0-21-amd64"
    assert body["identity"]["result"] == "ok"
    assert body["identity"]["violations"] == []
    assert body["secure_boot"]["state"] == "disabled"
    assert body["secure_boot"]["status"] == "ok"
    assert body["gpu"]["display_vendor"] == "nvidia"
    assert body["gpu"]["graphics_module"] == "nvidia"
    assert body["roles"]
    assert all(r["status"] == "ok" for r in body["roles"])
    assert body["summary"]["result"] == "pass"
    assert body["summary"]["exit_code"] == 0
    assert body["rollback"] == "none"
    assert body["apt"]["has_third_party"] is True
    assert "main" in body["apt"]["official_components"]


def test_crlf_newlines_are_normalized(fx):
    fx.efi().cmd_dpkg().cmd_uname().cmd_mokutil("disabled").satisfied_roles()
    fx.pci_gpu().modules("nvidia 1 1 live\n")
    # intentionally CRLF files, as a Windows staging pipeline would produce.
    fx._write(fx.root / "etc" / "os-release",
              'ID=debian\r\nVERSION_ID="13"\r\nVERSION_CODENAME=trixie\r\n')
    man = ["distro.id=debian", "distro.version=13", "distro.codename=trixie",
           "distro.arch=amd64", "secure_boot=disabled",
           "role.id=ufw", "role.bin=ufw", "role.pkg=ufw"]
    fx._write(fx.manifest, "\r\n".join(man) + "\r\n")
    proc, body = fx.json()
    assert proc.returncode == 0
    assert body["identity"]["id"] == "debian"
    assert body["identity"]["result"] == "ok"
    assert body["secure_boot"]["state"] == "disabled"
    assert body["summary"]["exit_code"] == 0


def test_non_debian_identified(fx):
    fx.efi().cmd_dpkg().cmd_uname().satisfied_roles()
    fx.os_release(("ID=ubuntu", 'VERSION_ID="24.04"', "VERSION_CODENAME=noble"))
    fx.default_manifest()
    proc, body = fx.json()
    assert proc.returncode == 11
    assert body["identity"]["id"] == "ubuntu"
    assert body["identity"]["result"] == "fail"
    assert "os_id" in body["identity"]["violations"]
    assert body["summary"]["exit_code"] == 11


def test_wrong_architecture(fx):
    fx.efi().cmd_dpkg("arm64").cmd_uname("6.1.0", "aarch64")
    fx.os_release(("ID=debian", 'VERSION_ID="13"', "VERSION_CODENAME=trixie"))
    fx.satisfied_roles().default_manifest()
    proc, body = fx.json()
    assert proc.returncode == 11
    assert "architecture" in body["identity"]["violations"]
    assert body["identity"]["architecture"]["effective"] == "arm64"


def test_wrong_version_and_codename(fx):
    fx.efi().cmd_dpkg().cmd_uname().satisfied_roles()
    fx.os_release(("ID=debian", 'VERSION_ID="12"', "VERSION_CODENAME=bookworm"))
    fx.default_manifest()
    proc, body = fx.json()
    assert proc.returncode == 11
    violations = body["identity"]["violations"]
    assert "os_version" in violations
    assert "os_codename" in violations


def test_rtx3060_gpu_match(fx):
    fx.efi().cmd_dpkg().cmd_uname().cmd_mokutil("disabled").satisfied_roles()
    fx.pci_gpu(vendor="0x10de", device="0x2504")
    fx.modules("nvidia_drm 1 0 live\nnvidia 4096 1 live\n")
    fx.default_manifest()
    proc, body = fx.json()
    assert proc.returncode == 0
    nvidia = [r for r in body["roles"] if r["id"] == "nvidia"][0]
    assert nvidia["status"] == "ok"
    assert body["gpu"]["display_vendor"] == "nvidia"


def test_gpu_mismatch(fx):
    fx.efi().cmd_dpkg().cmd_uname().cmd_mokutil("disabled").satisfied_roles()
    fx.pci_gpu(vendor="0x1002", device="0x731f")  # AMD
    fx.modules("amdgpu 1 0 live\n")
    fx.default_manifest()
    proc, body = fx.json()
    assert proc.returncode == 11
    nvidia = [r for r in body["roles"] if r["id"] == "nvidia"][0]
    assert nvidia["status"] == "fail"
    assert nvidia["reason"] == "gpu_mismatch"
    assert body["gpu"]["display_vendor"] == "amd"


# ---------------------------------------------------------------------------
# Secure Boot
# ---------------------------------------------------------------------------

def test_secure_boot_goal_disabled_host_enabled(fx):
    fx.efi().cmd_dpkg().cmd_uname().satisfied_roles()
    fx.cmd_mokutil("enabled")
    fx.pci_gpu().modules("nvidia 1 1 live\n")
    fx.default_manifest()
    proc, body = fx.json()
    assert proc.returncode == 11
    assert body["secure_boot"]["state"] == "enabled"
    assert body["secure_boot"]["status"] == "fail"
    assert "secure_boot" in body["identity"]["violations"]


def test_secure_boot_host_unknown(fx):
    fx.efi().cmd_dpkg().cmd_uname().satisfied_roles()
    fx.cmd_mokutil("missing")
    fx.pci_gpu().modules("nvidia 1 1 live\n")
    fx.default_manifest()
    proc, body = fx.json()
    assert body["secure_boot"]["state"] == "unknown"
    assert body["secure_boot"]["status"] == "unknown"
    assert proc.returncode == 10


def test_secure_boot_goal_unknown_accepts_any(fx):
    fx.efi().cmd_dpkg().cmd_uname().satisfied_roles()
    fx.cmd_mokutil("enabled")
    fx.pci_gpu().modules("nvidia 1 1 live\n")
    fx.default_manifest().write_manifest([
        "distro.id=debian", "distro.version=13", "distro.codename=trixie",
        "distro.arch=amd64", "secure_boot=any",
        "role.id=xorg", "role.pkg=xserver-xorg",
    ])
    proc, body = fx.json()
    assert proc.returncode == 0
    assert body["secure_boot"]["state"] == "enabled"
    assert body["secure_boot"]["status"] == "ok"


# ---------------------------------------------------------------------------
# Tools: missing / failure
# ---------------------------------------------------------------------------

def test_missing_apt_cache_unknown_data(fx):
    fx.efi().cmd_dpkg().cmd_uname().cmd_mokutil("disabled")
    fx.cmd_apt_cache(present=False)
    fx.pci_gpu().modules("nvidia 1 1 live\n")
    fx.write_manifest([
        "distro.id=debian", "distro.version=13", "distro.codename=trixie",
        "distro.arch=amd64", "secure_boot=disabled",
        "role.id=pipewire", "role.pkg=pipewire",
    ])
    proc, body = fx.json()
    assert proc.returncode == 10
    assert body["roles"][0]["status"] == "unknown"


def test_command_failure_unknown_data(fx):
    fx.efi().cmd_dpkg().cmd_uname().satisfied_roles()
    fx.cmd_apt_cache(policy={"pipewire": {"installed": "0.3", "candidate": "0.3"}})
    fx.cmd_mokutil("disabled", fail=True)
    fx.pci_gpu().modules("nvidia 1 1 live\n")
    fx.write_manifest([
        "distro.id=debian", "distro.version=13", "distro.codename=trixie",
        "distro.arch=amd64", "secure_boot=disabled",
        "role.id=pipewire", "role.bin=pipewire", "role.pkg=pipewire",
    ])
    fx.cmd_binary("pipewire")
    proc, body = fx.json()
    assert proc.returncode == 10
    assert body["secure_boot"]["state"] == "unknown"


def test_legacy_bios_secure_boot_unknown(fx):
    fx.efi(False).cmd_dpkg().cmd_uname().satisfied_roles()
    fx.pci_gpu().modules("nvidia 1 1 live\n")
    fx.default_manifest()
    proc, body = fx.json()
    assert body["identity"]["boot_mode"] == "legacy"
    assert proc.returncode == 10


# ---------------------------------------------------------------------------
# Repositories / packages / sanitization
# ---------------------------------------------------------------------------

def test_third_party_and_official_repos(fx):
    fx.efi().cmd_dpkg().cmd_uname().cmd_mokutil("disabled").satisfied_roles()
    fx.apt_sources(
        ["deb http://deb.debian.org/debian trixie main non-free",
         "deb http://security.debian.org/debian-security trixie-security main"],
        sources_d=[
            "deb http://archive.ubuntu.com/ubuntu jammy main universe",
            "deb http://evil.example-co-uk.com/repo custom unstable contrib",
        ])
    fx.default_manifest()
    body = fx.json()[1]
    assert body["apt"]["sources_count"] == 4
    assert body["apt"]["official_components"]
    assert "main" in body["apt"]["official_components"]
    assert body["apt"]["has_third_party"] is True
    assert body["apt"]["third_party_count"] >= 1
    assert "custom" in body["apt"]["third_party_suites"]


def test_sanitization_no_hostname_secret_leak(fx):
    secret_host = "k3y.example-co-uk.com"
    faux_token = "LRPSECRETSUPERSECRETVALUE"
    fx.efi().cmd_dpkg().cmd_uname().cmd_mokutil("disabled").satisfied_roles()
    fx.apt_sources(
        ["deb http://user:p4ssw0rd@" + secret_host + "/repo trixie main"])
    fx.os_release(("ID=debian", 'VERSION_ID="13"', "VERSION_CODENAME=trixie"))
    fx.write_manifest([
        "distro.id=debian", "distro.version=13", "distro.codename=trixie",
        "distro.arch=amd64", "secure_boot=disabled",
        "role.id=ufw", "role.pkg=ufw",
    ])
    fx.cmd_apt_cache({"ufw": {"installed": "0.36", "candidate": "0.37"}})
    proc = fx.run()
    body = json.loads(proc.stdout[proc.stdout.index("{"):])
    # raw output must never expose the hostname nor the embedded credentials.
    assert secret_host not in proc.stdout
    assert secret_host not in json.dumps(body)
    assert "p4ssw0rd" not in proc.stdout
    assert "user:" not in json.dumps(body["apt"])
    assert "://" not in json.dumps(body["apt"])
    assert faux_token not in proc.stdout
    assert body["apt"]["has_third_party"] is True


def test_deb822_official_and_third_party_in_one_stanza(fx):
    fx.efi().cmd_dpkg().cmd_uname().cmd_mokutil("disabled").satisfied_roles()
    fx.pci_gpu().modules("nvidia 1 1 live\n")
    fx.apt_sources_deb822(
        "Types: deb\n"
        "URIs: http://deb.debian.org/debian http://evil.example-co-uk.com/repo\n"
        "Suites: trixie\n"
        "Components: main\n")
    fx.default_manifest()
    proc, body = fx.json()
    apt = body["apt"]
    assert proc.returncode == 0
    assert apt["sources_count"] == 2          # 2 URIs x 1 suite
    assert apt["has_third_party"] is True
    assert apt["third_party_count"] == 1
    assert "main" in apt["official_components"]
    assert "trixie" in apt["third_party_suites"]
    # no raw URI / credential / host text may leak
    assert "://" not in json.dumps(apt)
    assert "example-co-uk.com" not in json.dumps(apt)


def test_deb822_multiple_suites_and_components(fx):
    fx.efi().cmd_dpkg().cmd_uname().cmd_mokutil("disabled").satisfied_roles()
    fx.pci_gpu().modules("nvidia 1 1 live\n")
    fx.apt_sources_deb822(
        "Types: deb\n"
        "URIs: https://deb.debian.org/debian https://evil.example-co-uk.com/apt\n"
        "Suites: trixie trixie-updates\n"
        "Components: main contrib non-free\n")
    fx.default_manifest()
    body = fx.json()[1]
    apt = body["apt"]
    assert apt["sources_count"] == 4          # 2 URIs x 2 suites
    assert apt["third_party_count"] == 2      # every (evil-host, suite) pair
    assert apt["has_third_party"] is True
    assert set(apt["official_components"].split(",")) == {
        "main", "contrib", "non-free"}
    assert "trixie" in apt["third_party_suites"]
    assert "trixie-updates" in apt["third_party_suites"]


def test_deb822_credentials_are_sanitized(fx):
    fx.efi().cmd_dpkg().cmd_uname().cmd_mokutil("disabled").satisfied_roles()
    fx.pci_gpu().modules("nvidia 1 1 live\n")
    fx.apt_sources_deb822(
        "Types: deb\n"
        "URIs: http://deploy:SuPeRsEcReTaRepO@mirror.example-co-uk.com/debian-tv\n"
        "Suites: unstable\n"
        "Components: main\n\n"
        "Types: deb\n"
        "URIs: https://deb.debian.org/debian\n"
        "Suites: trixie\n"
        "Components: main\n")
    fx.default_manifest()
    proc = fx.run()
    body = json.loads(proc.stdout[proc.stdout.index("{"):])
    apt = body["apt"]
    raw = proc.stdout
    assert apt["has_third_party"] is True
    assert apt["third_party_count"] == 1
    assert apt["sources_count"] == 2
    assert "SuPeRsEcReTaRepO" not in raw
    assert "deploy:" not in raw
    assert "mirror.example-co-uk.com" not in raw
    assert "://" not in json.dumps(apt)
    assert "unstable" in apt["third_party_suites"]


def test_deb822_deterministic_counts_and_detection(fx):
    fx.efi().cmd_dpkg().cmd_uname().cmd_mokutil("disabled").satisfied_roles()
    fx.pci_gpu().modules("nvidia 1 1 live\n")
    # Mixed stanzas: two stanzas, one official-only and one with a hidden
    # third-party URI behind several suites, plus a standalone official stanza.
    fx.apt_sources_deb822(
        "Types: deb\n"
        "URIs: https://deb.debian.org/debian https://security.debian.org/debian-security\n"
        "Suites: trixie trixie-security\n"
        "Components: main\n\n"
        "Types: deb\n"
        "URIs: https://deb.debian.org/debian https://c2.example-co-uk.com/stage\n"
        "Suites: trixie trixie-updates trixie-backports\n"
        "Components: main non-free-firmware\n")
    fx.default_manifest()
    body = fx.json()[1]
    apt = body["apt"]
    # stanza1: 2 uris x 2 suites = 4 entries, all official.
    # stanza2: 2 uris x 3 suites = 6 entries; the 3 (third-party host, suite)
    #          pairs are third-party, the other 3 are official.
    assert apt["sources_count"] == 10
    assert apt["third_party_count"] == 3
    assert apt["has_third_party"] is True
    assert "non-free-firmware" in apt["official_components"].split(",")
    assert set(apt["third_party_suites"].split(",")) == {
        "trixie", "trixie-updates", "trixie-backports"}


def test_explicit_package_candidate_handling(fx):
    fx.efi().cmd_dpkg().cmd_uname().cmd_mokutil("disabled")
    fx.cmd_apt_cache({
        "resolvable": {"installed": None, "candidate": "1.0"},
        "feebie": {"installed": "1.0", "candidate": "1.0"},
        "ghost": {"installed": None, "candidate": None},
    })
    fx.write_manifest([
        "distro.id=debian", "distro.version=13", "distro.codename=trixie",
        "distro.arch=amd64", "secure_boot=disabled",
        "role.id=r1", "role.pkg=resolvable,feebie",
        "role.id=r2", "role.pkg=ghost",
    ])
    proc, body = fx.json()
    assert proc.returncode == 11
    r1 = [r for r in body["roles"] if r["id"] == "r1"][0]
    r2 = [r for r in body["roles"] if r["id"] == "r2"][0]
    assert r1["status"] == "missing"
    assert r2["status"] == "fail"
    # explicit package names surfaced with candidate/installed data
    assert r1["packages"]["resolvable"]["candidate"] is True
    assert r1["packages"]["resolvable"]["installed"] is False
    assert r1["packages"]["feebie"]["installed"] is True
    assert r2["packages"]["ghost"]["candidate"] is False


def test_role_without_explicit_inputs_is_unresolved(fx):
    fx.efi().cmd_dpkg().cmd_uname().cmd_mokutil("disabled")
    fx.write_manifest([
        "distro.id=debian", "distro.version=13", "distro.codename=trixie",
        "distro.arch=amd64", "secure_boot=disabled",
        "role.id=mystery",
    ])
    proc, body = fx.json()
    assert proc.returncode == 10
    assert body["roles"][0]["status"] == "unresolved"
    assert body["summary"]["roles_unresolved"] == 1


def test_apt_cache_c_locale_is_scoped(fx):
    # The apt-cache stub only yields candidate data when LC_ALL=C is set. If
    # the probe failed to scope the locale, this returns no data -> unknown.
    fx.efi().cmd_dpkg().cmd_uname().cmd_mokutil("disabled")
    fx.cmd_apt_cache_raw(
        '#!/bin/sh\n'
        'if [ "$LC_ALL" = "C" ] && [ "$1" = policy ]; then\n'
        'case "$2" in\n'
        '  pipewire) echo "pipewire:"; echo "  Installed: 1.0.3"; '
        'echo "  Candidate: 1.0.4";;\n'
        'esac\nfi\n')
    fx.cmd_binary("pipewire")
    fx.write_manifest([
        "distro.id=debian", "distro.version=13", "distro.codename=trixie",
        "distro.arch=amd64", "secure_boot=disabled",
        "role.id=pipewire", "role.bin=pipewire", "role.pkg=pipewire",
    ])
    proc, body = fx.json()
    assert proc.returncode == 0, body["summary"]
    r = body["roles"][0]
    assert r["status"] == "ok"
    assert r["packages"]["pipewire"]["installed"] is True
    assert r["packages"]["pipewire"]["candidate"] is True


def test_apt_cache_spanish_locale_output_keeps_semantics(fx):
    # Simulates a host whose apt-cache output is localized (Spanish labels).
    # Candidate/installed semantics must be preserved: installed/ok, available
    # but uninstalled/missing, and unavailable/fail.
    fx.efi().cmd_dpkg().cmd_uname().cmd_mokutil("disabled")
    fx.cmd_apt_cache_raw(
        '#!/bin/sh\n'
        'if [ "$1" = policy ]; then\n'
        'case "$2" in\n'
        '  ufw) echo "ufw:"; echo "  Instalado: 0.36"; echo "  Candidato: 0.37";;\n'
        '  resolv) echo "resolv:"; echo "  Instalado: (none)"; echo "  Candidato: 1.2";;\n'
        '  ghost) echo "ghost:"; echo "  Instalado: (none)"; echo "  Candidato: (none)";;\n'
        'esac\nfi\n')
    fx.cmd_binary("ufw")
    fx.write_manifest([
        "distro.id=debian", "distro.version=13", "distro.codename=trixie",
        "distro.arch=amd64", "secure_boot=disabled",
        "role.id=rfx", "role.bin=ufw", "role.pkg=ufw",
        "role.id=rmiss", "role.pkg=resolv",
        "role.id=rfail", "role.pkg=ghost",
    ])
    proc, body = fx.json()
    roles = {r["id"]: r for r in body["roles"]}
    assert roles["rfx"]["status"] == "ok"
    assert roles["rfx"]["packages"]["ufw"]["installed"] is True
    assert roles["rmiss"]["status"] == "missing"
    assert roles["rmiss"]["packages"]["resolv"]["candidate"] is True
    assert roles["rmiss"]["packages"]["resolv"]["installed"] is False
    assert roles["rfail"]["status"] == "fail"
    assert roles["rfail"]["packages"]["ghost"]["candidate"] is False
    # a real failed requirement exists -> exit 11, no false success
    assert proc.returncode == 11


# ---------------------------------------------------------------------------
# Contract / exit codes
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("argv", ["--manifest /does/not/exist",
                                  "--manifest", "--bogus-flag"])
def test_invalid_contract_exit_12(fx, argv):
    fx.write_manifest(["distro.id=debian"])
    proc = fx.run(argv=argv)
    assert proc.returncode == 12
    body = json.loads(proc.stdout[proc.stdout.index("{"):])
    assert body["contract_valid"] is False
    assert body["summary"]["exit_code"] == 12


def test_json_schema_and_single_document(fx):
    fx.efi().pci_gpu().modules("nvidia 1 1 live\n")
    fx.apt_sources(["deb http://deb.debian.org/debian trixie main"])
    fx.cmd_uname().cmd_dpkg().cmd_mokutil("disabled")
    fx.satisfied_roles().default_manifest()
    proc = fx.run()
    stdout = proc.stdout.strip()
    assert stdout.startswith("{")
    assert stdout.endswith("}")
    assert stdout.count("{") == stdout.count("}")
    assert stdout.count("\n{") == 0, "more than one top-level JSON object"
    top = json.loads(stdout)
    for key in ("tool", "schema", "contract_valid", "identity",
                "secure_boot", "gpu", "modules", "apt", "rollback", "roles",
                "summary"):
        assert key in top
    for key in ("id", "version_id", "codename", "architecture", "kernel",
                "boot_mode", "result", "violations"):
        assert key in top["identity"]
    assert top["rollback"] == "none"
    assert top["summary"]["exit_code"] == 0
    assert set(top["summary"]) >= {"result", "roles_ok", "roles_missing",
                                   "roles_fail", "roles_unknown",
                                   "roles_unresolved", "exit_code"}


# ---------------------------------------------------------------------------
# Static source checks
# ---------------------------------------------------------------------------

def _code_only():
    """Return the preflight source with comment lines removed."""
    source = PREFLIGHT.read_text(encoding="utf-8")
    return "\n".join(line for line in source.splitlines()
                     if not line.lstrip().startswith("#"))


def test_static_no_forbidden_mutating_commands():
    lower = _code_only().lower()
    for token in FORBIDDEN_MUTATORS:
        assert token.lower() not in lower, \
            "forbidden mutating invocation present: {0}".format(token)


def test_static_no_write_operations():
    source = PREFLIGHT.read_text(encoding="utf-8")
    for token in ("rm -rf", "rm -", "sed -i", "tee ", "touch ",
                  "> /etc/", ">>", "mv ", "cp ", "install -", "echo >",
                  "cat >", "chmod ", "chown ", "usermod ", "groupadd"):
        assert token not in source, "write/privilege operation present: {0}".format(token)


def test_static_never_reads_secret_files():
    source = PREFLIGHT.read_text(encoding="utf-8")
    lower = source.lower()
    for token in (".env", "pairing_token", "/etc/passwd", "/etc/shadow",
                  "machine-id", ".ssh", "/home/", "api_key", ".pki/nssdb"):
        assert token not in lower, "sensitive artifact accessed: {0}".format(token)


def test_static_no_hostname_username_capture():
    source = PREFLIGHT.read_text(encoding="utf-8")
    lower = source.lower()
    # command-invocation forms only (the word may appear in a policy comment)
    for token in ("hostname ", "hostname)", "whoami", "getent", "logname",
                  "/etc/hosts", "/proc/sys/kernel/hostname"):
        assert token not in lower, "identity-capture operation present: {0}".format(token)


def test_static_emits_exit_mapping():
    code = _code_only()
    for token in ("exit 12", "exit_code=10", "exit_code=11", "exit_code=12",
                  "exit \"$exit_code\""):
        assert token in code, "missing exit mapping: {0}".format(token)
    assert "rollback" in code
    assert "\"none\"" in code


# ---------------------------------------------------------------------------
# T-122 required artifacts (durable invariants)
# ---------------------------------------------------------------------------
# Note: exact write-set equality is an audit-time gate (an engineer verifies the
# delivered diff), not a persistent product invariant. Later tasks legitimately
# add other files, so these tests assert only the artifacts T-122 owns: the
# required two files exist with the correct shell contract. They never inspect
# the repository's global untracked state.

def test_t122_required_artifacts_exist():
    assert PREFLIGHT.is_file(), "preflight script missing"
    assert (ROOT / "tests" / "test_debian_preflight.py").is_file(), \
        "T-122 test file missing"


def test_preflight_path_and_shell_contract():
    # Name and location contract.
    assert PREFLIGHT.name == "preflight.sh"
    assert PREFLIGHT.parent == ROOT / "scripts" / "debian"
    # Executable shell contract: the script declares itself a bash program via
    # its shebang. (POSIX exec bits are not reliably reported on a Windows
    # checkout, so the shebang is the durable, cross-platform contract.)
    first = PREFLIGHT.open(encoding="utf-8").readline().rstrip("\r\n")
    assert first == "#!/bin/bash", \
        "preflight must declare an executable bash shebang, got: {0!r}".format(first)
