# src/tools/orchestrator.py
"""
Autonomous Tool Orchestrator
---------------------------
A lightweight orchestrator that knows how to invoke external tools (e.g., literature search,
semantic scholar, data generators). In the full system this would handle API keys,
rate‑limiting, caching, etc. For the scaffold we provide a minimal implementation that
records calls so the rest of the framework can query the number of API calls made.
"""

import asyncio
import functools
import logging
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Dict, Any, List, Optional, Callable, TypeVar, Tuple, Type
from urllib.parse import urlencode

import aiohttp

logger = logging.getLogger(__name__)

# Type variable for generic return type
T = TypeVar('T')


class APIError(Exception):
    """Base exception for API errors."""
    def __init__(self, service: str, status_code: int, message: str):
        self.service = service
        self.status_code = status_code
        self.message = message
        super().__init__(f"{service} API error ({status_code}): {message}")


class RateLimitError(APIError):
    """Exception raised when rate limit is exceeded."""
    def __init__(self, service: str, retry_after: float):
        self.retry_after = retry_after
        super().__init__(service, 429, f"Rate limit exceeded, retry after {retry_after}s")


class AuthenticationError(APIError):
    """Exception raised when authentication fails."""
    def __init__(self, service: str, message: str = "Authentication failed"):
        super().__init__(service, 401, message)


