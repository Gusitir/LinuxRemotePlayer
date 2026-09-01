import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
UNINSTALL = (ROOT / "scripts/uninstall.sh").read_text(encoding="utf-8")
CLEANUP = (ROOT / "scripts/lrp-cleanup.sh").read_text(encoding="utf-8")
BUILDER = (ROOT / "scripts/build_deb.sh").read_text(encoding="utf-8")


def _find_bash():
    if os.name == "nt":
        candidate = Path("C:/Program Files/Git/bin/bash.exe")
        if candidate.exists():
            return str(candidate)
    return shutil.which("bash") or ("/bin/bash" if os.name != "nt" else str(candidate))


BASH = _find_bash()


def _msys(path):
    text = str(path).replace("\\", "/")
    if os.name != "nt":
        return str(Path(path).resolve())
    drive, rest = text.split(":", 1)
    return "/" + drive.lower() + rest



def test_uninstall_defaults_to_dry_run_and_lists_retained_data():
    assert "MODE=dry-run" in UNINSTALL
    assert "would_do" in UNINSTALL and "retained" in UNINSTALL
    assert "--apply --approve" in UNINSTALL
    assert "backend/.env" in UNINSTALL and "backend/.pairing_token" in UNINSTALL


def test_uninstall_requires_root_and_approval_for_mutation():
    assert "APPROVE" in UNINSTALL and "root_required" in UNINSTALL
    assert "approval_required" in UNINSTALL


def test_uninstall_orders_platform_then_session_and_daemon_reload():
    assert UNINSTALL.index('"$PLATFORM" --rollback --approve') < UNINSTALL.index('"$SESSION" --rollback --approve')
    assert "systemctl daemon-reload" in UNINSTALL
    assert '"$PLATFORM" --rollback --approve --strict' in UNINSTALL


def test_uninstall_skips_missing_states():
    assert "[ ! -f \"$PLATFORM_STATE\" ]" in UNINSTALL
    assert "[ ! -f \"$SESSION_STATE\" ]" in UNINSTALL


def test_uninstall_has_strict_failure_paths():
    assert "|| exit 11" in UNINSTALL
    assert "|| true" not in UNINSTALL


def test_cleanup_is_noninteractive_strict_or_package_best_effort():
    assert "set +e" in CLEANUP
    assert "--strict" in CLEANUP
    assert '[ "$STRICT" = 1 ] && exit "$rc"' in CLEANUP
    assert "exit 0" in CLEANUP
    assert 'extra=--strict' in CLEANUP


def test_cleanup_orders_owned_rollbacks_and_never_removes_data():
    assert CLEANUP.index('rollback "$PLATFORM"') < CLEANUP.index('rollback "$SESSION"')
    for forbidden in ("rm -rf", "backend/.env", "backend/.pairing_token", "backend/certs"):
        assert forbidden not in CLEANUP


def test_cleanup_removes_only_system_unit_and_reloads_daemon():
    assert 'rm -f "$ROOT/etc/systemd/system/linuxremoteplayer.service"' in CLEANUP
    assert "systemctl daemon-reload" in CLEANUP


def test_prerm_calls_cleanup_only_on_remove():
    prerm = BUILDER[BUILDER.index("cat <<'EOF' > pkg/DEBIAN/prerm"):]
    assert 'if [ "$1" = "remove" ]; then' in prerm
    assert "/opt/linuxremoteplayer/scripts/lrp-cleanup.sh" in prerm
    assert 'if [ "$1" = "upgrade" ]; then' not in prerm


def test_prerm_preserves_main_exit_guards_and_no_user_unit_fallback():
    prerm = BUILDER[BUILDER.index("cat <<'EOF' > pkg/DEBIAN/prerm"):]
    assert "systemctl --user" not in prerm
    assert "systemctl stop linuxremoteplayer.service" in prerm
    assert "update-desktop-database" in prerm


def test_uninstall_does_not_remove_packages_user_or_opt_data():
    for forbidden in ("apt-get remove", "userdel", "rm -rf", "rm -r /opt", "rm -rf /opt"):
        assert forbidden not in UNINSTALL
    assert "lrp user/home" in UNINSTALL


def test_repeat_safe_state_gated_rollback():
    assert "[ ! -f \"$PLATFORM_STATE\" ] ||" in UNINSTALL
    assert "[ ! -f \"$SESSION_STATE\" ] ||" in UNINSTALL
    assert "[ -f \"$SERVICE\" ]" in UNINSTALL


# ---------------------------------------------------------------------------
# Root gating + dry-run enumeration (fixture, executes the real script)
# ---------------------------------------------------------------------------

def test_uninstall_root_gate_precedes_apply_branch():
    # EUID 0 is required for dry-run AND apply immediately after args; approval
    # stays apply-only and must appear after the root gate.
    root_gate = UNINSTALL.index("root_required")
    approval = UNINSTALL.index("approval_required")
    apply_branch = UNINSTALL.index('if [ "$MODE" = apply ]')
    assert root_gate < approval < apply_branch

@pytest.fixture
def fake_root(tmp_path):
    """Fake LRP_ROOT carrying the protected-state markers dry-run enumerates."""
    svc = tmp_path / "etc/systemd/system/linuxremoteplayer.service"
    plt = tmp_path / "var/lib/linuxremoteplayer/platform/state"
    ses = tmp_path / "var/lib/linuxremoteplayer/session/state"
    svc.parent.mkdir(parents=True, exist_ok=True)
    plt.parent.mkdir(parents=True, exist_ok=True)
    ses.parent.mkdir(parents=True, exist_ok=True)
    svc.write_text("[Unit]\n", encoding="utf-8")
    plt.write_text("rollback\n", encoding="utf-8")
    ses.write_text("rollback\n", encoding="utf-8")
    return tmp_path


def _run_uninstall(root, elevated):
    """Run the real uninstall script against a fake root; `elevated` simulates EUID 0
    in the test-only copy (needed to reach dry-run enumeration without real root)."""
    script_text = UNINSTALL.replace("${EUID:-1}", "0") if elevated else UNINSTALL
    script = root / "_uninstall.sh"
    script.write_text(script_text, encoding="utf-8")
    env = dict(os.environ)
    env["LRP_ROOT"] = _msys(root)
    return subprocess.run([BASH, _msys(script), "--dry-run"],
                          env=env, capture_output=True, text=True)


def test_nonroot_dry_run_is_rejected(fake_root):
    proc = _run_uninstall(fake_root, elevated=False)
    assert proc.returncode == 12, proc.stdout + proc.stderr
    body = json.loads(proc.stdout[proc.stdout.index("{"):])
    assert body["contract_valid"] is False
    assert body["reason"] == "root_required"


def test_root_dry_run_enumerates_protected_state(fake_root):
    proc = _run_uninstall(fake_root, elevated=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    body = json.loads(proc.stdout[proc.stdout.index("{"):])
    assert body["mode"] == "dry-run"
    for action in ("stop_disable_remove_system_unit", "platform_rollback",
                   "session_rollback", "daemon_reload"):
        assert action in body["would_do"], body["would_do"]
    retained = ", ".join(body["retained"])
    assert "backend/.env" in retained and "backend/.pairing_token" in retained
