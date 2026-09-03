# 🔌 How to Add New Agent Adapters

This guide walks you through extending **Dialectic Arena** to support additional agentic coding CLIs or LLM engines (e.g., Aider, OpenHands, Ollama, Gemini SDK, OpenAI API, etc.).

---

## 1. The Adapter Architecture

All agents implement the `BaseAgentAdapter` abstract class located in `src/agent_orchestrator/adapters/base.py`:

```python
class BaseAgentAdapter(ABC):
    @abstractmethod
    def health_check(self) -> HealthCheckResult:
        """Verify that the tool binary or API service is available."""
        pass

    @abstractmethod
    def execute_turn(self, context: TurnContext) -> TurnResult:
        """Execute a single dialectic turn using the agent."""
        pass
```

### The Registry Pattern
New adapters register themselves using the `@AgentRegistry.register("type_name")` decorator. Once decorated, any configuration file can reference the adapter via `type: "type_name"`.

---

## 2. Example 1: Creating an Aider CLI Adapter

[Aider](https://aider.chat/) is a popular terminal-based AI pair programming tool.

Create `src/agent_orchestrator/adapters/aider.py`:

```python
import os
import shutil
import subprocess
import time
from agent_orchestrator.adapters.base import AgentRegistry, BaseAgentAdapter
from agent_orchestrator.types import HealthCheckResult, TurnContext, TurnResult
from agent_orchestrator.workspace.parser import OutputParser


@AgentRegistry.register("aider")
class AiderAdapter(BaseAgentAdapter):
    """Adapter for the Aider CLI coding assistant."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._binary = shutil.which("aider") or "aider"

    def health_check(self) -> HealthCheckResult:
        bin_path = shutil.which("aider")
        if not bin_path:
            return HealthCheckResult(
                is_available=False,
                error_details="Executable 'aider' not found in system PATH.",
            )
        try:
            res = subprocess.run([bin_path, "--version"], capture_output=True, text=True, timeout=5)
            return HealthCheckResult(
                is_available=res.returncode == 0,
                version=res.stdout.strip(),
                binary_path=bin_path,
            )
        except Exception as e:
            return HealthCheckResult(is_available=False, error_details=str(e))

    def execute_turn(self, context: TurnContext) -> TurnResult:
        prompt = self.build_prompt(context)
        start_time = time.time()

        # Run aider non-interactively with --message and skip git commits (orchestrator handles git)
        cmd = [
            self._binary,
            "--message", prompt,
            "--no-auto-commits",
            "--yes",
        ]

        if self.config.model:
            cmd.extend(["--model", self.config.model])

        try:
            res = subprocess.run(
                cmd,
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                timeout=self.config.timeout_seconds,
            )
            elapsed = time.time() - start_time
            parsed = OutputParser.parse(res.stdout)

            return TurnResult(
                agent_id=self.agent_id,
                agent_name=self.name,
                raw_output=res.stdout,
                dialogue=parsed.dialogue,
                ontology_contribution=parsed.ontology_contribution,
                internal_evolution=parsed.internal_evolution,
                turn_num=context.turn_num,
                step_num=context.step_num,
                step_label=context.step_label,
                execution_time_seconds=elapsed,
                exit_code=res.returncode,
                is_success=res.returncode == 0,
            )
        except Exception as e:
            return TurnResult(
                agent_id=self.agent_id,
                agent_name=self.name,
                raw_output="",
                dialogue=f"[Error executing Aider: {e}]",
                ontology_contribution="",
                internal_evolution="",
                turn_num=context.turn_num,
                step_num=context.step_num,
                step_label=context.step_label,
                execution_time_seconds=time.time() - start_time,
                exit_code=1,
                error_message=str(e),
                is_success=False,
            )
```

Export it in `src/agent_orchestrator/adapters/__init__.py`:
```python
from agent_orchestrator.adapters.aider import AiderAdapter
```

---

## 3. Example 2: Creating a Local Ollama Model Adapter

For 100% offline, private debates using open weights (e.g. Llama 3, DeepSeek, Qwen).

Create `src/agent_orchestrator/adapters/ollama_adapter.py`:

```python
import time
import requests
from agent_orchestrator.adapters.base import AgentRegistry, BaseAgentAdapter
from agent_orchestrator.types import HealthCheckResult, TurnContext, TurnResult
from agent_orchestrator.workspace.parser import OutputParser


@AgentRegistry.register("ollama")
class OllamaAdapter(BaseAgentAdapter):
    """Adapter for local models via the Ollama HTTP API."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.host = self.config.env.get("OLLAMA_HOST", "http://localhost:11434")
        self.model = self.config.model or "llama3.3:latest"

    def health_check(self) -> HealthCheckResult:
        try:
            res = requests.get(f"{self.host}/api/tags", timeout=3)
            return HealthCheckResult(
                is_available=res.status_code == 200,
                version=f"Ollama API ({self.model})",
                binary_path=self.host,
            )
        except Exception as e:
            return HealthCheckResult(is_available=False, error_details=str(e))

    def execute_turn(self, context: TurnContext) -> TurnResult:
        prompt = self.build_prompt(context)
        start_time = time.time()

        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            }
            res = requests.post(f"{self.host}/api/generate", json=payload, timeout=self.config.timeout_seconds)
            res.raise_for_status()
            data = res.json()
            raw_text = data.get("response", "")

            elapsed = time.time() - start_time
            parsed = OutputParser.parse(raw_text)

            return TurnResult(
                agent_id=self.agent_id,
                agent_name=self.name,
                raw_output=raw_text,
                dialogue=parsed.dialogue,
                ontology_contribution=parsed.ontology_contribution,
                internal_evolution=parsed.internal_evolution,
                turn_num=context.turn_num,
                step_num=context.step_num,
                step_label=context.step_label,
                execution_time_seconds=elapsed,
                is_success=True,
            )
        except Exception as e:
            return TurnResult(
                agent_id=self.agent_id,
                agent_name=self.name,
                raw_output="",
                dialogue=f"[Ollama Error: {e}]",
                ontology_contribution="",
                internal_evolution="",
                turn_num=context.turn_num,
                step_num=context.step_num,
                step_label=context.step_label,
                execution_time_seconds=time.time() - start_time,
                is_success=False,
                error_message=str(e),
            )
```

---

## 4. Testing Your New Adapter

Add a unit test in `tests/test_adapters.py`:

```python
def test_custom_adapter_discovery():
    assert "aider" in AgentRegistry.get_registered_types()
```

Run tests:
```bash
pytest tests/ -v
```

Now you can configure your new agent in any YAML file:
```yaml
agents:
  my_local_agent:
    type: "ollama"
    name: "DeepSeek Reasoner"
    model: "deepseek-r1:32b"
    role: "Formal Logician"
```
