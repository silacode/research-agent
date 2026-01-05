"""Writer Agent - Generates markdown reports from research findings."""

from pydantic import BaseModel, Field
import structlog

from src.agents.base import BaseAgent
from src.models.research import ResearchFindings, EnrichedSource
from src.models.report import FinalReport
from src.prompts.writer import (
    WRITER_SYSTEM_PROMPT,
    get_writer_user_prompt,
    get_revision_prompt,
)

logger = structlog.get_logger()


class ReportDraft(BaseModel):
    """Draft report output from the writer LLM."""
    
    title: str = Field(description="Report title")
    content: str = Field(description="Full markdown content of the report")


class WriterAgent(BaseAgent[ReportDraft]):
    """Agent that writes markdown reports from research findings.
    
    The writer:
    1. Synthesizes findings from all research tasks
    2. Creates a well-structured markdown report
    3. Properly cites sources with links
    4. Can revise based on editor feedback
    """

    @property
    def name(self) -> str:
        return "writer_agent"

    @property
    def system_prompt(self) -> str:
        return WRITER_SYSTEM_PROMPT

    @property
    def output_type(self) -> type[ReportDraft]:
        return ReportDraft

    async def write_report(
        self,
        question: str,
        findings: list[ResearchFindings],
    ) -> FinalReport:
        """Write a report from research findings.
        
        Args:
            question: The original research question
            findings: List of findings from all research tasks
            
        Returns:
            FinalReport with title, content, and sources
        """
        logger.info("writing_report", question=question, finding_count=len(findings))

        # Collect all sources
        all_sources = []
        for finding in findings:
            all_sources.extend(finding.sources)

        # Format findings for LLM
        findings_summary = self._format_findings_for_llm(findings)
        
        prompt = get_writer_user_prompt(question, findings_summary)
        draft = await self.run(prompt)

        logger.info(
            "report_draft_complete",
            title=draft.title,
            content_length=len(draft.content),
        )

        return FinalReport(
            title=draft.title,
            content=draft.content,
            sources=all_sources,
            iterations=1,
        )

    async def revise_report(
        self,
        question: str,
        current_report: FinalReport,
        feedback: str,
    ) -> FinalReport:
        """Revise a report based on editor feedback.
        
        Args:
            question: The original research question
            current_report: The current draft to revise
            feedback: Feedback from the editor
            
        Returns:
            Revised FinalReport
        """
        logger.info(
            "revising_report",
            title=current_report.title,
            iteration=current_report.iterations,
        )

        prompt = get_revision_prompt(question, current_report.content, feedback)
        revised = await self.run(prompt)

        logger.info("revision_complete", new_title=revised.title)

        return FinalReport(
            title=revised.title,
            content=revised.content,
            sources=current_report.sources,
            iterations=current_report.iterations + 1,
        )

    def _format_findings_for_llm(self, findings: list[ResearchFindings]) -> str:
        """Format all findings for the LLM prompt.
        
        Args:
            findings: List of research findings
            
        Returns:
            Formatted string for LLM prompt
        """
        parts = []

        for finding in findings:
            parts.append(f"## Research Task: {finding.query}\n")
            parts.append(f"**Summary**: {finding.summary}\n")
            
            if finding.arxiv_papers:
                parts.append("\n**ArXiv Papers Found:**")
                for paper in finding.arxiv_papers:
                    parts.append(
                        f"- [{paper.title}]({paper.url}) by {', '.join(paper.authors[:3])}"
                    )
                    parts.append(f"  Abstract: {paper.abstract[:300]}...")
            
            if finding.wikipedia_articles:
                parts.append("\n**Wikipedia Articles:**")
                for article in finding.wikipedia_articles:
                    parts.append(f"- [{article.title}]({article.url})")
                    parts.append(f"  Summary: {article.summary[:300]}...")
            
            parts.append("\n**All Sources:**")
            for source in finding.sources:
                source_label = f"[{source.source_type.upper()}]"
                parts.append(f"- {source_label} [{source.title}]({source.url})")
            
            parts.append("\n---\n")

        return "\n".join(parts)

