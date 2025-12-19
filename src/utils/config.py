# src/utils/config.py
"""
Utility helpers for loading configuration files (YAML/JSON) and API configuration management.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class APIConfig:
    """Configuration for external API services.
    
    Attributes
    ----------
    openai_api_key : Optional[str]
        API key for OpenAI services.
    anthropic_api_key : Optional[str]
        API key for Anthropic services.
    semantic_scholar_api_key : Optional[str]
        API key for Semantic Scholar API.
    llm_provider : str
        The LLM provider to use ("openai" or "anthropic").
    llm_model : str
        The specific model to use (e.g., "gpt-4" or "claude-3-sonnet").
    """
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    semantic_scholar_api_key: Optional[str] = None
    llm_provider: str = "openai"
    llm_model: str = "gpt-4"


class ConfigManager:
    """Manages API configuration loading and validation.
    
    This class handles loading API keys from environment variables,
    validating the configuration, and determining available services.
    """
    
    # Environment variable names for API keys
    ENV_OPENAI_API_KEY = "OPENAI_API_KEY"
    ENV_ANTHROPIC_API_KEY = "ANTHROPIC_API_KEY"
    ENV_SEMANTIC_SCHOLAR_API_KEY = "SEMANTIC_SCHOLAR_API_KEY"
    ENV_LLM_PROVIDER = "LLM_PROVIDER"
    ENV_LLM_MODEL = "LLM_MODEL"
    
    @staticmethod
    def load_from_env() -> APIConfig:
        """Load API configuration from environment variables.
        
        Returns
        -------
        APIConfig
            Configuration object populated from environment variables.
        """
        openai_key = os.environ.get(ConfigManager.ENV_OPENAI_API_KEY)
        anthropic_key = os.environ.get(ConfigManager.ENV_ANTHROPIC_API_KEY)
        semantic_scholar_key = os.environ.get(ConfigManager.ENV_SEMANTIC_SCHOLAR_API_KEY)
        llm_provider = os.environ.get(ConfigManager.ENV_LLM_PROVIDER, "openai")
        llm_model = os.environ.get(ConfigManager.ENV_LLM_MODEL, "gpt-4")
        
        config = APIConfig(
            openai_api_key=openai_key,
            anthropic_api_key=anthropic_key,
            semantic_scholar_api_key=semantic_scholar_key,
            llm_provider=llm_provider,
            llm_model=llm_model
        )
        
        return config
    
    @staticmethod
    def validate_config(config: APIConfig) -> List[str]:
        """Validate the configuration and return warnings for missing keys.
        
        Parameters
        ----------
        config : APIConfig
            The configuration to validate.
            
        Returns
        -------
        List[str]
            List of warning messages for missing or invalid configuration.
        """
        warnings: List[str] = []
        
        # Check LLM provider configuration
        if config.llm_provider == "openai" and not config.openai_api_key:
            warnings.append("OPENAI_API_KEY is missing but llm_provider is set to 'openai'. OpenAI services will be disabled.")
            logger.warning("OPENAI_API_KEY is missing but llm_provider is set to 'openai'. OpenAI services will be disabled.")
        
        if config.llm_provider == "anthropic" and not config.anthropic_api_key:
            warnings.append("ANTHROPIC_API_KEY is missing but llm_provider is set to 'anthropic'. Anthropic services will be disabled.")
            logger.warning("ANTHROPIC_API_KEY is missing but llm_provider is set to 'anthropic'. Anthropic services will be disabled.")
        
        # Check optional services
        if not config.semantic_scholar_api_key:
            warnings.append("SEMANTIC_SCHOLAR_API_KEY is missing. Semantic Scholar API will use unauthenticated access with lower rate limits.")
            logger.warning("SEMANTIC_SCHOLAR_API_KEY is missing. Semantic Scholar API will use unauthenticated access with lower rate limits.")
        
        # Validate llm_provider value
        if config.llm_provider not in ("openai", "anthropic"):
            warnings.append(f"Invalid llm_provider '{config.llm_provider}'. Must be 'openai' or 'anthropic'.")
            logger.warning(f"Invalid llm_provider '{config.llm_provider}'. Must be 'openai' or 'anthropic'.")
        
        return warnings
    
    @staticmethod
    def get_available_services(config: APIConfig) -> List[str]:
        """Determine which services are available based on configuration.
        
        Parameters
        ----------
        config : APIConfig
            The configuration to check.
            
        Returns
        -------
        List[str]
            List of available service names.
        """
        services: List[str] = []
        
        # arXiv is always available (no API key required)
        services.append("arxiv")
        
        # Semantic Scholar is always available but with different rate limits
        services.append("semantic_scholar")
        
        # LLM services depend on API keys
        if config.openai_api_key:
            services.append("openai")
        
        if config.anthropic_api_key:
            services.append("anthropic")
        
        return services
    
    @staticmethod
    def mask_api_key(key: Optional[str]) -> str:
        """Mask an API key for safe logging.
        
        Parameters
        ----------
        key : Optional[str]
            The API key to mask.
            
        Returns
        -------
        str
            Masked version of the key showing only first 4 and last 4 characters.
        """
        if not key:
            return "<not set>"
        if len(key) <= 8:
            return "****"
        return f"{key[:4]}...{key[-4:]}"
    
    @staticmethod
    def get_safe_config_summary(config: APIConfig) -> Dict[str, Any]:
        """Get a safe summary of the configuration without exposing API keys.
        
        Parameters
        ----------
        config : APIConfig
            The configuration to summarize.
            
        Returns
        -------
        Dict[str, Any]
            Dictionary with masked API keys and other config values.
        """
        return {
            "openai_api_key": ConfigManager.mask_api_key(config.openai_api_key),
            "anthropic_api_key": ConfigManager.mask_api_key(config.anthropic_api_key),
            "semantic_scholar_api_key": ConfigManager.mask_api_key(config.semantic_scholar_api_key),
            "llm_provider": config.llm_provider,
            "llm_model": config.llm_model,
            "available_services": ConfigManager.get_available_services(config)
        }


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
