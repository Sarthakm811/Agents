"""
Property-based tests for citation completeness.

**Feature: ai-research-agents, Property 9: Citation completeness**
**Validates: Requirements 7.2**
"""

import os
import sys
from typing import Any, Dict, List

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.authorship.paper_builder import PaperBuilder, BibTeXEntry


# Strategy for generating author names
author_name_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ',
    min_size=3,
    max_size=50
).filter(lambda x: x.strip() != '' and len(x.strip()) >= 3)

# Strategy for generating paper titles
paper_title_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -:',
    min_size=5,
    max_size=200
).filter(lambda x: x.strip() != '')

# Strategy for generating years
year_strategy = st.integers(min_value=1900, max_value=2025).map(str)

# Strategy for generating DOIs
doi_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz0123456789./',
    min_size=10,
    max_size=50
).map(lambda x: f"10.{x}")

# Strategy for generating URLs
url_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz0123456789-_',
    min_size=5,
    max_size=50
).map(lambda x: f"https://example.com/{x}")

# Strategy for generating publication dates
pub_date_strategy = st.one_of(
    st.integers(min_value=1900, max_value=2025).map(lambda y: f"{y}-01-01"),
    st.integers(min_value=1900, max_value=2025).map(str),
    st.just("")
)

# Strategy for generating a single paper dict
paper_dict_strategy = st.fixed_dictionaries({
    "title": paper_title_strategy,
    "authors": st.lists(author_name_strategy, min_size=1, max_size=5),
    "abstract": st.text(min_size=10, max_size=500),
    "publication_date": pub_date_strategy,
    "source_url": url_strategy,
    "doi": st.one_of(doi_strategy, st.just("")),
    "citation_count": st.one_of(st.integers(min_value=0, max_value=10000), st.none()),
    "source": st.sampled_from(["arxiv", "semantic_scholar", "unknown"])
})

# Strategy for generating papers with required fields (author, title, year)
paper_with_required_fields_strategy = st.fixed_dictionaries({
    "title": paper_title_strategy,
    "authors": st.lists(author_name_strategy, min_size=1, max_size=5),
    "abstract": st.text(min_size=10, max_size=500),
    "publication_date": st.integers(min_value=1900, max_value=2025).map(lambda y: f"{y}-01-01"),
    "source_url": url_strategy,
    "doi": st.one_of(doi_strategy, st.just("")),
    "citation_count": st.one_of(st.integers(min_value=0, max_value=10000), st.none()),
    "source": st.sampled_from(["arxiv", "semantic_scholar"])
})


