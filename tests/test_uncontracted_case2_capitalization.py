"""Deterministic tests for Case 2 ASCII capitalization."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from braille_app.translation.braille_cells import BRF_DOTS, cells_to_unicode, char_mask, unicode_to_cells
from braille_app.translation.expected_document import generate_expected_braille
from braille_app.translation.liblouis_translator import vendored_metadata
from braille_app.translation.profiles import UNCONTRACTED_UEB_CASE2
from braille_app.translation.source_normalization import (
    UnsupportedSourceError,
    normalize_uncontracted_case2,
)
from braille_app.validation.api import validate_document


CASES = {
    "lowercase alphabet": "abcdefghijklmnopqrstuvwxyz",
    "uppercase alphabet": "A B C D E F G H I J K L M N O P Q R S T U V W X Y Z",
    "ordinary words": "hello braille validator ordinary education computer",
    "capitalized words": "Hello Braille Validator Education",
    "isolated capitals": "A B D Z",
    "all cap words": "NASA UEB PDF ABC",
    "internal capitals": "iPhone eBay McDonald",
    "mixed sentence": "Hello NASA UEB PDF ABC hello",
}


def _master(source: str) -> dict:
    return {"pages": [{"print_page_number": 1, "blocks": [{"text": source}]}]}


def _brf(cells: tuple[int, ...]) -> str:
    reverse = {char_mask(char, "duxbury"): char for char in BRF_DOTS if char != " "}
    return "".join(" " if cell == 0 else reverse[cell] for cell in cells)


def _corrupt(value: str) -> str:
    cells = list(unicode_to_cells(value))
    index = next(i for i, cell in enumerate(cells) if cell)
    cells[index] = cells[index] ^ 1 or cells[index] | 2
    return cells_to_unicode(cells)


class UncontractedCase2Tests(unittest.TestCase):
    def test_extra_letter_in_capitalized_word_is_not_suppressed(self):
        master = _master("Hello")
        cells = list(unicode_to_cells(generate_expected_braille(master, UNCONTRACTED_UEB_CASE2).flatten()))
        cells.insert(3, char_mask("z", "duxbury"))

        result = validate_document(master, cells_to_unicode(cells), profile=UNCONTRACTED_UEB_CASE2)

        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.reviews, ())
        self.assertEqual(result.statistics["ignored_unmapped_insertions"], 0)

    def test_duxbury_typeform_control_is_not_an_error(self):
        master = _master("A")
        cells = (24, char_mask("2", "duxbury")) + unicode_to_cells(
            generate_expected_braille(master, UNCONTRACTED_UEB_CASE2).flatten()
        )

        result = validate_document(master, cells_to_unicode(cells), profile=UNCONTRACTED_UEB_CASE2)

        self.assertEqual(result.errors, ())
        self.assertEqual(result.reviews, ())

    def test_supported_families_clean_corrupt_and_brf_neighbor(self):
        for family, source in CASES.items():
            with self.subTest(family=family):
                master = _master(source)
                expected = generate_expected_braille(master, "uncontracted_case2_capitalization").flatten()

                clean = validate_document(master, expected, profile="uncontracted_case2_capitalization")
                self.assertEqual(clean.errors, ())
                self.assertEqual(clean.reviews, ())

                corrupted = validate_document(master, _corrupt(expected), profile="uncontracted_case2_capitalization")
                self.assertEqual(len(corrupted.errors), 1)
                self.assertEqual(corrupted.reviews, ())
                self.assertEqual(corrupted.errors[0].actual_page_number, 1)

                near = validate_document(
                    master,
                    _brf(unicode_to_cells(expected)),
                    profile="uncontracted_case2_capitalization",
                )
                self.assertEqual(near.errors, ())
                self.assertEqual(near.reviews, ())

    def test_unsupported_source_is_review_only(self):
        for value in ("Hello,", "hello\tworld", "hello\u00a0world", "123", "hello\nworld", "'Hello'"):
            with self.subTest(value=value):
                with self.assertRaises(UnsupportedSourceError):
                    normalize_uncontracted_case2(value)
                result = validate_document(_master(value), "", profile="uncontracted_case2_capitalization")
                self.assertEqual(result.errors, ())
                self.assertEqual(len(result.reviews), 1)

    def test_capital_modes_are_contextual_liblouis_output(self):
        translator = generate_expected_braille(_master("NASA UEB PDF ABC"), UNCONTRACTED_UEB_CASE2)
        cells = translator.flatten()
        self.assertTrue(cells.startswith("⠠⠠⠠"))
        self.assertTrue(cells.endswith("⠠⠄"))

    def test_vendored_runtime_identity(self):
        metadata = vendored_metadata(UNCONTRACTED_UEB_CASE2)
        self.assertEqual(metadata["version"], "3.38.0")
        self.assertEqual(metadata["table_list"], "unicode.dis,en-ueb-g1.ctb")
        self.assertEqual(len(metadata["table_hash_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
