import os 

def test_raw_data_files_exist():
    base_path = "./data/raw"
    files = [
        "usagers-2021.csv",
        "caracteristiques-2021.csv",
        "lieux-2021.csv",
        "vehicules-2021.csv"
    ]

    for f in files:
        file_path = os.path.join(base_path, f)
        assert os.path.isfile(file_path), f"Le fichier {f} est manquant dans {base_path}"

def test_preprocessed_data_file_exists():   
    base_path = "./data/preprocessed"
    files = [
        "X_train.csv",
        "X_test.csv",  
        "y_train.csv",
        "y_test.csv",
    ]

    for f in files:
        file_path = os.path.join(base_path, f)
        assert os.path.isfile(file_path), f"Le fichier {f} est manquant dans {base_path}"