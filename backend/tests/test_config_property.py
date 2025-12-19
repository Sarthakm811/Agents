"""
Property-based tests for API configuration security.

**Feature: ai-research-agents, Property 4: API key security**
**Validates: Requirements 3.3**
"""

import io
import logging
import os
import sys
from typing import Optional

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from utils.config import APIConfig, ConfigManager


# Strategy for generating realistic API keys
@st.composite
def api_key_strategy(draw):
    """Generate realistic API key strings."""
    # API keys are typically alphanumeric with some special chars
    prefix = draw(st.sampled_from(["sk-", "key-", "api-", "token-", ""]))
    body = draw(st.from_regex(r'[a-zA-Z0-9]{20,50}', fullmatch=True))
    return prefix + body


# Strategy for generating API config with at least one key set
@st.composite
def api_config_with_keys_strategy(draw):
    """Generate APIConfig with at least one API key set."""
    openai_key = draw(st.one_of(st.none(), api_key_strategy()))
    anthropic_key = draw(st.one_of(st.none(), api_key_strategy()))
    semantic_scholar_key = draw(st.one_of(st.none(), api_key_strategy()))
    
    # Ensure at least one key is set
    assume(openai_key is not None or anthropic_key is not None or semantic_scholar_key is not None)
    
    llm_provider = draw(st.sampled_from(["openai", "anthropic"]))
    llm_model = draw(st.sampled_from(["gpt-4", "gpt-3.5-turbo", "claude-3-sonnet", "claude-3-opus"]))
    
    return APIConfig(
        openai_api_key=openai_key,
        anthropic_api_key=anthropic_key,
        semantic_scholar_api_key=semantic_scholar_key,
        llm_provider=llm_provider,
        llm_model=llm_model
    )


def get_all_api_keys(config: APIConfig) -> list[str]:
    """Extract all non-None API keys from config."""
    keys = []
    if config.openai_api_key:
        keys.append(config.openai_api_key)
    if config.anthropic_api_key:
        keys.append(config.anthropic_api_key)
    if config.semantic_scholar_api_key:
        keys.append(config.semantic_scholar_api_key)
    return keys


def contains_any_key(text: str, keys: list[str]) -> Optional[str]:
    """Check if text contains any of the API keys. Returns the found key or None."""
    for key in keys:
        if key and key in text:
            return key
    return None


class TestAPIKeySecurityProperty:
    """
    **Feature: ai-research-agents, Property 4: API key security**
    
    *For any* error response, log output, or API response, the content SHALL NOT 
    contain any substring matching configured API key values.
    
    **Validates: Requirements 3.3**
    """

    @given(config=api_config_with_keys_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_safe_config_summary_does_not_expose_keys(self, config):
        """
        Property: Safe config summary never contains raw API keys.
        
        **Feature: ai-research-agents, Property 4: API key security**
        **Validates: Requirements 3.3**
        """
        summary = ConfigManager.get_safe_config_summary(config)
        summary_str = str(summary)
        
        keys = get_all_api_keys(config)
        found_key = contains_any_key(summary_str, keys)
        
        assert found_key is None, (
            f"API key was exposed in safe config summary. "
            f"Found key: {found_key[:8]}... in summary"
        )

    @given(config=api_config_with_keys_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_masked_key_does_not_expose_full_key(self, config):
        """
        Property: Masked API keys never contain the full original key.
        
        **Feature: ai-research-agents, Property 4: API key security**
        **Validates: Requirements 3.3**
        """
        keys = get_all_api_keys(config)
        
        for key in keys:
            masked = ConfigManager.mask_api_key(key)
            
            # The masked version should not equal the original
            assert masked != key, (
                f"Masked key equals original key: {key[:8]}..."
            )
            
            # For keys longer than 8 chars, the middle portion should be hidden
            if len(key) > 8:
                # The middle portion (chars 4 to -4) should not appear in masked
                middle = key[4:-4]
                assert middle not in masked, (
                    f"Middle portion of key exposed in masked version"
                )

    @given(config=api_config_with_keys_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_validation_warnings_do_not_expose_keys(self, config):
        """
        Property: Validation warnings never contain raw API keys.
        
        **Feature: ai-research-agents, Property 4: API key security**
        **Validates: Requirements 3.3**
        """
        # Capture log output
        log_capture = io.StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.DEBUG)
        
        logger = logging.getLogger('utils.config')
        original_handlers = logger.handlers[:]
        logger.handlers = [handler]
        logger.setLevel(logging.DEBUG)
        
        try:
            warnings = ConfigManager.validate_config(config)
            warnings_str = " ".join(warnings)
            log_output = log_capture.getvalue()
            
            keys = get_all_api_keys(config)
            
            # Check warnings don't contain keys
            found_in_warnings = contains_any_key(warnings_str, keys)
            assert found_in_warnings is None, (
                f"API key was exposed in validation warnings"
            )
            
            # Check log output doesn't contain keys
            found_in_logs = contains_any_key(log_output, keys)
            assert found_in_logs is None, (
                f"API key was exposed in log output"
            )
        finally:
            logger.handlers = original_handlers

    @given(key=api_key_strategy())
    @settings(max_examples=100)
    def test_mask_api_key_always_masks(self, key):
        """
        Property: mask_api_key always returns a masked version for non-empty keys.
        
        **Feature: ai-research-agents, Property 4: API key security**
        **Validates: Requirements 3.3**
        """
        masked = ConfigManager.mask_api_key(key)
        
        # Should never return the original key
        assert masked != key, "Masked key should not equal original"
        
        # Should contain masking characters
        assert "..." in masked or "****" in masked or masked == "<not set>", (
            f"Masked key should contain masking pattern, got: {masked}"
        )

    @given(config=api_config_with_keys_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_available_services_does_not_expose_keys(self, config):
        """
        Property: Available services list never contains API keys.
        
        **Feature: ai-research-agents, Property 4: API key security**
        **Validates: Requirements 3.3**
        """
        services = ConfigManager.get_available_services(config)
        services_str = " ".join(services)
        
        keys = get_all_api_keys(config)
        found_key = contains_any_key(services_str, keys)
        
        assert found_key is None, (
            f"API key was exposed in available services list"
        )
