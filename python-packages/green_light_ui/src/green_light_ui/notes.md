### Commands to run 

build docker image

```python
docker image build . -t accidents_ui:latest 

docker build  -t roadaccidentsmlops24/airflowdb:latest -f airflowdb.Dockerfile  .  --load

```
Run Streamlit directly 

streamlit run app.py --server.port=8501 --server.address=localhost

```python
docker container run -p 8501:8501  --rm -d --name accidents_ui accidents_ui:latest 
docker container run -p 8000:8000 -it -d --name accidents_ui accidents_ui:latest  bash
docker run -p 8000:8000 -p 8501:8501 accidents_ui:latest
```