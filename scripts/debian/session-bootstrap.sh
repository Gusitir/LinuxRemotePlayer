#!/bin/bash
set -o pipefail
export LC_ALL=C LANG=C

TOOL=lrp-session-bootstrap; SCHEMA=2.1.0
ROOT=${LRP_ROOT:-/}; COMMANDS=${LRP_COMMANDS:-}; COMMANDS_ONLY=${LRP_COMMANDS_ONLY:-0}
STATE_DIR="$ROOT/var/lib/linuxremoteplayer/session"; STATE_FILE="$STATE_DIR/state"; MANIFEST="$STATE_DIR/manifest"
SRC_LEGACY="$ROOT/etc/apt/sources.list"; SRC_DEB="$ROOT/etc/apt/sources.list.d/debian.sources"
USER_NAME=lrp; HOME_DIR="$ROOT/home/lrp"
TARGETS=("$ROOT/etc/lightdm/lightdm.conf.d/50-linuxremoteplayer.conf" "$ROOT/usr/share/xsessions/linuxremoteplayer.desktop" "$HOME_DIR/.config/openbox/rc.xml" "$HOME_DIR/.config/openbox/autostart")
PKGS=(lightdm xserver-xorg openbox dbus-x11 xauth mesa-utils lightdm-gtk-greeter)
declare -A WANT=(
 [lightdm]=1.32.0-6+b2 [xserver-xorg]=1:7.7+24+deb13u1 [openbox]=3.6.1-12+b2
 [dbus-x11]=1.16.2-2 [xauth]=1:1.1.2-1.1 [mesa-utils]=9.0.0-2+b2 [lightdm-gtk-greeter]=2.0.9-1)
EXPECTED=(main contrib non-free non-free-firmware)

json_escape() { printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e 's/\r//g' -e ':a' -e 'N' -e '$!ba' -e 's/\n/\\n/g'; }
json_array() { local x out=; for x in "$@"; do out="${out:+$out,}\"$(json_escape "$x")\""; done; printf '[%s]' "$out"; }
exists() { [ -n "$COMMANDS" ] && [ -f "$COMMANDS/$1" ] || { [ -z "$COMMANDS" ] && command -v "$1" >/dev/null 2>&1; }; }
run() { local n=$1; shift; if [ -n "$COMMANDS" ]; then [ -f "$COMMANDS/$n" ] || return 127; sh "$COMMANDS/$n" "$@"; else command -v "$n" >/dev/null 2>&1 || return 127; "$n" "$@"; fi; }
output() { local value rc; value=$(run "$@" 2>/dev/null); rc=$?; [ "$rc" = 0 ] && printf '%s' "$value"; return "$rc"; }
sha() { sha256sum "$1" 2>/dev/null | awk '{print $1}'; }
chmod_checked() { run chmod "$@"; }
chown_checked() { run chown "$@"; }
fail_json() { printf '{"tool":"%s","schema":"%s","contract_valid":false,"reason":"%s"}\n' "$TOOL" "$SCHEMA" "$1"; exit 12; }

MODE=plan; APPROVE=0
for arg in "$@"; do case "$arg" in
 --apply) MODE=apply;; --resume) MODE=resume;; --rollback) MODE=rollback;; --approve) APPROVE=1;; --help|-h) printf '%s\n' 'usage: session-bootstrap.sh [--apply --approve|--resume|--rollback --approve]'; exit 0;; *) fail_json invalid_argument;; esac; done
[ "$MODE" = plan ] && [ "$APPROVE" = 1 ] && fail_json approval_without_mutation
if [ "$MODE" = apply ] || [ "$MODE" = rollback ]; then [ "$APPROVE" = 1 ] || fail_json approval_required; fi
[ "$MODE" = plan ] || [ "$COMMANDS_ONLY" = 1 ] || [ "$EUID" = 0 ] || fail_json root_required

