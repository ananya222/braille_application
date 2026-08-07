import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from braille_app.diff_engine import DiffEngine

def test_diff_engine_base():
    print("=" * 60)
    print("RUNNING BASE DIFF ENGINE TEST (STREAM NORMALIZATION)")
    print("=" * 60)

    expected = [
        {"type": "heading1", "text": "Chapter One: The Beginning"},
        {"type": "body", "text": "This is an exact match paragraph that should have zero diffs."},
        {"type": "body", "text": "This paragraph has a wrong contraction in the middle of it."},
        {"type": "body", "text": "This paragraph has a minor punctuation difference!"},
        {"type": "heading2", "text": "Chapter Two: Future"},
        {"type": "body", "text": "This paragraph exists in expected."}
    ]

    actual = """
Chapter One: The Beg1nning
1

This is an exact match paragraph that should have zero diffs.
2

This paragraph has a wrong c0ntraction in the middle of it.
3

This paragraph has a minor punctuation difference.
4

Chapter Two: Future
5

This paragraph exists in expected.
6

This is an extra paragraph that breaks alignment.
7
"""

    engine = DiffEngine()
    results = engine.compare(expected, actual)
    print(json.dumps(results, indent=2))

    assert results["stats"]["total_expected_words"] == 41
    assert results["stats"]["total_actual_words"] == 49

    diffs = results["diffs"]
    alignment_failures = [d for d in diffs if d["confidence"] == "alignment_failure"]
    paragraph_errors = [
        d for d in diffs
        if d["type"] in ("missing_paragraph", "extra_paragraph", "missing_paragraph_layout", "extra_paragraph_layout")
    ]
    assert len(alignment_failures) == 0
    assert len(paragraph_errors) == 0

    high_conf = [d for d in diffs if d["confidence"] == "high_confidence" and d["type"] == "severe_mismatch"]
    assert any(d["expected"] == "Beginning" and d["actual"] == "Beg1nning" for d in high_conf)
    assert any(d["expected"] == "contraction" and d["actual"] == "c0ntraction" for d in high_conf)
    assert any("extra paragraph" in d["actual"] for d in high_conf)

    needs_review = [d for d in diffs if d["confidence"] == "needs_review"]
    assert len(needs_review) == 1
    assert needs_review[0]["expected"] == "difference!"
    assert needs_review[0]["actual"] == "difference."

    print("[OK] Base stream normalization test passed.\n")


def test_missing_content_in_actual():
    print("=" * 60)
    print("TEST 1: MISSING CONTENT IN ACTUAL STREAM")
    print("=" * 60)
    expected = [
        {"type": "body", "text": "Paragraph one"},
        {"type": "body", "text": "Paragraph two (missing in actual)"},
        {"type": "body", "text": "Paragraph three"}
    ]
    actual = """
Paragraph one

Paragraph three
"""
    engine = DiffEngine()
    results = engine.compare(expected, actual)
    print(json.dumps(results, indent=2))

    diffs = results["diffs"]
    paragraph_errors = [d for d in diffs if d["type"] in ("missing_paragraph", "extra_paragraph")]
    assert len(paragraph_errors) == 0

    deleted = [d for d in diffs if "missing in actual" in d.get("expected", "")]
    assert len(deleted) >= 1
    print("[OK] Missing content reported as stream diff, not paragraph alignment failure.\n")


def test_allowlist():
    print("=" * 60)
    print("TEST 2: ALLOWLIST DOWNGRADING")
    print("=" * 60)

    allowlist = [
        {
            "expected": "This paragraph has a minor punctuation difference!",
            "actual": "This paragraph has a minor punctuation difference."
        }
    ]

    expected = [{"type": "body", "text": "This paragraph has a minor punctuation difference!"}]
    actual = "This paragraph has a minor punctuation difference."

    engine = DiffEngine(allowlist=allowlist)
    results = engine.compare(expected, actual)
    print(json.dumps(results, indent=2))

    diffs = results["diffs"]
    ignored = [d for d in diffs if d["confidence"] == "ignored"]
    assert len(ignored) == 1
    assert ignored[0]["type"] == "allowed_difference"
    print("[OK] Allowlist successfully downgraded review to ignored.\n")


def test_pattern_detection_thresholds():
    print("=" * 60)
    print("TEST 3: PATTERN DETECTION THRESHOLDS (30% vs EXACTLY 30%)")
    print("=" * 60)

    print("  Subcase A: 4 of 10 blocks have punctuation difference (40% > 30%)")
    expected_a = [{"type": "body", "text": f"Paragraph {i}!"} for i in range(10)]
    actual_a = "\n\n".join([f"Paragraph {i}." if i < 4 else f"Paragraph {i}!" for i in range(10)])

    engine = DiffEngine()
    results_a = engine.compare(expected_a, actual_a)
    print(f"    Patterns: {results_a['patterns']}")
    assert len(results_a["patterns"]) == 1
    assert "punctuation_difference" in results_a["patterns"][0]["type"]
    print("    [OK] Collapsed successfully.")

    print("  Subcase B: 3 of 10 blocks have punctuation difference (30% exactly)")
    expected_b = [{"type": "body", "text": f"Paragraph {i}!"} for i in range(10)]
    actual_b = "\n\n".join([f"Paragraph {i}." if i < 3 else f"Paragraph {i}!" for i in range(10)])

    results_b = engine.compare(expected_b, actual_b)
    print(f"    Patterns: {results_b['patterns']}")
    assert len(results_b["patterns"]) == 0
    needs_review_count = len([d for d in results_b["diffs"] if d["confidence"] == "needs_review"])
    print(f"    Reported needs_review counts: {needs_review_count}")
    assert needs_review_count == 3
    print("    [OK] Shown normally (strict thresholding verified).\n")


