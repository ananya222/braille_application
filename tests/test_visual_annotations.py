import hashlib
import glob
import os
import tempfile
import unittest

from braille_app.visual_annotations import (
    VisualBox,
    export_annotated_pdf,
    group_provenance_boxes,
    pdf_box_to_screen,
    visual_issues_from_cell_issues,
)


def _cell(page=1, x0=10, x1=20, top=30, bottom=42, value="⠁"):
    return {
        "page": page,
        "x0": x0,
        "x1": x1,
        "top": top,
        "bottom": bottom,
        "unicode_cell": value,
    }


class VisualAnnotationModelTests(unittest.TestCase):
    def test_coordinate_mapping_and_zoom_scaling(self):
        box = VisualBox(page=1, x0=10, top=20, x1=30, bottom=40)
        self.assertEqual(pdf_box_to_screen(box, 100, 100, 50, 50), (5, 10, 15, 20))
        self.assertEqual(pdf_box_to_screen(box, 100, 100, 100, 100), (10, 20, 30, 40))
        self.assertEqual(pdf_box_to_screen(box, 100, 100, 200, 200), (20, 40, 60, 80))

    def test_same_line_cells_group_but_cross_line_cells_do_not(self):
        cells = [_cell(x0=10, x1=20), _cell(x0=20.5, x1=30.5), _cell(x0=10, x1=20, top=60, bottom=72)]
        boxes = group_provenance_boxes(cells)
        self.assertEqual(len(boxes), 2)
        self.assertEqual((boxes[0].x0, boxes[0].x1), (10, 30.5))

    def test_structural_broad_issue_has_marker_not_giant_rectangle(self):
        issue = {
            "kind": "structural_review",
            "page": 8,
            "context": "broad review",
            "confidence": "low_confidence",
            "provenance_cells": [_cell(x0=i * 12, x1=i * 12 + 10) for i in range(20)],
        }
        visual = visual_issues_from_cell_issues([issue])[0]
        self.assertEqual(visual.localization, "structural")
        self.assertEqual(visual.boxes, [])
        self.assertIsNone(visual.marker)

    def test_exact_and_deletion_records_keep_localization_state(self):
        exact = {
            "kind": "replacement",
            "page": 1,
            "expected": "⠁",
            "actual": "⠃",
            "provenance_cells": [_cell()],
        }
        deletion = {
            "kind": "deletion",
            "page": 1,
            "expected": "⠁",
            "actual": "",
            "x0": 50,
            "x1": 60,
            "top": 30,
            "bottom": 42,
            "provenance_cells": [],
        }
        records = visual_issues_from_cell_issues([exact, deletion])
        self.assertEqual(records[0].localization, "exact")
        self.assertEqual(len(records[0].boxes), 1)
        self.assertEqual(records[1].localization, "partial")
        self.assertEqual(records[1].boxes, [])
        self.assertIsNone(records[1].marker)

    def test_export_creates_new_pdf_and_preserves_original(self):
        pdf_path = glob.glob(os.path.join("testfiles", "Document 1", "*.pdf"))[0]
        with open(pdf_path, "rb") as source:
            before = hashlib.sha256(source.read()).digest()
        records = visual_issues_from_cell_issues([{
            "kind": "replacement",
            "page": 1,
            "expected": "⠁",
            "actual": "⠃",
            "provenance_cells": [_cell()],
        }])
        with tempfile.TemporaryDirectory() as temp_dir:
            output = os.path.join(temp_dir, "annotated.pdf")
            self.assertEqual(export_annotated_pdf(pdf_path, output, records), output)
            self.assertTrue(os.path.exists(output))
            with open(pdf_path, "rb") as source:
                self.assertEqual(hashlib.sha256(source.read()).digest(), before)
            with open(output, "rb") as annotated:
                self.assertGreater(len(annotated.read()), 0)
            from pypdf import PdfReader
            content = PdfReader(output).pages[0].get_contents().get_data()
            self.assertIn(b"1 1 1 rg", content)
            self.assertIn(b"10.000 799.920 10.000 12.000 re S", content)


if __name__ == "__main__":
    unittest.main()
