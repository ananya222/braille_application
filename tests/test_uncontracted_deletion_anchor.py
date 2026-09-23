"""Case-2 deletion uses the existing next-surviving-cell box convention."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from braille_app.input_reader import PdfCellProvenance
from braille_app.translation.braille_cells import cells_to_unicode, unicode_to_cells
from braille_app.translation.expected_document import generate_expected_braille
from braille_app.validation.api import ValidationIssue, ValidationResult
from braille_app.validation.api import validate_document
from braille_app.validation.pdf_annotation_adapter import (
    ProvenanceAlignment, ProvenancePage, validation_errors_to_legacy_cell_issues,
)
from braille_app.visual_annotations import group_provenance_boxes, visual_issues_from_cell_issues


class DeletionAnchorTests(unittest.TestCase):
    def test_adjacent_pdf_cells_merge_despite_rounding_jitter(self):
        boxes = group_provenance_boxes((
            {"page": 1, "x0": 130.0078161, "x1": 136.78857810000002, "top": 20.0, "bottom": 30.0},
            {"page": 1, "x0": 136.7885781, "x1": 143.5693401, "top": 20.0, "bottom": 30.0},
        ))
        self.assertEqual(len(boxes), 1)
        self.assertEqual((boxes[0].x0, boxes[0].x1), (130.0078161, 143.5693401))

    def test_deleted_letter_and_capital_indicator_anchor_to_next_cell(self):
        next_cell = PdfCellProvenance(1, 12.0, 18.0, 20.0, 30.0, "b", "⠃", "Braille", None)
        alignment = ProvenanceAlignment((ProvenancePage(1, (3,), (next_cell,)),), 1, 1, 0, 0)
        for expected, rule_id in (((1,), "UEB_CASE2_SCOPE"), ((32,), "UEB_8")):
            with self.subTest(expected=expected, rule_id=rule_id):
                issue = ValidationIssue(
                    issue_id="delete", status="ERROR", category="BRAILLE_MISMATCH",
                    rule_id=rule_id, source_document="", source_rule="",
                    source_page="1", source_page_number=1, braille_page=1,
                    actual_page_number=1, actual_cell_start=0, actual_cell_end=0,
                    actual_braille=(), expected_braille=expected,
                    rule_ids_considered=("UEB_8", "UEB_CASE2_SCOPE"),
                )
                result = ValidationResult((issue,), (), (), {}, {})
                cells = validation_errors_to_legacy_cell_issues(result, alignment)[0]["provenance_cells"]
                self.assertEqual(len(cells), 1)
                self.assertEqual((cells[0]["x0"], cells[0]["x1"]), (12.0, 18.0))

    def test_indicator_letter_swap_has_one_logical_issue_two_provenance_cells(self):
        master = {"pages": [{"print_page_number": 1, "blocks": [{"text": "Hello"}]}]}
        expected = list(unicode_to_cells(generate_expected_braille(master, "uncontracted_case2_capitalization").flatten()))
        actual = expected.copy()
        actual[:2] = actual[1], actual[0]
        result = validate_document(master, cells_to_unicode(actual), profile="uncontracted_case2_capitalization")
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].span["expected_end"] - result.errors[0].span["expected_start"], 2)
        provenance_cells = tuple(
            PdfCellProvenance(1, float(i * 8), float(i * 8 + 6), 20.0, 30.0,
                              chr(65 + i), cells_to_unicode((cell,)), "Braille", None)
            for i, cell in enumerate(actual)
        )
        alignment = ProvenanceAlignment((ProvenancePage(1, tuple(actual), provenance_cells),),
                                        len(actual), len(actual), 0, 0)
        cell_issues = validation_errors_to_legacy_cell_issues(result, alignment)
        self.assertEqual(len(cell_issues[0]["provenance_cells"]), 2)
        boxes = visual_issues_from_cell_issues(cell_issues)[0].boxes
        self.assertEqual(len(boxes), 1)
        self.assertEqual((boxes[0].x0, boxes[0].x1), (0.0, 14.0))

    def test_terminal_gap_uses_previous_cell_on_same_line(self):
        previous = PdfCellProvenance(1, 12.0, 18.0, 20.0, 30.0, "r", "⠗", "Braille", None)
        footer = PdfCellProvenance(1, 80.0, 86.0, 60.0, 70.0, "#", "⠼", "Braille", None)
        alignment = ProvenanceAlignment((ProvenancePage(1, (23, 0, 60), (previous, footer)),), 3, 2, 0, 0)
        issue = ValidationIssue(
            issue_id="terminal", status="ERROR", category="BRAILLE_MISMATCH",
            rule_id="UEB_CASE2_SCOPE", source_document="", source_rule="",
            source_page="1", source_page_number=1, braille_page=1,
            actual_page_number=1, actual_cell_start=1, actual_cell_end=1,
            actual_braille=(), expected_braille=(23,),
            rule_ids_considered=("UEB_CASE2_SCOPE",),
        )
        result = ValidationResult((issue,), (), (), {}, {})
        cells = validation_errors_to_legacy_cell_issues(result, alignment)[0]["provenance_cells"]
        self.assertEqual([cell["source_char"] for cell in cells], ["r"])

    def test_gap_does_not_anchor_to_duxbury_control_pair(self):
        cells = (
            PdfCellProvenance(1, 12.0, 18.0, 20.0, 30.0, "z", "⠵", "Braille", None),
            PdfCellProvenance(1, 20.0, 26.0, 20.0, 30.0, "^", "⠘", "Braille", None),
            PdfCellProvenance(1, 28.0, 34.0, 20.0, 30.0, "'", "⠄", "Braille", None),
        )
        alignment = ProvenanceAlignment((ProvenancePage(1, (53, 24, 4), cells),), 3, 3, 0, 0)
        issue = ValidationIssue(
            issue_id="control", status="ERROR", category="BRAILLE_MISMATCH",
            rule_id="UEB_8", source_document="", source_rule="",
            source_page="1", source_page_number=1, braille_page=1,
            actual_page_number=1, actual_cell_start=1, actual_cell_end=1,
            actual_braille=(), expected_braille=(53,),
            rule_ids_considered=("UEB_8", "UEB_CASE2_SCOPE"),
        )
        result = ValidationResult((issue,), (), (), {}, {})
        actual = validation_errors_to_legacy_cell_issues(result, alignment)[0]["provenance_cells"]
        self.assertEqual([cell["source_char"] for cell in actual], ["z"])


if __name__ == "__main__":
    unittest.main()
