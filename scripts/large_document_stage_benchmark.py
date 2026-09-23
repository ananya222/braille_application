"""Measure isolated pipeline stages for one repeated fixture."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from braille_app.doc_extractor import DocumentExtractor
from braille_app.input_reader import read_braille_pdf_with_provenance
from braille_app.translation.expected_document import generate_expected_braille
from braille_app.validation import validator as validator_module
from braille_app.validation.validator import BrailleValidator
from large_document_profile import memory_bytes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_pages", type=int)
    parser.add_argument("kind", choices=("clean", "sparse_corrupted"))
    args = parser.parse_args()
    fixture = ROOT / "reports" / "large_document_fixtures"
    stem = f"repeat_{args.source_pages:04d}_source_pages"
    source = fixture / f"{stem}_source.pdf"
    actual_path = fixture / f"{stem}_{args.kind}_braille.pdf"
    stages = {}

    def stage(name, fn):
        before, _ = memory_bytes()
        started = time.perf_counter()
        value = fn()
        after, peak = memory_bytes()
        stages[name] = {
            "seconds": time.perf_counter() - started,
            "rss_delta_bytes": after - before,
            "peak_working_set_bytes": peak,
        }
        return value

    master = stage("master_extraction", lambda: DocumentExtractor().extract(str(source)))
    actual = stage(
        "braille_pdf_extraction",
        lambda: read_braille_pdf_with_provenance(str(actual_path), profile="math"),
    )
    expected = stage("expected_generation_and_rules", lambda: generate_expected_braille(master))
    original = validator_module.generate_expected_braille
    validator_module.generate_expected_braille = lambda *_args, **_kwargs: expected
    try:
        report = stage("comparison_alignment", lambda: BrailleValidator().validate(master, actual.content))
    finally:
        validator_module.generate_expected_braille = original
    payload = {
        "source_pages": args.source_pages,
        "kind": args.kind,
        "source": str(source),
        "actual": str(actual_path),
        "stages": stages,
        "statistics": {
            "pages": report.pages,
            "expected_cells": report.total_expected_cells,
            "actual_stream_cells": len(report.actual_stream),
            "differences": len(report.differences),
            "source_passages": report.source_passages_total,
            "math_spans": report.math_spans_total,
        },
    }
    output = fixture / f"{stem}_{args.kind}_stage_benchmark.json"
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
