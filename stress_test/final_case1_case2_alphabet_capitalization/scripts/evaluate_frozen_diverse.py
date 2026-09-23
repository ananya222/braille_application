"""Read-only, one-to-one audit of the frozen diverse PDF against its manifest."""

from __future__ import annotations

import csv
import json
import time
from collections import Counter
from dataclasses import asdict
from pathlib import Path

import pdfplumber

import final_combined_closure as fc
from braille_app.validation.api import validate_document
from braille_app.validation.pdf_annotation_adapter import (
    build_provenance_alignment,
    validation_errors_to_legacy_cell_issues,
)
from braille_app.visual_annotations import group_provenance_boxes, visual_issues_from_cell_issues


BASE = Path(__file__).resolve().parents[1]
PDF = BASE / "corrupted_diverse_final/final_case1_case2_diverse_1000.pdf"
MANIFEST = BASE / "manifests/diverse_mutation_manifest.csv"


def same_box(box, char) -> bool:
    return all(abs(float(getattr(box, key)) - float(char[key])) < .02
               for key in ("x0", "x1", "top", "bottom"))


def identical_run(characters, index: int) -> tuple[int, ...]:
    """Physically adjacent, visually identical cells on one PDF line."""
    target = characters[index]
    left = right = index
    while (left > 0 and characters[left - 1]["text"] == target["text"]
           and abs(characters[left - 1]["top"] - target["top"]) < 2.5
           and characters[left]["x0"] - characters[left - 1]["x1"] <= 3.0):
        left -= 1
    while (right + 1 < len(characters) and characters[right + 1]["text"] == target["text"]
           and abs(characters[right + 1]["top"] - target["top"]) < 2.5
           and characters[right + 1]["x0"] - characters[right]["x1"] <= 3.0):
        right += 1
    return tuple(range(left, right + 1))


def complete_deletion_group(rows: list[dict], page: int, start: int, end: int) -> bool:
    """A grouped deletion may cover only contiguous manifested deleted cells."""
    indices = sorted(row["expected_index"] for row in rows
                     if row["page"] == page and row["operation"] == "deletion"
                     and start <= row["expected_index"] < end)
    return end - start > 1 and indices == list(range(start, end))


def identical_insertion_candidate(candidate, row, run_chars, cells, boxes):
    """Check the documented single-cell insertion equivalence, including its box."""
    geometry = lambda cell: tuple(round(float(cell[key]), 3) for key in ("x0", "x1", "top", "bottom"))
    return (
        len(run_chars) > 1
        and candidate.source_page_number == row["page"]
        and not candidate.expected_braille and len(candidate.actual_braille) == 1
        and candidate.actual_braille[0] == fc.char_mask(row["code_target"], "duxbury")
        and abs(candidate.span.get("expected_start", -10000) - row["expected_index"]) <= len(run_chars)
        and len(cells) == 1 and cells[0]["page"] == row["page"]
        and geometry(cells[0]) in {geometry(char) for char in run_chars}
        and len(boxes) == 1 and boxes[0].page == row["page"] and same_box(boxes[0], cells[0])
    )


