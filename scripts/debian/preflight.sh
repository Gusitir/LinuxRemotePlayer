#!/bin/bash
# lrp-debian-preflight v1.0.0 - READ-ONLY host probe (T-122).
#
# Emits a single sanitized JSON document and exits with a deterministic code:
#   0  success
#   10 missing data/tool (could not determine a requirement)
#   11 failed requirement (a goal is violated)
#   12 invalid contract (bad arguments or malformed manifest)
#
# The tool never writes to the filesystem, never runs privilege-elevating or
# mutating commands (no sudo, apt-get update/install, dpkg mutation, modprobe,
# systemctl, reboot) and never prints secrets, tokens, credentials, serials,
# usernames, hostnames or raw sensitive output.
#
# All package names seen are those declared explicitly in the manifest input;
# the tool does not invent package names. A role with no explicit inputs is
# reported as "unresolved".
#
# Usage:
#   ./scripts/debian/preflight.sh --manifest <manifest_file>
#
# Test-only injection (never defaults to values that alter real behavior):
#   LRP_ROOT            base filesystem to probe (default "/")
#   LRP_COMMANDS        directory of fake-command stubs (default: real PATH)
#   LRP_COMMANDS_ONLY   1 -> only use LRP_COMMANDS stubs, never fall back to PATH
#
# Manifest format (explicit inputs, one directive per line):
#   distro.id=<os_id>
#   distro.version=<version_id>
#   distro.codename=<codename>
#   distro.arch=<architecture>
#   secure_boot=<enabled|disabled|any>
#   role.id=<id>            starts a new role block
#   role.bin=<a,b,c>        comma-separated required binaries
#   role.pkg=<a,b,c>        comma-separated required package names
#   role.gpu=<nvidia|amd|intel|other>   PCI display vendor constraint
#   role.one_of=1           role satisfied when at least one binary exists

set -o pipefail

TOOL="lrp-debian-preflight"
SCHEMA="1.0.0"
ROOT="${LRP_ROOT:-/}"
COMMANDS="${LRP_COMMANDS:-}"
COMMANDS_ONLY_MODE="${LRP_COMMANDS_ONLY:-0}"

MANIFEST=""

# ---------- JSON escaping / sanitizers ------------------------------------
json_escape() {
    printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e 's/\t/\\t/g' -e 's/\r//g'
}

# Never emit anything that looks like a registered host/domain in free text.
redact_domains() {
    printf '%s' "$1" | sed -E \
        -e 's/[A-Za-z0-9_-]+\.(com|net|org|io|tv|dev|co|de|es|uk|ru|cn|jp|it|fr|br|ar|mx|app|site|club)/redacted/g'
}

contract_invalid() {
    local why="$1"
    local exit_code=12
    cat <<EOF
{"tool":"$TOOL","schema":"$SCHEMA","contract_valid":false,"reason":"$(json_escape "$why")",
 "identity":null,"gpu":null,"apt":null,"roles":null,
 "summary":{"result":"invalid_contract","exit_code":$exit_code}}
EOF
    exit 12
}

# ---------- argument parsing ----------------------------------------------
declare -a ARGV=("$@")
_i=0
while [ "$_i" -lt "${#ARGV[@]}" ]; do
    case "${ARGV[$_i]}" in
        --manifest|-m)
            _i=$((_i + 1))
            if [ "$_i" -lt "${#ARGV[@]}" ]; then MANIFEST="${ARGV[$_i]}"; fi
            ;;
        --manifest=*)
            MANIFEST="${ARGV[$_i]#--manifest=}"
            ;;
        --help|-h)
            printf 'lrp-debian-preflight v%s: %s\n' "$SCHEMA" "$TOOL" >&2
            exit 0
            ;;
        *)
            contract_invalid "invalid_argument:${ARGV[$_i]}"
            ;;
    esac
    _i=$((_i + 1))
done
unset _i ARGV

# ---------- command resolution seam ---------------------------------------
cmd_exists() {
    local name="$1"
    if [ -n "$COMMANDS" ]; then
        [ -f "$COMMANDS/$name" ]
    else
        command -v "$name" >/dev/null 2>&1
    fi
}

