"""Built-in script templates for common pentest tasks."""
from __future__ import annotations

from typing import TypedDict


class TemplateInfo(TypedDict):
    description: str
    category: str
    language: str
    tags: list[str]
    deps: list[str]
    content: str


TEMPLATES: dict[str, TemplateInfo] = {
    "recon/nmap": {
        "description": "Professional multi-phase Nmap reconnaissance (pro-grade)",
        "category": "recon",
        "language": "bash",
        "tags": ["nmap", "recon", "port-scan", "service-detection", "vuln", "osint"],
        "deps": ["nmap"],
        "content": """\
#!/usr/bin/env bash
# =============================================================================
# nmap_recon.sh  —  Professional Multi-Phase Nmap Reconnaissance
# =============================================================================
# Description : Complete Nmap scanner with phased workflow and reporting.
#
#   Phase 1  Host discovery        (ping sweep)
#   Phase 2  TCP port scan         (depth depends on --mode)
#   Phase 3  Service/version       (-sV --version-intensity 7)
#   Phase 4  NSE script scanning   (default + banner; +vuln in vuln mode)
#   Phase 5  OS fingerprinting     (requires root, --os flag)
#   Phase 6  UDP top-200 scan      (requires root, --udp flag)
#
# Output    : <dir>/pN_*.{nmap,gnmap,xml,html}  +  final summary
# Requires  : nmap >= 7.80
# Optional  : xsltproc (HTML reports), sudo/root (SYN scan, OS, UDP)
#
# Usage     : ./nmap_recon.sh [options] <target>
# =============================================================================
set -euo pipefail

readonly VERSION="1.0.0"
readonly SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"
readonly TS_START="$(date +%s)"

# ── Colors (auto-disabled outside a terminal) ─────────────────────────────
if [[ -t 1 ]]; then
    RED=$(tput setaf 1 2>/dev/null || echo '')
    GRN=$(tput setaf 2 2>/dev/null || echo '')
    YLW=$(tput setaf 3 2>/dev/null || echo '')
    BLU=$(tput setaf 4 2>/dev/null || echo '')
    MGT=$(tput setaf 5 2>/dev/null || echo '')
    CYN=$(tput setaf 6 2>/dev/null || echo '')
    BOLD=$(tput bold   2>/dev/null || echo '')
    DIM=$(tput dim     2>/dev/null || echo '')
    RST=$(tput sgr0    2>/dev/null || echo '')
else
    RED=''; GRN=''; YLW=''; BLU=''; MGT=''; CYN=''
    BOLD=''; DIM=''; RST=''
fi

readonly SEP="════════════════════════════════════════════════════════════"
readonly SUB="────────────────────────────────────────────────────────────"

# ── Defaults ─────────────────────────────────────────────────────────────────
MODE="standard"   # quick | standard | full | stealth | vuln
PORTS=""          # custom -p range (overrides mode)
TOP_PORTS=""      # override --top-ports N
TIMING=4          # nmap -T0..5
EXTRA_SCRIPTS=""  # extra NSE scripts (comma-separated)
OUTPUT_DIR=""     # default: ./recon_<target>_<date>/
NO_PING=false     # -Pn  skip host discovery
OS_DETECT=false   # phase 5: -O  (root)
UDP_SCAN=false    # phase 6: -sU (root)
VERBOSE=false
DRY_RUN=false
TARGET=""
OPEN_PORTS=""     # populated after phase 2

# ── Logging ──────────────────────────────────────────────────────────────────
_ts()  { date '+%H:%M:%S'; }
log()  { echo "${DIM}[$(_ts)]${RST} ${BLU}[*]${RST} $*"; }
ok()   { echo "${DIM}[$(_ts)]${RST} ${GRN}[+]${RST} $*"; }
warn() { echo "${DIM}[$(_ts)]${RST} ${YLW}[!]${RST} $*" >&2; }
err()  { echo "${DIM}[$(_ts)]${RST} ${RED}[-]${RST} $*" >&2; }
die()  { err "$*"; exit 1; }
dbg()  { "$VERBOSE" && echo "${DIM}[$(_ts)][D]${RST} $*" || true; }

section() {
    echo ""
    echo "${BOLD}${CYN}${SEP}${RST}"
    echo "${BOLD}${CYN}  $1${RST}"
    echo "${CYN}${SUB}${RST}"
}

banner() {
    echo "${BOLD}${MGT}"
    cat <<'BANNER'
  ╔═══════════════════════════════════════╗
  ║   GS-CYBERsecu  ·  nmap-recon        ║
  ╚═══════════════════════════════════════╝
BANNER
    echo "${RST}${DIM}  Professional Multi-Phase Nmap Reconnaissance  v${VERSION}${RST}"
    echo ""
}

# ── Usage ─────────────────────────────────────────────────────────────────────
usage() {
    cat <<EOF
${BOLD}Usage:${RST}
  ${SCRIPT_NAME} [options] <target>

${BOLD}Target:${RST}
  IP, CIDR range, hostname, or file path for nmap -iL

${BOLD}Scan modes  (-m):${RST}
  ${GRN}quick${RST}      Top 1000 TCP  | T4 | no scripts           ~  1 min
  ${GRN}standard${RST}   Top 5000 TCP  | T4 | default+banner       ~  5 min  (default)
  ${GRN}full${RST}       All 65535 TCP | T4 | default+banner       ~ 20 min
  ${GRN}stealth${RST}    Top 5000 TCP  | T2 | fragmented | random  ~ 15 min
  ${GRN}vuln${RST}       Top 5000 TCP  | T4 | default+banner+vuln  ~ 30 min

${BOLD}Options:${RST}
  -m, --mode <mode>        Scan mode  (default: standard)
  -p, --ports <range>      Custom port range, e.g. 22,80,443,8000-9000
      --top-ports <n>      Scan top N ports
  -T, --timing <0-5>       Nmap timing template  (default: 4)
  -o, --output <dir>       Output directory  (default: ./recon_TARGET_DATE)
      --scripts <list>     Additional NSE scripts, comma-separated
      --no-ping            Skip host discovery (-Pn)
      --os                 Phase 5: OS fingerprinting  (requires root)
      --udp                Phase 6: UDP top-200 scan   (requires root)
  -v, --verbose            Verbose output
      --dry-run            Print nmap commands without executing
  -h, --help               Show this help

${BOLD}Examples:${RST}
  ${SCRIPT_NAME} 10.10.14.5
  ${SCRIPT_NAME} -m full --os --udp 192.168.1.1
  ${SCRIPT_NAME} -m stealth -T2 --no-ping 10.10.10.0/24
  ${SCRIPT_NAME} -m vuln -o /tmp/audit 10.0.0.0/24
  ${SCRIPT_NAME} -p 80,443,8080-8090 --scripts "http-title,ssl-cert" 192.168.0.1

EOF
    exit 0
}

# ── Argument parsing ──────────────────────────────────────────────────────────
parse_args() {
    [[ $# -eq 0 ]] && { banner; usage; }
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -m|--mode)       MODE="$2";          shift 2 ;;
            -p|--ports)      PORTS="$2";         shift 2 ;;
               --top-ports)  TOP_PORTS="$2";     shift 2 ;;
            -T|--timing)     TIMING="$2";        shift 2 ;;
            -o|--output)     OUTPUT_DIR="$2";    shift 2 ;;
               --scripts)    EXTRA_SCRIPTS="$2"; shift 2 ;;
               --no-ping)    NO_PING=true;       shift   ;;
               --os)         OS_DETECT=true;     shift   ;;
               --udp)        UDP_SCAN=true;      shift   ;;
            -v|--verbose)    VERBOSE=true;       shift   ;;
               --dry-run)    DRY_RUN=true;       shift   ;;
            -h|--help)       usage ;;
            -*) die "Unknown option: $1 — run ${SCRIPT_NAME} --help" ;;
            *)  TARGET="$1"; shift ;;
        esac
    done
}

# ── Validation ────────────────────────────────────────────────────────────────
validate() {
    [[ -z "$TARGET" ]] && die "No target specified — run: ${SCRIPT_NAME} --help"
    local valid="quick standard full stealth vuln"
    [[ " ${valid} " == *" ${MODE} "* ]] || die "Invalid mode '${MODE}'. Valid: ${valid}"
    [[ "$TIMING" =~ ^[0-5]$ ]] || die "Timing must be 0–5, got: ${TIMING}"
    command -v nmap &>/dev/null || die "nmap not found — install: sudo apt install nmap"
    if { "$OS_DETECT" || "$UDP_SCAN" || [[ "$MODE" == "stealth" ]]; } && [[ $EUID -ne 0 ]]; then
        warn "OS detection, UDP, and SYN stealth require root — those phases will be skipped or degraded."
    fi
    dbg "$(nmap --version | head -1)"
}

# ── Output directory ──────────────────────────────────────────────────────────
setup_output() {
    local safe stamp
    safe="$(echo "$TARGET" | tr '/:' '__' | tr -c 'a-zA-Z0-9._-' '_')"
    stamp="$(date '+%Y%m%d_%H%M%S')"
    OUTPUT_DIR="${OUTPUT_DIR:-./recon_${safe}_${stamp}}"
    mkdir -p "$OUTPUT_DIR"
    ok "Output dir : ${BOLD}${OUTPUT_DIR}${RST}"
}

# ── Scan type: SYN (root) or TCP Connect (non-root) ──────────────────────────
_scan_type() { [[ $EUID -eq 0 ]] && echo "-sS" || echo "-sT"; }

# ── Execute one nmap phase ────────────────────────────────────────────────────
run_phase() {
    # run_phase <output_base> [nmap args...]
    local out="$1"; shift
    log "nmap $* -oA ${out}"
    "$DRY_RUN" && { warn "[DRY-RUN] nmap $* -oA ${out}"; return 0; }
    nmap "$@" -oA "$out" 2>&1 | tee "${out}.log"
}

# ── Phase 1: Host Discovery ───────────────────────────────────────────────────
phase1_discovery() {
    section "Phase 1 ── Host Discovery"
    if "$NO_PING"; then log "Skipped (--no-ping)"; return; fi
    local out="${OUTPUT_DIR}/p1_discovery"
    run_phase "$out" -sn -T4 "$TARGET"
    if [[ -f "${out}.gnmap" ]]; then
        local up
        up="$(grep -c 'Status: Up' "${out}.gnmap" 2>/dev/null || echo 0)"
        ok "Hosts up: ${BOLD}${GRN}${up}${RST}"
    fi
}

# ── Phase 2: Port Scan ────────────────────────────────────────────────────────
phase2_portscan() {
    section "Phase 2 ── TCP Port Scan  [${BOLD}${MODE}${RST}]"
    local out="${OUTPUT_DIR}/p2_portscan"
    local st timing
    st="$(_scan_type)"
    timing="-T${TIMING}"
    [[ "$MODE" == "stealth" ]] && timing="-T2"

    local -a port_args
    if   [[ -n "$PORTS" ]];     then port_args=(-p "$PORTS")
    elif [[ -n "$TOP_PORTS" ]]; then port_args=(--top-ports "$TOP_PORTS")
    else
        case "$MODE" in
            quick)         port_args=(--top-ports 1000) ;;
            full|vuln)     port_args=(-p-) ;;
            stealth)       port_args=(--top-ports 5000 -f --randomize-hosts) ;;
            *)             port_args=(--top-ports 5000) ;;
        esac
    fi

    run_phase "$out" "$st" $timing "${port_args[@]}" "$TARGET"

    if [[ -f "${out}.gnmap" ]]; then
        OPEN_PORTS="$(grep -oE '[0-9]+/open/tcp' "${out}.gnmap" | grep -oE '^[0-9]+' | sort -n | tr '\\n' ',' | sed 's/,$//' || true)"
    fi

    if [[ -z "$OPEN_PORTS" ]]; then
        warn "No open TCP ports found — check connectivity or try --no-ping."
    else
        ok "Open TCP ports: ${BOLD}${GRN}${OPEN_PORTS}${RST}"
    fi
}

# ── Phase 3: Service & Version Detection ──────────────────────────────────────
phase3_services() {
    section "Phase 3 ── Service & Version Detection"
    if [[ -z "$OPEN_PORTS" ]]; then warn "Skipped — no open ports."; return; fi
    local out="${OUTPUT_DIR}/p3_services"
    run_phase "$out" "$(_scan_type)" -T"${TIMING}" -sV --version-intensity 7 -p "$OPEN_PORTS" "$TARGET"
}

# ── Phase 4: NSE Script Scanning ──────────────────────────────────────────────
phase4_scripts() {
    section "Phase 4 ── NSE Script Scanning"
    if [[ -z "$OPEN_PORTS" ]]; then warn "Skipped — no open ports."; return; fi
    if [[ "$MODE" == "quick" ]]; then log "Skipped (quick mode)."; return; fi
    local out="${OUTPUT_DIR}/p4_scripts"
    local scripts="default,banner"
    [[ "$MODE" == "vuln" ]] && scripts="default,banner,vuln"
    [[ -n "$EXTRA_SCRIPTS" ]] && scripts="${scripts},${EXTRA_SCRIPTS}"
    run_phase "$out" "$(_scan_type)" -T"${TIMING}" --script "$scripts" -p "$OPEN_PORTS" "$TARGET"
}

# ── Phase 5: OS Fingerprinting ────────────────────────────────────────────────
phase5_os() {
    "$OS_DETECT" || return 0
    section "Phase 5 ── OS Fingerprinting"
    if [[ $EUID -ne 0 ]]; then warn "Skipped — requires root."; return; fi
    if [[ -z "$OPEN_PORTS" ]]; then warn "Skipped — no open ports."; return; fi
    run_phase "${OUTPUT_DIR}/p5_os" -sS -T"${TIMING}" -O --osscan-guess -p "$OPEN_PORTS" "$TARGET"
}

# ── Phase 6: UDP Top-200 ──────────────────────────────────────────────────────
phase6_udp() {
    "$UDP_SCAN" || return 0
    section "Phase 6 ── UDP Top-200 Scan"
    if [[ $EUID -ne 0 ]]; then warn "Skipped — requires root."; return; fi
    local out="${OUTPUT_DIR}/p6_udp"
    run_phase "$out" -sU -T4 --top-ports 200 --open "$TARGET"
    if [[ -f "${out}.gnmap" ]]; then
        local udp_open
        udp_open="$(grep -oE '[0-9]+/open/udp' "${out}.gnmap" | grep -oE '^[0-9]+' | sort -n | tr '\\n' ',' | sed 's/,$//' || true)"
        [[ -n "$udp_open" ]] && ok "Open UDP ports: ${BOLD}${GRN}${udp_open}${RST}"
    fi
}

# ── HTML Report ───────────────────────────────────────────────────────────────
generate_html() {
    command -v xsltproc &>/dev/null || return 0
    local xsl
    xsl="$(find /usr/share/nmap -name 'nmap.xsl' 2>/dev/null | head -1)"
    [[ -z "$xsl" ]] && return 0
    section "HTML Report Generation"
    local count=0
    for xml_file in "${OUTPUT_DIR}"/p*.xml; do
        [[ -f "$xml_file" ]] || continue
        local html_file="${xml_file%.xml}.html"
        xsltproc -o "$html_file" "$xsl" "$xml_file" 2>/dev/null && ok "HTML: $(basename "$html_file")" && (( count++ )) || true
    done
    [[ $count -gt 0 ]] && ok "${count} HTML report(s) generated." || true
}

# ── Final Summary ─────────────────────────────────────────────────────────────
summary() {
    local elapsed min sec
    elapsed=$(( $(date +%s) - TS_START ))
    min=$(( elapsed / 60 ))
    sec=$(( elapsed % 60 ))

    section "Scan Complete"

    local svc_file="${OUTPUT_DIR}/p3_services.nmap"
    if [[ -f "$svc_file" ]]; then
        echo ""
        echo "${BOLD}Open ports and services:${RST}"
        grep -E "^[0-9]+/tcp[[:space:]]+open" "$svc_file" | while IFS= read -r line; do
            echo "  ${GRN}${line}${RST}"
        done || true
    fi

    echo ""
    echo "${BOLD}Output files:${RST}"
    find "$OUTPUT_DIR" -maxdepth 1 -type f -name 'p*' | sort | while IFS= read -r f; do
        local sz
        sz="$(du -sh "$f" 2>/dev/null | cut -f1)"
        echo "  ${DIM}[${sz}]${RST}  $(basename "$f")"
    done

    echo ""
    echo "${BOLD}${CYN}${SEP}${RST}"
    echo "  ${BOLD}Target  :${RST}  ${TARGET}"
    echo "  ${BOLD}Mode    :${RST}  ${MODE}"
    echo "  ${BOLD}Ports   :${RST}  ${OPEN_PORTS:-none found}"
    echo "  ${BOLD}Duration:${RST}  ${min}m ${sec}s"
    echo "  ${BOLD}Output  :${RST}  ${OUTPUT_DIR}/"
    echo "${BOLD}${CYN}${SEP}${RST}"
    echo ""
}

# ── Cleanup on interrupt ──────────────────────────────────────────────────────
cleanup() {
    echo ""
    warn "Interrupted — partial results saved to: ${OUTPUT_DIR}/"
    exit 130
}
trap cleanup INT TERM

# ── Entry point ───────────────────────────────────────────────────────────────
main() {
    banner
    parse_args "$@"
    validate
    setup_output

    log "Target  : ${BOLD}${TARGET}${RST}"
    log "Mode    : ${BOLD}${MODE}${RST}"
    log "Timing  : T${TIMING}"
    [[ -n "$PORTS" ]] && log "Ports   : ${PORTS}"
    "$OS_DETECT"  && log "OS detection : enabled"
    "$UDP_SCAN"   && log "UDP scan     : enabled"
    "$DRY_RUN"    && warn "DRY-RUN — commands will be printed, not executed."

    phase1_discovery
    phase2_portscan
    phase3_services
    phase4_scripts
    phase5_os
    phase6_udp
    generate_html
    summary
}

main "$@"
""",
    },
}


def list_templates() -> list[tuple[str, str, str, str]]:
    """Return (name, category, language, description) for all templates."""
    return [
        (name, t["category"], t["language"], t["description"])
        for name, t in sorted(TEMPLATES.items())
    ]


def get_template(name: str) -> TemplateInfo | None:
    """Return template by exact name, or None if not found."""
    return TEMPLATES.get(name)


def search_templates(keyword: str) -> list[str]:
    """Return template names matching keyword in name, description, or tags."""
    kw = keyword.lower()
    return [
        name
        for name, t in TEMPLATES.items()
        if kw in name.lower()
        or kw in t["description"].lower()
        or any(kw in tag for tag in t["tags"])
    ]
