"""
Data preprocessing helpers for the data service.

Wraps the existing CLI-oriented data pipeline functions into callable
helpers that can be triggered by the FastAPI service.
"""

import logging
import os
from typing import Dict

from src.data.make_dataset import discover_raw_file_paths, process_data

logger = logging.getLogger(__name__)


def preprocess_data(raw_dir: str, preprocessed_dir: str) -> Dict[str, str]:
    """
    Run the preprocessing pipeline and return output metadata.

    Args:
        raw_dir: Directory containing the raw CSV files.
        preprocessed_dir: Directory where interim data will be written.

    Returns:
        Dictionary containing the path of the generated interim dataset.
    """
    os.makedirs(preprocessed_dir, exist_ok=True)

    input_users, input_caract, input_places, input_veh = discover_raw_file_paths(
        raw_dir
    )

    logger.info(
        "Running preprocessing with inputs: %s, %s, %s, %s",
        input_users,
        input_caract,
        input_places,
        input_veh,
    )

    process_data(
        input_filepath_users=input_users,
        input_filepath_caract=input_caract,
        input_filepath_places=input_places,
        input_filepath_veh=input_veh,
        output_folderpath=preprocessed_dir,
    )

    interim_path = os.path.join(preprocessed_dir, "interim_dataset.csv")
    return {"interim_dataset": interim_path}
