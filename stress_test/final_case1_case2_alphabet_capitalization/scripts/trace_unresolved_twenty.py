"""Capture pre/post deletion-tie diagnostics without editing production files.

Run once to save both full evaluations; analyze the saved JSON thereafter.
The pre variant removes exactly the latest deletion tie branch in memory.
"""

from __future__ import annotations

import contextlib
import csv
import hashlib
import inspect
import io
import json
import sys
from dataclasses import asdict
from pathlib import Path

import evaluate_frozen_diverse as audit
from braille_app.validation import alignment, api

OUT = audit.BASE / "results/unresolved_twenty_trace"
BRANCH = '''        elif (i + 1 < rows and j < cols
              and expected[i] == expected[i + 1] == actual[j]
              and distance[i][j] == 1 + distance[i + 1][j]):
            tag, next_i, next_j = "delete", i + 1, j
'''


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def capture(label, bounded_function):
    saved = {}
    original_adapt = api.adapt_validation_report
    original_bounded = alignment._align_bounded_block

    def adapt(report, **kwargs):
        saved["report"] = report
        return original_adapt(report, **kwargs)

    def profile(frame, event, arg):
        if event == "return" and frame.f_code is audit.run.__code__:
            saved["audit"] = frame.f_locals.copy()

    try:
        api.adapt_validation_report = adapt
        alignment._align_bounded_block = bounded_function
        sys.setprofile(profile)
        with contextlib.redirect_stdout(io.StringIO()):
            audit.run()
    finally:
        sys.setprofile(None)
        api.adapt_validation_report = original_adapt
        alignment._align_bounded_block = original_bounded

    state, report = saved["audit"], saved["report"]
    result = state["result"]
    snapshot = {
        "variant": label,
        "summary": state["summary"],
        "outcomes": state["outcomes"],
        "manifest": state["rows"],
        "targets": state["targets_by_id"],
        "findings": [
            {**asdict(issue), "provenance": state["issue_cells"][issue.issue_id],
             "boxes": [asdict(box) for box in state["issue_boxes"][issue.issue_id]]}
            for issue in result.errors
        ],
        "pages": [
            {"page": page.number, "source_offset": report.source_page_offsets[index],
             "actual_offset": report.actual_page_offsets[index],
             "expected": list(audit.fc.unicode_to_cells(page.flatten())),
             "actual": list(report.actual_pages[index]),
             "alignment": [asdict(op) for op in report.page_alignments[index]]}
            for index, page in enumerate(report.expected_document.pages)
        ],
    }
    path = OUT / f"{label}.json"
    path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    print(json.dumps({"variant": label, "path": str(path),
                      "policy": snapshot["summary"]["policy"]}), flush=True)


def capture_both():
    OUT.mkdir(parents=True, exist_ok=True)
    paths = [audit.fc.DOCX, audit.PDF, audit.MANIFEST,
             audit.PDF.with_suffix(".brf"),
             Path(alignment.__file__), Path(api.__file__),
             Path(inspect.getfile(api.BrailleValidator))]
    paths = [path for path in paths if path.is_file()]
    before = {str(path): digest(path) for path in paths}
    original = alignment._align_bounded_block
    source = inspect.getsource(original)
    assert source.count(BRANCH) == 1, "Latest tie branch changed; refuse an unverified pre variant"
    namespace = dict(vars(alignment))
    exec(compile(source.replace(BRANCH, ""), "<audit_pre_deletion_tie>", "exec"), namespace)
    capture("pre", namespace["_align_bounded_block"])
    capture("post", original)
    after = {str(path): digest(path) for path in paths}
    assert before == after, "Diagnostic modified an input or production file"
    (OUT / "integrity.json").write_text(json.dumps({
        "hashes_before": before, "hashes_after": after,
        "removed_branch": BRANCH,
        "coordinate_convention": "half-open spans; expected page-local; alignment actual document-global; box points top-origin",
    }, indent=2), encoding="utf-8")


def geometry(cell):
    return tuple(round(float(cell[key]), 3) for key in ("x0", "x1", "top", "bottom"))


