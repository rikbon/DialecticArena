"""
PiAgent CLI adapter.
Integrates the Pi Agent minimalist autonomous coding harness.
"""

import os
import shutil
import subprocess
import time
from typing import Optional

from agent_orchestrator.adapters.base import AgentRegistry, BaseAgentAdapter
from agent_orchestrator.types import HealthCheckResult, TurnContext, TurnResult
from agent_orchestrator.workspace.parser import OutputParser


@AgentRegistry.register("piagent")
@AgentRegistry.register("pi")
class PiAgentAdapter(BaseAgentAdapter):
    """Adapter for the Pi Agent terminal coding platform."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._binary = shutil.which("piagent") or shutil.which("pi")

    def health_check(self) -> HealthCheckResult:
        """Verify that piagent or pi CLI binary is accessible."""
        bin_path = shutil.which("piagent") or shutil.which("pi")
        if not bin_path:
            return HealthCheckResult(
                is_available=False,
                error_details=(
                    "Executable 'piagent' not found in system PATH. "
                    "Install via: npm install -g @piagent/platform"
                ),
            )

        try:
            res = subprocess.run(
                [bin_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if res.returncode == 0:
                return HealthCheckResult(
                    is_available=True,
                    version=res.stdout.strip() or "PiAgent CLI",
                    binary_path=bin_path,
                    error_details="Ready for autonomous terminal execution",
                )
            return HealthCheckResult(
                is_available=False,
                binary_path=bin_path,
                error_details=f"'piagent --version' returned exit code {res.returncode}",
            )
        except Exception as e:
            return HealthCheckResult(
                is_available=False,
                binary_path=bin_path,
                error_details=str(e),
            )

    def execute_turn(self, context: TurnContext) -> TurnResult:
        """Execute turn using PiAgent CLI."""
        prompt = self.build_prompt(context)
        bin_path = shutil.which("piagent") or shutil.which("pi") or "piagent"
        start_time = time.time()

        # Build non-interactive batch command
        cmd = [
            bin_path,
            "run",
            "--prompt", prompt,
            "--headless",
            "--no-interactive",
        ]

        if self.config.model:
            cmd.extend(["--model", self.config.model])

        if self.config.extra_args:
            cmd.extend(self.config.extra_args)

        env = os.environ.copy()
        if self.config.env:
            env.update(self.config.env)

        try:
            res = subprocess.run(
                cmd,
                cwd=self.workspace_dir,
                env=env,
                capture_output=True,
                text=True,
                timeout=self.config.timeout_seconds,
                check=False,
            )
            elapsed = time.time() - start_time
            raw_output = res.stdout.strip()

            if res.returncode != 0:
                err_msg = res.stderr.strip() or f"PiAgent exited with code {res.returncode}"
                return TurnResult(
                    agent_id=self.agent_id,
                    agent_name=self.name,
                    raw_output=raw_output,
                    dialogue=raw_output or f"[PiAgent error: {err_msg}]",
                    ontology_contribution="",
                    internal_evolution="",
                    turn_num=context.turn_num,
                    step_num=context.step_num,
                    step_label=context.step_label,
                    execution_time_seconds=elapsed,
                    exit_code=res.returncode,
                    error_message=err_msg,
                    is_success=False,
                )

            parsed = OutputParser.parse(raw_output)
            return TurnResult(
                agent_id=self.agent_id,
                agent_name=self.name,
                raw_output=raw_output,
                dialogue=parsed.dialogue,
                ontology_contribution=parsed.ontology_contribution,
                internal_evolution=parsed.internal_evolution,
                turn_num=context.turn_num,
                step_num=context.step_num,
                step_label=context.step_label,
                execution_time_seconds=elapsed,
                exit_code=0,
                is_success=True,
            )

        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            msg = f"PiAgent timed out after {self.config.timeout_seconds} seconds"
            return TurnResult(
                agent_id=self.agent_id,
                agent_name=self.name,
                raw_output="",
                dialogue=f"[{msg}]",
                ontology_contribution="",
                internal_evolution="",
                turn_num=context.turn_num,
                step_num=context.step_num,
                step_label=context.step_label,
                execution_time_seconds=elapsed,
                exit_code=124,
                error_message=msg,
                is_success=False,
            )
        except Exception as e:
            elapsed = time.time() - start_time
            return TurnResult(
                agent_id=self.agent_id,
                agent_name=self.name,
                raw_output="",
                dialogue=f"[Unexpected error running PiAgent: {e}]",
                ontology_contribution="",
                internal_evolution="",
                turn_num=context.turn_num,
                step_num=context.step_num,
                step_label=context.step_label,
                execution_time_seconds=elapsed,
                exit_code=1,
                error_message=str(e),
                is_success=False,
            )
