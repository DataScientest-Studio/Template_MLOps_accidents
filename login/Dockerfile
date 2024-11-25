FROM python:3.13-alpine3.20

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./src /code/src

ENV PYTHONPATH=/code/src

CMD ["/bin/sh", "-c", "cd src/repository_jdbc/; pyway migrate; cd -; fastapi run /code/src/main.py --port 80"]
