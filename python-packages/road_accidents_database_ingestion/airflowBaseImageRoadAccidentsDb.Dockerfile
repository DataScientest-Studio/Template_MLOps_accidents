FROM apache/airflow:2.9.2

WORKDIR /app

#copy in the needed requirements and files
COPY --chmod=777 . .

# Note: Run this first `sudo chmod -R 777 python-packages/road_accidents_database_ingestion` otherwise the `python -m pip install -e .` will fail.
#   or run `DOCKER_BUILDKIT=1 docker-compose up`
RUN python -m ensurepip --upgrade && python -m pip install --upgrade pip && python -m pip install -e .