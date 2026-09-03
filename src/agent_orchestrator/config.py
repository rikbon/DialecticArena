"""
Configuration schemas and loaders for Agent Orchestrator.
Uses Pydantic V2 for strict validation and PyYAML for config files.
"""

from pathlib import Path
from typing import Any, Optional
import yaml
from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    type: str = Field(..., description="Agent adapter type: 'agy', 'claude', 'mock', etc.")
    name: str = Field(..., description="Display name for the agent")
    role: str = Field(default="", description="Philosophical role or stance")
    color: str = Field(default="cyan", description="Rich console color tag")
    persona_file: Optional[str] = Field(default=None, description="Path to text file containing system persona")
    persona_text: Optional[str] = Field(default=None, description="Inline persona instructions")
    model: Optional[str] = Field(default=None, description="Model identifier if supported by CLI")
    effort: Optional[str] = Field(default=None, description="Reasoning effort: low|medium|high (agy)")
    timeout_seconds: int = Field(default=180, description="Process timeout in seconds")
    dangerously_skip_permissions: bool = Field(default=True, description="Auto-approve tool permissions")
    extra_args: list[str] = Field(default_factory=list, description="Additional CLI flags")
    env: dict[str, str] = Field(default_factory=dict, description="Custom environment variables")

    def get_persona(self, base_dir: Optional[Path] = None) -> str:
        """Resolve and read the persona text."""
        if self.persona_text:
            return self.persona_text.strip()
        if self.persona_file:
            path = Path(self.persona_file)
            if not path.is_absolute() and base_dir:
                path = base_dir / path
            if path.exists():
                return path.read_text(encoding="utf-8").strip()
            raise FileNotFoundError(f"Persona file not found: {path}")
        return f"You are {self.name}, participating as {self.role}."


class WorkspaceConfig(BaseModel):
    dir_path: str = Field(default="workspace", description="Directory path for shared workspace files")
    manifesto_filename: str = Field(default="arena_manifesto.md", description="Shared manifesto file")
    memory_prefix: str = Field(default="memory", description="Prefix for agent memory logs")
    git_track: bool = Field(default=True, description="Auto-commit updates to git if repository present")
    autonomous_tools: bool = Field(default=False, description="Let agents modify files directly via their tools")


class ArenaConfig(BaseModel):
    topic: str = Field(
        default="Is the universe purely mathematical structure, or does phenomenal consciousness represent an irreducible ontological primitive?",
        description="The core topic or controversy of the debate",
    )
    turns: int = Field(default=3, ge=1, le=50, description="Number of complete interactions ('botte e risposte')")
    rounds: Optional[int] = Field(default=None, description="Compatibility alias for turns")
    mode: str = Field(default="ping_pong", description="Debate mode: ping_pong, round_robin, moderated")
    mutate_personas: bool = Field(default=False, description="Whether to dynamically evolve and persist persona prompts across turns")
    convergence_tracking: bool = Field(default=True, description="Calculate proposition status and convergence alignment score")
    agents: dict[str, AgentConfig] = Field(default_factory=dict, description="Configured agents by ID")
    agent_order: list[str] = Field(default_factory=list, description="Ordered list of agent IDs for turns")
    workspace: WorkspaceConfig = Field(default_factory=WorkspaceConfig)
    max_history_turns: int = Field(default=6, description="Recent conversation turns included in prompt")

    def model_post_init(self, __context: Any) -> None:
        if self.rounds is not None and self.turns == 3:
            self.turns = self.rounds

    @property
    def total_turns(self) -> int:
        return self.turns

    def get_ordered_agents(self) -> list[tuple[str, AgentConfig]]:
        """Return list of (agent_id, AgentConfig) in execution order."""
        if self.agent_order:
            return [(agent_id, self.agents[agent_id]) for agent_id in self.agent_order if agent_id in self.agents]
        return list(self.agents.items())


def load_config(config_path: Path | str) -> ArenaConfig:
    """Load ArenaConfig from a YAML or JSON file."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    content = path.read_text(encoding="utf-8")
    data: dict[str, Any] = yaml.safe_load(content) or {}

    # Allow relative persona_file paths relative to config file directory
    base_dir = path.parent
    if "agents" in data and isinstance(data["agents"], dict):
        for agent_cfg in data["agents"].values():
            if isinstance(agent_cfg, dict) and "persona_file" in agent_cfg and agent_cfg["persona_file"]:
                pfile = Path(agent_cfg["persona_file"])
                if not pfile.is_absolute():
                    resolved = (base_dir / pfile).resolve()
                    if resolved.exists():
                        agent_cfg["persona_file"] = str(resolved)

    return ArenaConfig(**data)


def save_config(config: ArenaConfig, config_path: Path | str) -> None:
    """Save ArenaConfig to a YAML file."""
    path = Path(config_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = config.model_dump(mode="json")
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, indent=2)