declare -a ISSUES=() POST_ISSUES=(); PRE=ok; MUTATION=0; LAYOUT=; SOURCE_FILE=; COMPONENTS=; URI=; CODENAME=; ARCH=; SB=unknown
read_identity() {
 local f line; for f in "$ROOT/etc/os-release" "$ROOT/usr/lib/os-release"; do [ -f "$f" ] || continue
  while IFS= read -r line || [ -n "$line" ]; do case "$line" in ID=*) ID=${line#ID=};; VERSION_ID=*) VERSION=${line#VERSION_ID=}; VERSION=${VERSION//\"/};; VERSION_CODENAME=*) CODENAME=${line#VERSION_CODENAME=};; esac; done < "$f"; break
 done
 ARCH=$(output dpkg --print-architecture 2>/dev/null || true)
 [ -d "$ROOT/sys/firmware/efi" ] && { case "$(output mokutil --sb-state 2>/dev/null || true)" in *[Ee]nabled*) SB=enabled;; *[Dd]isabled*) SB=disabled;; esac; }
}
official_uri() { local u=$1 h; case "$u" in *'@'*) return 1;; esac; h=$(printf '%s' "$u" | sed -E 's#^[A-Za-z][A-Za-z0-9+.-]*://##'); h=${h%%/*}; h=${h%%:*}; case "$h" in debian.org|*.debian.org|debian.net|*.debian.net) return 0;; esac; return 1; }
active_source_file() { case "$1" in *.list|*.sources) grep -Eq '^[[:space:]]*(deb|deb-src|Types:|URIs:)' "$1";; *) return 1;; esac; }
component_union_ok() { local got=$1 x; for x in $got; do case " ${EXPECTED[*]} " in *" $x "*) ;; *) return 1;; esac; done; for x in "${EXPECTED[@]}"; do case " $got " in *" $x "*) ;; *) return 1;; esac; done; return 0; }
validate_legacy() {
 local line type idx uri suite comp all=; local -a t; while IFS= read -r line || [ -n "$line" ]; do line=${line%$'\r'}; line="${line#${line%%[![:space:]]*}}"; case "$line" in ''|\#*) continue;; esac
  read -ra t <<< "$line"; [ "${#t[@]}" -ge 4 ] || return 1; type=${t[0]}; case "$type" in deb|deb-src) ;; *) return 1;; esac; idx=1
  if [[ ${t[$idx]:-} == \[* ]]; then while [ "$idx" -lt "${#t[@]}" ] && [[ ${t[$idx]} != *\] ]]; do idx=$((idx+1)); done; idx=$((idx+1)); fi
  uri=${t[$idx]:-}; idx=$((idx+1)); suite=${t[$idx]:-}; idx=$((idx+1)); official_uri "$uri" || return 1
  case "$suite" in trixie|trixie-updates|trixie-security) ;; *) return 1;; esac
  [ "$idx" -lt "${#t[@]}" ] || return 1; while [ "$idx" -lt "${#t[@]}" ]; do comp=${t[$idx]}; idx=$((idx+1)); [[ $comp == \#* ]] && break; case "$comp" in main|contrib|non-free|non-free-firmware) all="${all:+$all }$comp";; *) return 1;; esac; done
  COMPONENTS="${COMPONENTS:+$COMPONENTS }$all"; URI=${URI:-$uri}
 done < "$SRC_LEGACY"; component_union_ok "$COMPONENTS"
}
validate_deb822() {
 local line key value stanza=0 types= uris= suites= comps= signed= all_comps=; local -i nt=0 nu=0 ns=0 nc=0 nb=0
 validate_stanza() { [ "$stanza" = 0 ] && return 0; [ "$nt" = 1 ] && [ "$nu" = 1 ] && [ "$ns" = 1 ] && [ "$nc" = 1 ] && [ "$nb" = 1 ] || return 1; local x; for x in $types; do case "$x" in deb|deb-src) ;; *) return 1;; esac; done; for x in $suites; do case "$x" in trixie|trixie-updates|trixie-security) ;; *) return 1;; esac; done; uris=${uris# }; [ "$(wc -w <<< "$uris")" = 1 ] && official_uri "$uris" || return 1; all_comps="$all_comps $comps"; }
 while IFS= read -r line || [ -n "$line" ]; do line=${line%$'\r'}; line="${line#${line%%[![:space:]]*}}"; case "$line" in '' ) validate_stanza || return 1; stanza=0; types=; uris=; suites=; comps=; signed=; nt=0; nu=0; ns=0; nc=0; nb=0;; \#*) continue;; *:*) key=${line%%:*}; value=${line#*:}; value="${value#${value%%[![:space:]]*}}"; case "$key" in Types) nt=$((nt+1)); types=$value;; URIs) nu=$((nu+1)); uris=$value;; Suites) ns=$((ns+1)); suites=$value;; Components) nc=$((nc+1)); comps=$value;; Signed-By) nb=$((nb+1)); signed=$value;; *) return 1;; esac; stanza=1;; *) return 1;; esac; done < "$SRC_DEB"
 validate_stanza || return 1; COMPONENTS=$all_comps; URI=$uris; component_union_ok "$COMPONENTS"
}
validate_sources() {
 local legacy=0 extra=0 f; [ -f "$SRC_LEGACY" ] && active_source_file "$SRC_LEGACY" && legacy=1
 for f in "$ROOT/etc/apt/sources.list.d"/*; do [ -f "$f" ] || continue; active_source_file "$f" || continue; [ "$f" = "$SRC_DEB" ] || extra=1; done
 [ "$extra" = 0 ] || return 1; [ "$legacy" = 0 ] || { [ ! -f "$SRC_DEB" ] || ! active_source_file "$SRC_DEB" || return 1; validate_legacy || return 1; LAYOUT=legacy; SOURCE_FILE=$SRC_LEGACY; return 0; }
 [ -f "$SRC_DEB" ] && active_source_file "$SRC_DEB" || return 1; validate_deb822 || return 1; LAYOUT=deb822; SOURCE_FILE=$SRC_DEB
}

read_state() { STATE_PHASE=; STATE_STATUS=; [ -f "$STATE_FILE" ] || return 0; local l; while IFS= read -r l; do case "$l" in phase=*) STATE_PHASE=${l#phase=};; status=*) STATE_STATUS=${l#status=};; esac; done < "$STATE_FILE"; }
safe_state() { mkdir -p "$STATE_DIR" || return 1; chmod_checked 0700 "$STATE_DIR" || return 1; local t; t=$(mktemp "$STATE_DIR/state.XXXXXX") || return 1; (umask 077; printf 'phase=%s\nstatus=%s\n' "$1" "$2" > "$t") || return 1; chmod_checked 0600 "$t" || return 1; chown_checked 0:0 "$t" || return 1; mv -f "$t" "$STATE_FILE" || return 1; chmod_checked 0600 "$STATE_FILE"; chown_checked 0:0 "$STATE_FILE"; }
package_candidates() { local p out candidate; for p in "${PKGS[@]}"; do out=$(output apt-cache policy "$p") || return 1; candidate=$(printf '%s\n' "$out" | sed -nE 's/^[[:space:]]*Candidate:[[:space:]]*//p' | head -n1); [ "$candidate" = "${WANT[$p]}" ] || return 1; done; }
package_verify() { local p q; for p in "${PKGS[@]}"; do q=$(output dpkg-query -W -f='${Version}\n' "$p") || return 1; [ "$q" = "${WANT[$p]}" ] || return 1; done; run dpkg -V "${PKGS[@]}" >/dev/null 2>&1; }
install_packages() { local a=(apt-get install -y) p; for p in "${PKGS[@]}"; do a+=("$p=${WANT[$p]}"); done; ( export DEBIAN_FRONTEND=noninteractive; run "${a[@]}" ) || return 1; package_verify; }
manifest_valid() { [ -f "$MANIFEST" ] || return 1; local p status h mode uid gid n=0; while IFS='|' read -r p status h mode uid gid; do n=$((n+1)); [ "$p" = "${TARGETS[$((n-1))]}" ] || return 1; case "$status" in present) [ -f "$STATE_DIR/backups/$n" ] && [ "$(sha "$STATE_DIR/backups/$n")" = "$h" ] || return 1;; absent) [ -z "$h$mode$uid$gid" ] || return 1;; *) return 1;; esac; done < "$MANIFEST"; [ "$n" = 4 ]; }
backup_targets() {
 mkdir -p "$STATE_DIR/backups" || return 1; chmod_checked 0700 "$STATE_DIR" || return 1
 if [ -f "$MANIFEST" ]; then manifest_valid || return 1; return 0; fi
 local tmp n=0 p h mode uid gid; tmp=$(mktemp "$STATE_DIR/manifest.XXXXXX") || return 1; (umask 077; : > "$tmp") || return 1
 for p in "${TARGETS[@]}"; do n=$((n+1)); if [ -e "$p" ]; then cp -p "$p" "$STATE_DIR/backups/$n" || return 1; h=$(sha "$p"); mode=$(stat -c '%a' "$p") || return 1; uid=$(stat -c '%u' "$p") || return 1; gid=$(stat -c '%g' "$p") || return 1; printf '%s|present|%s|%s|%s|%s\n' "$p" "$h" "$mode" "$uid" "$gid" >> "$tmp"; else printf '%s|absent||||\n' "$p" >> "$tmp"; fi; done
 chmod_checked 0600 "$tmp" || return 1; chown_checked 0:0 "$tmp" || return 1; mv -f "$tmp" "$MANIFEST" || return 1; chmod_checked 0600 "$MANIFEST"; chown_checked 0:0 "$MANIFEST"
 local b; for b in "$STATE_DIR/backups"/*; do [ -f "$b" ] || continue; chmod_checked 0600 "$b" || return 1; chown_checked 0:0 "$b" || return 1; done
}
validate_user() { local uid entry home shell pw groups; uid=$(output id -u "$USER_NAME" 2>/dev/null) || true; if [ -n "$uid" ]; then [ "$uid" != 0 ] || return 1; entry=$(output getent passwd "$USER_NAME") || return 1; home=$(printf '%s\n' "$entry" | awk -F: 'NF >= 7 {print $6}'); shell=$(printf '%s\n' "$entry" | awk -F: 'NF >= 7 {print $7}'); [ "$home" = "/home/$USER_NAME" ] && [ "$shell" = "/bin/bash" ] || return 1; pw=$(output passwd -S "$USER_NAME") || return 1; printf '%s' "$pw" | awk '$2 == "L" || $2 == "LK" {ok=1} END {exit !ok}' || return 1; groups=$(output id -nG "$USER_NAME") || return 1; case " $groups " in *" sudo "*|*" adm "*) return 1;; esac; CREATED=0; else run useradd --create-home --home-dir /home/lrp --shell /bin/bash lrp || return 1; run passwd -l lrp || return 1; CREATED=1; fi; chmod_checked 0750 "$HOME_DIR" || return 1; chown_checked lrp:lrp "$HOME_DIR" || return 1; mkdir -p "$HOME_DIR/.config/openbox" || return 1; chmod_checked 0750 "$HOME_DIR/.config" "$HOME_DIR/.config/openbox" || return 1; chown_checked lrp:lrp "$HOME_DIR/.config" "$HOME_DIR/.config/openbox"; }
write_file() { local target=$1 content=$2 tmp; mkdir -p "$(dirname "$target")" || return 1; tmp=$(mktemp "$(dirname "$target")/.lrp.XXXXXX") || return 1; printf '%s\n' "$content" > "$tmp" || return 1; chmod_checked 0644 "$tmp" || return 1; chown_checked 0:0 "$tmp" || return 1; mv -f "$tmp" "$target"; }
write_configs() { write_file "${TARGETS[0]}" $'[Seat:*]\ngreeter-session=lightdm-gtk-greeter\nautologin-user=lrp\nautologin-user-timeout=0\nuser-session=linuxremoteplayer' && write_file "${TARGETS[1]}" $'[Desktop Entry]\nName=LinuxRemotePlayer\nExec=openbox-session\nType=Application' && write_file "${TARGETS[2]}" '<openbox_config xmlns="http://openbox.org/3.4"></openbox_config>' && write_file "${TARGETS[3]}" '# LinuxRemotePlayer session marker' && write_file "$HOME_DIR/.Xresources" $'Xcursor.theme: DMZ-White\nXcursor.size: 48\n' && mkdir -p "$HOME_DIR/.icons/default" && write_file "$HOME_DIR/.icons/default/index.theme" $'[Icon Theme]\nInherits=DMZ-White\n' && write_file "$HOME_DIR/.config/openbox/environment" $'# TV cursor scaling (48px for 1080p, 96px for 4K)\nexport XCURSOR_THEME="DMZ-White"\nexport XCURSOR_SIZE=48\nif command -v xrandr >/dev/null 2>&1; then\n RES=$(xrandr --current 2>/dev/null | grep \'*\' | head -n1 | awk \'{print $1}\')\n WIDTH=${RES%%x*}\n HEIGHT=${RES##*x}\n if [ -n "$WIDTH" ] && [ -n "$HEIGHT" ] && { [ "$WIDTH" -ge 3840 ] 2>/dev/null || [ "$HEIGHT" -ge 2160 ] 2>/dev/null; }; then\n  export XCURSOR_SIZE=96\n fi\nfi\nif command -v xrdb >/dev/null 2>&1; then\n printf \'Xcursor.theme: %s\\nXcursor.size: %d\\n\' "$XCURSOR_THEME" "$XCURSOR_SIZE" | xrdb -merge 2>/dev/null || true\nfi\n' && chmod_checked 0750 "$HOME_DIR" && chown_checked lrp:lrp "${TARGETS[2]}" "${TARGETS[3]}" && chown_checked lrp:lrp "$HOME_DIR/.Xresources" "$HOME_DIR/.config/openbox/environment" && chown_checked -R lrp:lrp "$HOME_DIR/.icons"; }
configs_valid() { grep -Fxq 'autologin-user=lrp' "${TARGETS[0]}" && grep -Fxq 'Exec=openbox-session' "${TARGETS[1]}" && grep -Fxq '<openbox_config xmlns="http://openbox.org/3.4"></openbox_config>' "${TARGETS[2]}" && grep -Fxq '# LinuxRemotePlayer session marker' "${TARGETS[3]}" && grep -Fq 'Xcursor.size: 48' "$HOME_DIR/.Xresources" && grep -Fq 'XCURSOR_SIZE=48' "$HOME_DIR/.config/openbox/environment"; }
rollback_targets() { manifest_valid || return 1; local p status h mode uid gid n=0; while IFS='|' read -r p status h mode uid gid; do n=$((n+1)); if [ "$status" = present ]; then [ "$(sha "$STATE_DIR/backups/$n")" = "$h" ] || return 1; cp -p "$STATE_DIR/backups/$n" "$p" || return 1; chmod_checked "$mode" "$p" || return 1; chown_checked "$uid:$gid" "$p" || return 1; [ "$(sha "$p")" = "$h" ] || return 1; else [ ! -e "$p" ] || rm -f "$p" || return 1; fi; done < "$MANIFEST"; rm -f "$HOME_DIR/.Xresources" "$HOME_DIR/.config/openbox/environment"; rm -rf "$HOME_DIR/.icons"; }
resume_verify() { local ps pid user comm envfile display xauth; package_candidates || { POST_ISSUES+=(candidate_drift); return 1; }; package_verify || { POST_ISSUES+=(package_integrity); return 1; }; run systemctl is-active lightdm >/dev/null 2>&1 || { POST_ISSUES+=(lightdm_inactive); return 1; }; ps=$(output ps -eo pid=,user=,comm=) || return 1; printf '%s\n' "$ps" | awk '$2=="root" && ($3=="openbox" || $3=="openbox-session"){r=1} $2=="lrp" && ($3=="openbox" || $3=="openbox-session"){o=1} $3=="Xorg"{x=1} END{exit !(x&&o&&!r)}' || { POST_ISSUES+=(session_processes); return 1; }; while read -r pid user comm; do [ "$user" = lrp ] && [[ "$comm" = openbox* ]] || continue; envfile="$ROOT/proc/$pid/environ"; if [ -r "$envfile" ]; then display=$(tr '\0' '\n' < "$envfile" | sed -n 's/^DISPLAY=//p' | head -n1); xauth=$(tr '\0' '\n' < "$envfile" | sed -n 's/^XAUTHORITY=//p' | head -n1); fi; done <<< "$ps"; display=${display:-${LRP_DISPLAY:-}}; xauth=${xauth:-${LRP_XAUTHORITY:-}}; [ -n "$display" ] && [ -n "$xauth" ] || { POST_ISSUES+=(runtime_environment); return 1; }; export DISPLAY="$display" XAUTHORITY="$xauth"; run nvidia-smi >/dev/null 2>&1 || { POST_ISSUES+=(nvidia_smi); return 1; }; grep -Eq '^nvidia ' "$ROOT/proc/modules" && grep -Eq '^nvidia_modeset ' "$ROOT/proc/modules" && grep -Eq '^nvidia_drm ' "$ROOT/proc/modules" && grep -Eq '^nvidia_uvm ' "$ROOT/proc/modules" || { POST_ISSUES+=(nvidia_modules); return 1; }; grep -Eq '^nouveau ' "$ROOT/proc/modules" && { POST_ISSUES+=(nouveau_present); return 1; }; local glx; glx=$(output glxinfo -B) || return 1; case "$glx" in *NVIDIA*) ;; *llvmpipe*) POST_ISSUES+=(llvmpipe_renderer); return 1;; *) POST_ISSUES+=(nvidia_renderer); return 1;; esac; }

read_identity; read_state
if [ "$MODE" = rollback ]; then
 [ -f "$MANIFEST" ] && manifest_valid || { STATE_PHASE=failed; STATE_STATUS=rollback_manifest_invalid; safe_state failed rollback_manifest_invalid; exit 11; }; run systemctl stop lightdm || { safe_state failed rollback_stop_failed; exit 11; }; run systemctl disable lightdm || { safe_state failed rollback_disable_failed; exit 11; }; rollback_targets || { safe_state failed rollback_restore_failed; exit 11; }; STATE_PHASE=safe_console; STATE_STATUS=rolled_back; safe_state safe_console rolled_back || true; exit_code=0
elif [ "$MODE" = resume ]; then
 [ "$STATE_PHASE" = reboot_required ] || fail_json invalid_state; resume_verify && { STATE_PHASE=complete; STATE_STATUS=complete; safe_state complete complete || true; exit_code=0; } || { STATE_PHASE=post_reboot_failed; STATE_STATUS=post_reboot_failed; safe_state post_reboot_failed post_reboot_failed || true; exit_code=21; }
else
 validate_sources || { PRE=fail; ISSUES+=(sources); }; [ "$ID" = debian ] || { PRE=fail; ISSUES+=(os_id); }; [ "$VERSION" = 13 ] || { PRE=fail; ISSUES+=(os_version); }; [ "$CODENAME" = trixie ] || { PRE=fail; ISSUES+=(codename); }; [ "$ARCH" = amd64 ] || { PRE=fail; ISSUES+=(architecture); }; [ "$SB" = disabled ] || { PRE=fail; ISSUES+=(secure_boot); }; package_candidates || { PRE=fail; ISSUES+=(candidate_drift); }
 exit_code=0; if [ "$PRE" = fail ]; then exit_code=11; elif [ "$MODE" = apply ]; then MUTATION=1; run systemctl mask lightdm || { STATE_PHASE=failed; STATE_STATUS=mask_failed; safe_state failed mask_failed || true; exit_code=11; }; [ "$exit_code" = 0 ] && { install_packages || { STATE_PHASE=failed; STATE_STATUS=package_install_failed; safe_state failed package_install_failed || true; exit_code=11; }; }; [ "$exit_code" = 0 ] && { backup_targets || exit_code=11; }; [ "$exit_code" = 0 ] && { validate_user || exit_code=11; }; [ "$exit_code" = 0 ] && { write_configs && configs_valid || exit_code=11; }; [ "$exit_code" = 0 ] && { run systemctl unmask lightdm || exit_code=11; }; [ "$exit_code" = 0 ] && { run systemctl enable lightdm && run systemctl is-enabled lightdm >/dev/null 2>&1 || exit_code=11; }; [ "$exit_code" = 0 ] && { STATE_PHASE=reboot_required; STATE_STATUS=reboot_required; safe_state reboot_required reboot_required || exit_code=11; }; [ "$exit_code" = 0 ] && exit_code=20; else [ "$PRE" = ok ] || exit_code=11; fi
 fi
if [ "$MODE" = apply ] && [ "$MUTATION" = 1 ] && [ "$exit_code" = 11 ] && [ -z "$STATE_PHASE" ]; then STATE_PHASE=failed; STATE_STATUS=apply_failed; safe_state failed apply_failed || true; fi
RECOVERY='Press Ctrl+Alt+F3. Roll back with session-bootstrap.sh --rollback --approve. TTY recovery is required.'
JCOMP=$(json_escape "$COMPONENTS"); JISSUES=$(json_array "${ISSUES[@]}"); JPOST=$(json_array "${POST_ISSUES[@]}")
printf '%s\n' "{\"tool\":\"$TOOL\",\"schema\":\"$SCHEMA\",\"contract_valid\":true,\"mode\":\"$MODE\",\"sources\":{\"layout\":\"$LAYOUT\",\"components\":\"$JCOMP\"},\"preflight\":{\"status\":\"$PRE\",\"issues\":$JISSUES},\"post_reboot\":{\"issues\":$JPOST},\"state\":{\"phase\":\"$STATE_PHASE\",\"status\":\"$STATE_STATUS\"},\"recovery\":{\"tty\":\"$RECOVERY\"},\"exit_code\":$exit_code}"
exit "$exit_code"
