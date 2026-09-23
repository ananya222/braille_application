"""Independent BRF-vs-Liblouis audit comparison.

This is evidence tooling only.  It never writes production files or edits the
frozen inputs.  BRF is the comparison source; DXB is inspected separately for
configuration evidence.
"""

from __future__ import annotations

import csv
from difflib import SequenceMatcher
import itertools
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "stress_test" / "ueb_g1_duxbury_comparison"
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from braille_app.translation.braille_cells import BRF_DOTS, char_mask, cells_to_unicode, ascii_to_cells


def _reverse_brf() -> dict[int, str]:
    out: dict[int, str] = {}
    for char in BRF_DOTS:
        out.setdefault(char_mask(char, "duxbury"), char.upper() if char.isalpha() else char)
    return out


BRF_BY_MASK = _reverse_brf()


def cells_to_brf(cells: tuple[int, ...] | list[int]) -> str:
    return "".join(BRF_BY_MASK.get(cell, f"<dots:{cell}>") for cell in cells)


def _read_manifest() -> dict[str, dict[str, str]]:
    with (HERE / "source_case_manifest.csv").open(encoding="utf-8", newline="") as stream:
        rows = {}
        for row in csv.DictReader(stream):
            # The frozen file's first data rows contain page then source text
            # under the header names source_text then page. Do not edit that
            # frozen evidence; recover the intended fields by their content.
            if row["source_text"].isdigit() and not row["page"].isdigit():
                row["source_text"], row["page"] = row["page"], row["source_text"]
            rows[row["source_text"]] = row
        return rows


def _lib_pages() -> list[list[tuple[str, str, tuple[int, ...]]]]:
    source_pages = [page.splitlines() for page in (HERE / "ueb_g1_5page_stress.txt").read_text(encoding="utf-8").split("\n\n")]
    pages: list[list[tuple[str, tuple[int, ...]]]] = []
    for source_page, raw_page in zip(source_pages, (HERE / "liblouis_output.txt").read_text(encoding="utf-8").split("\f")):
        lines = [line for line in raw_page.splitlines() if line]
        if len(source_page) != len(lines):
            raise AssertionError(f"source/Liblouis line mismatch: {len(source_page)} != {len(lines)}")
        pages.append([(source, line, tuple(ord(ch) - 0x2800 if 0x2800 <= ord(ch) <= 0x28FF else 0 for ch in line)) for source, line in zip(source_page, lines)])
    return pages


def _duxbury_pages() -> list[list[str]]:
    raw = (HERE / "ueb_g1_5page_stress.brf").read_text(encoding="ascii")
    pages = []
    for raw_page in raw.split("\f"):
        lines = []
        for line in raw_page.splitlines():
            if not line.strip():
                continue
            # DBT footer page number: layout furniture, not Braille content.
            if re.fullmatch(r"\s*#[A-Z0-9]+\s*", line):
                continue
            content = line.strip()
            if content:
                lines.append(content)
        if lines:
            pages.append(lines)
    return pages


def _logical_lib(page: list[tuple[str, str, tuple[int, ...]]], manifest: dict[str, dict[str, str]], page_no: int):
    cells: list[int] = []
    spans: list[dict] = []
    for source, line, line_cells in page:
        if cells:
            cells.append(0)
        start = len(cells)
        cells.extend(line_cells)
        row = manifest.get(source)
        spans.append({"start": start, "end": len(cells), "case": row["case_id"] if row else f"P{page_no}-UNMANIFESTED", "source": source})
    return tuple(cells), spans


def _logical_dxb(page: list[str]):
    cells: list[int] = []
    for line in page:
        if cells:
            # BRF line endings are layout breaks.  A single logical blank is
            # retained where DBT wrapped between source words.
            cells.append(0)
        cells.extend(ascii_to_cells(line, "duxbury"))
    return tuple(cells)


def _case_at(spans: list[dict], start: int, end: int) -> dict:
    for span in spans:
        if start < span["end"] and end > span["start"]:
            return span
    if spans:
        nearest = min(spans, key=lambda span: abs(span["start"] - start))
        return nearest
    return {"case": "UNMAPPED", "source": ""}


