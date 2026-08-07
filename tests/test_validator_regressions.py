import os
import sys
import glob

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from braille_app.diff_engine import DiffEngine
from braille_app.input_reader import _pdf_page_to_braille_lines, PdfCellProvenance
from braille_app.input_reader import read_braille_pdf_with_provenance
from braille_app.brf_parser import BRFParser
from braille_app.doc_extractor import DocumentExtractor
from braille_app.provenance_resolver import resolve_mismatch_provenance
from braille_app.provenance_resolver import localize_diff_records
from braille_app.report_generator import ReportGenerator


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


def test_unverified_symbol_does_not_suppress_neighboring_difference():
    engine = DiffEngine()
    result = engine.compare(
        [{"type": "body", "text": r"\X1234 " + "\u2801"}],
        "\u2802 \u2803",
    )

    assert result["diffs"]
    assert all(d["confidence"] != "ignored" for d in result["diffs"])
    assert any(d["actual_start_idx"] == 0 and d["actual_end_idx"] == 2 for d in result["diffs"])


def test_unverified_symbol_only_difference_remains_reviewable():
    engine = DiffEngine()
    diff_type, confidence, _ = engine._classify_mismatch(
        r"\X1234", "\u2801", "replace", 1, 1
    )

    assert diff_type == "unverified_symbol_mapping"
    assert confidence == "needs_review"


def test_non_equal_replacement_range_is_not_dropped_for_symbol_uncertainty():
    engine = DiffEngine()
    result = engine.compare(
        [{"type": "body", "text": r"\X1234 " + "\u2801"}],
        "\u2802 \u2803",
    )

    ranges = {(d["actual_start_idx"], d["actual_end_idx"]) for d in result["diffs"]}
    assert (0, 2) in ranges


def _prov(source, cell, x):
    return PdfCellProvenance(1, x, x + 5, 10, 15, source, cell, "font", None)


def test_structural_provenance_returns_complete_actual_range():
    words = [[_prov("a", "\u2801", 10)], [_prov("b", "\u2803", 20)]]
    record = {
        "type": "structural_mismatch",
        "expected": "\u2801 \u2803",
        "actual": "\u2801 \u2803",
        "actual_start_idx": 0,
        "actual_end_idx": 2,
    }

    result = resolve_mismatch_provenance(record, words)

    assert result["kind"] == "full_range"
    assert result["cells"] == [words[0][0], words[1][0]]


def test_multi_word_replacement_uses_complete_actual_range():
    words = [[_prov("a", "\u2801", 10)], [_prov("b", "\u2803", 20)]]
    record = {
        "type": "word_mismatch",
        "expected": "\u2801 \u2803",
        "actual": "\u2802 \u2804",
        "actual_start_idx": 0,
        "actual_end_idx": 2,
    }

    result = resolve_mismatch_provenance(record, words)

    assert result["kind"] == "full_range"
    assert result["cells"] == [words[0][0], words[1][0]]


def legacy_cell_issue_replacement_omits_equal_neighbors():
    words = [[_prov("a", "⠐", 10), _prov("b", "⠣", 20), _prov("c", "⠈", 30), _prov("d", "⠈", 40), _prov("e", "⠉", 50), _prov("f", "⠏", 60), _prov("g", "⠊", 70), _prov("h", "⠈", 80), _prov("i", "⠜", 90)]]
    diff = {"type": "word_mismatch", "confidence": "high_confidence", "expected": "⠐⠣⠠⠠⠉⠏⠊⠠⠜", "actual": "⠐⠣⠈⠈⠉⠏⠊⠈⠜", "actual_start_idx": 0, "actual_end_idx": 1}
    issues = localize_diff_records([diff], words)
    assert len(issues) == 1
    assert issues[0]["expected_cells"] == ["⠠", "⠠"]
    assert issues[0]["actual_cells"] == ["⠈", "⠈"]
    assert issues[0]["context"] == "⠐⠣⠠⠠⠉⠏⠊⠠⠜"


def legacy_cell_issue_insertion_and_deletion():
    words = [[_prov("a", "⠁", 10), _prov("b", "⠃", 20)]]
    ins = {"type": "insertion", "confidence": "high_confidence", "expected": "⠁", "actual": "⠁⠃", "actual_start_idx": 0, "actual_end_idx": 1}
    dele = {"type": "deletion", "confidence": "high_confidence", "expected": "⠁⠃", "actual": "", "actual_start_idx": 0, "actual_end_idx": 0}
    assert localize_diff_records([ins], words)[0]["kind"] == "insertion"
    assert localize_diff_records([ins], words)[0]["actual_cells"] == ["⠃"]
    assert localize_diff_records([dele], words)[0]["kind"] == "deletion"
    assert localize_diff_records([dele], words)[0]["expected_cells"] == ["⠁", "⠃"]


def legacy_broad_diff_localizes_word_pairs():
    words = [[_prov("a", "⠁", 10)], [_prov("b", "⠃", 20)]]
    diff = {"type": "structural_mismatch", "confidence": "high_confidence", "expected": "⠁ ⠉", "actual": "⠁ ⠃", "actual_start_idx": 0, "actual_end_idx": 2}
    issues = localize_diff_records([diff], words)
    assert len(issues) == 1
    assert issues[0]["actual_cells"] == ["⠃"]
    assert issues[0]["parent_diff_type"] == "structural_mismatch"


def legacy_unlocalizable_broad_diff_is_structural_review():
    pass


def test_cell_issue_replacement_omits_equal_neighbors():
    c = lambda n: chr(0x2800 + n)
    words = [[_prov("a", c(0x10), 10), _prov("b", c(0x23), 20), _prov("c", c(0x08), 30), _prov("d", c(0x08), 40), _prov("e", c(0x09), 50), _prov("f", c(0x0f), 60), _prov("g", c(0x0a), 70), _prov("h", c(0x08), 80), _prov("i", c(0x1c), 90)]]
    diff = {"type": "word_mismatch", "confidence": "high_confidence", "expected": c(0x10)+c(0x23)+c(0x20)+c(0x20)+c(0x09)+c(0x0f)+c(0x0a)+c(0x20)+c(0x1c), "actual": c(0x10)+c(0x23)+c(0x08)+c(0x08)+c(0x09)+c(0x0f)+c(0x0a)+c(0x08)+c(0x1c), "actual_start_idx": 0, "actual_end_idx": 1}
    issues = localize_diff_records([diff], words)
    assert len(issues) == 2
    assert [i["expected_cells"] for i in issues] == [[c(0x20), c(0x20)], [c(0x20)]]
    assert [i["actual_cells"] for i in issues] == [[c(0x08), c(0x08)], [c(0x08)]]


