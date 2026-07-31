import sys
import os
import ctypes
import json
import logging

# Configure python logging to display warnings to console
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)

# Setup paths relative to execution environment
if hasattr(sys, "_MEIPASS"):
    base_dir = sys._MEIPASS
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

# Configure environment variables for liblouis DLL loading
tables_dir = os.path.join(base_dir, "vendor", "liblouis-win64", "share", "liblouis", "tables")
if not os.path.exists(tables_dir):
    # Fallback to local workspace paths
    tables_dir = os.path.abspath(os.path.join(base_dir, "vendor", "liblouis-win64", "share", "liblouis", "tables"))

os.environ["LOUIS_TABLEPATH"] = tables_dir
if sys.platform == "win32":
    try:
        ctypes.CDLL("msvcrt")._wputenv(f"LOUIS_TABLEPATH={tables_dir}")
    except Exception:
        pass

# Add module directories to system path
sys.path.insert(0, os.path.join(base_dir, "vendor", "liblouis-bindings"))
sys.path.insert(0, os.path.join(base_dir, "src"))

try:
    import louis
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "vendor", "liblouis-bindings")))
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))
    import louis

# Initialize liblouis tables path
try:
    louis.liblouis.lou_setDataPath.argtypes = [ctypes.c_char_p]
    louis.liblouis.lou_setDataPath.restype = None
    louis.liblouis.lou_setDataPath(tables_dir.encode('utf-8'))
except Exception:
    pass

from braille_app.doc_extractor import DocumentExtractor
from braille_app.brf_parser import BRFParser
from braille_app.input_reader import read_braille_input

import re as _re

def _legacy_post_process_expected(ascii_brf: str, grade: int) -> str:
    """
    Apply UEB post-processing corrections dynamically loaded from ueb_corrections.yaml.
    Filters by grade and applies Category A and B fixes.
    """
    # The selected liblouis UEB table is authoritative. Context-free regex
    # rewrites of quote/equality cells turned valid Grade 1 text into false diffs.
    return ascii_brf

    # Protect capital passage terminator from single quote regexes
    ascii_brf = ascii_brf.replace(",'", "___CAP_TERM___")

    manager = UEBCorrectionsManager()
    rules = manager.get_post_process_rules(grade)
    
    for rule in rules:
        rx_match = rule.get("regex_match")
        rx_replace = rule.get("regex_replace")
        if not rx_match or not rx_replace:
            continue
            
        if rx_match == "special_single_quotes":
            # Converts boundary apostrophes to correct opening (⠠⠦ / ,8) and closing (⠠⠴ / ,0) single quotes
            ascii_brf = _re.sub(r"(?<=\S)'(?= |$)", ",0", ascii_brf)
            ascii_brf = _re.sub(r"(^| )'(?=\S)", r"\1,8", ascii_brf)
        elif rx_replace == "special_equals_spacing":
            # Signs of comparison in UEB are normally spaced on both sides.
            ascii_brf = _re.sub(r'(?<=\S)"7', r' "7', ascii_brf)
            ascii_brf = _re.sub(r'"7(?=\S)', r'"7 ', ascii_brf)
        else:
            ascii_brf = _re.sub(rx_match, rx_replace, ascii_brf)
            
    # Restore capital passage terminator
    ascii_brf = ascii_brf.replace("___CAP_TERM___", ",'")
    return ascii_brf
from braille_app.diff_engine import DiffEngine
from braille_app.format_engine import FormatEngine
from braille_app.report_generator import ReportGenerator

def _legacy_read_braille_input(file_path: str) -> str:
    _, ext = os.path.splitext(file_path.lower())
    if ext == ".pdf":
        import pdfplumber
        content_pages = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                words = page.extract_words()
                if not words:
                    content_pages.append("")
                    continue
                
                lines_map = {}
                for w in words:
                    line_idx = int(round((w["top"] - 54.0) / 14.0))
                    if line_idx < 0:
                        line_idx = 0
                    lines_map.setdefault(line_idx, []).append(w)
                
                lines = []
                max_line = max(24, max(lines_map.keys()) if lines_map else 24)
                for i in range(max_line + 1):
                    if i in lines_map:
                        sorted_words = sorted(lines_map[i], key=lambda w: w["x0"])
                        line_text_raw = " ".join(w["text"] for w in sorted_words)
                        if "english (ueb)" in line_text_raw.lower():
                            continue  # Skip running header line
                        
                        first_x0 = sorted_words[0]["x0"]
                        indent_spaces = max(0, int(round((first_x0 - 54.0) / 6.6)))
                        
                        # Reconstruct words with their relative space gap
                        parts = []
                        last_end = first_x0
                        for idx, item in enumerate(sorted_words):
                            if idx > 0:
                                gap = item["x0"] - last_end
                                num_spaces = max(1, int(round(gap / 6.6)))
                                parts.append(" " * num_spaces)
                            parts.append(item["text"])
                            last_end = item["x1"]
                        
                        line_text = " " * indent_spaces + "".join(parts)
                        lines.append(line_text)
                    else:
                        lines.append("")
                content_pages.append("\n".join(lines))
        
        result_text = "\x0c".join(content_pages)
        # Check if PDF text is Unicode Braille dots, map to ASCII if so
        unicode_dots = [chr(c) for c in range(0x2800, 0x28FF)]
        if any(c in result_text for c in unicode_dots):
            from braille_app.brf_parser import ASCII_TO_UNICODE_BRAILLE
            rev_map = {v: k for k, v in ASCII_TO_UNICODE_BRAILLE.items()}
            rev_map['\u2800'] = ' '
            result_text = "".join(rev_map.get(c, c) for c in result_text)
        return result_text
    else:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            raw_text = f.read()
            # If input is Unicode dots, map back to ASCII for comparison engine
            unicode_dots = [chr(c) for c in range(0x2800, 0x28FF)]
            has_unicode = any(c in raw_text for c in unicode_dots)
            if has_unicode:
                from braille_app.brf_parser import ASCII_TO_UNICODE_BRAILLE
                rev_map = {v: k for k, v in ASCII_TO_UNICODE_BRAILLE.items()}
                # Ensure space mapping is correct
                rev_map['\u2800'] = ' '
                raw_text = "".join(rev_map.get(c, c) for c in raw_text)
            return raw_text