def compare() -> list[dict]:
    manifest = _read_manifest()
    lib_pages = _lib_pages()
    dxb_pages = _duxbury_pages()
    if len(lib_pages) != 5 or len(dxb_pages) != 5:
        raise AssertionError(f"expected five pages, Liblouis={len(lib_pages)}, Duxbury={len(dxb_pages)}")

    raw_rows: list[dict] = []
    difference_number = 0
    for page_no, (lib_page, dxb_page) in enumerate(zip(lib_pages, dxb_pages), 1):
        lib_cells, spans = _logical_lib(lib_page, manifest, page_no)
        dxb_cells = _logical_dxb(dxb_page)
        matcher = SequenceMatcher(None, lib_cells, dxb_cells, autojunk=False)
        opcodes = matcher.get_opcodes()
        for tag, a0, a1, b0, b1 in opcodes:
            if tag == "equal":
                continue
            difference_number += 1
            span = _case_at(spans, a0, a1)
            source_row = manifest.get(span["source"], {})
            raw_rows.append(
                {
                    "difference_id": f"D{difference_number:03d}",
                    "source_case_id": span["case"],
                    "page": page_no,
                    "rule_family": source_row.get("rule_family", "layout or unmanifested"),
                    "citation": source_row.get("iceb_ueb_2024_citation", ""),
                    "liblouis_start": a0,
                    "liblouis_end": a1,
                    "duxbury_start": b0,
                    "duxbury_end": b1,
                    "liblouis_cells": cells_to_brf(lib_cells[a0:a1]),
                    "duxbury_cells": cells_to_brf(dxb_cells[b0:b1]),
                    "liblouis_unicode": cells_to_unicode(lib_cells[a0:a1]),
                    "duxbury_unicode": cells_to_unicode(dxb_cells[b0:b1]),
                    "source_context": span["source"],
                    "opcode": tag,
                }
            )
    grouped: list[dict] = []
    def grouping_key(row: dict) -> tuple:
        # Separate distinct punctuation/whitespace tokens; combine repeated
        # typeform markers into one representation disagreement.
        if row["source_case_id"] in {"P3-PUNCT-ADJ", "P5-WHITESPACE"}:
            return (row["page"], row["source_case_id"], row["rule_family"], row["difference_id"])
        return (row["page"], row["source_case_id"], row["rule_family"])
    for group_number, (key, group_iter) in enumerate(itertools.groupby(raw_rows, key=grouping_key), 1):
        page, case_id, family = key[:3]
        group = list(group_iter)
        first = group[0]
        grouped.append(
            {
                "difference_id": f"G{group_number:03d}",
                "source_case_id": case_id,
                "page": page,
                "rule_family": family,
                "citation": first["citation"],
                "liblouis_start": min(row["liblouis_start"] for row in group),
                "liblouis_end": max(row["liblouis_end"] for row in group),
                "duxbury_start": min(row["duxbury_start"] for row in group),
                "duxbury_end": max(row["duxbury_end"] for row in group),
                "liblouis_cells": " / ".join(row["liblouis_cells"] for row in group),
                "duxbury_cells": " / ".join(row["duxbury_cells"] for row in group),
                "liblouis_unicode": " / ".join(row["liblouis_unicode"] for row in group),
                "duxbury_unicode": " / ".join(row["duxbury_unicode"] for row in group),
                "source_context": first["source_context"],
                "opcode": "grouped:" + ",".join(row["opcode"] for row in group),
                "raw_difference_ids": ",".join(row["difference_id"] for row in group),
                "raw_opcode_count": len(group),
            }
        )
    return grouped


def main() -> None:
    rows = compare()
    out = HERE / "aligned_differences.csv"
    fields = list(rows[0]) if rows else ["difference_id", "source_case_id", "page", "rule_family", "citation", "liblouis_start", "liblouis_end", "duxbury_start", "duxbury_end", "liblouis_cells", "duxbury_cells", "liblouis_unicode", "duxbury_unicode", "source_context", "opcode", "raw_difference_ids", "raw_opcode_count"]
    with out.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"differences={len(rows)}")
    for row in rows:
        print(row["difference_id"], row["source_case_id"], row["rule_family"], row["liblouis_cells"], "=>", row["duxbury_cells"])


if __name__ == "__main__":
    main()
