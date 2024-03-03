FROM python:3.8.10

COPY ./models /models
COPY ./src/api /src/api
COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Expose the port on which the application will run
EXPOSE 8000
