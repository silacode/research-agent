"""Wikipedia article extractor - conditional enrichment for encyclopedia content."""

import wikipediaapi
import structlog

from src.tools.base import BaseTool, ToolResult
from src.tools.link_analyzer import LinkAnalyzer
from src.models.research import WikiArticle

logger = structlog.get_logger()


class WikipediaExtractor(BaseTool):
    """Extract detailed content from Wikipedia articles.
    
    This is a conditional enrichment tool that activates when
    Tavily returns wikipedia.org links. It extracts full article
    content and metadata.
    """

    name = "wikipedia_extractor"
    description = "Extract detailed content from Wikipedia article URLs"

    def __init__(self, language: str = "en"):
        """Initialize Wikipedia extractor.
        
        Args:
            language: Wikipedia language code (default: "en")
        """
        self.link_analyzer = LinkAnalyzer()
        self.wiki = wikipediaapi.Wikipedia(
            user_agent="ResearchAgent/1.0 (research-agent@example.com)",
            language=language,
        )

    async def execute(self, query: str) -> list[ToolResult]:
        """Extract article info from a Wikipedia URL or title.
        
        Args:
            query: Wikipedia URL or article title
            
        Returns:
            List containing single ToolResult with article info
        """
        # Try to extract title from URL
        title = self.link_analyzer.extract_wikipedia_title(query)
        if not title:
            # Assume query is already an article title
            title = query

        # Replace underscores with spaces for Wikipedia API
        title = title.replace("_", " ")

        logger.info("wikipedia_extract_start", title=title)

        try:
            article = await self._fetch_article(title)
            if not article:
                return []

            result = ToolResult(
                content=article.content,
                url=article.url,
                metadata={
                    "title": article.title,
                    "summary": article.summary,
                    "categories": article.categories,
                },
            )

            logger.info("wikipedia_extract_complete", title=title)
            return [result]

        except Exception as e:
            logger.error("wikipedia_extract_error", title=title, error=str(e))
            return []

    async def _fetch_article(self, title: str) -> WikiArticle | None:
        """Fetch article content from Wikipedia API.
        
        Args:
            title: Wikipedia article title
            
        Returns:
            WikiArticle object or None if not found
        """
        page = self.wiki.page(title)

        if not page.exists():
            logger.warning("wikipedia_article_not_found", title=title)
            return None

        # Get categories (limit to first 10 for brevity)
        categories = list(page.categories.keys())[:10]
        # Clean up category names
        categories = [cat.replace("Category:", "") for cat in categories]

        return WikiArticle(
            title=page.title,
            url=page.fullurl,
            summary=page.summary,
            content=page.text,
            categories=categories,
        )

    async def extract_articles(self, urls: list[str]) -> list[WikiArticle]:
        """Extract articles from multiple Wikipedia URLs.
        
        Convenience method for batch extraction.
        
        Args:
            urls: List of Wikipedia URLs
            
        Returns:
            List of WikiArticle objects
        """
        articles = []
        for url in urls:
            title = self.link_analyzer.extract_wikipedia_title(url)
            if title:
                title = title.replace("_", " ")
                article = await self._fetch_article(title)
                if article:
                    articles.append(article)
        return articles

