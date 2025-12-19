# src/agents/swarm.py
"""
Agentic Research Swarm Implementation
-------------------------------------
Implements specialized research agents that work together to conduct
academic research: literature review, gap analysis, hypothesis generation,
methodology design, and paper writing.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from src.agents.llm_client import LLMClient, LLMResponse
from src.tools.orchestrator import AutonomousToolOrchestrator, Paper

logger = logging.getLogger(__name__)


@dataclass
class ResearchTopic:
    """Research topic configuration."""
    title: str
    description: str
    domain: str = "general"
    complexity: str = "intermediate"
    keywords: List[str] = field(default_factory=list)


@dataclass
class AgentResult:
    """Result from an agent execution."""
    agent_name: str
    output: Any
    tokens_used: int
    duration_seconds: float


class BaseAgent:
    """Base class for all research agents."""
    
    def __init__(self, llm_client: LLMClient, orchestrator: AutonomousToolOrchestrator):
        self.llm_client = llm_client
        self.orchestrator = orchestrator
        self.name = self.__class__.__name__
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        raise NotImplementedError("Subclasses must implement execute()")


class LiteratureAgent(BaseAgent):
    """Agent that searches and summarizes academic literature."""
    
    SYSTEM_PROMPT = """You are an expert academic researcher specializing in literature review.
Your task is to analyze and summarize academic papers to provide a comprehensive overview
of the current state of research on a given topic."""

    async def search_and_summarize(self, topic: ResearchTopic) -> AgentResult:
        start_time = time.time()
        total_tokens = 0
        
        search_query = self._build_search_query(topic)
        papers = await self.orchestrator.search_all_sources(search_query, max_results=20)
        
        if not papers:
            return AgentResult(
                agent_name=self.name,
                output={"summary": "No papers found.", "papers": [], "paper_count": 0},
                tokens_used=0,
                duration_seconds=time.time() - start_time
            )
        
        summary_prompt = self._build_summary_prompt(topic, papers)
        response = await self.llm_client.generate(
            prompt=summary_prompt,
            system_prompt=self.SYSTEM_PROMPT,
            max_tokens=2000,
            temperature=0.5
        )
        total_tokens += response.tokens_used
        
        return AgentResult(
            agent_name=self.name,
            output={
                "summary": response.content,
                "papers": [self._paper_to_dict(p) for p in papers],
                "paper_count": len(papers)
            },
            tokens_used=total_tokens,
            duration_seconds=time.time() - start_time
        )
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        topic = context.get("topic")
        if not topic:
            raise ValueError("Context must contain 'topic' key")
        if isinstance(topic, dict):
            topic = ResearchTopic(**topic)
        return await self.search_and_summarize(topic)
    
    def _build_search_query(self, topic: ResearchTopic) -> str:
        parts = [topic.title]
        if topic.keywords:
            parts.extend(topic.keywords[:3])
        return " ".join(parts)
    
    def _build_summary_prompt(self, topic: ResearchTopic, papers: List[Paper]) -> str:
        papers_text = "\n\n".join([
            f"Title: {p.title}\nAuthors: {', '.join(p.authors)}\nAbstract: {p.abstract}"
            for p in papers[:15]
        ])
        return f"""Research Topic: {topic.title}
Description: {topic.description}

Analyze these papers and provide a literature review summary:
{papers_text}"""

    def _paper_to_dict(self, paper: Paper) -> Dict[str, Any]:
        return {
            "title": paper.title, "authors": paper.authors, "abstract": paper.abstract,
            "publication_date": paper.publication_date, "source_url": paper.source_url,
            "doi": paper.doi, "citation_count": paper.citation_count, "source": paper.source
        }



class GapAnalysisAgent(BaseAgent):
    """Agent that identifies research gaps from literature analysis."""
    
    SYSTEM_PROMPT = """You are an expert research analyst specializing in identifying research gaps.
Analyze existing literature and identify underexplored areas and opportunities for novel contributions."""

    async def identify_gaps(self, literature_summary: str, topic: ResearchTopic) -> AgentResult:
        start_time = time.time()
        
        prompt = f"""Research Topic: {topic.title}
Description: {topic.description}

Literature Summary:
{literature_summary}

