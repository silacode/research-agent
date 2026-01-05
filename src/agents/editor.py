"""Editor Agent - Reviews and provides feedback on reports."""

import structlog

from src.agents.base import BaseAgent
from src.models.report import EditorFeedback
from src.prompts.editor import EDITOR_SYSTEM_PROMPT, get_editor_user_prompt

logger = structlog.get_logger()


class EditorAgent(BaseAgent[EditorFeedback]):
    """Agent that reviews reports and provides feedback.
    
    The editor evaluates reports on:
    - Accuracy: Are claims well-supported?
    - Completeness: Does it answer the question?
    - Clarity: Is it well-organized and clear?
    - Structure: Proper sections and flow?
    - Citations: Sources properly cited?
    - Objectivity: Balanced and factual?
    
    Returns a score (1-10) and approval decision.
    """

    @property
    def name(self) -> str:
        return "editor_agent"

    @property
    def system_prompt(self) -> str:
        return EDITOR_SYSTEM_PROMPT

    @property
    def output_type(self) -> type[EditorFeedback]:
        return EditorFeedback

    async def review(self, question: str, draft: str) -> EditorFeedback:
        """Review a draft report.
        
        Args:
            question: The original research question
            draft: The draft report to review
            
        Returns:
            EditorFeedback with score, approval, issues, and suggestions
        """
        logger.info("reviewing_draft", question=question, draft_length=len(draft))

        prompt = get_editor_user_prompt(question, draft)
        feedback = await self.run(prompt)

        logger.info(
            "review_complete",
            approved=feedback.approved,
            score=feedback.score,
            issue_count=len(feedback.issues),
        )

        return feedback

    def format_feedback_for_writer(self, feedback: EditorFeedback) -> str:
        """Format feedback for the writer to use in revision.
        
        Args:
            feedback: EditorFeedback from review
            
        Returns:
            Formatted feedback string
        """
        parts = [f"**Score**: {feedback.score}/10"]
        
        if feedback.issues:
            parts.append("\n**Issues Found:**")
            for issue in feedback.issues:
                parts.append(f"- {issue}")
        
        if feedback.suggestions:
            parts.append("\n**Suggestions for Improvement:**")
            for suggestion in feedback.suggestions:
                parts.append(f"- {suggestion}")
        
        return "\n".join(parts)

