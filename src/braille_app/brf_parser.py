import os
import re
import sys
import logging
from collections import Counter

# Set up logging to stdout for warning visibility
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger("BRFParser")

# =====================================================================
# CONFIGURATION BLOCK
# =====================================================================
# These are the top-level configuration values. 
# They are named and gathered here to allow easy recalibration once 
# real Duxbury files are available.
DEFAULT_BRF_CONFIG = {
    # -----------------------------------------------------------------
    # 1. Page Layout Assumptions
    # -----------------------------------------------------------------
    # Confirmed Spec: BRF files use standard 40-cell width and 25-line length
    # as common defaults, but these vary based on braille transcriber settings.
    "expected_line_width": 40,  # Expected characters per line
    "expected_page_lines": 25,  # Expected lines per page (including header/footer)

    # -----------------------------------------------------------------
    # 2. Page Numbering Assumptions
    # -----------------------------------------------------------------
    # Duxbury Guess: Page numbers might appear in the first line (header) 
    # or last line (footer) of a page, and are typically right-aligned.
    # Allowed options: "header" (index 0), "footer" (index -1), or None (ignore check)
    "page_number_position": "footer", 
    "page_number_alignment": "right",  # "left" or "right"

    # Duxbury Guess: Page numbers can be standard Arabic numerals (e.g. 1, 2) 
    # or ASCII Braille numbers. In ASCII Braille, numbers are prefixed with '#'
    # and use letters a-j (e.g. #a=1, #b=2, #c=3 ... #j=0, so #be = 25).
    # This regex matches either standard digits or ASCII Braille numbers.
    "page_number_pattern": r"(#[a-j]+|\d+)",
}

# =====================================================================
# ASCII BRAILLE TO STANDARD BRAILLE CODEPOINTS MAP (Helper)
# =====================================================================
# Confirmed Spec: Standard mapping of ASCII printable characters to 
# Confirmed Spec: Standard mapping of ASCII printable characters to 
# Unicode Braille patterns (U+2800 - U+283F) using NABCC standard.
_NABCC_STR = " a1b'k2l@cif/msp\"e3h9o6r^djg>ntq,*5<-u8v.%[$+x!&;:4\\0z7(_?w]#y)="
ASCII_TO_UNICODE_BRAILLE = {
    c: chr(0x2800 + i) for i, c in enumerate(_NABCC_STR)
}
# Map uppercase letters to the same braille patterns as lowercase
for i, c in enumerate(_NABCC_STR):
    if c.isalpha() and c.islower():
        ASCII_TO_UNICODE_BRAILLE[c.upper()] = chr(0x2800 + i)

def ascii_to_unicode_braille(text: str) -> str:
    """Converts a string of ASCII Braille characters into Unicode Braille patterns."""
    return "".join(ASCII_TO_UNICODE_BRAILLE.get(c, c) for c in text)

def braille_number_to_int(braille_num: str) -> int:
    """
    Duxbury Guess / UEB Standard: Converts a braille number (e.g. '#be' or '#e') to integer.
    In ASCII Braille, '#' represents the number sign.
    The letters a-j represent digits 1-9, and j represents 0.
    """
    if not braille_num.startswith('#'):
        # Fallback to standard digit parsing if it's already an Arabic numeral
        try:
            return int(braille_num)
        except ValueError:
            return -1
            
    digit_map = {
        'a': '1', 'b': '2', 'c': '3', 'd': '4', 'e': '5',
        'f': '6', 'g': '7', 'h': '8', 'i': '9', 'j': '0'
    }
    
    digits = []
    for char in braille_num[1:]:
        digit = digit_map.get(char.lower())
        if digit:
            digits.append(digit)
        else:
            # Non-number character inside the number pattern
            return -1
    return int("".join(digits)) if digits else -1


