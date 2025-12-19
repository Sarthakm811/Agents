"""
Property-based tests for paper normalization completeness.

**Feature: ai-research-agents, Property 1: Paper normalization completeness**
**Validates: Requirements 1.3**
"""

import os
import sys
from typing import List, Optional

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from tools.orchestrator import Paper, AutonomousToolOrchestrator


# XML-safe alphabet (excludes <, >, &, ', ")
XML_SAFE_CHARS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -.,;:!?'

# Strategy for generating valid author names (XML-safe)
author_name_strategy = st.text(
    alphabet=XML_SAFE_CHARS,
    min_size=1,
    max_size=50
).filter(lambda x: x.strip() != '')

# Strategy for generating valid titles (XML-safe)
title_strategy = st.text(
    alphabet=XML_SAFE_CHARS,
    min_size=1,
    max_size=200
).filter(lambda x: x.strip() != '')

# Strategy for generating valid abstracts (XML-safe)
abstract_strategy = st.text(
    alphabet=XML_SAFE_CHARS,
    min_size=10,
    max_size=1000
).filter(lambda x: x.strip() != '')

# Strategy for generating valid ISO dates (using text to avoid slow date generation)
date_strategy = st.sampled_from([
    "2023-01-15", "2023-06-20", "2024-03-10", "2022-12-01",
    "2021-08-25", "2020-04-18", "2019-11-30", "2024-09-05"
])

# Strategy for generating valid URLs
url_strategy = st.sampled_from([
    "http://arxiv.org/abs/2301.00001",
    "http://arxiv.org/abs/2312.12345",
    "https://arxiv.org/abs/1901.00001v1",
    "https://arxiv.org/abs/2401.00001v2",
]).flatmap(lambda base: st.just(base))


