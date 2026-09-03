"""
OpenAI Codex agent adapter.
Supports both local CLI binary ('codex') and direct API inference via OpenAI / LiteLLM.
"""

import os
import shutil
import subprocess
import time
from typing import Optional

from agent_orchestrator.adapters.base import AgentRegistry, BaseAgentAdapter
from agent_orchestrator.types import HealthCheckResult, TurnContext, TurnResult
from agent_orchestrator.workspace.parser import OutputParser


@AgentRegistry.register("codex")
@AgentRegistry.register("openai-codex")
class CodexAdapter(BaseAgentAdapter):
    """Adapter for OpenAI Codex CLI or API-driven code generation."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._binary = shutil.which("codex") or shutil.which("openai-codex")
        self.model = self.config.model or "gpt-4o"

    def health_check(self) -> HealthCheckResult:
        """Verify availability of either the 'codex' CLI binary or OpenAI API access."""
        bin_path = shutil.which("codex") or shutil.which("openai-codex")
        if bin_path:
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
                        version=res.stdout.strip() or "Codex CLI",
                        binary_path=bin_path,
                        error_details="Ready for headless CLI execution",
                    )
            except Exception:
                pass

        # Fallback to OpenAI API key in environment
        api_key = os.environ.get("OPENAI_API_KEY") or self.config.env.get("OPENAI_API_KEY")
        if api_key:
            return HealthCheckResult(
                is_available=True,
                version=f"OpenAI Codex API ({self.model})",
                binary_path=f"api://{self.model}",
                error_details="Configured via OPENAI_API_KEY",
            )

        return HealthCheckResult(
            is_available=False,
            error_details=(
                "Executable 'codex' not found in PATH and OPENAI_API_KEY is not set. "
                "Set OPENAI_API_KEY or install the codex CLI."
            ),
        )

    def execute_turn(self, context: TurnContext) -> TurnResult:
        """Execute dialectic turn using Codex CLI or direct API fallback."""
        prompt = self.build_prompt(context)
        start_time = time.time()

        bin_path = shutil.which("codex") or shutil.which("openai-codex")

        # Option A: Execute via CLI binary if available
        if bin_path:
            cmd = [bin_path, "exec", "--prompt", prompt]
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
                    err_msg = res.stderr.strip() or f"Codex CLI exited with code {res.returncode}"
                    return TurnResult(
                        agent_id=self.agent_id,
                        agent_name=self.name,
                        raw_output=raw_output,
                        dialogue=raw_output or f"[Error running Codex CLI: {err_msg}]",
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
                msg = f"Codex CLI timed out after {self.config.timeout_seconds} seconds"
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
                    dialogue=f"[Error executing Codex: {e}]",
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

        # Option B: Fallback to direct LiteLLM / OpenAI API call
        try:
            import litellm

            for k, v in self.config.env.items():
                os.environ[k] = v

            response = litellm.completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                timeout=self.config.timeout_seconds,
            )
            raw_output = response.choices[0].message.content or ""
            elapsed = time.time() - start_time
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
        except Exception as e:
            elapsed = time.time() - start_time
            return TurnResult(
                agent_id=self.agent_id,
                agent_name=self.name,
                raw_output="",
                dialogue=f"[Codex API execution failed: {e}]",
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
