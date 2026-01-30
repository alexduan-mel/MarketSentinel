import os
import yaml
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def load_yaml_config(file_path: str) -> Dict[str, Any]:
    """Load and parse a YAML configuration file."""
    try:
        if not os.path.exists(file_path):
            logger.warning(f"Config file not found: {file_path}")
            return {}
        
        with open(file_path, 'r') as f:
            config = yaml.safe_load(f)
            logger.info(f"Loaded config from: {file_path}")
            return config or {}
    except Exception as e:
        logger.error(f"Error loading config from {file_path}: {e}")
        return {}


def load_adapters_config(config_path: str = "config/adapters.yaml") -> Dict[str, Any]:
    """Load adapter configuration."""
    return load_yaml_config(config_path)


def load_watchlist_config(config_path: str = "config/watchlist.yaml") -> Dict[str, Any]:
    """Load watchlist configuration."""
    return load_yaml_config(config_path)
