"""Build the Case 4 flowing source and one verifiable, frozen 500-action fixture."""

from __future__ import annotations

import argparse
from bisect import bisect_right
import csv
import hashlib
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

from braille_app.translation.braille_cells import BRF_DOTS
from braille_app.translation.expected_document import generate_expected_braille
from braille_app.translation.liblouis_translator import LiblouisTranslator, vendored_metadata
from braille_app.translation.profiles import UNCONTRACTED_UEB_CASE4
from braille_app.translation.source_normalization import normalize_uncontracted_case4
from braille_app.translation.uncontracted_case4 import _translate_source_with_positions

OUT = ROOT / "stress_test" / "uncontracted_case4_punctuation"
SOURCE = OUT / "source" / "case4_punctuation_clean.docx"
EXPECTED = OUT / "expected" / "case4_expected_metadata.json"
COVERAGE = OUT / "expected" / "coverage_manifest.csv"
CLEAN_PDF = OUT / "output" / "case4_clean.pdf"
CLEAN_BRF = OUT / "output" / "case4_clean.brf"
CORRUPTED_PDF = OUT / "output" / "case4_corrupted.pdf"
CORRUPTED_BRF = OUT / "output" / "case4_corrupted.brf"
MANIFEST = OUT / "manifest" / "case4_500_mutations.csv"
INTEGRITY = OUT / "manifest" / "fixture_integrity.json"
FONT_PATH = Path(r"C:\Windows\Fonts\seguisym.ttf")
SEED = 20260923
PAGE_WIDTH, PAGE_LINES = 40, 25
FONT_SIZE, LINE_HEIGHT, LEFT, TOP = 14, 27, 42, 748
PUNCT = {",": "⠂", ".": "⠲", "?": "⠦", "!": "⠖", ":": "⠒", ";": "⠆"}
PUNCT_ORDER = tuple(PUNCT)
FAMILY_MARK = {
    "comma": ",", "period_full_stop": ".", "question_mark": "?",
    "exclamation_mark": "!", "colon": ":", "semicolon": ";",
}
METHOD_COUNTS = {
    "comma": {"delete": 20, "insert": 10, "duplicate": 10, "substitute": 20, "transpose": 20},
    "period_full_stop": {"delete": 20, "insert": 10, "duplicate": 10, "substitute": 20, "transpose": 20},
    "question_mark": {"delete": 18, "insert": 9, "duplicate": 9, "substitute": 16, "transpose": 18},
    "exclamation_mark": {"delete": 18, "insert": 9, "duplicate": 9, "substitute": 16, "transpose": 18},
    "colon": {"delete": 15, "insert": 8, "duplicate": 7, "substitute": 15, "transpose": 15},
    "semicolon": {"delete": 15, "insert": 8, "duplicate": 7, "substitute": 15, "transpose": 15},
    "punctuation_grade1": {"delete": 15, "insert": 15, "substitute": 10},
    "punctuation_capitalization_numeric_interactions": 20,
    "repeated_context_boundaries": 20,
}
SECTIONS = (
    "Daily Review", "Record Checks", "Reading Practice", "Entry Control",
    "Field Notes", "Status Reports", "Question Review", "Numbered Records",
    "Team Handover", "Final Summary",
)
TEMPLATES = (
    "During cycle {n}, the field group checked {amount} entries, then compared the earlier record. The final period closes the note; each check is recorded. Which page should the reader open next?",
    "The first reading is complete! The next reviewer checks the same amount, then confirms the result. Some readers ask whether the earlier total remains correct?",
    "At the desk, the lead wrote: compare the total; confirm the date, then file the result. Which line needs review? The clerk records the answer.",
    "In the ledger, the code a,b separates two labels. The numeric amount was {amount}, and the measure was 8.93. Is the entry clear?",
    "The schedule lists 10:30-? as a query case; a reviewer checks the indicator before filing. A second check confirms the value, then closes the record.",
    "Status: Ready, when the team checks the next section. The outcome is clear; the record remains complete! The question is whether the date is current?",
    "Readers compare the same entry across two copies, then confirm the page number. Some ask: Is the order clear? A clerk replies, Yes; the sequence is complete!",
    "For amount {amount}, the supervisor checked the reading, 8.93. The file was ready! A note asks whether the date is correct? The final check follows.",
    "At 3-D station {n}, staff ask: is the route clear? The report says, Yes; results remain stable, and review is complete. Which record comes next?",
    "The form names No. 4 as the next file, and lists the range 9-10. Which summary is current? The clerk responds, This one! The note is complete.",
    "The punctuation guide uses a,b and a;b for paired labels. It lists comma, period, question, exclamation, colon; semicolon. The group checks each example!",
    "The reader checked the copy, then asked whether the record was ready? The supervisor replied, Yes! The answer was added to the report; all cells were reviewed.",
)
REPEATED_NOTE = ("The pair a,b stays in order, and the same result remains on file; all staff confirm the "
                 "long entry before closing the regular review. A final note: no change is needed! Is the entry clear?")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _paragraphs():
    rows = [("Punctuation in Flowing Records", "Title", False, False),
            ("A fictional field guide for checking ordinary English records.", "Subtitle", False, False)]
    for section_index, section in enumerate(SECTIONS):
        rows.append((section, "Heading 1", section_index in {1, 5, 9}, False))
        for local in range(10):
            n = section_index * 10 + local + 1
            rows.append((TEMPLATES[(n - 1) % len(TEMPLATES)].format(
                n=n, amount=("4,500" if n % 2 else "12,750")), "Normal", False, False))
            if n % 3 == 0:
                rows.append((REPEATED_NOTE, "Normal", False, True))
    return rows


