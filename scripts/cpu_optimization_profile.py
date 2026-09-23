"""CPU baseline for the optimized validator; this script does not alter production code."""

from __future__ import annotations

import cProfile
import io
import json
import os
from pathlib import Path
import pstats
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from large_document_profile import memory_bytes
from braille_app.doc_extractor import DocumentExtractor
from braille_app.input_reader import read_braille_pdf_with_provenance
from braille_app.translation.expected_document import generate_expected_braille
from braille_app.translation import liblouis_translator
from braille_app.validation import validator as validator_module
from braille_app.validation.api import adapt_validation_report, validate_document
from braille_app.validation.pdf_annotation_adapter import (
    build_provenance_alignment,
    validation_errors_to_legacy_cell_issues,
)
from braille_app.validation.validator import BrailleValidator
from braille_app.visual_annotations import export_annotated_pdf, visual_issues_from_cell_issues


OUT = ROOT / "reports" / "cpu_optimization_profile_work"
REPORT = ROOT / "reports" / "cpu_optimization_baseline.md"
CORES = os.cpu_count() or 1


class CpuSampler:
    def __init__(self) -> None:
        self.samples: list[float] = []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self) -> None:
        previous_wall = time.perf_counter()
        previous_cpu = time.process_time()
        while not self._stop.wait(0.25):
            current_wall = time.perf_counter()
            current_cpu = time.process_time()
            wall_delta = current_wall - previous_wall
            if wall_delta > 0:
                self.samples.append(
                    max(0.0, (current_cpu - previous_cpu) / wall_delta / CORES * 100.0)
                )
            previous_wall, previous_cpu = current_wall, current_cpu

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> tuple[float, float]:
        self._stop.set()
        self._thread.join()
        return (
            sum(self.samples) / len(self.samples) if self.samples else 0.0,
            max(self.samples) if self.samples else 0.0,
        )


def profiled_stage(name: str, function):
    sampler = CpuSampler()
    before_rss, _ = memory_bytes()
    before_cpu = time.process_time()
    before_wall = time.perf_counter()
    profile = cProfile.Profile()
    sampler.start()
    profile.enable()
    try:
        value = function()
    finally:
        profile.disable()
    wall = time.perf_counter() - before_wall
    cpu = time.process_time() - before_cpu
    average_cpu, peak_cpu = sampler.stop()
    after_rss, peak_rss = memory_bytes()
    stream = io.StringIO()
    pstats.Stats(profile, stream=stream).sort_stats("cumulative").print_stats(30)
    stats = {
        "seconds": wall,
        "cpu_seconds": cpu,
        "average_cpu_percent_all_cores": average_cpu,
        "peak_cpu_percent_all_cores": peak_cpu,
        "rss_delta_bytes": after_rss - before_rss,
        "peak_working_set_bytes": peak_rss,
        "profile_text": stream.getvalue(),
    }
    (OUT / f"{name}_cprofile.txt").write_text(stats["profile_text"], encoding="utf-8")
    return value, stats