# run a command returning its status; when the command is missing it returns
# status 127 and prints nothing.
cmd_run() {
    local name="$1"; shift
    if [ -n "$COMMANDS" ]; then
        if [ "$COMMANDS_ONLY_MODE" = "1" ]; then
            if [ -f "$COMMANDS/$name" ]; then
                sh "$COMMANDS/$name" "$@"
                return $?
            fi
            return 127
        fi
        if [ -f "$COMMANDS/$name" ]; then
            sh "$COMMANDS/$name" "$@"
            return $?
        fi
        if command -v "$name" >/dev/null 2>&1; then
            "$name" "$@"
            return $?
        fi
        return 127
    fi
    if command -v "$name" >/dev/null 2>&1; then
        "$name" "$@"
        return $?
    fi
    return 127
}

cmd_out() {
    local name="$1"; shift
    local out rc
    out=$(cmd_run "$name" "$@" 2>/dev/null)
    rc=$?
    if [ "$rc" = "127" ]; then out=""; fi
    printf '%s' "$out"
}

# C-locale scoped command runner. Used for commands whose output is localized
# by the host (e.g. apt-cache), so the probe is locale-independent. LC_ALL and
# LANG are set only for this single invocation and never alter host state.
cmd_run_lc() {
    local name="$1"; shift
    if [ -n "$COMMANDS" ]; then
        if [ "$COMMANDS_ONLY_MODE" = "1" ]; then
            [ -f "$COMMANDS/$name" ] || return 127
            env LC_ALL=C LANG=C sh "$COMMANDS/$name" "$@"
            return $?
        fi
        if [ -f "$COMMANDS/$name" ]; then
            env LC_ALL=C LANG=C sh "$COMMANDS/$name" "$@"
            return $?
        fi
    fi
    if command -v "$name" >/dev/null 2>&1; then
        env LC_ALL=C LANG=C "$name" "$@"
        return $?
    fi
    return 127
}

cmd_out_lc() {
    local name="$1"; shift
    local out rc
    out=$(cmd_run_lc "$name" "$@" 2>/dev/null)
    rc=$?
    if [ "$rc" = "127" ]; then out=""; fi
    printf '%s' "$out"
}

# ---------- host identity -------------------------------------------------
os_id=""; os_version=""; os_codename=""
for _f in "$ROOT/etc/os-release" "$ROOT/usr/lib/os-release"; do
    [ -f "$_f" ] || continue
    while IFS= read -r _l || [ -n "$_l" ]; do
        # normalize CRLF / trailing control characters before comparison
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

dpkg_arch=""; um_arch=""; host_kernel=""
if cmd_exists dpkg; then dpkg_arch=$(cmd_out dpkg --print-architecture); fi
if cmd_exists uname; then
    um_arch=$(cmd_out uname -m)
    host_kernel=$(cmd_out uname -r)
fi
host_arch="${dpkg_arch:-$um_arch}"

efi=0
[ -d "$ROOT/sys/firmware/efi" ] && efi=1

sb="unknown"
if [ "$efi" = "1" ]; then
    _sbraw=$(cmd_out mokutil --sb-state)
    case "$_sbraw" in
        *[Ee]nabled*) sb="enabled" ;;
        *[Dd]isabled*) sb="disabled" ;;
        *) sb="unknown" ;;
    esac
    unset _sbraw
fi

# ---------- GPU identity (PCI display controllers) ------------------------
declare -A VNAME
VNAME[10de]=nvidia
VNAME[1002]=amd
VNAME[8086]=intel
VNAME[1af4]=virtio

