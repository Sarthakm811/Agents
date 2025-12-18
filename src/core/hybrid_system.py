# src/core/hybrid_system.py
"""
Main Hybrid Research System that combines originality guardrails with agentic autonomy.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from ..originality.guardrails import OriginalityGuardrailSystem
from ..agents.swarm import AgenticResearchSwarm
from ..tools.orchestrator import AutonomousToolOrchestrator
from ..authorship.paper_builder import AuthorCentricPaperBuilder
from ..publication.packager import PublicationReadyPackager
from ..ethics.governance import EthicalGovernanceSystem

logger = logging.getLogger(__name__)

@dataclass
class ResearchTopic:
    """Research topic data structure"""
    title: str
    domain: str
    keywords: List[str]
    complexity: str  # "basic", "intermediate", "advanced"
    constraints: Optional[Dict[str, Any]] = None

class HybridResearchSystem:
    """
    Main system class that orchestrates the entire hybrid research process.
    Combines originality verification with full agentic autonomy.
    """
    
    def __init__(
        self,
        research_topic: ResearchTopic,
        author_name: str,
        author_institution: str,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the hybrid research system.
        
        Args:
            research_topic: Research topic with metadata
            author_name: Name of the human author
            author_institution: Author's institution
            config: Optional configuration dictionary
        """
        self.topic = research_topic
        self.author_name = author_name
        self.author_institution = author_institution
        self.config = config or {}
        self.start_time = datetime.now()
        
        # Initialize subsystems
        logger.info(f"Initializing Hybrid Research System for: {author_name}")
        logger.info(f"Research Topic: {research_topic.title}")
        
        # PHASE 1: ORIGINALITY GUARDRAILS
        self.originality_layer = OriginalityGuardrailSystem(
            config=self.config.get('originality', {})
        )
        
        # PHASE 2: AGENTIC RESEARCH EXECUTION
        self.autonomous_agents = AgenticResearchSwarm(
            config=self.config.get('agents', {})
        )
        self.tool_orchestrator = AutonomousToolOrchestrator(
            config=self.config.get('tools', {})
        )
        
        # PHASE 3: AUTHORSHIP & PUBLICATION
        self.authorship_manager = AuthorCentricPaperBuilder(
            author_name=author_name,
            institution=author_institution,
            config=self.config.get('authorship', {})
        )
        self.publication_engine = PublicationReadyPackager(
            config=self.config.get('publication', {})
        )
        
        # ETHICS & STATE MANAGEMENT
        self.ethics_controller = EthicalGovernanceSystem(
            author_name=author_name,
            config=self.config.get('ethics', {})
        )
        
        # State tracking
        self.current_stage = "initialized"
        self.research_artifacts = {}
        self.originality_scores = {}
        
    def conduct_hybrid_research(self) -> Dict[str, Any]:
        """
        Complete autonomous research with originality guarantees.
        
        Returns:
            Dictionary containing all research outputs
        """
        logger.info("="*70)
        logger.info("🔬 HYBRID RESEARCH SYSTEM STARTED")
        logger.info(f"👤 Author: {self.author_name}")
        logger.info(f"🏫 Institution: {self.author_institution}")
        logger.info(f"📚 Topic: {self.topic.title}")
        logger.info(f"🏷️ Domain: {self.topic.domain}")
        logger.info("="*70)
        
        # STAGE 0: PRE-RESEARCH ORIGINALITY SCREENING
        logger.info("Stage 0: Pre-research originality screening...")
        screening_result = self.pre_research_screening()
        
        if not screening_result.get('proceed', False):
            logger.warning(f"Topic not sufficiently original: {screening_result.get('message')}")
            return self.handle_non_original_topic(screening_result)
        
        # STAGE 1: CREATE AUTONOMOUS RESEARCH PLAN
        logger.info("Stage 1: Creating autonomous research plan...")
        research_plan = self.create_autonomous_research_plan()
        self.research_artifacts['research_plan'] = research_plan
        
        # STAGE 2: EXECUTE AGENTIC RESEARCH WITH GUARDS
        logger.info("Stage 2: Executing agentic research with originality guards...")
        research_results = self.execute_agentic_research_with_guards(research_plan)
        self.research_artifacts['research_results'] = research_results
        
        # STAGE 3: PREPARE AUTHOR PUBLICATION PACKAGE
        logger.info("Stage 3: Preparing author publication package...")
        final_output = self.prepare_author_publication_package(research_results)
        
        # FINAL: GENERATE SYSTEM REPORT
        logger.info("Generating system report...")
        system_report = self.generate_system_report()
        final_output['system_report'] = system_report
        
        logger.info("✅ Hybrid research completed successfully!")
        return final_output
    
    def pre_research_screening(self) -> Dict[str, Any]:
        """
        Screen the research topic for originality before starting.
        
        Returns:
            Dictionary with screening results
        """
        try:
            # Check topic originality
            originality_check = self.originality_layer.validate_topic_originality(
                self.topic.title,
                self.topic.domain,
                self.topic.keywords
            )
            
            # Check for recent similar works
            similar_works = self.originality_layer.find_similar_works(
                self.topic.title,
                self.topic.keywords
            )
            
            # Calculate novelty score
            novelty_score = self.calculate_novelty_score(
                originality_check,
                similar_works
            )
            
            # Decide whether to proceed
            proceed = novelty_score >= self.config.get('novelty_threshold', 0.7)
            
            return {
                'proceed': proceed,
                'novelty_score': novelty_score,
                'originality_check': originality_check,
                'similar_works': similar_works,
                'similarity_percentage': originality_check.get('max_similarity', 0),
                'message': "Topic is sufficiently original" if proceed else "Topic lacks novelty"
            }
            
        except Exception as e:
            logger.error(f"Error in pre-research screening: {e}")
            return {
                'proceed': False,
                'error': str(e),
                'message': f"Screening failed: {e}"
            }
    
    def handle_non_original_topic(self, screening_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle cases where the topic is not sufficiently original.
        
        Args:
            screening_result: Results from pre-research screening
            
        Returns:
            Dictionary with suggested alternatives
        """
        logger.info("Generating novel topic variations...")
        
        # Generate alternative topics
        alternatives = self.generate_novel_topic_variations(
            self.topic,
            screening_result['similar_works']
        )
        
        # Score each alternative
        scored_alternatives = []
        for alt in alternatives:
            alt_score = self.score_topic_novelty(alt)
            scored_alternatives.append({
                'topic': alt,
                'novelty_score': alt_score,
                'reasoning': f"Variation to avoid similarity with existing works"
            })
        
        # Sort by novelty score
        scored_alternatives.sort(key=lambda x: x['novelty_score'], reverse=True)
        
        return {
            'status': 'topic_not_original',
            'original_topic': self.topic.title,
            'original_novelty_score': screening_result['novelty_score'],
            'similarity_with_existing': screening_result['similarity_percentage'],
            'suggested_alternatives': scored_alternatives[:5],  # Top 5
            'recommendation': 'Consider using one of the suggested novel variations',
            'next_steps': [
                "1. Review the suggested alternative topics",
                "2. Select one with high novelty score",
                "3. Re-initialize the system with the new topic"
            ]
        }
    
    def create_autonomous_research_plan(self) -> Dict[str, Any]:
        """
        Create a detailed research plan based on the topic.
        
        Returns:
            Detailed research plan
        """
        # Decompose research into stages and tasks
        research_stages = self.decompose_research_stages()
        
        # Estimate effort for each stage
        effort_estimates = self.estimate_research_effort(research_stages)
        
        # Assign agents to tasks
        agent_assignments = self.assign_agents_to_tasks(research_stages)
        
        # Define success criteria
        success_criteria = self.define_success_criteria()
        
        research_plan = {
            'topic': self.topic.title,
            'domain': self.topic.domain,
            'stages': research_stages,
            'effort_estimates': effort_estimates,
            'agent_assignments': agent_assignments,
            'success_criteria': success_criteria,
            'timeline': self.create_research_timeline(effort_estimates),
            'originality_requirements': {
                'hypothesis_novelty_threshold': 0.8,
                'methodology_novelty_threshold': 0.7,
                'text_similarity_threshold': 0.15,
                'result_novelty_threshold': 0.6
            },
            'quality_standards': {
                'minimum_citations': 15,
                'statistical_significance': 0.05,
                'replication_requirements': True
            }
        }
        
        logger.info(f"Created research plan with {len(research_stages)} stages")
        return research_plan
    
    def execute_agentic_research_with_guards(
        self,
        research_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute research using agents with originality guards.
        
        Args:
            research_plan: Detailed research plan
            
        Returns:
            Research results from all stages
        """
        results = {}
        originality_violations = []
        
        # Execute each research stage
        for stage in research_plan['stages']:
            stage_name = stage['name']
            logger.info(f"Executing stage: {stage_name}")
            
            # Get assigned agents for this stage
            stage_agents = research_plan['agent_assignments'].get(stage_name, [])
            
            # Execute stage with agents
            stage_result = self.execute_stage_with_agents(
                stage,
                stage_agents,
                research_plan
            )
            
            # Apply originality guardrails
            verified_result, violations = self.apply_originality_guardrails(
                stage_result,
                stage['output_type'],
                stage_name
            )
            
            if violations:
                originality_violations.extend(violations)
                logger.warning(f"Originality violations in {stage_name}: {len(violations)}")
            
            results[stage_name] = verified_result
            
            # Update state and check progress
            self.update_research_state(stage_name, verified_result)
            
            # Early termination if critical violation
            if self.has_critical_violation(violations):
                logger.error("Critical originality violation detected!")
                return self.handle_critical_violation(results, originality_violations)
        
        return {
            'stage_results': results,
            'originality_violations': originality_violations,
            'overall_originality_score': self.calculate_overall_originality(results),
            'completion_status': 'completed' if not originality_violations else 'completed_with_violations'
        }
    
    def prepare_author_publication_package(
        self,
        research_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare the final publication package with proper authorship.
        
        Args:
            research_results: Results from research execution
            
        Returns:
            Complete publication package
        """
        # Build the paper with authorship
        paper_package = self.authorship_manager.build_paper_with_authorship(
            research_results['stage_results']
        )
        
        # Prepare for publication
        publication_package = self.publication_engine.package_for_publication(
            paper_package,
            journal_requirements=self.config.get('journal_requirements', {})
        )
        
        # Add ethical compliance statement
        ethical_compliance = self.ethics_controller.generate_compliance_statement(
            research_results,
            paper_package
        )
        
        # Generate contribution certificate
        contribution_cert = self.authorship_manager.generate_contribution_certificate()
        
        # Compile final package
        final_package = {
            'paper': paper_package,
            'publication_ready': publication_package,
            'ethical_compliance': ethical_compliance,
            'contribution_certificate': contribution_cert,
            'originality_report': research_results.get('overall_originality_score', {}),
            'research_metadata': {
                'topic': self.topic.title,
                'author': self.author_name,
                'institution': self.author_institution,
                'completion_date': datetime.now().isoformat(),
                'system_version': '1.0.0'
            }
        }
        
        return final_package
    
    def decompose_research_stages(self) -> List[Dict[str, Any]]:
        """Decompose research into logical stages."""
        return [
            {
                'name': 'literature_review',
                'description': 'Comprehensive review of existing literature',
                'output_type': 'literature_map',
                'agents': ['literature_scout', 'gap_analyzer'],
                'tools': ['arxiv_search', 'semantic_scholar', 'google_scholar']
            },
            {
                'name': 'gap_analysis',
                'description': 'Identify research gaps and opportunities',
                'output_type': 'gap_report',
                'agents': ['gap_analyzer'],
                'tools': ['gap_analysis_tool']
            },
            {
                'name': 'hypothesis_generation',
                'description': 'Generate novel research hypotheses',
                'output_type': 'hypotheses',
                'agents': ['hypothesis_forger'],
                'tools': ['hypothesis_generator']
            },
            {
                'name': 'methodology_design',
                'description': 'Design original research methodology',
                'output_type': 'methodology',
                'agents': ['methodology_inventor'],
                'tools': ['methodology_designer']
            },
            {
                'name': 'experiment_design',
                'description': 'Design experiments or studies',
                'output_type': 'experiment_plan',
                'agents': ['experiment_designer'],
                'tools': ['experiment_planner']
            },
            {
                'name': 'data_collection_analysis',
                'description': 'Collect and analyze data',
                'output_type': 'analysis_results',
                'agents': ['data_collector', 'statistician'],
                'tools': ['data_generator', 'statistical_analysis']
            },
            {
                'name': 'results_synthesis',
                'description': 'Synthesize and interpret results',
                'output_type': 'synthesized_results',
                'agents': ['results_synthesizer'],
                'tools': ['results_analyzer']
            },
            {
                'name': 'paper_composition',
                'description': 'Compose the research paper',
                'output_type': 'draft_paper',
                'agents': ['paper_architect', 'writer'],
                'tools': ['latex_writer', 'citation_manager']
            }
        ]
    
    def calculate_novelty_score(
        self,
        originality_check: Dict[str, Any],
        similar_works: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate novelty score for the topic.
        
        Args:
            originality_check: Originality check results
            similar_works: List of similar works
            
        Returns:
            Novelty score between 0 and 1
        """
        # Base score from originality check
        base_score = 1.0 - originality_check.get('max_similarity', 0)
        
        # Penalize for many similar recent works
        recent_works = [w for w in similar_works if w.get('is_recent', False)]
        recency_penalty = min(len(recent_works) * 0.1, 0.5)
        
        # Adjust for domain saturation
        domain_saturation = self.assess_domain_saturation(similar_works)
        saturation_penalty = domain_saturation * 0.3
        
        final_score = base_score - recency_penalty - saturation_penalty
        
        # Ensure score is within bounds
        return max(0.0, min(1.0, final_score))
    
    def apply_originality_guardrails(
        self,
        stage_result: Any,
        output_type: str,
        stage_name: str
    ) -> tuple:
        """
        Apply originality guardrails to stage output.
        
        Returns:
            Tuple of (verified_result, violations)
        """
        violations = []
        
        if output_type == 'hypotheses':
            verified, violation = self.originality_layer.check_hypothesis_originality(
                stage_result
            )
            if violation:
                violations.append(violation)
                stage_result = self.regenerate_with_novelty(stage_result, output_type)
        
        elif output_type in ['methodology', 'experiment_plan']:
            verified, violation = self.originality_layer.check_methodology_originality(
                stage_result
            )
            if violation:
                violations.append(violation)
                stage_result = self.invent_novel_method(stage_result)
        
        elif output_type == 'text':
            stage_result = self.originality_layer.check_text_originality(stage_result)
        
        # Always log originality check
        originality_score = self.originality_layer.calculate_originality_score(stage_result)
        self.originality_scores[stage_name] = originality_score
        
        return stage_result, violations
    
    def generate_system_report(self) -> Dict[str, Any]:
        """Generate comprehensive system report."""
        return {
            'system_info': {
                'name': 'Hybrid AI Research System',
                'version': '1.0.0',
                'author': self.author_name
            },
            'execution_summary': {
                'start_time': self.start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration': str(datetime.now() - self.start_time),
                'stages_completed': len(self.research_artifacts.get('research_results', {}).get('stage_results', {})),
                'current_stage': self.current_stage
            },
            'originality_metrics': self.originality_scores,
            'agent_performance': self.autonomous_agents.get_performance_metrics(),
            'ethical_compliance': self.ethics_controller.get_compliance_report(),
            'resource_usage': {
                'api_calls': self.tool_orchestrator.get_api_call_count(),
                'computational_cost': 'TBD',
                'storage_used': 'TBD'
            },
            'recommendations': [
                "Review originality scores before submission",
                "Verify contribution statements accurately reflect your work",
                "Consider running additional plagiarism checks before publication"
            ]
        }
    
    # Helper methods (simplified for clarity)
    def estimate_research_effort(self, stages):
        return {stage['name']: 'medium' for stage in stages}
    
    def assign_agents_to_tasks(self, stages):
        return {stage['name']: stage['agents'] for stage in stages}
    
    def define_success_criteria(self):
        return {
            'originality': {'min_score': 0.8},
            'completeness': {'min_stages': 7},
            'quality': {'min_citations': 15}
        }
    
    def create_research_timeline(self, effort_estimates):
        return "2-4 weeks estimated timeline"
    
    def score_topic_novelty(self, topic):
        return 0.85  # Placeholder
    
    def generate_novel_topic_variations(self, topic, similar_works):
        variations = [
            f"{topic.title} with novel {topic.domain} approach",
            f"Re-examining {topic.title} through {topic.domain} lens",
            f"Advanced methodology for {topic.title} in {topic.domain}"
        ]
        return [ResearchTopic(title=v, **vars(topic)) for v in variations]
    
    def assess_domain_saturation(self, similar_works):
        return 0.3
    
    def execute_stage_with_agents(self, stage, agents, plan):
        return f"Results from {stage['name']}"
    
    def has_critical_violation(self, violations):
        return False
    
    def handle_critical_violation(self, results, violations):
        return {'error': 'critical_violation', 'results': results, 'violations': violations}
    
    def calculate_overall_originality(self, results):
        return {'score': 0.85, 'assessment': 'good'}
    
    def regenerate_with_novelty(self, content, output_type):
        return content
    
    def invent_novel_method(self, methodology):
        return methodology
    
    def update_research_state(self, stage_name, result):
        self.current_stage = stage_name