Identify 3-5 specific research gaps and opportunities."""

        response = await self.llm_client.generate(
            prompt=prompt, system_prompt=self.SYSTEM_PROMPT, max_tokens=1500, temperature=0.6
        )
        gaps = self._parse_gaps(response.content)
        
        return AgentResult(
            agent_name=self.name,
            output={"gaps": gaps, "raw_analysis": response.content, "gap_count": len(gaps)},
            tokens_used=response.tokens_used,
            duration_seconds=time.time() - start_time
        )
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        topic = context.get("topic")
        literature_summary = context.get("literature_summary", "")
        if not topic:
            raise ValueError("Context must contain 'topic' key")
        if isinstance(topic, dict):
            topic = ResearchTopic(**topic)
        return await self.identify_gaps(literature_summary, topic)
    
    def _parse_gaps(self, content: str) -> List[str]:
        gaps = []
        current_gap = []
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped and (stripped[0].isdigit() or stripped.startswith("Gap") or stripped.startswith("-")):
                if current_gap:
                    gaps.append(" ".join(current_gap))
                current_gap = [stripped]
            elif stripped and current_gap:
                current_gap.append(stripped)
        if current_gap:
            gaps.append(" ".join(current_gap))
        return gaps if gaps else [content.strip()]


class HypothesisAgent(BaseAgent):
    """Agent that generates research hypotheses based on identified gaps."""
    
    SYSTEM_PROMPT = """You are an expert research scientist specializing in hypothesis generation.
Propose novel, testable research hypotheses based on identified gaps in the literature."""

    async def generate_hypotheses(self, gaps: List[str], topic: ResearchTopic) -> AgentResult:
        start_time = time.time()
        gaps_text = "\n".join([f"- {gap}" for gap in gaps])
        
        prompt = f"""Research Topic: {topic.title}
Domain: {topic.domain}
Complexity: {topic.complexity}

Research Gaps:
{gaps_text}

Generate 3-5 novel research hypotheses with rationale and testing approach."""

        response = await self.llm_client.generate(
            prompt=prompt, system_prompt=self.SYSTEM_PROMPT, max_tokens=1500, temperature=0.7
        )
        hypotheses = self._parse_hypotheses(response.content)
        
        return AgentResult(
            agent_name=self.name,
            output={"hypotheses": hypotheses, "raw_content": response.content, "hypothesis_count": len(hypotheses)},
            tokens_used=response.tokens_used,
            duration_seconds=time.time() - start_time
        )
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        topic = context.get("topic")
        gaps = context.get("gaps", [])
        if not topic:
            raise ValueError("Context must contain 'topic' key")
        if isinstance(topic, dict):
            topic = ResearchTopic(**topic)
        return await self.generate_hypotheses(gaps, topic)
    
    def _parse_hypotheses(self, content: str) -> List[Dict[str, str]]:
        hypotheses = []
        current_hypothesis = {}
        current_text = []
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped and (stripped.lower().startswith("hypothesis") or (stripped[0].isdigit() and ":" in stripped[:10])):
                if current_text:
                    current_hypothesis["description"] = " ".join(current_text)
                    if current_hypothesis.get("title"):
                        hypotheses.append(current_hypothesis)
                current_hypothesis = {"title": stripped}
                current_text = []
            elif stripped:
                current_text.append(stripped)
        if current_text:
            current_hypothesis["description"] = " ".join(current_text)
            if current_hypothesis.get("title"):
                hypotheses.append(current_hypothesis)
        return hypotheses if hypotheses else [{"title": "Research Hypothesis", "description": content.strip()}]



class MethodologyAgent(BaseAgent):
    """Agent that designs research methodology."""
    
    SYSTEM_PROMPT = """You are an expert research methodologist.
Design rigorous, appropriate research methodologies for testing hypotheses."""

    async def design_methodology(self, hypotheses: List[Dict[str, str]], topic: ResearchTopic) -> AgentResult:
        start_time = time.time()
        hypotheses_text = "\n".join([f"- {h.get('title', 'Hypothesis')}: {h.get('description', '')[:200]}" for h in hypotheses])
        
        prompt = f"""Research Topic: {topic.title}
Domain: {topic.domain}
Complexity: {topic.complexity}

Hypotheses:
{hypotheses_text}