def retry_with_backoff(
    max_attempts: int = 3,
    backoff_base: float = 2.0,
    initial_delay: float = 1.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[int, Exception, float], None]] = None
):
    """
    Decorator that retries an async function with exponential backoff.
    
    This decorator implements retry logic with exponential backoff for handling
    transient failures in external API calls. It retries up to max_attempts times
    with delays of initial_delay * (backoff_base ** attempt) seconds.
    
    Parameters
    ----------
    max_attempts : int
        Maximum number of retry attempts (default 3).
    backoff_base : float
        Base for exponential backoff calculation (default 2.0).
    initial_delay : float
        Initial delay in seconds before first retry (default 1.0).
    exceptions : Tuple[Type[Exception], ...]
        Tuple of exception types to catch and retry on.
    on_retry : Optional[Callable[[int, Exception, float], None]]
        Optional callback called on each retry with (attempt, exception, delay).
        
    Returns
    -------
    Callable
        Decorated async function with retry logic.
        
    Example
    -------
    @retry_with_backoff(max_attempts=3, exceptions=(aiohttp.ClientError,))
    async def fetch_data(url: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception: Optional[Exception] = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    # Don't retry on the last attempt
                    if attempt == max_attempts - 1:
                        logger.warning(
                            "All %d retry attempts exhausted for %s: %s",
                            max_attempts, func.__name__, str(e)
                        )
                        raise
                    
                    # Calculate delay with exponential backoff: 1s, 2s, 4s, ...
                    delay = initial_delay * (backoff_base ** attempt)
                    
                    logger.info(
                        "Attempt %d/%d for %s failed: %s. Retrying in %.1fs...",
                        attempt + 1, max_attempts, func.__name__, str(e), delay
                    )
                    
                    # Call the on_retry callback if provided
                    if on_retry:
                        on_retry(attempt + 1, e, delay)
                    
                    await asyncio.sleep(delay)
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
            raise RuntimeError(f"Unexpected state in retry logic for {func.__name__}")
        
        # Store retry configuration on the wrapper for testing/inspection
        wrapper._retry_config = {
            'max_attempts': max_attempts,
            'backoff_base': backoff_base,
            'initial_delay': initial_delay,
            'exceptions': exceptions,
        }
        
        return wrapper
    return decorator


@dataclass
class Paper:
    """Normalized paper data structure for academic papers from various sources.
    
    Attributes:
        title: The title of the paper.
        authors: List of author names.
        abstract: The paper abstract.
        publication_date: Publication date as a string (ISO format preferred).
        source_url: URL to the paper source.
        doi: Digital Object Identifier (optional).
        citation_count: Number of citations (optional).
        source: The source database ("arxiv", "semantic_scholar", etc.).
    """
    title: str
    authors: List[str]
    abstract: str
    publication_date: str
    source_url: str
    doi: Optional[str] = None
    citation_count: Optional[int] = None
    source: str = "unknown"


class RateLimiter:
    """Rate limiter that enforces a maximum number of requests per time period."""

    def __init__(self, requests_per_period: int, period_seconds: float):
        if requests_per_period <= 0:
            raise ValueError("requests_per_period must be positive")
        if period_seconds <= 0:
            raise ValueError("period_seconds must be positive")
            
        self.requests_per_period = requests_per_period
        self.period_seconds = period_seconds
        self._request_timestamps: List[float] = []
        self._lock = asyncio.Lock()

    def _cleanup_old_timestamps(self, current_time: float) -> None:
        cutoff = current_time - self.period_seconds
        self._request_timestamps = [
            ts for ts in self._request_timestamps if ts > cutoff
        ]

    def get_wait_time(self) -> float:
        current_time = time.monotonic()
        self._cleanup_old_timestamps(current_time)
        
        if len(self._request_timestamps) < self.requests_per_period:
            return 0.0
        
        oldest_timestamp = self._request_timestamps[0]
        wait_time = (oldest_timestamp + self.period_seconds) - current_time
        return max(0.0, wait_time)

    async def acquire(self) -> None:
        async with self._lock:
            while True:
                current_time = time.monotonic()
                self._cleanup_old_timestamps(current_time)
                
                if len(self._request_timestamps) < self.requests_per_period:
                    self._request_timestamps.append(current_time)
                    return
                
                oldest_timestamp = self._request_timestamps[0]
                wait_time = (oldest_timestamp + self.period_seconds) - current_time
                
                if wait_time > 0:
                    await asyncio.sleep(wait_time)

    def get_current_usage(self) -> Dict[str, Any]:
        current_time = time.monotonic()
        self._cleanup_old_timestamps(current_time)
        
        return {
            "requests_in_window": len(self._request_timestamps),
            "requests_per_period": self.requests_per_period,
            "period_seconds": self.period_seconds,
            "wait_time": self.get_wait_time(),
        }


class AutonomousToolOrchestrator:
    """Orchestrator for external research tools including arXiv and Semantic Scholar."""

    ARXIV_API_URL = "http://export.arxiv.org/api/query"
    ARXIV_NAMESPACES = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom"
    }
    SEMANTIC_SCHOLAR_API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

    def __init__(self, config: Dict[str, Any] | None = None):
        self.config = config or {}
        self._api_call_counter: Dict[str, int] = {}
        self._arxiv_rate_limiter = RateLimiter(requests_per_period=1, period_seconds=3.0)
        self._semantic_scholar_rate_limiter = RateLimiter(requests_per_period=100, period_seconds=300.0)
        logger.info("AutonomousToolOrchestrator initialized with config keys: %s", list(self.config.keys()))

    def invoke_tool(self, tool_name: str, **kwargs: Any) -> Any:
        self._api_call_counter[tool_name] = self._api_call_counter.get(tool_name, 0) + 1
        return {"tool": tool_name, "status": "success", "payload": kwargs}

    def get_api_call_count(self) -> int:
        return sum(self._api_call_counter.values())

    def get_tool_usage(self) -> Dict[str, int]:
        return dict(self._api_call_counter)

    def list_available_tools(self) -> List[str]:
        return [
            "arxiv_search", "semantic_scholar", "google_scholar",
            "data_generator", "statistical_analysis", "experiment_planner",
        ]

    # arXiv API Integration
    async def search_arxiv(self, query: str, max_results: int = 20) -> List[Paper]:
        """Search arXiv with retry logic."""
        return await self._search_arxiv_with_retry(query, max_results)

    @retry_with_backoff(
        max_attempts=3, backoff_base=2.0, initial_delay=1.0,
        exceptions=(aiohttp.ClientError, APIError)
    )
    async def _search_arxiv_with_retry(self, query: str, max_results: int) -> List[Paper]:
        await self._arxiv_rate_limiter.acquire()
        
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending"
        }
        
        url = f"{self.ARXIV_API_URL}?{urlencode(params)}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status >= 400:
                    text = await response.text()
                    raise APIError("arXiv", response.status, text[:200])
                xml_content = await response.text()
        
        self._api_call_counter["arxiv_search"] = self._api_call_counter.get("arxiv_search", 0) + 1
        papers = self._parse_arxiv_response(xml_content)
        logger.info("arXiv search returned %d papers for query: %s", len(papers), query)
        return papers

    def _parse_arxiv_response(self, xml_content: str) -> List[Paper]:
        papers: List[Paper] = []
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            logger.error("Failed to parse arXiv XML response: %s", e)
            return papers
        
        for entry in root.findall("atom:entry", self.ARXIV_NAMESPACES):
            paper = self._parse_arxiv_entry(entry)
            if paper:
                papers.append(paper)
        return papers

    def _parse_arxiv_entry(self, entry: ET.Element) -> Optional[Paper]:
        ns = self.ARXIV_NAMESPACES
        
        title_elem = entry.find("atom:title", ns)
        title = self._clean_text(title_elem.text) if title_elem is not None and title_elem.text else ""
        
        authors: List[str] = []
        for author_elem in entry.findall("atom:author", ns):
            name_elem = author_elem.find("atom:name", ns)
            if name_elem is not None and name_elem.text:
                authors.append(name_elem.text.strip())
        
        summary_elem = entry.find("atom:summary", ns)
        abstract = self._clean_text(summary_elem.text) if summary_elem is not None and summary_elem.text else ""
        
        published_elem = entry.find("atom:published", ns)
        publication_date = published_elem.text.strip() if published_elem is not None and published_elem.text else ""
        
        source_url = ""
        for link_elem in entry.findall("atom:link", ns):
            if link_elem.get("type") == "text/html":
                source_url = link_elem.get("href", "")
                break
        
        if not source_url:
            id_elem = entry.find("atom:id", ns)
            if id_elem is not None and id_elem.text:
                source_url = id_elem.text.strip()
        
        doi_elem = entry.find("arxiv:doi", ns)
        doi = doi_elem.text.strip() if doi_elem is not None and doi_elem.text else None
        
        if not title or not authors or not abstract or not publication_date or not source_url:
            return None
        
        return Paper(
            title=title, authors=authors, abstract=abstract,
            publication_date=publication_date, source_url=source_url,
            doi=doi, citation_count=None, source="arxiv"
        )

    def _clean_text(self, text: Optional[str]) -> str:
        if not text:
            return ""
        return " ".join(text.split())


    # Semantic Scholar API Integration
    async def search_semantic_scholar(self, query: str, max_results: int = 20) -> List[Paper]:
        """Search Semantic Scholar with retry logic."""
        return await self._search_semantic_scholar_with_retry(query, max_results)

    @retry_with_backoff(
        max_attempts=3, backoff_base=2.0, initial_delay=1.0,
        exceptions=(aiohttp.ClientError, APIError)
    )
    async def _search_semantic_scholar_with_retry(self, query: str, max_results: int) -> List[Paper]:
        await self._semantic_scholar_rate_limiter.acquire()
        
        max_results = min(max_results, 100)
        params = {
            "query": query,
            "limit": max_results,
            "fields": "title,authors,abstract,year,url,externalIds,citationCount"
        }
        
        headers = {}
        api_key = self.config.get("semantic_scholar_api_key")
        if api_key:
            headers["x-api-key"] = api_key
        
        url = f"{self.SEMANTIC_SCHOLAR_API_URL}?{urlencode(params)}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status >= 400:
                    text = await response.text()
                    raise APIError("semantic_scholar", response.status, text[:200])
                json_content = await response.json()
        
        self._api_call_counter["semantic_scholar"] = self._api_call_counter.get("semantic_scholar", 0) + 1
        papers = self._parse_semantic_scholar_response(json_content)
        logger.info("Semantic Scholar search returned %d papers for query: %s", len(papers), query)
        return papers

    def _parse_semantic_scholar_response(self, json_content: Dict[str, Any]) -> List[Paper]:
        papers: List[Paper] = []
        data = json_content.get("data", [])
        
        for item in data:
            paper = self._parse_semantic_scholar_item(item)
            if paper:
                papers.append(paper)
        return papers

    def _parse_semantic_scholar_item(self, item: Dict[str, Any]) -> Optional[Paper]:
        title = self._clean_text(item.get("title", ""))
        
        authors: List[str] = []
        for author in item.get("authors", []):
            name = author.get("name", "")
            if name:
                authors.append(name.strip())
        
        abstract = self._clean_text(item.get("abstract", ""))
        year = item.get("year")
        publication_date = str(year) if year else ""
        source_url = item.get("url", "")
        
        external_ids = item.get("externalIds", {}) or {}
        doi = external_ids.get("DOI")
        citation_count = item.get("citationCount")
        
        if not title or not authors or not abstract or not publication_date or not source_url:
            return None
        
        return Paper(
            title=title, authors=authors, abstract=abstract,
            publication_date=publication_date, source_url=source_url,
            doi=doi, citation_count=citation_count, source="semantic_scholar"
        )

    def get_rate_limit_status(self) -> Dict[str, Any]:
        return {
            "arxiv": self._arxiv_rate_limiter.get_current_usage(),
            "semantic_scholar": self._semantic_scholar_rate_limiter.get_current_usage()
        }


    # Paper Deduplication
    def deduplicate_papers(
        self, 
        papers: List[Paper], 
        title_similarity_threshold: float = 0.9
    ) -> List[Paper]:
        """Deduplicate papers based on DOI matching and title similarity.
        
        This method removes duplicate papers from a list by:
        1. First matching papers with identical DOIs
        2. Then matching papers with similar titles (above threshold)
        
        When duplicates are found, the paper with more information is preferred.
        
        Parameters
        ----------
        papers : List[Paper]
            List of papers to deduplicate.
        title_similarity_threshold : float
            Minimum similarity ratio (0.0 to 1.0) for titles to be considered duplicates.
            Default is 0.9 (90% similarity).
            
        Returns
        -------
        List[Paper]
            Deduplicated list of papers.
        """
        if not papers:
            return []
        
        unique_papers: List[Paper] = []
        seen_dois: Dict[str, int] = {}  # DOI -> index in unique_papers
        
        for paper in papers:
            is_duplicate = False
            duplicate_index: Optional[int] = None
            
            # Check for DOI match first (exact match)
            if paper.doi:
                normalized_doi = paper.doi.lower().strip()
                if normalized_doi in seen_dois:
                    is_duplicate = True
                    duplicate_index = seen_dois[normalized_doi]
            
            # If no DOI match, check title similarity
            if not is_duplicate:
                for idx, existing_paper in enumerate(unique_papers):
                    similarity = self._calculate_title_similarity(
                        paper.title, existing_paper.title
                    )
                    if similarity >= title_similarity_threshold:
                        is_duplicate = True
                        duplicate_index = idx
                        break
            
            if is_duplicate and duplicate_index is not None:
                existing_paper = unique_papers[duplicate_index]
                if self._should_replace_paper(existing_paper, paper):
                    unique_papers[duplicate_index] = paper
                    if paper.doi:
                        seen_dois[paper.doi.lower().strip()] = duplicate_index
            else:
                if paper.doi:
                    seen_dois[paper.doi.lower().strip()] = len(unique_papers)
                unique_papers.append(paper)
        
        logger.info("Deduplicated %d papers to %d unique papers", len(papers), len(unique_papers))
        return unique_papers

    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity ratio between two paper titles."""
        normalized1 = self._normalize_title(title1)
        normalized2 = self._normalize_title(title2)
        return SequenceMatcher(None, normalized1, normalized2).ratio()

    def _normalize_title(self, title: str) -> str:
        """Normalize a title for comparison."""
        normalized = title.lower()
        normalized = " ".join(normalized.split())
        normalized = normalized.rstrip(".")
        return normalized

    def _should_replace_paper(self, existing: Paper, new: Paper) -> bool:
        """Determine if a new paper should replace an existing duplicate."""
        # Prefer paper with citation count
        if new.citation_count is not None and existing.citation_count is None:
            return True
        if existing.citation_count is not None and new.citation_count is None:
            return False
        
        # Prefer paper with DOI
        if new.doi and not existing.doi:
            return True
        if existing.doi and not new.doi:
            return False
        
        # Prefer paper with longer abstract
        if len(new.abstract) > len(existing.abstract):
            return True
        
        return False

    async def search_all_sources(self, query: str, max_results: int = 20) -> List[Paper]:
        """Search all available sources and return deduplicated results."""
        all_papers: List[Paper] = []
        
        try:
            arxiv_papers = await self.search_arxiv(query, max_results)
            all_papers.extend(arxiv_papers)
        except Exception as e:
            logger.warning("arXiv search failed: %s", str(e))
        
        try:
            ss_papers = await self.search_semantic_scholar(query, max_results)
            all_papers.extend(ss_papers)
        except Exception as e:
            logger.warning("Semantic Scholar search failed: %s", str(e))
        
        return self.deduplicate_papers(all_papers)
