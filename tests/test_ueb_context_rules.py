import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from braille_app.diff_engine import DiffEngine


def test_grade_one_reports_unspaced_equals_without_document_specific_rules():
    result = DiffEngine(grade=1).compare([{"text": 'a"7b'}], 'a"7b')
    assert [item["type"] for item in result["diffs"]] == ["comparison_sign_spacing"]


def test_grade_one_accepts_standalone_equals_and_apostrophes_inside_words():
    result = DiffEngine(grade=1).compare([{"text": '"7 didn\'t'}], '"7 didn\'t')
    assert result["diffs"] == []


def test_grade_one_reports_a_single_quote_pair_as_directional_quotes():
    result = DiffEngine(grade=1).compare([{"text": "',word'"}], "',word'")
    assert [item["type"] for item in result["diffs"]] == ["single_quote_direction"]


def test_isolated_ambiguous_punctuation_is_not_a_translation_error():
    engine = DiffEngine(grade=1)
    expected = engine._to_unicode_braille(",7")
    actual = engine._to_unicode_braille("0")
    assert engine._is_ambiguous_standalone_punctuation(expected, actual)


def test_duxbury_brace_terminator_variant_is_not_reported_as_an_error():
    result = DiffEngine(grade=1).compare([{"text": "_<xyz_>,'"}], "_<xyz,'_>")
    assert result["diffs"] == []
