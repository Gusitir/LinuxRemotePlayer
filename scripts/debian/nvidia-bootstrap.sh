#!/bin/bash
# lrp-nvidia-bootstrap v1.2.0 - Debian 13 trixie amd64 NVIDIA bootstrap (T-123).
#
# Bootstraps the NVIDIA driver stack on a verified Debian 13 appliance running
# Secure Boot disabled, targeting the RTX 3060 GPU (PCI 10de:2504), using only
# official Debian repositories. It never auto-reboots, never creates a
# duplicate apt source, and runs as read-only planning by default. Apply mode
# requires explicit owner approval.
#
# Exit contract:
#   0  complete (post-reboot verification passed)
#   10 unresolved preflight (prerequisite data cannot be determined)
#   11 failed requirement / transaction
#   12 invalid contract / state
#   20 reboot required (after a successful package install)
#   21 post-reboot verification failed
#
# State lives under root-owned $ROOT/var/lib/linuxremoteplayer/bootstrap with
# hashes registered. Logs/output are sanitized: no credentials, serials,
# hostnames or secrets.
#
# Usage:
#   ./scripts/debian/nvidia-bootstrap.sh                 # read-only plan
#   ./scripts/debian/nvidia-bootstrap.sh --apply --approve   # apply (owner ok)
#   ./scripts/debian/nvidia-bootstrap.sh --resume            # post-reboot verify
#
# Test-only injection (never alters real behavior):
#   LRP_ROOT            base filesystem to operate on (default "/")
#   LRP_COMMANDS        directory of fake-command stubs (default: real PATH)
#   LRP_COMMANDS_ONLY   1 -> only use LRP_COMMANDS stubs
#
# Exact package/version bundle (explicit inputs - not guessed):
#   nvidia-driver=550.163.01-2          nvidia-kernel-dkms=550.163.01-2
#   xserver-xorg-video-nvidia=550.163.01-2   firmware-nvidia-gsp=550.163.01-2
#   linux-headers-<verified-uname-r>=<matching-image-version>
#   dkms=3.2.2-1~deb13u1

set -o pipefail

TOOL="lrp-nvidia-bootstrap"
SCHEMA="1.2.0"
ROOT="${LRP_ROOT:-/}"
COMMANDS="${LRP_COMMANDS:-}"
COMMANDS_ONLY_MODE="${LRP_COMMANDS_ONLY:-0}"
BST="$ROOT/var/lib/linuxremoteplayer/bootstrap"
STATE_FILE="$BST/state"
BACKUP_FILE="$BST/sources.debian.bak"

GEXPECT_ID="debian"; GEXPECT_VER="13"; GEXPECT_CODENAME="trixie"; GEXPECT_ARCH="amd64"
GEXPECT_GPU_VENDOR="0x10de"; GEXPECT_GPU_DEVICE="0x2504"
EXPECTED_COMPONENTS="main contrib non-free non-free-firmware"
SOURCE_FILE=""
SOURCE_LAYOUT=""
SOURCE_LABEL=""
SOURCE_MODE="0644"
SOURCE_OWNER=""

declare -A PKG_VER=(
    [nvidia-driver]=550.163.01-2
    [nvidia-kernel-dkms]=550.163.01-2
    [xserver-xorg-video-nvidia]=550.163.01-2
    [firmware-nvidia-gsp]=550.163.01-2
    [dkms]=3.2.2-1~deb13u1
)
PKG_ORDER="nvidia-driver nvidia-kernel-dkms xserver-xorg-video-nvidia firmware-nvidia-gsp dkms"
HEADER_PKG=""; IMAGE_PKG=""; HEADER_VERSION=""; IMAGE_VERSION=""

# ---------- JSON / sanitization -------------------------------------------
json_escape() {
    printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e 's/\t/\\t/g' -e 's/\r//g'
}
redact_domains() {
    printf '%s' "$1" | sed -E \
        -e 's/[A-Za-z0-9_-]+\.(com|net|org|io|tv|dev|co|de|es|uk|ru|cn|jp|it|fr|br|ar|mx|app|site|club)/redacted/g'
}

# ---------- argument parsing ----------------------------------------------
MODE="plan"; APPROVE=0
declare -a ARGV=("$@")
_i=0
while [ "$_i" -lt "${#ARGV[@]}" ]; do
    case "${ARGV[$_i]}" in
        --apply) MODE="apply" ;;
        --approve) APPROVE=1 ;;
        --resume) MODE="resume" ;;
        --help|-h) printf 'lrp-nvidia-bootstrap v%s usage: [--apply --approve] | [--resume]\n' "$SCHEMA" >&2; exit 0 ;;
        *);;  # validated by dedicated checker below
    esac
    _i=$((_i + 1))
done
unset _i ARGV

# mode contract
if [ "$MODE" = "apply" ] && [ "$APPROVE" != "1" ]; then
    printf '{"tool":"%s","schema":"%s","contract_valid":false,"reason":"apply_requires_approval"}\n' "$TOOL" "$SCHEMA" >&2
    exit 12
