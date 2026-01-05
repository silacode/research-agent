"""Researcher Agent - Executes research tasks using Tavily + conditional enrichment."""

from pydantic import BaseModel, Field
import structlog

from src.agents.base import BaseAgent
from src.models.plan import ResearchTask
from src.models.research import (
    TavilyResult,
    EnrichedSource,
    ResearchFindings,
)
from src.tools.tavily import TavilySearchTool
from src.tools.arxiv import ArXivExtractor
from src.tools.wikipedia import WikipediaExtractor
from src.tools.link_analyzer import LinkAnalyzer
from src.prompts.researcher import (
    RESEARCHER_SYSTEM_PROMPT,
    get_researcher_user_prompt,
)

logger = structlog.get_logger()


class ResearchSummary(BaseModel):
    """Summary output from the researcher LLM."""
    
    summary: str = Field(description="Concise summary of findings")
    key_points: list[str] = Field(description="Key points from the research")


class ResearcherAgent(BaseAgent[ResearchSummary]):
    """Agent that executes research tasks using tools.
    
    The researcher:
    1. Uses Tavily for primary web search
    2. Analyzes returned URLs for ArXiv/Wikipedia links
    3. Enriches those links with specialized extractors
    4. Synthesizes all findings into a summary
    """

    def __init__(
        self,
        model_name: str = "gpt-4o",
        api_key: str | None = None,
        tavily_api_key: str | None = None,
        max_tavily_results: int = 10,
    ):
        """Initialize the researcher agent.
        
        Args:
            model_name: OpenAI model to use
            api_key: OpenAI API key
            tavily_api_key: Tavily API key for web search
            max_tavily_results: Maximum results from Tavily
        """
        super().__init__(model_name, api_key)
        
        if tavily_api_key is None:
            raise ValueError("tavily_api_key is required for ResearcherAgent")
        
        self.tavily = TavilySearchTool(tavily_api_key, max_tavily_results)
        self.arxiv = ArXivExtractor()
        self.wikipedia = WikipediaExtractor()
        self.link_analyzer = LinkAnalyzer()

    @property
    def name(self) -> str:
        return "researcher_agent"

    @property
    def system_prompt(self) -> str:
        return RESEARCHER_SYSTEM_PROMPT

    @property
    def output_type(self) -> type[ResearchSummary]:
        return ResearchSummary

    async def execute_task(self, task: ResearchTask) -> ResearchFindings:
        """Execute a single research task.
        
        Args:
            task: The research task to execute
            
        Returns:
            ResearchFindings with all sources and summary
        """
        logger.info("executing_research_task", task_id=task.id, query=task.query)

        # Step 1: Primary Tavily search
        tavily_results = self.tavily.search_to_tavily_results(task.query)
        logger.info("tavily_search_complete", result_count=len(tavily_results))

        # Step 2: Classify URLs for enrichment
        urls = [r.url for r in tavily_results]
        classified = self.link_analyzer.classify(urls)
        logger.info(
            "urls_classified",
            arxiv_count=len(classified.arxiv),
            wikipedia_count=len(classified.wikipedia),
            other_count=len(classified.other),
        )

        # Step 3: Conditional enrichment
        arxiv_papers = []
        wikipedia_articles = []

        if classified.arxiv:
            logger.info("enriching_arxiv", count=len(classified.arxiv))
            arxiv_papers = await self.arxiv.extract_papers(classified.arxiv)

        if classified.wikipedia:
            logger.info("enriching_wikipedia", count=len(classified.wikipedia))
            wikipedia_articles = await self.wikipedia.extract_articles(classified.wikipedia)

        # Step 4: Build enriched sources
        sources = self._build_enriched_sources(
            tavily_results, arxiv_papers, wikipedia_articles
        )

        # Step 5: Generate summary using LLM
        sources_summary = self._format_sources_for_llm(sources)
        prompt = get_researcher_user_prompt(
            query=task.query,
            task_reasoning=task.reasoning,
            sources_summary=sources_summary,
        )
        summary_result = await self.run(prompt)

        return ResearchFindings(
            task_id=task.id,
            query=task.query,
            sources=sources,
            arxiv_papers=arxiv_papers,
            wikipedia_articles=wikipedia_articles,
            summary=summary_result.summary,
        )

    def _build_enriched_sources(
        self,
        tavily_results: list[TavilyResult],
        arxiv_papers: list,
        wikipedia_articles: list,
    ) -> list[EnrichedSource]:
        """Build enriched sources from all results.
        
        Args:
            tavily_results: Raw Tavily search results
            arxiv_papers: Extracted ArXiv papers
            wikipedia_articles: Extracted Wikipedia articles
            
        Returns:
            List of EnrichedSource objects
        """
        sources = []

        # Create lookup sets for enriched URLs
        arxiv_urls = {p.url for p in arxiv_papers}
        wiki_urls = {a.url for a in wikipedia_articles}

        # Process Tavily results
        for result in tavily_results:
            # Check if this was enriched
            if result.url in arxiv_urls:
                # Find the enriched paper
                paper = next(p for p in arxiv_papers if p.url == result.url)
                sources.append(EnrichedSource(
                    source_type="arxiv",
                    url=result.url,
                    title=paper.title,
                    content=paper.abstract,
                    metadata={
                        "authors": paper.authors,
                        "published": paper.published,
                        "categories": paper.categories,
                    },
                ))
            elif result.url in wiki_urls:
                # Find the enriched article
                article = next(a for a in wikipedia_articles if a.url == result.url)
                sources.append(EnrichedSource(
                    source_type="wikipedia",
                    url=result.url,
                    title=article.title,
                    content=article.summary,
                    metadata={
                        "categories": article.categories,
                    },
                ))
            else:
                # Keep as regular web result
                sources.append(EnrichedSource(
                    source_type="web",
                    url=result.url,
                    title=result.title,
                    content=result.content,
                    metadata={"score": result.score},
                ))

        # Add any ArXiv papers not in original results (from URL extraction)
        for paper in arxiv_papers:
            if paper.url not in [s.url for s in sources]:
                sources.append(EnrichedSource(
                    source_type="arxiv",
                    url=paper.url,
                    title=paper.title,
                    content=paper.abstract,
                    metadata={
                        "authors": paper.authors,
                        "published": paper.published,
                        "categories": paper.categories,
                    },
                ))

        # Add any Wikipedia articles not in original results
        for article in wikipedia_articles:
            if article.url not in [s.url for s in sources]:
                sources.append(EnrichedSource(
                    source_type="wikipedia",
                    url=article.url,
                    title=article.title,
                    content=article.summary,
                    metadata={
                        "categories": article.categories,
                    },
                ))

        return sources

    def _format_sources_for_llm(self, sources: list[EnrichedSource]) -> str:
        """Format sources for LLM summarization.
        
        Args:
            sources: List of enriched sources
            
        Returns:
            Formatted string for LLM prompt
        """
        parts = []
        for i, source in enumerate(sources, 1):
            source_type_label = {
                "arxiv": "[ArXiv Paper]",
                "wikipedia": "[Wikipedia]",
                "web": "[Web]",
            }.get(source.source_type, "[Unknown]")

            parts.append(
                f"{i}. {source_type_label} **{source.title}**\n"
                f"   URL: {source.url}\n"
                f"   Content: {source.content[:500]}..."
            )

        return "\n\n".join(parts)

