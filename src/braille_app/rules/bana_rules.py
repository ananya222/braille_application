"""BANA mixed-text/math boundary rules."""

from __future__ import annotations

from .rule_result import RuleResult
from .sources import NEMETH_ERRATA_2025
from braille_app.translation.braille_cells import unicode_to_cells


def verify_switching_block(block, page: int | None, block_id: int | str | None) -> RuleResult:
    records = getattr(block, "math_records", ())
    expected_cells = unicode_to_cells(block.braille)
    if not records:
        return RuleResult(
            rule_id="BANA_SWITCH_003",
            status="PASS",
            source=block.source_text,
            original_braille=block.braille,
            corrected_braille=block.braille,
            explanation="No math span is present in this block.",
            page=page,
            block=block_id,
            standard_area="BANA",
            family="switching",
            source_document=NEMETH_ERRATA_2025,
            source_rule="Rule 4.2 (errata override)",
            source_page="4 (PDF p. 8)",
            source_construct="no explicit math span",
            original_cells=expected_cells,
            expected_cells=expected_cells,
            corrected_cells=expected_cells,
            justification="No UEB/Nemeth boundary is required for a prose-only block.",
        )
    expected_pairs = sum(1 for _ in records)
    # A mixed translation inserts exactly one verified pair for each explicit
    # math span.  This rule does not repair uncertain output; it reports it.
    switch_count = block.braille.count("⠸⠩")
    return_count = block.braille.count("⠸⠱")
    status = "PASS" if switch_count == return_count == expected_pairs else "REVIEW"
    explanation = (
        "Each explicit math span has one verified UEB/Nemeth switch pair."
        if status == "PASS"
        else "The number of verified switch pairs does not match the explicit math spans."
    )
    return RuleResult(
        rule_id="BANA_SWITCH_003",
        status=status,
        source=block.source_text,
        original_braille=block.braille,
        corrected_braille=block.braille,
        explanation=explanation,
        page=page,
        block=block_id,
        standard_area="BANA",
        family="switching",
        source_document=NEMETH_ERRATA_2025,
        source_rule="Rule 4.2 (errata override)",
        source_page="4 (PDF p. 8)",
        source_construct="explicit math span boundary",
        original_cells=expected_cells,
        expected_cells=expected_cells,
        corrected_cells=expected_cells,
        justification="One verified switch pair is required for each explicit math span.",
    )