def test_cell_issue_insertion_and_deletion():
    one, three = chr(0x2801), chr(0x2803)
    words = [[_prov("a", one, 10), _prov("b", three, 20)]]
    ins = {"type": "insertion", "confidence": "high_confidence", "expected": one, "actual": one+three, "actual_start_idx": 0, "actual_end_idx": 1}
    dele = {"type": "deletion", "confidence": "high_confidence", "expected": one+three, "actual": "", "actual_start_idx": 0, "actual_end_idx": 0}
    assert localize_diff_records([ins], words)[0]["kind"] == "insertion"
    assert localize_diff_records([ins], words)[0]["actual_cells"] == [three]
    assert localize_diff_records([dele], words)[0]["kind"] == "deletion"
    assert localize_diff_records([dele], words)[0]["expected_cells"] == list(one+three)


def test_broad_diff_localizes_word_pairs():
    one, three, nine = chr(0x2801), chr(0x2803), chr(0x2809)
    words = [[_prov("a", one, 10)], [_prov("b", three, 20)]]
    diff = {"type": "structural_mismatch", "confidence": "high_confidence", "expected": one+" "+nine, "actual": one+" "+three, "actual_start_idx": 0, "actual_end_idx": 2}
    issues = localize_diff_records([diff], words)
    assert len(issues) == 1
    assert issues[0]["actual_cells"] == [three]
    assert issues[0]["parent_diff_type"] == "structural_mismatch"


def test_unlocalizable_broad_diff_is_structural_review():
    one, three, nine, twentyfive = (chr(0x2801), chr(0x2803), chr(0x2809), chr(0x2819))
    words = [[_prov("a", one, 10)], [_prov("b", three, 20)]]
    diff = {"type": "structural_mismatch", "confidence": "high_confidence", "expected": one+" "+nine+" "+twentyfive, "actual": one+" "+three, "actual_start_idx": 0, "actual_end_idx": 2}
    issues = localize_diff_records([diff], words)
    assert issues
    assert all(i["kind"] == "structural_review" for i in issues)
    assert issues[0]["actual_cells"] == [three]
    assert len(issues[0]["provenance_cells"]) == 1
    assert issues[0]["actual_start_idx"] == 1
    assert issues[0]["actual_end_idx"] == 2
    assert issues[0]["reason"] == "bounded word alignment was not reliable"
    assert issues[0]["resolved_subissues"] == []
    return


def test_structural_fallback_conserves_actual_provenance():
    one, three, nine = chr(0x2801), chr(0x2803), chr(0x2809)
    words = [[_prov("a", one, 10)], [_prov("b", three, 20)], [_prov("c", nine, 30)]]
    diff = {
        "type": "structural_mismatch",
        "confidence": "needs_review",
        "expected": chr(0x2802) + " " + chr(0x2807),
        "actual": one + " " + three + " " + nine,
        "actual_start_idx": 0,
        "actual_end_idx": 3,
    }
    issues = localize_diff_records([diff], words)
    structural = [issue for issue in issues if issue["kind"] == "structural_review"]
    assert len(structural) == 1
    assert structural[0]["actual_cells"] == [one, three, nine]
    assert [cell["unicode_cell"] for cell in structural[0]["provenance_cells"]] == [one, three, nine]


def test_bounded_word_alignment_keeps_reliable_insertions_localized():
    one, three, nine = chr(0x2801), chr(0x2803), chr(0x2809)
    words = [[_prov("a", one, 10)], [_prov("b", three, 20)], [_prov("c", nine, 30)]]
    diff = {
        "type": "structural_mismatch",
        "confidence": "high_confidence",
        "expected": one + " " + nine,
        "actual": one + " " + three + " " + nine,
        "actual_start_idx": 0,
        "actual_end_idx": 3,
    }
    issues = localize_diff_records([diff], words)
    assert [issue["kind"] for issue in issues] == ["insertion"]
    assert issues[0]["actual_cells"] == [three]


def test_source_conditioned_single_capital_equivalence():
    cap, observed = chr(0x2820), chr(0x2808)
    words = [[_prov("S", observed, 10), _prov("e", chr(0x2811), 20)]]
    diff = {"type": "word_mismatch", "expected": cap + chr(0x2811),
            "actual": observed + chr(0x2811), "actual_start_idx": 0,
            "actual_end_idx": 1, "expected_start_idx": 0,
            "expected_end_idx": 1}
    assert localize_diff_records([diff], words, ["Section"]) == []


def test_source_conditioned_double_capital_equivalence():
    cap, observed = chr(0x2820), chr(0x2808)
    words = [[_prov("F", observed, 10), _prov("X", observed, 20), _prov("x", chr(0x280b), 30)]]
    diff = {"type": "word_mismatch", "expected": cap + cap + chr(0x280b),
            "actual": observed + observed + chr(0x280b), "actual_start_idx": 0,
            "actual_end_idx": 1, "expected_start_idx": 0,
            "expected_end_idx": 1}
    assert localize_diff_records([diff], words, ["FX"]) == []


def test_capitalization_equivalence_requires_capitalized_source_context():
    cap, observed = chr(0x2820), chr(0x2808)
    words = [[_prov("s", observed, 10), _prov("e", chr(0x2811), 20)]]
    diff = {"type": "word_mismatch", "expected": cap + chr(0x2811),
            "actual": observed + chr(0x2811), "actual_start_idx": 0,
            "actual_end_idx": 1, "expected_start_idx": 0,
            "expected_end_idx": 1}
    issues = localize_diff_records([diff], words, ["section"])
    assert len(issues) == 1


