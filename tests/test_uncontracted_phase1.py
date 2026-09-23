"""Dependency-free checks for the English-only uncontracted UEB slice."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from braille_app.translation.braille_cells import BRF_DOTS, char_mask, cells_to_unicode, unicode_to_cells
from braille_app.translation.expected_document import generate_expected_braille
from braille_app.translation.liblouis_translator import vendored_metadata
from braille_app.translation.profiles import UNCONTRACTED_UEB_PHASE1
from braille_app.translation.source_normalization import (
    UnsupportedSourceError,
    normalize_uncontracted_phase1,
)
from braille_app.validation.api import validate_document


CASES = {
    "lowercase alphabet": "abcdefghijklmnopqrstuvwxyz",
    "uppercase alphabet": "A B C D E F G H I J K L M N O P Q R S T U V W X Y Z",
    "ordinary words": "hello braille validator ordinary education computer",
    "capitalized words": "Hello Braille Validator Education",
    "isolated capitals": "A B D Z",
    "ordinary sentence": "Hello braille validator education computer",
}


def _brf(cells: tuple[int, ...]) -> str:
    reverse = {char_mask(char, "duxbury"): char for char in BRF_DOTS if char != " "}
    return "".join(" " if cell == 0 else reverse[cell] for cell in cells)


def _corrupt(value: str) -> str:
    cells = list(unicode_to_cells(value))
    index = next(i for i, cell in enumerate(cells) if cell)
    cells[index] = cells[index] ^ 1 or cells[index] | 2
    return cells_to_unicode(cells)


class UncontractedPhase1Tests(unittest.TestCase):
    def test_supported_families_clean_corrupt_and_non_error_neighbor(self):
        for family, source in CASES.items():
            with self.subTest(family=family):
                master = {"pages": [{"print_page_number": 1, "blocks": [{"text": source}]}]}
                expected = generate_expected_braille(master, "uncontracted_phase1").flatten()

                clean = validate_document(master, expected, profile="uncontracted_phase1")
                self.assertEqual(clean.errors, ())
                self.assertEqual(clean.reviews, ())

                corrupted = validate_document(master, _corrupt(expected), profile="uncontracted_phase1")
                self.assertEqual(len(corrupted.errors), 1)
                self.assertEqual(corrupted.reviews, ())
                self.assertEqual(corrupted.errors[0].actual_page_number, 1)
                self.assertLess(corrupted.errors[0].actual_cell_start, corrupted.errors[0].actual_cell_end)

                # Unicode Braille and the canonical six-dot BRF spelling are
                # distinct representations of the same physical cells.
                near = validate_document(master, _brf(unicode_to_cells(expected)), profile="uncontracted_phase1")
                self.assertEqual(near.errors, ())
                self.assertEqual(near.reviews, ())

    def test_unsupported_source_is_review_only(self):
        for value in ("hello,", "hello\tworld", "hello\u00a0world", "123", "hello\nworld", "'hello'"):
            with self.subTest(value=value):
                with self.assertRaises(UnsupportedSourceError):
                    normalize_uncontracted_phase1(value)
                master = {"pages": [{"print_page_number": 1, "blocks": [{"text": value}]}]}
                result = validate_document(master, "", profile="uncontracted_phase1")
                self.assertEqual(result.errors, ())
                self.assertEqual(len(result.reviews), 1)

    def test_vendored_runtime_identity(self):
        metadata = vendored_metadata(UNCONTRACTED_UEB_PHASE1)
        self.assertEqual(metadata["version"], "3.38.0")
        self.assertEqual(metadata["table_list"], "unicode.dis,en-ueb-g1.ctb")
        self.assertEqual(len(metadata["table_hash_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
