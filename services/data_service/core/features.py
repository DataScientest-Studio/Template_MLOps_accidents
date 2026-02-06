"""
Feature engineering helpers for the data service.

Wraps the build_features module so it can be triggered from FastAPI.
"""

import logging
import os
from typing import Dict

import joblib
import pandas as pd

from src.features.build_features import build_features

logger = logging.getLogger(__name__)


def build_feature_dataset(
    interim_path: str,
    preprocessed_dir: str,
    models_dir: str,
    apply_cyclic_encoding: bool = True,
    apply_interactions: bool = True,
) -> Dict[str, str]:
    """
    Run feature engineering and persist artifacts.

    Args:
        interim_path: Path to the interim dataset CSV.
        preprocessed_dir: Directory where engineered features will be saved.
        models_dir: Directory where label encoders will be saved.
        apply_cyclic_encoding: Whether to add cyclic temporal encodings.
        apply_interactions: Whether to add interaction features.

    Returns:
        Dictionary with paths to generated artifacts.
    """
    if not os.path.exists(interim_path):
        raise FileNotFoundError(f"Interim dataset not found: {interim_path}")

    os.makedirs(preprocessed_dir, exist_ok=True)
    os.makedirs(models_dir, exist_ok=True)

    logger.info("Loading interim dataset from %s", interim_path)
    df_interim = pd.read_csv(interim_path)

    df_features, label_encoders = build_features(
        df_interim,
        apply_cyclic_encoding=apply_cyclic_encoding,
        apply_interactions=apply_interactions,
    )

    features_path = os.path.join(preprocessed_dir, "features.csv")
    logger.info("Saving engineered features to %s", features_path)
    df_features.to_csv(features_path, index=False)

    encoders_path = os.path.join(models_dir, "label_encoders.joblib")
    logger.info("Saving label encoders to %s", encoders_path)
    joblib.dump(label_encoders, encoders_path)

    return {
        "features_path": features_path,
        "label_encoders_path": encoders_path,
    }
