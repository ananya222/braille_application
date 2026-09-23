"""Independent, local boundary verification; never calls a translator.

This module does not certify containing blocks. Exact cell provenance and
resolved inherited modes are prerequisites, not defaults inferred from a
matching candidate. See Nemeth 4.6.5(b)/4.2 and UEB 7.1/7.5.
"""
from dataclasses import dataclass
from enum import Enum
import re

from .rule_result import RuleResult
from .sources import NEMETH_2022, NEMETH_ERRATA_2025, UEB_2024

RULE_ID = "NEMETH_BOUNDARY_PUNCT_001"
DOCUMENTS = f"{NEMETH_2022}; {UEB_2024}; {NEMETH_ERRATA_2025}"
SECTIONS = "Nemeth 4.6.5(b), 4.2; UEB 7.1.1, 7.5.1–4, 2.6.1–3; errata 4.2"
PAGES = "Nemeth 4-1,4-12; UEB 15–17,75–76,81; errata p.4 (PDF 8)"
# Independently transcribed from UEB Section 7, printed p.75. No generator import.
SENTENCE_END = {".": "⠲", "!": "⠖", "?": "⠦"}
TERMINATOR = "⠸⠱"  # Nemeth 4.2 symbol table, as amended by errata.


class Ownership(str, Enum):
    OUTER_UEB = "OUTER_UEB_PUNCTUATION"
    INNER_NEMETH = "INNER_NEMETH_PUNCTUATION"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True)
class BoundaryContext:
    source_before: str
    math_source: str
    source_after: str
    # These must come from structured interpretation/provenance, not candidates.
    math_complete: bool = False
    source_boundary_exact: bool = False
    sentence_role_resolved: bool = False
    modes_known: bool = False
    active_code_before: str | None = None
    expected_code_after: str | None = None
    grade1_mode: bool | None = None
    numeric_mode: bool | None = None
    capitalization_mode: str | None = None
    script_level: int | None = None
    typeform_active: bool | None = None
    punctuation_mode: str | None = None
    layout_resolved: bool = False


@dataclass(frozen=True)
class BoundaryVerification:
    status: str
    owner: Ownership
    expected: str
    actual: str
    reason: str
    actual_start: int | None = None
    actual_end: int | None = None
    rule_id: str = RULE_ID
    source_document: str = DOCUMENTS
    source_rule: str = SECTIONS
    source_page: str = PAGES
    state_transition: str = "NEMETH → UEB"


def ownership(context: BoundaryContext) -> Ownership:
    """Source-only decision; marker placement alone is not semantic ownership."""
    if not context.source_boundary_exact or not context.sentence_role_resolved:
        return Ownership.AMBIGUOUS
    if context.math_source and context.math_source[-1] in SENTENCE_END:
        return Ownership.INNER_NEMETH
    after = context.source_after
    if not after or after[0] not in SENTENCE_END:
        return Ownership.UNSUPPORTED
    if len(after) > 1 and not after[1].isspace():
        return Ownership.AMBIGUOUS
    if any(c in context.source_before + after for c in '\r\n\f"\'“”‘’()[]{}'):
        return Ownership.AMBIGUOUS
    return Ownership.OUTER_UEB


def verify(context: BoundaryContext, actual_cells: str, *, actual_start: int | None = None,
           actual_end: int | None = None, exact_range: bool = False) -> BoundaryVerification:
    """Check an exact local interval from math end through attached punctuation.

Interval includes the inner blank, terminator, and punctuation, but excludes
subsequent prose spacing. Missing/extra cells must remain in that interval.
The caller must establish both endpoints via provenance; searching for the
desired punctuation/terminator does not establish an exact interval.
ERROR refers to this supplied stream, never automatically to user input when
the stream is an unverified generator candidate.
"""
    owner = ownership(context)
    def outcome(status, reason, expected=""):
        return BoundaryVerification(status, owner, expected, actual_cells, reason, actual_start, actual_end)
    if owner != Ownership.OUTER_UEB:
        return outcome("REVIEW", "Ownership is unsupported or ambiguous; inner/standalone/cluster punctuation is not certified.")
    if not context.math_complete or not context.math_source.strip():
        return outcome("REVIEW", "Math structure/termination dependencies are unresolved.")
    if (not context.modes_known or context.active_code_before != "NEMETH"
            or context.expected_code_after != "UEB" or context.grade1_mode is not False
            or context.numeric_mode is not False or context.capitalization_mode is not None
            or context.script_level != 0 or context.typeform_active is not False
            or context.punctuation_mode != "ordinary" or not context.layout_resolved):
        return outcome("REVIEW", "Inherited code/mode, typeform, script or layout context is not independently resolved.")
    if (not exact_range or actual_start is None or actual_end is None
            or actual_start < 0 or actual_end < actual_start
            or actual_end - actual_start != len(actual_cells)
            or any(not 0x2800 <= ord(c) <= 0x283F for c in actual_cells)):
        return outcome("REVIEW", "Exact canonical physical-cell interval has not been established.")
    required = "⠀" + TERMINATOR + SENTENCE_END[context.source_after[0]]
    return outcome("PASS" if actual_cells == required else "ERROR",
                   "Independent Nemeth termination and UEB sentence-punctuation expectation compared with the exact supplied interval.", required)


def inspect_block(block):
    """Conservative production handoff: do not invent missing mode/provenance.

ExpectedBlock has no inherited-mode proof or exact boundary-source cell map.
Only add diagnostics to already-REVIEW blocks; do not alter unrelated rules
or promote an entire block on a local boundary assumption.
"""
    matches = tuple(re.finditer(r"\[\[\*ts\*\]\](.*?)\[\[\*te\*\]\]", block.source_text, re.S))
    records = tuple(block.math_records)
    if len(matches) != len(records) or any(m.group(1) != r.source for m,r in zip(matches,records)):
        return ()
    results = []
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(block.source_text)
        after = block.source_text[match.end():end]
        if not after or after[0] not in SENTENCE_END:
            continue
        context = BoundaryContext(
            source_before=block.source_text[:match.start()], math_source=match.group(1),
            source_after=after, source_boundary_exact=True,
        )
        local = verify(context, "")  # no fabricated actual range or inherited mode proof
        results.append(RuleResult(
            rule_id=RULE_ID, status="REVIEW", source=block.source_text,
            original_braille=block.braille, corrected_braille=block.braille,
            explanation="Boundary candidate requires independently resolved inherited modes, semantic punctuation ownership and exact boundary provenance; block remains REVIEW.",
            page=block.source_page, block=block.source_block,
            standard_area="NEMETH", family="boundary-punctuation",
            source_document=DOCUMENTS, source_rule=SECTIONS, source_page=PAGES,
            source_construct="outer punctuation boundary candidate",
            justification=local.reason + " No default-mode assumption or whole-block promotion.",
        ))
    return tuple(results)
