#!/bin/bash
set -u

ROOT=${LRP_ROOT:-/}
BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATE_ROOT="$ROOT/var/lib/linuxremoteplayer"

[ "${EUID:-1}" = 0 ] || { printf '%s\n' root_required >&2; exit 12; }

MODE=apply
APPROVE=0
for arg in "$@"; do
    case "$arg" in
        --apply) MODE=apply ;;
        --resume) MODE=resume ;;
        --approve) APPROVE=1 ;;
        --help|-h) printf '%s\n' 'usage: bootstrap.sh [--apply --approve|--resume]'; exit 0 ;;
        *) printf '%s\n' invalid_argument >&2; exit 12 ;;
    esac
done
[ "$MODE" = resume ] || [ "$APPROVE" = 1 ] || { printf '%s\n' approval_required >&2; exit 12; }
[ "$MODE" = apply ] || [ "$APPROVE" = 0 ] || { printf '%s\n' approval_without_apply >&2; exit 12; }

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
        [ "$MODE" = resume ] || { printf '%s\n' 'Re-run: sudo lrp-setup --resume'; return 20; }
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
        20) printf '%s\n' 'Re-run: sudo lrp-setup --resume'; return 20 ;;
        *) return "$rc" ;;
    esac
}

run_phase nvidia "$BASE/nvidia-bootstrap.sh" "$STATE_ROOT/bootstrap/state" || exit $?
run_phase session "$BASE/session-bootstrap.sh" "$STATE_ROOT/session/state" || exit $?
exec "$BASE/../install.sh"
