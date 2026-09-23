"""Focused Case 1 tests: lowercase alphabet and ordinary words only."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from braille_app.translation.expected_document import generate_expected_braille
from braille_app.translation.liblouis_translator import vendored_metadata
from braille_app.translation.profiles import UNCONTRACTED_UEB_CASE1
from braille_app.translation.source_normalization import (
    UnsupportedSourceError,
    normalize_uncontracted_case1,
)
from braille_app.validation.api import validate_document


PROFILE = "uncontracted_case1_alphabet_words"


class UncontractedCase1Tests(unittest.TestCase):
    def test_lowercase_alphabet_and_words(self):
        values = (
            "abcdefghijklmnopqrstuvwxyz",
            "a i am an",
            "be in to of",
            "letter success bookkeeper",
            "education computer accessibility validation",
            "the quick brown fox jumps over the lazy dog",
            "test test test letter letter letter",
        )
        for value in values:
            with self.subTest(value=value):
                master = {"pages": [{"print_page_number": 1, "blocks": [{"text": value}]}]}
                expected = generate_expected_braille(master, PROFILE).flatten()
                result = validate_document(master, expected, profile=PROFILE)
                self.assertEqual(result.errors, ())
                self.assertEqual(result.reviews, ())

    def test_case1_rejects_later_families(self):
        for value in ("Hello", "123", "hello,", "hello-world", "don't", "hello\ththere", "héllo"):
            with self.subTest(value=value):
                with self.assertRaises(UnsupportedSourceError):
                    normalize_uncontracted_case1(value)
                master = {"pages": [{"print_page_number": 1, "blocks": [{"text": value}]}]}
                result = validate_document(master, "", profile=PROFILE)
                self.assertEqual(result.errors, ())
                self.assertEqual(len(result.reviews), 1)

    def test_profile_uses_the_audited_runtime(self):
        metadata = vendored_metadata(UNCONTRACTED_UEB_CASE1)
        self.assertEqual(metadata["version"], "3.38.0")
        self.assertEqual(metadata["table_list"], "unicode.dis,en-ueb-g1.ctb")
        self.assertEqual(len(metadata["table_hash_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
