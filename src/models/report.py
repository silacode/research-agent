"""Report and editor feedback models."""

from pydantic import BaseModel, Field

from src.models.research import EnrichedSource


class EditorFeedback(BaseModel):
    """Editor's review of a draft report."""

    approved: bool = Field(description="Whether the report is approved")
    score: int = Field(ge=1, le=10, description="Quality score from 1-10")
    issues: list[str] = Field(
        default_factory=list,
        description="List of issues found in the report",
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="Suggestions for improvement",
    )


class FinalReport(BaseModel):
    """The final markdown report."""

    title: str = Field(description="Report title")
    content: str = Field(description="Full markdown content")
    sources: list[EnrichedSource] = Field(
        default_factory=list,
        description="All sources used in the report",
    )
    iterations: int = Field(
        default=1,
        description="Number of revision iterations",
    )

