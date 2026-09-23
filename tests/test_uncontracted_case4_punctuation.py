"""Focused checks for the English uncontracted core-punctuation slice."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from braille_app.translation.expected_document import generate_expected_braille
from braille_app.translation.liblouis_translator import LiblouisTranslator
from braille_app.translation.profiles import UNCONTRACTED_UEB_CASE4
from braille_app.translation.source_normalization import (
    UnsupportedSourceError,
    normalize_uncontracted_case4,
)
from braille_app.translation.uncontracted_case4 import translate_source
from braille_app.validation.api import validate_document
from braille_app.validation.pdf_annotation_adapter import (
    build_provenance_alignment,
    validation_errors_to_legacy_cell_issues,
)
from braille_app.visual_annotations import visual_issues_from_cell_issues


def _master(source: str) -> dict:
    return {"pages": [{"print_page_number": 1, "blocks": [{"text": source}]}]}


class UncontractedCase4PunctuationTests(unittest.TestCase):
    def setUp(self):
        self.translator = LiblouisTranslator(UNCONTRACTED_UEB_CASE4)

    def test_authoritative_core_punctuation_cells_and_grade1_contexts(self):
        cases = {
            "Hello, world.": "⠠⠓⠑⠇⠇⠕⠂⠀⠺⠕⠗⠇⠙⠲",
            "The list: red; green.": "⠠⠞⠓⠑⠀⠇⠊⠎⠞⠒⠀⠗⠑⠙⠆⠀⠛⠗⠑⠑⠝⠲",
            "Stop!": "⠠⠎⠞⠕⠏⠖",
            "What?": "⠠⠺⠓⠁⠞⠦",
            "a,b": "⠁⠰⠂⠃",
            "a;b": "⠁⠰⠆⠃",
            "a:b": "⠁⠰⠒⠃",
            "a!b": "⠁⠰⠖⠃",
            "a?b": "⠁⠰⠦⠃",
            "10:30-?": "⠼⠁⠚⠒⠼⠉⠚⠤⠰⠦",
            "3-D": "⠼⠉⠤⠰⠠⠙",
            "Hello,   world.": "⠠⠓⠑⠇⠇⠕⠂⠀⠺⠕⠗⠇⠙⠲",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(translate_source(source, self.translator), expected)

    def test_question_mark_indicator_neighbors(self):
        direct = {"What?": "⠠⠺⠓⠁⠞⠦", "? x": "⠰⠦⠀⠭", "10:30?": "⠼⠁⠚⠒⠼⠉⠚⠦"}
        for source, expected in direct.items():
            with self.subTest(source=source):
                self.assertEqual(translate_source(source, self.translator), expected)

    def test_out_of_scope_constructs_fail_closed(self):
        for source in ("well-known", "‘Hello’", "it's", "(Hello)", "Hello %", "x-?"):
            with self.subTest(source=source):
                with self.assertRaises(UnsupportedSourceError):
                    normalize_uncontracted_case4(source)
                result = validate_document(
                    _master(source), "", profile=UNCONTRACTED_UEB_CASE4
                )
                self.assertEqual(result.errors, ())
                self.assertEqual(len(result.reviews), 1)

    def test_clean_and_corrupted_validation(self):
        source = "Hello, world. The list: red; green. What? Stop!"
        expected = generate_expected_braille(_master(source), UNCONTRACTED_UEB_CASE4)
        clean = validate_document(_master(source), expected.flatten(), profile=UNCONTRACTED_UEB_CASE4)
        self.assertEqual(clean.errors, ())
        self.assertEqual(clean.reviews, ())

        corrupted = expected.flatten().replace("⠂", "⠲", 1)
        result = validate_document(_master(source), corrupted, profile=UNCONTRACTED_UEB_CASE4)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.reviews, ())

    def test_extra_punctuation_cell_is_owned_by_case4_scope(self):
        master = _master("Hello, world.")
        expected = generate_expected_braille(master, UNCONTRACTED_UEB_CASE4).flatten()
        result = validate_document(master, "⠂" + expected, profile=UNCONTRACTED_UEB_CASE4)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.reviews, ())

    def test_pdf_punctuation_deletion_uses_existing_next_cell_anchor(self):
        master = _master("Hello, world.")
        expected = generate_expected_braille(master, UNCONTRACTED_UEB_CASE4).flatten()
        deleted_index = expected.index("⠂")
        actual = expected[:deleted_index] + expected[deleted_index + 1:]
        font_path = Path(r"C:\Windows\Fonts\seguisym.ttf")
        font_name = "Case4FocusedCells"
        if font_name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(font_name, str(font_path)))

        with tempfile.TemporaryDirectory() as temporary:
            pdf_path = Path(temporary) / "case4_deleted_comma.pdf"
            canvas = Canvas(str(pdf_path), pagesize=letter)
            canvas.setFont(font_name, 14)
            canvas.drawString(50, 720, actual)
            canvas.save()

            result = validate_document(
                master,
                pdf_path,
                retain_pdf_provenance=True,
                profile=UNCONTRACTED_UEB_CASE4.name,
            )
            self.assertEqual(len(result.errors), 1)
            provenance = build_provenance_alignment(result.pdf_input)
            issues = validation_errors_to_legacy_cell_issues(result, provenance)

        self.assertEqual(len(issues), 1)
        self.assertEqual(len(issues[0]["provenance_cells"]), 1)
        anchor = issues[0]["provenance_cells"][0]
        expected_anchor = next(cell for cell in actual[deleted_index:] if cell != "⠀")
        self.assertEqual(anchor["source_char"], expected_anchor)
        visuals = visual_issues_from_cell_issues(issues)
        self.assertEqual(len(visuals), 1)
        self.assertEqual(len(visuals[0].boxes), 1)
        box = visuals[0].boxes[0]
        self.assertEqual(box.page, anchor["page"])
        for key in ("x0", "x1", "top", "bottom"):
            self.assertAlmostEqual(getattr(box, key), anchor[key], places=2)


if __name__ == "__main__":
    unittest.main()
