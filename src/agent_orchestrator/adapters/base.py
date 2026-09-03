"""
Base adapter interface and factory registry for agent CLI integrations.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, ClassVar, Optional, Type

from agent_orchestrator.config import AgentConfig
from agent_orchestrator.types import HealthCheckResult, TurnContext, TurnResult


class BaseAgentAdapter(ABC):
    """Abstract base class for all agent adapters."""

    def __init__(
        self,
        agent_id: str,
        config: AgentConfig,
        workspace_dir: Path,
        base_dir: Optional[Path] = None,
    ):
        self.agent_id = agent_id
        self.config = config
        self.workspace_dir = workspace_dir
        self.base_dir = base_dir or Path.cwd()
        self.persona = config.get_persona(self.base_dir)

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def role(self) -> str:
        return self.config.role

    @property
    def color(self) -> str:
        return self.config.color

    def build_prompt(self, context: TurnContext) -> str:
        """Construct a rich prompt containing persona, workspace context, and opponent thesis."""
        lines = [
            f"# AGENT SYSTEM IDENTITY: {self.name}",
            f"Role: {self.role}",
            "",
            self.persona,
            "",
            "--- SHARED WORKSPACE STATE ---",
            f"Topic: {context.topic}",
            "",
            "--- CURRENT ARENA MANIFESTO (CO-AUTHORED ONTOLOGY) ---",
            context.manifesto_content if context.manifesto_content else "(Empty manifesto - you may propose the initial foundations)",
            "",
            f"--- YOUR PRIVATE MEMORY LOG ({self.name}) ---",
            context.agent_memory if context.agent_memory else "(No previous reflections recorded)",
            "",
            f"--- OPPONENT ARGUMENT ({context.opponent_name} - {context.opponent_role}) ---",
            context.opponent_dialogue,
            "",
            "--- YOUR MANDATORY OUTPUT PROTOCOL ---",
            "Structure your response strictly into these three clearly delineated markdown sections:",
            "",
            "### ARGUMENT",
            "Deliver your direct philosophical reply, formal deconstruction, or thesis directly to your opponent. Avoid polite conversational filler; be rigorous, dense, and intellectually piercing.",
            "",
            "### ONTOLOGY CONTRIBUTION",
            "Provide 1-3 formal definitions, propositions, or conceptual syntheses to be integrated into the shared arena manifesto.",
            "",
            "### INTERNAL EVOLUTION",
            "State in 2-4 sentences how this turn has shifted, refined, or challenged your internal framework.",
        ]
        return "\n".join(lines)

    @abstractmethod
    def execute_turn(self, context: TurnContext) -> TurnResult:
        """Execute a single debate turn using this agent."""
        pass

    @abstractmethod
    def health_check(self) -> HealthCheckResult:
        """Verify that the required binary/service is installed and operational."""
        pass


class AgentRegistry:
    """Registry for discovering and instantiating agent adapters."""

    _registry: ClassVar[dict[str, Type[BaseAgentAdapter]]] = {}

    @classmethod
    def register(cls, type_name: str) -> Callable[[Type[BaseAgentAdapter]], Type[BaseAgentAdapter]]:
        """Decorator to register an adapter class for a given type name."""
        def decorator(subclass: Type[BaseAgentAdapter]) -> Type[BaseAgentAdapter]:
            cls._registry[type_name.lower()] = subclass
            return subclass
        return decorator

    @classmethod
    def create(
        cls,
        agent_id: str,
        config: AgentConfig,
        workspace_dir: Path,
        base_dir: Optional[Path] = None,
    ) -> BaseAgentAdapter:
        """Instantiate the registered adapter for the configured type."""
        adapter_cls = cls._registry.get(config.type.lower())
        if not adapter_cls:
            available = ", ".join(cls._registry.keys())
            raise ValueError(
                f"Unknown agent type '{config.type}'. Available adapter types: {available}"
            )
        return adapter_cls(
            agent_id=agent_id,
            config=config,
            workspace_dir=workspace_dir,
            base_dir=base_dir,
        )

    @classmethod
    def get_registered_types(cls) -> list[str]:
        """Return list of registered agent adapter names."""
        return sorted(list(cls._registry.keys()))
