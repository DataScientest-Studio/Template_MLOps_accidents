# -*- coding: utf-8 -*-
"""
Base trainer class for all model types.

This module provides a base class that all model trainers should inherit from,
ensuring consistent behavior across different model types.
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple

import joblib
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)


class BaseTrainer(ABC):
    """
    Base class for all model trainers.

    This class provides common functionality for:
    - Data loading and splitting
    - Model evaluation
    - Metrics saving
    - Model and metadata saving
    - MLflow integration (via tags and logging)

    Subclasses should implement:
    - `_build_model()`: Create and configure the model
    - `_get_model_params()`: Extract model parameters for logging
    - `model_type`: Class attribute specifying model type (e.g., "xgboost", "random_forest")
    """

    def __init__(self, config: Dict):
        """
        Initialize the trainer with configuration.

        Parameters
        ----------
        config : dict
            Configuration dictionary from model_config.yaml
        """
        self.config = config
        self.model = None
        self.model_type = self.__class__.model_type

        # Get paths from config
        paths_config = config.get("paths", {})
        self.features_path = paths_config.get(
            "features", "data/preprocessed/features.csv"
        )
        self.metrics_dir = paths_config.get("metrics_dir", "data/metrics")
        self.label_encoders_path = paths_config.get(
            "label_encoders", "models/label_encoders.joblib"
        )
        self.model_metadata_path = paths_config.get(
            "model_metadata", "models/trained_model_metadata.joblib"
        )

        # Ensure metrics directory exists
        os.makedirs(self.metrics_dir, exist_ok=True)

        # Data split config
        data_split_config = config.get("data_split", {})
        self.test_size = data_split_config.get("test_size", 0.3)
        self.random_state = data_split_config.get("random_state", 42)
        self.shuffle = data_split_config.get("shuffle", True)

        # Feature engineering config
        feature_config = config.get("feature_engineering", {})
        self.apply_cyclic_encoding = feature_config.get("apply_cyclic_encoding", True)
        self.apply_interactions = feature_config.get("apply_interactions", True)

    def load_data(self) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Load feature-engineered dataset and separate features from target.

        Returns
        -------
        X : pd.DataFrame
            Feature matrix
        y : pd.Series
            Target variable
        """
        logger.info(f"Loading features from {self.features_path}")

        if not os.path.exists(self.features_path):
            raise FileNotFoundError(
                f"Features file not found: {self.features_path}\n"
                "Please run feature engineering step first."
            )

        df_features = pd.read_csv(
            self.features_path,
            on_bad_lines="warn",
        )

        if "grav" not in df_features.columns:
            raise ValueError("Target column 'grav' not found in features file")

        X = df_features.drop(columns=["grav"])
        y = df_features["grav"]

        logger.info(f"Loaded {len(X)} samples with {len(X.columns)} features")
        return X, y

    def split_data(
        self, X: pd.DataFrame, y: pd.Series
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """
        Split data into training and test sets.

        Parameters
        ----------
        X : pd.DataFrame
            Feature matrix
        y : pd.Series
            Target variable

        Returns
        -------
        X_train, X_test, y_train, y_test : tuple
            Split datasets
        """
        logger.info(
            f"Splitting data (test_size={self.test_size}, random_state={self.random_state})..."
        )

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=self.test_size,
            random_state=self.random_state,
            shuffle=self.shuffle,
        )

        logger.info(f"Training set: {X_train.shape[0]} samples")
        logger.info(f"Test set: {X_test.shape[0]} samples")

        return X_train, X_test, y_train, y_test

    @abstractmethod
    def _build_model(
        self, X_train: pd.DataFrame, y_train: pd.Series, use_grid_search: bool = False
    ):
        """
        Build and train the model.

        Parameters
        ----------
        X_train : pd.DataFrame
            Training features
        y_train : pd.Series
            Training target
        use_grid_search : bool
            Whether to use grid search for hyperparameter tuning

        Returns
        -------
        model : object
            Trained model
        best_params : dict
            Best parameters (from grid search or defaults)
        best_cv_score : float, optional
            Best cross-validation score (if grid search was used)
        training_times : dict, optional
            Dictionary with timing information containing:
            - best_model_fit_time: float, time to fit the best model in seconds
        """
        pass

    @abstractmethod
    def _get_model_params(self, model) -> Dict:
        """
        Extract model parameters for logging.

        Parameters
        ----------
        model : object
            Trained model

        Returns
        -------
        dict
            Dictionary of model parameters
        """
        pass

    def train(
        self,
        X_train: Optional[pd.DataFrame] = None,
        y_train: Optional[pd.Series] = None,
        use_grid_search: bool = False,
    ) -> Tuple[object, Dict, Optional[float], Optional[Dict]]:
        """
        Train the model.

        Parameters
        ----------
        X_train : pd.DataFrame, optional
            Training features (if None, will load from config)
        y_train : pd.Series, optional
            Training target (if None, will load from config)
        use_grid_search : bool
            Whether to use grid search for hyperparameter tuning

        Returns
        -------
        model : object
            Trained model
        best_params : dict
            Best parameters
        best_cv_score : float, optional
            Best CV score (if grid search was used)
        training_times : dict, optional
            Dictionary with timing information containing:
            - best_model_fit_time: float, time to fit the best model in seconds
        """
        if X_train is None or y_train is None:
            X, y = self.load_data()
            X_train, X_test, y_train, y_test = self.split_data(X, y)

        logger.info(f"Training {self.model_type} model...")

        model, best_params, best_cv_score, training_times = self._build_model(
            X_train, y_train, use_grid_search=use_grid_search
        )

        self.model = model
        return model, best_params, best_cv_score, training_times

    def evaluate(self, model: object, X_test: pd.DataFrame, y_test: pd.Series) -> Dict:
        """
        Evaluate model performance on test set.

        Parameters
        ----------
        model : object
            Trained model
        X_test : pd.DataFrame
            Test features
        y_test : pd.Series
            Test target

        Returns
        -------
        dict
            Dictionary containing all metrics
        """
        logger.info("Evaluating model on test set...")

        # Make predictions
        y_pred = model.predict(X_test)

        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)

        # Classification report
        report = classification_report(
            y_test,
            y_pred,
            target_names=["Non-Priority", "Priority"],
            output_dict=True,
        )

        metrics = {
            "accuracy": float(accuracy),
            "precision": float(precision),
            "recall": float(recall),
            "f1_score": float(f1),
            "classification_report": report,
            "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
            "y_pred": y_pred.tolist(),
        }

        logger.info("Test Set Metrics:")
        logger.info(f"  Accuracy:  {accuracy:.4f}")
        logger.info(f"  Precision: {precision:.4f}")
        logger.info(f"  Recall:    {recall:.4f}")
        logger.info(f"  F1-Score:  {f1:.4f}")

        return metrics

    def save_model(
        self,
        model: object,
        model_path: str,
        X_train: Optional[pd.DataFrame] = None,
    ):
        """
        Save model and metadata to disk.

        Parameters
        ----------
        model : object
            Trained model
        model_path : str
            Path to save the model
        X_train : pd.DataFrame, optional
            Training features (for extracting feature names)
        """
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        joblib.dump(model, model_path)
        logger.info(f"Model saved to {model_path}")

        # Save feature metadata
        if X_train is not None:
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
                "apply_cyclic_encoding": self.apply_cyclic_encoding,
                "apply_interactions": self.apply_interactions,
                "model_type": self.model_type,
            }

            metadata_path = model_path.replace(".joblib", "_metadata.joblib")
            joblib.dump(metadata, metadata_path)
            logger.info(f"Feature metadata saved to {metadata_path}")

    def get_mlflow_tags(self) -> Dict[str, str]:
        """
        Get MLflow tags for this model type.

        Returns
        -------
        dict
            Dictionary of MLflow tags
        """
        return {
            "model_type": self.model_type,
            "framework": "multi_model_training",
        }

    def get_registered_model_name(self) -> str:
        """
        Get the registered model name for MLflow Model Registry.

        Returns
        -------
        str
            Registered model name with format: "Accident_Prediction_{ModelType}"
        """
        mlflow_config = self.config.get("mlflow", {})
        registry_config = mlflow_config.get("model_registry", {})

        # Use model-specific name if available, otherwise use pattern
        model_name_pattern = registry_config.get(
            "registered_model_name", "Accident_Prediction"
        )

        # Create model-specific name: e.g., "Accident_Prediction_XGBoost"
        model_type_capitalized = (
            self.model_type.replace("_", " ").title().replace(" ", "_")
        )
        return f"{model_name_pattern}_{model_type_capitalized}"