fi
if [ "$APPROVE" = "1" ] && [ "$MODE" != "apply" ]; then
    printf '{"tool":"%s","schema":"%s","contract_valid":false,"reason":"approval_without_apply"}\n' "$TOOL" "$SCHEMA" >&2
    exit 12
fi

# ---------- command resolution seam ---------------------------------------
cmd_exists() {
    local name="$1"
    if [ -n "$COMMANDS" ]; then
        [ -f "$COMMANDS/$name" ]
    else
        command -v "$name" >/dev/null 2>&1
    fi
}
cmd_run() {
    local name="$1"; shift
    if [ -n "$COMMANDS" ]; then
        if [ "$COMMANDS_ONLY_MODE" = "1" ]; then
            [ -f "$COMMANDS/$name" ] || return 127
            sh "$COMMANDS/$name" "$@"; return $?
        fi
        if [ -f "$COMMANDS/$name" ]; then
            sh "$COMMANDS/$name" "$@"; return $?
        fi
    fi
    if command -v "$name" >/dev/null 2>&1; then
        "$name" "$@"; return $?
    fi
    return 127
}
cmd_out() {
    local out rc
    out=$(cmd_run "$@" 2>/dev/null); rc=$?
    if [ "$rc" = "127" ]; then out=""; fi
    printf '%s' "$out"
}
cmd_run_lc() {
    local name="$1"; shift
    if [ -n "$COMMANDS" ]; then
        if [ "$COMMANDS_ONLY_MODE" = "1" ]; then
            [ -f "$COMMANDS/$name" ] || return 127
            env LC_ALL=C LANG=C sh "$COMMANDS/$name" "$@"; return $?
        fi
        if [ -f "$COMMANDS/$name" ]; then
            env LC_ALL=C LANG=C sh "$COMMANDS/$name" "$@"; return $?
        fi
    fi
    if command -v "$name" >/dev/null 2>&1; then
        env LC_ALL=C LANG=C "$name" "$@"; return $?
    fi
    return 127
}
cmd_out_lc() {
    local out rc
    out=$(cmd_run_lc "$@" 2>/dev/null); rc=$?
    if [ "$rc" = "127" ]; then out=""; fi
    printf '%s' "$out"
}

sha() { sha256sum "$1" 2>/dev/null | awk '{print $1}'; }

# Permission ops routed through the command seam (testable + real-host safe).
setmode() { cmd_run chmod "$@" 2>/dev/null || true; }
setown() { cmd_run chown "$@" 2>/dev/null || true; }

# ---------- state ---------------------------------------------------------
state_phase=""; state_layout=""; state_components_enabled=0; state_apt_updated=0; state_packages_installed=0
state_reboot_required=0; state_post_reboot_ok=0; state_status=""; state_backup_sha=""
state_kernel_release=""; state_image_package=""; state_image_version=""
state_header_package=""; state_header_version=""

read_state() {
    [ -f "$STATE_FILE" ] || return 0
    local k v _l
    while IFS= read -r _l || [ -n "$_l" ]; do
        case "$_l" in
            ''|'#'*|*'=' ) continue ;;
            *\=*)
                k="${_l%%=*}"; v="${_l#*=}"
                case "$k" in
                    phase) state_phase="$v" ;;
                    layout) state_layout="$v" ;;
                    components_enabled) state_components_enabled="$v" ;;
                    apt_updated) state_apt_updated="$v" ;;
                    packages_installed) state_packages_installed="$v" ;;
                    reboot_required) state_reboot_required="$v" ;;
                    post_reboot_ok) state_post_reboot_ok="$v" ;;
                    status) state_status="$v" ;;
                    source_backup_sha256) state_backup_sha="$v" ;;
                    kernel_release) state_kernel_release="$v" ;;
                    image_package) state_image_package="$v" ;;
                    image_version) state_image_version="$v" ;;
                    header_package) state_header_package="$v" ;;
                    header_version) state_header_version="$v" ;;
                esac
                ;;
        esac
    done < "$STATE_FILE"
}

ensure_store() {
    [ -d "$BST" ] || mkdir -p "$BST" 2>/dev/null
    setmode 0700 "$BST"
    setown 0:0 "$BST"
}
write_state() {
    ensure_store
    local tmp; tmp=$(mktemp "$BST/state.XXXXXX" 2>/dev/null)
    if [ -z "$tmp" ]; then
        : > "$BST/state.invalid" 2>/dev/null
        return 1
    fi
    {
        printf 'phase=%s\n' "$state_phase"
        printf 'layout=%s\n' "$SOURCE_LAYOUT"
        printf 'components_enabled=%s\n' "$state_components_enabled"
        printf 'apt_updated=%s\n' "$state_apt_updated"
        printf 'packages_installed=%s\n' "$state_packages_installed"
        printf 'reboot_required=%s\n' "$state_reboot_required"
        printf 'post_reboot_ok=%s\n' "$state_post_reboot_ok"
        printf 'status=%s\n' "$state_status"
        printf 'source_backup_sha256=%s\n' "$state_backup_sha"
        printf 'kernel_release=%s\n' "$host_kernel"
        printf 'image_package=%s\n' "$IMAGE_PKG"
        printf 'image_version=%s\n' "$IMAGE_VERSION"
        printf 'header_package=%s\n' "$HEADER_PKG"
        printf 'header_version=%s\n' "$HEADER_VERSION"
    } > "$tmp"
    setmode 0600 "$tmp"
    setown 0:0 "$tmp"
    mv -f "$tmp" "$STATE_FILE"
    setmode 0600 "$STATE_FILE"
    setown 0:0 "$STATE_FILE"
}

