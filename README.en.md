# GS-CYBERsecu

**Script manager for cybersecurity and pentesting on Linux.**

> [🇫🇷 Français](README.md) · 🇬🇧 English

No required dependencies. Works on any Linux distribution with Python 3.10 or higher.

<br>

## Features

| Feature | Details |
|---|---|
| Script organisation | Categories: `recon`, `exploit`, `post-exploit`, `forensic`, `custom` |
| Advanced search | Filters by keyword, tags (AND logic), category, language, date, dependencies, author |
| Secure execution | Firejail or Docker sandboxing with automatic backend detection |
| Dependency checking | System binaries, Python packages, Go, Ruby gems, custom shell checks |
| Execution history | SQLite audit log + daily plain-text log files, JSON and CSV export |
| CLI interface | Built on stdlib `argparse`, zero external dependencies |
| GUI interface | Tkinter GUI bundled with Python (`gscs gui`) |
| Configuration | JSON or YAML files with project-level overrides and environment variable support |

<br>

## Installation

> The package is not yet published on PyPI. Install it from source.

### Kali / Parrot / BlackArch — recommended method

```bash
sudo apt install pipx
pipx ensurepath

git clone https://github.com/mirtus-git/gs-cybersecu
cd gs-cybersecu
pipx install .
```

With coloured output and YAML support:

```bash
pipx install ".[all]"
```

### Any distribution via venv

```bash
git clone https://github.com/mirtus-git/gs-cybersecu
cd gs-cybersecu

python3 -m venv .venv
source .venv/bin/activate
pip install .

gscs --help
```

### Development mode

```bash
git clone https://github.com/mirtus-git/gs-cybersecu
cd gs-cybersecu

python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/
```

<br>

## Quick Start

```bash
# Register a script
gscs add /opt/scripts/nmap_scan.sh --category recon --tags "nmap,port-scan" --desc "Port scanner"

# List all scripts
gscs list

# Search by keyword or tag
gscs search nmap
gscs search --category recon --tag nmap --tag stealth

# Run a script (sandboxed with Firejail if available)
gscs run nmap_scan --args "-sV 192.168.1.0/24"

# Check dependencies
gscs deps check nmap_scan

# View execution history
gscs history --last 20
gscs history --export csv --output logs.csv

# Remove a script
gscs remove nmap_scan

# Launch the GUI
gscs gui
```

<br>

## Command Reference

```
gscs add <path>           Register a script
  -n, --name              Name override (default: filename stem)
  -c, --category          recon | exploit | post-exploit | forensic | custom
  -l, --lang              python | bash | go | ruby | perl | other
  -t, --tags              Comma-separated tags
  -d, --desc              Short description
      --deps              Dependencies (e.g. "nmap,python:requests")
  -u, --update            Update if the script already exists

gscs search [keyword]     Search with filters
  -c, --category
  -t, --tag               Repeatable, AND logic
  -l, --lang
      --after, --before   Date filters YYYY-MM-DD
      --dep               Filter by dependency name
  -f, --format            table | json

gscs run <name>           Execute a script
      --args "..."        Arguments to pass to the script
      --sandbox           auto | firejail | docker | none
      --dry-run           Print the command without running it
      --force             Run without sandbox

gscs list                 List all scripts
gscs info <name>          Full details for a script
gscs history              Execution log
gscs deps check <name>    Check dependencies
gscs deps install <name>  Show install commands for missing deps
gscs remove <name>        Remove a script
gscs gui                  Launch the GUI
```

<br>

## Dependency Format

When adding a script with `--deps`:

| Format | Check performed |
|---|---|
| `nmap` | System binary (`which nmap`) |
| `python:requests` | Python package (`importlib`) |
| `go:subfinder` | Go binary in PATH |
| `ruby:nokogiri` | Ruby gem |
| `cmd:my command` | Arbitrary shell command (exit code 0 = satisfied) |

<br>

## Sandboxing

Automatic detection follows this priority order:

1. **Firejail** — lightweight, per-category profiles, network isolation
2. **Docker** — full container isolation, per-language image configuration
3. **None** — requires the `--force` flag

Install Firejail for best results:

```bash
sudo apt install firejail     # Debian / Ubuntu / Kali
sudo dnf install firejail     # Fedora / RHEL
sudo pacman -S firejail       # Arch / BlackArch
```

<br>

## Configuration

A config file is created automatically at `~/.config/gscs/config.json` on first run.

```json
{
  "storage": {
    "scripts_dir": "~/.local/share/gscs/scripts",
    "db_path": "~/.local/share/gscs/gscs.db",
    "logs_dir": "~/.local/share/gscs/logs",
    "log_retention_days": 90
  },
  "execution": {
    "sandbox": "auto",
    "timeout": 300,
    "require_force_no_sandbox": true
  }
}
```

Available environment variable overrides:

| Variable | Effect |
|---|---|
| `GSCS_DB_PATH` | Database path |
| `GSCS_SCRIPTS_DIR` | Scripts directory |
| `GSCS_SANDBOX` | Sandbox mode |
| `GSCS_TIMEOUT` | Execution timeout in seconds |

For a project-level override, create a `.gs-cybersecu.json` file in your working directory.

<br>

## Requirements

Python 3.10 or higher is all that is strictly required. Everything else is optional.

| Component | Purpose |
|---|---|
| `rich` | Coloured terminal output (`pipx install ".[rich]"`) |
| `pyyaml` | YAML config file support (`pipx install ".[yaml]"`) |
| `firejail` or `docker` | Sandboxed execution |
| `python3-tk` | GUI (`sudo apt install python3-tk`) |

<br>

## License

MIT © 2026 mirtus-git
