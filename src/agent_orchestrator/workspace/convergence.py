"""
Dialectic convergence analyzer and ontology proposition classification engine.
Evaluates consensus, tracks proposition states (Accepted, Contested, Refuted),
and computes real-time alignment scores across turns.
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PropositionItem:
    identifier: str
    statement: str
    author: str
    status: str  # "Accepted", "Contested", "Refuted"
    notes: str = ""


@dataclass
class ConvergenceReport:
    total_propositions: int = 0
    accepted_count: int = 0
    contested_count: int = 0
    refuted_count: int = 0
    convergence_score: float = 0.0  # 0.0 to 100.0%
    status_label: str = "Divergent"
    propositions: list[PropositionItem] = field(default_factory=list)

    def format_summary(self) -> str:
        """Format a human-readable text summary."""
        return (
            f"Convergence Score: {self.convergence_score:.1f}% [{self.status_label}] | "
            f"Accepted: {self.accepted_count}, Contested: {self.contested_count}, Refuted: {self.refuted_count} "
            f"(Total: {self.total_propositions})"
        )


class ConvergenceAnalyzer:
    """Analyzes shared manifesto documents to extract and classify propositions."""

    # Keywords signaling acceptance or consensus
    ACCEPTED_KEYWORDS = [
        "accept", "agree", "concede", "consensus", "shared axiom",
        "synthesized", "converged", "mutually valid", "common ground",
        "incorporated", "jointly held"
    ]

    # Keywords signaling explicit refutation or abandonment
    REFUTED_KEYWORDS = [
        "refute", "reject", "fallacy", "mereological fallacy", "unsustainable",
        "retract", "abandon", "disproven", "falsified", "invalidated",
        "epiphenomenal illusion"
    ]

    # Keywords signaling ongoing contestation
    CONTESTED_KEYWORDS = [
        "contest", "dispute", "challenge", "counter", "tension",
        "objection", "irreconcilable", "divergence", "unresolved"
    ]

    @classmethod
    def analyze(
        cls,
        manifesto_text: str,
        dialogue_history: Optional[list[str]] = None,
    ) -> ConvergenceReport:
        """Analyze manifesto text and optional dialogue history to classify propositions."""
        propositions = cls._extract_propositions(manifesto_text)
        combined_dialogue = " ".join(dialogue_history or []).lower()

        accepted_count = 0
        contested_count = 0
        refuted_count = 0

        dialogues = dialogue_history or []

        for prop in propositions:
            status = cls._determine_status(prop, manifesto_text.lower(), dialogues)
            prop.status = status
            if status == "Accepted":
                accepted_count += 1
            elif status == "Refuted":
                refuted_count += 1
            else:
                contested_count += 1

        total = len(propositions)
        if total > 0:
            # Accepted propositions provide full alignment;
            # mutually refuted propositions provide negative consensus (agreement on what is false)
            score = ((accepted_count * 1.0) + (refuted_count * 0.6)) / total * 100.0
            score = round(min(100.0, max(0.0, score)), 1)
        else:
            score = 0.0

        if score >= 75.0:
            label = "High Convergence"
        elif score >= 45.0:
            label = "Dialectically Progressing"
        elif score > 0.0:
            label = "Emerging Consensus"
        else:
            label = "Divergent"

        return ConvergenceReport(
            total_propositions=total,
            accepted_count=accepted_count,
            contested_count=contested_count,
            refuted_count=refuted_count,
            convergence_score=score,
            status_label=label,
            propositions=propositions,
        )

    @classmethod
    def _extract_propositions(cls, text: str) -> list[PropositionItem]:
        """Extract proposition statements from markdown headings and lists."""
        items: list[PropositionItem] = []
        current_author = "Unknown"

        # Regex for Turn header
        author_pattern = re.compile(r"###\s+Turn\s+\d+.*?—\s*\[(.*?)\]", re.IGNORECASE)

        # Regex for Proposition lines
        prop_pattern = re.compile(
            r"(?:^|\n)(?:[-*]\s+|\s*)(Proposition\s+[\d.]+|Axiom\s+[\d.]+|Theorem\s+[\d.]+|Claim\s+[\d.]+):\s*(.*?)(?=\n\n|\n[-*]|\nProposition|\n###|$)",
            re.IGNORECASE | re.DOTALL,
        )

        lines = text.splitlines()
        for idx, line in enumerate(lines):
            author_match = author_pattern.search(line)
            if author_match:
                current_author = author_match.group(1).strip()

        for match in prop_pattern.finditer(text):
            ident = match.group(1).strip()
            statement = match.group(2).strip().replace("\n", " ")
            # Truncate overly long blocks
            if len(statement) > 250:
                statement = statement[:247] + "..."

            if ident and statement:
                items.append(
                    PropositionItem(
                        identifier=ident,
                        statement=statement,
                        author=current_author,
                        status="Contested",
                    )
                )

        # Fallback: if no formal "Proposition X" markers found, look for bullet points under contributions
        if not items:
            bullet_pattern = re.compile(r"^[*-]\s+(.+)$", re.MULTILINE)
            for idx, match in enumerate(bullet_pattern.finditer(text), start=1):
                stmt = match.group(1).strip()
                if len(stmt) > 20 and not stmt.startswith("http"):
                    items.append(
                        PropositionItem(
                            identifier=f"Thesis {idx}",
                            statement=stmt[:200],
                            author=current_author,
                            status="Contested",
                        )
                    )

        return items

    @classmethod
    def _determine_status(
        cls,
        prop: PropositionItem,
        manifesto_lower: str,
        dialogues: list[str],
    ) -> str:
        """Classify a proposition as Accepted, Refuted, or Contested using sentence-level evaluation."""
        ident_clean = prop.identifier.lower()
        common_words = {"proposition", "axiom", "thesis", "claim", "theorem", "state", "states", "structure"}
        stmt_keywords = [
            w for w in re.findall(r"\b[a-z]{5,}\b", prop.statement.lower())
            if w not in common_words
        ][:3]

        # Break dialogues into individual sentences, ignoring decimal dots like '1.2'
        sentences = []
        for text in dialogues:
            chunks = re.split(r"(?<!\d)\.(?!\d)|[!?\n]+", text.lower())
            sentences.extend([c.strip() for c in chunks if c.strip()])

        # Find sentences addressing this proposition specifically
        matching_sentences = []
        for sent in sentences:
            if ident_clean in sent:
                matching_sentences.append(sent)
            elif stmt_keywords and any(kw in sent for kw in stmt_keywords):
                matching_sentences.append(sent)

        # Evaluate matched sentences
        is_refuted = False
        is_accepted = False

        for sent in matching_sentences:
            has_refute = any(ref in sent for ref in cls.REFUTED_KEYWORDS)
            has_accept = any(acc in sent for acc in cls.ACCEPTED_KEYWORDS)

            if has_refute and not has_accept:
                is_refuted = True
            elif has_accept and not has_refute:
                is_accepted = True
            elif has_accept and has_refute:
                is_accepted = True

        if is_accepted and not is_refuted:
            return "Accepted"
        if is_refuted:
            return "Refuted"

        # Check for moderation synthesis keywords in manifesto itself
        if "synthesis" in manifesto_lower and any(kw in manifesto_lower for kw in stmt_keywords):
            return "Accepted"

        return "Contested"

    @classmethod
    def generate_markdown_section(cls, report: ConvergenceReport) -> str:
        """Generate a formatted markdown section to be appended to the manifesto."""
        bar_filled = int(report.convergence_score / 5)
        progress_bar = f"[{'=' * bar_filled}{' ' * (20 - bar_filled)}] {report.convergence_score:.1f}%"

        lines = [
            "## Dialectic Convergence Status",
            "",
            f"**Alignment Score:** `{progress_bar}` ({report.status_label})  ",
            f"**Consensus Breakdown:** {report.accepted_count} Accepted | {report.contested_count} Contested | {report.refuted_count} Refuted (Total Propositions: {report.total_propositions})",
            "",
            "| Identifier | Author | Status | Statement |",
            "| :--- | :--- | :--- | :--- |",
        ]

        if not report.propositions:
            lines.append("| (None) | — | — | No formal propositions indexed yet. |")
        else:
            for p in report.propositions:
                clean_stmt = p.statement.replace("|", "\\|")
                lines.append(f"| {p.identifier} | {p.author} | **{p.status}** | {clean_stmt} |")

        lines.append("")
        return "\n".join(lines)
