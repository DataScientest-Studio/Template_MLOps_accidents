FROM python:3-slim-bookworm

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY 1_import.py /code/src/1_import.py

ENV PYTHONPATH=/code/src

CMD ["/bin/sh", "-c", "python /code/src/1_import.py"]
