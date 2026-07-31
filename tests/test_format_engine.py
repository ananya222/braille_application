import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from braille_app.format_engine import FormatEngine

def run_test_cases():
    print("=" * 60)
    print("RUNNING FORMATTING DIFF ENGINE VERIFICATION SUITE")
    print("=" * 60)
    
    # -------------------------------------------------------------
    # Case 1: Correct section - heading spacing, indentation, page numbering -> 0 diffs
    # -------------------------------------------------------------
    print("\n--- Test 1: Correct formatting (expected 0 diffs) ---")
    expected_1 = [
        {"type": "heading1", "text": "Chapter One"},
        {"type": "body", "text": "This is a correct paragraph starting at cell 3 and runover at cell 1."}
    ]
    # Heading 1 needs 2 blank lines before. Paragraph starts with cell 3 (2 spaces).
    actual_1 = "\n\n  Chapter One\n1\n\n  This is a correct paragraph starting at cell 3 and\nrunover at cell 1.\n#a"
    
    engine = FormatEngine()
    res_1 = engine.check_format(expected_1, actual_1)
    print(json.dumps(res_1, indent=2))
    assert len(res_1["diffs"]) == 0, "Test 1 failed: expected 0 diffs"
    print("[OK] Test 1 passed.")

    # -------------------------------------------------------------
    # Case 2: Heading missing blank line before (mid-page) -> high_confidence
    # -------------------------------------------------------------
    print("\n--- Test 2: Missing required blank line before heading (mid-page) ---")
    expected_2 = [
        {"type": "body", "text": "Preceding text block."},
        {"type": "heading2", "text": "Section A"},
        {"type": "body", "text": "Paragraph text."}
    ]
    # No blank lines before Section A (which is mid-page, immediately following body text)
    actual_2 = "  Preceding text block.\nSection A\n1\n\n  Paragraph text.\n#a"
    
    res_2 = engine.check_format(expected_2, actual_2)
    print(json.dumps(res_2, indent=2))
    spacing_errors = [d for d in res_2["diffs"] if d["type"] == "heading_spacing_error"]
    assert len(spacing_errors) == 1
    assert spacing_errors[0]["confidence"] == "high_confidence"
    print("[OK] Test 2 passed.")

    # -------------------------------------------------------------
    # Case 3: Page numbering sequence gap (page 4 followed by page 6) -> high_confidence
    # -------------------------------------------------------------
    print("\n--- Test 3: Page numbering sequence gap ---")
    expected_3 = [
        {"type": "body", "text": "Page one content."},
        {"type": "body", "text": "Page two content."}
    ]
    # Page 1 (starts with #a/1) then Page 3 (starts with #c/3), gap on Page 2
    actual_3 = "  Page one content.\n#a\x0c  Page two content.\n#c"
    
    res_3 = engine.check_format(expected_3, actual_3)
    print(json.dumps(res_3, indent=2))
    gap_errors = [d for d in res_3["diffs"] if d["type"] == "braille_page_gap"]
    assert len(gap_errors) == 1
    assert gap_errors[0]["confidence"] == "high_confidence"
    print("[OK] Test 3 passed.")

    # -------------------------------------------------------------
    # Case 4: Genuinely ambiguous spacing (blank_before == 1 for Heading 1) -> needs_review
    # -------------------------------------------------------------
    print("\n--- Test 4: Genuinely ambiguous minor spacing variance ---")
    expected_4 = [
        {"type": "body", "text": "Preceding text block."},
        {"type": "heading1", "text": "Chapter One"},
        {"type": "body", "text": "Paragraph content."},
        {"type": "body", "text": "Match paragraph two."},
        {"type": "body", "text": "Match paragraph three."}
    ]
    # Only 1 blank line before Heading 1 (BANA suggests 2, but 1 is a common layout choice)
    actual_4 = "  Preceding text block.\n\n  Chapter One\n1\n\n  Paragraph content.\n\n  Match paragraph two.\n\n  Match paragraph three.\n#a"

    
    res_4 = engine.check_format(expected_4, actual_4)
    print(json.dumps(res_4, indent=2))
    review_errors = [d for d in res_4["diffs"] if d["confidence"] == "needs_review"]
    assert len(review_errors) == 1
    assert review_errors[0]["type"] == "heading_spacing_error"
    print("[OK] Test 4 passed.")

    # -------------------------------------------------------------
    # Case 5: Pattern-detection: >30% vs exactly 30% collapse
    # -------------------------------------------------------------
    print("\n--- Test 5: Pattern-detection threshold (>30% vs exactly 30%) ---")
    expected_5a = [{"type": "body", "text": f"P {i}"} for i in range(10)]
    actual_5a = "\n\n".join([f" P {i}" if i < 4 else f"  P {i}" for i in range(10)]) + "\n#a"
    res_5a = engine.check_format(expected_5a, actual_5a)
    print("  Subcase A Patterns:", res_5a["patterns"])
    assert len(res_5a["patterns"]) == 1
    assert res_5a["patterns"][0]["type"] == "paragraph_indentation_error"
    assert len(res_5a["diffs"]) == 0
    print("  [OK] Subcase A collapsed successfully.")
    
    expected_5b = [{"type": "body", "text": f"P {i}"} for i in range(10)]
    actual_5b = "\n\n".join([f" P {i}" if i < 3 else f"  P {i}" for i in range(10)]) + "\n#a"
    res_5b = engine.check_format(expected_5b, actual_5b)
    print("  Subcase B Patterns:", res_5b["patterns"])
    assert len(res_5b["patterns"]) == 0
    reported = [d for d in res_5b["diffs"] if d["confidence"] == "needs_review"]
    assert len(reported) == 3
    print("  [OK] Subcase B shown normally per-page.")
    print("[OK] Test 5 passed.")

    # -------------------------------------------------------------
    # Case 6: State isolation test
    # -------------------------------------------------------------
    print("\n--- Test 6: State isolation ---")
    engine_iso = FormatEngine()
    engine_iso.check_format(expected_3, actual_3)
    res_iso2 = engine_iso.check_format(expected_1, actual_1)
    print("  Second run diffs:", res_iso2["diffs"])
    assert len(res_iso2["diffs"]) == 0
    print("[OK] Test 6 passed.")

    # -------------------------------------------------------------
    # Case 7: Heading level collapse detection
    # -------------------------------------------------------------
    print("\n--- Test 7: Heading level collapse detection ---")
    expected_7 = [
        {"type": "heading1", "text": "H1 Title"},
        {"type": "heading2", "text": "H2 Subtitle"}
    ]
    actual_7 = "\n\n    H1 Title\n1\n\n    H2 Subtitle\n2\n#b"
    res_7 = engine.check_format(expected_7, actual_7)
    print(json.dumps(res_7, indent=2))
    collapse_errors = [d for d in res_7["diffs"] if d["type"] == "heading_level_collapse"]
    assert len(collapse_errors) == 1
    assert collapse_errors[0]["confidence"] == "high_confidence"
    print("[OK] Test 7 passed.")

    # -------------------------------------------------------------
    # Case 8: Heading at page start bypasses spacing requirement (New check)
    # -------------------------------------------------------------
    print("\n--- Test 8: Heading at start of page (spacing check bypassed) ---")
    expected_8 = [
        {"type": "body", "text": "Preceding page paragraph."},
        {"type": "heading1", "text": "New Page Heading"}
    ]
    # Page 1 contains preceding paragraph. Page 2 begins with "New Page Heading" with 0 blank lines before it.
    actual_8 = "  Preceding page paragraph.\n#a\x0cNew Page Heading\n#b"
    res_8 = engine.check_format(expected_8, actual_8)
    print(json.dumps(res_8, indent=2))
    # Should not produce any spacing errors
    spacing_errors_8 = [d for d in res_8["diffs"] if d["type"] == "heading_spacing_error"]
    assert len(spacing_errors_8) == 0, "Heading at start of page should not raise spacing error"
    print("[OK] Test 8 passed.")

if __name__ == "__main__":
    run_test_cases()
