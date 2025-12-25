"""
Property-based tests for paper structure completeness.

**Feature: ai-research-agents, Property 5: Paper structure completeness**
**Validates: Requirements 2.5**
"""

import os
import sys
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from agents.swarm import (
    WritingAgent, ResearchTopic, AgentResult,
    LiteratureAgent, GapAnalysisAgent, HypothesisAgent, MethodologyAgent
)


# Strategy for generating research topics
topic_title_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -',
    min_size=5,
    max_size=100
).filter(lambda x: x.strip() != '')

topic_description_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -.,',
    min_size=10,
    max_size=500
).filter(lambda x: x.strip() != '')

domain_strategy = st.sampled_from([
    "computer science", "biology", "physics", "chemistry", 
    "mathematics", "economics", "psychology", "medicine"
])

complexity_strategy = st.sampled_from(["basic", "intermediate", "advanced"])

# Strategy for generating research context
gap_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -.,',
    min_size=10,
    max_size=200
).filter(lambda x: x.strip() != '')

hypothesis_strategy = st.fixed_dictionaries({
    "title": st.text(min_size=5, max_size=100).filter(lambda x: x.strip() != ''),
    "description": st.text(min_size=10, max_size=300).filter(lambda x: x.strip() != '')
})


def create_mock_llm_client():
    """Create a mock LLM client that returns valid section content."""
    mock_client = MagicMock()
    
    async def mock_generate(prompt, system_prompt=None, max_tokens=2000, temperature=0.7):
        # Return a mock response with content based on the prompt
        mock_response = MagicMock()
        mock_response.content = "This is generated academic content for the paper section."
        mock_response.tokens_used = 100
        return mock_response
    
    mock_client.generate = AsyncMock(side_effect=mock_generate)
    return mock_client


def create_mock_orchestrator():
    """Create a mock orchestrator."""
    return MagicMock()