def _master(rows):
    return {"pages": [{"print_page_number": 1,
                       "blocks": [{"text": row[0]} for row in rows]}]}


def _expected(rows):
    translator = LiblouisTranslator(UNCONTRACTED_UEB_CASE4)
    document = generate_expected_braille(_master(rows), UNCONTRACTED_UEB_CASE4, translator)
    if document.review_count or not all(b.rule_status == "PASS" for b in document.blocks if b.braille):
        raise AssertionError("Case 4 source contains unsupported/review blocks")
    return document, translator, vendored_metadata(UNCONTRACTED_UEB_CASE4)


def create_source():
    if SOURCE.exists():
        raise FileExistsError(f"Refusing to replace the Case 4 source: {SOURCE}")
    rows = _paragraphs()
    for text, _style, _break, _repeat in rows:
        normalize_uncontracted_case4(text)
    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Inches(8.5), Inches(11)
    section.top_margin, section.bottom_margin = Inches(.75), Inches(.75)
    section.left_margin, section.right_margin = Inches(.85), Inches(.85)
    normal = doc.styles["Normal"]
    normal.font.name, normal.font.size = "Arial", Pt(10.5)
    normal.font.color.rgb = RGBColor(0, 0, 0)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.05
    for text, style_name, page_break, _repeat in rows:
        paragraph = doc.add_paragraph(text, style=style_name)
        paragraph.paragraph_format.keep_together = True
        paragraph.paragraph_format.page_break_before = page_break
        if style_name in {"Title", "Subtitle", "Heading 1"}:
            paragraph.style.font.name = "Arial"
            paragraph.style.font.color.rgb = RGBColor(0, 0, 0)
        if style_name == "Title":
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    SOURCE.parent.mkdir(parents=True, exist_ok=True)
    doc.save(SOURCE)
    print(json.dumps({"source": str(SOURCE), "paragraphs": len(rows),
                      "words": sum(len(row[0].split()) for row in rows),
                      "sha256": sha256(SOURCE)}, indent=2))


def _block_maps(document, translator, rows):
    repeat_blocks = {index for index, row in enumerate(rows) if row[3]}
    blocks = []
    cursor = 0
    for block in document.blocks:
        if not block.braille:
            continue
        source = normalize_uncontracted_case4(block.source_text)
        braille, positions = _translate_source_with_positions(source, translator)
        if braille != block.braille or len(braille) != len(positions):
            raise AssertionError("Case 4 expected stream/source positions diverged")
        start = cursor
        blocks.append({"source_block": block.source_block, "source": source,
                       "braille": braille, "source_positions": positions,
                       "expected_start": start, "expected_end": start + len(braille),
                       "repeated_context": block.source_block in repeat_blocks})
        cursor += len(braille)
        if block is not document.blocks[-1]:
            cursor += 1
    if cursor != len(document.flatten()):
        raise AssertionError("Case 4 block offsets do not cover expected stream")
    return blocks


