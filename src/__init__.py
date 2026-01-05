"""Research Agent - A reflective research agent with tools.

This package provides a multi-agent research system that:
1. Plans research using ReAct prompting
2. Executes research with Tavily search + conditional enrichment
3. Writes reports with reflection-based quality improvement
4. Includes human-in-the-loop plan approval
"""

from src.orchestrator import Orchestrator
from src.models import (
    ResearchPlan,
    ResearchTask,
    ResearchFindings,
    FinalReport,
    EditorFeedback,
)

__version__ = "0.1.0"

__all__ = [
    "Orchestrator",
    "ResearchPlan",
    "ResearchTask",
    "ResearchFindings",
    "FinalReport",
    "EditorFeedback",
    "__version__",
]

