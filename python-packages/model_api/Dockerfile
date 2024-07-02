# Note: Run this first `sudo chmod -R 777 python-packages/road_accidents_database_ingestion` 
#   otherwise the `python -m pip install -e .` will fail.
#   or run `DOCKER_BUILDKIT=1 docker-compose up`
FROM python:3.12-slim

RUN apt-get update && apt-get install python3-pip -y

#set up a Working directory in the container
WORKDIR /app

#copy in the needed requirements and files
COPY --chmod=777 . .

#installing all necessary requirements
RUN python -m pip install -e .

EXPOSE 8000

#run the application
CMD ["python", "src/model_api/api.py"]