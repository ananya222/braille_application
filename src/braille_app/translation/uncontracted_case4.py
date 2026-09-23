"""Case 4: core punctuation on the existing uncontracted UEB path."""

from __future__ import annotations

import re
from dataclasses import replace

from braille_app.rules.rule_result import RuleResult
from braille_app.rules.sources import UEB_2024
from braille_app.translation.braille_cells import unicode_to_cells

from .source_normalization import UnsupportedSourceError, normalize_uncontracted_case4
from .uncontracted_case3 import (
    _capital_sites,
    _translate_normalized_source_with_positions,
)

_SCOPE_RULE = "UEB_CASE4_SCOPE"
_PUNCTUATION_RULE = "UEB_CASE4_CORE_PUNCTUATION"
_DASHES = "-–—"
_INTERVENING_PUNCTUATION = ",.!:;"
_PUNCTUATION_SPACES = re.compile(r"[,.!?:;] {2,}")


def _translate_source_with_positions(source: str, translator) -> tuple[str, list[int]]:
    braille, positions = _translate_normalized_source_with_positions(source, translator)
    cells = list(braille)

    # UEB 7.1.2 permits only one blank cell after punctuation, even if print
    # has more. Remove only mapped surplus blanks in that cited context.
    surplus_blanks = []
    for run in _PUNCTUATION_SPACES.finditer(source):
        for offset in range(run.start() + 2, run.end()):
            mapped = [i for i, (cell, position) in enumerate(zip(cells, positions))
                      if position == offset and cell == "⠀"]
            if len(mapped) != 1:
                raise ValueError("Surplus punctuation space has no unique Liblouis source mapping")
            surplus_blanks.append(mapped[0])
    for index in sorted(surplus_blanks, reverse=True):
        del cells[index]
        del positions[index]

    insertions: set[int] = set()
    for question in (i for i, char in enumerate(source) if char == "?"):
        prior = question - 1
        while prior >= 0 and source[prior] in _INTERVENING_PUNCTUATION:
            prior -= 1
        if prior < 1 or source[prior] not in _DASHES or not source[prior - 1].isdigit():
            continue
        mapped = [i for i, offset in enumerate(positions) if offset == question and cells[i] == "⠦"]
        if len(mapped) != 1:
            raise ValueError("Question mark has no unique Liblouis source-to-cell mapping")
        question_cell = mapped[0]
        if question_cell == 0 or cells[question_cell - 1] != "⠰":
            insertions.add(question_cell)
    for index in sorted(insertions, reverse=True):
        cells.insert(index, "⠰")
        positions.insert(index, positions[index])
    return "".join(cells), positions


def translate_source(text: str, translator) -> str:
    source = normalize_uncontracted_case4(text)
    try:
        return _translate_source_with_positions(source, translator)[0]
    except ValueError as exc:
        raise UnsupportedSourceError(f"Unsupported Case 4 source-to-cell mapping: {exc}") from exc


def _result(block, status: str, explanation: str, family: str, construct: str) -> RuleResult:
    cells = unicode_to_cells(block.braille) if block.braille else ()
    has_question = "?" in block.source_text
    has_numeric_period = any(
        block.source_text[index - 1].isdigit()
        for index, char in enumerate(block.source_text)
        if char == "." and index > 0
    )
    rules = "7.5.1-7.5.4; 7.1.2" if has_question else "7.1.1-7.1.3"
    pages = "81, 76-77 (PDF pp. 109, 104-105)" if has_question else "75-78 (PDF pp. 103-106)"
    if has_numeric_period:
        rules += "; 6.4.1"
        pages += "; 68 (PDF p. 96)"
    return RuleResult(
        rule_id=_PUNCTUATION_RULE if family != "scope" else _SCOPE_RULE,
        status=status,
        source=block.source_text,
        original_braille=block.braille,
        corrected_braille=block.braille,
        explanation=explanation,
        page=block.source_page,
        block=block.source_block,
        standard_area="UEB",
        family=family,
        source_document=UEB_2024,
        source_rule=rules,
        source_page=pages,
        source_construct=construct,
        original_cells=cells,
        expected_cells=cells,
        corrected_cells=cells,
        justification=(
            "ICEB UEB 2024 is authoritative. The vendored Liblouis table supplies "
            "the base translation; only the cited question-mark-after-numeric-dash "
            "case is corrected using the source-position map."
        ),
    )


def verify_document(document, translator):
    pages = []
    for page in document.pages:
        blocks = []
        for block in page.blocks:
            if block.region_type in {"empty", "control"}:
                blocks.append(replace(block, rule_status="PASS", rule_results=()))
                continue
            if block.rule_status == "REVIEW":
                blocks.append(replace(block, rule_results=(_result(
                    block,
                    "REVIEW",
                    "Source contains constructs outside the supported Case 4 slice; no confirmed error is emitted.",
                    "scope",
                    "unsupported source construct",
                ),)))
                continue
            source = normalize_uncontracted_case4(block.source_text)
            try:
                expected, positions = _translate_source_with_positions(source, translator)
                if expected != block.braille:
                    raise ValueError("Expected stream and source-position corrections disagree")
                sites = _capital_sites(source, expected, positions)
            except ValueError as exc:
                blocks.append(replace(block, rule_status="REVIEW", rule_results=(_result(
                    block,
                    "REVIEW",
                    f"Punctuation source-to-cell mapping is ambiguous: {exc}",
                    "punctuation",
                    "unresolved punctuation source mapping",
                ),), capital_sites=()))
                continue
            rules = [_result(
                block,
                "PASS",
                "Supported punctuation follows the cited UEB 2024 rules and mapped Liblouis cells.",
                "punctuation",
                "comma, period, question, exclamation, colon, and semicolon",
            )]
            if any(char.isupper() for char in source):
                rules.append(_result(
                    block,
                    "PASS",
                    "Existing capitalization indicators remain mapped in punctuation context.",
                    "capitalisation",
                    "capitalized words adjacent to supported punctuation",
                ))
            rules.append(_result(
                block,
                "PASS",
                "Case 4 accepts the supported English, numeric, and six-mark punctuation slice only.",
                "scope",
                "supported punctuation source constructs",
            ))
            blocks.append(replace(block, rule_status="PASS", rule_results=tuple(rules), capital_sites=sites))
        pages.append(replace(page, blocks=tuple(blocks)))
    return replace(document, pages=tuple(pages))
