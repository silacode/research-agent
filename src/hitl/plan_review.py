"""Human-in-the-loop plan review handler."""

from typing import Literal
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
import structlog

from src.models.plan import ResearchPlan, ResearchTask, HumanPlanReview

logger = structlog.get_logger()


class PlanReviewer:
    """Handles human review of research plans via CLI.
    
    Provides a Rich-based UI for:
    - Displaying the research plan
    - Collecting human decision (approve/modify/reject)
    - Editing plan tasks inline
    - Collecting rejection feedback
    """

    def __init__(self, console: Console | None = None):
        """Initialize the plan reviewer.
        
        Args:
            console: Rich Console instance (creates new if not provided)
        """
        self.console = console or Console()

    def display_plan(self, plan: ResearchPlan) -> None:
        """Render the research plan as a Rich panel.
        
        Args:
            plan: The research plan to display
        """
        # Create a table for tasks
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim", width=3)
        table.add_column("Query", style="green")
        table.add_column("Reasoning", style="yellow")

        for i, task in enumerate(plan.tasks, 1):
            table.add_row(str(i), task.query, task.reasoning)

        # Create the panel content
        content = f"[bold]Strategy:[/bold] {plan.strategy}\n\n"
        
        self.console.print()
        self.console.print(Panel(
            content,
            title=f"[bold blue]Research Plan for:[/bold blue] {plan.question}",
            border_style="blue",
        ))
        self.console.print(table)
        self.console.print()

    def get_decision(self) -> Literal["approve", "modify", "reject", "quit"]:
        """Prompt user for decision on the plan.
        
        Returns:
            User's decision
        """
        self.console.print("[bold]Options:[/bold]")
        self.console.print("  [green][A]pprove[/green] - Execute the plan as-is")
        self.console.print("  [yellow][M]odify[/yellow] - Edit the plan tasks")
        self.console.print("  [red][R]eject[/red] - Reject and provide feedback for replanning")
        self.console.print("  [dim][Q]uit[/dim] - Abort the workflow")
        self.console.print()

        while True:
            choice = Prompt.ask(
                "Your decision",
                choices=["a", "m", "r", "q", "approve", "modify", "reject", "quit"],
                default="a",
            ).lower()

            decision_map = {
                "a": "approve",
                "approve": "approve",
                "m": "modify",
                "modify": "modify",
                "r": "reject",
                "reject": "reject",
                "q": "quit",
                "quit": "quit",
            }

            return decision_map[choice]

    def edit_plan(self, plan: ResearchPlan) -> ResearchPlan:
        """Allow inline editing of plan tasks.
        
        Args:
            plan: The original plan
            
        Returns:
            Modified plan with user edits
        """
        self.console.print("\n[bold yellow]Editing Plan[/bold yellow]")
        self.console.print("For each task, you can modify the query or press Enter to keep it.\n")

        modified_tasks = []
        for i, task in enumerate(plan.tasks, 1):
            self.console.print(f"[bold]Task {i}:[/bold]")
            self.console.print(f"  Current query: [green]{task.query}[/green]")
            self.console.print(f"  Reasoning: [dim]{task.reasoning}[/dim]")

            new_query = Prompt.ask(
                "  New query (Enter to keep)",
                default=task.query,
            )

            # Ask if they want to delete this task
            if new_query.strip().lower() in ["delete", "remove", "skip"]:
                if Confirm.ask(f"  Delete task {i}?"):
                    continue

            modified_tasks.append(ResearchTask(
                id=task.id,
                query=new_query,
                reasoning=task.reasoning,
            ))

        # Ask if they want to add new tasks
        while Confirm.ask("\nAdd another task?", default=False):
            query = Prompt.ask("  Query")
            reasoning = Prompt.ask("  Reasoning")
            
            new_id = f"task_{len(modified_tasks) + 1}"
            modified_tasks.append(ResearchTask(
                id=new_id,
                query=query,
                reasoning=reasoning,
            ))

        return ResearchPlan(
            question=plan.question,
            tasks=modified_tasks,
            strategy=plan.strategy,
        )

    def get_rejection_feedback(self) -> str:
        """Get feedback from the user for replanning.
        
        Returns:
            User's feedback string
        """
        self.console.print("\n[bold red]Plan Rejected[/bold red]")
        self.console.print("Please provide feedback to help improve the plan:\n")
        
        feedback = Prompt.ask("Feedback")
        return feedback

    async def review(self, plan: ResearchPlan) -> HumanPlanReview:
        """Full review flow returning human decision.
        
        Args:
            plan: The research plan to review
            
        Returns:
            HumanPlanReview with the user's decision
        """
        logger.info("human_review_start", task_count=len(plan.tasks))

        # Display the plan
        self.display_plan(plan)

        # Get decision
        decision = self.get_decision()
        logger.info("human_decision", decision=decision)

        if decision == "quit":
            raise KeyboardInterrupt("User aborted workflow")

        if decision == "approve":
            return HumanPlanReview(action="approve")

        if decision == "modify":
            modified_plan = self.edit_plan(plan)
            self.console.print("\n[bold green]Modified plan saved.[/bold green]")
            return HumanPlanReview(
                action="modify",
                modified_plan=modified_plan,
            )

        if decision == "reject":
            feedback = self.get_rejection_feedback()
            return HumanPlanReview(
                action="reject",
                feedback=feedback,
            )

        # Should never reach here
        raise ValueError(f"Unknown decision: {decision}")

