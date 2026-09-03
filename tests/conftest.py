"""
Shared pytest fixtures for testing Dialectic Arena.
"""

import sys
from pathlib import Path
import pytest

# Ensure src is in python path
src_dir = Path(__file__).parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from agent_orchestrator.config import AgentConfig, ArenaConfig, WorkspaceConfig


@pytest.fixture
def temp_workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "test_workspace"
    ws.mkdir(parents=True, exist_ok=True)
    return ws


@pytest.fixture
def mock_arena_config(temp_workspace: Path) -> ArenaConfig:
    return ArenaConfig(
        topic="Is mathematics discovered or invented?",
        rounds=2,
        mode="ping_pong",
        workspace=WorkspaceConfig(
            dir_path=str(temp_workspace),
            manifesto_filename="test_manifesto.md",
            memory_prefix="mem",
            git_track=False,
        ),
        agents={
            "agent_a": AgentConfig(
                type="mock",
                name="Agent Alfa (Mock)",
                role="Analytical Realist",
                color="cyan",
                persona_text="Realist stance on mathematics.",
            ),
            "agent_b": AgentConfig(
                type="mock",
                name="Agent Beta (Mock)",
                role="Constructivist",
                color="magenta",
                persona_text="Constructivist stance on mathematics.",
            ),
        },
        agent_order=["agent_a", "agent_b"],
    )
