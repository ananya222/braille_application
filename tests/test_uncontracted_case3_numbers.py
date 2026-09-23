"""Deterministic Case 3 number tests against the vendored UEB Grade 1 table."""

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

from braille_app.translation.braille_cells import (
    BRF_DOTS,
    cells_to_unicode,
    char_mask,
    unicode_to_cells,
)
from braille_app.translation.expected_document import generate_expected_braille
from braille_app.translation.liblouis_translator import LiblouisTranslator, vendored_metadata
from braille_app.translation.profiles import UNCONTRACTED_UEB_CASE3
from braille_app.translation.source_normalization import (
    UnsupportedSourceError,
    normalize_uncontracted_case3,
)
from braille_app.translation.uncontracted_case3 import translate_source
from braille_app.validation.api import validate_document
from braille_app.validation.pdf_annotation_adapter import (
    build_provenance_alignment,
    validation_errors_to_legacy_cell_issues,
)
from braille_app.validation.validator import _align_case3_physical_pages


def _master(source: str) -> dict:
    return {"pages": [{"print_page_number": 1, "blocks": [{"text": source}]}]}


def _brf(cells: tuple[int, ...]) -> str:
    reverse = {char_mask(char, "duxbury"): char for char in BRF_DOTS if char != " "}
    return "".join(" " if cell == 0 else reverse[cell] for cell in cells)


def _corrupt_cell(value: str, index: int = 0) -> str:
    cells = list(unicode_to_cells(value))
    cells[index] ^= 1
    return cells_to_unicode(cells)


