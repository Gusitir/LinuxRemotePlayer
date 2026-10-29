#!/bin/bash
set -u

ROOT=${LRP_ROOT:-/}
BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATE_ROOT="$ROOT/var/lib/linuxremoteplayer"
UNATTENDED_ROOT="$ROOT/var/lib/linuxremoteplayer/unattended"
UNATTENDED_STATE="$UNATTENDED_ROOT/state"
UNATTENDED_UNIT="$ROOT/etc/systemd/system/linuxremoteplayer-bootstrap.service"

[ "${EUID:-1}" = 0 ] || { printf '%s\n' root_required >&2; exit 12; }

MODE=apply
APPROVE=0
UNATTENDED=0
for arg in "$@"; do
    case "$arg" in
        --apply) MODE=apply ;;
        --resume) MODE=resume ;;
        --approve) APPROVE=1 ;;
        --unattended) UNATTENDED=1 ;;
        --help|-h) printf '%s\n' 'usage: bootstrap.sh [--apply --approve|--resume]'; exit 0 ;;
        *) printf '%s\n' invalid_argument >&2; exit 12 ;;
    esac
done
[ "$MODE" = resume ] || [ "$APPROVE" = 1 ] || { printf '%s\n' approval_required >&2; exit 12; }
[ "$MODE" = apply ] || [ "$APPROVE" = 0 ] || { printf '%s\n' approval_without_apply >&2; exit 12; }
[ "$UNATTENDED" = 0 ] || [ "$MODE" = resume ] || [ "$APPROVE" = 1 ] || { printf '%s\n' unattended_requires_approval >&2; exit 12; }

state_phase() {
    local file="$1" line
    [ -f "$file" ] || return 1
    while IFS= read -r line; do
        case "$line" in phase=*) printf '%s' "${line#phase=}"; return 0 ;; esac
    done < "$file"
    return 1
}

run_phase() {
    local name="$1" script="$2" state="$3" phase rc
    phase=$(state_phase "$state" || true)
    [ "$phase" = complete ] && return 0
    if [ "$phase" = reboot_required ]; then
        [ "$MODE" = resume ] || { printf '%s\n' 'Re-run: sudo /opt/linuxremoteplayer/scripts/debian/bootstrap.sh --resume'; return 20; }
        "$script" --resume
    else
        if [ "$MODE" = resume ] && [ "$name" = nvidia ]; then
            printf '%s\n' nvidia_resume_requires_apply >&2
            return 12
        fi
        "$script" --apply --approve
    fi
    rc=$?
    case "$rc" in
        0) return 0 ;;
        10|11|12) return "$rc" ;;
        20) printf '%s\n' 'Re-run: sudo /opt/linuxremoteplayer/scripts/debian/bootstrap.sh --resume'; return 20 ;;
        *) return "$rc" ;;
    esac
}

wait_for_session() {
    local i
    for i in $(seq 1 90); do
        systemctl is-active --quiet lightdm 2>/dev/null && pgrep -u lrp -x openbox >/dev/null 2>&1 && pgrep -x Xorg >/dev/null 2>&1 && return 0
        sleep 1
    done
    return 21
}

cleanup_success() {
    systemctl disable linuxremoteplayer-bootstrap.service >/dev/null 2>&1 || true
    rm -f "$UNATTENDED_UNIT"
    systemctl daemon-reload >/dev/null 2>&1 || true
    rm -f "$UNATTENDED_STATE"
    rmdir "$UNATTENDED_ROOT" >/dev/null 2>&1 || true
}

cleanup_failure() {
    local rc="$1" count=0
    [ -f "$UNATTENDED_STATE" ] && count=$(sed -n 's/^reboots=//p' "$UNATTENDED_STATE" | tr -d '\r')
    mkdir -p "$UNATTENDED_ROOT"
    chmod 0700 "$UNATTENDED_ROOT"
    printf 'status=failed\nreboots=%s\n' "$count" > "$UNATTENDED_STATE"
    chmod 0600 "$UNATTENDED_STATE"
    systemctl disable linuxremoteplayer-bootstrap.service >/dev/null 2>&1 || true
    rm -f "$UNATTENDED_UNIT"
    systemctl daemon-reload >/dev/null 2>&1 || true
    return "$rc"
}

schedule_unattended() {
    local count=0
    [ -f "$UNATTENDED_STATE" ] && count=$(sed -n 's/^reboots=//p' "$UNATTENDED_STATE")
    count=$((count + 1))
    mkdir -p "$UNATTENDED_ROOT" || return 11
    chmod 0700 "$UNATTENDED_ROOT" || return 11
    if [ "$count" -gt 2 ]; then cleanup_failure 11; return $?; fi
    printf 'status=reboot_required\nreboots=%s\n' "$count" > "$UNATTENDED_STATE" || return 11
    chmod 0600 "$UNATTENDED_STATE" || return 11
    mkdir -p "$(dirname "$UNATTENDED_UNIT")" || return 11
    { cat > "$UNATTENDED_UNIT" <<EOF
[Unit]
Description=LinuxRemotePlayer unattended bootstrap
Wants=network-online.target
After=network-online.target display-manager.service

[Service]
Type=oneshot
ExecStart=/opt/linuxremoteplayer/scripts/debian/bootstrap.sh --resume --unattended

[Install]
WantedBy=multi-user.target
EOF
    } || return 11
    chmod 0644 "$UNATTENDED_UNIT" || return 11
    systemctl daemon-reload || return 11
    systemctl enable linuxremoteplayer-bootstrap.service || return 11
    systemctl reboot || return 11
    return 0
}

health_ready() {
    local i
    for i in $(seq 1 60); do
        curl -kfsS https://127.0.0.1:8000/health >/dev/null 2>&1 && return 0
        sleep 1
    done
    return 21
}

if [ "$UNATTENDED" = 1 ]; then
    run_phase nvidia "$BASE/nvidia-bootstrap.sh" "$STATE_ROOT/bootstrap/state"; rc=$?
    if [ "$rc" = 20 ]; then schedule_unattended; reboot_rc=$?; [ "$reboot_rc" = 0 ] && exit 0; cleanup_failure "$reboot_rc"; exit "$reboot_rc"; fi
    [ "$rc" = 0 ] || { cleanup_failure "$rc"; exit "$rc"; }
    session_phase=$(state_phase "$STATE_ROOT/session/state" || true)
    if [ "$session_phase" = reboot_required ]; then
        wait_for_session || { rc=$?; cleanup_failure "$rc"; exit "$rc"; }
    fi
    run_phase session "$BASE/session-bootstrap.sh" "$STATE_ROOT/session/state"; rc=$?
    if [ "$rc" = 20 ]; then schedule_unattended; reboot_rc=$?; [ "$reboot_rc" = 0 ] && exit 0; cleanup_failure "$reboot_rc"; exit "$reboot_rc"; fi
    [ "$rc" = 0 ] || { cleanup_failure "$rc"; exit "$rc"; }
    LRP_NONINTERACTIVE=1 "$BASE/../install.sh"; rc=$?
    [ "$rc" = 0 ] || { cleanup_failure "$rc"; exit "$rc"; }
    health_ready || { rc=$?; cleanup_failure "$rc"; exit "$rc"; }
    cleanup_success
    exit 0
fi
run_phase nvidia "$BASE/nvidia-bootstrap.sh" "$STATE_ROOT/bootstrap/state" || exit $?
run_phase session "$BASE/session-bootstrap.sh" "$STATE_ROOT/session/state" || exit $?
exec "$BASE/../install.sh"
