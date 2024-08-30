# Import des bibliothèques nécessaires au projet
import pandas as pd
import numpy as np
import warnings
import time
import scipy.stats as stats

# Ignorer les avertissements
warnings.filterwarnings("ignore", category=pd.errors.DtypeWarning)

from sklearn.model_selection import train_test_split
from imblearn.under_sampling import RandomUnderSampler

# crréation d'une fonction pour séparer les features et la colonne target
def split_features_target(df, target_column):

    X = df.drop(columns=[target_column])
    y = df[target_column]
    return X, y

# crréation d'une fonction pour reéquilibrer les data
def resample_data(X_train, y_train):
    
    ru = RandomUnderSampler()
    X_train_resampled, y_train_resampled = ru.fit_resample(X_train, y_train)
    return X_train_resampled, y_train_resampled

#création d'une fonction globale pour le pré-processing

def process_data(file_path):
    """
    réaliser lae pré-processing des data

    Args:
    - file_path (str): chemin du dataset.

    Returns:
    - X_train_resampled (pd.DataFrame): Resampled training features.
    - X_test (pd.DataFrame): Testing features.
    - y_train_resampled (pd.Series): Resampled training labels.
    - y_test (pd.Series): Testing labels.
    """

    #import du dataset
    df = pd.read_csv(file_path, index_col=0)
    
    # on sépare les variables cibles et les caractéristiques
    X, y = split_features_target(df, 'grav')

    # on divise les données en ensemble d'entraînement et de test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    

    # afin de régler ce déséquilibre de classe, nous allons faire  un randomundersampler et l'appliquer à nos données
    X_train_resampled, y_train_resampled = resample_data(X_train, y_train)
    

    return X_train_resampled, X_test, y_train_resampled, y_test

    



def main():
    file_path = '../data/data_2005a2021_final.csv'
    X_train_resampled, X_test, y_train_resampled, y_test = process_data(file_path)
    print(len(y_train_resampled))
    


if __name__ == "__main__":
    main()
    
    