# ---------- probe: identity / secure boot / gpu / modules ----------------
os_id=""; os_version=""; os_codename=""; host_arch=""; host_kernel=""
efi=0; sb="unknown"
for _f in "$ROOT/etc/os-release" "$ROOT/usr/lib/os-release"; do
    [ -f "$_f" ] || continue
    while IFS= read -r _l || [ -n "$_l" ]; do
        _l=$(printf '%s' "$_l" | tr -d '\r')
        case "$_l" in
            ID=*) os_id=$(printf '%s' "${_l#ID=}" | tr -d '"') ;;
            VERSION_ID=*) os_version=$(printf '%s' "${_l#VERSION_ID=}" | tr -d '"') ;;
            VERSION_CODENAME=*) os_codename=$(printf '%s' "${_l#VERSION_CODENAME=}" | tr -d '"') ;;
        esac
    done < "$_f"
    break
done
unset _f _l

if cmd_exists dpkg; then host_arch=$(cmd_out dpkg --print-architecture); fi
if [ -z "$host_arch" ] && cmd_exists uname; then host_arch=$(cmd_out uname -m); fi
if cmd_exists uname; then host_kernel=$(cmd_out uname -r); fi
[ -d "$ROOT/sys/firmware/efi" ] && efi=1
if [ "$efi" = "1" ]; then
    case "$(cmd_out mokutil --sb-state)" in
        *[Ee]nabled*) sb="enabled" ;;
        *[Dd]isabled*) sb="disabled" ;;
        *) sb="unknown" ;;
    esac
fi

# Kernel/header contract is resolved before any source or package mutation.
# The package name is derived only from the sanitized running kernel release;
# the amd64 meta package is never installed implicitly.
kernel_probe_status="ok"; kernel_probe_issue=""
case "$host_kernel" in
    ''|*[![:alnum:]._+-]*) kernel_probe_status="unknown"; kernel_probe_issue="kernel_release_unresolved" ;;
    *)
        HEADER_PKG="linux-headers-$host_kernel"
        IMAGE_PKG="linux-image-$host_kernel"
        ;;
esac

image_query=""; header_policy=""
if [ "$kernel_probe_status" = "ok" ]; then
    if ! cmd_exists dpkg-query; then
        kernel_probe_status="unknown"; kernel_probe_issue="kernel_image_tool_missing"
    else
        image_query=$(cmd_out_lc dpkg-query -W -f='${Status}\t${Version}\n' "$IMAGE_PKG")
        case "$image_query" in
            *"install ok installed"*) IMAGE_VERSION="$(printf '%s\n' "$image_query" | sed -n 's/.*install ok installed[[:space:]]*\t\?//p' | head -n 1)" ;;
            '') kernel_probe_status="unknown"; kernel_probe_issue="kernel_image_unresolved" ;;
            *) kernel_probe_status="fail"; kernel_probe_issue="kernel_image_not_installed" ;;
        esac
    fi
    if [ "$kernel_probe_status" = "ok" ]; then
        header_policy=$(cmd_out_lc apt-cache policy "$HEADER_PKG")
        HEADER_VERSION="$(printf '%s\n' "$header_policy" | grep -E '^[[:space:]]*Candidate:' | head -n 1 | sed -E 's/^[[:space:]]*Candidate:[[:space:]]*//')"
        if [ -z "$header_policy" ] || [ -z "$HEADER_VERSION" ]; then
            kernel_probe_status="unknown"; kernel_probe_issue="header_candidate_unresolved"
        elif [ "$HEADER_VERSION" = "(none)" ]; then
            kernel_probe_status="fail"; kernel_probe_issue="header_candidate_unavailable"; HEADER_VERSION=""
        fi
    fi
    if [ "$kernel_probe_status" = "ok" ] && [ -z "$IMAGE_VERSION" ]; then
        kernel_probe_status="unknown"; kernel_probe_issue="kernel_image_version_unresolved"
    fi
    if [ "$kernel_probe_status" = "ok" ] && [ "$IMAGE_VERSION" != "$HEADER_VERSION" ]; then
        kernel_probe_status="fail"; kernel_probe_issue="kernel_image_header_version_mismatch"
    fi
