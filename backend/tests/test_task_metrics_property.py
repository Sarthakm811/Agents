"""
Property-based tests for task completion metrics.

**Feature: ai-research-agents, Property 7: Task completion metrics**
**Validates: Requirements 5.3**
"""

import os
import sys
from typing import Any, Dict, List, Tuple
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from agents.swarm import (
    AgenticResearchSwarm, ResearchTopic, AgentResult, BaseAgent,
    LiteratureAgent, GapAnalysisAgent, HypothesisAgent, 
    MethodologyAgent, WritingAgent
)


# Strategies for generating test data
topic_title_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -',
    min_size=5,
    max_size=100
).filter(lambda x: x.strip() != '')

topic_description_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -.,',
    min_size=10,
    max_size=300
).filter(lambda x: x.strip() != '')

domain_strategy = st.sampled_from([
    "computer science", "biology", "physics", "chemistry",
    "mathematics", "economics", "psychology", "medicine"
])

complexity_strategy = st.sampled_from(["basic", "intermediate", "advanced"])

tokens_used_strategy = st.integers(min_value=0, max_value=10000)


def create_mock_agent(name: str, tokens_used: int = 100) -> MagicMock:
    """Create a mock agent that returns a valid AgentResult."""
    mock_agent = MagicMock(spec=BaseAgent)
    mock_result = AgentResult(
        agent_name=name,
        output={"test": "data"},
        tokens_used=tokens_used,
        duration_seconds=0.1
    )
    mock_agent.execute = AsyncMock(return_value=mock_result)
    return mock_agent


