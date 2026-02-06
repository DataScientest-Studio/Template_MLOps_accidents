# -*- coding: utf-8 -*-
"""
Model prediction script for inference.

This script loads a trained model and makes predictions on new data.
It uses the same preprocessing pipeline used during training to ensure consistency.

Architecture:
- MLflow Model Registry: Used for production model serving (default for production)
- Local filesystem: Used for development/testing and pipeline reproducibility

Supports loading models from:
- MLflow Model Registry (recommended for production) - by stage (Production/Staging) or version
- Local filesystem (for development/testing) - DVC-tracked model files

Best Practice:
- Production inference should load from MLflow Model Registry (Production stage)
- Local model files are tracked by DVC for pipeline reproducibility only
- Use --use-mlflow-production flag or set USE_MLFLOW_PRODUCTION=true to default to MLflow
- Use --use-best-model flag to automatically select the best performing Production model across all model types
"""

import json
import logging
import os
import sys
import tempfile

import joblib
import yaml

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.features.preprocess import align_features_with_model, preprocess_for_inference

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def find_best_production_model(
    config_path: str = "src/config/model_config.yaml",
    metric: str = "f1_score",
    stage: str = "Production",
) -> tuple:
    """
    Find the best performing model across all model types in Production stage.

    This function queries all Production models from MLflow Model Registry,
    compares their metrics, and returns the best one.

    Parameters
    ----------
    config_path : str
        Path to configuration file
    metric : str
        Metric to use for comparison (default: "f1_score")
    stage : str
        Stage to search (default: "Production")

    Returns
    -------
    tuple
        (model_name, model_type, metrics_dict) or (None, None, None) if no models found
    """
    try:
        import mlflow
        from mlflow.tracking import MlflowClient
    except ImportError:
        raise ImportError(
            "MLflow is required to find best model. " "Install with: pip install mlflow"
        )

    # Setup MLflow
    if config_path and os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        mlflow_config = config.get("mlflow", {})
        tracking_uri = mlflow_config.get("tracking_uri") or os.getenv(
            "MLFLOW_TRACKING_URI"
        )
    else:
        tracking_uri = os.getenv("MLFLOW_TRACKING_URI")

    if not tracking_uri:
        dagshub_repo = os.getenv("DAGSHUB_REPO")
        if dagshub_repo:
            tracking_uri = f"https://dagshub.com/{dagshub_repo}.mlflow"
        else:
            raise ValueError(
                "MLflow tracking URI not configured. "
                "Set MLFLOW_TRACKING_URI or DAGSHUB_REPO environment variable."
            )

    mlflow.set_tracking_uri(tracking_uri)
    client = MlflowClient()

    # Get base model name from config
    if config_path and os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        mlflow_config = config.get("mlflow", {})
        registry_config = mlflow_config.get("model_registry", {})
        base_name = registry_config.get("registered_model_name", "Accident_Prediction")
    else:
        base_name = "Accident_Prediction"

    # Get enabled model types from config
    enabled_models = []
    if config_path and os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        multi_model_config = config.get("multi_model", {})
        enabled_models = multi_model_config.get("enabled_models", ["xgboost"])
    else:
        enabled_models = ["xgboost"]

    # Search for Production models across all model types
    best_model = None
    best_score = None
    best_model_type = None
    best_metrics = None

    for model_type in enabled_models:
        # Format model type: "xgboost" -> "XGBoost"
        model_type_formatted = model_type.replace("_", " ").title().replace(" ", "_")
        model_name = f"{base_name}_{model_type_formatted}"

        try:
            model_version = None
            alias = stage.lower()

            # Try to get Production model by alias (lowercase) - primary method
            try:
                model_version = client.get_model_version_by_alias(model_name, alias)
                logger.debug(f"Found {model_name} with '{alias}' alias")
            except Exception:
                # Fallback: search all versions and check for production stage or try to verify alias
                logger.debug(
                    f"No {stage} alias found for {model_name}, searching all versions..."
                )
                try:
                    # Search all versions of this model
                    all_versions = client.search_model_versions(f"name='{model_name}'")

                    if not all_versions:
                        logger.debug(f"No versions found for {model_name}")
                        continue

                    # Check each version for production stage (deprecated but still used)
                    # or verify if any version actually has the alias (in case of timing issues)
                    for mv in all_versions:
                        found = False

                        # Method 1: Check deprecated current_stage for backward compatibility
                        if hasattr(mv, "current_stage") and mv.current_stage == stage:
                            model_version = mv
                            found = True
                            logger.debug(
                                f"Found {model_name} version {mv.version} in {stage} stage (deprecated stage system)"
                            )

                        # Method 2: Try to verify if this version has the alias by getting detailed version info
                        # Some MLflow backends may have aliases that aren't immediately available via get_model_version_by_alias
                        if not found:
                            try:
                                mv_detail = client.get_model_version(
                                    model_name, mv.version
                                )
                                # Some backends store aliases differently - check if we can access them
                                # If the detailed version matches what we'd get by alias, use it
                                # This handles cases where alias lookup failed but the version actually has the alias
                                if hasattr(mv_detail, "aliases") and alias in (
                                    mv_detail.aliases or []
                                ):
                                    model_version = mv
                                    found = True
                                    logger.debug(
                                        f"Found {model_name} version {mv.version} with '{alias}' alias (via version detail)"
                                    )
                            except Exception:
                                pass

                        if found:
                            break

                    if model_version is None:
                        logger.debug(
                            f"No {stage} model found for {model_name} (checked all {len(all_versions)} versions)"
                        )
                        continue
                except Exception as e:
                    logger.debug(f"Error searching versions for {model_name}: {e}")
                    continue

            if model_version is None:
                continue

            # Get run metrics
            run = client.get_run(model_version.run_id)
            metrics = run.data.metrics

            # Check if the comparison metric exists
            if metric in metrics:
                score = metrics[metric]
                logger.info(f"Found {model_name}: {metric}={score:.4f}")

                if best_score is None or score > best_score:
                    best_score = score
                    best_model = model_name
                    best_model_type = model_type
                    best_metrics = metrics
            else:
                logger.warning(f"Metric '{metric}' not found for {model_name}")

        except Exception as e:
            logger.warning(f"Error checking {model_name}: {e}")
            continue

    if best_model:
        logger.info(
            f"Best Production model: {best_model} ({best_model_type}) "
            f"with {metric}={best_score:.4f}"
        )
        return best_model, best_model_type, best_metrics
    else:
        logger.warning(
            f"No Production models found across enabled model types: {enabled_models}"
        )
        # Build list of checked model names
        checked_models = [
            f"{base_name}_{m.replace('_', ' ').title().replace(' ', '_')}"
            for m in enabled_models
        ]
        logger.warning(f"Checked models: {checked_models}")
        logger.warning(
            "Tip: Ensure models are promoted to Production using: "
            "python scripts/manage_model_registry.py promote <model_name> Production"
        )
        return None, None, None