fi
if [ "$kernel_probe_status" = "ok" ]; then
    PKG_VER[$HEADER_PKG]="$HEADER_VERSION"
    PKG_ORDER="nvidia-driver nvidia-kernel-dkms xserver-xorg-video-nvidia firmware-nvidia-gsp $HEADER_PKG dkms"
fi

# expected GPU PCI device present + driver binding
gpu_expected_found=0; gpu_bound=""
declare -a GPU_DEVS=()
for _d in "$ROOT"/sys/bus/pci/devices/*/; do
    [ -d "$_d" ] || continue
    _v=$(cat "$_d/vendor" 2>/dev/null); _dv=$(cat "$_d/device" 2>/dev/null)
    [ "$_v" = "$GEXPECT_GPU_VENDOR" ] && [ "$_dv" = "$GEXPECT_GPU_DEVICE" ] || continue
    gpu_expected_found=1
    if [ -L "$_d/driver" ]; then
        gpu_bound=$(basename "$(readlink "$_d/driver" 2>/dev/null)")
    elif [ -f "$_d/driver" ]; then
        gpu_bound=$(cat "$_d/driver" 2>/dev/null)
    fi
done
unset _d _v _dv

mods=""; modules_csv=""
if [ -f "$ROOT/proc/modules" ]; then mods=$(cat "$ROOT/proc/modules" 2>/dev/null); fi
while IFS= read -r _m || [ -n "$_m" ]; do
    _mn="${_m%% *}"
    [ -n "$_mn" ] || continue
    modules_csv="${modules_csv:+$modules_csv,}$_mn"
done <<< "$mods"
unset _m _mn
mod_has() { case ",$modules_csv," in *",$1,"*) return 0;; *) return 1;; esac; }

# ---------- probe: apt sources contract -----------------------------------
# Exactly one active layout is accepted:
#   A: /etc/apt/sources.list.d/debian.sources (one official deb822 stanza)
#   B: /etc/apt/sources.list (official deb/deb-src trixie lines only)
src_reject=0; src_reject_reason=""; official_only=0
ds_uris=""; ds_suites=""; ds_comps=""; ds_signedby=""; ds_types=""
ds_components_tokens=""; ds_field_types=0; ds_field_uris=0; ds_field_suites=0
ds_field_comps=0; ds_field_signedby=0; ds_seen_content=0; ds_stanzas=0
legacy_active=0; legacy_bad=0; legacy_reason=""; legacy_components=""
legacy_all_components_expected=1

source_line_active() {
    grep -Eq '^[[:space:]]*(deb|deb-src|Types:|URIs:)' "$1"
}

uri_is_official() {
    local uri="$1" h
    case "$uri" in *'@'*) return 1;; esac
    h=$(printf '%s' "$uri" | sed -E 's#^[A-Za-z][A-Za-z0-9+.-]*://##')
    h="${h%%/*}"; h="${h%%:*}"
    case "$h" in *.debian.org|debian.org|*.debian.net|debian.net) return 0;; esac
    return 1
}

legacy_line_check() {
    local line="$1" type idx uri suite comp comp_csv
    declare -a tok
    line=$(printf '%s' "$line" | sed 's/\r$//;s/^[[:space:]]*//')
    case "$line" in ''|\#*) return 0;; esac
    read -ra tok <<< "$line"
    [ "${#tok[@]}" -ge 4 ] || { legacy_bad=1; legacy_reason="malformed_legacy_line"; return; }
    type="${tok[0]}"
    case "$type" in deb|deb-src) ;; *) legacy_bad=1; legacy_reason="unexpected_legacy_type"; return;; esac
    idx=1
    if [[ "${tok[$idx]:-}" == \[* ]]; then
        while [ "$idx" -lt "${#tok[@]}" ] && [[ "${tok[$idx]}" != *\] ]]; do idx=$((idx + 1)); done
        idx=$((idx + 1))
    fi
    uri="${tok[$idx]:-}"; idx=$((idx + 1)); suite="${tok[$idx]:-}"; idx=$((idx + 1))
    uri_is_official "$uri" || { legacy_bad=1; legacy_reason="third_party_or_credential_uri"; return; }
    case "$suite" in trixie|trixie-updates|trixie-security) ;; *) legacy_bad=1; legacy_reason="unexpected_legacy_suite"; return;; esac
    [ "$idx" -lt "${#tok[@]}" ] || { legacy_bad=1; legacy_reason="missing_legacy_components"; return; }
    comp_csv=""
    while [ "$idx" -lt "${#tok[@]}" ]; do
        comp="${tok[$idx]}"; idx=$((idx + 1))
        case "$comp" in \#*) break;;
            main|contrib|non-free|non-free-firmware) comp_csv="${comp_csv:+$comp_csv,}$comp" ;;
            *) legacy_bad=1; legacy_reason="unexpected_legacy_component"; return;;
        esac
    done
    if [ "$(printf '%s' "$comp_csv" | tr ',' '\n' | sed '/^$/d' | sort)" != "$(printf '%s\n' $EXPECTED_COMPONENTS | sort)" ]; then
        legacy_all_components_expected=0
    fi
    [ -n "$legacy_components" ] || legacy_components="$comp_csv"
    legacy_active=1
}