def wrap_translation_calls():
    counts = {"prose_calls": 0, "math_calls": 0, "prose_cpu_seconds": 0.0, "math_cpu_seconds": 0.0}
    original_prose = liblouis_translator.LiblouisTranslator.translate_prose
    original_math = liblouis_translator.LiblouisTranslator.translate_math_ascii

    def prose(self, text):
        started = time.process_time()
        try:
            return original_prose(self, text)
        finally:
            counts["prose_calls"] += 1
            counts["prose_cpu_seconds"] += time.process_time() - started

    def math(self, text):
        started = time.process_time()
        try:
            return original_math(self, text)
        finally:
            counts["math_calls"] += 1
            counts["math_cpu_seconds"] += time.process_time() - started

    liblouis_translator.LiblouisTranslator.translate_prose = prose
    liblouis_translator.LiblouisTranslator.translate_math_ascii = math
    return counts, original_prose, original_math


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    source = ROOT / "reports" / "large_document_fixtures" / "repeat_0100_source_pages_source.pdf"
    actual_path = ROOT / "reports" / "large_document_fixtures" / "repeat_0100_source_pages_clean_braille.pdf"
    stages = {}
    master, stages["master_extraction"] = profiled_stage(
        "master_extraction", lambda: DocumentExtractor().extract(str(source))
    )
    actual, stages["braille_pdf_extraction"] = profiled_stage(
        "braille_pdf_extraction",
        lambda: read_braille_pdf_with_provenance(str(actual_path), profile="math"),
    )
    counts, original_prose, original_math = wrap_translation_calls()
    try:
        expected, stages["expected_generation_and_rules"] = profiled_stage(
            "expected_generation_and_rules", lambda: generate_expected_braille(master)
        )
    finally:
        liblouis_translator.LiblouisTranslator.translate_prose = original_prose
        liblouis_translator.LiblouisTranslator.translate_math_ascii = original_math

    original_generator = validator_module.generate_expected_braille
    validator_module.generate_expected_braille = lambda *_args, **_kwargs: expected
    try:
        raw_report, stages["comparison_alignment"] = profiled_stage(
            "comparison_alignment", lambda: BrailleValidator().validate(master, actual.content)
        )
    finally:
        validator_module.generate_expected_braille = original_generator

    adapted, stages["finding_generation"] = profiled_stage(
        "finding_generation", lambda: adapt_validation_report(raw_report)
    )
    provenance, stages["provenance_mapping"] = profiled_stage(
        "provenance_mapping", lambda: build_provenance_alignment(actual)
    )
    legacy = validation_errors_to_legacy_cell_issues(adapted, provenance)
    visual = visual_issues_from_cell_issues(legacy)
    annotated = OUT / "cpu_baseline_annotated.pdf"
    _, stages["annotated_pdf_generation"] = profiled_stage(
        "annotated_pdf_generation",
        lambda: export_annotated_pdf(str(actual_path), str(annotated), visual),
    )
    payload = {
        "fixture": {"source": str(source), "actual": str(actual_path)},
        "logical_cores": CORES,
        "inputs": {
            "source_pages": len(master["pages"]),
            "source_blocks": sum(len(page["blocks"]) for page in master["pages"]),
            "source_chars": sum(len(block.get("text", "")) for page in master["pages"] for block in page["blocks"]),
            "actual_pdf_pages": len(actual.content.split("\f")),
            "actual_stream_chars": len(actual.content),
            "expected_cells": raw_report.total_expected_cells,
        },
        "translation": counts,
        "stages": stages,
        "statistics": adapted.statistics,
    }
    (OUT / "baseline.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    REPORT.write_text(render_report(payload), encoding="utf-8")
    print(json.dumps(payload, indent=2))


def render_report(payload: dict) -> str:
    lines = [
        "# CPU optimization baseline",
        "",
        "This is a second-pass CPU profile of the post-large-document-optimization application. It makes no production changes. The profiled fixture is the deterministic 100-source-page repeated real-document pair.",
        "",
        f"Logical CPU count: {payload['logical_cores']}. CPU percentages are process CPU normalized across all logical cores; peak is the highest 250 ms sample. cProfile timings include profiler overhead and are used for attribution, not headline wall-clock claims.",
        "",
        "## Stage measurements",
        "",
        "| Stage | Wall time | Process CPU | Avg CPU | Peak CPU | Peak RAM |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, stage in payload["stages"].items():
        lines.append(
            f"| {name} | {stage['seconds']:.3f}s | {stage['cpu_seconds']:.3f}s | {stage['average_cpu_percent_all_cores']:.1f}% | {stage['peak_cpu_percent_all_cores']:.1f}% | {stage['peak_working_set_bytes'] / 1024 / 1024:.1f} MiB |"
        )
    translation = payload["translation"]
    lines += [
        "",
        "## Liblouis translation attribution",
        "",
        f"- prose calls: {translation['prose_calls']}",
        f"- math calls: {translation['math_calls']}",
        f"- prose process CPU: {translation['prose_cpu_seconds']:.3f}s",
        f"- math process CPU: {translation['math_cpu_seconds']:.3f}s",
        "",
        "## Profiling evidence",
        "",
        "Per-stage cProfile top-30 reports are in `reports/cpu_optimization_profile_work/`. These are the evidence source for any follow-up optimization; no optimization is justified by a function name alone without a correctness rerun.",
        "",
        "The previous pass already added exact/nonblank-equivalent alignment fast paths and per-page PDF cache release. This baseline is intended to identify remaining CPU work after those changes.",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
