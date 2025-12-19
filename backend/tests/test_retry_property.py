"""
Property-based tests for retry behavior on failure.

**Feature: ai-research-agents, Property 3: Retry behavior on failure**
**Validates: Requirements 1.4**
"""

import asyncio
import os
import sys
import time
from typing import List, Tuple
from unittest.mock import AsyncMock, MagicMock

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from tools.orchestrator import retry_with_backoff, APIError


class TestRetryBehaviorProperty:
    """
    **Feature: ai-research-agents, Property 3: Retry behavior on failure**
    
    *For any* API request that fails, the system SHALL retry exactly 3 times 
    with exponential backoff (delays of 1s, 2s, 4s) before returning an error.
    
    **Validates: Requirements 1.4**
    """

    def test_retry_decorator_retries_exactly_3_times(self):
        """
        Property: The retry decorator SHALL retry exactly 3 times before raising.
        
        **Feature: ai-research-agents, Property 3: Retry behavior on failure**
        **Validates: Requirements 1.4**
        """
        call_count = 0
        
        @retry_with_backoff(
            max_attempts=3,
            backoff_base=2.0,
            initial_delay=0.01,  # Use small delays for testing
            exceptions=(ValueError,)
        )
        async def failing_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Test error")
        
        async def run_test():
            nonlocal call_count
            call_count = 0
            with pytest.raises(ValueError):
                await failing_function()
            return call_count
        
        result = asyncio.run(run_test())
        assert result == 3, f"Expected 3 attempts, got {result}"

    @given(
        max_attempts=st.integers(min_value=1, max_value=5),
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_retry_decorator_respects_max_attempts(self, max_attempts: int):
        """
        Property: The retry decorator SHALL respect the configured max_attempts.
        
        **Feature: ai-research-agents, Property 3: Retry behavior on failure**
        **Validates: Requirements 1.4**
        """
        call_count = 0
        
        @retry_with_backoff(
            max_attempts=max_attempts,
            backoff_base=2.0,
            initial_delay=0.001,  # Very small delay for testing
            exceptions=(ValueError,)
        )
        async def failing_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Test error")
        
        async def run_test():
            nonlocal call_count
            call_count = 0
            with pytest.raises(ValueError):
                await failing_function()
            return call_count
        
        result = asyncio.run(run_test())
        assert result == max_attempts, (
            f"Expected {max_attempts} attempts, got {result}"
        )

    def test_exponential_backoff_delays(self):
        """
        Property: Retry delays SHALL follow exponential backoff pattern (1s, 2s, 4s).
        
        **Feature: ai-research-agents, Property 3: Retry behavior on failure**
        **Validates: Requirements 1.4**
        """
        delays: List[float] = []
        
        def on_retry(attempt: int, exception: Exception, delay: float):
            delays.append(delay)
        
        @retry_with_backoff(
            max_attempts=3,
            backoff_base=2.0,
            initial_delay=1.0,
            exceptions=(ValueError,),
            on_retry=on_retry
        )
        async def failing_function():
            raise ValueError("Test error")
        
        async def run_test():
            with pytest.raises(ValueError):
                await failing_function()
        
        asyncio.run(run_test())
        
        # Should have 2 delays (between attempts 1-2 and 2-3)
        assert len(delays) == 2, f"Expected 2 delays, got {len(delays)}"
        
        # Check exponential backoff: 1s, 2s (initial_delay * backoff_base^attempt)
        expected_delays = [1.0, 2.0]  # 1*2^0, 1*2^1
        for i, (actual, expected) in enumerate(zip(delays, expected_delays)):
            assert abs(actual - expected) < 0.01, (
                f"Delay {i} was {actual}, expected {expected}"
            )

    def test_successful_call_does_not_retry(self):
        """
        Property: A successful call SHALL NOT trigger any retries.
        
        **Feature: ai-research-agents, Property 3: Retry behavior on failure**
        **Validates: Requirements 1.4**
        """
        call_count = 0
        
        @retry_with_backoff(
            max_attempts=3,
            backoff_base=2.0,
            initial_delay=0.01,
            exceptions=(ValueError,)
        )
        async def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"
        
        async def run_test():
            nonlocal call_count
            call_count = 0
            result = await successful_function()
            return result, call_count
        
        result, count = asyncio.run(run_test())
        assert result == "success"
        assert count == 1, f"Expected 1 call, got {count}"

    def test_retry_succeeds_on_later_attempt(self):
        """
        Property: If a call succeeds on a retry attempt, it SHALL return the result.
        
        **Feature: ai-research-agents, Property 3: Retry behavior on failure**
        **Validates: Requirements 1.4**
        """
        call_count = 0
        
        @retry_with_backoff(
            max_attempts=3,
            backoff_base=2.0,
            initial_delay=0.01,
            exceptions=(ValueError,)
        )
        async def eventually_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Not yet")
            return "success"
        
        async def run_test():
            nonlocal call_count
            call_count = 0
            result = await eventually_succeeds()
            return result, call_count
        
        result, count = asyncio.run(run_test())
        assert result == "success"
        assert count == 3, f"Expected 3 calls, got {count}"

    def test_retry_only_catches_specified_exceptions(self):
        """
        Property: The retry decorator SHALL only catch specified exception types.
        
        **Feature: ai-research-agents, Property 3: Retry behavior on failure**
        **Validates: Requirements 1.4**
        """
        call_count = 0
        
        @retry_with_backoff(
            max_attempts=3,
            backoff_base=2.0,
            initial_delay=0.01,
            exceptions=(ValueError,)  # Only catch ValueError
        )
        async def raises_type_error():
            nonlocal call_count
            call_count += 1
            raise TypeError("Different error")
        
        async def run_test():
            nonlocal call_count
            call_count = 0
            with pytest.raises(TypeError):
                await raises_type_error()
            return call_count
        
        count = asyncio.run(run_test())
        # Should only be called once since TypeError is not in exceptions
        assert count == 1, f"Expected 1 call (no retry), got {count}"

    def test_retry_with_api_error(self):
        """
        Property: The retry decorator SHALL work with APIError exceptions.
        
        **Feature: ai-research-agents, Property 3: Retry behavior on failure**
        **Validates: Requirements 1.4**
        """
        call_count = 0
        
        @retry_with_backoff(
            max_attempts=3,
            backoff_base=2.0,
            initial_delay=0.01,
            exceptions=(APIError,)
        )
        async def api_failing_function():
            nonlocal call_count
            call_count += 1
            raise APIError("test_service", 500, "Server error")
        
        async def run_test():
            nonlocal call_count
            call_count = 0
            with pytest.raises(APIError):
                await api_failing_function()
            return call_count
        
        count = asyncio.run(run_test())
        assert count == 3, f"Expected 3 attempts, got {count}"

    def test_retry_config_stored_on_wrapper(self):
        """
        Property: The retry configuration SHALL be stored on the wrapper function.
        
        **Feature: ai-research-agents, Property 3: Retry behavior on failure**
        **Validates: Requirements 1.4**
        """
        @retry_with_backoff(
            max_attempts=3,
            backoff_base=2.0,
            initial_delay=1.0,
            exceptions=(ValueError,)
        )
        async def test_function():
            pass
        
        assert hasattr(test_function, '_retry_config')
        config = test_function._retry_config
        assert config['max_attempts'] == 3
        assert config['backoff_base'] == 2.0
        assert config['initial_delay'] == 1.0
        assert ValueError in config['exceptions']

    @given(
        backoff_base=st.floats(min_value=1.5, max_value=3.0, allow_nan=False, allow_infinity=False),
        initial_delay=st.floats(min_value=0.001, max_value=0.01, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    def test_backoff_delays_follow_exponential_pattern(
        self, backoff_base: float, initial_delay: float
    ):
        """
        Property: Retry delays SHALL follow the pattern initial_delay * backoff_base^attempt.
        
        **Feature: ai-research-agents, Property 3: Retry behavior on failure**
        **Validates: Requirements 1.4**
        """
        delays: List[float] = []
        
        def on_retry(attempt: int, exception: Exception, delay: float):
            delays.append(delay)
        
        @retry_with_backoff(
            max_attempts=4,
            backoff_base=backoff_base,
            initial_delay=initial_delay,
            exceptions=(ValueError,),
            on_retry=on_retry
        )
        async def failing_function():
            raise ValueError("Test error")
        
        async def run_test():
            with pytest.raises(ValueError):
                await failing_function()
        
        asyncio.run(run_test())
        
        # Should have 3 delays (between 4 attempts)
        assert len(delays) == 3
        
        # Check exponential pattern
        for i, actual_delay in enumerate(delays):
            expected_delay = initial_delay * (backoff_base ** i)
            assert abs(actual_delay - expected_delay) < 0.0001, (
                f"Delay {i} was {actual_delay}, expected {expected_delay}"
            )

    def test_default_retry_configuration_matches_spec(self):
        """
        Property: Default retry configuration SHALL be 3 attempts with 1s, 2s, 4s delays.
        
        This validates that the arXiv and Semantic Scholar search methods use
        the correct retry configuration as specified in Requirements 1.4.
        
        **Feature: ai-research-agents, Property 3: Retry behavior on failure**
        **Validates: Requirements 1.4**
        """
        from tools.orchestrator import AutonomousToolOrchestrator
        
        orchestrator = AutonomousToolOrchestrator()
        
        # Check arXiv retry config
        arxiv_config = orchestrator._search_arxiv_with_retry._retry_config
        assert arxiv_config['max_attempts'] == 3
        assert arxiv_config['backoff_base'] == 2.0
        assert arxiv_config['initial_delay'] == 1.0
        
        # Check Semantic Scholar retry config
        ss_config = orchestrator._search_semantic_scholar_with_retry._retry_config
        assert ss_config['max_attempts'] == 3
        assert ss_config['backoff_base'] == 2.0
        assert ss_config['initial_delay'] == 1.0
