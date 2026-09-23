"""Phase-1 English-only uncontracted UEB scope and capitalization checks."""

from __future__ import annotations

import re
from dataclasses import replace

from braille_app.rules.basic_capitalization import CapitalSite
from braille_app.rules.rule_result import RuleResult
from braille_app.rules.sources import UEB_2024
from braille_app.translation.braille_cells import unicode_to_cells
from braille_app.translation.liblouis_translator import LiblouisTranslator


_WORDS = re.compile(r"[A-Za-z]+")
_CAPS_RULE = "UEB_8"
_SCOPE_RULE = "UEB_PHASE1_SCOPE"


def translate_source(text: str, translator: LiblouisTranslator) -> str:
    """Translate each supported word independently, retaining every space."""

    return translate_source_with_positions(text, translator)[0]


def translate_source_with_positions(text: str, translator: LiblouisTranslator):
    output: list[str] = []
    positions: list[int] = []
    offset = 0
    for part in re.split(r"( +)", text):
        if part and part[0] == " ":
            output.append("\u2800" * len(part))
            positions.extend(range(offset, offset + len(part)))
        elif part:
            cells, local_positions = translator.translate_prose_with_positions(part)
            output.append(cells)
            positions.extend(offset + position for position in local_positions)
        offset += len(part)
    return "".join(output), tuple(positions)


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
        source_rule="4.1; 8.3.1-3",
        source_page="41-44; 89-90 (PDF pp. 69-72; 117-118)",
        source_construct=construct,
        original_cells=cells,
        expected_cells=cells,
        corrected_cells=cells,
        justification="ICEB UEB 2024 is the authority; vendored Liblouis supplies only the candidate cell translation.",
    )


def _capital_sites(block, translator: LiblouisTranslator):
    words = tuple(_WORDS.finditer(block.source_text))
    if not words:
        return (), None
    if any(
        word.group().isupper() and len(word.group()) > 1
        or any(char.isupper() for char in word.group()[1:])
        for word in words
    ):
        return (), _result(
            block,
            _CAPS_RULE,
            "REVIEW",
            "All-capital and internal-capital words are outside phase-1 capitalization scope.",
            "capitalisation",
            "capitalization outside basic word-initial single-capital scope",
        )

    translated, positions = translate_source_with_positions(block.source_text, translator)
    if translated != block.braille or len(translated) != len(positions):
        return (), _result(
            block,
            _CAPS_RULE,
            "REVIEW",
            "The capitalization source-to-cell map was not deterministic.",
            "capitalisation",
            "unresolved source-to-cell capitalization mapping",
        )
    sites: list[CapitalSite] = []
    for word in words:
        indexes = [index for index, source_offset in enumerate(positions) if source_offset == word.start()]
        if not indexes:
            return (), _result(
                block,
                _CAPS_RULE,
                "REVIEW",
                "The word-initial capitalization cell has no exact source anchor.",
                "capitalisation",
                "unresolved word-initial capitalization anchor",
            )
        start = indexes[0]
        uppercase = word.group()[0].isupper()
        following = start + int(uppercase)
        if following >= len(translated) or positions[following] != word.start():
            return (), _result(
                block,
                _CAPS_RULE,
                "REVIEW",
                "The word-initial capitalization cell is not a one-letter UEB mapping.",
                "capitalisation",
                "non-single-cell capitalization mapping",
            )
        if uppercase and translated[start] != "⠠":
            return (), _result(
                block,
                _CAPS_RULE,
                "REVIEW",
                "Liblouis did not produce the expected single-capital indicator candidate.",
                "capitalisation",
                "unexpected capitalization candidate",
            )
        if not uppercase and translated[start] == "⠠":
            return (), _result(
                block,
                _CAPS_RULE,
                "REVIEW",
                "A lowercase word unexpectedly received a capitalization indicator candidate.",
                "capitalisation",
                "unexpected lowercase capitalization candidate",
            )
        sites.append(CapitalSite(
            word=word.group(),
            source_start=word.start(),
            expected_start=start,
            uppercase=uppercase,
            following_cell=ord(translated[following]) - 0x2800,
        ))
    return tuple(sites), _result(
        block,
        _CAPS_RULE,
        "PASS",
        "Basic word-initial single-capital sites are source-mapped in regular uncontracted UEB prose.",
        "capitalisation",
        "word-initial single capitalization",
    ) if any(site.uppercase for site in sites) else None


def verify_document(document, translator: LiblouisTranslator):
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
                    "The source contains unsupported phase-1 material; no confirmed error is emitted.",
                    "scope",
                    "unsupported source construct",
                ),)))
                continue
            sites, cap_result = _capital_sites(block, translator)
            if cap_result is not None and cap_result.status == "REVIEW":
                blocks.append(replace(
                    block,
                    rule_status="REVIEW",
                    rule_results=(_result(
                        block,
                        _SCOPE_RULE,
                        "PASS",
                        "Letters and ordinary spaces are within phase-1 source scope.",
                        "scope",
                        "English letters and ordinary spaces",
                    ), cap_result),
                    capital_sites=(),
                ))
                continue
            results = [_result(
                block,
                _SCOPE_RULE,
                "PASS",
                "English letters and ordinary spaces translated as uncontracted UEB.",
                "scope",
                "English letters and ordinary spaces",
            )]
            if cap_result is not None:
                results.append(cap_result)
            blocks.append(replace(
                block,
                rule_status="PASS",
                rule_results=tuple(results),
                capital_sites=sites,
            ))
        pages.append(replace(page, blocks=tuple(blocks)))
    return replace(document, pages=tuple(pages))
