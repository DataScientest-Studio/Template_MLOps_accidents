# Makefile (version ed02) à la racine Template_MLOps_accidents

# ==========================================
# --- CONFIGURATION GLOBALE (Directives) ---
# ==========================================
# Sur Ubuntu, /bin/sh pointe vers dash ultra-rapide et léger, mais il est très "strict
# Selon les machines, /bin/sh peut aussi pointer autre part
# Comme /bin/bash est beaucoup plus puissant que dash. On va l'utiliser par défaut.
# et ainsi on garantit le même fonctionnement quelque soit la machine
# Doit être la 1ème ligne de commande
SHELL := /bin/bash

# Indiquer que ces cibles ne sont pas des fichiers
.PHONY: install setup-ci quality pipeline push setup run all

# Raccourci : taper juste "make" lancera uniquement run = quality pipeline push
.DEFAULT_GOAL := run

# ========================================
# --- VARIABLES (Paramètres du Projet) ---
# ========================================
# ex: make all MSG="Upd periodic" et = msg de commit par défaut si on oublie de le préciser
# ? permet d'assigner de façon conditionnelle uniquement si MSG n'est pas défini dans une commande
# DANS LE make xxx MSG="yyy" ON DOIT METTRE LES ""
# Mais pour la variable surtout pas sinon le git commit -m "$(MSG)" || @echo "Rien à commiter"
# plante car il y aura ""xxxx"" et donc inohérent
MSG ?= Mise à jour automatique du pipeline
DAGSHUB_USER ?= sage-flfay

# Définition du chemin pour uv (sinon pb avec Makefile qui perd uv à la ligne suivante)
UV_BIN = $(HOME)/.local/bin/uv
UV_PATH := $(HOME)/.local/bin

# Pour utiliser uv au lieu de $(UV_BIN) uniquement dans le MakeFile.
# Avantage: pour la cible "pipeline:" en faisant uv run dvc repro, 
# dvc.yaml en hérite mais uniquement dans ce cas. Donc on rajoute UV_PATH au PATH
export PATH := $(UV_PATH):$(PATH)
# NB: Chaque ligne de commande est vue comme un Shell (avec ".ONESHELL:" présent, c'est pour chaque cible)
# Ainsi, après import de uv, on passe à la ligne de commande suivante ET l'export PATH, lui,
# est réinjecté par Make dans chaque nouveau Shell qu'il ouvre <=> donc pour chaque nouvelle ligne commande

# On assigne de façon définitive (les :)
REPO := Template_MLOps_accidents
CUR_DIR := $(HOME)/$(REPO)

# Chemin absolu du fichier Makefile
# ROOT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
# Inutilisé pour le moment mais gardé au cas où!!

# ====================================
# --- GROUPE DE COMMANDE AVEC MAKE ---
# ====================================
# NB: penser à rajouter MSG = “xxx” utile pour le git commit
# Initialisation (à faire une fois au début)
setup: install

# cycle de dev (à faire à chaque changement de code/csv)
run: quality pipeline push

# Tout faire d’un coup
all: setup run

# =================================================
# --- SETUP COMPLET (À lancer la première fois) ---
# =================================================
# NB: ne jamais mettre de commentaire après \ car génère une erreur
# @ devant une commande (ex: @if) pour que la commande ne soit pas affichée
# Pour les if comme on a déjà @if, la commande echo "xxx" n'est donc pas affichée et donc pas de risque d'avoir le message affiché 2 fois

