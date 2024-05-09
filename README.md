# 🛡️ Project Name: SHIELD

(Safety Hazard Identification and Emergency Law Deployment)


## Project Organization
------------

    ├── LICENSE
    ├── README.md          <- The top-level README for developers using this project.
    ├── data
    │   ├── external       <- Data from third party sources.
    │   ├── interim        <- Intermediate data that has been transformed.
    │   ├── processed      <- The final, canonical data sets for modeling.
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
    ├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
    │   └── figures        <- Generated graphics and figures to be used in reporting
    │
    ├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
    │                         generated with `pip freeze > requirements.txt`
    │
    ├── src                <- Source code for use in this project.
    │   ├── __init__.py    <- Makes src a Python module
    │   │
    │   ├── api           <- Scripts concerning the api  
    │   │   ├── api.py 
    │   │   └── test_api.py
    │   │
    │   ├── data           <- Scripts to download or generate data
    │   │   ├── create_data_tree.py 
    │   │   ├── import_raw_data.py 
    │   │   ├── make_dataset.py 
    │   │   └── update_data.py
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

---------

## Steps to follow on Linux

Convention : All python scripts must be run from the root specifying the relative file path.

### 1- Create a virtual environment using Virtualenv.

    `python -m venv my_env`

###   Activate it 

    `chmod +x my_env/bin/activate
    source my_env/bin/activate`

###   Install the packages from requirements.txt

    `pip install -r requirements.txt` 

### 3- Create data tree:

    `python src/data/create_data_tree.py`

### 4- Execute import_raw_data.py to import the 4 datasets.

   `python src/data/import_raw_data.py`

### 5- Execute make_dataset.py 

    `python src/data/make_dataset.py`

### 6- Execute train_model.py to instanciate the model in joblib format

    `python src/models/train_model.py`

### 7- Create users database:

    `python src/users_db/create_users_db.py

### 8- Run the api:

    `uvicorn --app-dir src/api api:api --reload --host=127.0.0.1 --port=8000`

### 9- Check if the api is running:

In a new terminal, type:

    `curl -X GET http://127.0.0.1:8000/status`

It should return: "L'api fonctionne."

### 10- Run the tests:

    `python src/api/test_api.py`

### 11- Manually test the api:

In your navigator, go to http://127.0.0.1:8000/docs

You can test all the endpoints. When needed, you will be asked a username and a password. We implemented two types of users:
_ Adminstrator Users: try it with `admin:4dmin`. This user's type can run every endpoint.
_ Standard Users: try it with `fdo:c0ps`. This user's type can only run the following endpoints: /status (which doesn't requires any identification), /predict_from_call, /predict_from_test, /label

### 12- Test the api with terminal command:

All commands are written in the file ./src/api/Readme_api.md


------------------------
## Steps to follow on Windows

Convention : All python scripts must be run from the root specifying the relative file path.

### 1- Create a virtual environment using Virtualenv.

    `python -m venv my_env`

###   Activate it 

    `my_env/Scripts/activate`

###   Install the packages from requirements.txt

    `pip install -r requirements.txt` 

### 3- Create data tree:

    `python src/data/create_data_tree.py`

### 4- Execute import_raw_data.py to import the 4 datasets.

    `python src/data/import_raw_data.py`

### 5- Execute make_dataset.py 

    `python src/data/make_dataset.py`

### 6- Execute train_model.py to instanciate the model in joblib format

    `python src/models/train_model.py`

### 7- Create users database:

    `python src/users_db/create_users_db.py

### 8- Run the api:

    `uvicorn --app-dir src/api api:api --reload --host=127.0.0.1 --port=8000`

### 9- Check if the api is running:

In a new terminal, type:

    `curl -X GET http://127.0.0.1:8000/status`

It should return: "L'api fonctionne."

### 10- Run the tests:

    `python src/api/test_api.py`

### 11- Manually test the api:

In your navigator, go to http://127.0.0.1:8000/docs

You can test all the endpoints. When needed, you will be asked a username and a password. We implemented two types of users:
_ Adminstrator Users: try it with `admin:4dmin`. This user's type can run every endpoint.
_ Standard Users: try it with `fdo:c0ps`. This user's type can only run the following endpoints: /status (which doesn't requires any identification), /predict_from_call, /predict_from_test, /label

### 12- Test the api with terminal command:

All commands are written in the file ./src/api/Readme_api.md


<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
