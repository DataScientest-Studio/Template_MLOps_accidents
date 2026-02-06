# -*- coding: utf-8 -*-
import logging
import os
from pathlib import Path

import click
import numpy as np
import pandas as pd
import pandera as pa

try:
    from .check_structure import check_existing_file, check_existing_folder
    from .data_schemas import CharactSchema, PlaceSchema, UserSchema, VehicleSchema
except ImportError:
    from check_structure import (  # type: ignore[import-not-found,no-redef]
        check_existing_file,
        check_existing_folder,
    )
    from data_schemas import CharactSchema, PlaceSchema, UserSchema, VehicleSchema

# Note: train_test_split moved to model training pipeline
# Interim dataset is saved instead of train/test split

# File name patterns used to discover raw CSVs (any file whose name contains
# the pattern is considered; first match when sorted is used).
RAW_FILE_PATTERNS = {
    "usagers": "usagers",
    "caracteristiques": "caracteristiques",
    "lieux": "lieux",
    "vehicules": "vehicules",
}


def discover_raw_file_paths(raw_dir: str):
    """
    Discover raw CSV file paths by pattern in a directory.

    Looks for one CSV per category (usagers, caracteristiques, lieux, vehicules).
    Any file whose name contains the pattern is accepted (e.g. usagers-2021.csv,
    usagers-2022.csv). If multiple files match, the first when sorted is used.

    Args:
        raw_dir: Directory containing raw CSV files.

    Returns:
        Tuple (users_path, caract_path, places_path, veh_path).

    Raises:
        FileNotFoundError: If the directory does not exist or a category has
            no matching CSV file.
    """
    if not os.path.isdir(raw_dir):
        raise FileNotFoundError(f"Raw data directory does not exist: {raw_dir}")

    try:
        entries = os.listdir(raw_dir)
    except OSError as e:
        raise FileNotFoundError(f"Cannot list raw data directory {raw_dir}: {e}") from e

    csv_files = [
        f
        for f in entries
        if os.path.isfile(os.path.join(raw_dir, f)) and f.lower().endswith(".csv")
    ]
    paths = {}

    for key, pattern in RAW_FILE_PATTERNS.items():
        matches = sorted(f for f in csv_files if pattern in f.lower())
        if not matches:
            available = ", ".join(csv_files) if csv_files else "(none)"
            raise FileNotFoundError(
                f"No CSV file matching '{pattern}' found in {raw_dir}. "
                f"Available files: {available}"
            )
        paths[key] = os.path.join(raw_dir, matches[0])

    return (
        paths["usagers"],
        paths["caracteristiques"],
        paths["lieux"],
        paths["vehicules"],
    )


@click.command()
@click.argument(
    "input_filepath", type=click.Path(exists=False), required=0, default="data/raw"
)
@click.argument(
    "output_filepath",
    type=click.Path(exists=False),
    required=0,
    default="data/preprocessed",
)
def main(input_filepath, output_filepath):
    """Runs data processing scripts to turn raw data from (../raw) into
    cleaned data ready to be analyzed (saved in ../preprocessed).
    """
    logger = logging.getLogger(__name__)
    logger.info("making final data set from raw data")

    # Use defaults if not provided
    if not input_filepath:
        input_filepath = click.prompt(
            "Enter the directory path for the input raw data",
            type=click.Path(exists=False),
            default="data/raw",
        )
    else:
        logger.info(f"Using input path: {input_filepath}")

    # Ensure input directory exists
    if not os.path.exists(input_filepath):
        logger.error(f"Input directory does not exist: {input_filepath}")
        logger.info("Please run 'make run-import' first to download raw data")
        raise click.Abort()

    (
        input_filepath_users,
        input_filepath_caract,
        input_filepath_places,
        input_filepath_veh,
    ) = discover_raw_file_paths(input_filepath)
    logger.info(
        "Discovered raw files: usagers=%s, caract=%s, lieux=%s, vehicules=%s",
        input_filepath_users,
        input_filepath_caract,
        input_filepath_places,
        input_filepath_veh,
    )

    if not output_filepath:
        output_filepath = click.prompt(
            "Enter the file path for the output preprocessed data",
            type=click.Path(),
            default="data/preprocessed",
        )
    else:
        logger.info(f"Using output path: {output_filepath}")

    # Call the main data processing function with the provided file paths
    process_data(
        input_filepath_users,
        input_filepath_caract,
        input_filepath_places,
        input_filepath_veh,
        output_filepath,
    )


