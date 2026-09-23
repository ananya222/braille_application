"""Independently match frozen Case 3 actions to validator findings and PDF cells."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "stress_test" / "final_case1_case2_alphabet_capitalization" / "scripts"))

from braille_app.visual_annotations import group_provenance_boxes
from evaluate_frozen_diverse import identical_run

BASE = ROOT / "stress_test" / "uncontracted_case3_numbers"
SOURCE = BASE / "source" / "case3_numbers_clean.docx"
PDF = BASE / "output" / "case3_corrupted.pdf"
BRF = BASE / "output" / "case3_corrupted.brf"
FREEZE = BASE / "manifest" / "case3_fixture_frozen.json"
MANIFEST = BASE / "manifest" / "case3_500_mutations.csv"
RESULT = BASE / "results" / "case3_validation_result_after_boundary_refinement.json"
OUTPUT = BASE / "results" / "case3_observable_evaluation_after_boundary_refinement.json"
OUTCOMES_CSV = BASE / "results" / "case3_mutation_outcomes_after_boundary_refinement.csv"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _pdf_grid(path: Path) -> tuple[list[list[list[dict]]], list[dict | None]]:
    pages: list[list[list[dict]]] = []
    logical_locations: list[dict | None] = []
    with pdfplumber.open(path) as document:
        for page_index, page in enumerate(document.pages, 1):
            rows: list[list[dict]] = []
            for char in sorted(page.chars, key=lambda item: (item["top"], item["x0"])):
                if not rows or abs(char["top"] - rows[-1][0]["top"]) > 2.0:
                    rows.append([])
                rows[-1].append(char)
            for row in rows:
                row.sort(key=lambda item: item["x0"])
                if not all(len(c["text"]) == 1 and 0x2800 <= ord(c["text"]) <= 0x28FF for c in row):
                    raise AssertionError(f"Non-Braille text on corrupted PDF page {page_index}")
            pages.append(rows)
            for line_index, row in enumerate(rows):
                for cell_index, char in enumerate(row, 1):
                    logical_locations.append({"page": page_index, "line": line_index + 1, "cell": cell_index})
                if line_index + 1 < len(rows) or page_index < len(document.pages):
                    logical_locations.append(None)
    return pages, logical_locations


def _replay(base: str, rows: list[dict]) -> list[dict]:
    tokens = [{"cell": char, "origin": index} for index, char in enumerate(base)]
    for row in sorted(rows, key=lambda item: item["expected_start"], reverse=True):
        start = row["expected_start"]
        expected, actual, operation = row["expected_cells"], row["actual_cells"], row["operation"]
        if base[start:start + len(expected)] != expected:
            raise AssertionError(f"Manifest source span mismatch: {row['mutation_id']}")
        if operation == "insert":
            tokens[start:start] = [{"cell": char, "origin": None} for char in actual]
        elif operation == "delete":
            del tokens[start:start + len(expected)]
        elif operation in {"substitute", "transpose"}:
            tokens[start:start + len(expected)] = [
                {"cell": char, "origin": None} for char in actual
            ]
        else:
            raise AssertionError(f"Unexpected operation {operation!r}")
    return tokens


def _loc_char(grid, location):
    return grid[location["page"] - 1][location["line"] - 1][location["cell"] - 1]


def _geometry(value: dict, page: int | None = None) -> tuple:
    return (
        int(value.get("page", page or 0)),
        *(round(float(value[key]), 3) for key in ("x0", "x1", "top", "bottom")),
    )


def _box_key(value: dict) -> tuple:
    return (
        int(value["page"]),
        *(round(float(value[key]), 2) for key in ("x0", "x1", "top", "bottom")),
    )


def _expected_span(row: dict) -> tuple[int, int]:
    start = row["expected_start"]
    return start, start + len(row["expected_cells"])


def _shape_matches(operation: str, issue: dict) -> bool:
    expected, actual = issue["expected_braille"], issue["actual_braille"]
    if operation == "insert":
        return not expected and len(actual) == 1
    if operation == "delete":
        return len(expected) == 1 and not actual
    if operation == "transpose":
        return len(expected) == len(actual) == 2
    return len(expected) == len(actual) == 1


def _semantic_cell(line: list[dict], index: int) -> bool:
    char = line[index]
    if char["text"] in {"⠀", "^", "#"} or (index and line[index - 1]["text"] == "^"):
        return False
    return not any(other["text"] == "#" and abs(other["top"] - char["top"]) < 2.5 for other in line)


def _deletion_anchor(row: dict, gap: int, line_positions: dict, grid: list,
                     locations: list[dict | None]) -> tuple[dict, dict]:
    """Mirror the product's same-line next-semantic-cell deletion anchor."""
    location = locations[gap] if gap < len(locations) else None
    if location is None and gap:
        location = locations[gap - 1]
    if location is None:
        raise AssertionError(f"No physical line for deletion gap: {row['mutation_id']}")
    key = (int(location["page"]), int(location["line"]))
    positions = line_positions.get(key, ())
    following = []
    preceding = []
    for stream_index, location in positions:
        char = _loc_char(grid, location)
        if not _semantic_cell(grid[key[0] - 1][key[1] - 1], location["cell"] - 1):
            continue
        (following if stream_index >= gap else preceding).append((location, char))
    if following:
        return following[0]
    if preceding:
        return preceding[-1]
    raise AssertionError(f"No same-line semantic deletion anchor: {row['mutation_id']}")


