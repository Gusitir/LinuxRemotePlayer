import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).parents[1]
BUILD = ROOT / "scripts" / "build_deb.sh"
INSTALLER = ROOT / "website" / "beta" / "install.sh"


def test_beta_manifest_template_is_not_live_manifest():
    template_path = ROOT / "website" / "beta" / "latest.template.json"
    fixture_path = ROOT / "tests" / "fixtures" / "beta-manifest.json"
    template = json.loads(template_path.read_text())
    fixture = json.loads(fixture_path.read_text())
    assert "__BETA_VERSION__" in template["version"]
    assert fixture["version"] != "__BETA_VERSION__"
    assert re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", fixture["version"])


def test_beta_installer_contract():
    source = INSTALLER.read_text()
    assert 'MANIFEST_URL="https://www.linuxremoteplayer.com/beta/latest.json"' in source
    assert "source " not in source and "eval " not in source
    assert 'LRP_CHANNEL=beta' in source
    assert 'architecture != "amd64"' in source
    assert 'f"linuxremoteplayer_{version}_amd64.deb"' in source
    assert "sha256sum -c" in source
    assert "/usr/local/bin/lrp-setup --apply --approve --unattended < /dev/tty" in source
    assert "Run: sudo lrp-setup --apply --approve --unattended" in source
    assert "Reboot required. Run: sudo lrp-setup --resume" in source
    assert "mktemp \"$ENV_DIR/.env.XXXXXX\"" in source
    assert 'chmod --reference="$ENV_FILE" "$ENV_TMP"' in source
    assert 'chown --reference="$ENV_FILE" "$ENV_TMP"' in source


def _awk_program(source, start, end):
    match = re.search(start + r"(.*?)" + end, source, re.S)
    assert match, "production awk program not found"
    return match.group(1)


def _run_awk(program, input_path):
    awk = shutil.which("awk")
    if awk:
        program_path = input_path.with_suffix(".awk")
        program_path.write_text(program)
        command = [awk, "-f", str(program_path), str(input_path)]
    else:
        drive = input_path.drive.rstrip(":").lower()
        wsl_path = f"/mnt/{drive}{input_path.as_posix()[2:]}"
        program_path = input_path.with_suffix(".awk")
        program_path.write_text(program)
        wsl_program_path = f"/mnt/{drive}{program_path.as_posix()[2:]}"
        command = ["wsl", "awk", "-f", wsl_program_path, wsl_path]
    return subprocess.run(command, capture_output=True, text=True, check=True)


def test_beta_installer_removes_all_channel_assignments():
    source = INSTALLER.read_text()
    program = _awk_program(
        source,
        r"    awk '\n",
        r"' \"\$ENV_FILE\" > \"\$ENV_TMP\"",
    )
    content = "before=1\n  LRP_CHANNEL = old\nLRP_CHANNEL=middle\nLRP_CHANNEL\t=\tbeta\nafter=2\n"
    with tempfile.TemporaryDirectory() as directory:
        env_file = Path(directory) / ".env"
        env_file.write_text(content)
        result = _run_awk(program, env_file)
    assert result.stdout == "before=1\nafter=2\nLRP_CHANNEL=beta\n"
    assert result.stdout.count("LRP_CHANNEL=") == 1


def test_generated_updater_uses_last_assignment_and_exact_beta_value():
    source = BUILD.read_text()
    program = _awk_program(
        source,
        r"        CHANNEL=\$\(awk '\n",
        r"' \"\$ENV_FILE\"\)",
    )
    cases = {
        "": "stable",
        "LRP_CHANNEL=beta\nLRP_CHANNEL=stable\n": "stable",
        "LRP_CHANNEL=stable\n  LRP_CHANNEL = beta  \n": "beta",
        "LRP_CHANNEL=beta\nLRP_CHANNEL = beta\t\n": "beta",
        "LRP_CHANNEL=beta\nLRP_CHANNEL = beta # comment\n": "stable",
        "NOT_LRP_CHANNEL=beta\nLRP_CHANNEL_EXTRA=beta\n": "stable",
    }
    with tempfile.TemporaryDirectory() as directory:
        for index, (content, expected) in enumerate(cases.items()):
            env_file = Path(directory) / f"env-{index}"
            env_file.write_text(content)
            result = _run_awk(program, env_file)
            assert result.stdout.strip() == expected, (content, repr(program), result.stderr)


def test_build_script_is_lf_and_heredoc_markers_are_intact():
    raw = BUILD.read_bytes()
    assert b"\r" not in raw
    source = raw.decode()
    assert "cat <<EOF > pkg/usr/share/applications/linuxremoteplayer-panel.desktop" in source
    assert "cat <<'EOF' > pkg/DEBIAN/postinst" in source
    assert "cat <<'INNEREOF' > /usr/local/bin/lrp-update" in source
    assert "main \"$@\"; exit $?\nINNEREOF" in source
    assert source.count("\nEOF\n") >= 4


def test_generated_updater_contract_and_override_matrix():
    source = BUILD.read_text()
    assert "source " not in source and "eval " not in source
    assert 'https://www.linuxremoteplayer.com/latest.json' in source
    assert 'https://www.linuxremoteplayer.com/beta/latest.json' in source
    assert 'UPDATE_MANIFEST_URL' not in source
    assert 'BETA_UPDATE_MANIFEST_URL' not in source
    assert 'main "$@"; exit $?' in source
    assert "trap restart_services EXIT" in source

    assert "MANIFEST_URL=\"https://www.linuxremoteplayer.com/beta/latest.json\"" in source
    assert "MANIFEST_URL=\"https://www.linuxremoteplayer.com/latest.json\"" in source
    assert "sub(/^[[:space:]]*/, \"\", value)" in source
    assert "channel == \"beta\"" in source
    assert "exit" not in _awk_program(
        source, r"        CHANNEL=\$\(awk '\n", r"' \"\$ENV_FILE\"\)"
    )
