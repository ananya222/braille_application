"""Bounded uncontracted alignment must recover after local edits."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from braille_app.validation.alignment import align_monotonic_page_regions


def align(expected: str, actual: str):
    left = tuple(map(ord, expected))
    right = tuple(map(ord, actual))
    return align_monotonic_page_regions(
        (left,), (right,), (0,), (0,),
        expected_blocks=((left,),), actual_line_pages=((right,),),
        edit_block_alignment=True,
    )


def align_cells(expected: tuple[int, ...], actual: tuple[int, ...]):
    return align_monotonic_page_regions(
        (expected,), (actual,), (0,), (0,),
        expected_blocks=((expected,),), actual_line_pages=((actual,),),
        edit_block_alignment=True,
    )


class IndelRecoveryTests(unittest.TestCase):
    def test_paired_indels_recover_before_suffix(self):
        opcodes = align("abcdefghij", "zabcdfghij")
        self.assertEqual([(o.tag, o.expected_start, o.expected_end, o.actual_start, o.actual_end) for o in opcodes], [
            ("insert", 0, 0, 0, 1),
            ("equal", 0, 4, 1, 5),
            ("delete", 4, 5, 5, 5),
            ("equal", 5, 10, 5, 10),
        ])

    def test_repeated_run_stays_near_original_position(self):
        opcodes = align(
            "abcdefghijklmnopqrstuvwxyz abcdefghijklmnopqrstuvwxyz",
            "bcdefghikjlmnopqrztuvwxyz zabcdefghiklmnopqrtsuvwxyz",
        )
        self.assertFalse(any(o.tag in {"insert", "delete"} and max(o.expected_end-o.expected_start, o.actual_end-o.actual_start) > 3 for o in opcodes))
        self.assertTrue(any(o.tag == "equal" and o.expected_start < 26 and o.actual_start < 26 for o in opcodes))

    def test_single_indels_and_transposition_recover(self):
        for actual, tag in (("bcdef abcdef", "delete"), ("zabcdef abcdef", "insert"), ("bacdef abcdef", "replace")):
            with self.subTest(actual=actual):
                opcodes = align("abcdef abcdef", actual)
                self.assertEqual(opcodes[0].tag, tag)
                self.assertEqual(opcodes[-1].tag, "equal")
                self.assertEqual(opcodes[-1].expected_end, len("abcdef abcdef"))

    def test_indicator_transposition_next_to_insertion(self):
        expected = (21, 0, 32, 19, 17, 7, 7, 21)
        actual = (21, 0, 19, 32, 32, 17, 7, 7, 21)
        opcodes = align_cells(expected, actual)
        self.assertIn(("replace", 2, 4, 2, 4), [
            (o.tag, o.expected_start, o.expected_end, o.actual_start, o.actual_end)
            for o in opcodes
        ])
        self.assertIn(("insert", 4, 4, 4, 5), [
            (o.tag, o.expected_start, o.expected_end, o.actual_start, o.actual_end)
            for o in opcodes
        ])
        self.assertEqual(opcodes[-1].tag, "equal")
        self.assertEqual(opcodes[-1].expected_end, len(expected))

    def test_transposition_recovery_contexts(self):
        cases = (
            ("simple", "abcdef", "bacdef", 0),
            ("repeated word", "hello hello", "hello ehllo", 6),
            ("repeated alphabet", "abcdef abcdef", "abcdef bacdef", 7),
            ("near deletion", "abcdef ghij", "bacdef ghj", 0),
            ("near block end", "hello abcdef", "hello abcdfe", 10),
        )
        for name, expected, actual, start in cases:
            with self.subTest(name=name):
                opcodes = align(expected, actual)
                self.assertTrue(any(o.tag == "replace" and o.expected_start == start
                                    and o.expected_end == start + 2 for o in opcodes))
                if name != "near block end":
                    self.assertEqual(opcodes[-1].tag, "equal")
                    self.assertEqual(opcodes[-1].expected_end, len(expected))

    def test_transposition_near_page_boundary(self):
        first = tuple(map(ord, "abcdef"))
        second = tuple(map(ord, "ghijkl"))
        actual_first = tuple(map(ord, "abcdfe"))
        opcodes = align_monotonic_page_regions(
            (first, second), (actual_first, second), (0, 7), (0, 7),
            expected_blocks=((first,), (second,)),
            actual_line_pages=((actual_first,), (second,)),
            edit_block_alignment=True,
        )
        self.assertTrue(any(o.tag == "replace" and o.expected_start == 4 and o.expected_end == 6 for o in opcodes))
        self.assertTrue(any(o.tag == "equal" and o.expected_start >= 7 and o.expected_end == 13 for o in opcodes))

    def test_identical_inserted_cell_uses_first_equivalent_position(self):
        for expected, actual, index in (("address", "adddress", 1),
                                        ("success", "succcess", 2),
                                        ("HELLO", "HELLLO", 2)):
            with self.subTest(expected=expected):
                opcodes = align(expected, actual)
                self.assertTrue(any(o.tag == "insert" and o.expected_start == index
                                    and o.actual_start == index and o.actual_end == index + 1
                                    for o in opcodes))
                self.assertEqual(opcodes[-1].tag, "equal")
                self.assertEqual(opcodes[-1].expected_end, len(expected))

    def test_repeated_deletion_preserves_already_matched_prefix(self):
        for expected, actual, index in (
            (tuple(map(ord, "braille")), tuple(map(ord, "braile")), 5),
            (tuple(map(ord, "sleep")), tuple(map(ord, "slep")), 3),
            ((32, 32, 9, 1), (32, 9, 1), 1),
            ((1, 32, 32, 9), (1, 32, 9), 2),
        ):
            with self.subTest(expected=expected):
                opcodes = align_cells(expected, actual)
                self.assertTrue(any(o.tag == "delete" and o.expected_start == index
                                    and o.expected_end == index + 1 for o in opcodes))
                self.assertEqual(opcodes[-1].expected_end, len(expected))
                self.assertEqual(opcodes[-1].tag, "equal")

    def test_run_recovery_separates_deletion_from_neighbor_substitution(self):
        # The surviving run separates two observable edits and their anchors.
        # Arbitrary cells exercise exactly the same rule as indicators.
        for expected, actual in ((tuple(map(ord, "xxxyab")), tuple(map(ord, "xxzab"))),
                                 ((32, 32, 32, 29, 1, 3), (32, 32, 53, 1, 3))):
            opcodes = align_cells(expected, actual)
            self.assertEqual([(o.tag, o.expected_start, o.expected_end, o.actual_start, o.actual_end) for o in opcodes], [
                ("delete", 0, 1, 0, 0), ("equal", 1, 3, 0, 2),
                ("replace", 3, 4, 2, 3), ("equal", 4, 6, 3, 5),
            ])
            self.assertNotEqual(opcodes[0].actual_start, opcodes[2].actual_start)

    def test_deletion_continuity_unique_repeated_and_near_insertion(self):
        for expected, actual, deleted, recovery in (
            ("abcdef", "abdef", 2, 3),
            ("abbbcdef", "abbcdef", 3, 4),
            ("axybbbcdef", "zaxybbcdef", 5, 6),
        ):
            with self.subTest(actual=actual):
                opcodes = align(expected, actual)
                deletion = next(op for op in opcodes if op.tag == "delete")
                self.assertEqual((deletion.expected_start, deletion.expected_end), (deleted, deleted + 1))
                self.assertEqual(opcodes[-1].tag, "equal")
                self.assertEqual(opcodes[-1].expected_start, recovery)
                self.assertEqual(opcodes[-1].expected_end, len(expected))

    def test_repeated_block_consumes_semantic_continuation_not_footer(self):
        expected = tuple(map(ord, "notebook notebook notebook notebook notebook"))
        lines = tuple(tuple(map(ord, line)) for line in (
            "notebookynotebozk notebook yotexook", "notzyzyk", "#DD"
        ))
        actual = tuple(cell for index, line in enumerate(lines)
                       for cell in ((*line, 0) if index + 1 < len(lines) else line))
        opcodes = align_monotonic_page_regions(
            (expected,), (actual,), (0,), (0,),
            expected_blocks=((expected,),), actual_line_pages=(lines,),
            edit_block_alignment=True,
        )
        self.assertGreaterEqual(max(o.actual_end for o in opcodes), len(lines[0]) + 1 + len(lines[1]))
        self.assertLessEqual(max(o.actual_end for o in opcodes), len(actual) - len(lines[-1]) - 1)


if __name__ == "__main__":
    unittest.main()
