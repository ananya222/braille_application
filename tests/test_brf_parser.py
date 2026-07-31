import os
import sys
import ctypes
from braille_app.brf_parser import BRFParser, generate_fake_brf_content  # updated import

# Reconfigure stdout/stderr for Unicode Braille character rendering
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Set up Liblouis environment so we can back-translate parsed ASCII Braille lines.
# vendor/liblouis-win64 lives two levels above this file (tests/ → root → vendor/).
tables_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "vendor", "liblouis-win64", "share", "liblouis", "tables")
)
os.environ["LOUIS_TABLEPATH"] = tables_dir
if sys.platform == "win32":
    try:
        ctypes.CDLL("msvcrt")._wputenv(f"LOUIS_TABLEPATH={tables_dir}")
    except Exception:
        pass

try:
    import louis
    HAS_LOUIS = True
except ImportError:
    HAS_LOUIS = False
    print("Warning: liblouis Python package not found, skipping back-translation test.")

# Output directory for generated test files
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def test_parser():
    print("=" * 60)
    print("RUNNING BRF PARSER VERIFICATION WITH MOCK BRF DATA")
    print("=" * 60)

    # 1. Generate and write mock BRF content to tests/output/
    brf_content = generate_fake_brf_content()
    brf_file_path = os.path.join(OUTPUT_DIR, "mock_test.brf")

    with open(brf_file_path, "w", encoding="utf-8") as f:
        f.write(brf_content)
    print(f"Generated fake BRF file: {os.path.abspath(brf_file_path)}")

    # 2. Instantiate and execute the parser
    # Config is default (line width = 40, page lines = 25, footer-right page numbers)
    parser = BRFParser()
    result = parser.parse_file(brf_file_path)
    parsed_pages = result["pages"]
    detected_patterns = result["detected_patterns"]

    print(f"\nParsed {len(parsed_pages)} pages successfully.")

    # ── Calibration Report ───────────────────────────────────────────
    cal = parser.last_calibration
    cfg_w = parser.config["expected_line_width"]
    cfg_l = parser.config["expected_page_lines"]
    det_w = cal["detected_line_width"]
    det_l = cal["detected_page_lines"]

    print("\n" + "=" * 60)
    print("CALIBRATION REPORT")
    print("=" * 60)
    print(f"  Line Width  — detected: {det_w} cells   configured: {cfg_w} cells  "
          f"{'✓ MATCH' if det_w == cfg_w else '✗ MISMATCH'}")
    print(f"  Page Length — detected: {det_l} lines   configured: {cfg_l} lines  "
          f"{'✓ MATCH' if det_l == cfg_l else '✗ MISMATCH'}")
    print(f"\n  Line-length frequency table (length: count):")
    for length, count in sorted(cal["line_width_counts"].items()):
        marker = "  <-- modal (detected)" if length == det_w else ""
        print(f"    {length:4d} chars : {count:4d} lines{marker}")
    print(f"\n  Page-length frequency table (lines/page: count):")
    for page_len, count in sorted(cal["page_length_counts"].items()):
        marker = "  <-- modal (detected)" if page_len == det_l else ""
        print(f"    {page_len:4d} lines : {count:4d} pages{marker}")
    print("=" * 60 + "\n")
    # ─────────────────────────────────────────────────────────────────

    # ── Pattern Detection Report ─────────────────────────────────────
    if detected_patterns:
        print("=" * 60)
        print("SYSTEMIC PATTERNS DETECTED")
        print("=" * 60)
        for pattern in detected_patterns:
            print(f"  * {pattern['message']}")
            print(f"    Affected pages: {pattern['pages']}")
        print("=" * 60 + "\n")
    else:
        print("No systemic patterns detected (>30% of pages).\n")
    # ─────────────────────────────────────────────────────────────────

    for page in parsed_pages:
        idx = page["page_index"]
        print("+" + "-" * 58 + "+")
        print(f" PAGE {idx} SUMMARY ")
        print("+" + "-" * 58 + "+")
        print(f"  Line count           : {page['line_count']}")
        print(f"  Extracted Page Number: {page['extracted_page_number']}")

        hc = page["high_confidence"]
        # Show only unsuppressed/reported ones in the per-page summary
        nr_reported = page["needs_review_reported"]
        nr_suppressed = page["needs_review_suppressed"]

        if hc:
            print("  HIGH CONFIDENCE issues:")
            for issue in hc:
                print(f"    \u2717 {issue}")
        else:
            print("  High Confidence      : NONE")

        if nr_reported:
            print("  NEEDS REVIEW issues (unsuppressed):")
            for issue in nr_reported:
                # issue is now a dict
                print(f"    ? {issue['message']}")
        else:
            print("  Needs Review         : NONE")

        if nr_suppressed:
            print(f"  Needs Review (suppressed by systemic pattern): {len(nr_suppressed)} issue(s)")


        print("\n  Sample Raw Braille Lines (ASCII vs Unicode):")
        printed_lines = 0
        for ascii_line, unicode_line in zip(page["raw_lines"], page["unicode_braille_lines"]):
            if ascii_line.strip() and printed_lines < 3:
                print(f"    ASCII:   {ascii_line.strip()}")
                print(f"    Unicode: {unicode_line.strip()}")

                if HAS_LOUIS:
                    try:
                        translated_text = louis.backTranslateString(["en-ueb-g2.ctb"], ascii_line.strip())
                        print(f"    Text:    {translated_text}")
                    except Exception as e:
                        print(f"    Text:    (Translation failed: {e})")
                print("-" * 50)
                printed_lines += 1

    # Clean up generated BRF file
    if os.path.exists(brf_file_path):
        os.remove(brf_file_path)
        print("\nCleaned up mock BRF file.")


