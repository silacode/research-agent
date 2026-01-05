"""Research plan models."""

from typing import Literal
from pydantic import BaseModel, Field


class ResearchTask(BaseModel):
    """A single research task from the planner."""

    id: str = Field(description="Unique identifier for the task")
    query: str = Field(description="The search query to execute")
    reasoning: str = Field(description="ReAct thought explaining why this query is needed")


class ResearchPlan(BaseModel):
    """Full research plan from planner."""

    question: str = Field(description="The original user question")
    tasks: list[ResearchTask] = Field(description="List of research tasks to execute")
    strategy: str = Field(description="Overall research strategy explanation")


class HumanPlanReview(BaseModel):
    """Human's decision on the research plan."""

    action: Literal["approve", "modify", "reject"] = Field(
        description="The action taken by the human reviewer"
    )
    modified_plan: ResearchPlan | None = Field(
        default=None,
        description="The modified plan if action is 'modify'",
    )
    feedback: str | None = Field(
        default=None,
        description="Feedback for the planner if action is 'reject'",
    )

