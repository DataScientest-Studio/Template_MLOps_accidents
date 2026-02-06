# -*- coding: utf-8 -*-
"""
Feature engineering module optimized for XGBoost model training.

This module transforms interim datasets into feature-engineered datasets
ready for XGBoost model training, including:
- Temporal feature engineering with cyclic encoding
- Categorical feature transformations
- Feature encoding and interactions
"""

import logging
import os
from typing import Dict, Optional

import click
import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder

logger = logging.getLogger(__name__)


def create_temporal_features(df, apply_cyclic_encoding=True):
    """
    Create temporal features optimized for XGBoost with cyclic encoding.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe with datetime or temporal columns (jour, mois, an, hrmn)
    apply_cyclic_encoding : bool
        Whether to apply cyclic encoding for temporal features

    Returns
    -------
    pd.DataFrame
        Dataframe with temporal features added
    """
    df = df.copy()

    # Create datetime if not present (from jour, mois, an, hrmn)
    if "datetime" not in df.columns:
        if all(col in df.columns for col in ["jour", "mois", "an", "hrmn"]):
            df["datetime_str"] = (
                df["jour"].astype(str)
                + "/"
                + df["mois"].astype(str)
                + "/"
                + df["an"].astype(str)
                + " "
                + df["hrmn"]
            )
            df["datetime"] = pd.to_datetime(
                df["datetime_str"], format="%d/%m/%Y %H:%M", errors="coerce"
            )
            df.drop(columns=["datetime_str"], inplace=True, errors="ignore")
        else:
            logger.warning(
                "Cannot create datetime column: missing jour, mois, an, or hrmn columns"
            )
            return df

    if "datetime" not in df.columns:
        logger.warning("datetime column not found and could not be created")
        return df

    # Extract basic temporal features
    df["hour"] = df["datetime"].dt.hour
    df["month"] = df["datetime"].dt.month
    df["day_of_week"] = df["datetime"].dt.dayofweek  # 0=Monday, 6=Sunday
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)

    # Season (1=Spring, 2=Summer, 3=Fall, 4=Winter)
    df["season"] = df["month"].apply(lambda x: (x % 12 + 3) // 3)

    # Cyclic encoding for XGBoost (captures cyclical patterns)
    if apply_cyclic_encoding:
        df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
        df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
        df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
        df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
        df["day_of_week_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
        df["day_of_week_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)

    # Drop datetime column (XGBoost requires numeric only)
    df = df.drop(columns=["datetime"], errors="ignore")

    return df


def create_victim_age_feature(df):
    """
    Create victim_age feature with outlier handling.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe with year_acc and an_nais columns (from interim dataset)

    Returns
    -------
    pd.DataFrame
        Dataframe with victim_age feature added
    """
    df = df.copy()

    # Calculate age if both year_acc and an_nais are present
    if "an_nais" in df.columns and "year_acc" in df.columns:
        df["victim_age"] = df["year_acc"] - df["an_nais"]
        # Handle outliers (same logic as notebook)
        df.loc[(df["victim_age"] > 120) | (df["victim_age"] < 0), "victim_age"] = np.nan

        # Drop intermediate columns
        df = df.drop(columns=["an_nais", "year_acc"], errors="ignore")
    elif "an_nais" not in df.columns:
        logger.warning("an_nais column not found, cannot calculate victim_age")
    elif "year_acc" not in df.columns:
        logger.warning("year_acc column not found, cannot calculate victim_age")

    # Age binning (optional, for categorical representation)
    if "victim_age" in df.columns:
        df["victim_age_binned"] = pd.cut(
            df["victim_age"], bins=[0, 18, 30, 50, 70, 120], labels=[0, 1, 2, 3, 4]
        ).astype(float)

    return df


def transform_atm_feature(df):
    """
    Group atmospheric conditions into Risky/Normal (binary for XGBoost).

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe with atm column

    Returns
    -------
    pd.DataFrame
        Dataframe with transformed atm feature
    """
    df = df.copy()
    if "atm" in df.columns:
        atm_mapping = {1: 0, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 0, 9: 0}
        df["atm"] = df["atm"].replace(atm_mapping)
    return df


def transform_catv_feature(df):
    """
    Group vehicle types into categories (reduces cardinality for XGBoost).

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe with catv column

    Returns
    -------
    pd.DataFrame
        Dataframe with transformed catv feature
    """
    df = df.copy()
    if "catv" in df.columns:
        catv_value = [
            0,
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
            19,
            20,
            21,
            30,
            31,
            32,
            33,
            34,
            35,
            36,
            37,
            38,
            39,
            40,
            41,
            42,
            43,
            50,
            60,
            80,
            99,
        ]
        catv_value_new = [
            0,
            1,
            1,
            2,
            1,
            1,
            6,
            2,
            5,
            5,
            5,
            5,
            5,
            4,
            4,
            4,
            4,
            4,
            3,
            3,
            4,
            4,
            1,
            1,
            1,
            1,
            1,
            6,
            6,
            3,
            3,
            3,
            3,
            1,
            1,
            1,
            1,
            1,
            0,
            0,
        ]
        df["catv"] = df["catv"].replace(catv_value, catv_value_new)
    return df


def convert_actp_feature(df):
    """
    Convert actp from string to int (A→10, B→11).

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe with actp column

    Returns
    -------
    pd.DataFrame
        Dataframe with converted actp feature
    """
    df = df.copy()
    if "actp" in df.columns:
        df["actp"] = (
            df["actp"].astype(str).str.replace("A", "10").str.replace("B", "11")
        )
        df["actp"] = pd.to_numeric(df["actp"], errors="coerce")
    return df


def encode_categorical_features(df, categorical_cols=None, label_encoders=None):
    """
    Label encode categorical features for XGBoost.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe
    categorical_cols : list, optional
        List of categorical column names to encode. If None, auto-detects.
    label_encoders : dict, optional
        Dictionary of pre-fitted label encoders for inference. If None, fits new encoders.

    Returns
    -------
    pd.DataFrame
        Dataframe with encoded categorical features
    dict
        Dictionary of label encoders (fitted or provided)
    """
    df = df.copy()

    if categorical_cols is None:
        # Auto-detect categorical columns (low cardinality, object type or int with <10 unique values)
        categorical_cols = []
        for col in df.columns:
            if df[col].dtype == "object":
                categorical_cols.append(col)
            elif df[col].dtype in ["int64", "int32", "float64"]:
                if df[col].nunique() < 10 and df[col].nunique() > 1:
                    categorical_cols.append(col)

    if label_encoders is None:
        label_encoders = {}

    for col in categorical_cols:
        if col in df.columns:
            if col in label_encoders:
                # Use pre-fitted encoder (for inference)
                le = label_encoders[col]
                # Handle unseen categories by mapping to -1
                df[col] = df[col].astype(str)
                df[col] = df[col].apply(
                    lambda x: le.transform([x])[0] if x in le.classes_ else -1
                )
            else:
                # Fit new encoder (for training)
                le = LabelEncoder()
                df[col] = le.fit_transform(df[col].astype(str))
                label_encoders[col] = le

    return df, label_encoders


def create_interaction_features(df):
    """
    Create interaction features that might help XGBoost.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe

    Returns
    -------
    pd.DataFrame
        Dataframe with interaction features added
    """
    df = df.copy()

    # Ratio features
    if "nb_victim" in df.columns and "nb_vehicules" in df.columns:
        df["victims_per_vehicle"] = df["nb_victim"] / (df["nb_vehicules"] + 1e-6)

    # Interaction features
    if "hour" in df.columns and "is_weekend" in df.columns:
        df["hour_weekend"] = df["hour"] * df["is_weekend"]

    if "atm" in df.columns and "lum" in df.columns:
        df["atm_lum"] = df["atm"] * df["lum"]

    return df


def ensure_numeric_features(df):
    """
    Ensure all features are numeric (XGBoost requirement).

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe

    Returns
    -------
    pd.DataFrame
        Dataframe with only numeric features
    """
    df = df.copy()

    # Convert object columns to numeric where possible
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Final check: drop any remaining non-numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df = df[numeric_cols]

    return df


def prepare_input_for_feature_engineering(
    features: Dict, default_values: Optional[Dict] = None
) -> pd.DataFrame:
    """
    Prepare input features dictionary for feature engineering pipeline.

    Converts user-friendly input format to interim dataset format expected
    by build_features. Handles common input variations (e.g., year_acc vs an,
    hour vs hrmn).

    This function is used for inference when input comes as a dictionary
    instead of a DataFrame. It ensures the input is in the correct format
    for the feature engineering pipeline.

    Parameters
    ----------
    features : dict
        Input features dictionary (can be in simplified or interim format)
    default_values : dict, optional
        Default values for missing columns. If None, uses standard defaults.

    Returns
    -------
    pd.DataFrame
        DataFrame in interim dataset format ready for build_features
    """
    df = pd.DataFrame([features])

    # Standard default values for interim dataset columns
    if default_values is None:
        default_values = {
            "locp": 0,
            "actp": 0,
            "etatp": 0,
            "obs": 0,
            "v1": 0,
            "vosp": 0,
            "prof": 0,
            "plan": 0,
            "larrout": 0.0,
            "infra": 0,
        }

    # Convert year_acc to an if needed (an is used for datetime creation)
    if "year_acc" in df.columns and "an" not in df.columns:
        df["an"] = df["year_acc"]

    # Ensure hrmn is in HH:MM format if hour is provided instead
    if "hour" in df.columns and "hrmn" not in df.columns:
        hour = int(df["hour"].iloc[0])
        df["hrmn"] = f"{hour:02d}:00"

    # Ensure jour, mois, an are present for datetime creation
    if "jour" not in df.columns:
        df["jour"] = 1
    if "mois" not in df.columns:
        df["mois"] = 1
    if "an" not in df.columns and "year_acc" in df.columns:
        df["an"] = df["year_acc"]

    # Calculate an_nais from victim_age if victim_age is provided but an_nais is not
    if "victim_age" in df.columns and "an_nais" not in df.columns:
        if "year_acc" in df.columns:
            df["an_nais"] = df["year_acc"] - df["victim_age"]
        elif "an" in df.columns:
            df["an_nais"] = df["an"] - df["victim_age"]
        else:
            df["an_nais"] = 1900
    elif "an_nais" not in df.columns:
        df["an_nais"] = 1900

    # Remove victim_age if present (it will be recalculated by build_features)
    if "victim_age" in df.columns:
        df = df.drop(columns=["victim_age"])

    # Add missing columns with default values
    for col, default_val in default_values.items():
        if col not in df.columns:
            df[col] = default_val

    return df


def build_features(
    df_interim,
    apply_cyclic_encoding=True,
    apply_interactions=True,
    label_encoders=None,
    model_type=None,
):
    """
    Main function to build all features from interim dataset for XGBoost.

    Parameters
    ----------
    df_interim : pd.DataFrame
        Interim dataset from make_dataset.py
    apply_cyclic_encoding : bool
        Whether to apply cyclic encoding for temporal features
    apply_interactions : bool
        Whether to create interaction features
    label_encoders : dict, optional
        Pre-fitted label encoders for inference. If None, fits new encoders.
    model_type : str, optional
        Model type (e.g., "XGBoost", "LightGBM", "RandomForest") for logging purposes.
        If None, the log message will not mention a specific model type.

    Returns
    -------
    pd.DataFrame
        Dataset with all engineered features (all numeric)
    dict
        Dictionary of label encoders for categorical features
    """
    if model_type:
        logger.info(f"Starting feature engineering for {model_type}")
    else:
        logger.info("Starting feature engineering")
    df = df_interim.copy()

    # Temporal features
    logger.info("Creating temporal features...")
    df = create_temporal_features(df, apply_cyclic_encoding=apply_cyclic_encoding)

    # Victim age feature
    logger.info("Creating victim_age feature...")
    df = create_victim_age_feature(df)

    # Categorical transformations
    logger.info("Transforming categorical features...")
    df = transform_atm_feature(df)
    df = transform_catv_feature(df)
    df = convert_actp_feature(df)

    # Interaction features (optional)
    if apply_interactions:
        logger.info("Creating interaction features...")
        df = create_interaction_features(df)

    # Encode categorical features
    logger.info("Encoding categorical features...")
    df, label_encoders = encode_categorical_features(df, label_encoders=label_encoders)

    # Ensure all features are numeric
    logger.info("Ensuring all features are numeric...")
    df = ensure_numeric_features(df)

    # Final validation: no missing values
    if df.isnull().sum().sum() > 0:
        logger.warning("Found missing values, filling with median...")
        df = df.fillna(df.median())

    logger.info(f"Feature engineering complete. Final shape: {df.shape}")
    return df, label_encoders


@click.command()
@click.argument(
    "input_filepath",
    type=click.Path(exists=True),
    required=0,
    default="data/preprocessed/interim_dataset.csv",
)
@click.argument(
    "output_filepath",
    type=click.Path(exists=False),
    required=0,
    default="data/preprocessed",
)
@click.option(
    "--cyclic-encoding/--no-cyclic-encoding",
    default=True,
    help="Apply cyclic encoding for temporal features",
)
@click.option(
    "--interactions/--no-interactions", default=True, help="Create interaction features"
)
def main(input_filepath, output_filepath, cyclic_encoding, interactions):
    """
    Build features from interim dataset for XGBoost model training.

    Reads interim dataset, applies feature engineering, and saves final features
    along with label encoders for inference.
    """
    logger.info("Building features from interim dataset")

    # Use defaults if not provided
    if not input_filepath:
        input_filepath = click.prompt(
            "Enter the file path for the interim dataset",
            type=click.Path(exists=True),
            default="data/preprocessed/interim_dataset.csv",
        )
    else:
        logger.info(f"Using input path: {input_filepath}")

    # Load interim dataset
    logger.info(f"Loading interim dataset from {input_filepath}")
    df_interim = pd.read_csv(input_filepath)

    # Build features
    df_features, label_encoders = build_features(
        df_interim,
        apply_cyclic_encoding=cyclic_encoding,
        apply_interactions=interactions,
    )

    # Use defaults if not provided
    if not output_filepath:
        output_filepath = click.prompt(
            "Enter the file path for the output features (directory)",
            type=click.Path(),
            default="data/preprocessed",
        )
    else:
        logger.info(f"Using output path: {output_filepath}")

    # Create output directory if needed
    os.makedirs(output_filepath, exist_ok=True)

    # Save features
    features_path = os.path.join(output_filepath, "features.csv")
    logger.info(f"Saving features to {features_path}")
    df_features.to_csv(features_path, index=False)

    # Save label encoders to models directory (project root)
    models_dir = "models"
    os.makedirs(models_dir, exist_ok=True)
    encoders_path = os.path.join(models_dir, "label_encoders.joblib")
    logger.info(f"Saving label encoders to {encoders_path}")
    joblib.dump(label_encoders, encoders_path)

    logger.info("Feature engineering complete!")


if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    main()
