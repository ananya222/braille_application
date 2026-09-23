"""Independently audit the Case 3 fixture before freezing or running it."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from braille_app.brf_parser import ascii_to_unicode_braille

BASE = ROOT / "stress_test" / "uncontracted_case3_numbers"
SOURCE = BASE / "source" / "case3_numbers_clean.docx"
EXPECTED = BASE / "expected" / "case3_expected_metadata.json"
COVERAGE = BASE / "expected" / "coverage_manifest.csv"
CLEAN_PDF = BASE / "output" / "case3_clean.pdf"
CLEAN_BRF = BASE / "output" / "case3_clean.brf"
CORRUPTED_PDF = BASE / "output" / "case3_corrupted.pdf"
CORRUPTED_BRF = BASE / "output" / "case3_corrupted.brf"
MANIFEST = BASE / "manifest" / "case3_500_mutations.csv"
INTEGRITY = BASE / "manifest" / "fixture_integrity.json"
FREEZE = BASE / "manifest" / "case3_fixture_frozen.json"
VERIFICATION = BASE / "results" / "case3_fixture_verification.json"

REQUIRED_FAMILIES = {
    "numeric_indicators": 70,
    "digit_substitutions": 60,
    "deletions": 50,
    "insertions": 50,
    "transpositions": 40,
    "numeric_mode_transitions": 60,
    "letter_after_number_grade1": 50,
    "uppercase_after_number": 40,
    "numeric_punctuation": 30,
    "repeated_numeric_context": 25,
    "boundaries": 25,
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _brf_pages(path: Path) -> list[list[str]]:
    decoded = ascii_to_unicode_braille(path.read_text(encoding="latin1"))
    return [page.splitlines() for page in decoded.split("\f")]


def _pdf_pages(path: Path) -> list[list[str]]:
    result = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            rows: list[list[dict]] = []
            for char in sorted(page.chars, key=lambda item: (item["top"], item["x0"])):
                if not rows or abs(char["top"] - rows[-1][0]["top"]) > 2.0:
                    rows.append([])
                rows[-1].append(char)
            lines = []
            for row in rows:
                row.sort(key=lambda item: item["x0"])
                chars = [item["text"] for item in row]
                if not all(len(char) == 1 and 0x2800 <= ord(char) <= 0x28FF for char in chars):
                    raise AssertionError(f"Non-Braille or non-cell PDF text on page {page.page_number}")
                lines.append("".join(chars))
            result.append(lines)
    return result


def _logical_stream(pages: list[list[str]]) -> tuple[str, list[dict | None]]:
    """Rejoin only physical line/page boundaries as the layout blank they replace."""
    chars: list[str] = []
    locations: list[dict | None] = []
    for page_index, page in enumerate(pages, 1):
        for line_index, line in enumerate(page, 1):
            for cell_index, char in enumerate(line, 1):
                chars.append(char)
                locations.append({"page": page_index, "line": line_index, "cell": cell_index})
            if line_index < len(page) or page_index < len(pages):
                chars.append("⠀")
                locations.append(None)
    return "".join(chars), locations


def _source_map(blocks: list[dict]) -> list[tuple[str, str, int] | None]:
    mapped: list[tuple[str, str, int] | None] = []
    for block_index, block in enumerate(blocks):
        mapped.extend(
            (block["source"], block["source"][offset], offset)
            for offset in block["source_positions"]
        )
        if block_index + 1 < len(blocks):
            mapped.append(None)
    return mapped


def _simulate(base: str, rows: list[dict]) -> tuple[list[dict], set[int]]:
    tokens = [
        {"cell": char, "origin": index, "mutation_id": ""}
        for index, char in enumerate(base)
    ]
    deleted_origins: set[int] = set()
    footprints: set[int] = set()
    for row in rows:
        start = int(row["expected_start"])
        expected = list(row["expected_cells"])
        operation = row["operation"]
        width = len(expected)
        if start < 0 or start > len(base) or (operation != "insert" and not width):
            raise AssertionError(f"Invalid expected span for {row['mutation_id']}")
        footprint = range(start, start + max(1, width))
        if any(index in footprints for index in footprint):
            raise AssertionError(f"Overlapping target in {row['mutation_id']}")
        footprints.update(footprint)
        if base[start:start + width] != "".join(expected):
            raise AssertionError(f"Manifest expected cells disagree at {row['mutation_id']}")

    for row in sorted(rows, key=lambda item: int(item["expected_start"]), reverse=True):
        start = int(row["expected_start"])
        expected = list(row["expected_cells"])
        actual = list(row["actual_cells"])
        operation = row["operation"]
        mutation_id = row["mutation_id"]
        if operation == "insert":
            if expected or len(actual) != 1:
                raise AssertionError(f"Invalid insertion shape in {mutation_id}")
            tokens.insert(start, {"cell": actual[0], "origin": None, "mutation_id": mutation_id})
        elif operation == "delete":
            if len(expected) != 1 or actual:
                raise AssertionError(f"Invalid deletion shape in {mutation_id}")
            deleted_origins.add(start)
            del tokens[start:start + 1]
        elif operation == "substitute":
            if len(expected) != 1 or len(actual) != 1 or expected == actual:
                raise AssertionError(f"Invalid/no-op substitution in {mutation_id}")
            tokens[start]["cell"] = actual[0]
            tokens[start]["mutation_id"] = mutation_id
        elif operation == "transpose":
            if len(expected) != 2 or len(actual) != 2 or expected[0] == expected[1]:
                raise AssertionError(f"Invalid/no-op transposition in {mutation_id}")
            if actual != expected[::-1]:
                raise AssertionError(f"Transposition is not an adjacent swap in {mutation_id}")
            tokens[start]["cell"], tokens[start + 1]["cell"] = actual
            tokens[start]["mutation_id"] = mutation_id
            tokens[start + 1]["mutation_id"] = mutation_id
        else:
            raise AssertionError(f"Unknown operation {operation!r}")
    return tokens, deleted_origins


def _check_scope(row: dict, source_entry, source_texts: list[str]) -> None:
    family = row["family"]
    start = int(row["expected_start"])
    expected = row["expected_cells"]
    actual = row["actual_cells"]
    if source_entry is None:
        raise AssertionError(f"Mutation {row['mutation_id']} targets a block separator")
    text, source_char, offset = source_entry
    if row["source_char"] != source_char:
        raise AssertionError(f"Source map mismatch in {row['mutation_id']}")
    if any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ,.-" for char in text):
        raise AssertionError("Source corpus contains an unsupported Case 3 character")

    if family == "numeric_indicators" and expected and expected != "⠼":
        raise AssertionError(f"Numeric-indicator action has wrong target in {row['mutation_id']}")
    if family == "numeric_mode_transitions":
        target = actual if row["operation"] == "insert" else expected
        if target not in {"⠼", "⠤", "⠰"}:
            raise AssertionError(f"Numeric-mode transition has wrong target in {row['mutation_id']}")
    if family == "letter_after_number_grade1" and expected != "⠰":
        raise AssertionError(f"Grade 1 action does not target its indicator in {row['mutation_id']}")
    if family == "uppercase_after_number":
        if row["operation"] == "transpose" and expected != "⠰⠠":
            raise AssertionError(f"Capital ordering action has wrong target in {row['mutation_id']}")
        if row["operation"] == "delete" and expected != "⠠":
            raise AssertionError(f"Capital deletion does not target the cap cell in {row['mutation_id']}")
        if not re.search(r"\d[-–][A-Za-z]$", text[max(0, offset - 3):offset + 1]):
            raise AssertionError(f"Capital-after-number mutation is not in a hyphen suffix: {row['mutation_id']}")
    if family == "numeric_punctuation":
        if source_char not in {",", "."} or offset == 0 or offset + 1 >= len(text):
            raise AssertionError(f"Numeric punctuation action is outside a numeric context: {row['mutation_id']}")
        if not text[offset - 1].isdigit() or not text[offset + 1].isdigit():
            raise AssertionError(f"Punctuation is not between digits in {row['mutation_id']}")
    if family == "repeated_numeric_context":
        match = next((item for item in re.finditer(r"[0-9]+(?:[,.][0-9]+)*", text)
                      if item.start() <= offset < item.end()), None)
        if match is None or sum(text.count(match.group()) for text in source_texts) < 2:
            raise AssertionError(f"Repeated-context action is not in a repeated number: {row['mutation_id']}")
    if family == "boundaries":
        if row["subtype"] not in {
            "line edge numeric mutation", "page edge numeric mutation",
            "paragraph edge numeric mutation",
        }:
            raise AssertionError(f"Unclassified numeric boundary in {row['mutation_id']}")


def verify_and_freeze() -> dict:
    if FREEZE.exists():
        raise FileExistsError(f"Refusing to rewrite frozen Case 3 fixture record: {FREEZE}")
    metadata = json.loads(EXPECTED.read_text(encoding="utf-8"))
    integrity = json.loads(INTEGRITY.read_text(encoding="utf-8"))
    with MANIFEST.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        row["expected_start"] = int(row["expected_start"])
        row["initial_page"] = int(row["initial_page"])
        row["initial_line"] = int(row["initial_line"])
        row["initial_cell"] = int(row["initial_cell"])
        row["actual_locations"] = json.loads(row["actual_locations"])

    base = metadata["expected_braille"]
    source_map = _source_map(metadata["expected_blocks"])
    if len(source_map) != len(base) or any(char is not None and source_map[i] is None
                                            for i, char in enumerate(base) if char != "⠀"):
        raise AssertionError("Expected source-position map is incomplete")
    if sha256(SOURCE) != metadata["source_sha256"]:
        raise AssertionError("Clean source changed after expected metadata generation")
    if len(rows) != 500 or len({row["mutation_id"] for row in rows}) != 500:
        raise AssertionError("Manifest must contain 500 unique logical mutation IDs")
    expected_ids = {f"C3-{index:04d}" for index in range(1, 501)}
    if {row["mutation_id"] for row in rows} != expected_ids:
        raise AssertionError("Mutation IDs are incomplete or malformed")
    family_counts = dict(Counter(row["family"] for row in rows))
    if family_counts != REQUIRED_FAMILIES:
        raise AssertionError(f"Wrong family distribution: {family_counts}")

    source_texts = [block["source"] for block in metadata["expected_blocks"]]
    supported = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ,.-")
    if any(char not in supported for text in source_texts for char in text):
        raise AssertionError("Source corpus contains an unsupported Case 3 character")
    for row in rows:
        index = row["expected_start"]
        _check_scope(row, source_map[index], source_texts)
    if Counter(row["subtype"] for row in rows if row["family"] == "boundaries") != Counter({
        "line edge numeric mutation": 15,
        "page edge numeric mutation": 5,
        "paragraph edge numeric mutation": 5,
    }):
        raise AssertionError("Boundary family lacks the required line/page/paragraph spread")

    clean_brf = _brf_pages(CLEAN_BRF)
    clean_pdf = _pdf_pages(CLEAN_PDF)
    actual_brf = _brf_pages(CORRUPTED_BRF)
    actual_pdf = _pdf_pages(CORRUPTED_PDF)
    if clean_pdf != clean_brf or actual_pdf != actual_brf:
        raise AssertionError("PDF glyph-cell streams do not exactly match the BRF physical pages")
    if _logical_stream(clean_brf)[0] != base:
        raise AssertionError("Clean BRF does not encode the generated expected stream")

    simulated, deleted_origins = _simulate(base, rows)
    simulated_stream = "".join(token["cell"] for token in simulated)
    actual_stream, actual_locations = _logical_stream(actual_brf)
    if simulated_stream != actual_stream:
        raise AssertionError("Corrupted PDF/BRF stream differs from independent manifest replay")
    if len(simulated) - len(base) != 105 - 132:
        raise AssertionError("Insert/delete stream length delta does not reconcile")
    if len(deleted_origins) != 132:
        raise AssertionError("Deletion actions did not remove 132 unique expected cells")

    clean_rows = clean_brf
    id_locations: dict[str, list[dict]] = {}
    for token_index, token in enumerate(simulated):
        mutation_id = token["mutation_id"]
        if mutation_id:
            location = actual_locations[token_index]
            if location is None:
                raise AssertionError(f"Changed cell has no PDF location: {mutation_id}")
            id_locations.setdefault(mutation_id, []).append(location)

    for row in rows:
        page, line, cell = row["initial_page"], row["initial_line"], row["initial_cell"]
        expected = row["expected_cells"]
        physical = clean_rows[page - 1][line - 1]
        if expected and physical[cell - 1:cell - 1 + len(expected)] != expected:
            raise AssertionError(f"Clean physical target differs from the manifest: {row['mutation_id']}")
        found = id_locations.get(row["mutation_id"], [])
        if row["operation"] == "delete":
            if found or row["actual_locations"]:
                raise AssertionError(f"Deletion has a rendered target glyph: {row['mutation_id']}")
        elif found != row["actual_locations"]:
            raise AssertionError(f"Manifest/PDF physical cell index mismatch: {row['mutation_id']}")
        actual_at_locations = "".join(
            actual_brf[location["page"] - 1][location["line"] - 1][location["cell"] - 1]
            for location in found
        )
        if actual_at_locations != row["actual_cells"]:
            raise AssertionError(f"Manifest actual locations contain wrong cells: {row['mutation_id']}")
        if row["family"] == "boundaries":
            subtype = row["subtype"]
            if subtype == "line edge numeric mutation":
                if cell > 3 and cell < metadata["physical_layout"]["columns"] - 2:
                    raise AssertionError(f"Not at a line edge: {row['mutation_id']}")
            elif subtype == "page edge numeric mutation":
                if line not in {1, metadata["physical_layout"]["rows_per_page"]}:
                    raise AssertionError(f"Not at a page edge: {row['mutation_id']}")
            else:
                _text, _char, offset = source_map[row["expected_start"]]
                source = source_map[row["expected_start"]][0]
                if not (offset <= 3 or len(source) - offset <= 4):
                    raise AssertionError(f"Not at a paragraph edge: {row['mutation_id']}")

    files = {
        "source_docx": SOURCE,
        "expected_metadata": EXPECTED,
        "coverage_manifest": COVERAGE,
        "clean_pdf": CLEAN_PDF,
        "clean_brf": CLEAN_BRF,
        "corrupted_pdf": CORRUPTED_PDF,
        "corrupted_brf": CORRUPTED_BRF,
        "mutation_manifest": MANIFEST,
        "generator_integrity": INTEGRITY,
    }
    hashes = {key: sha256(path) for key, path in files.items()}
    for key, expected_hash in {
        "source_docx": integrity["source_sha256"],
        "clean_pdf": integrity["clean_pdf_sha256"],
        "clean_brf": integrity["clean_brf_sha256"],
        "corrupted_pdf": integrity["corrupted_pdf_sha256"],
        "corrupted_brf": integrity["corrupted_brf_sha256"],
        "mutation_manifest": integrity["manifest_sha256"],
    }.items():
        if hashes[key] != expected_hash:
            raise AssertionError(f"Generator hash does not reconcile for {key}")

    result = {
        "status": "PASS",
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "logical_actions": len(rows),
        "family_counts": family_counts,
        "operation_counts": dict(Counter(row["operation"] for row in rows)),
        "net_cell_delta": len(simulated) - len(base),
        "distinct_initial_physical_lines": len({
            (row["initial_page"], row["initial_line"]) for row in rows
        }),
        "physical_pages": len(actual_brf),
        "pdf_matches_brf_physical_cells": True,
        "manifest_replay_matches_corrupted_logical_stream": True,
        "all_mutated_cells_match_manifest_locations": True,
        "clean_logical_stream_matches_expected": True,
        "hashes": hashes,
    }
    VERIFICATION.parent.mkdir(parents=True, exist_ok=True)
    VERIFICATION.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    FREEZE.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(verify_and_freeze(), ensure_ascii=False, indent=2))