def test_capitalization_cells_do_not_suppress_neighboring_punctuation():
    cap, observed = chr(0x2820), chr(0x2808)
    expected = chr(0x2810) + chr(0x2823) + cap + chr(0x2811)
    actual = chr(0x2808) + chr(0x2823) + observed + chr(0x2811)
    words = [[_prov("(", actual[0], 10), _prov("E", actual[1], 20),
              _prov("d", actual[2], 30), _prov("x", actual[3], 40)]]
    diff = {"type": "word_mismatch", "expected": expected, "actual": actual,
            "actual_start_idx": 0, "actual_end_idx": 1,
            "expected_start_idx": 0, "expected_end_idx": 1}
    issues = localize_diff_records([diff], words, ["(E_d"])
    assert len(issues) == 1
    assert issues[0]["expected_cells"] == [chr(0x2810)]


def test_source_conditioned_comma_equivalence():
    comma, observed = chr(0x2802), chr(0x2801)
    words = [[_prov("w", chr(0x2813), 10), _prov(",", observed, 20)]]
    diff = {"type": "word_mismatch", "expected": chr(0x2813) + comma,
            "actual": chr(0x2813) + observed, "actual_start_idx": 0,
            "actual_end_idx": 1, "expected_start_idx": 0,
            "expected_end_idx": 1}
    assert localize_diff_records([diff], words, ["word,"]) == []


def test_comma_equivalence_requires_source_comma_context():
    comma, observed = chr(0x2802), chr(0x2801)
    words = [[_prov("w", chr(0x2813), 10), _prov("x", observed, 20)]]
    diff = {"type": "word_mismatch", "expected": chr(0x2813) + comma,
            "actual": chr(0x2813) + observed, "actual_start_idx": 0,
            "actual_end_idx": 1, "expected_start_idx": 0,
            "expected_end_idx": 1}
    issues = localize_diff_records([diff], words, ["word"])
    assert len(issues) == 1
    assert issues[0]["expected_cells"] == [comma]


def test_comma_equivalence_does_not_suppress_period_family():
    period, wrong_period = chr(0x2832), chr(0x2819)
    words = [[_prov(".", wrong_period, 10)]]
    diff = {"type": "word_mismatch", "expected": period,
            "actual": wrong_period, "actual_start_idx": 0,
            "actual_end_idx": 1, "expected_start_idx": 0,
            "expected_end_idx": 1}
    issues = localize_diff_records([diff], words, ["2.0%"])
    assert len(issues) == 1
    assert issues[0]["expected_cells"] == [period]


def test_source_conditioned_text_hyphen_equivalence():
    hyphen, text_hyphen = chr(0x2824), "\u2011"
    words = [[_prov("-", text_hyphen, 10)]]
    diff = {"type": "word_mismatch", "expected": hyphen,
            "actual": text_hyphen, "actual_start_idx": 0,
            "actual_end_idx": 1, "expected_start_idx": 0,
            "expected_end_idx": 1}
    assert localize_diff_records([diff], words, ["(E_d"]) == []


def test_text_hyphen_equivalence_requires_underscore_source_context():
    hyphen, text_hyphen = chr(0x2824), "\u2011"
    words = [[_prov("-", text_hyphen, 10)]]
    diff = {"type": "word_mismatch", "expected": hyphen,
            "actual": text_hyphen, "actual_start_idx": 0,
            "actual_end_idx": 1, "expected_start_idx": 0,
            "expected_end_idx": 1}
    issues = localize_diff_records([diff], words, ["-0.45"])
    assert len(issues) == 1
    assert issues[0]["expected_cells"] == [hyphen]


def test_text_hyphen_equivalence_does_not_suppress_braille_hyphen_mismatch():
    hyphen, wrong = chr(0x2824), chr(0x2809)
    words = [[_prov("-", wrong, 10)]]
    diff = {"type": "word_mismatch", "expected": hyphen,
            "actual": wrong, "actual_start_idx": 0,
            "actual_end_idx": 1, "expected_start_idx": 0,
            "expected_end_idx": 1}
    issues = localize_diff_records([diff], words, ["(E_d"])
    assert len(issues) == 1
    assert issues[0]["expected_cells"] == [hyphen]


def test_source_conditioned_hyphen_minus_equivalence():
    hyphen, observed = chr(0x2824), chr(0x2809)
    words = [[_prov("-", observed, 10)]]
    diff = {"type": "word_mismatch", "expected": hyphen,
            "actual": observed, "actual_start_idx": 0,
            "actual_end_idx": 1, "expected_start_idx": 0,
            "expected_end_idx": 1}
    assert localize_diff_records([diff], words, ["p-value"]) == []


def test_hyphen_minus_equivalence_requires_source_hyphen_context():
    hyphen, observed = chr(0x2824), chr(0x2809)
    words = [[_prov("x", observed, 10)]]
    diff = {"type": "word_mismatch", "expected": hyphen,
            "actual": observed, "actual_start_idx": 0,
            "actual_end_idx": 1, "expected_start_idx": 0,
            "expected_end_idx": 1}
    issues = localize_diff_records([diff], words, ["pvalue"])
    assert len(issues) == 1
    assert issues[0]["expected_cells"] == [hyphen]


def test_hyphen_minus_rule_does_not_suppress_compound_capitalization_issue():
    hyphen, cap = chr(0x2824), chr(0x2820)
    observed_hyphen, observed_cap = chr(0x2809), chr(0x2808)
    words = [[_prov("-", observed_hyphen, 10), _prov("F", observed_cap, 20)]]
    diff = {"type": "word_mismatch", "expected": hyphen + cap,
            "actual": observed_hyphen + observed_cap, "actual_start_idx": 0,
            "actual_end_idx": 1, "expected_start_idx": 0,
            "expected_end_idx": 1}
    issues = localize_diff_records([diff], words, ["Dickey-Fuller"])
    assert len(issues) == 1
    assert issues[0]["expected_cells"] == [cap]
    assert issues[0]["actual_cells"] == [observed_cap]
    assert issues[0]["compound_resolution"][0]["reason"] == "source_hyphen_minus_equivalence"


