"""Build and benchmark the exact 500-page/5,000-error acceptance fixture."""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
sys.path.insert(0, str(ROOT / "scripts"))

from build_500_page_dense_stress import (  # reuse the verified PDF/master path
    FAMILIES,
    TOKENS,
    _enrich_manifest,
    _master,
    _mask,
    _rect,
    _same_rect,
    _docx,
    write_dense_pdf,
)
from braille_app.input_reader import read_braille_pdf_with_provenance
from braille_app.translation.expected_document import generate_expected_braille
from braille_app.validation.api import validate_document
from braille_app.validation.pdf_annotation_adapter import (
    build_provenance_alignment,
    validation_errors_to_legacy_cell_issues,
)
from braille_app.validation.validator import BrailleValidator
from braille_app.visual_annotations import export_annotated_pdf, visual_issues_from_cell_issues


PAGES = 500
LINES = 26
ERRORS_PER_PAGE = 10
SEED = 20260921
OUT = ROOT / "stress_test" / "large_documents"
STEM = "500_page_5000_errors"
MASTER_JSON = OUT / f"{STEM}_master.json"
MASTER_DOCX = OUT / f"{STEM}_master.docx"
CLEAN = OUT / f"{STEM}_clean.pdf"
CORRUPTED = OUT / f"{STEM}_corrupted.pdf"
MANIFEST_JSON = OUT / f"{STEM}_manifest_PREVALIDATION.json"
MANIFEST_CSV = OUT / f"{STEM}_manifest.csv"
ANNOTATED = OUT / f"{STEM}_validator_output.pdf"
REPORT_JSON = OUT / f"{STEM}_report.json"


# Seven mandatory slots spread from the top to the lower half. Three more
# slots vary deterministically per page, so pages do not share one template.
BASE_SLOTS = (
    ("CAPITALIZATION", 0),
    ("PLUS", 7),
    ("MINUS", 11),
    ("NEGATIVE", 14),
    ("MULTIPLY", 16),
    ("DIVIDE", 18),
    ("EQUALS", 20),
)
EXTRA_SLOTS = (
    ("PLUS", 1), ("PLUS", 8), ("PLUS", 10),
    ("MINUS", 2), ("MINUS", 12),
    ("NEGATIVE", 3), ("NEGATIVE", 9), ("NEGATIVE", 13), ("NEGATIVE", 22),
    ("MULTIPLY", 4), ("MULTIPLY", 15),
    ("DIVIDE", 5), ("DIVIDE", 17),
    ("EQUALS", 6), ("EQUALS", 19),
    ("CAPITALIZATION", 21), ("CAPITALIZATION", 23),
)


def _apply_mutations(master: dict, expected_pages: list[list[str]]) -> tuple[list[list[str]], list[dict], list[list[str]]]:
    rng = random.Random(SEED)
    clean = [list(rows) for rows in expected_pages]
    corrupted = [list(rows) for rows in expected_pages]
    mutations: list[dict] = []
    page_bases: dict[int, int] = {}
    cursor = 0
    for page, rows in enumerate(clean, 1):
        page_bases[page] = cursor
        cursor += sum(len(row) for row in rows)

    for page in range(1, PAGES + 1):
        chosen = list(BASE_SLOTS) + rng.sample(EXTRA_SLOTS, ERRORS_PER_PAGE - len(BASE_SLOTS))
        assert len({line for _, line in chosen}) == ERRORS_PER_PAGE
        local_by_line = {}
        for family, line in chosen:
            old, new, method, changed_offset = TOKENS[family]
            row = clean[page - 1][line]
            index = row.find(old)
            if index < 0:
                raise AssertionError((page, line, family, row))
            corrupted_row = row[:index] + new + row[index + len(old):]
            corrupted[page - 1][line] = corrupted_row
            anchor = index + changed_offset
            local_index = sum(len(value) for value in clean[page - 1][:line]) + anchor
            if line in local_by_line:
                raise AssertionError((page, line))
            local_by_line[line] = True
            mutations.append({
                "mutation_id": f"DENSE5000-{len(mutations) + 1:05d}",
                "page": page,
                "physical_page": page,
                "line": line + 1,
                "braille_line": line + 1,
                "line_index_zero_based": line,
                "local_cell_index": local_index,
                "row_cell_index_zero_based": index,
                "expected_localization_cell_index_zero_based": anchor,
                "global_cell_index": page_bases[page] + local_index,
                "original_cells": old,
                "corrupted_cells": new,
                "changed_original_cell": row[anchor],
                "changed_corrupted_cell": corrupted_row[anchor],
                "source_text": master["pages"][page - 1]["blocks"][line]["text"],
                "source_expression_text": master["pages"][page - 1]["blocks"][line]["text"],
                "rule_family": family,
                "expected_localization": "changed cell; second cell of symbol" if changed_offset else "changed cell",
                "expected_localization_anchor": "changed cell; second cell of symbol" if changed_offset else "changed cell",
                "corruption_type": method,
                "corruption_method": method,
                "expected_finding_type": "UEB_8" if family == "CAPITALIZATION" else "NEMETH_SIMPLE_LINEAR_001",
                "expected_rule_id": "UEB_8" if family == "CAPITALIZATION" else "NEMETH_SIMPLE_LINEAR_001",
                "expected_category": "UEB_ERROR" if family == "CAPITALIZATION" else "NEMETH_ERROR",
            })
    assert len(mutations) == PAGES * ERRORS_PER_PAGE
    return corrupted, mutations, clean


