"""Focused regression tests for uncontracted repeated-region alignment."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from braille_app.translation.braille_cells import cells_to_unicode, unicode_to_cells
from braille_app.translation.expected_document import generate_expected_braille
from braille_app.validation.api import validate_document


PROFILE = "uncontracted_case2_capitalization"


def _master(pages: list[list[str]]) -> dict:
    return {
        "pages": [
            {
                "print_page_number": page_number,
                "blocks": [{"text": text} for text in blocks],
            }
            for page_number, blocks in enumerate(pages, 1)
        ]
    }


def _clean_pages(master: dict) -> list[list[int]]:
    expected = generate_expected_braille(master, PROFILE)
    return [list(unicode_to_cells(page.flatten())) for page in expected.pages]


def _block_start(master: dict, page_number: int, block_index: int) -> int:
    page = generate_expected_braille(master, PROFILE).pages[page_number - 1]
    return sum(
        len(unicode_to_cells(block.braille)) + 1
        for block in page.blocks[:block_index]
        if block.braille
    )


def _actual(
    master: dict,
    pages: list[list[int]],
    deltas: dict[tuple[int, int], int] | None = None,
) -> str:
    deltas = deltas or {}
    expected = generate_expected_braille(master, PROFILE)
    rendered = []
    for page_number, (page, expected_page) in enumerate(zip(pages, expected.pages), 1):
        cursor = 0
        lines = []
        blocks = [block for block in expected_page.blocks if block.braille]
        for block_index, block in enumerate(blocks):
            width = len(unicode_to_cells(block.braille)) + deltas.get(
                (page_number, block_index), 0
            )
            lines.append(cells_to_unicode(tuple(page[cursor:cursor + width])))
            cursor += width
            if block_index + 1 < len(blocks) and cursor < len(page) and page[cursor] == 0:
                cursor += 1
        if cursor < len(page):
            lines.append(cells_to_unicode(tuple(page[cursor:])))
        rendered.append("\n".join(lines))
    return "\f".join(rendered)


class RepeatedRegionAlignmentTests(unittest.TestCase):
    def _assert_errors(
        self,
        master: dict,
        pages: list[list[int]] | str,
        count: int,
        physical_page: int | None = None,
        deltas: dict[tuple[int, int], int] | None = None,
    ) -> None:
        actual = pages if isinstance(pages, str) else _actual(master, pages, deltas)
        result = validate_document(master, actual, profile=PROFILE)
        self.assertEqual(len(result.errors), count)
        self.assertEqual(result.reviews, ())
        self.assertEqual(len({issue.issue_id for issue in result.errors}), count)
        if physical_page is not None:
            self.assertTrue(
                all(issue.actual_page_number == physical_page for issue in result.errors)
            )

    def test_repeated_region_cases(self):
        cases = []

        master = _master([["hello world", "hello world"]])
        pages = _clean_pages(master)
        pages[0][_block_start(master, 1, 1) + 1] ^= 1
        cases.append(("two identical paragraphs, second", master, pages, 1, 1))

        master = _master([["hello world", "hello world", "hello world"]])
        pages = _clean_pages(master)
        pages[0][_block_start(master, 1, 1) + 2] ^= 1
        cases.append(("three identical paragraphs, middle", master, pages, 1, 1))

        master = _master([["hello world"], ["hello world"]])
        pages = _clean_pages(master)
        pages[1][2] ^= 1
        cases.append(("identical lines across pages", master, pages, 1, 2))

        master = _master([["hello world", "hello world"], ["hello world", "hello world"]])
        pages = _clean_pages(master)
        pages[1][_block_start(master, 2, 1) + 3] ^= 1
        cases.append(("repeated page-like blocks", master, pages, 1, 2))

        master = _master([["hello Hello hello"]])
        pages = _clean_pages(master)
        pages[0][8] ^= 1
        cases.append(("same words with nearby capitalization", master, pages, 1, 1))

        master = _master([["hello world", "hello world"]])
        pages = _clean_pages(master)
        start = _block_start(master, 1, 1)
        pages[0].insert(start + 2, 45)
        cases.append(("insertion in repeated block", master, pages, 1, 1, {(1, 1): 1}))

        master = _master([["hello world", "hello world"]])
        pages = _clean_pages(master)
        start = _block_start(master, 1, 1)
        del pages[0][start + 2]
        cases.append(("deletion in repeated block", master, pages, 1, 1, {(1, 1): -1}))

        master = _master([["hello world", "hello world", "hello world"]])
        pages = _clean_pages(master)
        pages[0][1] ^= 1
        pages[0][_block_start(master, 1, 2) + 2] ^= 1
        cases.append(("multiple repeated-block corruptions", master, pages, 2, 1))

        master = _master([["hello world", "hello world"]])
        pages = _clean_pages(master)
        pages[0][0] ^= 1
        cases.append(("beginning of repeated region", master, pages, 1, 1))

        master = _master([["hello world", "hello world"]])
        pages = _clean_pages(master)
        pages[0][-1] ^= 1
        cases.append(("end of repeated region", master, pages, 1, 1))

        master = _master([["unique alpha", "hello world", "hello world", "unique omega"]])
        pages = _clean_pages(master)
        pages[0][_block_start(master, 1, 2) + 1] ^= 1
        cases.append(("repeated regions separated by unique context", master, pages, 1, 1))

        master = _master([["xhello y", "zhello q"]])
        pages = _clean_pages(master)
        pages[0][_block_start(master, 1, 1) + 3] ^= 1
        cases.append(("small unique prefixes and suffixes", master, pages, 1, 1))

        master = _master([["hello world", "unique source"], ["second page"]])
        expected = generate_expected_braille(master, PROFILE)
        first = list(unicode_to_cells(expected.pages[0].blocks[0].braille))
        second = list(unicode_to_cells(expected.pages[0].blocks[1].braille))
        third = list(unicode_to_cells(expected.pages[1].flatten()))
        split = len(second) // 2
        actual_text = "\f".join(
            (
                cells_to_unicode(tuple(first))
                + "\n"
                + cells_to_unicode(tuple(second[:split])),
                cells_to_unicode(tuple(second[split:])),
                cells_to_unicode(tuple(third[:-1] + [third[-1] ^ 1])),
            )
        )
        cases.append(("Duxbury-style block crossing physical pages", master, actual_text, 1, 3, None))

        for name, case_master, case_pages, count, physical_page, *rest in cases:
            with self.subTest(name=name):
                self._assert_errors(case_master, case_pages, count, physical_page, rest[0] if rest else None)


if __name__ == "__main__":
    unittest.main()
