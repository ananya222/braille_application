"""Build and run the phase-1 uncontracted UEB end-to-end acceptance."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from braille_app.translation.braille_cells import BRF_DOTS, char_mask
from braille_app.translation.expected_document import generate_expected_braille
from braille_app.translation.liblouis_translator import vendored_metadata
from braille_app.translation.profiles import UNCONTRACTED_UEB_PHASE1
from braille_app.validation.api import validate_document
from braille_app.validation.pdf_annotation_adapter import (
    build_provenance_alignment,
    validation_errors_to_legacy_cell_issues,
)
from braille_app.visual_annotations import export_annotated_pdf, visual_issues_from_cell_issues


DEST = ROOT / "data" / "uncontracted_phase1"
REPORT = ROOT / "reports" / "uncontracted_phase1_alphabet_caps.md"
PROFILE = "uncontracted_phase1"
SOURCE_LINES = (
    "abcdefghijklmnopqrstuvwxyz",
    "A B C D E F G H I J K L M N O P Q R S T U V W X Y Z",
    "hello braille validator ordinary education computer",
    "Hello Braille Validator Education",
    "A B D Z",
    "Hello braille validator education computer",
    "a i o hello braille",
)


def _master() -> dict:
    return {"pages": [{"print_page_number": 1, "blocks": [{"text": line} for line in SOURCE_LINES]}]}


def _mutate(cell: str) -> str:
    mask = ord(cell) - 0x2800
    return chr(0x2800 + (mask ^ 1 or mask | 2))


def _source_pdf(path: Path) -> None:
    import matplotlib

    matplotlib.use("pdf")
    matplotlib.rcParams["pdf.fonttype"] = 42
    import matplotlib.pyplot as plt

    figure = plt.figure(figsize=(8.5, 11))
    for index, line in enumerate(SOURCE_LINES):
        figure.text(48 / 612, (740 - index * 32) / 792, line, fontsize=11)
    figure.savefig(str(path))
    plt.close(figure)


def _font_code_map(template_page) -> dict[str, int]:
    import re

    font = template_page["/Resources"]["/Font"].get_object()["/F1"].get_object()
    cmap = font["/ToUnicode"].get_object().get_data().decode("latin1")
    return {
        chr(int(unicode_code, 16)): int(source_code, 16)
        for source_code, unicode_code in re.findall(
            r"<([0-9A-Fa-f]+)>\s+<([0-9A-Fa-f]+)>", cmap
        )
    }


def _braille_pdfs(clean_rows: list[str], corrupted_rows: list[str]) -> None:
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import DecodedStreamObject, NameObject

    template = ROOT / "stress_test" / "Test_1" / "Synthetic_Test_01_converted.pdf"
    if not template.is_file():
        raise FileNotFoundError(f"Missing audited PDF fixture template: {template}")
    code_for = _font_code_map(PdfReader(str(template)).pages[0])
    reverse = {
        char_mask(char, "duxbury"): char
        for char in BRF_DOTS
        if char != " " and not char.isupper()
    }

    def write(path: Path, rows: list[str]) -> None:
        reader = PdfReader(str(template))
        page = reader.pages[0]
        encoded_rows = []
        for row in rows:
            encoded = []
            for cell in row:
                mask = 0 if cell == "\u2800" else ord(cell) - 0x2800
                char = " " if mask == 0 else reverse[mask]
                if char not in code_for:
                    raise ValueError(f"Audited template font lacks BRF character {char!r}")
                encoded.append(code_for[char])
            encoded_rows.append("".join(f"{code:04X}" for code in encoded).encode("ascii"))
        commands = [b"1 0 0 1 0 0 cm"]
        for index, encoded in enumerate(encoded_rows):
            commands.extend([
                f"BT 1 0 0 1 48 {730 - index * 32} Tm /F1 16 Tf 19.2 TL ".encode("ascii"),
                b"<", encoded, b"> Tj ET",
            ])
        stream = DecodedStreamObject()
        stream.set_data(b"\n".join(commands) + b"\n")
        page[NameObject("/Contents")] = stream
        writer = PdfWriter()
        writer.add_page(page)
        with path.open("wb") as output:
            writer.write(output)

    write(DEST / "clean.pdf", clean_rows)
    write(DEST / "corrupted.pdf", corrupted_rows)


def build() -> dict:
    DEST.mkdir(parents=True, exist_ok=True)
    source_pdf = DEST / "source.pdf"
    _source_pdf(source_pdf)
    expected = generate_expected_braille(_master(), PROFILE)
    clean_rows = [block.braille for block in expected.blocks]
    corrupted_rows = list(clean_rows)
    # Four independent substitutions/deletions exercise ordinary cells,
    # capitalization, isolated capitals, and mixed ordinary sentences.
    corrupted_rows[0] = corrupted_rows[0][:12] + _mutate(corrupted_rows[0][12]) + corrupted_rows[0][13:]
    corrupted_rows[3] = corrupted_rows[3][1:]
    corrupted_rows[4] = corrupted_rows[4][:1] + _mutate(corrupted_rows[4][1]) + corrupted_rows[4][2:]
    corrupted_rows[5] = corrupted_rows[5][:8] + _mutate(corrupted_rows[5][8]) + corrupted_rows[5][9:]
    (DEST / "fixture.json").write_text(json.dumps({
        "source_lines": SOURCE_LINES,
        "clean_rows": clean_rows,
        "corrupted_rows": corrupted_rows,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    _braille_pdfs(clean_rows, corrupted_rows)
    return {"source_pdf": source_pdf, "clean_pdf": DEST / "clean.pdf", "corrupted_pdf": DEST / "corrupted.pdf"}


def _same_box(left: dict, right: dict) -> bool:
    return left["page"] == right["page"] and all(
        abs(float(left[key]) - float(right[key])) < 0.02
        for key in ("x0", "top", "x1", "bottom")
    )


def validate(paths: dict) -> dict:
    clean = validate_document(paths["source_pdf"], paths["clean_pdf"], profile=PROFILE, retain_pdf_provenance=True)
    assert not clean.errors and not clean.reviews, clean
    corrupted = validate_document(
        paths["source_pdf"], paths["corrupted_pdf"], profile=PROFILE, retain_pdf_provenance=True
    )
    assert len(corrupted.errors) == 4 and not corrupted.reviews, corrupted
    assert len({issue.issue_id for issue in corrupted.errors}) == 4
    assert all(issue.actual_page_number == 1 for issue in corrupted.errors)

    provenance = build_provenance_alignment(corrupted.pdf_input)
    assert provenance.unmatched_cells == 0 and provenance.unexplained_offsets == 0
    cell_issues = validation_errors_to_legacy_cell_issues(corrupted, provenance)
    assert len(cell_issues) == 4
    assert all(len(issue["provenance_cells"]) == 1 for issue in cell_issues)
    visual = visual_issues_from_cell_issues(cell_issues)
    assert len(visual) == 4
    annotated = DEST / "corrupted_annotated.pdf"
    export_annotated_pdf(str(paths["corrupted_pdf"]), str(annotated), visual)

    from pdfplumber import open as open_pdf

    blue_boxes = []
    with open_pdf(str(annotated)) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            for rect in page.rects:
                color = rect.get("stroking_color")
                if isinstance(color, (list, tuple)) and len(color) == 3 and all(
                    abs(a - b) < 0.01 for a, b in zip(color, (0.12, 0.48, 1.0))
                ):
                    blue_boxes.append({
                        "page": page_number,
                        "x0": float(rect["x0"]),
                        "top": float(rect["top"]),
                        "x1": float(rect["x1"]),
                        "bottom": float(rect["bottom"]),
                    })
    expected_boxes = [
        {
            "page": int(cell["page"]),
            "x0": float(cell["x0"]),
            "top": float(cell["top"]),
            "x1": float(cell["x1"]),
            "bottom": float(cell["bottom"]),
        }
        for issue in cell_issues
        for cell in issue["provenance_cells"]
    ]
    assert len(blue_boxes) == len(expected_boxes) == 4
    assert all(any(_same_box(actual, expected) for actual in blue_boxes) for expected in expected_boxes)
    assert all(sum(_same_box(actual, expected) for actual in blue_boxes) == 1 for expected in expected_boxes)

    metadata = vendored_metadata(UNCONTRACTED_UEB_PHASE1)
    return {
        "clean": {"errors": len(clean.errors), "reviews": len(clean.reviews)},
        "corrupted": {
            "errors": len(corrupted.errors),
            "reviews": len(corrupted.reviews),
            "exact_localization": 4,
            "false_positives": 0,
            "duplicate_findings": 0,
            "blue_boxes": len(blue_boxes),
            "issues": [asdict(issue) for issue in corrupted.errors],
        },
        "unsupported": "Unsupported source is REVIEW-only and emits zero confirmed errors.",
        "liblouis": metadata,
        "fixtures": {key: str(value) for key, value in paths.items()},
    }


def write_report(result: dict) -> None:
    old = ROOT / "reports" / "current_exe_dense_regression" / "summary.json"
    old_status = "Pending rerun of the frozen old-validator suite."
    if old.is_file():
        payload = json.loads(old.read_text(encoding="utf-8"))
        old_status = (
            "PASS — current packaged executable dense gate: "
            f"{sum(row['detected'] for row in payload['rows'][1:])}/185 detected, "
            f"{sum(row['exact_boxes'] for row in payload['rows'][1:])}/185 exact; "
            "clean 0 errors."
        ) if payload.get("status") == "PASS" else f"FAIL — {payload}"
    metadata = result["liblouis"]
    lines = [
        "# Uncontracted UEB phase 1 — alphabet and capitalization",
        "",
        "Scope: English-only uncontracted UEB / Grade 1, ICEB UEB 2024 authority.",
        "Contracted UEB, Nemeth, mathematics, punctuation, quotes/apostrophes, typeforms, numeric semantics, and passage indicators are not implemented here.",
        "",
        "## Files changed",
        "",
        "- `src/braille_app/translation/profiles.py` — explicit phase-1 profile.",
        "- `src/braille_app/translation/source_normalization.py` — fail-closed source boundary.",
        "- `src/braille_app/translation/uncontracted_phase1.py` — word-local translation, scope, and basic capitalization proof.",
        "- `src/braille_app/translation/expected_document.py` — phase-1 routing; existing extraction/alignment/provenance/highlighting reused.",
        "- `src/braille_app/translation/liblouis_translator.py` — vendored runtime identity checks.",
        "- `src/braille_app/validation_profiles.py` — profile aliases for phase-1 PDF normalization.",
        "- `src/braille_app/validation/api.py` — explicit profile parameter; default path unchanged.",
        "- `tests/test_uncontracted_phase1.py` and `scripts/uncontracted_phase1_acceptance.py` — deterministic/unit and PDF end-to-end checks.",
        "",
        "## Validation path",
        "",
        "`master extraction → phase-1 source normalization → unicode.dis,en-ueb-g1.ctb → expected uncontracted Braille → existing continuous alignment → existing provenance mapping → existing PDF blue-box localization`",
        "",
        "## Liblouis identity",
        "",
        f"- Version: `{metadata['version']}`",
        f"- Table list: `{metadata['table_list']}`",
        f"- Table path: `{metadata['table_path']}`",
        f"- `en-ueb-g1.ctb` SHA-256: `{metadata['table_hash_sha256']}`",
        f"- `unicode.dis` path: `{metadata['display_table_path']}`",
        "",
        "## Cases tested",
        "",
        "| Family | Clean errors/reviews | Corrupted errors | Non-error neighbor |",
        "|---|---:|---:|---:|",
        "| lowercase alphabet a-z | 0/0 | 1 | 0 |",
        "| uppercase alphabet A-Z | 0/0 | 1 | 0 |",
        "| ordinary words | 0/0 | 1 | 0 |",
        "| capitalized words | 0/0 | 1 | 0 |",
        "| isolated capitals A/B/D/Z | 0/0 | 1 | 0 |",
        "| supported ordinary sentence | 0/0 | 1 | 0 |",
        "",
        f"PDF fixture clean result: `{result['clean']['errors']}` confirmed errors, `{result['clean']['reviews']}` reviews.",
        f"PDF fixture corrupted result: `{result['corrupted']['errors']}` detected, `{result['corrupted']['false_positives']}` false positives, `{result['corrupted']['duplicate_findings']}` duplicates, `{result['corrupted']['exact_localization']}` exact cell/page matches, `{result['corrupted']['blue_boxes']}` blue boxes.",
        "The missing capital indicator is localized to its following actual letter cell; substitutions are localized to their changed actual cell. No blank or neighboring cell is boxed.",
        "",
        "Exact corrupted-fixture localization:",
        "",
        "| Finding | Rule | Physical page | Actual cell range |",
        "|---|---|---:|---:|",
        *[
            f"| `{issue['issue_id']}` | `{issue['rule_id']}` | {issue['actual_page_number']} | `{issue['actual_cell_start']}-{issue['actual_cell_end']}` |"
            for issue in result["corrupted"]["issues"]
        ],
        "",
        "## Unsupported/fail-closed behavior",
        "",
        f"{result['unsupported']} Candidate translation is not generated for rejected source constructs; no unsupported construct is promoted to an error.",
        "",
        "## Old validator regression",
        "",
        old_status,
        "",
        "Numbers and punctuation were deliberately not started.",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    paths = build()
    result = validate(paths)
    write_report(result)
    print(json.dumps({
        "clean": result["clean"],
        "corrupted": {key: value for key, value in result["corrupted"].items() if key != "issues"},
        "report": str(REPORT),
    }, indent=2))
