🚦 Green Light Services
==============================

<p align="center">
 <img src="./python-packages/green_light_ui/src/green_light_ui/assets/GreenLights.png" alt="alt text" height="150">
</p>


The `Green Light Services` provide Dashboards for historic traffic situations in local municipalities and it makes predictions on the gravity of [road accidents](https://www.data.gouv.fr/en/datasets/bases-de-donnees-annuelles-des-accidents-corporels-de-la-circulation-routiere-annees-de-2005-a-2019/) in selected hot spots. 

This project is a starting Pack for MLOps projects based on the subject "road accident". It's not perfect so feel free to make some modifications on it.

# 👨🏼‍💻👩‍💻👨🏻‍💻 Development Team

Green Lights Services has been developed by:
- Josef Hartmann
- Paula Robina Beck
- Evan Stromatias

Green Light Services represents our final project for the DataScientest MLOps Program, May 2024.

# 🏗️ Architecture

The Green Light Services is a web application that uses microservices and runs on [Docker compose](https://docs.docker.com/compose/). The following figure summarizes the architecture of the Green Light Services application:

![Green Light Services architecture](./python-packages/green_light_ui/src/green_light_ui/assets/ServicePlatform.png)
<p align="center">
    <b>Figure 1.</b> The Green Light Services architecture.
</p>

Our docker-compose application includes the following:
- `Airflow` with a custom base docker image.
- A dedicated `postgres` database `RoadAccidents` where the raw road accidents data are stored.
- `pgadmin` which is a dashboard to manage the `RoadAccidents` database.
- `model_api` which is a FastAPI application responsible for making ML predictions
- `UI` the Green Light Services UI Dashboard

The Green Light Services docker-compose application is configured through enviroment variables stored in the `.env` file.

We use the Github Actions to implement the CI/CD pipelines of the Green Light Services app. More specifically:
- CI: every time there is a Pull Request to merge a branch to master all unit-tests need to pass
- CD: The docker images are build and pushed to the Docker Hub [roadaccidentsmlops24]](https://hub.docker.com/repositories/roadaccidentsmlops24).


# 📂 Project Organization
The repository is structured as follows:

```
    ├── .github/
    │    │
    │    └── workflows/                     
    │
    ├── README.md          
    │
    ├── Airflow                
    │   │
    │   ├── dags           
    │   │   ├── ingest_road_accident_csv_to_db.py    
    │   │   └── 1_training_pipeline_dag.py 
    │   │
    ├── Volumes     
    │   │
    │   ├── airflow/            <- Airflow creates this       
    │   │
    │   ├── data/         
    │   │   ├── metrics/        <- used by TODO    
    │   │   ├── mlflow/         <- used by TODO    
    │   │   │   └── run_mlflow_server.sh   <- Starts the MLFlow server locally (ouside docker-compose)
    │   │   │
    │   │   ├── predictions/    <- used by TODO    
    │   │   └── preprocessed/   <- used by TODO
    │   │
    │   ├── db/                 <- The RoadAccidents Postgres DB files       
    │   │
    │   ├── db_admin/           <- The PgAdmin files, used to monitor the RoadAccidents DB
    │   │
    │   ├── models
    │   │   ├── archive  
    │   │   ├── new  
    │   │   └── trained_model.joblib <- The ML model currently used in production
    │   │
    │   ├── road_accidents_data_directories/      <- Clients Add Road Accidents CSV Directories   
    │   │   ├── 2021/                             <- For example for the year '2021'    
    │   │   │   ├── caracteristiques_2021.csv   
    │   │   │   ├── lieux-2021.csv   
    │   │   │   ├── usagers-2020.csv   
    │   │   │   └── vehicules-2020.csv   
    │   │   │
    ├── notebooks          
    │
    ├── python-packages                
    │   │
    │   ├── green_light_ui
    │   ├── model_api           
    │   └── road_accidents_database_ingestion
    │
    ├── references         
    │
    ├── .env         
    │
    └── docker-compose.yml         
```

# 👩‍💻 Development

Running the `Green Light Services` application in `development` mode means running the app without using the Docker images that the [CI/CD pipelines](https://github.com/DataScientest-Studio/may24_bmlops_accidents/tree/master/.github/workflows) build and pushed to [`roadaccidentsmlops24`](https://hub.docker.com/u/roadaccidentsmlops24) Docker Hub. Instead when running in `development` mode the local `Dockerfiles` are used to build the Docker Images. 

To start the application in `development` mode execute the `DEV-docker-compose-up.sh` shell script from the root of the `may24_bmlops_accidents` project:

```sh
./DEV-docker-compose-up.sh
```

This script will:
- Prompt the user if they would like to remove all local unused Docker Images by running `docker image prune -a
`
- build the `roadaccidentsmlops24/airflowdb:latest` Docker image using the local `airflowdb.Dockerfile`
- Build the `roadaccidentsmlops24/model_api:latest` Docker image using the local `Dockerfile`
- Build the `roadaccidentsmlops24/accidents_ui:latest` Docker image using the local `Dockerfile`
- Start the docker compose application by running `DOCKER_BUILDKIT=1 docker compose up -d`
- Start the `MLFlow` [server](http://127.0.0.1:5000/)

>Keep in mind: The `development` mode only applies to code and Docker images. Not the data/databases of the application.

### Releasing a New Version of The App

When a new feature has been developed and its PR has been approved and merged to the `master` branch users can create a new versioned release using git's `tag` feature.

Releasing the application using specific versions makes it possible to roll-back to a working version if/when something breaks.

To release a new version of the app do the following:  

* `git checkout master`
* `git pull origin master`
* `git tag v{x}.{y}.{z}`
    - where the `v{x}.{y}.{z}` defines the [Semantic Versioning](https://semver.org/) of the release (eg: `v0.1.0`).
* `git push origin --tags`

Then the [`deploy-docker-images-on-new-tag.yml`](https://github.com/DataScientest-Studio/may24_bmlops_accidents/blob/master/.github/workflows/deploy-docker-images-on-new-tag.yml) workflow is triggered, which for each of the [Python packages](https://github.com/DataScientest-Studio/may24_bmlops_accidents/tree/master/python-packages) of this project will run the following steps:

1. Checkout the repository.
2. Login to Docker Hub using a Github [Secret](https://github.com/DataScientest-Studio/may24_bmlops_accidents/settings/secrets/actions) to store the password.
3. Build the `Dockerfile` successfully using two `tags` for each image: 
    * `latest`
    * The specified tag version ([example `roadaccidentsmlops24/model_api:v0.0.4`](https://hub.docker.com/layers/roadaccidentsmlops24/model_api/v0.0.4/images/sha256-7aecabc78a37a5318910f6d892b386aefb52bfbd6b39f3af8294f897a2ed9535?context=explore))
4. Push the Docker built image to the [`roadaccidentsmlops24` Docker Repo](https://hub.docker.com/u/roadaccidentsmlops24).


> Keep in mind: When running the application in the `development` mode using the `DEV-docker-compose-up.sh`, the environment variable `GLS_TAG` has no effect. In `development` mode, the Docker images are build using the local `Dockerfiles` instead of being pulled from the Docker Hub.


# 👟 Running the App

Running the `Green Light Services` application in `production` mode means pulling the `latest` Docker images that the [CI/CD pipelines](https://github.com/DataScientest-Studio/may24_bmlops_accidents/tree/master/.github/workflows) build and pushed to [`roadaccidentsmlops24`](https://hub.docker.com/u/roadaccidentsmlops24) Docker Hub. 

To start the application in `production` mode execute the `PROD-docker-compose-up.sh` shell script from the root of the `may24_bmlops_accidents` projects.

```sh
./PROD-docker-compose-up.sh
```

This script will:
- Prompt the user if they would like to remove all local unused Docker Images by running `docker image prune -a`
- Start the docker compose application by running `DOCKER_BUILDKIT=1 docker compose up -d`
- Start the `MLFlow` [server](http://127.0.0.1:5000/)


### Running the App Using a Specific Released Version

A specific release (`tag`) version can be used when starting the Docker Compose app in `production` mode by setting the environment variable `GLS_TAG` 
(where `GLS` stands for `Green Light Services`). 

If a specific release version is requested then Docker compose will pull the images from Docker hub that correspond the specified `tag`. 

For example if one would like to start the application using the release version `v0.0.4`:

```
GLS_TAG="v0.0.4" ./PROD-docker-compose-up.sh
```

or:

```
GLS_TAG="v0.0.4" DOCKER_BUILDKIT=1 docker compose up -d
```

> Keep in mind: If the `GLS_TAG` environment variable is not set, then the `latest` tag will be used.

> Keep in mind: When running the application in the `development` mode using the `DEV-docker-compose-up.sh`, the environment variable `GLS_TAG` has no effect. In `development` mode, the Docker images are build using the local `Dockerfiles` instead of being pulled from the Docker Hub.""")


To view all the available released versions of this application you can visit the project's repo:

[https://github.com/DataScientest-Studio/may24_bmlops_accidents/tags](https://github.com/DataScientest-Studio/may24_bmlops_accidents/tags)

And/or the project's Docker Hub repo:

[https://hub.docker.com/u/roadaccidentsmlops24](https://hub.docker.com/u/roadaccidentsmlops24)

# 👀 Monitoring the App

## Airflow

The Airflow UI can be accessed through this [link](http://localhost:8080/).


In order to receive emails when an Airflow DAG fails, the user needs to add a variable `alert_email` with its value set to the email that would like to receive the alerts.

> To login to the Airflow Web UI use the `Green Light Services` admin credentials (`ADMIN_USERNAME`, `ADMIN_PASSWORD`) which are 
defined in the [`./.env`](https://github.com/DataScientest-Studio/may24_bmlops_accidents/blob/master/.env) file.             


## MLFlow For ML Models

When the `Green Light Services` application has been been started in `production` mode (`PROD-docker-compose-up.sh`) or in `development` mode (`DEV-docker-compose-up.sh`) then the `MLFlow` server can be accessed through this [link](http://127.0.0.1:5000).

## Road Accidents Database

The `Road Accidents` database can be monitored through this [link](http://localhost:8888/browser/).
                
> For accessing the `Road Accident` database use the `Green Light Services` admin password (`ADMIN_PASSWORD`) which is defined in the [`./.env`](https://github.com/DataScientest-Studio/may24_bmlops_accidents/blob/master/.env) file.

To see or query the `Road Accidents` tables navigate to: 

`Servers` -> `RoadAccidents` -> `Databases` -> `Schemas` -> `Tables`


------------------------

<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
