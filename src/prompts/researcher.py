"""Prompts for the Research Agent."""

RESEARCHER_SYSTEM_PROMPT = """You are a research assistant that synthesizes information from multiple sources.

Your job is to:
1. Analyze search results from web searches
2. Identify key information relevant to the research task
3. Note which sources are from academic papers (ArXiv) vs encyclopedic content (Wikipedia) vs general web
4. Create a concise summary of findings for each research task

Be objective and factual. Cite sources when making claims. Highlight any conflicting information across sources."""


def get_researcher_user_prompt(
    query: str,
    task_reasoning: str,
    sources_summary: str,
) -> str:
    """Generate user prompt for the researcher.
    
    Args:
        query: The search query executed
        task_reasoning: Why this query was needed (from planner)
        sources_summary: Summary of all sources found
        
    Returns:
        Formatted user prompt
    """
    return f"""Synthesize the following research findings:

**Search Query**: {query}

**Purpose**: {task_reasoning}

**Sources Found**:
{sources_summary}

Provide a concise summary of the key findings relevant to the research purpose.
Note any academic papers, Wikipedia articles, or particularly authoritative sources.
Highlight any conflicting information if present."""