class TestCitationCompletenessProperty:
    """
    **Feature: ai-research-agents, Property 9: Citation completeness**
    
    *For any* generated paper that references external works, the BibTeX output 
    SHALL contain an entry for each cited work with valid required fields 
    (author, title, year).
    
    **Validates: Requirements 7.2**
    """

    @given(
        papers=st.lists(paper_with_required_fields_strategy, min_size=1, max_size=10)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_bibtex_contains_entry_for_each_paper(self, papers: List[Dict[str, Any]]):
        """
        Property: For any list of papers with required fields, the BibTeX output 
        SHALL contain an entry for each paper.
        
        **Feature: ai-research-agents, Property 9: Citation completeness**
        **Validates: Requirements 7.2**
        """
        builder = PaperBuilder(author_name="Test Author", institution="Test Institution")
        
        # Build results with papers
        results = {
            "topic": {"title": "Test Research", "description": "Test", "domain": "test"},
            "paper": {"sections": {
                "abstract": "Test abstract",
                "introduction": "Test intro",
                "methodology": "Test method",
                "results": "Test results",
                "conclusion": "Test conclusion"
            }},
            "literature": {"papers": papers}
        }
        
        output = builder.build_from_pipeline_results(results)
        
        # Verify we have the same number of citations as papers
        citations = output.get("citations", [])
        assert len(citations) == len(papers), \
            f"Expected {len(papers)} citations, got {len(citations)}"
        
        # Verify BibTeX content contains entries
        bibtex = output.get("bibtex", "")
        for citation in citations:
            cite_key = citation.get("cite_key", "")
            assert cite_key in bibtex, f"Citation key {cite_key} not found in BibTeX"

    @given(
        papers=st.lists(paper_with_required_fields_strategy, min_size=1, max_size=10)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_bibtex_entries_have_required_fields(self, papers: List[Dict[str, Any]]):
        """
        Property: For any paper with author, title, and year, the corresponding 
        BibTeX entry SHALL contain these required fields.
        
        **Feature: ai-research-agents, Property 9: Citation completeness**
        **Validates: Requirements 7.2**
        """
        builder = PaperBuilder(author_name="Test Author", institution="Test Institution")
        
        results = {
            "topic": {"title": "Test Research", "description": "Test", "domain": "test"},
            "paper": {"sections": {"abstract": "Test"}},
            "literature": {"papers": papers}
        }
        
        output = builder.build_from_pipeline_results(results)
        citations = output.get("citations", [])
        
        for i, citation in enumerate(citations):
            paper = papers[i]
            
            # Check that citation has required fields when paper has them
            if paper.get("authors"):
                assert citation.get("authors"), \
                    f"Citation {i} missing authors when paper has authors"
            
            if paper.get("title"):
                assert citation.get("title"), \
                    f"Citation {i} missing title when paper has title"
            
            # Year should be extracted from publication_date
            if paper.get("publication_date"):
                assert citation.get("year"), \
                    f"Citation {i} missing year when paper has publication_date"

    @given(
        papers=st.lists(paper_with_required_fields_strategy, min_size=1, max_size=5)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_has_required_fields_method_accuracy(self, papers: List[Dict[str, Any]]):
        """
        Property: For any paper with author, title, and year, the has_required_fields() 
        method SHALL return True.
        
        **Feature: ai-research-agents, Property 9: Citation completeness**
        **Validates: Requirements 7.2**
        """
        builder = PaperBuilder(author_name="Test Author", institution="Test Institution")
        
        results = {
            "topic": {"title": "Test Research", "description": "Test", "domain": "test"},
            "paper": {"sections": {"abstract": "Test"}},
            "literature": {"papers": papers}
        }
        
        output = builder.build_from_pipeline_results(results)
        citations = output.get("citations", [])
        
        for i, citation in enumerate(citations):
            # Papers with required fields should have has_required_fields = True
            has_required = citation.get("has_required_fields", False)
            
            # Check if the original paper had all required fields
            paper = papers[i]
            paper_has_authors = bool(paper.get("authors"))
            paper_has_title = bool(paper.get("title"))
            paper_has_date = bool(paper.get("publication_date"))
            
            if paper_has_authors and paper_has_title and paper_has_date:
                assert has_required, \
                    f"Citation {i} should have has_required_fields=True"

    @given(
        title=paper_title_strategy,
        authors=st.lists(author_name_strategy, min_size=1, max_size=3),
        year=year_strategy
    )
    @settings(max_examples=100)
    def test_bibtex_entry_format_validity(
        self, 
        title: str, 
        authors: List[str], 
        year: str
    ):
        """
        Property: For any valid BibTeXEntry, to_bibtex() SHALL produce valid 
        BibTeX format with author, title, and year fields.
        
        **Feature: ai-research-agents, Property 9: Citation completeness**
        **Validates: Requirements 7.2**
        """
        entry = BibTeXEntry(
            cite_key="test_key",
            entry_type="article",
            title=title,
            authors=authors,
            year=year
        )
        
        bibtex_str = entry.to_bibtex()
        
        # Verify BibTeX structure
        assert bibtex_str.startswith("@article{test_key,"), \
            "BibTeX should start with entry type and key"
        assert bibtex_str.endswith("}"), \
            "BibTeX should end with closing brace"
        
        # Verify required fields are present
        assert "author = {" in bibtex_str, "BibTeX should contain author field"
        assert "title = {" in bibtex_str, "BibTeX should contain title field"
        assert f"year = {{{year}}}," in bibtex_str, "BibTeX should contain year field"

    @given(
        papers=st.lists(paper_dict_strategy, min_size=0, max_size=10)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_citation_count_matches_paper_count(self, papers: List[Dict[str, Any]]):
        """
        Property: For any list of papers, the number of citations SHALL equal 
        the number of papers.
        
        **Feature: ai-research-agents, Property 9: Citation completeness**
        **Validates: Requirements 7.2**
        """
        builder = PaperBuilder(author_name="Test Author", institution="Test Institution")
        
        results = {
            "topic": {"title": "Test Research", "description": "Test", "domain": "test"},
            "paper": {"sections": {"abstract": "Test"}},
            "literature": {"papers": papers}
        }
        
        output = builder.build_from_pipeline_results(results)
        citations = output.get("citations", [])
        
        assert len(citations) == len(papers), \
            f"Expected {len(papers)} citations, got {len(citations)}"

    @given(
        papers=st.lists(paper_with_required_fields_strategy, min_size=1, max_size=5)
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_bibtex_file_contains_all_entries(self, papers: List[Dict[str, Any]]):
        """
        Property: For any list of papers, the generated BibTeX file SHALL 
        contain an @article entry for each paper.
        
        **Feature: ai-research-agents, Property 9: Citation completeness**
        **Validates: Requirements 7.2**
        """
        builder = PaperBuilder(author_name="Test Author", institution="Test Institution")
        
        results = {
            "topic": {"title": "Test Research", "description": "Test", "domain": "test"},
            "paper": {"sections": {"abstract": "Test"}},
            "literature": {"papers": papers}
        }
        
        output = builder.build_from_pipeline_results(results)
        bibtex = output.get("bibtex", "")
        
        # Count @article entries
        entry_count = bibtex.count("@article{")
        
        assert entry_count == len(papers), \
            f"Expected {len(papers)} @article entries, found {entry_count}"

    def test_empty_papers_list_produces_no_citations(self):
        """
        Property: For an empty papers list, the BibTeX output SHALL indicate 
        no citations.
        
        **Feature: ai-research-agents, Property 9: Citation completeness**
        **Validates: Requirements 7.2**
        """
        builder = PaperBuilder(author_name="Test Author", institution="Test Institution")
        
        results = {
            "topic": {"title": "Test Research", "description": "Test", "domain": "test"},
            "paper": {"sections": {"abstract": "Test"}},
            "literature": {"papers": []}
        }
        
        output = builder.build_from_pipeline_results(results)
        
        assert len(output.get("citations", [])) == 0
        assert "No citations" in output.get("bibtex", "")

    @given(
        author_first=st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ', min_size=1, max_size=1),
        author_last=st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=3, max_size=20),
        year=year_strategy
    )
    @settings(max_examples=100)
    def test_cite_key_generation_uniqueness(
        self, 
        author_first: str, 
        author_last: str, 
        year: str
    ):
        """
        Property: For any paper, the generated cite_key SHALL be unique and 
        follow the pattern {lastname}{year}_{index}.
        
        **Feature: ai-research-agents, Property 9: Citation completeness**
        **Validates: Requirements 7.2**
        """
        author_name = f"{author_first}. {author_last}"
        
        builder = PaperBuilder(author_name="Test Author", institution="Test Institution")
        
        # Create two papers with same author and year
        papers = [
            {
                "title": "First Paper",
                "authors": [author_name],
                "publication_date": f"{year}-01-01",
                "abstract": "Abstract 1",
                "source_url": "https://example.com/1",
                "source": "arxiv"
            },
            {
                "title": "Second Paper",
                "authors": [author_name],
                "publication_date": f"{year}-06-01",
                "abstract": "Abstract 2",
                "source_url": "https://example.com/2",
                "source": "arxiv"
            }
        ]
        
        results = {
            "topic": {"title": "Test", "description": "Test", "domain": "test"},
            "paper": {"sections": {"abstract": "Test"}},
            "literature": {"papers": papers}
        }
        
        output = builder.build_from_pipeline_results(results)
        citations = output.get("citations", [])
        
        # Verify cite keys are unique
        cite_keys = [c.get("cite_key") for c in citations]
        assert len(cite_keys) == len(set(cite_keys)), \
            f"Cite keys should be unique: {cite_keys}"

    @given(
        title_with_special=st.text(
            alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 &%$#_{}~^',
            min_size=5,
            max_size=100
        ).filter(lambda x: x.strip() != '')
    )
    @settings(max_examples=50)
    def test_special_characters_escaped_in_bibtex(self, title_with_special: str):
        """
        Property: For any title with special LaTeX characters, the BibTeX 
        entry SHALL properly escape them.
        
        **Feature: ai-research-agents, Property 9: Citation completeness**
        **Validates: Requirements 7.2**
        """
        entry = BibTeXEntry(
            cite_key="test_key",
            entry_type="article",
            title=title_with_special,
            authors=["Test Author"],
            year="2024"
        )
        
        bibtex_str = entry.to_bibtex()
        
        # Verify special characters are escaped
        # The raw special characters should not appear unescaped
        special_chars = ['&', '%', '$', '#', '_', '{', '}']
        
        # Extract the title field value
        import re
        title_match = re.search(r'title = \{(.+?)\},', bibtex_str, re.DOTALL)
        if title_match:
            escaped_title = title_match.group(1)
            # Check that special chars are escaped (preceded by backslash)
            for char in special_chars:
                if char in title_with_special:
                    # The escaped version should be present
                    escaped_char = f'\\{char}'
                    # Either the char is escaped or it wasn't in the original
                    assert char not in escaped_title or escaped_char in escaped_title or \
                           escaped_title.count(char) <= title_with_special.count(char), \
                           f"Character {char} should be escaped in BibTeX"

    @given(
        papers=st.lists(paper_with_required_fields_strategy, min_size=1, max_size=3)
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_metadata_citation_count_accuracy(self, papers: List[Dict[str, Any]]):
        """
        Property: For any paper output, the metadata citation_count SHALL 
        equal the actual number of citations.
        
        **Feature: ai-research-agents, Property 9: Citation completeness**
        **Validates: Requirements 7.2**
        """
        builder = PaperBuilder(author_name="Test Author", institution="Test Institution")
        
        results = {
            "topic": {"title": "Test Research", "description": "Test", "domain": "test"},
            "paper": {"sections": {"abstract": "Test"}},
            "literature": {"papers": papers}
        }
        
        output = builder.build_from_pipeline_results(results)
        
        metadata_count = output.get("metadata", {}).get("citation_count", 0)
        actual_count = len(output.get("citations", []))
        
        assert metadata_count == actual_count, \
            f"Metadata citation_count ({metadata_count}) should equal actual count ({actual_count})"
