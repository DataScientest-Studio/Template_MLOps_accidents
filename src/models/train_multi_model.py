# -*- coding: utf-8 -*-
"""
Multi-model training orchestrator.

This script trains multiple models and compares their performance.
It uses the base trainer framework and integrates with MLflow for tracking.

Usage:
    # Train all models specified in config
    python src/models/train_multi_model.py

    # Train specific models
    python src/models/train_multi_model.py --models xgboost random_forest

    # Use grid search for all models
    python src/models/train_multi_model.py --grid-search
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional

import click
import mlflow
import pandas as pd
import yaml

from src.models.base_trainer import BaseTrainer
from src.models.mlflow_utils import log_model_to_mlflow, setup_mlflow
from src.models.model_trainers import (
    LightGBMTrainer,
    LogisticRegressionTrainer,
    RandomForestTrainer,
    XGBoostTrainer,
)

logger = logging.getLogger(__name__)

# Model type to trainer class mapping
MODEL_TRAINERS = {
    "xgboost": XGBoostTrainer,
    "random_forest": RandomForestTrainer,
    "logistic_regression": LogisticRegressionTrainer,
    "lightgbm": LightGBMTrainer,
}


def get_available_models() -> List[str]:
    """Get list of available model types."""
    return list(MODEL_TRAINERS.keys())


def create_trainer(model_type: str, config: Dict) -> BaseTrainer:
    """
    Create a trainer instance for the specified model type.

    Parameters
    ----------
    model_type : str
        Type of model (e.g., "xgboost", "random_forest")
    config : dict
        Configuration dictionary

    Returns
    -------
    BaseTrainer
        Trainer instance
    """
    if model_type not in MODEL_TRAINERS:
        available = ", ".join(get_available_models())
        raise ValueError(
            f"Unknown model type: {model_type}. Available models: {available}"
        )

    trainer_class = MODEL_TRAINERS[model_type]
    return trainer_class(config)


def train_single_model(
    model_type: str,
    config: Dict,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    use_grid_search: bool = False,
    mlflow_enabled: bool = False,
) -> Dict:
    """
    Train a single model and return results.

    Parameters
    ----------
    model_type : str
        Type of model to train
    config : dict
        Configuration dictionary
    X_train, y_train : training data
    X_test, y_test : test data
    use_grid_search : bool
        Whether to use grid search
    mlflow_enabled : bool
        Whether MLflow is enabled

    Returns
    -------
    dict
        Dictionary containing model, metrics, and metadata
    """
    logger.info("=" * 60)
    logger.info(f"Training {model_type} model")
    logger.info("=" * 60)

    try:
        # Create trainer
        trainer = create_trainer(model_type, config)

        # Start MLflow run BEFORE training (so duration includes training)
        if mlflow_enabled:
            run_name_prefix = "GridSearch" if use_grid_search else "DefaultParams"
            model_type_capitalized = (
                trainer.model_type.replace("_", " ").title().replace(" ", "_")
            )
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            run_name = f"{model_type_capitalized}_{run_name_prefix}_{timestamp}"

            mlflow.start_run(run_name=run_name)

            # Set tags early
            tags = trainer.get_mlflow_tags()
            for tag_key, tag_value in tags.items():
                mlflow.set_tag(tag_key, tag_value)

            if use_grid_search:
                mlflow.set_tag("training_method", "grid_search")
                mlflow.set_tag("hyperparameter_tuning", "true")
            else:
                mlflow.set_tag("training_method", "default_params")
                mlflow.set_tag("hyperparameter_tuning", "false")

        # Capture overall training start time
        overall_start_time = time.perf_counter()

        # Train model
        model, best_params, best_cv_score, training_times = trainer.train(
            X_train=X_train, y_train=y_train, use_grid_search=use_grid_search
        )

        # Capture overall training end time
        overall_end_time = time.perf_counter()
        overall_training_duration = overall_end_time - overall_start_time

        # Log timing metrics to MLflow
        if mlflow_enabled:
            mlflow.log_metric(
                "overall_training_duration_seconds", overall_training_duration
            )

            # Log best model fit time if available
            if training_times and "best_model_fit_time" in training_times:
                mlflow.log_metric(
                    "best_model_fit_time_seconds", training_times["best_model_fit_time"]
                )

        # Evaluate model
        metrics = trainer.evaluate(model, X_test, y_test)
        logger.info("Test F1 for %s: %.4f", model_type, metrics["f1_score"])

        # Save model
        paths_config = config.get("paths", {})
        model_output_dir = os.path.dirname(
            paths_config.get("model_output", "models/trained_model.joblib")
        )
        model_filename = f"{model_type}_model.joblib"
        model_path = os.path.join(model_output_dir, model_filename)

        trainer.save_model(model, model_path, X_train=X_train)

        # Save metrics with model-specific prefix
        metrics_filename = f"{model_type}_metrics.json"
        metrics_path = os.path.join(trainer.metrics_dir, metrics_filename)
        os.makedirs(trainer.metrics_dir, exist_ok=True)

        # Create DVC-compliant metrics
        dvc_metrics = {
            f"{model_type}_test_accuracy": float(metrics["accuracy"]),
            f"{model_type}_test_precision": float(metrics["precision"]),
            f"{model_type}_test_recall": float(metrics["recall"]),
            f"{model_type}_test_f1_score": float(metrics["f1_score"]),
        }

        if best_cv_score is not None:
            dvc_metrics[f"{model_type}_best_cv_f1_score"] = float(best_cv_score)

        with open(metrics_path, "w") as f:
            json.dump(dvc_metrics, f, indent=2)

        logger.info(f"Metrics saved to {metrics_path}")

        # Log to MLflow (run is already started)
        if mlflow_enabled:
            y_pred = model.predict(X_test)
            metrics["y_pred"] = y_pred.tolist()

            log_model_to_mlflow(
                config=config,
                trainer=trainer,
                model=model,
                metrics=metrics,
                params=best_params,
                best_cv_score=best_cv_score,
                X_train=X_train,
                y_train=y_train,
                X_test=X_test,
                y_test=y_test,
                use_grid_search=use_grid_search,
            )

            # End the MLflow run
            mlflow.end_run()

        logger.info(f"✓ {model_type} model training completed")

        return {
            "model_type": model_type,
            "model": model,
            "metrics": metrics,
            "best_params": best_params,
            "best_cv_score": best_cv_score,
            "model_path": model_path,
            "metrics_path": metrics_path,
        }

    except Exception as e:
        # Make sure to end MLflow run on error
        if mlflow_enabled and mlflow.active_run():
            mlflow.end_run()
        logger.error(f"Failed to train {model_type} model: {e}", exc_info=True)
        return {
            "model_type": model_type,
            "error": str(e),
        }


def compare_models(results: List[Dict]) -> pd.DataFrame:
    """
    Compare results from multiple models.

    Parameters
    ----------
    results : list
        List of result dictionaries from train_single_model

    Returns
    -------
    pd.DataFrame
        Comparison DataFrame with metrics for each model
    """
    comparison_data = []

    for result in results:
        if "error" in result:
            continue

        metrics = result["metrics"]
        comparison_data.append(
            {
                "model_type": result["model_type"],
                "accuracy": metrics["accuracy"],
                "precision": metrics["precision"],
                "recall": metrics["recall"],
                "f1_score": metrics["f1_score"],
                "best_cv_score": result.get("best_cv_score"),
            }
        )

    if not comparison_data:
        logger.warning("No successful model training results to compare")
        return pd.DataFrame()

    df = pd.DataFrame(comparison_data)
    df = df.sort_values("f1_score", ascending=False)

    return df


@click.command()
@click.option(
    "--config",
    type=click.Path(exists=True),
    default="src/config/model_config.yaml",
    help="Path to model configuration YAML file",
)
@click.option(
    "--models",
    multiple=True,
    type=click.Choice(get_available_models(), case_sensitive=False),
    help="Specific models to train (can be used multiple times). If not specified, trains all enabled models.",
)
@click.option(
    "--grid-search/--no-grid-search",
    default=None,
    help="Enable grid search for hyperparameter tuning (overrides config)",
)
@click.option(
    "--compare/--no-compare",
    default=True,
    help="Generate model comparison report",
)
def main(config: str, models: tuple, grid_search: Optional[bool], compare: bool):
    """
    Train multiple models and compare their performance.

    Models are trained using the same train/test split for fair comparison.
    Results are logged to MLflow with model-specific tags for easy filtering.
    """
    logger.info("=" * 60)
    logger.info("Multi-Model Training")
    logger.info("=" * 60)

    # Load configuration
    if not os.path.exists(config):
        raise FileNotFoundError(f"Configuration file not found: {config}")

    with open(config, "r") as f:
        config_dict = yaml.safe_load(f)

    logger.info(f"Configuration loaded from: {config}")

    # Determine which models to train
    if models:
        model_types = [m.lower() for m in models]
    else:
        # Get enabled models from config
        multi_model_config = config_dict.get("multi_model", {})
        enabled_models = multi_model_config.get("enabled_models", ["xgboost"])
        model_types = enabled_models

    logger.info(f"Models to train: {', '.join(model_types)}")

    # Get grid search setting
    if grid_search is None:
        grid_search_config = config_dict.get("grid_search", {})
        grid_search = grid_search_config.get("enabled", False)

    logger.info(f"Grid search: {'Enabled' if grid_search else 'Disabled'}")

    # Setup MLflow
    mlflow_enabled = setup_mlflow(config_dict)

    # Load and split data once (for fair comparison)
    trainer = create_trainer(model_types[0], config_dict)
    X, y = trainer.load_data()
    X_train, X_test, y_train, y_test = trainer.split_data(X, y)

    # Train all models
    results = []
    for model_type in model_types:
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

    # Compare models
    if compare:
        logger.info("=" * 60)
        logger.info("Model Comparison")
        logger.info("=" * 60)

        comparison_df = compare_models(results)

        if not comparison_df.empty:
            logger.info("\n" + comparison_df.to_string(index=False))

            # Save comparison to file
            comparison_path = os.path.join(
                config_dict.get("paths", {}).get("metrics_dir", "data/metrics"),
                "model_comparison.csv",
            )
            comparison_df.to_csv(comparison_path, index=False)
            logger.info(f"\nComparison saved to {comparison_path}")

            # Find best model
            best_model = comparison_df.iloc[0]
            logger.info(
                f"\nBest model: {best_model['model_type']} (F1: {best_model['f1_score']:.4f})"
            )
        else:
            logger.warning("No models were successfully trained for comparison")

    logger.info("=" * 60)
    logger.info("Multi-model training completed!")
    logger.info("=" * 60)


if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    main()
