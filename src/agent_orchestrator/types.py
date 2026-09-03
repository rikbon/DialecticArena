"""
Core domain types and data structures for Agent Orchestrator.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class EventType(str, Enum):
    ARENA_START = "arena_start"
    ARENA_COMPLETE = "arena_complete"
    ROUND_START = "round_start"
    ROUND_COMPLETE = "round_complete"
    TURN_START = "turn_start"
    TURN_COMPLETE = "turn_complete"
    MANIFESTO_UPDATED = "manifesto_updated"
    MEMORY_UPDATED = "memory_updated"
    GIT_COMMITTED = "git_committed"
    ERROR = "error"


@dataclass
class ArenaEvent:
    event_type: EventType
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    round_num: int = 0
    turn_num: int = 0
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthCheckResult:
    is_available: bool
    version: Optional[str] = None
    binary_path: Optional[str] = None
    error_details: Optional[str] = None


@dataclass
class TurnContext:
    round_num: int
    turn_num: int
    agent_id: str
    agent_name: str
    agent_role: str
    opponent_id: str
    opponent_name: str
    opponent_role: str
    opponent_dialogue: str
    topic: str
    manifesto_content: str
    agent_memory: str
    history_summary: str = ""


@dataclass
class TurnResult:
    agent_id: str
    agent_name: str
    raw_output: str
    dialogue: str
    ontology_contribution: str
    internal_evolution: str
    execution_time_seconds: float = 0.0
    exit_code: int = 0
    error_message: Optional[str] = None
    is_success: bool = True
