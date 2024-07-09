"""CSV file checking utils."""

from pathlib import Path
from typing import List, Dict, Optional
import hashlib

import pandas as pd
import numpy as np

from road_accidents_database_ingestion.enums import RawRoadAccidentCsvFileNames
from road_accidents_database_ingestion.models import RawRoadAccidentsCsvFile



def validate_road_accident_files_are_the_expected_ones(file_paths: List[Path]) -> bool:
    """Checks if the raw csv files in a directory are the expected ones.

    Each road accident directory should contain 4 `csv` files:
        - caracteristiques
        - lieux
        - usagers
        - vehicules

    Args:
        file_paths: List of file names.

    Raises:
        FileNotFoundError:
            If there are no 4 road accident `csv` files.
    """
    expected_files = set(RawRoadAccidentCsvFileNames)
    for exp_file in expected_files:
        if any(exp_file in f.name for f in file_paths):
            continue
        raise FileNotFoundError(f"Error: could not find file '{exp_file}' in files: {file_paths}")
    return True


def get_road_accident_file2model(
    path_raw_data_dir: Path, file_pfix: str = "csv"
) -> Optional[Dict[RawRoadAccidentCsvFileNames, RawRoadAccidentsCsvFile]]:
    """Returns a dictonary where the key is a specific road accident file.


    Args:
        path_raw_data_dir: Path to a directory that should contain
            `csv` files of road accidents.
        file_pfix: Postfix of road accident fies to search
            for in the `path_raw_data_dir` directory. Defaults to "csv".

    Returns:
        - A dictonary where the key is a specific road accident file and the
            values are a DB table SQLModel.
        - `None` if the `path_raw_data_dir` directory has not files ending 
            in `file_pfix`.
    """
    files = list(path_raw_data_dir.glob(f"*.{file_pfix}"))
    if not files:
        return None
    validate_road_accident_files_are_the_expected_ones(files)

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
            file_stats[raw_accident_csv_file] = RawRoadAccidentsCsvFile(
                raw_accident_file=raw_accident_csv_file,
                file_name=file.name,
                dir_name=file.parent.name,
                path=f"{file}",
                md5=hashlib.md5(open(file, "rb").read()).hexdigest(),
                sha256=hashlib.sha256(open(file, "rb").read()).hexdigest(),
            )

    return file_stats


def get_dataframe(path: Path) -> pd.DataFrame:
    # --Importing dataset
    df = pd.read_csv(path, sep=";", encoding="utf-8").replace({np.nan: None})
    df = df.rename(columns={"Accident_Id": "Num_Acc"}) # the 2022 caracteristiques has `Accident_Id` instead of `Num_Acc`
    return df
