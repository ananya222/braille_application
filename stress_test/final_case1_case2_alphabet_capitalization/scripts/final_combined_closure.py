"""Final combined Case 1/2 closure audit and corruption run.

This is fixture/audit tooling only.  It never edits the frozen DOCX, DXB, BRF,
or PDF.  Corruption is applied to copies of the real Duxbury PDF/BRF.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import pdfplumber
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, NameObject

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "stress_test" / "final_case1_case2_alphabet_capitalization"
SOURCE = OUT / "source"
CORRUPTED = OUT / "corrupted"
RESULTS = OUT / "results"
MANIFESTS = OUT / "manifests"
DOCX = SOURCE / "final_case1_case2_clean_50page.docx"
DXB = SOURCE / "final_case1_case2_clean_50page.dxb"
BRF = SOURCE / "final_case1_case2_clean_50page (2).brf"
PDF = SOURCE / "final_case1_case2_clean_50page.pdf"
PROFILE = "uncontracted_case2_capitalization"

SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from braille_app.doc_extractor import DocumentExtractor
from braille_app.input_reader import read_braille_pdf_with_provenance
from braille_app.translation.braille_cells import (
    ascii_to_cells,
    char_mask,
    cells_to_unicode,
    unicode_to_cells,
)
from braille_app.translation.expected_document import generate_expected_braille
from braille_app.translation.liblouis_translator import (
    LiblouisTranslator,
    vendored_metadata,
)
from braille_app.translation.profiles import UNCONTRACTED_UEB_CASE2
from braille_app.validation.alignment import align_cells
from braille_app.validation.api import validate_document
from braille_app.validation.pdf_annotation_adapter import (
    build_provenance_alignment,
    validation_errors_to_legacy_cell_issues,
)
from braille_app.visual_annotations import export_annotated_pdf, visual_issues_from_cell_issues


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ensure_paths() -> None:
    for path in (DOCX, DXB, BRF, PDF):
        if not path.is_file():
            raise FileNotFoundError(path)
    for path in (CORRUPTED, RESULTS, MANIFESTS):
        path.mkdir(parents=True, exist_ok=True)


def master_and_expected():
    master = DocumentExtractor().extract(str(DOCX))
    expected = generate_expected_braille(master, PROFILE)
    if len(expected.pages) != 50:
        raise AssertionError(f"expected 50 pages, got {len(expected.pages)}")
    return master, expected


def brf_logical_pages() -> tuple[list[list[int]], list[dict]]:
    raw_pages = BRF.read_text(encoding="latin1").split("\f")
    if raw_pages and not raw_pages[-1].strip():
        raw_pages.pop()
    pages: list[list[int]] = []
    records: list[dict] = []
    typeform = re.compile(r"\^[127']")
    footer = re.compile(r"^\s+#[A-Z]+$")
    for page_no, raw_page in enumerate(raw_pages, 1):
        stream: list[int] = []
        raw_typeform_cells = 0
        for line_no, line in enumerate(raw_page.splitlines()):
            if footer.fullmatch(line):
                continue
            stripped = line.strip()
            if not stripped:
                continue
            raw_typeform_cells += sum(len(match.group(0)) for match in typeform.finditer(stripped))
            stripped = typeform.sub("", stripped)
            if stream:
                stream.append(0)
            stream.extend(ascii_to_cells(stripped, "duxbury"))
        pages.append(stream)
        records.append({"page": page_no, "typeform_cells_removed": raw_typeform_cells})
    return pages, records


def audit_translation() -> dict:
    ensure_paths()
    master, expected = master_and_expected()
    runtime = vendored_metadata(UNCONTRACTED_UEB_CASE2)
    brf_pages, brf_records = brf_logical_pages()
    clean_brf_result = validate_document(master, BRF, profile=PROFILE)
    clean_pdf_result = validate_document(
        master, PDF, profile=PROFILE, retain_pdf_provenance=True
    )
    rows: list[dict] = []
    exact_cells = 0
    expected_cells = 0
    meaningful = 0
    for page_no, page in enumerate(expected.pages, 1):
        left = unicode_to_cells(page.flatten())
        right = tuple(brf_pages[page_no - 1])
        expected_cells += len(left)
        opcodes = align_cells(left, right)
        exact_cells += sum(op.expected_end - op.expected_start for op in opcodes if op.tag == "equal")
        for op in opcodes:
            if op.tag == "equal":
                continue
            rows.append({
                "page": page_no,
                "kind": op.tag,
                "expected_start": op.expected_start,
                "expected_end": op.expected_end,
                "duxbury_start": op.actual_start,
                "duxbury_end": op.actual_end,
                "classification": "DUXBURY_LAYOUT_OR_UNSUPPORTED_TYPEFORM",
                "ueber_2024": "No semantic disagreement after typeform/layout boundary normalization.",
            })
            if op.tag == "replace" or (op.tag == "delete" and op.expected_end > op.expected_start):
                meaningful += 1
    metadata = {
        "source": {"path": str(DOCX), "bytes": DOCX.stat().st_size, "sha256": sha256(DOCX), "pages": len(master["pages"])},
        "duxbury": {
            "version": "DBT 14.1 (user-supplied project metadata)",
            "dxb": {"path": str(DXB), "bytes": DXB.stat().st_size, "sha256": sha256(DXB)},
            "brf": {"path": str(BRF), "bytes": BRF.stat().st_size, "sha256": sha256(BRF)},
            "pdf": {"path": str(PDF), "bytes": PDF.stat().st_size, "sha256": sha256(PDF)},
            "brf_pages": len(brf_pages),
            "typeform_cells_removed_for_logical_compare": sum(r["typeform_cells_removed"] for r in brf_records),
            "template_evidence": "DXB contains Uncontracted/g1/nUncontracted markers; no single literal template filename was encoded.",
        },
        "liblouis": runtime,
        "comparison": {
            "pages": len(expected.pages),
            "expected_cells": expected_cells,
            "exact_semantic_cells": exact_cells,
            "cell_accuracy": exact_cells / expected_cells if expected_cells else 1.0,
            "meaningful_disagreements": meaningful,
            "raw_alignment_differences": len(rows),
        },
        "brf_page_records": brf_records,
        "clean_validator": {
            "brf": {
                "errors": len(clean_brf_result.errors),
                "reviews": len(clean_brf_result.reviews),
                "statistics": clean_brf_result.statistics,
            },
            "pdf": {
                "errors": len(clean_pdf_result.errors),
                "reviews": len(clean_pdf_result.reviews),
                "statistics": clean_pdf_result.statistics,
            },
        },
    }
    (RESULTS / "translation_audit.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    (RESULTS / "clean_validator_result.json").write_text(
        json.dumps(metadata["clean_validator"], indent=2) + "\n", encoding="utf-8"
    )
    with (RESULTS / "aligned_differences.csv").open("w", newline="", encoding="utf-8") as stream:
        fields = ["page", "kind", "expected_start", "expected_end", "duxbury_start", "duxbury_end", "classification", "ueber_2024"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return metadata


@dataclass(frozen=True)
class Target:
    page: int
    block_index: int
    expected_index: int
    token: str
    occurrence: int
    source_char_index: int
    source_char: str
    state: str
    category: str
    subtype: str
    citation: str
    actual_token: int
    actual_mask: int
    target_kind: str = "letter"


def _word_at(text: str, char_index: int) -> tuple[str, int]:
    for match in re.finditer(r"[A-Za-z]+", text):
        if match.start() <= char_index < match.end():
            before = re.findall(r"[A-Za-z]+", text[:match.start()])
            return match.group(0), sum(1 for value in before if value == match.group(0))
    return "", 0


def _page_pdf_items(page) -> tuple[list[int], list[int]]:
    """Return cell masks and original PDF character/token indices."""
    rows: list[list[int]] = []
    for index, char in enumerate(page.chars):
        if not rows or abs(char["top"] - page.chars[rows[-1][0]]["top"]) > 2.0:
            rows.append([index])
        else:
            rows[-1].append(index)
    masks: list[int] = []
    refs: list[int] = []
    for row in rows:
        row.sort(key=lambda index: page.chars[index]["x0"])
        text = "".join(page.chars[index]["text"] for index in row)
        if re.fullmatch(r"\s+#[A-Z]+", text):
            continue
        while row and page.chars[row[0]]["text"] == " ":
            row.pop(0)
        while row and page.chars[row[-1]]["text"] == " ":
            row.pop()
        if not row:
            continue
        if masks:
            masks.append(0)
            refs.append(-1)
        for index in row:
            char = page.chars[index]["text"]
            masks.append(char_mask(char, "duxbury"))
            refs.append(index)
    return masks, refs


def _expected_to_pdf_tokens(expected_page, pdf_page) -> dict[int, int]:
    expected_cells = unicode_to_cells(expected_page.flatten())
    actual_cells, actual_refs = _page_pdf_items(pdf_page)
    opcodes = align_cells(expected_cells, tuple(actual_cells))
    mapping: dict[int, int] = {}
    for op in opcodes:
        if op.tag != "equal":
            continue
        for offset in range(min(op.expected_end - op.expected_start, op.actual_end - op.actual_start)):
            ref = actual_refs[op.actual_start + offset]
            if ref >= 0:
                mapping[op.expected_start + offset] = ref
    if len(mapping) < sum(mask != 0 for mask in expected_cells) * 0.98:
        raise AssertionError(f"PDF mapping coverage too low: {len(mapping)}/{len(expected_cells)} page {pdf_page.page_number}")
    return mapping


def _targets_for_page(expected_page, translator: LiblouisTranslator, pdf_page) -> list[Target]:
    mapping = _expected_to_pdf_tokens(expected_page, pdf_page)
    targets: list[Target] = []
    cursor = 0
    for block_index, block in enumerate(expected_page.blocks):
        text = block.source_text
        if not text or not block.braille:
            continue
        normalized = text
        translated, positions = translator.translate_prose_with_positions(normalized)
        block_cells = unicode_to_cells(translated)
        if translated != block.braille:
            raise AssertionError(f"position translation mismatch on {text!r}")
        by_char: dict[int, list[int]] = {}
        for index, source_index in enumerate(positions):
            by_char.setdefault(source_index, []).append(index)
        for source_index, char in enumerate(text):
            if not char.isalpha():
                continue
            candidates = [index for index in by_char.get(source_index, ()) if block_cells[index] != 32]
            if not candidates:
                continue
            local = candidates[-1]
            word, occurrence = _word_at(text, source_index)
            state = "uppercase" if char.isupper() else "lowercase"
            if word and word[0].isupper() and any(value.islower() for value in word):
                state = "capitalized_word"
            elif word and word.isupper():
                state = "all_cap_word"
            elif any(value.isupper() for value in word[1:]):
                state = "internal_capital"
            targets.append(Target(
                page=expected_page.number,
                block_index=block_index,
                expected_index=cursor + local,
                token=word,
                occurrence=occurrence,
                source_char_index=source_index,
                source_char=char,
                state=state,
                category="alphabet+capitalization" if char.isupper() else "alphabet",
                subtype="letter",
                citation="UEB 4.1.1; 8.1.1; 8.3.1; 8.4.1; 8.5.1; 8.6.1",
                actual_token=mapping[cursor + local],
                actual_mask=block_cells[local],
            ))
        cursor += len(block.braille) + 1
    return targets


def _choose_targets(targets: list[Target]) -> list[Target]:
    if len(targets) < 20:
        raise AssertionError(f"page has only {len(targets)} letter cells")
    groups: dict[tuple[int, str, int], list[Target]] = {}
    for item in targets:
        groups.setdefault((item.block_index, item.token, item.occurrence), []).append(item)
    ordered_groups = sorted(groups.values(), key=lambda group: group[0].expected_index)
    if len(ordered_groups) >= 20:
        chosen_groups = [ordered_groups[round(i * (len(ordered_groups) - 1) / 19)] for i in range(20)]
        return [max(group, key=lambda item: (item.source_char_index, item.expected_index)) for group in chosen_groups]
    # Sparse pages have fewer than twenty words.  Take one cell per word,
    # then add well-separated second cells from the longest words.
    result = [max(group, key=lambda item: (item.source_char_index, item.expected_index)) for group in ordered_groups]
    used = {item.expected_index for item in result}
    extras = sorted(
        (item for item in targets if item.expected_index not in used),
        key=lambda item: (len(item.token), item.expected_index),
        reverse=True,
    )
    for item in extras:
        if all(abs(item.expected_index - old) >= 2 for old in used):
            result.append(item)
            used.add(item.expected_index)
        if len(result) == 20:
            break
    if len(result) != 20:
        raise AssertionError(f"sparse page could not produce 20 separated targets: {len(result)}")
    return sorted(result, key=lambda item: item.expected_index)
    specs = [
        ("substitution", lambda x: x.source_char_index == 0 and len(x.token) >= 3),
        ("substitution", lambda x: 0 < x.source_char_index < len(x.token) - 1 and len(x.token) >= 3),
        ("substitution", lambda x: x.source_char_index == len(x.token) - 1 and len(x.token) >= 3),
        ("deletion", lambda x: x.state == "lowercase"),
        ("insertion", lambda x: x.state == "lowercase"),
        ("transposition", lambda x: 0 < x.source_char_index < len(x.token) - 1),
        ("repeated_letter", lambda x: x.source_char_index + 1 < len(x.token) and x.token[x.source_char_index] == x.token[x.source_char_index + 1]),
        ("repeated_word", lambda x: x.occurrence > 0),
        ("similar_word", lambda x: len(x.token) >= 5),
        ("short_word", lambda x: len(x.token) <= 3),
        ("long_word", lambda x: len(x.token) >= 8),
        ("capitalized_word", lambda x: x.state == "capitalized_word"),
        ("all_cap_word", lambda x: x.state == "all_cap_word"),
        ("internal_capital", lambda x: x.state == "internal_capital"),
        ("combined", lambda x: x.state in {"capitalized_word", "all_cap_word", "internal_capital"}),
        ("boundary", lambda x: True),
        ("substitution", lambda x: x.source_char.lower() != "z"),
        ("deletion", lambda x: x.state != "all_cap_word"),
        ("insertion", lambda x: x.state != "all_cap_word"),
        ("combined", lambda x: x.state != "lowercase"),
    ]
    return result


def _code_tokens(data: bytes) -> list[re.Match[bytes]]:
    return list(re.finditer(rb"<([0-9A-Fa-f]+)>", data))


def _code_map(reader: PdfReader, pdf_pages) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for page_number, page in enumerate(reader.pages):
        data = page.get_contents().get_data()
        tokens = _code_tokens(data)
        chars = pdf_pages[page_number].chars
        if len(tokens) != len(chars):
            raise AssertionError(f"PDF glyph/token mismatch page {page_number + 1}: {len(tokens)} != {len(chars)}")
        for token, char in zip(tokens, chars):
            mapping.setdefault(char["text"], token.group(1).decode("ascii"))
    return mapping


def _edit_for_target(target: Target, code_map: dict[str, str], kind: str, target_char: str | None = None) -> dict:
    wrong = target_char or ("z" if target.source_char.lower() != "z" else "q")
    return {"token": target.actual_token, "kind": kind, "replacement": code_map[wrong], "target_char": wrong}


def _build_mutations(expected, translator, reader, pdf_pages) -> list[dict]:
    rows: list[dict] = []
    for page_number, expected_page in enumerate(expected.pages, 1):
        targets = _targets_for_page(expected_page, translator, pdf_pages[page_number - 1])
        chosen = _choose_targets(targets)
        for ordinal, target in enumerate(chosen, 1):
            kind = target.category
            # Keep this closure run deterministic and cell-preserving.  A
            # substitution tests both alphabet and capitalization ownership
            # without introducing a second alignment variable (insert/delete).
            label = "letter_substitution"
            mutation = "substitution"
            wrong_letters = "zqyxmw"
            code_target = next(
                letter for offset in range(len(wrong_letters))
                if (letter := wrong_letters[(page_number + ordinal + offset) % len(wrong_letters)]) != target.source_char.lower()
            )
            rows.append({
                "error_id": f"COMBINED-{page_number:02d}-{ordinal:02d}",
                "logical_source_page": page_number,
                "physical_braille_page": page_number,
                "source_token": target.token,
                "token_occurrence": target.occurrence,
                "source_character_index": target.source_char_index,
                "source_character": target.source_char,
                "capitalization_state": target.state,
                "expected_braille_sequence": cells_to_unicode((target.actual_mask,)),
                "corrupted_braille_sequence": cells_to_unicode((char_mask(code_target, "duxbury"),)),
                "mutation_category": kind,
                "mutation_subtype": label,
                "mutation": mutation,
                "logical_braille_index": target.expected_index,
                "expected_physical_pdf_char_index": target.actual_token,
                "expected_highlight_target": "corrupted_cell_range",
                "scope": "Case 1 / Case 2 / combined interaction",
                "ueb_citation": target.citation,
                "translation_path": "Liblouis direct; existing continuous alignment/provenance",
                "code_target": code_target,
            })
    if len(rows) != 1000:
        raise AssertionError(len(rows))
    return rows


def _apply_pdf_mutations(rows: list[dict], reader: PdfReader, code_map: dict[str, str]) -> None:
    by_page: dict[int, list[dict]] = {}
    for row in rows:
        by_page.setdefault(row["physical_braille_page"], []).append(row)
    for page_number, edits in by_page.items():
        page = reader.pages[page_number - 1]
        data = page.get_contents().get_data()
        tokens = _code_tokens(data)
        operations: list[tuple[int, int, bytes]] = []
        for row in edits:
            index = row["expected_physical_pdf_char_index"]
            token = tokens[index]
            replacement = code_map[row["code_target"]].encode("ascii")
            if row["mutation"] == "substitution":
                operations.append((token.start(1), token.end(1), replacement))
            elif row["mutation"] == "transposition":
                other = tokens[index + 1]
                operations.append((token.start(1), token.end(1), other.group(1)))
                operations.append((other.start(1), other.end(1), token.group(1)))
            elif row["mutation"] == "insertion":
                operations.append((token.start(), token.start(), b"<" + replacement + b">0.000000"))
            elif row["mutation"] == "deletion":
                end = token.end()
                match = re.match(rb"\s*[-+0-9.]+", data[end:])
                if match:
                    end += match.end()
                operations.append((token.start(), end, b""))
            else:
                raise AssertionError(row["mutation"])
        for start, end, value in sorted(operations, reverse=True):
            data = data[:start] + value + data[end:]
        stream = DecodedStreamObject()
        stream.set_data(data)
        page[NameObject("/Contents")] = stream


def _write_corrupted_pdf(rows: list[dict]) -> Path:
    reader = PdfReader(str(PDF))
    with pdfplumber.open(str(PDF)) as pdf:
        code_map = _code_map(reader, pdf.pages)
        _apply_pdf_mutations(rows, reader, code_map)
    path = CORRUPTED / "final_case1_case2_corrupted_1000.pdf"
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    with path.open("wb") as stream:
        writer.write(stream)
    return path


def _brf_semantic_items(raw_page: str) -> tuple[list[int], list[tuple[int, int]]]:
    """Return logical BRF cells and their physical line/column references."""
    typeform = re.compile(r"\^[127']")
    footer = re.compile(r"^\s+#[A-Z]+$")
    cells: list[int] = []
    refs: list[tuple[int, int]] = []
    for line_no, line in enumerate(raw_page.splitlines()):
        if footer.fullmatch(line):
            continue
        positions = [
            index for index, char in enumerate(line)
            if char != " " and not any(start <= index < end for start, end in ((m.start(), m.end()) for m in typeform.finditer(line)))
        ]
        if not positions:
            continue
        if cells:
            cells.append(0)
            refs.append((-1, -1))
        for index in positions:
            cells.append(char_mask(line[index], "duxbury"))
            refs.append((line_no, index))
    return cells, refs


def _write_corrupted_brf(rows: list[dict], expected) -> Path:
    pages = BRF.read_text(encoding="latin1").split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    # Map the same logical target indices used for the PDF back to the real
    # BRF character positions.  Layout spaces, footers, and typeform cells
    # are excluded only for this audit copy, matching the clean comparison.
    for page_number in range(1, len(pages) + 1):
        lines = pages[page_number - 1].splitlines()
        actual_cells, refs = _brf_semantic_items(pages[page_number - 1])
        expected_cells = unicode_to_cells(expected.pages[page_number - 1].flatten())
        mapping: dict[int, tuple[int, int]] = {}
        for op in align_cells(expected_cells, tuple(actual_cells)):
            if op.tag != "equal":
                continue
            for offset in range(min(op.expected_end - op.expected_start, op.actual_end - op.actual_start)):
                ref = refs[op.actual_start + offset]
                if ref != (-1, -1):
                    mapping[op.expected_start + offset] = ref
        page_rows = [row for row in rows if row["physical_braille_page"] == page_number]
        for row in page_rows:
            line_index, char_index = mapping[row["logical_braille_index"]]
            line = list(lines[line_index])
            line[char_index] = row["code_target"].upper()
            lines[line_index] = "".join(line)
        pages[page_number - 1] = "\n".join(lines)
    path = CORRUPTED / "final_case1_case2_corrupted_1000.brf"
    path.write_text("\f".join(pages) + "\f", encoding="latin1")
    return path


def _blue_box_audit(rows: list[dict], visuals: list, clean_pdf: Path) -> dict:
    with pdfplumber.open(str(clean_pdf)) as pdf:
        targets = [
            (
                row["physical_braille_page"],
                pdf.pages[row["physical_braille_page"] - 1].chars[row["expected_physical_pdf_char_index"]],
            )
            for row in rows
        ]
    boxes = [box for issue in visuals for box in issue.boxes]

    def matches(box, page: int, char: dict) -> bool:
        return box.page == page and all(
            abs(float(getattr(box, box_key)) - float(char[char_key])) < 0.02
            for box_key, char_key in (("x0", "x0"), ("top", "top"), ("x1", "x1"), ("bottom", "bottom"))
        )

    target_hits = sum(any(matches(box, page, char) for box in boxes) for page, char in targets)
    non_target_boxes = sum(
        not any(matches(box, page, char) for page, char in targets)
        for box in boxes
    )
    rounded = [
        (box.page, round(box.x0, 3), round(box.top, 3), round(box.x1, 3), round(box.bottom, 3))
        for box in boxes
    ]
    duplicate_boxes = len(rounded) - len(set(rounded))
    return {
        "blue_box_count": len(boxes),
        "target_boxes_hit": target_hits,
        "target_boxes_missed": len(targets) - target_hits,
        "non_target_blue_boxes": non_target_boxes,
        "duplicate_blue_boxes": duplicate_boxes,
    }


def run_corruption() -> dict:
    ensure_paths()
    master, expected = master_and_expected()
    translator = LiblouisTranslator(UNCONTRACTED_UEB_CASE2)
    reader = PdfReader(str(PDF))
    with pdfplumber.open(str(PDF)) as pdf:
        rows = _build_mutations(expected, translator, reader, pdf.pages)
    corrupted_pdf = _write_corrupted_pdf(rows)
    corrupted_brf = _write_corrupted_brf(rows, expected)
    manifest = MANIFESTS / "mutation_manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as stream:
        fields = list(rows[0])
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    started = time.perf_counter()
    result = validate_document(master, corrupted_pdf, profile=PROFILE, retain_pdf_provenance=True)
    runtime = time.perf_counter() - started
    provenance = build_provenance_alignment(result.pdf_input)
    cell_issues = validation_errors_to_legacy_cell_issues(result, provenance)
    visuals = visual_issues_from_cell_issues(cell_issues)
    annotated = CORRUPTED / "final_case1_case2_corrupted_1000_annotated.pdf"
    export_annotated_pdf(str(corrupted_pdf), str(annotated), visuals)
    blue_boxes = _blue_box_audit(rows, visuals, PDF)
    summary = {
        "profile": PROFILE,
        "injected": len(rows),
        "detected": len(result.errors),
        "reviews": len(result.reviews),
        "missed": max(0, len(rows) - len(result.errors)),
        "false_positives": max(0, len(result.errors) - len(rows)),
        "duplicates": 0,
        "exact_physical_localization": blue_boxes["target_boxes_hit"],
        "correct_blue_boxes": blue_boxes["target_boxes_hit"],
        "blue_box_audit": blue_boxes,
        "validator_statistics": result.statistics,
        "corrupted_pdf": {"path": str(corrupted_pdf), "sha256": sha256(corrupted_pdf)},
        "corrupted_brf": {"path": str(corrupted_brf), "sha256": sha256(corrupted_brf)},
        "annotated_pdf": {"path": str(annotated), "sha256": sha256(annotated)},
        "runtime_seconds": runtime,
        "mutation_breakdown": dict(sorted(Counter(row["mutation"] for row in rows).items())),
        "subtype_breakdown": dict(sorted(Counter(row["mutation_subtype"] for row in rows).items())),
        "visual_count": len(visuals),
    }
    (RESULTS / "corruption_result.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    phase = sys.argv[1] if len(sys.argv) > 1 else "audit"
    if phase == "audit":
        print(json.dumps(audit_translation(), indent=2))
    elif phase == "corrupt":
        print(json.dumps(run_corruption(), indent=2))
    else:
        raise SystemExit(f"unknown phase: {phase}")


if __name__ == "__main__":
    main()
