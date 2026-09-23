"""Run the packaged GUI smoke path under a two-core affinity mask."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
EXE = ROOT / "dist" / "BrailleValidator" / "BrailleValidator.exe"
FIXTURES = ROOT / "reports" / "low_end_2core_8gb_fixtures"
OUT = ROOT / "reports" / "low_end_2core_8gb_ui"
SIZES = (50, 100, 250, 500)

sys.path.insert(0, str(ROOT / "scripts"))
from low_end_2core_benchmark import _set_affinity


def main() -> None:
    if not EXE.is_file():
        raise FileNotFoundError(EXE)
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    for size in SIZES:
        stem = f"low_end_{size:03d}_pages"
        result_path = OUT / f"{stem}.json"
        command = [
            str(EXE),
            "--packaging-smoke",
            "--master",
            str(FIXTURES / f"{stem}_master.docx"),
            "--braille",
            str(FIXTURES / f"{stem}_clean.pdf"),
            "--result",
            str(result_path),
        ]
        environment = dict(**__import__("os").environ, QT_QPA_PLATFORM="offscreen")
        started = time.perf_counter()
        process = subprocess.Popen(command, cwd=ROOT, env=environment)
        _set_affinity(process.pid)
        try:
            return_code = process.wait(timeout=180)
            timeout = False
        except subprocess.TimeoutExpired:
            process.kill()
            return_code = None
            timeout = True
        wall = time.perf_counter() - started
        smoke = json.loads(result_path.read_text(encoding="utf-8")) if result_path.is_file() else None
        results.append({
            "pages": size,
            "return_code": return_code,
            "timeout": timeout,
            "wall_seconds": wall,
            "smoke": smoke,
        })
        print(f"completed packaged UI smoke {size} pages", flush=True)
    destination = ROOT / "reports" / "low_end_2core_8gb_ui.json"
    destination.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