Design a comprehensive methodology including:
1. Research Design
2. Data Collection Methods
3. Analysis Approach
4. Validity and Reliability
5. Ethical Considerations
6. Timeline and Resources"""

        response = await self.llm_client.generate(
            prompt=prompt, system_prompt=self.SYSTEM_PROMPT, max_tokens=2000, temperature=0.5
        )
        methodology = self._parse_methodology(response.content)
        
        return AgentResult(
            agent_name=self.name,
            output={"methodology": methodology, "raw_content": response.content},
            tokens_used=response.tokens_used,
            duration_seconds=time.time() - start_time
        )
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        topic = context.get("topic")
        hypotheses = context.get("hypotheses", [])
        if not topic:
            raise ValueError("Context must contain 'topic' key")
        if isinstance(topic, dict):
            topic = ResearchTopic(**topic)
        return await self.design_methodology(hypotheses, topic)
    
    def _parse_methodology(self, content: str) -> Dict[str, str]:
        sections = {"research_design": "", "data_collection": "", "analysis_approach": "",
                    "validity_reliability": "", "ethical_considerations": "", "timeline_resources": "",
                    "full_methodology": content}
        current_section = None
        current_content = []
        
        for line in content.split("\n"):
            lower = line.lower().strip()
            new_section = None
            if "research design" in lower:
                new_section = "research_design"
            elif "data collection" in lower:
                new_section = "data_collection"
            elif "analysis" in lower:
                new_section = "analysis_approach"
            elif "validity" in lower or "reliability" in lower:
                new_section = "validity_reliability"
            elif "ethical" in lower:
                new_section = "ethical_considerations"
            elif "timeline" in lower or "resource" in lower:
                new_section = "timeline_resources"
            
            if new_section:
                if current_section and current_content:
                    sections[current_section] = "\n".join(current_content)
                current_section = new_section
                current_content = []
            elif current_section:
                current_content.append(line)
        
        if current_section and current_content:
            sections[current_section] = "\n".join(current_content)
        return sections



class WritingAgent(BaseAgent):
    """Agent that composes the research paper with all required sections."""
    
    SYSTEM_PROMPT = """You are an expert academic writer with extensive experience in scholarly publishing.
You are writing a RESEARCH PROPOSAL that presents a planned original study based on identified gaps in the literature.

CRITICAL FORMATTING GUIDELINES:
1. TENSE CONSISTENCY:
   - Use FUTURE TENSE for proposed work ("This study will...", "We propose to...")
   - Use PRESENT TENSE only for established facts from literature
   - Do NOT write as if the study has been completed

2. STRUCTURE:
   - Write in coherent paragraphs, NOT bullet points or fragmented sentences
   - Each paragraph should have a clear topic sentence
   - Use smooth transitions between paragraphs
   - Avoid repetition between sections

3. CITATION FORMAT:
   - When referencing literature, use numbered citations like [1], [2], etc.
   - Place citations at the end of the relevant sentence before the period
   - Multiple citations: [1, 2, 3] or [1-3] for consecutive

