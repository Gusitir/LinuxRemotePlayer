import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
def _find_bash():
    if os.name == "nt":
        candidate = Path("C:/Program Files/Git/bin/bash.exe")
        if candidate.exists():
            return str(candidate)
    return shutil.which("bash") or ("/bin/bash" if os.name != "nt" else str(candidate))


BASH = _find_bash()
INSTALLER = (ROOT / "scripts" / "install.sh").read_text()
BUILDER = (ROOT / "scripts" / "build_deb.sh").read_text()


def test_installer_requires_the_existing_lrp_identity():
    assert 'TARGET_USER="lrp"' in INSTALLER
    assert 'getent passwd "$TARGET_USER"' in INSTALLER
    assert 'USER_UID" = "0"' in INSTALLER
    assert 'USER_HOME" != "/home/lrp"' in INSTALLER
    assert 'USER_SHELL" != "/bin/bash"' in INSTALLER
    assert "useradd" not in INSTALLER


def test_installer_never_prompts_or_selects_a_different_user():
    assert "PROMPT_USER" not in INSTALLER
    assert 'read -p "Que usuario' not in INSTALLER
    assert "logname" not in INSTALLER
    assert "loginctl" not in INSTALLER
    assert 'TARGET_USER="$SUDO_USER"' not in INSTALLER
    assert 'TARGET_USER="lrp"' in INSTALLER


def test_passwd_mapping_behavior_accepts_valid_lrp_and_rejects_uid_zero():
    validation = r'''
TARGET_USER="lrp"
USER_RECORD=$(getent passwd "$TARGET_USER")
IFS=: read -r _ _ USER_UID _ _ USER_HOME USER_SHELL <<EOF
$USER_RECORD
EOF
if [ "$USER_UID" = "0" ] || [ "$USER_HOME" != "/home/lrp" ] || [ "$USER_SHELL" != "/bin/bash" ]; then
    exit 1
fi
'''
    valid = subprocess.run(
        [BASH, "-c", 'getent() { printf "%s\\n" "lrp:x:1001:1001::/home/lrp:/bin/bash"; }; ' + validation],
        capture_output=True,
    )
    root = subprocess.run(
        [BASH, "-c", 'getent() { printf "%s\\n" "lrp:x:0:0::/home/lrp:/bin/bash"; }; ' + validation],
        capture_output=True,
    )
    assert valid.returncode == 0
    assert root.returncode == 1
    assert 'IFS=: read -r _ _ USER_UID _ _ USER_HOME USER_SHELL' in INSTALLER


def test_installer_does_not_write_mode_assignments():
    mode_var = "LRP" + "_MODE"
    assert mode_var not in INSTALLER


def test_installer_does_not_expose_pairing_token_in_display_output():
    assert "TOKEN_FILE" not in INSTALLER
    assert 'TOKEN="guest"' not in INSTALLER
    assert "?token=" not in INSTALLER
    assert "Escribe el PIN que muestra el panel en tu TV." in INSTALLER
    assert "Introduce el PIN que muestra el panel en tu TV para emparejar." in INSTALLER
    assert "os.chmod(token_file, 0o600)" in INSTALLER


def test_installer_generates_one_system_unit_with_required_dependencies():
    unit = INSTALLER[INSTALLER.index("cat <<EOF > /etc/systemd/system/linuxremoteplayer.service"):]
    assert "User=lrp" in unit
    assert "Wants=network-online.target" in unit
    assert "After=display-manager.service network-online.target" in unit
    assert "WantedBy=graphical.target" in unit
    assert INSTALLER.count("/etc/systemd/system/linuxremoteplayer.service") == 1


def test_installer_removes_the_lrp_legacy_user_unit_before_starting_system_unit():
    legacy = INSTALLER.index("cleanup_legacy_user_unit()")
    service = INSTALLER.index("cat <<EOF > /etc/systemd/system/linuxremoteplayer.service")
    block = INSTALLER[legacy:service]
    assert 'legacy_record=$(getent passwd "$legacy_user"' in block
    assert 'legacy_unit="$legacy_home/.config/systemd/user/linuxremoteplayer.service"' in block
    assert 'systemctl --user stop linuxremoteplayer.service' in block
    assert 'systemctl --user disable linuxremoteplayer.service' in block
    assert 'rm -f "$legacy_unit"' in block
    assert 'cleanup_legacy_user_unit "$TARGET_USER"' in block
    assert 'cleanup_legacy_user_unit "$SUDO_USER"' in block
    assert '"$SUDO_USER" != "$TARGET_USER"' in block
    assert INSTALLER.index("systemctl daemon-reload") > service


def test_installer_uses_system_lifecycle_only():
    assert "systemctl daemon-reload" in INSTALLER
    assert "systemctl enable linuxremoteplayer.service" in INSTALLER
    assert "systemctl restart linuxremoteplayer.service" in INSTALLER
    assert 'systemctl --user daemon-reload' not in INSTALLER
    assert 'systemctl --user disable linuxremoteplayer.service' in INSTALLER  # legacy cleanup only


def test_package_prerm_has_no_user_service_lifecycle_and_preserves_guards():
    prerm = BUILDER[BUILDER.index("cat <<'EOF' > pkg/DEBIAN/prerm"):]
    assert "systemctl --user" not in prerm
    assert 'if [ "$1" = "remove" ]; then' in prerm
    assert "lrp-cleanup.sh" in prerm
    assert "systemctl stop linuxremoteplayer.service" in prerm
    assert "platform-bootstrap.sh" in INSTALLER
    assert "qdbus" not in INSTALLER
    assert "kbuildsycoca" not in INSTALLER
