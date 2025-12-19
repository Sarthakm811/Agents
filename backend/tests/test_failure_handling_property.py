"""
Property-based tests for session failure handling.

**Feature: ai-research-agents, Property 10: Session failure handling**
**Validates: Requirements 4.4**
"""

import asyncio
import os
import sys
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tasks import (
    BackgroundTaskManager, TaskState, StageProgress,
    TaskStatus, StageStatus
)


# Strategies for generating test data
session_id_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz0123456789-',
    min_size=5,
    max_size=50
).filter(lambda x: x.strip() != '' and not x.startswith('-'))

error_message_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?:-_',
    min_size=1,
    max_size=500
).filter(lambda x: x.strip() != '')

# Strategy for generating various exception types
exception_strategy = st.sampled_from([
    ValueError,
    RuntimeError,
    TypeError,
    KeyError,
    ConnectionError,
    TimeoutError,
    IOError
])


class MockResearchSwarm:
    """Mock research swarm for testing failure scenarios."""
    
    def __init__(self, should_fail: bool = False, error_message: str = "Test error"):
        self.should_fail = should_fail
        self.error_message = error_message
        self.execute_called = False
    
    async def execute_pipeline(self, topic, progress_callback=None):
        self.execute_called = True
        if self.should_fail:
            raise RuntimeError(self.error_message)
        return {"status": "completed", "paper": {"sections": {}}}


