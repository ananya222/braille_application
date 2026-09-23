"""Run the Case 4 production validator without reading fixture history."""

from __future__ import annotations

import argparse
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

BASE = ROOT / "stress_test" / "uncontracted_case4_punctuation"
SOURCE = BASE / "source" / "case4_punctuation_clean.docx"
FREEZE = BASE / "manifest" / "case4_fixture_frozen.json"
PROFILE = "uncontracted_case4_punctuation"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _issue(issue) -> dict:
    return {"issue_id": issue.issue_id, "status": issue.status, "category": issue.category,
        "rule_id": issue.rule_id, "source_page_number": issue.source_page_number,
        "actual_page_number": issue.actual_page_number, "braille_page": issue.braille_page,
        "block_id": issue.block_id, "span": issue.span, "source_text": issue.source_text,
        "expected_braille": list(issue.expected_braille), "actual_braille": list(issue.actual_braille),
        "actual_cell_start": issue.actual_cell_start, "actual_cell_end": issue.actual_cell_end,
        "localized_actual_ranges": [list(value) for value in issue.localized_actual_ranges],
        "rule_ids_considered": list(issue.rule_ids_considered),
        "structural_subtype": issue.structural_subtype}


def run(clean: bool = False, result_path: Path | None = None) -> dict:
    frozen = json.loads(FREEZE.read_text(encoding="utf-8"))
    pdf_key = "clean_pdf" if clean else "corrupted_pdf"
    pdf_name = "case4_clean.pdf" if clean else "case4_corrupted.pdf"
    pdf = BASE / "output" / pdf_name
    result_path = result_path or BASE / "results" / (
        "case4_clean_validation.json" if clean
        else "case4_validation_result_after_insert_ownership.json"
    )
    if result_path.exists():
        raise FileExistsError(f"Refusing to overwrite Case 4 validator result: {result_path}")
    if _sha(SOURCE) != frozen["hashes"]["source_docx"] or _sha(pdf) != frozen["hashes"][pdf_key]:
        raise AssertionError("Case 4 frozen source/PDF hash mismatch")
    started = time.perf_counter()
    validation = validate_document(SOURCE, pdf, profile=PROFILE, retain_pdf_provenance=True)
    runtime = time.perf_counter() - started
    provenance = build_provenance_alignment(validation.pdf_input)
    cell_issues = validation_errors_to_legacy_cell_issues(validation, provenance)
    visuals = visual_issues_from_cell_issues(cell_issues)
    if len(cell_issues) != len(validation.errors) or len(visuals) != len(validation.errors):
        raise AssertionError("A confirmed Case 4 finding did not reach PDF highlighting")
    errors = [{**_issue(issue), "provenance_cells": cell_issues[index]["provenance_cells"],
               "boxes": [asdict(box) for box in visuals[index].boxes]}
              for index, issue in enumerate(validation.errors)]
    result = {"profile": PROFILE, "source_sha256": _sha(SOURCE),
        "pdf_sha256": _sha(pdf), "clean_run": clean,
        "runtime_seconds": round(runtime, 4), "statistics": validation.statistics,
        "error_count": len(errors), "review_count": len(validation.reviews),
        "exclusion_count": len(validation.exclusions),
        "duplicate_issue_ids": len(errors) - len({issue["issue_id"] for issue in errors}),
        "errors": errors, "reviews": [_issue(issue) for issue in validation.reviews],
        "exclusions": [_issue(issue) for issue in validation.exclusions],
        "alignment_diagnostics": [_issue(issue) for issue in validation.alignment_diagnostics],
        "physical_provenance": {"validator_cells": provenance.validator_cell_count,
            "pdf_cells": provenance.provenance_cell_count,
            "unmatched_cells": provenance.unmatched_cells,
            "unexplained_offsets": provenance.unexplained_offsets}}
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--result-path", type=Path)
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    output = run(clean=args.clean, result_path=args.result_path)
    print(json.dumps({key: output[key] for key in (
        "clean_run", "runtime_seconds", "error_count", "review_count",
        "duplicate_issue_ids", "statistics", "physical_provenance")}, ensure_ascii=False, indent=2))