# =====================================================================
# BRF PARSER CLASS
# =====================================================================
class BRFParser:
    def __init__(self, config: dict = None):
        self.config = {**DEFAULT_BRF_CONFIG, **(config or {})}
        
    def parse_file(self, file_path: str) -> dict:
        """
        Parses a BRF file and returns a dictionary containing parsed pages and detected patterns.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"BRF file not found: {file_path}")
            
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            
        return self.parse_content(content)
        
    def parse_content(self, content: str) -> dict:
        """
        Parses raw BRF content.
        Confirmed Spec: BRF pages are split by form-feed (0x0C, '\x0c') characters.
        """
        # Split pages based on form-feed character
        raw_pages = content.split('\x0c')

        # If the file ends with a form-feed, the last element will be empty; discard if so.
        if raw_pages and not raw_pages[-1].strip():
            raw_pages.pop()

        # ── Self-Calibration ─────────────────────────────────────────
        calibration = self._calibrate(raw_pages)
        self.last_calibration = calibration          # expose for callers

        cfg_width = self.config["expected_line_width"]
        cfg_lines = self.config["expected_page_lines"]
        det_width = calibration["detected_line_width"]
        det_lines = calibration["detected_page_lines"]

        border = "=" * 60
        if det_width != cfg_width:
            logger.warning(
                "\n%s\n"
                "CALIBRATION MISMATCH — LINE WIDTH\n"
                "  Detected  (from file) : %d cells\n"
                "  Configured (assumption): %d cells\n"
                "  Validation will use the CONFIGURED value.\n"
                "  Update DEFAULT_BRF_CONFIG['expected_line_width'] to silence this.\n"
                "%s",
                border, det_width, cfg_width, border,
            )
        else:
            logger.warning(
                "Calibration OK — line width matches config (%d cells).", det_width
            )

        if det_lines != cfg_lines:
            logger.warning(
                "\n%s\n"
                "CALIBRATION MISMATCH — PAGE LENGTH\n"
                "  Detected  (from file) : %d lines\n"
                "  Configured (assumption): %d lines\n"
                "  Validation will use the CONFIGURED value.\n"
                "  Update DEFAULT_BRF_CONFIG['expected_page_lines'] to silence this.\n"
                "%s",
                border, det_lines, cfg_lines, border,
            )
        else:
            logger.warning(
                "Calibration OK — page length matches config (%d lines).", det_lines
            )
        # ─────────────────────────────────────────────────────────────

        # Initial parsing of all pages
        parsed_pages = []
        for idx, raw_page in enumerate(raw_pages, start=1):
            page_data = self._parse_page(raw_page, idx)
            parsed_pages.append(page_data)

        # ── Pattern Detection ────────────────────────────────────────
        # 1. Group occurrences of each issue type
        issue_pages_map = {}
        for page in parsed_pages:
            page_num = page["page_index"]
            for issue in page["needs_review"]:
                itype = issue["type"]
                issue_pages_map.setdefault(itype, []).append((page_num, issue))

        total_pages = len(parsed_pages)
        detected_patterns = []
        suppressed_types = set()

        if total_pages > 0:
            for itype, occurrences in issue_pages_map.items():
                unique_pages = sorted(list(set(p for p, _ in occurrences)))
                pct = (len(unique_pages) / total_pages) * 100
                if pct > 30.0:
                    suppressed_types.add(itype)
                    msg = (
                        f"PATTERN DETECTED: {len(unique_pages)} of {total_pages} pages ({pct:.0f}%) "
                        f"show a {itype} mismatch. This suggests the tool's configuration doesn't match "
                        f"this document's actual format — recommend recalibrating (see CALIBRATION REPORT above) "
                        f"before treating individual page findings as final."
                    )
                    detected_patterns.append({
                        "type": itype,
                        "percentage": pct,
                        "pages": unique_pages,
                        "message": msg
                    })

        # 2. Suppress console summaries for matching types but preserve underlying data
        for page in parsed_pages:
            # We keep the original list under needs_review for JSON integrity, but add
            # needs_review_reported to store the unsuppressed ones for rendering.
            # This preserves the full underlying data in the JSON structure.
            page["needs_review_reported"] = [
                iss for iss in page["needs_review"] if iss["type"] not in suppressed_types
            ]
            page["needs_review_suppressed"] = [
                iss for iss in page["needs_review"] if iss["type"] in suppressed_types
            ]

        # Reset state on instance for safety, but primary output is returned
        self.last_detected_patterns = detected_patterns

        return {
            "pages": parsed_pages,
            "detected_patterns": detected_patterns
        }

    def _calibrate(self, raw_pages: list[str]) -> dict:
        """
        Scans all pages and detects the most likely line width and page
        length from the file itself, using modal (most-common) values.

        Line width  — modal length of all non-empty lines across every page.
        Page length — modal line-count across all pages.

        Returns a dict with:
          detected_line_width  : int  — modal non-empty line length
          detected_page_lines  : int  — modal lines-per-page
          line_width_counts    : dict — full frequency table for widths
          page_length_counts   : dict — full frequency table for page sizes
        """
        line_length_counter: Counter = Counter()
        page_length_counter: Counter = Counter()

        for raw_page in raw_pages:
            lines = raw_page.splitlines()
            page_length_counter[len(lines)] += 1

            for line in lines:
                # Only count non-empty lines — blank padding lines are not
                # representative of the intended line width.
                if line.strip():
                    line_length_counter[len(line)] += 1

        # Modal values; fall back to config defaults if the file is empty.
        if line_length_counter:
            detected_width = line_length_counter.most_common(1)[0][0]
        else:
            detected_width = self.config["expected_line_width"]

        if page_length_counter:
            detected_page_lines = page_length_counter.most_common(1)[0][0]
        else:
            detected_page_lines = self.config["expected_page_lines"]

        return {
            "detected_line_width": detected_width,
            "detected_page_lines": detected_page_lines,
            "line_width_counts": dict(line_length_counter.most_common()),
            "page_length_counts": dict(page_length_counter.most_common()),
        }

    def _parse_page(self, raw_page: str, page_number: int) -> dict:
        """
        Parses an individual page of a BRF document and classifies findings
        into two tiers:

          high_confidence — true regardless of any config assumption:
            • Page is completely empty (no braille content at all)
            • Page number token matched the pattern but decoded to an invalid integer

          needs_review — depends on configured / detected layout values being correct:
            • Page line count differs from expected_page_lines
            • A line is longer than expected_line_width
            • Page number not found at the expected position
            • Page number token is not right-aligned within the allowed margin
        """
        high_confidence: list[str] = []
        needs_review:    list[dict] = []

        # Split the page into individual lines (preserving blank layout lines).
        raw_lines = raw_page.splitlines()
        line_count = len(raw_lines)

        # ── HIGH CONFIDENCE: completely empty page ────────────────────
        if line_count == 0 or all(not ln.strip() for ln in raw_lines):
            high_confidence.append(
                "Page is completely empty — no braille content found."
            )

        # ── NEEDS REVIEW: page length (depends on expected_page_lines) ─
        expected_len = self.config["expected_page_lines"]
        if line_count != expected_len:
            needs_review.append({
                "type": "page-length",
                "message": f"Page length mismatch: expected {expected_len} lines, but found {line_count}."
            })

        # ── NEEDS REVIEW: line width (depends on expected_line_width) ──
        expected_width = self.config["expected_line_width"]
        for line_idx, line in enumerate(raw_lines, start=1):
            if len(line) > expected_width:
                needs_review.append({
                    "type": "line-width",
                    "message": f"Line {line_idx} exceeds expected line width of {expected_width} (length={len(line)}).",
                    "line_idx": line_idx
                })

        # ── Page number extraction & validation ───────────────────────
        extracted_page_num = None
        pos     = self.config["page_number_position"]
        align   = self.config["page_number_alignment"]
        pattern = self.config["page_number_pattern"]

        if pos is not None and raw_lines:
            target_line_idx = 0 if pos == "header" else -1
            if abs(target_line_idx) < len(raw_lines):
                target_line = raw_lines[target_line_idx]
                matches = list(re.finditer(pattern, target_line))

                if matches:
                    # Rightmost token is the page number candidate.
                    matched_token = matches[-1]
                    matched_value = matched_token.group(0)
                    decoded = braille_number_to_int(matched_value)

                    if decoded == -1:
                        # HIGH CONFIDENCE: token matched the regex but is not
                        # a valid braille number — not a config assumption.
                        high_confidence.append(
                            f"Page number field '{matched_value}' matched the "
                            f"pattern but could not be decoded to a valid integer."
                        )
                    else:
                        extracted_page_num = decoded

                    # NEEDS REVIEW: alignment depends on page_number_alignment config.
                    if align == "right":
                        margin = len(target_line) - matched_token.end()
                        if margin > 3:
                            needs_review.append({
                                "type": "page-number-alignment",
                                "message": f"Page number '{matched_value}' is not right-aligned (trailing margin = {margin} cells)."
                            })
                else:
                    # NEEDS REVIEW: depends on page_number_position config being correct.
                    needs_review.append({
                        "type": "page-number-missing",
                        "message": f"Page number pattern not found on the expected {pos} line."
                    })

        # ── Logging ───────────────────────────────────────────────────
        # Use ERROR for high_confidence (config-independent, always actionable).
        # Use WARNING for needs_review (config-dependent, may be a false alarm).
        for issue in high_confidence:
            logger.error("[Page %d][HIGH] %s", page_number, issue)
        for issue in needs_review:
            logger.warning("[Page %d][REVIEW] %s", page_number, issue["message"])

        return {
            "page_index":           page_number,
            "raw_lines":            raw_lines,
            "line_count":           line_count,
            "extracted_page_number": extracted_page_num,
            "high_confidence":      high_confidence,
            "needs_review":         needs_review,
            "unicode_braille_lines": [ascii_to_unicode_braille(ln) for ln in raw_lines],
        }


# =====================================================================
# FAKE BRF FILE GENERATION (Helper for test validation)
# =====================================================================
def generate_fake_brf_content(
    total_pages: int = 5,
    line_width_issue_pages: list[int] = None,
    alignment_issue_pages: list[int] = None
) -> str:
    """
    Generates a mock BRF file adhering to standard layout specs:
    - 25 lines per page
    - Config default is 40 cells per line
    - Parameterizable page count and page-specific issue locations
    """
    if line_width_issue_pages is None:
        line_width_issue_pages = [1, 2, 3, 5]
    if alignment_issue_pages is None:
        alignment_issue_pages = [4]

    # Helper to build a page with a specific line width
    def build_page(num: int, line_width: int, text_str: str, page_num_str: str, align_middle: bool = False) -> str:
        padded_text = text_str.ljust(line_width)[:line_width]
        lines = [padded_text]
        empty_line = " " * line_width
        while len(lines) < 24:
            lines.append(empty_line)
        
        if align_middle:
            half = line_width // 2
            footer = (" " * half) + page_num_str + (" " * (line_width - half - len(page_num_str)))
        else:
            footer = page_num_str.rjust(line_width)
        lines.append(footer)
        return "\n".join(lines)

    pages = []
    for i in range(1, total_pages + 1):
        has_width_issue = i in line_width_issue_pages
        has_align_issue = i in alignment_issue_pages
        
        width = 42 if has_width_issue else 40
        page_num_str = f"#{chr(96 + i)}" if i <= 26 else f"#{i}"
        
        pages.append(build_page(
            num=i,
            line_width=width,
            text_str=f",page {i} content",
            page_num_str=page_num_str,
            align_middle=has_align_issue
        ))

    return "\x0c".join(pages)