graphics_vendor=""
gpu_vendors_list=""
for _cf in "$ROOT"/sys/bus/pci/devices/*/class; do
    [ -f "$_cf" ] || continue
    _cls=$(cat "$_cf" 2>/dev/null); _cls="${_cls#0x}"
    case "$_cls" in
        0300*|0302*|0380*) ;;
        *) continue ;;
    esac
    _d="$(dirname "$_cf")"
    _v=$(cat "$_d/vendor" 2>/dev/null); _v="${_v#0x}"
    [ -n "$_v" ] || _v="0000"
    _dv=$(cat "$_d/device" 2>/dev/null); _dv="${_dv#0x}"
    [ -n "$_dv" ] || _dv="0000"
    _vn="${VNAME[$_v]:-other}"
    [ -n "$graphics_vendor" ] || graphics_vendor="$_vn"
    gpu_vendors_list="${gpu_vendors_list:+$gpu_vendors_list,}$_vn"
done
unset _cf _cls _d _v _dv _vn

# ---------- loaded modules ------------------------------------------------
mods=""; graphics_module=""
if [ -f "$ROOT/proc/modules" ]; then mods=$(cat "$ROOT/proc/modules" 2>/dev/null); fi
modules_csv=""
while IFS= read -r _m || [ -n "$_m" ]; do
    _mn="${_m%% *}"
    [ -n "$_mn" ] || continue
    modules_csv="${modules_csv:+$modules_csv,}$_mn"
done <<< "$mods"
for _gm in nvidia nouveau i915 amdgpu intel radeon; do
    case ",$modules_csv," in
        *",$_gm,"*) graphics_module="$_gm"; break ;;
    esac
done
unset _m _mn _gm

# ---------- apt sources / components / third-party ------------------------
official_components=""
has_third_party=0
third_party_count=0
third_party_suites=""
sources_count=0

classify_uri() {
    local uri="$1" suite="$2" comps="$3" host official comp
    # Extract the authority, dropping scheme, any user:pass@ credentials and
    # any explicit port. Only the resulting host is used for classification;
    # the raw URI/authority/credentials are never emitted.
    host=$(printf '%s' "$uri" | sed -E 's#^[A-Za-z][A-Za-z0-9+.-]*://##')
    host="${host%%/*}"
    host="${host##*@}"
    host="${host%%:*}"
    official=0
    case "$host" in
        *.debian.org|debian.org|*.debian.net|debian.net) official=1 ;;
        archive.ubuntu.com|security.ubuntu.com|ports.ubuntu.com|*.ubuntu.com) official=1 ;;
        *) official=0 ;;
    esac
    sources_count=$((sources_count + 1))
    if [ "$official" = "1" ]; then
        IFS=' ,' read -ra _ca <<< "$comps"
        for comp in "${_ca[@]}"; do
            comp=$(printf '%s' "$comp" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
            [ -n "$comp" ] || continue
            official_components="${official_components:+$official_components,}$comp"
        done
        unset _ca
    else
        has_third_party=1
        third_party_count=$((third_party_count + 1))
        third_party_suites="${third_party_suites:+$third_party_suites,}$suite"
    fi
}

# deb822 (.sources) is stanza-based: fields collect within a stanza and a
# blank line (or EOF) ends it. Every URI x suite entry is classified so a
# third-party source can never hide behind an official URI in the same stanza.
deb822_classify() {
    local uris suites comps
    uris=$(printf '%s' "$1" | tr ',' ' ')
    suites=$(printf '%s' "$2" | tr ',' ' ')
    comps=$(printf '%s' "$3" | tr ',' ' ')
    read -ra _uarr <<< "$uris"
    read -ra _sarr <<< "$suites"
    if [ "${#_uarr[@]}" -eq 0 ]; then
        unset _uarr _sarr
        return 0
    fi
    if [ "${#_sarr[@]}" -eq 0 ]; then
        _sarr=("<none>")
    fi
    for _u in "${_uarr[@]}"; do
        for _s in "${_sarr[@]}"; do
            classify_uri "$_u" "$_s" "$comps"
        done
    done
    unset _uarr _sarr _u _s
}

_deb_uris=""; _deb_suites=""; _deb_comps=""
deb822_flush() {
    deb822_classify "$_deb_uris" "$_deb_suites" "$_deb_comps"
    _deb_uris=""; _deb_suites=""; _deb_comps=""
}

apt_deb822_from() {
    local f="$1" _l
    while IFS= read -r _l || [ -n "$_l" ]; do
        _l=$(printf '%s' "$_l" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        if [ -z "$_l" ]; then
            deb822_flush
            continue
        fi
        case "$_l" in
            \#*) continue ;;
            URIs:*) _deb_uris="${_l#URIs:}" ;;
            Suites:*) _deb_suites="${_l#Suites:}" ;;
            Components:*) _deb_comps="${_l#Components:}" ;;
        esac
    done < "$f"
    deb822_flush
}

apt_oneline_from() {
    local f="$1" line uri idx r
    while IFS= read -r line || [ -n "$line" ]; do
        line=${line%%#*}
        read -ra _tokens <<< "$line"
        [ "${#_tokens[@]}" -ge 2 ] || continue
        uri=""; idx=0
        while [ "$idx" -lt "${#_tokens[@]}" ]; do
            case "${_tokens[$idx]}" in
                *://*) uri="${_tokens[$idx]}"; break ;;
            esac
            idx=$((idx + 1))
        done
        [ -n "$uri" ] || continue
        r=$((idx + 1))
        suite="${_tokens[$r]:-}"
        comps=""
        r=$((r + 1))
        while [ "$r" -lt "${#_tokens[@]}" ]; do
            case "${_tokens[$r]}" in
                \[*\]*) ;;
                *) comps="${comps:+$comps,}${_tokens[$r]}" ;;
            esac
            r=$((r + 1))
        done
        classify_uri "$uri" "$suite" "$comps"
    done < "$f"
    unset _tokens
}

for _src in "$ROOT/etc/apt/sources.list" "$ROOT"/etc/apt/sources.list.d/*; do
    [ -f "$_src" ] || continue
    case "$_src" in
        *.sources) apt_deb822_from "$_src" ;;
        *.list) apt_oneline_from "$_src" ;;
        *) apt_oneline_from "$_src" ;;
    esac
done
unset _src

# ---------- manifest loading ----------------------------------------------
DGOAL_ID=""; DGOAL_VER=""; DGOAL_CODENAME=""; DGOAL_ARCH=""; SB_GOAL=""
declare -a ROLES=()
_cur=""; _curbin=""; _curpkg=""; _curgpu=""; _cuoneof=0

if [ -z "$MANIFEST" ]; then
    contract_invalid "manifest_required"
fi
if [ ! -f "$MANIFEST" ]; then
    contract_invalid "manifest_unreadable"
fi
if ! read -r < "$MANIFEST" 2>/dev/null; then
    contract_invalid "manifest_unreadable"
fi

while IFS= read -r _l || [ -n "$_l" ]; do
    _l=$(printf '%s' "$_l" | sed 's/[[:space:]]*$//')
    case "$_l" in
        ''|\#*) continue ;;
        distro.id=*) DGOAL_ID="${_l#distro.id=}" ;;
        distro.version=*) DGOAL_VER="${_l#distro.version=}" ;;
        distro.codename=*) DGOAL_CODENAME="${_l#distro.codename=}" ;;
        distro.arch=*) DGOAL_ARCH="${_l#distro.arch=}" ;;
        secure_boot=*) SB_GOAL="${_l#secure_boot=}" ;;
        role.id=*)
            if [ -n "$_cur" ]; then
                ROLES+=("$_cur|$_curbin|$_curpkg|$_curgpu|$_cuoneof")
            fi
            _cur="${_l#role.id=}"; _curbin=""; _curpkg=""; _curgpu=""; _cuoneof=0
            ;;
        role.bin=*) _curbin="${_l#role.bin=}" ;;
        role.pkg=*) _curpkg="${_l#role.pkg=}" ;;
        role.gpu=*) _curgpu="${_l#role.gpu=}" ;;
        role.one_of=*) _cuoneof=1 ;;
    esac
done < "$MANIFEST"
if [ -n "$_cur" ]; then
    ROLES+=("$_cur|$_curbin|$_curpkg|$_curgpu|$_cuoneof")
fi
unset _cur _curbin _curpkg _curgpu _cuoneof _l

if [ -z "$DGOAL_ID" ]; then
    contract_invalid "missing_distro_id"
fi

# ---------- package policy ------------------------------------------------
declare -A PKG_INST PKG_CAND PKG_UNKNOWN
probe_policy() {
    local pkg="$1" out inst cand
    if [ -z "${PKG_INST[$pkg]+_}" ]; then
        # LC_ALL/LANG=C scoped to this apt-cache call only -> output is not
        # localized by host gettext. Parser also tolerates localized labels.
        out=$(cmd_out_lc apt-cache policy "$pkg")
        if [ -z "$out" ]; then
            PKG_INST[$pkg]=""; PKG_CAND[$pkg]=""; PKG_UNKNOWN[$pkg]=1
            return
        fi
        inst=$(printf '%s\n' "$out" | grep -E '^[[:space:]]*([Ii]nstalled|[Ii]nstalado):' | head -n 1 | sed -E 's/^[[:space:]]*([Ii]nstalled|[Ii]nstalado):[[:space:]]*//')
        cand=$(printf '%s\n' "$out" | grep -E '^[[:space:]]*([Cc]andidate|[Cc]andidato):' | head -n 1 | sed -E 's/^[[:space:]]*([Cc]andidate|[Cc]andidato):[[:space:]]*//')
        [ "$inst" = "(none)" ] && inst=""
        [ "$cand" = "(none)" ] && cand=""
        PKG_INST[$pkg]="$inst"; PKG_CAND[$pkg]="$cand"; PKG_UNKNOWN[$pkg]=0
    fi
}

