from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
import joblib
import os
from passlib.context import CryptContext
import pickle

# on définit notre API
app_accuracy = FastAPI()

# on charge notre modele allant être appelé dans l API
model_path = '../../../models/model_rf_clf.pkl'
if not os.path.exists(model_path):
    raise FileNotFoundError(f"Le fichier de modèle {model_path} n'existe pas.")
with open(model_path, 'rb') as model_file:
    model_data = joblib.load(model_file)
    print(model_data)
    if not isinstance(model_data, dict):
        raise ValueError("Le fichier pickle ne contient pas de dictionnaire.")

    model = model_data.get('model')
    accuracy = model_data.get('accuracy')

    if model is None or accuracy is None:
        raise ValueError("Le dictionnaire chargé ne contient pas les clés 'model' et 'accuracy'.")

# on définit une BaseModel permettant de cadrer le format de requete avec l ajout de nouvelles donnees d accident pour appeler le modele
class DonneesAccident(BaseModel):
    place: int
    catu: int
    trajet: float
    an_nais: int
    catv: int
    choc: float
    manv: float
    mois: int
    jour: int
    lum: int
    agg: int
    int: int
    col: float
    com: int
    dep: int
    hr: int
    mn: int
    catr: int
    circ: float
    nbv: int
    prof: float
    plan: float
    lartpc: int
    larrout: int
    situ: float


# on définit la sécurité de notre app

security = HTTPBasic()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# on crée une base d utilisateur fictive
users = {
    "user1": {
        "username": "user1",
        "name": "Sousou",
        "hashed_password": pwd_context.hash('datascientest'),
        "role": "standard",
    },
    "user2": {
        "username": "user2",
        "name": "Mim",
        "hashed_password": pwd_context.hash('secret'),
        "role": "standard",
    },
    "admin": {
        "username": "admin",
        "name": "Admin",
        "hashed_password": pwd_context.hash('adminsecret'),
        "role": "admin",
    }
}

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    username = credentials.username
    user = users.get(username)
    if not user or not pwd_context.verify(credentials.password, user['hashed_password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiant ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user


def get_current_admin_user(user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Droits non autorisés",
        )
    return user

@app_accuracy.get("/")
def current_user(user: dict = Depends(get_current_admin_user)):
    """
    Description:
    Cette route renvoie un message de bienvenue personnalisé en utilisant le nom d'utilisateur fourni.

    Args:
    - user : utilisateur récupéré à partir de la dépendance `get_current_user`.

    Returns:
    - str: Un message de bienvenue personnalisé sur l application
    """
    return {"message": f"Bienvenue sur notre application de prédiction d'accident, {user['name']}!"}


@app_accuracy.get("/accuracy")
def get_accuracy(user: dict = Depends(get_current_admin_user)):
    """
    Description:
    Endpoint pour obtenir l'accuracy du modèle.

    Args:
    - user : L'utilisateur récupéré à partir de la dépendance `get_current_admin_user`.

    Returns:
    - dict: L'accuracy du modèle.
    """
    return {"L accuracy du modele utilise est de " : accuracy}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app_accuracy, host="0.0.0.0", port=8002)
