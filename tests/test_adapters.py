"""
Tests for agent adapters and registry.
"""

from pathlib import Path
from agent_orchestrator.adapters.base import AgentRegistry, BaseAgentAdapter
from agent_orchestrator.adapters.mock import MockAgentAdapter
from agent_orchestrator.adapters.agy import AntigravityAdapter
from agent_orchestrator.adapters.claude import ClaudeCodeAdapter
from agent_orchestrator.config import AgentConfig
from agent_orchestrator.types import TurnContext


def test_agent_registry_discovery():
    types = AgentRegistry.get_registered_types()
    assert "mock" in types
    assert "agy" in types
    assert "antigravity" in types
    assert "claude" in types
    assert "claude-code" in types


def test_mock_adapter_execution(tmp_path: Path):
    cfg = AgentConfig(type="mock", name="Mock Alfa", role="Analytic", persona_text="Test persona")
    adapter = AgentRegistry.create("mock_alfa", cfg, tmp_path)

    assert isinstance(adapter, MockAgentAdapter)
    assert adapter.name == "Mock Alfa"
    assert adapter.health_check().is_available is True

    context = TurnContext(
        turn_num=1,
        step_num=1,
        step_label="Thesis",
        total_turns=3,
        agent_id="mock_alfa",
        agent_name="Mock Alfa",
        agent_role="Analytic",
        opponent_id="mock_beta",
        opponent_name="Mock Beta",
        opponent_role="Holist",
        opponent_dialogue="Let us begin the discussion.",
        topic="Determinism vs Emergence",
        manifesto_content="",
        agent_memory="",
    )

    result = adapter.execute_turn(context)
    assert result.is_success is True
    assert len(result.dialogue) > 0
    assert len(result.ontology_contribution) > 0
    assert len(result.internal_evolution) > 0


def test_agy_adapter_health_check(tmp_path: Path):
    cfg = AgentConfig(type="agy", name="Antigravity", effort="high")
    adapter = AgentRegistry.create("agy_agent", cfg, tmp_path)
    assert isinstance(adapter, AntigravityAdapter)
    health = adapter.health_check()
    assert health.is_available is True
    assert health.version is not None


def test_claude_adapter_health_check(tmp_path: Path):
    cfg = AgentConfig(type="claude", name="Claude Code")
    adapter = AgentRegistry.create("claude_agent", cfg, tmp_path)
    assert isinstance(adapter, ClaudeCodeAdapter)
    health = adapter.health_check()
    assert health.is_available is True
    assert health.version is not None
