# src/utils/config.py
"""
Utility helpers for loading configuration files (YAML/JSON).
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

import yaml

logger = logging.getLogger(__name__)


def load_yaml_config(file_path: str | os.PathLike) -> Dict[str, Any]:
    """Load a YAML configuration file and return a dictionary.
    
    Parameters
    ----------
    file_path: str or Path
        Path to the YAML file.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    logger.debug("Loaded YAML config %s (keys: %s)", file_path, list(data.keys()))
    return data or {}


def load_json_config(file_path: str | os.PathLike) -> Dict[str, Any]:
    """Load a JSON configuration file.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    logger.debug("Loaded JSON config %s (keys: %s)", file_path, list(data.keys()))
    return data
