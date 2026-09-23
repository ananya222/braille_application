"""Read-only active controls; never invoke fixture writers or the old validator."""
import ast
import csv
import hashlib
import json
import time

import final_combined_closure as fc
from braille_app.validation.api import validate_document
from braille_app.validation.pdf_annotation_adapter import build_provenance_alignment, validation_errors_to_legacy_cell_issues
from braille_app.visual_annotations import visual_issues_from_cell_issues


def validate(master, pdf, profile):
    started = time.perf_counter()
    result = validate_document(master, pdf, profile=profile, retain_pdf_provenance=True)
    visuals = visual_issues_from_cell_issues(validation_errors_to_legacy_cell_issues(
        result, build_provenance_alignment(result.pdf_input)))
    metadata = {"findings": len(result.errors), "reviews": len(result.reviews),
                "duplicate_ids": len(result.errors) - len({issue.issue_id for issue in result.errors}),
                "runtime_seconds": round(time.perf_counter() - started, 3)}
    return result, visuals, metadata


def main():
    diverse = json.loads((fc.RESULTS / "frozen_observable_closure.json").read_text(encoding="utf-8"))
    assert diverse["closure_pass"], "Run controls only after the diverse pass"
    case1 = fc.ROOT / "stress_test/uncontracted_case1_alphabet_words"
    inputs = [fc.DOCX, fc.PDF, fc.CORRUPTED / "final_case1_case2_corrupted_1000.pdf",
              fc.MANIFESTS / "mutation_manifest.csv", case1 / "case1_source.json",
              case1 / "case1_corrupted.pdf", case1 / "mutation_manifest.csv"]
    before = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs}
    master, _ = fc.master_and_expected()
    _, _, clean = validate(master, fc.PDF, fc.PROFILE)
    assert clean["findings"] == clean["reviews"] == clean["duplicate_ids"] == 0
    print("Clean Duxbury: " + json.dumps(clean), flush=True)

    pdf = fc.CORRUPTED / "final_case1_case2_corrupted_1000.pdf"
    _, visuals, substitutions = validate(master, pdf, fc.PROFILE)
    with (fc.MANIFESTS / "mutation_manifest.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        for field in ("physical_braille_page", "expected_physical_pdf_char_index"):
            row[field] = int(row[field])
    substitutions.update(fc._blue_box_audit(rows, visuals, pdf))
    assert substitutions["findings"] == substitutions["target_boxes_hit"] == 1000
    assert substitutions["reviews"] == substitutions["duplicate_ids"] == substitutions["non_target_blue_boxes"] == substitutions["duplicate_blue_boxes"] == 0
    print("Frozen substitutions: " + json.dumps(substitutions), flush=True)

    master1 = json.loads((case1 / "case1_source.json").read_text(encoding="utf-8"))
    result1, visuals1, case1_metrics = validate(master1, case1 / "case1_corrupted.pdf", "uncontracted_case1_alphabet_words")
    with (case1 / "mutation_manifest.csv").open(newline="", encoding="utf-8") as stream:
        golden = list(csv.DictReader(stream))
    targets = [(int(row["page"]), ast.literal_eval(row["actual_cell_location"])["box"]) for row in golden]
    def exact(box, target):
        return box.page == target[0] and all(abs(getattr(box, key) - target[1][key]) < .02 for key in ("x0", "x1", "top", "bottom"))
    boxes = [box for visual in visuals1 for box in visual.boxes]
    keys = [(box.page, *(round(getattr(box, key), 3) for key in ("x0", "x1", "top", "bottom"))) for box in boxes]
    case1_metrics.update({"exact_boxes": sum(any(exact(box, target) for box in boxes) for target in targets),
                          "off_target_boxes": sum(not any(exact(box, target) for target in targets) for box in boxes),
                          "duplicate_boxes": len(keys) - len(set(keys)),
                          "oracle": "Frozen Case 1 accepted physical anchor/box records, not current validator output"})
    assert case1_metrics["findings"] == case1_metrics["exact_boxes"] == 500
    assert case1_metrics["reviews"] == case1_metrics["duplicate_ids"] == case1_metrics["off_target_boxes"] == case1_metrics["duplicate_boxes"] == 0
    print("Case 1: " + json.dumps(case1_metrics), flush=True)
    after = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs}
    assert before == after
    output = {"pass": True, "clean": clean, "substitutions": substitutions, "case1": case1_metrics,
              "hashes_before": before, "hashes_after": after, "old_contracted_nemeth_run": False}
    (fc.RESULTS / "active_uncontracted_controls.json").write_text(json.dumps(output, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
