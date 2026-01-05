"""Main workflow orchestrator with HITL and reflection loop."""

import structlog
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.markdown import Markdown

from src.models.plan import ResearchPlan, HumanPlanReview
from src.models.research import ResearchFindings
from src.models.report import FinalReport, EditorFeedback
from src.agents.planner import PlannerAgent
from src.agents.researcher import ResearcherAgent
from src.agents.writer import WriterAgent
from src.agents.editor import EditorAgent
from src.hitl.plan_review import PlanReviewer
from src.utils.config import Settings

logger = structlog.get_logger()


class Orchestrator:
    """Main workflow coordinator for the research agent.
    
    Coordinates the following workflow:
    1. Planner creates research plan
    2. Human reviews/approves plan (HITL)
    3. Researcher executes tasks with Tavily + enrichment
    4. Writer creates report from findings
    5. Editor reviews with quality threshold loop
    6. Output final markdown report
    """

    def __init__(
        self,
        settings: Settings,
        console: Console | None = None,
    ):
        """Initialize the orchestrator.
        
        Args:
            settings: Application settings
            console: Rich Console for output
        """
        self.settings = settings
        self.console = console or Console()

        # Initialize agents
        self.planner = PlannerAgent(
            model_name=settings.model_name,
            api_key=settings.openai_api_key,
        )
        self.researcher = ResearcherAgent(
            model_name=settings.model_name,
            api_key=settings.openai_api_key,
            tavily_api_key=settings.tavily_api_key,
            max_tavily_results=settings.max_tavily_results,
        )
        self.writer = WriterAgent(
            model_name=settings.model_name,
            api_key=settings.openai_api_key,
        )
        self.editor = EditorAgent(
            model_name=settings.model_name,
            api_key=settings.openai_api_key,
        )

        # HITL handler
        self.plan_reviewer = PlanReviewer(self.console)

    async def run(self, question: str) -> FinalReport:
        """Run the complete research workflow.
        
        Args:
            question: The user's research question
            
        Returns:
            FinalReport with the completed research report
        """
        logger.info("workflow_start", question=question)
        self.console.print(Panel(
            f"[bold]Research Question:[/bold] {question}",
            title="[bold blue]Research Agent[/bold blue]",
            border_style="blue",
        ))

        # Phase 1: Planning with HITL
        plan = await self._planning_phase(question)

        # Phase 2: Research
        findings = await self._research_phase(plan)

        # Phase 3: Writing with reflection loop
        report = await self._writing_phase(question, findings)

        # Output final report
        self._display_final_report(report)

        logger.info("workflow_complete", title=report.title, iterations=report.iterations)
        return report

    async def _planning_phase(self, question: str) -> ResearchPlan:
        """Execute the planning phase with HITL.
        
        Args:
            question: The research question
            
        Returns:
            Approved research plan
        """
        self.console.print("\n[bold cyan]Phase 1: Planning[/bold cyan]")
        
        plan_attempts = 0
        plan: ResearchPlan | None = None

        while plan_attempts < self.settings.max_plan_attempts:
            plan_attempts += 1

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task("Creating research plan...", total=None)
                
                if plan_attempts == 1:
                    plan = await self.planner.create_plan(question)
                else:
                    # This is a replan attempt
                    pass  # Plan is already set from the rejection flow

                progress.update(task, completed=True)

            if plan is None:
                raise RuntimeError("Failed to create plan")

            # Human review
            review = await self.plan_reviewer.review(plan)

            if review.action == "approve":
                self.console.print("[green]✓ Plan approved[/green]")
                return plan

            if review.action == "modify":
                if review.modified_plan:
                    self.console.print("[yellow]✓ Using modified plan[/yellow]")
                    return review.modified_plan
                return plan

            if review.action == "reject":
                if plan_attempts >= self.settings.max_plan_attempts:
                    self.console.print(
                        f"[red]Maximum plan attempts ({self.settings.max_plan_attempts}) reached.[/red]"
                    )
                    raise RuntimeError("Maximum plan attempts exceeded")

                self.console.print("[yellow]Replanning based on feedback...[/yellow]")
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=self.console,
                ) as progress:
                    task = progress.add_task("Replanning...", total=None)
                    plan = await self.planner.replan(question, review.feedback or "")
                    progress.update(task, completed=True)

        raise RuntimeError("Unexpected end of planning phase")

    async def _research_phase(self, plan: ResearchPlan) -> list[ResearchFindings]:
        """Execute the research phase.
        
        Args:
            plan: The approved research plan
            
        Returns:
            List of research findings
        """
        self.console.print("\n[bold cyan]Phase 2: Research[/bold cyan]")
        
        findings: list[ResearchFindings] = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            for i, task in enumerate(plan.tasks, 1):
                task_id = progress.add_task(
                    f"[{i}/{len(plan.tasks)}] Researching: {task.query[:50]}...",
                    total=None,
                )
                
                finding = await self.researcher.execute_task(task)
                findings.append(finding)

                progress.update(task_id, completed=True)
                self.console.print(
                    f"  [dim]Found {len(finding.sources)} sources, "
                    f"{len(finding.arxiv_papers)} papers, "
                    f"{len(finding.wikipedia_articles)} wiki articles[/dim]"
                )

        self.console.print(f"[green]✓ Research complete: {len(findings)} tasks executed[/green]")
        return findings

    async def _writing_phase(
        self,
        question: str,
        findings: list[ResearchFindings],
    ) -> FinalReport:
        """Execute the writing phase with reflection loop.
        
        Args:
            question: The original question
            findings: Research findings to synthesize
            
        Returns:
            Final approved report
        """
        self.console.print("\n[bold cyan]Phase 3: Writing & Editing[/bold cyan]")

        # Initial draft
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Writing initial draft...", total=None)
            report = await self.writer.write_report(question, findings)
            progress.update(task, completed=True)

        self.console.print(f"  [dim]Draft complete: {len(report.content)} characters[/dim]")

        # Reflection loop
        iteration = 0
        while iteration < self.settings.max_reflection_iterations:
            iteration += 1

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task(
                    f"Editor reviewing (iteration {iteration})...",
                    total=None,
                )
                feedback = await self.editor.review(question, report.content)
                progress.update(task, completed=True)

            self.console.print(
                f"  [dim]Score: {feedback.score}/10, "
                f"Issues: {len(feedback.issues)}, "
                f"Approved: {feedback.approved}[/dim]"
            )

            # Check approval conditions
            if feedback.approved:
                self.console.print("[green]✓ Report approved by editor[/green]")
                return report

            if feedback.score >= self.settings.approval_threshold:
                self.console.print(
                    f"[green]✓ Report meets quality threshold "
                    f"(score {feedback.score} >= {self.settings.approval_threshold})[/green]"
                )
                return report

            if iteration >= self.settings.max_reflection_iterations:
                self.console.print(
                    f"[yellow]⚠ Maximum iterations ({self.settings.max_reflection_iterations}) "
                    f"reached. Using current draft.[/yellow]"
                )
                return report

            # Revise based on feedback
            feedback_text = self.editor.format_feedback_for_writer(feedback)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task(
                    f"Revising draft (iteration {iteration})...",
                    total=None,
                )
                report = await self.writer.revise_report(question, report, feedback_text)
                progress.update(task, completed=True)

        return report

    def _display_final_report(self, report: FinalReport) -> None:
        """Display the final report.
        
        Args:
            report: The final report to display
        """
        self.console.print("\n" + "=" * 60)
        self.console.print(Panel(
            Markdown(report.content),
            title=f"[bold green]{report.title}[/bold green]",
            border_style="green",
        ))
        self.console.print("=" * 60)
        self.console.print(
            f"\n[dim]Report completed in {report.iterations} iteration(s) "
            f"with {len(report.sources)} sources.[/dim]"
        )