def validate_df(df_model, df):
    logger = logging.getLogger(__name__)
    schema = df_model.to_schema()
    try:
        val_df = schema(df, lazy=True)
        logger.info(f"{schema.name} validation passed")
        return val_df
    except pa.errors.SchemaErrors as err:
        logger.error(f"{schema.name} validation failed")
        logger.error(f"\n{err.failure_cases}")
        return None


def process_data(
    input_filepath_users,
    input_filepath_caract,
    input_filepath_places,
    input_filepath_veh,
    output_folderpath,
):
    logger = logging.getLogger(__name__)
    logger.info("Processing raw data to create interim dataset")

    # --Importing dataset
    df_users = pd.read_csv(input_filepath_users, sep=";")
    df_caract = pd.read_csv(input_filepath_caract, sep=";", header=0, low_memory=False)
    df_places = pd.read_csv(input_filepath_places, sep=";", encoding="utf-8")
    df_veh = pd.read_csv(input_filepath_veh, sep=";")

    # --Validating datasets
    logger.info("Validating raw datasets against their schemas:")

    df_users = validate_df(UserSchema, df_users)
    df_caract = validate_df(CharactSchema, df_caract)
    df_places = validate_df(PlaceSchema, df_places)
    df_veh = validate_df(VehicleSchema, df_veh)

    if any(df is None for df in (df_users, df_caract, df_places, df_veh)):
        raise ValueError("Validation failed for at least one data schema")
    else:
        logger.info("All schema validations passed")

    # --Creating new columns
    nb_victim = pd.crosstab(df_users.Num_Acc, "count").reset_index()
    nb_vehicules = pd.crosstab(df_veh.Num_Acc, "count").reset_index()

    # --Users dataset preprocessing
    # Changing grav values (needed for merging to keep most severe injury)
    df_users["grav"] = df_users["grav"].replace([1, 2, 3, 4], [1, 3, 4, 2])

    # Removing secu2 and secu3
    df_users.drop(["secu2", "secu3"], inplace=True, axis=1)

    # Note: victim_age will be created in build_features.py

    # --Caracteristics dataset preprocessing
    # Rename agg to agg_
    df_caract.rename({"agg": "agg_"}, inplace=True, axis=1)
    # Replace Corsica codes
    df_caract["dep"] = df_caract["dep"].str.replace("2A", "201")
    df_caract["dep"] = df_caract["dep"].str.replace("2B", "202")
    df_caract["com"] = df_caract["com"].str.replace("2A", "201")
    df_caract["com"] = df_caract["com"].str.replace("2B", "202")

    # Converting columns types
    # Note: hour, month, datetime will be created in build_features.py
    # Keep hrmn, jour, mois, an for feature engineering
    df_caract[["dep", "com"]] = df_caract[["dep", "com"]].astype(int)

    # Converting lat and long to float
    df_caract["lat"] = df_caract["lat"].str.replace(",", ".")
    df_caract["long"] = df_caract["long"].str.replace(",", ".")
    dico_to_float = {"lat": float, "long": float}
    df_caract = df_caract.astype(dico_to_float)

    # Removing adr column
    df_caract = df_caract.drop(columns="adr")

    # Note: atm grouping will be done in build_features.py

    # --Vehicles dataset preprocessing
    # Note: catv grouping will be done in build_features.py

    # --Merging datasets
    fusion1 = df_users.merge(
        df_veh, on=["Num_Acc", "num_veh", "id_vehicule"], how="inner"
    )
    fusion1 = fusion1.sort_values(by="grav", ascending=False)
    fusion1 = fusion1.drop_duplicates(subset=["Num_Acc"], keep="first")
    fusion2 = fusion1.merge(df_places, on="Num_Acc", how="left")
    df = fusion2.merge(df_caract, on="Num_Acc", how="left")

    # --Adding new columns
    df = df.merge(nb_victim, on="Num_Acc", how="inner")
    df.rename({"count": "nb_victim"}, axis=1, inplace=True)
    df = df.merge(nb_vehicules, on="Num_Acc", how="inner")
    df.rename({"count": "nb_vehicules"}, axis=1, inplace=True)

    # --Creating year_acc from Num_Acc (needed for victim_age calculation in build_features.py)
    # Extract year from accident number (first 4 digits)
    df["year_acc"] = (
        df["Num_Acc"].astype(str).apply(lambda x: int(x[:4]) if len(x) >= 4 else np.nan)
    )

    # --Modification of the target variable: 1 : prioritary // 0 : non-prioritary
    df["grav"] = df["grav"].replace([2, 3, 4], [0, 1, 1])

    # --Removing variables with more than 70% missing values
    missing_values_count = df.isnull().sum()
    total_cells = len(df)
    missing_percentage = (missing_values_count / total_cells) * 100
    missing_df = pd.DataFrame(
        {
            "Column": missing_percentage.index,
            "MissingPercentage": missing_percentage.values,
        }
    )
    missing_df = missing_df.sort_values(by="MissingPercentage", ascending=False)
    list_to_drop_missing = missing_df[missing_df["MissingPercentage"] >= 70][
        "Column"
    ].tolist()
    df.drop(list_to_drop_missing, inplace=True, axis=1)

    # --Replacing values -1 and 0 with NaN
    col_to_replace0_na = ["actp", "trajet", "catv", "motor"]
    col_to_replace1_na = [
        "actp",
        "trajet",
        "secu1",
        "catv",
        "obsm",
        "motor",
        "circ",
        "larrout",
        "surf",
        "situ",
        "vma",
        "atm",
        "col",
    ]
    df[col_to_replace1_na] = df[col_to_replace1_na].replace(-1, np.nan)
    df[col_to_replace0_na] = df[col_to_replace0_na].replace(0, np.nan)

    # Note: actp conversion will be done in build_features.py

    # --Converting larrout to float
    df["larrout"] = df["larrout"].str.replace(",", ".")
    df["larrout"] = df["larrout"].astype(float)

    # --Dropping columns
    # Note: Keep jour, mois, an, hrmn for temporal feature engineering in build_features.py
    # Note: Keep year_acc and an_nais for victim_age calculation in build_features.py
    list_to_drop = [
        "senc",
        "manv",
        "choc",
        "nbv",
        "Num_Acc",
        "id_vehicule",
        "num_veh",
        "pr",
        "pr1",
        "voie",
        "trajet",
    ]
    df.drop(list_to_drop, axis=1, inplace=True)

    # --Filling NaN values with mode
    col_to_fill_na = ["surf", "situ", "circ", "col", "motor"]
    df[col_to_fill_na] = df[col_to_fill_na].fillna(df[col_to_fill_na].mode().iloc[0])

    # --Dropping all remaining NaN rows
    df = df.dropna(axis=0)

    # Create folder if necessary
    if check_existing_folder(output_folderpath):
        os.makedirs(output_folderpath)

    # --Saving interim dataset (before feature engineering)
    # This dataset will be used by build_features.py for feature engineering
    interim_filepath = os.path.join(output_folderpath, "interim_dataset.csv")
    if check_existing_file(interim_filepath):
        logger.info(f"Saving interim dataset to {interim_filepath}")
        df.to_csv(interim_filepath, index=False)
        logger.info(f"Interim dataset saved. Shape: {df.shape}")
        logger.info(
            "Next step: Run build_features.py on this interim dataset to create "
            "feature-engineered dataset for XGBoost training."
        )


if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    main()