def test_source_conditioned_equals_equivalence():
    expected = chr(0x2810) + chr(0x2836)
    actual = chr(0x2808) + chr(0x281B)
    words = [[_prov('"', actual[0], 10), _prov("7", actual[1], 20)]]
    diff = {"type": "word_mismatch", "expected": expected,
            "actual": actual, "actual_start_idx": 0,
            "actual_end_idx": 1, "expected_start_idx": 0,
            "expected_end_idx": 1}
    assert localize_diff_records([diff], words, ["="]) == []


def test_equals_equivalence_requires_literal_equals_source_token():
    expected = chr(0x2810) + chr(0x2836)
    actual = chr(0x2808) + chr(0x281B)
    words = [[_prov('"', actual[0], 10), _prov("7", actual[1], 20)]]
    diff = {"type": "word_mismatch", "expected": expected,
            "actual": actual, "actual_start_idx": 0,
            "actual_end_idx": 1, "expected_start_idx": 0,
            "expected_end_idx": 1}
    issues = localize_diff_records([diff], words, ["=="])
    assert len(issues) == 1
    assert issues[0]["expected_cells"] == list(expected)


def test_equals_rule_does_not_suppress_neighboring_formula_difference():
    equals_expected = chr(0x2810) + chr(0x2836)
    equals_actual = chr(0x2808) + chr(0x281B)
    period, wrong_period = chr(0x2832), chr(0x2819)
    words = [[_prov('"', equals_actual[0], 10), _prov("7", equals_actual[1], 20),
              _prov(".", wrong_period, 30)]]
    diff = {"type": "word_mismatch", "expected": equals_expected + period,
            "actual": equals_actual + wrong_period, "actual_start_idx": 0,
            "actual_end_idx": 1, "expected_start_idx": 0,
            "expected_end_idx": 1}
    issues = localize_diff_records([diff], words, ["="])
    assert len(issues) == 1
    assert issues[0]["expected_cells"] == [period]
    assert issues[0]["actual_cells"] == [wrong_period]
    assert issues[0]["compound_resolution"][0]["reason"] == "source_equals_equivalence"


def _numeric_parenthesis_issue(source_token, expected, actual, sources=None):
    actual_provenance = [
        _prov(source, cell, 10 + index * 10)
        for index, (source, cell) in enumerate(zip(sources or [source_token] * len(actual), actual))
    ]
    diff = {
        "type": "word_mismatch",
        "expected": expected,
        "actual": actual,
        "actual_start_idx": 0,
        "actual_end_idx": 1,
        "expected_start_idx": 0,
        "expected_end_idx": 1,
    }
    return localize_diff_records([diff], [actual_provenance], [source_token])


def test_numeric_parenthesized_decimal_accepts_opening_indicator():
    expected = "\u2810\u2823\u283c\u2803\u2832\u280a\u2803\u2803\u2810\u283c"
    actual = "\u2808\u2823\u283c\u2803\u2832\u280a\u2803\u2803\u2808\u283c"
    issues = _numeric_parenthesis_issue("(0.9200)", expected, actual)
    assert issues == []


def test_numeric_parenthesized_decimal_accepts_closing_indicator():
    expected = "\u2810\u2823\u283c\u2803\u2832\u280a\u2803\u2803\u2810\u283c"
    actual = "\u2808\u2823\u283c\u2803\u2832\u280a\u2803\u2803\u2808\u283c"
    issues = _numeric_parenthesis_issue("(0.9200)", expected, actual)
    assert issues == []


def test_second_numeric_parenthesized_decimal_is_accepted():
    issues = _numeric_parenthesis_issue("(1.2850)", "\u2810", "\u2808")
    assert issues == []


def test_negative_decimal_accepts_only_closing_parenthesis_indicator():
    issues = _numeric_parenthesis_issue("-0.45)", "\u2810", "\u2808")
    assert issues == []


def test_negative_decimal_parenthesis_equivalence_preserves_period_difference():
    parenthesis = "\u2810"
    actual_parenthesis = "\u2808"
    closing = "\u283c"
    period = "\u2832"
    wrong_period = "\u2819"
    sources = [")", ")", "."]
    actual_provenance = [
        _prov(source, cell, 10 + index * 10)
        for index, (source, cell) in enumerate(zip(sources, [actual_parenthesis, closing, wrong_period]))
    ]
    diff = {
        "type": "word_mismatch",
        "expected": parenthesis + closing + period,
        "actual": actual_parenthesis + closing + wrong_period,
        "actual_start_idx": 0,
        "actual_end_idx": 1,
        "expected_start_idx": 0,
        "expected_end_idx": 1,
    }
    issues = localize_diff_records([diff], [actual_provenance], ["-2.15)."])
    assert len(issues) == 1
    assert issues[0]["expected_cells"] == [period]
    assert issues[0]["actual_cells"] == [wrong_period]


def test_numeric_parenthesis_rule_does_not_suppress_red_identifier_cases():
    for source_token in ["(CPI)", "(BoP).", "(+/-", "0.5%).", "unrelated"]:
        issues = _numeric_parenthesis_issue(source_token, "\u2810", "\u2808")
        assert len(issues) == 1
        assert issues[0]["expected_cells"] == ["\u2810"]


def test_numeric_parenthesis_rule_does_not_suppress_structural_without_exact_provenance():
    words = [
        [_prov("(", "\u2808", 10)],
        [_prov("x", "\u2802", 20)],
        [_prov("y", "\u2803", 30)],
    ]
    diff = {
        "type": "structural_mismatch",
        "expected": "\u2810 \u2801",
        "actual": "\u2808 \u2802 \u2803",
        "actual_start_idx": 0,
        "actual_end_idx": 3,
        "expected_start_idx": 0,
        "expected_end_idx": 2,
    }
    issues = localize_diff_records([diff], words, ["(0.9200)"])
    assert len(issues) == 1
    assert issues[0]["kind"] == "structural_review"


def test_numeric_parenthesized_decimal_period_remains_unresolved():
    issues = _numeric_parenthesis_issue("(0.9200)", "\u2832", "\u2819")
    assert len(issues) == 1
    assert issues[0]["expected_cells"] == ["\u2832"]


