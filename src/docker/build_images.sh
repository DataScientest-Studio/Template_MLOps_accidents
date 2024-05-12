#!/bin/bash

# IMPORT_DATA
docker image build  -f ./src/data/import_data.Dockerfile -t alexandrewinger/shield:import_data .

# MAKE_DATASET
docker image build  -f ./src/data/make_dataset.Dockerfile -t alexandrewinger/shield:make_dataset .

# CREATE_USERS
docker image build  -f ./src/users_db/create_users_db.Dockerfile -t alexandrewinger/shield:create_users_db .

# TRAIN_MODEL
docker image build  -f ./src/models/model.Dockerfile -t alexandrewinger/shield:train_model .

# API
docker image build  -f ./src/api/api.Dockerfile -t alexandrewinger/shield:api .

# TEST_API
docker image build  -f ./src/api/test_api.Dockerfile -t alexandrewinger/shield:test_api .
