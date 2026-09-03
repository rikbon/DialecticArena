"""
Tests for core Orchestrator execution loop.
"""

from agent_orchestrator.config import ArenaConfig
from agent_orchestrator.core.events import EventBus
from agent_orchestrator.core.orchestrator import Orchestrator
from agent_orchestrator.types import ArenaEvent, EventType


def test_orchestrator_full_loop(mock_arena_config: ArenaConfig):
    events_received: list[ArenaEvent] = []

    bus = EventBus()
    bus.subscribe(lambda ev: events_received.append(ev))

    orchestrator = Orchestrator(config=mock_arena_config, event_bus=bus)
    orchestrator.initialize()

    # Verify health
    health = orchestrator.check_agents_health()
    assert health["agent_a"].is_available is True
    assert health["agent_b"].is_available is True

    # Run 2 rounds
    results = orchestrator.run()

    # 2 rounds * 2 agents = 4 turns
    assert len(results) == 4
    for res in results:
        assert res.is_success is True
        assert len(res.dialogue) > 0

    # Verify events
    event_types = [ev.event_type for ev in events_received]
    assert EventType.ARENA_START in event_types
    assert EventType.ROUND_START in event_types
    assert EventType.TURN_START in event_types
    assert EventType.TURN_COMPLETE in event_types
    assert EventType.ROUND_COMPLETE in event_types
    assert EventType.ARENA_COMPLETE in event_types

    # Verify files created and populated
    manifesto = orchestrator.workspace.read_manifesto()
    assert "Proposition" in manifesto
    assert len(manifesto) > 200

    mem_a = orchestrator.workspace.read_memory("agent_a")
    assert "Reflection" in mem_a
