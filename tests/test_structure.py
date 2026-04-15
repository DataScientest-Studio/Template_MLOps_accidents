# test_structure.py (version ed01) dans le répertoire ./tests/

import os
import pandas as pd

def test_data_files_exist():
    """ Vérifie si les fichiers de données ont été générés """
    # On vérifie si après le run, les fichiers sont bien là
    assert os.path.exists("data/preprocessed/X_train.csv")
    assert os.path.exists("data/preprocessed/X_test.csv")

def test_training_data_content():
    """ Vérifie si le fichier n'est pas vide et a les bonnes colonnes """
    if os.path.exists("data/preprocessed/X_train.csv"):
        df = pd.read_csv("data/preprocessed/X_train.csv")
        assert len(df) > 0  # On veut au moins une ligne !
        assert "nb_victim" in df.columns  # On vérifie qu'une colonne clé existe