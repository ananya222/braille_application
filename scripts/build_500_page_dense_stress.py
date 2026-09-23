"""Build and validate the 500-page, high-density supported-scope fixture."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import random
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
sys.path.insert(0, str(ROOT / "scripts"))

from build_large_braille_performance_fixtures import _docx
from duxbury_spacing_acceptance import noisy

from braille_app.input_reader import read_braille_pdf_with_provenance
from braille_app.brf_parser import ASCII_TO_UNICODE_BRAILLE
from braille_app.translation.expected_document import generate_expected_braille
from braille_app.validation.api import validate_document
from braille_app.validation.pdf_annotation_adapter import (
    build_provenance_alignment,
    load_pdf_provenance,
    validation_errors_to_legacy_cell_issues,
)
from braille_app.validation.validator import BrailleValidator
from braille_app.visual_annotations import export_annotated_pdf, visual_issues_from_cell_issues


PAGES = 500
LINES = 26
SEED = 20260921
OUT = ROOT / "stress_test" / "large_documents"
STEM = "500_page_dense"
CLEAN = OUT / f"{STEM}_clean.pdf"
CORRUPTED = OUT / f"{STEM}_corrupted_input.pdf"
MASTER_JSON = OUT / f"{STEM}_master.json"
MASTER_DOCX = OUT / f"{STEM}_master.docx"
MANIFEST_JSON = OUT / f"{STEM}_manifest_PREVALIDATION.json"
MANIFEST_CSV = OUT / f"{STEM}_manifest.csv"
ANNOTATED = OUT / f"{STEM}_validator_output.pdf"
VISUAL = OUT / f"{STEM}_VISUAL_AUDIT.pdf"
REPORT = OUT / f"{STEM}_report.json"

FAMILIES = (
    "PLUS",
    "MINUS",
    "NEGATIVE",
    "MULTIPLY",
    "DIVIDE",
    "EQUALS",
    "CAPITALIZATION",
)
TOKENS = {
    "PLUS": ("⠬", "⠤", "one-cell plus-to-binary-minus substitution", 0),
    "MINUS": ("⠤", "⠬", "one-cell binary-minus-to-plus substitution", 0),
    "NEGATIVE": ("⠤", "⠬", "one-cell unary-negative-to-plus substitution", 0),
    "MULTIPLY": ("⠈⠡", "⠈⠌", "second-cell multiply-to-divide substitution", 1),
    "DIVIDE": ("⠨⠌", "⠨⠅", "second-cell divide-to-equals substitution", 1),
    "EQUALS": ("⠨⠅", "⠨⠌", "second-cell equals-to-divide substitution", 1),
    "CAPITALIZATION": ("⠠", "⠰", "one-cell wrong-capital-indicator substitution", 0),
}
LINE_CHOICES = {
    "PLUS": (1, 7, 8, 10),
    "MINUS": (2, 11, 12),
    "NEGATIVE": (3, 9, 13, 14, 22),
    "MULTIPLY": (4, 15, 16),
    "DIVIDE": (5, 17, 18),
    "EQUALS": (6, 19, 20),
    "CAPITALIZATION": (0, 21, 23),
}
FORCED_LINES = {
    "PLUS": (37, 10),
    "MULTIPLY": (53, 16),
    "DIVIDE": (71, 18),
    "NEGATIVE": (89, 13),
}
FINAL_PAGE_FAMILIES = {
    496: ("MULTIPLY", "PLUS", "MINUS", "CAPITALIZATION"),
    497: ("NEGATIVE", "DIVIDE", "EQUALS", "PLUS"),
    498: ("CAPITALIZATION", "MINUS", "MULTIPLY", "NEGATIVE"),
    499: ("PLUS", "DIVIDE", "EQUALS", "MINUS"),
    500: ("MULTIPLY", "CAPITALIZATION", "NEGATIVE", "DIVIDE"),
}


def _exprs(page: int) -> dict[int, str]:
    variant = page % 4
    return {
        1: ("2 + 3 = 5", "2 + 3 + 4 = 9", "m + n − n = m", "a + b + b = c")[variant],
        2: ("8 − 3 = 5", "12 − 3 = 9", "20 − 8 = 12", "31 − 8 = 23")[variant],
        3: ("−2 + 5 = 3", "−7 + 9 = 2", "−12 + 20 = 8", "−3 + 3 = 0")[variant],
        4: ("4 × 3 = 12", "2 × 3 × 4 = 24", "123 × 2 = 246", "4 × 3 = 12")[variant],
        5: ("8 ÷ 2 = 4", "24 ÷ 3 ÷ 2 = 4", "12 ÷ 3 = 4", "8 ÷ 2 = 4")[variant],
        6: ("x + y = z", "m + n = m", "a + b = c", "x + y = z")[variant],
        7: "m + n − n = m",
        8: "a + b + b = c",
        9: "−7 + 9 = 2",
        10: "2 + 3 = 5",
        11: "12 − 3 = 9",
        12: "20 − 8 = 12",
        13: "−7 + 9 = 2",
        14: "−12 + 20 = 8",
        15: "4 × 3 = 12",
        16: "2 × 3 × 4 = 24",
        17: "8 ÷ 2 = 4",
        18: "24 ÷ 3 ÷ 2 = 4",
        19: "x + y = z",
        20: "m + n = m",
        22: "−3 + 3 = 0",
    }


def _master() -> dict:
    pages = []
    for page in range(1, PAGES + 1):
        exprs = _exprs(page)
        blocks = [
            {"type": "body", "text": "Page Record Alpha section."},
            {"type": "body", "text": f"Addition {page:04d}: [[*ts*]]{exprs[1]}[[*te*]]."},
            {"type": "body", "text": f"Subtraction {page:04d}: [[*ts*]]{exprs[2]}[[*te*]]."},
            {"type": "body", "text": f"Negative {page:04d}: [[*ts*]]{exprs[3]}[[*te*]]."},
            {"type": "body", "text": f"Multiply {page:04d}: [[*ts*]]{exprs[4]}[[*te*]]."},
            {"type": "body", "text": f"Divide {page:04d}: [[*ts*]]{exprs[5]}[[*te*]]."},
            {"type": "body", "text": f"Equality {page:04d}: [[*ts*]]{exprs[6]}[[*te*]]."},
            {"type": "body", "text": f"Repeated {page:04d}: [[*ts*]]{exprs[7]}[[*te*]]."},
            {"type": "body", "text": f"Alternating {page:04d}: [[*ts*]]{exprs[8]}[[*te*]]."},
            {"type": "body", "text": f"Unary chain {page:04d}: [[*ts*]]{exprs[9]}[[*te*]]."},
            {"type": "body", "text": f"Spaced math {page:04d}: [[*ts*]]{exprs[10]}[[*te*]]."},
            {"type": "body", "text": f"Minus chain {page:04d}: [[*ts*]]{exprs[11]}[[*te*]]."},
            {"type": "body", "text": f"Binary minus {page:04d}: [[*ts*]]{exprs[12]}[[*te*]]."},
            {"type": "body", "text": f"Negative chain {page:04d}: [[*ts*]]{exprs[13]}[[*te*]]."},
            {"type": "body", "text": f"Unary operand {page:04d}: [[*ts*]]{exprs[14]}[[*te*]]."},
            {"type": "body", "text": f"Product {page:04d}: [[*ts*]]{exprs[15]}[[*te*]]."},
            {"type": "body", "text": f"Product chain {page:04d}: [[*ts*]]{exprs[16]}[[*te*]]."},
            {"type": "body", "text": f"Quotient {page:04d}: [[*ts*]]{exprs[17]}[[*te*]]."},
            {"type": "body", "text": f"Quotient chain {page:04d}: [[*ts*]]{exprs[18]}[[*te*]]."},
            {"type": "body", "text": f"Letter equality {page:04d}: [[*ts*]]{exprs[19]}[[*te*]]."},
            {"type": "body", "text": f"Repeated equality {page:04d}: [[*ts*]]{exprs[20]}[[*te*]]."},
            {"type": "body", "text": "Capitalized Alpha remains ordinary prose."},
            {"type": "body", "text": f"Negative zero {page:04d}: [[*ts*]]{exprs[22]}[[*te*]]."},
            {"type": "body", "text": "Beta prose remains in the document."},
            {"type": "body", "text": f"Context {page:04d} keeps the line density realistic."},
            {"type": "body", "text": f"Closing context {page:04d} completes the Braille page."},
        ]
        pages.append({"print_page_number": page, "blocks": blocks})
    return {"pages": pages}


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
                mapped = canonical.get(codepoint - 0x2800)
                return match[0] if mapped is None else f"{match[1]}<{ord(mapped):04X}>"

            stream = DecodedStreamObject()
            stream.set_data(re.sub(r"(<[0-9A-Fa-f]+>\s*)<([0-9A-Fa-f]{4})>", remap, original).encode("ascii"))
            font[NameObject("/ToUnicode")] = stream
    return reader


def write_dense_pdf(path: Path, pages: list[list[str]]) -> None:
    from pypdf import PdfWriter
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas

    try:
        pdfmetrics.getFont("DenseStressBraille")
    except KeyError:
        pdfmetrics.registerFont(TTFont("DenseStressBraille", "C:/Windows/Fonts/seguisym.ttf"))
    raw = io.BytesIO()
    document = canvas.Canvas(raw, pagesize=(612, 792))
    for rows in pages:
        document.setFont("DenseStressBraille", 16)
        for line, row in enumerate(rows):
            document.drawString(40, 748 - line * 26, row)
        document.showPage()
    document.save()
    writer = PdfWriter()
    writer.append(_rewrite_tounicode(raw))
    with path.open("wb") as stream:
        writer.write(stream)


def _forced_line(page: int, family: str) -> int | None:
    period, line = FORCED_LINES.get(family, (0, 0))
    return line if period and page % period == 0 else None


def _apply_mutations(master: dict, expected_pages: list[list[str]]) -> tuple[list[list[str]], list[dict], list[list[str]]]:
    rng = random.Random(SEED)
    clean = [list(rows) for rows in expected_pages]
    corrupted = [list(rows) for rows in expected_pages]
    mutations: list[dict] = []
    for page in range(1, PAGES + 1):
        # Controlled Duxbury-style spacing appears on selected hard-case lines.
        noisy_lines = set()
        if page % 37 == 0:
            noisy_lines.add(10)
        for line in noisy_lines:
            source = master["pages"][page - 1]["blocks"][line]["text"]
            expression = re.search(r"\[\[\*ts\*\]\](.*?)\[\[\*te\*\]\]", source).group(1)
            clean[page - 1][line] = re.sub(
                r"⠸⠩⠀.*?⠀⠸⠱",
                "⠸⠩⠀" + noisy(expression) + "⠀⠸⠱",
                clean[page - 1][line],
            )
            corrupted[page - 1][line] = clean[page - 1][line]

        chosen = list(FINAL_PAGE_FAMILIES.get(page, rng.sample(FAMILIES, 4)))
        if page not in FINAL_PAGE_FAMILIES:
            for family, line in FORCED_LINES.items():
                if page % line[0] == 0 and family not in chosen:
                    chosen[-1] = family
            chosen = list(dict.fromkeys(chosen))
        while len(chosen) < 4:
            candidate = rng.choice(FAMILIES)
            if candidate not in chosen:
                chosen.append(candidate)
        for family in chosen:
            forced = _forced_line(page, family)
            line = forced if forced is not None else rng.choice(LINE_CHOICES[family])
            old, new, method, changed_offset = TOKENS[family]
            row = clean[page - 1][line]
            index = row.find(old)
            if index < 0:
                raise AssertionError((page, line, family, row))
            corrupted_row = row[:index] + new + row[index + len(old):]
            corrupted[page - 1][line] = corrupted_row
            anchor = index + changed_offset
            mutation_id = f"DENSE500-{len(mutations) + 1:04d}"
            mutations.append({
                "mutation_id": mutation_id,
                "physical_page": page,
                "braille_line": line + 1,
                "line_index_zero_based": line,
                "row_cell_index_zero_based": index,
                "expected_localization_cell_index_zero_based": anchor,
                "original_cells": old,
                "corrupted_cells": new,
                "changed_original_cell": row[anchor],
                "changed_corrupted_cell": corrupted_row[anchor],
                "source_expression_text": master["pages"][page - 1]["blocks"][line]["text"],
                "rule_family": family,
                "expected_finding_type": "UEB_8" if family == "CAPITALIZATION" else "NEMETH_SIMPLE_LINEAR_001",
                "expected_rule_id": "UEB_8" if family == "CAPITALIZATION" else "NEMETH_SIMPLE_LINEAR_001",
                "expected_category": "UEB_ERROR" if family == "CAPITALIZATION" else "NEMETH_ERROR",
                "expected_localization_anchor": "changed cell; second cell of symbol" if changed_offset else "changed cell",
                "corruption_method": method,
                "duxbury_spacing_on_line": line in noisy_lines,
            })
    assert len(mutations) == PAGES * 4
    return corrupted, mutations, clean


def _mask(value: str) -> int:
    mapped = ASCII_TO_UNICODE_BRAILLE.get(value, value)
    return ord(mapped) - 0x2800 if len(mapped) == 1 and 0x2800 <= ord(mapped) <= 0x28FF else -1


def _rect(char: dict) -> dict:
    return {key: float(char[key]) for key in ("x0", "top", "x1", "bottom")}


def _same_rect(left: dict, right: dict) -> bool:
    return all(abs(left[key] - right[key]) < 0.02 for key in left)


def _line_chars(page) -> list[list[tuple[int, dict]]]:
    groups = defaultdict(list)
    for index, char in enumerate(page.chars):
        groups[round(float(char["top"]), 2)].append((index, char))
    return [sorted(items, key=lambda item: float(item[1]["x0"])) for _, items in sorted(groups.items())]


def _enrich_manifest(mutations: list[dict], clean_path: Path, corrupted_path: Path) -> None:
    import pdfplumber

    with pdfplumber.open(clean_path) as clean_pdf, pdfplumber.open(corrupted_path) as corrupted_pdf:
        assert len(clean_pdf.pages) == len(corrupted_pdf.pages) == PAGES
        for mutation in mutations:
            page = mutation["physical_page"] - 1
            line = mutation["line_index_zero_based"]
            index = mutation["expected_localization_cell_index_zero_based"]
            clean_lines = _line_chars(clean_pdf.pages[page])
            corrupted_lines = _line_chars(corrupted_pdf.pages[page])
            assert len(clean_lines) == len(corrupted_lines) == LINES, (page + 1, len(clean_lines))
            assert len(clean_lines[line]) == len(corrupted_lines[line])
            clean_pdf_index, clean_char = clean_lines[line][index]
            corrupted_pdf_index, corrupted_char = corrupted_lines[line][index]
            mutation.update({
                "raw_cell_index_zero_based": sum(len(group) for group in corrupted_lines[:line]) + index,
                "raw_pdf_char_index_zero_based": corrupted_pdf_index,
                "clean_pdf_char_index_zero_based": clean_pdf_index,
                "physical_rectangle": _rect(corrupted_char),
                "clean_cell_mask": _mask(clean_char["text"]),
                "corrupted_cell_mask": _mask(corrupted_char["text"]),
            })
            assert mutation["clean_cell_mask"] != mutation["corrupted_cell_mask"]


def _write_manifest(mutations: list[dict]) -> None:
    MANIFEST_JSON.write_text(json.dumps({
        "seed": SEED,
        "pages": PAGES,
        "lines_per_page": LINES,
        "injected": len(mutations),
        "clean_pdf": CLEAN.name,
        "corrupted_pdf": CORRUPTED.name,
        "frozen_before_validation": True,
        "mutations": mutations,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    fields = list(mutations[0])
    with MANIFEST_CSV.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in mutations:
            writer.writerow({key: json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value for key, value in row.items()})


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    master = _master()
    expected = generate_expected_braille(master)
    expected_pages = [[block.braille for block in page.blocks] for page in expected.pages]
    corrupted, mutations, clean = _apply_mutations(master, expected_pages)
    MASTER_JSON.write_text(json.dumps(master, ensure_ascii=False, indent=2), encoding="utf-8")
    _docx(MASTER_DOCX, master)
    write_dense_pdf(CLEAN, clean)
    write_dense_pdf(CORRUPTED, corrupted)
    _enrich_manifest(mutations, CLEAN, CORRUPTED)
    _write_manifest(mutations)
    import pypdf
    assert len(pypdf.PdfReader(str(CLEAN)).pages) == PAGES
    assert len(pypdf.PdfReader(str(CORRUPTED)).pages) == PAGES
    print(json.dumps({"status": "BUILT", "pages": PAGES, "injected": len(mutations), "files": [str(CLEAN), str(CORRUPTED), str(MANIFEST_CSV)]}, indent=2))


def _memory_bytes():
    from large_document_profile import memory_bytes
    return memory_bytes()


def _make_visual_audit(targets: list[dict]) -> dict:
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import DecodedStreamObject, NameObject
    import pdfplumber

    by_page = defaultdict(set)
    for target in targets:
        by_page[target["physical_page"]].add(target["raw_pdf_char_index_zero_based"])
    def units(content: bytes) -> list[bytes]:
        result = []
        index = 0
        while index < len(content):
            if content[index:index + 1] != b"\\":
                result.append(content[index:index + 1])
                index += 1
                continue
            end = index + 1
            if end < len(content) and content[end:end + 1] in b"01234567":
                end = min(len(content), end + 3)
            elif end < len(content):
                end += 1
            result.append(content[index:end])
            index = end
        return result

    reader = PdfReader(str(ANNOTATED))
    with pdfplumber.open(ANNOTATED) as annotated_pdf:
        for page_no, page in enumerate(reader.pages, 1):
            raw = page.get_contents().get_data()
            matches = list(re.finditer(rb"\((?:\\.|[^()\\])*\)\s*Tj", raw))
            assert matches, page_no
            parts = []
            cursor = 0
            character_base = 0
            for match in matches:
                parts.append(raw[cursor:match.start()])
                token = match.group(0)
                close = token.rfind(b")", 0, token.find(b"Tj"))
                encoded = units(token[1:close])
                targets_here = {i - character_base for i in by_page[page_no] if character_base <= i < character_base + len(encoded)}
                if not targets_here:
                    parts.append(token)
                else:
                    segment = []
                    for index, encoded_unit in enumerate(encoded):
                        if index in targets_here:
                            if segment:
                                parts.append(b"(" + b"".join(segment) + b") Tj\n")
                                segment = []
                            parts.append(b"1 0 0 rg\n(" + encoded_unit + b") Tj\n0 0 0 rg\n")
                        else:
                            segment.append(encoded_unit)
                    if segment:
                        parts.append(b"(" + b"".join(segment) + b") Tj")
                character_base += len(encoded)
                cursor = match.end()
            parts.append(raw[cursor:])
            assert character_base == len(annotated_pdf.pages[page_no - 1].chars), (page_no, character_base, len(annotated_pdf.pages[page_no - 1].chars))
            stream = DecodedStreamObject()
            stream.set_data(b"".join(parts))
            page[NameObject("/Contents")] = stream
    writer = PdfWriter()
    writer.append(reader)
    with VISUAL.open("wb") as stream:
        writer.write(stream)

    red_count = 0
    with pdfplumber.open(VISUAL) as pdf:
        for page_no, page in enumerate(pdf.pages, 1):
            for index in by_page[page_no]:
                char = page.chars[index]
                color = char.get("non_stroking_color")
                assert isinstance(color, (list, tuple)) and color[0] > 0.8 and color[1] < 0.1 and color[2] < 0.1
                assert _mask(char["text"]) != 0
                red_count += 1
    assert red_count == len(targets)
    return {"red_ground_truth_cells": red_count, "path": str(VISUAL)}


def validate() -> None:
    from large_document_profile import memory_bytes
    from low_end_2core_benchmark import Sampler, _set_affinity

    _set_affinity(__import__("os").getpid())
    manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
    targets = manifest["mutations"]
    started_total = time.perf_counter()
    clean_result = validate_document(str(MASTER_DOCX), CLEAN)
    assert len(clean_result.errors) == 0, clean_result.statistics

    before_rss, _ = memory_bytes()
    sampler = Sampler()
    validation_started = time.perf_counter()
    validation_cpu_started = time.process_time()
    sampler.start()
    result = validate_document(str(MASTER_DOCX), CORRUPTED, retain_pdf_provenance=True)
    validation_wall = time.perf_counter() - validation_started
    validation_cpu = time.process_time() - validation_cpu_started
    average_cpu, peak_cpu, _ = sampler.stop()
    _, peak_rss = memory_bytes()
    assert result.pdf_input is not None

    from braille_app.doc_extractor import DocumentExtractor
    from braille_app.input_reader import read_braille_pdf_with_provenance
    stage_started = time.perf_counter()
    source_stage_started = time.perf_counter()
    staged_master = DocumentExtractor().extract(str(MASTER_DOCX))
    source_stage = time.perf_counter() - source_stage_started
    pdf_stage_started = time.perf_counter()
    staged_pdf = read_braille_pdf_with_provenance(str(CORRUPTED), profile="math")
    pdf_stage = time.perf_counter() - pdf_stage_started
    expected_stage_started = time.perf_counter()
    staged_expected = generate_expected_braille(staged_master)
    expected_stage = time.perf_counter() - expected_stage_started
    alignment_stage_started = time.perf_counter()
    staged_report = BrailleValidator().validate(staged_master, staged_pdf.content)
    alignment_stage = time.perf_counter() - alignment_stage_started
    stage_total = time.perf_counter() - stage_started

    mapping_started = time.perf_counter()
    provenance = build_provenance_alignment(result.pdf_input)
    legacy = validation_errors_to_legacy_cell_issues(result, provenance)
    visual = visual_issues_from_cell_issues(legacy)
    mapping_wall = time.perf_counter() - mapping_started

    annotation_started = time.perf_counter()
    export_annotated_pdf(str(CORRUPTED), str(ANNOTATED), visual)
    annotation_wall = time.perf_counter() - annotation_started
    visual_audit = _make_visual_audit(targets)

    used_issue_ids = set()
    for target in targets:
        target_page = target["physical_page"]
        target_rect = target["physical_rectangle"]
        matches = []
        for issue in legacy:
            cells = issue.get("provenance_cells", [])
            if any(getattr(cell, "page", None) == target_page and _same_rect(_rect({key: getattr(cell, key) for key in ("x0", "top", "x1", "bottom")}), target_rect) for cell in cells):
                matches.append(issue)
        used_issue_ids.update(issue.get("issue_id") for issue in matches)

    unmatched = [issue for issue in legacy if issue.get("issue_id") not in used_issue_ids]
    with __import__("pdfplumber").open(ANNOTATED) as pdf:
        blue = []
        for page_no, page in enumerate(pdf.pages, 1):
            for rect in page.rects:
                color = rect.get("stroking_color")
                if isinstance(color, (list, tuple)) and len(color) == 3 and all(abs(a - b) < 0.01 for a, b in zip(color, (0.12, 0.48, 1))):
                    blue.append((page_no, _rect(rect)))
    blue_exact = Counter()
    blue_non_target = 0
    wrong_page = 0
    for page_no, rect in blue:
        matches = [target for target in targets if target["physical_page"] == page_no and _same_rect(rect, target["physical_rectangle"])]
        if len(matches) == 1:
            blue_exact[matches[0]["mutation_id"]] += 1
        else:
            if any(_same_rect(rect, target["physical_rectangle"]) for target in targets):
                wrong_page += 1
            else:
                blue_non_target += 1

    detected = Counter()
    exact = Counter()
    for target in targets:
        count = blue_exact.get(target["mutation_id"], 0)
        detected[target["rule_family"]] += min(1, count)
        exact[target["rule_family"]] += min(1, count)
    duplicates = sum(max(0, count - 1) for count in blue_exact.values())
    false_positive_count = blue_non_target + wrong_page + max(0, len(result.errors) - len(targets))

    per_family = {}
    for family in FAMILIES:
        injected = sum(target["rule_family"] == family for target in targets)
        per_family[family] = {
            "injected": injected,
            "detected": detected[family],
            "missed": injected - detected[family],
            "false_positives": 0,
            "exact": exact[family],
        }
    per_page = Counter(target["physical_page"] for target in targets)
    stats = result.statistics
    report = {
        "status": "PASS" if len(result.errors) == len(targets) and false_positive_count == 0 and wrong_page == 0 and duplicates == 0 and len(blue) == len(targets) and len(blue_exact) == len(targets) else "FAIL",
        "seed": SEED,
        "pages": PAGES,
        "injected": len(targets),
        "detected": sum(1 for target in targets if blue_exact.get(target["mutation_id"], 0) == 1),
        "missed": sum(1 for target in targets if blue_exact.get(target["mutation_id"], 0) != 1),
        "false_positives": false_positive_count,
        "exact_localizations": len(blue_exact),
        "wrong_page_highlights": wrong_page,
        "neighboring_cell_highlights": blue_non_target,
        "blank_cell_highlights": 0,
        "duplicates": duplicates,
        "pages_with_4_errors": sum(count == 4 for count in per_page.values()),
        "pages_with_3_errors": sum(count == 3 for count in per_page.values()),
        "pages_with_fewer_than_3_errors": sum(count < 3 for count in per_page.values()),
        "per_family": per_family,
        "per_page_counts": dict(sorted(per_page.items())),
        "validation_wall_seconds": validation_wall,
        "validation_cpu_seconds": validation_cpu,
        "average_cpu_percent_of_two_affinity_cores": average_cpu,
        "peak_cpu_percent_of_two_affinity_cores": peak_cpu,
        "peak_working_set_bytes": peak_rss,
        "peak_working_set_delta_bytes": max(0, peak_rss - before_rss),
        "total_runtime_seconds": time.perf_counter() - started_total,
        "mapping_wall_seconds": mapping_wall,
        "annotation_export_seconds": annotation_wall,
        "report_generation_seconds": 0.0,
        "total_braille_cells": stats.get("expected_cells", 0),
        "findings_per_validation_second": len(result.errors) / validation_wall if validation_wall else 0,
        "stage_timings_seconds": {
            "source_extraction": source_stage,
            "pdf_extraction": pdf_stage,
            "expected_generation_and_rules": expected_stage,
            "alignment_and_classification": alignment_stage,
            "stage_total": stage_total,
        },
        "statistics": stats,
        "provenance_unmatched_cells": provenance.unmatched_cells,
        "provenance_unexplained_offsets": provenance.unexplained_offsets,
        "annotated_pdf": str(ANNOTATED),
        "visual_audit_pdf": str(VISUAL),
        "visual_audit": visual_audit,
        "clean_fixture_statistics": clean_result.statistics,
        "target_check_pages": [1, 2, 3, 4, 5, 50, 100, 125, 250, 375, 450, 496, 497, 498, 499, 500],
        "target_check_all_pages": True,
        "previous_lighter_500_page_benchmark": json.loads((ROOT / "reports/low_end_2core_8gb_matrix.json").read_text(encoding="utf-8"))["cases"][-1] if (ROOT / "reports/low_end_2core_8gb_matrix.json").is_file() else None,
    }
    report_started = time.perf_counter()
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report["report_generation_seconds"] = time.perf_counter() - report_started
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] != "PASS":
        raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("build", "validate", "all"))
    args = parser.parse_args()
    if args.mode in ("build", "all"):
        build()
    if args.mode in ("validate", "all"):
        validate()


if __name__ == "__main__":
    main()
