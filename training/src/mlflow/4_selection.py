import codecs
import os
import pickle
from typing import Annotated

import lakefs
import mlflow
import redis
import requests
from authlib.oauth2.rfc9068 import JWTBearerTokenValidator
from fastapi import Depends, Request
from fastapi import FastAPI
from lakefs.client import Client
from mlflow import MlflowClient
from starlette.responses import JSONResponse

app = FastAPI()

ISS = os.environ.get('ISS', 'http://127.0.0.1:8000')

LAKE_FS_HOST = os.environ.get('LAKE_FS_HOST', 'http://localhost:8083')
LAKE_FS_USERNAME = os.environ.get('LAKE_FS_USERNAME', 'AKIAIOSFOLQUICKSTART')
LAKE_FS_PASSWORD = os.environ.get('LAKE_FS_PASSWORD', 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY')

REDIS_URL = os.environ.get('REDIS_URL', 'localhost')

redis = redis.StrictRedis(REDIS_URL)


class AccidentJWTBearerTokenValidator(JWTBearerTokenValidator):
    def get_jwks(self):
        response = requests.get(os.path.join(ISS, '.well-known/jwks.json'), timeout=2,
                                headers={"Content-Type": "application/json"})
        return response.json()


def get_admin_user(
        request: Request,
):
    token = request.headers.get('Authorization')
    token_decode = AccidentJWTBearerTokenValidator.authenticate_token(
        AccidentJWTBearerTokenValidator(issuer=ISS, resource_server=ISS),
        codecs.encode(token)
    )
    AccidentJWTBearerTokenValidator.validate_token(
        AccidentJWTBearerTokenValidator(issuer=ISS, resource_server=ISS),
        token=token_decode,
        scopes=['admin'],
        request='')
    return token_decode.get('sub')


# LakeFS
clt = Client(
    host=LAKE_FS_HOST,
    username=LAKE_FS_USERNAME,
    password=LAKE_FS_PASSWORD
)


def deploy_latest_model_version():
    client = MlflowClient()
    registered_model = client.search_model_versions(
        filter_string="name = 'accidents_sk-learn-random-forest-class-model' and tag.validation_status = 'approved'",
        order_by=['version_number DESC'],
        max_results=1
    )
    model_uri = f"models:/accidents_sk-learn-random-forest-class-model/{registered_model[0].version}"
    model = mlflow.sklearn.load_model(model_uri)
    redis.set('accidents', pickle.dumps(model))
    redis.set('version', registered_model[0].version)


@app.post('/models/{experiment_id}/promote')
async def promote(
        experiment_id: str,
        current_user: Annotated[str, Depends(get_admin_user)],
) -> JSONResponse:
    # LakeFS
    branch = lakefs.repository('accidents', client=clt).branch(experiment_id)
    main = lakefs.repository('accidents', client=clt).branch('main')

    branch.merge_into(main)
    # retrieve pull request bug
    # pr = clt.sdk_client.pulls_api.list_pull_requests('accidents', status='open')
    # clt.sdk_client.pulls_api.merge_pull_request('accidents', pr[0].id)
    branch.delete()

    # MLflow
    client = MlflowClient()
    model = client.get_model_version_by_alias('accidents_sk-learn-random-forest-class-model', experiment_id)
    client.set_model_version_tag(
        'accidents_sk-learn-random-forest-class-model',
        model.version,
        'validation_status',
        'approved'
    )
    return JSONResponse(status_code=204, content=None)


@app.post('/models/deploy')
async def promote(
        current_user: Annotated[str, Depends(get_admin_user)],
) -> JSONResponse:
    deploy_latest_model_version()
    return JSONResponse(status_code=204, content=None)