def test_negative_decimal_parenthesis_period_remains_unresolved():
    issues = _numeric_parenthesis_issue("-2.15).", "\u2832", "\u2819")
    assert len(issues) == 1
    assert issues[0]["expected_cells"] == ["\u2832"]


def test_safe_alphabetic_word_final_period_is_accepted():
    issues = _numeric_parenthesis_issue("Pricing.", "\u2832", "\u2819")
    assert issues == []


def test_period_percent_collision_remains_reported():
    issues = _numeric_parenthesis_issue("2.0%", "\u2832", "\u2819")
    assert len(issues) == 1
    assert issues[0]["expected_cells"] == ["\u2832"]


def test_percent_after_parenthesis_period_remains_unresolved():
    issues = _numeric_parenthesis_issue("0.5%).", "\u2832", "\u2819")
    assert len(issues) == 1
    assert issues[0]["expected_cells"] == ["\u2832"]


def test_unproven_plain_decimal_period_remains_reported():
    issues = _numeric_parenthesis_issue("0.8745", "\u2832", "\u2819")
    assert len(issues) == 1
    assert issues[0]["expected_cells"] == ["\u2832"]


def test_report_renders_cell_issue_provenance_without_raw_range():
    html = ReportGenerator().generate_report(
        {"pages": []},
        {"diffs": [{"type": "word_mismatch", "confidence": "high_confidence", "expected": "RAW_LONG_RANGE", "actual": "RAW_LONG_RANGE"}],
         "cell_issues": [{"kind": "replacement", "expected_cells": [chr(0x2801)], "actual_cells": [chr(0x2803)], "page": 3, "x0": 10.0, "x1": 15.0, "top": 20.0, "bottom": 25.0, "context": "CPI", "confidence": "high_confidence", "parent_diff_type": "word_mismatch"}]},
        {}, 1,
    )
    assert "page 3, x 10.00-15.00" in html
    assert "Context: CPI" in html
    assert "RAW_LONG_RANGE" not in html
    words = [[_prov("a", "⠁", 10)], [_prov("b", "⠃", 20)]]
    diff = {"type": "structural_mismatch", "confidence": "high_confidence", "expected": "⠁ ⠉ ⠙", "actual": "⠁ ⠃", "actual_start_idx": 0, "actual_end_idx": 2}
    issues = localize_diff_records([diff], words)
    assert issues
    assert all(i["kind"] == "structural_review" for i in issues)


def test_structural_parent_splits_at_reliable_word_anchors():
    one, three, four, nine = (chr(0x2801), chr(0x2803), chr(0x2804), chr(0x2809))
    words = [[_prov("one", one, 10)], [_prov("three", three, 20)],
             [_prov("four", four, 30)], [_prov("nine", nine, 40)]]
    diff = {
        "type": "structural_mismatch", "confidence": "high_confidence",
        "expected": one + " " + nine,
        "actual": one + " " + three + " " + four + " " + nine,
        "actual_start_idx": 0, "actual_end_idx": 4,
        "expected_start_idx": 0, "expected_end_idx": 3,
    }
    issues = localize_diff_records([diff], words)
    assert [issue["kind"] for issue in issues] == ["insertion", "insertion"]
    assert [issue["actual_cells"] for issue in issues] == [[three], [four]]


def test_structural_parent_keeps_ambiguous_remainder_structural():
    one, three, nine = chr(0x2801), chr(0x2803), chr(0x2809)
    words = [[_prov("one", one, 10)], [_prov("three", three, 20)],
             [_prov("nine", nine, 30)]]
    diff = {
        "type": "structural_mismatch", "confidence": "needs_review",
        "expected": one + " " + chr(0x2807),
        "actual": one + " " + three + " " + nine,
        "actual_start_idx": 0, "actual_end_idx": 3,
        "expected_start_idx": 0, "expected_end_idx": 2,
    }
    issues = localize_diff_records([diff], words)
    structural = [issue for issue in issues if issue["kind"] == "structural_review"]
    assert len(structural) == 1
    assert structural[0]["actual_cells"] == [three, nine]
    assert structural[0]["provenance_cells"]


def test_weak_source_hint_does_not_split_ambiguous_structural_parent():
    one, three, nine, twentyfive = (
        chr(0x2801), chr(0x2803), chr(0x2809), chr(0x2819)
    )
    words = [
        [_prov("actual_a", three, 10)],
        [_prov("actual_b", nine, 20)],
        [_prov("actual_c", twentyfive, 30)],
    ]
    diff = {
        "type": "structural_mismatch", "confidence": "needs_review",
        "expected": one + " " + chr(0x2807),
        "actual": three + " " + nine + " " + twentyfive,
        "actual_start_idx": 0, "actual_end_idx": 3,
        "expected_start_idx": 0, "expected_end_idx": 2,
    }

    issues = localize_diff_records(
        [diff], words, ["unique_source_hint", "another_source_hint"]
    )

    assert issues
    assert all(issue["kind"] == "structural_review" for issue in issues)


def _synthetic_braille_word(text):
    return "".join(chr(0x2800 + ord(character) - ord("a") + 1)
                   for character in text)


def test_local_structural_alignment_splits_anchored_islands_and_residual():
    expected_word = _synthetic_braille_word("abcdefghijklmnopqr")
    actual_word = (
        expected_word[:3] + "\u283f" + expected_word[4:9]
        + "\u283e" + expected_word[10:]
    )
    extra_word = _synthetic_braille_word("zzz")
    words = [
        [_prov("source", cell, 10 + index * 5)
         for index, cell in enumerate(actual_word)],
        [_prov("extra", cell, 100 + index * 5)
         for index, cell in enumerate(extra_word)],
    ]
    diff = {
        "type": "structural_mismatch", "confidence": "needs_review",
        "expected": expected_word, "actual": actual_word + " " + extra_word,
        "actual_start_idx": 0, "actual_end_idx": 2,
        "expected_start_idx": 0,
    }

    issues = localize_diff_records([diff], words, ["source"])

    assert [issue["kind"] for issue in issues] == [
        "replacement", "replacement", "structural_review"
    ]
    assert [issue["actual_cells"] for issue in issues[:2]] == [
        ["\u283f"], ["\u283e"]
    ]
    assert issues[2]["actual_cells"] == list(extra_word)
    resolved = issues[0]["resolved_equal_cells"]
    assert len(resolved) == len(expected_word) - 2
    assert {cell["unicode_cell"] for cell in resolved} == (
        set(expected_word) - {expected_word[3], expected_word[9]}
    )


