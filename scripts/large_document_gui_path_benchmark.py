"""Compare GUI provenance reuse with the former second-PDF-parse path."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from braille_app.validation.api import validate_document
from braille_app.validation.pdf_annotation_adapter import (
    build_provenance_alignment,
    load_pdf_provenance,
)


def timed(function):
    started = time.perf_counter()
    value = function()
    return value, time.perf_counter() - started


def main() -> None:
    pages = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    fixture = ROOT / "reports" / "large_document_fixtures"
    stem = f"repeat_{pages:04d}_source_pages"
    source = fixture / f"{stem}_source.pdf"
    actual = fixture / f"{stem}_clean_braille.pdf"

    legacy_result, legacy_validation_seconds = timed(
        lambda: validate_document(str(source), str(actual))
    )
    _, legacy_provenance_seconds = timed(
        lambda: load_pdf_provenance(str(actual), profile="math")
    )

    retained_result, retained_validation_seconds = timed(
        lambda: validate_document(
            str(source), str(actual), retain_pdf_provenance=True
        )
    )
    _, retained_mapping_seconds = timed(
        lambda: build_provenance_alignment(retained_result.pdf_input)
    )
    payload = {
        "source_pages": pages,
        "legacy_reparse": {
            "validation_seconds": legacy_validation_seconds,
            "second_provenance_parse_seconds": legacy_provenance_seconds,
            "statistics": legacy_result.statistics,
        },
        "retained_provenance": {
            "validation_seconds": retained_validation_seconds,
            "provenance_mapping_seconds": retained_mapping_seconds,
            "statistics": retained_result.statistics,
        },
    }
    output = fixture / f"{stem}_gui_path_benchmark.json"
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
