import codecs
import os
from datetime import datetime
from typing import Annotated

import requests
from authlib.oauth2.rfc9068 import JWTBearerTokenValidator
from fastapi import Depends, Request
from fastapi import FastAPI
from kafka import KafkaProducer
from starlette.responses import JSONResponse

app = FastAPI()
ISS = os.environ.get('ISS', 'http://127.0.0.1:8000')

KAFKA_HOST = os.environ.get('KAFKA_HOST', 'localhost:9092')
KAFKA_GROUP_ID = os.environ.get('KAFKA_GROUP_ID', 'init_step')
KAFKA_OFFSET = os.environ.get('KAFKA_OFFSET', 'earliest')

kafka_producer = KafkaProducer(
    bootstrap_servers=KAFKA_HOST,
    client_id="easy_production",
    value_serializer=lambda v: v.encode('utf-8')
)


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


@app.post('/experiments')
async def experiments(
        current_admin: Annotated[str, Depends(get_admin_user)],
) -> JSONResponse:
    experiment = 'experiment-' + str(datetime.today().strftime('%Y-%m-%d_%H-%M-%S'))
    kafka_producer.send(topic=KAFKA_GROUP_ID, value=experiment)
    kafka_producer.flush()
    return JSONResponse(status_code=204, content=None)
