"""Benchmark the packaged 5,000-error fixture with unrestricted system use."""

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
sys.path.insert(0, str(ROOT / "scripts"))
from build_500_page_dense_stress import _same_rect

EXE = ROOT / "dist" / "BrailleValidator" / "BrailleValidator.exe"
MASTER = ROOT / "stress_test" / "large_documents" / "500_page_5000_errors_master.docx"
BRAILLE = ROOT / "stress_test" / "large_documents" / "500_page_5000_errors_corrupted.pdf"
MANIFEST = ROOT / "stress_test" / "large_documents" / "500_page_5000_errors_manifest_PREVALIDATION.json"
OUT = ROOT / "reports" / "5000_packaged_unrestricted"
LOCAL_APP_DATA = OUT / "localappdata"
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
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
        ("PrivateUsage", ctypes.c_size_t),
    ]


class _FileTime(ctypes.Structure):
    _fields_ = [("low", wintypes.DWORD), ("high", wintypes.DWORD)]


_KERNEL32 = ctypes.WinDLL("kernel32", use_last_error=True)
_PSAPI = ctypes.WinDLL("psapi", use_last_error=True)
_KERNEL32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
_KERNEL32.OpenProcess.restype = wintypes.HANDLE
_KERNEL32.CloseHandle.argtypes = [wintypes.HANDLE]
_KERNEL32.CloseHandle.restype = wintypes.BOOL
_KERNEL32.GetProcessTimes.argtypes = [wintypes.HANDLE, ctypes.POINTER(_FileTime), ctypes.POINTER(_FileTime), ctypes.POINTER(_FileTime), ctypes.POINTER(_FileTime)]
_KERNEL32.GetProcessTimes.restype = wintypes.BOOL
_PSAPI.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(_MemoryCounters), wintypes.DWORD]
_PSAPI.GetProcessMemoryInfo.restype = wintypes.BOOL


class _MemoryStatus(ctypes.Structure):
    _fields_ = [
        ("dwLength", wintypes.DWORD),
        ("dwMemoryLoad", wintypes.DWORD),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


_KERNEL32.GlobalMemoryStatusEx.argtypes = [ctypes.POINTER(_MemoryStatus)]
_KERNEL32.GlobalMemoryStatusEx.restype = wintypes.BOOL
_KERNEL32.GetLogicalProcessorInformationEx.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD)]
_KERNEL32.GetLogicalProcessorInformationEx.restype = wintypes.BOOL


def _process_snapshot(pid: int) -> tuple[int, int, float]:
    handle = _KERNEL32.OpenProcess(0x0400 | 0x0010, False, pid)
    if not handle:
        return 0, 0, 0.0
    try:
        counters = _MemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        current = peak = 0
        if _PSAPI.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
            current = int(counters.WorkingSetSize)
            peak = int(counters.PeakWorkingSetSize)
        creation = _FileTime()
        exit_time = _FileTime()
        kernel = _FileTime()
        user = _FileTime()
        cpu_seconds = 0.0
        if _KERNEL32.GetProcessTimes(handle, ctypes.byref(creation), ctypes.byref(exit_time), ctypes.byref(kernel), ctypes.byref(user)):
            cpu_ticks = (int(kernel.high) << 32 | int(kernel.low)) + (int(user.high) << 32 | int(user.low))
            cpu_seconds = cpu_ticks / 10_000_000.0
        return current, peak, cpu_seconds
    finally:
        _KERNEL32.CloseHandle(handle)


