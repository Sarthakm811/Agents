# src/utils/validators.py
"""
Simple validation helpers used across the scaffold.
"""

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


def validate_non_empty_string(value: Any, name: str) -> str:
    """Ensure *value* is a non‑empty string, otherwise raise ``ValueError``.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non‑empty string")
    return value.strip()


def validate_callable(obj: Any, name: str) -> Callable:
    """Validate that *obj* is callable.
    """
    if not callable(obj):
        raise ValueError(f"{name} must be callable")
    return obj


def safe_execute(func: Callable, *args, **kwargs) -> Any:
    """Execute *func* with *args*/**kwargs* and log any exception.
    Returns ``None`` on error.
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error("Error executing %s: %s", func.__name__, e)
        return None
