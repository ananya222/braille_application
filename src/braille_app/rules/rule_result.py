"""Structured outcomes emitted by the production rule engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


RuleStatus = Literal["PASS", "CORRECTED", "REVIEW", "EXCLUDED_OUT_OF_SCOPE"]


@dataclass(frozen=True)
class RuleResult:
    rule_id: str
    status: RuleStatus
    source: str
    original_braille: str
    corrected_braille: str
    explanation: str
    page: int | None = None
    block: int | str | None = None
    # Traceability fields keep the rule decision tied to a standards area and
    # to the exact source construct/cells that were checked.  They are added
    # after the original fields so existing positional callers remain valid.
    standard_area: str = ""
    family: str = ""
    source_document: str = ""
    source_rule: str = ""
    source_page: str = ""
    source_construct: str = ""
    original_cells: tuple[int, ...] = ()
    expected_cells: tuple[int, ...] = ()
    corrected_cells: tuple[int, ...] = ()
    justification: str = ""
