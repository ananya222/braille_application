"""One-to-one mutation/finding and PDF-box evaluation for frozen Case 4."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "stress_test" / "uncontracted_case3_numbers"))

from braille_app.visual_annotations import group_provenance_boxes
from evaluate_case3_validation import (
    _box_key, _box_matches_cell, _deletion_anchor, _expected_span,
    _geometry, _identical_deletion_proof, _identical_insertion_proof,
    _loc_char, _pdf_grid, _replay, _shape_matches,
)

BASE = ROOT / "stress_test" / "uncontracted_case4_punctuation"
SOURCE = BASE / "source" / "case4_punctuation_clean.docx"
PDF = BASE / "output" / "case4_corrupted.pdf"
BRF = BASE / "output" / "case4_corrupted.brf"
FREEZE = BASE / "manifest" / "case4_fixture_frozen.json"
MANIFEST = BASE / "manifest" / "case4_500_mutations.csv"
EXPECTED = BASE / "expected" / "case4_expected_metadata.json"
RESULT = BASE / "results" / "case4_validation_result_after_insert_ownership.json"
CLEAN_RESULT = BASE / "results" / "case4_clean_validation.json"
OUTPUT = BASE / "results" / "case4_observable_evaluation.json"
OUTCOMES_CSV = BASE / "results" / "case4_mutation_outcomes.csv"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _semantic_cell(line: list[dict], index: int) -> bool:
    char = line[index]
    if char["text"] in {"⠀", "^", "#"} or (index and line[index - 1]["text"] == "^"):
        return False
    return not any(other["text"] == "#" and abs(other["top"] - char["top"]) < 2.5 for other in line)


def _issue_boxes_valid(issue: dict) -> bool:
    cells = issue["provenance_cells"]
    if not cells or not issue["boxes"]:
        return False
    groups = group_provenance_boxes([
        {"page": int(cell["page"]), **{key: cell[key] for key in ("x0", "x1", "top", "bottom")}}
        for cell in cells
    ])
    expected = {(box.page, *(round(getattr(box, key), 2) for key in ("x0", "x1", "top", "bottom")))
                for box in groups}
    return expected == {_box_key(box) for box in issue["boxes"]}


def evaluate(result_path: Path = RESULT, output_path: Path = OUTPUT,
             outcomes_path: Path = OUTCOMES_CSV) -> dict:
    if output_path.exists() or outcomes_path.exists():
        raise FileExistsError("Refusing to overwrite Case 4 evaluation output")
    frozen = json.loads(FREEZE.read_text(encoding="utf-8"))
    validation = json.loads(result_path.read_text(encoding="utf-8"))
    clean = json.loads(CLEAN_RESULT.read_text(encoding="utf-8"))
    for path, key in ((SOURCE, "source_docx"), (PDF, "corrupted_pdf"),
                      (BRF, "corrupted_brf"), (MANIFEST, "mutation_manifest")):
        if _sha(path) != frozen["hashes"][key]:
            raise AssertionError(f"Frozen Case 4 hash mismatch: {key}")
    if validation["source_sha256"] != frozen["hashes"]["source_docx"] or validation["pdf_sha256"] != frozen["hashes"]["corrupted_pdf"]:
        raise AssertionError("Validator result does not refer to the frozen Case 4 source/PDF")
    if clean["error_count"] or clean["review_count"] or clean["duplicate_issue_ids"]:
        raise AssertionError("Clean Case 4 control is not clean")

    with MANIFEST.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        for field in ("expected_start", "target_expected_index", "initial_page", "initial_line",
                      "initial_cell", "source_offset", "source_block"):
            row[field] = int(row[field])
        row["actual_locations"] = json.loads(row["actual_locations"])
    if len(rows) != 500 or len({row["mutation_id"] for row in rows}) != 500:
        raise AssertionError("Frozen Case 4 manifest must have 500 unique actions")
    metadata = json.loads(EXPECTED.read_text(encoding="utf-8"))
    replay = _replay(metadata["expected_braille"], rows)
    grid, locations = _pdf_grid(PDF)
    pdf_stream = []
    for page_index, page in enumerate(grid, 1):
        for line_index, line in enumerate(page, 1):
            pdf_stream.extend(char["text"] for char in line)
            if line_index < len(page) or page_index < len(grid):
                pdf_stream.append("⠀")
    if "".join(token["cell"] for token in replay) != "".join(pdf_stream):
        raise AssertionError("Frozen Case 4 mutation replay differs from corrupted PDF")
    if len(replay) != len(locations):
        raise AssertionError("Case 4 PDF logical cell/location stream is not 1:1")

    line_positions: dict[tuple[int, int], list[tuple[int, dict]]] = {}
    for stream_index, location in enumerate(locations):
        if location is not None:
            line_positions.setdefault((location["page"], location["line"]), []).append((stream_index, location))
    target_cells = {}
    for row in rows:
        if row["operation"] == "delete":
            prior_delta = sum(
                len(other["actual_cells"]) - len(other["expected_cells"])
                for other in rows if other["expected_start"] < row["expected_start"]
            )
            gap = row["expected_start"] + prior_delta
            anchor, _char = _deletion_anchor(row, gap, line_positions, grid, locations)
            target_cells[row["mutation_id"]] = [(anchor, _loc_char(grid, anchor))]
        else:
            records = [(location, _loc_char(grid, location)) for location in row["actual_locations"]]
            if "".join(char["text"] for _location, char in records) != row["actual_cells"]:
                raise AssertionError(f"Manifest/PDF target mismatch: {row['mutation_id']}")
            target_cells[row["mutation_id"]] = records

    issues = validation["errors"]
    issue_by_id = {issue["issue_id"]: issue for issue in issues}
    available = set(issue_by_id)
    issue_geometry = {issue["issue_id"]: {_geometry(cell) for cell in issue["provenance_cells"]}
                      for issue in issues}
    issues_by_start: dict[int, list[dict]] = {}
    issues_by_geometry: dict[tuple, list[dict]] = {}
    for issue in issues:
        issues_by_start.setdefault(issue["span"].get("expected_start", -1), []).append(issue)
        for key in issue_geometry[issue["issue_id"]]:
            issues_by_geometry.setdefault(key, []).append(issue)

    outcomes = []
    expected_boxes, expected_cell_keys, equivalent_box_keys = set(), set(), set()
    rendered_box_keys, wrong_page_boxes = [], 0
    for row in sorted(rows, key=lambda item: item["expected_start"]):
        target = target_cells[row["mutation_id"]]
        target_pages = {int(location["page"]) for location, _char in target}
        target_geometry = {_geometry(char, location["page"]) for location, char in target}
        expected_cell_keys.update(target_geometry)
        grouped = group_provenance_boxes([
            {"page": int(location["page"]), **{key: char[key] for key in ("x0", "x1", "top", "bottom")}}
            for location, char in target
        ])
        required_boxes = {(box.page, *(round(getattr(box, key), 2) for key in ("x0", "x1", "top", "bottom")))
                          for box in grouped}
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
            # Reuse the Case 1–3 exact identical-run helper; only a visually
            # indistinguishable insertion can consume this equivalence.
            from evaluate_frozen_diverse import identical_run
            for index in identical_run(line, int(location["cell"]) - 1):
                candidate_ids.update(issue["issue_id"] for issue in issues_by_geometry.get(
                    _geometry(line[index], int(location["page"])), ()))
        candidates = []
        for issue_id in candidate_ids:
            issue = issue_by_id[issue_id]
            if issue_id not in available or not _shape_matches(row["operation"], issue):
                continue
            span = issue["span"]
            issue_start, issue_end = span.get("expected_start", -1), span.get("expected_end", -1)
            exact_span = issue_start == start and issue_end == end
            near_span = abs(issue_start - start) <= 4 and (issue_end >= start or issue_start == start)
            geometry = issue_geometry[issue_id]
            exact_physical = geometry == target_geometry
            overlap = bool(geometry & target_geometry)
            proof = (_identical_insertion_proof(issue, row, grid) if row["operation"] == "insert" else
                     _identical_deletion_proof(issue, row, metadata, grid, target) if row["operation"] == "delete" else None)
            if exact_span or near_span or overlap or proof:
                score = 4 * exact_physical + 2 * exact_span + overlap
                if proof and not exact_physical:
                    score += 3
                candidates.append((score, issue, proof if not exact_physical else None))
        candidates.sort(key=lambda item: (-item[0], item[1]["issue_id"]))
        if not candidates:
            outcomes.append({"mutation_id": row["mutation_id"], "family": row["family"],
                "subtype": row["subtype"], "operation": row["operation"], "state": "MISSED"})
            continue
        best_score = candidates[0][0]
        best = [(issue, proof) for score, issue, proof in candidates if score == best_score]
        if len(best) != 1:
            outcomes.append({"mutation_id": row["mutation_id"], "family": row["family"],
                "subtype": row["subtype"], "operation": row["operation"],
                "state": "ASSOCIATION_AMBIGUOUS", "candidate_issue_ids": [i["issue_id"] for i, _ in best]})
            continue
        issue, proof = best[0]
        available.remove(issue["issue_id"])
        geometry = issue_geometry[issue["issue_id"]]
        physical_exact = geometry == target_geometry
        span_exact = issue["span"].get("expected_start") == start and issue["span"].get("expected_end") == end
        boxes = issue["boxes"]
        box_keys = [_box_key(box) for box in boxes]
        rendered_box_keys.extend(box_keys)
        wrong_page_boxes += sum(key[0] not in target_pages for key in box_keys)
        boxes_exact = len(box_keys) == len(required_boxes) and set(box_keys) == required_boxes
        if proof:
            boxes_exact = len(boxes) == len(issue["provenance_cells"]) == 1 and _box_matches_cell(
                boxes[0], issue["provenance_cells"][0], next(iter(target_pages)))
            equivalent_box_keys.update(box_keys)
        localized = boxes_exact and (physical_exact or proof is not None)
        outcomes.append({"mutation_id": row["mutation_id"], "family": row["family"],
            "subtype": row["subtype"], "operation": row["operation"],
            "state": "EQUIVALENTLY_DETECTED_AND_LOCALIZED" if localized and proof else
                     "CORRECTLY_DETECTED_AND_LOCALIZED" if localized else "DETECTED_BUT_MISLOCALIZED",
            "issue_id": issue["issue_id"], "source_span_exact": span_exact,
            "physical_exact": physical_exact, "boxes_exact": boxes_exact,
            "equivalence": proof, "target_cells": len(target),
            "provenance_cells": len(issue["provenance_cells"]),
            "expected_span": [start, end],
            "finding_span": [issue["span"].get("expected_start"), issue["span"].get("expected_end")]})

    unmatched = [issue for issue in issues if issue["issue_id"] in available]
    all_boxes = [box for issue in issues for box in issue["boxes"]]
    all_box_keys = [_box_key(box) for box in all_boxes]
    all_provenance = set().union(*issue_geometry.values()) if issue_geometry else set()
    strict_off_target = sum(key not in expected_boxes for key in all_box_keys)
    explained_equivalence = sum(key not in expected_boxes and key in equivalent_box_keys for key in all_box_keys)
    equivalent_cells = {_geometry(item["equivalence"]["finding_cell"], item["equivalence"]["page"])
                        for item in outcomes if item.get("equivalence")}
    result = {
        "mutations": len(rows), "findings": len(issues), "reviews": validation["review_count"],
        "duplicate_issue_ids": validation["duplicate_issue_ids"], "runtime_seconds": validation["runtime_seconds"],
        "statistics": validation["statistics"], "outcomes": outcomes,
        "states": dict(Counter(item["state"] for item in outcomes)),
        "by_family": {family: dict(Counter(item["state"] for item in outcomes if item["family"] == family))
                      for family in sorted({row["family"] for row in rows})},
        "correctly_detected_and_localized": sum(item["state"] == "CORRECTLY_DETECTED_AND_LOCALIZED" for item in outcomes),
        "equivalently_detected_and_localized": sum(item["state"] == "EQUIVALENTLY_DETECTED_AND_LOCALIZED" for item in outcomes),
        "actions_detected_and_localized": sum(item["state"] in {"CORRECTLY_DETECTED_AND_LOCALIZED", "EQUIVALENTLY_DETECTED_AND_LOCALIZED"} for item in outcomes),
        "detected_but_mislocalized": sum(item["state"] == "DETECTED_BUT_MISLOCALIZED" for item in outcomes),
        "missed": sum(item["state"] == "MISSED" for item in outcomes),
        "association_ambiguous": sum(item["state"] == "ASSOCIATION_AMBIGUOUS" for item in outcomes),
        "unmatched_findings": len(unmatched), "unmatched_issue_ids": [issue["issue_id"] for issue in unmatched],
        "physical": {"required_target_cells": len(expected_cell_keys),
            "target_cells_with_provenance": len(expected_cell_keys & all_provenance),
            "required_boxes": len(expected_boxes), "rendered_boxes": len(all_box_keys),
            "off_target_boxes": strict_off_target - explained_equivalence,
            "strict_off_target_boxes": strict_off_target,
            "equivalence_explained_boxes": explained_equivalence,
            "duplicate_boxes": len(all_box_keys) - len(set(all_box_keys)),
            "incorrect_page_boxes": wrong_page_boxes,
            "invalid_provenance_boxes": sum(not _issue_boxes_valid(issue) for issue in issues)},
        "deletion_anchor_policy": "next semantic nonblank cell on the original physical line; previous semantic cell at line end",
    }
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with outcomes_path.open("w", encoding="utf-8", newline="") as stream:
        fields = ["mutation_id", "family", "subtype", "operation", "state", "issue_id",
                  "source_span_exact", "physical_exact", "boxes_exact", "equivalence"]
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(outcomes)
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-path", type=Path, default=RESULT)
    parser.add_argument("--output-path", type=Path, default=OUTPUT)
    parser.add_argument("--outcomes-path", type=Path, default=OUTCOMES_CSV)
    args = parser.parse_args()
    result = evaluate(args.result_path, args.output_path, args.outcomes_path)
    print(json.dumps({key: value for key, value in result.items()
                      if key not in {"outcomes", "unmatched_issue_ids"}}, ensure_ascii=True, indent=2))
