#!/bin/bash
# Shared noninteractive rollback. Default package mode is best-effort; uninstall uses --strict.
set +e
STRICT=0; [ "${1:-}" = --strict ] && STRICT=1
ROOT=${LRP_ROOT:-/}; SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLATFORM="$SCRIPT_DIR/debian/platform-bootstrap.sh"; SESSION="$SCRIPT_DIR/debian/session-bootstrap.sh"
rc=0; fail() { [ "$rc" = 0 ] && rc=$1; }
rollback() { local script="$1" state="$2" extra=; [ -f "$state" ] || return 0; [ -x "$script" ] || { fail 1; return; }; [ "$STRICT" = 1 ] && extra=--strict; "$script" --rollback --approve $extra || fail $?; }
if [ -f "$ROOT/etc/systemd/system/linuxremoteplayer.service" ]; then systemctl stop linuxremoteplayer.service || fail $?; systemctl disable linuxremoteplayer.service || fail $?; rm -f "$ROOT/etc/systemd/system/linuxremoteplayer.service" || fail $?; systemctl daemon-reload || fail $?; fi
rollback "$PLATFORM" "$ROOT/var/lib/linuxremoteplayer/platform/state"
rollback "$SESSION" "$ROOT/var/lib/linuxremoteplayer/session/state"
systemctl daemon-reload || fail $?
[ "$STRICT" = 1 ] && exit "$rc"
exit 0
