import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from braille_app.diff_engine import DiffEngine
from braille_app.input_reader import _pdf_page_to_braille_lines


def test_matching_ueb_symbol_cells_are_not_reported_as_font_errors():
    # These are ordinary UEB punctuation/operator patterns, not proof of a
    # font fault.  A byte-for-byte/cell-for-cell match must have no findings.
    text = '"6 "7 _< _> ,0'
    result = DiffEngine(grade=1).compare([{"type": "body", "text": text}], text)

    assert result["diffs"] == []


def test_pdf_reader_uses_measured_cell_pitch_for_spacing_and_indent():
    # Word geometry represents a 16-point monospaced braille cell.  The old
    # fixed 6.6-point assumption made one-cell gaps appear as multiple cells.
    words = [
        {"text": "abc", "x0": 100.0, "x1": 148.0, "top": 20.0},
        {"text": "de", "x0": 164.0, "x1": 196.0, "top": 20.0},
        {"text": "f", "x0": 132.0, "x1": 148.0, "top": 44.0},
    ]

    assert _pdf_page_to_braille_lines(words) == ["abc de", "  f"]
