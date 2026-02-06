# -*- coding: utf-8 -*-
"""
MLflow utilities for model training and logging.

This module provides reusable functions for MLflow integration that work
with the multi-model training framework.
"""

import logging
import os
import warnings
from typing import Dict, Optional

import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend
import matplotlib.pyplot as plt
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import auc, confusion_matrix, roc_curve

# Suppress FutureWarnings for deprecated MLflow methods
warnings.filterwarnings("ignore", category=FutureWarning, module="mlflow")

logger = logging.getLogger(__name__)


def setup_mlflow(config: Dict) -> bool:
    """
    Setup MLflow tracking with Dagshub.

    Parameters
    ----------
    config : dict
        Configuration dictionary

    Returns
    -------
    bool
        True if MLflow is enabled and configured, False otherwise
    """
    mlflow_config = config.get("mlflow", {})

    if not mlflow_config.get("enabled", False):
        logger.info("MLflow tracking is disabled in config")
        return False

    # Get tracking URI from config or environment
    tracking_uri = mlflow_config.get("tracking_uri") or os.getenv("MLFLOW_TRACKING_URI")

    # If not set, construct from DAGSHUB_REPO
    if not tracking_uri:
        dagshub_repo = os.getenv("DAGSHUB_REPO")
        if dagshub_repo:
            tracking_uri = f"https://dagshub.com/{dagshub_repo}.mlflow"
        else:
            logger.warning(
                "MLflow tracking URI not configured. "
                "Set MLFLOW_TRACKING_URI or DAGSHUB_REPO environment variable."
            )
            return False

    # Set tracking URI
    mlflow.set_tracking_uri(tracking_uri)

    # Set experiment name
    experiment_name = mlflow_config.get("experiment_name", "accident_prediction")
    mlflow.set_experiment(experiment_name)

    logger.info(f"MLflow tracking enabled: {tracking_uri}")
    logger.info(f"MLflow experiment: {experiment_name}")

    return True


def log_visualizations_to_mlflow(
    model, X_test: pd.DataFrame, y_test, y_pred, model_type: str
):
    """
    Log visualizations (confusion matrix, ROC curve, feature importance) to MLflow.

    Parameters
    ----------
    model : sklearn estimator
        Trained model
    X_test : pd.DataFrame
        Test features
    y_test : array-like
        True labels
    y_pred : array-like
        Predicted labels
    model_type : str
        Type of model (for feature importance extraction)
    """
    try:
        logger.info("Logging visualizations to MLflow...")

        # Confusion Matrix
        cm = confusion_matrix(y_test, y_pred)

        plt.figure(figsize=(8, 6))
        sns.heatmap(
            cm,
            annot=True,
            fmt="d",
            cmap="Blues",
            xticklabels=["Non-Priority", "Priority"],
            yticklabels=["Non-Priority", "Priority"],
            cbar_kws={"label": "Count"},
        )
        plt.title("Confusion Matrix")
        plt.ylabel("Actual")
        plt.xlabel("Predicted")

        cm_path = "confusion_matrix.png"
        plt.savefig(cm_path, dpi=150, bbox_inches="tight")
        plt.close()
        mlflow.log_artifact(cm_path, "plots")
        os.remove(cm_path)
        logger.info("Logged confusion matrix to MLflow")

        # ROC Curve (if model supports predict_proba)
        if hasattr(model, "predict_proba"):
            try:
                y_pred_proba = model.predict_proba(X_test)[:, 1]
                fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
                roc_auc = auc(fpr, tpr)

                plt.figure(figsize=(8, 6))
                plt.plot(
                    fpr,
                    tpr,
                    color="darkorange",
                    lw=2,
                    label=f"ROC curve (AUC = {roc_auc:.2f})",
                )
                plt.plot(
                    [0, 1], [0, 1], color="navy", lw=2, linestyle="--", label="Random"
                )
                plt.xlim([0.0, 1.0])
                plt.ylim([0.0, 1.05])
                plt.xlabel("False Positive Rate")
                plt.ylabel("True Positive Rate")
                plt.title("ROC Curve")
                plt.legend(loc="lower right")

                roc_path = "roc_curve.png"
                plt.savefig(roc_path, dpi=150, bbox_inches="tight")
                plt.close()
                mlflow.log_artifact(roc_path, "plots")
                os.remove(roc_path)
                mlflow.log_metric("roc_auc", roc_auc)
                logger.info("Logged ROC curve to MLflow")
            except Exception as e:
                logger.warning(f"Could not generate ROC curve: {e}")

        # Feature Importance (for tree-based models)
        try:
            estimator = model
            if hasattr(model, "steps") and len(model.steps) > 0:
                # Find estimator step in pipeline
                for step_name, step_model in model.steps:
                    if hasattr(step_model, "feature_importances_"):
                        estimator = step_model
                        break

            if hasattr(estimator, "feature_importances_"):
                feature_importance = estimator.feature_importances_
                feature_names = X_test.columns.tolist()

                # Get top 20 features
                top_n = min(20, len(feature_names))
                top_indices = np.argsort(feature_importance)[-top_n:]

                plt.figure(figsize=(10, 8))
                plt.barh(range(len(top_indices)), feature_importance[top_indices])
                plt.yticks(
                    range(len(top_indices)), [feature_names[i] for i in top_indices]
                )
                plt.xlabel("Importance")
                plt.title(f"Top {top_n} Feature Importance")
                plt.tight_layout()

                importance_path = "feature_importance.png"
                plt.savefig(importance_path, dpi=150, bbox_inches="tight")
                plt.close()
                mlflow.log_artifact(importance_path, "plots")
                os.remove(importance_path)
                logger.info("Logged feature importance to MLflow")
        except Exception as e:
            logger.warning(f"Could not generate feature importance plot: {e}")

        logger.info("Visualization logging completed!")

    except Exception as e:
        logger.warning(f"Failed to log visualizations to MLflow: {e}")


