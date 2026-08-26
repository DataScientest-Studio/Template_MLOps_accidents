FROM python:3.12-slim

WORKDIR /app

COPY ./src/bentoml/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./src/bentoml/. .
EXPOSE 3000

CMD ["bentoml", "serve", "service:PredictService", "--host", "0.0.0.0", "--port", "3000", "--production"]
