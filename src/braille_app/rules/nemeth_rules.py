"""Rules that verify the supported Nemeth translation subset."""

from __future__ import annotations

import re

from braille_app.translation.braille_cells import unicode_to_cells

from .rule_result import RuleResult
from .sources import NEMETH_2022
from .letter_grouping import record_promotion_contexts, verify_record
from .rule_catalog import ValidationContext
from braille_app.translation.simple_math import expected as simple_expected, RULE_ID, SOURCE_RULE, SOURCE_PAGE


# These structural constructs do not have a verified physical-cell rule in
# the current calibrated Nemeth subset.  They are surfaced as REVIEW instead
# of being treated as definite user errors.
_UNSUPPORTED_NEMETH = re.compile(
    # These Unicode symbols are defined by the vendored nemethdefs.cti and
    # are therefore not review-only.  The remaining characters here require
    # structural handling that the current probe table does not provide.
    r"(?:[₀₁₂₃₄₅₆₇₈₉⁰¹⁴⁵⁶⁷⁸⁹⁻ⁿᵢⱼ]|[√]|\[|\]|R_\*)"
)

_SUPPORTED_SIMPLE_SCRIPTS = re.compile(
    r"[A-Za-z](?:[₀₁₂₃₄₅₆₇₈₉]|[⁰¹⁴⁵⁶⁷⁸⁹ⁿ]|⁻[¹])"
)


def _unsupported_construct(source: str):
    """Return an unsupported construct after removing Rule 14 simple forms."""

    residual = _SUPPORTED_SIMPLE_SCRIPTS.sub("", source)
    return _UNSUPPORTED_NEMETH.search(residual)

_CALIBRATION_GAP_NEMETH = re.compile(
    r"(?:\(\s*\d+\s*,|\b[A-Za-z]+\s*\([^)]*\)|"
    r"\b[A-Za-z]+\s*:|(?:[A-Za-zπ][₀₁₂₃₄₅₆₇₈₉⁰¹⁴⁵⁶⁷⁸⁹ⁿ⁻]*|\d+)\s*/\s*\d+|\)\s*/\s*\d+|\.\.\.+|"
    r"\b(?:sin|cos|tan|sec|csc|cot)\s+[A-Za-z][₀₁₂₃₄₅₆₇₈₉]|"
    r"\b[A-Za-z]_[A-Za-z0-9*]+|\d+!|\b(?:both|either|where|such that)\b)"
)


