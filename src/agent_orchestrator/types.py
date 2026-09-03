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
    TURN_START = "turn_start"          # Start of a complete exchange interaction
    TURN_COMPLETE = "turn_complete"    # End of a complete exchange interaction
    STEP_START = "step_start"          # Individual agent speaking (Thesis, Antithesis, etc.)
    STEP_COMPLETE = "step_complete"    # Individual agent completed response
    ROUND_START = "turn_start"         # Compatibility alias
    ROUND_COMPLETE = "turn_complete"   # Compatibility alias
    MANIFESTO_UPDATED = "manifesto_updated"
    MEMORY_UPDATED = "memory_updated"
    GIT_COMMITTED = "git_committed"
    ERROR = "error"


@dataclass
class ArenaEvent:
    event_type: EventType
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    turn_num: int = 0                  # 1, 2, 3 (Interaction exchange number)
    step_num: int = 0                  # 1 (Thesis), 2 (Antithesis), etc.
    step_label: str = ""               # "Thesis", "Antithesis", "Rebuttal"
    round_num: int = 0                 # Alias for turn_num
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
    turn_num: int                      # Interaction exchange index (1, 2, 3...)
    step_num: int                      # 1 = Thesis, 2 = Antithesis
    step_label: str                    # "Thesis" or "Antithesis"
    total_turns: int                   # Total interaction exchanges planned
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
    round_num: int = 0                 # Alias for turn_num


@dataclass
class TurnResult:
    agent_id: str
    agent_name: str
    raw_output: str
    dialogue: str
    ontology_contribution: str
    internal_evolution: str
    turn_num: int = 0
    step_num: int = 0
    step_label: str = ""
    execution_time_seconds: float = 0.0
    exit_code: int = 0
    error_message: Optional[str] = None
    is_success: bool = True