def _manual_offsets(rows, blocks):
    return [block["expected_start"] for block in blocks
            if block["source_block"] < len(rows) and rows[block["source_block"]][2]]


def _tokens(text):
    return [{"cell": char, "origin": index, "mutation_id": ""}
            for index, char in enumerate(text)]


def _paginate(tokens, manual_offsets=()):
    force = {int(offset) for offset in manual_offsets}
    forced_indices = sorted(i for i, token in enumerate(tokens) if token["origin"] in force)
    forced_set = set(forced_indices)
    pages, break_kinds, current = [], [], []
    cursor = 0

    def flush(kind):
        nonlocal current
        if current:
            pages.append(current)
            break_kinds.append(kind)
            current = []

    while cursor < len(tokens):
        if cursor in forced_set:
            if current:
                flush("manual")
        if len(current) >= PAGE_LINES:
            flush("natural")
        end = min(cursor + PAGE_WIDTH, len(tokens))
        force_index = bisect_right(forced_indices, cursor)
        next_force = forced_indices[force_index] if force_index < len(forced_indices) else len(tokens)
        end = min(end, next_force)
        if end <= cursor:
            continue
        if end < len(tokens) and end == cursor + PAGE_WIDTH:
            blanks = [i for i in range(cursor + 1, end) if tokens[i]["cell"] == "⠀"]
            if blanks:
                end = blanks[-1] + 1
        row = tokens[cursor:end]
        while row and row[-1]["cell"] == "⠀":
            row = row[:-1]
        if row:
            current.append(row)
        cursor = end
    flush("end")
    return pages or [[]], break_kinds


def _font_name(page):
    name = f"Case4Cells{page}"
    if name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(name, str(FONT_PATH)))
    return name


def _write_pdf(path, pages):
    canvas = Canvas(str(path), pagesize=letter)
    canvas.setTitle("Case 4 English uncontracted UEB punctuation fixture")
    for page_index, page in enumerate(pages):
        canvas.setFont(_font_name(page_index), FONT_SIZE)
        y = TOP
        for row in page:
            canvas.drawString(LEFT, y, "".join(token["cell"] for token in row))
            y -= LINE_HEIGHT
        canvas.showPage()
    canvas.save()


def _brf_map():
    reverse = {}
    for char, dots in BRF_DOTS.items():
        reverse.setdefault(sum(1 << (int(dot) - 1) for dot in dots),
                           char.upper() if char.isalpha() else char)
    return reverse


def _write_brf(path, pages):
    reverse = _brf_map()
    path.write_text("\f".join("\n".join(
        "".join(reverse[ord(token["cell"]) - 0x2800] for token in row) for row in page
    ) for page in pages), encoding="ascii")


def _check_layout(pages, breaks):
    natural, manual = breaks.count("natural"), breaks.count("manual")
    count = len(pages)
    if not 22 <= count <= 28:
        raise AssertionError(f"Case 4 corpus paginates to {count} pages, expected 22–28")
    if manual < 3 or manual > (count - 1) / 4:
        raise AssertionError(f"Manual-break ratio is outside bounds: {manual}/{count - 1}")
    if natural < 5 or natural < (count - 1) / 2:
        raise AssertionError(f"Not enough natural page transitions: {natural}/{count - 1}")
    if sum(len(page) >= 20 for page in pages) < 10 or not any(5 <= len(p) < 20 for p in pages):
        raise AssertionError("Corpus lacks dense pages or shorter pages")
    return {"page_count": count, "natural_page_transitions": natural,
            "manual_page_transitions": manual, "break_kinds": breaks,
            "page_line_counts": [len(page) for page in pages]}


