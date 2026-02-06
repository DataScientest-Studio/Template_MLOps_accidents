#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MLflow Model Registry Management Script

This script provides utilities for managing models in the MLflow Model Registry:
- List registered models and versions
- Assign aliases to model versions (replaces deprecated stages: staging, production, archived)
- Promote models to production
- Get model information by alias or version
- Delete model versions or entire registered models

Note: This script uses MLflow aliases instead of deprecated stages. Aliases are
lowercase versions of stage names (e.g., "Production" -> "production" alias).

Usage:
    # List all registered models
    python scripts/manage_model_registry.py list-models

    # List all versions of a model
    python scripts/manage_model_registry.py list-versions --model-name XGBoost_Accident_Prediction

    # Assign an alias to a model version (replaces stage transition)
    python scripts/manage_model_registry.py transition --model-name XGBoost_Accident_Prediction --version 1 --stage Production

    # Promote latest version to Production (assigns "production" alias)
    python scripts/manage_model_registry.py promote --model-name XGBoost_Accident_Prediction --stage Production

    # Get model info by alias
    python scripts/manage_model_registry.py get-model --model-name XGBoost_Accident_Prediction --stage Production

    # Archive a model version (assigns "archived" alias)
    python scripts/manage_model_registry.py archive --model-name XGBoost_Accident_Prediction --version 1

    # Delete a specific model version
    python scripts/manage_model_registry.py delete-version --model-name XGBoost_Accident_Prediction --version 1

    # Delete an entire registered model (all versions) - requires confirmation
    python scripts/manage_model_registry.py delete-model --model-name XGBoost_Accident_Prediction

    # Delete model without confirmation prompt (use with caution!)
    python scripts/manage_model_registry.py delete-model --model-name XGBoost_Accident_Prediction --confirm
"""
import argparse
import logging
import os
import sys
from datetime import datetime

import mlflow
import yaml
from mlflow.tracking import MlflowClient

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def setup_mlflow_client(config_path="src/config/model_config.yaml"):
    """
    Setup MLflow client using configuration from config file.

    Parameters
    ----------
    config_path : str
        Path to configuration YAML file

    Returns
    -------
    MlflowClient
        Configured MLflow client
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            "Please ensure model_config.yaml exists in src/config/"
        )

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    mlflow_config = config.get("mlflow", {})

    if not mlflow_config.get("enabled", False):
        raise ValueError("MLflow is disabled in configuration")

    # Get tracking URI from config or environment
    tracking_uri = mlflow_config.get("tracking_uri") or os.getenv("MLFLOW_TRACKING_URI")

    # If not set, construct from DAGSHUB_REPO
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
    logger.info(f"MLflow tracking URI: {tracking_uri}")

    return MlflowClient()


def list_models(client):
    """List all registered models."""
    logger.info("Fetching registered models...")
    try:
        models = client.search_registered_models()
        if not models:
            print("No registered models found.")
            return

        print("\n" + "=" * 80)
        print("Registered Models")
        print("=" * 80)
        for model in models:
            print(f"\nModel Name: {model.name}")
            print(f"  Latest Versions: {len(model.latest_versions)}")
            if model.latest_versions:
                for version in model.latest_versions:
                    print(
                        f"    Version {version.version}: {version.current_stage} "
                        f"(Created: {version.creation_timestamp})"
                    )
        print("\n" + "=" * 80)
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise


def list_versions(client, model_name):
    """List all versions of a registered model."""
    logger.info(f"Fetching versions for model '{model_name}'...")
    try:
        versions = client.search_model_versions(f"name='{model_name}'")
        if not versions:
            print(f"No versions found for model '{model_name}'")
            return

        print("\n" + "=" * 80)
        print(f"Versions for Model: {model_name}")
        print("=" * 80)
        for version in sorted(versions, key=lambda v: v.version, reverse=True):
            print(f"\nVersion {version.version}")
            print(f"  Stage: {version.current_stage}")
            print(f"  Status: {version.status}")
            print(f"  Created: {version.creation_timestamp}")
            print(f"  Run ID: {version.run_id}")
            if version.description:
                print(f"  Description: {version.description}")
        print("\n" + "=" * 80)
    except Exception as e:
        logger.error(f"Failed to list versions: {e}")
        raise


