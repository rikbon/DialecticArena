"""
Workspace manager for the Dialectic Arena.
Maintains living documents on disk: manifesto, agent memory logs, and round snapshots.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from agent_orchestrator.config import WorkspaceConfig, AgentConfig
from agent_orchestrator.types import TurnResult
from agent_orchestrator.workspace.git_tracker import GitTracker


class WorkspaceManager:
    """Manages files in the shared arena workspace directory."""

    def __init__(self, config: WorkspaceConfig, base_dir: Optional[Path] = None):
        self.config = config
        base = base_dir or Path.cwd()
        self.workspace_dir = (base / config.dir_path).resolve()
        self.manifesto_path = self.workspace_dir / config.manifesto_filename
        self.rounds_dir = self.workspace_dir / "rounds"
        self.personas_dir = self.workspace_dir / "personas"
        self.topic_path = self.workspace_dir / "topic.md"
        self.git_tracker = GitTracker(self.workspace_dir, enabled=config.git_track)

    def initialize(self, topic: str, agents: dict[str, AgentConfig]) -> None:
        """Create workspace folders and initial seed files if they do not exist."""
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.rounds_dir.mkdir(parents=True, exist_ok=True)
        self.personas_dir.mkdir(parents=True, exist_ok=True)

        # Initialize topic.md
        if not self.topic_path.exists():
            self.topic_path.write_text(
                f"# Debate Topic\n\n> {topic}\n\n*Initialized: {datetime.now(timezone.utc).isoformat()}*\n",
                encoding="utf-8",
            )

        # Initialize arena_manifesto.md
        if not self.manifesto_path.exists():
            header = (
                "# Dialectic Arena Manifesto\n\n"
                f"> **Core Thesis / Seed Problem:**\n> {topic}\n\n"
                "## Participants\n"
            )
            for agent_id, agent_cfg in agents.items():
                header += f"- **{agent_cfg.name}** (`{agent_id}`): {agent_cfg.role}\n"
            header += (
                "\n---\n\n"
                "## Co-Authored Ontological Structure\n\n"
                "*The propositions below represent the emergent consensus, formal contradictions, "
                "and conceptual milestones produced during the dialectic exchange.*\n\n"
            )
            self.manifesto_path.write_text(header, encoding="utf-8")

        # Initialize memory files and dynamic persona files for each agent
        for agent_id, agent_cfg in agents.items():
            mem_path = self.get_memory_path(agent_id)
            if not mem_path.exists():
                mem_header = (
                    f"# Cognitive Evolution Log: {agent_cfg.name}\n\n"
                    f"- **Agent ID:** `{agent_id}`\n"
                    f"- **Role:** {agent_cfg.role}\n"
                    f"- **Adapter Type:** {agent_cfg.type}\n\n"
                    "---\n\n"
                    "## Internal Paradigm Shifts\n\n"
                )
                mem_path.write_text(mem_header, encoding="utf-8")

            # Seed dynamic persona file
            persona_path = self.get_persona_path(agent_id)
            if not persona_path.exists():
                base_persona = agent_cfg.get_persona()
                persona_path.write_text(base_persona, encoding="utf-8")

        # Ensure git repo initialized if requested
        if self.config.git_track:
            self.git_tracker.init_repo_if_needed()

    def get_memory_path(self, agent_id: str) -> Path:
        """Get the memory log path for a specific agent."""
        return self.workspace_dir / f"{self.config.memory_prefix}_{agent_id}.md"

    def get_persona_path(self, agent_id: str) -> Path:
        """Get the dynamic persona prompt file path for an agent."""
        return self.personas_dir / f"{agent_id}.txt"

    def read_manifesto(self) -> str:
        """Read current content of the manifesto."""
        if self.manifesto_path.exists():
            return self.manifesto_path.read_text(encoding="utf-8").strip()
        return ""

    def read_memory(self, agent_id: str) -> str:
        """Read current memory log for a specific agent."""
        mem_path = self.get_memory_path(agent_id)
        if mem_path.exists():
            return mem_path.read_text(encoding="utf-8").strip()
        return ""

    def read_persona(self, agent_id: str) -> str:
        """Read active dynamic persona for a specific agent."""
        p_path = self.get_persona_path(agent_id)
        if p_path.exists():
            return p_path.read_text(encoding="utf-8").strip()
        return ""

    def mutate_persona(
        self,
        agent_id: str,
        evolution_text: str,
        turn_num: int,
    ) -> str:
        """Append cognitive evolution directly into the agent's dynamic persona file on disk."""
        if not evolution_text.strip():
            return self.read_persona(agent_id)

        p_path = self.get_persona_path(agent_id)
        delta = (
            f"\n\n---\n"
            f"# DYNAMIC COGNITIVE CONCESSION & SYNTHESIS (Turn {turn_num})\n"
            f"*Incorporated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}*\n\n"
            f"{evolution_text.strip()}\n"
        )
        with open(p_path, "a", encoding="utf-8") as f:
            f.write(delta)
        return self.read_persona(agent_id)

    def update_manifesto_convergence(self, convergence_markdown: str) -> None:
        """Replace or append the Dialectic Convergence Status section in the manifesto."""
        if not self.manifesto_path.exists():
            return

        content = self.manifesto_path.read_text(encoding="utf-8")
        marker = "## Dialectic Convergence Status"

        if marker in content:
            # Cut at marker and replace
            base_content = content.split(marker)[0].rstrip()
            new_content = f"{base_content}\n\n{convergence_markdown.strip()}\n"
        else:
            new_content = f"{content.rstrip()}\n\n---\n\n{convergence_markdown.strip()}\n"

        self.manifesto_path.write_text(new_content, encoding="utf-8")

    def update_manifesto(
        self,
        agent_name: str,
        turn_num: int,
        step_label: str = "Proposition",
        contribution: str = "",
        round_num: Optional[int] = None,
    ) -> None:
        """Append an agent's ontological contribution to the shared manifesto."""
        if not contribution.strip():
            return
        t_num = turn_num or round_num or 1
        label = f" ({step_label})" if step_label else ""
        entry = (
            f"\n### Turn {t_num}{label} — [{agent_name}]\n"
            f"*{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}*\n\n"
            f"{contribution.strip()}\n\n"
            "---\n"
        )
        with open(self.manifesto_path, "a", encoding="utf-8") as f:
            f.write(entry)

    def append_memory(
        self,
        agent_id: str,
        agent_name: str,
        turn_num: int,
        step_label: str = "Reflection",
        evolution: str = "",
        round_num: Optional[int] = None,
    ) -> None:
        """Append an internal evolution reflection to the agent's private memory log."""
        if not evolution.strip():
            return
        t_num = turn_num or round_num or 1
        label = f" ({step_label})" if step_label else ""
        mem_path = self.get_memory_path(agent_id)
        entry = (
            f"\n### Turn {t_num}{label} Reflection\n"
            f"*{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}*\n\n"
            f"{evolution.strip()}\n\n"
            "---\n"
        )
        with open(mem_path, "a", encoding="utf-8") as f:
            f.write(entry)

    def save_turn_snapshot(
        self,
        turn_num: int,
        step_num: int,
        step_label: str,
        agent_id: str,
        result: TurnResult,
    ) -> Path:
        """Save a snapshot of the interaction step in JSON format for reproducibility."""
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"turn_{turn_num:02d}_step_{step_num:02d}_{agent_id}_{timestamp_str}.json"
        snapshot_path = self.rounds_dir / filename

        data = {
            "turn": turn_num,
            "step": step_num,
            "step_label": step_label,
            "agent_id": agent_id,
            "agent_name": result.agent_name,
            "execution_time_seconds": result.execution_time_seconds,
            "dialogue": result.dialogue,
            "ontology_contribution": result.ontology_contribution,
            "internal_evolution": result.internal_evolution,
            "raw_output": result.raw_output,
            "exit_code": result.exit_code,
            "error_message": result.error_message,
        }

        with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return snapshot_path

    def save_round_snapshot(self, *args, **kwargs) -> Path:
        """Compatibility wrapper for save_turn_snapshot."""
        if "round_num" in kwargs and "turn_num" in kwargs:
            return self.save_turn_snapshot(
                turn_num=kwargs["round_num"],
                step_num=kwargs["turn_num"],
                step_label="Step",
                agent_id=kwargs["agent_id"],
                result=kwargs["result"],
            )
        elif len(args) == 4:
            return self.save_turn_snapshot(
                turn_num=args[0],
                step_num=args[1],
                step_label="Step",
                agent_id=args[2],
                result=args[3],
            )
        return self.save_turn_snapshot(*args, **kwargs)

    def commit_turn(
        self,
        agent_name: str,
        turn_num: int,
        step_label: str = "Thesis",
        summary: str = "",
        round_num: Optional[int] = None,
    ) -> Optional[str]:
        """Commit current workspace files to git."""
        if not self.config.git_track:
            return None
        return self.git_tracker.commit_turn(
            agent_name=agent_name,
            turn_num=turn_num or round_num or 1,
            step_label=step_label,
            summary=summary,
        )
