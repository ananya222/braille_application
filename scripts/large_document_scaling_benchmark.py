"""Run one isolated public-API scaling benchmark fixture."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from large_document_profile import memory_bytes
from braille_app.validation.api import validate_document


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_pages", type=int)
    parser.add_argument("kind", choices=("clean", "sparse_corrupted"))
    args = parser.parse_args()
    fixture = ROOT / "reports" / "large_document_fixtures"
    stem = f"repeat_{args.source_pages:04d}_source_pages"
    source = fixture / f"{stem}_source.pdf"
    actual = fixture / f"{stem}_{args.kind}_braille.pdf"
    before, _ = memory_bytes()
    started = time.perf_counter()
    report = validate_document(str(source), str(actual))
    seconds = time.perf_counter() - started
    after, peak = memory_bytes()
    payload = {
        "source_pages": args.source_pages,
        "kind": args.kind,
        "source": str(source),
        "actual": str(actual),
        "seconds": seconds,
        "rss_delta_bytes": after - before,
        "peak_working_set_bytes": peak,
        "statistics": report.statistics,
    }
    output = fixture / f"{stem}_{args.kind}_benchmark.json"
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