def test_local_structural_alignment_keeps_multiword_middle_ambiguous():
    expected_word = _synthetic_braille_word("abcdefghi")
    words = [
        [_prov("source", cell, 10 + index * 5)
         for index, cell in enumerate(_synthetic_braille_word("abc"))],
        [_prov("middle_a", cell, 100 + index * 5)
         for index, cell in enumerate(_synthetic_braille_word("qqq"))],
        [_prov("middle_b", cell, 200 + index * 5)
         for index, cell in enumerate(_synthetic_braille_word("rrr"))],
        [_prov("tail", cell, 300 + index * 5)
         for index, cell in enumerate(_synthetic_braille_word("ghi"))],
    ]
    diff = {
        "type": "structural_mismatch", "confidence": "needs_review",
        "expected": expected_word,
        "actual": " ".join(_synthetic_braille_word(word)
                            for word in ("abc", "qqq", "rrr", "ghi")),
        "actual_start_idx": 0, "actual_end_idx": 4,
        "expected_start_idx": 0,
    }

    issues = localize_diff_records([diff], words, ["source"])

    assert issues
    assert all(issue["kind"] == "structural_review" for issue in issues)
    owned = {
        cell["unicode_cell"]
        for issue in issues
        for field in ("provenance_cells", "resolved_equal_cells")
        for cell in issue.get(field, [])
    }
    assert set(_synthetic_braille_word("abcqqqrrrghi")) <= owned


def test_existing_equivalence_can_anchor_a_structural_span():
    expected_word = "\u2820" + _synthetic_braille_word("itle")
    actual_word = "\u2808" + _synthetic_braille_word("itle")
    words = [
        [_prov("T", actual_word[0], 10)]
        + [_prov(character, actual_word[index], 15 + index * 5)
           for index, character in enumerate("itle", 1)],
        [_prov("extra", "\u2801", 100)],
    ]
    diff = {
        "type": "structural_mismatch", "confidence": "needs_review",
        "expected": expected_word, "actual": actual_word + " \u2801",
        "actual_start_idx": 0, "actual_end_idx": 2,
        "expected_start_idx": 0,
    }

    issues = localize_diff_records([diff], words, ["Title"])

    assert issues
    pairs = issues[0]["resolved_equal_pairs"]
    assert any(pair["reason"] == "source_conditioned_equivalence" for pair in pairs)
    assert all(issue["kind"] == "structural_review" for issue in issues)


def test_local_structural_alignment_has_single_owner_for_every_actual_cell():
    expected_word = _synthetic_braille_word("abcdefghi")
    actual_word = _synthetic_braille_word("abcxdefyghi")
    extra_word = _synthetic_braille_word("zzz")
    words = [
        [_prov("source", cell, 10 + index * 5)
         for index, cell in enumerate(actual_word)],
        [_prov("extra", cell, 100 + index * 5)
         for index, cell in enumerate(extra_word)],
    ]
    diff = {
        "type": "structural_mismatch", "confidence": "needs_review",
        "expected": expected_word, "actual": actual_word + " " + extra_word,
        "actual_start_idx": 0, "actual_end_idx": 2,
        "expected_start_idx": 0,
    }
    issues = localize_diff_records([diff], words, ["source"])
    owner_counts = {}
    for issue in issues:
        for field in ("provenance_cells", "resolved_equal_cells"):
            for cell in issue.get(field, []):
                key = (cell["page"], cell["x0"], cell["top"], cell["unicode_cell"])
                owner_counts[key] = owner_counts.get(key, 0) + 1
    expected_keys = {
        (cell.page, cell.x0, cell.top, cell.unicode_cell)
        for word in words for cell in word
    }
    assert set(owner_counts) == expected_keys
    assert all(count == 1 for count in owner_counts.values())


def test_structural_parent_is_segmented_at_page_boundary():
    one, three, nine = chr(0x2801), chr(0x2803), chr(0x2809)
    words = [[_prov("one", one, 10)],
             [_prov("three", three, 20)],
             [PdfCellProvenance(2, 30, 35, 10, 15, "nine", nine, "font", None)]]
    diff = {
        "type": "structural_mismatch", "confidence": "needs_review",
        "expected": one + " " + chr(0x2807),
        "actual": one + " " + three + " " + nine,
        "actual_start_idx": 0, "actual_end_idx": 3,
        "expected_start_idx": 0, "expected_end_idx": 2,
    }
    issues = localize_diff_records([diff], words)
    structural = [issue for issue in issues if issue["kind"] == "structural_review"]
    assert len(structural) == 2
    assert [issue["actual_cells"] for issue in structural] == [[three], [nine]]
    assert {cell["page"] for issue in structural for cell in issue["provenance_cells"]} == {1, 2}


def test_structural_parent_is_segmented_at_pdf_line_boundary():
    """A broad parent must not own later physical lines as one range."""
    one, three, nine = chr(0x2801), chr(0x2803), chr(0x2809)
    words = [
        [_prov("line_one", one, 10)],
        [PdfCellProvenance(1, 20, 25, 30, 35, "three", three, "font", None)],
        [PdfCellProvenance(1, 30, 35, 30, 35, "nine", nine, "font", None)],
    ]
    diff = {
        "type": "structural_mismatch", "confidence": "needs_review",
        "expected": chr(0x2802) + " " + chr(0x2807),
        "actual": one + " " + three + " " + nine,
        "actual_start_idx": 0, "actual_end_idx": 3,
        "expected_start_idx": 0, "expected_end_idx": 2,
    }
    issues = localize_diff_records([diff], words)
    structural = [issue for issue in issues if issue["kind"] == "structural_review"]
    assert len(structural) == 2
    assert [issue["actual_cells"] for issue in structural] == [[one], [three, nine]]
    assert [issue["provenance_cells"][0]["top"] for issue in structural] == [10, 30]


