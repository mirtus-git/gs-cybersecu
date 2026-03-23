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
| Historique d'exécution | Base SQLite + logs texte quotidiens, export JSON et CSV |
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

# Utiliser un template de script
gscs template list
gscs template use recon/nmap-quick -o /opt/scripts/nmap_quick.sh --register

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

gscs template list        Liste les templates disponibles
gscs template show <nom>  Prévisualise un template
gscs template use <nom> -o <fichier>
                          Génère un script depuis un template
      --register          Enregistre automatiquement le script généré
      --force             Écrase si le fichier existe déjà

gscs export               Exporte la bibliothèque en archive JSON
  -o, --output            Fichier de sortie (défaut : stdout)
  -c, --category          N'exporter qu'une catégorie
      --no-content        Métadonnées uniquement (sans le contenu des fichiers)

gscs import <archive>     Importe depuis une archive JSON
      --skip-existing     Ignore les scripts déjà enregistrés
      --update            Écrase les scripts existants sans confirmation
      --no-restore        Ne pas restaurer les fichiers depuis l'archive
      --dry-run           Prévisualise sans appliquer les changements
```

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
