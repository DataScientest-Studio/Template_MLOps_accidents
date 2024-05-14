#!/bin/bash

# IMPORT DATA
docker run --rm --mount type=volume,src=shield_volume,dst=/home/volume alexandrewinger/shield:import_data

# MAKE DATASET
docker run --rm --mount type=volume,src=shield_volume,dst=/home/volume alexandrewinger/shield:make_dataset

# CREATE USERS DB
docker run --rm --mount type=volume,src=shield_volume,dst=/home/volume alexandrewinger/shield:create_users_db

# TRAIN MODEL
docker run --rm --mount type=volume,src=shield_volume,dst=/home/volume alexandrewinger/shield:train_model

# API
docker run -p 8000:8000 --rm --mount type=volume,src=shield_volume,dst=/home/volume/ --network=shield-network --name api alexandrewinger/shield:api

# TEST
docker run --rm --mount type=volume,src=shield_volume,dst=/home/volume --network=shield-network --name test_shield alexandrewinger/shield:test_shield