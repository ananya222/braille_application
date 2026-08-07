import ctypes
import os
import sys
import unittest
from unittest.mock import patch


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TABLES_DIR = os.path.join(ROOT, "vendor", "liblouis-win64", "share", "liblouis", "tables")
sys.path.insert(0, os.path.join(ROOT, "vendor", "liblouis-bindings"))
sys.path.insert(0, os.path.join(ROOT, "src"))
os.environ["LOUIS_TABLEPATH"] = TABLES_DIR

if sys.platform == "win32":
    ctypes.CDLL("msvcrt")._wputenv(f"LOUIS_TABLEPATH={TABLES_DIR}")

import louis
from braille_app.brf_parser import ASCII_TO_UNICODE_BRAILLE, ascii_to_unicode_braille


TABLE = os.path.join(TABLES_DIR, "en-ueb-g1.ctb")
BACKTICK = chr(96)


def translate_and_normalize(source):
    """Test-only equivalent of the validator's translate-then-normalize boundary."""
    raw = louis.translateString([TABLE], source)
    return raw, ascii_to_unicode_braille(raw)


class TestAsciiBrailleNormalization(unittest.TestCase):
    def test_backtick_is_dot_four(self):
        self.assertEqual(ASCII_TO_UNICODE_BRAILLE[BACKTICK], "\u2808")
        self.assertEqual(ascii_to_unicode_braille(BACKTICK), "\u2808")

    def test_liblouis_backtick_cell_normalizes(self):
        self.assertEqual(ascii_to_unicode_braille(BACKTICK + "a"), "\u2808\u2801")

    def test_vertical_bar_is_dots_1256(self):
        self.assertEqual(ASCII_TO_UNICODE_BRAILLE["|"], "\u2833")
        self.assertEqual(ascii_to_unicode_braille("|"), "\u2833")

    def test_liblouis_vertical_bar_cell_normalizes(self):
        raw = louis.translateString([TABLE], "|")
        self.assertEqual(raw, "_|")
        self.assertEqual(ascii_to_unicode_braille(raw), "\u2838\u2833")

    def test_source_vertical_bar_is_passed_unchanged_before_translation(self):
        source = "|"
        with patch.object(louis, "translateString", return_value="_|") as translate:
            raw = louis.translateString([TABLE], source)
        translate.assert_called_once_with([TABLE], source)
        self.assertEqual(raw, "_|")
        self.assertEqual(ascii_to_unicode_braille(raw), "\u2838\u2833")

    def test_punctuation_translations_no_longer_leave_literal_backticks(self):
        for source in ("@", "<", ">"):
            raw, normalized = translate_and_normalize(source)
            self.assertIn(BACKTICK, raw)
            self.assertNotIn(BACKTICK, normalized)

    def test_source_backtick_is_passed_unchanged_before_translation(self):
        source = BACKTICK
        with patch.object(louis, "translateString", return_value=".*") as translate:
            raw = louis.translateString([TABLE], source)
        translate.assert_called_once_with([TABLE], source)
        self.assertEqual(raw, ".*")
        self.assertEqual(ascii_to_unicode_braille(raw), "\u2828\u2821")

    def test_existing_ascii_braille_conversions_remain_unchanged(self):
        expected = {"a": "\u2801", "b": "\u2803", "1": "\u2802", "?": "\u2839", "#": "\u283c"}
        for ascii_cell, unicode_cell in expected.items():
            self.assertEqual(ascii_to_unicode_braille(ascii_cell), unicode_cell)

    def test_normalized_liblouis_expected_output_is_braille_or_whitespace(self):
        for source in ("<", ">", "@", "$", "&", "<trade>", "test@example.com"):
            _, normalized = translate_and_normalize(source)
            self.assertTrue(all(c.isspace() or 0x2800 <= ord(c) <= 0x28FF for c in normalized))


if __name__ == "__main__":
    unittest.main()
