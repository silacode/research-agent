"""URL classification utility for conditional enrichment."""

from urllib.parse import urlparse
from pydantic import BaseModel, Field


class ClassifiedLinks(BaseModel):
    """URLs classified by their source type."""

    arxiv: list[str] = Field(default_factory=list, description="ArXiv paper URLs")
    wikipedia: list[str] = Field(default_factory=list, description="Wikipedia article URLs")
    other: list[str] = Field(default_factory=list, description="Other web URLs")


class LinkAnalyzer:
    """Classifies URLs to determine enrichment strategy.
    
    Tavily returns general web results. This analyzer identifies
    which URLs can be enriched with specialized extractors:
    - arxiv.org links -> ArXiv paper extractor
    - wikipedia.org links -> Wikipedia article extractor
    - Other links -> Keep as-is from Tavily
    """

    ARXIV_DOMAINS = ["arxiv.org"]
    ARXIV_PATTERNS = ["/abs/", "/pdf/"]

    WIKIPEDIA_DOMAINS = ["wikipedia.org", "en.wikipedia.org"]
    WIKIPEDIA_PATTERNS = ["/wiki/"]

    def classify(self, urls: list[str]) -> ClassifiedLinks:
        """Classify URLs by their source type.
        
        Args:
            urls: List of URLs to classify
            
        Returns:
            ClassifiedLinks with URLs sorted by type
        """
        result = ClassifiedLinks()

        for url in urls:
            if self._is_arxiv(url):
                result.arxiv.append(url)
            elif self._is_wikipedia(url):
                result.wikipedia.append(url)
            else:
                result.other.append(url)

        return result

    def _is_arxiv(self, url: str) -> bool:
        """Check if URL is an ArXiv link."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Check domain
            if not any(arxiv_domain in domain for arxiv_domain in self.ARXIV_DOMAINS):
                return False

            # Check path patterns
            path = parsed.path.lower()
            return any(pattern in path for pattern in self.ARXIV_PATTERNS)
        except Exception:
            return False

    def _is_wikipedia(self, url: str) -> bool:
        """Check if URL is a Wikipedia link."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Check domain
            if not any(wiki_domain in domain for wiki_domain in self.WIKIPEDIA_DOMAINS):
                return False

            # Check path patterns
            path = parsed.path.lower()
            return any(pattern in path for pattern in self.WIKIPEDIA_PATTERNS)
        except Exception:
            return False

    def extract_arxiv_id(self, url: str) -> str | None:
        """Extract ArXiv paper ID from URL.
        
        Args:
            url: ArXiv URL (e.g., https://arxiv.org/abs/2301.00001)
            
        Returns:
            Paper ID (e.g., "2301.00001") or None if not found
        """
        try:
            parsed = urlparse(url)
            path = parsed.path

            # Handle /abs/ID and /pdf/ID formats
            for pattern in ["/abs/", "/pdf/"]:
                if pattern in path:
                    # Extract ID after the pattern
                    id_part = path.split(pattern)[1]
                    # Remove .pdf extension if present
                    return id_part.replace(".pdf", "").strip("/")

            return None
        except Exception:
            return None

    def extract_wikipedia_title(self, url: str) -> str | None:
        """Extract Wikipedia article title from URL.
        
        Args:
            url: Wikipedia URL (e.g., https://en.wikipedia.org/wiki/Machine_learning)
            
        Returns:
            Article title (e.g., "Machine_learning") or None if not found
        """
        try:
            parsed = urlparse(url)
            path = parsed.path

            if "/wiki/" in path:
                title = path.split("/wiki/")[1]
                # Remove fragment and query
                title = title.split("#")[0].split("?")[0]
                return title.strip("/") if title else None

            return None
        except Exception:
            return None