if [ -f "$ROOT/etc/apt/sources.list" ]; then
    while IFS= read -r _l || [ -n "$_l" ]; do legacy_line_check "$_l"; done < "$ROOT/etc/apt/sources.list"
fi

for _f in "$ROOT"/etc/apt/sources.list.d/*; do
    [ -f "$_f" ] || continue
    if source_line_active "$_f"; then
        if [ "$_f" = "$ROOT/etc/apt/sources.list.d/debian.sources" ]; then
            [ "$legacy_active" = "0" ] || { src_reject=1; src_reject_reason="both_source_layouts_active"; }
        else
            src_reject=1; src_reject_reason="unexpected_extra_source"
        fi
    fi
done
unset _f

if [ "$legacy_active" = "1" ] || [ "$legacy_bad" = "1" ]; then
    if [ "$legacy_bad" = "1" ]; then
        src_reject=1; src_reject_reason="$legacy_reason"
    elif [ -f "$ROOT/etc/apt/sources.list.d/debian.sources" ] && source_line_active "$ROOT/etc/apt/sources.list.d/debian.sources"; then
        src_reject=1; src_reject_reason="both_source_layouts_active"
    else
        SOURCE_LAYOUT="legacy"; SOURCE_FILE="$ROOT/etc/apt/sources.list"; SOURCE_LABEL="sources.list"
        BACKUP_FILE="$BST/sources.list.bak"
        official_only=1
    fi
fi

if [ "$SOURCE_LAYOUT" = "" ] && [ "$src_reject" = "0" ]; then
    SOURCE_FILE="$ROOT/etc/apt/sources.list.d/debian.sources"
    if [ ! -f "$SOURCE_FILE" ] || ! source_line_active "$SOURCE_FILE"; then
        src_reject=1; src_reject_reason="missing_debian_sources"
    else
        SOURCE_LAYOUT="deb822"; SOURCE_LABEL="debian.sources"
        BACKUP_FILE="$BST/sources.debian.bak"
        while IFS= read -r _l || [ -n "$_l" ]; do
            _l=$(printf '%s' "$_l" | tr -d '\r' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
            if [ -z "$_l" ]; then
                [ "$ds_seen_content" = "1" ] && ds_stanzas=$((ds_stanzas + 1)); ds_seen_content=0; continue
            fi
            case "$_l" in
                \#*) continue ;;
                Types:*) ds_field_types=$((ds_field_types + 1)); ds_types="$(printf '%s' "${_l#Types:}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')" ;;
                URIs:*) ds_field_uris=$((ds_field_uris + 1)); ds_uris="$(printf '%s' "${_l#URIs:}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')" ;;
                Suites:*) ds_field_suites=$((ds_field_suites + 1)); ds_suites="$(printf '%s' "${_l#Suites:}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')" ;;
                Components:*) ds_field_comps=$((ds_field_comps + 1)); ds_comps="$(printf '%s' "${_l#Components:}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')" ;;
                Signed-By:*) ds_field_signedby=$((ds_field_signedby + 1)); ds_signedby="$(printf '%s' "${_l#Signed-By:}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')" ;;
                *) src_reject=1; src_reject_reason="malformed_deb822_field" ;;
            esac
            ds_seen_content=1
        done < "$SOURCE_FILE"
        [ "$ds_seen_content" = "1" ] && ds_stanzas=$((ds_stanzas + 1))
        ds_components_tokens="$(printf '%s' "$ds_comps" | tr ' ,' '\n' | sed '/^$/d' | sort)"
        ds_bad_type=0; ds_bad_suite=0
        for _t in $ds_types; do case "$_t" in deb|deb-src) ;; *) ds_bad_type=1;; esac; done
        for _s in $ds_suites; do case "$_s" in trixie|trixie-updates|trixie-security|trixie-backports) ;; *) ds_bad_suite=1;; esac; done
        if [ "$ds_stanzas" != "1" ] || [ "$ds_field_types" != "1" ] || [ "$ds_field_uris" != "1" ] || [ "$ds_field_suites" != "1" ] || [ "$ds_field_comps" != "1" ] || [ "$ds_field_signedby" != "1" ] || [ "$ds_bad_type" = "1" ] || [ "$ds_bad_suite" = "1" ]; then
            src_reject=1; src_reject_reason="ambiguous_deb822_stanza"
        elif [ -z "$ds_uris" ] || case "$ds_uris" in *' '*) true;; *) false;; esac; then
            src_reject=1; src_reject_reason="ambiguous_multiple_uris"
        elif ! uri_is_official "$ds_uris"; then
            src_reject=1; src_reject_reason="third_party_or_credential_uri"
        else
            official_only=1
        fi
        unset _t _s
    fi
fi

if [ "$src_reject" = "0" ] && [ -n "$SOURCE_FILE" ]; then
    SOURCE_MODE="0$(stat -c '%a' "$SOURCE_FILE" 2>/dev/null || printf '644')"
    SOURCE_OWNER="$(stat -c '%u:%g' "$SOURCE_FILE" 2>/dev/null || true)"
fi

# ---------- probe: package installed state -------------------------------
declare -A PKG_INSTALLED=()
for _p in $PKG_ORDER; do
    if cmd_exists dpkg; then
        if cmd_run dpkg -s "$_p" >/dev/null 2>&1; then PKG_INSTALLED[$_p]=1; else PKG_INSTALLED[$_p]=0; fi
    else
        PKG_INSTALLED[$_p]=0
    fi
done
unset _p

# ---------- preflight gates -----------------------------------------------
prf_status="ok"          # ok / fail / unknown
declare -a PRF_ISSUES=()
prf_fail() { PRF_ISSUES+=("$1"); prf_status="fail"; }
prf_unknown() { PRF_ISSUES+=("$1"); [ "$prf_status" = "fail" ] || prf_status="unknown"; }

if [ "$os_id" != "$GEXPECT_ID" ]; then prf_fail "os_id"; fi
if [ "$os_version" != "$GEXPECT_VER" ]; then prf_fail "os_version"; fi
if [ "$os_codename" != "$GEXPECT_CODENAME" ]; then prf_fail "os_codename"; fi
if [ -z "$os_id" ] || [ -z "$os_version" ] || [ -z "$host_arch" ]; then prf_unknown "identity_unresolved"; fi
if [ -n "$host_arch" ] && [ "$host_arch" != "$GEXPECT_ARCH" ]; then prf_fail "architecture"; fi
if [ "$sb" = "enabled" ]; then prf_fail "secure_boot"; fi
if [ "$sb" = "unknown" ]; then prf_unknown "secure_boot_unresolved"; fi
if [ "$gpu_expected_found" = "0" ]; then prf_fail "expected_gpu_missing"; fi
if [ "$kernel_probe_status" = "unknown" ]; then prf_unknown "$kernel_probe_issue"; fi
if [ "$kernel_probe_status" = "fail" ]; then prf_fail "$kernel_probe_issue"; fi
# A pre-install nouveau binding is expected and is not an unresolved gate.
# Binding, loaded NVIDIA modules, nvidia-smi and nouveau absence are enforced
# only by verify_post_reboot after the owner performs the reboot.

# ---------- post-reboot verify --------------------------------------------
with_nvidia_modules=0; nouveau_present=0
mod_has nvidia && mod_has nvidia_modeset && mod_has nvidia_drm && mod_has nvidia_uvm && with_nvidia_modules=1
mod_has nouveau && nouveau_present=1
nvidia_smi_ok=0
if cmd_exists nvidia-smi; then if cmd_run nvidia-smi >/dev/null 2>&1; then nvidia_smi_ok=1; fi; fi

pvr_ok=0; declare -a PVR_ISSUES=()
verify_post_reboot() {
    [ "$gpu_expected_found" = "1" ] || PVR_ISSUES+=("gpu_not_found")
    [ "$gpu_bound" = "nvidia" ] || PVR_ISSUES+=("gpu_not_bound_to_nvidia")
    [ "$with_nvidia_modules" = "1" ] || PVR_ISSUES+=("nvidia_modules_absent")
    [ "$nouveau_present" = "0" ] || PVR_ISSUES+=("nouveau_present")
    [ "$nvidia_smi_ok" = "1" ] || PVR_ISSUES+=("nvidia_smi_unavailable")
    if [ "${#PVR_ISSUES[@]}" = "0" ]; then pvr_ok=1; fi
}

# ---------- source backup / edit / restore --------------------------------
backup_source() {
    ensure_store
    if [ ! -f "$BACKUP_FILE" ]; then
        cp -p "$SOURCE_FILE" "$BACKUP_FILE" 2>/dev/null
        setmode 0600 "$BACKUP_FILE"
        setown 0:0 "$BACKUP_FILE"
    fi
    state_backup_sha="$(sha "$BACKUP_FILE")"
}

components_match_expected() {
    if [ "$SOURCE_LAYOUT" = "legacy" ]; then
        [ "$legacy_all_components_expected" = "1" ]
    else
        [ "$ds_components_tokens" = "$(printf '%s\n' $EXPECTED_COMPONENTS | tr ' ,' '\n' | sed '/^$/d' | sort)" ]
    fi
}

enable_components() {
    if components_match_expected; then return 0; fi
    local tmp; tmp=$(mktemp "$BST/edit.XXXXXX" 2>/dev/null)
    [ -n "$tmp" ] || return 1
    if [ "$SOURCE_LAYOUT" = "legacy" ]; then
        awk -v expected="$EXPECTED_COMPONENTS" '
            {
                original=$0
                if (original ~ /^[[:space:]]*(deb|deb-src)[[:space:]]+/) {
                    comment=""; line=original; pos=index(line, "#")
                    if (pos) { comment=substr(line, pos); line=substr(line, 1, pos-1) }
                    n=split(line, a, /[[:space:]]+/); t=1
                    while (t <= n && a[t] == "") t++
                    x=t+1; opts=""
                    if (x <= n && a[x] ~ /^\[/) {
                        opts=a[x]; x++
                        while (x <= n && a[x-1] !~ /\]$/) { opts=opts " " a[x]; x++ }
                    }
                    if (t <= n && x+1 <= n) {
                        out=a[t]
                        if (opts != "") out=out " " opts
                        out=out " " a[x] " " a[x+1] " " expected
                        if (comment != "") out=out " " comment
                        print out; next
                    }
                }
                print original
            }
        ' "$SOURCE_FILE" > "$tmp"
    else
        sed -E "s/^([[:space:]]*Components:).*/\1 $EXPECTED_COMPONENTS/" "$SOURCE_FILE" > "$tmp"
    fi
    setmode 0644 "$tmp"
    setown 0:0 "$tmp"
    cp -p --attributes-only "$SOURCE_FILE" "$tmp" 2>/dev/null || true
    mv -f "$tmp" "$SOURCE_FILE"
    setmode "$SOURCE_MODE" "$SOURCE_FILE"
    [ -n "$SOURCE_OWNER" ] && setown "$SOURCE_OWNER" "$SOURCE_FILE"
    if [ "$SOURCE_LAYOUT" = "legacy" ]; then
        legacy_components="$EXPECTED_COMPONENTS"
        legacy_all_components_expected=1
    else
        ds_comps="$EXPECTED_COMPONENTS"
        ds_components_tokens="$(printf '%s\n' $EXPECTED_COMPONENTS | tr ' ,' '\n' | sed '/^$/d' | sort)"
    fi
}

