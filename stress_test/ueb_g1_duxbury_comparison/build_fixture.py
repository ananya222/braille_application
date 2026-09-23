"""Build the frozen five-page Liblouis/Duxbury comparison corpus.

Audit-only code.  It deliberately imports the existing vendored Liblouis
adapter and does not alter production validation behavior.
"""

from __future__ import annotations

import csv
import hashlib
import html
import json
from pathlib import Path
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "stress_test" / "ueb_g1_duxbury_comparison"
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


PAGES = [
    [
        "Page 1 English letters and ordinary words",
        "Lowercase alphabet: a b c d e f g h i j k l m n o p q r s t u v w x y z",
        "Uppercase alphabet: A B C D E F G H I J K L M N O P Q R S T U V W X Y Z",
        "Ordinary words: hello braille validator ordinary education computer.",
        "Capitalized words: Hello Braille Validator Education.",
        "Isolated capitals: A B D Z I O.",
        "Acronyms and consecutive capitals: NASA UEB PDF ABC.",
        "Sentence starts and punctuation adjacency: Hello, Braille. Validator! Education?",
        "A small ordinary English paragraph keeps the letters easy to compare.",
    ],
    [
        "Page 2 numeric context and spaces",
        "Digits and forms: 3 22 101 1,234 12.50 50% 3:30 21st 2024.",
        "Letters near numbers: 3-D 22b 22B Room 101 Version 2B.",
        "Numeric and letter contexts: 1a 1b 1j 1k 1z 1A 1K.",
        "Audited numeric-space examples: 1 234 and 12 345 remain source spaces.",
        "Ordinary sentence: Room 101 opens at 3:30 on the 21st of June.",
        "Currency and percent context: $25 costs 50% less than $50.",
        "Near-neighbor wording: one two three, 1 2 3, and 123 are distinct inputs.",
    ],
    [
        "Page 3 punctuation quotes and apostrophes",
        "Common punctuation: . , ; : ! ? - ( ) [ ] { } / \\ + = * @ # $ % &",
        "Quote contexts: 'hello' and \"hello\" sit beside ordinary words.",
        "Nested quotation: She said, “Read ‘Peter Rabbit’ again.”",
        "Internal punctuation: a.b a,b a/b a-b a+b a=b.",
        "Apostrophe contexts: don't can't children's teachers' words.",
        "Punctuation adjacency: Hello,world; test:done! Is this correct?",
        "A short paragraph tests punctuation without changing the source words.",
    ],
    [
        "Page 4 symbols and Grade 1 contexts",
        "Common symbols: A & B, me@site.com, © 2024 Example, UEB® and ™.",
        "Currency and units: $25 £10 €9 ¥100, 20°C, 5′ 6″, § 7, 50%, • item.",
        "Letters standing alone: a b c d e f g h i j k l m n o p q r s t u v w x y z.",
        "Grade 1 context probes: 1a 1b 1j 1k 1z; A 1A; punctuation between a.b and a/b.",
        "Indicators near capitals: A 3 B 22B and a word after a number.",
        "The same symbol can be adjacent to a word, a capital, or a number.",
        "This page is evidence for policy decisions, not a standards oracle by itself.",
    ],
    [
        "Page 5 hard interactions typeforms and whitespace",
        "A realistic mix combines Hello Braille, Room 101, 50%, and A.B in one sentence.",
        "Typeform samples: Bold Braille, Italic Validator, and Underline Education.",
        "Typeform with punctuation and numbers: Bold, Italic 22B, and Underline!",
        "Passage-like wording: The Braille validator checks a complete English sentence.",
        "Whitespace policy labels: two  spaces, a\u00a0nonbreaking space, a\u2009thin space, and a\u200bzero-width space.",
        "Unsupported whitespace is retained in this source so the comparison can expose policy differences.",
        "Final mixed case: NASA reads ‘Braille’ at 3:30; Room 101 is ready.",
    ],
]


