# Pipeline MLOps - Prédiction de la Gravité des Accidents

Ce dépôt met en place un pipeline MLOps pour classer la gravité d’un accident de la route à partir de données ouvertes. Il combine ingestion, préparation, entraînement automatique, tracking MLflow, déploiement BentoML et monitoring.

## 1. Architecture et Schéma du Projet

Ce dépôt implémente un pipeline MLOps complet pour la prédiction de la gravité d’un accident routier. Le flux combine :

- un entraînement autonome piloté par Airflow,
- un suivi et un registre de modèles avec MLflow,
- un service de prédiction BentoML exposé via une API,
- un déploiement continu du modèle par rechargement à chaud,
- un monitoring Prometheus/Grafana et une interface utilisateur Streamlit.

```mermaid
flowchart TD
  subgraph Orchestration
    P1[postgres-airflow]
    P2[airflow-init]
    P3[airflow]
  end

  subgraph Tracking_Registre
    MLF[mlflow]
  end

  subgraph Modélisation
    PRE[preprocess Docker]
    TRN[train Docker]
  end

  subgraph API_Serving
    API[ml-api / BentoML]
  end

  subgraph Monitoring_Front
    PROM[prometheus]
    GRAF[grafana]
    STRM[streamlit]
    NGINX[nginx]
  end

  P3 -->|schedule| PRE
  P3 -->|schedule| TRN
  PRE -->|data volume| TRN
  TRN -->|metrics + model| MLF
  TRN -->|registry| MLF
  MLF -->|champion alias| API
  P3 -->|reload_model| API
  API -->|metrics| PROM
  STRM -->|api requests| API
  NGINX -->|proxy| STRM
  NGINX -->|proxy /predict| API
  PROM -->|datasource| GRAF
  MLF -->|ui| GRAF
```


## 2. Structure du Repository

    ├── LICENSE
    ├── README.md                         <- Documentation technique MLOps du projet
    ├── docker-compose.yml                <- Orchestration des services Docker
    ├── Dockerfile.airflow                <- Image Airflow utilisée pour le scheduler et le webserver
    ├── .github/                          <- Configuration CI/CD GitHub Actions
    │   └── workflows/                    <- Workflows d’intégration continue
    │       └── ci.yml                    <- Vérification de syntaxe et build Docker
    ├── dags/                             <- DAG Airflow principal pour le pipeline
    │   └── pipeline_accidents.py         <- Orchestration des tâches preprocess/train/evaluate/promote/reload
    ├── grafana/                          <- Dashboards et datasources Grafana
    ├── mlruns/                           <- Artefacts et métadonnées MLflow
    ├── notebooks/                        <- Notebooks d’exploration et de prototypage
    ├── references/                       <- Documents de référence et sources de données
    │   └── data_sources.md               <- Description des sources de données utilisées
    ├── src/                              <- Code source applicatif
    │   ├── bentoml/                      <- Service de prédiction BentoML + Dockerfile
    │   ├── nginx/                        <- Reverse proxy Nginx et configuration HTTPS
    │   ├── preprocess/                   <- Préparation des données + Dockerfile
    │   ├── prometheus/                   <- Configuration Prometheus
    │   ├── streamlit/                    <- Application Streamlit frontend
    │   └── train/                        <- Entraînement du modèle + Dockerfile

## 3. Fonctionnement du Pipeline (Workflow Airflow)

Le DAG `mlops_accident_gravity_pipeline` orchestre les étapes suivantes :

1. `preprocess` : exécution d’un container Docker `mlops_accidents-preprocess:latest` qui prépare les données et alimente le volume partagé `accidents-data`.
2. `train` : exécution d’un container Docker `mlops_accidents-train:latest` qui entraîne un modèle et enregistre les métriques dans MLflow.
3. `evaluate_metrics` : tâche Python qui lit le dernier `run` MLflow, vérifie le `f1_score`, compare au modèle en production et bloque la promotion si la qualité chute.
4. `promote_model` : tâche Python qui tague la dernière version validée du modèle MLflow avec l’alias `champion` dans le Registry.
5. `reload_predict_service` : tâche Python qui appelle l’endpoint `POST /reload_model` du service `ml-api` pour recharger le modèle en mémoire.

### Stratégie de déploiement

Le service `ml-api` basé sur BentoML expose un endpoint interne `/reload_model`. Après promotion du modèle dans MLflow, Airflow appelle cet endpoint pour forcer une relecture du modèle `Modèle_Gravité_Accidents@champion` sans redémarrage de conteneur.

## 4. Guide de Démarrage Rapide

### Prérequis

- Docker Desktop (WSL2 sous Windows)
- Docker Compose
- Git

### Commandes principales

Avant de lancer le pipeline, il est nécessaire de préparer le dossier de données à la racine du projet. Créez le dossier avec la commande suivante :

```bash
mkdir data
```

Puis placez-y les fichiers CSV de la source officielle :

- `caracteristiques.csv`
- `lieux.csv`
- `usagers.csv`
- `vehicules.csv`

Ces fichiers peuvent être téléchargés depuis la plateforme officielle Data.gouv : https://www.data.gouv.fr/datasets/bases-de-donnees-annuelles-des-accidents-corporels-de-la-circulation-routiere-annees-de-2005-a-2024

1. Création des certificats Nginx :

```bash
mkdir -p src/nginx/certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout src/nginx/certs/nginx.key -out src/nginx/certs/nginx.crt -subj "//CN=localhost" -batch
```

Cette commande génère les fichiers `nginx.crt` et `nginx.key` nécessaires au reverse proxy HTTPS.

2. Build initial des images d'entraînement :

```bash
docker compose build
```

3. Lancement de la stack complète :

```bash
docker compose up -d
```

4. Vérification de l'état des conteneurs :

```bash
docker compose ps
```

5. Consultation des logs (ex : Airflow ou ml-api) :

```bash
docker compose logs -f ml-api
```

6. Arrêt et nettoyage complet (volumes inclus) :

```bash
docker compose down -v
```

## 5. CI / Intégration Continue

Le dépôt intègre une pipeline CI GitHub Actions définie dans [.github/workflows/ci.yml](.github/workflows/ci.yml). Elle couvre deux validations principales :

- une vérification de syntaxe Python avec `python -m py_compile $(find src -name "*.py")` ;
- un build des images Docker via `docker compose build` lors des pull requests ciblant la branche `main`.

Cette automatisation permet de détecter rapidement les erreurs de compilation ou de conteneurisation avant la fusion des changements.

## 6. Accès aux Interfaces (URLs et Ports)


| Service               | URL                                                                                    | Identifiants / Notes | Rôle                                            |
| --------------------- | -------------------------------------------------------------------------------------- | -------------------- | ------------------------------------------------ |
| Airflow Webserver     | http://localhost:8080                                                                  | admin / admin        | Orchestration du pipeline et exécution des DAGs |
| MLflow Tracking UI    | http://localhost:5000                                                                  | -                    | Suivi des expériences et modèle MLflow         |
| API BentoML / Swagger | via Nginx : https://localhost (port 443) / direct conteneur : non exposé publiquement | -                    | Service de prédiction et endpoint`/predict`     |
| Interface Streamlit   | via Nginx : https://localhost (port 443)                                               | -                    | UI de saisie et démonstration de prédiction    |
| Grafana               | http://localhost:3000                                                                  | admin / admin        | Dashboard de monitoring Prometheus               |
| Prometheus            | http://localhost:9090                                                                  | -                    | Collecte des métriques BentoML                  |

> En production, Nginx reverse-proxy les services Streamlit et ml-api sur HTTP/HTTPS.
