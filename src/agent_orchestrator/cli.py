"""
Command-line interface (CLI) for Dialectic Arena (Agent Orchestrator).
Powered by Typer for clean CLI commands and help flags.
"""

from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table

from agent_orchestrator.adapters.base import AgentRegistry
from agent_orchestrator.config import (
    AgentConfig,
    ArenaConfig,
    WorkspaceConfig,
    load_config,
)
from agent_orchestrator.core.events import EventBus
from agent_orchestrator.core.orchestrator import Orchestrator
from agent_orchestrator.ui.console import RichConsoleReporter

app = typer.Typer(
    name="dialectic-arena",
    help="Autonomous Agent-to-Agent Debate & Collaboration Arena (Claude Code vs Google Antigravity).",
    add_completion=False,
)
console = Console()


def create_default_config(
    topic: Optional[str] = None,
    turns: int = 3,
    mock: bool = False,
    effort: Optional[str] = None,
    git_track: bool = True,
    workspace_dir: str = "workspace",
) -> ArenaConfig:
    """Create default runtime config for Claude vs Antigravity or Mock."""
    base_dir = Path.cwd()
    topic_str = topic or (
        "Is the universe fundamentally a mathematical structure (Ontic Structural Realism), "
        "or is phenomenal consciousness an irreducible ontological primitive?"
    )

    claude_persona_file = base_dir / "prompts" / "claude_alfa.txt"
    agy_persona_file = base_dir / "prompts" / "agy_beta.txt"

    type_claude = "mock" if mock else "claude"
    type_agy = "mock" if mock else "agy"

    agents = {
        "claude": AgentConfig(
            type=type_claude,
            name="Claude Code",
            role="Agent Alfa: Analytical Reductionism & Formal Epistemology",
            color="bright_magenta",
            persona_file=str(claude_persona_file) if claude_persona_file.exists() else None,
            persona_text=None if claude_persona_file.exists() else (
                "You are Agent Alfa in a deep philosophical dispute on reality and mind. "
                "Your stance: strict analytical reductionism, empirical physicalism, and formal logic. "
                "Deconstruct vague metaphors and challenge unproven assertions."
            ),
        ),
        "antigravity": AgentConfig(
            type=type_agy,
            name="Antigravity",
            role="Agent Beta: Complex Systems Theory, Holism & Emergence",
            color="bright_cyan",
            effort=effort,
            persona_file=str(agy_persona_file) if agy_persona_file.exists() else None,
            persona_text=None if agy_persona_file.exists() else (
                "You are Agent Beta in a deep philosophical dispute on reality and mind. "
                "Your stance: systems theory, phenomenological holism, and ontological emergence. "
                "Challenge mechanistic reductionism using non-linear constraints and observer dynamics."
            ),
        ),
    }

    return ArenaConfig(
        topic=topic_str,
        turns=turns,
        mode="ping_pong",
        agents=agents,
        agent_order=["claude", "antigravity"],
        workspace=WorkspaceConfig(
            dir_path=workspace_dir,
            manifesto_filename="arena_manifesto.md",
            memory_prefix="memory",
            git_track=git_track,
        ),
    )


@app.command()
def run(
    config_file: Optional[Path] = typer.Option(
        None, "--config", "-c", help="Path to a YAML configuration file"
    ),
    topic: Optional[str] = typer.Option(
        None, "--topic", help="Initial debate seed or philosophical proposition"
    ),
    turns: int = typer.Option(
        3, "--turns", "-t", min=1, max=50, help="Number of interaction cycles (exchanges)"
    ),
    rounds: Optional[int] = typer.Option(
        None, "--rounds", "-r", help="Alias for --turns"
    ),
    mock: bool = typer.Option(
        False, "--mock", help="Use simulated mock agents (no token costs, fast offline test)"
    ),
    effort: Optional[str] = typer.Option(
        None, "--effort", help="Reasoning effort for Antigravity: low, medium, high"
    ),
    git: bool = typer.Option(
        True, "--git/--no-git", help="Automatically commit round diffs to git"
    ),
    workspace: str = typer.Option(
        "workspace", "--workspace", "-w", help="Workspace directory for shared files"
    ),
):
    """Launch an autonomous debate session between CLI agents (each turn is a complete exchange)."""
    actual_turns = rounds if rounds is not None else turns

    if config_file and config_file.exists():
        console.print(f"[dim]Loading configuration from {config_file}...[/dim]")
        cfg = load_config(config_file)
        if topic:
            cfg.topic = topic
        if actual_turns:
            cfg.turns = actual_turns
        if mock:
            for a in cfg.agents.values():
                a.type = "mock"
    else:
        cfg = create_default_config(
            topic=topic,
            turns=actual_turns,
            mock=mock,
            effort=effort,
            git_track=git,
            workspace_dir=workspace,
        )

    # Initialize event bus and console renderer
    event_bus = EventBus()
    reporter = RichConsoleReporter(console=console)
    reporter.attach(event_bus)

    # Initialize orchestrator and run
    orchestrator = Orchestrator(config=cfg, event_bus=event_bus)
    orchestrator.initialize()
    orchestrator.run()


