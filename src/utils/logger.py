# src/utils/logger.py
"""
Simple logger configuration helper.
"""

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    """Configure the root logger with a stream handler.
    
    Parameters
    ----------
    level: str, optional
        Logging level name (e.g., "DEBUG", "INFO"). Defaults to "INFO".
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )
    logging.getLogger().info("Logging configured at %s level", level.upper())
