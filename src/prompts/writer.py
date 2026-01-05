"""Prompts for the Writer Agent."""

WRITER_SYSTEM_PROMPT = """You are an expert research writer. Your job is to synthesize research findings into a well-structured, comprehensive markdown report.

Your reports should:
1. Have a clear, descriptive title
2. Include an executive summary/introduction
3. Be organized with logical sections and headings
4. Present information clearly and accurately
5. Cite sources appropriately with links
6. Include a references/sources section at the end
7. Be written in an accessible but professional tone

Use proper markdown formatting:
- # for main title
- ## for major sections
- ### for subsections
- **bold** for emphasis
- > for important quotes or callouts
- - or 1. for lists
- [text](url) for source links"""


def get_writer_user_prompt(question: str, findings_summary: str) -> str:
    """Generate user prompt for the writer.
    
    Args:
        question: The original research question
        findings_summary: Combined summary of all research findings
        
    Returns:
        Formatted user prompt
    """
    return f"""Write a comprehensive research report based on the following:

**Original Question**: {question}

**Research Findings**:
{findings_summary}

Create a well-structured markdown report that:
1. Directly answers the original question
2. Synthesizes information from all sources
3. Is organized logically with clear sections
4. Cites sources with links where available
5. Includes a references section at the end

The report should be thorough but readable, suitable for someone wanting to understand this topic in depth."""


def get_revision_prompt(
    question: str,
    current_draft: str,
    editor_feedback: str,
) -> str:
    """Generate prompt for revising a draft based on editor feedback.
    
    Args:
        question: The original research question
        current_draft: The current draft to revise
        editor_feedback: Feedback from the editor
        
    Returns:
        Formatted revision prompt
    """
    return f"""Revise the following research report based on editor feedback:

**Original Question**: {question}

**Current Draft**:
{current_draft}

**Editor Feedback**:
{editor_feedback}

Please revise the report to address all the feedback while maintaining the overall structure and accuracy.
Focus on:
1. Fixing any issues identified
2. Incorporating suggestions for improvement
3. Maintaining or improving clarity and readability
4. Ensuring all sources are still properly cited"""

