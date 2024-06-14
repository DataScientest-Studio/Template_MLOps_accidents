#

## Prepare the data

### Prepare the docker volumes
In the root of this project add the following directories:
- `Volumes/db`: Will be used by the Postgres db service
- `Volumes/db_admin`: Will be used by the Postgres db UI (pgAdmin)
- `Volumes/data/raw`: Inside this directory copy the csv files for a particular year (eg 2021)

### Start the docker compose
```
docker-compose up -d
```

It will start the Postgres DB service as well as a container that will read data from
the `Volumes/data/raw` directory and populate the `RoadAccidents` DB.

### UI tool for the DB (optional)


Navigate to this [link](http://localhost:8888/browser/), left click on the `Servers`, `Register` -> `new server`. Choose any name for the `Name` option. Then, move to the `Connection` tab and for the `Host name/address` set it to `postgres`. The remaining fields:

* `Maintenance database` = RoadAccidents
* `Username` = postgres
* `Password` = changeme

The aforementioned info can be found in the `.env` file.
Now you can see the data in the db by navigating to `Name` -> `Databases` -> `RoadAccidents` -> `Schemas` -> `Tables`. There should be 4 tables with the same names as the csv files. Right click in one of them
and click on `View Data` -> `First 100 rows`.

## Steps to follow 

Convention : All python scripts must be run from the root specifying the relative file path.

### 1- Create a virtual environment using Virtualenv.

    `python -m venv my_env`

###   Activate it 

    `./my_env/Scripts/activate`

###   Install the packages from requirements.txt

    `pip install -r .\requirements.txt` ### You will have an error in "setup.py" but this won't interfere with the rest

### 2- Execute make_dataset.py to fetch the data from the DB

    `python ./src/data/make_dataset_from_db.py`

### 4- Execute train_model.py to instanciate the model in joblib format

    `python ./src/models/train_model.py`

### 5- Finally, execute predict_model.py with respect to one of these rules :
  
  - Provide a json file as follow : 

    
    `python ./src/models/predict_model.py ./src/models/test_features.json`

  test_features.json is an example that you can try 

  - If you do not specify a json file, you will be asked to enter manually each feature. 
