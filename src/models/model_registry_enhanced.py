# -*- coding: utf-8 -*-
"""
Enhanced MLflow Model Registry with automated comparison and promotion workflows.

This module provides:
1. Automated model comparison across different training runs/versions
2. Automated model promotion workflow based on performance thresholds
3. Model visualization and comparison reports

Note: Performance tracking over time and degradation detection are handled by
Evidently AI (planned for Phase 4). Prometheus/Grafana will handle production
metrics visualization and alerting.
"""

import json
import logging
import os
import tempfile
import warnings
from datetime import datetime
from typing import Dict, List, Optional

import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend
import matplotlib.pyplot as plt
import mlflow
import mlflow.sklearn
import pandas as pd
from mlflow.tracking import MlflowClient

# Suppress FutureWarnings for deprecated MLflow methods
warnings.filterwarnings("ignore", category=FutureWarning, module="mlflow")

logger = logging.getLogger(__name__)


class EnhancedModelRegistry:
    """
    Enhanced MLflow Model Registry with automated workflows.

    Features:
    - Automated model comparison across versions
    - Performance-based promotion automation
    - Model visualization and comparison reports

    Note: Performance tracking over time and degradation detection are handled by
    Evidently AI (planned for Phase 4). Prometheus/Grafana will handle production
    metrics visualization and alerting.
    """

    def __init__(self, config: Dict):
        """
        Initialize enhanced model registry.

        Parameters
        ----------
        config : dict
            Configuration dictionary from model_config.yaml
        """
        self.config = config
        self.mlflow_config = config.get("mlflow", {})
        self.registry_config = self.mlflow_config.get("model_registry", {})
        self.promotion_config = self.registry_config.get("promotion", {})
        # Get comparison stage from auto_promotion config (defaults to Production)
        # Can be a string (single stage) or list (multiple stages - compares against best)
        auto_promotion_config = self.registry_config.get("auto_promotion", {})
        comparison_stage_config = auto_promotion_config.get(
            "comparison_stage", "Production"
        )
        # Normalize to list for consistent handling
        if isinstance(comparison_stage_config, str):
            self.comparison_stages = [comparison_stage_config]
        elif isinstance(comparison_stage_config, list):
            self.comparison_stages = comparison_stage_config
        else:
            self.comparison_stages = ["Production"]
        # Keep backward compatibility - use first stage as primary for display purposes
        self.comparison_stage = (
            self.comparison_stages[0] if self.comparison_stages else "Production"
        )

        # Setup MLflow client
        self._setup_mlflow_client()

    def _setup_mlflow_client(self):
        """Setup MLflow client with tracking URI from config."""
        tracking_uri = self.mlflow_config.get("tracking_uri") or os.getenv(
            "MLFLOW_TRACKING_URI"
        )

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
        self.client = MlflowClient()
        logger.info(f"MLflow client initialized with tracking URI: {tracking_uri}")

    def compare_models_across_versions(
        self,
        model_name: str,
        versions: Optional[List[int]] = None,
        include_stages: Optional[List[str]] = None,
        output_format: str = "html",
    ) -> Dict:
        """
        Compare models across different versions or stages.

        Parameters
        ----------
        model_name : str
            Name of the registered model
        versions : list of int, optional
            Specific versions to compare. If None, compares all versions.
        include_stages : list of str, optional
            Stages to include (e.g., ["Production", "Staging"]). If None, includes all.
        output_format : str
            Output format: "html", "json", or "dataframe"

        Returns
        -------
        dict
            Comparison results with metrics, visualizations, and recommendations
        """
        logger.info(f"Comparing versions of model '{model_name}'")

        # Get model versions
        try:
            if versions:
                model_versions = []
                for version in versions:
                    try:
                        mv = self.client.get_model_version(model_name, version)
                        model_versions.append(mv)
                    except Exception as e:
                        logger.warning(f"Could not fetch version {version}: {e}")
            else:
                # Get all versions using search_model_versions without filter (works with DagsHub)
                all_versions = self.client.search_model_versions()
                model_versions = [mv for mv in all_versions if mv.name == model_name]

                # Filter by stages if specified
                if include_stages and model_versions:
                    model_versions = [
                        mv
                        for mv in model_versions
                        if mv.current_stage in include_stages
                    ]
        except Exception as e:
            logger.warning(f"Error fetching model versions for '{model_name}': {e}")
            return {}

        if not model_versions:
            logger.warning(f"No versions found for model '{model_name}'")
            return {}

        # Sort by version number (descending)
        model_versions = sorted(
            model_versions, key=lambda v: int(v.version), reverse=True
        )

        # Collect metrics for each version
        comparison_data = []
        for mv in model_versions:
            try:
                # Get run details
                run = self.client.get_run(mv.run_id)

                # Extract metrics
                metrics = {
                    "version": int(mv.version),
                    "stage": mv.current_stage,
                    "created": mv.creation_timestamp,
                    "run_id": mv.run_id,
                    "status": mv.status,
                }

                # Get performance metrics
                for metric_name in [
                    "accuracy",
                    "precision",
                    "recall",
                    "f1_score",
                    "roc_auc",
                ]:
                    if metric_name in run.data.metrics:
                        metrics[metric_name] = run.data.metrics[metric_name]

                # Get model size (if available)
                try:
                    model_uri = f"models:/{model_name}/{mv.version}"
                    model = mlflow.sklearn.load_model(model_uri)
                    # Estimate model size (rough approximation)
                    import pickle

                    model_size_bytes = len(pickle.dumps(model))
                    metrics["model_size_mb"] = model_size_bytes / (1024 * 1024)
                except Exception as e:
                    logger.debug(
                        f"Could not estimate model size for version {mv.version}: {e}"
                    )
                    metrics["model_size_mb"] = None

                # Get training parameters
                metrics["n_estimators"] = run.data.params.get("n_estimators", "N/A")
                metrics["max_depth"] = run.data.params.get("max_depth", "N/A")
                metrics["learning_rate"] = run.data.params.get("learning_rate", "N/A")

                comparison_data.append(metrics)

            except Exception as e:
                logger.warning(f"Error processing version {mv.version}: {e}")
                continue

        if not comparison_data:
            logger.warning("No valid comparison data collected")
            return {}

        # Create comparison DataFrame
        comparison_df = pd.DataFrame(comparison_data)

        # Generate comparison report
        comparison_result = {
            "model_name": model_name,
            "comparison_date": datetime.now().isoformat(),
            "num_versions": len(comparison_df),
            "data": comparison_df.to_dict("records"),
        }

        # Generate visualizations
        if len(comparison_df) > 1:
            comparison_result["visualizations"] = (
                self._generate_comparison_visualizations(comparison_df, model_name)
            )

        # Generate recommendations
        comparison_result["recommendations"] = (
            self._generate_comparison_recommendations(comparison_df)
        )

        # Generate output in requested format
        if output_format == "html":
            comparison_result["html_report"] = self._generate_html_report(
                comparison_result
            )
        elif output_format == "dataframe":
            comparison_result["dataframe"] = comparison_df

        return comparison_result

    def _generate_comparison_visualizations(
        self, comparison_df: pd.DataFrame, model_name: str
    ) -> Dict[str, str]:
        """
        Generate visualization plots for model comparison.

        Returns
        -------
        dict
            Dictionary mapping plot names to file paths
        """
        plots = {}

        # Metrics comparison plot
        metrics_to_plot = ["accuracy", "precision", "recall", "f1_score"]
        available_metrics = [m for m in metrics_to_plot if m in comparison_df.columns]

        if available_metrics:
            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            axes = axes.flatten()

            for idx, metric in enumerate(available_metrics[:4]):
                ax = axes[idx]
                comparison_df.plot(
                    x="version",
                    y=metric,
                    kind="line",
                    marker="o",
                    ax=ax,
                    title=f"{metric.replace('_', ' ').title()} by Version",
                )
                ax.set_xlabel("Version")
                ax.set_ylabel(metric.replace("_", " ").title())
                ax.grid(True, alpha=0.3)

            plt.tight_layout()
            metrics_plot_path = tempfile.mktemp(suffix=".png")
            plt.savefig(metrics_plot_path, dpi=150, bbox_inches="tight")
            plt.close()
            plots["metrics_comparison"] = metrics_plot_path

        # Stage distribution
        if "stage" in comparison_df.columns:
            fig, ax = plt.subplots(figsize=(8, 6))
            stage_counts = comparison_df["stage"].value_counts()
            stage_counts.plot(kind="bar", ax=ax, color="steelblue")
            ax.set_title("Model Versions by Stage")
            ax.set_xlabel("Stage")
            ax.set_ylabel("Count")
            ax.tick_params(axis="x", rotation=45)
            plt.tight_layout()
            stage_plot_path = tempfile.mktemp(suffix=".png")
            plt.savefig(stage_plot_path, dpi=150, bbox_inches="tight")
            plt.close()
            plots["stage_distribution"] = stage_plot_path

        return plots

    def _generate_comparison_recommendations(
        self, comparison_df: pd.DataFrame
    ) -> List[Dict[str, str]]:
        """
        Generate recommendations based on comparison results.

        Returns
        -------
        list
            List of recommendation dictionaries
        """
        recommendations = []

        if "f1_score" not in comparison_df.columns:
            return recommendations

        # Find best performing version
        best_version = comparison_df.loc[comparison_df["f1_score"].idxmax()]

        # Check if best version is in Production
        production_versions = comparison_df[comparison_df["stage"] == "Production"]
        if not production_versions.empty:
            prod_best = production_versions.loc[
                production_versions["f1_score"].idxmax()
            ]

            if best_version["version"] != prod_best["version"]:
                f1_improvement = (
                    (best_version["f1_score"] - prod_best["f1_score"])
                    / prod_best["f1_score"]
                ) * 100
                recommendations.append(
                    {
                        "type": "promotion",
                        "message": (
                            f"Version {best_version['version']} outperforms Production version "
                            f"{prod_best['version']} by {f1_improvement:.2f}% in F1 score. "
                            f"Consider promoting to Production."
                        ),
                        "best_version": int(best_version["version"]),
                        "current_prod_version": int(prod_best["version"]),
                        "f1_improvement_pct": float(f1_improvement),
                    }
                )

        # Check for performance degradation
        if len(comparison_df) >= 2:
            sorted_df = comparison_df.sort_values("version")
            recent_f1 = sorted_df.iloc[-1]["f1_score"]
            previous_f1 = sorted_df.iloc[-2]["f1_score"]

            if recent_f1 < previous_f1:
                degradation_pct = ((previous_f1 - recent_f1) / previous_f1) * 100
                if degradation_pct > 5:  # More than 5% degradation
                    recommendations.append(
                        {
                            "type": "degradation",
                            "message": (
                                f"Performance degradation detected: Version {sorted_df.iloc[-1]['version']} "
                                f"shows {degradation_pct:.2f}% decrease in F1 score compared to "
                                f"version {sorted_df.iloc[-2]['version']}."
                            ),
                            "degradation_pct": float(degradation_pct),
                        }
                    )

        return recommendations

    def _generate_html_report(self, comparison_result: Dict) -> str:
        """Generate HTML report from comparison results."""
        html_parts = [
            "<!DOCTYPE html>",
            "<html><head>",
            "<title>Model Comparison Report</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 20px; }",
            "table { border-collapse: collapse; width: 100%; margin: 20px 0; }",
            "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
            "th { background-color: #4CAF50; color: white; }",
            "tr:nth-child(even) { background-color: #f2f2f2; }",
            ".recommendation { padding: 10px; margin: 10px 0; border-left: 4px solid #2196F3; background-color: #E3F2FD; }",
            ".warning { border-left-color: #FF9800; background-color: #FFF3E0; }",
            "</style>",
            "</head><body>",
            f"<h1>Model Comparison Report: {comparison_result['model_name']}</h1>",
            f"<p><strong>Generated:</strong> {comparison_result['comparison_date']}</p>",
            f"<p><strong>Versions Compared:</strong> {comparison_result['num_versions']}</p>",
        ]

        # Add comparison table
        if comparison_result["data"]:
            html_parts.append("<h2>Comparison Table</h2>")
            html_parts.append("<table>")

            # Header
            headers = list(comparison_result["data"][0].keys())
            html_parts.append(
                "<tr>" + "".join([f"<th>{h}</th>" for h in headers]) + "</tr>"
            )

            # Rows
            for row in comparison_result["data"]:
                html_parts.append(
                    "<tr>"
                    + "".join([f"<td>{row.get(h, 'N/A')}</td>" for h in headers])
                    + "</tr>"
                )

            html_parts.append("</table>")

        # Add visualizations
        if "visualizations" in comparison_result:
            html_parts.append("<h2>Visualizations</h2>")
            for plot_name, plot_path in comparison_result["visualizations"].items():
                if os.path.exists(plot_path):
                    # Convert to base64 for embedding
                    import base64

                    with open(plot_path, "rb") as f:
                        img_data = base64.b64encode(f.read()).decode()
                    html_parts.append(f'<h3>{plot_name.replace("_", " ").title()}</h3>')
                    html_parts.append(
                        f'<img src="data:image/png;base64,{img_data}" style="max-width: 100%;">'
                    )

        # Add recommendations
        if comparison_result.get("recommendations"):
            html_parts.append("<h2>Recommendations</h2>")
            for rec in comparison_result["recommendations"]:
                css_class = (
                    "warning" if rec["type"] == "degradation" else "recommendation"
                )
                html_parts.append(
                    f'<div class="{css_class}"><strong>{rec["type"].title()}:</strong> {rec["message"]}</div>'
                )

        html_parts.append("</body></html>")
        return "\n".join(html_parts)

    def log_comparison_to_mlflow(
        self, model_name: str, comparison_result: Dict, run_id: Optional[str] = None
    ):
        """
        Log comparison report to MLflow as artifacts.

        Parameters
        ----------
        model_name : str
            Model name
        comparison_result : dict
            Comparison result dictionary
        run_id : str, optional
            Run ID to log to. If None, creates a new run.
        """
        # Check if we're already in an active run
        active_run = mlflow.active_run()

        # If we're already in an active run, log directly to it
        # (This is the normal case during training)
        if active_run:
            # Log directly to the current active run
            mlflow.set_tag("comparison_type", "model_registry")
            mlflow.set_tag("model_name", model_name)
            self._log_comparison_artifacts(comparison_result)
        else:
            # No active run, create a new one
            # Note: We don't use nested runs as they're not supported by all MLflow backends
            with mlflow.start_run(
                run_name=f"model_comparison_{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            ):
                mlflow.set_tag("comparison_type", "model_registry")
                mlflow.set_tag("model_name", model_name)
                self._log_comparison_artifacts(comparison_result)

    def _log_comparison_artifacts(self, comparison_result: Dict):
        """Log comparison artifacts to MLflow."""
        files_to_cleanup = []

        try:
            # Save JSON report
            json_path = tempfile.mktemp(suffix=".json")
            files_to_cleanup.append(json_path)
            with open(json_path, "w") as f:
                json.dump(comparison_result, f, indent=2, default=str)
            mlflow.log_artifact(json_path, "comparison")

            # Save HTML report
            if "html_report" in comparison_result:
                html_path = tempfile.mktemp(suffix=".html")
                files_to_cleanup.append(html_path)
                with open(html_path, "w") as f:
                    f.write(comparison_result["html_report"])
                mlflow.log_artifact(html_path, "comparison")

            # Log visualization plots
            if "visualizations" in comparison_result:
                for plot_name, plot_path in comparison_result["visualizations"].items():
                    if os.path.exists(plot_path):
                        mlflow.log_artifact(plot_path, "comparison/plots")
                        files_to_cleanup.append(plot_path)
        finally:
            # Cleanup temporary files
            for file_path in files_to_cleanup:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    logger.warning(f"Could not remove temporary file {file_path}: {e}")

    def evaluate_promotion_candidate(
        self, model_name: str, candidate_version: int, target_stage: str = "Production"
    ) -> Dict:
        """
        Evaluate if a model version should be promoted based on configured rules.

        Parameters
        ----------
        model_name : str
            Model name
        candidate_version : int
            Version to evaluate for promotion
        target_stage : str
            Target stage (default: Production)

        Returns
        -------
        dict
            Evaluation result with promotion decision and reasoning
        """
        logger.info(
            f"Evaluating promotion candidate: {model_name} version {candidate_version} to {target_stage}"
        )

        # Get candidate version metrics
        try:
            candidate_mv = self.client.get_model_version(model_name, candidate_version)
            candidate_run = self.client.get_run(candidate_mv.run_id)
            candidate_metrics = candidate_run.data.metrics
        except Exception as e:
            logger.error(f"Could not fetch candidate version: {e}")
            return {
                "promote": False,
                "reason": f"Error fetching candidate version: {e}",
            }

        # Compare against the stage(s) specified in auto_promotion.comparison_stage config
        # If multiple stages, find the best performing model across all stages
        # Use alias instead of deprecated stage
        current_prod = None
        best_prod_score = None
        best_prod_stage = None

        promotion_rules = self.promotion_config.get("rules", {})
        primary_metric = promotion_rules.get("primary_metric", "f1_score")

        # Check all comparison stages and find the best one
        for comparison_stage in self.comparison_stages:
            try:
                # Convert stage name to lowercase alias (e.g., "Production" -> "production")
                comparison_alias = comparison_stage.lower()
                try:
                    stage_model_version = self.client.get_model_version_by_alias(
                        model_name, comparison_alias
                    )
                    # Get metrics for this stage's model
                    stage_run = self.client.get_run(stage_model_version.run_id)
                    stage_metrics = stage_run.data.metrics

                    # Check if this stage's model is better than current best
                    if primary_metric in stage_metrics:
                        stage_score = stage_metrics[primary_metric]
                        if best_prod_score is None or stage_score > best_prod_score:
                            best_prod_score = stage_score
                            best_prod_stage = comparison_stage
                            current_prod = stage_model_version
                except Exception:
                    # No model with this alias - skip this stage (only use fallback for single stage for backward compatibility)
                    if len(self.comparison_stages) == 1:
                        # Fallback: search for latest version if alias doesn't exist (backward compatibility)
                        try:
                            comparison_versions = self.client.search_model_versions(
                                f"name='{model_name}'",
                                max_results=1,
                                order_by=["version_number DESC"],
                            )
                            if comparison_versions:
                                stage_model_version = comparison_versions[0]
                                stage_run = self.client.get_run(
                                    stage_model_version.run_id
                                )
                                stage_metrics = stage_run.data.metrics

                                if primary_metric in stage_metrics:
                                    stage_score = stage_metrics[primary_metric]
                                    if (
                                        best_prod_score is None
                                        or stage_score > best_prod_score
                                    ):
                                        best_prod_score = stage_score
                                        best_prod_stage = comparison_stage
                                        current_prod = stage_model_version
                        except Exception:
                            logger.debug(
                                f"No model found for comparison stage: {comparison_stage}"
                            )
                    else:
                        logger.debug(
                            f"No model found for comparison stage: {comparison_stage} (skipping)"
                        )
            except Exception as e:
                logger.debug(f"Error checking comparison stage {comparison_stage}: {e}")
                continue

        if len(self.comparison_stages) > 1 and current_prod:
            logger.info(
                f"Comparing against best model from stages {self.comparison_stages}: "
                f"{best_prod_stage} (score: {best_prod_score:.4f})"
            )

        evaluation = {
            "candidate_version": candidate_version,
            "target_stage": target_stage,
            "promote": False,
            "reason": "",
            "metrics_comparison": {},
        }

        # Check promotion rules (primary_metric already retrieved above)
        min_threshold = promotion_rules.get("min_threshold", {})
        improvement_threshold = promotion_rules.get("improvement_threshold_pct", 0)

        # Check minimum threshold
        if primary_metric in candidate_metrics:
            candidate_score = candidate_metrics[primary_metric]
            min_score = min_threshold.get(primary_metric, 0)

            if candidate_score < min_score:
                evaluation["promote"] = False
                evaluation["reason"] = (
                    f"Candidate {primary_metric} ({candidate_score:.4f}) "
                    f"below minimum threshold ({min_score:.4f})"
                )
                return evaluation

        # Compare with current comparison stage version (if exists)
        if current_prod:
            try:
                prod_run = self.client.get_run(current_prod.run_id)
                prod_metrics = prod_run.data.metrics

                if (
                    primary_metric in candidate_metrics
                    and primary_metric in prod_metrics
                ):
                    candidate_score = candidate_metrics[primary_metric]
                    prod_score = prod_metrics[primary_metric]

                    improvement_pct = (
                        (candidate_score - prod_score) / prod_score
                    ) * 100

                    # Build comparison description
                    if len(self.comparison_stages) > 1:
                        comparison_desc = f"best model from {self.comparison_stages} ({best_prod_stage})"
                    else:
                        comparison_desc = self.comparison_stage

                    evaluation["metrics_comparison"] = {
                        "candidate": {primary_metric: candidate_score},
                        f"current_{best_prod_stage.lower() if best_prod_stage else self.comparison_stage.lower()}": {
                            primary_metric: prod_score
                        },
                        "comparison_stages": self.comparison_stages,
                        "best_comparison_stage": best_prod_stage,
                        "improvement_pct": improvement_pct,
                    }

                    if improvement_pct >= improvement_threshold:
                        evaluation["promote"] = True
                        evaluation["reason"] = (
                            f"Candidate outperforms {comparison_desc} by {improvement_pct:.2f}% "
                            f"(threshold: {improvement_threshold}%)"
                        )
                    else:
                        evaluation["promote"] = False
                        evaluation["reason"] = (
                            f"Candidate improvement ({improvement_pct:.2f}%) "
                            f"below threshold ({improvement_threshold}%)"
                        )
                else:
                    evaluation["promote"] = False
                    evaluation["reason"] = (
                        f"Primary metric '{primary_metric}' not found in both versions"
                    )

            except Exception as e:
                comparison_desc = (
                    f"{self.comparison_stages}"
                    if len(self.comparison_stages) > 1
                    else self.comparison_stage
                )
                logger.warning(f"Error comparing with {comparison_desc}: {e}")
                evaluation["promote"] = False
                evaluation["reason"] = f"Error comparing with {comparison_desc}: {e}"
        else:
            # No current comparison stage version(s) - promote if meets minimum threshold
            if primary_metric in candidate_metrics:
                candidate_score = candidate_metrics[primary_metric]
                min_score = min_threshold.get(primary_metric, 0)

                comparison_desc = (
                    f"{self.comparison_stages}"
                    if len(self.comparison_stages) > 1
                    else self.comparison_stage
                )

                if candidate_score >= min_score:
                    evaluation["promote"] = True
                    evaluation["reason"] = (
                        f"No current {comparison_desc} version(s). "
                        f"Candidate meets minimum threshold ({candidate_score:.4f} >= {min_score:.4f})"
                    )
                else:
                    evaluation["promote"] = False
                    evaluation["reason"] = (
                        f"Candidate {primary_metric} ({candidate_score:.4f}) "
                        f"below minimum threshold ({min_score:.4f})"
                    )

        return evaluation

    def auto_promote_model(
        self,
        model_name: str,
        candidate_version: int,
        target_stage: str = "Production",
        rollback_on_failure: bool = True,
    ) -> Dict:
        """
        Automatically promote a model version if it meets promotion criteria.

        Parameters
        ----------
        model_name : str
            Model name
        candidate_version : int
            Version to promote
        target_stage : str
            Target stage (default: Production)
        rollback_on_failure : bool
            If True, rollback promotion if new model performs worse

        Returns
        -------
        dict
            Promotion result with status and details
        """
        logger.info(
            f"Attempting auto-promotion: {model_name} version {candidate_version} to {target_stage}"
        )

        # Evaluate promotion candidate
        evaluation = self.evaluate_promotion_candidate(
            model_name, candidate_version, target_stage
        )

        result = {
            "model_name": model_name,
            "candidate_version": candidate_version,
            "target_stage": target_stage,
            "promoted": False,
            "evaluation": evaluation,
            "timestamp": datetime.now().isoformat(),
        }

        if not evaluation["promote"]:
            result["reason"] = evaluation["reason"]
            logger.info(f"Promotion rejected: {evaluation['reason']}")
            return result

        # Perform promotion
        try:
            # Get current version with target stage (if exists) for potential rollback
            previous_prod_version = None
            try:
                # Search for versions in the target stage
                all_versions = self.client.search_model_versions(f"name='{model_name}'")
                for mv in all_versions:
                    if mv.current_stage == target_stage:
                        previous_prod_version = mv.version
                        break
            except Exception:
                # No existing version in this stage
                pass

            # Transition stage (this is the method that shows up in MLflow UI)
            # Note: transition_model_version_stage is deprecated but still functional
            # and is required for stage visibility in MLflow UI (including DagsHub)
            self.client.transition_model_version_stage(
                name=model_name,
                version=str(candidate_version),
                stage=target_stage,
                archive_existing_versions=False,  # Don't auto-archive other versions
            )

            # Also set alias for modern MLflow compatibility
            target_alias = target_stage.lower()
            try:
                self.client.set_registered_model_alias(
                    name=model_name, alias=target_alias, version=str(candidate_version)
                )
            except Exception as e:
                logger.debug(f"Could not set alias (non-critical): {e}")

            # Archive previous version if it was in the same stage
            if previous_prod_version and str(previous_prod_version) != str(
                candidate_version
            ):
                try:
                    self.client.transition_model_version_stage(
                        name=model_name,
                        version=str(previous_prod_version),
                        stage="Archived",
                    )
                    result["previous_version_archived"] = previous_prod_version
                except Exception as e:
                    logger.warning(f"Could not archive previous version: {e}")

            result["promoted"] = True
            result["reason"] = "Promotion successful"
            logger.info(
                f"Successfully promoted {model_name} version {candidate_version} to {target_stage}"
            )

            # Log promotion event
            self._log_promotion_event(result)

        except Exception as e:
            result["promoted"] = False
            result["reason"] = f"Promotion failed: {e}"
            logger.error(f"Promotion failed: {e}")

        return result

    def _log_promotion_event(self, promotion_result: Dict):
        """Log promotion event to MLflow."""
        try:
            # Check if there's an active run - if so, log to it instead of creating a new one
            active_run = mlflow.active_run()

            if active_run:
                # Log promotion info as tags to the current active run
                mlflow.set_tag("promotion_event", "true")
                mlflow.set_tag(
                    "promoted_version", str(promotion_result["candidate_version"])
                )
                mlflow.set_tag(
                    "promotion_target_stage", promotion_result["target_stage"]
                )
                mlflow.set_tag(
                    "promotion_status",
                    "success" if promotion_result.get("promoted") else "failed",
                )

                # Log promotion details as JSON artifact
                json_path = tempfile.mktemp(suffix=".json")
                try:
                    with open(json_path, "w") as f:
                        json.dump(promotion_result, f, indent=2, default=str)
                    mlflow.log_artifact(json_path, "promotion")
                finally:
                    if os.path.exists(json_path):
                        os.remove(json_path)
            else:
                # No active run, create a new one
                with mlflow.start_run(
                    run_name=f"promotion_{promotion_result['model_name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                ):
                    mlflow.set_tag("event_type", "model_promotion")
                    mlflow.set_tag("model_name", promotion_result["model_name"])
                    mlflow.set_tag(
                        "promoted_version", str(promotion_result["candidate_version"])
                    )
                    mlflow.set_tag("target_stage", promotion_result["target_stage"])

                    # Log promotion details as JSON
                    json_path = tempfile.mktemp(suffix=".json")
                    try:
                        with open(json_path, "w") as f:
                            json.dump(promotion_result, f, indent=2, default=str)
                        mlflow.log_artifact(json_path, "promotion")
                    finally:
                        if os.path.exists(json_path):
                            os.remove(json_path)
        except Exception as e:
            logger.warning(f"Could not log promotion event: {e}")