CASES = [
    ("P1-ALPHA-LOWER", 1, PAGES[0][1], "alphabet", "4.1.1-4.1.3", "lowercase alphabet coverage"),
    ("P1-ALPHA-UPPER", 1, PAGES[0][2], "alphabet", "4.1.1-4.1.3", "uppercase alphabet coverage"),
    ("P1-WORDS", 1, PAGES[0][3], "ordinary words", "4.1.1-4.1.3", "ordinary English word coverage"),
    ("P1-CAPS-WORDS", 1, PAGES[0][4], "capitalization", "8.1.1-8.3.3", "basic word-initial capitalization"),
    ("P1-ISOLATED-CAPS", 1, PAGES[0][5], "capitalization", "8.1.1-8.3.3", "isolated single capitals"),
    ("P1-ACRONYMS", 1, PAGES[0][6], "capitalization", "8.3.1-8.3.3", "consecutive capitals and acronyms"),
    ("P1-PUNCT-ADJ", 1, PAGES[0][7], "punctuation adjacency", "7.1.1-7.6.15", "capital and punctuation adjacency"),
    ("P1-PROSE", 1, PAGES[0][8], "ordinary words", "4.1.1-4.1.3", "natural prose control"),
    ("P2-NUMERIC-FORMS", 2, PAGES[1][1], "numeric context", "6.1.1-6.6.2", "digits, decimals, dates, times, ordinals"),
    ("P2-LETTER-NEAR-NUM", 2, PAGES[1][2], "numeric context", "5.8.1; 6.5.4", "letters immediately near numbers"),
    ("P2-G1-CONTEXT", 2, PAGES[1][3], "Grade 1 context", "5.8.1; 6.5.4", "numeric to Grade 1 interactions"),
    ("P2-NUMERIC-SPACES", 2, PAGES[1][4], "numeric spaces", "6.1.1-6.6.2", "semantic numeric spaces"),
    ("P2-NUMERIC-SENTENCE", 2, PAGES[1][5], "numeric context", "6.1.1-6.6.2", "natural numeric prose"),
    ("P2-CURRENCY-PERCENT", 2, PAGES[1][6], "numeric context", "6.1.1-6.6.2; 7.6.1", "currency and percent adjacency"),
    ("P2-NEAR-NEIGHBORS", 2, PAGES[1][7], "numeric context", "6.1.1-6.6.2", "word and digit near-neighbors"),
    ("P3-PUNCT-ALL", 3, PAGES[2][1], "punctuation", "7.1.1-7.6.15", "common punctuation inventory"),
    ("P3-QUOTES-ASCII", 3, PAGES[2][2], "quotes", "7.6.2; 7.6.9", "ASCII quote contexts"),
    ("P3-QUOTES-NESTED", 3, PAGES[2][3], "quotes", "7.6.2; 7.6.9", "nested single and double quotes"),
    ("P3-PUNCT-INTERNAL", 3, PAGES[2][4], "punctuation", "7.1.1-7.6.15", "punctuation between letters"),
    ("P3-APOSTROPHES", 3, PAGES[2][5], "apostrophes", "7.6.13; 7.6.15", "internal and standing apostrophes"),
    ("P3-PUNCT-ADJ", 3, PAGES[2][6], "punctuation adjacency", "7.1.1-7.6.15", "punctuation without surrounding spaces"),
    ("P3-PROSE", 3, PAGES[2][7], "ordinary words", "4.1.1-4.1.3", "punctuation prose control"),
    ("P4-SYMBOLS", 4, PAGES[3][1], "symbols", "3.1.1-3.23; 7.6.1", "common symbols beside words"),
    ("P4-UNITS", 4, PAGES[3][2], "symbols", "3.1.1-3.23; 7.6.1", "currency, units, section and bullet"),
    ("P4-STANDING", 4, PAGES[3][3], "Grade 1 context", "5.8.1-5.10", "standing-alone letters"),
    ("P4-G1-PROBES", 4, PAGES[3][4], "Grade 1 context", "5.8.1; 5.10; 6.5.4", "Grade 1 indicator contexts"),
    ("P4-CAP-NEAR-NUM", 4, PAGES[3][5], "capitalization and numeric", "6.5.4; 8.3.1-8.3.3", "capital near numeric indicator"),
    ("P4-SYMBOL-ADJ", 4, PAGES[3][6], "symbols", "3.1.1-3.23", "symbol adjacency policy"),
    ("P4-POLICY", 4, PAGES[3][7], "policy", "ICEB UEB 2024", "evidence boundary"),
    ("P5-MIX", 5, PAGES[4][1], "hard interaction", "4.1.1-4.1.3; 6.1.1-6.6.2; 8.3.1-8.3.3", "realistic mixed sentence"),
    ("P5-TYPEFORMS", 5, PAGES[4][2], "typeforms", "9.1.1-9.8.2", "bold italic underline source runs"),
    ("P5-TYPE-NUM-PUNCT", 5, PAGES[4][3], "typeforms", "9.1.1-9.8.2; 6.1.1-6.6.2", "typeform with punctuation and numbers"),
    ("P5-PASSAGE", 5, PAGES[4][4], "capitalization passage", "8.4.1-8.5.3", "passage-like wording"),
    ("P5-WHITESPACE", 5, PAGES[4][5], "whitespace", "3.23", "ordinary, NBSP, thin and zero-width spaces"),
    ("P5-WHITESPACE-POLICY", 5, PAGES[4][6], "whitespace", "3.23", "explicit unsupported whitespace policy"),
    ("P5-MIX-FINAL", 5, PAGES[4][7], "hard interaction", "7.6.2; 6.1.1-6.6.2; 8.3.1-8.3.3", "final mixed control"),
]


def _xml(value: str) -> str:
    return html.escape(value, quote=True)


def write_text() -> None:
    (OUT / "ueb_g1_5page_stress.txt").write_text(
        "\n\n".join("\n".join(page) for page in PAGES) + "\n", encoding="utf-8"
    )


