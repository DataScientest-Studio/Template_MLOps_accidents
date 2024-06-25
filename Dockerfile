FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8
#FROM python:3.12

RUN pip install --upgrade pip
COPY setup.py setup.py
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY ./src/api/api.py /src/api/api.py
# Le pipeline se charge de mettre l'artifact du modèle au bon endroit.
COPY ./src/models/trained_model.joblib /src/models/trained_model.joblib

# Exposition des ports.
EXPOSE 8000

# Lancement du serveur
CMD ["uvicorn", "--app-dir=./src/api", "api:api", "--host", "0.0.0.0", "--port", "8000"]
