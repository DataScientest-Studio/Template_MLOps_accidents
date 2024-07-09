cd Volumes/data/mlflow/mlruns
mlflow server --host 127.0.0.1 --port 5000 & 
cd /home/ubuntu/Documents/Developoment/may24_bmlops_accidents
docker compose down
DOCKER_BUILDKIT=1 docker compose up -d 
# DOCKER_BUILDKIT=1 docker compose up -d  --force-recreate