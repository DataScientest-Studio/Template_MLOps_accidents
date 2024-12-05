FROM python:3-slim-bookworm

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY 0_init.py /code/src/0_init.py

ENV PYTHONPATH=/code/src

CMD ["/bin/sh", "-c", "fastapi run /code/src/0_init.py --port 80"]
