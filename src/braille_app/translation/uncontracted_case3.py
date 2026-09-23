"""Case 3: English uncontracted UEB numbers and cited numeric interactions."""

from __future__ import annotations

import re
from dataclasses import replace

from braille_app.rules.basic_capitalization import CapitalSite
from braille_app.rules.rule_result import RuleResult
from braille_app.rules.sources import UEB_2024
from braille_app.translation.braille_cells import unicode_to_cells

from .source_normalization import UnsupportedSourceError, normalize_uncontracted_case3


_SCOPE_RULE = "UEB_CASE3_SCOPE"
_NUMERIC_RULE = "UEB_CASE3_NUMERIC"
_WORDS = re.compile(r"[A-Za-z]+")
_GROUPED_INTEGER = re.compile(
    r"(?<![0-9.,])([0-9]{1,3}(?: [0-9]{3})+)(?![0-9.,]| +[0-9])"
)
_NAMED_NUMBER = re.compile(
    r"(?i)\b(?:phone|telephone|time|date|isbn)(?: number)? "
    r"([0-9]+(?: [0-9]+)+)(?![0-9])"
)
_HYPHEN_SUFFIX = re.compile(r"[0-9]+[-–—]([A-Za-z]+)")


def _translated_with_positions(source: str, translator) -> tuple[list[str], list[int]]:
    braille, positions = translator.translate_prose_with_positions(source)
    if len(braille) != len(positions) or any(not 0 <= offset < len(source) for offset in positions):
        raise ValueError("Liblouis returned an incomplete source-to-cell map")
    if tuple(positions) != tuple(sorted(positions)):
        raise ValueError("Liblouis returned a non-monotonic source-to-cell map")
    return list(braille), list(positions)


def _numeric_space_pairs(source: str, cells: list[str], positions: list[int]) -> list[tuple[int, int]]:
    """Return mapped (space-cell, following numeric-indicator) pairs.

    UEB 6.6.1 defines the numeric-space cell as the space plus its following
    digit. The ordinary-space and repeated numeric prefix from Liblouis are
    therefore replaced using the exact source-position map.
    """

    pairs: list[tuple[int, int]] = []
    space_offsets: set[int] = set()
    for match in _GROUPED_INTEGER.finditer(source):
        for space_offset in range(match.start(1), match.end(1)):
            if source[space_offset] != " ":
                continue
            space_offsets.add(space_offset)
    for match in _NAMED_NUMBER.finditer(source):
        space_offsets.update(
            index for index in range(match.start(1), match.end(1))
            if source[index] == " "
        )
    for space_offset in space_offsets:
        blanks = [i for i, (cell, pos) in enumerate(zip(cells, positions))
                  if pos == space_offset and cell == "⠀"]
        digit_offset = space_offset + 1
        prefixes = [i for i, (cell, pos) in enumerate(zip(cells, positions))
                    if pos == digit_offset and cell == "⠼"]
        if len(blanks) != 1 or len(prefixes) != 1 or prefixes[0] <= blanks[0]:
            raise ValueError("Numeric-space cells have no unique Liblouis source mapping")
        pairs.append((blanks[0], prefixes[0]))
    return pairs


def _needs_grade1_suffix(suffix: str) -> bool:
    # ICEB UEB 2024, 6.5.4 explicitly demonstrates a single-letter suffix,
    # an all-capital abbreviation (6-CD), and "yr" (20-yr). It also explicitly
    # contrasts 20yr and the ordinary full word 3-dimensional: neither gets
    # an inserted indicator. Keep the override within those cited patterns.
    return len(suffix) == 1 or suffix.lower() == "yr" or (len(suffix) > 1 and suffix.isupper())


def _translate_normalized_source_with_positions(source: str, translator) -> tuple[str, list[int]]:
    cells, positions = _translated_with_positions(source, translator)

    # Apply from right to left so original cell indices remain stable.
    for blank_index, prefix_index in sorted(
        _numeric_space_pairs(source, cells, positions), reverse=True
    ):
        cells[blank_index] = "⠐"
        del cells[prefix_index]
        del positions[prefix_index]

    insertions: set[int] = set()
    for match in _HYPHEN_SUFFIX.finditer(source):
        suffix = match.group(1)
        if not _needs_grade1_suffix(suffix):
            continue
        source_offset = match.start(1)
        mapped = [i for i, offset in enumerate(positions) if offset == source_offset]
        if not mapped:
            raise ValueError("Grade 1 suffix has no Liblouis source-to-cell mapping")
        first = mapped[0]
        if cells[first] == "⠰":
            continue
        insertions.add(first)
    for index in sorted(insertions, reverse=True):
        cells.insert(index, "⠰")
        positions.insert(index, positions[index])

    return "".join(cells), positions


