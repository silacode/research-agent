"""Planner Agent - Creates research plans using ReAct prompting."""

import structlog

from src.agents.base import BaseAgent
from src.models.plan import ResearchPlan
from src.prompts.planner import (
    PLANNER_SYSTEM_PROMPT,
    get_planner_user_prompt,
    get_replan_prompt,
)

logger = structlog.get_logger()


class PlannerAgent(BaseAgent[ResearchPlan]):
    """Agent that creates research plans using ReAct prompting.
    
    The planner analyzes the user's question and creates a structured
    research plan with specific search queries. Uses the ReAct pattern:
    - Thought: What information is needed?
    - Action: What queries will gather it?
    - Observation: Is the plan complete?
    """

    @property
    def name(self) -> str:
        return "planner_agent"

    @property
    def system_prompt(self) -> str:
        return PLANNER_SYSTEM_PROMPT

    @property
    def output_type(self) -> type[ResearchPlan]:
        return ResearchPlan

    async def create_plan(self, question: str) -> ResearchPlan:
        """Create a research plan for the given question.
        
        Args:
            question: The user's research question
            
        Returns:
            ResearchPlan with strategy and tasks
        """
        logger.info("creating_research_plan", question=question)
        prompt = get_planner_user_prompt(question)
        plan = await self.run(prompt)
        logger.info(
            "research_plan_created",
            task_count=len(plan.tasks),
            strategy=plan.strategy[:100],
        )
        return plan

    async def replan(self, question: str, feedback: str) -> ResearchPlan:
        """Create a new plan based on human feedback.
        
        Args:
            question: The original research question
            feedback: Human feedback on why the previous plan was rejected
            
        Returns:
            Revised ResearchPlan
        """
        logger.info("replanning", question=question, feedback=feedback[:100])
        prompt = get_replan_prompt(question, feedback)
        plan = await self.run(prompt)
        logger.info(
            "replan_complete",
            task_count=len(plan.tasks),
        )
        return plan

