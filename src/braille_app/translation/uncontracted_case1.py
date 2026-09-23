"""Case 1: lowercase English alphabet and ordinary words only."""

from __future__ import annotations

from dataclasses import replace

from braille_app.rules.rule_result import RuleResult
from braille_app.rules.sources import UEB_2024
from braille_app.translation.braille_cells import unicode_to_cells

from .uncontracted_phase1 import translate_source_with_positions


_SCOPE_RULE = "UEB_CASE1_SCOPE"


def translate_source(text, translator):
    return translate_source_with_positions(text, translator)[0]


def _result(block, status: str, explanation: str) -> RuleResult:
    cells = unicode_to_cells(block.braille) if block.braille else ()
    return RuleResult(
        rule_id=_SCOPE_RULE,
        status=status,
        source=block.source_text,
        original_braille=block.braille,
        corrected_braille=block.braille,
        explanation=explanation,
        page=block.source_page,
        block=block.source_block,
        standard_area="UEB",
        family="alphabet and ordinary words",
        source_document=UEB_2024,
        source_rule="4.1.1-4.1.3",
        source_page="41-44 (PDF pp. 69-72)",
        source_construct="lowercase English letters and ordinary ASCII spaces",
        original_cells=cells,
        expected_cells=cells,
        corrected_cells=cells,
        justification=(
            "ICEB UEB 2024 is the authority; vendored Liblouis supplies the "
            "candidate letter-by-letter cells."
        ),
    )


def verify_document(document, _translator):
    pages = []
    for page in document.pages:
        blocks = []
        for block in page.blocks:
            if block.region_type in {"empty", "control"}:
                blocks.append(replace(block, rule_status="PASS", rule_results=()))
            elif block.rule_status == "REVIEW":
                blocks.append(replace(
                    block,
                    rule_results=(_result(
                        block,
                        "REVIEW",
                        "The source is outside Case 1; no confirmed error is emitted.",
                    ),),
                ))
            else:
                blocks.append(replace(
                    block,
                    rule_status="PASS",
                    rule_results=(_result(
                        block,
                        "PASS",
                        "Lowercase English letters and ordinary ASCII spaces are in Case 1 scope.",
                    ),),
                ))
        pages.append(replace(page, blocks=tuple(blocks)))
    return replace(document, pages=tuple(pages))
