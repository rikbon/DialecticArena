"""
Agent Orchestrator (Dialectic Arena)
An extensible multi-agent debate and collaboration framework for agentic coding CLIs.
"""

from agent_orchestrator.types import (
    TurnContext,
    TurnResult,
    HealthCheckResult,
    ArenaEvent,
    EventType,
)
from agent_orchestrator.config import (
    ArenaConfig,
    AgentConfig,
    WorkspaceConfig,
    load_config,
)
from agent_orchestrator.core.orchestrator import Orchestrator
from agent_orchestrator.adapters.base import BaseAgentAdapter, AgentRegistry

__version__ = "0.1.0"
__all__ = [
    "Orchestrator",
    "ArenaConfig",
    "AgentConfig",
    "WorkspaceConfig",
    "load_config",
    "BaseAgentAdapter",
    "AgentRegistry",
    "TurnContext",
    "TurnResult",
    "HealthCheckResult",
    "ArenaEvent",
    "EventType",
]