def log_model_to_mlflow(
    config: Dict,
    trainer,
    model,
    metrics: Dict,
    params: Dict,
    best_cv_score: Optional[float],
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    use_grid_search: bool = False,
):
    """
    Log experiment to MLflow with model-specific tags.

    Assumes MLflow run is already started (run should be started before training).

    Parameters
    ----------
    config : dict
        Configuration dictionary
    trainer : BaseTrainer
        Trainer instance (for getting tags and model name)
    model : sklearn estimator
        Trained model
    metrics : dict
        Evaluation metrics
    params : dict
        Model parameters
    best_cv_score : float, optional
        Best cross-validation score (if grid search was used)
    X_train, y_train : training data
    X_test, y_test : test data
    use_grid_search : bool
        Whether grid search was used
    """
    mlflow_config = config.get("mlflow", {})

    if not mlflow_config.get("enabled", False):
        return

    try:
        # Check that a run is active
        if not mlflow.active_run():
            logger.warning("No active MLflow run found. Skipping logging.")
            return

        logger.info("Logging experiment to MLflow...")

        # Log parameters
        logger.info("Logging parameters to MLflow...")

        for param_name, param_value in params.items():
            mlflow.log_param(param_name, param_value)

        # Log data split parameters
        data_split = config.get("data_split", {})
        mlflow.log_param("test_size", data_split.get("test_size", 0.3))
        mlflow.log_param("random_state", data_split.get("random_state", 42))

        # Log feature engineering flags
        feature_config = config.get("feature_engineering", {})
        mlflow.log_param(
            "apply_cyclic_encoding", feature_config.get("apply_cyclic_encoding", True)
        )
        mlflow.log_param(
            "apply_interactions", feature_config.get("apply_interactions", True)
        )

        # Log SMOTE configuration
        smote_config = config.get("smote", {})
        mlflow.log_param("smote_enabled", smote_config.get("enabled", True))

        # Log grid search info
        mlflow.log_param("used_grid_search", use_grid_search)
        if use_grid_search:
            grid_config = config.get("grid_search", {})
            mlflow.log_param("grid_search_cv", grid_config.get("cv", 5))
            mlflow.log_param("grid_search_scoring", grid_config.get("scoring", "f1"))
            mlflow.log_param("grid_search_n_jobs", grid_config.get("n_jobs", -1))

            if best_cv_score is not None:
                mlflow.log_metric("best_cv_f1_score", best_cv_score)
                mlflow.set_tag("best_cv_score", f"{best_cv_score:.4f}")

        # Log metrics
        logger.info("Logging metrics to MLflow...")
        mlflow.log_metric("accuracy", metrics["accuracy"])
        mlflow.log_metric("precision", metrics["precision"])
        mlflow.log_metric("recall", metrics["recall"])
        mlflow.log_metric("f1_score", metrics["f1_score"])

        # Log dataset info
        mlflow.log_param("train_samples", len(X_train))
        mlflow.log_param("test_samples", len(X_test))
        mlflow.log_param("n_features", X_train.shape[1])
        mlflow.log_param("n_classes", len(y_train.unique()))

        # Log model to registry
        if mlflow_config.get("log_model", True):
            logger.info("Logging model to MLflow...")
            registered_model_name = trainer.get_registered_model_name()

            mlflow.sklearn.log_model(
                model, name="model", registered_model_name=registered_model_name
            )

            # Get the version that was just created
            try:
                from mlflow.tracking import MlflowClient

                client = MlflowClient()

                # Use search_model_versions instead of deprecated get_latest_versions
                # Get the latest version by searching for the model name and sorting by version
                model_versions = client.search_model_versions(
                    f"name='{registered_model_name}'",
                    max_results=1,
                    order_by=["version_number DESC"],
                )

                if model_versions:
                    model_version_num = model_versions[0].version
                    logger.info(
                        f"Model registered as '{registered_model_name}' version {model_version_num}"
                    )

                    # Enhanced registry features
                    registry_config = mlflow_config.get("model_registry", {})

                    # Auto-assign staging alias if configured (replaces deprecated stage transition)
                    if registry_config.get("auto_transition_to_staging", False):
                        try:
                            # Use aliases instead of deprecated stage transitions
                            client.set_registered_model_alias(
                                name=registered_model_name,
                                alias="staging",
                                version=model_version_num,
                            )
                            logger.info(
                                f"Model version {model_version_num} automatically assigned 'staging' alias"
                            )
                        except Exception as e:
                            logger.warning(f"Failed to assign staging alias: {e}")

                    # Automated comparison if enabled
                    if registry_config.get("auto_comparison", {}).get("enabled", False):
                        try:
                            from src.models.model_registry_enhanced import (
                                EnhancedModelRegistry,
                            )

                            enhanced_registry = EnhancedModelRegistry(config)

                            # Get include_stages from config
                            auto_comparison_config = registry_config.get(
                                "auto_comparison", {}
                            )
                            include_stages = auto_comparison_config.get(
                                "include_stages"
                            )

                            # Compare with previous versions (filtered by stages if configured)
                            comparison_result = (
                                enhanced_registry.compare_models_across_versions(
                                    model_name=registered_model_name,
                                    include_stages=include_stages,
                                    output_format="html",
                                )
                            )

                            if comparison_result:
                                # Log comparison to MLflow (use current run)
                                current_run_id = (
                                    mlflow.active_run().info.run_id
                                    if mlflow.active_run()
                                    else None
                                )
                                enhanced_registry.log_comparison_to_mlflow(
                                    model_name=registered_model_name,
                                    comparison_result=comparison_result,
                                    run_id=current_run_id,
                                )
                                logger.info(
                                    "Automated model comparison completed and logged"
                                )
                        except Exception as e:
                            logger.warning(f"Automated comparison failed: {e}")

                    # Auto-promotion if enabled
                    if registry_config.get("auto_promotion", {}).get("enabled", False):
                        try:
                            from src.models.model_registry_enhanced import (
                                EnhancedModelRegistry,
                            )

                            enhanced_registry = EnhancedModelRegistry(config)

                            # Evaluate and potentially promote
                            promotion_result = enhanced_registry.auto_promote_model(
                                model_name=registered_model_name,
                                candidate_version=int(model_version_num),
                                target_stage=registry_config.get(
                                    "auto_promotion", {}
                                ).get("target_stage", "Production"),
                            )

                            if promotion_result.get("promoted"):
                                logger.info(
                                    f"Model automatically promoted: {promotion_result.get('reason')}"
                                )
                            else:
                                logger.info(
                                    f"Auto-promotion skipped: {promotion_result.get('reason')}"
                                )
                        except Exception as e:
                            logger.warning(f"Auto-promotion failed: {e}")

            except Exception as e:
                logger.warning(f"Could not retrieve model version: {e}")

        # Log artifacts
        if mlflow_config.get("log_artifacts", True):
            logger.info("Logging artifacts to MLflow...")
            metrics_dir = config.get("paths", {}).get("metrics_dir", "data/metrics")
            if os.path.exists(metrics_dir):
                mlflow.log_artifacts(metrics_dir, "metrics")

            # Log model metadata as artifact
            logger.info("Logging model metadata to MLflow...")
            try:
                import joblib

                # Create metadata dictionary
                feature_names = list(X_train.columns)

                # Try to extract from model if it's a pipeline
                if hasattr(model, "steps") and len(model.steps) > 0:
                    estimator = model.steps[-1][1]
                    if (
                        hasattr(estimator, "feature_names_in_")
                        and estimator.feature_names_in_ is not None
                    ):
                        feature_names = list(estimator.feature_names_in_)

                metadata = {
                    "feature_names": feature_names,
                    "apply_cyclic_encoding": trainer.apply_cyclic_encoding,
                    "apply_interactions": trainer.apply_interactions,
                    "model_type": trainer.model_type,
                }

                # Save metadata temporarily and log as artifact
                metadata_path = "model_metadata.joblib"
                joblib.dump(metadata, metadata_path)
                mlflow.log_artifact(metadata_path, "artifacts")
                os.remove(metadata_path)
                logger.info("Model metadata logged to MLflow")
            except Exception as e:
                logger.warning(f"Failed to log model metadata: {e}")

            # Log label encoders as artifact
            logger.info("Logging label encoders to MLflow...")
            try:
                import joblib

                paths_config = config.get("paths", {})
                label_encoders_path = paths_config.get(
                    "label_encoders", "models/label_encoders.joblib"
                )

                if os.path.exists(label_encoders_path):
                    mlflow.log_artifact(label_encoders_path, "artifacts")
                    logger.info("Label encoders logged to MLflow")
                else:
                    logger.warning(
                        f"Label encoders file not found at {label_encoders_path}"
                    )
            except Exception as e:
                logger.warning(f"Failed to log label encoders: {e}")

        # Log visualizations
        if mlflow_config.get("log_artifacts", True) and "y_pred" in metrics:
            y_pred = np.array(metrics["y_pred"])
            log_visualizations_to_mlflow(
                model, X_test, y_test, y_pred, trainer.model_type
            )

        logger.info("MLflow logging completed successfully!")

    except Exception as e:
        logger.warning(f"Failed to log to MLflow: {e}")
        logger.warning("Continuing without MLflow logging...")
