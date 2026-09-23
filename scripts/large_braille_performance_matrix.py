"""Run isolated clean/corrupted performance cases for the CPU audit."""

from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "large_braille_performance_work"
FIXTURES = ROOT / "stress_test" / "large_documents"
SIZES = (50, 100, 250, 500)
CORES = os.cpu_count() or 1

sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from large_document_profile import memory_bytes


class CpuSampler:
    def __init__(self) -> None:
        self.samples: list[float] = []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self) -> None:
        previous_wall = time.perf_counter()
        previous_cpu = time.process_time()
        while not self._stop.wait(0.25):
            wall = time.perf_counter()
            cpu = time.process_time()
            elapsed = wall - previous_wall
            if elapsed:
                self.samples.append(max(0.0, (cpu - previous_cpu) / elapsed / CORES * 100.0))
            previous_wall, previous_cpu = wall, cpu

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> tuple[float, float]:
        self._stop.set()
        self._thread.join()
        if not self.samples:
            return 0.0, 0.0
        return sum(self.samples) / len(self.samples), max(self.samples)


def _fixture_paths(size: int, mode: str) -> tuple[Path, Path]:
    stem = f"performance_braille_{size:03d}_pages"
    master = FIXTURES / f"performance_master_{size:03d}_pages.docx"
    pdf = FIXTURES / f"{stem}{'_corrupted' if mode == 'corrupted' else ''}.pdf"
    return master, pdf


def _mutation_target(manifest: dict, page: int, line: int, cell: int, provenance, page_text: str) -> object | None:
    page_record = provenance.pages[page - 1]
    target = next(item for item in manifest["mutations"] if item["fixture_page"] == page and item["line_index_zero_based"] == line)
    original = target["original_braille"]
    lines = page_text.replace("\r", "").split("\n")
    nonblank_before = sum(
        sum(ord(char) - 0x2800 != 0 for char in row if 0x2800 <= ord(char) < 0x2900)
        for row in lines[:line]
    )
    nonblank_before += sum(
        ord(char) - 0x2800 != 0
        for char in original[:cell]
        if 0x2800 <= ord(char) < 0x2900
    )
    return page_record.provenance_cells[nonblank_before]


def run_one(size: int, mode: str) -> dict:
    from braille_app.validation.api import validate_document
    from braille_app.validation.pdf_annotation_adapter import (
        build_provenance_alignment,
        validation_errors_to_legacy_cell_issues,
    )
    from braille_app.visual_annotations import export_annotated_pdf, visual_issues_from_cell_issues

    master_path, pdf_path = _fixture_paths(size, mode)
    manifest_path = FIXTURES / f"performance_braille_{size:03d}_pages_corruption_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    before_rss, _ = memory_bytes()
    before_peak = memory_bytes()[1]
    sampler = CpuSampler()
    started_wall = time.perf_counter()
    started_cpu = time.process_time()
    sampler.start()
    try:
        result = validate_document(master_path, pdf_path, retain_pdf_provenance=True)
    finally:
        validation_wall = time.perf_counter() - started_wall
        validation_cpu = time.process_time() - started_cpu
        average_cpu, peak_cpu = sampler.stop()
    after_rss, peak_rss = memory_bytes()

    if result.pdf_input is None:
        raise AssertionError("retained PDF provenance was not returned")
    mapping_started = time.perf_counter()
    provenance = build_provenance_alignment(result.pdf_input)
    legacy = validation_errors_to_legacy_cell_issues(result, provenance)
    visual = visual_issues_from_cell_issues(legacy)
    annotation_wall = 0.0
    annotation_path = None
    if mode == "corrupted":
        annotation_path = OUT / f"performance_braille_{size:03d}_pages_corrupted_annotated.pdf"
        annotation_started = time.perf_counter()
        export_annotated_pdf(str(pdf_path), str(annotation_path), visual)
        annotation_wall = time.perf_counter() - annotation_started
    mapping_wall = time.perf_counter() - mapping_started

    localization_matches = 0
    localization_misses = []
    if mode == "corrupted":
        for target in manifest["mutations"]:
            expected = _mutation_target(
                manifest,
                target["fixture_page"],
                target["line_index_zero_based"],
                target["cell_index_zero_based"] + (1 if target["family"] == "EQUALS" else 0),
                provenance,
                result.pdf_input.content.split("\f")[target["fixture_page"] - 1],
            )
            expected_matches = [
                issue for issue in legacy
                if any(
                    cell["page"] == expected.page
                    and abs(cell["x0"] - expected.x0) < 0.01
                    and abs(cell["top"] - expected.top) < 0.01
                    for cell in issue["provenance_cells"]
                )
            ]
            if expected_matches:
                localization_matches += 1
            else:
                localization_misses.append(target)

    expected_cells = result.statistics.get("expected_cells", provenance.validator_cell_count)
    return {
        "size_pages": size,
        "mode": mode,
        "master": str(master_path),
        "pdf": str(pdf_path),
        "validation_wall_seconds": validation_wall,
        "validation_cpu_seconds": validation_cpu,
        "total_wall_seconds": time.perf_counter() - started_wall,
        "mapping_wall_seconds": mapping_wall,
        "annotation_wall_seconds": annotation_wall,
        "average_cpu_percent_all_cores": average_cpu,
        "peak_cpu_percent_all_cores": peak_cpu,
        "peak_working_set_bytes": peak_rss,
        "peak_working_set_delta_from_start_bytes": max(0, peak_rss - before_rss),
        "end_working_set_bytes": after_rss,
        "expected_cells": expected_cells,
        "cells_per_validation_second": expected_cells / validation_wall if validation_wall else 0,
        "errors": len(result.errors),
        "reviews": len(result.reviews),
        "statistics": result.statistics,
        "provenance_unmatched_cells": provenance.unmatched_cells,
        "provenance_unexplained_offsets": provenance.unexplained_offsets,
        "visual_issue_count": len(visual),
        "localization_matches": localization_matches,
        "localization_misses": localization_misses,
        "annotation": str(annotation_path) if annotation_path else None,
        "error_summary": [
            {
                "issue_id": issue.issue_id,
                "category": issue.category,
                "rule_id": issue.rule_id,
                "actual_page_number": issue.actual_page_number,
                "actual_cell_start": issue.actual_cell_start,
                "actual_cell_end": issue.actual_cell_end,
                "source_text": issue.source_text,
            }
            for issue in result.errors
        ],
    }


def _single(size: int, mode: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("RESULT_JSON=" + json.dumps(run_one(size, mode), ensure_ascii=True))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if len(sys.argv) == 4 and sys.argv[1] == "--single":
        _single(int(sys.argv[2]), sys.argv[3])
        return

    cases = []
    for size in SIZES:
        for mode in ("clean", "corrupted"):
            completed = subprocess.run(
                [sys.executable, __file__, "--single", str(size), mode],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            if completed.returncode:
                raise RuntimeError(
                    f"{size}/{mode} failed with {completed.returncode}:\n{completed.stdout}\n{completed.stderr}"
                )
            line = next(line for line in completed.stdout.splitlines() if line.startswith("RESULT_JSON="))
            cases.append(json.loads(line.removeprefix("RESULT_JSON=")))
            print(f"completed {size} pages {mode}")
    payload = {"logical_cores": CORES, "cases": cases}
    (OUT / "matrix.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
