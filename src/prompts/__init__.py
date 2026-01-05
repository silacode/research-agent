"""Prompt templates for all agents."""

from src.prompts.planner import PLANNER_SYSTEM_PROMPT, get_planner_user_prompt, get_replan_prompt
from src.prompts.researcher import RESEARCHER_SYSTEM_PROMPT, get_researcher_user_prompt
from src.prompts.writer import WRITER_SYSTEM_PROMPT, get_writer_user_prompt, get_revision_prompt
from src.prompts.editor import EDITOR_SYSTEM_PROMPT, get_editor_user_prompt

__all__ = [
    "PLANNER_SYSTEM_PROMPT",
    "get_planner_user_prompt",
    "get_replan_prompt",
    "RESEARCHER_SYSTEM_PROMPT",
    "get_researcher_user_prompt",
    "WRITER_SYSTEM_PROMPT",
    "get_writer_user_prompt",
    "get_revision_prompt",
    "EDITOR_SYSTEM_PROMPT",
    "get_editor_user_prompt",
]