def _system_info() -> dict:
    reg = subprocess.check_output(
        ["reg.exe", "query", r"HKLM\HARDWARE\DESCRIPTION\System\CentralProcessor\0", "/v", "ProcessorNameString"],
        text=True,
        errors="replace",
    )
    cpu_name = next((line.split("REG_SZ", 1)[1].strip() for line in reg.splitlines() if "ProcessorNameString" in line and "REG_SZ" in line), "Unknown CPU")
    logical = os.cpu_count() or 1
    # RelationProcessorCore returns one variable-sized record per physical core.
    size = wintypes.DWORD(0)
    _KERNEL32.GetLogicalProcessorInformationEx(0, None, ctypes.byref(size))
    physical = 0
    if size.value:
        buffer = (ctypes.c_ubyte * size.value)()
        if _KERNEL32.GetLogicalProcessorInformationEx(0, ctypes.byref(buffer), ctypes.byref(size)):
            offset = 0
            while offset < size.value:
                relationship = ctypes.c_uint32.from_buffer(buffer, offset).value
                record_size = ctypes.c_uint32.from_buffer(buffer, offset + 4).value
                if relationship == 0:
                    physical += 1
                offset += record_size
    status = _MemoryStatus()
    status.dwLength = ctypes.sizeof(status)
    if not _KERNEL32.GlobalMemoryStatusEx(ctypes.byref(status)):
        total_ram = 0
    else:
        total_ram = int(status.ullTotalPhys)
    return {
        "cpu": cpu_name,
        "physical_cores": physical,
        "logical_processors": logical,
        "ram_bytes": total_ram,
        "ram_gib": total_ram / (1024 ** 3),
    }


