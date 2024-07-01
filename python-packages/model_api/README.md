# Model API

A Python package to train and serve an ML model of the Road Accidents application.


## Building the Python package

Create a new venv:
```
python3.12 -m venv .venv
```

Activate the newly created venv:
```
source .venv/bin/activate
```

To build the python package run:
```
python -m pip install -e .
```

## Running the tests

```
pytest tests
```
## Configuration

The Python scripts are configured through the following enviroment variables:

- `api.py`:
    - `MODEL_PATH`: Path to the train scikit-learn model.
    - `ADMIN_USERNAME`: The admin username used to generate an authorization token.
    - `ADMIN_PASSWORD`: The admin password used to generate an authorization token.
- `make_dataset_from_db.py`:
    - `ROAD_ACCIDENTS_POSTGRES_HOST`: The Hostname of the Road Accidents database.
    - `ROAD_ACCIDENTS_POSTGRES_DB`: The database of the Road Accidents application.
    - `ADMIN_USERNAME`: The user name of the Road Accidents database.
    - `ADMIN_PASSWORD`: The password of the Road Accidents database.
    - `ROAD_ACCIDENTS_POSTGRES_PORT`: The port of the Road Accidents database.

## Building the Docker Image

Build the docker image:

```
DOCKER_BUILDKIT=1 docker image build --no-cache . -t model_api:latest
```

>> If `DOCKER_BUILDKIT=1` doesn't work for you then before building the docker image run:
```
sudo chmod -R 777 python-packages/road_accidents_database_ingestion
```

## Running the Docker Image

```
docker container run --name model_api -p 8001:8000 -v ./model:/model -e MODEL_PATH=/model/trained_model.joblib -e ADMIN_USERNAME=YOUR_ADMIN_USERNAME -e ADMIN_PASSWORD=YOUR_ADMIN_PASSWORD -d model_api:latest
```

Then access the Swagger Docs: [localhost](http://localhost:8000/docs)

## Running the Model API Locally (no docker)

Given a saved trained model in a location (eg: `../../Volumes/model/trained_model.joblib`), the API can be started by executing:

```
MODEL_PATH=../../Volumes/model/trained_model.joblib ADMIN_USERNAME=admin ADMIN_PASSWORD=adm1n python src/model_api/api.py
```

Then access the Swagger Docs: [localhost](http://localhost:8000/docs)


# Training a new model

## Download the Road Accidents Data

### Download the Road Accidents data from the Road Accidents DB (docker-compose)
Assuming you have started the Road Accidents App using docker-compose (`DOCKER_BUILDKIT=1 docker-compose up`),
the Python code will need the `.env` file to know the DB URLs, ports etc (this env file is used 
by docker-compose). 

However the `.env` fileis not present in this directory (`model_api/`), but in the root of the Road Accidents project(`may24_bmlops_accidents/`). 

You can use an enviroment variable to set the correct `.env` file path while running the script
to fetch the Road Accidents data from the DB:

```
DOTENV_PATH=../../.env python src/model_api/feature_extraction/make_dataset_from_db.py
```

### (old-way) Download the Road Accidents data from AWS (local)

Download the Road Accidents CSV files:
```
python src/model_api/feature_extraction/import_raw_data.py
```

## Make the ML dataset

Preprocess the original Road Accidents dataset to generate the:
- `X_train.csv`
- `y_train.csv`
- `X_test.csv`
- `y_test.csv`

files required to train and evaluate the ML model.

```
python src/model_api/feature_extraction/make_dataset.py
```

## Train the model

Execute the following script from the root directory of the `model_api/` package:

```
python src/model_api/train_model.py
```

The trained model will be stored at the `./../Volumes/model/trained_model.joblib`
which is used by the docker-compose project.


# Further reading

- https://packaging.python.org/en/latest/tutorials/packaging-projects/
- https://github.com/pypa/sampleproject