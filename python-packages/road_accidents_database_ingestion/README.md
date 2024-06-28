# Road Accidents Database Ingestion



## Running the tests

```
pytest tests
```

## Development

To build the python package in development mode run:
```
python -m pip install -e .
```

### Building the Airflow docker image

Make sure to run this command first `sudo chmod -R 777 python-packages/road_accidents_database_ingestion` otherwise the `python -m pip install -e .` will fail. Or you can run docker compose as `DOCKER_BUILDKIT=1 docker-compose up`.


# Further reading

- https://packaging.python.org/en/latest/tutorials/packaging-projects/
- https://github.com/pypa/sampleproject


# TODO

- [sos] ignore empty dirs
- 