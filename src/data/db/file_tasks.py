"""CSV file checking utils."""
from pathlib import Path
from typing import Tuple
import os

import pandas as pd 
import numpy as np
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

def check_if_files_are_the_expected_ones(path_raw_data_dir: Path, file_pfix: str = "csv"):
    """Checks if the raw csv files in a directory are the expected ones."""
    expected_files = {"caracteristiques", "lieux", "usagers", "vehicules"}

    files = list(path_raw_data_dir.glob(f"*.{file_pfix}"))
    for exp_file in expected_files:
        if any(exp_file in f.name for f in files):
            continue
        raise FileNotFoundError(f"Error: could not find file '{exp_file}' in files.")

def check_if_files_are_same_year(path_raw_data_dir: Path, file_pfix: str = "csv", f_sep: str = "-") -> str:
    files = list(path_raw_data_dir.glob(f"*.{file_pfix}"))
    fs = [f.name.split(f".{file_pfix}")[0] for f in files]
    years = {f.split(f_sep)[-1] for f in fs}
    if len(years) > 1:
        raise ValueError("Error: More than 1 year found in the filenames: {years}")
    year = years.pop()
    return year


def get_filenames(path_raw_data_dir: Path, file_pfix: str = "csv"):
    files = list(path_raw_data_dir.glob(f"*.{file_pfix}"))

    caracteristiques_file = None
    lieux_file = None
    usagers_file = None
    vehicules_file = None

    for file in files:
        if "caracteristiques" in file.name:
            caracteristiques_file = file
        if "lieux" in file.name:
            lieux_file = file
        if "usagers" in file.name:
            usagers_file = file
        if "vehicules" in file.name:
            vehicules_file = file

    return caracteristiques_file, lieux_file, usagers_file, vehicules_file


def get_dataframes(caracteristiques_file:Path, lieux_file:Path, usagers_file: Path, vehicules_file:Path) -> Tuple[pd.DataFrame]:
    #--Importing dataset
    df_users = pd.read_csv(usagers_file, sep=";").replace({np.NaN: None})
    df_caract = pd.read_csv(caracteristiques_file, sep=";", header=0, low_memory=False).replace({np.NaN: None})
    df_places = pd.read_csv(lieux_file, sep = ";", encoding='utf-8')
    df_veh = pd.read_csv(vehicules_file, sep=";")

    return df_caract, df_places, df_users, df_veh


def main():
    path = os.getenv("RAW_FILES_ROOT_DIR")
    if not path:
        raise Exception("Env variable `RAW_FILES_ROOT_DIR` not set!")
    
    path = Path(path)
    check_if_files_are_the_expected_ones(path_raw_data_dir=path)
    year = check_if_files_are_same_year(path_raw_data_dir=path)
    print(f"Year of data is = {year}")
    caracteristiques_file, lieux_file, usagers_file, vehicules_file = get_filenames(path_raw_data_dir=path)
    df_caract, df_places, df_users, df_veh = get_dataframes(caracteristiques_file=caracteristiques_file,
                                                            lieux_file=lieux_file,
                                                            usagers_file=usagers_file,
                                                            vehicules_file=vehicules_file)
    
    return df_caract, df_places, df_users, df_veh, year

if __name__ == "__main__":
    main()