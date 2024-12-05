FROM python:3-slim-bookworm

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY 3_train_model.py /code/src/3_train_model.py
COPY 4_selection.py /code/src/4_selection.py

ENV PYTHONPATH=/code/src

CMD ["/bin/sh", "-c", "mlflow ui --host 0.0.0.0 --port 5000 & python /code/src/3_train_model.py & fastapi run /code/src/4_selection.py --port 80"]
