"""Independent audit equivalence never broadens production matching."""

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "stress_test/final_case1_case2_alphabet_capitalization/scripts"))

from evaluate_frozen_diverse import complete_deletion_group, identical_run, identical_insertion_candidate, identical_deletion_candidate
from braille_app.visual_annotations import VisualBox


class DiverseEquivalencePolicyTests(unittest.TestCase):
    def test_deletion_equivalence_requires_same_intact_run_and_line(self):
        row = {"page": 1, "expected_index": 1}
        expected = (1, 7, 7, 17)
        candidate = SimpleNamespace(source_page_number=1, expected_braille=(7,), actual_braille=(),
                                    span={"expected_start": 2, "expected_end": 3})
        chars = [{"page": 1, "text": text, "x0": i * 8, "x1": i * 8 + 6, "top": 20, "bottom": 30}
                 for i, text in enumerate("ale")]
        box = VisualBox(1, 16, 20, 22, 30)
        proof = identical_deletion_candidate(candidate, row, expected, (0, 4), chars, [1], [chars[2]], [box])
        self.assertEqual(proof["allowed_anchor_pdf_indices"], [1, 2])
        for targets, span in (([0], (0, 4)), ([1], (0, 2))):
            self.assertIsNone(identical_deletion_candidate(candidate, row, expected, span, chars, targets, [chars[2]], [box]))
        next_line = [*chars[:2], {**chars[2], "top": 40, "bottom": 50}]
        self.assertIsNone(identical_deletion_candidate(candidate, row, expected, (0, 4), next_line, [1],
                                                      [next_line[2]], [VisualBox(1, 16, 40, 22, 50)]))
        self.assertIsNone(identical_deletion_candidate(candidate, row, (1, 7, 7, 7), (0, 4), chars, [1], [chars[2]], [box]))
        self.assertIsNone(identical_deletion_candidate(candidate, row, expected, (0, 4), chars, [1],
                                                      [chars[2]], [VisualBox(1, 17, 20, 23, 30)]))

    def test_inserted_capital_mask_is_not_original_neighbor_mask(self):
        row = {"page": 1, "expected_index": 2, "actual_mask": 15, "code_target": ","}
        candidate = SimpleNamespace(source_page_number=1, expected_braille=(), actual_braille=(32,),
                                    span={"expected_start": 1})
        chars = [{"page": 1, "text": ",", "x0": x, "x1": x + 6, "top": 20, "bottom": 30}
                 for x in (10, 18)]
        box = VisualBox(1, 10, 20, 16, 30)
        self.assertTrue(identical_insertion_candidate(candidate, row, chars, [chars[0]], [box]))
        for field, value in (("source_page_number", 2), ("actual_braille", (15,)),
                             ("span", {"expected_start": 50})):
            invalid = SimpleNamespace(**{**vars(candidate), field: value})
            self.assertFalse(identical_insertion_candidate(invalid, row, chars, [chars[0]], [box]))
        neighbor = {**chars[0], "x0": 26, "x1": 32, "text": "p"}
        self.assertFalse(identical_insertion_candidate(candidate, row, chars, [neighbor], [VisualBox(1, 26, 20, 32, 30)]))
        self.assertFalse(identical_insertion_candidate(candidate, row, chars, [chars[0]], [VisualBox(1, 11, 20, 17, 30)]))

    def test_identical_insertion_equivalence_stops_at_neighbor_and_line(self):
        chars = [
            {"text": text, "top": top, "x0": float(i * 8), "x1": float(i * 8 + 6)}
            for i, (text, top) in enumerate((
                ("e", 20), ("l", 20), ("l", 20), ("l", 20), ("o", 20), ("l", 40)
            ))
        ]
        self.assertEqual(identical_run(chars, 2), (1, 2, 3))

    def test_grouped_deletion_requires_complete_contiguous_coverage(self):
        rows = [
            {"page": 1, "expected_index": 10, "operation": "deletion"},
            {"page": 1, "expected_index": 11, "operation": "deletion"},
        ]
        self.assertTrue(complete_deletion_group(rows, 1, 10, 12))
        self.assertFalse(complete_deletion_group(rows, 1, 10, 13))
        self.assertFalse(complete_deletion_group(rows, 2, 10, 12))


if __name__ == "__main__":
    unittest.main()
