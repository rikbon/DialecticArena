"""
Tests for OutputParser.
"""

from agent_orchestrator.workspace.parser import OutputParser


def test_parser_standard_three_sections():
    raw = """
### ARGUMENT
Reductionism is the only method that provides mechanistic explanation.

### ONTOLOGY CONTRIBUTION
Proposition 1: Mind supervenes on matter.

### INTERNAL EVOLUTION
Refining my definition of supervenience.
"""
    parsed = OutputParser.parse(raw)
    assert "Reductionism is the only method" in parsed.dialogue
    assert "Proposition 1: Mind supervenes" in parsed.ontology_contribution
    assert "Refining my definition" in parsed.internal_evolution


def test_parser_italian_headers():
    raw = """
### DIBATTITO
La coscienza non può essere ridotta al calcolo deterministico.

### AGGIORNAMENTO MANIFESTO
Definizione: Emergenza debole vs forte.

### EVOLUZIONE MENTALE
Ho rivalutato la complessità non lineare di Alfa.
"""
    parsed = OutputParser.parse(raw)
    assert "non può essere ridotta" in parsed.dialogue
    assert "Emergenza debole vs forte" in parsed.ontology_contribution
    assert "Ho rivalutato la complessità" in parsed.internal_evolution


def test_parser_fallback_no_headers():
    raw = "This is an unstructured free-form reply by an agent without headers."
    parsed = OutputParser.parse(raw)
    assert parsed.dialogue == raw
    assert parsed.ontology_contribution == ""
    assert parsed.internal_evolution == ""


def test_parser_empty_string():
    parsed = OutputParser.parse("")
    assert parsed.dialogue == ""
    assert parsed.ontology_contribution == ""
    assert parsed.internal_evolution == ""