def verify_math_block(block, page: int | None, block_id: int | str | None, *, allow_letter_grouping: bool = False, allow_simple_math: bool = False) -> RuleResult:
    records = getattr(block, "math_records", ())
    expected_cells = unicode_to_cells(block.braille)
    unsupported = []
    calibration_gaps = []
    grouping_context_known = allow_letter_grouping and all(record_promotion_contexts(block))
    proofs = [simple_expected(record.source) if allow_simple_math else None for record in records]
    if records and all(proof is not None for proof in proofs):
        correct = all(record.braille == proof for record, proof in zip(records, proofs))
        return RuleResult(
            rule_id=RULE_ID, status="PASS" if correct else "REVIEW",
            source=block.source_text, original_braille=block.braille,
            corrected_braille=block.braille,
            explanation="Complete baseline linear expressions satisfy the closed grammar and cited cell rules."
                if correct else "Simple-math candidate disagrees with the cited structural rules.",
            page=page, block=block_id, standard_area="Nemeth", family="simple-linear-math",
            source_document=NEMETH_2022, source_rule=SOURCE_RULE, source_page=SOURCE_PAGE,
            source_construct="complete simple linear expression",
            original_cells=expected_cells, expected_cells=expected_cells, corrected_cells=expected_cells,
            justification="Full parse; regular baseline integers/single lowercase variables; no unsupported tokens or inherited modes. Actual comparison is performed by the production validator.",
        )
    # Full-source applicability, never accept an unsupported suffix merely
    # because its individual printable symbols exist in a translation table.
    if any(
        proof is None and not (
            grouping_context_known
            and (group_proof := verify_record(record, ValidationContext(code="NEMETH"))) is not None
            and group_proof.status == "PASS"
        )
        for record, proof in zip(records, proofs)
    ):
        return RuleResult(
            rule_id="NEMETH_SIMPLE_SCOPE_001", status="REVIEW", source=block.source_text,
            original_braille=block.braille, corrected_braille=block.braille,
            explanation="Expression is outside the trusted simple-math grammar; no complete structural proof is available on this path.",
            page=page, block=block_id, standard_area="Nemeth", family="simple-math-scope",
            source_document=NEMETH_2022, source_rule="1.3.1; " + SOURCE_RULE,
            source_page="1-2; " + SOURCE_PAGE, source_construct="unsupported complete expression",
            original_cells=expected_cells, expected_cells=expected_cells, corrected_cells=expected_cells,
            justification="Do not infer radical vinculum, implied multiplication, scripts or other excluded structure.",
        )
    for record in records:
        match = _unsupported_construct(record.source)
        if match:
            unsupported.append(match.group(0))
        proof = verify_record(record, ValidationContext(code="NEMETH")) if grouping_context_known else None
        gap = None if proof is not None and proof.status == "PASS" else _CALIBRATION_GAP_NEMETH.search(record.source)
        if gap:
            calibration_gaps.append(gap.group(0))
    unresolved = [
        record.ascii_braille
        for record in records
        if re.search(r"\\X[0-9A-F]{4,}", record.ascii_braille, re.I)
    ]
    if unsupported:
        construct = ", ".join(dict.fromkeys(unsupported))
        return RuleResult(
            rule_id="NEMETH_RULE_002",
            status="REVIEW",
            source=block.source_text,
            original_braille=block.braille,
            corrected_braille=block.braille,
            explanation="The math span contains a construct outside the verified Nemeth subset.",
            page=page,
            block=block_id,
            standard_area="Nemeth",
            family="scripts/grouping",
            source_document=NEMETH_2022,
            source_rule="14 Superscripts and Subscripts",
            source_page="14-1 to 14-33 (PDF pp. 170-202)",
            source_construct=construct,
            original_cells=expected_cells,
            expected_cells=expected_cells,
            corrected_cells=expected_cells,
            justification="No authoritative local rule currently proves the rendered cells for this construct.",
        )
    if calibration_gaps:
        construct = ", ".join(dict.fromkeys(calibration_gaps))
        return RuleResult(
            rule_id="NEMETH_RULE_003",
            status="REVIEW",
            source=block.source_text,
            original_braille=block.braille,
            corrected_braille=block.braille,
            explanation="The math span uses punctuation, function, collection, fraction, or index syntax "
            "whose calibrated physical-cell rule is not yet complete.",
            page=page,
            block=block_id,
            standard_area="Nemeth",
            family="numeric/functions/fractions/collections",
            source_document=NEMETH_2022,
            source_rule="3 Numeric; 13 Fractions; 18 Functions; 19 Grouping",
            source_page="3-1 to 3-25; 13-1 to 13-15; 18-1 to 18-7; 19-1 to 19-13",
            source_construct=construct,
            original_cells=expected_cells,
            expected_cells=expected_cells,
            corrected_cells=expected_cells,
            justification="The current local rules do not prove the Duxbury-independent cell sequence for this construct.",
        )
    if unresolved:
        return RuleResult(
            rule_id="NEMETH_RULE_001",
            status="REVIEW",
            source=block.source_text,
            original_braille=block.braille,
            corrected_braille=block.braille,
            explanation="The supported Nemeth table emitted an unresolved symbol escape.",
            page=page,
            block=block_id,
            standard_area="Nemeth",
            family="symbols",
            source_document=NEMETH_2022,
            source_rule="1.3.2 Uniformity and Appendix D",
            source_page="1-2; D-1 to D-35",
            source_construct="unresolved Liblouis symbol escape",
            original_cells=expected_cells,
            expected_cells=expected_cells,
            corrected_cells=expected_cells,
            justification="Unresolved escapes cannot be accepted without manual verification.",
        )
    return RuleResult(
        rule_id="NEMETH_RULE_001",
        status="PASS",
        source=block.source_text,
        original_braille=block.braille,
        corrected_braille=block.braille,
        explanation="Math spans translated through the calibrated Nemeth table without unresolved escapes.",
        page=page,
        block=block_id,
        standard_area="Nemeth",
        family="calibrated-symbols",
        source_document=NEMETH_2022,
        source_rule="2 Nemeth Indicators and 20-23 Signs and Symbols",
        source_page="2-1 to 2-5; 20-1 to 23-14",
        source_construct="explicit math span",
        original_cells=expected_cells,
        expected_cells=expected_cells,
        corrected_cells=expected_cells,
        justification="The calibrated Nemeth path and normalization rules cover this construct.",
    )