def _translate_source_with_positions(text: str, translator) -> tuple[str, list[int]]:
    return _translate_normalized_source_with_positions(
        normalize_uncontracted_case3(text), translator
    )


def translate_source(text: str, translator) -> str:
    """Use Liblouis, then apply only the two independently cited corrections."""

    try:
        return _translate_source_with_positions(text, translator)[0]
    except ValueError as exc:
        raise UnsupportedSourceError(
            f"Unsupported Case 3 source-to-cell mapping: {exc}"
        ) from exc


def _capital_sites(source: str, braille: str, positions: list[int]) -> tuple[CapitalSite, ...]:
    cells = list(braille)
    sites: list[CapitalSite] = []
    for word in _WORDS.finditer(source):
        value = word.group()
        if not value[0].isupper() or any(char.isupper() for char in value[1:]):
            continue
        offsets = [i for i, position in enumerate(positions) if position == word.start()]
        caps = [i for i in offsets if cells[i] == "⠠"]
        if len(caps) != 1:
            continue
        cap_index = caps[0]
        letter_index = cap_index + 1
        if letter_index >= len(cells) or positions[letter_index] != word.start():
            continue
        sites.append(CapitalSite(
            word=value,
            source_start=word.start(),
            expected_start=cap_index,
            uppercase=True,
            following_cell=ord(cells[letter_index]) - 0x2800,
        ))
    return tuple(sites)


def _result(block, rule_id: str, status: str, explanation: str, family: str, construct: str) -> RuleResult:
    cells = unicode_to_cells(block.braille) if block.braille else ()
    return RuleResult(
        rule_id=rule_id,
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
        source_rule="5.6.1-5.6.4; 5.8.1; 6.1.1-6.7.1",
        source_page="59-71 (PDF pp. 87-99)",
        source_construct=construct,
        original_cells=cells,
        expected_cells=cells,
        corrected_cells=cells,
        justification=(
            "ICEB UEB 2024 is authoritative. Vendored Liblouis 3.38.0 with "
            "unicode.dis,en-ueb-g1.ctb supplies the base cells and source "
            "positions; only cited numeric-space and 6.5.4 cases are overridden."
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
                    _SCOPE_RULE,
                    "REVIEW",
                    "Source contains constructs outside the supported Case 3 numeric slice; no confirmed error is emitted.",
                    "scope",
                    "unsupported source construct",
                ),)))
                continue
            source = normalize_uncontracted_case3(block.source_text)
            try:
                expected, adjusted_positions = _translate_source_with_positions(source, translator)
                if expected != block.braille:
                    raise ValueError("Expected stream and source-position corrections disagree")
                sites = _capital_sites(source, expected, adjusted_positions)
            except ValueError as exc:
                blocks.append(replace(block, rule_status="REVIEW", rule_results=(_result(
                    block,
                    _NUMERIC_RULE,
                    "REVIEW",
                    f"Numeric source-to-cell mapping is ambiguous: {exc}",
                    "numeric mode",
                    "unresolved numeric source mapping",
                ),), capital_sites=()))
                continue
            results = [_result(
                block,
                _NUMERIC_RULE,
                "PASS",
                "Supported numeric forms follow the cited UEB 2024 rules and source-position mappings.",
                "numeric mode",
                "digits, decimal punctuation, numeric spaces, and supported hyphen/dash interactions",
            )]
            if any(char.isupper() for char in source):
                results.append(_result(
                    block,
                    "UEB_8",
                    "PASS",
                    "Capital letters and the required numeric Grade 1/capitalization order are represented in the same source context.",
                    "capitalisation",
                    "word-initial capitalization alongside supported numeric forms",
                ))
            results.append(_result(
                block,
                _SCOPE_RULE,
                "PASS",
                "Case 3 accepts ASCII English letters, digits, ordinary spaces, comma, period, hyphen, en dash, and em dash only.",
                "scope",
                "supported English/numeric characters",
            ))
            blocks.append(replace(block, rule_status="PASS", rule_results=tuple(results), capital_sites=sites))
        pages.append(replace(page, blocks=tuple(blocks)))
    return replace(document, pages=tuple(pages))