restore_source() {
    [ -f "$BACKUP_FILE" ] || return 1
    local want
    want="$(sha "$BACKUP_FILE")"
    if [ "$want" != "$state_backup_sha" ] && [ -n "$state_backup_sha" ]; then
        return 1
    fi
    cp -p "$BACKUP_FILE" "$SOURCE_FILE" 2>/dev/null
    setmode "$SOURCE_MODE" "$SOURCE_FILE"
    [ -n "$SOURCE_OWNER" ] && setown "$SOURCE_OWNER" "$SOURCE_FILE"
    state_components_enabled=0; state_apt_updated=0
    return 0
}

install_bundle() {
    declare -a ARG=()
    ARG+=(apt-get install -y)
    for _p in $PKG_ORDER; do ARG+=("$_p=${PKG_VER[$_p]}"); done
    cmd_run "${ARG[@]}"
    return $?
}

# ---------- apply ---------------------------------------------------------
run_apply() {
    # bail out before any mutation if preflight is not gated-ok
    if [ "$prf_status" = "fail" ]; then state_phase="preflight"; state_status="preflight_failed"; exit_code=11; return; fi
    if [ "$prf_status" = "unknown" ]; then state_phase="preflight"; state_status="preflight_unresolved"; exit_code=10; return; fi

    state_phase="source_backed_up"
    backup_source
    if [ -z "$state_backup_sha" ]; then state_phase="failed"; state_status="backup_failed"; exit_code=11; return; fi
    write_state

    state_phase="components_enabled"
    if ! enable_components; then state_phase="failed"; state_status="components_failed"; exit_code=11; return; fi
    state_components_enabled=1
    write_state

    state_phase="apt_updated"
    if ! cmd_run apt-get update >/dev/null 2>&1; then
        state_status="apt_update_failed"
        restore_source
        write_state
        exit_code=11
        return
    fi
    state_apt_updated=1
    write_state

    state_phase="packages_installed"
    if ! install_bundle; then
        state_status="package_install_failed"
        write_state
        exit_code=11
        return
    fi
    state_packages_installed=1
    write_state

    # successful install completes the mutation; keep components for future
    # updates and request a reboot. No automatic reboot, no driver rollback.
    state_phase="reboot_required"
    state_reboot_required=1
    state_status="reboot_required"
    write_state
    exit_code=20
}

