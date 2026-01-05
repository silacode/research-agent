"""Workflow state models for future persistence support."""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

from src.models.plan import ResearchPlan, HumanPlanReview
from src.models.research import ResearchFindings
from src.models.report import FinalReport, EditorFeedback


class WorkflowState(BaseModel):
    """Complete workflow state for persistence and resume.
    
    This model captures the entire state of a research workflow,
    enabling save/restore functionality for long-running processes.
    """

    # Identification
    workflow_id: str = Field(description="Unique workflow identifier")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Current stage
    stage: Literal[
        "planning",
        "human_review",
        "researching",
        "writing",
        "editing",
        "completed",
        "failed",
    ] = Field(default="planning", description="Current workflow stage")

    # Input
    question: str = Field(description="Original user question")

    # Planning stage
    plan: ResearchPlan | None = Field(default=None)
    human_review: HumanPlanReview | None = Field(default=None)
    plan_attempts: int = Field(default=0)

    # Research stage
    current_task_index: int = Field(default=0)
    findings: list[ResearchFindings] = Field(default_factory=list)

    # Writing/editing stage
    current_draft: str | None = Field(default=None)
    editor_feedback: list[EditorFeedback] = Field(default_factory=list)
    revision_count: int = Field(default=0)

    # Final output
    final_report: FinalReport | None = Field(default=None)

    # Error tracking
    error_message: str | None = Field(default=None)

