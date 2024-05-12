#!/bin/bash

# IMPORT_DATA
docker push alexandrewinger/shield:import_data

# MAKE_DATASET
docker push alexandrewinger/shield:make_dataset

# CREATE_USERS
docker push alexandrewinger/shield:create_users_db

# TRAIN_MODEL
docker push alexandrewinger/shield:train_model

# API
docker push alexandrewinger/shield:api

# TEST_API
docker push alexandrewinger/shield:test_api
