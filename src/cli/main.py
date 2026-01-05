"""CLI entry point for the research agent."""

import asyncio
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from src.orchestrator import Orchestrator
from src.utils.config import get_settings
from src.utils.logging import setup_logging

console = Console()


def cli() -> None:
    """Main CLI entry point."""
    try:
        # Load settings
        settings = get_settings()
        
        # Setup logging
        setup_logging(settings.log_level, settings.log_format)

        # Display welcome banner
        console.print(Panel(
            "[bold]Research Agent[/bold]\n"
            "A reflective research agent that creates comprehensive reports.\n\n"
            "[dim]Type your research question or 'quit' to exit.[/dim]",
            title="[bold blue]Welcome[/bold blue]",
            border_style="blue",
        ))

        # Get question from user
        question = Prompt.ask("\n[bold]Enter your research question[/bold]")

        if question.lower() in ["quit", "exit", "q"]:
            console.print("[dim]Goodbye![/dim]")
            return

        # Run the orchestrator
        orchestrator = Orchestrator(settings, console)
        report = asyncio.run(orchestrator.run(question))

        # Offer to save the report
        save_path = Prompt.ask(
            "\n[bold]Save report to file?[/bold] (Enter path or press Enter to skip)",
            default="",
        )

        if save_path:
            path = Path(save_path)
            if not path.suffix:
                path = path.with_suffix(".md")
            
            path.write_text(report.content, encoding="utf-8")
            console.print(f"[green]✓ Report saved to {path}[/green]")

    except KeyboardInterrupt:
        console.print("\n[dim]Aborted by user.[/dim]")
        sys.exit(0)

    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        console.print("[dim]Use LOG_LEVEL=DEBUG for more details.[/dim]")
        sys.exit(1)


def main() -> None:
    """Wrapper for CLI entry point."""
    cli()


if __name__ == "__main__":
    main()

