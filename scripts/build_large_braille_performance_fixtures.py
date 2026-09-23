"""Build deterministic, text-based Braille PDFs for the CPU audit.

The fixture source is intentionally ordinary current-production input.  The
PDF is rendered from the application's generated Braille, then its ToUnicode
map is changed to the existing NABCC-compatible representation so the normal
PDF reader/provenance path is exercised.  No production module is modified.
"""

from __future__ import annotations

from hashlib import sha256
import io
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

OUT = ROOT / "stress_test" / "large_documents"
SIZES = (50, 100, 250, 500)
LINES_PER_PAGE = 26
SEED = 20260921


def _source_line(page: int, line: int) -> str:
    label = f"{page:04d} {line:02d}"
    if line == 2:
        return f"Addition {label}: [[*ts*]]2 + 3 = 5[[*te*]] today."
    if line == 3:
        return f"Subtraction {label}: [[*ts*]]8 + 3 = 11[[*te*]] today."
    if line == 4:
        return f"Multiplication {label}: [[*ts*]]4 × 3 = 12[[*te*]] today."
    if line == 5:
        return f"Equality {label}: [[*ts*]]x + y = z[[*te*]] today."
    if line == 6:
        return f"Dates {label}: The review uses page {page} and line {line}."
    if line == 7:
        return f"Numbers {label}: 12,345.67 and 09:30 remain ordinary text."
    words = ("alpha", "beta", "gamma", "delta", "epsilon", "theta")
    first = words[(page + line) % len(words)]
    second = words[(page * 3 + line) % len(words)]
    return f"Sample {label}: {first} {second} gamma delta."


def make_master(page_count: int) -> dict:
    return {
        "pages": [
            {
                "print_page_number": page,
                "blocks": [
                    {"type": "body", "text": _source_line(page, line)}
                    for line in range(LINES_PER_PAGE)
                ],
            }
            for page in range(1, page_count + 1)
        ]
    }


def _rewrite_tounicode(buffer: io.BytesIO):
    from pypdf import PdfReader
    from pypdf.generic import DecodedStreamObject, NameObject
    from braille_app.translation.braille_cells import BRF_DOTS, char_mask

    reader = PdfReader(buffer)
    canonical = {
        char_mask(char, "duxbury"): char.upper() if char.isalpha() else char
        for char in BRF_DOTS
    }
    for page in reader.pages:
        for ref in page["/Resources"]["/Font"].values():
            font = ref.get_object()
            if "/ToUnicode" not in font:
                continue
            original = font["/ToUnicode"].get_object().get_data().decode("ascii")

            def remap(match):
                codepoint = int(match[2], 16)
                if not 0x2800 <= codepoint < 0x2840:
                    return match[0]
                mapped = canonical.get(chr(codepoint))
                if mapped is None:
                    return match[0]
                return f"{match[1]}<{ord(mapped):04X}>"

            stream = DecodedStreamObject()
            stream.set_data(
                re.sub(
                    r"(<[0-9A-Fa-f]+>\s*)<([0-9A-Fa-f]{4})>",
                    remap,
                    original,
                ).encode("ascii")
            )
            font[NameObject("/ToUnicode")] = stream
    return reader


def write_braille_pdf(path: Path, pages: list[list[str]]) -> None:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas
    from pypdf import PdfWriter

    try:
        pdfmetrics.getFont("PerformanceBraille")
    except KeyError:
        pdfmetrics.registerFont(
            TTFont("PerformanceBraille", "C:/Windows/Fonts/seguisym.ttf")
        )

    raw = io.BytesIO()
    document = canvas.Canvas(raw, pagesize=(612, 792))
    for rows in pages:
        document.setFont("PerformanceBraille", 16)
        for line, row in enumerate(rows):
            document.drawString(40, 748 - line * 26, row)
        document.showPage()
    document.save()

    reader = _rewrite_tounicode(raw)
    writer = PdfWriter()
    writer.append(reader)
    with path.open("wb") as stream:
        writer.write(stream)