def test_synthetic_nineteen_vs_two_hundred_structural_range_is_line_bounded():
    """The 19-vs-200 shape is bounded before it can become one giant review."""
    expected = " ".join(chr(0x2801) for _ in range(19))
    actual_words = []
    for index in range(200):
        line = index // 20
        actual_words.append([PdfCellProvenance(
            1, index * 5, index * 5 + 4, line * 20, line * 20 + 5,
            "actual", chr(0x2802), "font", None
        )])
    actual = " ".join(chr(0x2802) for _ in range(200))
    diff = {
        "type": "structural_mismatch", "confidence": "needs_review",
        "expected": expected, "actual": actual,
        "actual_start_idx": 0, "actual_end_idx": 200,
        "expected_start_idx": 0, "expected_end_idx": 19,
    }
    issues = localize_diff_records([diff], actual_words)
    structural = [issue for issue in issues if issue["kind"] == "structural_review"]
    assert structural
    assert max(len(issue["provenance_cells"]) for issue in structural) <= 20


def test_normal_issue_retains_exact_actual_provenance():
    one, three = chr(0x2801), chr(0x2803)
    words = [[_prov("word", three, 10)]]
    diff = {
        "type": "word_mismatch", "confidence": "high_confidence",
        "expected": one, "actual": three,
        "actual_start_idx": 0, "actual_end_idx": 1,
    }
    issue = localize_diff_records([diff], words)[0]
    assert issue["actual_cells"] == [three]
    assert [cell["unicode_cell"] for cell in issue["provenance_cells"]] == [three]


def test_suppressed_equivalence_retains_proven_equal_word_provenance():
    separator, hyphen, letter, extra = (
        chr(0x2824), "\u2011", chr(0x2801), chr(0x2803)
    )
    words = [[
        _prov("s", chr(0x2828), 10),
        _prov("-", hyphen, 20),
        _prov("a", letter, 30),
        _prov("x", extra, 40),
    ]]
    diff = {
        "type": "word_mismatch", "confidence": "high_confidence",
        "expected": chr(0x2828) + separator + letter,
        "actual": chr(0x2828) + hyphen + letter + extra,
        "actual_start_idx": 0, "actual_end_idx": 1,
        "expected_start_idx": 0, "expected_end_idx": 1,
    }
    issues = localize_diff_records([diff], words, ["source_word_with_"])
    assert issues
    assert issues[0]["actual_cells"] == [extra]
    resolved = issues[0]["resolved_equal_cells"]
    assert any(cell["unicode_cell"] == hyphen for cell in resolved)
    assert any(cell["unicode_cell"] == chr(0x2828) for cell in resolved)
    assert any(
        pair["expected_cell"] == separator
        and pair["actual_cell"]["unicode_cell"] == hyphen
        and pair["reason"] == "source_conditioned_equivalence"
        for pair in issues[0]["resolved_equal_pairs"]
    )


def test_compound_two_existing_equivalences_resolves_with_component_proof():
    expected = chr(0x2820) + chr(0x2802)
    actual = chr(0x2808) + chr(0x2801)
    words = [[_prov("W", actual[0], 10), _prov(",", actual[1], 20)]]
    diff = {
        "type": "word_mismatch", "confidence": "high_confidence",
        "expected": expected, "actual": actual,
        "actual_start_idx": 0, "actual_end_idx": 1,
        "expected_start_idx": 0, "expected_end_idx": 1,
    }

    issues = localize_diff_records([diff], words, ["Word,"])

    assert len(issues) == 1
    assert issues[0]["kind"] == "resolved_equal"
    assert issues[0]["confidence"] == "ignored"
    assert [item["reason"] for item in issues[0]["compound_resolution"]] == [
        "source_capitalization_equivalence", "source_comma_equivalence"
    ]
    assert len(issues[0]["resolved_equal_cells"]) == 2


def test_compound_partial_decomposition_keeps_only_unresolved_component():
    expected = chr(0x2820) + chr(0x2802)
    actual = chr(0x2808) + chr(0x2803)
    words = [[_prov("W", actual[0], 10), _prov(",", actual[1], 20)]]
    diff = {
        "type": "word_mismatch", "confidence": "high_confidence",
        "expected": expected, "actual": actual,
        "actual_start_idx": 0, "actual_end_idx": 1,
        "expected_start_idx": 0, "expected_end_idx": 1,
    }

    issues = localize_diff_records([diff], words, ["Word,"])

    assert len(issues) == 1
    assert issues[0]["kind"] == "replacement"
    assert issues[0]["expected_cells"] == [chr(0x2802)]
    assert issues[0]["actual_cells"] == [chr(0x2803)]
    assert [item["reason"] for item in issues[0]["compound_resolution"]] == [
        "source_capitalization_equivalence"
    ]
    assert len(issues[0]["resolved_equal_cells"]) == 1


def test_compound_exact_equivalence_exact_preserves_all_provenance():
    expected = chr(0x2801) + chr(0x2820) + chr(0x2802) + chr(0x2803)
    actual = chr(0x2801) + chr(0x2808) + chr(0x2801) + chr(0x2803)
    words = [[_prov("a", actual[0], 10), _prov("W", actual[1], 20),
              _prov(",", actual[2], 30), _prov("z", actual[3], 40)]]
    diff = {
        "type": "word_mismatch", "confidence": "high_confidence",
        "expected": expected, "actual": actual,
        "actual_start_idx": 0, "actual_end_idx": 1,
        "expected_start_idx": 0, "expected_end_idx": 1,
    }

    issues = localize_diff_records([diff], words, ["Aword,"])

    assert len(issues) == 1
    assert issues[0]["kind"] == "resolved_equal"
    assert len(issues[0]["resolved_equal_cells"]) == 4
    assert [item["reason"] for item in issues[0]["compound_resolution"]] == [
        "exact_equal", "source_capitalization_equivalence",
        "source_comma_equivalence", "exact_equal",
    ]


