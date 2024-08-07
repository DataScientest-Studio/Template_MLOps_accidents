# Import des bibliothèques nécessaires au projet
import pandas as pd
import numpy as np
import warnings
import logging 


# Ignorer les avertissements
warnings.filterwarnings("ignore", category=pd.errors.DtypeWarning)

from sklearn.ensemble import RandomForestClassifier
import pickle
import joblib
from  Preprocessing import process_data 
from config_logging import setup_logging

# Configuration du logging
setup_logging('predict.log')

# Création d'un logger
logger = logging.getLogger(__name__)


#création d'une fonction pour prédiction
def predict_model(model, X_test):

    """
    Description:
    Réaliser des prédiction en utilisant le modèle entrainé.

    Args:
    - model (RandomForestClassifier): modèle entrainé.
    - X_test (pd.DataFrame): l'échantillon test..

    Returns:
    - y_pred (np.ndarray): les prédictions.
    """
    try:
        y_pred = model.predict(X_test)
        return y_pred
    except Exception as e:
        logger.error(f"Failed to make predictions: {e}")
        raise



def main():
    try:
        file_path = '../data/data_2005a2021.csv'
        X_train_resampled, X_test, y_train_resampled, y_test = process_data(file_path)
        model_output_path = '../../models/model_rf_clf.pkl'
        
        # Charger le modèle
        model_data = joblib.load(model_output_path)
        if isinstance(model_data, dict):
            model = model_data.get('model', None)
            if model is None:
                raise ValueError("No model found in the loaded data.")
        else:
            model = model_data
        
        logger.info("Model loaded successfully")

        # Réaliser les prédictions
        y_pred = predict_model(model, X_test)
        
        # Enregistrer les 10 premières prédictions dans le log
        logger.info(f"Les 10 premières prédictions : {y_pred[:10]}")

    except Exception as e:
        logger.error(f"Failed in main execution: {e}")
        raise




if __name__ == "__main__":
    main()