def _mutate_row(row: str, family: str) -> tuple[str, int]:
    replacements = {
        "PLUS": ("⠬", "⠈"),
        "MINUS": ("⠬", "⠈"),
        "MULTIPLY": ("⠡", "⠌"),
        "EQUALS": ("⠨⠅", "⠨⠌"),
        "CAPITALIZATION": ("⠠", "⠐"),
    }
    old, new = replacements[family]
    index = row.find(old)
    if index < 0:
        raise AssertionError(f"{family} mutation not found in {row!r}")
    mutated = row[:index] + new + row[index + len(old) :]
    return mutated, index


def _corruption_manifest(expected_pages: list[list[str]], page_count: int) -> tuple[list[list[str]], list[dict]]:
    target_pages = [
        1,
        round((page_count - 1) * 0.25) + 1,
        round((page_count - 1) * 0.50) + 1,
        round((page_count - 1) * 0.75) + 1,
        page_count,
    ]
    families = ("PLUS", "MINUS", "MULTIPLY", "EQUALS", "CAPITALIZATION")
    corrupted = [list(rows) for rows in expected_pages]
    entries = []
    for page, family in zip(target_pages, families):
        line = {"PLUS": 2, "MINUS": 3, "MULTIPLY": 4, "EQUALS": 5, "CAPITALIZATION": 0}[family]
        old_row = corrupted[page - 1][line]
        new_row, cell_index = _mutate_row(old_row, family)
        corrupted[page - 1][line] = new_row
        entries.append(
            {
                "fixture_page": page,
                "line_index_zero_based": line,
                "cell_index_zero_based": cell_index,
                "family": family,
                "original_braille": old_row,
                "corrupted_braille": new_row,
                "source_text": _source_line(page, line),
                "expected_category": "NEMETH_ERROR" if family != "CAPITALIZATION" else "UEB_ERROR",
                "expected_finding": "one-cell mutation at the named source location",
            }
        )
    return corrupted, entries


def _docx(path: Path, master: dict) -> None:
    from docx import Document

    document = Document()
    for page_index, page in enumerate(master["pages"]):
        document.add_paragraph(f"=== PAGE {page['print_page_number']} ===")
        for block in page["blocks"]:
            document.add_paragraph(block["text"])
        if page_index + 1 < len(master["pages"]):
            document.add_page_break()
    document.save(path)


def _sha(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_one(page_count: int) -> dict:
    from braille_app.translation.expected_document import generate_expected_braille

    master = make_master(page_count)
    expected = generate_expected_braille(master)
    expected_pages = [[block.braille for block in page.blocks] for page in expected.pages]
    corrupted_pages, mutations = _corruption_manifest(expected_pages, page_count)
    stem = f"performance_braille_{page_count:03d}_pages"
    master_stem = f"performance_master_{page_count:03d}_pages"
    OUT.mkdir(parents=True, exist_ok=True)
    master_json = OUT / f"{master_stem}.json"
    master_json.write_text(json.dumps(master, ensure_ascii=False, indent=2), encoding="utf-8")
    _docx(OUT / f"{master_stem}.docx", master)
    write_braille_pdf(OUT / f"{stem}.pdf", expected_pages)
    write_braille_pdf(OUT / f"{stem}_corrupted.pdf", corrupted_pages)
    manifest = {
        "seed": SEED,
        "fixture": stem,
        "pages": page_count,
        "lines_per_page": LINES_PER_PAGE,
        "master_json": master_json.name,
        "master_docx": f"{master_stem}.docx",
        "clean_pdf": f"{stem}.pdf",
        "corrupted_pdf": f"{stem}_corrupted.pdf",
        "mutations": mutations,
    }
    manifest_path = OUT / f"{stem}_corruption_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "pages": page_count,
        "files": {
            name: {"path": str(OUT / name), "sha256": _sha(OUT / name)}
            for name in (master_json.name, f"{master_stem}.docx", f"{stem}.pdf", f"{stem}_corrupted.pdf", manifest_path.name)
        },
        "mutation_count": len(mutations),
    }


def main() -> None:
    summary = {"seed": SEED, "sizes": [build_one(size) for size in SIZES]}
    (OUT / "performance_fixture_manifest.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