install:
	@# ******************************************************************************************************
	@# 0. Vérification des clés et code secrets dans le make (Priorité n°1)
	@# ******************************************************************************************************

	@if [ -z "$(DAGSHUB_ACCESS_KEY_ID)" ] || [ -z "$(DAGSHUB_SECRET_ACCESS_KEY)" ]; then \
		echo "---------------------------------------------------------------------------------"; \
		echo "❌ ERREUR : Clés DagsHub manquantes !"; \
		echo "👉 Commande : make setup DAGSHUB_ACCESS_KEY_ID=XXX DAGSHUB_SECRET_ACCESS_KEY=YYY"; \
		echo "---------------------------------------------------------------------------------"; \
		echo "💡 NOTE : L'erreur 'make: *** Error 1' qui va suivre est NORMALE,"; \
		echo "          elle confirme l'arrêt de la procédure."; \
		exit 1; \
	fi

	@# ******************************************************************************************************
	@# 1. Installation de uv si absent
	@# ******************************************************************************************************

	@if [ ! -f $(UV_BIN) ]; then \
		echo "🚀 Installation de uv..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	else \
		echo "✅ uv est déjà installé."; \
	fi

	@echo "Vérification de la version"
	uv --version

	@# ******************************************************************************************************
	@# 2. Création du .venv si absent
	@# ******************************************************************************************************

	@if [ ! -d ".venv" ]; then \
		echo "🌱 Création de l'environnement virtuel (.venv)..."; \
		uv venv; \
	fi

	@# ******************************************************************************************************
	@# 3. Gestion des dépendances
	@# ******************************************************************************************************

	@# 3.1 : Migration (Si absent, on le crée à partir du .txt)
	@# NB: grep -vE '^\s*#|^-e|^\s*$$'
	@#   -vE : exclut toutes les lignes qui correspondent à :
	@#     ^\s*# : commence par # (avec ou sans espaces avant) -> commentaires
	@#     ^-e   : commence par -e -> installation locale éditable
	@#     ^\s*$$ : ligne vide
	@# uv init --lib --no-readme : 
	@#     uv init : crée le fichier pyproject.toml;
	@#     --lib : crée si nécessaire __init__.py dans chaque dossier 
	@#             = projet configuré comme une bibliothèque (ou un package structuré).
	@#     --no-readme : ne pas créer README.md
	@# uv add : remplit le pyproject.toml ET génère le uv.lock initial
	@# exclusion de -e . dans le grep pour éviter risque conflit de syntaxe de uv add
	@# uv pip install -e . : pour installer le projet en mode éditable (cf requirements.txt pour explication)
	@if [ ! -f pyproject.toml ] && [ -f requirements.txt ]; then \
		echo "📄 Installation via requirements.txt..."; \
		echo "📄 Création pyproject.toml via uv init"; \
		uv init --lib --no-readme; \
		echo "⚙️  Migration requirements.txt vers pyproject.toml ET creation uv.lock via uv add"; \
		uv add $$(grep -vE '^\s*#|^-e|^\s*$$' requirements.txt); \
		uv pip install -e .; \
	fi

	@# 3.2 : Installation (car .toml présent) / Synchronisation
	@# uv sync : vérifie que le .venv correspond exactement au uv.lock (installe/supprime si besoin)
	@echo "🔄 Synchronisation de l'environnement virtuel..."
	@uv sync || (echo "❌ Erreur 1 : pyproject.toml introuvable ou corrompu !"; exit 1)

	@# ******************************************************************************************************
	@# 4. Initialisation de DVC avec signature locale (.AccidentsSetupDVC_AlreadyDone)
	@# ******************************************************************************************************

	@# Commentaires pour les différentes instructions SI LE SETUP N'A PAS ETE FAIT PAR CE MAKEFILE
	@# rm -rf .dvc : on supprime le dossier .dvc : cela emporte config ET config.local d'un coup.
	@#   - Ainsi, on part toujours du même état quelque soit la machine
	@#   - NB: -f: si le/les rep/fichiers pas présent on passe à la suite
	@# uv run dvc init --no-scm :  Initialisation du fichier .dvc/config
	@#   - --no-scm (Srce Ctrl Management): ne pas toucher au .gitignore s’il existe

	@if [ -f ".AccidentsSetupDVC_AlreadyDone" ]; then \
		echo "---------------------------------------------------------------------------------"; \
		echo "🛡️  SIGNATURE DÉTECTÉE : .AccidentsSetupDVC_AlreadyDone"; \
		echo "✅ DVC déjà configuré via Makefile. La configuration actuelle est préservée."; \
		echo "---------------------------------------------------------------------------------"; \
	else \
		echo "🧹 Aucune signature : Nettoyage complet et configuration initiale de DVC..."; \
		rm -rf .dvc; \
		uv run dvc init --no-scm; \
		touch .AccidentsSetupDVC_AlreadyDone; \
	fi

	@# On crée 'origin' directement en mode S3 car plus robuste et optimisé que le HTTPS
	@# Dans config, on configure le remote origin par défaut grâce à -d 
	@# Dans config, on fournit l'URL du remote. --force oblige à remplacer l'URL si déjà présent
	@# NB: --force inutile ici (on part de 0) mais il est présent pour les règles de bonne pratique de robustesse
	@echo "🔗 Configuration du remote S3 DagsHub pour $(DAGSHUB_USER)/$(REPO)..."; \
	uv run dvc remote add -d --force origin s3://dvc; \

	@# On définit l'URL technique S3 de DagsHub
	uv run dvc remote modify origin endpointurl https://dagshub.com/$(DAGSHUB_USER)/$(REPO).s3

	@# ******************************************************************************************************
	@# 5. Section sécurité uniquement locale uniquement
	@# ******************************************************************************************************

	@# On crée ou on met à jour le fichier local .dvc/config_local avec les clées et codes secrets
	@echo "uv run dvc remote modify origin --local access_key_id ************"
	@# "$(DAGSHUB_xxxx_KEY_ID)" : on le met toujours entre guillemet dans le Makefile pour être interprété
	@# comme une chaine de caractère et ainsi éviter une potentielle commande dû à des caractères spéciaux
	@uv run dvc remote modify origin --local access_key_id "$(DAGSHUB_ACCESS_KEY_ID)"
	@echo "uv run dvc remote modify origin --local secret_access_key ************"
	@uv run dvc remote modify origin --local secret_access_key "$(DAGSHUB_SECRET_ACCESS_KEY)"
	@echo "✅ Identifiants configurés (Valeurs masquées pour la sécurité)."

	@# ******************************************************************************************************
	@# 6. Initialisation ou update du .gitignore sous la racine pour les règles dvc
	@# ******************************************************************************************************

	@echo "🛠️ Vérification/Upate des protections dans $(CUR_DIR)...."
	@# Crée le fichier s'il n'existe pas, sinon ne fait rien
	@touch .gitignore
	@# -qxF: q (quiet): mode silence, x (exact match): tous les carctères entre " et ";
	@# F (Fixed Strings): à traiter comme une chaine de caractère brute
	@grep -qxF ".venv/" .gitignore || echo ".venv/" >> .gitignore
	@grep -qxF "__pycache__/" .gitignore || echo "__pycache__/" >> .gitignore
	@grep -qxF "/data/" .gitignore || echo "/data/" >> .gitignore
	@grep -qxF "/models/" .gitignore || echo "/models/" >> .gitignore
	@grep -qxF "/.dvc/cache/" .gitignore || echo "/.dvc/cache/" >> .gitignore
	@grep -qxF "/.dvc/tmp/" .gitignore || echo "/.dvc/tmp/" >> .gitignore
	@grep -qxF "/.dvc/config.local" .gitignore || echo "/.dvc/config.local" >> .gitignore
	@echo "✅ $(CUR_DIR).gitignore réinitialisé/updaté proprement."

	@# ******************************************************************************************************
	@# 7. Configuration du terminal pour utiliser uv en mode manuel
	@# ******************************************************************************************************

	@echo " --------------------------------------------------------------------"
	@echo "--- 🔧 Configuration du terminal pour utiliser uv en mode manuel ---"
	@echo " --------------------------------------------------------------------"
	@# Test de l'existence du .bashrc (dans le home) et mise à jour si présent (et si pas déjà fait)
	@if [ -f ~/.bashrc ]; then \
		if grep -qF "$(UV_PATH)" ~/.bashrc; then \
			echo "✅ Le PATH pour uv est déjà configuré dans ~/.bashrc."; \
		else \
			echo 'export PATH="$(UV_PATH):$$PATH"' >> ~/.bashrc; \
			echo "🚀 PATH pour uv ajouté à ~/.bashrc."; \
			echo "👉 ACTION : Tapez 'source ~/.bashrc' pour utiliser 'uv' sans le Makefile."; \
		fi \
	else \
		ech ""; \
		echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"; \
		echo "⚠️ WARNING : ~/.bashrc introuvable."; \
		echo "Faire manuellement la commande export PATH := $(UV_PATH):$(PATH)"; \
		echo "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"; \
	fi