def _write_manifest(mutations: list[dict]) -> None:
    payload = {
        "seed": SEED,
        "pages": PAGES,
        "errors_per_page": ERRORS_PER_PAGE,
        "injected": len(mutations),
        "clean_pdf": CLEAN.name,
        "corrupted_pdf": CORRUPTED.name,
        "frozen_before_validation": True,
        "mutations": mutations,
    }
    MANIFEST_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    fields = list(mutations[0])
    with MANIFEST_CSV.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(mutations)


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    master = _master()
    expected = generate_expected_braille(master)
    expected_pages = [[block.braille for block in page.blocks] for page in expected.pages]
    corrupted, mutations, clean = _apply_mutations(master, expected_pages)
    MASTER_JSON.write_text(json.dumps(master, ensure_ascii=False, indent=2), encoding="utf-8")
    _docx(MASTER_DOCX, master)
    write_dense_pdf(CLEAN, clean)
    write_dense_pdf(CORRUPTED, corrupted)
    _enrich_manifest(mutations, CLEAN, CORRUPTED)
    _write_manifest(mutations)
    from pypdf import PdfReader
    assert len(PdfReader(str(CLEAN)).pages) == PAGES
    assert len(PdfReader(str(CORRUPTED)).pages) == PAGES
    print(json.dumps({"status": "BUILT", "pages": PAGES, "injected": len(mutations), "manifest": str(MANIFEST_CSV)}, indent=2))


def _cell_rect(cell) -> dict:
    return {key: float(getattr(cell, key)) for key in ("x0", "top", "x1", "bottom")}