class UncontractedCase3NumberTests(unittest.TestCase):
    def setUp(self):
        self.translator = LiblouisTranslator(UNCONTRACTED_UEB_CASE3)

    def test_cited_numeric_space_and_hyphen_suffix_outputs(self):
        expected = {
            "4 500 000": "⠼⠙⠐⠑⠚⠚⠐⠚⠚⠚",
            "3 245 000": "⠼⠉⠐⠃⠙⠑⠐⠚⠚⠚",
            "3-D": "⠼⠉⠤⠰⠠⠙",
            "4-m": "⠼⠙⠤⠰⠍",
            "6-CD": "⠼⠋⠤⠰⠠⠠⠉⠙",
            "20-yr": "⠼⠃⠚⠤⠰⠽⠗",
            "20yr": "⠼⠃⠚⠽⠗",
            "3-dimensional": "⠼⠉⠤⠙⠊⠍⠑⠝⠎⠊⠕⠝⠁⠇",
            "3b": "⠼⠉⠰⠃",
            "3B": "⠼⠉⠠⠃",
            "4.b": "⠼⠙⠲⠰⠃",
            "4.B": "⠼⠙⠲⠠⠃",
            "date 1947 08 31": "⠙⠁⠞⠑⠀⠼⠁⠊⠙⠛⠐⠚⠓⠐⠉⠁",
            "time 16 00": "⠞⠊⠍⠑⠀⠼⠁⠋⠐⠚⠚",
            "ISBN 978 1 55468 513 4": "⠠⠠⠊⠎⠃⠝⠀⠼⠊⠛⠓⠐⠁⠐⠑⠑⠙⠋⠓⠐⠑⠁⠉⠐⠙",
            "phone 61 3 1234 5678": "⠏⠓⠕⠝⠑⠀⠼⠋⠁⠐⠉⠐⠁⠃⠉⠙⠐⠑⠋⠛⠓",
        }
        for source, cells in expected.items():
            with self.subTest(source=source):
                self.assertEqual(translate_source(source, self.translator), cells)

    def test_direct_liblouis_cases_and_nontrigger_neighbors_remain_unchanged(self):
        direct = (
            "0123456789", "3,500", "8.93", ".7", ",7", "3k", "4.m",
            "9-10", "1st 2nd", "4 5", "6-can pack", "4-bed ward", "No. 4",
        )
        for source in direct:
            with self.subTest(source=source):
                self.assertEqual(
                    translate_source(source, self.translator),
                    self.translator.translate_prose(source),
                )

    def test_single_multi_long_and_repeated_digits(self):
        self.assertEqual(translate_source("0", self.translator), "⠼⠚")
        self.assertEqual(
            translate_source("1234567890", self.translator),
            "⠼⠁⠃⠉⠙⠑⠋⠛⠓⠊⠚",
        )
        self.assertEqual(
            translate_source("00000000000000000000", self.translator),
            "⠼" + "⠚" * 20,
        )
        self.assertEqual(
            translate_source("77 777 77", self.translator),
            self.translator.translate_prose("77 777 77"),
        )

    def test_numeric_indicator_missing_extra_wrong_and_repeated(self):
        master = _master("Read 1234 values.")
        expected = generate_expected_braille(master, UNCONTRACTED_UEB_CASE3).flatten()
        prefix = expected.index("⠼")
        mutations = {
            "missing": lambda cells: cells.pop(prefix),
            "extra": lambda cells: cells.insert(prefix + 2, ord("⠼") - 0x2800),
            "wrong": lambda cells: cells.__setitem__(prefix, ord("⠰") - 0x2800),
            "repeated": lambda cells: cells.insert(prefix + 1, ord("⠼") - 0x2800),
        }
        for name, mutate in mutations.items():
            with self.subTest(kind=name):
                cells = list(unicode_to_cells(expected))
                mutate(cells)
                result = validate_document(
                    master, cells_to_unicode(cells), profile=UNCONTRACTED_UEB_CASE3
                )
                self.assertEqual(len(result.errors), 1)
                self.assertEqual(result.reviews, ())

    def test_mode_termination_and_numeric_transitions(self):
        direct = {
            "9-10": "⠼⠊⠤⠼⠁⠚",
            "9–10": "⠼⠊⠠⠤⠼⠁⠚",
            "3b": "⠼⠉⠰⠃",
            "3B": "⠼⠉⠠⠃",
            "3k": "⠼⠉⠅",
            "4.b": "⠼⠙⠲⠰⠃",
            "4.B": "⠼⠙⠲⠠⠃",
            "4.m": "⠼⠙⠲⠍",
        }
        for source, cells in direct.items():
            with self.subTest(source=source):
                self.assertEqual(translate_source(source, self.translator), cells)

    def test_paragraph_line_and_physical_page_boundaries(self):
        master = {"pages": [{"print_page_number": 1, "blocks": [
            {"text": "The first log contains 123 readings."},
            {"text": "The next log contains 456 readings."},
        ]}]}
        expected = generate_expected_braille(master, UNCONTRACTED_UEB_CASE3).flatten()
        self.assertEqual(validate_document(
            master, expected, profile=UNCONTRACTED_UEB_CASE3
        ).errors, ())

        source = _master("The sample is 3-D and has 4 500 000 cells.")
        expected = generate_expected_braille(source, UNCONTRACTED_UEB_CASE3).flatten()
        split = expected.index("⠼", expected.index("⠰"))
        split = expected.rfind("⠀", 0, split)
        self.assertGreater(split, 0)
        line_wrapped = expected[:split] + "\n" + expected[split + 1:]
        self.assertEqual(validate_document(
            source, line_wrapped, profile=UNCONTRACTED_UEB_CASE3
        ).errors, ())

        page_split = expected[:split] + "\f" + expected[split + 1:]
        paginated = validate_document(
            source, page_split, profile=UNCONTRACTED_UEB_CASE3
        )
        self.assertEqual(paginated.errors, ())
        self.assertEqual(paginated.reviews, ())

    def test_page_regions_recover_after_indels_without_jumping_to_repeated_page(self):
        def repeated_page(first_cell: int) -> tuple[int, ...]:
            return tuple(
                cell
                for group in range(40)
                for cell in (first_cell, first_cell + 1, first_cell + 2, first_cell + 3, 0)
            )

        first = repeated_page(1)
        middle = repeated_page(21)
        last = first  # Deliberately repeated content on a later physical page.
        expected = first + (0,) + middle + (0,) + last

        # One insertion on page 1 and one deletion on page 2 have zero net drift
        # by page 3.  The local sequence matcher must recover at each page anchor.
        actual_pages = (
            first[:100] + (31,) + first[100:],
            middle[:101] + middle[102:],
            last[:100] + (last[101], last[100]) + last[102:],
        )
        actual_offsets = (
            0,
            len(actual_pages[0]) + 1,
            len(actual_pages[0]) + len(actual_pages[1]) + 2,
        )

        opcodes = _align_case3_physical_pages(expected, actual_pages, actual_offsets)
        self.assertIsNotNone(opcodes)
        self.assertTrue(any(op.tag == "insert" for op in opcodes))
        self.assertTrue(any(op.tag == "delete" for op in opcodes))
        self.assertTrue(any(
            op.tag == "replace"
            and op.expected_end - op.expected_start == 2
            and op.actual_end - op.actual_start == 2
            for op in opcodes
        ))

        page3_expected_start = len(first) + 1 + len(middle) + 1
        target = page3_expected_start + 150
        mapped = next(
            op.actual_start + target - op.expected_start
            for op in opcodes
            if op.tag == "equal" and op.expected_start <= target < op.expected_end
        )
        self.assertEqual(mapped, target)

    def test_page_boundary_uses_local_content_when_later_page_is_shorter(self):
        first = tuple(range(1, 41))
        second = tuple(cell for value in range(20) for cell in (21 + value % 35, 0))
        expected = first + (0,) + second
        actual_pages = (first, second[:24])
        offsets = (0, len(first) + 1)

        aligned = _align_case3_physical_pages(expected, actual_pages, offsets)
        self.assertIsNotNone(aligned)
        self.assertFalse(any(
            op.tag != "equal" and op.expected_start < len(first) + 10
            for op in aligned
        ))
        self.assertTrue(any(
            op.tag == "equal" and op.expected_start <= len(first) + 1
            and op.expected_end >= len(first) + 9
            and op.actual_start == len(first) + 1
            for op in aligned
        ))

    def test_repeated_numeric_context_clean_and_second_occurrence_corruption(self):
        source = "The first reading is 8.93 and the later reading is 8.93."
        master = _master(source)
        expected = generate_expected_braille(master, UNCONTRACTED_UEB_CASE3).flatten()
        clean = validate_document(master, expected, profile=UNCONTRACTED_UEB_CASE3)
        self.assertEqual(clean.errors, ())
        second_decimal = expected.rfind("⠲")
        corrupted = validate_document(
            master,
            _corrupt_cell(expected, second_decimal),
            profile=UNCONTRACTED_UEB_CASE3,
        )
        self.assertEqual(len(corrupted.errors), 1)
        self.assertEqual(corrupted.reviews, ())

    def test_clean_corrupt_and_brf_near_neighbor_by_family(self):
        cases = {
            "digits": ("The room has 123 seats.", 14),
            "decimal punctuation": ("The reading is 8.93 today.", 8),
            "comma punctuation": ("The batch contains 3,500 parts.", 8),
            "numeric space": ("Population reached 3 245 000 today.", 16),
            "letters after digits": ("Use 3b or 3B for the listed size.", 9),
            "capitalized numeric suffix": ("Hello from the 3-D model.", 11),
            "lowercase numeric suffix": ("Choose a 4-m shelf.", 9),
            "capitalized abbreviation": ("Store this in a 6-CD case.", 11),
            "numeric termination": ("Read 9-10 pages today.", 9),
            "ordinary word after hyphen": ("The 3-dimensional model is ready.", 9),
        }
        for family, (source, target) in cases.items():
            with self.subTest(family=family):
                expected = generate_expected_braille(_master(source), UNCONTRACTED_UEB_CASE3).flatten()
                clean = validate_document(_master(source), expected, profile=UNCONTRACTED_UEB_CASE3)
                self.assertEqual(clean.errors, ())
                self.assertEqual(clean.reviews, ())

                corrupted = validate_document(
                    _master(source), _corrupt_cell(expected, target), profile=UNCONTRACTED_UEB_CASE3
                )
                self.assertEqual(len(corrupted.errors), 1)
                self.assertEqual(corrupted.reviews, ())

                equivalent_brf = validate_document(
                    _master(source), _brf(unicode_to_cells(expected)), profile=UNCONTRACTED_UEB_CASE3
                )
                self.assertEqual(equivalent_brf.errors, ())
                self.assertEqual(equivalent_brf.reviews, ())

    def test_numeric_context_is_translated_once_and_capital_sites_survive_overrides(self):
        source = "The 3-D model uses 4 500 000 units."
        document = generate_expected_braille(_master(source), UNCONTRACTED_UEB_CASE3)
        block = document.blocks[0]
        self.assertIn("⠼⠉⠤⠰⠠⠙", block.braille)
        self.assertIn("⠼⠙⠐⠑⠚⠚⠐⠚⠚⠚", block.braille)
        self.assertTrue(block.capital_sites)
        self.assertEqual(block.rule_status, "PASS")

    def test_extra_numeric_cell_is_a_confirmed_error_not_an_ignored_insertion(self):
        source = "The 3-D model is ready."
        master = _master(source)
        expected = generate_expected_braille(master, UNCONTRACTED_UEB_CASE3).flatten()
        cells = list(unicode_to_cells(expected))
        cells.insert(expected.index("⠙"), char_mask("a"))

        result = validate_document(
            master, cells_to_unicode(cells), profile=UNCONTRACTED_UEB_CASE3
        )

        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.reviews, ())
        self.assertEqual(result.statistics["ignored_unmapped_insertions"], 0)

    def test_extra_numeric_indicator_is_not_hidden_as_manual_review(self):
        master = _master("Value 1234.")
        expected = generate_expected_braille(master, UNCONTRACTED_UEB_CASE3).flatten()
        cells = list(unicode_to_cells(expected))
        numeric_start = expected.index("⠼")
        cells.insert(numeric_start + 3, ord("⠼") - 0x2800)

        result = validate_document(
            master, cells_to_unicode(cells), profile=UNCONTRACTED_UEB_CASE3
        )

        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.reviews, ())

    def test_pdf_deletion_uses_existing_same_line_anchor_policy(self):
        master = _master("3-D")
        expected = generate_expected_braille(master, UNCONTRACTED_UEB_CASE3).flatten()
        actual = expected[1:]
        font_path = Path(r"C:\Windows\Fonts\seguisym.ttf")
        font_name = "Case3FocusedCells"
        if font_name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(font_name, str(font_path)))

        with tempfile.TemporaryDirectory() as temporary:
            pdf_path = Path(temporary) / "case3_deleted_numeric_indicator.pdf"
            canvas = Canvas(str(pdf_path), pagesize=letter)
            canvas.setFont(font_name, 14)
            canvas.drawString(50, 720, actual)
            canvas.save()

            result = validate_document(
                master,
                pdf_path,
                retain_pdf_provenance=True,
                profile=UNCONTRACTED_UEB_CASE3.name,
            )
            self.assertEqual(len(result.errors), 1)
            provenance = build_provenance_alignment(result.pdf_input)
            issues = validation_errors_to_legacy_cell_issues(result, provenance)

        self.assertEqual(len(issues), 1)
        self.assertEqual(len(issues[0]["provenance_cells"]), 1)
        self.assertEqual(issues[0]["provenance_cells"][0]["page"], 1)
        self.assertIn(issues[0]["provenance_cells"][0]["source_char"], actual)

    def test_unsupported_constructs_fail_closed_as_review(self):
        for source in (
            "Date 08/31/2024", "Time 10:30", "$8.75", "(3)", "3\t4",
            "3\u00a04", "3\u20094", "3\u200b4", "3^2",
        ):
            with self.subTest(source=source):
                with self.assertRaises(UnsupportedSourceError):
                    normalize_uncontracted_case3(source)
                result = validate_document(_master(source), "", profile=UNCONTRACTED_UEB_CASE3)
                self.assertEqual(result.errors, ())
                self.assertEqual(len(result.reviews), 1)

    def test_vendored_runtime_identity(self):
        metadata = vendored_metadata(UNCONTRACTED_UEB_CASE3)
        self.assertEqual(metadata["version"], "3.38.0")
        self.assertEqual(metadata["table_list"], "unicode.dis,en-ueb-g1.ctb")
        self.assertEqual(
            metadata["table_hash_sha256"],
            "446717b55e49ff41aef2c204b58ea1d2872a77a4473a821e766bffd51cee0b4d",
        )


if __name__ == "__main__":
    unittest.main()
