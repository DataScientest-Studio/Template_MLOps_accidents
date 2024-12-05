FROM python:3-slim-bookworm

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY 2_make_dataset.py /code/src/2_make_dataset.py

ENV PYTHONPATH=/code/src

CMD ["/bin/sh", "-c", "python /code/src/2_make_dataset.py"]
