"""Agent adapter registry and built-in implementations."""

from agent_orchestrator.adapters.base import BaseAgentAdapter, AgentRegistry
from agent_orchestrator.adapters.agy import AntigravityAdapter
from agent_orchestrator.adapters.claude import ClaudeCodeAdapter
from agent_orchestrator.adapters.mock import MockAgentAdapter

__all__ = [
    "BaseAgentAdapter",
    "AgentRegistry",
    "AntigravityAdapter",
    "ClaudeCodeAdapter",
    "MockAgentAdapter",
]
