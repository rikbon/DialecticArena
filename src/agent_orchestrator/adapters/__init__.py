"""Agent adapter registry and built-in implementations."""

from agent_orchestrator.adapters.base import BaseAgentAdapter, AgentRegistry
from agent_orchestrator.adapters.agy import AntigravityAdapter
from agent_orchestrator.adapters.claude import ClaudeCodeAdapter
from agent_orchestrator.adapters.mock import MockAgentAdapter
from agent_orchestrator.adapters.ollama import OllamaAdapter
from agent_orchestrator.adapters.aider import AiderAdapter
from agent_orchestrator.adapters.api import DirectApiAdapter

__all__ = [
    "BaseAgentAdapter",
    "AgentRegistry",
    "AntigravityAdapter",
    "ClaudeCodeAdapter",
    "MockAgentAdapter",
    "OllamaAdapter",
    "AiderAdapter",
    "DirectApiAdapter",
]