# ---------- identity / goal evaluation ------------------------------------
identity_result="ok"
declare -a VIOLATIONS=()
sb_status="ok"

# Each goal field is evaluated independently so every real mismatch is
# recorded. A mismatch is a failed requirement (fail); missing data is
# downgraded to "unknown" only when no real mismatch has been seen.
check_goal() {
    local goal="$1" actual="$2" name="$3"
    [ -n "$goal" ] || return 0
    if [ -z "$actual" ]; then
        [ "$identity_result" = "fail" ] || identity_result="unknown"
    elif [ "$actual" != "$goal" ]; then
        VIOLATIONS+=("$name")
        identity_result="fail"
    fi
}
check_goal "$DGOAL_ID" "$os_id" "os_id"
check_goal "$DGOAL_VER" "$os_version" "os_version"
check_goal "$DGOAL_CODENAME" "$os_codename" "os_codename"
check_goal "$DGOAL_ARCH" "$host_arch" "architecture"

if [ "$SB_GOAL" = "any" ] || [ -z "$SB_GOAL" ]; then
    sb_status="ok"
elif [ "$sb" = "unknown" ]; then
    sb_status="unknown"
elif [ "$sb" != "$SB_GOAL" ]; then
    sb_status="fail"
    VIOLATIONS+=("secure_boot")