def build_clean():
    paths = (EXPECTED, COVERAGE, CLEAN_PDF, CLEAN_BRF)
    if any(path.exists() for path in paths):
        raise FileExistsError("Refusing to overwrite Case 4 clean fixture artifacts")
    if not SOURCE.is_file():
        raise FileNotFoundError("Run --create-source first")
    rows = _paragraphs()
    document, translator, runtime = _expected(rows)
    blocks = _block_maps(document, translator, rows)
    manual = _manual_offsets(rows, blocks)
    pages, breaks = _paginate(_tokens(document.flatten()), manual)
    layout = _check_layout(pages, breaks)
    metadata = {"profile": UNCONTRACTED_UEB_CASE4.name, "runtime": runtime,
                "source_path": str(SOURCE), "source_sha256": sha256(SOURCE),
                "expected_braille": document.flatten(),
                "expected_cell_count": len(document.flatten()),
                "expected_blocks": blocks, "manual_page_break_expected_offsets": manual,
                "physical_layout": layout}
    EXPECTED.parent.mkdir(parents=True, exist_ok=True)
    OUT.joinpath("output").mkdir(parents=True, exist_ok=True)
    with COVERAGE.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("family", "UEB_2024_rule", "example", "audit_status"))
        for row in (("comma", "7.1.1-7.1.3", "Hello, world.; a,b", "DIRECT plus cited G1"),
                    ("period", "7.1.1-7.1.3; 6.4.1", "End. No. 4; 8.93", "DIRECT"),
                    ("question", "7.5.1-7.5.4", "What?; ? x; 10:30-?", "CITED OVERRIDE after numeric dash"),
                    ("exclamation", "7.1.1-7.1.3", "Stop!; a!b", "DIRECT"),
                    ("colon", "7.1.1-7.1.3", "Status: Ready; a:b", "DIRECT"),
                    ("semicolon", "7.1.1-7.1.3", "red; green; a;b", "DIRECT"),
                    ("punctuation spaces", "7.1.2", "Hello,   world.", "CITED MAPPED SPACE REDUCTION")):
            writer.writerow(row)
    EXPECTED.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_pdf(CLEAN_PDF, pages)
    _write_brf(CLEAN_BRF, pages)
    print(json.dumps({"source_sha256": sha256(SOURCE), "cells": len(document.flatten()),
                      "layout": layout, "clean_pdf_sha256": sha256(CLEAN_PDF),
                      "clean_brf_sha256": sha256(CLEAN_BRF)}, indent=2))


def _origin_map(pages):
    result = {}
    for pi, page in enumerate(pages):
        for ri, row in enumerate(page):
            for ci, token in enumerate(row):
                if token["origin"] is not None:
                    result[token["origin"]] = (pi, ri, ci)
    return result


def _source_cells(expected, blocks, pages):
    cells = list(expected)
    source_char = [None] * len(cells)
    source_offset = [None] * len(cells)
    block_index = [None] * len(cells)
    repeated = [False] * len(cells)
    for bi, block in enumerate(blocks):
        for local, pos in enumerate(block["source_positions"]):
            at = block["expected_start"] + local
            source_char[at] = block["source"][pos]
            source_offset[at] = pos
            block_index[at] = bi
            repeated[at] = block["repeated_context"]
    loc = _origin_map(pages)
    records = []
    for i, cell in enumerate(cells):
        if cell not in PUNCT.values() or source_char[i] not in PUNCT:
            continue
        if loc.get(i) is None:
            continue
        b = block_index[i]
        source = blocks[b]["source"]
        offset = source_offset[i]
        if source[offset] != source_char[i]:
            raise AssertionError("Punctuation source map does not identify its source mark")
        same_offset = (i > 0 and cells[i - 1] == "⠰" and source_offset[i - 1] == offset)
        records.append({"index": i, "cell": cell, "mark": source_char[i],
                        "source_char": source_char[i],
                        "block": b, "source": source, "source_offset": offset,
                        "location": loc[i], "repeated": repeated[i],
                        "grade1_before": same_offset})
    return cells, source_char, source_offset, block_index, records


def _line_select(candidates, count, used_lines, used_spans, rng, family):
    by_line = defaultdict(list)
    for start, width, data in candidates:
        line = data.get("location")
        if line is None or line[:2] in used_lines:
            continue
        if any(i in used_spans for i in range(start, start + max(1, width))):
            continue
        by_line[line[:2]].append((start, width, data))
    line_keys = list(by_line)
    rng.shuffle(line_keys)
    chosen = []
    for line in line_keys:
        choice = rng.choice(by_line[line])
        chosen.append(choice)
        used_lines.add(line)
        start, width, _ = choice
        used_spans.update(range(start, start + max(1, width)))
        if len(chosen) == count:
            return chosen
    raise AssertionError(f"Only {len(chosen)}/{count} distinct-line candidates for {family}")


