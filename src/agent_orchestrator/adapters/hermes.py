"""
Nous Research Hermes Agent adapter.
Supports Nous Research Hermes CLI and Hermes open-weight model endpoints.
"""

import os
import shutil
import subprocess
import time
from typing import Optional
import requests

from agent_orchestrator.adapters.base import AgentRegistry, BaseAgentAdapter
from agent_orchestrator.types import HealthCheckResult, TurnContext, TurnResult
from agent_orchestrator.workspace.parser import OutputParser


@AgentRegistry.register("hermes")
@AgentRegistry.register("hermes-agent")
@AgentRegistry.register("nous-hermes")
class HermesAdapter(BaseAgentAdapter):
    """Adapter for Nous Research Hermes Agent CLI or Hermes model runtime."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._binary = shutil.which("hermes")
        self.model = self.config.model or "hermes3:8b"
        self.ollama_host = self.config.env.get("OLLAMA_HOST", "http://localhost:11434")

    def health_check(self) -> HealthCheckResult:
        """Verify availability of Hermes CLI or local Ollama Hermes model."""
        bin_path = shutil.which("hermes")
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
                        version=res.stdout.strip() or "Hermes Agent CLI",
                        binary_path=bin_path,
                        error_details="Ready for autonomous CLI execution",
                    )
            except Exception:
                pass

        # Check local Ollama for Hermes model
        try:
            res = requests.get(f"{self.ollama_host}/api/tags", timeout=2)
            if res.status_code == 200:
                data = res.json()
                models = [m.get("name", "").lower() for m in data.get("models", [])]
                hermes_models = [m for m in models if "hermes" in m]
                if hermes_models:
                    return HealthCheckResult(
                        is_available=True,
                        version=f"Hermes via Ollama ({hermes_models[0]})",
                        binary_path=f"{self.ollama_host}/api/generate",
                        error_details="Connected to local Ollama Hermes model",
                    )
        except Exception:
            pass

        # Check OpenRouter / Nous API key
        if os.environ.get("OPENROUTER_API_KEY") or os.environ.get("NOUS_API_KEY"):
            return HealthCheckResult(
                is_available=True,
                version=f"Nous Hermes Cloud ({self.model})",
                binary_path="api://nousresearch",
                error_details="Configured via API key",
            )

        return HealthCheckResult(
            is_available=False,
            error_details=(
                "Executable 'hermes' not found and no local Ollama Hermes model detected. "
                "Install Hermes Agent CLI or pull a model via 'ollama pull hermes3'."
            ),
        )

    def execute_turn(self, context: TurnContext) -> TurnResult:
        """Execute turn using Hermes CLI or local/cloud model."""
        prompt = self.build_prompt(context)
        start_time = time.time()

        bin_path = shutil.which("hermes")

        # Mode A: Hermes CLI Subprocess
        if bin_path:
            cmd = [
                bin_path,
                "run",
                "--prompt", prompt,
                "--non-interactive",
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
                    err_msg = res.stderr.strip() or f"Hermes exited with code {res.returncode}"
                    return TurnResult(
                        agent_id=self.agent_id,
                        agent_name=self.name,
                        raw_output=raw_output,
                        dialogue=raw_output or f"[Hermes error: {err_msg}]",
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
                msg = f"Hermes timed out after {self.config.timeout_seconds} seconds"
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
                    dialogue=f"[Unexpected error executing Hermes CLI: {e}]",
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

        # Mode B: Ollama / LiteLLM API inference
        try:
            # Check Ollama first
            url = f"{self.ollama_host}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            }
            res = requests.post(url, json=payload, timeout=self.config.timeout_seconds)
            if res.status_code == 200:
                raw_output = res.json().get("response", "").strip()
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
        except Exception:
            pass

        # Fallback to LiteLLM
        try:
            import litellm

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
                dialogue=f"[Hermes execution failed: {e}]",
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
