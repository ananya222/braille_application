"""Create deterministic standalone Braille stress-test PDFs."""

from __future__ import annotations

import json
from pathlib import Path
import random
import sys

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "stress_test" / "large_documents"
SEED = 20260921
LINES_PER_PAGE = 26
GROUPS_PER_LINE = 5
CELLS_PER_GROUP = 7
SIZES = (50, 100, 250, 500)

sys.path.insert(0, str(ROOT / "scripts"))
from build_large_braille_performance_fixtures import write_braille_pdf


def make_pages(page_count: int) -> list[list[str]]:
    rng = random.Random(SEED)
    valid_patterns = [pattern for pattern in range(1, 64) if pattern != 0x24]
    pages: list[list[str]] = []
    for _page in range(page_count):
        rows = []
        for _line in range(LINES_PER_PAGE):
            groups = [
                "".join(chr(0x2800 + rng.choice(valid_patterns)) for _ in range(CELLS_PER_GROUP))
                for _ in range(GROUPS_PER_LINE)
            ]
            rows.append("\u2800".join(groups))
        pages.append(rows)
    return pages


def verify(path: Path, expected_pages: int, expected_cells_per_page: int) -> dict:
    reader = PdfReader(path)
    if len(reader.pages) != expected_pages:
        raise AssertionError(f"{path.name}: expected {expected_pages} pages, got {len(reader.pages)}")
    size = path.stat().st_size
    return {
        "path": str(path),
        "pages": len(reader.pages),
        "braille_cells": expected_pages * expected_cells_per_page,
        "average_cells_per_page": expected_cells_per_page,
        "file_size_bytes": size,
        "seed": SEED,
        "lines_per_page": LINES_PER_PAGE,
        "cells_per_line": GROUPS_PER_LINE * CELLS_PER_GROUP + GROUPS_PER_LINE - 1,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cells_per_page = LINES_PER_PAGE * (GROUPS_PER_LINE * CELLS_PER_GROUP + GROUPS_PER_LINE - 1)
    summary = []
    for page_count in SIZES:
        pages = make_pages(page_count)
        path = OUT / f"performance_braille_{page_count:03d}_pages.pdf"
        write_braille_pdf(path, pages)
        summary.append(verify(path, page_count, cells_per_page))
    destination = ROOT / "reports" / "standalone_large_braille_documents.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps({"seed": SEED, "files": summary}, indent=2), encoding="utf-8")
    print(json.dumps({"seed": SEED, "files": summary}, indent=2))


if __name__ == "__main__":
    main()