class TestTaskCompletionMetricsProperty:
    """
    **Feature: ai-research-agents, Property 7: Task completion metrics**
    
    *For any* completed agent task, the tasksCompleted metric SHALL increment 
    by exactly 1 and activeAgents SHALL accurately reflect the count of 
    currently executing agents.
    
    **Validates: Requirements 5.3**
    """

    def test_initial_metrics_state(self):
        """
        Property: Initial metrics SHALL have tasks_completed=0 and active_agents=0.
        
        **Feature: ai-research-agents, Property 7: Task completion metrics**
        **Validates: Requirements 5.3**
        """
        swarm = AgenticResearchSwarm()
        metrics = swarm.get_performance_metrics()
        
        assert metrics["tasks_completed"] == 0
        assert metrics["active_agents"] == 0
        assert metrics["total_agents"] == 5

    def test_reset_metrics(self):
        """
        Property: reset_metrics SHALL restore all metrics to initial values.
        
        **Feature: ai-research-agents, Property 7: Task completion metrics**
        **Validates: Requirements 5.3**
        """
        swarm = AgenticResearchSwarm()
        
        # Manually modify metrics
        swarm._metrics["tasks_completed"] = 3
        swarm._metrics["active_agents"] = 1
        swarm._metrics["total_tokens"] = 500
        
        # Reset
        swarm.reset_metrics()
        metrics = swarm.get_performance_metrics()
        
        assert metrics["tasks_completed"] == 0
        assert metrics["active_agents"] == 0
        assert metrics["total_tokens"] == 0

    @given(tokens_used=tokens_used_strategy)
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_execute_agent_increments_tasks_completed_by_one(
        self,
        tokens_used: int
    ):
        """
        Property: For any agent execution, tasks_completed SHALL increment by exactly 1.
        
        **Feature: ai-research-agents, Property 7: Task completion metrics**
        **Validates: Requirements 5.3**
        """
        swarm = AgenticResearchSwarm()
        mock_agent = create_mock_agent("TestAgent", tokens_used)
        
        initial_tasks = swarm._metrics["tasks_completed"]
        
        # Execute agent
        await swarm._execute_agent(
            mock_agent,
            {"topic": {"title": "Test", "description": "Test desc"}},
            "test_stage"
        )
        
        # Verify increment by exactly 1
        assert swarm._metrics["tasks_completed"] == initial_tasks + 1

    @given(num_executions=st.integers(min_value=1, max_value=10))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    @pytest.mark.asyncio
    async def test_multiple_agent_executions_increment_correctly(
        self,
        num_executions: int
    ):
        """
        Property: For any sequence of N agent executions, tasks_completed 
        SHALL equal N.
        
        **Feature: ai-research-agents, Property 7: Task completion metrics**
        **Validates: Requirements 5.3**
        """
        swarm = AgenticResearchSwarm()
        swarm.reset_metrics()
        
        for i in range(num_executions):
            mock_agent = create_mock_agent(f"TestAgent{i}", 100)
            
            await swarm._execute_agent(
                mock_agent,
                {"topic": {"title": "Test", "description": "Test desc"}},
                f"stage_{i}"
            )
        
        assert swarm._metrics["tasks_completed"] == num_executions

    @pytest.mark.asyncio
    async def test_active_agents_is_zero_after_execution(self):
        """
        Property: After agent execution completes, active_agents SHALL be 0.
        
        **Feature: ai-research-agents, Property 7: Task completion metrics**
        **Validates: Requirements 5.3**
        """
        swarm = AgenticResearchSwarm()
        mock_agent = create_mock_agent("TestAgent")
        
        await swarm._execute_agent(
            mock_agent,
            {"topic": {"title": "Test", "description": "Test desc"}},
            "test_stage"
        )
        
        assert swarm._metrics["active_agents"] == 0

    @pytest.mark.asyncio
    async def test_active_agents_is_one_during_execution(self):
        """
        Property: During agent execution, active_agents SHALL be 1.
        
        **Feature: ai-research-agents, Property 7: Task completion metrics**
        **Validates: Requirements 5.3**
        """
        swarm = AgenticResearchSwarm()
        active_during_execution = None
        
        async def capture_active_agents(*args, **kwargs):
            nonlocal active_during_execution
            # Capture active_agents during execution
            active_during_execution = swarm._metrics["active_agents"]
            return AgentResult(
                agent_name="TestAgent",
                output={"test": "data"},
                tokens_used=100,
                duration_seconds=0.1
            )
        
        mock_agent = MagicMock(spec=BaseAgent)
        mock_agent.execute = AsyncMock(side_effect=capture_active_agents)
        
        await swarm._execute_agent(
            mock_agent,
            {"topic": {"title": "Test", "description": "Test desc"}},
            "test_stage"
        )
        
        # During execution, active_agents should have been 1
        assert active_during_execution == 1
        # After execution, it should be 0
        assert swarm._metrics["active_agents"] == 0

    @given(tokens_used=tokens_used_strategy)
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_tokens_accumulate_correctly(
        self,
        tokens_used: int
    ):
        """
        Property: For any agent execution, total_tokens SHALL increase by 
        the tokens_used from that execution.
        
        **Feature: ai-research-agents, Property 7: Task completion metrics**
        **Validates: Requirements 5.3**
        """
        swarm = AgenticResearchSwarm()
        swarm.reset_metrics()
        
        mock_agent = create_mock_agent("TestAgent", tokens_used)
        
        initial_tokens = swarm._metrics["total_tokens"]
        
        await swarm._execute_agent(
            mock_agent,
            {"topic": {"title": "Test", "description": "Test desc"}},
            "test_stage"
        )
        
        assert swarm._metrics["total_tokens"] == initial_tokens + tokens_used

    @pytest.mark.asyncio
    async def test_progress_callback_called_with_correct_values(self):
        """
        Property: Progress callback SHALL be called with 0 at start and 100 at end.
        
        **Feature: ai-research-agents, Property 7: Task completion metrics**
        **Validates: Requirements 5.3**
        """
        swarm = AgenticResearchSwarm()
        callback_calls: List[Tuple[str, int]] = []
        
        def progress_callback(stage: str, progress: int):
            callback_calls.append((stage, progress))
        
        mock_agent = create_mock_agent("TestAgent")
        
        await swarm._execute_agent(
            mock_agent,
            {"topic": {"title": "Test", "description": "Test desc"}},
            "test_stage",
            progress_callback
        )
        
        assert len(callback_calls) == 2
        assert callback_calls[0] == ("test_stage", 0)
        assert callback_calls[1] == ("test_stage", 100)

    @given(
        num_stages=st.integers(min_value=1, max_value=10),
        tokens_per_stage=st.integers(min_value=0, max_value=1000)
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    @pytest.mark.asyncio
    async def test_metrics_accumulate_across_multiple_stages(
        self,
        num_stages: int,
        tokens_per_stage: int
    ):
        """
        Property: For any number of stages, metrics SHALL accumulate correctly.
        
        **Feature: ai-research-agents, Property 7: Task completion metrics**
        **Validates: Requirements 5.3**
        """
        swarm = AgenticResearchSwarm()
        swarm.reset_metrics()
        
        callback_calls: List[Tuple[str, int]] = []
        
        def progress_callback(stage: str, progress: int):
            callback_calls.append((stage, progress))
        
        for i in range(num_stages):
            mock_agent = create_mock_agent(f"Agent{i}", tokens_per_stage)
            await swarm._execute_agent(
                mock_agent,
                {"topic": {"title": "Test", "description": "Test desc"}},
                f"stage_{i}",
                progress_callback
            )
        
        # Verify tasks completed
        assert swarm._metrics["tasks_completed"] == num_stages
        
        # Verify tokens accumulated
        assert swarm._metrics["total_tokens"] == num_stages * tokens_per_stage
        
        # Verify callback calls (2 per stage)
        assert len(callback_calls) == num_stages * 2
        
        # Verify active_agents is 0 after all executions
        assert swarm._metrics["active_agents"] == 0

    @pytest.mark.asyncio
    async def test_five_sequential_agents_complete_five_tasks(self):
        """
        Property: Executing 5 agents sequentially SHALL result in tasks_completed=5.
        
        This simulates the full pipeline behavior without external dependencies.
        
        **Feature: ai-research-agents, Property 7: Task completion metrics**
        **Validates: Requirements 5.3**
        """
        swarm = AgenticResearchSwarm()
        swarm.reset_metrics()
        
        stages = ["literature_review", "gap_analysis", "hypothesis_generation", 
                  "methodology", "writing"]
        
        callback_calls: List[Tuple[str, int]] = []
        
        def progress_callback(stage: str, progress: int):
            callback_calls.append((stage, progress))
        
        for stage in stages:
            mock_agent = create_mock_agent(f"{stage}_agent", 100)
            await swarm._execute_agent(
                mock_agent,
                {"topic": {"title": "Test", "description": "Test desc"}},
                stage,
                progress_callback
            )
        
        # Verify exactly 5 tasks completed
        assert swarm._metrics["tasks_completed"] == 5
        
        # Verify active_agents is 0
        assert swarm._metrics["active_agents"] == 0
        
        # Verify all stages were called with progress
        assert len(callback_calls) == 10  # 2 calls per stage
        
        stages_called = set(call[0] for call in callback_calls)
        assert stages_called == set(stages)

    @pytest.mark.asyncio
    async def test_metrics_structure_is_complete(self):
        """
        Property: get_performance_metrics SHALL return all required metric fields.
        
        **Feature: ai-research-agents, Property 7: Task completion metrics**
        **Validates: Requirements 5.3**
        """
        swarm = AgenticResearchSwarm()
        metrics = swarm.get_performance_metrics()
        
        required_fields = ["total_agents", "active_agents", "tasks_completed", 
                          "total_tokens", "total_duration"]
        
        for field in required_fields:
            assert field in metrics, f"Missing required field: {field}"

    @pytest.mark.asyncio
    async def test_get_performance_metrics_returns_copy(self):
        """
        Property: get_performance_metrics SHALL return a copy, not the original dict.
        
        **Feature: ai-research-agents, Property 7: Task completion metrics**
        **Validates: Requirements 5.3**
        """
        swarm = AgenticResearchSwarm()
        
        metrics1 = swarm.get_performance_metrics()
        metrics1["tasks_completed"] = 999
        
        metrics2 = swarm.get_performance_metrics()
        
        # Modifying the returned dict should not affect internal state
        assert metrics2["tasks_completed"] == 0

    def test_pipeline_stages_constant_has_five_stages(self):
        """
        Property: PIPELINE_STAGES SHALL contain exactly 5 stages.
        
        **Feature: ai-research-agents, Property 7: Task completion metrics**
        **Validates: Requirements 5.3**
        """
        assert hasattr(AgenticResearchSwarm, 'PIPELINE_STAGES')
        assert len(AgenticResearchSwarm.PIPELINE_STAGES) == 5
        
        expected_stages = ["literature_review", "gap_analysis", 
                          "hypothesis_generation", "methodology", "writing"]
        assert AgenticResearchSwarm.PIPELINE_STAGES == expected_stages

    @given(
        title=topic_title_strategy,
        description=topic_description_strategy,
        domain=domain_strategy
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    @pytest.mark.asyncio
    async def test_execute_agent_returns_agent_result(
        self,
        title: str,
        description: str,
        domain: str
    ):
        """
        Property: _execute_agent SHALL return the AgentResult from the agent.
        
        **Feature: ai-research-agents, Property 7: Task completion metrics**
        **Validates: Requirements 5.3**
        """
        swarm = AgenticResearchSwarm()
        
        expected_output = {"title": title, "description": description, "domain": domain}
        mock_agent = MagicMock(spec=BaseAgent)
        mock_result = AgentResult(
            agent_name="TestAgent",
            output=expected_output,
            tokens_used=100,
            duration_seconds=0.1
        )
        mock_agent.execute = AsyncMock(return_value=mock_result)
        
        result = await swarm._execute_agent(
            mock_agent,
            {"topic": {"title": title, "description": description}},
            "test_stage"
        )
        
        assert result == mock_result
        assert result.output == expected_output
