# Green Light Services UI

A Python package for the Road Accidents UI.

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

- TODO: None yet but probably the admin username & password in order to call the Model API and get the authorization token.

## Running the UI Locally (no docker)

Assumming you are in the root directory of the `green_light_ui` Python project, then run:

```
streamlit run src/green_light_ui/app.py --server.port=8501 --server.address=localhost
```

Then access the UI: [localhost](http://localhost:8501/)

## Building the Docker Image

Assumming you are in the root directory of the `green_light_ui` Python project, then build the docker image by:

```
DOCKER_BUILDKIT=1 docker image build --no-cache . -t roadaccidentsmlops24/accidents_ui:latest
```

>> If `DOCKER_BUILDKIT=1` doesn't work for you then before building the docker image run:
```
sudo chmod -R 777 python-packages/green_light_ui
```
## Running the Docker Image

```
docker container run --name accidents_ui -p 8501:8501 roadaccidentsmlops24/accidents_ui:latest
```

# Further reading

- https://packaging.python.org/en/latest/tutorials/packaging-projects/
- https://github.com/pypa/sampleproject