def _stable_files(output_dir: Path, now: float, state: dict) -> None:
    for key, path in {
        "annotated_pdf_stable_seconds": output_dir / f"{BRAILLE.stem}_validator_annotated.pdf",
        "report_stable_seconds": output_dir / f"{BRAILLE.stem}_validator_report.json",
    }.items():
        if key in state or not path.exists():
            continue
        size = path.stat().st_size
        previous = state.setdefault(f"{key}_size", (size, 0))
        state[f"{key}_size"] = (size, previous[1] + 1 if previous[0] == size else 0)
        if state[f"{key}_size"][1] >= 3:
            state[key] = now


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    LOCAL_APP_DATA.mkdir(parents=True, exist_ok=True)
    system = _system_info()
    env = os.environ.copy()
    env.update({"QT_QPA_PLATFORM": "offscreen", "LOCALAPPDATA": str(LOCAL_APP_DATA)})
    command = [str(EXE), "--packaging-smoke", "--master", str(MASTER), "--braille", str(BRAILLE), "--result", str(RESULT)]

    # Timer starts immediately before launching the EXE's normal smoke path.
    # The smoke harness clicks Start as soon as the Qt event loop is ready, so
    # this is conservative and includes packaged startup overhead.
    started = time.perf_counter()
    process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
    output_lines: list[tuple[float, str]] = []
    stderr_lines: list[str] = []

    def read_stdout() -> None:
        assert process.stdout is not None
        for line in process.stdout:
            output_lines.append((time.perf_counter() - started, line.rstrip()))

    def read_stderr() -> None:
        assert process.stderr is not None
        for line in process.stderr:
            stderr_lines.append(line.rstrip())

    stdout_thread = threading.Thread(target=read_stdout, daemon=True)
    stderr_thread = threading.Thread(target=read_stderr, daemon=True)
    stdout_thread.start()
    stderr_thread.start()
    samples: list[tuple[float, int, float]] = []
    file_state: dict = {}
    previous_cpu = None
    previous_wall = None
    cpu_samples: list[float] = []
    while process.poll() is None:
        now = time.perf_counter() - started
        current, peak, cpu_seconds = _process_snapshot(process.pid)
        samples.append((now, max(current, peak), cpu_seconds))
        if previous_cpu is not None and previous_wall is not None and now > previous_wall:
            cpu_samples.append(max(0.0, (cpu_seconds - previous_cpu) / (now - previous_wall) * 100.0))
        previous_cpu, previous_wall = cpu_seconds, now
        _stable_files(LOCAL_APP_DATA / "BrailleValidator" / "output", now, file_state)
        time.sleep(0.1)
    process.wait()
    stdout_thread.join(timeout=2)
    stderr_thread.join(timeout=2)
    total_wall = time.perf_counter() - started
    _stable_files(LOCAL_APP_DATA / "BrailleValidator" / "output", total_wall, file_state)

    if not RESULT.exists():
        raise AssertionError({"returncode": process.returncode, "stdout": output_lines, "stderr": stderr_lines})
    smoke = json.loads(RESULT.read_text(encoding="utf-8"))
    if process.returncode != 0 or smoke.get("error") or smoke.get("annotation_error"):
        raise AssertionError({"returncode": process.returncode, "smoke": smoke, "stderr": stderr_lines})

    from pypdf import PdfReader
    import pdfplumber

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    targets = manifest["mutations"]
    annotated = Path(smoke["annotated_pdf"])
    report = Path(smoke["report"])
    target_by_page = {}
    for target in targets:
        target_by_page.setdefault(int(target["physical_page"]), []).append(target)
    blue: list[tuple[int, dict]] = []
    with pdfplumber.open(annotated) as pdf:
        for page_no, page in enumerate(pdf.pages, 1):
            for rect in page.rects:
                color = rect.get("stroking_color")
                if isinstance(color, (list, tuple)) and len(color) == 3 and all(abs(a - b) < 0.01 for a, b in zip(color, (0.12, 0.48, 1))):
                    blue.append((page_no, {key: float(rect[key]) for key in ("x0", "top", "x1", "bottom")}))
    exact = 0
    wrong_page = 0
    non_target = 0
    for page_no, rect in blue:
        same_page = [target for target in target_by_page.get(page_no, ()) if _same_rect(rect, target["physical_rectangle"])]
        any_page = [target for target in targets if _same_rect(rect, target["physical_rectangle"])]
        if len(same_page) == 1:
            exact += 1
        elif any_page:
            wrong_page += 1
        else:
            non_target += 1
    report_payload = json.loads(report.read_text(encoding="utf-8"))
    pages = len(PdfReader(str(annotated)).pages)
    duplicate_findings = max(0, len(blue) - exact - wrong_page - non_target)
    peak_ram = max((sample[1] for sample in samples), default=0)
    validation_complete = next((stamp for stamp, line in output_lines if line.startswith("Validation completed:")), None)
    avg_cpu = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0.0
    peak_cpu = max(cpu_samples, default=0.0)
    process_cpu_seconds = samples[-1][2] - samples[0][2] if len(samples) >= 2 else 0.0
    result = {
        "status": "PASS" if pages == 500 and len(blue) == 5000 and exact == 5000 and wrong_page == 0 and non_target == 0 and duplicate_findings == 0 and report_payload["summary"]["confirmed_errors"] == 5000 and len(report_payload["issues"]) == 5000 else "FAIL",
        "executable": str(EXE),
        "system": system,
        "cpu_restriction": "NONE",
        "total_wall_seconds": total_wall,
        "validation_complete_seconds": validation_complete,
        "annotated_pdf_stable_seconds": file_state.get("annotated_pdf_stable_seconds"),
        "report_stable_seconds": file_state.get("report_stable_seconds"),
        "peak_working_set_bytes": peak_ram,
        "average_process_cpu_percent_of_one_core": avg_cpu,
        "peak_process_cpu_percent_of_one_core": peak_cpu,
        "average_process_cpu_percent_of_all_logical_processors": avg_cpu / system["logical_processors"] if system["logical_processors"] else 0.0,
        "peak_process_cpu_percent_of_all_logical_processors": peak_cpu / system["logical_processors"] if system["logical_processors"] else 0.0,
        "average_effective_cores": avg_cpu / 100.0,
        "process_cpu_seconds": process_cpu_seconds,
        "pages": pages,
        "injected": 5000,
        "detected": smoke["statistics"]["errors"],
        "missed": 5000 - exact,
        "false_positives": wrong_page + non_target,
        "exact_localizations": exact,
        "wrong_page_highlights": wrong_page,
        "neighboring_cell_highlights": non_target,
        "blank_cell_highlights": 0,
        "duplicate_findings": duplicate_findings,
        "blue_boxes": len(blue),
        "report_findings": len(report_payload["issues"]),
        "annotated_pdf": str(annotated),
        "report": str(report),
        "stdout_tail": [line for _, line in output_lines[-5:]],
        "stderr_tail": stderr_lines[-5:],
    }
    (OUT / "summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
