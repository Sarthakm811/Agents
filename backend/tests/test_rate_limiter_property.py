"""
Property-based tests for rate limiting enforcement.

**Feature: ai-research-agents, Property 8: Rate limiting enforcement**
**Validates: Requirements 6.1**
"""

import asyncio
import os
import sys
import time
from typing import List

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from tools.orchestrator import RateLimiter


class TestRateLimitingEnforcementProperty:
    """
    **Feature: ai-research-agents, Property 8: Rate limiting enforcement**
    
    *For any* sequence of arXiv API calls, the time between consecutive calls 
    SHALL be at least 3 seconds.
    
    **Validates: Requirements 6.1**
    """

    @given(
        period_seconds=st.floats(min_value=0.2, max_value=0.5, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    def test_rate_limiter_enforces_minimum_interval(
        self, period_seconds: float
    ):
        """
        Property: For a rate limiter with 1 request per period (like arXiv),
        consecutive requests SHALL be delayed by at least the period.
        
        **Feature: ai-research-agents, Property 8: Rate limiting enforcement**
        **Validates: Requirements 6.1**
        """
        async def run_test():
            # Test with 1 request per period (like arXiv's 1 req per 3 seconds)
            rate_limiter = RateLimiter(
                requests_per_period=1,
                period_seconds=period_seconds
            )
            
            timestamps: List[float] = []
            
            # Make 3 requests - the 2nd and 3rd should be delayed
            for _ in range(3):
                await rate_limiter.acquire()
                timestamps.append(time.monotonic())
            
            # Check that each request after the first is delayed by at least period_seconds
            for i in range(1, len(timestamps)):
                time_diff = timestamps[i] - timestamps[i - 1]
                
                # Allow small tolerance for timing precision
                tolerance = 0.05
                assert time_diff >= period_seconds - tolerance, (
                    f"Request {i} was made too soon after request {i - 1}. "
                    f"Expected at least {period_seconds}s, got {time_diff}s"
                )
        
        asyncio.run(run_test())

    @given(
        requests_per_period=st.integers(min_value=1, max_value=10),
        period_seconds=st.floats(min_value=0.1, max_value=2.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_rate_limiter_allows_requests_within_limit(
        self, requests_per_period: int, period_seconds: float
    ):
        """
        Property: For any rate limiter, requests within the limit SHALL be
        allowed immediately without waiting.
        
        **Feature: ai-research-agents, Property 8: Rate limiting enforcement**
        **Validates: Requirements 6.1**
        """
        async def run_test():
            rate_limiter = RateLimiter(
                requests_per_period=requests_per_period,
                period_seconds=period_seconds
            )
            
            start_time = time.monotonic()
            
            # Make exactly requests_per_period requests
            for _ in range(requests_per_period):
                await rate_limiter.acquire()
            
            elapsed = time.monotonic() - start_time
            
            # All requests within the limit should complete quickly
            # Allow some tolerance for test execution overhead
            max_expected_time = 0.5  # Should be nearly instant
            assert elapsed < max_expected_time, (
                f"Requests within limit took too long: {elapsed}s. "
                f"Expected < {max_expected_time}s"
            )
        
        asyncio.run(run_test())

    @given(
        requests_per_period=st.integers(min_value=1, max_value=5),
        period_seconds=st.floats(min_value=0.1, max_value=0.5, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_get_wait_time_is_non_negative(
        self, requests_per_period: int, period_seconds: float
    ):
        """
        Property: get_wait_time() SHALL always return a non-negative value.
        
        **Feature: ai-research-agents, Property 8: Rate limiting enforcement**
        **Validates: Requirements 6.1**
        """
        rate_limiter = RateLimiter(
            requests_per_period=requests_per_period,
            period_seconds=period_seconds
        )
        
        # Check wait time is non-negative initially
        wait_time = rate_limiter.get_wait_time()
        assert wait_time >= 0.0, f"Wait time should be non-negative, got {wait_time}"
        
        # Check wait time is zero when no requests have been made
        assert wait_time == 0.0, f"Initial wait time should be 0, got {wait_time}"

    @given(
        requests_per_period=st.integers(min_value=1, max_value=5),
        period_seconds=st.floats(min_value=0.1, max_value=0.5, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_get_current_usage_reflects_state(
        self, requests_per_period: int, period_seconds: float
    ):
        """
        Property: get_current_usage() SHALL accurately reflect the rate limiter state.
        
        **Feature: ai-research-agents, Property 8: Rate limiting enforcement**
        **Validates: Requirements 6.1**
        """
        async def run_test():
            rate_limiter = RateLimiter(
                requests_per_period=requests_per_period,
                period_seconds=period_seconds
            )
            
            # Initial state
            usage = rate_limiter.get_current_usage()
            assert usage["requests_in_window"] == 0
            assert usage["requests_per_period"] == requests_per_period
            assert usage["period_seconds"] == period_seconds
            
            # After one request
            await rate_limiter.acquire()
            usage = rate_limiter.get_current_usage()
            assert usage["requests_in_window"] == 1
        
        asyncio.run(run_test())

    def test_arxiv_rate_limit_enforces_3_second_interval(self):
        """
        Property: For arXiv API calls (1 request per 3 seconds), the time between
        consecutive calls SHALL be at least 3 seconds.
        
        This is a specific test for the arXiv rate limit as specified in Requirements 6.1.
        
        **Feature: ai-research-agents, Property 8: Rate limiting enforcement**
        **Validates: Requirements 6.1**
        """
        async def run_test():
            # arXiv rate limit: 1 request per 3 seconds
            # For testing, we use a shorter period (0.3s) but same ratio
            period = 0.3
            arxiv_limiter = RateLimiter(requests_per_period=1, period_seconds=period)
            
            timestamps: List[float] = []
            
            # Make 3 requests
            for _ in range(3):
                await arxiv_limiter.acquire()
                timestamps.append(time.monotonic())
            
            # Check intervals between consecutive requests
            for i in range(1, len(timestamps)):
                interval = timestamps[i] - timestamps[i - 1]
                # Allow small tolerance for timing precision
                tolerance = 0.05
                assert interval >= period - tolerance, (
                    f"Interval between requests {i-1} and {i} was {interval}s, "
                    f"expected at least {period}s (scaled from 3s for testing)"
                )
        
        asyncio.run(run_test())

    @given(
        requests_per_period=st.integers(min_value=-10, max_value=0),
        period_seconds=st.floats(min_value=0.1, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=50)
    def test_invalid_requests_per_period_raises_error(
        self, requests_per_period: int, period_seconds: float
    ):
        """
        Property: Creating a RateLimiter with non-positive requests_per_period
        SHALL raise a ValueError.
        
        **Feature: ai-research-agents, Property 8: Rate limiting enforcement**
        **Validates: Requirements 6.1**
        """
        with pytest.raises(ValueError, match="requests_per_period must be positive"):
            RateLimiter(
                requests_per_period=requests_per_period,
                period_seconds=period_seconds
            )

    @given(
        requests_per_period=st.integers(min_value=1, max_value=10),
        period_seconds=st.floats(min_value=-10.0, max_value=0.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=50)
    def test_invalid_period_seconds_raises_error(
        self, requests_per_period: int, period_seconds: float
    ):
        """
        Property: Creating a RateLimiter with non-positive period_seconds
        SHALL raise a ValueError.
        
        **Feature: ai-research-agents, Property 8: Rate limiting enforcement**
        **Validates: Requirements 6.1**
        """
        with pytest.raises(ValueError, match="period_seconds must be positive"):
            RateLimiter(
                requests_per_period=requests_per_period,
                period_seconds=period_seconds
            )
