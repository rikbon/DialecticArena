"""
Tests for CLI commands.
"""

from typer.testing import CliRunner
from agent_orchestrator.cli import app

runner = CliRunner()


def test_cli_verify():
    result = runner.invoke(app, ["verify"])
    assert result.exit_code == 0
    assert "Antigravity" in result.stdout
    assert "Claude" in result.stdout


def test_cli_run_mock_dry_run(tmp_path):
    ws_dir = tmp_path / "mock_test_workspace"
    result = runner.invoke(
        app,
        [
            "run",
            "--mock",
            "--rounds", "1",
            "--workspace", str(ws_dir),
            "--no-git",
        ],
    )
    assert result.exit_code == 0
    assert "DIALECTIC ARENA" in result.stdout
    assert (ws_dir / "arena_manifesto.md").exists()
    assert (ws_dir / "memory_claude.md").exists()
    assert (ws_dir / "memory_antigravity.md").exists()
