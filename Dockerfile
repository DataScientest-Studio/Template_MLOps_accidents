FROM python:3.10-slim

RUN apt-get -y update && apt-get install -y --no-install-recommends git

WORKDIR /code

# Copy requirements.txt first (for Docker layer cache)
COPY ./requirements.txt /code/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# ENSURE CORRECT PYDANTIC
RUN pip install --force-reinstall "pydantic==1.10.13"

# Optional: Show version info for debug
RUN pip show pydantic && pip show fastapi && pip show bentoml && pip show starlette

COPY . .
COPY bentoml/models /root/bentoml/models

