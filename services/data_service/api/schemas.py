"""
Pydantic schemas for the data service API.
"""

from typing import Optional

from pydantic import BaseModel, Field


class PreprocessRequest(BaseModel):
    """Request payload for preprocessing."""

    raw_dir: Optional[str] = Field(
        default=None,
        description="Path to raw data directory containing the 2021 CSV files.",
    )
    preprocessed_dir: Optional[str] = Field(
        default=None,
        description="Directory to write interim dataset.",
    )


class BuildFeaturesRequest(BaseModel):
    """Request payload for feature engineering."""

    interim_path: Optional[str] = Field(
        default=None,
        description="Path to interim_dataset.csv. Defaults to <preprocessed_dir>/interim_dataset.csv",
    )
    preprocessed_dir: Optional[str] = Field(
        default=None,
        description="Directory to write engineered features (features.csv).",
    )
    models_dir: Optional[str] = Field(
        default=None,
        description="Directory to write label encoders.",
    )
    cyclic_encoding: bool = Field(
        default=True,
        description="Apply cyclic encoding to temporal features.",
    )
    interactions: bool = Field(
        default=True,
        description="Create interaction features.",
    )
