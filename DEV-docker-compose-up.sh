#!/bin/sh

######################################################################################
# This shell scripts starts the docker-compose application in Development mode       #
#   Development mode means that instead of pulling our Docker images from the        #
#   DockerHub (CI/CD pipeline), it builds the local Docker Images.                   #
#                                                                                    #  
# Execute this script from the root directory of the may24_bmlops_accidents project: #
#   ./DEV-docker-compose-up.sh                                                       #
######################################################################################

echo "Remove all Docker Images not assigned to a Docker Container"
docker image prune -a

echo "Build the local 'airflowdb' Docker Image"
cd python-packages
DOCKER_BUILDKIT=1 docker image build --no-cache -f airflowdb.Dockerfile . -t roadaccidentsmlops24/airflowdb:latest

echo "Build the local 'model_api' Docker Image"
cd model_api
DOCKER_BUILDKIT=1 docker image build --no-cache . -t roadaccidentsmlops24/model_api:latest

echo "Build the local 'green_light_ui' Docker Image"
cd ../green_light_ui
DOCKER_BUILDKIT=1 docker image build --no-cache . -t roadaccidentsmlops24/accidents_ui:latest

echo "Start the Docker Compose App."
cd ../../
DOCKER_BUILDKIT=1 docker-compose up -d
