#!/bin/bash
set -euo pipefail

ROOT=${LRP_ROOT:-/}; SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLATFORM="$SCRIPT_DIR/debian/platform-bootstrap.sh"; SESSION="$SCRIPT_DIR/debian/session-bootstrap.sh"
SERVICE="$ROOT/etc/systemd/system/linuxremoteplayer.service"; PLATFORM_STATE="$ROOT/var/lib/linuxremoteplayer/platform/state"; SESSION_STATE="$ROOT/var/lib/linuxremoteplayer/session/state"
MODE=dry-run; APPROVE=0
for arg in "$@"; do case "$arg" in --dry-run) MODE=dry-run;; --apply) MODE=apply;; --approve) APPROVE=1;; --help|-h) echo 'usage: uninstall.sh [--dry-run|--apply --approve]'; exit 0;; *) echo '{"contract_valid":false,"reason":"invalid_argument"}'; exit 12;; esac; done
[ "${EUID:-1}" = 0 ] || { echo '{"contract_valid":false,"reason":"root_required"}'; exit 12; }
[ "$MODE" != apply ] || { [ "$APPROVE" = 1 ] || { echo '{"contract_valid":false,"reason":"approval_required"}'; exit 12; }; }
would=(); [ -f "$SERVICE" ] && would+=(stop_disable_remove_system_unit); [ -f "$PLATFORM_STATE" ] && would+=(platform_rollback); [ -f "$SESSION_STATE" ] && would+=(session_rollback); would+=(daemon_reload)
if [ "$MODE" = apply ]; then
    [ -x "$PLATFORM" ] || [ ! -f "$PLATFORM_STATE" ] || exit 11
    [ -x "$SESSION" ] || [ ! -f "$SESSION_STATE" ] || exit 11
    if [ -f "$SERVICE" ]; then systemctl stop linuxremoteplayer.service; systemctl disable linuxremoteplayer.service; rm -f "$SERVICE"; fi
    [ ! -f "$PLATFORM_STATE" ] || "$PLATFORM" --rollback --approve --strict
    [ ! -f "$SESSION_STATE" ] || "$SESSION" --rollback --approve
    systemctl daemon-reload
    printf '%s\n' '{"mode":"apply","status":"rolled_back","retained":["nvidia/kernel packages","all apt packages","lrp user/home","/opt/linuxremoteplayer/backend/.env","/opt/linuxremoteplayer/backend/.pairing_token","/opt/linuxremoteplayer/backend/.license_cache","/opt/linuxremoteplayer/backend/certs","/opt/linuxremoteplayer backend owner data"]}'
else
    printf '{"mode":"dry-run","would_do":[%s],"retained":["nvidia/kernel packages","all apt packages","lrp user/home","/opt/linuxremoteplayer/backend/.env","/opt/linuxremoteplayer/backend/.pairing_token","/opt/linuxremoteplayer/backend/.license_cache","/opt/linuxremoteplayer/backend/certs","/opt/linuxremoteplayer backend owner data"]}\n' "$(printf '"%s",' "${would[@]}" | sed 's/,$//')"
fi
