# The Python packages of the Green Light Services App.

This directory includes Python packages used by the Green Light Services App. More specifically:
- `green_light_ui`
    - The Green Light Services UI Dashboard.
- `model_api`
    - Responsible for: (TODO maybe too many responsilities in one python package, consider spliting it up.)
        - serving a trained ML model.
        - training and evaluating a ML model.
        - extracting features (preprocessing) the raw data.
- `road_accidents_database_ingestion`
    - Includes to code and models to ingest road accident CSV files to the `RoadAccidents` Database.



## Building the Docker Images
This section describes how to build the Docker images of the aforementioned Python packages. These Docker images are used by the docker-compose app.

Building the Docker images manually is not mandatory since they will be pulled from the Docker Hub ([roadaccidentsmlops24](https://hub.docker.com/repositories/roadaccidentsmlops24)).
However it may be useful during the development process to build and test some changes locally.

### Building roadaccidentsmlops24/airflowdb Docker Image

The `roadaccidentsmlops24/airflowd` is the Airflow base Docker image and includes the Python packages required by the Green Light Services Airflow DAGs.


```
DOCKER_BUILDKIT=1 docker image build --no-cache -f airflowdb.Dockerfile . -t roadaccidentsmlops24/airflowdb:latest
```

### Building roadaccidentsmlops24/model_api Docker Image

Please refer to the [documentation of the `model_api` package](./model_api/README.md)

### Building roadaccidentsmlops24/accidents_ui Docker Image

Please refer to the [documentation of the `green_light_ui` package](./green_light_ui/README.md)