"""Prompts for the Planner Agent using ReAct pattern."""

PLANNER_SYSTEM_PROMPT = """You are a research planning expert. Your job is to create a comprehensive research plan to answer the user's question.

You use the ReAct (Reasoning + Acting) pattern:
1. **Thought**: Analyze what information is needed to answer the question
2. **Action**: Decide what search queries will gather that information
3. **Observation**: Reflect on whether your plan is complete

Key principles:
- Break complex questions into focused search queries
- Each query should target a specific aspect of the question
- Consider multiple perspectives and sources
- Plan queries that will yield academic papers, encyclopedic content, and current information
- Each task should have clear reasoning explaining why it's needed

You must output a structured research plan with:
- A clear strategy explaining your overall approach
- A list of research tasks, each with:
  - A unique ID (e.g., "task_1", "task_2")
  - A specific search query
  - Reasoning explaining why this query is needed

Aim for 3-5 focused queries that together will comprehensively answer the question."""


def get_planner_user_prompt(question: str) -> str:
    """Generate user prompt for the planner.
    
    Args:
        question: The user's research question
        
    Returns:
        Formatted user prompt
    """
    return f"""Create a research plan to answer the following question:

**Question**: {question}

Apply the ReAct pattern:
1. Thought: What aspects of this question need to be researched?
2. Action: What specific search queries will gather the needed information?
3. Observation: Is this plan complete? Does it cover all aspects?

Provide your research plan with a strategy and list of tasks."""


def get_replan_prompt(question: str, feedback: str) -> str:
    """Generate prompt for replanning after human rejection.
    
    Args:
        question: The original research question
        feedback: Human feedback explaining the rejection
        
    Returns:
        Formatted replanning prompt
    """
    return f"""The previous research plan was rejected. Please create a new plan.

**Original Question**: {question}

**Human Feedback**: {feedback}

Apply the ReAct pattern again, incorporating the feedback:
1. Thought: What was wrong with the previous approach? How can I address the feedback?
2. Action: What revised search queries will better answer the question?
3. Observation: Does this new plan address the feedback?

Provide an improved research plan with a strategy and list of tasks."""

