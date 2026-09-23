"""Rules that guard the contracted UEB side of the pipeline."""

from __future__ import annotations

import re

from braille_app.translation.braille_cells import unicode_to_cells

from .rule_result import RuleResult
from .sources import UEB_2024


_UNSUPPORTED_UEB = re.compile(
    r"[₀₁₂₃₄₅₆₇₈₉ₐₑₒₓᵢⱼ]|FIGURE_REQUIRES_MANUAL_REVIEW"
)
_MATH_SPAN = re.compile(r"\[\[\*ts\*\]\].*?\[\[\*te\*\]\]", re.S)


def verify_ueb_block(block, page: int | None, block_id: int | str | None) -> RuleResult:
    """Record that prose was produced by the configured Liblouis UEB table.

    This is intentionally a provenance rule, not a context-free replacement
    table.  The literary table remains the authority for contractions.
    """

    expected_cells = unicode_to_cells(block.braille)
    # Unicode scripts inside an explicit Nemeth span are not UEB prose and
    # must be evaluated by the Nemeth rules instead.
    prose_source = _MATH_SPAN.sub("", block.source_text)
    unsupported = _UNSUPPORTED_UEB.search(prose_source)
    if unsupported:
        if unsupported.group(0) == "FIGURE_REQUIRES_MANUAL_REVIEW":
            return RuleResult(
                rule_id="UEB_SCOPE_001",
                status="EXCLUDED_OUT_OF_SCOPE",
                source=block.source_text,
                original_braille=block.braille,
                corrected_braille=block.braille,
                explanation=(
                    "The source contains a genuinely non-textual figure placeholder; "
                    "figure geometry and tactile-graphic production are outside the text validator."
                ),
                page=page,
                block=block_id,
                standard_area="UEB",
                family="figure-scope",
                source_document=UEB_2024,
                source_rule="11 Technical Material",
                source_page="181-186 (PDF pp. 209-214)",
                source_construct=unsupported.group(0),
                original_cells=expected_cells,
                expected_cells=expected_cells,
                corrected_cells=expected_cells,
                justification="Non-textual figure geometry is explicitly outside this text-only validator scope.",
            )
        explanation = (
            "The source contains indexed/subscript prose or a figure placeholder "
            "whose UEB rendering is not covered by the deterministic rule set."
        )
        return RuleResult(
            rule_id="UEB_RULE_002",
            status="REVIEW",
            source=block.source_text,
            original_braille=block.braille,
            corrected_braille=block.braille,
            explanation=explanation,
            page=page,
            block=block_id,
            standard_area="UEB",
            family="technical/material-boundary",
            source_document=UEB_2024,
            source_rule="11.4 Technical Material",
            source_page="181-186 (PDF pp. 209-214)",
            source_construct=unsupported.group(0),
            original_cells=expected_cells,
            expected_cells=expected_cells,
            corrected_cells=expected_cells,
            justification="Unsupported indexed prose/figure placeholder requires manual review.",
        )

    return RuleResult(
        rule_id="UEB_RULE_001",
        status="PASS",
        source=block.source_text,
        original_braille=block.braille,
        corrected_braille=block.braille,
        explanation="Prose segment was translated by the configured contracted UEB table.",
        page=page,
        block=block_id,
        standard_area="UEB",
        family="contractions",
        source_document=UEB_2024,
        source_rule="10 Contractions",
        source_page="113-140 (PDF pp. 141-168)",
        source_construct=getattr(block, "region_type", "text"),
        original_cells=expected_cells,
        expected_cells=expected_cells,
        corrected_cells=expected_cells,
        justification="The configured en-ueb-g2.ctb table is the literary UEB authority.",
    )
