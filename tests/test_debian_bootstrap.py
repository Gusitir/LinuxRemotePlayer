import os
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "debian" / "bootstrap.sh"


def test_bootstrap_is_rooted_and_has_resumable_phase_contract():
    source = SCRIPT.read_text(encoding="utf-8")
    assert '[ "${EUID:-1}" = 0 ]' in source
    assert 'MODE=apply' in source and '--resume' in source
    assert 'state_phase()' in source
    assert '"$phase" = complete' in source
    assert 'phase" = reboot_required' in source
    assert 'Re-run: sudo /opt/linuxremoteplayer/scripts/debian/bootstrap.sh --resume' in source
    assert 'exec "$BASE/../install.sh"' in source


def test_bootstrap_matrix_preserves_child_codes_and_never_reboots():
    source = SCRIPT.read_text(encoding="utf-8")
    for code in ("10", "11", "12", "20"):
        assert code in source
    assert "systemctl reboot" in source
    assert 'run_phase nvidia "$BASE/nvidia-bootstrap.sh"' in source
    assert 'run_phase session "$BASE/session-bootstrap.sh"' in source


def test_bootstrap_matrix_cases_are_encoded():
    source = SCRIPT.read_text(encoding="utf-8")
    cases = {
        "fresh_apply": '"$script" --apply --approve',
        "nvidia_resume": '"$script" --resume',
        "resume_fresh_nvidia": '[ "$MODE" = resume ] && [ "$name" = nvidia ]',
        "failure_propagation": 'return "$rc"',
        "complete_idempotent": '[ "$phase" = complete ] && return 0',
    }
    for name, contract in cases.items():
        assert contract in source, name


def test_bootstrap_is_executable_entrypoint():
    assert SCRIPT.is_file()
    build = (ROOT / "scripts/build_deb.sh").read_text(encoding="utf-8")
    assert "/opt/linuxremoteplayer/scripts/debian/bootstrap.sh --resume --unattended" in build


def test_unattended_bootstrap_unit_and_reboot_budget_are_explicit():
    source = SCRIPT.read_text(encoding="utf-8")
    for phrase in (
        "--unattended", "reboots=", "-gt 2", "systemctl reboot",
        "WantedBy=multi-user.target", "After=network-online.target display-manager.service",
        "ExecStart=/opt/linuxremoteplayer/scripts/debian/bootstrap.sh --resume --unattended",
        "LRP_NONINTERACTIVE=1 \"$BASE/../install.sh\"",
    ):
        assert phrase in source
    assert "systemctl disable linuxremoteplayer-bootstrap.service" in source
    assert "rm -f \"$UNATTENDED_STATE\"" in source
    assert "health_ready" in source
    assert "LRP_NONINTERACTIVE=1 \"$BASE/../install.sh\"" in source


def _fixture():
    directory = Path(tempfile.mkdtemp())
    debian = directory / "scripts/debian"
    debian.mkdir(parents=True)
    commands = directory / "commands"
    commands.mkdir()
    source = SCRIPT.read_text(encoding="utf-8").replace(
        '[ "${EUID:-1}" = 0 ] || { printf \'%s\\n\' root_required >&2; exit 12; }',
        "true",
    )
    wrapper = debian / "bootstrap.sh"
    wrapper.write_bytes(source.encode("utf-8"))
    child = """#!/bin/bash
set -u
root="${LRP_ROOT:?}"; state="$root/var/lib/linuxremoteplayer/STATE_DIR/state"
mkdir -p "$(dirname "$state")"
phase=
[ -f "$state" ] && phase=$(sed -n 's/^phase=//p' "$state")
printf '%s %s\n' KIND "${1:-}" >> "$root/calls"
if [ "$1" = --apply ]; then printf 'phase=reboot_required\n' > "$state"; exit 20; fi
if [ "$1" = --resume ]; then printf 'phase=complete\n' > "$state"; exit 0; fi
exit 11
"""
    for name in ("nvidia-bootstrap.sh", "session-bootstrap.sh"):
        path = debian / name
        kind = name.split("-")[0]
        state_dir = "bootstrap" if kind == "nvidia" else "session"
        path.write_bytes(child.replace("KIND", kind).replace("STATE_DIR", state_dir).encode("utf-8"))
        path.chmod(0o755)
    install = directory / "scripts/install.sh"
    install.write_bytes(b"#!/bin/bash\nprintf installed > \"${LRP_ROOT}/installed\"\n")
    install.chmod(0o755)
    for name, body in {
        "systemctl": '#!/bin/sh\necho "systemctl $*" >> "$LRP_ROOT/reboots"\n[ "$1" = enable ] && [ "${LRP_FAIL_ENABLE:-0}" = 1 ] && exit 1\nexit 0\n',
        "pgrep": "#!/bin/sh\nexit 0\n",
        "curl": "#!/bin/sh\nexit 0\n",
        "sleep": "#!/bin/sh\nexit 0\n",
    }.items():
        stub = commands / name
        stub.write_bytes(body.encode("utf-8"))
        stub.chmod(0o755)
    wrapper.chmod(0o755)
    bash = shutil.which("bash")
    if not bash:
        raise RuntimeError("bash unavailable")
    return directory, wrapper, bash, commands