# ==========================================================
# --- SETUP CONTINUOUS INTEGRATION (pour python-app.yml) ---
# ==========================================================
setup-ci:
	@# uniquement utilisé dans python-app.yml pour le workflow de CI (ex: GitHub Actions)
	@# git push déclenche automatiquement python-app.yml et donc cette séquence
	@echo "🛠️ Préparation de l'environnement pour GitHub Actions..."
	
	@# 1. Synchronisation stricte
	@# --frozen : garantit que uv ne cherchera pas à mettre à jour le uv.lock. 
	@# Si le lock est absent ou incohérent, la commande échoue (sécurité).
	@echo "🔄 Installation via uv.lock..."
	uv sync --frozen || (echo "❌ Erreur 1 : Fichier uv.lock absent ou corrompu !"; exit 1)

	@# 2. Installation du projet en mode éditable (sécurité pour les imports)
	@# Refait par sécurité
	uv pip install -e .

	@# 3. Vérification des secrets et Configuration DVC (sans tout réinitialiser)
	@echo "🔐 Vérification des variables d'accès DagsHub..."
	@if [ -z "$(DAGSHUB_ACCESS_KEY_ID)" ] || [ -z "$(DAGSHUB_SECRET_ACCESS_KEY)" ]; then \
		echo "❌ Erreur 1: Les secrets DAGSHUB ne sont pas configurés dans l'env."; \
		exit 1; \
	fi

	@# Ici on ne fait PAS de 'dvc init', on utilise le .dvc/ déjà présent dans Git
	@echo "🔐 Configuration des accès DagsHub..."
	@# "$(DAGSHUB_xxxx_KEY_ID)" : on le met toujours entre guillemet dans le Makefile pour être interprété
	@# comme une chaine de caractère et ainsi éviter une potentielle commande dû à des caractères spéciaux
	uv run dvc remote modify origin --local access_key_id "$(DAGSHUB_ACCESS_KEY_ID)"
	uv run dvc remote modify origin --local secret_access_key "$(DAGSHUB_SECRET_ACCESS_KEY)"
	@echo "✅ Environnement prêt pour la CI (Continuous Integration)."


