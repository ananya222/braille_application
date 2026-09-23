"""Fresh, isolated Liblouis/BRF evidence for the disputed audit cases.

Audit tooling only.  It deliberately calls the vendored binding directly and
does not read the existing Liblouis output or any expected-output artifact.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "stress_test" / "ueb_g1_duxbury_comparison"
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from braille_app.translation.braille_cells import ascii_to_cells, cells_to_unicode
from braille_app.translation.liblouis_translator import (
    VENDOR_DLL,
    VENDOR_TABLES,
    load_liblouis,
)

TABLE_LIST = ["unicode.dis", "en-ueb-g1.ctb"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_codepoints(value: str) -> list[str]:
    return [f"U+{ord(ch):04X}" for ch in value]


def dots(value: str) -> list[str]:
    result = []
    for ch in value:
        bits = ord(ch) - 0x2800
        result.append("0" if bits == 0 else "".join(str(i) for i in range(1, 9) if bits & (1 << (i - 1))))
    return result


def liblouis_case(louis, source: str) -> dict[str, object]:
    # Exact API invocation under audit: louis.translateString(table_list, source),
    # with no translation options or mode flags.
    output = louis.translateString(TABLE_LIST, source)
    return {
        "source": source,
        "source_codepoints": source_codepoints(source),
        "api_call": "louis.translateString([\"unicode.dis\", \"en-ueb-g1.ctb\"], source)",
        "table_list": TABLE_LIST,
        "options_mode": "default translateString options; no flags or mode",
        "output_unicode": output,
        "output_codepoints": [f"U+{ord(ch):04X}" for ch in output],
        "output_dots": dots(output),
    }


def dxb_contexts() -> dict[str, dict[str, object]]:
    raw = (HERE / "ueb_g1_5page_stress.brf").read_text(encoding="ascii")
    # BRF line wrapping is layout only; join wrapped lines with one blank so
    # the requested logical cell substring can cross a physical line break.
    logical = " ".join(line.strip() for line in raw.splitlines() if line.strip())
    wanted = {
        "3-D": "#C-,D",
        "a,b": "INTERNAL PUNCTUATION3 A4B A1B",
        "a.b": "INTERNAL PUNCTUATION3 A4B",
        "'hello'": "'HELLO'",
        "nested quotation": ",SHE SAID1 8,READ ,8,PETER ,RABBIT,0 AGAIN40",
    }
    result = {}
    for name, needle in wanted.items():
        marker = needle
        if name == "a,b":
            marker = "A1B"
            start = logical.find(needle) + len("INTERNAL PUNCTUATION3 A4B ")
        elif name == "a.b":
            marker = "A4B"
            start = logical.find(needle) + len("INTERNAL PUNCTUATION3 ")
        else:
            start = logical.find(needle)
        if start < 0:
            raise AssertionError(f"BRF needle not found: {name}: {needle!r}")
        brf = marker
        cells = ascii_to_cells(brf, "duxbury")
        result[name] = {
            "needle": needle,
            "brf_context": logical[max(0, start - 30):start + len(needle) + 30],
            "brf_substring": brf,
            "unicode": cells_to_unicode(cells),
            "dots": dots(cells_to_unicode(cells)),
        }
    return result


def main() -> None:
    louis = load_liblouis()
    cases = {
        "isolated": {
            "3-D": "3-D",
            "a,b": "a,b",
            "a.b": "a.b",
            "ASCII single quote pair": "'hello'",
            "curly single quote pair": "‘hello’",
            "coverage nested quotation": "“She said, ‘yes’.”",
            "Duxbury nested quotation": "She said, “Read ‘Peter Rabbit’ again.”",
        },
        "ordinary_sentence_context": {
            "3-D": "The model is 3-D.",
            "a,b": "The token a,b is adjacent.",
            "a.b": "The abbreviation a.b is adjacent.",
            "ASCII single quote pair": "The word 'hello' is ordinary.",
            "curly single quote pair": "The word ‘hello’ is ordinary.",
            "nested quotation": "She said, “Read ‘Peter Rabbit’ again.”",
        },
        "coverage_closure_exact": {
            "3-D": "3-D",
            "a,b": "a,b",
            "a.b": "a.b",
            "ASCII single quote pair": "'hello'",
            "curly single quote pair": "‘hello’",
            "nested quotation": "“She said, ‘yes’.”",
        },
        "duxbury_corpus_exact": {
            "3-D": "Letters near numbers: 3-D 22b 22B Room 101 Version 2B.",
            "a,b": "Internal punctuation: a.b a,b a/b a-b a+b a=b.",
            "a.b": "Internal punctuation: a.b a,b a/b a-b a+b a=b.",
            "ASCII single quote pair": "Quote contexts: 'hello' and \"hello\" sit beside ordinary words.",
            "curly single quote pair": "Nested quotation: She said, “Read ‘Peter Rabbit’ again.”",
            "nested quotation": "Nested quotation: She said, “Read ‘Peter Rabbit’ again.”",
        },
    }
    translations = {
        context: {name: liblouis_case(louis, source) for name, source in values.items()}
        for context, values in cases.items()
    }
    result = {
        "runtime": {
            "version": str(louis.version()).strip(),
            "dll_path": str(VENDOR_DLL.resolve()),
            "table_path": str((VENDOR_TABLES / "en-ueb-g1.ctb").resolve()),
            "table_hash_sha256": sha256(VENDOR_TABLES / "en-ueb-g1.ctb"),
            "unicode_dis_hash_sha256": sha256(VENDOR_TABLES / "unicode.dis"),
            "table_list": TABLE_LIST,
        },
        "translations": translations,
        "duxbury_brf": dxb_contexts(),
    }
    out = HERE / "reconciliation_fresh_raw.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
