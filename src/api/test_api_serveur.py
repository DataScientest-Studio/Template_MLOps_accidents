import pytest
import requests


def test_status():
    url = "http://127.0.0.1:8000/status"    
    response = requests.get(url)
    
    if response.status_code == 200:
        assert response.json()['status'] == 'ok'
    else:
        print(f"Erreur : {response.status_code}")
        assert False


def test_create_user_success():
    url = "http://127.0.0.1:8000/new_user"
    users = {"alice": "wonderland"}    
    response = requests.post(
        url,
        json={"name": "testuser", "password": "testpass"}, 
        auth = ('admin1', 'admin1')
    )
    assert response.status_code == 200, response.text
    assert response.json() == {"user créé avec succès": {"name": "testuser", "password": "testpass"}}

def test_create_user_already_exists():
    url = "http://127.0.0.1:8000/new_user"
    users = {"alice": "wonderland"}    
    response = requests.post(
        url,
        json={"name": "testuser", "password": "testpass"}, 
        auth = ('admin1', 'admin1')
    )
    assert response.status_code == 405, response.text
    assert response.json() == {"detail": "name already present, choose another name"}

def test_create_admin_success():
    url = "http://127.0.0.1:8000/new_admin"
    admin = {"admin1": "admin1"}    
    response = requests.post(
        url,
        json={"name": "testadmin", "password": "testadminpass"}, 
        auth = ('admin1', 'admin1')
    )
    assert response.status_code == 200, response.text
    assert response.json() == {"new admin créee avec succes": {"name": "testadmin", "password": "testadminpass"}}

def test_create_admin_already_exists():
    """ Si le name est déja dans users, le refuser """
    url = "http://127.0.0.1:8000/new_admin"
    admin = {"admin1": "admin1"} 
    users = {"alice": "wonderland", "admin1": "admin1"}     
    response = requests.post(
        url,
        json={"name": "admin1", "password": "testadminpass"}, 
        auth = ('admin1', 'admin1')
    )
    assert response.status_code == 405, response.text
    assert response.json() == {"detail": "name already present, choose another name"}

def test_prediction():
    url = "http://127.0.0.1:8000/prediction"
    features_4_prediction = {'place':10,
                                'catu':3,
                                'sexe':2,
                                'secu1':0.0,
                                'year_acc':2021,
                                'victim_age':19.0,
                                'catv':2.0,
                                'obsm':1.0,
                                'motor':1.0,
                                'catr':4,
                                'circ':2.0,
                                'surf':1.0,
                                'situ':1.0,
                                'vma':30.0,
                                'jour':4,
                                'mois':11,
                                'lum':5,
                                'dep':59,
                                'com':59350,
                                'agg_':2,
                                'int':2,
                                'atm':0.0,
                                'col':6.0,
                                'lat':50.6325934047,
                                'long':3.0522062542,
                                'hour':22,
                                'nb_victim':4,
                                'nb_vehicules':1
                            }
    # En-têtes (headers) si nécessaire
    headers = {
        "Content-Type": "application/json",
        # Ajoutez d'autres en-têtes ici
    }
    response = requests.post(url, json=features_4_prediction, headers=headers, 
                            auth = ('admin1', 'admin1'))
    if response.status_code == 200:
        print(response.json()['prediction'])
        assert response.json()['prediction'] == 0
    else:
        print(f"Erreur : {response.status_code}")
        assert False

if __name__ == '__main__':
    #
    #
    # Uniquement à des fins de debug en manuel (sans passer par le serveur FastAPI)
    #
    #
    test_status()
    test_prediction()