def test_pattern_detection_by_type_field():
    print("\n" + "=" * 60)
    print("TESTING PATTERN DETECTION GROUPING BY TYPE FIELD DIRECTLY")
    print("=" * 60)

    # 1. Manually set up parsed pages with a deliberately reworded warning
    # and the correct "type" field. We have 5 pages total, and 4 pages
    # contain the reworded warning for "line-width" (80% frequency).
    parser = BRFParser()
    dummy_pages = [
        {
            "page_index": 1,
            "needs_review": [{"type": "line-width", "message": "This line is way too chunky!!", "line_idx": 5}]
        },
        {
            "page_index": 2,
            "needs_review": [{"type": "line-width", "message": "Extremely fat line encountered!", "line_idx": 10}]
        },
        {
            "page_index": 3,
            "needs_review": [{"type": "line-width", "message": "Wide lines are wide.", "line_idx": 12}]
        },
        {
            "page_index": 4,
            "needs_review": []  # Under 30% page-number-alignment (1 of 5 = 20%)
        },
        {
            "page_index": 5,
            "needs_review": [{"type": "line-width", "message": "Another unusually bulky row.", "line_idx": 1}]
        }
    ]

    # Create dummy content to pass splitlines/split counts
    # and override parse_content internal behavior to test pattern-detection post-pass
    content = "\x0c\x0c\x0c\x0c\x0c"  # 5 pages
    
    # Temporarily monkeypatch _parse_page to return our pre-built dummy_pages
    original_parse_page = parser._parse_page
    iterator = iter(dummy_pages)
    parser._parse_page = lambda raw, idx: next(iterator)

    # Invoke parse_content (which triggers pattern detection internally)
    result = parser.parse_content(content)
    
    # Restore the method
    parser._parse_page = original_parse_page

    detected_patterns = result["detected_patterns"]

    print("Detected Patterns:")
    for pat in detected_patterns:
        print(f"  Type: {pat['type']} | Message: {pat['message']}")
        print(f"  Pages affected: {pat['pages']}")

    # Verify that the pattern was successfully detected for "line-width"
    # despite the randomized messages
    assert len(detected_patterns) == 1, "Should detect exactly one pattern type"
    assert detected_patterns[0]["type"] == "line-width", "Detected type must be 'line-width'"
    assert detected_patterns[0]["pages"] == [1, 2, 3, 5], "Pages [1, 2, 3, 5] should be affected"
    print("\n✓ SUCCESS: Grouping and pattern detection is confirmed to use the 'type' field directly!")
    print("=" * 60 + "\n")