def test_state_isolation():
    print("=" * 60)
    print("TEST 4: STATE ISOLATION (SEQUENTIAL RUNS)")
    print("=" * 60)

    engine = DiffEngine()

    print("  Run 1: Mismatched texts...")
    res1 = engine.compare([{"type": "body", "text": "Hello"}], "Goodbye")
    assert len(res1["diffs"]) > 0

    print("  Run 2: Identical texts...")
    res2 = engine.compare([{"type": "body", "text": "Hello"}], "Hello")
    print(f"    Run 2 Diffs: {res2['diffs']}")
    assert len(res2["diffs"]) == 0
    print("[OK] State isolation verified (no carryover between sequential calls).\n")


def test_capitalization_indicator_needs_review():
    print("=" * 60)
    print("TEST 5: UEB CAPITALIZATION REPRESENTATION")
    print("=" * 60)

    expected = [
        {"type": "body", "text": "He has ,,knowledge of it."},
        {"type": "body", "text": "Match paragraph two."},
        {"type": "body", "text": "Match paragraph three."},
        {"type": "body", "text": "Match paragraph four."}
    ]
    actual = """
He has ,knowledge of it.

Match paragraph two.

Match paragraph three.

Match paragraph four.
"""

    engine = DiffEngine()
    results = engine.compare(expected, actual)
    print(json.dumps(results, indent=2))

    diffs = results["diffs"]
    needs_review = [d for d in diffs if d["confidence"] == "needs_review"]
    high_conf = [d for d in diffs if d["confidence"] == "high_confidence"]

    assert len(needs_review) == 0
    assert len(high_conf) == 1
    assert high_conf[0]["type"] == "capitalization_variance"
    assert high_conf[0]["expected"] == ",,knowledge"
    assert high_conf[0]["actual"] == ",knowledge"
    print("[OK] Capitalization variance correctly classified under high_confidence.\n")




def test_heading_mismatch_as_content_diff():
    print("=" * 60)
    print("TEST 6: HEADING MISMATCH REPORTED AS CONTENT DIFF")
    print("=" * 60)

    expected = [
        {"type": "heading1", "text": "Chapter One: The Beginning"},
        {"type": "body", "text": "Paragraph content."}
    ]
    actual = """
Totally Different Title
1

Paragraph content.
2
"""
    engine = DiffEngine()
    results = engine.compare(expected, actual)
    print(json.dumps(results, indent=2))

    diffs = results["diffs"]
    heading_errors = [d for d in diffs if d["type"] == "heading_translation_error"]
    paragraph_errors = [d for d in diffs if d["type"] in ("missing_paragraph", "extra_paragraph")]
    assert len(heading_errors) == 0
    assert len(paragraph_errors) == 0
    assert len(diffs) >= 1
    assert all(d["confidence"] != "alignment_failure" for d in diffs)
    print("[OK] Heading mismatch reported as stream content diff only.\n")


def test_stream_resilience_across_paragraph_boundaries():
    print("=" * 60)
    print("TEST 7: STREAM COMPARISON IGNORES PARAGRAPH BOUNDARIES")
    print("=" * 60)

    expected = [
        {"type": "heading1", "text": "Heading A"},
        {"type": "body", "text": "This is paragraph under A."},
        {"type": "heading1", "text": "Heading B"},
        {"type": "body", "text": "This is paragraph under B."},
        {"type": "heading1", "text": "Heading C"},
        {"type": "body", "text": "This is paragraph under C."}
    ]

    actual = """
Heading A
1

This is paragraph under A.
2

Totally Different Title B
3

This is paragraph under B.
4

Heading C
5

This is paragraph under C.
6
"""

    engine = DiffEngine()
    results = engine.compare(expected, actual)
    print(json.dumps(results, indent=2))

    diffs = results["diffs"]
    paragraph_errors = [d for d in diffs if d["type"] in ("missing_paragraph", "extra_paragraph")]
    assert len(paragraph_errors) == 0

    body_diffs = [
        d for d in diffs
        if "paragraph under A" in d.get("expected", "") + d.get("actual", "")
        or "paragraph under C" in d.get("expected", "") + d.get("actual", "")
    ]
    assert len(body_diffs) == 0

    heading_diffs = [d for d in diffs if "Heading" in d.get("expected", "") or "Totally" in d.get("actual", "")]
    assert len(heading_diffs) >= 1
    print("[OK] Paragraph boundaries ignored; only heading content differences reported.\n")


def test_normalization_collapses_whitespace():
    print("=" * 60)
    print("TEST 8: WHITESPACE AND LINE-BREAK NORMALIZATION")
    print("=" * 60)

    expected = [{"type": "body", "text": "Line one.\nLine two."}]
    actual = "Line one.\r\n\r\n   Line two."
    engine = DiffEngine()
    results = engine.compare(expected, actual)
    assert results["diffs"] == []
    print("[OK] Equivalent content with different line breaks produces no diffs.\n")


if __name__ == "__main__":
    test_diff_engine_base()
    test_missing_content_in_actual()
    test_allowlist()
    test_pattern_detection_thresholds()
    test_state_isolation()
    test_capitalization_indicator_needs_review()
    test_heading_mismatch_as_content_diff()
    test_stream_resilience_across_paragraph_boundaries()
    test_normalization_collapses_whitespace()
