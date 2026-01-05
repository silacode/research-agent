"""ArXiv paper extractor - conditional enrichment for research papers."""

import arxiv
import structlog

from src.tools.base import BaseTool, ToolResult
from src.tools.link_analyzer import LinkAnalyzer
from src.models.research import ArXivPaper

logger = structlog.get_logger()


class ArXivExtractor(BaseTool):
    """Extract detailed metadata from ArXiv papers.
    
    This is a conditional enrichment tool that activates when
    Tavily returns arxiv.org links. It extracts full paper metadata
    including abstract, authors, and categories.
    """

    name = "arxiv_extractor"
    description = "Extract detailed metadata from ArXiv paper URLs"

    def __init__(self):
        """Initialize ArXiv extractor."""
        self.link_analyzer = LinkAnalyzer()
        self.client = arxiv.Client()

    async def execute(self, query: str) -> list[ToolResult]:
        """Extract paper info from an ArXiv URL or ID.
        
        Args:
            query: ArXiv URL or paper ID
            
        Returns:
            List containing single ToolResult with paper info
        """
        # Try to extract paper ID from URL
        paper_id = self.link_analyzer.extract_arxiv_id(query)
        if not paper_id:
            # Assume query is already a paper ID
            paper_id = query

        logger.info("arxiv_extract_start", paper_id=paper_id)

        try:
            paper = await self._fetch_paper(paper_id)
            if not paper:
                return []

            result = ToolResult(
                content=paper.abstract,
                url=paper.url,
                metadata={
                    "title": paper.title,
                    "authors": paper.authors,
                    "published": paper.published,
                    "pdf_url": paper.pdf_url,
                    "categories": paper.categories,
                },
            )

            logger.info("arxiv_extract_complete", paper_id=paper_id, title=paper.title)
            return [result]

        except Exception as e:
            logger.error("arxiv_extract_error", paper_id=paper_id, error=str(e))
            return []

    async def _fetch_paper(self, paper_id: str) -> ArXivPaper | None:
        """Fetch paper metadata from ArXiv API.
        
        Args:
            paper_id: ArXiv paper ID
            
        Returns:
            ArXivPaper object or None if not found
        """
        search = arxiv.Search(id_list=[paper_id])

        # arxiv library is synchronous
        results = list(self.client.results(search))
        if not results:
            return None

        paper = results[0]
        return ArXivPaper(
            arxiv_id=paper_id,
            title=paper.title,
            authors=[author.name for author in paper.authors],
            abstract=paper.summary,
            published=paper.published.isoformat(),
            url=paper.entry_id,
            pdf_url=paper.pdf_url,
            categories=list(paper.categories),
        )

    async def extract_papers(self, urls: list[str]) -> list[ArXivPaper]:
        """Extract papers from multiple ArXiv URLs.
        
        Convenience method for batch extraction.
        
        Args:
            urls: List of ArXiv URLs
            
        Returns:
            List of ArXivPaper objects
        """
        papers = []
        for url in urls:
            paper_id = self.link_analyzer.extract_arxiv_id(url)
            if paper_id:
                paper = await self._fetch_paper(paper_id)
                if paper:
                    papers.append(paper)
        return papers

