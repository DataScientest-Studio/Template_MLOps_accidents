"""CSV file checking utils."""
from pathlib import Path
from typing import Tuple, Dict
import os
import hashlib

import pandas as pd 
import numpy as np
from dotenv import load_dotenv

from src.data.db.enum import RawRoadAccidentCsvFileNames
from src.data.db.models import RawRoadAccidentsCsvFile

load_dotenv()  # take environment variables from .env.

def check_if_files_are_the_expected_ones(path_raw_data_dir: Path, file_pfix: str = "csv") -> bool:
    """Checks if the raw csv files in a directory are the expected ones."""
    expected_files = {RawRoadAccidentCsvFileNames.caracteristiques, 
                      RawRoadAccidentCsvFileNames.lieux, 
                      RawRoadAccidentCsvFileNames.usagers,
                      RawRoadAccidentCsvFileNames.vehicules}

    files = list(path_raw_data_dir.glob(f"*.{file_pfix}"))
    for exp_file in expected_files:
        if any(exp_file in f.name for f in files):
            continue
        raise FileNotFoundError(f"Error: could not find file '{exp_file}' in files.")
    return True

def get_files(path_raw_data_dir: Path, file_pfix: str = "csv", f_sep: str = "-")-> Dict[RawRoadAccidentCsvFileNames, RawRoadAccidentsCsvFile]:
    files = list(path_raw_data_dir.glob(f"*.{file_pfix}"))
    file_stats = {}
    for file in files:
        raw_accident_csv_file = None
        if RawRoadAccidentCsvFileNames.caracteristiques in file.name:
            raw_accident_csv_file = RawRoadAccidentCsvFileNames.caracteristiques
        if RawRoadAccidentCsvFileNames.lieux in file.name:
            raw_accident_csv_file = RawRoadAccidentCsvFileNames.lieux
        if RawRoadAccidentCsvFileNames.usagers in file.name:
            raw_accident_csv_file = RawRoadAccidentCsvFileNames.usagers
        if RawRoadAccidentCsvFileNames.vehicules in file.name:
            raw_accident_csv_file = RawRoadAccidentCsvFileNames.vehicules
        
        if raw_accident_csv_file:
            file_stats[raw_accident_csv_file]=RawRoadAccidentsCsvFile(
                    raw_accident_file=raw_accident_csv_file,
                    file_name=file.name,
                    dir_name=file.parent.name,
                    md5=hashlib.md5(open(file, 'rb').read()).hexdigest(),
                   sha256=hashlib.sha256(open(file, 'rb').read()).hexdigest()
                )
            
    return file_stats



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

def convert_object_cols_to_str(df: pd.DataFrame) -> pd.DataFrame:
    stringcols = df.select_dtypes(include='object').columns
    df[stringcols] = df[stringcols].fillna('').astype(str)
    return df

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
    df_places = convert_object_cols_to_str(df_places)
    return df_caract, df_places, df_users, df_veh, year

if __name__ == "__main__":
    main()