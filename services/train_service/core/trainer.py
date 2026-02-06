"""
Training helpers for the train service.
"""

import logging
from typing import Dict, List, Optional

import yaml

from src.models.mlflow_utils import setup_mlflow
from src.models.train_multi_model import (
    compare_models,
    create_trainer,
    get_available_models,
    train_single_model,
)

logger = logging.getLogger(__name__)


def run_training(
    model_types: Optional[List[str]] = None,
    grid_search: Optional[bool] = None,
    compare: bool = True,
    config_path: str = "src/config/model_config.yaml",
    config_dict: Optional[Dict] = None,
) -> Dict:
    """
    Run the multi-model training workflow programmatically.

    Args:
        model_types: Optional list of model identifiers to train. Defaults to enabled models in config.
        grid_search: Enable hyperparameter search. Defaults to config value.
        compare: Generate comparison report and pick best model.
        config_path: Path to the training configuration YAML (ignored when config_dict is provided).
        config_dict: Optional inline config for this run only; when set, config_path is not read.

    Returns:
        Dictionary containing training results and optional comparison metadata.
    """
    if config_dict is None:
        with open(config_path, "r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f)

    # Determine model list
    if model_types:
        selected_models = [m.lower() for m in model_types]
    else:
        multi_model_config = config_dict.get("multi_model", {})
        selected_models = multi_model_config.get(
            "enabled_models", get_available_models()
        )

    # Determine grid search flag
    if grid_search is None:
        grid_search_config = config_dict.get("grid_search", {})
        grid_search = grid_search_config.get("enabled", False)

    logger.info("Training models: %s", ", ".join(selected_models))
    logger.info("Grid search: %s", "enabled" if grid_search else "disabled")

    # Setup MLflow once
    mlflow_enabled = setup_mlflow(config_dict)
    logger.info("MLflow: %s", "enabled" if mlflow_enabled else "disabled")

    # Load and split data once for all models
    logger.info(
        "Loading and splitting data (shared across %d model(s))...",
        len(selected_models),
    )
    base_trainer = create_trainer(selected_models[0], config_dict)
    X, y = base_trainer.load_data()
    X_train, X_test, y_train, y_test = base_trainer.split_data(X, y)

    results: List[Dict] = []
    for i, model_type in enumerate(selected_models):
        logger.info("Training model %d/%d: %s", i + 1, len(selected_models), model_type)
        result = train_single_model(
            model_type=model_type,
            config=config_dict,
            X_train=X_train,
            y_train=y_train,
            X_test=X_test,
            y_test=y_test,
            use_grid_search=grid_search,
            mlflow_enabled=mlflow_enabled,
        )
        results.append(result)

    logger.info("All models trained.")

    comparison_path = None
    best_model = None
    best_metrics = None

    if compare:
        logger.info("Comparing models and selecting best...")
        comparison_df = compare_models(results)
        if not comparison_df.empty:
            comparison_path = f"{config_dict.get('paths', {}).get('metrics_dir', 'data/metrics')}/model_comparison.csv"
            comparison_df.to_csv(comparison_path, index=False)
            logger.info("Comparison saved to %s", comparison_path)
            best_row = comparison_df.iloc[0]
            best_model = best_row["model_type"]
            best_metrics = best_row.to_dict()
            logger.info("Best model: %s (F1: %.4f)", best_model, best_row["f1_score"])

    return {
        "results": results,
        "comparison_path": comparison_path,
        "best_model": best_model,
        "best_metrics": best_metrics,
    }
