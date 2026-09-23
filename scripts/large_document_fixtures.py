"""Build repeated real-document fixtures for the large-document benchmark."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter


ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "stress_test" / "Test_1" / "Synthetic_Test_01.pdf"
BASE_CLEAN = ROOT / "stress_test" / "Test_1" / "Synthetic_Test_01_converted.pdf"
BASE_CORRUPTED = ROOT / "stress_test" / "Test_1" / "corrupted" / "Synthetic_Test_01_corrupted_stress.pdf"
OUT = ROOT / "reports" / "large_document_fixtures"

TARGET_SOURCE_PAGES = (10, 100, 250, 500, 1000)
SOURCE_PACKET_PAGES = 5
BRAILLE_PACKET_PAGES = 15


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_repeated(reader: PdfReader, repeats: int, path: Path) -> None:
    writer = PdfWriter()
    for _ in range(repeats):
        writer.append(reader)
    with path.open("wb") as handle:
        writer.write(handle)


def write_sparse_corruption(
    clean: PdfReader,
    corrupted: PdfReader,
    repeats: int,
    path: Path,
) -> list[dict]:
    writer = PdfWriter()
    # Five clusters are enough to exercise beginning/interior/end localization
    # without multiplying the existing 59-cell corruption set through every packet.
    selected_packets = {0, max(0, repeats // 4), max(0, repeats // 2), max(0, (3 * repeats) // 4), repeats - 1}
    selected_packets = sorted(selected_packets)
    manifest = []
    for packet in range(repeats):
        for page in range(BRAILLE_PACKET_PAGES):
            use_corrupted = packet in selected_packets and page == 0
            source = corrupted if use_corrupted else clean
            writer.add_page(source.pages[page])
            if use_corrupted:
                manifest.append(
                    {
                        "cluster": len(manifest) + 1,
                        "packet": packet,
                        "source_page": packet * SOURCE_PACKET_PAGES + 1,
                        "actual_pdf_page": packet * BRAILLE_PACKET_PAGES + 1,
                        "source_corruption_manifest": "stress_test/Test_1/corrupted/Synthetic_Test_01_corruption_manifest.json",
                        "note": "page 1 of the known 59-error stress page substituted into an otherwise clean repeated packet",
                    }
                )
    with path.open("wb") as handle:
        writer.write(handle)
    return manifest


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    source_reader = PdfReader(BASE_SOURCE)
    clean_reader = PdfReader(BASE_CLEAN)
    corrupted_reader = PdfReader(BASE_CORRUPTED)
    all_fixtures = []
    for source_pages in TARGET_SOURCE_PAGES:
        repeats = source_pages // SOURCE_PACKET_PAGES
        stem = f"repeat_{source_pages:04d}_source_pages"
        source = OUT / f"{stem}_source.pdf"
        clean = OUT / f"{stem}_clean_braille.pdf"
        corrupted = OUT / f"{stem}_sparse_corrupted_braille.pdf"
        write_repeated(source_reader, repeats, source)
        write_repeated(clean_reader, repeats, clean)
        clusters = write_sparse_corruption(clean_reader, corrupted_reader, repeats, corrupted)
        manifest = {
            "source_pages": source_pages,
            "source_packet_repeats": repeats,
            "source_packet_pages": SOURCE_PACKET_PAGES,
            "braille_packet_pages": BRAILLE_PACKET_PAGES,
            "expected_clean_braille_pages": repeats * BRAILLE_PACKET_PAGES,
            "corruption_clusters": clusters,
            "files": {
                "source": {"path": str(source), "sha256": sha256(source)},
                "clean_braille": {"path": str(clean), "sha256": sha256(clean)},
                "sparse_corrupted_braille": {"path": str(corrupted), "sha256": sha256(corrupted)},
            },
        }
        manifest_path = OUT / f"{stem}_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        all_fixtures.append(manifest)
    (OUT / "manifest.json").write_text(json.dumps(all_fixtures, indent=2), encoding="utf-8")
    print(json.dumps(all_fixtures, indent=2))


if __name__ == "__main__":
    main()
