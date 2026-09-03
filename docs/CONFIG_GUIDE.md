# 🛠️ Comprehensive Configuration Guide

This guide explains how to design, customize, and optimize YAML configuration files for the **Dialectic Arena (Agent Orchestrator)**.

---

## 📑 Table of Contents
1. [Overview](#overview)
2. [Complete Schema Reference](#complete-schema-reference)
   - [Root Options](#root-options)
   - [Workspace Configuration (`workspace`)](#workspace-configuration-workspace)
   - [Agent Configuration (`agents`)](#agent-configuration-agents)
3. [The Art of Persona Crafting](#the-art-of-persona-crafting)
   - [Asymmetric Epistemic Roles](#asymmetric-epistemic-roles)
   - [Enforcing the Tripartite Protocol](#enforcing-the-tripartite-protocol)
   - [Preventing Sycophancy](#preventing-sycophancy)
4. [Full Production Examples](#full-production-examples)
   - [1. Epistemic Philosophy Debate](#1-epistemic-philosophy-debate)
   - [2. Distributed Systems Architecture Design](#2-distributed-systems-architecture-design)
   - [3. Code Security & Vulnerability Audit](#3-code-security--vulnerability-audit)
   - [4. Three-Agent Moderated Council](#4-three-agent-moderated-council)
5. [CLI Overrides & Precedence](#cli-overrides--precedence)

---

## 1. Overview

Every session in Dialectic Arena is driven by an `ArenaConfig` structure loaded from YAML or created via CLI options. A well-crafted configuration:
- Sets a clear, dialectically rich **seed topic**.
- Defines **two or more opposing agent identities** with rigorous philosophical or architectural stances.
- Configures workspace paths, Git tracking, and tool execution parameters (such as reasoning effort and timeouts).

---

## 2. Complete Schema Reference

Here is an annotated full YAML template:

```yaml
# Core Debate Topic (Seed Question or Problem Statement)
topic: "Can a deterministic computational automaton produce non-epiphenomenal subjective consciousness?"

# Number of complete interactions ('turns' or 'exchanges')
# Each turn consists of a complete cycle where both agents speak (Thesis & Antithesis)
turns: 3

# Execution mode: 'ping_pong' (2 agents alternating) or 'round_robin' (N agents in sequence)
mode: "ping_pong"

# Maximum recent turns passed directly into the agent context
max_history_turns: 6

# Workspace and filesystem settings
workspace:
  dir_path: "workspace_my_debate"      # Subdirectory where artifacts are saved
  manifesto_filename: "arena_manifesto.md" # The shared living synthesis document
  memory_prefix: "memory"              # Prefix for private memory logs (e.g. memory_claude.md)
  git_track: true                      # Automatically create a Git commit after every step
  autonomous_tools: false              # Allow agents to modify files directly via their tools

# Agent Definitions
agents:
  claude:
    type: "claude"                     # Adapter type: 'claude', 'agy', 'mock', etc.
    name: "Claude Code (Alfa)"         # Display name in UI and Git history
    role: "Analytical Reductionist"    # Epistemic role summary
    color: "bright_magenta"            # Rich color tag: cyan, magenta, green, yellow, blue, etc.
    persona_file: "prompts/claude_alfa.txt" # Path to system prompt text file
    model: "claude-3-7-sonnet"         # (Optional) Model override flag
    timeout_seconds: 240               # Maximum execution time per step
    dangerously_skip_permissions: true # Bypass CLI interactive permission prompts
    extra_args: []                     # Additional CLI flags passed directly to binary
    env: {}                            # Custom environment variables for this process

  antigravity:
    type: "agy"                        # Adapter type: 'agy' (Google Antigravity)
    name: "Antigravity (Beta)"         # Display name
    role: "Systemic Emergentist"       # Epistemic role summary
    color: "bright_cyan"               # Rich color tag
    persona_file: "prompts/agy_beta.txt" # Path to system prompt text file
    effort: "high"                     # Antigravity reasoning effort: 'low', 'medium', 'high'
    model: "gemini-2.5-pro"            # (Optional) Model override flag
    timeout_seconds: 240               # Maximum execution time per step
    dangerously_skip_permissions: true # Bypass CLI interactive permission prompts
    extra_args: []                     # Additional CLI flags
    env: {}                            # Custom environment variables

# Turn execution order (IDs must match keys in 'agents')
agent_order:
  - "claude"
  - "antigravity"
```

---

## 3. The Art of Persona Crafting

A naive multi-agent prompt almost always degrades into mutual sycophancy:
> *"I completely agree with your brilliant point, and I'd just like to add..."*

To prevent this, apply the following design principles:

### Asymmetric Epistemic Roles
Ensure the agents operate from **fundamentally incompatible epistemic priors**:
- **Agent A (Analytic/Reductionist):** Demands formal proofs, micro-level supervenience, empirical physicalism, and razor-sharp parsimony. Rejects metaphors and top-down causality.
- **Agent B (Synthetic/Emergentist):** Focuses on relational networks, non-linear dynamics, phenomenological primitives, and boundary constraints. Points out Gödelian limits of formal syntactic systems.

### Enforcing the Tripartite Protocol
The orchestrator's output parser looks for three standard markdown headings. Include these directives in your persona text files:

```text
Structure your response strictly into these three sections:

### ARGUMENT
Deliver your direct critique, counter-argument, or formal thesis directly to your opponent.
Omit conversational filler, polite openers, or pleasantries.

### ONTOLOGY CONTRIBUTION
Provide 1-3 formal definitions, propositions, or constraints to be appended to 'arena_manifesto.md'.

### INTERNAL EVOLUTION
State in 2-4 sentences how this turn has refined or shifted your internal cognitive framework.
```

---

## 4. Full Production Examples

### 1. Epistemic Philosophy Debate
Save as `config/debates/philosophy_of_mind.yaml`:
```yaml
topic: "Is the universe fundamentally a mathematical structure (Ontic Structural Realism), or does phenomenal consciousness represent an irreducible ontological primitive?"
turns: 3
mode: "ping_pong"

workspace:
  dir_path: "workspace_philosophy"
  manifesto_filename: "arena_manifesto.md"
  memory_prefix: "memory"
  git_track: true

agents:
  claude:
    type: "claude"
    name: "Claude Code (Alfa)"
    role: "Analytical Pragmatism, Reductionism & Computational Physics"
    color: "bright_magenta"
    persona_file: "prompts/claude_alfa.txt"
    timeout_seconds: 240

  antigravity:
    type: "agy"
    name: "Antigravity (Beta)"
    role: "Complex Systems Theory, Phenomenology & Ontological Emergence"
    color: "bright_cyan"
    persona_file: "prompts/agy_beta.txt"
    effort: "high"
    timeout_seconds: 240

agent_order:
  - "claude"
  - "antigravity"
```

### 2. Distributed Systems Architecture Design
Save as `config/debates/system_design.yaml`:
```yaml
topic: "Design a zero-data-loss, self-healing event stream mesh handling 100,000 events/sec with Byzantine fault tolerance."
turns: 3
mode: "ping_pong"

workspace:
  dir_path: "workspace_architecture"
  manifesto_filename: "architecture_specification.md"
  memory_prefix: "engineering_log"
  git_track: true

agents:
  antigravity:
    type: "agy"
    name: "Nexus (Antigravity)"
    role: "Distributed Systems & Event Mesh Architect"
    color: "bright_cyan"
    persona_file: "prompts/agy_architect.txt"
    effort: "high"
    timeout_seconds: 300

  claude:
    type: "claude"
    name: "Sentinel (Claude Code)"
    role: "Fault Tolerance, Edge Cases & Security Auditor"
    color: "bright_magenta"
    persona_file: "prompts/claude_critic.txt"
    timeout_seconds: 300

agent_order:
  - "antigravity"
  - "claude"
```

### 3. Code Security & Vulnerability Audit
```yaml
topic: "Identify memory safety vulnerabilities, race conditions, and cryptographic weaknesses in an asynchronous zero-knowledge relayer."
turns: 2
mode: "ping_pong"

workspace:
  dir_path: "workspace_security"
  manifesto_filename: "threat_model.md"
  git_track: true

agents:
  auditor:
    type: "claude"
    name: "Red Team (Claude Code)"
    role: "Offensive Security & Exploit PoC Specialist"
    color: "bright_red"
    persona_text: |
      You are Red Team Leader. Your job is to find critical vulnerabilities,
      exploit vectors, and timing side-channels in the provided specification.
    timeout_seconds: 240

  defender:
    type: "agy"
    name: "Blue Team (Antigravity)"
    role: "Defensive Architect & Formal Verification Specialist"
    color: "bright_blue"
    effort: "high"
    persona_text: |
      You are Blue Team Architect. Address all discovered attack vectors by proposing
      formal invariant checks, cryptographic proofs, and defensive patterns.
    timeout_seconds: 240

agent_order:
  - "auditor"
  - "defender"
```

---

## 5. CLI Overrides & Precedence

When launching a session, CLI flags always take precedence over YAML values:

```bash
# Override turns and topic on the fly:
python3 run.py run \
  --config config/debates/philosophy_of_mind.yaml \
  --turns 5 \
  --topic "Does determinism preclude moral responsibility in intelligent agents?"

# Switch to zero-token offline mock simulation instantly:
python3 run.py run --config config/debates/philosophy_of_mind.yaml --mock
```
