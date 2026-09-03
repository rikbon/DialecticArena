"""
Tests for WorkspaceManager and GitTracker.
"""

from pathlib import Path
from agent_orchestrator.config import AgentConfig, WorkspaceConfig
from agent_orchestrator.types import TurnResult
from agent_orchestrator.workspace.manager import WorkspaceManager


def test_workspace_initialization(tmp_path: Path):
    ws_config = WorkspaceConfig(
        dir_path=str(tmp_path / "ws"),
        manifesto_filename="test_manifesto.md",
        memory_prefix="mem",
        git_track=False,
    )
    manager = WorkspaceManager(ws_config)
    agents = {
        "claude": AgentConfig(type="mock", name="Claude", role="Alfa"),
        "antigravity": AgentConfig(type="mock", name="Antigravity", role="Beta"),
    }

    manager.initialize("Nature of Computation", agents)

    assert manager.manifesto_path.exists()
    assert manager.topic_path.exists()
    assert manager.get_memory_path("claude").exists()
    assert manager.get_memory_path("antigravity").exists()

    manifesto_text = manager.read_manifesto()
    assert "Nature of Computation" in manifesto_text
    assert "Claude" in manifesto_text
    assert "Antigravity" in manifesto_text


def test_workspace_updates(tmp_path: Path):
    ws_config = WorkspaceConfig(
        dir_path=str(tmp_path / "ws"),
        manifesto_filename="test_manifesto.md",
        memory_prefix="mem",
        git_track=False,
    )
    manager = WorkspaceManager(ws_config)
    agents = {"agent_1": AgentConfig(type="mock", name="Agent 1", role="R1")}
    manager.initialize("Test Topic", agents)

    # Update manifesto
    manager.update_manifesto("Agent 1", round_num=1, contribution="Proposition: Truth is invariant.")
    updated_manifesto = manager.read_manifesto()
    assert "Proposition: Truth is invariant." in updated_manifesto

    # Update memory
    manager.append_memory("agent_1", "Agent 1", round_num=1, evolution="Shifted paradigm.")
    updated_memory = manager.read_memory("agent_1")
    assert "Shifted paradigm." in updated_memory

    # Save snapshot
    res = TurnResult(
        agent_id="agent_1",
        agent_name="Agent 1",
        raw_output="raw",
        dialogue="dialogue text",
        ontology_contribution="ontology",
        internal_evolution="evolution",
    )
    snap_path = manager.save_round_snapshot(1, 1, "agent_1", res)
    assert snap_path.exists()
