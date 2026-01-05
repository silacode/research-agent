"""Base agent abstraction using PydanticAI."""

import os
from abc import ABC, abstractmethod
from typing import TypeVar, Generic
from pydantic import BaseModel
from pydantic_ai import Agent
import structlog

logger = structlog.get_logger()

# Type variable for agent output
T = TypeVar("T", bound=BaseModel)


class BaseAgent(ABC, Generic[T]):
    """Base class for all research agents.

    Provides common functionality for PydanticAI-based agents:
    - Model initialization via string format (e.g., 'openai:gpt-4o')
    - Structured output parsing
    - Logging and error handling
    """

    def __init__(
        self,
        model_name: str = "gpt-4o",
        api_key: str | None = None,
    ):
        """Initialize the base agent.

        Args:
            model_name: Model to use (e.g., 'gpt-4o', 'gpt-4o-mini')
            api_key: OpenAI API key (uses OPENAI_API_KEY env var if not provided)
        """
        self.model_name = model_name
        self.api_key = api_key
        self._agent: Agent[None, T] | None = None

        # Set API key in environment if provided (PydanticAI reads from env)
        if api_key:
            os.environ.setdefault("OPENAI_API_KEY", api_key)

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent name for logging."""
        ...

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """System prompt for the agent."""
        ...

    @property
    @abstractmethod
    def output_type(self) -> type[T]:
        """Pydantic model type for structured output."""
        ...

    def _create_agent(self) -> Agent[None, T]:
        """Create the PydanticAI agent.

        Returns:
            Configured Agent instance
        """
        # Use string format for model specification (e.g., 'openai:gpt-4o')
        model_str = (
            f"openai:{self.model_name}"
            if ":" not in self.model_name
            else self.model_name
        )

        return Agent(  # type: ignore[return-value]
            model_str,
            output_type=self.output_type,
            system_prompt=self.system_prompt,
        )

    @property
    def agent(self) -> Agent[None, T]:
        """Get or create the agent (lazy initialization)."""
        if self._agent is None:
            self._agent = self._create_agent()
        return self._agent

    async def run(self, prompt: str) -> T:
        """Run the agent with the given prompt.

        Args:
            prompt: User prompt to process

        Returns:
            Structured output of type T
        """
        logger.info(f"{self.name}_start", prompt_length=len(prompt))

        try:
            result = await self.agent.run(prompt)
            logger.info(f"{self.name}_complete")
            return result.output  # type: ignore[return-value]

        except Exception as e:
            logger.error(f"{self.name}_error", error=str(e))
            raise