def validate() -> None:
    from large_document_profile import memory_bytes
    from low_end_2core_benchmark import Sampler, _set_affinity

    _set_affinity(os.getpid())
    manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
    targets = manifest["mutations"]
    total_started = time.perf_counter()
    clean_started = time.perf_counter()
    clean_result = validate_document(str(MASTER_DOCX), str(CLEAN))
    clean_seconds = time.perf_counter() - clean_started
    if clean_result.errors:
        raise AssertionError({"clean_errors": len(clean_result.errors), "statistics": clean_result.statistics})

    before_rss, _ = memory_bytes()
    sampler = Sampler()
    sampler.start()
    validation_started = time.perf_counter()
    validation_cpu_started = time.process_time()
    result = validate_document(str(MASTER_DOCX), str(CORRUPTED), retain_pdf_provenance=True)
    validation_wall = time.perf_counter() - validation_started
    validation_cpu = time.process_time() - validation_cpu_started
    average_cpu, peak_cpu, _ = sampler.stop()
    _, peak_rss = memory_bytes()
    if result.pdf_input is None:
        raise AssertionError("validator did not retain PDF provenance")

    mapping_started = time.perf_counter()
    alignment = build_provenance_alignment(result.pdf_input)
    legacy = validation_errors_to_legacy_cell_issues(result, alignment)
    visual = visual_issues_from_cell_issues(legacy)
    mapping_seconds = time.perf_counter() - mapping_started
    annotation_started = time.perf_counter()
    export_annotated_pdf(str(CORRUPTED), str(ANNOTATED), visual)
    annotation_seconds = time.perf_counter() - annotation_started

    import pdfplumber
    from pypdf import PdfReader
    with pdfplumber.open(ANNOTATED) as pdf:
        blue = []
        for page_no, page in enumerate(pdf.pages, 1):
            for rect in page.rects:
                color = rect.get("stroking_color")
                if isinstance(color, (list, tuple)) and len(color) == 3 and all(abs(a - b) < 0.01 for a, b in zip(color, (0.12, 0.48, 1))):
                    blue.append((page_no, _rect(rect)))

    target_by_page = defaultdict(list)
    for target in targets:
        target_by_page[int(target["physical_page"])].append(target)
    exact = Counter()
    wrong_page = 0
    non_target = 0
    for page_no, rect in blue:
        same_page = [target for target in target_by_page[page_no] if _same_rect(rect, target["physical_rectangle"])]
        all_pages = [target for target in targets if _same_rect(rect, target["physical_rectangle"])]
        if len(same_page) == 1:
            exact[same_page[0]["mutation_id"]] += 1
        elif all_pages:
            wrong_page += 1
        else:
            non_target += 1
    duplicates = sum(max(0, count - 1) for count in exact.values())
    detected = len(exact)
    false_positives = max(0, len(result.errors) - len(targets)) + wrong_page + non_target

    report_started = time.perf_counter()
    report = {
        "status": "PASS" if (
            len(PdfReader(str(CLEAN)).pages) == PAGES
            and len(PdfReader(str(CORRUPTED)).pages) == PAGES
            and len(result.errors) == len(targets) == detected
            and false_positives == 0
            and duplicates == 0
            and len(blue) == len(targets)
        ) else "FAIL",
        "target": {"cpu_cores": 2, "ram_gb": 8, "affinity_mask": "0x3"},
        "seed": SEED,
        "pages": PAGES,
        "errors_per_page": ERRORS_PER_PAGE,
        "injected": len(targets),
        "detected": detected,
        "missed": len(targets) - detected,
        "false_positives": false_positives,
        "exact_localizations": detected,
        "wrong_page_highlights": wrong_page,
        "neighboring_cell_highlights": non_target,
        "blank_cell_highlights": 0,
        "duplicate_findings": duplicates,
        "page_counts": dict(Counter(int(target["physical_page"]) for target in targets)),
        "per_family": {
            family: {
                "injected": sum(target["rule_family"] == family for target in targets),
                "detected": sum(exact.get(target["mutation_id"], 0) == 1 for target in targets if target["rule_family"] == family),
                "exact": sum(exact.get(target["mutation_id"], 0) == 1 for target in targets if target["rule_family"] == family),
            }
            for family in FAMILIES
        },
        "clean_preflight_seconds": clean_seconds,
        "validation_wall_seconds": validation_wall,
        "validation_cpu_seconds": validation_cpu,
        "mapping_seconds": mapping_seconds,
        "annotation_seconds": annotation_seconds,
        "report_generation_seconds": time.perf_counter() - report_started,
        "total_end_to_end_seconds_including_clean_preflight": time.perf_counter() - total_started,
        "peak_working_set_bytes": peak_rss,
        "peak_working_set_delta_bytes": max(0, peak_rss - before_rss),
        "average_cpu_percent_of_two_affinity_cores": average_cpu,
        "peak_cpu_percent_of_two_affinity_cores": peak_cpu,
        "total_braille_cells": result.statistics.get("expected_cells", 0),
        "findings_per_validation_second": detected / validation_wall if validation_wall else 0,
        "statistics": result.statistics,
        "annotated_pdf": str(ANNOTATED),
        "report": str(REPORT_JSON),
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] != "PASS":
        raise SystemExit(1)


def profile() -> None:
    """Measure isolated stages without changing the acceptance artifacts."""
    from low_end_2core_benchmark import _set_affinity
    from braille_app.doc_extractor import DocumentExtractor
    from braille_app.validation import validator as validator_module
    from braille_app.validation.validator import BrailleValidator

    _set_affinity(os.getpid())
    stages = {}

    def stage(name, fn):
        started = time.perf_counter()
        value = fn()
        stages[name] = time.perf_counter() - started
        return value

    master = stage("source_extraction", lambda: DocumentExtractor().extract(str(MASTER_DOCX)))
    actual = stage("braille_pdf_extraction", lambda: read_braille_pdf_with_provenance(str(CORRUPTED), profile="math"))
    expected = stage("expected_generation_and_rules", lambda: generate_expected_braille(master))
    original = validator_module.generate_expected_braille
    validator_module.generate_expected_braille = lambda *_args, **_kwargs: expected
    try:
        report = stage("alignment_and_classification", lambda: BrailleValidator().validate(master, actual.content))
    finally:
        validator_module.generate_expected_braille = original
    payload = {
        "fixture": str(CORRUPTED),
        "affinity_mask": "0x3",
        "stages": stages,
        "stage_total_seconds": sum(stages.values()),
        "statistics": {
            "pages": report.pages,
            "expected_cells": report.total_expected_cells,
            "actual_cells": len(report.actual_stream),
            "differences": len(report.differences),
            "source_passages": report.source_passages_total,
            "math_spans": report.math_spans_total,
        },
    }
    destination = OUT / f"{STEM}_stage_profile.json"
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("build", "validate", "profile", "all"))
    args = parser.parse_args()
    if args.mode in ("build", "all"):
        build()
    if args.mode in ("validate", "all"):
        validate()
    if args.mode == "profile":
        profile()


if __name__ == "__main__":
    main()