def analyze():
    """Offline adjudication of saved runs; never invokes validation."""
    snapshots = {name: json.loads((OUT / f"{name}.json").read_text(encoding="utf-8"))
                 for name in ("pre", "post")}
    pre, post = snapshots["pre"], snapshots["post"]
    accepted = {"correct", "equivalent_identical_insertion", "equivalent_adjacent_deletion"}
    unresolved = [item for item in post["outcomes"] if item["state"] not in accepted]
    assert len(unresolved) == 20
    rows = {row["error_id"]: row for row in post["manifest"]}
    evidence = []
    with audit.pdfplumber.open(str(audit.PDF)) as pdf:
        for outcome in unresolved:
            row = rows[outcome["id"]]
            page, index, kind = row["page"], row["expected_index"], row["operation"]
            chars = pdf.pages[page - 1].chars
            targets = post["targets"][outcome["id"]][1]
            target_geometry = {geometry(char) for char in targets}
            target_indices = [i for i, char in enumerate(chars) if geometry(char) in target_geometry]
            assert len(target_indices) == 1
            expected_span = [index, index if kind == "insertion" else index + 1]
            run = audit.identical_run(chars, target_indices[0]) if kind == "insertion" else ()
            run_geometry = {geometry(chars[i]) for i in run}
            inserted_mask = audit.fc.char_mask(row["code_target"], "duxbury") if kind == "insertion" else None
            record = {
                "id": outcome["id"], "type": kind, "page": page,
                "manifest": row, "expected_span": expected_span,
                "target_pdf_character_indices": target_indices,
                "target_cells": [{key: char[key] for key in ("text", "x0", "x1", "top", "bottom")}
                                 for char in targets],
                "identical_insertion_run": list(run), "inserted_mask": inserted_mask,
            }
            for label, snapshot in snapshots.items():
                outcomes = {item["id"]: item for item in snapshot["outcomes"]}
                row_order = [item["id"] for item in snapshot["outcomes"]]
                prior = snapshot["outcomes"][:row_order.index(outcome["id"])]
                consumed_before = {item["issue_id"]: item["id"] for item in prior
                                   if "issue_id" in item and item["state"] != "equivalent_adjacent_deletion"}
                owners = {}
                for item in snapshot["outcomes"]:
                    if "issue_id" in item:
                        owners.setdefault(item["issue_id"], []).append(item["id"])
                candidates = []
                for finding in snapshot["findings"]:
                    if finding["source_page_number"] != page:
                        continue
                    span = finding["span"]
                    cells, boxes = finding["provenance"], finding["boxes"]
                    span_exact = [span["expected_start"], span["expected_end"]] == expected_span
                    physical_exact = {geometry(cell) for cell in cells} == target_geometry
                    shape = (not finding["expected_braille"] if kind == "insertion" else not finding["actual_braille"])
                    strict = abs(span["expected_start"] - index) <= 4 and shape and (span_exact or physical_exact)
                    guards = {
                        "insertion": kind == "insertion",
                        "empty_expected": not finding["expected_braille"],
                        "one_actual_cell": len(finding["actual_braille"]) == 1,
                        "actual_mask_matches_original_manifest_mask": finding["actual_braille"] == [int(row["actual_mask"])],
                        "actual_mask_matches_inserted_cell": finding["actual_braille"] == [inserted_mask],
                        "near_expected_run": abs(span["expected_start"] - index) <= len(run),
                        "one_provenance_in_run": len(cells) == 1 and geometry(cells[0]) in run_geometry,
                        "exact_box_on_provenance": len(boxes) == len(cells) == 1 and boxes[0]["page"] == page
                                                   and all(abs(boxes[0][key] - cells[0][key]) < .02
                                                           for key in ("x0", "x1", "top", "bottom")),
                        "nontrivial_run": len(run) > 1,
                    }
                    common = [value for key, value in guards.items() if not key.startswith("actual_mask_matches")]
                    equivalence_current = all(common) and guards["actual_mask_matches_original_manifest_mask"]
                    equivalence_intended = all(common) and guards["actual_mask_matches_inserted_cell"]
                    candidates.append({
                        "finding_id": finding["issue_id"], "strict_compatible": strict,
                        "current_equivalence_compatible": equivalence_current,
                        "inserted_mask_equivalence_compatible": equivalence_intended,
                        "available_at_row": finding["issue_id"] not in consumed_before,
                        "consumed_before_by": consumed_before.get(finding["issue_id"]),
                        "final_associations": owners.get(finding["issue_id"], []),
                        "span_exact": span_exact, "physical_exact": physical_exact,
                        "shape_match": shape, "equivalence_guards": guards,
                    })
                if kind == "deletion":
                    pre_outcome = next(item for item in pre["outcomes"] if item["id"] == outcome["id"])
                    primary_id = pre_outcome["issue_id"]
                else:
                    intended = [item for item in candidates if item["inserted_mask_equivalence_compatible"]]
                    assert len(intended) == 1 and intended[0]["available_at_row"]
                    primary_id = intended[0]["finding_id"]
                primary = next(finding for finding in snapshot["findings"] if finding["issue_id"] == primary_id)
                page_record = snapshot["pages"][page - 1]
                opcodes = [op for op in page_record["alignment"]
                           if op["expected_end"] >= index - 2 and op["expected_start"] <= index + 2]
                char_indices = [[i for i, char in enumerate(chars) if geometry(char) == geometry(cell)]
                                for cell in primary["provenance"]]
                assert all(len(indices) == 1 for indices in char_indices)
                assert len(primary["boxes"]) == len(primary["provenance"]) == 1
                assert geometry(primary["boxes"][0]) == geometry(primary["provenance"][0])
                astart, aend = primary["actual_cell_start"], primary["actual_cell_end"]
                # Independent raw-cell rank check: the finding's actual cell
                # (or zero-width gap's following cell) is the boxed PDF glyph.
                nonblank_pdf = [i for i, char in enumerate(chars)
                                if audit.fc.char_mask(char["text"], "duxbury") != 0]
                raw_rank = sum(mask != 0 for mask in page_record["actual"][:astart])
                assert page_record["actual"][astart] != 0
                assert nonblank_pdf[raw_rank] == char_indices[0][0]
                assert page_record["actual"][astart] == audit.fc.char_mask(primary["provenance"][0]["source_char"], "duxbury")
                record[label] = {
                    "outcome": outcomes[outcome["id"]], "finding": primary,
                    "alignment_operations": opcodes,
                    "expected_context_start": max(0, index - 4),
                    "expected_context": page_record["expected"][max(0, index - 4):index + 5],
                    "actual_page_span": [astart, aend],
                    "actual_document_span": [page_record["actual_offset"] + astart,
                                             page_record["actual_offset"] + aend],
                    "actual_context_start": max(0, astart - 3),
                    "actual_context": page_record["actual"][max(0, astart - 3):max(astart + 4, aend)],
                    "pdf_character_indices": char_indices,
                    "independent_actual_cell_to_pdf_rank": raw_rank,
                    "actual_to_provenance_verified": True,
                    "all_same_page_candidate_checks": candidates,
                    "all_current_compatible_candidates": [item for item in candidates
                        if item["strict_compatible"] or item["current_equivalence_compatible"]],
                    "all_inserted_mask_equivalent_candidates": [item for item in candidates
                        if item["inserted_mask_equivalence_compatible"]],
                }
            if kind == "deletion":
                before, after = record["pre"]["finding"], record["post"]["finding"]
                assert record["pre"]["outcome"]["state"] == "correct"
                assert before["span"]["expected_start"] == index
                assert after["span"]["expected_start"] == index - 1
                assert after["span"]["expected_end"] == index
                assert before["expected_braille"] == after["expected_braille"]
                assert before["actual_cell_start"] == after["actual_cell_start"] + 1
                expected = post["pages"][page - 1]["expected"]
                assert expected[index - 1] == expected[index]
                assert expected[:index - 1] + expected[index:] == expected[:index] + expected[index + 1:]
                assert not record["post"]["all_current_compatible_candidates"]
                primary_checks = next(check for check in record["post"]["all_same_page_candidate_checks"]
                                      if check["finding_id"] == after["issue_id"])
                assert primary_checks["available_at_row"] and not primary_checks["final_associations"]
                assert all(check["available_at_row"] for check in record["pre"]["all_current_compatible_candidates"])
                record["category"] = "A"
                record["evidence"] = (
                    "The only runtime change moves the deletion from the second to the first identical expected cell. "
                    "The gap and its exact provenance/box move one surviving cell earlier. Pre is exact under the current "
                    "deletion-anchor policy; post fails. This is a localization-policy regression, not downstream mapping "
                    "corruption: deleting either identical expected cell produces the same cell stream. "
                    "No evaluator-compatible candidate was consumed by another mutation."
                )
            else:
                assert record["pre"]["finding"] == record["post"]["finding"]
                assert record["pre"]["alignment_operations"] == record["post"]["alignment_operations"]
                assert inserted_mask == 32 and int(row["actual_mask"]) == 15
                assert all(audit.fc.char_mask(chars[i]["text"], "duxbury") == inserted_mask for i in run)
                assert not record["post"]["all_current_compatible_candidates"]
                record["category"] = "B"
                record["evidence"] = (
                    "Pre/post alignment, finding, provenance, and box are identical. One available insertion finding "
                    "lies in the same contiguous two-comma run as the target and satisfies every equivalence guard "
                    "except comparison against actual_mask=15 (the original target p). code_target=',' and the actual "
                    "inserted PDF glyph both encode mask 32. The evaluator checks the wrong manifest field. "
                    "The unique compatible finding has not been consumed by another mutation."
                )
            evidence.append(record)

    counts = {key: sum(item["category"] == key for item in evidence) for key in "ABCDEFG"}
    assert counts == {"A": 15, "B": 5, "C": 0, "D": 0, "E": 0, "F": 0, "G": 0}
    assert sum(counts.values()) == 20
    payload = {"bucket_counts": counts, "cases": evidence}
    (OUT / "twenty_cases.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    columns = ["mutation_id", "type", "page", "expected_span", "target_pdf_indices", "target_cells",
               "pre_finding", "pre_alignment", "pre_actual_span", "pre_provenance", "pre_box", "pre_candidates",
               "post_finding", "post_alignment", "post_actual_span", "post_provenance", "post_box", "post_candidates",
               "policy_compatible_candidates", "category", "evidence"]
    with (OUT / "twenty_cases.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for item in evidence:
            row = {"mutation_id": item["id"], "type": item["type"], "page": item["page"],
                   "expected_span": item["expected_span"], "target_pdf_indices": item["target_pdf_character_indices"],
                   "target_cells": item["target_cells"], "category": item["category"], "evidence": item["evidence"],
                   "policy_compatible_candidates": item["post"]["all_inserted_mask_equivalent_candidates"]}
            for label in ("pre", "post"):
                trace = item[label]
                row.update({f"{label}_finding": trace["finding"],
                            f"{label}_alignment": trace["alignment_operations"],
                            f"{label}_actual_span": trace["actual_page_span"],
                            f"{label}_provenance": trace["finding"]["provenance"],
                            f"{label}_box": trace["finding"]["boxes"],
                            f"{label}_candidates": trace["all_current_compatible_candidates"]})
            writer.writerow({key: json.dumps(value) if isinstance(value, (list, dict)) else value
                             for key, value in row.items()})
    write_report(evidence, counts)
    print(json.dumps({"buckets": counts, "total": len(evidence), "evidence": str(OUT)}, indent=2))


def write_report(evidence, counts):
    lines = [
        "# Audit of the 20 unresolved diverse-fixture mutations", "",
        "All 20 are accounted for: A=15, B=5, C=D=E=F=G=0. Production and fixture files were unchanged.", "",
        "The diagnostic executed two controlled evaluations of the same frozen inputs. The pre variant removed only "
        "the latest identical-cell deletion branch in memory; post used the on-disk function unchanged. This is not the "
        "older global fallback. Both complete outputs are saved in `results/unresolved_twenty_trace/pre.json` and "
        "`post.json`; subsequent analysis reads those snapshots without rerunning validation. `integrity.json` records "
        "the removed branch and matching before/after SHA-256 hashes.", "",
        "Pre: 989 policy-accepted mutations, 11 unresolved. Post: 980 accepted, 20 unresolved. The tie-break repairs "
        "six earlier deletion associations and regresses 15 previously exact deletion anchors: net -9 accepted mutations. "
        "The five insertion failures exist in both variants.", "",
        "| Bucket | Count |", "| --- | ---: |",
    ]
    names = {"A": "Regression caused by latest deletion tie-break", "B": "Valid identical-run equivalence rejected by evaluator",
             "C": "Evaluator association/consumption collision", "D": "Genuine pre-existing alignment defect",
             "E": "Correct alignment, wrong provenance", "F": "Correct provenance, wrong box", "G": "Other"}
    lines.extend(f"| {key}. {names[key]} | {counts[key]} |" for key in "ABCDEFG")
    lines.extend([
        "| Total | 20 |", "",
        "A means regression against the established strict deletion-anchor policy. All 15 delete one of two identical "
        "expected cells; either deletion produces the same stream. The new branch selects the earlier cell, moving the "
        "gap and next-surviving-cell anchor one position earlier. Provenance and rectangles faithfully follow that "
        "new gap. No evidence supports a separate provenance or renderer defect. These cases have not been silently "
        "accepted under an expanded deletion-equivalence policy.", "",
        "B is a concrete audit field error: `evaluate_frozen_diverse.py` compares the insertion mask to "
        "`row['actual_mask']`. In these five rows that is the original target `p` (15); the inserted `code_target` is "
        "`,` (32). The PDF contains a contiguous pair of identical capitalization cells. The unique available finding "
        "boxes the other member of that pair. Every existing equivalence condition passes when tested against the "
        "inserted cell. No candidate was consumed by another mutation. This report diagnoses the guard without changing it.", "",
        "Coordinates: all spans are zero-based and half-open. E is expected page-local; a is actual validator page-local. "
        "Detailed alignment operations use document-global actual offsets and are saved with both coordinate systems. "
        "PDF character indices are zero-based on the corrupted PDF page. Boxes are `(x0, top, x1, bottom)` in points. "
        "Displayed coordinates are rounded to three decimals; JSON/CSV preserve full precision. Each reported box "
        "exactly equals its one provenance cell. `none` in the candidate columns means no finding meets the current "
        "literal evaluator predicates even before availability filtering. All same-page candidate checks, guard booleans, "
        "and consumption owners are preserved in `twenty_cases.json`.", "",
        "| ID/type | Page / intended E | Pre finding: E; a; PDF char | Post finding: E; a; PDF char | Current compatible candidates pre / post | Proven equivalence candidate | Bucket |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ])
    def brief(trace):
        finding = trace["finding"]
        return (f"{finding['issue_id']}: [{finding['span']['expected_start']},{finding['span']['expected_end']}); "
                f"{trace['actual_page_span']}; {trace['pdf_character_indices']}")
    def ids(items):
        return ", ".join(item["finding_id"] for item in items) or "none"
    for item in evidence:
        lines.append(f"| {item['id']} {item['type']} | {item['page']} / {item['expected_span']} | "
                     f"{brief(item['pre'])} | {brief(item['post'])} | "
                     f"{ids(item['pre']['all_current_compatible_candidates'])} / {ids(item['post']['all_current_compatible_candidates'])} | "
                     f"{ids(item['post']['all_inserted_mask_equivalent_candidates'])} | {item['category']} |")
    for item in evidence:
        lines.extend(["", f"## {item['id']} — bucket {item['category']}", "", item["evidence"], "",
                      f"Expected mutation span: {item['expected_span']}; target PDF char {item['target_pdf_character_indices']}.", "",
                      "| Trace | Expected → actual masks | Actual span (page / document) | Provenance: PDF char, glyph, box |",
                      "| --- | --- | --- | --- |"])
        for label in ("pre", "post"):
            trace, finding = item[label], item[label]["finding"]
            cell = finding["provenance"][0]
            box = tuple(round(cell[key], 3) for key in ("x0", "top", "x1", "bottom"))
            lines.append(f"| {label} | {finding['expected_braille']} → {finding['actual_braille']} | "
                         f"{trace['actual_page_span']} / {trace['actual_document_span']} | "
                         f"{trace['pdf_character_indices']}, `{cell['source_char']}`, {box} |")
        target = item["target_cells"][0]
        lines.extend(["", f"Required target/anchor: `{target['text']}` at "
                      f"{tuple(round(target[key], 3) for key in ('x0', 'top', 'x1', 'bottom'))}.", "",
                      "Pre alignment: `" + json.dumps(item["pre"]["alignment_operations"]) + "`", "",
                      "Post alignment: `" + json.dumps(item["post"]["alignment_operations"]) + "`"])
    lines.extend(["", "## Engineering conclusion", "",
                  "The dominant cause is the new global preference for the first deletable identical cell (15/20). "
                  "The remaining 5/20 are rejected insertion equivalences caused by reading the original target mask. "
                  "There is no association collision in this cohort, and no independent provenance or box defect. "
                  "Any subsequent production fix must preserve the six repaired cases while addressing the 15 shifted "
                  "anchors, or explicitly establish deletion equivalence before changing adjudication. Merely reverting "
                  "the branch would restore those 15 but reintroduce the six earlier failures. The insertion evaluator "
                  "can use the actual inserted cell independently of production. No production/evaluator behavior was "
                  "changed in this diagnostic task. Combined closure remains FAIL.", ""])
    report = audit.fc.ROOT / "reports/unresolved_twenty_tie_break_audit.md"
    report.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    if "--capture" in sys.argv:
        capture_both()
    else:
        analyze()
