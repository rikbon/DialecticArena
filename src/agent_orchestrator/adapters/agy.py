"""
Antigravity CLI (agy) agent adapter.
Invokes Google Antigravity in headless print mode with permission controls.
"""

import os
import shutil
import subprocess
import time
from typing import Optional

from agent_orchestrator.adapters.base import AgentRegistry, BaseAgentAdapter
from agent_orchestrator.types import HealthCheckResult, TurnContext, TurnResult
from agent_orchestrator.workspace.parser import OutputParser


@AgentRegistry.register("agy")
@AgentRegistry.register("antigravity")
class AntigravityAdapter(BaseAgentAdapter):
    """Adapter for Google Antigravity CLI (agy)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._binary = shutil.which("agy") or "agy"

    def health_check(self) -> HealthCheckResult:
        """Check if agy binary exists and reports a version."""
        bin_path = shutil.which("agy")
        if not bin_path:
            return HealthCheckResult(
                is_available=False,
                error_details="Executable 'agy' was not found in system PATH.",
            )

        try:
            res = subprocess.run(
                [bin_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if res.returncode == 0:
                version = res.stdout.strip()
                return HealthCheckResult(
                    is_available=True,
                    version=version,
                    binary_path=bin_path,
                )
            return HealthCheckResult(
                is_available=False,
                binary_path=bin_path,
                error_details=f"'agy --version' exited with code {res.returncode}: {res.stderr.strip()}",
            )
        except Exception as e:
            return HealthCheckResult(
                is_available=False,
                binary_path=bin_path,
                error_details=str(e),
            )

    def execute_turn(self, context: TurnContext) -> TurnResult:
        """Run Antigravity CLI for a turn."""
        prompt = self.build_prompt(context)

        cmd = [self._binary, "-p", prompt]

        if self.config.dangerously_skip_permissions:
            cmd.append("--dangerously-skip-permissions")

        if self.config.effort:
            cmd.extend(["--effort", str(self.config.effort).lower()])

        if self.config.model:
            cmd.extend(["--model", self.config.model])

        if self.config.extra_args:
            cmd.extend(self.config.extra_args)

        env = os.environ.copy()
        if self.config.env:
            env.update(self.config.env)

        start_time = time.time()
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
                error_msg = res.stderr.strip() or f"Process exited with code {res.returncode}"
                return TurnResult(
                    agent_id=self.agent_id,
                    agent_name=self.name,
                    raw_output=raw_output,
                    dialogue=raw_output or f"[Error in Antigravity execution: {error_msg}]",
                    ontology_contribution="",
                    internal_evolution="",
                    execution_time_seconds=elapsed,
                    exit_code=res.returncode,
                    error_message=error_msg,
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
                execution_time_seconds=elapsed,
                exit_code=0,
                is_success=True,
            )

        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            msg = f"Antigravity timed out after {self.config.timeout_seconds} seconds"
            return TurnResult(
                agent_id=self.agent_id,
                agent_name=self.name,
                raw_output="",
                dialogue=f"[{msg}]",
                ontology_contribution="",
                internal_evolution="",
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
                dialogue=f"[Unexpected error running Antigravity: {e}]",
                ontology_contribution="",
                internal_evolution="",
                execution_time_seconds=elapsed,
                exit_code=1,
                error_message=str(e),
                is_success=False,
            )
