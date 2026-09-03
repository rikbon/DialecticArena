"""
Unit tests for the Dialectic Convergence Analyzer and Dynamic Persona Mutation.
"""

from pathlib import Path
from agent_orchestrator.workspace.convergence import ConvergenceAnalyzer, ConvergenceReport
from agent_orchestrator.config import WorkspaceConfig, AgentConfig, ArenaConfig
from agent_orchestrator.workspace.manager import WorkspaceManager
from agent_orchestrator.core.events import EventBus
from agent_orchestrator.core.orchestrator import Orchestrator
from agent_orchestrator.types import EventType


def test_convergence_analyzer_extraction_and_scoring():
    sample_manifesto = """# Dialectic Arena Manifesto

## Co-Authored Ontological Structure

### Turn 1 (Thesis) — [Claude Code]
Proposition 1.1: Supervenience Axiom: Macro-states strictly supervene on micro-states.
Proposition 1.2: Epistemic Compression: Holism is computational compression.

### Turn 1 (Antithesis) — [Antigravity]
Proposition 1.3: Relational Ontic Thesis: Relational networks cannot be factored into isolated parts.
Proposition 1.4: Mereological Invariance: The observer is the boundary condition.
"""

    dialogue_history = [
        "I accept and concede the Supervenience Axiom as a shared axiom for physical configurations.",
        "However, I refute Proposition 1.2 as a fallacy that neglects non-linear constraint dynamics.",
    ]

    report = ConvergenceAnalyzer.analyze(sample_manifesto, dialogue_history)

    assert report.total_propositions == 4
    assert report.accepted_count >= 1  # Proposition 1.1 accepted
    assert report.refuted_count >= 1   # Proposition 1.2 refuted
    assert 0.0 <= report.convergence_score <= 100.0
    assert report.status_label in ["Emerging Consensus", "Dialectically Progressing", "High Convergence", "Divergent"]

    markdown = ConvergenceAnalyzer.generate_markdown_section(report)
    assert "## Dialectic Convergence Status" in markdown
    assert "Alignment Score:" in markdown
    assert "Proposition 1.1" in markdown


def test_workspace_persona_mutation(tmp_path: Path):
    ws_cfg = WorkspaceConfig(dir_path="test_ws", git_track=False)
    wm = WorkspaceManager(ws_cfg, base_dir=tmp_path)

    agents = {
        "alfa": AgentConfig(type="mock", name="Alfa", persona_text="Base persona Alfa"),
        "beta": AgentConfig(type="mock", name="Beta", persona_text="Base persona Beta"),
    }
    wm.initialize(topic="Test topic", agents=agents)

    # Check that dynamic persona files were created
    p_path_alfa = wm.get_persona_path("alfa")
    assert p_path_alfa.exists()
    assert wm.read_persona("alfa") == "Base persona Alfa"

    # Mutate persona
    updated = wm.mutate_persona(
        agent_id="alfa",
        evolution_text="I concede that complexity requires non-linear category theory.",
        turn_num=1,
    )
    assert "DYNAMIC COGNITIVE CONCESSION & SYNTHESIS (Turn 1)" in updated
    assert "non-linear category theory" in updated
    assert wm.read_persona("alfa") == updated


def test_orchestrator_dynamic_mutation_and_convergence(tmp_path: Path):
    ws_cfg = WorkspaceConfig(dir_path="ws_mutation", git_track=False)
    agents = {
        "a1": AgentConfig(type="mock", name="Agent One", persona_text="Persona One"),
        "a2": AgentConfig(type="mock", name="Agent Two", persona_text="Persona Two"),
    }
    config = ArenaConfig(
        topic="Testing dynamic mutation",
        turns=2,
        mode="ping_pong",
        mutate_personas=True,
        convergence_tracking=True,
        agents=agents,
        agent_order=["a1", "a2"],
        workspace=ws_cfg,
    )

    events_fired = []
    bus = EventBus()
    bus.subscribe(lambda ev: events_fired.append(ev.event_type))

    orch = Orchestrator(config, event_bus=bus, base_dir=tmp_path)
    orch.initialize()
    results = orch.run()

    assert len(results) == 4  # 2 turns * 2 steps
    assert EventType.PERSONA_MUTATED in events_fired
    assert EventType.CONVERGENCE_EVALUATED in events_fired

    # Verify manifesto has convergence section
    manifesto_content = orch.workspace.read_manifesto()
    assert "## Dialectic Convergence Status" in manifesto_content
    assert "Alignment Score:" in manifesto_content

    # Verify adapter persona was updated in memory and on disk
    adapter_one = orch.adapters["a1"]
    assert "DYNAMIC COGNITIVE CONCESSION" in adapter_one.persona