def identical_deletion_candidate(candidate, row, expected, block_span, chars, target_indices, cells, boxes):
    """Prove equal-cell deletion gaps from the expected block and surviving PDF run.

    Only a single deletion with an otherwise intact same-line run qualifies.
    The legal anchors are that surviving run and its immediate semantic successor.
    """
    start = candidate.span.get("expected_start", -1)
    end = candidate.span.get("expected_end", -1)
    index = row["expected_index"]
    if (candidate.source_page_number != row["page"] or candidate.actual_braille
        or end != start + 1 or len(candidate.expected_braille) != 1
        or not block_span[0] <= min(start, index) <= max(start, index) < block_span[1]
        or len(target_indices) != 1 or len(cells) != 1 or len(boxes) != 1
        or cells[0]["page"] != row["page"] or boxes[0].page != row["page"]
        or not same_box(boxes[0], cells[0])):
        return None
    mask = expected[index]
    left, right = index, index + 1
    while left > block_span[0] and expected[left - 1] == mask:
        left -= 1
    while right < block_span[1] and expected[right] == mask:
        right += 1
    if not mask or right - left < 2 or not left <= start < right or candidate.expected_braille[0] != mask:
        return None
    anchor_indices = [i for i, char in enumerate(chars) if same_box(boxes[0], char)]
    if len(anchor_indices) != 1:
        return None
    anchor = anchor_indices[0]
    seed = anchor if fc.char_mask(chars[anchor]["text"], "duxbury") == mask else anchor - 1
    if seed < 0 or fc.char_mask(chars[seed]["text"], "duxbury") != mask:
        return None
    run = identical_run(chars, seed)
    if len(run) != right - left - 1:
        return None

    def semantic(i):
        char = chars[i]
        return (char["text"].strip() and char["text"] not in {"\u2800", "^"}
                and not (i and chars[i - 1]["text"] == "^")
                and not any(other["text"] == "#" and abs(other["top"] - char["top"]) < 2.5 for other in chars))

    allowed = list(run)
    following = run[-1] + 1
    if (following < len(chars) and semantic(following)
        and abs(chars[following]["top"] - chars[run[-1]]["top"]) < 2.5
        and chars[following]["x0"] - chars[run[-1]]["x1"] <= 3):
        allowed.append(following)
    if (not all(semantic(i) for i in run) or anchor not in allowed or target_indices[0] not in allowed):
        return None
    return {"expected_run": [left, right], "actual_run_pdf_indices": list(run),
            "allowed_anchor_pdf_indices": allowed, "chosen_anchor_pdf_index": anchor,
            "mask": mask, "same_block": list(block_span)}


