"""Tavily web search tool - primary discovery mechanism."""

import structlog
from tavily import TavilyClient

from src.tools.base import BaseTool, ToolResult
from src.models.research import TavilyResult

logger = structlog.get_logger()


class TavilySearchTool(BaseTool):
    """Primary web search tool using Tavily API.
    
    Tavily is the main discovery tool that performs general web searches.
    Results are then analyzed to determine if ArXiv or Wikipedia enrichment
    should be applied based on the returned URLs.
    """

    name = "tavily_search"
    description = "Search the web for information using Tavily"

    def __init__(self, api_key: str, max_results: int = 10):
        """Initialize Tavily search tool.
        
        Args:
            api_key: Tavily API key
            max_results: Maximum number of results to return
        """
        self.client = TavilyClient(api_key=api_key)
        self.max_results = max_results

    async def execute(self, query: str) -> list[ToolResult]:
        """Execute a web search using Tavily.
        
        Args:
            query: Search query string
            
        Returns:
            List of ToolResult objects with search results
        """
        logger.info("tavily_search_start", query=query)

        try:
            # Tavily client is synchronous, but we wrap it for async interface
            response = self.client.search(
                query=query,
                max_results=self.max_results,
                include_answer=False,
                include_raw_content=False,
            )

            results = []
            for item in response.get("results", []):
                result = ToolResult(
                    content=item.get("content", ""),
                    url=item.get("url", ""),
                    metadata={
                        "title": item.get("title", ""),
                        "score": item.get("score", 0.0),
                    },
                )
                results.append(result)

            logger.info("tavily_search_complete", query=query, result_count=len(results))
            return results

        except Exception as e:
            logger.error("tavily_search_error", query=query, error=str(e))
            raise

    def search_to_tavily_results(self, query: str) -> list[TavilyResult]:
        """Execute search and return typed TavilyResult objects.
        
        Convenience method that returns strongly-typed results
        for use in the research pipeline.
        
        Args:
            query: Search query string
            
        Returns:
            List of TavilyResult objects
        """
        response = self.client.search(
            query=query,
            max_results=self.max_results,
            include_answer=False,
            include_raw_content=False,
        )

        results = []
        for item in response.get("results", []):
            result = TavilyResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                content=item.get("content", ""),
                score=item.get("score", 0.0),
            )
            results.append(result)

        return results

