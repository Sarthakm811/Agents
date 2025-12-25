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
        # Pull a comprehensive paper set to support extensive citations for 20-30 page papers
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
            max_tokens=2500,  # comprehensive literature summary for extensive papers
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
            prompt=prompt, system_prompt=self.SYSTEM_PROMPT, max_tokens=900, temperature=0.6
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
            prompt=prompt, system_prompt=self.SYSTEM_PROMPT, max_tokens=900, temperature=0.7
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
            prompt=prompt, system_prompt=self.SYSTEM_PROMPT, max_tokens=1200, temperature=0.5
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

=== ABSOLUTE REQUIREMENTS (FAILURE TO FOLLOW = REJECTION) ===

1. CITATION FORMAT - IEEE STYLE ONLY (NO EXCEPTIONS):
   - Use ONLY numbered citations: [1], [2], [3], etc.
   - NEVER EVER use Author-Year format like "(Smith et al., 2020)" or "Smith et al. (2020)"
   - NEVER include inline references like "Chen et al. showed..." - write "Prior work showed... [1]"
   - Place citation numbers at sentence end before period: "...as demonstrated previously [1]."
   - Multiple citations: [1, 2, 3] or [1-3] for consecutive
   - DO NOT create separate reference lists within sections - there will be ONE list at the end
   - DO NOT write out author names with years anywhere in the text

2. RESEARCH FOCUS COHERENCE (CRITICAL):
   - ALL sections must discuss the SAME research topic and methodology
   - If Abstract mentions "lung lesion segmentation", then Methodology, Results, AND Conclusion must ALL be about lung lesion segmentation
   - Do NOT introduce new topics (like NLP, report generation) in later sections
   - The research focus stated in Abstract = focus in Introduction = focus in Methodology = focus in Results = focus in Discussion = focus in Conclusion
   - Pick ONE specific application domain and stick to it throughout

3. NO PLACEHOLDER TEXT:
   - NEVER write "[Insert IRB Approval Number]" or similar placeholders
   - NEVER write "[Insert Figure Here]" or "[Citation Needed]"
   - Instead write: "IRB approval will be obtained prior to data collection" or "Ethical approval is pending"
   - If you don't have specific information, write around it naturally

4. TENSE CONSISTENCY:
   - FUTURE TENSE for all proposed work: "will collect", "will analyze", "will employ"
   - PRESENT TENSE for facts: "GANs are generative models"
   - PAST TENSE only for citing completed prior work: "demonstrated [1]"

5. SPELLING - DOUBLE-CHECK THESE:
   - "Generative" NOT "Genrative"
   - "Field" NOT "Feild"
   - "Artificial" NOT "Artifical"
   - "Neural" NOT "Nueral"
   - "Algorithm" NOT "Alogrithm"
   - "Healthcare" NOT "Heathcare"

6. STRUCTURE:
   - Write in coherent paragraphs, NOT bullet points
   - Each paragraph should have a clear topic sentence
   - Use smooth transitions between paragraphs
   - Avoid repetition between sections