def _box_matches_cell(box: dict, cell: dict, page: int) -> bool:
    return int(box.get("page", page)) == page and all(
        abs(float(box[key]) - float(cell[key])) < .02
        for key in ("x0", "x1", "top", "bottom")
    )


def _identical_insertion_proof(issue: dict, row: dict, grid: list) -> dict | None:
    """Accept only an indistinguishable inserted cell in its intact visual run."""
    if row["operation"] != "insert" or len(row["actual_locations"]) != 1:
        return None
    location = row["actual_locations"][0]
    page, line_no, cell_no = int(location["page"]), int(location["line"]), int(location["cell"])
    line = grid[page - 1][line_no - 1]
    run = identical_run(line, cell_no - 1)
    if len(run) < 2:
        return None
    target_char = line[cell_no - 1]["text"]
    if (issue["expected_braille"] or issue["actual_braille"] != [ord(target_char) - 0x2800]
        or int(issue.get("actual_page_number") or issue.get("braille_page") or page) != page
        or abs(issue["span"].get("expected_start", -10000) - row["expected_start"]) > len(run)
        or len(issue["provenance_cells"]) != 1 or len(issue["boxes"]) != 1):
        return None
    provenance = issue["provenance_cells"][0]
    if int(provenance.get("page", page)) != page or not any(
        _geometry(provenance, page) == _geometry(line[index], page) for index in run
    ) or not _box_matches_cell(issue["boxes"][0], provenance, page):
        return None
    return {"kind": "identical_run_insertion", "page": page, "line": line_no,
            "run_cells": list(run), "finding_cell": provenance}