def _run(directory, wrapper, bash, commands, *args):
    env = os.environ.copy()
    root = directory.as_posix()
    script = wrapper.as_posix()
    if os.name == "nt":
        drive = directory.drive.rstrip(":").lower()
        root = f"/mnt/{drive}{root[2:]}"
        script = f"/mnt/{drive}{script[2:]}"
    env["LRP_ROOT"] = root
    command_path = commands.as_posix()
    if os.name == "nt":
        drive = commands.drive.rstrip(":").lower()
        command_path = f"/mnt/{drive}{command_path[2:]}"
    env["PATH"] = command_path + ":" + env.get("PATH", "")
    command = "export LRP_ROOT=%s; export PATH=%s:\"$PATH\"; exec %s %s" % (
        shlex.quote(root), shlex.quote(command_path), shlex.quote(script), " ".join(shlex.quote(arg) for arg in args)
    )
    return subprocess.run(
        [bash, "-c", command],
        env=env, capture_output=True, text=True,
    )


def test_fixture_full_resume_sequence_and_idempotence():
    directory, wrapper, bash, commands = _fixture()
    try:
        result = _run(directory, wrapper, bash, commands, "--resume")
        assert result.returncode == 12, result.stderr
        assert _run(directory, wrapper, bash, commands, "--apply", "--approve", "--unattended").returncode == 0
        assert _run(directory, wrapper, bash, commands, "--resume", "--unattended").returncode == 0
        assert _run(directory, wrapper, bash, commands, "--resume", "--unattended").returncode == 0
        assert (directory / "installed").read_text() == "installed"
        assert not (directory / "etc/systemd/system/linuxremoteplayer-bootstrap.service").exists()
        assert not (directory / "var/lib/linuxremoteplayer/unattended").exists()
        assert (directory / "calls").read_text().splitlines() == [
            "nvidia --apply", "nvidia --resume", "session --apply", "session --resume"
        ]
        assert (directory / "reboots").read_text().count("systemctl reboot") == 2
    finally:
        shutil.rmtree(directory)


def test_fixture_failure_propagates_without_install():
    directory, wrapper, bash, commands = _fixture()
    try:
        nvidia = directory / "scripts/debian/nvidia-bootstrap.sh"
        nvidia.write_bytes(b"#!/bin/bash\nexit 11\n")
        assert _run(directory, wrapper, bash, commands, "--apply", "--approve", "--unattended").returncode == 11
        assert not (directory / "installed").exists()
    finally:
        shutil.rmtree(directory)


def test_unattended_third_reboot_request_fails_without_reboot():
    directory, wrapper, bash, commands = _fixture()
    try:
        state = directory / "var/lib/linuxremoteplayer/unattended/state"
        state.parent.mkdir(parents=True)
        state.write_bytes(b"status=reboot_required\nreboots=2\n")
        result = _run(directory, wrapper, bash, commands, "--apply", "--approve", "--unattended")
        assert result.returncode == 11
        assert "systemctl reboot" not in (directory / "reboots").read_text()
        assert not (directory / "etc/systemd/system/linuxremoteplayer-bootstrap.service").exists()
    finally:
        shutil.rmtree(directory)