def run():
    with MANIFEST.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        for field in ("page", "expected_index", "actual_token", "secondary_token", "secondary_expected_index"):
            row[field] = int(row[field]) if row.get(field) else (None if field.startswith("secondary") else 0)

    master, expected_document = fc.master_and_expected()
    started = time.perf_counter()
    result = validate_document(master, PDF, profile=fc.PROFILE, retain_pdf_provenance=True)
    runtime_seconds = time.perf_counter() - started
    provenance = build_provenance_alignment(result.pdf_input)
    cell_issues = validation_errors_to_legacy_cell_issues(result, provenance)
    visuals = visual_issues_from_cell_issues(cell_issues)
    issue_cells = {
        issue.issue_id: cell_issues[index]["provenance_cells"]
        for index, issue in enumerate(result.errors)
    }
    issue_boxes = {
        issue.issue_id: visuals[index].boxes
        for index, issue in enumerate(result.errors)
    }

    by_page = {}
    for row in rows:
        by_page.setdefault(row["page"], []).append(row)

    def shifted_index(page, token):
        return token + sum(
            1 if item["operation"] == "insertion" else -1 if item["operation"] == "deletion" else 0
            for item in by_page[page] if item["actual_token"] < token
        )

    available = {issue.issue_id for issue in result.errors}
    outcomes = []
    expected_physical_boxes = []
    expected_physical_cells = []
    targets_by_id = {}
    equivalent_allowed_boxes = []
    with pdfplumber.open(str(PDF)) as pdf, pdfplumber.open(str(fc.PDF)) as clean_pdf:
        for row in rows:
            page = row["page"]
            index = row["expected_index"]
            kind = row["operation"]
            expected_end = (row["secondary_expected_index"] + 1 if kind == "transposition"
                            else index if kind == "insertion" else index + 1)
            page_chars = pdf.pages[page - 1].chars
            target_indices = []
            if kind == "deletion":
                # The original target's line is known to this independent
                # evaluator (not to production). Anchor the gap to the next
                # surviving cell on that line, else the previous one.
                target_top = clean_pdf.pages[page - 1].chars[row["actual_token"]]["top"]
                insertion_point = shifted_index(page, row["actual_token"])
                footer_tops = [char["top"] for char in page_chars if char["text"] == "#"]
                def same_source_line(value):
                    char = page_chars[value]
                    return (abs(char["top"] - target_top) < 2.5
                            and char["text"].strip() and char["text"] != "\u2800"
                            and char["text"] != "^"
                            and not (value > 0 and page_chars[value - 1]["text"] == "^")
                            and not any(abs(char["top"] - top) < 2.5 for top in footer_tops))
                following = next((value for value in range(insertion_point, len(page_chars))
                                  if same_source_line(value)), None)
                preceding = next((value for value in range(insertion_point - 1, -1, -1)
                                  if same_source_line(value)), None)
                selected = following if following is not None else preceding
                if selected is not None:
                    target_indices = [selected]
            else:
                target_indices = [shifted_index(page, row["actual_token"])]
                if kind == "transposition":
                    target_indices.append(shifted_index(page, row["secondary_token"]))
            target_chars = [page_chars[value] for value in target_indices if 0 <= value < len(page_chars)]
            targets_by_id[row["error_id"]] = (page, target_chars)
            expected_physical_cells.extend((page, char) for char in target_chars)
            expected_physical_boxes.extend(group_provenance_boxes([
                {"page": page, **{key: char[key] for key in ("x0", "x1", "top", "bottom")}}
                for char in target_chars
            ]))
            expected_geometry = {tuple(round(float(char[key]), 3) for key in ("x0", "x1", "top", "bottom"))
                                 for char in target_chars}
            candidates = []
            for candidate in result.errors:
                if candidate.issue_id not in available or candidate.source_page_number != page:
                    continue
                if abs(candidate.span.get("expected_start", -10000) - index) > 4:
                    continue
                span_match = (candidate.span.get("expected_start") == index
                              and candidate.span.get("expected_end") == expected_end)
                cells = issue_cells[candidate.issue_id]
                cell_geometry = {tuple(round(float(cell[key]), 3) for key in ("x0", "x1", "top", "bottom"))
                                 for cell in cells}
                physical_match = len(target_chars) == len(target_indices) and cell_geometry == expected_geometry
                shape_match = ((kind == "insertion" and not candidate.expected_braille)
                               or (kind == "deletion" and not candidate.actual_braille)
                               or (kind == "transposition" and len(candidate.expected_braille) == 2
                                   and len(candidate.actual_braille) == 2)
                               or (kind == "substitution" and len(candidate.expected_braille) == 1
                                   and len(candidate.actual_braille) == 1))
                if (span_match or physical_match) and shape_match:
                    candidates.append((2 * physical_match + span_match, candidate))
            candidates.sort(key=lambda pair: (-pair[0], pair[1].issue_id))
            issue = candidates[0][1] if candidates else None
            identical_equivalence = False
            deletion_equivalence = None
            if issue is None and kind == "insertion" and len(target_chars) == 1:
                run = identical_run(page_chars, target_indices[0])
                equivalent = [candidate for candidate in result.errors
                              if candidate.issue_id in available
                              and identical_insertion_candidate(candidate, row, [page_chars[value] for value in run],
                                                                issue_cells[candidate.issue_id], issue_boxes[candidate.issue_id])]
                if len(run) > 1 and len(equivalent) == 1:
                    issue = equivalent[0]
                    identical_equivalence = True
            if issue is None and kind == "deletion":
                expected_page = expected_document.pages[page - 1]
                expected_cells = fc.unicode_to_cells(expected_page.flatten())
                cursor = 0
                block_span = (0, 0)
                for block in expected_page.blocks:
                    if not block.braille:
                        continue
                    end = cursor + len(block.braille)
                    if cursor <= index < end:
                        block_span = (cursor, end)
                        break
                    cursor = end + 1
                equivalent = []
                for candidate in result.errors:
                    if candidate.issue_id not in available:
                        continue
                    proof = identical_deletion_candidate(
                        candidate, row, expected_cells, block_span, page_chars, target_indices,
                        issue_cells[candidate.issue_id], issue_boxes[candidate.issue_id])
                    if proof:
                        equivalent.append((candidate, proof))
                if len(equivalent) == 1:
                    issue, deletion_equivalence = equivalent[0]
            if issue is None:
                outcomes.append({"id": row["error_id"], "page": page, "operation": kind,
                                 "state": "missed_or_merged", "expected_index": index,
                                 "candidate_count": len(candidates)})
                continue
            available.remove(issue.issue_id)
            cells = issue_cells[issue.issue_id]
            boxes = issue_boxes[issue.issue_id]
            actual_geometry = {tuple(round(float(cell[key]), 3) for key in ("x0", "x1", "top", "bottom"))
                               for cell in cells}
            provenance_exact = len(target_chars) == len(target_indices) and actual_geometry == expected_geometry
            source_span_exact = (issue.span.get("expected_start") == index
                                 and issue.span.get("expected_end") == expected_end)
            expected_boxes = group_provenance_boxes([{"page": page, **{key: char[key] for key in ("x0", "x1", "top", "bottom")}} for char in target_chars])
            boxes_exact = len(boxes) == len(expected_boxes) and all(
                any(box.page == target.page and all(abs(getattr(box, key) - getattr(target, key)) < .02
                        for key in ("x0", "x1", "top", "bottom")) for box in boxes)
                for target in expected_boxes
            )
            if kind == "deletion" and not target_indices:
                state = "unanchored_terminal"
            elif identical_equivalence:
                state = "equivalent_identical_insertion"
                equivalent_allowed_boxes.extend(boxes)
            elif deletion_equivalence:
                state = "equivalent_identical_deletion"
                equivalent_allowed_boxes.extend(boxes)
            elif provenance_exact:
                state = "correct" if boxes_exact else "wrong_box"
            else:
                state = "wrong_provenance"
            outcomes.append({"id": row["error_id"], "page": page, "operation": kind,
                             "state": state, "issue_id": issue.issue_id,
                             "expected_index": index, "source_span_exact": source_span_exact,
                             "actual_span": [issue.actual_cell_start, issue.actual_cell_end],
                             "target_indices": target_indices, "target_cells": len(target_chars),
                             "provenance_cells": len(cells), "boxes": len(boxes),
                             "expected_boxes": len(expected_boxes), "deletion_equivalence": deletion_equivalence})

    for outcome in outcomes:
        if outcome["operation"] != "deletion" or outcome["state"] != "missed_or_merged":
            continue
        page, target_chars = targets_by_id[outcome["id"]]
        index = outcome["expected_index"]
        target_geometry = {tuple(round(float(char[key]), 3) for key in ("x0", "x1", "top", "bottom"))
                           for char in target_chars}
        equivalent = []
        for candidate in result.errors:
            start = candidate.span.get("expected_start", -1)
            end = candidate.span.get("expected_end", -1)
            if (candidate.source_page_number != page or candidate.actual_braille
                or not start <= index < end or not complete_deletion_group(rows, page, start, end)
                or not any(item.get("issue_id") == candidate.issue_id and item["state"] == "correct"
                           for item in outcomes)):
                continue
            actual_geometry = {tuple(round(float(cell[key]), 3) for key in ("x0", "x1", "top", "bottom"))
                               for cell in issue_cells[candidate.issue_id]}
            target_boxes = group_provenance_boxes([
                {"page": page, **{key: char[key] for key in ("x0", "x1", "top", "bottom")}}
                for char in target_chars
            ])
            actual_boxes = issue_boxes[candidate.issue_id]
            if (actual_geometry == target_geometry and len(actual_boxes) == len(target_boxes)
                and all(any(box.page == target.page and same_box(box, vars(target))
                            for box in actual_boxes) for target in target_boxes)):
                equivalent.append(candidate)
        if len(equivalent) == 1:
            outcome.update(state="equivalent_adjacent_deletion", issue_id=equivalent[0].issue_id,
                           target_cells=len(target_chars))

    all_boxes = [box for visual in visuals for box in visual.boxes]
    def box_key(box):
        return (box.page, *(round(getattr(box, field), 2) for field in ("x0", "x1", "top", "bottom")))
    def cell_key(page, cell):
        return (page, *(round(float(cell[field]), 2) for field in ("x0", "x1", "top", "bottom")))
    expected_box_keys = {box_key(box) for box in expected_physical_boxes}
    policy_allowed_box_keys = expected_box_keys | {box_key(box) for box in equivalent_allowed_boxes}
    actual_box_keys = [box_key(box) for box in all_boxes]
    actual_cell_keys = {cell_key(cell["page"], cell)
                        for records in issue_cells.values() for cell in records}
    accepted_states = {"correct", "equivalent_identical_insertion", "equivalent_adjacent_deletion", "equivalent_identical_deletion"}
    accepted = [item for item in outcomes if item["state"] in accepted_states]
    matched_issue_ids = {item["issue_id"] for item in accepted}
    summary = {
        "outcomes": outcomes,
        "findings_detail": [{**asdict(issue), "provenance": issue_cells[issue.issue_id],
                              "boxes": [asdict(box) for box in issue_boxes[issue.issue_id]]}
                             for issue in result.errors],
        "mutations": len(rows), "findings": len(result.errors), "reviews": len(result.reviews),
        "runtime_seconds": round(runtime_seconds, 3),
        "unmatched_findings": len(available), "duplicate_issue_ids": len(result.errors) - len({x.issue_id for x in result.errors}),
        "policy": {
            "accepted_mutations": len(accepted),
            "unresolved_mutations": len(rows) - len(accepted),
            "unique_matched_findings": len(matched_issue_ids),
            "unrelated_findings": len(available),
            "equivalent_identical_insertions": sum(item["state"] == "equivalent_identical_insertion" for item in outcomes),
            "equivalent_adjacent_deletions": sum(item["state"] == "equivalent_adjacent_deletion" for item in outcomes),
            "equivalent_identical_deletions": sum(item["state"] == "equivalent_identical_deletion" for item in outcomes),
        },
        "physical": {
            "target_cell_slots": len(expected_physical_cells),
            "target_cell_slots_with_provenance": sum(cell_key(page, char) in actual_cell_keys
                                                     for page, char in expected_physical_cells),
            "required_grouped_boxes": len(expected_physical_boxes),
            "required_unique_grouped_boxes": len(expected_box_keys),
            "actual_boxes": len(all_boxes),
            "target_boxes_present": sum(box_key(box) in actual_box_keys for box in expected_physical_boxes),
            "off_target_boxes": sum(box not in expected_box_keys for box in actual_box_keys),
            "policy_target_slots_satisfied": sum(len(targets_by_id[item["id"]][1]) for item in accepted),
            "invalid_off_region_boxes": sum(box not in policy_allowed_box_keys for box in actual_box_keys),
            "incorrect_page_boxes": sum(
                box.page != item["page"]
                for item in accepted if item.get("issue_id") in issue_boxes
                for box in issue_boxes[item["issue_id"]]
            ),
            "duplicate_boxes": len(actual_box_keys) - len(set(actual_box_keys)),
        },
        "states": dict(Counter(item["state"] for item in outcomes)),
        "by_operation": {operation: dict(Counter(item["state"] for item in outcomes if item["operation"] == operation))
                         for operation in sorted({item["operation"] for item in outcomes})},
        "transposition_correct_box_counts": dict(Counter(item["boxes"] for item in outcomes
                                                     if item["operation"] == "transposition" and item["state"] == "correct")),
        "physically_correct_but_reanchored": dict(Counter(item["operation"] for item in outcomes
                                                     if item["state"] == "correct" and not item.get("source_span_exact", True))),
        "problem_ids": {operation: [item["id"] for item in outcomes if item["operation"] == operation and item["state"] not in accepted_states]
                        for operation in ("transposition", "insertion", "substitution", "deletion")},
        "examples": {state: [item for item in outcomes if item["state"] == state][:5]
                     for state in sorted({item["state"] for item in outcomes})},
        "nearby": {
            item["id"]: [
                {"issue": issue.issue_id, "span": issue.span,
                 "expected": list(issue.expected_braille), "actual": list(issue.actual_braille),
                 "cells": [(cell["x0"], cell["top"], cell["source_char"])
                           for cell in issue_cells[issue.issue_id]]}
                for issue in result.errors if issue.source_page_number == item["page"]
                and abs(issue.span.get("expected_start", -10000) - item["expected_index"]) <= 3
            ]
            for item in outcomes if item["id"] in {
                "DIV-0067", "DIV-0130", "DIV-0263", "DIV-0023", "DIV-0062",
                "DIV-0086", "DIV-0274", "DIV-0004", "DIV-0867"
            }
        },
    }
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
