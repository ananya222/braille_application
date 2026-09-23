"""Fresh, isolated vendored-Liblouis probes for the Case 3 rules audit."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from braille_app.translation.braille_cells import dots_for_cells, unicode_to_cells
from braille_app.translation.liblouis_translator import LiblouisTranslator, vendored_metadata
from braille_app.translation.profiles import UNCONTRACTED_UEB_CASE2


CASES = (
    ("digits", "0123456789", "6.2.1"),
    ("grouped integer", "4 500 000", "6.6.1"),
    ("grouped integer in sentence", "The total is 4 500 000 today.", "6.6.1"),
    ("other clear grouping", "3 245 000", "6.6.1"),
    ("date numeric spaces", "date 1947 08 31", "6.6.1; 6.7.1"),
    ("time numeric spaces", "time 16 00", "6.6.1; 6.7.1"),
    ("ISBN numeric spaces", "ISBN 978 1 55468 513 4", "6.6.1; 6.7.1"),
    ("phone numeric spaces", "phone 61 3 1234 5678", "6.6.1; 6.7.1"),
    ("non-grouping space", "4 5", "6.6.1"),
    ("irregular grouped-looking spaces", "77 777 77", "6.6.1"),
    ("comma decimal", "3,500", "6.2.1"),
    ("period decimal", "8.93", "6.2.1"),
    ("leading period", ".7", "6.2.1"),
    ("leading comma", ",7", "6.2.1"),
    ("digit then lowercase a-j", "3b", "6.5.2"),
    ("digit then uppercase", "3B", "6.5.2"),
    ("digit then k", "3k", "6.5.2"),
    ("period then lowercase a-j", "4.b", "6.5.2"),
    ("period then uppercase", "4.B", "6.5.2"),
    ("period before following number", "No. 4", "6.4.1"),
    ("hyphen then capital single letter", "3-D", "6.5.4; 5.8.1"),
    ("hyphen then lowercase single letter", "4-m", "6.5.4"),
    ("hyphen then capital abbreviation", "6-CD", "6.5.4; 5.8.1"),
    ("hyphen then yr", "20-yr", "6.5.4"),
    ("hyphen then full ordinary word", "4-bed", "6.5.4"),
    ("hyphen then can", "6-can", "6.5.4"),
    ("same letters without hyphen", "20yr", "6.5.4"),
    ("full word after hyphen", "3-dimensional", "6.5.4"),
    ("numeric-mode termination", "9-10", "6.3.1"),
    ("numeric-mode termination at dash", "9–10", "6.3.1; 6.5.1"),
    ("number ordinals", "1st 2nd", "6.7.1"),
    ("whole-sentence context", "The 3-D model costs 4-m each.", "6.5.4"),
    ("mixed suffix context", "Use a 6-CD case for 20-yr records.", "6.5.4"),
)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    translator = LiblouisTranslator(UNCONTRACTED_UEB_CASE2)
    metadata = vendored_metadata(UNCONTRACTED_UEB_CASE2)
    records = []
    for label, source, citation in CASES:
        translated, positions = translator.translate_prose_with_positions(source)
        records.append({
            "case": label,
            "source": source,
            "source_codepoints": [f"U+{ord(char):04X}" for char in source],
            "citation_to_check": citation,
            "api_call": "louis.translate(['unicode.dis', 'en-ueb-g1.ctb'], source) via LiblouisTranslator.translate_prose_with_positions",
            "table_list": metadata["table_list"],
            "options": "default Liblouis options; no extra translation options",
            "mode": "uncontracted English UEB Grade 1 table en-ueb-g1.ctb",
            "unicode_braille": translated,
            "dot_cells": list(dots_for_cells(unicode_to_cells(translated))),
            "source_positions": list(positions),
        })
    print(json.dumps({"runtime": metadata, "cases": records}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
