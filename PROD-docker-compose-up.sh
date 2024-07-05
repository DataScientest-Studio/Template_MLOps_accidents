#!/bin/sh

######################################################################################
# This shell scripts starts the docker-compose application in Production mode        #
#   Production mode means that the Docker images will be pulled from the DockerHub   #
#   (added there from our CI/CD pipeline).                                           #
#                                                                                    #  
# Execute this script from the root directory of the may24_bmlops_accidents project: #
#   ./PROD-docker-compose-up.sh                                                      #
######################################################################################

echo "Remove all Docker Images not assigned to a Docker Container"
docker image prune -a

echo "Start the Docker Compose App."
cd ../../
DOCKER_BUILDKIT=1 docker-compose up -d
