# Road Accidents Database Ingestion

This Python package contains the Python code (tasks) that is used by the `my_dir_sensor_dag` airflow DAG to ingest the raw road accidents CSV files to the RoadAccidents Database.

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

- `ROAD_ACCIDENTS_RAW_CSV_FILES_ROOT_DIR`: Path to the root directorty where new directories with Road Accidents CSV files will be added.
- `ROAD_ACCIDENTS_POSTGRES_HOST`: The Hostname of the Road Accidents database.
- `ROAD_ACCIDENTS_POSTGRES_DB`: The database of the Road Accidents application.
- `ADMIN_USERNAME`: The user name of the Road Accidents database.
- `ADMIN_PASSWORD`: The password of the Road Accidents database.
- `ROAD_ACCIDENTS_POSTGRES_PORT`: The port of the Road Accidents database.

# Further reading

- https://packaging.python.org/en/latest/tutorials/packaging-projects/
- https://github.com/pypa/sampleproject


# TODO

- [sos] ignore empty dirs
- Remove `tqdm` from stdout because it floods the airflow logs!
- Finish this documentation (project structure)