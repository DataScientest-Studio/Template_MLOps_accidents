#!/bin/sh

######################################################################################
#                                                                                    #  
# This shell scripts starts the docker-compose application in Production mode        #
#   Production mode means that the Docker images will be pulled from the DockerHub   #
#   (added there from our CI/CD pipeline).                                           #
#                                                                                    #  
# Execute this script from the root directory of the may24_bmlops_accidents project: #
#   ./PROD-docker-compose-up.sh                                                      #
#                                                                                    #  
# Or if you want to use a specific Release (Tag) of the may24_bmlops_accidents:      #  
#   GLS_TAG="v0.0.4" ./PROD-docker-compose-up.sh                                     #
#                                                                                    #  
# You can find the released version for each Docker Image in this link:              #  
#    https://hub.docker.com/u/roadaccidentsmlops24  by clicking to a specific image  #
#                                                                                    #  
######################################################################################

echo "Remove all Docker Images not assigned to a Docker Container"
docker image prune -a

echo "Start the Docker Compose App."
DOCKER_BUILDKIT=1 docker compose up -d

echo "Starting MLFlow server"
cd Volumes/data/mlflow
./run_mlfow_server.sh
cd ../../../