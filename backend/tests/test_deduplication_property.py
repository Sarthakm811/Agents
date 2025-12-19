"""
Property-based tests for paper deduplication correctness.

**Feature: ai-research-agents, Property 2: Paper deduplication correctness**
**Validates: Requirements 1.5**
"""

import os
import sys
from typing import List, Optional

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from tools.orchestrator import Paper, AutonomousToolOrchestrator


# Strategy for generating valid DOIs
doi_strategy = st.one_of(
    st.none(),
    st.text(
        alphabet='0123456789abcdefghijklmnopqrstuvwxyz./-',
        min_size=5,
        max_size=30
    ).filter(lambda x: x.strip() != '')
)

# Strategy for generating valid titles
title_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -.,;:!?',
    min_size=10,
    max_size=100
).filter(lambda x: x.strip() != '')

# Strategy for generating author names
author_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ',
    min_size=3,
    max_size=30
).filter(lambda x: x.strip() != '')

# Strategy for generating abstracts
abstract_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -.,;:!?',
    min_size=20,
    max_size=200
).filter(lambda x: x.strip() != '')


def create_paper(
    title: str,
    authors: List[str],
    abstract: str,
    doi: Optional[str] = None,
    citation_count: Optional[int] = None,
    source: str = "arxiv"
) -> Paper:
    """Helper to create a Paper with default values."""
    return Paper(
        title=title,
        authors=authors,
        abstract=abstract,
        publication_date="2023-01-01",
        source_url=f"http://example.com/{hash(title) % 10000}",
        doi=doi,
        citation_count=citation_count,
        source=source
    )


