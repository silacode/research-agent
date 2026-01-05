"""Base tool protocol and shared types."""

from abc import ABC, abstractmethod
from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    """Standard result from any tool."""

    content: str = Field(description="Main content from the tool")
    url: str | None = Field(default=None, description="Source URL if applicable")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class BaseTool(ABC):
    """Base class for all research tools."""

    name: str
    description: str

    @abstractmethod
    async def execute(self, query: str) -> list[ToolResult]:
        """Execute the tool with the given query.
        
        Args:
            query: The search query or URL to process
            
        Returns:
            List of tool results
        """
        ...