class TestPaperNormalizationCompletenessProperty:
    """
    **Feature: ai-research-agents, Property 1: Paper normalization completeness**
    
    *For any* valid API response from arXiv or Semantic Scholar, the normalized Paper 
    object SHALL contain non-empty values for title, authors, abstract, publication_date, 
    and source_url fields.
    
    **Validates: Requirements 1.3**
    """

    @given(
        title=title_strategy,
        authors=st.lists(author_name_strategy, min_size=1, max_size=10),
        abstract=abstract_strategy,
        publication_date=date_strategy,
        source_url=url_strategy,
        doi=st.one_of(st.none(), st.text(min_size=5, max_size=50).filter(lambda x: x.strip() != '')),
        citation_count=st.one_of(st.none(), st.integers(min_value=0, max_value=100000)),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_paper_has_all_required_fields(
        self,
        title: str,
        authors: List[str],
        abstract: str,
        publication_date: str,
        source_url: str,
        doi: Optional[str],
        citation_count: Optional[int],
    ):
        """
        Property: For any Paper object created with valid inputs, all required fields
        SHALL be non-empty.
        
        **Feature: ai-research-agents, Property 1: Paper normalization completeness**
        **Validates: Requirements 1.3**
        """
        paper = Paper(
            title=title,
            authors=authors,
            abstract=abstract,
            publication_date=publication_date,
            source_url=source_url,
            doi=doi,
            citation_count=citation_count,
            source="arxiv"
        )
        
        # Verify all required fields are non-empty
        assert paper.title and paper.title.strip(), "Title must be non-empty"
        assert paper.authors and len(paper.authors) > 0, "Authors must be non-empty"
        assert all(a.strip() for a in paper.authors), "All author names must be non-empty"
        assert paper.abstract and paper.abstract.strip(), "Abstract must be non-empty"
        assert paper.publication_date and paper.publication_date.strip(), "Publication date must be non-empty"
        assert paper.source_url and paper.source_url.strip(), "Source URL must be non-empty"


    @given(
        title=title_strategy,
        authors=st.lists(author_name_strategy, min_size=1, max_size=5),
        abstract=abstract_strategy,
        publication_date=date_strategy,
    )
    @settings(max_examples=100)
    def test_arxiv_entry_parsing_produces_complete_paper(
        self,
        title: str,
        authors: List[str],
        abstract: str,
        publication_date: str,
    ):
        """
        Property: For any valid arXiv XML entry, parsing SHALL produce a Paper with
        all required fields populated.
        
        **Feature: ai-research-agents, Property 1: Paper normalization completeness**
        **Validates: Requirements 1.3**
        """
        # Generate a valid arXiv XML entry
        authors_xml = "\n".join([
            f'<author><name>{author}</name></author>'
            for author in authors
        ])
        
        xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2301.00001v1</id>
    <title>{title}</title>
    {authors_xml}
    <summary>{abstract}</summary>
    <published>{publication_date}T00:00:00Z</published>
    <link href="http://arxiv.org/abs/2301.00001v1" type="text/html"/>
  </entry>
</feed>'''
        
        orchestrator = AutonomousToolOrchestrator()
        papers = orchestrator._parse_arxiv_response(xml_content)
        
        # Should parse exactly one paper
        assert len(papers) == 1, f"Expected 1 paper, got {len(papers)}"
        
        paper = papers[0]
        
        # Verify all required fields are non-empty
        assert paper.title and paper.title.strip(), "Title must be non-empty"
        assert paper.authors and len(paper.authors) > 0, "Authors must be non-empty"
        assert paper.abstract and paper.abstract.strip(), "Abstract must be non-empty"
        assert paper.publication_date and paper.publication_date.strip(), "Publication date must be non-empty"
        assert paper.source_url and paper.source_url.strip(), "Source URL must be non-empty"
        assert paper.source == "arxiv", "Source must be 'arxiv'"

    def test_arxiv_entry_with_missing_title_is_skipped(self):
        """
        Property: An arXiv entry with missing title SHALL be skipped during parsing.
        
        **Feature: ai-research-agents, Property 1: Paper normalization completeness**
        **Validates: Requirements 1.3**
        """
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2301.00001v1</id>
    <title></title>
    <author><name>John Doe</name></author>
    <summary>This is an abstract.</summary>
    <published>2023-01-01T00:00:00Z</published>
    <link href="http://arxiv.org/abs/2301.00001v1" type="text/html"/>
  </entry>
</feed>'''
        
        orchestrator = AutonomousToolOrchestrator()
        papers = orchestrator._parse_arxiv_response(xml_content)
        
        # Entry with empty title should be skipped
        assert len(papers) == 0, "Entry with empty title should be skipped"

    def test_arxiv_entry_with_missing_authors_is_skipped(self):
        """
        Property: An arXiv entry with no authors SHALL be skipped during parsing.
        
        **Feature: ai-research-agents, Property 1: Paper normalization completeness**
        **Validates: Requirements 1.3**
        """
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2301.00001v1</id>
    <title>Test Paper Title</title>
    <summary>This is an abstract.</summary>
    <published>2023-01-01T00:00:00Z</published>
    <link href="http://arxiv.org/abs/2301.00001v1" type="text/html"/>
  </entry>
</feed>'''
        
        orchestrator = AutonomousToolOrchestrator()
        papers = orchestrator._parse_arxiv_response(xml_content)
        
        # Entry with no authors should be skipped
        assert len(papers) == 0, "Entry with no authors should be skipped"

    def test_arxiv_entry_with_missing_abstract_is_skipped(self):
        """
        Property: An arXiv entry with missing abstract SHALL be skipped during parsing.
        
        **Feature: ai-research-agents, Property 1: Paper normalization completeness**
        **Validates: Requirements 1.3**
        """
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2301.00001v1</id>
    <title>Test Paper Title</title>
    <author><name>John Doe</name></author>
    <summary></summary>
    <published>2023-01-01T00:00:00Z</published>
    <link href="http://arxiv.org/abs/2301.00001v1" type="text/html"/>
  </entry>
</feed>'''
        
        orchestrator = AutonomousToolOrchestrator()
        papers = orchestrator._parse_arxiv_response(xml_content)
        
        # Entry with empty abstract should be skipped
        assert len(papers) == 0, "Entry with empty abstract should be skipped"

    def test_arxiv_entry_with_doi_includes_doi(self):
        """
        Property: An arXiv entry with DOI SHALL include the DOI in the parsed Paper.
        
        **Feature: ai-research-agents, Property 1: Paper normalization completeness**
        **Validates: Requirements 1.3**
        """
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2301.00001v1</id>
    <title>Test Paper Title</title>
    <author><name>John Doe</name></author>
    <summary>This is an abstract for testing.</summary>
    <published>2023-01-01T00:00:00Z</published>
    <link href="http://arxiv.org/abs/2301.00001v1" type="text/html"/>
    <arxiv:doi>10.1234/test.doi.12345</arxiv:doi>
  </entry>
</feed>'''
        
        orchestrator = AutonomousToolOrchestrator()
        papers = orchestrator._parse_arxiv_response(xml_content)
        
        assert len(papers) == 1
        assert papers[0].doi == "10.1234/test.doi.12345"

    @given(
        num_entries=st.integers(min_value=1, max_value=5),
    )
    @settings(max_examples=50)
    def test_multiple_arxiv_entries_all_normalized(self, num_entries: int):
        """
        Property: For any number of valid arXiv entries, ALL parsed Papers SHALL
        have complete required fields.
        
        **Feature: ai-research-agents, Property 1: Paper normalization completeness**
        **Validates: Requirements 1.3**
        """
        entries_xml = ""
        for i in range(num_entries):
            entries_xml += f'''
  <entry>
    <id>http://arxiv.org/abs/2301.{i:05d}v1</id>
    <title>Test Paper Title {i}</title>
    <author><name>Author {i}</name></author>
    <summary>This is abstract number {i} for testing purposes.</summary>
    <published>2023-01-{(i % 28) + 1:02d}T00:00:00Z</published>
    <link href="http://arxiv.org/abs/2301.{i:05d}v1" type="text/html"/>
  </entry>'''
        
        xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
{entries_xml}
</feed>'''
        
        orchestrator = AutonomousToolOrchestrator()
        papers = orchestrator._parse_arxiv_response(xml_content)
        
        # Should parse all entries
        assert len(papers) == num_entries, f"Expected {num_entries} papers, got {len(papers)}"
        
        # All papers should have complete required fields
        for i, paper in enumerate(papers):
            assert paper.title and paper.title.strip(), f"Paper {i}: Title must be non-empty"
            assert paper.authors and len(paper.authors) > 0, f"Paper {i}: Authors must be non-empty"
            assert paper.abstract and paper.abstract.strip(), f"Paper {i}: Abstract must be non-empty"
            assert paper.publication_date and paper.publication_date.strip(), f"Paper {i}: Publication date must be non-empty"
            assert paper.source_url and paper.source_url.strip(), f"Paper {i}: Source URL must be non-empty"
            assert paper.source == "arxiv", f"Paper {i}: Source must be 'arxiv'"

    def test_clean_text_normalizes_whitespace(self):
        """
        Property: The _clean_text method SHALL normalize whitespace in text.
        
        **Feature: ai-research-agents, Property 1: Paper normalization completeness**
        **Validates: Requirements 1.3**
        """
        orchestrator = AutonomousToolOrchestrator()
        
        # Test with various whitespace patterns
        assert orchestrator._clean_text("  hello  world  ") == "hello world"
        assert orchestrator._clean_text("hello\nworld") == "hello world"
        assert orchestrator._clean_text("hello\t\tworld") == "hello world"
        assert orchestrator._clean_text("  \n  hello  \n  world  \n  ") == "hello world"
        assert orchestrator._clean_text(None) == ""
        assert orchestrator._clean_text("") == ""

    @given(
        title=title_strategy,
        authors=st.lists(author_name_strategy, min_size=1, max_size=5),
        abstract=abstract_strategy,
        year=st.integers(min_value=1990, max_value=2024),
        citation_count=st.integers(min_value=0, max_value=100000),
    )
    @settings(max_examples=100)
    def test_semantic_scholar_entry_parsing_produces_complete_paper(
        self,
        title: str,
        authors: List[str],
        abstract: str,
        year: int,
        citation_count: int,
    ):
        """
        Property: For any valid Semantic Scholar JSON entry, parsing SHALL produce a Paper with
        all required fields populated.
        
        **Feature: ai-research-agents, Property 1: Paper normalization completeness**
        **Validates: Requirements 1.3**
        """
        # Generate a valid Semantic Scholar JSON response
        json_content = {
            "data": [
                {
                    "title": title,
                    "authors": [{"name": author} for author in authors],
                    "abstract": abstract,
                    "year": year,
                    "url": "https://www.semanticscholar.org/paper/abc123",
                    "externalIds": {"DOI": "10.1234/test.doi"},
                    "citationCount": citation_count,
                }
            ]
        }
        
        orchestrator = AutonomousToolOrchestrator()
        papers = orchestrator._parse_semantic_scholar_response(json_content)
        
        # Should parse exactly one paper
        assert len(papers) == 1, f"Expected 1 paper, got {len(papers)}"
        
        paper = papers[0]
        
        # Verify all required fields are non-empty
        assert paper.title and paper.title.strip(), "Title must be non-empty"
        assert paper.authors and len(paper.authors) > 0, "Authors must be non-empty"
        assert paper.abstract and paper.abstract.strip(), "Abstract must be non-empty"
        assert paper.publication_date and paper.publication_date.strip(), "Publication date must be non-empty"
        assert paper.source_url and paper.source_url.strip(), "Source URL must be non-empty"
        assert paper.source == "semantic_scholar", "Source must be 'semantic_scholar'"
        assert paper.citation_count == citation_count, "Citation count must match"

    def test_semantic_scholar_entry_with_missing_title_is_skipped(self):
        """
        Property: A Semantic Scholar entry with missing title SHALL be skipped during parsing.
        
        **Feature: ai-research-agents, Property 1: Paper normalization completeness**
        **Validates: Requirements 1.3**
        """
        json_content = {
            "data": [
                {
                    "title": "",
                    "authors": [{"name": "John Doe"}],
                    "abstract": "This is an abstract.",
                    "year": 2023,
                    "url": "https://www.semanticscholar.org/paper/abc123",
                    "citationCount": 10,
                }
            ]
        }
        
        orchestrator = AutonomousToolOrchestrator()
        papers = orchestrator._parse_semantic_scholar_response(json_content)
        
        # Entry with empty title should be skipped
        assert len(papers) == 0, "Entry with empty title should be skipped"

    def test_semantic_scholar_entry_with_missing_authors_is_skipped(self):
        """
        Property: A Semantic Scholar entry with no authors SHALL be skipped during parsing.
        
        **Feature: ai-research-agents, Property 1: Paper normalization completeness**
        **Validates: Requirements 1.3**
        """
        json_content = {
            "data": [
                {
                    "title": "Test Paper Title",
                    "authors": [],
                    "abstract": "This is an abstract.",
                    "year": 2023,
                    "url": "https://www.semanticscholar.org/paper/abc123",
                    "citationCount": 10,
                }
            ]
        }
        
        orchestrator = AutonomousToolOrchestrator()
        papers = orchestrator._parse_semantic_scholar_response(json_content)
        
        # Entry with no authors should be skipped
        assert len(papers) == 0, "Entry with no authors should be skipped"

    def test_semantic_scholar_entry_with_missing_abstract_is_skipped(self):
        """
        Property: A Semantic Scholar entry with missing abstract SHALL be skipped during parsing.
        
        **Feature: ai-research-agents, Property 1: Paper normalization completeness**
        **Validates: Requirements 1.3**
        """
        json_content = {
            "data": [
                {
                    "title": "Test Paper Title",
                    "authors": [{"name": "John Doe"}],
                    "abstract": "",
                    "year": 2023,
                    "url": "https://www.semanticscholar.org/paper/abc123",
                    "citationCount": 10,
                }
            ]
        }
        
        orchestrator = AutonomousToolOrchestrator()
        papers = orchestrator._parse_semantic_scholar_response(json_content)
        
        # Entry with empty abstract should be skipped
        assert len(papers) == 0, "Entry with empty abstract should be skipped"

    def test_semantic_scholar_entry_with_doi_includes_doi(self):
        """
        Property: A Semantic Scholar entry with DOI SHALL include the DOI in the parsed Paper.
        
        **Feature: ai-research-agents, Property 1: Paper normalization completeness**
        **Validates: Requirements 1.3**
        """
        json_content = {
            "data": [
                {
                    "title": "Test Paper Title",
                    "authors": [{"name": "John Doe"}],
                    "abstract": "This is an abstract for testing.",
                    "year": 2023,
                    "url": "https://www.semanticscholar.org/paper/abc123",
                    "externalIds": {"DOI": "10.1234/test.doi.12345"},
                    "citationCount": 42,
                }
            ]
        }
        
        orchestrator = AutonomousToolOrchestrator()
        papers = orchestrator._parse_semantic_scholar_response(json_content)
        
        assert len(papers) == 1
        assert papers[0].doi == "10.1234/test.doi.12345"
        assert papers[0].citation_count == 42

    @given(
        num_entries=st.integers(min_value=1, max_value=5),
    )
    @settings(max_examples=50)
    def test_multiple_semantic_scholar_entries_all_normalized(self, num_entries: int):
        """
        Property: For any number of valid Semantic Scholar entries, ALL parsed Papers SHALL
        have complete required fields.
        
        **Feature: ai-research-agents, Property 1: Paper normalization completeness**
        **Validates: Requirements 1.3**
        """
        data = []
        for i in range(num_entries):
            data.append({
                "title": f"Test Paper Title {i}",
                "authors": [{"name": f"Author {i}"}],
                "abstract": f"This is abstract number {i} for testing purposes.",
                "year": 2020 + (i % 5),
                "url": f"https://www.semanticscholar.org/paper/abc{i:05d}",
                "externalIds": {"DOI": f"10.1234/test.{i:05d}"},
                "citationCount": i * 10,
            })
        
        json_content = {"data": data}
        
        orchestrator = AutonomousToolOrchestrator()
        papers = orchestrator._parse_semantic_scholar_response(json_content)
        
        # Should parse all entries
        assert len(papers) == num_entries, f"Expected {num_entries} papers, got {len(papers)}"
        
        # All papers should have complete required fields
        for i, paper in enumerate(papers):
            assert paper.title and paper.title.strip(), f"Paper {i}: Title must be non-empty"
            assert paper.authors and len(paper.authors) > 0, f"Paper {i}: Authors must be non-empty"
            assert paper.abstract and paper.abstract.strip(), f"Paper {i}: Abstract must be non-empty"
            assert paper.publication_date and paper.publication_date.strip(), f"Paper {i}: Publication date must be non-empty"
            assert paper.source_url and paper.source_url.strip(), f"Paper {i}: Source URL must be non-empty"
            assert paper.source == "semantic_scholar", f"Paper {i}: Source must be 'semantic_scholar'"
            assert paper.citation_count is not None, f"Paper {i}: Citation count must be present"