fi

# ---------- role evaluation ----------------------------------------------
ROLES_JSON=""
n_ok=0; n_missing=0; n_fail=0; n_unknown=0; n_unresolved=0

for _e in "${ROLES[@]}"; do
    IFS='|' read -r rid rbins rpkgs rgpu roneof <<< "$_e"
    rstatus="ok"; rreason=""; seen_any_req=0

    if [ -n "$rgpu" ]; then
        seen_any_req=1
        if [ "$graphics_vendor" != "$rgpu" ]; then
            rstatus="fail"; rreason="gpu_mismatch"
        fi
    fi

    # binaries
    missing_bins=""
    if [ -n "$rbins" ]; then
        seen_any_req=1
        bin_count=0; bin_present_count=0
        IFS=',' read -ra _ba <<< "$rbins"
        for _b in "${_ba[@]}"; do
            [ -n "$_b" ] || continue
            bin_count=$((bin_count + 1))
            if cmd_exists "$_b"; then
                bin_present_count=$((bin_present_count + 1))
            else
                missing_bins="${missing_bins:+$missing_bins,}$_b"
            fi
        done
        unset _ba _b
        if [ "$roneof" = "1" ]; then
            if [ "$bin_present_count" -ge 1 ]; then
                missing_bins=""
                [ "$rstatus" = "missing" ] && rstatus="ok"
            else
                rstatus="missing"
            fi
        else
            [ "$bin_count" -eq "$bin_present_count" ] || rstatus="missing"
        fi
    fi

    # packages
    unresolvable_pkgs=""; unknown_pkgs=""; missing_pkgs=""
    if [ -n "$rpkgs" ]; then
        seen_any_req=1
        IFS=',' read -ra _pa <<< "$rpkgs"
        for _p in "${_pa[@]}"; do
            [ -n "$_p" ] || continue
            probe_policy "$_p"
            if [ "${PKG_UNKNOWN[$_p]}" = "1" ]; then
                unknown_pkgs="${unknown_pkgs:+$unknown_pkgs,}$_p"
            elif [ -z "${PKG_INST[$_p]}" ]; then
                if [ -n "${PKG_CAND[$_p]}" ]; then
                    missing_pkgs="${missing_pkgs:+$missing_pkgs,}$_p"
                else
                    unresolvable_pkgs="${unresolvable_pkgs:+$unresolvable_pkgs,}$_p"
                fi
            fi
        done
        unset _pa _p
    fi

    # status precedence: fail > unknown > missing > unresolved > ok
    [ "$rstatus" = "fail" ] || {
        if [ -n "$unresolvable_pkgs" ]; then rstatus="fail"; rreason="package_unavailable"; fi
    }
    [ "$rstatus" = "fail" ] || {
        if [ -n "$unknown_pkgs" ]; then rstatus="unknown"; rreason="tool_or_data_missing"; fi
    }
    [ "$rstatus" = "fail" ] || [ "$rstatus" = "unknown" ] || {
        if [ -n "$missing_bins" ] || [ -n "$missing_pkgs" ]; then rstatus="missing"; fi
    }
    if [ "$seen_any_req" = "0" ]; then rstatus="unresolved"; fi

    # per-role JSON
    rbin_json=""
    if [ -n "$rbins" ]; then
        IFS=',' read -ra _ba <<< "$rbins"
        for _b in "${_ba[@]}"; do
            [ -n "$_b" ] || continue
            _p=0; cmd_exists "$_b" && _p=1
            rbin_json="${rbin_json:+$rbin_json,}\"$(json_escape "$_b")\":$([ "$_p" = 1 ] && printf true || printf false)"
        done
        unset _ba _b _p
    fi
    rpkg_json=""
    if [ -n "$rpkgs" ]; then
        IFS=',' read -ra _pa <<< "$rpkgs"
        for _p in "${_pa[@]}"; do
            [ -n "$_p" ] || continue
            if [ "${PKG_UNKNOWN[$_p]}" = "1" ]; then
                _pst="unknown"
            elif [ -n "${PKG_INST[$_p]}" ]; then
                _pst="ok"
            elif [ -n "${PKG_CAND[$_p]}" ]; then
                _pst="missing"
            else
                _pst="fail"
            fi
            rpkg_json="${rpkg_json:+$rpkg_json,}\"$(json_escape "$_p")\":{\"installed\":$([ -n "${PKG_INST[$_p]}" ] && printf true || printf false),\"candidate\":$([ -n "${PKG_CAND[$_p]}" ] && printf true || printf false),\"status\":\"$_pst\"}"
        done
        unset _pa _p _pst
    fi

    ROLES_JSON="${ROLES_JSON:+$ROLES_JSON,}"
    ROLES_JSON="$ROLES_JSON{\"id\":\"$(json_escape "$rid")\",\"status\":\"$rstatus\",\"reason\":\"$(json_escape "$rreason")\",\"gpu\":\"$rgpu\",\"binaries\":{$rbin_json},\"packages\":{$rpkg_json}}"

    case "$rstatus" in
        ok) n_ok=$((n_ok + 1)) ;;
        missing) n_missing=$((n_missing + 1)) ;;
        fail) n_fail=$((n_fail + 1)) ;;
        unknown) n_unknown=$((n_unknown + 1)) ;;
        unresolved) n_unresolved=$((n_unresolved + 1)) ;;
    esac
