"""
Property-based tests for stage progress consistency.

**Feature: ai-research-agents, Property 6: Stage progress consistency**
**Validates: Requirements 4.2, 4.3**
"""

import os
import sys
from typing import List, Tuple

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tasks import (
    BackgroundTaskManager, TaskState, StageProgress,
    TaskStatus, StageStatus
)


# Strategies for generating test data
progress_value_strategy = st.integers(min_value=0, max_value=100)

stage_name_strategy = st.sampled_from([
    "literature_review",
    "gap_analysis",
    "hypothesis_generation",
    "methodology",
    "writing"
])

session_id_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz0123456789-',
    min_size=5,
    max_size=50
).filter(lambda x: x.strip() != '' and not x.startswith('-'))


class TestStageProgressConsistencyProperty:
    """
    **Feature: ai-research-agents, Property 6: Stage progress consistency**
    
    *For any* research session, stage progress values SHALL be monotonically 
    increasing (never decrease) and status transitions SHALL follow the valid 
    sequence: pending → running → completed|failed.
    
    **Validates: Requirements 4.2, 4.3**
    """

    def test_initial_stage_status_is_pending(self):
        """
        Property: Initial stage status SHALL be pending.
        
        **Feature: ai-research-agents, Property 6: Stage progress consistency**
        **Validates: Requirements 4.2, 4.3**
        """
        stage = StageProgress(name="test_stage")
        assert stage.status == StageStatus.PENDING
        assert stage.progress == 0

    def test_initial_task_state_has_all_stages_pending(self):
        """
        Property: Initial TaskState SHALL have all stages in pending status.
        
        **Feature: ai-research-agents, Property 6: Stage progress consistency**
        **Validates: Requirements 4.2, 4.3**
        """
        task_state = TaskState(session_id="test-session")
        
        expected_stages = [
            "literature_review",
            "gap_analysis",
            "hypothesis_generation",
            "methodology",
            "writing"
        ]
        
        assert len(task_state.stages) == len(expected_stages)
        
        for stage_name in expected_stages:
            assert stage_name in task_state.stages
            stage = task_state.stages[stage_name]
            assert stage.status == StageStatus.PENDING
            assert stage.progress == 0

    @given(
        current_progress=progress_value_strategy,
        new_progress=progress_value_strategy
    )
    @settings(max_examples=100)
    def test_progress_monotonicity_validation(
        self,
        current_progress: int,
        new_progress: int
    ):
        """
        Property: Progress validation SHALL reject decreasing values.
        
        **Feature: ai-research-agents, Property 6: Stage progress consistency**
        **Validates: Requirements 4.2, 4.3**
        """
        manager = BackgroundTaskManager()
        
        is_valid = manager._validate_progress_monotonic(current_progress, new_progress)
        
        # Progress is valid if and only if it doesn't decrease
        assert is_valid == (new_progress >= current_progress)

    @given(progress_values=st.lists(progress_value_strategy, min_size=1, max_size=20))
    @settings(max_examples=100)
    def test_monotonic_progress_sequence_accepted(
        self,
        progress_values: List[int]
    ):
        """
        Property: A monotonically increasing sequence of progress values 
        SHALL all be accepted.
        
        **Feature: ai-research-agents, Property 6: Stage progress consistency**
        **Validates: Requirements 4.2, 4.3**
        """
        # Sort to make monotonically increasing
        sorted_values = sorted(progress_values)
        
        manager = BackgroundTaskManager()
        
        current = 0
        for value in sorted_values:
            assert manager._validate_progress_monotonic(current, value)
            current = value

    @given(
        progress_values=st.lists(
            progress_value_strategy, 
            min_size=2, 
            max_size=10
        )
    )
    @settings(max_examples=100)
    def test_non_monotonic_progress_rejected(
        self,
        progress_values: List[int]
    ):
        """
        Property: Any decrease in progress SHALL be rejected.
        
        **Feature: ai-research-agents, Property 6: Stage progress consistency**
        **Validates: Requirements 4.2, 4.3**
        """
        manager = BackgroundTaskManager()
        
        for i in range(len(progress_values) - 1):
            current = progress_values[i]
            next_val = progress_values[i + 1]
            
            is_valid = manager._validate_progress_monotonic(current, next_val)
            
            if next_val < current:
                assert not is_valid, f"Decreasing progress {current} -> {next_val} should be rejected"

    def test_valid_status_transitions_from_pending(self):
        """
        Property: From pending, only running and failed transitions SHALL be valid.
        
        **Feature: ai-research-agents, Property 6: Stage progress consistency**
        **Validates: Requirements 4.2, 4.3**
        """
        manager = BackgroundTaskManager()
        
        # Valid transitions from pending
        assert manager._validate_stage_transition(StageStatus.PENDING, StageStatus.RUNNING)
        assert manager._validate_stage_transition(StageStatus.PENDING, StageStatus.FAILED)
        
        # Invalid transitions from pending
        assert not manager._validate_stage_transition(StageStatus.PENDING, StageStatus.COMPLETED)
        assert not manager._validate_stage_transition(StageStatus.PENDING, StageStatus.PENDING)

    def test_valid_status_transitions_from_running(self):
        """
        Property: From running, only completed and failed transitions SHALL be valid.
        
        **Feature: ai-research-agents, Property 6: Stage progress consistency**
        **Validates: Requirements 4.2, 4.3**
        """
        manager = BackgroundTaskManager()
        
        # Valid transitions from running
        assert manager._validate_stage_transition(StageStatus.RUNNING, StageStatus.COMPLETED)
        assert manager._validate_stage_transition(StageStatus.RUNNING, StageStatus.FAILED)
        
        # Invalid transitions from running
        assert not manager._validate_stage_transition(StageStatus.RUNNING, StageStatus.PENDING)
        assert not manager._validate_stage_transition(StageStatus.RUNNING, StageStatus.RUNNING)

    def test_completed_is_terminal_state(self):
        """
        Property: Completed SHALL be a terminal state with no valid transitions.
        
        **Feature: ai-research-agents, Property 6: Stage progress consistency**
        **Validates: Requirements 4.2, 4.3**
        """
        manager = BackgroundTaskManager()
        
        # No valid transitions from completed
        assert not manager._validate_stage_transition(StageStatus.COMPLETED, StageStatus.PENDING)
        assert not manager._validate_stage_transition(StageStatus.COMPLETED, StageStatus.RUNNING)
        assert not manager._validate_stage_transition(StageStatus.COMPLETED, StageStatus.COMPLETED)
        assert not manager._validate_stage_transition(StageStatus.COMPLETED, StageStatus.FAILED)

    def test_failed_is_terminal_state(self):
        """
        Property: Failed SHALL be a terminal state with no valid transitions.
        
        **Feature: ai-research-agents, Property 6: Stage progress consistency**
        **Validates: Requirements 4.2, 4.3**
        """
        manager = BackgroundTaskManager()
        
        # No valid transitions from failed
        assert not manager._validate_stage_transition(StageStatus.FAILED, StageStatus.PENDING)
        assert not manager._validate_stage_transition(StageStatus.FAILED, StageStatus.RUNNING)
        assert not manager._validate_stage_transition(StageStatus.FAILED, StageStatus.COMPLETED)
        assert not manager._validate_stage_transition(StageStatus.FAILED, StageStatus.FAILED)

    @given(session_id=session_id_strategy, stage_name=stage_name_strategy)
    @settings(max_examples=100)
    def test_update_stage_progress_creates_stage_if_missing(
        self,
        session_id: str,
        stage_name: str
    ):
        """
        Property: Updating progress for a missing stage SHALL create it.
        
        **Feature: ai-research-agents, Property 6: Stage progress consistency**
        **Validates: Requirements 4.2, 4.3**
        """
        manager = BackgroundTaskManager()
        
        # Create task state with empty stages
        task_state = TaskState(session_id=session_id)
        task_state.stages = {}  # Clear default stages
        manager._tasks[session_id] = task_state
        
        # Update progress for non-existent stage
        manager._update_stage_progress(session_id, stage_name, 50)
        
        # Stage should now exist
        assert stage_name in task_state.stages
        assert task_state.stages[stage_name].progress == 50

    @given(
        session_id=session_id_strategy,
        stage_name=stage_name_strategy,
        progress=progress_value_strategy
    )
    @settings(max_examples=100)
    def test_update_stage_progress_sets_running_on_zero(
        self,
        session_id: str,
        stage_name: str,
        progress: int
    ):
        """
        Property: Setting progress to 0 SHALL transition status to running.
        
        **Feature: ai-research-agents, Property 6: Stage progress consistency**
        **Validates: Requirements 4.2, 4.3**
        """
        assume(progress == 0)
        
        manager = BackgroundTaskManager()
        task_state = TaskState(session_id=session_id)
        manager._tasks[session_id] = task_state
        
        # Ensure stage exists and is pending
        if stage_name not in task_state.stages:
            task_state.stages[stage_name] = StageProgress(name=stage_name)
        
        initial_status = task_state.stages[stage_name].status
        assume(initial_status == StageStatus.PENDING)
        
        manager._update_stage_progress(session_id, stage_name, 0)
        
        assert task_state.stages[stage_name].status == StageStatus.RUNNING
        assert task_state.stages[stage_name].started_at is not None

    @given(
        session_id=session_id_strategy,
        stage_name=stage_name_strategy
    )
    @settings(max_examples=100)
    def test_update_stage_progress_sets_completed_on_100(
        self,
        session_id: str,
        stage_name: str
    ):
        """
        Property: Setting progress to 100 SHALL transition status to completed.
        
        **Feature: ai-research-agents, Property 6: Stage progress consistency**
        **Validates: Requirements 4.2, 4.3**
        """
        manager = BackgroundTaskManager()
        task_state = TaskState(session_id=session_id)
        manager._tasks[session_id] = task_state
        
        # Ensure stage exists
        if stage_name not in task_state.stages:
            task_state.stages[stage_name] = StageProgress(name=stage_name)
        
        # First set to running (progress 0)
        manager._update_stage_progress(session_id, stage_name, 0)
        assert task_state.stages[stage_name].status == StageStatus.RUNNING
        
        # Then set to completed (progress 100)
        manager._update_stage_progress(session_id, stage_name, 100)
        
        assert task_state.stages[stage_name].status == StageStatus.COMPLETED
        assert task_state.stages[stage_name].completed_at is not None

    @given(
        session_id=session_id_strategy,
        stage_name=stage_name_strategy,
        progress_sequence=st.lists(
            progress_value_strategy,
            min_size=2,
            max_size=10
        )
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_progress_never_decreases_after_updates(
        self,
        session_id: str,
        stage_name: str,
        progress_sequence: List[int]
    ):
        """
        Property: After any sequence of updates, progress SHALL never decrease.
        
        **Feature: ai-research-agents, Property 6: Stage progress consistency**
        **Validates: Requirements 4.2, 4.3**
        """
        manager = BackgroundTaskManager()
        task_state = TaskState(session_id=session_id)
        manager._tasks[session_id] = task_state
        
        # Ensure stage exists
        if stage_name not in task_state.stages:
            task_state.stages[stage_name] = StageProgress(name=stage_name)
        
        previous_progress = 0
        
        for progress in progress_sequence:
            manager._update_stage_progress(session_id, stage_name, progress)
            current_progress = task_state.stages[stage_name].progress
            
            # Progress should never decrease
            assert current_progress >= previous_progress, \
                f"Progress decreased from {previous_progress} to {current_progress}"
            
            previous_progress = current_progress

    @given(
        session_id=session_id_strategy,
        stage_name=stage_name_strategy
    )
    @settings(max_examples=100)
    def test_status_follows_valid_sequence(
        self,
        session_id: str,
        stage_name: str
    ):
        """
        Property: Status transitions SHALL follow pending → running → completed.
        
        **Feature: ai-research-agents, Property 6: Stage progress consistency**
        **Validates: Requirements 4.2, 4.3**
        """
        manager = BackgroundTaskManager()
        task_state = TaskState(session_id=session_id)
        manager._tasks[session_id] = task_state
        
        # Ensure stage exists
        if stage_name not in task_state.stages:
            task_state.stages[stage_name] = StageProgress(name=stage_name)
        
        stage = task_state.stages[stage_name]
        
        # Initial state
        assert stage.status == StageStatus.PENDING
        
        # Transition to running
        manager._update_stage_progress(session_id, stage_name, 0)
        assert stage.status == StageStatus.RUNNING
        
        # Intermediate progress
        manager._update_stage_progress(session_id, stage_name, 50)
        assert stage.status == StageStatus.RUNNING
        
        # Transition to completed
        manager._update_stage_progress(session_id, stage_name, 100)
        assert stage.status == StageStatus.COMPLETED

    def test_stage_progress_to_dict(self):
        """
        Property: to_dict SHALL return all required fields.
        
        **Feature: ai-research-agents, Property 6: Stage progress consistency**
        **Validates: Requirements 4.2, 4.3**
        """
        stage = StageProgress(name="test_stage")
        result = stage.to_dict()
        
        required_fields = ["name", "status", "progress", "started_at", "completed_at", "error"]
        
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"
        
        assert result["name"] == "test_stage"
        assert result["status"] == "pending"
        assert result["progress"] == 0

    @given(session_id=session_id_strategy)
    @settings(max_examples=50)
    def test_get_stage_progress_returns_all_stages(
        self,
        session_id: str
    ):
        """
        Property: get_stage_progress SHALL return progress for all stages.
        
        **Feature: ai-research-agents, Property 6: Stage progress consistency**
        **Validates: Requirements 4.2, 4.3**
        """
        manager = BackgroundTaskManager()
        task_state = TaskState(session_id=session_id)
        manager._tasks[session_id] = task_state
        
        progress = manager.get_stage_progress(session_id)
        
        expected_stages = [
            "literature_review",
            "gap_analysis",
            "hypothesis_generation",
            "methodology",
            "writing"
        ]
        
        assert len(progress) == len(expected_stages)
        
        for stage_name in expected_stages:
            assert stage_name in progress
            assert "status" in progress[stage_name]
            assert "progress" in progress[stage_name]

    def test_get_stage_progress_returns_empty_for_unknown_session(self):
        """
        Property: get_stage_progress SHALL return empty dict for unknown session.
        
        **Feature: ai-research-agents, Property 6: Stage progress consistency**
        **Validates: Requirements 4.2, 4.3**
        """
        manager = BackgroundTaskManager()
        
        progress = manager.get_stage_progress("unknown-session")
        
        assert progress == {}

    @given(
        session_id=session_id_strategy,
        high_progress=st.integers(min_value=50, max_value=100),
        low_progress=st.integers(min_value=0, max_value=49)
    )
    @settings(max_examples=100)
    def test_decreasing_progress_is_ignored(
        self,
        session_id: str,
        high_progress: int,
        low_progress: int
    ):
        """
        Property: Attempts to decrease progress SHALL be ignored.
        
        **Feature: ai-research-agents, Property 6: Stage progress consistency**
        **Validates: Requirements 4.2, 4.3**
        """
        assume(high_progress > low_progress)
        
        manager = BackgroundTaskManager()
        task_state = TaskState(session_id=session_id)
        manager._tasks[session_id] = task_state
        
        stage_name = "literature_review"
        
        # Set initial progress
        manager._update_stage_progress(session_id, stage_name, 0)
        manager._update_stage_progress(session_id, stage_name, high_progress)
        
        # Try to decrease progress
        manager._update_stage_progress(session_id, stage_name, low_progress)
        
        # Progress should remain at high value
        assert task_state.stages[stage_name].progress == high_progress