def _other_mark(mark, seed):
    options = [cell for cell in PUNCT.values() if cell != mark]
    return options[seed % len(options)]


def _make_mutations(expected, blocks, clean_pages):
    cells, source_char, source_offset, block_index, records = _source_cells(expected, blocks, clean_pages)
    locations = _origin_map(clean_pages)
    if "".join(cells) != expected:
        raise AssertionError("Source-position map does not cover expected cells")
    marker_records = []
    for i, cell in enumerate(cells):
        if cell != "⠰" or source_offset[i] is None or block_index[i] is None:
            continue
        source = blocks[block_index[i]]["source"]
        pos = source_offset[i]
        if pos < len(source) and source[pos] in PUNCT and i + 1 < len(cells) and source_offset[i + 1] == pos:
            marker_records.append({"index": i, "mark": source[pos], "block": block_index[i],
                                   "source_char": source[pos],
                                   "source": source, "source_offset": pos,
                                   "location": locations.get(i)})
    records_by_family = {family: [r for r in records if r["mark"] == mark and not r["grade1_before"]]
                         for family, mark in FAMILY_MARK.items()}
    actions = []
    requests = []

    def req(family, candidates, count, make):
        lines = {row[2]["location"][:2] for row in candidates if row[2].get("location")}
        scarcity = count / max(1, len(lines))
        swap_priority = 0 if any(width == 2 for _start, width, _data in candidates) else 1
        requests.append((scarcity, swap_priority, family, candidates, count, make, len(lines)))

    rng = random.Random(SEED)
    for family, methods in METHOD_COUNTS.items():
        if family not in FAMILY_MARK:
            continue
        mark = FAMILY_MARK[family]
        candidates = records_by_family[family]
        for operation, count in methods.items():
            if operation in {"delete", "substitute"}:
                pool = [(r["index"], 1, r) for r in candidates]
            elif operation == "duplicate":
                pool = [(r["index"] + 1, 0, r) for r in candidates]
            elif operation == "insert":
                pool = []
                for i, char in enumerate(cells[:-1]):
                    if source_char[i] and source_char[i].isascii() and source_char[i].isalpha():
                        location = locations.get(i)
                        next_location = locations.get(i + 1)
                        if location and next_location and location[:2] == next_location[:2] and location[2] < PAGE_WIDTH - 1:
                            pool.append((i + 1, 0, {"index": i, "mark": mark,
                                "block": block_index[i], "source": "", "source_offset": source_offset[i],
                                "source_char": source_char[i], "location": location, "repeated": False}))
            else:
                pool = []
                for r in candidates:
                    i = r["index"]
                    if i and source_char[i - 1] and source_char[i - 1].isalpha():
                        loc = _origin_map(clean_pages).get(i - 1)
                        if loc and loc[:2] == r["location"][:2]:
                            pool.append((i - 1, 2, {**r, "punct_index": i, "location": loc}))

            def factory(start, width, data, ordinal, op=operation, fam=family, punc=mark):
                if op == "delete":
                    expected_cells, replacement = cells[start:start + width], ""
                elif op == "insert":
                    expected_cells, replacement = (), PUNCT[punc]
                elif op == "duplicate":
                    expected_cells, replacement = (), PUNCT[punc]
                elif op == "substitute":
                    expected_cells, replacement = cells[start:start + width], _other_mark(PUNCT[punc], ordinal)
                else:
                    expected_cells, replacement = cells[start:start + width], cells[start + 1] + cells[start]
                return {"family": fam, "subtype": {
                    "delete": "punctuation deletion", "insert": "punctuation insertion",
                    "duplicate": "duplicate punctuation", "substitute": "punctuation substitution",
                    "transpose": "misplaced adjacent punctuation/letter order",
                }[op], "operation": "insert" if op == "duplicate" else op,
                    "method": op, "start": start, "width": width,
                    "expected": expected_cells, "replacement": replacement,
                    "target_index": data.get("punct_index", data["index"]),
                    "source_char": data.get("source_char", data.get("mark", punc)),
                    "source_offset": data.get("source_offset"),
                    "source_block": data.get("block"), "line": data["location"]}

            req(family, pool, count, factory)

    required_markers = [(r["index"], 1, r) for r in marker_records]
    optional_marks = [(r["index"], 0, r) for r in records if not r["grade1_before"]]
    for operation, count in METHOD_COUNTS["punctuation_grade1"].items():
        if operation == "delete":
            pool = required_markers
        elif operation == "substitute":
            pool = required_markers
        else:
            pool = optional_marks
        def g1_factory(start, width, data, ordinal, op=operation):
            return {"family": "punctuation_grade1", "subtype": {
                "delete": "missing required Grade 1 indicator",
                "insert": "extra Grade 1 indicator",
                "substitute": "wrong Grade 1 indicator",
            }[op], "operation": op, "method": op, "start": start, "width": width,
                "expected": cells[start:start + width] if width else (),
                "replacement": "" if op == "delete" else "⠰" if op == "insert" else "⠠",
                "target_index": data["index"],
                "source_char": data.get("source_char", data.get("mark", "")),
                "source_offset": data.get("source_offset"), "source_block": data.get("block"),
                "line": data["location"]}
        req("punctuation_grade1", pool, count, g1_factory)

    def next_caps(source, offset):
        return next((char for char in source[offset + 1:] if char != " "), "").isupper()

    cap_records = [r for r in records if not r["grade1_before"] and next_caps(r["source"], r["source_offset"])]
    numeric_records = [r for r in records if not r["grade1_before"] and (
        (r["source_offset"] > 0 and r["source"][r["source_offset"] - 1].isdigit())
        or (r["source_offset"] + 1 < len(r["source"]) and r["source"][r["source_offset"] + 1].isdigit())
    )]
    # Numeric Grade-1 question marks are tracked separately from the ordinary
    # punctuation candidates so the interaction family exercises §7.5.4.
    for bucket, pool in (("capitalization", cap_records), ("numeric", numeric_records)):
        candidates = [(r["index"], 1, r) for r in pool]
        ops = ("delete", "insert", "substitute")
        counts = (3, 3, 4)
        for operation, count in zip(ops, counts):
            def inter_factory(start, width, data, ordinal, op=operation):
                mark = data["mark"]
                repl = "" if op == "delete" else PUNCT[mark] if op == "insert" else _other_mark(PUNCT[mark], ordinal)
                return {"family": "punctuation_capitalization_numeric_interactions",
                    "subtype": f"{bucket}-adjacent punctuation {op}",
                    "operation": "insert" if op == "insert" else op, "method": op,
                    "start": start if op != "insert" else start + 1,
                    "width": 0 if op == "insert" else 1,
                    "expected": () if op == "insert" else cells[start:start + 1],
                    "replacement": repl, "target_index": data["index"],
                    "source_char": data.get("source_char", mark), "source_offset": data["source_offset"],
                    "source_block": data["block"], "line": data["location"]}
            req("punctuation_capitalization_numeric_interactions", candidates, count, inter_factory)

    all_boundary = [r for r in records if not r["grade1_before"]]
    line_edge = [(r["index"], 1, r) for r in all_boundary
                 if r["location"][2] <= 2 or r["location"][2] >= PAGE_WIDTH - 3]
    page_edge = [(r["index"], 1, r) for r in all_boundary
                 if r["location"][1] == 0 or r["location"][1] >= len(clean_pages[r["location"][0]]) - 1]
    repeated = [(r["index"], 1, r) for r in all_boundary if r["repeated"]]
    for context, pool, count in (("line-edge", line_edge, 5), ("page-edge", page_edge, 5), ("repeated-content", repeated, 10)):
        def boundary_factory(start, width, data, ordinal, label=context):
            return {"family": "repeated_context_boundaries", "subtype": label + " punctuation substitution",
                    "operation": "substitute", "method": "substitute", "start": start,
                    "width": 1, "expected": cells[start:start + 1],
                    "replacement": _other_mark(data["cell"], ordinal),
                    "target_index": data["index"],
                    "source_char": data.get("source_char", data["mark"]),
                    "source_offset": data["source_offset"], "source_block": data["block"],
                    "line": data["location"]}
        req("repeated_context_boundaries", pool, count, boundary_factory)

    used_lines, used_spans = set(), set()
    for _scarcity, _swap, family, pool, count, factory, available_lines in sorted(
        requests, key=lambda item: (-item[0], item[1])
    ):
        request_name = f"{family} ({count}, {available_lines} candidate lines)"
        for start, width, data in _line_select(pool, count, used_lines, used_spans, rng, request_name):
            actions.append(factory(start, width, data, len(actions)))
    for ordinal, action in enumerate(actions, 1):
        action["mutation_id"] = f"C4-{ordinal:04d}"
        action["expected_cells"] = "".join(action["expected"])
    expected_counts = {key: value if isinstance(value, int) else sum(value.values())
                       for key, value in METHOD_COUNTS.items()}
    if len(actions) != 500 or Counter(a["family"] for a in actions) != Counter(expected_counts):
        raise AssertionError("Case 4 action count/family distribution is not exact")
    occupied = set()
    for action in actions:
        for pos in range(action["start"], action["start"] + max(1, action["width"])):
            if pos in occupied:
                raise AssertionError(f"Overlapping mutation span at expected cell {pos}")
            occupied.add(pos)
        if action["method"] in {"substitute", "transpose"} and action["expected_cells"] == action["replacement"]:
            raise AssertionError(f"No-op action: {action}")
        if action["method"] == "transpose" and len(set(action["expected_cells"])) < 2:
            raise AssertionError(f"Invalid equal-cell transposition: {action['mutation_id']}")
    return actions, cells