def transition_model(client, model_name, version, stage):
    """
    Assign an alias to a model version (replaces deprecated stage transition).

    Parameters
    ----------
    client : MlflowClient
        MLflow client
    model_name : str
        Name of the registered model
    version : int
        Model version number
    stage : str
        Target stage/alias (None, Staging, Production, Archived)
    """
    valid_stages = ["None", "Staging", "Production", "Archived"]
    if stage not in valid_stages:
        raise ValueError(f"Invalid stage '{stage}'. Must be one of: {valid_stages}")

    logger.info(f"Assigning '{stage.lower()}' alias to {model_name} version {version}...")
    try:
        # Convert stage to lowercase alias (e.g., "Production" -> "production")
        alias = stage.lower()
        
        # If stage is "None", remove any existing aliases instead
        if stage == "None":
            # Try to remove common aliases if they exist
            for common_alias in ["staging", "production", "archived"]:
                try:
                    existing_mv = client.get_model_version_by_alias(model_name, common_alias)
                    if existing_mv.version == str(version):
                        client.delete_registered_model_alias(model_name, common_alias)
                        print(f"✓ Removed '{common_alias}' alias from {model_name} version {version}")
                        return
                except Exception:
                    pass
            print(f"✓ No alias to remove for {model_name} version {version}")
        else:
            # Remove alias from any previous version that had it
            try:
                previous_mv = client.get_model_version_by_alias(model_name, alias)
                client.delete_registered_model_alias(model_name, alias)
                logger.info(f"Removed '{alias}' alias from version {previous_mv.version}")
            except Exception:
                # No previous version with this alias, which is fine
                pass
            
            # Set alias for the specified version
            client.set_registered_model_alias(
                name=model_name,
                alias=alias,
                version=str(version)
            )
            print(f"✓ Successfully assigned '{alias}' alias to {model_name} version {version}")
    except Exception as e:
        logger.error(f"Failed to assign alias: {e}")
        raise


def promote_model(client, model_name, stage="Production"):
    """
    Promote the latest version of a model to a specific stage.

    Parameters
    ----------
    client : MlflowClient
        MLflow client
    model_name : str
        Name of the registered model
    stage : str
        Target stage (default: Production)
    """
    logger.info(f"Promoting latest version of {model_name} to {stage}...")
    try:
        # Get latest version
        versions = client.search_model_versions(f"name='{model_name}'")
        if not versions:
            raise ValueError(f"No versions found for model '{model_name}'")

        latest_version = max(versions, key=lambda v: int(v.version))
        transition_model(client, model_name, int(latest_version.version), stage)
    except Exception as e:
        logger.error(f"Failed to promote model: {e}")
        raise


def get_model_by_stage(client, model_name, stage):
    """
    Get model information by alias (replaces deprecated stage-based lookup).

    Parameters
    ----------
    client : MlflowClient
        MLflow client
    model_name : str
        Name of the registered model
    stage : str
        Alias name (Staging, Production, etc.)
    """
    logger.info(f"Fetching {model_name} with '{stage.lower()}' alias...")
    try:
        # Convert stage to lowercase alias (e.g., "Production" -> "production")
        alias = stage.lower()
        
        try:
            version = client.get_model_version_by_alias(model_name, alias)
            print("\n" + "=" * 80)
            print(f"Model: {model_name} (Alias: {alias})")
            print("=" * 80)
            print(f"Version: {version.version}")
            print(f"Alias: {alias}")
            print(f"Status: {version.status}")
            print(f"Created: {version.creation_timestamp}")
            print(f"Run ID: {version.run_id}")
            print(f"Model URI: models:/{model_name}@{alias}")
            if version.description:
                print(f"Description: {version.description}")
            print("=" * 80 + "\n")
        except Exception:
            # Fallback: search for versions if alias doesn't exist
            print(f"No model found with '{alias}' alias for '{model_name}'")
            print("Searching for latest version...")
            model_versions = client.search_model_versions(
                f"name='{model_name}'",
                max_results=1,
                order_by=["version_number DESC"]
            )
            if model_versions:
                version = model_versions[0]
                print(f"\nLatest version found: {version.version} (no alias assigned)")
            return
    except Exception as e:
        logger.error(f"Failed to get model: {e}")
        raise


def archive_model(client, model_name, version):
    """
    Archive a model version.

    Parameters
    ----------
    client : MlflowClient
        MLflow client
    model_name : str
        Name of the registered model
    version : int
        Model version number
    """
    transition_model(client, model_name, version, "Archived")


def delete_model_version(client, model_name, version):
    """
    Delete a specific model version.

    Parameters
    ----------
    client : MlflowClient
        MLflow client
    model_name : str
        Name of the registered model
    version : int
        Model version number to delete
    """
    logger.warning(f"Deleting {model_name} version {version}...")
    try:
        client.delete_model_version(name=model_name, version=version)
        print(f"✓ Successfully deleted {model_name} version {version}")
    except Exception as e:
        logger.error(f"Failed to delete model version: {e}")
        raise