# ---------- resume --------------------------------------------------------
run_resume() {
    case "$state_phase" in
        packages_installed|reboot_required|post_reboot_verify) ;;
        *) printf '{"tool":"%s","schema":"%s","contract_valid":false,"reason":"resume_state_invalid","phase":"%s"}\n' "$TOOL" "$SCHEMA" "$(json_escape "$state_phase")" >&2
           exit 12 ;;
    esac
    state_phase="post_reboot_verify"
    write_state
    verify_post_reboot
    if [ "$pvr_ok" = "1" ]; then
        state_phase="complete"; state_post_reboot_ok=1; state_status="complete"
        write_state
        exit_code=0
    else
        state_phase="post_reboot_verify"; state_status="post_reboot_failed"
        write_state
        exit_code=21
    fi
}

# ---------- report --------------------------------------------------------
report_issues() {
    local out=""
    for _v in "$@"; do out="${out:+$out,}\"$(json_escape "$_v")\""; done
    printf '[%s]' "$out"
}

print_report() {
    local pkg_json="" p
    for p in $PKG_ORDER; do
        pkg_json="${pkg_json:+$pkg_json,}\"$(json_escape "$p")\":{\"version\":\"$(json_escape "${PKG_VER[$p]}")\",\"installed\":$([ "${PKG_INSTALLED[$p]:-0}" = "1" ] && printf true || printf false)}"
    done
    printf '{\n'
    printf '  "tool":"%s",\n' "$TOOL"
    printf '  "schema":"%s",\n' "$SCHEMA"
    printf '  "contract_valid":true,\n'
    printf '  "mode":"%s",\n' "$MODE"
    printf '  "identity":{"id":"%s","version_id":"%s","codename":"%s","arch":"%s","kernel":"%s","secure_boot":"%s"},\n' "$(json_escape "$os_id")" "$(json_escape "$os_version")" "$(json_escape "$os_codename")" "$(json_escape "$host_arch")" "$(json_escape "$host_kernel")" "$(json_escape "$sb")"
    printf '  "gpu":{"expected":true,"found":%s,"bound":"%s","modules_loaded":%s,"nouveau_absent":%s,"nvidia_smi_ok":%s},\n' "$([ "$gpu_expected_found" = "1" ] && printf true || printf false)" "$(json_escape "$gpu_bound")" "$([ "$with_nvidia_modules" = "1" ] && printf true || printf false)" "$([ "$nouveau_present" = "0" ] && printf true || printf false)" "$([ "$nvidia_smi_ok" = "1" ] && printf true || printf false)"
    printf '  "sources":{"contract_ok":%s,"layout":"%s","file":"%s","uri_host_class":"%s","components":"%s"},\n' "$([ "$src_reject" = "0" ] && printf true || printf false)" "$(json_escape "$SOURCE_LAYOUT")" "$(json_escape "$SOURCE_LABEL")" "$( [ "$official_only" = "1" ] && printf official || printf other )" "$(json_escape "${ds_comps:-$legacy_components}")"
    printf '  "post_reboot":{"issues":%s},\n' "$(report_issues "${PVR_ISSUES[@]}")"
    printf '  "kernel":{"release":"%s","image_package":"%s","image_version":"%s","header_package":"%s","header_version":"%s","probe":"%s"},\n' "$(json_escape "$host_kernel")" "$(json_escape "$IMAGE_PKG")" "$(json_escape "$IMAGE_VERSION")" "$(json_escape "$HEADER_PKG")" "$(json_escape "$HEADER_VERSION")" "$(json_escape "$kernel_probe_status")"
    printf '  "packages":{%s},\n' "$pkg_json"
    printf '  "preflight":{"status":"%s","issues":%s},\n' "$prf_status" "$(report_issues "${PRF_ISSUES[@]}")"
    printf '  "state":{"phase":"%s","layout":"%s","components_enabled":%s,"apt_updated":%s,"packages_installed":%s,"reboot_required":%s,"post_reboot_ok":%s,"status":"%s"},\n' "$(json_escape "$state_phase")" "$(json_escape "${state_layout:-$SOURCE_LAYOUT}")" "$state_components_enabled" "$state_apt_updated" "$state_packages_installed" "$state_reboot_required" "$state_post_reboot_ok" "$(json_escape "$state_status")"
    printf '  "rollback":"verified_source_restore",\n'
    printf '  "exit_code":%d\n' "$exit_code"
    printf '}\n'
}

