"""
Ollama agent adapter for local and private open-weight LLMs.
Communicates with local Ollama service via HTTP API.
"""

import shutil
import subprocess
import time
from typing import Optional
import requests

from agent_orchestrator.adapters.base import AgentRegistry, BaseAgentAdapter
from agent_orchestrator.types import HealthCheckResult, TurnContext, TurnResult
from agent_orchestrator.workspace.parser import OutputParser


@AgentRegistry.register("ollama")
@AgentRegistry.register("local")
class OllamaAdapter(BaseAgentAdapter):
    """Adapter for local models via the Ollama server."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.host = self.config.env.get("OLLAMA_HOST", "http://localhost:11434")
        self.model = self.config.model or "gemma4:31b-cloud"

    def health_check(self) -> HealthCheckResult:
        """Verify that Ollama server is running and accessible."""
        bin_path = shutil.which("ollama")

        # First check if the HTTP API endpoint is reachable
        try:
            res = requests.get(f"{self.host}/api/tags", timeout=3)
            if res.status_code == 200:
                data = res.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                model_info = f"Models available: {', '.join(models) if models else 'none'}"
                return HealthCheckResult(
                    is_available=True,
                    version=f"Ollama API ({model_info})",
                    binary_path=bin_path or self.host,
                    error_details=f"Connected to {self.host} (target: {self.model})",
                )
        except Exception:
            pass

        # Fallback: check if the CLI binary exists
        if bin_path:
            try:
                cli_res = subprocess.run(
                    [bin_path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                if cli_res.returncode == 0:
                    return HealthCheckResult(
                        is_available=False,
                        version=cli_res.stdout.strip(),
                        binary_path=bin_path,
                        error_details=f"Ollama CLI is installed, but server at {self.host} is not running. Run 'ollama serve'.",
                    )
            except Exception:
                pass

        return HealthCheckResult(
            is_available=False,
            error_details=f"Ollama server not reachable at {self.host} and binary not found.",
        )

    def execute_turn(self, context: TurnContext) -> TurnResult:
        """Execute turn using local Ollama model."""
        prompt = self.build_prompt(context)
        start_time = time.time()

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
            },
        }

        try:
            url = f"{self.host}/api/generate"
            res = requests.post(url, json=payload, timeout=self.config.timeout_seconds)
            elapsed = time.time() - start_time

            if res.status_code != 200:
                err_msg = f"Ollama HTTP {res.status_code}: {res.text}"
                return TurnResult(
                    agent_id=self.agent_id,
                    agent_name=self.name,
                    raw_output="",
                    dialogue=f"[{err_msg}]",
                    ontology_contribution="",
                    internal_evolution="",
                    turn_num=context.turn_num,
                    step_num=context.step_num,
                    step_label=context.step_label,
                    execution_time_seconds=elapsed,
                    exit_code=res.status_code,
                    error_message=err_msg,
                    is_success=False,
                )

            data = res.json()
            raw_output = data.get("response", "").strip()

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

        except requests.exceptions.Timeout:
            elapsed = time.time() - start_time
            msg = f"Ollama request timed out after {self.config.timeout_seconds}s"
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
                dialogue=f"[Unexpected error communicating with Ollama: {e}]",
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
