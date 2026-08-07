import unittest


try:
    from main_gui import build_display_errors
except ModuleNotFoundError as exc:
    if exc.name != "PySide6":
        raise
    build_display_errors = None

from braille_app.report_generator import ReportGenerator


@unittest.skipIf(build_display_errors is None, "PySide6 is unavailable")
class GuiCellIssueDisplayTests(unittest.TestCase):
    def test_normal_display_payload_uses_cell_issue_fields(self):
        issues = build_display_errors([
            {
                "kind": "replacement",
                "expected_cells": ["⠐"],
                "actual_cells": ["⠈"],
                "page": 3,
                "context": "CPI",
                "confidence": "high_confidence",
                "parent_diff_type": "word_mismatch",
            }
        ])

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["page"], 3)
        self.assertEqual(issues[0]["kind"], "replacement")
        self.assertEqual(issues[0]["expected"], "⠐")
        self.assertEqual(issues[0]["actual"], "⠈")
        self.assertEqual(issues[0]["context"], "CPI")
        self.assertEqual(issues[0]["confidence"], "high_confidence")

    def test_structural_review_is_concise_and_needs_review_remains_visible(self):
        issues = build_display_errors([
            {
                "kind": "structural_review",
                "expected_cells": ["⠠"] * 200,
                "actual_cells": ["⠈"] * 200,
                "page": 4,
                "context": "macro section",
                "confidence": "needs_review",
            }
        ])

        self.assertEqual(issues[0]["kind"], "structural_group")
        self.assertEqual(issues[0]["child_count"], 1)
        self.assertEqual(issues[0]["expected"], "")
        self.assertEqual(issues[0]["actual"], "")
        self.assertEqual(
            issues[0]["message"],
            "Exact error location could not be fully localized. Internal structural segments: 1. Child IDs: 1.",
        )
        self.assertEqual(issues[0]["confidence"], "needs_review")

    def test_report_uses_cell_issue_and_concise_structural_message(self):
        html = ReportGenerator().generate_report(
            {"pages": []},
            {
                "diffs": [{
                    "type": "structural_mismatch",
                    "confidence": "high_confidence",
                    "expected": "RAW_PARENT_RANGE",
                    "actual": "RAW_PARENT_RANGE",
                }],
                "cell_issues": [{
                    "kind": "structural_review",
                    "expected_cells": ["⠠"] * 200,
                    "actual_cells": ["⠈"] * 200,
                    "page": 4,
                    "x0": 10.0,
                    "x1": 15.0,
                    "top": 20.0,
                    "bottom": 25.0,
                    "context": "macro section",
                    "confidence": "needs_review",
                }],
            },
            {},
            1,
        )

        self.assertIn("structural mismatch - needs review", html)
        self.assertIn("Exact error location could not be fully localized.", html)
        self.assertIn("Child IDs: 1", html)
        self.assertIn("macro section", html)
        self.assertNotIn("RAW_PARENT_RANGE", html)


if __name__ == "__main__":
    unittest.main()