4. FORMATTING:
   - Do NOT include section titles in your output (they will be added separately)
   - Do NOT use markdown formatting (**, ##, etc.)
   - Write plain academic prose
   - Use consistent terminology throughout

5. ACADEMIC VOICE:
   - Formal, objective tone
   - Avoid first person singular ("I") - use "we" or passive voice
   - Be precise and specific, avoid vague language"""

    REQUIRED_SECTIONS = ["abstract", "introduction", "methodology", "results", "conclusion"]

    async def compose_paper(self, research_context: Dict[str, Any]) -> AgentResult:
        start_time = time.time()
        total_tokens = 0
        
        topic = research_context.get("topic", {})
        if isinstance(topic, ResearchTopic):
            topic = {"title": topic.title, "description": topic.description, "domain": topic.domain}
        
        paper_sections = {}
        
        # Generate each required section
        for section_name in self.REQUIRED_SECTIONS:
            section_result = await self._generate_section(section_name, research_context, topic)
            paper_sections[section_name] = section_result["content"]
            total_tokens += section_result["tokens_used"]
        
        return AgentResult(
            agent_name=self.name,
            output={
                "sections": paper_sections,
                "title": topic.get("title", "Research Paper"),
                "section_count": len(paper_sections)
            },
            tokens_used=total_tokens,
            duration_seconds=time.time() - start_time
        )
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        return await self.compose_paper(context)
    
    async def _generate_section(self, section_name: str, context: Dict[str, Any], topic: Dict[str, Any]) -> Dict[str, Any]:
        prompts = {
            "abstract": self._get_abstract_prompt(context, topic),
            "introduction": self._get_introduction_prompt(context, topic),
            "methodology": self._get_methodology_prompt(context, topic),
            "results": self._get_results_prompt(context, topic),
            "conclusion": self._get_conclusion_prompt(context, topic)
        }
        
        max_tokens_map = {"abstract": 400, "introduction": 800, "methodology": 1000, "results": 800, "conclusion": 600}
        
        response = await self.llm_client.generate(
            prompt=prompts[section_name],
            system_prompt=self.SYSTEM_PROMPT,
            max_tokens=max_tokens_map.get(section_name, 800),
            temperature=0.5
        )
        return {"content": response.content, "tokens_used": response.tokens_used}
    
    def _get_abstract_prompt(self, context: Dict[str, Any], topic: Dict[str, Any]) -> str:
        return f"""Write a research proposal abstract (200-250 words) as a SINGLE COHERENT PARAGRAPH.

Topic: {topic.get('title', 'Research')}
Domain: {topic.get('domain', '')}

The abstract must flow as continuous prose covering:
- Background context (1-2 sentences, present tense)
- Research gap being addressed (1 sentence)
- Study objectives (1-2 sentences, future tense with "will")
- Proposed methodology overview (1-2 sentences, future tense)
- Expected contributions (1-2 sentences, future tense)

IMPORTANT:
- Write as ONE paragraph with no line breaks
- Do NOT include a title or "Abstract:" label
- Do NOT use bullet points or numbered lists
- Use future tense for proposed work
- Do NOT mention "findings" or "results" as if completed"""

    def _get_introduction_prompt(self, context: Dict[str, Any], topic: Dict[str, Any]) -> str:
        return f"""Write the Introduction section (500-700 words) as flowing academic prose.

Topic: {topic.get('title', 'Research')}
Literature Context: {context.get('literature_summary', '')[:600]}
Research Gaps: {self._format_list(context.get('gaps', []))[:400]}

Write 4-5 paragraphs covering:
Paragraph 1: Opening hook - why this topic matters now (present tense)
Paragraph 2: Literature review - key findings from existing research, use citations [1], [2], etc.
Paragraph 3: Research gap - what remains unknown or unaddressed
Paragraph 4: Research objectives - what this study will investigate (future tense)
Paragraph 5: Paper structure - brief roadmap of remaining sections

IMPORTANT:
- Write in complete paragraphs, NOT bullet points
- Use numbered citations [1], [2] when referencing literature
- Smooth transitions between paragraphs
- Do NOT repeat content from the abstract
- Do NOT include section headers within the text"""

    def _get_methodology_prompt(self, context: Dict[str, Any], topic: Dict[str, Any]) -> str:
        methodology = context.get("methodology", {})
        meth_text = methodology.get("full_methodology", str(methodology)) if isinstance(methodology, dict) else str(methodology)
        return f"""Write the Methodology section (600-800 words) as flowing academic prose.

Topic: {topic.get('title', 'Research')}
Methodology Framework: {meth_text[:800]}

Write 5-6 paragraphs covering:
Paragraph 1: Research design - type of study and rationale
Paragraph 2: Participants/Data sources - sampling strategy, inclusion criteria
Paragraph 3: Data collection - instruments, procedures to be used
Paragraph 4: Data analysis - analytical techniques to be employed
Paragraph 5: Validity and reliability - how quality will be ensured
Paragraph 6: Ethical considerations - IRB approval, consent, data protection

IMPORTANT:
- Use FUTURE TENSE throughout ("will be collected", "will employ")
- Write in complete paragraphs, NOT bullet points or numbered lists
- Be specific about methods, not vague
- Do NOT include subsection headers like "3.1 Research Design"
- This is a PROPOSAL - describe what WILL BE done"""

    def _get_results_prompt(self, context: Dict[str, Any], topic: Dict[str, Any]) -> str:
        return f"""Write the Expected Outcomes section (400-500 words) as flowing academic prose.

Topic: {topic.get('title', 'Research')}
Research Hypotheses: {self._format_hypotheses(context.get('hypotheses', []))[:500]}

Write 3-4 paragraphs covering:
Paragraph 1: Expected findings - what results are anticipated based on hypotheses
Paragraph 2: Theoretical implications - how findings will contribute to existing theory
Paragraph 3: Practical applications - potential real-world impact and applications
Paragraph 4: Conceptual framework - the model or framework being proposed

IMPORTANT:
- Use FUTURE TENSE throughout ("It is anticipated that...", "Results will likely show...")
- Do NOT present actual data or completed results
- Write in complete paragraphs, NOT bullet points
- This describes what you EXPECT to discover, not what you found
- Do NOT include subsection headers"""

    def _get_conclusion_prompt(self, context: Dict[str, Any], topic: Dict[str, Any]) -> str:
        return f"""Write the Conclusion section (300-400 words) as flowing academic prose.

Topic: {topic.get('title', 'Research')}
Gaps Being Addressed: {self._format_list(context.get('gaps', []))[:300]}

Write 3-4 paragraphs covering:
Paragraph 1: Summary - brief recap of the proposed research and its objectives
Paragraph 2: Expected contributions - how this research will advance the field (future tense)
Paragraph 3: Limitations - acknowledged constraints of the proposed study
Paragraph 4: Future directions and closing - how this work could lead to further research

IMPORTANT:
- Use future tense for proposed contributions
- Be realistic and honest about limitations
- Write in complete paragraphs, NOT bullet points
- End with a strong closing statement on significance
- Do NOT include subsection headers"""

    def _format_list(self, items: List[str]) -> str:
        if not items:
            return "None specified."
        return "\n".join([f"- {item[:100]}" for item in items[:5]])
    
    def _format_hypotheses(self, hypotheses: List[Dict[str, str]]) -> str:
        if not hypotheses:
            return "None specified."
        return "\n".join([f"- {h.get('title', 'H')}: {h.get('description', '')[:80]}" for h in hypotheses[:5]])



class AgenticResearchSwarm:
    """Orchestrates multiple research agents to conduct end-to-end research.
    
    This class coordinates the execution of specialized research agents in sequence:
    1. LiteratureAgent - searches and summarizes academic papers
    2. GapAnalysisAgent - identifies research gaps from literature
    3. HypothesisAgent - generates research hypotheses based on gaps
    4. MethodologyAgent - designs research methodology
    5. WritingAgent - composes the final research paper
    
    The pipeline provides real-time progress updates via callback and tracks
    performance metrics including tasks completed, active agents, and token usage.
    """
    
    PIPELINE_STAGES = [
        "literature_review",
        "gap_analysis", 
        "hypothesis_generation",
        "methodology",
        "writing"
    ]
    
    def __init__(self, config=None):
        self.config = config or {}
        self.agents: List[BaseAgent] = []
        self._metrics = {
            "total_agents": 5,
            "active_agents": 0,
            "tasks_completed": 0,
            "total_tokens": 0,
            "total_duration": 0.0
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Return a copy of current performance metrics.
        
        Returns
        -------
        Dict[str, Any]
            Dictionary containing:
            - total_agents: Total number of agents in the pipeline
            - active_agents: Number of currently executing agents (0 or 1)
            - tasks_completed: Number of agent tasks completed
            - total_tokens: Total LLM tokens used
            - total_duration: Total pipeline execution time in seconds
        """
        return dict(self._metrics)
    
    def reset_metrics(self) -> None:
        """Reset all metrics to initial values."""
        self._metrics = {
            "total_agents": 5,
            "active_agents": 0,
            "tasks_completed": 0,
            "total_tokens": 0,
            "total_duration": 0.0
        }
    
    async def _execute_agent(
        self,
        agent: BaseAgent,
        context: Dict[str, Any],
        stage_name: str,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> AgentResult:
        """Execute a single agent with metrics tracking.
        
        Parameters
        ----------
        agent : BaseAgent
            The agent to execute.
        context : Dict[str, Any]
            Context data for the agent.
        stage_name : str
            Name of the current pipeline stage.
        progress_callback : Optional[Callable[[str, int], None]]
            Callback for progress updates.
            
        Returns
        -------
        AgentResult
            Result from the agent execution.
        """
        # Signal agent is starting
        self._metrics["active_agents"] = 1
        
        if progress_callback:
            progress_callback(stage_name, 0)
        
        # Execute the agent
        result = await agent.execute(context)
        
        # Update metrics after completion
        self._metrics["tasks_completed"] += 1
        self._metrics["total_tokens"] += result.tokens_used
        self._metrics["active_agents"] = 0
        
        if progress_callback:
            progress_callback(stage_name, 100)
        
        return result
    
    async def execute_pipeline(
        self,
        topic: ResearchTopic,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> Dict[str, Any]:
        """Execute the full research pipeline.
        
        Runs all research agents in sequence, passing results from each stage
        to the next. Provides real-time progress updates via callback.
        
        Parameters
        ----------
        topic : ResearchTopic
            The research topic to investigate.
        progress_callback : Optional[Callable[[str, int], None]]
            Callback for progress updates (stage_name, progress_percent).
            Called with 0 when a stage starts and 100 when it completes.
            
        Returns
        -------
        Dict[str, Any]
            Complete research results including:
            - topic: The original research topic
            - literature: Literature review results
            - literature_summary: Summary text from literature review
            - gap_analysis: Gap analysis results
            - gaps: List of identified research gaps
            - hypothesis_generation: Hypothesis generation results
            - hypotheses: List of generated hypotheses
            - methodology_design: Methodology design results
            - methodology: Designed methodology details
            - paper: Generated paper with all sections
            - metrics: Performance metrics from the pipeline
        """
        from src.utils.config import ConfigManager
        
        # Reset metrics for new pipeline execution
        self.reset_metrics()
        
        # Load configuration
        config = ConfigManager.load_from_env()
        llm_client = LLMClient(config)
        
        # Pass Semantic Scholar API key to orchestrator
        orchestrator_config = dict(self.config)
        if config.semantic_scholar_api_key:
            orchestrator_config["semantic_scholar_api_key"] = config.semantic_scholar_api_key
        orchestrator = AutonomousToolOrchestrator(orchestrator_config)
        
        results: Dict[str, Any] = {"topic": topic}
        start_time = time.time()
        
        # Stage 1: Literature Review
        lit_agent = LiteratureAgent(llm_client, orchestrator)
        lit_result = await self._execute_agent(
            lit_agent, 
            {"topic": topic}, 
            "literature_review",
            progress_callback
        )
        results["literature"] = lit_result.output
        results["literature_summary"] = lit_result.output.get("summary", "")
        
        # Stage 2: Gap Analysis
        gap_agent = GapAnalysisAgent(llm_client, orchestrator)
        gap_result = await self._execute_agent(
            gap_agent,
            {
                "topic": topic,
                "literature_summary": results["literature_summary"]
            },
            "gap_analysis",
            progress_callback
        )
        results["gap_analysis"] = gap_result.output
        results["gaps"] = gap_result.output.get("gaps", [])
        
        # Stage 3: Hypothesis Generation
        hyp_agent = HypothesisAgent(llm_client, orchestrator)
        hyp_result = await self._execute_agent(
            hyp_agent,
            {
                "topic": topic,
                "gaps": results["gaps"]
            },
            "hypothesis_generation",
            progress_callback
        )
        results["hypothesis_generation"] = hyp_result.output
        results["hypotheses"] = hyp_result.output.get("hypotheses", [])
        
        # Stage 4: Methodology Design
        meth_agent = MethodologyAgent(llm_client, orchestrator)
        meth_result = await self._execute_agent(
            meth_agent,
            {
                "topic": topic,
                "hypotheses": results["hypotheses"]
            },
            "methodology",
            progress_callback
        )
        results["methodology_design"] = meth_result.output
        results["methodology"] = meth_result.output.get("methodology", {})
        
        # Stage 5: Paper Writing
        write_agent = WritingAgent(llm_client, orchestrator)
        write_result = await self._execute_agent(
            write_agent,
            results,
            "writing",
            progress_callback
        )
        results["paper"] = write_result.output
        
        # Finalize metrics
        self._metrics["total_duration"] = time.time() - start_time
        results["metrics"] = self.get_performance_metrics()
        
        return results
