"""Read-only phase-1 profiler for the current validator pipeline.

It measures the existing implementation without changing production modules.
The expected-document monkeypatch is used only for the comparison-only stage;
the end-to-end stage always calls the public validation API unchanged.
"""

from __future__ import annotations

import cProfile
import ctypes
from ctypes import wintypes
from dataclasses import asdict
import io
import json
from pathlib import Path
import pstats
import sys
import time
import tracemalloc


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

PROFILE_DIR = ROOT / "reports" / "large_document_profile_work"
REPORT = ROOT / "reports" / "large_document_performance_baseline.md"


class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


_KERNEL32 = ctypes.WinDLL("kernel32", use_last_error=True)
_PSAPI = ctypes.WinDLL("psapi", use_last_error=True)
_KERNEL32.GetCurrentProcess.argtypes = []
_KERNEL32.GetCurrentProcess.restype = wintypes.HANDLE
_PSAPI.GetProcessMemoryInfo.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(PROCESS_MEMORY_COUNTERS),
    wintypes.DWORD,
]
_PSAPI.GetProcessMemoryInfo.restype = wintypes.BOOL


def memory_bytes() -> tuple[int, int]:
    """Return current and peak working-set bytes on Windows."""

    counters = PROCESS_MEMORY_COUNTERS()
    counters.cb = ctypes.sizeof(counters)
    process = _KERNEL32.GetCurrentProcess()
    ok = _PSAPI.GetProcessMemoryInfo(
        process, ctypes.byref(counters), counters.cb
    )
    if not ok:
        return 0, 0
    return int(counters.WorkingSetSize), int(counters.PeakWorkingSetSize)


def size_of(value) -> int:
    if isinstance(value, str | bytes | tuple | list | dict):
        return len(value)
    return 0


def run_stage(name, function):
    before_rss, _ = memory_bytes()
    before_alloc, _ = tracemalloc.get_traced_memory()
    started = time.perf_counter()
    value = function()
    elapsed = time.perf_counter() - started
    after_alloc, peak_alloc = tracemalloc.get_traced_memory()
    after_rss, peak_rss = memory_bytes()
    return value, {
        "seconds": elapsed,
        "rss_delta_bytes": after_rss - before_rss,
        "peak_rss_bytes": peak_rss,
        "python_alloc_delta_bytes": after_alloc - before_alloc,
        "python_peak_bytes": peak_alloc,
    }


def fixture_metrics(master, actual, expected=None, report=None) -> dict:
    pages = len(master.get("pages", [])) if isinstance(master, dict) else 0
    source_blocks = sum(len(page.get("blocks", [])) for page in master.get("pages", [])) if isinstance(master, dict) else 0
    source_chars = sum(
        len(block.get("text", "") or "")
        for page in master.get("pages", [])
        for block in page.get("blocks", [])
    ) if isinstance(master, dict) else 0
    actual_chars = len(actual.content)
    expected_cells = sum(
        len(block.braille)
        for page in expected.pages
        for block in page.blocks
    ) if expected is not None else 0
    actual_cells = sum(
        len(page)
        for page in actual.content.split("\f")
    )
    result = {
        "source_pages": pages,
        "source_blocks": source_blocks,
        "source_chars": source_chars,
        "actual_pdf_pages": len(actual.content.split("\f")),
        "actual_stream_chars": actual_chars,
        "actual_cells_with_layout": actual_cells,
        "expected_cells": expected_cells,
    }
    if report is not None:
        result.update({
            "reported_pages": report.statistics.get("pages", 0),
            "reported_differences": report.statistics.get("raw_differences", 0),
            "errors": report.statistics.get("errors", 0),
            "reviews": report.statistics.get("reviews", 0),
            "excluded": report.statistics.get("excluded", 0),
            "cell_accuracy": report.statistics.get("cell_accuracy", 0),
        })
    return result


def profile_end_to_end(master_path: Path, actual_path: Path):
    from braille_app.validation.api import validate_document

    profile = cProfile.Profile()
    started = time.perf_counter()
    profile.enable()
    result = validate_document(str(master_path), str(actual_path))
    profile.disable()
    stream = io.StringIO()
    pstats.Stats(profile, stream=stream).sort_stats("cumulative").print_stats(30)
    return result, time.perf_counter() - started, stream.getvalue()