def delete_registered_model(client, model_name, confirm=False):
    """
    Delete an entire registered model (all versions).

    Parameters
    ----------
    client : MlflowClient
        MLflow client
    model_name : str
        Name of the registered model to delete
    confirm : bool
        If True, skip confirmation prompt
    """
    # Safety check: require confirmation unless explicitly confirmed
    if not confirm:
        # Get model info first
        try:
            versions = client.search_model_versions(f"name='{model_name}'")
            num_versions = len(versions) if versions else 0
            print(f"\n⚠️  WARNING: This will delete the entire model '{model_name}' and all {num_versions} versions!")
            print("This action cannot be undone.")
            response = input("Type 'DELETE' to confirm: ")
            if response != "DELETE":
                print("Deletion cancelled.")
                return
        except Exception as e:
            logger.warning(f"Could not fetch model info: {e}")
            response = input(f"Are you sure you want to delete '{model_name}'? Type 'DELETE' to confirm: ")
            if response != "DELETE":
                print("Deletion cancelled.")
                return
    
    logger.warning(f"Deleting entire registered model '{model_name}'...")
    try:
        client.delete_registered_model(name=model_name)
        print(f"✓ Successfully deleted registered model '{model_name}' and all its versions")
    except Exception as e:
        logger.error(f"Failed to delete registered model: {e}")
        raise


def compare_models_enhanced(config_path, model_name, versions=None, stages=None, output_format="html"):
    """
    Compare models across versions using enhanced registry.
    
    Parameters
    ----------
    config_path : str
        Path to config file
    model_name : str
        Model name
    versions : list of int, optional
        Specific versions to compare
    stages : list of str, optional
        Stages to include
    output_format : str
        Output format (html, json, dataframe)
    """
    import yaml
    from src.models.model_registry_enhanced import EnhancedModelRegistry
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    registry = EnhancedModelRegistry(config)
    
    result = registry.compare_models_across_versions(
        model_name=model_name,
        versions=versions,
        include_stages=stages,
        output_format=output_format
    )
    
    if output_format == "html" and "html_report" in result:
        output_file = f"model_comparison_{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(output_file, "w") as f:
            f.write(result["html_report"])
        print(f"\nComparison report saved to: {output_file}")
    elif output_format == "json":
        import json
        output_file = f"model_comparison_{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\nComparison report saved to: {output_file}")
    else:
        print("\n" + "=" * 80)
        print("Model Comparison Results")
        print("=" * 80)
        if "dataframe" in result:
            print(result["dataframe"].to_string(index=False))
        
        if result.get("recommendations"):
            print("\nRecommendations:")
            for rec in result["recommendations"]:
                print(f"  - {rec['message']}")


def evaluate_promotion(config_path, model_name, version, target_stage="Production"):
    """Evaluate if a model version should be promoted."""
    import yaml
    from src.models.model_registry_enhanced import EnhancedModelRegistry
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    registry = EnhancedModelRegistry(config)
    evaluation = registry.evaluate_promotion_candidate(model_name, version, target_stage)
    
    print("\n" + "=" * 80)
    print(f"Promotion Evaluation: {model_name} version {version}")
    print("=" * 80)
    print(f"Promote: {'YES' if evaluation['promote'] else 'NO'}")
    print(f"Reason: {evaluation['reason']}")
    
    if evaluation.get("metrics_comparison"):
        print("\nMetrics Comparison:")
        import json
        print(json.dumps(evaluation["metrics_comparison"], indent=2))


