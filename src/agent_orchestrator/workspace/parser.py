"""
Output parser for agent responses.
Extracts public dialogue, ontology contributions, and internal evolution logs
using resilient regex pattern matching and intelligent fallbacks.
"""

import re
from dataclasses import dataclass


@dataclass
class ParsedTurnOutput:
    dialogue: str
    ontology_contribution: str
    internal_evolution: str


class OutputParser:
    """Parses structured markdown output from agents."""

    ARGUMENT_PATTERNS = [
        r"###\s*(?:ARGUMENT|DIALOGUE|DIBATTITO|REPLICA|TESI|COUNTER-ARGUMENT)[\s:]*\n?(.*?)(?=(?:###\s*(?:ONTOLOGY|MANIFESTO|EVOLUZIONE|INTERNAL)|$))",
        r"##\s*(?:ARGUMENT|DIALOGUE|DIBATTITO|REPLICA|TESI|COUNTER-ARGUMENT)[\s:]*\n?(.*?)(?=(?:##\s*(?:ONTOLOGY|MANIFESTO|EVOLUZIONE|INTERNAL)|$))",
    ]

    ONTOLOGY_PATTERNS = [
        r"###\s*(?:ONTOLOGY\s+CONTRIBUTION|MANIFESTO\s+UPDATE|AGGIORNAMENTO\s+MANIFESTO|ONTOLOGIA|PROPOSTA\s+MANIFESTO)[\s:]*\n?(.*?)(?=(?:###\s*(?:INTERNAL|EVOLUZIONE|ARGUMENT)|$))",
        r"##\s*(?:ONTOLOGY\s+CONTRIBUTION|MANIFESTO\s+UPDATE|AGGIORNAMENTO\s+MANIFESTO|ONTOLOGIA|PROPOSTA\s+MANIFESTO)[\s:]*\n?(.*?)(?=(?:##\s*(?:INTERNAL|EVOLUZIONE|ARGUMENT)|$))",
    ]

    EVOLUTION_PATTERNS = [
        r"###\s*(?:INTERNAL\s+EVOLUTION|EVOLUZIONE\s+MENTALE|INTERNAL\s+SHIFT|MEMORIA\s+INTERNA|NOTE\s+EVOLUTIVE)[\s:]*\n?(.*?)(?=(?:###\s*(?:ARGUMENT|ONTOLOGY|MANIFESTO)|$))",
        r"##\s*(?:INTERNAL\s+EVOLUTION|EVOLUZIONE\s+MENTALE|INTERNAL\s+SHIFT|MEMORIA\s+INTERNA|NOTE\s+EVOLUTIVE)[\s:]*\n?(.*?)(?=(?:##\s*(?:ARGUMENT|ONTOLOGY|MANIFESTO)|$))",
    ]

    @classmethod
    def parse(cls, raw_output: str) -> ParsedTurnOutput:
        """Parse raw agent output into dialogue, ontology updates, and internal evolution."""
        text = raw_output.strip()
        if not text:
            return ParsedTurnOutput(dialogue="", ontology_contribution="", internal_evolution="")

        dialogue = ""
        ontology = ""
        evolution = ""

        # Try to match ontology section
        for pattern in cls.ONTOLOGY_PATTERNS:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                ontology = match.group(1).strip()
                break

        # Try to match evolution section
        for pattern in cls.EVOLUTION_PATTERNS:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                evolution = match.group(1).strip()
                break

        # Try to match explicit argument section
        for pattern in cls.ARGUMENT_PATTERNS:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                dialogue = match.group(1).strip()
                break

        # Fallback 1: If no explicit argument pattern matched, but ontology or evolution was extracted,
        # extract everything before the first recognized section marker as the dialogue.
        if not dialogue:
            markers = [
                "### ONTOLOGY CONTRIBUTION",
                "### MANIFESTO UPDATE",
                "### AGGIORNAMENTO MANIFESTO",
                "### INTERNAL EVOLUTION",
                "### EVOLUZIONE MENTALE",
                "### INTERNAL SHIFT",
                "## ONTOLOGY CONTRIBUTION",
                "## INTERNAL EVOLUTION",
            ]
            first_idx = len(text)
            for marker in markers:
                idx = text.upper().find(marker.upper())
                if idx != -1 and idx < first_idx:
                    first_idx = idx

            if first_idx < len(text):
                dialogue = text[:first_idx].strip()
            else:
                dialogue = text.strip()

        # Clean any remaining delimiter headers inside extracted texts
        dialogue = re.sub(r"^###\s*(?:ARGUMENT|DIALOGUE|REPLICA)[\s:]*", "", dialogue, flags=re.IGNORECASE).strip()

        return ParsedTurnOutput(
            dialogue=dialogue,
            ontology_contribution=ontology,
            internal_evolution=evolution,
        )
