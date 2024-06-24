FROM python:3.9.13-slim-buster

RUN apt-get update && apt-get install python3-pip -y

WORKDIR /app/

COPY . .

RUN pip3 install -r requirements.txt

CMD python3 src/data/db/db_tasks.py