"""Case 2: ASCII English capitalization in uncontracted UEB."""

from __future__ import annotations

import re
from dataclasses import replace

from braille_app.rules.basic_capitalization import CapitalSite
from braille_app.rules.rule_result import RuleResult
from braille_app.rules.sources import UEB_2024
from braille_app.translation.braille_cells import unicode_to_cells

from .source_normalization import normalize_uncontracted_case2


_WORDS = re.compile(r"[A-Za-z]+")
_CAPS_RULE = "UEB_8"
_SCOPE_RULE = "UEB_CASE2_SCOPE"


def translate_source(text, translator):
    """Translate one supported source block in one Liblouis context."""

    return translator.translate_prose(text)


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
        source_rule="8.1.1; 8.2.1; 8.3.1; 8.4.1-2; 8.5.1-3; 8.6.1",
        source_page="89-96 (PDF pp. 117-124)",
        source_construct=construct,
        original_cells=cells,
        expected_cells=cells,
        corrected_cells=cells,
        justification=(
            "ICEB UEB 2024 is the authority; vendored Liblouis supplies the "
            "candidate uncontracted cell stream and source positions."
        ),
    )


def _single_indicator_sites(block, translator):
    """Expose only unambiguous one-indicator sites to the existing locator."""

    source = normalize_uncontracted_case2(block.source_text)
    translated, positions = translator.translate_prose_with_positions(source)
    if translated != block.braille or len(translated) != len(positions):
        return (), False
    sites: list[CapitalSite] = []
    for match in _WORDS.finditer(source):
        for offset in range(match.start(), match.end()):
            indexes = [index for index, position in enumerate(positions) if position == offset]
            if len(indexes) != 2 or translated[indexes[0]] != "⠠":
                continue
            if indexes[1] != indexes[0] + 1:
                continue
            sites.append(CapitalSite(
                word=match.group(),
                source_start=offset,
                expected_start=indexes[0],
                uppercase=source[offset].isupper(),
                following_cell=ord(translated[indexes[1]]) - 0x2800,
            ))
    return tuple(sites), True


def verify_document(document, translator):
    pages = []
    for page in document.pages:
        blocks = []
        for block in page.blocks:
            if block.region_type in {"empty", "control"}:
                blocks.append(replace(block, rule_status="PASS", rule_results=()))
                continue
            if block.rule_status == "REVIEW":
                blocks.append(replace(
                    block,
                    rule_results=(_result(
                        block,
                        _SCOPE_RULE,
                        "REVIEW",
                        "The source is outside Case 2; no confirmed error is emitted.",
                        "scope",
                        "unsupported source construct",
                    ),),
                ))
                continue
            sites, mapped = _single_indicator_sites(block, translator)
            if not mapped:
                blocks.append(replace(
                    block,
                    rule_status="REVIEW",
                    rule_results=(_result(
                        block,
                        _CAPS_RULE,
                        "REVIEW",
                        "Liblouis did not provide a deterministic source-to-cell capitalization map.",
                        "capitalisation",
                        "unresolved capitalization mapping",
                    ),),
                    capital_sites=(),
                ))
                continue
            has_capital = any(char.isupper() for char in block.source_text)
            results = [_result(
                block,
                _CAPS_RULE,
                "PASS",
                "ASCII capitalization modes are translated in one vendored Liblouis source context.",
                "capitalisation",
                "capital letter, capitalized word, and in-block capitalized passage",
            )] if has_capital else []
            results.append(_result(
                block,
                _SCOPE_RULE,
                "PASS",
                "ASCII English letters and ordinary ASCII spaces are in Case 2 scope.",
                "scope",
                "English letters and ordinary ASCII spaces",
            ))
            blocks.append(replace(
                block,
                rule_status="PASS",
                rule_results=tuple(results),
                capital_sites=sites,
            ))
        pages.append(replace(page, blocks=tuple(blocks)))
    return replace(document, pages=tuple(pages))
