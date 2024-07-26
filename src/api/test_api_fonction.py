import pytest
from src.api.api import predict

"""
def test_performance():
    #récupérer les scores de scores.json
    
    assert performance>0.6
"""

def test_predict():
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
    ma_prediction = predict(features_4_prediction)
    assert ma_prediction == 0


# def test_predict_aws_s3():
    # features_4_prediction = {'place':10,
                             # 'catu':3,
                             # 'sexe':2,
                             # 'secu1':0.0,
                             # 'year_acc':2021,
                             # 'victim_age':19.0,
                             # 'catv':2.0,
                             # 'obsm':1.0,
                             # 'motor':1.0,
                             # 'catr':4,
                             # 'circ':2.0,
                             # 'surf':1.0,
                             # 'situ':1.0,
                             # 'vma':30.0,
                             # 'jour':4,
                             # 'mois':11,
                             # 'lum':5,
                             # 'dep':59,
                             # 'com':59350,
                             # 'agg_':2,
                             # 'int':2,
                             # 'atm':0.0,
                             # 'col':6.0,
                             # 'lat':50.6325934047,
                             # 'long':3.0522062542,
                             # 'hour':22,
                             # 'nb_victim':4,
                             # 'nb_vehicules':1
                            # }    
    # ma_prediction = predict_aws_s3(features_4_prediction)
    # assert ma_prediction == 0