def _identical_deletion_proof(issue: dict, row: dict, metadata: dict, grid: list,
                              target: list[tuple[dict, dict]]) -> dict | None:
    """Prove one removed cell from an otherwise intact same-line identical run."""
    if (row["operation"] != "delete" or issue["actual_braille"]
        or len(issue["expected_braille"]) != 1 or len(issue["provenance_cells"]) != 1
        or len(issue["boxes"]) != 1 or len(target) != 1):
        return None
    start, end = issue["span"].get("expected_start", -1), issue["span"].get("expected_end", -1)
    index = row["expected_start"]
    if end != start + 1:
        return None
    block = next((item for item in metadata["expected_blocks"]
                  if item["expected_start"] <= index < item["expected_end"]), None)
    if block is None or not block["expected_start"] <= start < block["expected_end"]:
        return None
    block_start, block_end = block["expected_start"], block["expected_end"]
    expected = metadata["expected_braille"]
    mask_char = expected[index]
    mask = ord(mask_char) - 0x2800
    if not mask or issue["expected_braille"] != [mask] or not block_start <= start < block_end:
        return None
    left, right = index, index + 1
    while left > block_start and expected[left - 1] == mask_char:
        left -= 1
    while right < block_end and expected[right] == mask_char:
        right += 1
    if right - left < 2 or not left <= start < right:
        return None

    page, line_no = int(target[0][0]["page"]), int(target[0][0]["line"])
    if page < 1 or line_no < 1 or page > len(grid) or line_no > len(grid[page - 1]):
        return None
    line = grid[page - 1][line_no - 1]
    provenance = issue["provenance_cells"][0]
    anchor_indices = [i for i, char in enumerate(line)
                      if _geometry(char, page) == _geometry(provenance, page)]
    if len(anchor_indices) != 1:
        return None
    anchor = anchor_indices[0]
    if line[anchor]["text"] == mask_char:
        seed = anchor
    elif anchor > 0 and line[anchor - 1]["text"] == mask_char:
        seed = anchor - 1
    else:
        return None
    run = identical_run(line, seed)
    if len(run) != right - left - 1:
        return None

    allowed = list(run)
    following = run[-1] + 1
    if (following < len(line) and _semantic_cell(line, following)
        and abs(line[following]["top"] - line[run[-1]]["top"]) < 2.5
        and line[following]["x0"] - line[run[-1]]["x1"] <= 3):
        allowed.append(following)
    target_location = target[0][0]
    if (int(target_location["page"]) != page or int(target_location["line"]) != line_no
        or target_location["cell"] - 1 not in allowed
        or not _box_matches_cell(issue["boxes"][0], provenance, page)):
        return None
    return {"kind": "identical_run_deletion", "page": page, "line": line_no,
            "expected_run": [left, right], "actual_run_cells": list(run),
            "allowed_anchor_cells": allowed, "finding_cell": provenance}