# ---------- main ----------------------------------------------------------
read_state

# Source contract is a trust boundary: unexpected/multiple/ambiguous/third-party
# sources invalidate the whole run (invalid contract), before any mode/mutation.
if [ "$src_reject" != "0" ]; then
    printf '{"tool":"%s","schema":"%s","contract_valid":false,"reason":"source_contract_invalid","detail":"%s"}\n' "$TOOL" "$SCHEMA" "$(json_escape "$src_reject_reason")" >&2
    exit 12
fi
if [ -n "$state_layout" ] && [ "$state_layout" != "$SOURCE_LAYOUT" ]; then
    printf '{"tool":"%s","schema":"%s","contract_valid":false,"reason":"state_layout_mismatch"}\n' "$TOOL" "$SCHEMA" >&2
    exit 12
fi

exit_code=0
case "$MODE" in
    resume) run_resume ;;
    apply) run_apply ;;
    plan)
        # read-only: never mutate. Report current/planned status.
        exit_code=0
        if [ "$state_phase" = "complete" ]; then exit_code=0
        elif [ "$state_phase" = "reboot_required" ]; then exit_code=20
        elif [ "$state_phase" = "post_reboot_verify" ]; then exit_code=0
        elif [ "$prf_status" = "fail" ]; then exit_code=11
        elif [ "$prf_status" = "unknown" ]; then exit_code=10
        fi
        ;;
esac
print_report
exit "$exit_code"