class TestPaperStructureCompletenessProperty:
    """
    **Feature: ai-research-agents, Property 5: Paper structure completeness**
    
    *For any* completed research session, the generated paper SHALL contain all 
    required sections: abstract, introduction, methodology, results, and conclusion.
    
    **Validates: Requirements 2.5**
    """

    def test_writing_agent_has_required_sections_constant(self):
        """
        Property: WritingAgent SHALL define all required sections.
        
        **Feature: ai-research-agents, Property 5: Paper structure completeness**
        **Validates: Requirements 2.5**
        """
        required = ["abstract", "introduction", "methodology", "results", "discussion", "conclusion"]
        assert hasattr(WritingAgent, 'REQUIRED_SECTIONS')
        assert set(WritingAgent.REQUIRED_SECTIONS) == set(required)

    @given(
        title=topic_title_strategy,
        description=topic_description_strategy,
        domain=domain_strategy,
        complexity=complexity_strategy,
        gaps=st.lists(gap_strategy, min_size=1, max_size=5),
        hypotheses=st.lists(hypothesis_strategy, min_size=1, max_size=3),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @pytest.mark.asyncio
    async def test_compose_paper_returns_all_required_sections(
        self,
        title: str,
        description: str,
        domain: str,
        complexity: str,
        gaps: List[str],
        hypotheses: List[Dict[str, str]],
    ):
        """
        Property: For any valid research context, compose_paper SHALL return
        a paper containing all required sections.
        
        **Feature: ai-research-agents, Property 5: Paper structure completeness**
        **Validates: Requirements 2.5**
        """
        mock_llm = create_mock_llm_client()
        mock_orchestrator = create_mock_orchestrator()
        
        agent = WritingAgent(mock_llm, mock_orchestrator)
        
        research_context = {
            "topic": {
                "title": title,
                "description": description,
                "domain": domain
            },
            "literature_summary": "Literature review summary content.",
            "gaps": gaps,
            "hypotheses": hypotheses,
            "methodology": {"full_methodology": "Methodology content."}
        }
        
        result = await agent.compose_paper(research_context)
        
        # Verify result structure
        assert isinstance(result, AgentResult)
        assert result.agent_name == "WritingAgent"
        assert "sections" in result.output
        
        sections = result.output["sections"]
        
        # Verify ALL required sections are present
        for section_name in WritingAgent.REQUIRED_SECTIONS:
            assert section_name in sections, f"Missing required section: {section_name}"
            assert sections[section_name], f"Section {section_name} is empty"
            assert isinstance(sections[section_name], str), f"Section {section_name} must be a string"

    @given(
        title=topic_title_strategy,
        description=topic_description_strategy,
    )
    @settings(max_examples=50)
    @pytest.mark.asyncio
    async def test_compose_paper_with_minimal_context(
        self,
        title: str,
        description: str,
    ):
        """
        Property: For any research context with minimal data, compose_paper SHALL
        still return all required sections.
        
        **Feature: ai-research-agents, Property 5: Paper structure completeness**
        **Validates: Requirements 2.5**
        """
        mock_llm = create_mock_llm_client()
        mock_orchestrator = create_mock_orchestrator()
        
        agent = WritingAgent(mock_llm, mock_orchestrator)
        
        # Minimal context - only topic
        research_context = {
            "topic": {"title": title, "description": description}
        }
        
        result = await agent.compose_paper(research_context)
        
        sections = result.output["sections"]
        
        # Even with minimal context, all sections must be present
        for section_name in WritingAgent.REQUIRED_SECTIONS:
            assert section_name in sections, f"Missing required section: {section_name}"

    @given(
        title=topic_title_strategy,
        description=topic_description_strategy,
        domain=domain_strategy,
    )
    @settings(max_examples=50)
    @pytest.mark.asyncio
    async def test_compose_paper_with_research_topic_object(
        self,
        title: str,
        description: str,
        domain: str,
    ):
        """
        Property: For any ResearchTopic object, compose_paper SHALL return
        all required sections.
        
        **Feature: ai-research-agents, Property 5: Paper structure completeness**
        **Validates: Requirements 2.5**
        """
        mock_llm = create_mock_llm_client()
        mock_orchestrator = create_mock_orchestrator()
        
        agent = WritingAgent(mock_llm, mock_orchestrator)
        
        topic = ResearchTopic(
            title=title,
            description=description,
            domain=domain
        )
        
        research_context = {
            "topic": topic,
            "literature_summary": "Summary content.",
            "gaps": ["Gap 1", "Gap 2"],
            "hypotheses": [{"title": "H1", "description": "Hypothesis 1"}],
            "methodology": {"full_methodology": "Method content."}
        }
        
        result = await agent.compose_paper(research_context)
        
        sections = result.output["sections"]
        
        for section_name in WritingAgent.REQUIRED_SECTIONS:
            assert section_name in sections, f"Missing required section: {section_name}"

    @pytest.mark.asyncio
    async def test_compose_paper_section_count_matches_required(self):
        """
        Property: The section_count in output SHALL match the number of required sections.
        
        **Feature: ai-research-agents, Property 5: Paper structure completeness**
        **Validates: Requirements 2.5**
        """
        mock_llm = create_mock_llm_client()
        mock_orchestrator = create_mock_orchestrator()
        
        agent = WritingAgent(mock_llm, mock_orchestrator)
        
        research_context = {
            "topic": {"title": "Test Topic", "description": "Test description"}
        }
        
        result = await agent.compose_paper(research_context)
        
        assert result.output["section_count"] == len(WritingAgent.REQUIRED_SECTIONS)

    @pytest.mark.asyncio
    async def test_compose_paper_includes_title(self):
        """
        Property: The output SHALL include the paper title from the topic.
        
        **Feature: ai-research-agents, Property 5: Paper structure completeness**
        **Validates: Requirements 2.5**
        """
        mock_llm = create_mock_llm_client()
        mock_orchestrator = create_mock_orchestrator()
        
        agent = WritingAgent(mock_llm, mock_orchestrator)
        
        test_title = "Machine Learning in Healthcare"
        research_context = {
            "topic": {"title": test_title, "description": "Test description"}
        }
        
        result = await agent.compose_paper(research_context)
        
        assert "title" in result.output
        assert result.output["title"] == test_title

    @given(
        gaps=st.lists(gap_strategy, min_size=0, max_size=10),
        hypotheses=st.lists(hypothesis_strategy, min_size=0, max_size=10),
    )
    @settings(max_examples=50)
    @pytest.mark.asyncio
    async def test_compose_paper_handles_varying_context_sizes(
        self,
        gaps: List[str],
        hypotheses: List[Dict[str, str]],
    ):
        """
        Property: For any size of gaps and hypotheses lists, compose_paper SHALL
        return all required sections.
        
        **Feature: ai-research-agents, Property 5: Paper structure completeness**
        **Validates: Requirements 2.5**
        """
        mock_llm = create_mock_llm_client()
        mock_orchestrator = create_mock_orchestrator()
        
        agent = WritingAgent(mock_llm, mock_orchestrator)
        
        research_context = {
            "topic": {"title": "Test Topic", "description": "Test description"},
            "gaps": gaps,
            "hypotheses": hypotheses,
        }
        
        result = await agent.compose_paper(research_context)
        
        sections = result.output["sections"]
        
        for section_name in WritingAgent.REQUIRED_SECTIONS:
            assert section_name in sections, f"Missing required section: {section_name}"

    @pytest.mark.asyncio
    async def test_execute_calls_compose_paper(self):
        """
        Property: The execute method SHALL call compose_paper and return its result.
        
        **Feature: ai-research-agents, Property 5: Paper structure completeness**
        **Validates: Requirements 2.5**
        """
        mock_llm = create_mock_llm_client()
        mock_orchestrator = create_mock_orchestrator()
        
        agent = WritingAgent(mock_llm, mock_orchestrator)
        
        context = {
            "topic": {"title": "Test", "description": "Test desc"}
        }
        
        result = await agent.execute(context)
        
        assert isinstance(result, AgentResult)
        assert "sections" in result.output
        
        for section_name in WritingAgent.REQUIRED_SECTIONS:
            assert section_name in result.output["sections"]

    @pytest.mark.asyncio
    async def test_tokens_used_is_sum_of_all_sections(self):
        """
        Property: The tokens_used SHALL be the sum of tokens from all section generations.
        
        **Feature: ai-research-agents, Property 5: Paper structure completeness**
        **Validates: Requirements 2.5**
        """
        mock_llm = create_mock_llm_client()
        mock_orchestrator = create_mock_orchestrator()
        
        agent = WritingAgent(mock_llm, mock_orchestrator)
        
        research_context = {
            "topic": {"title": "Test", "description": "Test desc"}
        }
        
        result = await agent.compose_paper(research_context)
        
        # Each section uses 100 tokens (from mock), 5 sections total
        expected_tokens = 100 * len(WritingAgent.REQUIRED_SECTIONS)
        assert result.tokens_used == expected_tokens

    @pytest.mark.asyncio
    async def test_duration_is_positive(self):
        """
        Property: The duration_seconds SHALL be a positive number.
        
        **Feature: ai-research-agents, Property 5: Paper structure completeness**
        **Validates: Requirements 2.5**
        """
        mock_llm = create_mock_llm_client()
        mock_orchestrator = create_mock_orchestrator()
        
        agent = WritingAgent(mock_llm, mock_orchestrator)
        
        research_context = {
            "topic": {"title": "Test", "description": "Test desc"}
        }
        
        result = await agent.compose_paper(research_context)
        
        assert result.duration_seconds >= 0