def load_best_production_model(
    config_path: str = "src/config/model_config.yaml",
    metric: str = "f1_score",
    stage: str = "Production",
):
    """
    Find the best Production model in MLflow and load it (model + encoders + metadata).
    Used by the predict service at startup. Fails if no Production model exists.

    Returns
    -------
    tuple
        (model, label_encoders, metadata, model_type) e.g. model_type "lightgbm"
    """
    best_model_name, best_model_type, _ = find_best_production_model(
        config_path=config_path,
        metric=metric,
        stage=stage,
    )
    if not best_model_name:
        raise ValueError(
            "No Production model found in MLflow. "
            "Promote a model to Production (e.g. via MLflow UI or manage_model_registry)."
        )
    model, label_encoders, metadata = load_model_from_registry(
        best_model_name,
        stage=stage,
        config_path=config_path,
    )
    return model, label_encoders, metadata, best_model_type


def get_model_name_from_config(
    model_type: str = "XGBoost", config_path: str = "src/config/model_config.yaml"
) -> str:
    """
    Get registered model name from configuration file.

    Parameters
    ----------
    model_type : str
        Model type (e.g., "XGBoost", "RandomForest"). Default: "XGBoost"
    config_path : str
        Path to configuration file

    Returns
    -------
    str
        Registered model name (e.g., "Accident_Prediction_XGBoost")
    """
    if not os.path.exists(config_path):
        logger.warning(
            f"Config file not found: {config_path}. Using default model name."
        )
        return f"Accident_Prediction_{model_type}"

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        mlflow_config = config.get("mlflow", {})
        registry_config = mlflow_config.get("model_registry", {})
        base_name = registry_config.get("registered_model_name", "Accident_Prediction")

        # Format model type: "XGBoost" -> "XGBoost", "random_forest" -> "Random_Forest"
        model_type_formatted = model_type.replace("_", " ").title().replace(" ", "_")
        return f"{base_name}_{model_type_formatted}"
    except Exception as e:
        logger.warning(f"Error reading config: {e}. Using default model name.")
        return f"Accident_Prediction_{model_type}"


