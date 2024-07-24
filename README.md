# **mar24_mlops_accidents**
==============================
"Ce projet développe un modèle prédictif pour évaluer la gravité des accidents de la route à partir des premières observations sur place, aidant à déterminer les ressources nécessaires et améliorer l'anticipation des secours. Il intègre également des pratiques de MLOps et CI/CD pour assurer un déploiement automatisé, une surveillance continue et des mises à jour régulières du modèle, garantissant ainsi sa performance et son actualisation constante.".

Project Organization
------------

    ├── LICENSE
    ├── README.md          <- The top-level README for developers using this project.
    ├── data
    │   ├── external       <- Data from third party sources.
    │   ├── interim        <- Intermediate data that has been transformed.
    │   ├── processed      <- The final, canonical data sets for modeling.
    │   ├── user_db        <- Data of the users and admins
    │   └── raw            <- The original, immutable data dump.
    │
    ├── logs               <- Logs from training and predicting
    │
    ├── models             <- Trained and serialized models, model predictions, or model summaries
    │
    ├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
    │                         the creator's initials, and a short `-` delimited description, e.g.
    │                         `1.0-jqp-initial-data-exploration`.
    │
    ├── references         <- Data dictionaries, manuals, and all other explanatory materials.
    │
    ├── reports            <- Generated analysis as Cahier_des_charges, HTML, PDF, LaTeX, etc.
    │   ├── figures        <- Generated graphics and figures to be used in reporting
    │   └── cahier_des_charges
    │
    ├── requirements.txt   <- The full list of libraries installed on the python env used for development.
    │                         generated with `pip freeze > requirements.txt`
    │
    ├── src                <- Source code for use in this project.
    │   ├── __init__.py    <- Makes src a Python module
    │   │
    │   ├── api            <- Scripts for the api
    │   │   ├── api.py     
    │   │   ├── test_api_authentification.py    
    │   │   ├── test_api_fonction.py    
    │   │   └── test_api_serveur.py    
    │   │
    │   ├── data           <- Scripts to download or generate data
    │   │   ├── check_structure.py    
    │   │   ├── import_raw_data.py 
    │   │   └── make_dataset.py
    │   │
    │   ├── features       <- Scripts to turn raw data into features for modeling
    │   │   └── build_features.py
    │   │
    │   ├── models         <- Scripts to train models and then use trained models to make
    │   │   │                 predictions
    │   │   ├── predict_model.py
    │   │   └── train_model.py
    │   │
    │   ├── visualization  <- Scripts to create exploratory and results oriented visualizations
    │   │   └── visualize.py
    │   └── config         <- Describe the parameters used in train_model.py and predict_model.py
    │ 
    ├── streamlit          <- Source code for a streamlit interface to access the API
    │   ├── README.md      <- The README for developers using this streamlit.
    │   └── images         <- Source images 
    │  
    ├── Dockerfile         <- The app's image builder, allows to run the app in a container without needing any condfiguration.
    │  
    ├── .github\workflows       <- GitHub Actions workflows for CI/CD
        ├── git_action.yml      <- Workflow for running unit tests and building and pushing Docker images
        └── model_deployment.yml<- Workflow for deploying the model
---------

# **To install the applications**

## Steps to follow for the main application (predict model)

Convention : All python scripts must be run from the root specifying the relative file path.

### 1- Create a virtual environment using Virtualenv.

    `python -m venv my_env`

###   Activate it 

    `./my_env/Scripts/activate`

###   Install the packages from requirements.txt

    `pip install -r .\requirements.txt` ### You will have an error in "setup.py" but this won't interfere with the rest

### 2- Execute import_raw_data.py to import the 4 datasets.

    `python .\src\data\import_raw_data.py` ### It will ask you to create a new folder, accept it.

### 3- Execute make_dataset.py initializing `./data/raw` as input file path and `./data/preprocessed` as output file path.

    `python .\src\data\make_dataset.py`

### 4- Execute train_model.py to instanciate the model in joblib format

    `python .\src\models\train_model.py`

