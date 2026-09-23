"""Emit deterministic Case 2 Liblouis capitalization probes."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from braille_app.translation.liblouis_translator import LiblouisTranslator, vendored_metadata
from braille_app.translation.profiles import UNCONTRACTED_UEB_CASE2


CASES = (
    ("isolated capital A", "A", "8.1.1; 8.3.1"),
    ("isolated capital B", "B", "8.1.1; 8.3.1"),
    ("isolated capital Z", "Z", "8.1.1; 8.3.1"),
    ("capitalized Hello", "Hello", "8.1.1; 8.3.1"),
    ("capitalized Braille", "Braille", "8.1.1; 8.3.1"),
    ("capitalized Validator", "Validator", "8.1.1; 8.3.1"),
    ("capitalized Education", "Education", "8.1.1; 8.3.1"),
    ("all-cap NASA", "NASA", "8.1.1; 8.4.1-2"),
    ("all-cap UEB", "UEB", "8.1.1; 8.4.1-2"),
    ("all-cap PDF", "PDF", "8.1.1; 8.4.1-2"),
    ("all-cap ABC", "ABC", "8.1.1; 8.4.1-2"),
    ("repeated isolated capitals", "A B D Z", "8.3.1; 8.5.1-3; 8.6.1"),
    ("capital passage", "THIS IS ALL CAPS", "8.4.1-2; 8.5.1-3; 8.6.1"),
    ("capitalized repeated words", "Hello Hello Hello", "8.1.1; 8.3.1"),
    ("all-cap next to lowercase", "NASA hello", "8.4.1-2"),
    ("lowercase next to all-cap", "hello NASA", "8.4.1-2"),
    ("internal iPhone", "iPhone", "8.1.1; 8.3.1; 8.4.1-2"),
    ("internal eBay", "eBay", "8.1.1; 8.3.1; 8.4.1-2"),
    ("internal McDonald", "McDonald", "8.1.1; 8.3.1; 8.4.1-2"),
    ("mixed ordinary sentence", "Hello NASA UEB PDF ABC hello", "8.1.1; 8.4.1-2; 8.5.1-3; 8.6.1"),
    ("source beginning and end", "Hello", "8.1.1; 8.3.1"),
)


def dots(value: str) -> list[str]:
    return ["".join(str(dot) for dot in range(1, 9) if (ord(char) - 0x2800) & (1 << (dot - 1))) or "blank" for char in value]


def main() -> None:
    translator = LiblouisTranslator(UNCONTRACTED_UEB_CASE2)
    metadata = vendored_metadata(UNCONTRACTED_UEB_CASE2)
    rows = []
    for label, source, citation in CASES:
        output, positions = translator.translate_prose_with_positions(source)
        rows.append({
            "label": label,
            "source": source,
            "source_codepoints": [f"U+{ord(char):04X}" for char in source],
            "citation": citation,
            "liblouis_call": "louis.translate([\"unicode.dis\", \"en-ueb-g1.ctb\"], source)",
            "translation_call": "LiblouisTranslator.translate_prose_with_positions(source)",
            "output": output,
            "output_codepoints": [f"U+{ord(char):04X}" for char in output],
            "dots": dots(output),
            "positions": list(positions),
            "assessment": "PASS",
            "custom_handling": "none",
        })
    payload = {"metadata": metadata, "cases": rows}
    encoded = json.dumps(payload, ensure_ascii=False, indent=2)
    output_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if output_path:
        output_path.write_text(encoded + "\n", encoding="utf-8")
    print(encoded.encode("ascii", "backslashreplace").decode("ascii"))


if __name__ == "__main__":
    main()
