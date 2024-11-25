import codecs
import os
from typing import Annotated

from authlib.oauth2.rfc9068 import JWTBearerTokenValidator
from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from starlette.responses import JSONResponse

from api import TokenDto, UserCreationDto
from domain import UserService, NotFoundException, User, Role, JwtService, PasswordException
from main import app
from repository_jdbc import UserRepositoryImpl
from repository_jwt import JwtRepositoryImpl

user_service = UserService(UserRepositoryImpl())
jwt_service = JwtService(JwtRepositoryImpl())

ISS = os.environ.get('ISS', 'http://127.0.0.1:8080')


async def get_current_user(
        request: Request,
):
    token = request.headers.get("Authorization")
    token_decode = AccidentJWTBearerTokenValidator.authenticate_token(
        AccidentJWTBearerTokenValidator(issuer=ISS, resource_server=ISS),
        codecs.encode(token)
    )
    AccidentJWTBearerTokenValidator.validate_token(
        AccidentJWTBearerTokenValidator(issuer=ISS, resource_server=ISS),
        token=token_decode,
        scopes=[],
        request="")
    return token_decode.get('sub')


class AccidentJWTBearerTokenValidator(JWTBearerTokenValidator):
    def get_jwks(self):
        return jwt_service.get_jwks()


@app.post("/token")
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> TokenDto:
    user: User = user_service.authenticate_user(form_data.username, form_data.password)
    token = jwt_service.create_access_token(user)
    return TokenDto(access_token=token.access_token, token_type=token.token_type)


@app.post("/users")
async def create_user(
        user: UserCreationDto,
        current_user: Annotated[str, Depends(get_current_user)],
) -> JSONResponse:
    user_service.add_user(user.username, user.password, Role.POLICE)
    return JSONResponse(status_code=204, content=None)


@app.post("/admins")
async def create_admin(
) -> JSONResponse:
    user_service.add_user('admin', 'admin', Role.ADMIN)
    return JSONResponse(status_code=204, content=None)


@app.get("/.well-known/jwks.json")
async def jwks() -> dict:
    return jwt_service.get_jwks()


@app.get("/token/verify")
async def verify_token(
        current_user: Annotated[str, Depends(get_current_user)],
) -> JSONResponse:
    return JSONResponse(status_code=200, content={"response": "ok"})


@app.exception_handler(NotFoundException)
def api_exception_handler(
        request: Request,
        exception: NotFoundException
):
    return JSONResponse(
        status_code=404,
        content={
            'message': 'User not found'
        }
    )

@app.exception_handler(PasswordException)
def api_exception_handler(
        request: Request,
        exception: PasswordException
):
    return JSONResponse(
        status_code=401,
        content={
            'message': 'Password error'
        }
    )
