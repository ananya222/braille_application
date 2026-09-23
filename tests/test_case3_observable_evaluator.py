"""Independent physical-target and identical-run policies for Case 3."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "stress_test" / "uncontracted_case3_numbers"))

from evaluate_case3_validation import (
    _deletion_anchor,
    _identical_deletion_proof,
    _identical_insertion_proof,
)


def _char(text: str, index: int) -> dict:
    return {"text": text, "x0": index * 8.0, "x1": index * 8.0 + 6.0,
            "top": 20.0, "bottom": 30.0}


class Case3ObservableEvaluatorTests(unittest.TestCase):
    def test_deletion_anchor_skips_blank_and_falls_back_on_same_line(self):
        line = [_char(text, index) for index, text in enumerate(("⠁", "⠀", "⠠", "⠃"))]
        locations = [{"page": 1, "line": 1, "cell": index + 1} for index in range(len(line))]
        positions = {(1, 1): list(enumerate(locations))}
        row = {"mutation_id": "D1"}

        anchor, char = _deletion_anchor(row, 1, positions, [[line]], locations)
        self.assertEqual(anchor["cell"], 3)
        self.assertEqual(char["text"], "⠠")

        short_line = line[:2]
        short_locations = locations[:2]
        anchor, char = _deletion_anchor(
            row, 1, {(1, 1): list(enumerate(short_locations))}, [[short_line]], short_locations
        )
        self.assertEqual(anchor["cell"], 1)
        self.assertEqual(char["text"], "⠁")

    def test_identical_insertion_requires_same_run_provenance_and_box(self):
        line = [_char(text, index) for index, text in enumerate(("⠁", "⠠", "⠠", "⠠", "⠃"))]
        row = {"operation": "insert", "expected_start": 5, "actual_cells": "⠠",
               "actual_locations": [{"page": 1, "line": 1, "cell": 3}]}
        provenance = {"page": 1, **line[3]}
        issue = {"expected_braille": [], "actual_braille": [32], "actual_page_number": 1,
                 "span": {"expected_start": 4}, "provenance_cells": [provenance],
                 "boxes": [{"page": 1, **line[3]}]}
        self.assertIsNotNone(_identical_insertion_proof(issue, row, [[line]]))

        invalid = {**issue, "provenance_cells": [{"page": 1, **line[4]}],
                   "boxes": [{"page": 1, **line[4]}]}
        self.assertIsNone(_identical_insertion_proof(invalid, row, [[line]]))

    def test_identical_deletion_requires_one_missing_cell_and_permitted_anchor(self):
        line = [_char(text, index) for index, text in enumerate(("⠠", "⠠", "⠁"))]
        provenance = {"page": 1, **line[2]}
        issue = {"actual_braille": [], "expected_braille": [32],
                 "span": {"expected_start": 1, "expected_end": 2},
                 "provenance_cells": [provenance], "boxes": [{"page": 1, **line[2]}]}
        row = {"operation": "delete", "expected_start": 1,
               "initial_page": 1, "initial_line": 1}
        metadata = {"expected_braille": "⠠⠠⠠⠁",
                    "expected_blocks": [{"expected_start": 0, "expected_end": 4}]}
        target = [({"page": 1, "line": 1, "cell": 3}, line[2])]
        self.assertIsNotNone(_identical_deletion_proof(issue, row, metadata, [[line]], target))

        wrong_target = [({"page": 1, "line": 2, "cell": 1}, line[0])]
        self.assertIsNone(_identical_deletion_proof(issue, row, metadata, [[line]], wrong_target))

        shortened_twice = [_char("⠠", 0), _char("⠁", 1)]
        short_issue = {**issue,
                       "provenance_cells": [{"page": 1, **shortened_twice[1]}],
                       "boxes": [{"page": 1, **shortened_twice[1]}]}
        short_target = [({"page": 1, "line": 1, "cell": 2}, shortened_twice[1])]
        self.assertIsNone(_identical_deletion_proof(
            short_issue, row, metadata, [[shortened_twice]], short_target
        ))


if __name__ == "__main__":
    unittest.main()