def load_model_for_inference(
    model_type: str = "XGBoost",
    stage: str = "Production",
    version: int = None,
    config_path: str = "src/config/model_config.yaml",
    fallback_to_local: bool = True,
    local_model_path: str = None,
):
    """
    Load model for inference - defaults to MLflow Production stage (best practice).

    This function implements the best practice: MLflow for production models,
    local filesystem as fallback for development.

    Parameters
    ----------
    model_type : str
        Model type (e.g., "XGBoost", "RandomForest"). Default: "XGBoost"
    stage : str
        MLflow stage (default: "Production"). Use "Staging" for testing.
    version : int, optional
        Specific model version. If None, uses the model at the specified stage.
    config_path : str
        Path to configuration file
    fallback_to_local : bool
        If True, falls back to local filesystem if MLflow load fails
    local_model_path : str, optional
        Path to local model file for fallback. If None, uses default path.

    Returns
    -------
    tuple
        (model, label_encoders, metadata) tuple
    """
    model_name = get_model_name_from_config(model_type, config_path)

    # Try MLflow first (production path)
    try:
        logger.info(
            f"Loading model from MLflow Model Registry: {model_name} (stage: {stage})"
        )
        return load_model_from_registry(
            model_name=model_name, stage=stage, version=version, config_path=config_path
        )
    except Exception as e:
        if fallback_to_local:
            logger.warning(
                f"MLflow load failed: {e}. "
                f"Falling back to local filesystem (development mode)."
            )
            if local_model_path is None:
                # Default local path based on model type
                model_type_lower = model_type.lower().replace("_", "_")
                local_model_path = f"models/{model_type_lower}_model.joblib"
            return load_model_artifacts(local_model_path)
        else:
            raise


