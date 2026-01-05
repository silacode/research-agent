"""Research findings models."""

from typing import Literal
from pydantic import BaseModel, Field


class TavilyResult(BaseModel):
    """Raw result from Tavily search."""

    title: str = Field(description="Title of the search result")
    url: str = Field(description="URL of the search result")
    content: str = Field(description="Snippet/content from the result")
    score: float = Field(description="Relevance score from Tavily")


class ArXivPaper(BaseModel):
    """Extracted ArXiv paper metadata."""

    arxiv_id: str = Field(description="ArXiv paper ID")
    title: str = Field(description="Paper title")
    authors: list[str] = Field(description="List of paper authors")
    abstract: str = Field(description="Paper abstract")
    published: str = Field(description="Publication date")
    url: str = Field(description="ArXiv URL")
    pdf_url: str = Field(description="Direct PDF URL")
    categories: list[str] = Field(default_factory=list, description="ArXiv categories")


class WikiArticle(BaseModel):
    """Extracted Wikipedia article content."""

    title: str = Field(description="Article title")
    url: str = Field(description="Wikipedia URL")
    summary: str = Field(description="Article summary/intro")
    content: str = Field(description="Full article content")
    categories: list[str] = Field(default_factory=list, description="Wikipedia categories")


class EnrichedSource(BaseModel):
    """Source after optional enrichment."""

    source_type: Literal["web", "arxiv", "wikipedia"] = Field(
        description="Type of the source"
    )
    url: str = Field(description="Source URL")
    title: str = Field(description="Source title")
    content: str = Field(description="Extracted content")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class ResearchFindings(BaseModel):
    """Aggregated research output for a single task."""

    task_id: str = Field(description="ID of the research task")
    query: str = Field(description="The search query used")
    sources: list[EnrichedSource] = Field(
        default_factory=list,
        description="All enriched sources from this task",
    )
    arxiv_papers: list[ArXivPaper] = Field(
        default_factory=list,
        description="Extracted ArXiv papers",
    )
    wikipedia_articles: list[WikiArticle] = Field(
        default_factory=list,
        description="Extracted Wikipedia articles",
    )
    summary: str = Field(default="", description="Summary of findings for this task")

