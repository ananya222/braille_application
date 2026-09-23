"""Run the production validator without loading the mutation manifest."""

from __future__ import annotations

import hashlib
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from braille_app.validation.api import validate_document
from braille_app.validation.pdf_annotation_adapter import (
    build_provenance_alignment,
    validation_errors_to_legacy_cell_issues,
)
from braille_app.visual_annotations import visual_issues_from_cell_issues

BASE = ROOT / "stress_test" / "uncontracted_case3_numbers"
SOURCE = BASE / "source" / "case3_numbers_clean.docx"
PDF = BASE / "output" / "case3_corrupted.pdf"
FREEZE = BASE / "manifest" / "case3_fixture_frozen.json"
RESULT = BASE / "results" / "case3_validation_result_after_boundary_refinement.json"
PROFILE = "uncontracted_case3_numbers"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def issue_record(issue) -> dict:
    return {
        "issue_id": issue.issue_id,
        "status": issue.status,
        "category": issue.category,
        "rule_id": issue.rule_id,
        "source_page_number": issue.source_page_number,
        "actual_page_number": issue.actual_page_number,
        "braille_page": issue.braille_page,
        "block_id": issue.block_id,
        "span": issue.span,
        "source_text": issue.source_text,
        "expected_braille": list(issue.expected_braille),
        "actual_braille": list(issue.actual_braille),
        "actual_cell_start": issue.actual_cell_start,
        "actual_cell_end": issue.actual_cell_end,
        "localized_actual_ranges": [list(value) for value in issue.localized_actual_ranges],
        "rule_ids_considered": list(issue.rule_ids_considered),
        "structural_subtype": issue.structural_subtype,
    }


def run() -> dict:
    if RESULT.exists():
        raise FileExistsError(f"Refusing to overwrite the single Case 3 validator run: {RESULT}")
    frozen = json.loads(FREEZE.read_text(encoding="utf-8"))
    expected_hashes = frozen["hashes"]
    if sha256(SOURCE) != expected_hashes["source_docx"]:
        raise AssertionError("Frozen source hash changed")
    if sha256(PDF) != expected_hashes["corrupted_pdf"]:
        raise AssertionError("Frozen corrupted PDF hash changed")

    started = time.perf_counter()
    validation = validate_document(
        SOURCE, PDF, profile=PROFILE, retain_pdf_provenance=True
    )
    runtime = time.perf_counter() - started
    provenance = build_provenance_alignment(validation.pdf_input)
    cell_issues = validation_errors_to_legacy_cell_issues(validation, provenance)
    visuals = visual_issues_from_cell_issues(cell_issues)
    if len(cell_issues) != len(validation.errors) or len(visuals) != len(validation.errors):
        raise AssertionError("A confirmed validator finding did not reach the physical presentation stage")

    issues = []
    for index, issue in enumerate(validation.errors):
        issues.append({
            **issue_record(issue),
            "provenance_cells": cell_issues[index]["provenance_cells"],
            "boxes": [asdict(box) for box in visuals[index].boxes],
        })
    result = {
        "profile": PROFILE,
        "source_sha256": expected_hashes["source_docx"],
        "corrupted_pdf_sha256": expected_hashes["corrupted_pdf"],
        "runtime_seconds": round(runtime, 4),
        "statistics": validation.statistics,
        "error_count": len(validation.errors),
        "review_count": len(validation.reviews),
        "exclusion_count": len(validation.exclusions),
        "duplicate_issue_ids": len(validation.errors) - len({issue.issue_id for issue in validation.errors}),
        "errors": issues,
        "reviews": [issue_record(issue) for issue in validation.reviews],
        "exclusions": [issue_record(issue) for issue in validation.exclusions],
        "alignment_diagnostics": [issue_record(issue) for issue in validation.alignment_diagnostics],
        "physical_provenance": {
            "validator_cells": provenance.validator_cell_count,
            "pdf_cells": provenance.provenance_cell_count,
            "unmatched_cells": provenance.unmatched_cells,
            "unexplained_offsets": provenance.unexplained_offsets,
        },
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    result = run()
    print(json.dumps({
        "runtime_seconds": result["runtime_seconds"],
        "errors": result["error_count"],
        "reviews": result["review_count"],
        "duplicates": result["duplicate_issue_ids"],
        "statistics": result["statistics"],
        "result": str(RESULT.relative_to(ROOT)),
    }, ensure_ascii=False, indent=2))
