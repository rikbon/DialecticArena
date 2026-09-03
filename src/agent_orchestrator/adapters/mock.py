"""
Mock agent adapter for fast offline testing, CI/CD, and dry runs.
Simulates philosophical arguments and mental shifts without external CLI calls.
"""

import time
from typing import Optional

from agent_orchestrator.adapters.base import AgentRegistry, BaseAgentAdapter
from agent_orchestrator.types import HealthCheckResult, TurnContext, TurnResult


@AgentRegistry.register("mock")
@AgentRegistry.register("simulator")
class MockAgentAdapter(BaseAgentAdapter):
    """Simulated agent adapter producing scripted or contextual responses."""

    def health_check(self) -> HealthCheckResult:
        """Mock adapter is always available."""
        return HealthCheckResult(
            is_available=True,
            version="mock-1.0.0",
            binary_path="in-memory-mock",
        )

    def execute_turn(self, context: TurnContext) -> TurnResult:
        """Generate a simulated dialectic response."""
        start_time = time.time()

        r = context.round_num
        is_alfa = "alfa" in self.agent_id.lower() or "claude" in self.agent_id.lower()

        if is_alfa:
            arg = (
                f"[Round {r} Dialectic Analysis by {self.name}]\n"
                f"The premise asserted by {context.opponent_name} relies on an ontological reification of systemic emergence. "
                "While emergence is a valid descriptive heuristic in complex non-linear dynamics, "
                "it does not confer causal autonomy over the fundamental physical substrate. "
                "Any macro-state $M$ is strictly supervenient upon micro-state configuration $S$. "
                "Without a formal account of downward causation that violates conservation laws, "
                "holistic claims remain epiphenomenal metaphors rather than explanatory primitives."
            )
            onto = (
                f"Proposition {r}.1: Supervenience Axiom: No macroscopic psychological state can vary without a variation in underlying physical substrate.\n"
                f"Proposition {r}.2: Epistemic Boundary: Holism is an operational compression, not an ontological ground."
            )
            evo = (
                f"Acknowledged {context.opponent_name}'s emphasis on dynamic constraint fields; "
                "refining my framework to distinguish between strong emergence (rejected) and weak computational incompressibility (accepted)."
            )
        else:
            arg = (
                f"[Round {r} Phenomenological Critique by {self.name}]\n"
                f"{context.opponent_name}'s reductionism commits the mereological fallacy by conflating constituent parts with relational integrity. "
                "A formal system cannot validate its own semantic grounding purely from internal axiomatic syntax (as demonstrated by Gödel). "
                "Consciousness and observer-relative measurement cannot be dismissed as epiphenomena when they constitute the very epistemic aperture "
                "through which empirical physicalism is formulated. The observer is not outside the equation; it is the boundary condition."
            )
            onto = (
                f"Proposition {r}.3: Relational Ontic Thesis: Reality consists of relational networks whose properties are non-factorable into isolated constituents.\n"
                f"Proposition {r}.4: Phenomenological Invariance: First-person subjectivity is the primitive datum of all empirical verification."
            )
            evo = (
                f"Recognized {context.opponent_name}'s valid critique regarding vague metaphors; "
                "shifting defense toward formal category theory and thermodynamic constraints to ground systemic holism."
            )

        raw = (
            f"### ARGUMENT\n{arg}\n\n"
            f"### ONTOLOGY CONTRIBUTION\n{onto}\n\n"
            f"### INTERNAL EVOLUTION\n{evo}"
        )

        time.sleep(0.05)  # brief simulation delay
        elapsed = time.time() - start_time

        return TurnResult(
            agent_id=self.agent_id,
            agent_name=self.name,
            raw_output=raw,
            dialogue=arg,
            ontology_contribution=onto,
            internal_evolution=evo,
            execution_time_seconds=elapsed,
            exit_code=0,
            is_success=True,
        )