def evaluate() -> dict:
    if OUTPUT.exists() or OUTCOMES_CSV.exists():
        raise FileExistsError("Refusing to overwrite the frozen Case 3 evaluation")
    frozen = json.loads(FREEZE.read_text(encoding="utf-8"))
    validation = json.loads(RESULT.read_text(encoding="utf-8"))
    if validation["source_sha256"] != frozen["hashes"]["source_docx"] or _sha(SOURCE) != frozen["hashes"]["source_docx"]:
        raise AssertionError("Frozen source hash mismatch")
    if validation["corrupted_pdf_sha256"] != frozen["hashes"]["corrupted_pdf"] or _sha(PDF) != frozen["hashes"]["corrupted_pdf"]:
        raise AssertionError("Frozen corrupted PDF hash mismatch")
    if _sha(BRF) != frozen["hashes"]["corrupted_brf"]:
        raise AssertionError("Frozen corrupted BRF hash mismatch")
    if _sha(MANIFEST) != frozen["hashes"]["mutation_manifest"]:
        raise AssertionError("Frozen mutation manifest hash mismatch")

    with MANIFEST.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        row["expected_start"] = int(row["expected_start"])
        row["initial_page"] = int(row["initial_page"])
        row["initial_line"] = int(row["initial_line"])
        row["expected_cells"] = row["expected_cells"]
        row["actual_cells"] = row["actual_cells"]
        row["actual_locations"] = json.loads(row["actual_locations"])
    if len(rows) != 500 or len({row["mutation_id"] for row in rows}) != 500:
        raise AssertionError("The frozen manifest must contain 500 unique actions")

    metadata = json.loads((BASE / "expected" / "case3_expected_metadata.json").read_text(encoding="utf-8"))
    tokens = _replay(metadata["expected_braille"], rows)
    grid, locations = _pdf_grid(PDF)
    pdf_stream = []
    for page_index, page in enumerate(grid, 1):
        for line_index, line in enumerate(page, 1):
            pdf_stream.extend(char["text"] for char in line)
            if line_index < len(page) or page_index < len(grid):
                pdf_stream.append("⠀")
    if "".join(token["cell"] for token in tokens) != "".join(pdf_stream):
        raise AssertionError("Evaluator manifest replay differs from corrupted PDF logical cells")
    if len(tokens) != len(locations):
        raise AssertionError("Corrupted PDF cell/location stream is not 1:1")

    line_positions: dict[tuple[int, int], list[tuple[int, dict]]] = {}
    for stream_index, location in enumerate(locations):
        if location is not None:
            line_positions.setdefault((location["page"], location["line"]), []).append((stream_index, location))

    target_cells: dict[str, list[tuple[dict, dict]]] = {}
    for row in rows:
        if row["operation"] == "delete":
            earlier_delta = sum(
                len(other["actual_cells"]) - len(other["expected_cells"])
                for other in rows if other["expected_start"] < row["expected_start"]
            )
            gap = row["expected_start"] + earlier_delta
            anchor, _ = _deletion_anchor(row, gap, line_positions, grid, locations)
            target_cells[row["mutation_id"]] = [(anchor, _loc_char(grid, anchor))]
        else:
            records = [(location, _loc_char(grid, location)) for location in row["actual_locations"]]
            chars = [char for _location, char in records]
            if "".join(char["text"] for char in chars) != row["actual_cells"]:
                raise AssertionError(f"Physical mutation cells disagree: {row['mutation_id']}")
            target_cells[row["mutation_id"]] = records

    issues = validation["errors"]
    available = {issue["issue_id"] for issue in issues}
    issue_by_id = {issue["issue_id"]: issue for issue in issues}
    issue_geometry = {issue["issue_id"]: {_geometry(cell) for cell in issue["provenance_cells"]}
                      for issue in issues}
    issues_by_start: dict[int, list[dict]] = {}
    issues_by_geometry: dict[tuple, list[dict]] = {}
    for issue in issues:
        issues_by_start.setdefault(issue["span"].get("expected_start", -1), []).append(issue)
        for key in issue_geometry[issue["issue_id"]]:
            issues_by_geometry.setdefault(key, []).append(issue)
    outcomes = []
    expected_boxes: set[tuple] = set()
    expected_cell_keys: set[tuple] = set()
    equivalent_box_keys: set[tuple] = set()
    actual_box_keys = []
    incorrect_page_boxes = 0
    for row in sorted(rows, key=lambda item: item["expected_start"]):
        target = target_cells[row["mutation_id"]]
        page = int(target[0][0]["page"])
        target_pages = {int(location["page"]) for location, _char in target}
        target_geometry = {_geometry(char, location["page"]) for location, char in target}
        expected_cell_keys.update(target_geometry)
        grouped = group_provenance_boxes([
            {"page": int(location["page"]), **{key: char[key] for key in ("x0", "x1", "top", "bottom")}}
            for location, char in target
        ])
        required_boxes = {
            (box.page, *(round(getattr(box, field), 2) for field in ("x0", "x1", "top", "bottom")))
            for box in grouped
        }
        expected_boxes.update(required_boxes)
        start, end = _expected_span(row)
        candidate_ids = set()
        for offset in range(start - 4, start + 5):
            candidate_ids.update(issue["issue_id"] for issue in issues_by_start.get(offset, ()))
        for key in target_geometry:
            candidate_ids.update(issue["issue_id"] for issue in issues_by_geometry.get(key, ()))
        if row["operation"] == "insert" and row["actual_locations"]:
            location = row["actual_locations"][0]
            line = grid[int(location["page"]) - 1][int(location["line"]) - 1]
            for index in identical_run(line, int(location["cell"]) - 1):
                candidate_ids.update(issue["issue_id"] for issue in issues_by_geometry.get(
                    _geometry(line[index], int(location["page"])), ()))
        candidates = []
        for issue_id in candidate_ids:
            issue = issue_by_id[issue_id]
            if issue["issue_id"] not in available or not _shape_matches(row["operation"], issue):
                continue
            span = issue["span"]
            issue_start, issue_end = span.get("expected_start", -1), span.get("expected_end", -1)
            span_exact = issue_start == start and issue_end == end
            span_near = abs(issue_start - start) <= 4 and (issue_end >= start or issue_start == start)
            found_geometry = issue_geometry[issue["issue_id"]]
            physical_exact = found_geometry == target_geometry
            physical_overlap = bool(found_geometry & target_geometry)
            proof = None
            if row["operation"] == "insert":
                proof = _identical_insertion_proof(issue, row, grid)
            elif row["operation"] == "delete":
                proof = _identical_deletion_proof(issue, row, metadata, grid, target)
            if span_exact or span_near or physical_overlap or proof:
                score = 4 * physical_exact + 2 * span_exact + physical_overlap
                if proof and not physical_exact:
                    score += 3
                candidates.append((score, issue, proof if not physical_exact else None))
        candidates.sort(key=lambda pair: (-pair[0], pair[1]["issue_id"]))
        if not candidates:
            outcomes.append({"mutation_id": row["mutation_id"], "family": row["family"], "subtype": row["subtype"], "operation": row["operation"], "state": "MISSED"})
            continue
        best_score = candidates[0][0]
        best = [(issue, proof) for score, issue, proof in candidates if score == best_score]
        if len(best) != 1:
            outcomes.append({"mutation_id": row["mutation_id"], "family": row["family"], "subtype": row["subtype"], "operation": row["operation"], "state": "ASSOCIATION_AMBIGUOUS", "candidate_issue_ids": [issue["issue_id"] for issue, _ in best]})
            continue
        issue, equivalence_proof = best[0]
        available.remove(issue["issue_id"])
        found_geometry = issue_geometry[issue["issue_id"]]
        physical_exact = found_geometry == target_geometry
        span_exact = issue["span"].get("expected_start") == start and issue["span"].get("expected_end") == end
        box_keys = [_box_key(box) for box in issue["boxes"]]
        actual_box_keys.extend(box_keys)
        incorrect_page_boxes += sum(key[0] not in target_pages for key in box_keys)
        boxes_exact = len(box_keys) == len(required_boxes) and set(box_keys) == required_boxes
        if equivalence_proof:
            boxes_exact = (len(issue["boxes"]) == len(issue["provenance_cells"]) == 1
                           and _box_matches_cell(issue["boxes"][0], issue["provenance_cells"][0], page))
            equivalent_box_keys.update(box_keys)
        localized = boxes_exact and (physical_exact or equivalence_proof is not None)
        outcomes.append({
            "mutation_id": row["mutation_id"], "family": row["family"],
            "subtype": row["subtype"], "operation": row["operation"],
            "state": ("EQUIVALENTLY_DETECTED_AND_LOCALIZED" if localized and equivalence_proof
                      else "CORRECTLY_DETECTED_AND_LOCALIZED" if localized
                      else "DETECTED_BUT_MISLOCALIZED"),
            "issue_id": issue["issue_id"], "source_span_exact": span_exact,
            "physical_exact": physical_exact, "boxes_exact": boxes_exact,
            "equivalence": equivalence_proof,
            "target_cells": len(target), "provenance_cells": len(issue["provenance_cells"]),
            "expected_span": [start, end], "finding_span": [issue["span"].get("expected_start"), issue["span"].get("expected_end")],
            "target_geometry": sorted(target_geometry), "finding_geometry": sorted(found_geometry),
        })

    unmatched = [issue for issue in issues if issue["issue_id"] in available]
    all_issue_boxes = [box for issue in issues for box in issue["boxes"]]
    all_box_keys = [_box_key(box) for box in all_issue_boxes]
    all_provenance_geometry = set().union(*issue_geometry.values()) if issue_geometry else set()
    strict_off_target = sum(key not in expected_boxes for key in all_box_keys)
    equivalent_explained = sum(key not in expected_boxes and key in equivalent_box_keys for key in all_box_keys)
    equivalent_cell_keys = {
        _geometry(item["equivalence"]["finding_cell"], item["equivalence"]["page"])
        for item in outcomes if item.get("equivalence")
    }
    result = {
        "mutations": len(rows), "findings": len(issues), "reviews": validation["review_count"],
        "duplicate_issue_ids": validation["duplicate_issue_ids"],
        "runtime_seconds": validation["runtime_seconds"], "statistics": validation["statistics"],
        "outcomes": outcomes,
        "states": dict(Counter(item["state"] for item in outcomes)),
        "by_family": {
            family: dict(Counter(item["state"] for item in outcomes if item.get("family") == family))
            for family in sorted({row["family"] for row in rows})
        },
        "correctly_detected_and_localized": sum(item["state"] == "CORRECTLY_DETECTED_AND_LOCALIZED" for item in outcomes),
        "equivalently_detected_and_localized": sum(item["state"] == "EQUIVALENTLY_DETECTED_AND_LOCALIZED" for item in outcomes),
        "actions_detected_and_localized": sum(item["state"] in {
            "CORRECTLY_DETECTED_AND_LOCALIZED", "EQUIVALENTLY_DETECTED_AND_LOCALIZED"
        } for item in outcomes),
        "detected_but_mislocalized": sum(item["state"] == "DETECTED_BUT_MISLOCALIZED" for item in outcomes),
        "missed": sum(item["state"] == "MISSED" for item in outcomes),
        "association_ambiguous": sum(item["state"] == "ASSOCIATION_AMBIGUOUS" for item in outcomes),
        "unmatched_findings": len(unmatched), "unmatched_issue_ids": [issue["issue_id"] for issue in unmatched],
        "physical": {
            "required_target_cells": len(expected_cell_keys),
            "target_cells_with_provenance": sum(key in all_provenance_geometry for key in expected_cell_keys),
            "target_cells_with_provenance_after_equivalence": sum(
                key in all_provenance_geometry for key in expected_cell_keys
            ) + sum(key in all_provenance_geometry for key in equivalent_cell_keys - expected_cell_keys),
            "required_boxes": len(expected_boxes), "rendered_boxes": len(all_box_keys),
            "off_target_boxes": strict_off_target - equivalent_explained,
            "strict_off_target_boxes": strict_off_target,
            "equivalence_explained_boxes": equivalent_explained,
            "duplicate_boxes": len(all_box_keys) - len(set(all_box_keys)),
            "incorrect_page_boxes": incorrect_page_boxes,
        },
        "localization_policy": {
            "deletion_anchor": "next semantic nonblank cell on the original physical line; otherwise previous semantic cell on that line",
            "identical_insertions": "accept any cell in the same intact physically contiguous identical-cell run only with one exact matching provenance cell and box",
            "identical_deletions": "accept an anchor in the shortened same-line identical run or its immediate semantic successor only when the expected run is shortened by exactly one cell",
        },
    }
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with OUTCOMES_CSV.open("w", encoding="utf-8", newline="") as stream:
        fields = ["mutation_id", "family", "subtype", "operation", "state", "issue_id", "source_span_exact", "physical_exact", "boxes_exact", "equivalence"]
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(outcomes)
    return result


if __name__ == "__main__":
    result = evaluate()
    print(json.dumps({key: value for key, value in result.items() if key not in {"outcomes", "unmatched_issue_ids"}}, ensure_ascii=True, indent=2))
