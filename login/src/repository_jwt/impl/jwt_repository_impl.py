import os
import uuid
from datetime import datetime, timedelta, timezone

from authlib.jose import jwt
from joserfc._keys import JWKRegistry

from domain import User, Role, Token, JwtRepository

ACCESS_TOKEN_EXPIRE_MINUTES = 60
ISS = os.environ.get('ISS', 'http://127.0.0.1:8080')

key = JWKRegistry.generate_key("RSA", 2048, {"use": "sig"})
public_key = key.public_key
private_key = key.private_key


class JwtRepositoryImpl(JwtRepository):

    def create_access_token(self, user: User) -> Token:
        scopes = []
        if Role.ADMIN in user.roles:
            scopes = ['admin']
        to_encode = {
            "sub": user.username,
            "scope": scopes,
            'iss': ISS,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            'aud': ISS,
            'iat': datetime.now(timezone.utc),
            'jti': uuid.uuid4().__str__(),
            'client_id': 'test'
        }
        encoded_jwt = jwt.encode({'alg': 'RS256', 'typ': 'at+jwt'}, to_encode, private_key)
        return Token(encoded_jwt, 'Bearer')

    def get_jwks(self) -> dict:
        return key.dict_value