class TestSessionFailureHandlingProperty:
    """
    **Feature: ai-research-agents, Property 10: Session failure handling**
    
    *For any* background task that throws an exception, the session status 
    SHALL be set to "failed" and error_message SHALL contain a non-empty description.
    
    **Validates: Requirements 4.4**
    """

    @given(session_id=session_id_strategy, error_message=error_message_strategy)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @pytest.mark.asyncio
    async def test_exception_sets_status_to_failed(
        self,
        session_id: str,
        error_message: str
    ):
        """
        Property: Any exception SHALL set session status to failed.
        
        **Feature: ai-research-agents, Property 10: Session failure handling**
        **Validates: Requirements 4.4**
        """
        manager = BackgroundTaskManager()
        mock_swarm = MockResearchSwarm(should_fail=True, error_message=error_message)
        mock_topic = MagicMock()
        
        # Start the task
        task = await manager.start_research_task(
            session_id=session_id,
            research_swarm=mock_swarm,
            topic=mock_topic
        )
        
        # Wait for task to complete (it should fail)
        try:
            await task
        except Exception:
            pass  # Expected to fail
        
        # Give a moment for async cleanup
        await asyncio.sleep(0.1)
        
        # Verify status is failed
        task_state = manager.get_task_state(session_id)
        assert task_state is not None
        assert task_state.status == TaskStatus.FAILED

    @given(session_id=session_id_strategy, error_message=error_message_strategy)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @pytest.mark.asyncio
    async def test_exception_stores_non_empty_error_message(
        self,
        session_id: str,
        error_message: str
    ):
        """
        Property: Exception error_message SHALL be non-empty.
        
        **Feature: ai-research-agents, Property 10: Session failure handling**
        **Validates: Requirements 4.4**
        """
        manager = BackgroundTaskManager()
        mock_swarm = MockResearchSwarm(should_fail=True, error_message=error_message)
        mock_topic = MagicMock()
        
        # Start the task
        task = await manager.start_research_task(
            session_id=session_id,
            research_swarm=mock_swarm,
            topic=mock_topic
        )
        
        # Wait for task to complete
        try:
            await task
        except Exception:
            pass
        
        await asyncio.sleep(0.1)
        
        # Verify error message is non-empty
        task_state = manager.get_task_state(session_id)
        assert task_state is not None
        assert task_state.error_message is not None
        assert len(task_state.error_message) > 0

    @given(session_id=session_id_strategy, error_message=error_message_strategy)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @pytest.mark.asyncio
    async def test_error_callback_invoked_on_failure(
        self,
        session_id: str,
        error_message: str
    ):
        """
        Property: Error callback SHALL be invoked when task fails.
        
        **Feature: ai-research-agents, Property 10: Session failure handling**
        **Validates: Requirements 4.4**
        """
        manager = BackgroundTaskManager()
        mock_swarm = MockResearchSwarm(should_fail=True, error_message=error_message)
        mock_topic = MagicMock()
        
        callback_invoked = False
        received_session_id = None
        received_error = None
        
        def on_error(sid: str, err: str):
            nonlocal callback_invoked, received_session_id, received_error
            callback_invoked = True
            received_session_id = sid
            received_error = err
        
        # Start the task with error callback
        task = await manager.start_research_task(
            session_id=session_id,
            research_swarm=mock_swarm,
            topic=mock_topic,
            on_error=on_error
        )
        
        # Wait for task to complete
        try:
            await task
        except Exception:
            pass
        
        await asyncio.sleep(0.1)
        
        # Verify callback was invoked
        assert callback_invoked
        assert received_session_id == session_id
        assert received_error is not None
        assert len(received_error) > 0

    @given(
        session_id=session_id_strategy,
        exception_type=exception_strategy,
        error_message=error_message_strategy
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    @pytest.mark.asyncio
    async def test_various_exception_types_handled(
        self,
        session_id: str,
        exception_type: type,
        error_message: str
    ):
        """
        Property: Any exception type SHALL result in failed status.
        
        **Feature: ai-research-agents, Property 10: Session failure handling**
        **Validates: Requirements 4.4**
        """
        manager = BackgroundTaskManager()
        mock_topic = MagicMock()
        
        # Create a swarm that raises the specific exception type
        class FailingSwarm:
            async def execute_pipeline(self, topic, progress_callback=None):
                raise exception_type(error_message)
        
        mock_swarm = FailingSwarm()
        
        # Start the task
        task = await manager.start_research_task(
            session_id=session_id,
            research_swarm=mock_swarm,
            topic=mock_topic
        )
        
        # Wait for task to complete
        try:
            await task
        except Exception:
            pass
        
        await asyncio.sleep(0.1)
        
        # Verify status is failed regardless of exception type
        task_state = manager.get_task_state(session_id)
        assert task_state is not None
        assert task_state.status == TaskStatus.FAILED
        assert task_state.error_message is not None

    @pytest.mark.asyncio
    async def test_empty_exception_message_handled(self):
        """
        Property: Empty exception message SHALL result in non-empty error_message.
        
        **Feature: ai-research-agents, Property 10: Session failure handling**
        **Validates: Requirements 4.4**
        """
        manager = BackgroundTaskManager()
        mock_topic = MagicMock()
        
        # Create a swarm that raises exception with empty message
        class EmptyMessageSwarm:
            async def execute_pipeline(self, topic, progress_callback=None):
                raise RuntimeError("")
        
        mock_swarm = EmptyMessageSwarm()
        
        # Start the task
        task = await manager.start_research_task(
            session_id="test-session",
            research_swarm=mock_swarm,
            topic=mock_topic
        )
        
        # Wait for task to complete
        try:
            await task
        except Exception:
            pass
        
        await asyncio.sleep(0.1)
        
        # Verify error message is non-empty even for empty exception
        task_state = manager.get_task_state("test-session")
        assert task_state is not None
        assert task_state.status == TaskStatus.FAILED
        assert task_state.error_message is not None
        assert len(task_state.error_message) > 0

    @given(session_id=session_id_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    @pytest.mark.asyncio
    async def test_successful_completion_not_marked_failed(
        self,
        session_id: str
    ):
        """
        Property: Successful completion SHALL NOT set status to failed.
        
        **Feature: ai-research-agents, Property 10: Session failure handling**
        **Validates: Requirements 4.4**
        """
        manager = BackgroundTaskManager()
        mock_swarm = MockResearchSwarm(should_fail=False)
        mock_topic = MagicMock()
        
        # Start the task
        task = await manager.start_research_task(
            session_id=session_id,
            research_swarm=mock_swarm,
            topic=mock_topic
        )
        
        # Wait for task to complete
        await task
        await asyncio.sleep(0.1)
        
        # Verify status is completed, not failed
        task_state = manager.get_task_state(session_id)
        assert task_state is not None
        assert task_state.status == TaskStatus.COMPLETED
        assert task_state.error_message is None

    @given(session_id=session_id_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    @pytest.mark.asyncio
    async def test_completion_callback_invoked_on_success(
        self,
        session_id: str
    ):
        """
        Property: Completion callback SHALL be invoked on success.
        
        **Feature: ai-research-agents, Property 10: Session failure handling**
        **Validates: Requirements 4.4**
        """
        manager = BackgroundTaskManager()
        mock_swarm = MockResearchSwarm(should_fail=False)
        mock_topic = MagicMock()
        
        callback_invoked = False
        received_results = None
        
        def on_complete(sid: str, results: Dict[str, Any]):
            nonlocal callback_invoked, received_results
            callback_invoked = True
            received_results = results
        
        # Start the task with completion callback
        task = await manager.start_research_task(
            session_id=session_id,
            research_swarm=mock_swarm,
            topic=mock_topic,
            on_complete=on_complete
        )
        
        # Wait for task to complete
        await task
        await asyncio.sleep(0.1)
        
        # Verify callback was invoked
        assert callback_invoked
        assert received_results is not None

    @given(num_sessions=st.integers(min_value=1, max_value=5))
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    @pytest.mark.asyncio
    async def test_mark_interrupted_sessions_failed(
        self,
        num_sessions: int
    ):
        """
        Property: mark_interrupted_sessions_failed SHALL mark all running sessions as failed.
        
        **Feature: ai-research-agents, Property 10: Session failure handling**
        **Validates: Requirements 4.4, 4.5**
        """
        manager = BackgroundTaskManager()
        
        # Create multiple task states in running status
        session_ids = [f"session-{i}" for i in range(num_sessions)]
        
        for session_id in session_ids:
            task_state = TaskState(session_id=session_id)
            task_state.status = TaskStatus.RUNNING
            manager._tasks[session_id] = task_state
        
        # Mark interrupted sessions as failed
        marked = await manager.mark_interrupted_sessions_failed()
        
        # Verify all sessions were marked
        assert len(marked) == num_sessions
        
        for session_id in session_ids:
            task_state = manager.get_task_state(session_id)
            assert task_state.status == TaskStatus.FAILED
            assert task_state.error_message is not None
            assert "interrupted" in task_state.error_message.lower() or "restart" in task_state.error_message.lower()

    @pytest.mark.asyncio
    async def test_mark_interrupted_does_not_affect_completed(self):
        """
        Property: mark_interrupted_sessions_failed SHALL NOT affect completed sessions.
        
        **Feature: ai-research-agents, Property 10: Session failure handling**
        **Validates: Requirements 4.4, 4.5**
        """
        manager = BackgroundTaskManager()
        
        # Create a completed session
        task_state = TaskState(session_id="completed-session")
        task_state.status = TaskStatus.COMPLETED
        manager._tasks["completed-session"] = task_state
        
        # Create a running session
        running_state = TaskState(session_id="running-session")
        running_state.status = TaskStatus.RUNNING
        manager._tasks["running-session"] = running_state
        
        # Mark interrupted sessions
        marked = await manager.mark_interrupted_sessions_failed()
        
        # Only running session should be marked
        assert len(marked) == 1
        assert "running-session" in marked
        
        # Completed session should remain completed
        completed = manager.get_task_state("completed-session")
        assert completed.status == TaskStatus.COMPLETED

    @given(session_id=session_id_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    @pytest.mark.asyncio
    async def test_cancel_task_sets_cancelled_status(
        self,
        session_id: str
    ):
        """
        Property: Cancelling a task SHALL set status to cancelled.
        
        **Feature: ai-research-agents, Property 10: Session failure handling**
        **Validates: Requirements 4.4, 4.5**
        """
        manager = BackgroundTaskManager()
        mock_topic = MagicMock()
        
        # Create a slow swarm that we can cancel
        class SlowSwarm:
            async def execute_pipeline(self, topic, progress_callback=None):
                await asyncio.sleep(10)  # Long enough to cancel
                return {"status": "completed"}
        
        mock_swarm = SlowSwarm()
        
        # Start the task
        task = await manager.start_research_task(
            session_id=session_id,
            research_swarm=mock_swarm,
            topic=mock_topic
        )
        
        # Give task time to start
        await asyncio.sleep(0.1)
        
        # Cancel the task
        cancelled = manager.cancel_task(session_id)
        assert cancelled
        
        # Wait for cancellation to process
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        await asyncio.sleep(0.1)
        
        # Verify status is cancelled
        task_state = manager.get_task_state(session_id)
        assert task_state is not None
        assert task_state.status == TaskStatus.CANCELLED

    def test_cancel_nonexistent_task_returns_false(self):
        """
        Property: Cancelling non-existent task SHALL return False.
        
        **Feature: ai-research-agents, Property 10: Session failure handling**
        **Validates: Requirements 4.4**
        """
        manager = BackgroundTaskManager()
        
        result = manager.cancel_task("nonexistent-session")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_cancel_completed_task_returns_false(self):
        """
        Property: Cancelling completed task SHALL return False.
        
        **Feature: ai-research-agents, Property 10: Session failure handling**
        **Validates: Requirements 4.4**
        """
        manager = BackgroundTaskManager()
        mock_swarm = MockResearchSwarm(should_fail=False)
        mock_topic = MagicMock()
        
        # Start and complete a task
        task = await manager.start_research_task(
            session_id="test-session",
            research_swarm=mock_swarm,
            topic=mock_topic
        )
        
        await task
        await asyncio.sleep(0.1)
        
        # Try to cancel completed task
        result = manager.cancel_task("test-session")
        
        assert result is False

    @given(session_id=session_id_strategy)
    @settings(max_examples=50)
    def test_get_running_tasks_returns_only_running(
        self,
        session_id: str
    ):
        """
        Property: get_running_tasks SHALL return only running task IDs.
        
        **Feature: ai-research-agents, Property 10: Session failure handling**
        **Validates: Requirements 4.4**
        """
        manager = BackgroundTaskManager()
        
        # Create tasks in various states
        running_state = TaskState(session_id=session_id)
        running_state.status = TaskStatus.RUNNING
        manager._tasks[session_id] = running_state
        
        completed_state = TaskState(session_id="completed")
        completed_state.status = TaskStatus.COMPLETED
        manager._tasks["completed"] = completed_state
        
        failed_state = TaskState(session_id="failed")
        failed_state.status = TaskStatus.FAILED
        manager._tasks["failed"] = failed_state
        
        # Get running tasks
        running = manager.get_running_tasks()
        
        # Only the running session should be returned
        assert session_id in running
        assert "completed" not in running
        assert "failed" not in running

    @given(session_id=session_id_strategy, error_message=error_message_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    @pytest.mark.asyncio
    async def test_error_message_contains_exception_text(
        self,
        session_id: str,
        error_message: str
    ):
        """
        Property: error_message SHALL contain the exception text.
        
        **Feature: ai-research-agents, Property 10: Session failure handling**
        **Validates: Requirements 4.4**
        """
        manager = BackgroundTaskManager()
        mock_swarm = MockResearchSwarm(should_fail=True, error_message=error_message)
        mock_topic = MagicMock()
        
        # Start the task
        task = await manager.start_research_task(
            session_id=session_id,
            research_swarm=mock_swarm,
            topic=mock_topic
        )
        
        # Wait for task to complete
        try:
            await task
        except Exception:
            pass
        
        await asyncio.sleep(0.1)
        
        # Verify error message contains the exception text
        task_state = manager.get_task_state(session_id)
        assert task_state is not None
        assert error_message in task_state.error_message
