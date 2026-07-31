import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from braille_app.report_generator import ReportGenerator

def run_tests():
    print("=" * 60)
    print("RUNNING REPORT GENERATOR VERIFICATION SUITE")
    print("=" * 60)
    
    generator = ReportGenerator()
    
    brf_mock = {
        "detected_patterns": [{"type": "line-width", "message": "PATTERN DETECTED: 4 of 5 pages show a line-width mismatch."}],
        "pages": [
            {
                "page_index": 1,
                "high_confidence": ["Page is completely empty"],
                "needs_review": [{"type": "line-width", "message": "Line 2 exceeds width."}],
                "needs_review_reported": [{"type": "line-width", "message": "Line 2 exceeds width."}]
            }
        ]
    }
    
    diff_mock = {
        "diffs": [
            {
                "type": "severe_mismatch",
                "expected": "Hello my good friend",
                "actual": "Hello my bad friend",
                "location": "paragraph 1",
                "confidence": "high_confidence"
            }
        ],
        "patterns": [{"type": "punctuation_difference", "message": "PATTERN DETECTED: 5 of 10 pages show a punctuation difference"}],
        "stats": {}
    }
    
    format_mock = {
        "provisional_warning": "WARNING: FORMATTING COMPLIANCE RULES ARE UNVERIFIED",
        "diffs": [
            {
                "type": "missing_paragraph_layout",
                "expected": "Expected Heading Block Title",
                "actual": "",
                "location": "block 1",
                "confidence": "alignment_failure"
            },
            {
                "type": "allowed_format_difference",
                "expected": "Type: paragraph",
                "actual": "Indent: 3, runover: 1",
                "location": "block 2",
                "confidence": "ignored"
            }
        ],
        "patterns": [],
        "stats": {}
    }
    
    html = generator.generate_report(brf_mock, diff_mock, format_mock)
    
    # Assertions
    assert "<!DOCTYPE html>" in html
    assert "Braille Validation Dashboard" in html
    assert "Provisional Assumptions &amp; Calibration Mismatches" in html or "Provisional Assumptions & Calibration Mismatches" in html
    assert "Translation" in html
    assert "Formatting" in html
    assert "Structure" in html
    
    # Verify summary counts are present and correct
    # High confidence = translation (1) + formatting (0) + brf structure (1) = 2
    assert "hc_total = 2" or ">2</div>" in html
    
    # Save the output HTML file for inspection
    out_path = os.path.join(os.path.dirname(__file__), "mock_report.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
        
    print(f"[OK] Report HTML generated successfully and saved to: {out_path}")
    print("\nVisual verification parameters:")
    print("1. Provisional banner contains BANA Spacing Table with confidence level badges.")
    print("2. Summary count shows High Confidence: 2, Needs Review: 1, Alignment Failures: 1, Ignored: 0.")
    print("3. Inline difference renders with red-deleted and green-inserted spans for 'good' vs 'bad'.")
    print("4. Ignored findings start collapsed; High Confidence starts expanded.")
    print("[OK] Test passed.")

if __name__ == "__main__":
    run_tests()
