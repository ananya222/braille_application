"""Independent replay, PDF/BRF, source-map, and freeze gate for Case 4."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from braille_app.brf_parser import ascii_to_unicode_braille
from braille_app.translation.expected_document import generate_expected_braille
from braille_app.translation.liblouis_translator import LiblouisTranslator, vendored_metadata
from braille_app.translation.profiles import UNCONTRACTED_UEB_CASE4
from braille_app.translation.source_normalization import normalize_uncontracted_case4
from braille_app.translation.uncontracted_case4 import _translate_source_with_positions
from braille_app.validation.api import _docx_paragraph_dict

BASE = ROOT / "stress_test" / "uncontracted_case4_punctuation"
SOURCE = BASE / "source" / "case4_punctuation_clean.docx"
EXPECTED = BASE / "expected" / "case4_expected_metadata.json"
COVERAGE = BASE / "expected" / "coverage_manifest.csv"
CLEAN_PDF = BASE / "output" / "case4_clean.pdf"
CLEAN_BRF = BASE / "output" / "case4_clean.brf"
CORRUPTED_PDF = BASE / "output" / "case4_corrupted.pdf"
CORRUPTED_BRF = BASE / "output" / "case4_corrupted.brf"
MANIFEST = BASE / "manifest" / "case4_500_mutations.csv"
INTEGRITY = BASE / "manifest" / "fixture_integrity.json"
FREEZE = BASE / "manifest" / "case4_fixture_frozen.json"
VERIFICATION = BASE / "results" / "case4_fixture_verification.json"
REQUIRED = {
    "comma": 80, "period_full_stop": 80, "question_mark": 70,
    "exclamation_mark": 70, "colon": 60, "semicolon": 60,
    "punctuation_grade1": 40,
    "punctuation_capitalization_numeric_interactions": 20,
    "repeated_context_boundaries": 20,
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _pdf_pages(path: Path) -> list[list[str]]:
    pages = []
    with pdfplumber.open(path) as pdf:
        for page_index, page in enumerate(pdf.pages, 1):
            rows: list[list[dict]] = []
            for char in sorted(page.chars, key=lambda item: (item["top"], item["x0"])):
                if not rows or abs(char["top"] - rows[-1][0]["top"]) > 2:
                    rows.append([])
                rows[-1].append(char)
            lines = []
            for row in rows:
                row.sort(key=lambda item: item["x0"])
                if not all(len(c["text"]) == 1 and 0x2800 <= ord(c["text"]) <= 0x28FF for c in row):
                    raise AssertionError(f"Non-Braille text or furniture on PDF page {page_index}")
                lines.append("".join(c["text"] for c in row))
            pages.append(lines)
    return pages


def _brf_pages(path: Path) -> list[list[str]]:
    decoded = ascii_to_unicode_braille(path.read_text(encoding="latin1"))
    pages = [page.splitlines() for page in decoded.split("\f")]
    if not all(0x2800 <= ord(cell) <= 0x28FF for page in pages for line in page for cell in line):
        raise AssertionError(f"BRF contains non-braille cells: {path}")
    return pages


def _logical(pages: list[list[str]]) -> tuple[str, list[dict | None]]:
    stream, locations = [], []
    for pi, page in enumerate(pages, 1):
        for ri, line in enumerate(page, 1):
            for ci, cell in enumerate(line, 1):
                stream.append(cell)
                locations.append({"page": pi, "line": ri, "cell": ci})
            if ri < len(page) or pi < len(pages):
                stream.append("⠀")
                locations.append(None)
    return "".join(stream), locations


def _replay(expected: str, rows: list[dict]) -> str:
    tokens = list(expected)
    occupied = set()
    for row in sorted(rows, key=lambda item: item["expected_start"], reverse=True):
        start, source, operation = row["expected_start"], row["expected_cells"], row["operation"]
        width = len(source)
        footprint = range(start, start + max(1, width))
        if start < 0 or start > len(expected) or any(i in occupied for i in footprint):
            raise AssertionError(f"Invalid/overlapping target: {row['mutation_id']}")
        occupied.update(footprint)
        if expected[start:start + width] != source:
            raise AssertionError(f"Expected span mismatch: {row['mutation_id']}")
        actual = row["actual_cells"]
        if operation == "insert":
            if len(actual) != 1:
                raise AssertionError(f"Insertion must add one cell: {row['mutation_id']}")
            tokens[start:start] = list(actual)
        elif operation == "delete":
            if not width or actual:
                raise AssertionError(f"Malformed deletion: {row['mutation_id']}")
            del tokens[start:start + width]
        elif operation == "substitute":
            if width != 1 or len(actual) != 1 or actual == source:
                raise AssertionError(f"Malformed/no-op substitution: {row['mutation_id']}")
            tokens[start:start + width] = list(actual)
        elif operation == "transpose":
            if width != 2 or source[0] == source[1] or actual != source[::-1]:
                raise AssertionError(f"Malformed/no-op transposition: {row['mutation_id']}")
            tokens[start:start + width] = list(actual)
        else:
            raise AssertionError(f"Unknown operation {operation}: {row['mutation_id']}")
    return "".join(tokens)


def verify(freeze: bool = False) -> dict:
    required_paths = (SOURCE, EXPECTED, COVERAGE, CLEAN_PDF, CLEAN_BRF,
                      CORRUPTED_PDF, CORRUPTED_BRF, MANIFEST, INTEGRITY)
    if not all(path.is_file() for path in required_paths):
        raise FileNotFoundError("One or more canonical Case 4 fixture files are missing")
    frozen = json.loads(INTEGRITY.read_text(encoding="utf-8"))
    for key, path in (("source_sha256", SOURCE), ("expected_sha256", EXPECTED),
                      ("clean_pdf_sha256", CLEAN_PDF), ("clean_brf_sha256", CLEAN_BRF),
                      ("corrupted_pdf_sha256", CORRUPTED_PDF), ("corrupted_brf_sha256", CORRUPTED_BRF),
                      ("manifest_sha256", MANIFEST)):
        if _sha(path) != frozen[key]:
            raise AssertionError(f"Artifact hash mismatch: {key}")

    metadata = json.loads(EXPECTED.read_text(encoding="utf-8"))
    master = _docx_paragraph_dict(SOURCE)
    translator = LiblouisTranslator(UNCONTRACTED_UEB_CASE4)
    document = generate_expected_braille(master, UNCONTRACTED_UEB_CASE4, translator)
    if document.review_count or document.flatten() != metadata["expected_braille"]:
        raise AssertionError("Independent clean source translation differs from frozen expected stream")
    if metadata["runtime"] != vendored_metadata(UNCONTRACTED_UEB_CASE4):
        raise AssertionError("Vendored Liblouis runtime/table identity changed")
    for block in metadata["expected_blocks"]:
        normalize_uncontracted_case4(block["source"])
        braille, positions = _translate_source_with_positions(block["source"], translator)
        if braille != block["braille"] or len(braille) != len(positions):
            raise AssertionError(f"Expected block/source map mismatch at block {block['source_block']}")

    clean_pdf_pages, clean_brf_pages = _pdf_pages(CLEAN_PDF), _brf_pages(CLEAN_BRF)
    if clean_pdf_pages != clean_brf_pages:
        raise AssertionError("Clean BRF and PDF physical cells differ")
    clean_stream, _ = _logical(clean_pdf_pages)
    if clean_stream != metadata["expected_braille"]:
        raise AssertionError("Clean PDF logical stream differs from expected translation")

    pdf_pages, brf_pages = _pdf_pages(CORRUPTED_PDF), _brf_pages(CORRUPTED_BRF)
    if pdf_pages != brf_pages:
        raise AssertionError("Corrupted BRF and PDF physical cells differ")
    pdf_stream, locations = _logical(pdf_pages)
    with MANIFEST.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        row["expected_start"] = int(row["expected_start"])
        row["target_expected_index"] = int(row["target_expected_index"])
        row["source_offset"] = int(row["source_offset"])
        row["source_block"] = int(row["source_block"])
        row["actual_locations"] = json.loads(row["actual_locations"])
        row["location"] = json.loads(row["location"])
    if len(rows) != 500 or len({row["mutation_id"] for row in rows}) != 500:
        raise AssertionError("Manifest must contain exactly 500 unique actions")
    counts = dict(Counter(row["family"] for row in rows))
    if counts != REQUIRED:
        raise AssertionError(f"Required family totals differ: {counts}")

    method_counts = Counter(row["method"] for row in rows)
    expected_by_method = {"delete": 127, "insert": 75, "duplicate": 52,
                          "substitute": 140, "transpose": 106}
    if dict(method_counts) != expected_by_method:
        raise AssertionError(f"Method distribution changed: {dict(method_counts)}")

    for row in rows:
        block_index, source_offset = row["source_block"], row["source_offset"]
        if not 0 <= block_index < len(metadata["expected_blocks"]):
            raise AssertionError(f"Invalid source block: {row['mutation_id']}")
        block = metadata["expected_blocks"][block_index]
        if not 0 <= source_offset < len(block["source"]):
            raise AssertionError(f"Invalid source offset: {row['mutation_id']}")
        if block["source"][source_offset] != row["source_char"]:
            raise AssertionError(f"Source-character mapping mismatch: {row['mutation_id']}")
        if not 1 <= len(row["actual_locations"]) <= 2:
            if row["operation"] != "delete" or row["actual_locations"]:
                raise AssertionError(f"Physical target missing/invalid: {row['mutation_id']}")
        if row["operation"] == "delete" and row["actual_locations"]:
            raise AssertionError(f"Deletion unexpectedly owns a surviving cell: {row['mutation_id']}")
        if row["operation"] == "transpose" and len(row["actual_locations"]) != 2:
            raise AssertionError(f"Transposition must resolve to two actual cells: {row['mutation_id']}")
        if row["operation"] not in {"delete", "transpose"} and len(row["actual_locations"]) != 1:
            raise AssertionError(f"Single-cell action has wrong physical target count: {row['mutation_id']}")
        physical = []
        for loc in row["actual_locations"]:
            p, l, c = int(loc["page"]), int(loc["line"]), int(loc["cell"])
            if not (1 <= p <= len(pdf_pages) and 1 <= l <= len(pdf_pages[p - 1])
                    and 1 <= c <= len(pdf_pages[p - 1][l - 1])):
                raise AssertionError(f"Physical location out of bounds: {row['mutation_id']}")
            physical.append(pdf_pages[p - 1][l - 1][c - 1])
        if physical and "".join(physical) != row["actual_cells"]:
            raise AssertionError(f"Manifest/PDF target cells disagree: {row['mutation_id']}")
        if row["method"] == "duplicate" and row["operation"] != "insert":
            raise AssertionError(f"Duplicate method is not represented as an insertion: {row['mutation_id']}")

    simulated = _replay(metadata["expected_braille"], rows)
    if simulated != pdf_stream:
        raise AssertionError("Manifest replay differs from corrupted PDF logical stream")
    delta = len(simulated) - len(metadata["expected_braille"])
    if delta != 0 or delta != frozen["length_delta"]:
        raise AssertionError(f"Unexpected net stream delta: {delta}")
    expected_actions = {
        "source_docx": SOURCE, "expected_metadata": EXPECTED, "coverage_manifest": COVERAGE,
        "clean_pdf": CLEAN_PDF, "clean_brf": CLEAN_BRF,
        "corrupted_pdf": CORRUPTED_PDF, "corrupted_brf": CORRUPTED_BRF,
        "mutation_manifest": MANIFEST, "fixture_integrity": INTEGRITY,
    }
    result = {
        "case": 4, "actions": len(rows), "family_counts": counts,
        "method_counts": dict(method_counts), "expected_stream_cells": len(metadata["expected_braille"]),
        "simulated_stream_cells": len(simulated), "net_cell_delta": delta,
        "clean_pages": len(clean_pdf_pages), "corrupted_pages": len(pdf_pages),
        "clean_pdf_brf_exact": True, "corrupted_pdf_brf_exact": True,
        "clean_expected_stream_exact": True, "manifest_replay_exact": True,
        "all_targets_resolve": True, "all_sources_resolve": True,
        "out_of_scope_constructs": 0, "footer_or_control_targets": 0,
        "hashes": {key: _sha(path) for key, path in expected_actions.items()},
        "physical_layout": metadata["physical_layout"],
    }
    if VERIFICATION.exists():
        if json.loads(VERIFICATION.read_text(encoding="utf-8")) != result:
            raise FileExistsError("Verification output exists with different contents")
    else:
        VERIFICATION.parent.mkdir(parents=True, exist_ok=True)
        VERIFICATION.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    if freeze:
        if FREEZE.exists():
            raise FileExistsError(f"Fixture is already frozen: {FREEZE}")
        freeze_record = {**result, "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
                         "status": "FROZEN_VERIFIED"}
        FREEZE.write_text(json.dumps(freeze_record, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", action="store_true")
    args = parser.parse_args()
    print(json.dumps(verify(freeze=args.freeze), indent=2))
