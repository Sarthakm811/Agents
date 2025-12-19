# src/authorship/paper_builder.py
"""
Author-Centric Paper Builder
----------------------------
Creates a draft research paper from the artifacts produced by the research
pipeline and injects proper authorship metadata. Generates LaTeX documents
with BibTeX citations for all referenced papers.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BibTeXEntry:
    """Represents a single BibTeX citation entry."""
    cite_key: str
    entry_type: str = "article"
    title: str = ""
    authors: List[str] = None
    year: str = ""
    journal: str = ""
    url: str = ""
    doi: str = ""
    abstract: str = ""
    
    def __post_init__(self):
        if self.authors is None:
            self.authors = []
    
    def to_bibtex(self) -> str:
        """Convert entry to BibTeX format string."""
        lines = [f"@{self.entry_type}{{{self.cite_key},"]
        
        if self.authors:
            author_str = " and ".join(self.authors)
            lines.append(f"  author = {{{author_str}}},")
        
        if self.title:
            escaped_title = self._escape_latex(self.title)
            lines.append(f"  title = {{{escaped_title}}},")
        
        if self.year:
            lines.append(f"  year = {{{self.year}}},")
        
        if self.journal:
            lines.append(f"  journal = {{{self._escape_latex(self.journal)}}},")
        
        if self.url:
            lines.append(f"  url = {{{self.url}}},")
        
        if self.doi:
            lines.append(f"  doi = {{{self.doi}}},")
        
        lines.append("}")
        return "\n".join(lines)
    
    def _escape_latex(self, text: str) -> str:
        """Escape special LaTeX characters in text."""
        if not text:
            return ""
        replacements = [
            ('&', r'\&'),
            ('%', r'\%'),
            ('$', r'\$'),
            ('#', r'\#'),
            ('_', r'\_'),
            ('{', r'\{'),
            ('}', r'\}'),
            ('~', r'\textasciitilde{}'),
            ('^', r'\textasciicircum{}'),
        ]
        result = text
        for old, new in replacements:
            result = result.replace(old, new)
        return result
    
    def has_required_fields(self) -> bool:
        """Check if entry has all required BibTeX fields (author, title, year)."""
        return bool(self.authors) and bool(self.title) and bool(self.year)


class PaperBuilder:
    """Builds complete research papers from agent outputs with LaTeX and BibTeX support."""
    
    REQUIRED_SECTIONS = ["abstract", "introduction", "methodology", "results", "conclusion"]
    
    def __init__(
        self,
        author_name: str = "Anonymous",
        institution: str = "Unknown Institution",
        citation_style: str = "ieee",
        config: Optional[Dict[str, Any]] = None
    ):
        self.author_name = author_name
        self.institution = institution
        self.citation_style = citation_style
        self.config = config or {}
        self._citations: List[BibTeXEntry] = []
    
    def build_from_pipeline_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Build a complete paper from research pipeline results.
        
        Parameters
        ----------
        results : Dict[str, Any]
            Results from AgenticResearchSwarm.execute_pipeline() containing:
            - topic: ResearchTopic or dict with title, description, domain
            - literature: Literature review results with papers list
            - paper: WritingAgent output with sections dict
            
        Returns
        -------
        Dict[str, Any]
            Complete paper output containing:
            - latex: Complete LaTeX document string
            - bibtex: BibTeX file content string
            - sections: Dict of section name to content
            - citations: List of citation entries
            - metadata: Paper metadata dict
        """
        self._citations = []
        
        # Extract topic info
        topic = results.get("topic", {})
        if hasattr(topic, "title"):
            title = topic.title
            domain = getattr(topic, "domain", "general")
        else:
            title = topic.get("title", "Research Paper")
            domain = topic.get("domain", "general")
        
        # Extract paper sections from writing agent output
        paper_output = results.get("paper", {})
        sections = paper_output.get("sections", {})
        
        # Extract papers from literature review for citations
        literature = results.get("literature", {})
        papers = literature.get("papers", [])
        
        # Build citations from referenced papers
        self._build_citations_from_papers(papers)
        
        # Generate LaTeX document
        latex_content = self._generate_latex_document(title, sections, domain)
        
        # Generate BibTeX file
        bibtex_content = self._generate_bibtex_file()
        
        return {
            "latex": latex_content,
            "bibtex": bibtex_content,
            "sections": sections,
            "citations": [self._citation_to_dict(c) for c in self._citations],
            "metadata": {
                "title": title,
                "author": self.author_name,
                "institution": self.institution,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "citation_count": len(self._citations),
                "section_count": len(sections),
            }
        }

    def _build_citations_from_papers(self, papers: List[Dict[str, Any]]) -> None:
        """Build BibTeX entries from paper dictionaries.
        
        Parameters
        ----------
        papers : List[Dict[str, Any]]
            List of paper dictionaries from literature search results.
        """
        for i, paper in enumerate(papers):
            cite_key = self._generate_cite_key(paper, i)
            
            # Extract year from publication_date
            pub_date = paper.get("publication_date", "")
            year = self._extract_year(pub_date)
            
            entry = BibTeXEntry(
                cite_key=cite_key,
                entry_type="article",
                title=paper.get("title", ""),
                authors=paper.get("authors", []),
                year=year,
                journal=paper.get("source", ""),
                url=paper.get("source_url", ""),
                doi=paper.get("doi", ""),
                abstract=paper.get("abstract", "")
            )
            
            self._citations.append(entry)
    
    def _generate_cite_key(self, paper: Dict[str, Any], index: int) -> str:
        """Generate a unique citation key for a paper.
        
        Parameters
        ----------
        paper : Dict[str, Any]
            Paper dictionary.
        index : int
            Index of the paper in the list.
            
        Returns
        -------
        str
            Unique citation key.
        """
        authors = paper.get("authors", [])
        year = self._extract_year(paper.get("publication_date", ""))
        
        if authors:
            # Use first author's last name
            first_author = authors[0]
            # Extract last name (assume "First Last" or "Last, First" format)
            if "," in first_author:
                last_name = first_author.split(",")[0].strip()
            else:
                parts = first_author.split()
                last_name = parts[-1] if parts else "unknown"
            # Clean the last name for use as cite key
            last_name = re.sub(r'[^a-zA-Z]', '', last_name).lower()
        else:
            last_name = "unknown"
        
        if not year:
            year = "nd"  # no date
        
        return f"{last_name}{year}_{index}"
    
    def _extract_year(self, date_str: str) -> str:
        """Extract year from a date string.
        
        Parameters
        ----------
        date_str : str
            Date string in various formats.
            
        Returns
        -------
        str
            Four-digit year or empty string.
        """
        if not date_str:
            return ""
        
        # Try to find a 4-digit year
        match = re.search(r'\b(19|20)\d{2}\b', date_str)
        if match:
            return match.group(0)
        
        return ""
    
    def _generate_latex_document(
        self,
        title: str,
        sections: Dict[str, str],
        domain: str
    ) -> str:
        """Generate a complete LaTeX document.
        
        Parameters
        ----------
        title : str
            Paper title.
        sections : Dict[str, str]
            Dictionary of section name to content.
        domain : str
            Research domain.
            
        Returns
        -------
        str
            Complete LaTeX document string.
        """
        escaped_title = self._escape_latex_text(title)
        escaped_author = self._escape_latex_text(self.author_name)
        escaped_institution = self._escape_latex_text(self.institution)
        
        # Build document preamble
        preamble = self._get_latex_preamble()
        
        # Build document body
        body_parts = [
            preamble,
            "",
            f"\\title{{{escaped_title}}}",
            f"\\author{{{escaped_author}\\\\{escaped_institution}}}",
            "\\date{\\today}",
            "",
            "\\begin{document}",
            "",
            "\\maketitle",
            "",
        ]
        
        # Add abstract if present
        if "abstract" in sections and sections["abstract"]:
            body_parts.extend([
                "\\begin{abstract}",
                self._escape_latex_text(sections["abstract"]),
                "\\end{abstract}",
                "",
            ])
        
        # Add main sections
        section_order = ["introduction", "methodology", "results", "conclusion"]
        section_titles = {
            "introduction": "Introduction",
            "methodology": "Methodology",
            "results": "Results",
            "conclusion": "Conclusion"
        }
        
        for section_name in section_order:
            if section_name in sections and sections[section_name]:
                section_title = section_titles.get(section_name, section_name.title())
                content = self._escape_latex_text(sections[section_name])
                # Add citations to the content
                content = self._add_citations_to_content(content)
                body_parts.extend([
                    f"\\section{{{section_title}}}",
                    content,
                    "",
                ])
        
        # Add bibliography
        if self._citations:
            body_parts.extend([
                "\\bibliographystyle{ieeetr}",
                "\\bibliography{references}",
                "",
            ])
        
        body_parts.append("\\end{document}")
        
        return "\n".join(body_parts)
    
    def _get_latex_preamble(self) -> str:
        """Get the LaTeX document preamble."""
        return """\\documentclass{article}
\\usepackage[utf8]{inputenc}
\\usepackage{amsmath}
\\usepackage{amssymb}
\\usepackage{graphicx}
\\usepackage{hyperref}
\\usepackage{natbib}
\\usepackage[margin=1in]{geometry}"""
    
    def _escape_latex_text(self, text: str) -> str:
        """Escape special LaTeX characters in text content.
        
        Parameters
        ----------
        text : str
            Raw text content.
            
        Returns
        -------
        str
            LaTeX-safe text.
        """
        if not text:
            return ""
        
        replacements = [
            ('\\', r'\textbackslash{}'),
            ('&', r'\&'),
            ('%', r'\%'),
            ('$', r'\$'),
            ('#', r'\#'),
            ('_', r'\_'),
            ('{', r'\{'),
            ('}', r'\}'),
            ('~', r'\textasciitilde{}'),
            ('^', r'\textasciicircum{}'),
        ]
        
        result = text
        for old, new in replacements:
            result = result.replace(old, new)
        
        return result
    
    def _add_citations_to_content(self, content: str) -> str:
        """Add citation references to content where appropriate.
        
        Parameters
        ----------
        content : str
            Section content.
            
        Returns
        -------
        str
            Content with citation references added.
        """
        if not self._citations:
            return content
        
        # Add a general citation at the end of introduction-like content
        # In a real implementation, this would be more sophisticated
        cite_keys = [c.cite_key for c in self._citations[:5]]  # Cite first 5 papers
        if cite_keys:
            cite_command = "\\cite{" + ",".join(cite_keys) + "}"
            # Add citation reference if content doesn't already have citations
            if "\\cite" not in content and content.strip():
                content = content.rstrip() + " " + cite_command
        
        return content
    
    def _generate_bibtex_file(self) -> str:
        """Generate BibTeX file content from citations.
        
        Returns
        -------
        str
            Complete BibTeX file content.
        """
        if not self._citations:
            return "% No citations\n"
        
        entries = []
        for citation in self._citations:
            entries.append(citation.to_bibtex())
        
        header = f"% BibTeX file generated by PaperBuilder\n% Generated: {datetime.now(timezone.utc).isoformat()}\n\n"
        return header + "\n\n".join(entries)
    
    def _citation_to_dict(self, citation: BibTeXEntry) -> Dict[str, Any]:
        """Convert a BibTeXEntry to a dictionary.
        
        Parameters
        ----------
        citation : BibTeXEntry
            Citation entry.
            
        Returns
        -------
        Dict[str, Any]
            Dictionary representation.
        """
        return {
            "cite_key": citation.cite_key,
            "entry_type": citation.entry_type,
            "title": citation.title,
            "authors": citation.authors,
            "year": citation.year,
            "journal": citation.journal,
            "url": citation.url,
            "doi": citation.doi,
            "has_required_fields": citation.has_required_fields()
        }
    
    def get_citations(self) -> List[BibTeXEntry]:
        """Get the list of citations.
        
        Returns
        -------
        List[BibTeXEntry]
            List of citation entries.
        """
        return list(self._citations)
    
    def add_citation(self, citation: BibTeXEntry) -> None:
        """Add a citation entry.
        
        Parameters
        ----------
        citation : BibTeXEntry
            Citation entry to add.
        """
        self._citations.append(citation)
    
    def generate_markdown(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a markdown version of the paper.
        
        Parameters
        ----------
        results : Dict[str, Any]
            Results from research pipeline.
            
        Returns
        -------
        Dict[str, Any]
            Markdown paper output.
        """
        topic = results.get("topic", {})
        if hasattr(topic, "title"):
            title = topic.title
        else:
            title = topic.get("title", "Research Paper")
        
        paper_output = results.get("paper", {})
        sections = paper_output.get("sections", {})
        
        md_parts = [
            f"# {title}",
            "",
            f"*{self.author_name}*",
            f"*{self.institution}*",
            "",
            f"*Generated on {datetime.now(timezone.utc).isoformat()} UTC*",
            "",
        ]
        
        section_order = ["abstract", "introduction", "methodology", "results", "conclusion"]
        for section_name in section_order:
            if section_name in sections and sections[section_name]:
                md_parts.extend([
                    f"## {section_name.title()}",
                    "",
                    sections[section_name],
                    "",
                ])
        
        # Add references section
        literature = results.get("literature", {})
        papers = literature.get("papers", [])
        if papers:
            md_parts.extend([
                "## References",
                "",
            ])
            for i, paper in enumerate(papers[:10], 1):
                authors = ", ".join(paper.get("authors", ["Unknown"])[:3])
                if len(paper.get("authors", [])) > 3:
                    authors += " et al."
                title = paper.get("title", "Untitled")
                year = self._extract_year(paper.get("publication_date", ""))
                md_parts.append(f"{i}. {authors}. \"{title}\" ({year})")
            md_parts.append("")
        
        return {
            "format": "markdown",
            "content": "\n".join(md_parts),
            "metadata": {
                "title": title,
                "author": self.author_name,
                "institution": self.institution,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
        }

    def build_paper_with_authorship(self, stage_results: Dict[str, Any]) -> Dict[str, Any]:
        """Build a paper with proper authorship from stage results.
        
        This method is used by HybridResearchSystem to build the final paper
        from the research pipeline stage results.
        
        Parameters
        ----------
        stage_results : Dict[str, Any]
            Results from all research stages.
            
        Returns
        -------
        Dict[str, Any]
            Complete paper package with authorship information.
        """
        # Convert stage results to pipeline results format
        pipeline_results = {
            "topic": stage_results.get("topic", {"title": "Research Paper"}),
            "literature": stage_results.get("literature_review", {}),
            "paper": stage_results.get("paper_composition", {})
        }
        
        # Build the paper using the standard method
        paper_output = self.build_from_pipeline_results(pipeline_results)
        
        # Add authorship information
        paper_output["authorship"] = {
            "author": self.author_name,
            "institution": self.institution,
            "contribution_statement": f"{self.author_name} conceived and directed the research with AI assistance.",
            "ai_disclosure": "This research was conducted with AI assistance using the Hybrid AI Research System."
        }
        
        return paper_output
    
    def generate_contribution_certificate(self) -> Dict[str, Any]:
        """Generate a contribution certificate for the author.
        
        Returns
        -------
        Dict[str, Any]
            Contribution certificate with authorship details.
        """
        return {
            "certificate_type": "research_contribution",
            "author": self.author_name,
            "institution": self.institution,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "contributions": [
                "Research direction and topic selection",
                "Oversight of AI-assisted research process",
                "Review and validation of generated content",
                "Final approval of research outputs"
            ],
            "ai_assistance_disclosure": (
                "This research was conducted with AI assistance. "
                "The human author provided direction, oversight, and final approval."
            ),
            "verification_hash": None  # Would be computed in production
        }


# Alias for backward compatibility with HybridResearchSystem
AuthorCentricPaperBuilder = PaperBuilder