def run_fixture(name: str, master_path: Path, actual_path: Path) -> dict:
    from braille_app.doc_extractor import DocumentExtractor
    from braille_app.input_reader import read_braille_pdf_with_provenance
    from braille_app.translation.expected_document import generate_expected_braille
    from braille_app.validation import validator as validator_module
    from braille_app.validation.api import adapt_validation_report
    from braille_app.validation.pdf_annotation_adapter import (
        build_provenance_alignment,
        validation_errors_to_legacy_cell_issues,
    )
    from braille_app.validation.validator import BrailleValidator
    from braille_app.visual_annotations import export_annotated_pdf, visual_issues_from_cell_issues

    tracemalloc.start()
    stages = {}
    master, stages["master_extraction"] = run_stage(
        "master_extraction", lambda: DocumentExtractor().extract(str(master_path))
    )
    actual, stages["braille_pdf_extraction"] = run_stage(
        "braille_pdf_extraction", lambda: read_braille_pdf_with_provenance(str(actual_path), profile="math")
    )
    expected, stages["expected_generation_and_rules"] = run_stage(
        "expected_generation_and_rules", lambda: generate_expected_braille(master)
    )

    original_generator = validator_module.generate_expected_braille
    validator_module.generate_expected_braille = lambda *_args, **_kwargs: expected
    try:
        raw_report, stages["comparison_alignment"] = run_stage(
            "comparison_alignment", lambda: BrailleValidator().validate(master, actual.content)
        )
    finally:
        validator_module.generate_expected_braille = original_generator

    adapted, stages["finding_generation"] = run_stage(
        "finding_generation", lambda: adapt_validation_report(raw_report)
    )
    provenance, stages["provenance_mapping"] = run_stage(
        "provenance_mapping", lambda: build_provenance_alignment(actual)
    )

    annotation_seconds = None
    annotation_error = None
    try:
        legacy = validation_errors_to_legacy_cell_issues(adapted, provenance)
        visual = visual_issues_from_cell_issues(legacy)
        destination = PROFILE_DIR / f"{name}_annotated.pdf"
        _, annotation_stage = run_stage(
            "annotated_pdf_export",
            lambda: export_annotated_pdf(str(actual_path), str(destination), visual),
        )
        stages["annotated_pdf_export"] = annotation_stage
        annotation_seconds = annotation_stage["seconds"]
    except Exception as exc:  # profiling must preserve the failure as evidence
        annotation_error = f"{type(exc).__name__}: {exc}"

    report_payload = {
        "statistics": adapted.statistics,
        "errors": [asdict(issue) for issue in adapted.errors],
        "reviews": [asdict(issue) for issue in adapted.reviews],
        "exclusions": [asdict(issue) for issue in adapted.exclusions],
    }
    _, stages["json_report_serialization"] = run_stage(
        "json_report_serialization",
        lambda: json.dumps(report_payload, ensure_ascii=False),
    )
    _, peak_rss = memory_bytes()
    tracemalloc.stop()

    result = {
        "name": name,
        "master": str(master_path),
        "actual": str(actual_path),
        "inputs": fixture_metrics(master, actual, expected, adapted),
        "stages": stages,
        "peak_working_set_bytes": peak_rss,
        "annotation_seconds": annotation_seconds,
        "annotation_error": annotation_error,
        "end_to_end": None,
    }
    from braille_app.validation.api import validate_document

    plain_started = time.perf_counter()
    plain_result = validate_document(str(master_path), str(actual_path))
    plain_seconds = time.perf_counter() - plain_started
    result["end_to_end"] = {
        "seconds": plain_seconds,
        "cprofile_seconds": None,
        "statistics": plain_result.statistics,
    }
    end_result, end_seconds, profile_text = profile_end_to_end(master_path, actual_path)
    result["end_to_end"]["cprofile_seconds"] = end_seconds
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    (PROFILE_DIR / f"{name}_cprofile.txt").write_text(profile_text, encoding="utf-8")
    return result