def test_unequal_length_compound_keeps_unproved_insertion_visible():
    expected = chr(0x2820) + chr(0x2802)
    actual = chr(0x2808) + chr(0x2801) + chr(0x2803)
    words = [[_prov("W", actual[0], 10), _prov(",", actual[1], 20),
              _prov("extra", actual[2], 30)]]
    diff = {
        "type": "word_mismatch", "confidence": "high_confidence",
        "expected": expected, "actual": actual,
        "actual_start_idx": 0, "actual_end_idx": 1,
        "expected_start_idx": 0, "expected_end_idx": 1,
    }

    issues = localize_diff_records([diff], words, ["Word,"])

    assert [issue["kind"] for issue in issues] == ["insertion"]
    assert issues[0]["actual_cells"] == [chr(0x2803)]
    assert len(issues[0]["resolved_equal_cells"]) == 2


def test_compound_source_condition_failure_does_not_reuse_pair_mapping():
    expected = chr(0x2820) + chr(0x2802)
    actual = chr(0x2808) + chr(0x2801)
    words = [[_prov("w", actual[0], 10), _prov("x", actual[1], 20)]]
    diff = {
        "type": "word_mismatch", "confidence": "high_confidence",
        "expected": expected, "actual": actual,
        "actual_start_idx": 0, "actual_end_idx": 1,
        "expected_start_idx": 0, "expected_end_idx": 1,
    }

    issues = localize_diff_records([diff], words, ["word"])

    assert [issue["kind"] for issue in issues] == ["replacement"]
    assert len(issues[0].get("resolved_equal_cells", [])) == 0


def test_compound_does_not_resolve_generic_pair_only_mapping():
    expected = chr(0x2804) + chr(0x2800)
    actual = chr(0x2809) + chr(0x2808)
    words = [[_prov("x", actual[0], 10), _prov("y", actual[1], 20)]]
    diff = {
        "type": "word_mismatch", "confidence": "high_confidence",
        "expected": expected, "actual": actual,
        "actual_start_idx": 0, "actual_end_idx": 1,
        "expected_start_idx": 0, "expected_end_idx": 1,
    }

    issues = localize_diff_records([diff], words, ["xy"])

    assert [issue["kind"] for issue in issues] == ["replacement"]
    assert issues[0]["expected_cells"] == list(expected)
    assert issues[0]["actual_cells"] == list(actual)


def test_exact_equal_cells_are_owned_when_word_has_another_issue():
    expected = chr(0x2801) + chr(0x2803) + chr(0x2805)
    actual = chr(0x2801) + chr(0x2804) + chr(0x2805)
    words = [[
        _prov("a", actual[0], 10),
        _prov("b", actual[1], 20),
        _prov("c", actual[2], 30),
    ]]
    diff = {
        "type": "word_mismatch", "confidence": "high_confidence",
        "expected": expected, "actual": actual,
        "actual_start_idx": 0, "actual_end_idx": 1,
    }

    issues = localize_diff_records([diff], words)

    assert len(issues) == 1
    assert issues[0]["actual_cells"] == [actual[1]]
    resolved = issues[0]["resolved_equal_cells"]
    assert [cell["unicode_cell"] for cell in resolved] == [actual[0], actual[2]]
    assert [pair["reason"] for pair in issues[0]["resolved_equal_pairs"]] == [
        "exact_equal", "exact_equal"
    ]


def _fixture_red_region_count(red_cells):
    """Count connected red cell regions for the test-only fixture audit."""
    parent = list(range(len(red_cells)))

    def find(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left, right):
        left, right = find(left), find(right)
        if left != right:
            parent[right] = left

    for index, cell in enumerate(red_cells):
        for previous, other in enumerate(red_cells[:index]):
            if cell.page != other.page:
                continue
            vertical_gap = max(0, other.top - cell.bottom, cell.top - other.bottom)
            horizontal_gap = max(0, other.x0 - cell.x1, cell.x0 - other.x1)
            if vertical_gap <= 2.0 and horizontal_gap <= 1.5:
                union(index, previous)
    return len({find(index) for index in range(len(red_cells))})


def test_document1_red_audit_preserves_all_fixture_regions():
    """The structural-localization pass must still represent all 29 red regions."""
    import main

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    fixture_dir = os.path.join(base_dir, "testfiles", "Document 1")
    docx_path = glob.glob(os.path.join(fixture_dir, "*Master File.docx"))[0]
    pdf_path = glob.glob(os.path.join(fixture_dir, "*Highlighted in Red.pdf"))[0]

    extracted = DocumentExtractor().extract(docx_path)
    expected_blocks = []
    for page in extracted.get("pages", []):
        for block in page.get("blocks", []):
            source_text = block.get("text", "")
            translated = (
                main.louis.translateString(["en-ueb-g1.ctb"], source_text)
                if source_text.strip() else ""
            )
            expected_blocks.append({
                "type": block.get("type", "body"),
                "text": main._post_process_expected(translated, 1),
                "source_text": source_text,
            })

    pdf_input = read_braille_pdf_with_provenance(pdf_path)
    parsed = BRFParser().parse_content(pdf_input.content)
    actual = "\x0c".join(
        "\n".join(page.get("raw_lines", []))
        for page in parsed.get("pages", [])
    )
    engine = DiffEngine(grade=1)
    diffs = engine.compare(expected_blocks, actual)["diffs"]
    source_tokens = engine._source_tokens_for_expected(expected_blocks)
    issues = []
    for diff in diffs:
        issues.extend(localize_diff_records(
            [diff], pdf_input.word_provenance, source_tokens
        ))

    red_cells = [
        cell
        for word in pdf_input.word_provenance
        for cell in word
        if cell.color and cell.color[0] > 0.8
        and cell.color[1] < 0.1 and cell.color[2] < 0.1
    ]
    owners = {}
    for issue in issues:
        for field in ("provenance_cells", "resolved_equal_cells"):
            for cell in issue.get(field, []):
                key = (cell["page"], round(cell["x0"], 3),
                       round(cell["top"], 3), cell["unicode_cell"])
                owners.setdefault(key, []).append(issue)

    red_keys = [
        (cell.page, round(cell.x0, 3), round(cell.top, 3), cell.unicode_cell)
        for cell in red_cells
    ]
    assert _fixture_red_region_count(red_cells) == 29
    assert all(key in owners for key in red_keys)
    assert all(len(owners[key]) == 1 for key in red_keys)