def load_model_from_registry(
    model_name: str, stage: str = None, version: int = None, config_path: str = None
):
    """
    Load model from MLflow Model Registry.

    Parameters
    ----------
    model_name : str
        Name of the registered model
    stage : str, optional
        Stage name (Staging, Production). Required if version is not provided.
    version : int, optional
        Model version number. Required if stage is not provided.
    config_path : str, optional
        Path to configuration file for MLflow setup

    Returns
    -------
    tuple
        (model, label_encoders, metadata) tuple
    """
    try:
        import mlflow
        import mlflow.sklearn
    except ImportError:
        raise ImportError(
            "MLflow is required to load models from registry. "
            "Install with: pip install mlflow"
        )

    # Setup MLflow tracking URI
    if config_path and os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        mlflow_config = config.get("mlflow", {})
        tracking_uri = mlflow_config.get("tracking_uri") or os.getenv(
            "MLFLOW_TRACKING_URI"
        )
    else:
        tracking_uri = os.getenv("MLFLOW_TRACKING_URI")

    if not tracking_uri:
        dagshub_repo = os.getenv("DAGSHUB_REPO")
        if dagshub_repo:
            tracking_uri = f"https://dagshub.com/{dagshub_repo}.mlflow"
        else:
            raise ValueError(
                "MLflow tracking URI not configured. "
                "Set MLFLOW_TRACKING_URI or DAGSHUB_REPO environment variable."
            )

    mlflow.set_tracking_uri(tracking_uri)

    # Construct model URI
    if stage:
        model_uri = f"models:/{model_name}/{stage}"
        logger.info(f"Loading model from MLflow registry: {model_uri}")
    elif version:
        model_uri = f"models:/{model_name}/{version}"
        logger.info(
            f"Loading model version {version} from MLflow registry: {model_uri}"
        )
    else:
        raise ValueError("Either 'stage' or 'version' must be provided")

    # Load model from registry
    model = mlflow.sklearn.load_model(model_uri)
    logger.info("Successfully loaded model from MLflow registry")

    # Load metadata and label encoders from MLflow artifacts
    label_encoders = None
    metadata = None

    try:
        from mlflow.tracking import MlflowClient

        client = MlflowClient()

        # Get the model version to find the run_id
        if stage:
            # Get model version by alias (stage)
            alias = stage.lower()
            try:
                model_version = client.get_model_version_by_alias(model_name, alias)
            except Exception:
                # Fallback: search for model version with the stage
                model_versions = client.search_model_versions(
                    f"name='{model_name}'",
                    max_results=1,
                    order_by=["version_number DESC"],
                )
                if model_versions:
                    model_version = model_versions[0]
                else:
                    raise ValueError(
                        f"No model version found for {model_name} with stage {stage}"
                    )
        elif version:
            model_version = client.get_model_version(model_name, version)
        else:
            raise ValueError("Either 'stage' or 'version' must be provided")

        run_id = model_version.run_id
        logger.info(f"Loading artifacts from MLflow run: {run_id}")

        # Download artifacts to a temporary directory.
        # Training logs metadata/encoders under "artifacts/"; the run may not have that path
        # (e.g. older run or different backend), so list first and download root if needed.
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_path_to_download = "artifacts"
            try:
                top_level = client.list_artifacts(run_id, "")
                path_names = [p.path for p in top_level] if top_level else []
                if "artifacts" not in path_names:
                    # Run has no "artifacts" folder (e.g. promoted from older run); download root
                    artifact_path_to_download = ""
                    logger.debug(
                        "Run has no 'artifacts' path (found: %s), downloading run root",
                        path_names or "[]",
                    )
            except Exception as list_err:
                logger.debug("Could not list run artifacts: %s", list_err)

            downloaded_root = False
            try:
                artifacts_path = client.download_artifacts(
                    run_id, artifact_path_to_download, temp_dir
                )
                logger.debug(f"Downloaded artifacts to: {artifacts_path}")
            except Exception as download_err:
                if artifact_path_to_download == "artifacts":
                    # Retry with root in case path format differs (e.g. remote backend)
                    try:
                        artifacts_path = client.download_artifacts(run_id, "", temp_dir)
                        downloaded_root = True
                        logger.debug("Downloaded run root instead: %s", artifacts_path)
                    except Exception:
                        raise download_err
                else:
                    raise download_err

            # Resolve artifacts subfolder when we downloaded root (files are in artifacts/)
            search_base = artifacts_path
            if artifact_path_to_download == "" or downloaded_root:
                artifacts_sub = os.path.join(artifacts_path, "artifacts")
                if os.path.isdir(artifacts_sub):
                    search_base = artifacts_sub

            # Load metadata - try multiple possible locations
            metadata_file = os.path.join(search_base, "model_metadata.joblib")
            if not os.path.exists(metadata_file):
                metadata_file = os.path.join(artifacts_path, "model_metadata.joblib")
            if not os.path.exists(metadata_file):
                metadata_file = os.path.join(
                    temp_dir, "artifacts", "model_metadata.joblib"
                )

            if os.path.exists(metadata_file):
                metadata = joblib.load(metadata_file)
                logger.info("Loaded model metadata from MLflow artifacts")
            else:
                logger.warning(
                    "Model metadata not found in MLflow artifacts. "
                    "Consider storing metadata as MLflow artifacts during training."
                )

            # Load label encoders - try multiple possible locations
            encoders_file = os.path.join(search_base, "label_encoders.joblib")
            if not os.path.exists(encoders_file):
                encoders_file = os.path.join(artifacts_path, "label_encoders.joblib")
            if not os.path.exists(encoders_file):
                encoders_file = os.path.join(
                    temp_dir, "artifacts", "label_encoders.joblib"
                )

            if os.path.exists(encoders_file):
                label_encoders = joblib.load(encoders_file)
                logger.info("Loaded label encoders from MLflow artifacts")
            else:
                logger.warning(
                    "Label encoders not found in MLflow artifacts. "
                    "Consider storing encoders as MLflow artifacts during training."
                )
                # Fallback to local filesystem
                local_encoders_path = "models/label_encoders.joblib"
                if os.path.exists(local_encoders_path):
                    label_encoders = joblib.load(local_encoders_path)
                    logger.info(
                        f"Loaded label encoders from local filesystem fallback: {local_encoders_path}"
                    )

    except Exception as e:
        logger.warning(f"Failed to load artifacts from MLflow: {e}")
        logger.warning("Falling back to local filesystem...")

        # Fallback to local filesystem
        local_encoders_path = "models/label_encoders.joblib"
        local_metadata_path = "models/trained_model_metadata.joblib"

        if os.path.exists(local_encoders_path):
            label_encoders = joblib.load(local_encoders_path)
            logger.info(
                f"Loaded label encoders from local filesystem: {local_encoders_path}"
            )

        if os.path.exists(local_metadata_path):
            metadata = joblib.load(local_metadata_path)
            logger.info(f"Loaded metadata from local filesystem: {local_metadata_path}")

    return model, label_encoders, metadata


