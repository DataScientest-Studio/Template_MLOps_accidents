from fastapi import Request, HTTPException, Body, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, conint, confloat, Field, field_validator
from fastapi import FastAPI
import pandas as pd
import sys
import json
import joblib
import uvicorn
from typing import Dict
import time
import jwt

# JWT settings
JWT_SECRET = "secret"
JWT_ALGORITHM = "HS256"

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "adm1n"

users=[]

# Loading the saved model
loaded_model = joblib.load("src/models/trained_model.joblib")

# Pydantic model for user schema
class UserSchema(BaseModel):
    username: str
    password: str

# Pydantic model for the prediction 
class PredictRequestModel(BaseModel):
    features: Dict[str, float]
    
class ModelInputFeatures(BaseModel):
    place: int
    catu: conint(ge=1, le=4)    #User category
    sexe : conint(ge=1, le=2)   #sex is male (1) or female(2)
    secu1 : float
    year_acc : int
    victim_age : int
    catv : conint(ge=1, le=13)  #Category of vehicle
    obsm : int 
    motor : int
    catr: int = Field(...) #Category of road 1-6 and 9!
    
    @field_validator('catr')
    def validate_catr(cls, value):
        if value not in list(range(1, 7)) + [9]:
            raise ValueError('catr must be between 1-6 or 9')
        return value
      
    circ : conint(ge=1, le=4)   #Traffic regime
    surf : conint(ge=1, le=9)   #surface condition
    situ : conint(ge=1, le=5)   #Situation of the accident
    vma : int
    jour : conint(ge=1, le=31)  # day should be between 1 and 31
    mois : conint(ge=1, le=12)  # month should be between 1 and 12
    lum : conint(ge=1, le=5)    # lighting conditions 5 categories
    dep : int #Department
    com : int #commune number
    agg_ : int
    int : conint(ge=1, le=9)    #type of intersection 9 categories
    atm : conint(ge=1, le=9)    #Atmospheric conditions 9 categories
    col :conint(ge=1, le=7)     #Type of collision 7 cat
    lat : confloat(ge=-90, le=90)  # lat should be between -90 and 90
    long : confloat(ge=-180, le=180)  # long should be between -180 and 180
    hour : conint(ge=0, le=24)  #hour of the day
    nb_victim : int
    nb_vehicules : int 
    
def check_user(data: UserSchema):
    for user in users:
        if user.username == data.username and user.password == data.password:
            return True
    return False


def token_response(token: str):
    return {"access_token": token}

def sign_jwt(user_id: str):
    payload = {"user_id": user_id, "expires": time.time() + 600} # Token expires withni 10 minutes
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return token_response(token)


def decode_jwt(token: str):
    try:
        decoded_token = jwt.decode(
            token, JWT_SECRET, algorithms=[JWT_ALGORITHM]
        )
        return (
            decoded_token if decoded_token["expires"] >= time.time() else None
        )
    except Exception:
        return {}

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(
            JWTBearer, self
        ).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=403, detail="Invalid authentication scheme."
                )
            if not self.verify_jwt(credentials.credentials):
                raise HTTPException(
                    status_code=403, detail="Invalid token or expired token."
                )
            return credentials.credentials
        else:
            raise HTTPException(
                status_code=403, detail="Invalid authorization code."
            )

    def verify_jwt(self, jwtoken: str):
        isTokenValid: bool = False

        try:
            payload = decode_jwt(jwtoken)
        except Exception:
            payload = None
        if payload:
            isTokenValid = True
        return isTokenValid
    
api = FastAPI()

@api.get("/", tags=["root"])
async def read_root():
    return {"message": "Hello World!"}


@api.get("/secured", dependencies=[Depends(JWTBearer())], tags=["root"])
async def read_root_secured():
    return {"message": "Hello World! but secured"}


@api.post("/user/signup", tags=["user"])
async def create_user(user: UserSchema = Body(...)):
    users.append(user)
    return sign_jwt(user.username)

@api.post("/user/login", tags=["user"])
async def user_login(user: UserSchema = Body(...)):
    if user.username == ADMIN_USERNAME and user.password == ADMIN_PASSWORD:
        return sign_jwt(user.username)
    raise HTTPException(status_code=401, detail="Invalid username or password")

@api.post("/predict", tags=["prediction"])
def predict_model(features: ModelInputFeatures):
    input_df = pd.DataFrame([features.model_dump()])
    print(input_df)
    prediction = loaded_model.predict(input_df)
    return {"prediction": prediction.tolist()}

def get_feature_values_manually(feature_names):
    features = {}
    for feature_name in feature_names:
        feature_value = float(input(f"Enter value for {feature_name}: "))
        features[feature_name] = feature_value
    return features

if __name__ == "__main__":
    if len(sys.argv) == 2:
        json_file = sys.argv[1]
        with open(json_file, 'r') as file:
            features = json.load(file)
    else:
        X_train = pd.read_csv("data/preprocessed/X_train.csv")
        feature_names = X_train.columns.tolist()
        features = get_feature_values_manually(feature_names)

    result = predict_model(features)
    print(f"prediction : {result['prediction'][0]}")

    #uvicorn.run(api, host="0.0.0.0", port=8000)