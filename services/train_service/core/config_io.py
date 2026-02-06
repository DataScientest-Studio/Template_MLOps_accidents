"""
Load/save model config YAML and ensure default config exists on first run.
Config structure must match src/config/model_config.yaml.
"""

import logging
import shutil
from pathlib import Path
from typing import Any, Dict

import yaml

logger = logging.getLogger(__name__)

DEFAULT_REPO_CONFIG_PATH = "src/config/model_config.yaml"


def load_config(path: str) -> Dict[str, Any]:
    """Load config from a YAML file. Returns dict (structure matches model_config.yaml)."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_config(path: str, config: Dict[str, Any]) -> None:
    """Write config dict to a YAML file."""
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(
            config, f, default_flow_style=False, allow_unicode=True, sort_keys=False
        )


def ensure_config_exists(
    active_path: str, default_path: str = DEFAULT_REPO_CONFIG_PATH
) -> None:
    """
    If the active config file does not exist, copy from the default repo config.
    Call on first run so the writable config (e.g. /app/data/model_config.yaml) is seeded.
    """
    if Path(active_path).exists():
        return
    if not Path(default_path).exists():
        logger.warning(
            "Active config path %s does not exist and default %s not found; config must be created manually.",
            active_path,
            default_path,
        )
        return
    try:
        shutil.copy2(default_path, active_path)
        logger.info(
            "Copied default config from %s to %s (first run).",
            default_path,
            active_path,
        )
    except OSError as e:
        logger.warning("Could not copy default config to %s: %s", active_path, e)