def auto_promote(config_path, model_name, version, target_stage="Production"):
    """Automatically promote a model version if it meets criteria."""
    import yaml
    from src.models.model_registry_enhanced import EnhancedModelRegistry
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    registry = EnhancedModelRegistry(config)
    result = registry.auto_promote_model(model_name, version, target_stage)
    
    print("\n" + "=" * 80)
    print(f"Auto-Promotion Result: {model_name} version {version}")
    print("=" * 80)
    print(f"Promoted: {'YES' if result['promoted'] else 'NO'}")
    print(f"Reason: {result['reason']}")
    
    if result.get("previous_version_archived"):
        print(f"Previous version {result['previous_version_archived']} archived")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Manage MLflow Model Registry",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--config",
        type=str,
        default="src/config/model_config.yaml",
        help="Path to model configuration YAML file",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List models command
    list_models_parser = subparsers.add_parser("list-models", help="List all registered models")

    # List versions command
    list_versions_parser = subparsers.add_parser(
        "list-versions", help="List all versions of a model"
    )
    list_versions_parser.add_argument(
        "--model-name",
        type=str,
        required=True,
        help="Name of the registered model",
    )

    # Transition command
    transition_parser = subparsers.add_parser(
        "transition", help="Transition a model version to a stage"
    )
    transition_parser.add_argument(
        "--model-name", type=str, required=True, help="Name of the registered model"
    )
    transition_parser.add_argument(
        "--version", type=int, required=True, help="Model version number"
    )
    transition_parser.add_argument(
        "--stage",
        type=str,
        required=True,
        choices=["None", "Staging", "Production", "Archived"],
        help="Target stage",
    )

    # Promote command
    promote_parser = subparsers.add_parser(
        "promote", help="Promote latest version to a stage"
    )
    promote_parser.add_argument(
        "--model-name", type=str, required=True, help="Name of the registered model"
    )
    promote_parser.add_argument(
        "--stage",
        type=str,
        default="Production",
        choices=["Staging", "Production"],
        help="Target stage (default: Production)",
    )

    # Get model command
    get_model_parser = subparsers.add_parser(
        "get-model", help="Get model information by stage"
    )
    get_model_parser.add_argument(
        "--model-name", type=str, required=True, help="Name of the registered model"
    )
    get_model_parser.add_argument(
        "--stage",
        type=str,
        required=True,
        choices=["Staging", "Production"],
        help="Stage name",
    )

    # Archive command
    archive_parser = subparsers.add_parser("archive", help="Archive a model version")
    archive_parser.add_argument(
        "--model-name", type=str, required=True, help="Name of the registered model"
    )
    archive_parser.add_argument(
        "--version", type=int, required=True, help="Model version number"
    )

    # Delete version command
    delete_version_parser = subparsers.add_parser(
        "delete-version", help="Delete a specific model version"
    )
    delete_version_parser.add_argument(
        "--model-name", type=str, required=True, help="Name of the registered model"
    )
    delete_version_parser.add_argument(
        "--version", type=int, required=True, help="Model version number to delete"
    )

    # Delete model command
    delete_model_parser = subparsers.add_parser(
        "delete-model", help="Delete an entire registered model (all versions)"
    )
    delete_model_parser.add_argument(
        "--model-name", type=str, required=True, help="Name of the registered model to delete"
    )
    delete_model_parser.add_argument(
        "--confirm",
        action="store_true",
        help="Skip confirmation prompt (use with caution!)",
    )

    # Enhanced registry commands
    # Compare models command
    compare_parser = subparsers.add_parser(
        "compare-models", help="Compare models across versions (enhanced)"
    )
    compare_parser.add_argument(
        "--model-name", type=str, required=True, help="Name of the registered model"
    )
    compare_parser.add_argument(
        "--versions",
        type=int,
        nargs="+",
        help="Specific versions to compare (optional)",
    )
    compare_parser.add_argument(
        "--stages",
        type=str,
        nargs="+",
        choices=["None", "Staging", "Production", "Archived"],
        help="Stages to include (optional)",
    )
    compare_parser.add_argument(
        "--output-format",
        type=str,
        choices=["html", "json", "dataframe"],
        default="html",
        help="Output format (default: html)",
    )

    # Evaluate promotion command
    eval_promote_parser = subparsers.add_parser(
        "evaluate-promotion", help="Evaluate if a model should be promoted"
    )
    eval_promote_parser.add_argument(
        "--model-name", type=str, required=True, help="Name of the registered model"
    )
    eval_promote_parser.add_argument(
        "--version", type=int, required=True, help="Model version number"
    )
    eval_promote_parser.add_argument(
        "--target-stage",
        type=str,
        default="Production",
        choices=["Staging", "Production"],
        help="Target stage (default: Production)",
    )

    # Auto-promote command
    auto_promote_parser = subparsers.add_parser(
        "auto-promote", help="Automatically promote model if it meets criteria"
    )
    auto_promote_parser.add_argument(
        "--model-name", type=str, required=True, help="Name of the registered model"
    )
    auto_promote_parser.add_argument(
        "--version", type=int, required=True, help="Model version number"
    )
    auto_promote_parser.add_argument(
        "--target-stage",
        type=str,
        default="Production",
        choices=["Staging", "Production"],
        help="Target stage (default: Production)",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        # Enhanced registry commands
        if args.command == "compare-models":
            compare_models_enhanced(
                args.config,
                args.model_name,
                versions=args.versions,
                stages=args.stages,
                output_format=args.output_format,
            )
        elif args.command == "evaluate-promotion":
            evaluate_promotion(args.config, args.model_name, args.version, args.target_stage)
        elif args.command == "auto-promote":
            auto_promote(args.config, args.model_name, args.version, args.target_stage)
        else:
            # Original commands
            client = setup_mlflow_client(args.config)

            if args.command == "list-models":
                list_models(client)
            elif args.command == "list-versions":
                list_versions(client, args.model_name)
            elif args.command == "transition":
                transition_model(client, args.model_name, args.version, args.stage)
            elif args.command == "promote":
                promote_model(client, args.model_name, args.stage)
            elif args.command == "get-model":
                get_model_by_stage(client, args.model_name, args.stage)
            elif args.command == "archive":
                archive_model(client, args.model_name, args.version)
            elif args.command == "delete-version":
                delete_model_version(client, args.model_name, args.version)
            elif args.command == "delete-model":
                delete_registered_model(client, args.model_name, confirm=args.confirm)

    except Exception as e:
        logger.error(f"Command failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

