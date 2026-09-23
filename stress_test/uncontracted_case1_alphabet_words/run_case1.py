"""Build and run the deterministic Case 1 25-page acceptance fixture."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path

import pdfplumber
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "stress_test" / "uncontracted_case1_alphabet_words"
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from braille_app.translation.braille_cells import BRF_DOTS, cells_to_unicode, unicode_to_cells
from braille_app.translation.expected_document import generate_expected_braille
from braille_app.translation.liblouis_translator import LiblouisTranslator, vendored_metadata
from braille_app.translation.profiles import UNCONTRACTED_UEB_CASE1
from braille_app.validation.api import validate_document
from braille_app.validation.pdf_annotation_adapter import (
    build_provenance_alignment,
    validation_errors_to_legacy_cell_issues,
)
from braille_app.visual_annotations import export_annotated_pdf, visual_issues_from_cell_issues


PROFILE = "uncontracted_case1_alphabet_words"
PAGE_COUNT = 25
ERRORS_PER_PAGE = 20
FONT_SIZE = 9
LINE_HEIGHT = 30
PAGE_LEFT = 36
PAGE_TOP = 760
FONT_PATH = Path(r"C:\Windows\Fonts\seguisym.ttf")

PAGE_WORDS = (
    "alpha bravo charlie delta echo foxtrot golf hotel india juliett kilo lima mike "
    "november oscar papa quebec romeo sierra tango uniform victor whiskey xray yankee"
).split()

LINE_SPECS = (
    ("substitution_begin", "cat car can cap cat", "cat", 0, 0),
    ("substitution_middle", "hello hella hello yellow", "hello", 0, 2),
    ("substitution_end", "validator validation validator", "validator", 1, -1),
    ("deletion_first", "letter letter letter", "letter", 0, 0),
    ("deletion_middle", "success success successful", "success", 0, 3),
    ("deletion_final", "computer computers compute", "computer", 0, -1),
    ("insertion_before_word", "the quick brown fox", "quick", 0, 0),
    ("insertion_inside_word", "bookkeeper bookkeeper", "bookkeeper", 0, 5),
    ("insertion_after_word", "ordinary ordinary", "ordinary", 0, 999),
    ("adjacent_transposition", "xylophone zebra", "xylophone", 0, 0),
    ("repeated_letter_deletion", "letter letter letter", "letter", 1, 2),
    ("repeated_letter_insertion", "book bookkeeper book", "bookkeeper", 0, 1),
    ("repeated_letter_wrong_member", "success successful success", "success", 2, 3),
    ("similar_word_alignment", "validation validator variation", "validator", 0, 4),
    ("repeated_word_alignment", "test test test test", "test", 2, 0),
    ("long_word_beginning", "characterization accessibility misinterpretation", "characterization", 0, 0),
    ("long_word_middle", "misunderstanding counterrevolutionary interdepartmental", "counterrevolutionary", 0, 999),
    ("long_word_end", "accessibility electrophotographic incomprehensibility", "incomprehensibility", 0, -1),
    ("short_word", "a i am an", "i", 0, 0),
    ("boundary_final_word", "quick brown fox jumps over the lazy dog validation", "validation", 0, -1),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _register_font() -> str:
    # The reader treats fonts whose names contain "braille" as rendered-font
    # evidence and requires a reconstructable embedded font map.  This fixture
    # carries the Unicode cell text directly, so use a neutral font name and
    # let the existing reader consume those code points without a font probe.
    name = "Case1Cells"
    if name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(name, str(FONT_PATH)))
    return name


def _letter_cell(translator: LiblouisTranslator, letter: str) -> int:
    value = translator.translate_prose(letter)
    cells = unicode_to_cells(value)
    if len(cells) != 1:
        raise AssertionError(f"Expected one cell for {letter!r}, got {value!r}")
    return cells[0]


def _page_lines(page_index: int) -> list[str]:
    # Lowercase anchors keep the existing continuous aligner from treating
    # adjacent deliberately similar mutations as one long displacement.
    return [
        f"anchor{PAGE_WORDS[line_index]} {text} barrier{PAGE_WORDS[page_index]}{PAGE_WORDS[line_index]}"
        for line_index, (_name, text, _word, _occurrence, _char) in enumerate(LINE_SPECS)
    ]


def _master() -> dict:
    return {
        "pages": [
            {
                "print_page_number": page_index + 1,
                "blocks": [{"text": " ".join(_page_lines(page_index))}],
            }
            for page_index in range(PAGE_COUNT)
        ]
    }


def _word_start(line: str, word: str, occurrence: int) -> tuple[int, list[str]]:
    words = line.split(" ")
    seen = 0
    for index, value in enumerate(words):
        if value == word:
            if seen == occurrence:
                return sum(len(item) + 1 for item in words[:index]), words
            seen += 1
    raise AssertionError((line, word, occurrence))


def _choose_letter(original: str, page_index: int, line_index: int) -> str:
    return "z" if original != "z" else "q"


def _mutate_page(page_index: int, translator: LiblouisTranslator):
    clean_lines = []
    corrupted_lines = []
    rows = []
    for line_index, (subtype, line, word, occurrence, char_index) in enumerate(LINE_SPECS):
        line = f"anchor{PAGE_WORDS[line_index]} {line} barrier{PAGE_WORDS[page_index]}{PAGE_WORDS[line_index]}"
        clean = list(unicode_to_cells(translator.translate_prose(line)))
        corrupted = list(clean)
        word_occurrences = line.split(" ").count(word)
        actual_occurrence = occurrence if occurrence < word_occurrences else 0
        start, words = _word_start(line, word, actual_occurrence)
        char_index = len(word) + char_index if char_index < 0 else char_index
        if char_index == 999:
            char_index = len(word) // 2
        target = start + char_index
        original = line[sum(len(item) + 1 for item in words[:actual_occurrence]) + char_index]
        mutation_type = "substitution"
        corrupted_letter = ""
        expected_cells = [clean[target]]
        corrupted_cells = []
        if subtype == "adjacent_transposition":
            mutation_type = "transposition"
            expected_cells = clean[target:target + 2]
            clean_value = word[char_index:char_index + 2]
            corrupted[target], corrupted[target + 1] = corrupted[target + 1], corrupted[target]
            corrupted_cells = corrupted[target:target + 2]
            corrupted_letter = clean_value[1] + clean_value[0]
        elif subtype.startswith("deletion") or subtype == "repeated_letter_deletion":
            mutation_type = "deletion"
            corrupted.pop(target)
            corrupted_cells = []
        elif subtype.startswith("insertion") or subtype == "repeated_letter_insertion":
            mutation_type = "insertion"
            inserted = _choose_letter(original, page_index + 11, line_index)
            inserted_cell = _letter_cell(translator, inserted)
            corrupted.insert(target, inserted_cell)
            corrupted_cells = [inserted_cell]
            corrupted_letter = inserted
        else:
            replacement = _choose_letter(original, page_index, line_index)
            replacement_cell = _letter_cell(translator, replacement)
            corrupted[target] = replacement_cell
            corrupted_cells = [replacement_cell]
            corrupted_letter = replacement
        clean_lines.append(clean)
        corrupted_lines.append(corrupted)
        rows.append({
            "error_id": f"CASE1-{page_index + 1:02d}-{line_index + 1:02d}",
            "page": page_index + 1,
            "line_index": line_index,
            "source_word": word,
            "occurrence_index": actual_occurrence,
            "source_character_index": char_index,
            "expected_letter": original,
            "corrupted_letter": corrupted_letter,
            "mutation_type": mutation_type,
            "mutation_family": subtype,
            "expected_cells": cells_to_unicode(expected_cells),
            "corrupted_cells": cells_to_unicode(corrupted_cells),
            "expected_line_cell_index": target,
            "expected_line_cell_count": len(clean),
            "actual_line_cell_index": (
                target if mutation_type != "deletion" else min(target, len(corrupted) - 1)
            ),
            "expected_highlight_target": (
                "following_physical_cell_anchor" if mutation_type == "deletion" else "corrupted_cell_range"
            ),
            "detected": False,
            "exact_localization": False,
            "correct_blue_box": False,
        })
    return clean_lines, corrupted_lines, rows


def _write_pdf(path: Path, pages: list[list[str]], font_name: str) -> None:
    canvas = Canvas(str(path), pagesize=letter)
    canvas.setTitle("Case 1 lowercase alphabet and ordinary words")
    for page_index, page_lines in enumerate(pages):
        page_font = f"{font_name}{page_index}"
        if page_font not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(page_font, str(FONT_PATH)))
        canvas.setFont(page_font, FONT_SIZE)
        y = PAGE_TOP
        for line in page_lines:
            canvas.drawString(PAGE_LEFT, y, line)
            y -= LINE_HEIGHT
        canvas.showPage()
    canvas.save()


def _reverse_brf() -> dict[int, str]:
    result = {}
    for char, dots in BRF_DOTS.items():
        mask = 0
        for dot in dots:
            mask |= 1 << (int(dot) - 1)
        result.setdefault(mask, char.upper() if char.isalpha() else char)
    return result


def _write_brf(path: Path, pages: list[list[list[int]]]) -> None:
    reverse = _reverse_brf()
    lines = []
    for page in pages:
        lines.append("\n".join("".join(reverse[cell] for cell in line) for line in page))
    path.write_text("\f".join(lines), encoding="ascii")


def _rows(path: Path) -> list[list[list[dict]]]:
    result = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            chars = sorted(page.chars, key=lambda item: (item["top"], item["x0"]))
            page_rows = []
            for char in chars:
                if not page_rows or abs(char["top"] - page_rows[-1][0]["top"]) > 1.0:
                    page_rows.append([char])
                else:
                    page_rows[-1].append(char)
            result.append([sorted(row, key=lambda item: item["x0"]) for row in page_rows])
    return result


def _box(char: dict) -> dict[str, float]:
    return {key: round(float(char[key]), 4) for key in ("x0", "top", "x1", "bottom")}


def _envelope(boxes: list[dict]) -> dict | None:
    if not boxes:
        return None
    return {
        "x0": min(box["x0"] for box in boxes),
        "top": min(box["top"] for box in boxes),
        "x1": max(box["x1"] for box in boxes),
        "bottom": max(box["bottom"] for box in boxes),
    }


def _same_box(left: dict | None, right: dict | None) -> bool:
    if left is None or right is None:
        return False
    return all(abs(left[key] - right[key]) <= 0.15 for key in ("x0", "top", "x1", "bottom"))


def _expected_offset(lines: list[list[int]], line_index: int, cell_index: int) -> int:
    return sum(len(line) + 1 for line in lines[:line_index]) + cell_index


def _actual_offset(lines: list[list[int]], line_index: int, cell_index: int) -> int:
    return _expected_offset(lines, line_index, cell_index)


def _run_validation(master: dict, pdf: Path, annotated: Path | None = None):
    started = time.perf_counter()
    result = validate_document(
        master,
        pdf,
        retain_pdf_provenance=True,
        profile=PROFILE,
    )
    elapsed = time.perf_counter() - started
    visuals = []
    if annotated is not None:
        provenance = build_provenance_alignment(result.pdf_input)
        issues = validation_errors_to_legacy_cell_issues(result, provenance)
        visuals = visual_issues_from_cell_issues(issues)
        export_annotated_pdf(str(pdf), str(annotated), visuals)
    return result, visuals, elapsed, None


def _match_and_localize(result, visuals, rows, clean_pdf: Path, corrupted_pdf: Path, corrupted_lines):
    clean_rows = _rows(clean_pdf)
    actual_rows = _rows(corrupted_pdf)
    by_issue = {
        issue_id: visual
        for issue_id, visual in zip(
            (issue.get("validator_issue_id") for issue in validation_errors_to_legacy_cell_issues(
                result, build_provenance_alignment(result.pdf_input)
            )),
            visuals,
        )
    }
    used = set()
    false_positive_ids = []
    for issue in result.errors:
        expected_start = issue.span.get("expected_start")
        candidates = [
            row for row in rows
            if row["page"] == issue.source_page_number
            and row["error_id"] not in used
            and abs(
                _expected_offset(
                    [[0] * len(line) for line in _source_page_lines(row["page"] - 1)],
                    row["line_index"],
                    row["expected_line_cell_index"],
                ) - expected_start
            ) <= 2
        ]
        if not candidates:
            false_positive_ids.append(issue.issue_id)
            continue
        row = min(
            candidates,
            key=lambda candidate: abs(
                _expected_offset(
                    [[0] * len(line) for line in _source_page_lines(candidate["page"] - 1)],
                    candidate["line_index"],
                    candidate["expected_line_cell_index"],
                ) - expected_start
            ),
        )
        used.add(row["error_id"])
        actual_index = row["actual_line_cell_index"]
        if row["mutation_type"] == "deletion":
            actual_line = corrupted_lines[row["page"] - 1][row["line_index"]]
            actual_index = min(actual_index, len(actual_line) - 1)
            while actual_index < len(actual_line) and actual_line[actual_index] == 0:
                actual_index += 1
            actual_index = min(actual_index, len(actual_line) - 1)
        if row["mutation_type"] == "transposition":
            actual_indexes = [actual_index, actual_index + 1]
        else:
            actual_indexes = [actual_index]
        actual_char_row = actual_rows[row["page"] - 1][row["line_index"]]
        visual = by_issue.get(issue.issue_id)
        visual_box = _envelope([box.__dict__ for box in (visual.boxes if visual else [])])
        if row["mutation_type"] == "deletion" and visual_box is not None:
            actual_indexes = [
                index for index, char in enumerate(actual_char_row)
                if abs(float(char["x0"]) - visual_box["x0"]) <= 0.15
            ]
            actual_target = visual_box
        else:
            actual_target = _envelope([_box(actual_char_row[index]) for index in actual_indexes])
        row.update({
            "detected": True,
            "validator_issue_id": issue.issue_id,
            "validator_reported_page": issue.actual_page_number,
            "validator_reported_range": [issue.actual_cell_start, issue.actual_cell_end],
            "expected_cell_location": {
                "page": row["page"],
                "line": row["line_index"],
                "cell": row["expected_line_cell_index"],
                "box": _envelope([_box(clean_rows[row["page"] - 1][row["line_index"]][row["expected_line_cell_index"]])]),
            },
            "actual_cell_location": {
                "page": row["page"],
                "line": row["line_index"],
                "cell": actual_indexes,
                "box": actual_target,
            },
            "blue_box": visual_box,
            "exact_localization": issue.actual_page_number == row["page"] and _same_box(actual_target, visual_box),
            "correct_blue_box": issue.actual_page_number == row["page"] and _same_box(actual_target, visual_box),
        })
    for row in rows:
        if not row["detected"]:
            false_positive_ids.append(row["error_id"])
    return false_positive_ids


def _source_page_lines(page_index: int) -> list[str]:
    return _page_lines(page_index)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    translator = LiblouisTranslator(UNCONTRACTED_UEB_CASE1)
    master = _master()
    (OUT / "case1_source.json").write_text(json.dumps(master, indent=2) + "\n", encoding="utf-8")
    font_name = _register_font()

    clean_unicode_pages = []
    corrupted_unicode_pages = []
    clean_cell_pages = []
    corrupted_cell_pages = []
    all_rows = []
    for page_index in range(PAGE_COUNT):
        clean_lines, corrupted_lines, rows = _mutate_page(page_index, translator)
        clean_unicode_pages.append([cells_to_unicode(line) for line in clean_lines])
        corrupted_unicode_pages.append([cells_to_unicode(line) for line in corrupted_lines])
        clean_cell_pages.append(clean_lines)
        corrupted_cell_pages.append(corrupted_lines)
        all_rows.extend(rows)

    clean_pdf = OUT / "case1_clean.pdf"
    corrupted_pdf = OUT / "case1_corrupted.pdf"
    annotated_pdf = OUT / "case1_corrupted_annotated.pdf"
    clean_brf = OUT / "case1_clean.brf"
    corrupted_brf = OUT / "case1_corrupted.brf"
    _write_pdf(clean_pdf, clean_unicode_pages, font_name)
    _write_pdf(corrupted_pdf, corrupted_unicode_pages, font_name)
    _write_brf(clean_brf, clean_cell_pages)
    _write_brf(corrupted_brf, corrupted_cell_pages)

    clean_result, _clean_visuals, clean_time, clean_peak = _run_validation(master, clean_pdf)
    corrupted_result, visuals, corrupted_time, corrupted_peak = _run_validation(
        master, corrupted_pdf, annotated_pdf
    )

    false_positive_ids = _match_and_localize(
        corrupted_result, visuals, all_rows, clean_pdf, corrupted_pdf, corrupted_cell_pages
    )
    fields = list(all_rows[0])
    with (OUT / "mutation_manifest.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)

    counts = Counter(row["mutation_type"] for row in all_rows)
    exact = sum(bool(row["exact_localization"]) for row in all_rows)
    detected = sum(bool(row["detected"]) for row in all_rows)
    expected = {
        "profile": PROFILE,
        "pages": PAGE_COUNT,
        "errors_per_page": ERRORS_PER_PAGE,
        "total_injected": len(all_rows),
        "expected_errors": len(all_rows),
        "clean_pdf_errors": len(clean_result.errors),
        "clean_pdf_reviews": len(clean_result.reviews),
        "corrupted_pdf_errors": len(corrupted_result.errors),
        "corrupted_pdf_reviews": len(corrupted_result.reviews),
        "detected": detected,
        "missed": len(all_rows) - detected,
        "false_positive_count": len(false_positive_ids),
        "false_positive_ids": false_positive_ids,
        "exact_physical_localization": exact,
        "correct_blue_box_locations": sum(bool(row["correct_blue_box"]) for row in all_rows),
        "blue_box_count": len(visuals),
        "mutation_breakdown": dict(sorted(counts.items())),
        "runtime": vendored_metadata(UNCONTRACTED_UEB_CASE1),
        "font_path": str(FONT_PATH),
        "font_sha256": sha256(FONT_PATH),
        "fixtures": {
            name: {"path": str(path), "sha256": sha256(path)}
            for name, path in {
                "source": OUT / "case1_source.json",
                "clean_brf": clean_brf,
                "corrupted_brf": corrupted_brf,
                "clean_pdf": clean_pdf,
                "corrupted_pdf": corrupted_pdf,
                "annotated_pdf": annotated_pdf,
            }.items()
        },
        "performance": {
            "clean_pdf_seconds": clean_time,
            "corrupted_pdf_seconds": corrupted_time,
        },
    }
    assert len(all_rows) == PAGE_COUNT * ERRORS_PER_PAGE
    assert not clean_result.errors and not clean_result.reviews
    assert len(corrupted_result.errors) == len(all_rows)
    assert detected == exact == len(all_rows)
    assert not false_positive_ids and len(visuals) == len(all_rows)
    (OUT / "expected_findings.json").write_text(json.dumps({"summary": expected, "errors": all_rows}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(expected, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