def _post_process_expected(ascii_brf: str, grade: int) -> str:
    """Keep the table-produced UEB Grade 1/2 cells unchanged for comparison."""
    return ascii_brf


def main():
    print("=" * 60)
    print("        BRAILLE TRANSLATION & LAYOUT VERIFICATION")
    print("=" * 60)
    
    grade = 2
    if "--grade" in sys.argv:
        try:
            idx = sys.argv.index("--grade")
            if idx + 1 < len(sys.argv):
                grade_val = sys.argv[idx + 1]
                if grade_val in ["1", "2"]:
                    grade = int(grade_val)
                sys.argv.pop(idx + 1)
                sys.argv.pop(idx)
        except Exception:
            pass

    if len(sys.argv) >= 3:
        english_file = sys.argv[1]
        braille_file = sys.argv[2]
    else:
        english_file = input("Enter path to English document (.docx or .pdf): ").strip().strip('"')
        braille_file = input("Enter path to Braille document (.pdf or .brf): ").strip().strip('"')
        
    if not os.path.exists(english_file):
        print(f"Error: English file does not exist: {english_file}")
        input("\nPress Enter to exit...")
        sys.exit(1)
    if not os.path.exists(braille_file):
        print(f"Error: Braille file does not exist: {braille_file}")
        input("\nPress Enter to exit...")
        sys.exit(1)
        
    print(f"\nProcessing English input: {english_file}")
    print(f"Processing Braille input: {braille_file}")
    
    # 1. Extract structural metadata from print document
    try:
        extractor = DocumentExtractor()
        extracted_data = extractor.extract(english_file)
    except Exception as e:
        print(f"Error extracting structural metadata from print document: {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)
        
    # 2. Read and parse Braille file
    try:
        braille_content = read_braille_input(braille_file)
        parser = BRFParser()
        brf_results = parser.parse_content(braille_content)
    except Exception as e:
        print(f"Error parsing Braille document: {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)
        
    # 3. Translate print document blocks using liblouis to produce the expected Braille string/blocks
    expected_blocks = []
    table_list = ["en-ueb-g2.ctb" if grade == 2 else "en-ueb-g1.ctb"]
    for page in extracted_data.get("pages", []):
        for block in page.get("blocks", []):
            text = block.get("text", "")
            b_type = block.get("type", "body")
            
            translated_braille = ""
            if text.strip():
                try:
                    translated_braille = louis.translateString(table_list, text)
                    translated_braille = _post_process_expected(translated_braille, grade)
                except Exception as ex:
                    print(f"Warning: translation failed for '{text[:20]}...': {ex}")
                    translated_braille = text
            
            expected_blocks.append({
                "type": b_type,
                "text": translated_braille
            })
            
    # 4. Compare expected vs actual braille as normalized streams (Translation Diff Engine)
    try:
        diff_engine = DiffEngine(grade=grade)
        actual_paragraphs = []
        for page in brf_results.get("pages", []):
            page_text = "\n".join(page.get("raw_lines", []))
            actual_paragraphs.append(page_text)
        actual_content_text = "\x0c".join(actual_paragraphs)
        
        diff_results = diff_engine.compare(expected_blocks, actual_content_text)
    except Exception as e:
        print(f"Error running translation comparison: {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)
        
    # 5. Compare layout/formatting compliance (Formatting Diff Engine)
    try:
        format_engine = FormatEngine()
        format_results = format_engine.check_format(expected_blocks, actual_content_text)
    except Exception as e:
        print(f"Error running layout formatting comparison: {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)
        
    # 6. Generate single comprehensive HTML dashboard report
    try:
        report_gen = ReportGenerator()
        html_report = report_gen.generate_report(brf_results, diff_results, format_results, grade)
        
        # Save HTML report next to the Braille file
        base_name, _ = os.path.splitext(braille_file)
        report_path = f"{base_name}_validation_report.html"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_report)
            
        print("\n" + "=" * 60)
        print("                 VALIDATION COMPLETED")
        print("=" * 60)
        print(f"Report saved successfully at: {os.path.abspath(report_path)}")
        print("Double-click the HTML file to open the interactive dashboard in your browser.")
        print("=" * 60)
        input("\nPress Enter to exit...")
    except Exception as e:
        print(f"Error generating validation report: {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()