def write_manifest() -> None:
    with (OUT / "source_case_manifest.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["case_id", "source_text", "page", "rule_family", "iceb_ueb_2024_citation", "purpose"])
        writer.writerows(CASES)


def _run(text: str, *, bold: bool = False, italic: bool = False, underline: bool = False) -> str:
    props = []
    if bold:
        props.append("<w:b/>")
    if italic:
        props.append("<w:i/>")
    if underline:
        props.append('<w:u w:val="single"/>')
    rpr = f"<w:rPr>{''.join(props)}</w:rPr>" if props else ""
    return f"<w:r>{rpr}<w:t xml:space=\"preserve\">{_xml(text)}</w:t></w:r>"


def _paragraph(text: str, *, heading: bool = False, runs: list[tuple[str, dict]] | None = None) -> str:
    if runs is None:
        runs = [(text, {})]
    body = "".join(_run(value, **options) for value, options in runs)
    style = '<w:pStyle w:val="Heading1"/>' if heading else '<w:pStyle w:val="Normal"/>'
    return f"<w:p><w:pPr>{style}<w:spacing w:after=\"120\"/></w:pPr>{body}</w:p>"


def write_docx() -> None:
    body: list[str] = []
    for page_number, page in enumerate(PAGES, 1):
        body.append(_paragraph(page[0], heading=True))
        for line in page[1:]:
            if page_number == 5 and line.startswith("Typeform samples:"):
                body.append(_paragraph("", runs=[("Typeform samples: ", {}), ("Bold Braille", {"bold": True}), (", ", {}), ("Italic Validator", {"italic": True}), (", and ", {}), ("Underline Education", {"underline": True}), (".", {})]))
            elif page_number == 5 and line.startswith("Typeform with"):
                body.append(_paragraph("", runs=[("Typeform with punctuation and numbers: ", {}), ("Bold,", {"bold": True}), (" ", {}), ("Italic 22B,", {"italic": True}), (" and ", {}), ("Underline!", {"underline": True})]))
            else:
                body.append(_paragraph(line))
        if page_number != len(PAGES):
            body.append("<w:p><w:r><w:br w:type=\"page\"/></w:r></w:p>")

    document = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:body>{''.join(body)}
<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="900" w:right="900" w:bottom="900" w:left="900"/></w:sectPr>
</w:body></w:document>'''
    styles = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:rPr><w:rFonts w:ascii="Aptos" w:hAnsi="Aptos"/><w:sz w:val="22"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:uiPriority w:val="9"/><w:qFormat/><w:rPr><w:b/><w:sz w:val="30"/></w:rPr></w:style>
</w:styles>'''
    content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>'''
    rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'''
    doc_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>'''
    with zipfile.ZipFile(OUT / "ueb_g1_5page_stress.docx", "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("word/document.xml", document)
        archive.writestr("word/styles.xml", styles)
        archive.writestr("word/_rels/document.xml.rels", doc_rels)


def write_liblouis() -> None:
    from braille_app.translation.liblouis_translator import LiblouisTranslator, vendored_metadata
    from braille_app.translation.profiles import UNCONTRACTED_UEB_PHASE1
    from braille_app.translation.braille_cells import BRF_DOTS, char_mask

    metadata = vendored_metadata(UNCONTRACTED_UEB_PHASE1)
    metadata["unicode_dis_sha256"] = hashlib.sha256(
        Path(metadata["display_table_path"]).read_bytes()
    ).hexdigest()
    metadata["source_document_sha256"] = hashlib.sha256(
        (OUT / "ueb_g1_5page_stress.txt").read_bytes()
    ).hexdigest()
    (OUT / "liblouis_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    translator = LiblouisTranslator(UNCONTRACTED_UEB_PHASE1)
    translated_pages = []
    for page in PAGES:
        translated_pages.append("\n".join(translator.translate_prose(line) for line in page))
    raw = "\f\n".join(translated_pages) + "\n"
    (OUT / "liblouis_output.txt").write_text(raw, encoding="utf-8")

    reverse: dict[int, str] = {}
    for char in BRF_DOTS:
        reverse.setdefault(char_mask(char, "duxbury"), char.upper() if char.isalpha() else char)
    brf: list[str] = []
    for char in raw:
        if char in "\r\n\f":
            brf.append(char)
        elif char == "\u2800":
            brf.append(" ")
        elif 0x2800 <= ord(char) <= 0x28FF:
            mask = ord(char) - 0x2800
            if mask not in reverse:
                raise ValueError(f"No six-dot BRF spelling for Liblouis cell U+{ord(char):04X}")
            brf.append(reverse[mask])
        else:
            raise ValueError(f"Unexpected Liblouis output character {char!r}")
    (OUT / "liblouis_output.brf").write_text("".join(brf), encoding="ascii")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    write_text()
    write_manifest()
    write_docx()
    write_liblouis()
    print(json.dumps({"output": str(OUT), "cases": len(CASES), "pages": len(PAGES)}))


if __name__ == "__main__":
    main()
