import pytest
from fastapi import HTTPException
from fastapi.security import HTTPBasicCredentials

# Problème:
# Pourquoi "from api import" ne fonctionne pas ? alors que dans "test_api_fonction" cela marche.
#from api import verif_user, verif_admin
from src.api.api import verif_user, verif_admin


def test_verif_user_ok():
    creds = HTTPBasicCredentials(username="alice", password="wonderland")
    users = {"alice": "wonderland"}
    result = verif_user(creds) 
    assert result == True 


def test_verif_user_not_ok():
    creds = HTTPBasicCredentials(username="alice", password="7ùé#")
    users = {"alice": "wonderland"}
    with pytest.raises(HTTPException):
        verif_user(creds) 
       
def test_verif_admin_ok():
    creds = HTTPBasicCredentials(username="admin1", password="admin1")
    admins = {"admin1": "admin1"}
    result = verif_admin(creds)    
    assert result == True 

def test_verif_admin_not_ok():
    creds = HTTPBasicCredentials(username="alice", password="7ùé#")
    admins = {"admin1": "admin1"}
    with pytest.raises(HTTPException):
        verif_admin(creds)  

        



