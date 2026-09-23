"""Two-core/8-GB-target benchmark for the current validator."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "reports" / "low_end_2core_8gb_fixtures"
OUT = ROOT / "reports" / "low_end_2core_8gb_work"
SIZES = (50, 100, 250, 500)
AFFINITY_MASK = 0x3
AFFINITY_CORES = 2

sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))


class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
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
        ("PrivateUsage", ctypes.c_size_t),
    ]


class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", wintypes.DWORD),
        ("dwMemoryLoad", wintypes.DWORD),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


_KERNEL32 = ctypes.WinDLL("kernel32", use_last_error=True)
_PSAPI = ctypes.WinDLL("psapi", use_last_error=True)
_KERNEL32.GetCurrentProcess.restype = wintypes.HANDLE
_KERNEL32.GlobalMemoryStatusEx.argtypes = [ctypes.POINTER(MEMORYSTATUSEX)]
_KERNEL32.GlobalMemoryStatusEx.restype = wintypes.BOOL
_PSAPI.GetProcessMemoryInfo.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(PROCESS_MEMORY_COUNTERS_EX),
    wintypes.DWORD,
]
_PSAPI.GetProcessMemoryInfo.restype = wintypes.BOOL
_KERNEL32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
_KERNEL32.OpenProcess.restype = wintypes.HANDLE
_KERNEL32.SetProcessAffinityMask.argtypes = [wintypes.HANDLE, ctypes.c_size_t]
_KERNEL32.SetProcessAffinityMask.restype = wintypes.BOOL
_KERNEL32.CloseHandle.argtypes = [wintypes.HANDLE]
_KERNEL32.CloseHandle.restype = wintypes.BOOL


def memory_snapshot() -> dict:
    counters = PROCESS_MEMORY_COUNTERS_EX()
    counters.cb = ctypes.sizeof(counters)
    ok = _PSAPI.GetProcessMemoryInfo(
        _KERNEL32.GetCurrentProcess(), ctypes.byref(counters), counters.cb
    )
    if not ok:
        return {"working_set_bytes": 0, "peak_working_set_bytes": 0, "private_bytes": 0, "page_faults": 0}
    return {
        "working_set_bytes": int(counters.WorkingSetSize),
        "peak_working_set_bytes": int(counters.PeakWorkingSetSize),
        "private_bytes": int(counters.PrivateUsage),
        "page_faults": int(counters.PageFaultCount),
    }


def system_memory_snapshot() -> dict:
    status = MEMORYSTATUSEX()
    status.dwLength = ctypes.sizeof(status)
    if not _KERNEL32.GlobalMemoryStatusEx(ctypes.byref(status)):
        return {"total_bytes": 0, "available_bytes": 0, "available_pagefile_bytes": 0, "memory_load_percent": 0}
    return {
        "total_bytes": int(status.ullTotalPhys),
        "available_bytes": int(status.ullAvailPhys),
        "available_pagefile_bytes": int(status.ullAvailPageFile),
        "memory_load_percent": int(status.dwMemoryLoad),
    }


class Sampler:
    def __init__(self) -> None:
        self.samples: list[float] = []
        self.available: list[int] = []
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
                self.samples.append(max(0.0, (cpu - previous_cpu) / elapsed / AFFINITY_CORES * 100.0))
            self.available.append(system_memory_snapshot()["available_bytes"])
            previous_wall, previous_cpu = wall, cpu

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> tuple[float, float, int | None]:
        self._stop.set()
        self._thread.join()
        average = sum(self.samples) / len(self.samples) if self.samples else 0.0
        peak = max(self.samples) if self.samples else 0.0
        minimum_available = min(self.available) if self.available else None
        return average, peak, minimum_available


def _fixture_paths(size: int, mode: str) -> tuple[Path, Path, Path]:
    stem = f"low_end_{size:03d}_pages"
    return (
        FIXTURES / f"{stem}_master.docx",
        FIXTURES / f"{stem}_{mode}.pdf",
        FIXTURES / f"{stem}_manifest.json",
    )


def run_single(size: int, mode: str) -> dict:
    from braille_app.validation.api import validate_document
    from braille_app.validation.pdf_annotation_adapter import (
        build_provenance_alignment,
        validation_errors_to_legacy_cell_issues,
        validation_to_diagnostic_cell_issues,
    )
    from braille_app.visual_annotations import (
        export_annotated_pdf,
        export_diagnostic_pdf,
        visual_issues_from_cell_issues,
    )
    from large_braille_performance_matrix import _mutation_target

    master_path, pdf_path, manifest_path = _fixture_paths(size, mode)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    case_out = OUT / f"{size:03d}_{mode}"
    case_out.mkdir(parents=True, exist_ok=True)
    before = memory_snapshot()
    system_before = system_memory_snapshot()
    sampler = Sampler()
    total_started = time.perf_counter()
    total_cpu_started = time.process_time()
    sampler.start()
    validation_started = time.perf_counter()
    result = validate_document(master_path, pdf_path, retain_pdf_provenance=True)
    validation_wall = time.perf_counter() - validation_started

    mapping_started = time.perf_counter()
    if result.pdf_input is None:
        raise AssertionError("retained PDF provenance was not returned")
    alignment = build_provenance_alignment(result.pdf_input)
    legacy = validation_errors_to_legacy_cell_issues(result, alignment)
    visual = visual_issues_from_cell_issues(legacy)
    annotated_path = case_out / f"{size:03d}_{mode}_annotated.pdf"
    export_annotated_pdf(str(pdf_path), str(annotated_path), visual)
    diagnostic_records, unmapped_reviews = validation_to_diagnostic_cell_issues(result, alignment)
    diagnostic_visual = visual_issues_from_cell_issues(diagnostic_records)
    diagnostic_path = case_out / f"{size:03d}_{mode}_diagnostic.pdf"
    export_diagnostic_pdf(str(pdf_path), str(diagnostic_path), diagnostic_visual)
    export_wall = time.perf_counter() - mapping_started

    localization_matches = 0
    localization_misses = []
    if mode == "corrupted":
        for target in manifest["mutations"]:
            expected = _mutation_target(
                manifest,
                target["fixture_page"],
                target["line_index_zero_based"],
                target["cell_index_zero_based"] + (1 if target["family"] == "EQUALS" else 0),
                alignment,
                result.pdf_input.content.split("\f")[target["fixture_page"] - 1],
            )
            matched = any(
                cell["page"] == expected.page
                and abs(cell["x0"] - expected.x0) < 0.01
                and abs(cell["top"] - expected.top) < 0.01
                for issue in legacy
                for cell in issue["provenance_cells"]
            )
            if matched:
                localization_matches += 1
            else:
                localization_misses.append(target)

    total_wall = time.perf_counter() - total_started
    total_cpu = time.process_time() - total_cpu_started
    average_cpu, peak_cpu, minimum_available = sampler.stop()
    after = memory_snapshot()
    system_after = system_memory_snapshot()
    expected_cells = int(result.statistics.get("expected_cells", 0))
    pages = len(result.pdf_input.content.split("\f"))
    return {
        "pages": pages,
        "requested_pages": size,
        "braille_cells": expected_cells,
        "mode": mode,
        "master": str(master_path),
        "braille": str(pdf_path),
        "affinity_mask": hex(AFFINITY_MASK),
        "affinity_cores": AFFINITY_CORES,
        "runtime_seconds": total_wall,
        "validation_seconds": validation_wall,
        "export_seconds": export_wall,
        "cpu_seconds": total_cpu,
        "average_cpu_percent_of_two_cores": average_cpu,
        "peak_cpu_percent_of_two_cores": peak_cpu,
        "working_set_bytes_end": after["working_set_bytes"],
        "peak_working_set_bytes": after["peak_working_set_bytes"],
        "private_bytes_end": after["private_bytes"],
        "page_faults_delta": max(0, after["page_faults"] - before["page_faults"]),
        "system_total_memory_bytes": system_before["total_bytes"],
        "system_available_memory_bytes_start": system_before["available_bytes"],
        "system_available_memory_bytes_min_sampled": minimum_available,
        "system_available_memory_bytes_end": system_after["available_bytes"],
        "system_memory_load_percent_start": system_before["memory_load_percent"],
        "system_memory_load_percent_end": system_after["memory_load_percent"],
        "errors": len(result.errors),
        "reviews": len(result.reviews),
        "false_positives": len(result.errors) if mode == "clean" else None,
        "missed_injected_errors": (len(manifest["mutations"]) - localization_matches) if mode == "corrupted" else None,
        "exact_pdf_localization": localization_matches if mode == "corrupted" else alignment.unmatched_cells == 0,
        "localization_misses": localization_misses,
        "provenance_unmatched_cells": alignment.unmatched_cells,
        "provenance_unexplained_offsets": alignment.unexplained_offsets,
        "visual_issue_count": len(visual),
        "annotation_error": None,
        "statistics": result.statistics,
        "annotated_pdf": str(annotated_path),
        "diagnostic_pdf": str(diagnostic_path),
    }


def _set_affinity(pid: int) -> None:
    process = _KERNEL32.OpenProcess(0x0200 | 0x0400, False, pid)
    if not process:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        if not _KERNEL32.SetProcessAffinityMask(process, AFFINITY_MASK):
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        _KERNEL32.CloseHandle(process)


def _task_count() -> int:
    try:
        output = subprocess.check_output(["tasklist", "/fo", "csv", "/nh"], text=True, errors="replace")
        return sum(bool(line.strip()) for line in output.splitlines())
    except Exception:
        return -1


def run_matrix() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    background = {
        "logical_processors_visible": os.cpu_count(),
        "task_count_before": _task_count(),
        "system_memory_before": system_memory_snapshot(),
    }
    cases = []
    for size in SIZES:
        for mode in ("clean", "corrupted"):
            command = [sys.executable, __file__, "--single", str(size), mode]
            completed = subprocess.Popen(
                command,
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
            _set_affinity(completed.pid)
            stdout, stderr = completed.communicate()
            if completed.returncode:
                raise RuntimeError(f"{size}/{mode} failed:\n{stdout}\n{stderr}")
            line = next(line for line in stdout.splitlines() if line.startswith("RESULT_JSON="))
            cases.append(json.loads(line.removeprefix("RESULT_JSON=")))
            print(f"completed {size} pages {mode}", flush=True)
    payload = {
        "target": {"cpu_cores": 2, "ram_gb": 8, "affinity_mask": hex(AFFINITY_MASK)},
        "background": background,
        "cases": cases,
    }
    destination = ROOT / "reports" / "low_end_2core_8gb_matrix.json"
    destination.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return payload


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--single":
        print("RESULT_JSON=" + json.dumps(run_single(int(sys.argv[2]), sys.argv[3]), ensure_ascii=True))
    else:
        run_matrix()
