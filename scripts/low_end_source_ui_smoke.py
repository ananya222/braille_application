"""Measure Qt event-loop responsiveness while the current ValidationThread runs."""

from __future__ import annotations

import json
from pathlib import Path
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "reports" / "low_end_2core_8gb_fixtures"
OUT = ROOT / "reports" / "low_end_2core_8gb_ui_source"
SIZES = (50, 100, 250, 500)

sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))
from low_end_2core_benchmark import _set_affinity


def run_single(size: int) -> dict:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication
    from main_gui import MainWindow

    app = QApplication(sys.argv[:1])
    window = MainWindow()
    stem = f"low_end_{size:03d}_pages"
    window.english_path = str(FIXTURES / f"{stem}_master.docx")
    window.braille_path = str(FIXTURES / f"{stem}_clean.pdf")
    tick_times: list[float] = []
    statuses: list[str] = []
    started = time.perf_counter()
    finished = {"done": False}

    def tick() -> None:
        tick_times.append(time.perf_counter())

    def watch_thread() -> None:
        thread = getattr(window, "thread", None)
        if thread is not None and not thread.isRunning() and window.current_result is not None and not finished["done"]:
            finished["done"] = True
            QTimer.singleShot(100, app.quit)

    timer = QTimer()
    timer.timeout.connect(tick)
    timer.start(100)
    watcher = QTimer()
    watcher.timeout.connect(watch_thread)
    watcher.start(100)
    window.run_btn.click()
    if getattr(window, "thread", None) is not None:
        window.thread.status_update.connect(statuses.append)
    app.exec()
    elapsed = time.perf_counter() - started
    gaps = [right - left for left, right in zip(tick_times, tick_times[1:])]
    window.close()
    return {
        "pages": size,
        "runtime_seconds": elapsed,
        "event_loop_ticks": len(tick_times),
        "max_timer_gap_seconds": max(gaps) if gaps else None,
        "progress_updates": statuses,
        "status": "RESPONSIVE" if tick_times and (not gaps or max(gaps) < 1.0) else "INCONCLUSIVE",
        "findings": len(window.current_result.errors) if window.current_result else None,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if len(sys.argv) == 3 and sys.argv[1] == "--single":
        path = OUT / f"{int(sys.argv[2]):03d}.json"
        result = run_single(int(sys.argv[2]))
        path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print("RESULT_JSON=" + json.dumps(result, ensure_ascii=True))
        return
    results = []
    for size in SIZES:
        process = subprocess.Popen(
            [sys.executable, __file__, "--single", str(size)],
            cwd=ROOT,
            env=dict(os.environ, QT_QPA_PLATFORM="offscreen"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        _set_affinity(process.pid)
        stdout, stderr = process.communicate(timeout=180)
        if process.returncode:
            raise RuntimeError(f"UI smoke failed for {size}:\n{stdout}\n{stderr}")
        line = next(line for line in stdout.splitlines() if line.startswith("RESULT_JSON="))
        results.append(json.loads(line.removeprefix("RESULT_JSON=")))
        print(f"completed source UI smoke {size} pages", flush=True)
    destination = ROOT / "reports" / "low_end_2core_8gb_ui_source.json"
    destination.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
