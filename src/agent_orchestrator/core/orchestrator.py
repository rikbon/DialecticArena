"""
Core orchestration loop for multi-agent debates and collaborations.
Coordinates turn taking, workspace persistence, event emission, and git tracking.
"""

from pathlib import Path
from typing import Optional

from agent_orchestrator.adapters.base import AgentRegistry, BaseAgentAdapter
from agent_orchestrator.config import ArenaConfig
from agent_orchestrator.core.events import EventBus
from agent_orchestrator.types import (
    ArenaEvent,
    EventType,
    HealthCheckResult,
    TurnContext,
    TurnResult,
)
from agent_orchestrator.workspace.manager import WorkspaceManager
from agent_orchestrator.workspace.convergence import ConvergenceAnalyzer, ConvergenceReport


class Orchestrator:
    """Orchestrates turn-based interactions between CLI agents."""

    def __init__(
        self,
        config: ArenaConfig,
        base_dir: Optional[Path] = None,
        event_bus: Optional[EventBus] = None,
    ):
        self.config = config
        self.base_dir = (base_dir or Path.cwd()).resolve()
        self.event_bus = event_bus or EventBus()
        self.workspace = WorkspaceManager(config.workspace, base_dir=self.base_dir)
        self.adapters: dict[str, BaseAgentAdapter] = {}

    def initialize(self) -> None:
        """Initialize workspace and instantiate all configured agent adapters."""
        self.workspace.initialize(self.config.topic, self.config.agents)

        for agent_id, agent_cfg in self.config.agents.items():
            adapter = AgentRegistry.create(
                agent_id=agent_id,
                config=agent_cfg,
                workspace_dir=self.workspace.workspace_dir,
                base_dir=self.base_dir,
            )
            self.adapters[agent_id] = adapter

    def check_agents_health(self) -> dict[str, HealthCheckResult]:
        """Perform health checks on all configured agents."""
        results = {}
        for agent_id, adapter in self.adapters.items():
            results[agent_id] = adapter.health_check()
        return results

    def run(self) -> list[TurnResult]:
        """Run the full debate loop according to configured rounds and agents."""
        if not self.adapters:
            self.initialize()

        ordered_agents = self.config.get_ordered_agents()
        if len(ordered_agents) < 2:
            raise ValueError("At least two agents are required to run an arena debate.")

        all_results: list[TurnResult] = []
        total_turns = self.config.total_turns

        # Emit ARENA_START
        self.event_bus.dispatch(
            ArenaEvent(
                event_type=EventType.ARENA_START,
                payload={
                    "topic": self.config.topic,
                    "total_turns": total_turns,
                    "agents": {aid: acfg.name for aid, acfg in ordered_agents},
                },
            )
        )

        current_input = self.config.topic
        last_agent_id = ordered_agents[-1][0]
        last_agent_name = ordered_agents[-1][1].name
        last_agent_role = ordered_agents[-1][1].role

        try:
            for turn_idx in range(1, total_turns + 1):
                # Start of complete interaction
                self.event_bus.dispatch(
                    ArenaEvent(
                        event_type=EventType.TURN_START,
                        turn_num=turn_idx,
                        round_num=turn_idx,
                        payload={"turn": turn_idx, "total_turns": total_turns},
                    )
                )

                turn_exchange_dialogue: list[str] = []

                for step_idx, (agent_id, agent_cfg) in enumerate(ordered_agents, start=1):
                    adapter = self.adapters[agent_id]
                    
                    # Determine step label
                    if self.config.mode == "moderated" and len(ordered_agents) >= 3:
                        if step_idx == 1:
                            step_label = "Thesis"
                        elif step_idx == 2:
                            step_label = "Antithesis"
                        elif step_idx == 3:
                            step_label = "Synthesis & Moderation"
                        else:
                            step_label = f"Intervention {step_idx}"
                    else:
                        step_label = (
                            "Thesis" if step_idx == 1
                            else ("Antithesis" if step_idx == 2 else f"Rebuttal {step_idx}")
                        )

                    # Read current workspace state
                    manifesto = self.workspace.read_manifesto()
                    agent_memory = self.workspace.read_memory(agent_id)

                    # Determine opponent dialogue
                    if self.config.mode == "moderated" and step_idx == 3 and turn_exchange_dialogue:
                        step_opponent_dialogue = "\n\n---\n\n".join(turn_exchange_dialogue)
                        step_opponent_name = "Council Participants"
                        step_opponent_role = "Thesis & Antithesis Proponents"
                        step_opponent_id = "council"
                    else:
                        step_opponent_dialogue = current_input
                        step_opponent_name = last_agent_name
                        step_opponent_role = last_agent_role
                        step_opponent_id = last_agent_id

                    context = TurnContext(
                        turn_num=turn_idx,
                        step_num=step_idx,
                        step_label=step_label,
                        total_turns=total_turns,
                        round_num=turn_idx,
                        agent_id=agent_id,
                        agent_name=adapter.name,
                        agent_role=adapter.role,
                        opponent_id=step_opponent_id,
                        opponent_name=step_opponent_name,
                        opponent_role=step_opponent_role,
                        opponent_dialogue=step_opponent_dialogue,
                        topic=self.config.topic,
                        manifesto_content=manifesto,
                        agent_memory=agent_memory,
                    )

                    # Notify step start
                    self.event_bus.dispatch(
                        ArenaEvent(
                            event_type=EventType.STEP_START,
                            turn_num=turn_idx,
                            step_num=step_idx,
                            step_label=step_label,
                            round_num=turn_idx,
                            agent_id=agent_id,
                            agent_name=adapter.name,
                            payload={"context": context},
                        )
                    )

                    # Execute turn
                    result = adapter.execute_turn(context)
                    result.turn_num = turn_idx
                    result.step_num = step_idx
                    result.step_label = step_label
                    all_results.append(result)

                    # Handle turn updates
                    if result.is_success:
                        # 1. Update manifesto if ontology contribution present
                        if result.ontology_contribution:
                            self.workspace.update_manifesto(
                                agent_name=adapter.name,
                                turn_num=turn_idx,
                                step_label=step_label,
                                contribution=result.ontology_contribution,
                            )
                            self.event_bus.dispatch(
                                ArenaEvent(
                                    event_type=EventType.MANIFESTO_UPDATED,
                                    turn_num=turn_idx,
                                    step_num=step_idx,
                                    step_label=step_label,
                                    round_num=turn_idx,
                                    agent_id=agent_id,
                                    agent_name=adapter.name,
                                    payload={"contribution": result.ontology_contribution},
                                )
                            )

                        # 2. Update agent memory log
                        if result.internal_evolution:
                            self.workspace.append_memory(
                                agent_id=agent_id,
                                agent_name=adapter.name,
                                turn_num=turn_idx,
                                step_label=step_label,
                                evolution=result.internal_evolution,
                            )
                            self.event_bus.dispatch(
                                ArenaEvent(
                                    event_type=EventType.MEMORY_UPDATED,
                                    turn_num=turn_idx,
                                    step_num=step_idx,
                                    step_label=step_label,
                                    round_num=turn_idx,
                                    agent_id=agent_id,
                                    agent_name=adapter.name,
                                    payload={"evolution": result.internal_evolution},
                                )
                            )

                            # 2b. Dynamic persona mutation (Self-Modifying Prompts)
                            if self.config.mutate_personas:
                                updated_persona = self.workspace.mutate_persona(
                                    agent_id=agent_id,
                                    evolution_text=result.internal_evolution,
                                    turn_num=turn_idx,
                                )
                                adapter.update_persona(updated_persona)
                                self.event_bus.dispatch(
                                    ArenaEvent(
                                        event_type=EventType.PERSONA_MUTATED,
                                        turn_num=turn_idx,
                                        step_num=step_idx,
                                        step_label=step_label,
                                        round_num=turn_idx,
                                        agent_id=agent_id,
                                        agent_name=adapter.name,
                                        payload={"agent_id": agent_id, "updated_persona": updated_persona},
                                    )
                                )

                        # 3. Save snapshot
                        self.workspace.save_turn_snapshot(
                            turn_num=turn_idx,
                            step_num=step_idx,
                            step_label=step_label,
                            agent_id=agent_id,
                            result=result,
                        )

                        # 4. Optional git commit
                        commit_hash = self.workspace.commit_turn(
                            agent_name=adapter.name,
                            turn_num=turn_idx,
                            step_label=step_label,
                            summary=result.dialogue[:60],
                        )
                        if commit_hash:
                            self.event_bus.dispatch(
                                ArenaEvent(
                                    event_type=EventType.GIT_COMMITTED,
                                    turn_num=turn_idx,
                                    step_num=step_idx,
                                    step_label=step_label,
                                    round_num=turn_idx,
                                    agent_id=agent_id,
                                    agent_name=adapter.name,
                                    payload={"commit_hash": commit_hash},
                                )
                            )

                    # Notify step completion
                    self.event_bus.dispatch(
                        ArenaEvent(
                            event_type=EventType.STEP_COMPLETE,
                            turn_num=turn_idx,
                            step_num=step_idx,
                            step_label=step_label,
                            round_num=turn_idx,
                            agent_id=agent_id,
                            agent_name=adapter.name,
                            payload={"result": result},
                        )
                    )

                    # Record this step in the current turn's exchange
                    if result.dialogue:
                        turn_exchange_dialogue.append(f"[{adapter.name} ({step_label})]:\n{result.dialogue}")

                    # Update context for the next turn
                    current_input = result.dialogue
                    last_agent_id = agent_id
                    last_agent_name = adapter.name
                    last_agent_role = adapter.role

                # Evaluate dialectic convergence across turns
                turn_convergence = None
                if self.config.convergence_tracking:
                    manifesto_text = self.workspace.read_manifesto()
                    dialogue_history = [r.dialogue for r in all_results if r.dialogue]
                    turn_convergence = ConvergenceAnalyzer.analyze(manifesto_text, dialogue_history)
                    convergence_md = ConvergenceAnalyzer.generate_markdown_section(turn_convergence)
                    self.workspace.update_manifesto_convergence(convergence_md)
                    self.event_bus.dispatch(
                        ArenaEvent(
                            event_type=EventType.CONVERGENCE_EVALUATED,
                            turn_num=turn_idx,
                            round_num=turn_idx,
                            payload={"report": turn_convergence},
                        )
                    )

                # Completed full interaction
                self.event_bus.dispatch(
                    ArenaEvent(
                        event_type=EventType.TURN_COMPLETE,
                        turn_num=turn_idx,
                        round_num=turn_idx,
                        payload={"turn": turn_idx, "convergence": turn_convergence},
                    )
                )

        except KeyboardInterrupt:
            self.event_bus.dispatch(
                ArenaEvent(
                    event_type=EventType.ERROR,
                    payload={"error": "Debate interrupted by user."},
                )
            )

        # Final convergence summary
        final_convergence = None
        if self.config.convergence_tracking:
            manifesto_text = self.workspace.read_manifesto()
            dialogue_history = [r.dialogue for r in all_results if r.dialogue]
            final_convergence = ConvergenceAnalyzer.analyze(manifesto_text, dialogue_history)

        # Emit ARENA_COMPLETE
        self.event_bus.dispatch(
            ArenaEvent(
                event_type=EventType.ARENA_COMPLETE,
                payload={
                    "total_turns": total_turns,
                    "total_steps": len(all_results),
                    "manifesto_path": str(self.workspace.manifesto_path),
                    "final_convergence": final_convergence,
                },
            )
        )

        return all_results