# ======================
# --- QUALITÉ (PEP8) ---
# ======================
quality:
	@echo "📍 Analyse du code source uniquement..."
	uv run black src/
	@echo "uv run flake8 src/"
	@uv run flake8 src/ || ( \
		echo " "; \
		echo "----------------------------------------------------------------------------"; \
		echo "❌ Error 1: Flake8 a détecté des écarts de style (voir ci-dessus)."; \
		echo "💡 NOTE : Le pipeline s'arrête ici pour garantir la propreté du code."; \
		echo "----------------------------------------------------------------------------"; \
		exit 1; \
	)
	@echo "✅ Qualité validée : aucun problème détecté."

# ======================
# --- PIPELINE (DVC) ---
# ======================
# Cette commande lance automatiquement le dvc.yaml
pipeline:
	uv run dvc repro

# ==================================
# --- STOCKAGE DAGSHUB ET GITHUB ---
# ==================================
# DAGSHUB (gros fichiers (données/model)) ET GITHUB (fichiers légers)
push:
	@# On pousse les fichiers lourds vers DagsHub
	@# dvc remote list donne la liste de tous les lieux de stockages dvc.
	@# Par défaut origin correspond à https://dagshub.com/xx/Template_MLOps_accidents.dvc
	uv run dvc push -r origin

	@echo "🔍 État du dépôt avant commit :"
	git status
	@# On pousse le code et les métriques vers GitHub
	git add .
	@# NB: mode silencieux @ SEULEMENT EN DEBUT DE LIGNE (DONC PAS LE DROIT APRES ||)
	@echo "On commit avec le message: $(MSG)"
	@git commit -m "$(MSG)" || echo "Rien à commiter"
	@# CI = Continuous Integration (c’est ce qui suit avec le git push et son comportement)
	@# En faisant git push, GitHub reçoit le code et détecte si un fichier est présent dans
	@#.github/workflows/python-app.yml. Si oui, alors, GitHub ouvre une VM (ubuntu) et lance
	@# lance le python-app.yml = installe le projet et vérifie la qualité Lint/Test.. 
	@# Si une étape échoue, une croix rouge apparaît sur GitHub pour ce commit.
	@# git remote -v donne la liste de tous les lieux de stockages git.
	@# Par défaut c'est origin avec https://github.com/XXXX/Template_MLOps_accidents.git
	git push origin master