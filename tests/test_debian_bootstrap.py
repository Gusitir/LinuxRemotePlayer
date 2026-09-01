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
    assert 'Re-run: sudo lrp-setup --resume' in source
    assert 'exec "$BASE/../install.sh"' in source


def test_bootstrap_matrix_preserves_child_codes_and_never_reboots():
    source = SCRIPT.read_text(encoding="utf-8")
    for code in ("10", "11", "12", "20"):
        assert code in source
    assert "systemctl reboot" not in source
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


def test_bootstrap_and_setup_wrapper_are_executable_entrypoints():
    assert SCRIPT.is_file()
    build = (ROOT / "scripts/build_deb.sh").read_text(encoding="utf-8")
    assert "exec ./debian/bootstrap.sh \"$@\"" in build


def _fixture():
    directory = Path(tempfile.mkdtemp())
    debian = directory / "scripts/debian"
    debian.mkdir(parents=True)
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
    wrapper.chmod(0o755)
    bash = shutil.which("bash")
    if not bash:
        raise RuntimeError("bash unavailable")
    return directory, wrapper, bash


def _run(directory, wrapper, bash, *args):
    env = os.environ.copy()
    root = directory.as_posix()
    script = wrapper.as_posix()
    if os.name == "nt":
        drive = directory.drive.rstrip(":").lower()
        root = f"/mnt/{drive}{root[2:]}"
        script = f"/mnt/{drive}{script[2:]}"
    env["LRP_ROOT"] = root
    command = "export LRP_ROOT=%s; exec %s %s" % (
        shlex.quote(root), shlex.quote(script), " ".join(shlex.quote(arg) for arg in args)
    )
    return subprocess.run(
        [bash, "-c", command],
        env=env, capture_output=True, text=True,
    )


def test_fixture_full_resume_sequence_and_idempotence():
    directory, wrapper, bash = _fixture()
    try:
        assert _run(directory, wrapper, bash, "--resume").returncode == 12
        assert _run(directory, wrapper, bash, "--apply", "--approve").returncode == 20
        assert _run(directory, wrapper, bash, "--resume").returncode == 20
        assert _run(directory, wrapper, bash, "--resume").returncode == 0
        assert (directory / "installed").read_text() == "installed"
        assert _run(directory, wrapper, bash, "--resume").returncode == 0
        assert (directory / "calls").read_text().splitlines() == [
            "nvidia --apply", "nvidia --resume", "session --apply", "session --resume"
        ]
    finally:
        shutil.rmtree(directory)


def test_fixture_failure_propagates_without_install():
    directory, wrapper, bash = _fixture()
    try:
        nvidia = directory / "scripts/debian/nvidia-bootstrap.sh"
        nvidia.write_bytes(b"#!/bin/bash\nexit 11\n")
        assert _run(directory, wrapper, bash, "--apply", "--approve").returncode == 11
        assert not (directory / "installed").exists()
    finally:
        shutil.rmtree(directory)
