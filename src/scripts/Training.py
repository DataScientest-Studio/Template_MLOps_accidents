# Import des bibliothèques nécessaires au projet
import pandas as pd
import numpy as np
import warnings
import logging

import time

# Ignorer les avertissements
warnings.filterwarnings("ignore", category=pd.errors.DtypeWarning)

from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.ensemble import RandomForestClassifier
import pickle
import joblib
from  Preprocessing import process_data 
from config_logging import setup_logging

# Configuration du logging
setup_logging('training.log')

# Création d'un logger
logger = logging.getLogger(__name__)


# création de la fonction pour training

def train_model(X_train, y_train, random_state=42):
    try:
        model_rf_clf = RandomForestClassifier(random_state=random_state)
        start_time = time.time()
        model_rf_clf.fit(X_train, y_train)
        end_time = time.time()
        training_time = end_time - start_time
        logger.info(f"Temps d'entraînement du modèle : {training_time:.2f} secondes")
        return model_rf_clf, training_time
    except Exception as e:
        logger.error(f"Failed to train model: {e}")
        raise


# Création de la fonction pour évaluation
def evaluate_model(model, X_test, y_test):
    try:
        y_pred = model.predict(X_test)
        
        logger.info("Confusion Matrix:")
        logger.info(confusion_matrix(y_test, y_pred))

        logger.info("\nClassification Report:")
        logger.info(classification_report(y_test, y_pred))

        logger.info("\nAccuracy Score:")
        accuracy=accuracy_score(y_test, y_pred)
        logger.info(accuracy)
        return accuracy
    except Exception as e:
        logger.error(f"Failed to evaluate model: {e}")
        raise


# Création de la fonction pour sauvegarde de modèle et l'accuracy
def save_model(model,accuracy,model_output_path):
    try:
        model_data = {
                        'model': model,
                        'accuracy': accuracy
                     }
        with open(model_output_path, 'wb') as file:
            joblib.dump(model_data , file)
        logger.info(f"Model saved to {model_output_path}")
    except Exception as e:
        logger.error(f"Failed to save model: {e}")
        raise






def main():
    try:
        file_path = "../data/data_2005a2021_final.csv"
        X_train_resampled, X_test, y_train_resampled, y_test = process_data(file_path)
        model_output_path = '../../models/model_rf_clf.pkl'

        # Train the model
        model, training_time = train_model(X_train_resampled, y_train_resampled)

        # Evaluate the model
        accuracy=evaluate_model(model, X_test, y_test)

        # Save the model
        #save_model(model,accuracy, model_output_path)

    except Exception as e:
        logger.error(f"Error in training process: {e}")

if __name__ == "__main__":
    main()
   