class TestPaperDeduplicationCorrectnessProperty:
    """
    **Feature: ai-research-agents, Property 2: Paper deduplication correctness**
    
    *For any* list of papers containing duplicates (same DOI or similar titles), 
    deduplication SHALL return a list where no two papers have the same DOI 
    and no two papers have title similarity above 0.9.
    
    **Validates: Requirements 1.5**
    """

    @given(
        titles=st.lists(title_strategy, min_size=1, max_size=10),
        dois=st.lists(doi_strategy, min_size=1, max_size=10),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_no_duplicate_dois_after_deduplication(
        self, titles: List[str], dois: List[Optional[str]]
    ):
        """
        Property: After deduplication, no two papers SHALL have the same DOI.
        
        **Feature: ai-research-agents, Property 2: Paper deduplication correctness**
        **Validates: Requirements 1.5**
        """
        # Create papers with potentially duplicate DOIs
        papers = []
        for i, title in enumerate(titles):
            doi = dois[i % len(dois)]  # Reuse DOIs to create duplicates
            papers.append(create_paper(
                title=f"{title} {i}",  # Make titles unique
                authors=["Author A"],
                abstract="This is a test abstract for the paper.",
                doi=doi
            ))
        
        orchestrator = AutonomousToolOrchestrator()
        deduplicated = orchestrator.deduplicate_papers(papers)
        
        # Check no duplicate DOIs
        seen_dois = set()
        for paper in deduplicated:
            if paper.doi:
                normalized_doi = paper.doi.lower().strip()
                assert normalized_doi not in seen_dois, (
                    f"Found duplicate DOI after deduplication: {paper.doi}"
                )
                seen_dois.add(normalized_doi)

    @given(
        base_title=title_strategy,
        num_duplicates=st.integers(min_value=2, max_value=5),
    )
    @settings(max_examples=100)
    def test_no_similar_titles_after_deduplication(
        self, base_title: str, num_duplicates: int
    ):
        """
        Property: After deduplication, no two papers SHALL have title similarity above 0.9.
        
        **Feature: ai-research-agents, Property 2: Paper deduplication correctness**
        **Validates: Requirements 1.5**
        """
        # Create papers with very similar titles (should be deduplicated)
        papers = []
        for i in range(num_duplicates):
            # Create slight variations that should still be similar
            title = base_title if i == 0 else f"{base_title}."
            papers.append(create_paper(
                title=title,
                authors=["Author A"],
                abstract="This is a test abstract for the paper.",
                doi=None
            ))
        
        orchestrator = AutonomousToolOrchestrator()
        deduplicated = orchestrator.deduplicate_papers(papers)
        
        # Check no two papers have similarity above threshold
        for i, paper1 in enumerate(deduplicated):
            for j, paper2 in enumerate(deduplicated):
                if i < j:
                    similarity = orchestrator._calculate_title_similarity(
                        paper1.title, paper2.title
                    )
                    assert similarity < 0.9, (
                        f"Found similar titles after deduplication: "
                        f"'{paper1.title}' and '{paper2.title}' "
                        f"(similarity: {similarity:.2f})"
                    )

    @given(
        num_papers=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_deduplication_preserves_unique_papers(
        self, num_papers: int
    ):
        """
        Property: Deduplication SHALL preserve all unique papers (different DOIs and titles).
        
        **Feature: ai-research-agents, Property 2: Paper deduplication correctness**
        **Validates: Requirements 1.5**
        """
        # Create papers with truly unique titles and DOIs
        # Use completely different base words to ensure titles are dissimilar
        base_words = [
            "quantum", "neural", "genetic", "statistical", "cryptographic",
            "distributed", "parallel", "semantic", "syntactic", "probabilistic"
        ]
        papers = []
        for i in range(num_papers):
            # Use different base words to ensure titles are truly unique
            unique_title = f"{base_words[i % len(base_words)]} research paper number {i * 1000}"
            unique_doi = f"10.{i:04d}/unique.paper.{i}"
            papers.append(create_paper(
                title=unique_title,
                authors=["Author A"],
                abstract="This is a test abstract for the paper.",
                doi=unique_doi
            ))
        
        orchestrator = AutonomousToolOrchestrator()
        deduplicated = orchestrator.deduplicate_papers(papers)
        
        # All papers should be preserved since they're unique
        assert len(deduplicated) == len(papers), (
            f"Expected {len(papers)} unique papers, got {len(deduplicated)}"
        )

    def test_doi_duplicates_are_removed(self):
        """
        Property: Papers with identical DOIs SHALL be deduplicated.
        
        **Feature: ai-research-agents, Property 2: Paper deduplication correctness**
        **Validates: Requirements 1.5**
        """
        papers = [
            create_paper(
                title="First Paper Title",
                authors=["Author A"],
                abstract="Abstract one",
                doi="10.1234/test.001"
            ),
            create_paper(
                title="Second Paper Title",
                authors=["Author B"],
                abstract="Abstract two",
                doi="10.1234/test.001"  # Same DOI
            ),
            create_paper(
                title="Third Paper Title",
                authors=["Author C"],
                abstract="Abstract three",
                doi="10.1234/test.002"  # Different DOI
            ),
        ]
        
        orchestrator = AutonomousToolOrchestrator()
        deduplicated = orchestrator.deduplicate_papers(papers)
        
        # Should have 2 papers (one duplicate removed)
        assert len(deduplicated) == 2
        
        # Check no duplicate DOIs
        dois = [p.doi for p in deduplicated if p.doi]
        assert len(dois) == len(set(d.lower() for d in dois))

    def test_similar_titles_are_deduplicated(self):
        """
        Property: Papers with similar titles (>0.9 similarity) SHALL be deduplicated.
        
        **Feature: ai-research-agents, Property 2: Paper deduplication correctness**
        **Validates: Requirements 1.5**
        """
        papers = [
            create_paper(
                title="Machine Learning for Natural Language Processing",
                authors=["Author A"],
                abstract="Abstract one",
                doi=None
            ),
            create_paper(
                title="Machine Learning for Natural Language Processing.",  # Very similar
                authors=["Author B"],
                abstract="Abstract two",
                doi=None
            ),
            create_paper(
                title="Deep Learning for Computer Vision",  # Different
                authors=["Author C"],
                abstract="Abstract three",
                doi=None
            ),
        ]
        
        orchestrator = AutonomousToolOrchestrator()
        deduplicated = orchestrator.deduplicate_papers(papers)
        
        # Should have 2 papers (similar titles deduplicated)
        assert len(deduplicated) == 2

    def test_empty_list_returns_empty(self):
        """
        Property: Deduplicating an empty list SHALL return an empty list.
        
        **Feature: ai-research-agents, Property 2: Paper deduplication correctness**
        **Validates: Requirements 1.5**
        """
        orchestrator = AutonomousToolOrchestrator()
        deduplicated = orchestrator.deduplicate_papers([])
        assert deduplicated == []

    def test_single_paper_returns_same(self):
        """
        Property: Deduplicating a single paper SHALL return that paper.
        
        **Feature: ai-research-agents, Property 2: Paper deduplication correctness**
        **Validates: Requirements 1.5**
        """
        paper = create_paper(
            title="Single Paper",
            authors=["Author A"],
            abstract="Abstract",
            doi="10.1234/single"
        )
        
        orchestrator = AutonomousToolOrchestrator()
        deduplicated = orchestrator.deduplicate_papers([paper])
        
        assert len(deduplicated) == 1
        assert deduplicated[0].title == paper.title

    @given(
        num_papers=st.integers(min_value=2, max_value=10),
    )
    @settings(max_examples=50)
    def test_deduplication_prefers_paper_with_citation_count(
        self, num_papers: int
    ):
        """
        Property: When deduplicating, papers with citation counts SHALL be preferred.
        
        **Feature: ai-research-agents, Property 2: Paper deduplication correctness**
        **Validates: Requirements 1.5**
        """
        # Create duplicate papers, one with citation count
        papers = [
            create_paper(
                title="Same Title Paper",
                authors=["Author A"],
                abstract="Abstract",
                doi="10.1234/same",
                citation_count=None,
                source="arxiv"
            ),
            create_paper(
                title="Same Title Paper",
                authors=["Author B"],
                abstract="Abstract",
                doi="10.1234/same",
                citation_count=42,
                source="semantic_scholar"
            ),
        ]
        
        orchestrator = AutonomousToolOrchestrator()
        deduplicated = orchestrator.deduplicate_papers(papers)
        
        assert len(deduplicated) == 1
        assert deduplicated[0].citation_count == 42

    def test_doi_case_insensitive_matching(self):
        """
        Property: DOI matching SHALL be case-insensitive.
        
        **Feature: ai-research-agents, Property 2: Paper deduplication correctness**
        **Validates: Requirements 1.5**
        """
        papers = [
            create_paper(
                title="First Paper",
                authors=["Author A"],
                abstract="Abstract one",
                doi="10.1234/ABC.def"
            ),
            create_paper(
                title="Second Paper",
                authors=["Author B"],
                abstract="Abstract two",
                doi="10.1234/abc.DEF"  # Same DOI, different case
            ),
        ]
        
        orchestrator = AutonomousToolOrchestrator()
        deduplicated = orchestrator.deduplicate_papers(papers)
        
        assert len(deduplicated) == 1