4. TEXT FORMATTING:
   - Do NOT include section titles in your output (they will be added separately)
   - Do NOT use markdown formatting (**, ##, etc.)
   - Write plain academic prose with proper punctuation
   - Use only standard ASCII characters - avoid special Unicode characters
   - Spell out abbreviations on first use

5. ACADEMIC VOICE:
   - Formal, objective tone
   - Avoid first person singular ("I") - use "we" or passive voice
   - Be precise and specific, avoid vague language"""

    # Required sections for comprehensive 20-30 page research proposals
    # Discussion section is critical for thorough analysis and interpretation
    REQUIRED_SECTIONS = ["abstract", "introduction", "methodology", "results", "discussion", "conclusion"]

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
            "discussion": self._get_discussion_prompt(context, topic),
            "conclusion": self._get_conclusion_prompt(context, topic)
        }
        
        # Token allocations for 20-30 page comprehensive research papers
        # Total ~13,500 tokens = ~10,000 words = ~20 pages minimum
        max_tokens_map = {
            "abstract": 400,           # ~300 words (expanded abstract)
            "introduction": 2800,      # ~2100 words (~4-5 pages with extensive lit review)
            "methodology": 3500,       # ~2600 words (~5 pages with detailed procedures)
            "results": 2800,           # ~2100 words (~4 pages with comprehensive findings)
            "discussion": 3200,        # ~2400 words (~5 pages with thorough analysis)
            "conclusion": 800,         # ~600 words (~1 page)
        }
        
        response = await self.llm_client.generate(
            prompt=prompts[section_name],
            system_prompt=self.SYSTEM_PROMPT,
            max_tokens=max_tokens_map.get(section_name, 800),
            temperature=0.5
        )
        return {"content": response.content, "tokens_used": response.tokens_used}
    
    def _get_abstract_prompt(self, context: Dict[str, Any], topic: Dict[str, Any]) -> str:
        # Extract keywords from topic for consistency
        keywords = topic.get('keywords', ['research', 'analysis', 'methodology'])
        if isinstance(keywords, list) and keywords:
            keywords_str = ', '.join(keywords[:5])
        else:
            keywords_str = topic.get('domain', 'research')
        
        return f"""Write a comprehensive research proposal abstract (250-350 words) as flowing paragraphs.

Topic: {topic.get('title', 'Research')}
Domain: {topic.get('domain', '')}
Keywords to incorporate: {keywords_str}

Write 2-3 paragraphs covering:
Paragraph 1: Background context, research gap, and significance (100-120 words)
Paragraph 2: Study objectives, methodology approach, and key research questions (100-120 words)
Paragraph 3: Expected contributions, implications, and potential impact (50-80 words)

CRITICAL RULES:
- Write as flowing paragraphs with proper transitions
- Do NOT include a title or "Abstract:" label
- DO NOT include ANY citations [1], [2], etc. in the abstract - IEEE prohibits citations in abstracts
- The research focus you state here MUST be maintained in ALL other sections
- Use FUTURE TENSE for proposed work
- SPELL CHECK: Generative, Field, Artificial, Neural (not Genrative, Feild, etc.)"""

    def _build_citation_reference_block(self, papers: List[Dict[str, Any]], limit: int = 10) -> str:
        """Format a short numbered reference map for prompts."""
        if not papers:
            return ""
        paper_refs = "\n\nCITATION REFERENCE (keep numbers consistent across ALL sections):\n"
        for i, p in enumerate(papers[:limit], 1):
            title = p.get('title', 'Unknown')[:80]
            paper_refs += f"[{i}] = {title}...\n"
        if len(papers) > limit:
            paper_refs += f"Additional sources available beyond [{limit}]"  # hint there are more
        return paper_refs

    def _get_introduction_prompt(self, context: Dict[str, Any], topic: Dict[str, Any]) -> str:
        papers = context.get('papers', [])
        paper_refs = self._build_citation_reference_block(papers, limit=20)
        
        return f"""Write a comprehensive Introduction section (2000-2500 words, approximately 4-5 pages) as flowing academic prose with multiple subsections.

Topic: {topic.get('title', 'Research')}
Literature Context: {context.get('literature_summary', '')[:800]}
Research Gaps: {self._format_list(context.get('gaps', []))[:500]}{paper_refs}

Structure your introduction with 8-10 SUBSTANTIAL paragraphs organized into implicit subsections:

SECTION 1: BACKGROUND & CONTEXT (3-4 paragraphs, ~600-800 words)
Paragraph 1: Introduce the broad research domain and its current significance. Explain why this field matters today.
Paragraph 2: Historical development and key milestones in the field. How did we get here? [Include 3-4 citations]
Paragraph 3: Current state of practice and existing approaches. What methods are currently used? [Include 3-4 citations]
Paragraph 4: Emerging trends and recent developments in the field. [Include 2-3 citations]

SECTION 2: LITERATURE REVIEW (3-4 paragraphs, ~700-900 words)
Paragraph 5: Foundational theories and seminal work. What are the theoretical underpinnings? [Include 4-5 citations]
Paragraph 6: Recent empirical studies and their findings. What has recent research discovered? [Include 4-5 citations]
Paragraph 7: Methodological approaches used in prior work. How have others tackled similar problems? [Include 3-4 citations]
Paragraph 8: Critical analysis of existing literature - strengths and limitations. [Include 2-3 citations]

SECTION 3: RESEARCH GAP & OBJECTIVES (2 paragraphs, ~400-500 words)
Paragraph 9: Specific research gap(s) this study addresses. What remains unknown or inadequately studied? Why is this gap important?
Paragraph 10: Clear research objectives, questions, and hypotheses. What will this study accomplish? (FUTURE TENSE)

SECTION 4: PAPER ORGANIZATION (1 paragraph, ~200-300 words)
Paragraph 11: Detailed roadmap of the paper structure and what each section will cover.

CRITICAL RULES:
- Use at least 15-20 UNIQUE citations distributed across the section
- Each paragraph should be 150-250 words (substantial and detailed)
- CITATION ACCURACY: [1] must reference paper [1] above, [2] must reference paper [2], etc.
- Each paragraph must have DIFFERENT content - NO repetition of ideas
- Write in complete paragraphs with smooth transitions
- Include specific examples, statistics, or findings from cited works
- Demonstrate deep understanding of the literature
- Do NOT repeat content from the abstract verbatim
- Spell-check all technical terms carefully"""

    def _get_methodology_prompt(self, context: Dict[str, Any], topic: Dict[str, Any]) -> str:
        methodology = context.get("methodology", {})
        meth_text = methodology.get("full_methodology", str(methodology)) if isinstance(methodology, dict) else str(methodology)
        papers = context.get('papers', [])
        paper_refs = self._build_citation_reference_block(papers, limit=20)
        return f"""Write a comprehensive Methodology section (2500-3000 words, approximately 5 pages) as flowing academic prose with clear subsections.

Topic: {topic.get('title', 'Research')}
Methodology Framework: {meth_text[:1000]}
Reference Map: Cite methodological precedents from the sources below to justify design choices.{paper_refs}

Structure with 10-12 DETAILED paragraphs organized into implicit subsections:

SECTION 1: RESEARCH DESIGN & APPROACH (2-3 paragraphs, ~500-700 words)
Paragraph 1: Overall research design and philosophical approach. Explain the research paradigm and why it's appropriate for this study. [Include 2-3 citations for methodological precedents]
Paragraph 2: Study type (experimental, observational, computational, etc.) and detailed rationale. Why is this design optimal for answering the research questions?
Paragraph 3: Research framework, theoretical model, or architectural design that will guide the study.

SECTION 2: PARTICIPANTS/DATA SOURCES (2 paragraphs, ~400-600 words)
Paragraph 4: Population, sampling strategy, and sample size determination. For deep learning: 5,000-50,000 samples; for surveys: 300-1,000 participants. Include power analysis or data requirements justification. [Cite similar studies for sample size rationale]
Paragraph 5: Inclusion/exclusion criteria, recruitment procedures, and data source specifications. Be specific about where and how data will be obtained.

SECTION 3: DATA COLLECTION PROCEDURES (2-3 paragraphs, ~500-700 words)
Paragraph 6: Detailed instruments, tools, and measurement procedures. Name specific software, hardware, questionnaires, or protocols.
Paragraph 7: Variables to be measured or collected - independent, dependent, control variables. Define operational definitions.
Paragraph 8: Data collection timeline, procedures, and quality control measures. How will data integrity be ensured?

SECTION 4: DATA ANALYSIS METHODS (2-3 paragraphs, ~600-800 words)
Paragraph 9: Statistical or computational analysis techniques. Name SPECIFIC tests, algorithms, or models (e.g., "mixed-effects ANOVA", "U-Net architecture with ResNet-50 backbone", "latent Dirichlet allocation"). [Include 3-4 citations for analytical methods]
Paragraph 10: Analysis software and computational resources. Specify versions, settings, and configurations.
Paragraph 11: Performance metrics and evaluation criteria (e.g., Dice Similarity Coefficient, F1-score, RMSE, Cohen's kappa). How will success be measured?

SECTION 5: VALIDITY & RELIABILITY (1-2 paragraphs, ~300-400 words)
Paragraph 12: Internal and external validity measures. How will threats to validity be addressed?
Paragraph 13 (if needed): Reliability measures and quality assurance procedures.

SECTION 6: ETHICAL CONSIDERATIONS (1 paragraph, ~200-300 words)
Paragraph 14: State "Ethical approval will be obtained from the Institutional Review Board prior to data collection." Discuss informed consent, data privacy, confidentiality, and risk mitigation.

CRITICAL RULES:
- FOCUS COHERENCE: Methodology must match the research described in Abstract
- Use FUTURE TENSE: "will be collected", "will employ", "will be analyzed"
- Include at least 8-10 citations distributed across the section
- Each paragraph should be 200-300 words (detailed and specific)
- NO PLACEHOLDERS: Never write "[Insert IRB Number]"
- Use IEEE citations [1], [2] ONLY - NEVER use (Author, Year) format
- Write in paragraphs, NOT bullet points
- Be specific with ALL methodological details
- SPELL CHECK all technical terms"""

    def _get_results_prompt(self, context: Dict[str, Any], topic: Dict[str, Any]) -> str:
        papers = context.get('papers', [])
        paper_refs = self._build_citation_reference_block(papers, limit=20)
        return f"""Write a comprehensive Results section (2000-2500 words, approximately 4 pages) as flowing academic prose with detailed subsections.

Topic: {topic.get('title', 'Research')}
Hypotheses: {self._format_hypotheses(context.get('hypotheses', []))[:600]}
Methodology Reference: {context.get('methodology', {})}{paper_refs}

Structure with 8-10 DETAILED paragraphs organized into implicit subsections:

SECTION 1: OVERVIEW OF FINDINGS (1 paragraph, ~250-300 words)
Paragraph 1: Brief summary of the main anticipated results and how they address the research questions. What will be the overarching story the data tells?

SECTION 2: PRIMARY FINDINGS (3-4 paragraphs, ~700-900 words)
Paragraph 2: FIRST MAJOR FINDING - Describe the primary expected result in detail. Present specific quantitative metrics with realistic ranges (e.g., "accuracy of 87.3±2.1%", "p < 0.001", "Dice coefficient of 0.84"). [Include 2-3 citations for comparison to prior benchmarks]
Paragraph 3: DETAILED BREAKDOWN - Break down the primary finding by subgroups, conditions, or categories. How will results vary across different segments?
Paragraph 4: SECOND MAJOR FINDING - Present the next most important expected result with detailed metrics and statistical analysis.
Paragraph 5: QUANTITATIVE ANALYSIS - Present expected statistical tests, confidence intervals, effect sizes, and significance levels. Be specific about tests (e.g., "paired t-test: t(49) = 4.23, p < 0.001, Cohen's d = 0.86").

SECTION 3: COMPARATIVE ANALYSIS (2-3 paragraphs, ~500-700 words)
Paragraph 6: BASELINE COMPARISONS - How will the proposed approach compare to existing baseline methods? Present expected performance differentials with specific metrics. [Include 3-4 citations to methods being compared]
Paragraph 7: BENCHMARKING RESULTS - Compare to state-of-the-art approaches from the literature. Which methods will the proposed approach outperform and by how much?
Paragraph 8 (if applicable): ABLATION STUDIES or SENSITIVITY ANALYSIS - What will happen when key components are modified? How robust will the results be?

SECTION 4: SECONDARY FINDINGS (2-3 paragraphs, ~400-600 words)
Paragraph 9: ADDITIONAL PATTERNS - Describe secondary trends, correlations, or insights expected from the data. What other interesting discoveries will emerge?
Paragraph 10: UNEXPECTED OBSERVATIONS - Discuss any anticipated edge cases, outliers, contradictions, or surprising patterns. Where might the approach face challenges?
Paragraph 11 (if needed): QUALITATIVE INSIGHTS - For applicable studies, describe expected qualitative patterns, themes, or observations.

CRITICAL RULES:
- FUTURE TENSE: "The analysis will reveal...", "Results will demonstrate...", "We expect to observe..."
- Include at least 8-10 unique citations comparing to prior work
- Each paragraph should be 200-300 words with substantial detail
- Include REALISTIC quantitative metrics appropriate to the domain (accuracy, precision, recall, F1, AUC, p-values, Dice scores, RMSE, R-squared, correlation coefficients, etc.)
- Present expected statistical test results with proper notation
- FOCUS COHERENCE: Results must directly address hypotheses and align with methodology
- Write in paragraphs, NOT bullet points or tables
- Use numbered citations [1], [2] per IEEE format
- NO PLACEHOLDERS or "Figure X shows" - describe patterns in prose
- Be specific about performance improvements (e.g., "15% reduction in error rate compared to [1]")"""

    def _get_conclusion_prompt(self, context: Dict[str, Any], topic: Dict[str, Any]) -> str:
        papers = context.get('papers', [])
        paper_refs = self._build_citation_reference_block(papers, limit=10)
        return f"""Write a comprehensive Conclusion section (600-800 words, approximately 1.5 pages) as flowing academic prose.

Topic: {topic.get('title', 'Research')}
Gaps Being Addressed: {self._format_list(context.get('gaps', []))[:300]}{paper_refs}

Write 5-6 SUBSTANTIAL paragraphs:

Paragraph 1: RESEARCH RECAP (120-150 words) - Begin by restating the research problem and objectives. Briefly remind readers what this study set out to accomplish and why it matters. Set the stage for summarizing contributions.

Paragraph 2: SUMMARY OF APPROACH (120-150 words) - Concisely describe the methodological approach taken without excessive detail. Highlight what made this approach novel or appropriate for addressing the research questions.

Paragraph 3: KEY CONTRIBUTIONS & FINDINGS (150-200 words) - Enumerate the main expected contributions this research will make. What are the 3-5 most important takeaways? Be specific about anticipated findings and their significance.

Paragraph 4: THEORETICAL SIGNIFICANCE (100-150 words) - Explain how this work will advance theoretical understanding in the domain. What conceptual insights will emerge? How will this reshape thinking about the phenomenon? [Include 1-2 citations]

Paragraph 5: PRACTICAL IMPLICATIONS (100-150 words) - Discuss expected real-world impact and applications. Who will benefit from these findings and how? Connect research to practical problems in industry, healthcare, education, policy, or society.

Paragraph 6: CLOSING VISION (100-150 words) - End with a forward-looking perspective. How will this research open new directions? What doors will it open? Paint a vision of how the field will evolve based on these contributions. End on an aspirational note about the potential impact.

CRITICAL RULES:
- FUTURE TENSE: "This study will...", "The research is expected to...", "Findings will contribute..."
- Include 2-3 citations when discussing significance relative to existing work
- NO detailed results, statistics, or methodology repetition
- Each paragraph should be 100-200 words (substantial and meaningful)
- Keep focused on the research stated in Abstract - do NOT introduce new topics
- Write in flowing paragraphs, NOT bullet points
- Balance between summarizing what was done and emphasizing impact
- End on a strong, inspirational note about future potential
- Spell-check all terms
- Demonstrate the work's value and significance clearly"""

    def _format_list(self, items: List[str]) -> str:
        if not items:
            return "None specified."
        return "\n".join([f"- {item[:100]}" for item in items[:5]])
    
    def _format_hypotheses(self, hypotheses: List[Dict[str, str]]) -> str:
        if not hypotheses:
            return "None specified."
        return "\n".join([f"- {h.get('title', 'H')}: {h.get('description', '')[:80]}" for h in hypotheses[:5]])

    def _get_discussion_prompt(self, context: Dict[str, Any], topic: Dict[str, Any]) -> str:
        papers = context.get('papers', [])
        paper_refs = self._build_citation_reference_block(papers, limit=20)
        return f"""Write a comprehensive Discussion section (2500-3000 words, approximately 5 pages) as flowing academic prose with detailed analysis.

Topic: {topic.get('title', 'Research')}
Research Gaps: {self._format_list(context.get('gaps', []))[:300]}
Hypotheses: {self._format_hypotheses(context.get('hypotheses', []))[:600]}{paper_refs}

Structure with 10-12 DETAILED paragraphs organized into implicit subsections:

SECTION 1: INTERPRETATION OF FINDINGS (3-4 paragraphs, ~700-900 words)
Paragraph 1: OVERVIEW - Restate the main expected findings briefly, then provide initial interpretation. What will the results fundamentally reveal about the research problem?
Paragraph 2: PRIMARY FINDING INTERPRETATION - Deep dive into what the main result means theoretically and practically. Why will this finding emerge? What mechanisms or principles explain it? [Include 3-4 citations to theoretical frameworks]
Paragraph 3: SECONDARY FINDINGS INTERPRETATION - Analyze what the additional results suggest. How do multiple findings interconnect?
Paragraph 4: UNEXPECTED PATTERNS - Discuss the implications of surprising or counterintuitive findings. What do these reveal about the phenomenon under study?

SECTION 2: COMPARISON WITH LITERATURE (3 paragraphs, ~600-800 words)
Paragraph 5: ALIGNMENT WITH PRIOR WORK - Discuss how findings will support, extend, or validate existing literature. Which prior studies [1], [2], [3] will these results corroborate? Why is this convergence important? [Include 4-5 citations]
Paragraph 6: DIVERGENCE FROM LITERATURE - Where will results contradict or challenge existing findings? What could explain these discrepancies? [Include 3-4 citations to contrasting work]
Paragraph 7: CONTRIBUTION TO DEBATE - How will this work resolve existing controversies or advance ongoing debates in the field? Position findings within broader scholarly discourse. [Include 2-3 citations]

SECTION 3: THEORETICAL & PRACTICAL IMPLICATIONS (2-3 paragraphs, ~500-700 words)
Paragraph 8: THEORETICAL CONTRIBUTIONS - What new theoretical insights will emerge? How will this advance conceptual understanding of the phenomenon? Will new models or frameworks be needed?
Paragraph 9: PRACTICAL APPLICATIONS - Describe specific real-world uses of these findings. Who will benefit and how? Be concrete about applications in industry, healthcare, education, policy, etc.
Paragraph 10 (if needed): METHODOLOGICAL CONTRIBUTIONS - How will the methodology itself advance the field? What new techniques or approaches will be demonstrated?

SECTION 4: LIMITATIONS (2 paragraphs, ~400-600 words)
Paragraph 11: METHODOLOGICAL LIMITATIONS - Acknowledge constraints in study design, sample size, measurement instruments, generalizability, or analytical approaches. Be specific but not overly self-critical.
Paragraph 12: SCOPE AND BOUNDARY CONDITIONS - Discuss contexts or conditions where findings may not apply. What are the edges of generalizability?

SECTION 5: FUTURE RESEARCH DIRECTIONS (1-2 paragraphs, ~300-500 words)
Paragraph 13: IMMEDIATE NEXT STEPS - Suggest 3-5 specific follow-up studies that directly build on this work. Be concrete about what should be investigated next.
Paragraph 14 (if needed): LONG-TERM RESEARCH AGENDA - Outline broader questions or directions for the field that stem from these findings.

CRITICAL RULES:
- FUTURE/CONDITIONAL TENSE: "The findings will suggest...", "This would indicate...", "Results are expected to demonstrate..."
- Include at least 12-15 unique citations throughout the discussion
- Each paragraph should be 200-300 words with deep analysis
- Do NOT simply repeat results - provide rich INTERPRETATION of their meaning
- Connect findings to broader theoretical frameworks and literature
- Balance discussion of strengths and limitations
- Be specific about implications rather than vague statements
- FOCUS COHERENCE: Discussion must address the same research focus as Abstract and other sections
- Write in complete paragraphs, NOT bullet points
- Use numbered citations [1], [2] per IEEE format"""


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
        results["papers"] = lit_result.output.get("papers", [])  # Include papers for citation sync
        
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