def test_custom_mock_scenarios():
    print("\n" + "=" * 60)
    print("RUNNING THREE CUSTOM PATTERN THRESHOLD SCENARIOS")
    print("=" * 60)

    # Output directory for test files
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    parser = BRFParser()

    # -------------------------------------------------------------
    # Scenario 1: Exactly 4 of 10 pages (40% > 30%) have line-width issue
    # Expected: Pattern detected & per-page entries suppressed.
    # -------------------------------------------------------------
    print("\n--- Scenario 1: 4 of 10 pages (40% > 30%) with line-width issues ---")
    content_s1 = generate_fake_brf_content(total_pages=10, line_width_issue_pages=[1, 2, 3, 4], alignment_issue_pages=[])
    res_s1 = parser.parse_content(content_s1)
    
    # Check assertions
    pattern_types = [p["type"] for p in res_s1["detected_patterns"]]
    print(f"  Detected pattern types: {pattern_types}")
    assert "line-width" in pattern_types, "Pattern detection should have fired for line-width"
    print("  ✓ Pattern successfully fired (above 30% limit).")
    
    # Verify per-page suppression
    suppressed_count = sum(len(page["needs_review_suppressed"]) for page in res_s1["pages"])
    reported_count = sum(len(page["needs_review_reported"]) for page in res_s1["pages"])
    print(f"  Suppressed per-page warnings: {suppressed_count} | Reported per-page warnings: {reported_count}")
    assert suppressed_count > 0, "Line-width warnings should be suppressed from individual pages"
    assert reported_count == 0, "No line-width warnings should remain reported per-page"
    print("  ✓ Widespread warnings successfully suppressed from per-page output.")

    # -------------------------------------------------------------
    # Scenario 2: Exactly 2 of 10 pages (20% < 30%) have line-width issue
    # Expected: Pattern NOT detected & per-page entries unsuppressed.
    # -------------------------------------------------------------
    print("\n--- Scenario 2: 2 of 10 pages (20% < 30%) with line-width issues ---")
    content_s2 = generate_fake_brf_content(total_pages=10, line_width_issue_pages=[1, 2], alignment_issue_pages=[])
    res_s2 = parser.parse_content(content_s2)
    
    # Check assertions
    pattern_types_s2 = [p["type"] for p in res_s2["detected_patterns"]]
    print(f"  Detected pattern types: {pattern_types_s2}")
    assert "line-width" not in pattern_types_s2, "Pattern detection should NOT have fired for line-width"
    print("  ✓ Pattern did not fire (below 30% threshold).")
    
    # Verify per-page unsuppressed
    suppressed_count_s2 = sum(len(page["needs_review_suppressed"]) for page in res_s2["pages"])
    reported_count_s2 = sum(len(page["needs_review_reported"]) for page in res_s2["pages"])
    print(f"  Suppressed per-page warnings: {suppressed_count_s2} | Reported per-page warnings: {reported_count_s2}")
    assert suppressed_count_s2 == 0, "No warnings should be suppressed"
    assert reported_count_s2 > 0, "Warnings should appear normally per-page"
    print("  ✓ Rare/isolated warnings shown normally per-page.")

    # -------------------------------------------------------------
    # Scenario 3: Mixed Issues (4 line-width [40%] + 1 alignment [10%] out of 10)
    # Expected: ONLY line-width pattern detected & suppressed; alignment shows normally.
    # -------------------------------------------------------------
    print("\n--- Scenario 3: Mixed (4 line-width [40%] + 1 alignment [10%]) out of 10 ---")
    content_s3 = generate_fake_brf_content(total_pages=10, line_width_issue_pages=[1, 2, 3, 4], alignment_issue_pages=[5])
    res_s3 = parser.parse_content(content_s3)
    
    # Check assertions
    pattern_types_s3 = [p["type"] for p in res_s3["detected_patterns"]]
    print(f"  Detected pattern types: {pattern_types_s3}")
    assert "line-width" in pattern_types_s3, "Line-width pattern should fire"
    assert "page-number-alignment" not in pattern_types_s3, "Alignment pattern should NOT fire"
    print("  ✓ Only line-width pattern fired as expected.")

    # Verify that alignment on Page 5 is reported normally, but line-width is suppressed
    page_5 = res_s3["pages"][4]
    print(f"  Page 5 summary:")
    print(f"    Reported needs_review:   {[i['type'] for i in page_5['needs_review_reported']]}")
    print(f"    Suppressed needs_review: {[i['type'] for i in page_5['needs_review_suppressed']]}")
    
    assert any(i["type"] == "page-number-alignment" for i in page_5["needs_review_reported"]), "Page 5 alignment must be reported"
    assert not any(i["type"] == "line-width" for i in page_5["needs_review_reported"]), "Page 5 line-width must be suppressed"
    print("  ✓ Systemic issues collapsed, isolated/rare issues left visible per-page.")
    print("=" * 60 + "\n")