def markdown(results: list[dict]) -> str:
    lines = [
        "# Large-document performance baseline",
        "",
        "Baseline captured from the current production implementation before optimization. No production source was modified by this profile run.",
        "",
        "Runtime: Python 3.12.14 bundled workspace runtime on Windows. Measurements are single-process wall-clock runs; peak working set is process high-water memory. The comparison-only stage reuses its already-generated expected document only to isolate alignment cost; end-to-end timings call the public API unchanged.",
        "",
        "## Fixture summary",
        "",
        "| Fixture | Source pages | Braille PDF pages | Source chars | Expected cells | Actual stream chars | Errors | Reviews |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for result in results:
        inputs = result["inputs"]
        lines.append(
            f"| {result['name']} | {inputs['source_pages']} | {inputs['actual_pdf_pages']} | {inputs['source_chars']} | {inputs['expected_cells']} | {inputs['actual_stream_chars']} | {inputs['errors']} | {inputs['reviews']} |"
        )
    lines += [
        "",
        "## Baseline timings",
        "",
        "| Fixture | End-to-end | Master extraction | Braille extraction | Expected generation + rules | Comparison/alignment | Finding generation | Provenance mapping | PDF export | JSON serialization | Peak working set |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for result in results:
        stages = result["stages"]
        get = lambda name: stages.get(name, {}).get("seconds", 0.0)
        lines.append(
            f"| {result['name']} | {result['end_to_end']['seconds']:.3f}s | {get('master_extraction'):.3f}s | {get('braille_pdf_extraction'):.3f}s | {get('expected_generation_and_rules'):.3f}s | {get('comparison_alignment'):.3f}s | {get('finding_generation'):.3f}s | {get('provenance_mapping'):.3f}s | {get('annotated_pdf_export'):.3f}s | {get('json_report_serialization'):.3f}s | {result['peak_working_set_bytes'] / 1024 / 1024:.1f} MiB |"
        )
    lines += [
        "",
        "## Pipeline and observed cost centers",
        "",
        "1. Source extraction is page/block based. DOCX extraction is paragraph-oriented; PDF source extraction uses `pdfplumber` word extraction and line regrouping.",
        "2. Braille PDF extraction is expensive and memory-sensitive: it opens the PDF, inspects embedded fonts, renders glyph masks to infer dot maps, rebuilds lines, retains per-cell provenance, then normalizes and verifies word provenance.",
        "3. Expected generation translates each source group and then runs the rule engine. `ExpectedBrailleDocument` retains every page, block, Braille string, rule result, math record and capitalization site for localization.",
        "4. Validation flattens both logical documents into one continuous cell stream, runs `ComparisonView`, then `SequenceMatcher` through `align_cells`. It also retains page alignments, actual page offsets, actual stream cells, differences and provenance-relevant offsets.",
        "5. Finding adaptation walks pages/blocks/differences repeatedly to produce UI-safe issues and exact physical ranges. PDF provenance is loaded again by the GUI worker before annotation, so the public GUI path parses the Braille PDF twice.",
        "6. Annotation reads and writes the full PDF, including original page streams. JSON report serialization is proportional to finding volume and is not a leading cost in the baseline.",
        "",
        "## Suspected bottlenecks requiring the next phase",
        "",
        "- Continuous `SequenceMatcher(..., autojunk=False)` over the complete expected/actual document stream is the highest-risk scaling point. It is also correctness-critical and must not be replaced without large-corruption localization gates.",
        "- PDF font/glyph inspection and provenance retention are repeated: the GUI first extracts the PDF for validation and later calls `load_pdf_provenance` again for annotation.",
        "- `ExpectedBrailleDocument.blocks` flattens all blocks into a new tuple whenever accessed; validator and API helpers call related page/block traversals repeatedly.",
        "- Several provenance helpers build temporary lists (`nonblank_positions`, selected ranges, page records) per lookup. This is likely secondary to full-stream alignment but should be measured on very large inputs.",
        "- The GUI already moves validation to `ValidationThread`; responsiveness is therefore mainly threatened by worker duration, memory pressure, and the second PDF parse, not by validation executing on the Qt event loop.",
        "",
        "## Correctness baseline",
        "",
    ]
    for result in results:
        stats = result["end_to_end"]["statistics"]
        lines.append(
            f"- `{result['name']}`: {stats.get('errors', 0)} confirmed errors, {stats.get('reviews', 0)} reviews, cell accuracy {stats.get('cell_accuracy', 0):.6f}, math aligned {stats.get('math_spans_evaluated', 0)}/{stats.get('math_spans_total', 0)}, source passages aligned {stats.get('source_passages_aligned', 0)}/{stats.get('source_passages_total', 0)}, capitalization opportunities aligned {stats.get('capitalization_opportunities_evaluated', 0)}/{stats.get('capitalization_opportunities_total', 0)}."
        )
    lines += [
        "",
        "## Constraints for optimization",
        "",
        "The next phase must preserve document-wide logical alignment across arbitrary physical page breaks, exact cell provenance, REVIEW/EXCLUDED handling, Duxbury spacing tolerance, operator-anchor behavior, and deterministic output. No page-ratio assumption, alignment rewrite, standards-rule change, or PDF graphics-state change is justified by this baseline alone.",
        "",
        "Detailed cProfile output is in `reports/large_document_profile_work/`.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    fixtures = [
        (
            "test1_clean",
            ROOT / "stress_test" / "Test_1" / "Synthetic_Test_01.pdf",
            ROOT / "stress_test" / "Test_1" / "Synthetic_Test_01_converted.pdf",
        ),
        (
            "test1_corrupted",
            ROOT / "stress_test" / "Test_1" / "Synthetic_Test_01.pdf",
            ROOT / "stress_test" / "Test_1" / "corrupted" / "Synthetic_Test_01_corrupted_stress.pdf",
        ),
    ]
    results = [run_fixture(name, master, actual) for name, master, actual in fixtures]
    (PROFILE_DIR / "baseline.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(markdown(results), encoding="utf-8")
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