done
unset _e rid rbins rpkgs rgpu roneof

# ---------- exit code -----------------------------------------------------
# Deterministic mapping: 11 for any real failed requirement, otherwise 10 for
# any missing/unknown/unresolved datum or tool, otherwise 0 on success.
exit_code=0
result="pass"
if [ "$identity_result" = "fail" ] || [ "$sb_status" = "fail" ] || [ "$n_fail" -gt 0 ]; then
    exit_code=11; result="fail"
elif [ "$identity_result" = "unknown" ] || [ "$sb_status" = "unknown" ] \
     || [ "$n_missing" -gt 0 ] || [ "$n_unknown" -gt 0 ] || [ "$n_unresolved" -gt 0 ]; then
    exit_code=10; result="unknown"
fi

# ---------- assemble output ----------------------------------------------
ROLES_JSON_PRINT="$ROLES_JSON"
if [ "${#ROLES[@]}" = "0" ]; then ROLES_JSON_PRINT=""; fi
RSTATUS_ALL="[${ROLES_JSON_PRINT}]"

VIOL_JSON=""
for _v in "${VIOLATIONS[@]}"; do
    VIOL_JSON="${VIOL_JSON:+$VIOL_JSON,}\"$(json_escape "$_v")\""
done
VIOL_ALL="[${VIOL_JSON}]"
unset _v