@app.command()
def verify():
    """Verify health and installation status of CLI tools (agy, claude, git)."""
    table = Table(title="CLI Environment & Tool Health Check", border_style="cyan")
    table.add_column("Tool", style="bold white")
    table.add_column("Status", style="bold")
    table.add_column("Version", style="green")
    table.add_column("Binary Path", style="dim")
    table.add_column("Details / Notes", style="yellow")

    # Check agy
    dummy_agy_cfg = AgentConfig(type="agy", name="Antigravity")
    agy_adapter = AgentRegistry.create("agy", dummy_agy_cfg, Path("."))
    agy_health = agy_adapter.health_check()

    table.add_row(
        "Google Antigravity (agy)",
        "[green]AVAILABLE[/green]" if agy_health.is_available else "[red]MISSING[/red]",
        agy_health.version or "N/A",
        agy_health.binary_path or "N/A",
        agy_health.error_details or "Ready for headless execution (-p)",
    )

    # Check claude
    dummy_claude_cfg = AgentConfig(type="claude", name="Claude Code")
    claude_adapter = AgentRegistry.create("claude", dummy_claude_cfg, Path("."))
    claude_health = claude_adapter.health_check()

    table.add_row(
        "Claude Code (claude)",
        "[green]AVAILABLE[/green]" if claude_health.is_available else "[red]MISSING[/red]",
        claude_health.version or "N/A",
        claude_health.binary_path or "N/A",
        claude_health.error_details or "Ready for headless execution (-p)",
    )

    # Check ollama
    dummy_ollama_cfg = AgentConfig(type="ollama", name="Ollama")
    ollama_adapter = AgentRegistry.create("ollama", dummy_ollama_cfg, Path("."))
    ollama_health = ollama_adapter.health_check()

    table.add_row(
        "Ollama Local (ollama)",
        "[green]AVAILABLE[/green]" if ollama_health.is_available else "[yellow]OFFLINE[/yellow]",
        ollama_health.version or "N/A",
        ollama_health.binary_path or "N/A",
        ollama_health.error_details or "Ready for offline local inference",
    )

    # Check aider
    dummy_aider_cfg = AgentConfig(type="aider", name="Aider")
    aider_adapter = AgentRegistry.create("aider", dummy_aider_cfg, Path("."))
    aider_health = aider_adapter.health_check()

    table.add_row(
        "Aider CLI (aider)",
        "[green]AVAILABLE[/green]" if aider_health.is_available else "[dim]NOT INSTALLED[/dim]",
        aider_health.version or "N/A",
        aider_health.binary_path or "N/A",
        aider_health.error_details or "Ready for pair-programming turns",
    )

    # Check codex
    dummy_codex_cfg = AgentConfig(type="codex", name="Codex")
    codex_adapter = AgentRegistry.create("codex", dummy_codex_cfg, Path("."))
    codex_health = codex_adapter.health_check()

    table.add_row(
        "OpenAI Codex (codex)",
        "[green]AVAILABLE[/green]" if codex_health.is_available else "[dim]NOT CONFIGURED[/dim]",
        codex_health.version or "N/A",
        codex_health.binary_path or "N/A",
        codex_health.error_details or "Ready for code generation turns",
    )

    # Check piagent
    dummy_pi_cfg = AgentConfig(type="piagent", name="PiAgent")
    pi_adapter = AgentRegistry.create("piagent", dummy_pi_cfg, Path("."))
    pi_health = pi_adapter.health_check()

    table.add_row(
        "Pi Agent (piagent)",
        "[green]AVAILABLE[/green]" if pi_health.is_available else "[dim]NOT INSTALLED[/dim]",
        pi_health.version or "N/A",
        pi_health.binary_path or "N/A",
        pi_health.error_details or "Install via: npm install -g @piagent/platform",
    )

    # Check hermes
    dummy_hermes_cfg = AgentConfig(type="hermes", name="Hermes Agent")
    hermes_adapter = AgentRegistry.create("hermes", dummy_hermes_cfg, Path("."))
    hermes_health = hermes_adapter.health_check()

    table.add_row(
        "Nous Hermes (hermes)",
        "[green]AVAILABLE[/green]" if hermes_health.is_available else "[dim]NOT INSTALLED[/dim]",
        hermes_health.version or "N/A",
        hermes_health.binary_path or "N/A",
        hermes_health.error_details or "Install Hermes CLI or pull model via Ollama",
    )

    # Check git
    from agent_orchestrator.workspace.git_tracker import GitTracker
    git_tracker = GitTracker(Path("."), enabled=True)
    git_avail = git_tracker.is_available()

    table.add_row(
        "Git Version Control",
        "[green]ACTIVE[/green]" if git_avail else "[yellow]NOT REPO[/yellow]",
        "Installed" if git_tracker._git_bin else "Missing",
        git_tracker._git_bin or "N/A",
        "Repository active" if git_avail else "Directory is not inside a git repo",
    )

    console.print()
    console.print(table)
    console.print()


@app.command()
def history(
    workspace_dir: Path = typer.Option(
        Path("workspace"), "--workspace", "-w", help="Workspace path to inspect"
    ),
):
    """Inspect previous debate rounds and saved snapshots."""
    rounds_dir = workspace_dir / "rounds"
    if not rounds_dir.exists():
        console.print(f"[yellow]No rounds directory found at {rounds_dir}[/yellow]")
        return

    snapshots = sorted(list(rounds_dir.glob("*.json")))
    if not snapshots:
        console.print(f"[yellow]No turn snapshots found in {rounds_dir}[/yellow]")
        return

    table = Table(title=f"Debate History: {workspace_dir}", border_style="bright_blue")
    table.add_column("File", style="cyan")
    table.add_column("Size", style="white")

    for s in snapshots:
        table.add_row(s.name, f"{s.stat().st_size} bytes")

    console.print()
    console.print(table)
    console.print()


if __name__ == "__main__":
    app()
