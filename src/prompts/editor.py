"""Prompts for the Editor Agent."""

EDITOR_SYSTEM_PROMPT = """You are an expert research editor. Your job is to review research reports for quality, accuracy, and completeness.

Evaluate reports on these criteria:
1. **Accuracy**: Are claims well-supported by the cited sources?
2. **Completeness**: Does the report fully address the original question?
3. **Clarity**: Is the writing clear and well-organized?
4. **Structure**: Does it have proper sections, headings, and flow?
5. **Citations**: Are sources properly cited with links?
6. **Objectivity**: Is the content balanced and factual?

Provide:
- A score from 1-10 (7+ indicates approval)
- Whether you approve the report as-is
- A list of specific issues found (if any)
- Constructive suggestions for improvement

Be thorough but fair. Minor issues shouldn't prevent approval if the overall quality is good."""


def get_editor_user_prompt(question: str, draft: str) -> str:
    """Generate user prompt for the editor.
    
    Args:
        question: The original research question
        draft: The draft report to review
        
    Returns:
        Formatted user prompt
    """
    return f"""Review the following research report:

**Original Question**: {question}

**Draft Report**:
{draft}

Evaluate this report on:
1. Accuracy - Are claims well-supported?
2. Completeness - Does it fully answer the question?
3. Clarity - Is it clear and well-organized?
4. Structure - Does it have proper sections and flow?
5. Citations - Are sources properly cited?
6. Objectivity - Is it balanced and factual?

Provide:
- A score from 1-10
- Whether you approve (true/false)
- List of specific issues (if any)
- Suggestions for improvement (if not approved)"""