printf '{\n'
printf '  "tool":"%s",\n' "$TOOL"
printf '  "schema":"%s",\n' "$SCHEMA"
printf '  "contract_valid":true,\n'
printf '  "identity":{\n'
printf '    "id":"%s",\n' "$(json_escape "$os_id")"
printf '    "version_id":"%s",\n' "$(json_escape "$os_version")"
printf '    "codename":"%s",\n' "$(json_escape "$os_codename")"
printf '    "architecture":{"dpkg":"%s","uname":"%s","effective":"%s"},\n' \
    "$(json_escape "$dpkg_arch")" "$(json_escape "$um_arch")" "$(json_escape "$host_arch")"
printf '    "kernel":"%s",\n' "$(json_escape "$host_kernel")"
printf '    "boot_mode":"%s",\n' "$( [ "$efi" = "1" ] && printf uefi || printf legacy )"
printf '    "result":"%s",\n' "$identity_result"
printf '    "violations":%s\n' "$VIOL_ALL"
printf '  },\n'
printf '  "secure_boot":{"state":"%s","goal":"%s","status":"%s"},\n' "$sb" "$SB_GOAL" "$sb_status"
printf '  "gpu":{\n'
printf '    "display_vendor":"%s",\n' "$(json_escape "$graphics_vendor")"
printf '    "vendors":"%s",\n' "$(json_escape "$gpu_vendors_list")"
printf '    "graphics_module":"%s"\n' "$(json_escape "$graphics_module")"
printf '  },\n'
printf '  "modules":{"loaded":"%s"},\n' "$(json_escape "$modules_csv")"
printf '  "apt":{\n'
printf '    "sources_count":%d,\n' "$sources_count"
printf '    "official_components":"%s",\n' "$(json_escape "$(redact_domains "$official_components")")"
printf '    "has_third_party":%s,\n' "$( [ "$has_third_party" = "1" ] && printf true || printf false )"
printf '    "third_party_count":%d,\n' "$third_party_count"
printf '    "third_party_suites":"%s"\n' "$(json_escape "$(redact_domains "$third_party_suites")")"
printf '  },\n'
printf '  "rollback":"none",\n'
printf '  "roles":%s,\n' "$RSTATUS_ALL"
printf '  "summary":{\n'
printf '    "result":"%s",\n' "$result"
printf '    "roles_ok":%d,"roles_missing":%d,"roles_fail":%d,"roles_unknown":%d,"roles_unresolved":%d,\n' \
    "$n_ok" "$n_missing" "$n_fail" "$n_unknown" "$n_unresolved"
printf '    "exit_code":%d\n' "$exit_code"
printf '  }\n'
printf '}\n'

exit "$exit_code"