def load_model_artifacts(model_path: str):
    """
    Load model and associated artifacts (encoders, metadata) from local filesystem.

    Parameters
    ----------
    model_path : str
        Path to the trained model file

    Returns
    -------
    tuple
        (model, label_encoders, metadata) tuple
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model file not found: {model_path}\n"
            "Please run 'make run-train' first to train the model."
        )

    model = joblib.load(model_path)
    logger.info(f"Loaded model from {model_path}")

    # Load label encoders
    # Try to find label encoders in the same directory as the model
    model_dir = os.path.dirname(model_path)
    encoders_path = os.path.join(model_dir, "label_encoders.joblib")
    label_encoders = None
    if os.path.exists(encoders_path):
        label_encoders = joblib.load(encoders_path)
        logger.info(f"Loaded label encoders from {encoders_path}")
    else:
        logger.warning(f"Label encoders not found at {encoders_path}")

    # Load feature metadata - use the same pattern as base_trainer.py
    metadata_path = model_path.replace(".joblib", "_metadata.joblib")
    metadata = None
    if os.path.exists(metadata_path):
        loaded_metadata = joblib.load(metadata_path)
        # Ensure metadata is a dictionary (not a Pipeline or other object)
        if isinstance(loaded_metadata, dict):
            metadata = loaded_metadata
            logger.info(f"Loaded feature metadata from {metadata_path}")
        else:
            logger.warning(
                f"Metadata file exists but is not a dictionary (type: {type(loaded_metadata)}). "
                "Using default preprocessing settings."
            )
    else:
        logger.warning(f"Feature metadata not found at {metadata_path}")

    return model, label_encoders, metadata


def get_expected_features(model, metadata=None):
    """
    Extract expected feature names from model or metadata.

    Parameters
    ----------
    model : object
        Trained model (pipeline)
    metadata : dict, optional
        Feature metadata dictionary

    Returns
    -------
    list
        List of expected feature names
    """
    # Try metadata first (ensure it's a dictionary)
    if metadata and isinstance(metadata, dict) and "feature_names" in metadata:
        return metadata["feature_names"]

    # Try to extract from model
    if hasattr(model, "steps") and len(model.steps) > 0:
        xgb_model = model.steps[-1][1]
        if (
            hasattr(xgb_model, "feature_names_in_")
            and xgb_model.feature_names_in_ is not None
        ):
            return list(xgb_model.feature_names_in_)
        elif hasattr(xgb_model, "get_booster"):
            booster = xgb_model.get_booster()
            if hasattr(booster, "feature_names"):
                return booster.feature_names

    return None


def predict(
    features: dict,
    model_path: str = None,
    model_name: str = None,
    model_type: str = "XGBoost",
    stage: str = None,
    version: int = None,
    use_mlflow_production: bool = None,
    use_best_model: bool = None,
    config_path: str = "src/config/model_config.yaml",
):
    """
    Make prediction from input features.

    This function applies the same preprocessing pipeline used during training.

    Best Practice: Use MLflow Model Registry for production inference.
    Set use_mlflow_production=True or USE_MLFLOW_PRODUCTION=true to default to MLflow Production.
    Set use_best_model=True to automatically select the best performing Production model.

    Parameters
    ----------
    features : dict
        Input features dictionary
    model_path : str, optional
        Path to the trained model file (for local filesystem loading)
        Ignored if use_mlflow_production=True or model_name is provided
    model_name : str, optional
        Name of the registered model (for MLflow registry loading)
        If None and use_mlflow_production=True, inferred from config or best model
    model_type : str
        Model type (e.g., "XGBoost", "RandomForest"). Used when inferring model_name.
        Default: "XGBoost". Ignored if use_best_model=True
    stage : str, optional
        Stage name (Staging, Production). Default: "Production" if use_mlflow_production=True
    version : int, optional
        Model version number - alternative to stage for registry loading
    use_mlflow_production : bool, optional
        If True, loads from MLflow Production stage (best practice).
        If None, checks USE_MLFLOW_PRODUCTION environment variable.
        If False or not set, uses local filesystem (development mode)
    use_best_model : bool, optional
        If True, automatically finds and uses the best performing Production model
        across all model types (compares by f1_score).
        If None, checks USE_BEST_MODEL environment variable.
        Overrides model_name and model_type if set.
    config_path : str
        Path to configuration file (for MLflow setup)

    Returns
    -------
    prediction : array
        Model prediction
    """
    # Check if we should use MLflow Production (best practice)
    if use_mlflow_production is None:
        use_mlflow_production = (
            os.getenv("USE_MLFLOW_PRODUCTION", "false").lower() == "true"
        )

    # Check if we should use best model across all types
    if use_best_model is None:
        use_best_model = os.getenv("USE_BEST_MODEL", "false").lower() == "true"

    # Determine loading method
    if use_mlflow_production or model_name or use_best_model:
        # Load from MLflow registry (production path)
        if use_best_model:
            # Find best model across all Production models
            logger.info("Finding best Production model across all model types...")
            best_model_name, best_model_type, best_metrics = find_best_production_model(
                config_path=config_path, stage=stage or "Production"
            )

            if best_model_name:
                model_name = best_model_name
                model_type = best_model_type
                logger.info(f"Using best model: {model_name} (type: {model_type})")
            else:
                # Fallback to default if no Production models found
                logger.warning(
                    "No Production models found, falling back to default XGBoost"
                )
                model_name = get_model_name_from_config("XGBoost", config_path)
                model_type = "XGBoost"
        elif model_name is None:
            model_name = get_model_name_from_config(model_type, config_path)

        if stage is None:
            stage = "Production"  # Default to Production stage

        logger.info(
            f"Loading model from MLflow Model Registry: {model_name} (stage: {stage})"
        )
        model, label_encoders, metadata = load_model_from_registry(
            model_name, stage=stage, version=version, config_path=config_path
        )
    else:
        # Load from local filesystem (development/testing mode)
        if model_path is None:
            model_path = "models/trained_model.joblib"
        logger.info(f"Loading model from local filesystem: {model_path}")
        model, label_encoders, metadata = load_model_artifacts(model_path)

    # Get preprocessing parameters from metadata or use defaults
    # Ensure metadata is a dictionary before accessing it
    if metadata and not isinstance(metadata, dict):
        logger.warning(
            f"Metadata is not a dictionary (type: {type(metadata)}). "
            "Using default preprocessing settings."
        )
        metadata = None

    apply_cyclic_encoding = (
        metadata.get("apply_cyclic_encoding", True)
        if isinstance(metadata, dict)
        else True
    )
    apply_interactions = (
        metadata.get("apply_interactions", True) if isinstance(metadata, dict) else True
    )

    # Preprocess features
    logger.info("Preprocessing input features...")
    # Format model_type for display (e.g., "lightgbm" -> "LightGBM", "xgboost" -> "XGBoost")
    if model_type:
        # Handle common model type names
        model_type_lower = model_type.lower()
        model_type_map = {
            "lightgbm": "LightGBM",
            "xgboost": "XGBoost",
            "random_forest": "RandomForest",
            "randomforest": "RandomForest",
            "logistic_regression": "LogisticRegression",
            "logisticregression": "LogisticRegression",
        }
        model_type_display = model_type_map.get(model_type_lower)
        if not model_type_display:
            # Fallback: capitalize first letter of each word
            model_type_display = model_type.replace("_", " ").title().replace(" ", "")
    else:
        model_type_display = None
    df_features = preprocess_for_inference(
        features,
        label_encoders=label_encoders,
        apply_cyclic_encoding=apply_cyclic_encoding,
        apply_interactions=apply_interactions,
        model_type=model_type_display,
    )

    # Get expected features from model
    expected_features = get_expected_features(model, metadata)
    if expected_features is None:
        logger.warning(
            "Could not determine expected features, using all preprocessed features"
        )
        expected_features = list(df_features.columns)
    else:
        # Align features with model expectations
        df_features = align_features_with_model(df_features, expected_features)

    logger.info(f"Making prediction with {len(expected_features)} features...")

    # Make prediction
    prediction = model.predict(df_features)

    return prediction


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Make predictions using trained model",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "json_file",
        nargs="?",
        default="src/models/test_features.json",
        help="Path to JSON file with input features",
    )
    parser.add_argument(
        "--model-path",
        type=str,
        help="Path to local model file (for development/testing). Ignored if --use-mlflow-production is set.",
    )
    parser.add_argument(
        "--model-name",
        type=str,
        help="Name of registered model in MLflow (for registry loading). If not provided and --use-mlflow-production is set, inferred from config.",
    )
    parser.add_argument(
        "--model-type",
        type=str,
        default="XGBoost",
        help="Model type (e.g., XGBoost, RandomForest). Used when inferring model name. Default: XGBoost",
    )
    parser.add_argument(
        "--stage",
        type=str,
        choices=["Staging", "Production"],
        help="Stage name for registry loading. Default: Production if --use-mlflow-production is set",
    )
    parser.add_argument(
        "--version",
        type=int,
        help="Model version number for registry loading (alternative to --stage)",
    )
    parser.add_argument(
        "--use-mlflow-production",
        action="store_true",
        help="Load model from MLflow Production stage (best practice for production inference). "
        "Can also be set via USE_MLFLOW_PRODUCTION=true environment variable.",
    )
    parser.add_argument(
        "--use-best-model",
        action="store_true",
        help="Automatically find and use the best performing Production model across all model types "
        "(compares by f1_score). Overrides --model-name and --model-type. "
        "Can also be set via USE_BEST_MODEL=true environment variable.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="src/config/model_config.yaml",
        help="Path to model configuration file",
    )

    args = parser.parse_args()

    # Validate arguments
    if (
        args.model_name
        and not args.stage
        and not args.version
        and not args.use_mlflow_production
    ):
        parser.error(
            "--stage or --version is required when using --model-name (or use --use-mlflow-production)"
        )

    # Load features from JSON file
    try:
        with open(args.json_file, "r") as file:
            features = json.load(file)
        print(f"Loaded features from {args.json_file}")
    except FileNotFoundError:
        print(f"Error: JSON file not found: {args.json_file}")
        print(
            f"Please create {args.json_file} with the required features or specify a different file."
        )
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {args.json_file}: {e}")
        sys.exit(1)

    # Make prediction
    try:
        result = predict(
            features,
            model_path=args.model_path,
            model_name=args.model_name,
            model_type=args.model_type,
            stage=args.stage,
            version=args.version,
            use_mlflow_production=args.use_mlflow_production,
            use_best_model=args.use_best_model,
            config_path=args.config,
        )
        print(f"\nPrediction: {result[0]}")
        print(f"Interpretation: {'Priority' if result[0] == 1 else 'Non-Priority'}")
    except Exception as e:
        logger.error(f"Prediction failed: {e}", exc_info=True)
        sys.exit(1)