### 5- Finally, execute predict_model.py with respect to one of these rules :
  
  - Provide a json file as follow : `python ./src/models/predict_model.py ./src/models/test_features.json`
    test_features.json is an example that you can try 

  - If you do not specify a json file, you will be asked to enter manually each feature. 

## Steps to follow To run the API locally  :

1/ It is necessary to have installed the main application

2/ Be sure to have the environment activated

3/ In the prompt :
   a) use an environment with uvicorn or install it with `pip install uvicornt`
   b) uvicorn src.api.api:api       # starts the api on : http://localhost:8000

## Steps to follow To run a streamlit demo :

see the README in the streamlit directory
------------------------

# **Description détaillée du projet**

## Description
Ce projet vise à développer un modèle prédictif pour évaluer la gravité des accidents de la route en fonction des premières observations effectuées sur le site de l'accident. Ce modèle aide à définir les besoins en ressources pour chaque accident et permet une meilleure anticipation et allocation des secours.

## Contexte et Objectifs
"Ce projet intégrera un travail de MLOps complet, notamment à travers une intégration CI/CD. Cela inclut l'automatisation du déploiement du modèle, la surveillance continue de ses performances, et des mises à jour régulières. Les pipelines CI/CD assureront des tests unitaires et d'intégration, garantissant que chaque modification est correctement validée avant d'être déployée. De plus, la conteneurisation avec Docker facilitera la gestion des environnements de déploiement, assurant une cohérence et une reproductibilité maximales."

### Mise en situation
Le logiciel propose une estimation de la gravité d'un accident en analysant les caractéristiques du lieu de l'accident, des véhicules impliqués, et du type de choc. La gravité de l'accident est classée en deux catégories:
- **Classe 0** : Indemnes ou blessés légers (sans hospitalisation)
- **Classe 1** : Blessés à hospitaliser ou tués

### Utilisateurs  
Les principaux utilisateurs de ce modèle sont les services de sécurité routière et les services d'urgence, qui pourront ainsi optimiser l'allocation des ressources en fonction des besoins réels.

### Fonctionnement du Modèle
Le modèle utilise un algorithme de Random Forest pour prédire la gravité des accidents en se basant sur 28 variables d'entrée possibles. La performance du modèle est évaluée à l'aide du f1-score, pour s'assurer d'une bonne précision et rappel.

## Entraînement et Évaluation
Le modèle est réentraîné et évalué à chaque modification du code et tous les mois pour tenir compte des changements dans la base de données.

## Base de Données
Le modèle utilise les bases de données annuelles des accidents corporels de la circulation routière fournies par l'Observatoire National Interministériel de la Sécurité Routière (ONISR).

### API
L'API permet de :
- Utiliser le modèle pour prédire la gravité des accidents
- Enregistrer les prédictions dans des logs
- Gérer l'authentification des utilisateurs et administrateurs

## Endpoints
1. `/status` : Vérification du fonctionnement de l’API
2. `/new_user` : Inscription d’un utilisateur
3. `/new_admin` : Inscription d’un administrateur
4. `/delete_user` : Suppression d’un utilisateur
5. `/delete_admin` : Suppression d’un administrateur
6. `/prediction` : Prédictions de priorité à partir de données saisies

### Isolation, Intégration Continue et Livraison Continue
Le projet utilise Docker pour la conteneurisation du modèle et de l'API, et GitHub Actions pour l'intégration continue. Le déploiement se fait via Heroku, assurant ainsi une livraison continue et automatisée du modèle et de l'API.

## Workflows CI/CD
- **CI Workflow** : Entraînement, test, et construction de l'image Docker.
- **CD Workflow** : Déploiement de l'API sur Heroku si les tests sont réussis.

## Schéma d’implémentation
Un schéma d'implémentation détaillé est fourni dans le cahier des charges (repertoire reoprts) pour illustrer le processus complet du développement à la mise en production.

### Workflows CI/CD
- **CI Workflow** : Entraînement, test, et construction de l'image Docker.
- **CD Workflow** : Déploiement de l'API sur Heroku si les tests sont réussis.


