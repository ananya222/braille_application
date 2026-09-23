"""Run the exact 5,000-error fixture through the packaged GUI executable."""

from __future__ import annotations

import json
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_500_page_dense_stress import _same_rect
from low_end_2core_benchmark import _set_affinity


EXE = ROOT / "dist" / "BrailleValidator" / "BrailleValidator.exe"
MASTER = ROOT / "stress_test" / "large_documents" / "500_page_5000_errors_master.docx"
BRAILLE = ROOT / "stress_test" / "large_documents" / "500_page_5000_errors_corrupted.pdf"
MANIFEST = ROOT / "stress_test" / "large_documents" / "500_page_5000_errors_manifest_PREVALIDATION.json"
OUT = ROOT / "reports" / "5000_packaged_smoke"
RESULT = OUT / "result.json"


class _MemoryCounters(ctypes.Structure):
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


_KERNEL32 = ctypes.WinDLL("kernel32", use_last_error=True)
_PSAPI = ctypes.WinDLL("psapi", use_last_error=True)
_KERNEL32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
_KERNEL32.OpenProcess.restype = wintypes.HANDLE
_KERNEL32.CloseHandle.argtypes = [wintypes.HANDLE]
_KERNEL32.CloseHandle.restype = wintypes.BOOL
_PSAPI.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(_MemoryCounters), wintypes.DWORD]
_PSAPI.GetProcessMemoryInfo.restype = wintypes.BOOL


def _memory_snapshot(pid: int) -> tuple[int, int]:
    handle = _KERNEL32.OpenProcess(0x0400 | 0x0010, False, pid)
    if not handle:
        return 0, 0
    try:
        counters = _MemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        if not _PSAPI.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
            return 0, 0
        return int(counters.WorkingSetSize), int(counters.PeakWorkingSetSize)
    finally:
        _KERNEL32.CloseHandle(handle)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    local_app_data = OUT / "localappdata"
    local_app_data.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update({"QT_QPA_PLATFORM": "offscreen", "LOCALAPPDATA": str(local_app_data)})
    command = [
        str(EXE), "--packaging-smoke",
        "--master", str(MASTER),
        "--braille", str(BRAILLE),
        "--result", str(RESULT),
    ]
    started = time.perf_counter()
    process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    _set_affinity(process.pid)
    samples: list[int] = []
    sampler_stop = threading.Event()
    def sample_memory() -> None:
        while not sampler_stop.wait(0.1):
            current, reported_peak = _memory_snapshot(process.pid)
            samples.append(max(current, reported_peak))
    sampler = threading.Thread(target=sample_memory, daemon=True)
    sampler.start()
    stdout, stderr = process.communicate(timeout=300)
    sampler_stop.set()
    sampler.join()
    wall = time.perf_counter() - started
    if not RESULT.exists():
        raise AssertionError({"returncode": process.returncode, "stdout": stdout, "stderr": stderr})

    smoke = json.loads(RESULT.read_text(encoding="utf-8"))
    if process.returncode != 0 or smoke.get("error") or smoke.get("annotation_error"):
        raise AssertionError({"returncode": process.returncode, "smoke": smoke, "stderr": stderr})
    if smoke.get("statistics", {}).get("errors") != 5000 or smoke.get("issue_count") != 5000:
        raise AssertionError({"smoke": smoke})

    from pypdf import PdfReader
    import pdfplumber

    annotated = Path(smoke["annotated_pdf"])
    report = Path(smoke["report"])
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    targets = manifest["mutations"]
    if not annotated.exists() or not report.exists():
        raise AssertionError({"annotated": str(annotated), "report": str(report)})
    with pdfplumber.open(annotated) as pdf:
        blue = []
        for page_no, page in enumerate(pdf.pages, 1):
            for rect in page.rects:
                color = rect.get("stroking_color")
                if isinstance(color, (list, tuple)) and len(color) == 3 and all(abs(a - b) < 0.01 for a, b in zip(color, (0.12, 0.48, 1))):
                    blue.append((page_no, {key: float(rect[key]) for key in ("x0", "top", "x1", "bottom")}))
    exact = 0
    for target in targets:
        if sum(page == target["physical_page"] and _same_rect(rect, target["physical_rectangle"]) for page, rect in blue) == 1:
            exact += 1
    report_payload = json.loads(report.read_text(encoding="utf-8"))
    result = {
        "status": "PASS" if len(PdfReader(str(annotated)).pages) == 500 and len(blue) == 5000 and exact == 5000 and report_payload["summary"]["confirmed_errors"] == 5000 and len(report_payload["issues"]) == 5000 else "FAIL",
        "executable": str(EXE),
        "affinity_mask": "0x3",
        "wall_seconds": wall,
        "peak_working_set_bytes": max(samples, default=0),
        "returncode": process.returncode,
        "statistics": smoke.get("statistics"),
        "issue_count": smoke.get("issue_count"),
        "annotated_pdf": str(annotated),
        "annotated_pages": len(PdfReader(str(annotated)).pages),
        "blue_boxes": len(blue),
        "exact_boxes": exact,
        "report": str(report),
        "report_findings": len(report_payload["issues"]),
        "stdout_tail": stdout[-2000:],
        "stderr_tail": stderr[-2000:],
    }
    (OUT / "summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