def test_boundary_scenario_exactly_30_percent():
    print("\n" + "=" * 60)
    print("RUNNING BOUNDARY TEST: EXACTLY 30% THRESHOLD")
    print("=" * 60)

    parser = BRFParser()
    # Exactly 3 of 10 pages have line-width issues (30.0%)
    content = generate_fake_brf_content(total_pages=10, line_width_issue_pages=[1, 2, 3], alignment_issue_pages=[])
    res = parser.parse_content(content)

    pattern_types = [p["type"] for p in res["detected_patterns"]]
    print(f"  Detected pattern types: {pattern_types}")
    assert "line-width" not in pattern_types, "Pattern detection should NOT have fired for exactly 30%"
    print("  ✓ Strict threshold match verified: 30% exactly does not trigger pattern reporting.")

    # Verify per-page unsuppressed
    suppressed_count = sum(len(page["needs_review_suppressed"]) for page in res["pages"])
    reported_count = sum(len(page["needs_review_reported"]) for page in res["pages"])
    print(f"  Suppressed per-page warnings: {suppressed_count} | Reported per-page warnings: {reported_count}")
    assert suppressed_count == 0, "No warnings should be suppressed at exactly 30%"
    assert reported_count > 0, "Warnings should appear normally per-page"
    print("  ✓ All warnings shown normally per-page.")
    print("=" * 60 + "\n")

def test_cross_file_reuse_isolation():
    print("\n" + "=" * 60)
    print("RUNNING CROSS-FILE REUSE ISOLATION TEST")
    print("=" * 60)

    parser = BRFParser()

    # 1. Parse File A (Strong pattern: 8 of 10 pages)
    print("  Processing File A (Widespread issues)...")
    content_a = generate_fake_brf_content(total_pages=10, line_width_issue_pages=[1, 2, 3, 4, 5, 6, 7, 8], alignment_issue_pages=[])
    res_a = parser.parse_content(content_a)
    assert len(res_a["detected_patterns"]) == 1, "File A must trigger line-width pattern"
    
    # 2. Immediately parse File B (Clean file: 10 pages with zero issues)
    print("  Processing File B (Zero issues)...")
    content_b = generate_fake_brf_content(total_pages=10, line_width_issue_pages=[], alignment_issue_pages=[])
    res_b = parser.parse_content(content_b)

    # Check that File B's results are completely clean
    pattern_types_b = [p["type"] for p in res_b["detected_patterns"]]
    print(f"  File B detected pattern types: {pattern_types_b}")
    assert len(res_b["detected_patterns"]) == 0, "File B must not have any patterns"
    
    total_needs_review_b = sum(len(page["needs_review"]) for page in res_b["pages"])
    print(f"  File B total needs_review issues: {total_needs_review_b}")
    assert total_needs_review_b == 0, "File B must have 0 needs_review issues"
    print("  ✓ Re-use isolation confirmed: parser instance state does not leak between sequential calls.")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    test_parser()
    test_pattern_detection_by_type_field()
    test_custom_mock_scenarios()
    test_boundary_scenario_exactly_30_percent()
    test_cross_file_reuse_isolation()



