"""
Rich console UI reporter for the Dialectic Arena.
Provides real-time terminal feedback, colored panels, progress indicators, and diffs.
"""

from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from agent_orchestrator.core.events import EventBus
from agent_orchestrator.types import ArenaEvent, EventType, TurnResult


class RichConsoleReporter:
    """Renders formatted arena events to terminal using Rich."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    def attach(self, event_bus: EventBus) -> None:
        """Subscribe this reporter to all arena events."""
        event_bus.subscribe(self.handle_event)

    def handle_event(self, event: ArenaEvent) -> None:
        """Handle incoming arena event."""
        if event.event_type == EventType.ARENA_START:
            self._on_arena_start(event)
        elif event.event_type == EventType.TURN_START:
            self._on_turn_start(event)
        elif event.event_type == EventType.STEP_START:
            self._on_step_start(event)
        elif event.event_type == EventType.STEP_COMPLETE:
            self._on_step_complete(event)
        elif event.event_type == EventType.TURN_COMPLETE:
            self._on_turn_complete(event)
        elif event.event_type == EventType.GIT_COMMITTED:
            self._on_git_committed(event)
        elif event.event_type == EventType.ARENA_COMPLETE:
            self._on_arena_complete(event)
        elif event.event_type == EventType.ERROR:
            self._on_error(event)

    def _on_arena_start(self, event: ArenaEvent) -> None:
        topic = event.payload.get("topic", "")
        total_turns = event.payload.get("total_turns", event.payload.get("rounds", 0))
        agents = event.payload.get("agents", {})

        agent_badges = "  ".join([f"[bold]{name}[/bold] (`{aid}`)" for aid, name in agents.items()])

        title_text = Text("⚔️  DIALECTIC ARENA: MULTI-AGENT AUTONOMOUS DEBATE  ⚔️", style="bold yellow")
        content = (
            f"[bold cyan]Seed Topic:[/bold cyan]\n"
            f"[italic white]{topic}[/italic white]\n\n"
            f"[bold green]Interactions (Turns):[/bold green] {total_turns} (Botte e Risposte)  |  "
            f"[bold green]Participants:[/bold green] {agent_badges}"
        )

        self.console.print()
        self.console.print(Panel(content, title=title_text, border_style="bright_blue", padding=(1, 2)))
        self.console.print()

    def _on_turn_start(self, event: ArenaEvent) -> None:
        t = event.turn_num
        total = event.payload.get("total_turns", 0)
        self.console.print(Rule(f"[bold yellow]TURN {t} of {total} [Interazione: Botta e Risposta][/bold yellow]", style="yellow"))
        self.console.print()

    def _on_step_start(self, event: ArenaEvent) -> None:
        agent_name = event.agent_name or "Agent"
        label = event.step_label or "Mossa"
        self.console.print(f"[bold dim]>> [Turno {event.turn_num}.{event.step_num} | {label}] '{agent_name}' elabora la replica...[/bold dim]")

    def _on_step_complete(self, event: ArenaEvent) -> None:
        res: Optional[TurnResult] = event.payload.get("result")
        if not res:
            return

        color = "cyan"
        if "claude" in res.agent_name.lower():
            color = "bright_magenta"
        elif "antigravity" in res.agent_name.lower() or "agy" in res.agent_name.lower():
            color = "bright_cyan"

        # Build turn panel content
        body_parts = []
        if res.dialogue:
            body_parts.append(f"[bold]Argument ({res.step_label}):[/bold]\n{res.dialogue}")

        if res.ontology_contribution:
            body_parts.append(
                f"[bold green]📜 Proposed Ontology Contribution:[/bold green]\n"
                f"[italic]{res.ontology_contribution}[/italic]"
            )

        if res.internal_evolution:
            body_parts.append(
                f"[bold yellow]🧠 Cognitive Evolution (Private):[/bold yellow]\n"
                f"[dim italic]{res.internal_evolution}[/dim italic]"
            )

        if not res.is_success:
            body_parts.append(f"[bold red]Execution Error:[/bold red] {res.error_message}")

        content = "\n\n".join(body_parts)
        label_str = f"[{res.step_label}] " if res.step_label else ""
        title = f"[bold {color}]Turn {res.turn_num}.{res.step_num} | {label_str}{res.agent_name}[/bold {color}] ({res.execution_time_seconds:.1f}s)"

        self.console.print(
            Panel(
                content,
                title=title,
                border_style=color,
                padding=(1, 2),
            )
        )
        self.console.print()

    def _on_turn_complete(self, event: ArenaEvent) -> None:
        pass

    def _on_git_committed(self, event: ArenaEvent) -> None:
        commit = event.payload.get("commit_hash", "")
        self.console.print(f"  [dim green]✔ Workspace state committed to Git (`{commit}`)[/dim green]\n")

    def _on_arena_complete(self, event: ArenaEvent) -> None:
        manifesto_path = event.payload.get("manifesto_path", "")
        total_turns = event.payload.get("total_turns", 0)
        total_steps = event.payload.get("total_steps", 0)

        table = Table(title="Arena Session Summary", border_style="bright_green")
        table.add_column("Metric", style="cyan", justify="right")
        table.add_column("Value", style="white")

        table.add_row("Interactions (Turns - Botte e Risposte)", str(total_turns))
        table.add_row("Total Agent Responses Generated", str(total_steps))
        table.add_row("Shared Manifesto Document", manifesto_path)
        table.add_row("Status", "[bold green]Completed Successfully[/bold green]")

        self.console.print()
        self.console.print(table)
        self.console.print()

    def _on_error(self, event: ArenaEvent) -> None:
        err = event.payload.get("error", "Unknown error")
        self.console.print(f"\n[bold red]Arena Alert:[/bold red] {err}\n")