def _apply_mutations(tokens, actions):
    result = [dict(token) for token in tokens]
    for action in sorted(actions, key=lambda row: row["start"], reverse=True):
        start, width, method = action["start"], action["width"], action["method"]
        mutation_id = action["mutation_id"]
        if method == "delete":
            action["actual_cells"] = ""
            del result[start:start + width]
        elif method in {"insert", "duplicate"}:
            action["actual_cells"] = action["replacement"]
            result.insert(start, {"cell": action["replacement"], "origin": None,
                                  "mutation_id": mutation_id})
        elif method == "substitute":
            result[start]["cell"] = action["replacement"]
            result[start]["mutation_id"] = mutation_id
            action["actual_cells"] = action["replacement"]
        else:
            result[start]["cell"], result[start + 1]["cell"] = result[start + 1]["cell"], result[start]["cell"]
            result[start]["mutation_id"] = result[start + 1]["mutation_id"] = mutation_id
            action["actual_cells"] = action["replacement"]
    if len(result) != len(tokens) + sum(1 if a["method"] in {"insert", "duplicate"} else -1 if a["method"] == "delete" else 0 for a in actions):
        raise AssertionError("Mutation stream delta does not reconcile")
    return result


def build_corrupted():
    for path in (CORRUPTED_PDF, CORRUPTED_BRF, MANIFEST, INTEGRITY):
        if path.exists():
            raise FileExistsError(f"Refusing to replace Case 4 corruption artifact: {path}")
    metadata = json.loads(EXPECTED.read_text(encoding="utf-8"))
    if sha256(SOURCE) != metadata["source_sha256"]:
        raise AssertionError("Case 4 source changed after the clean build")
    expected = metadata["expected_braille"]
    rows = _paragraphs()
    blocks = metadata["expected_blocks"]
    clean_pages, _ = _paginate(_tokens(expected), metadata["manual_page_break_expected_offsets"])
    actions, _ = _make_mutations(expected, blocks, clean_pages)
    mutated = _apply_mutations(_tokens(expected), actions)
    pages, breaks = _paginate(mutated, metadata["manual_page_break_expected_offsets"])
    layout = _check_layout(pages, breaks)
    OUT.joinpath("output").mkdir(parents=True, exist_ok=True)
    _write_pdf(CORRUPTED_PDF, pages)
    _write_brf(CORRUPTED_BRF, pages)
    locations = defaultdict(list)
    for pi, page in enumerate(pages, 1):
        for ri, line in enumerate(page, 1):
            for ci, token in enumerate(line, 1):
                if token["mutation_id"]:
                    locations[token["mutation_id"]].append({"page": pi, "line": ri, "cell": ci})
    for action in actions:
        action["actual_locations"] = locations[action["mutation_id"]]
        action["initial_page"], action["initial_line"], action["initial_cell"] = (n + 1 for n in action["line"])
        action["logical_target_count"] = action["width"] if action["method"] == "transpose" else 1
        action["target_policy"] = (
            "next semantic nonblank cell on the original physical line; previous cell at line end"
            if action["method"] == "delete" else "all changed actual cells in the mutation span"
        )
    fields = ("mutation_id", "family", "subtype", "operation", "method", "expected_start",
              "target_expected_index", "expected_cells", "actual_cells", "logical_target_count",
              "target_policy", "initial_page", "initial_line", "initial_cell", "actual_locations",
              "source_char", "source_offset", "source_block", "location")
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for action in actions:
            writer.writerow({"mutation_id": action["mutation_id"], "family": action["family"],
                "subtype": action["subtype"], "operation": action["operation"], "method": action["method"],
                "expected_start": action["start"], "target_expected_index": action["target_index"],
                "expected_cells": action["expected_cells"], "actual_cells": action["actual_cells"],
                "logical_target_count": action["logical_target_count"], "target_policy": action["target_policy"],
                "initial_page": action["initial_page"], "initial_line": action["initial_line"],
                "initial_cell": action["initial_cell"], "actual_locations": json.dumps(action["actual_locations"]),
                "source_char": action["source_char"], "source_offset": action["source_offset"],
                "source_block": action["source_block"], "location": json.dumps(action["line"])})
    integrity = {"seed": SEED, "total_actions": len(actions),
        "family_counts": dict(Counter(a["family"] for a in actions)),
        "required_family_counts": {key: value if isinstance(value, int) else sum(value.values())
                                   for key, value in METHOD_COUNTS.items()},
        "method_counts": dict(Counter(a["method"] for a in actions)),
        "length_delta": len(mutated) - len(expected),
        "no_overlapping_expected_targets": True,
        "all_substitutions_change_a_cell": True,
        "all_transpositions_swap_unequal_adjacent_cells": True,
        "all_non_deletions_have_physical_targets": all(a["method"] == "delete" or a["actual_locations"] for a in actions),
        "source_sha256": sha256(SOURCE), "expected_sha256": sha256(EXPECTED),
        "clean_pdf_sha256": sha256(CLEAN_PDF), "clean_brf_sha256": sha256(CLEAN_BRF),
        "corrupted_pdf_sha256": sha256(CORRUPTED_PDF), "corrupted_brf_sha256": sha256(CORRUPTED_BRF),
        "manifest_sha256": sha256(MANIFEST), "physical_layout": layout,
        "no_duxbury_controls_or_footer_targets": True}
    integrity["delta_by_method"] = {
        "insert": sum(a["method"] in {"insert", "duplicate"} for a in actions),
        "delete": -sum(a["method"] == "delete" for a in actions),
        "substitute_or_transpose": 0}
    if integrity["length_delta"] != sum(integrity["delta_by_method"].values()):
        raise AssertionError("Case 4 net stream delta does not match action arithmetic")
    INTEGRITY.write_text(json.dumps(integrity, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(integrity, indent=2))


def preview():
    rows = _paragraphs()
    document, translator, runtime = _expected(rows)
    blocks = _block_maps(document, translator, rows)
    manual = _manual_offsets(rows, blocks)
    pages, breaks = _paginate(_tokens(document.flatten()), manual)
    layout = _check_layout(pages, breaks)
    actions, _ = _make_mutations(document.flatten(), blocks, pages)
    print(json.dumps({"source_paragraphs": len(rows), "words": sum(len(r[0].split()) for r in rows),
        "expected_cells": len(document.flatten()), "layout": layout,
        "actions": len(actions), "families": dict(Counter(a["family"] for a in actions)),
        "methods": dict(Counter(a["method"] for a in actions)), "runtime": runtime}, indent=2))


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--preview", action="store_true")
    group.add_argument("--create-source", action="store_true")
    group.add_argument("--build-clean", action="store_true")
    group.add_argument("--build-corrupted", action="store_true")
    args = parser.parse_args()
    if args.preview:
        preview()
    elif args.create_source:
        create_source()
    elif args.build_clean:
        build_clean()
    else:
        build_corrupted()


if __name__ == "__main__":
    main()
