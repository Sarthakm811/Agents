# src/authorship/paper_builder.py
"""
Author‑Centric Paper Builder
----------------------------
Creates a draft research paper from the artifacts produced by the research
pipeline and injects proper authorship metadata. The implementation below is a
minimal scaffold that assembles a simple markdown document. In a real system you
might generate LaTeX, handle citations, and format sections according to a
journal template.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class AuthorCentricPaperBuilder:
    """Build a paper document with author attribution.

    Parameters
    ----------
    author_name: str
        Name of the primary human author.
    institution: str
        Institutional affiliation.
    config: dict, optional
        Additional configuration (e.g., preferred citation style).
    """

    def __init__(self, author_name: str, institution: str, config: Dict[str, Any] | None = None):
        self.author_name = author_name
        self.institution = institution
        self.config = config or {}
        self.citation_style = self.config.get("citation_style", "APA")
        logger.info("PaperBuilder initialized for %s (%s)", author_name, institution)

    # ---------------------------------------------------------------------
    # Public API used by HybridResearchSystem
    # ---------------------------------------------------------------------
    def build_paper_with_authorship(self, stage_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create a simple markdown representation of the paper.

        The *stage_results* dictionary is expected to contain the output of each
        research stage (e.g., literature map, hypothesis list, methodology,
        results, etc.). The method stitches those pieces together into a
        markdown string and returns a structure that also contains metadata.
        """
        logger.debug("Building paper from %d stage results", len(stage_results))
        sections = []
        # Title & metadata
        title = self._determine_title(stage_results)
        sections.append(f"# {title}\n")
        sections.append(self._author_block())
        sections.append("---\n")
        # Iterate over known stages in a sensible order
        ordered_keys = [
            "literature_review",
            "gap_analysis",
            "hypothesis_generation",
            "methodology_design",
            "experiment_design",
            "data_collection_analysis",
            "results_synthesis",
            "paper_composition",
        ]
        for key in ordered_keys:
            if key in stage_results:
                sections.append(self._format_section(key, stage_results[key]))
        # Footer with timestamp
        sections.append(f"\n*Generated on {datetime.utcnow().isoformat()} UTC*")
        markdown = "\n".join(sections)
        logger.info("Paper markdown generated (length %d characters)", len(markdown))
        return {
            "format": "markdown",
            "content": markdown,
            "metadata": {
                "title": title,
                "author": self.author_name,
                "institution": self.institution,
                "generated_at": datetime.utcnow().isoformat(),
                "citation_style": self.citation_style,
            },
        }

    def generate_contribution_certificate(self) -> Dict[str, str]:
        """Return a simple JSON‑style contribution certificate.

        In a production system this could be a signed PDF. Here we provide a plain
        dictionary that can be serialized easily.
        """
        cert = {
            "author": self.author_name,
            "institution": self.institution,
            "date": datetime.utcnow().date().isoformat(),
            "statement": "This work was generated with assistance from the Hybrid AI Research System.",
        }
        logger.debug("Contribution certificate created for %s", self.author_name)
        return cert

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------
    def _determine_title(self, stage_results: Dict[str, Any]) -> str:
        """Derive a paper title from the research topic or fallback.
        """
        # Try to pull a title from the literature review if present
        if "literature_review" in stage_results:
            # Very naive heuristic – just use the first line of the map
            first_line = str(stage_results["literature_review"]).splitlines()[0]
            return f"Exploratory Study: {first_line[:60]}..."
        return "Hybrid AI‑Generated Research Paper"

    def _author_block(self) -> str:
        """Return a markdown block with author and affiliation.
        """
        return f"*{self.author_name}*\\\n{self.institution}\n"

    def _format_section(self, stage_name: str, content: Any) -> str:
        """Render a stage's content as a markdown section.
        """
        header = stage_name.replace("_", " ").title()
        body = str(content)
        return f"## {header}\n\n{body}\n"
