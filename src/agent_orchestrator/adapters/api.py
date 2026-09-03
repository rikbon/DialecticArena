"""
Direct API agent adapter using LiteLLM / OpenAI SDK.
Provides low-overhead API access when CLI binaries are not installed.
"""

import os
import time
from typing import Optional

from agent_orchestrator.adapters.base import AgentRegistry, BaseAgentAdapter
from agent_orchestrator.types import HealthCheckResult, TurnContext, TurnResult
from agent_orchestrator.workspace.parser import OutputParser


@AgentRegistry.register("api")
@AgentRegistry.register("litellm")
@AgentRegistry.register("openai")
class DirectApiAdapter(BaseAgentAdapter):
    """Direct API adapter for cloud model inference without CLI tools."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = self.config.model or "gpt-4o"

    def health_check(self) -> HealthCheckResult:
        """Verify that necessary API keys are present in the environment."""
        # Detect required key based on model prefix
        m = self.model.lower()
        if "gemini" in m:
            key_name = "GEMINI_API_KEY"
        elif "claude" in m or "anthropic" in m:
            key_name = "ANTHROPIC_API_KEY"
        else:
            key_name = "OPENAI_API_KEY"

        has_key = bool(os.environ.get(key_name) or self.config.env.get(key_name))
        if not has_key:
            return HealthCheckResult(
                is_available=False,
                error_details=f"Environment variable '{key_name}' is not set for model '{self.model}'",
            )

        return HealthCheckResult(
            is_available=True,
            version="Direct API (LiteLLM)",
            binary_path=f"api://{self.model}",
            error_details=f"Configured with {key_name}",
        )

    def execute_turn(self, context: TurnContext) -> TurnResult:
        """Call model API directly."""
        prompt = self.build_prompt(context)
        start_time = time.time()

        # Update environment if needed
        for k, v in self.config.env.items():
            os.environ[k] = v

        try:
            import litellm

            messages = [
                {"role": "user", "content": prompt}
            ]

            response = litellm.completion(
                model=self.model,
                messages=messages,
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
                dialogue=f"[API Error calling {self.model}: {e}]",
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
