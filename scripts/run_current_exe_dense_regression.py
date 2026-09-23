"""Run the current packaged EXE against the established dense regressions."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_500_page_dense_stress import _same_rect
from low_end_2core_benchmark import _set_affinity

EXE = ROOT / "dist" / "BrailleValidator" / "BrailleValidator.exe"
OUT = ROOT / "reports" / "current_exe_dense_regression"


def run_case(test: int, kind: str, expected: int) -> dict:
    source_dir = ROOT / "stress_test" / f"Test_{test}"
    corrupted_dir = source_dir / "corrupted"
    prefix = f"Synthetic_Test_{test:02d}"
    master = source_dir / f"{prefix}.pdf"
    actual = source_dir / f"{prefix}_converted.pdf" if kind == "clean" else corrupted_dir / f"{prefix}_corrupted_stress.pdf"
    manifest_path = corrupted_dir / f"{prefix}_corruption_manifest_PREVALIDATION.json"
    folder = OUT / f"Test_{test}_{kind}"
    local_app_data = folder / "localappdata"
    folder.mkdir(parents=True, exist_ok=True)
    local_app_data.mkdir(parents=True, exist_ok=True)
    result_path = folder / "result.json"
    env = os.environ.copy()
    env.update({"QT_QPA_PLATFORM": "offscreen", "LOCALAPPDATA": str(local_app_data)})
    command = [str(EXE), "--packaging-smoke", "--master", str(master), "--braille", str(actual), "--result", str(result_path)]
    started = time.perf_counter()
    process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    _set_affinity(process.pid)
    stdout, stderr = process.communicate(timeout=180)
    wall = time.perf_counter() - started
    smoke = json.loads(result_path.read_text(encoding="utf-8"))
    if process.returncode != 0 or smoke.get("error") or smoke.get("annotation_error"):
        raise AssertionError({"test": test, "kind": kind, "returncode": process.returncode, "smoke": smoke, "stderr": stderr})
    if smoke.get("statistics", {}).get("errors") != expected or smoke.get("issue_count") != expected:
        raise AssertionError({"test": test, "kind": kind, "smoke": smoke})

    annotated = Path(smoke["annotated_pdf"])
    report = Path(smoke["report"])
    from pypdf import PdfReader
    import pdfplumber
    with pdfplumber.open(annotated) as pdf:
        blue = []
        for page_no, page in enumerate(pdf.pages, 1):
            for rect in page.rects:
                color = rect.get("stroking_color")
                if isinstance(color, (list, tuple)) and len(color) == 3 and all(abs(a - b) < 0.01 for a, b in zip(color, (0.12, 0.48, 1))):
                    blue.append((page_no, {key: float(rect[key]) for key in ("x0", "top", "x1", "bottom")}))
    exact = 0
    if expected:
        targets = json.loads(manifest_path.read_text(encoding="utf-8"))["targets"]
        exact = sum(
            sum(page == target["page"] and _same_rect(rect, target["physical_rectangle"]) for page, rect in blue) == 1
            for target in targets
        )
    report_payload = json.loads(report.read_text(encoding="utf-8"))
    passed = (
        process.returncode == 0
        and smoke.get("frozen")
        and len(PdfReader(str(annotated)).pages) == len(PdfReader(str(actual)).pages)
        and len(blue) == expected
        and exact == expected
        and report_payload["summary"]["confirmed_errors"] == expected
        and len(report_payload["issues"]) == expected
    )
    return {"test": test, "kind": kind, "expected": expected, "detected": smoke["statistics"]["errors"], "blue_boxes": len(blue), "exact_boxes": exact, "wall_seconds": wall, "passed": passed, "annotated_pdf": str(annotated), "report": str(report), "stdout_tail": stdout[-500:], "stderr_tail": stderr[-500:]}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = [run_case(1, "clean", 0), run_case(1, "dense", 67), run_case(2, "dense", 68), run_case(4, "dense", 50)]
    report = {"status": "PASS" if all(row["passed"] for row in rows) else "FAIL", "executable": str(EXE), "affinity_mask": "0x3", "rows": rows}
    (OUT / "summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
