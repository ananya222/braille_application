"""Build matching clean/corrupt audit fixtures without touching production code."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
sys.path.insert(0, str(ROOT / "scripts"))

from build_large_braille_performance_fixtures import (
    _corruption_manifest,
    _docx,
    make_master,
    write_braille_pdf,
)
from braille_app.translation.expected_document import generate_expected_braille


OUT = ROOT / "reports" / "low_end_2core_8gb_fixtures"
SIZES = (50, 100, 250, 500)


def build_one(size: int) -> dict:
    master = make_master(size)
    expected = generate_expected_braille(master)
    clean_pages = [[block.braille for block in page.blocks] for page in expected.pages]
    corrupted_pages, mutations = _corruption_manifest(clean_pages, size)
    OUT.mkdir(parents=True, exist_ok=True)
    stem = f"low_end_{size:03d}_pages"
    master_json = OUT / f"{stem}_master.json"
    master_json.write_text(json.dumps(master, ensure_ascii=False, indent=2), encoding="utf-8")
    _docx(OUT / f"{stem}_master.docx", master)
    write_braille_pdf(OUT / f"{stem}_clean.pdf", clean_pages)
    write_braille_pdf(OUT / f"{stem}_corrupted.pdf", corrupted_pages)
    manifest = {
        "pages": size,
        "master_json": master_json.name,
        "master_docx": f"{stem}_master.docx",
        "clean_pdf": f"{stem}_clean.pdf",
        "corrupted_pdf": f"{stem}_corrupted.pdf",
        "mutations": mutations,
    }
    (OUT / f"{stem}_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return {"pages": size, "mutations": len(mutations), "stem": stem}


def main() -> None:
    summary = [build_one(size) for size in SIZES]
    (OUT / "manifest.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
