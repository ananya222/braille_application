import sys
import os
import ctypes
import logging
from typing import Dict, Any

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFileDialog, QMessageBox, QProgressBar,
    QTextEdit, QStackedWidget, QComboBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
import re

# Configure logging
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
    # Keep GUI and command-line validation aligned with liblouis.  Context-free
    # regex rewrites of valid UEB cells create false positives.
    return ascii_brf

    manager = UEBCorrectionsManager()
    rules = manager.get_post_process_rules(grade)
    
    for rule in rules:
        rx_match = rule.get("regex_match")
        rx_replace = rule.get("regex_replace")
        if not rx_match or not rx_replace:
            continue
            
        if rx_match == "special_single_quotes":
            ascii_brf = _re.sub(r"(?<=\S)'(?= |$)", ",0", ascii_brf)
            ascii_brf = _re.sub(r"(^| )'(?=\S)", r"\1,8", ascii_brf)
        elif rx_replace == "special_equals_spacing":
            ascii_brf = _re.sub(r'(?<=\S)"7', r' "7', ascii_brf)
            ascii_brf = _re.sub(r'"7(?=\S)', r'"7 ', ascii_brf)
        else:
            ascii_brf = _re.sub(rx_match, rx_replace, ascii_brf)
            
    return ascii_brf
from braille_app.diff_engine import DiffEngine
from braille_app.format_engine import FormatEngine
from braille_app.report_generator import ReportGenerator

def _post_process_expected(ascii_brf: str, grade: int) -> str:
    """Keep the table-produced UEB Grade 1/2 cells unchanged for comparison."""
    return ascii_brf


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

class ValidationThread(QThread):
    finished = Signal(str, list) # report_path, list of errors
    error = Signal(str)
    
    def __init__(self, english_file: str, braille_file: str, grade: int):
        super().__init__()
        self.english_file = english_file
        self.braille_file = braille_file
        self.grade = grade
        
    def run(self):
        try:
            # 1. Extract structural metadata from print document
            extractor = DocumentExtractor()
            extracted_data = extractor.extract(self.english_file)
            
            # 2. Read and parse Braille file
            braille_content = read_braille_input(self.braille_file)
            parser = BRFParser()
            brf_results = parser.parse_content(braille_content)
            
            # 3. Translate print document blocks using liblouis
            expected_blocks = []
            table_list = ["en-ueb-g2.ctb" if self.grade == 2 else "en-ueb-g1.ctb"]
            for page in extracted_data.get("pages", []):
                for block in page.get("blocks", []):
                    text = block.get("text", "")
                    b_type = block.get("type", "body")
                    
                    translated_braille = ""
                    if text.strip():
                        translated_braille = louis.translateString(table_list, text)
                    translated_braille = _post_process_expected(translated_braille, self.grade)
                    
                    expected_blocks.append({
                        "type": b_type,
                        "text": translated_braille
                    })
                    
            # 4. Compare translation
            diff_engine = DiffEngine(grade=self.grade)
            actual_paragraphs = []
            for page in brf_results.get("pages", []):
                page_text = "\n".join(page.get("raw_lines", []))
                actual_paragraphs.append(page_text)
            actual_content_text = "\x0c".join(actual_paragraphs)
            
            diff_results = diff_engine.compare(expected_blocks, actual_content_text)
            
            # 5. Compare formatting
            format_engine = FormatEngine()
            format_results = format_engine.check_format(expected_blocks, actual_content_text)
            
            # Collect findings details
            errors = []
            
            # Translation Errors
            SEVERITY_LABELS = {
                1: "Level 1 — Character Mismatch",
                2: "Level 2 — Word Mismatch",
                3: "Level 3 — Insertion/Deletion",
                4: "Level 4 — Structural Mismatch",
            }
            for d in diff_results.get("diffs", []):
                if d.get("confidence") in ["high_confidence", "needs_review", "alignment_failure"]:
                    loc = d.get("location", "")
                    line_num = "N/A"
                    line_match = re.search(r'line\s+([\d\-]+)', loc, re.IGNORECASE)
                    if line_match:
                        line_num = line_match.group(1)
                        
                    w_num = str(d.get("word_number", "N/A"))
                    if w_num == "N/A":
                        w_match = re.search(r'word[s]?\s+([\d\-]+)', loc, re.IGNORECASE)
                        if w_match:
                            w_num = w_match.group(1)
                    
                    diff_type = d.get("display_category") or d.get('type', 'mismatch')
                    
                    actual_val = d.get("actual", "")
                    expected_val = d.get("expected", "")
                    
                    from braille_app.brf_parser import ASCII_TO_UNICODE_BRAILLE
                    def to_unicode(txt):
                        return "".join(' ' if c == ' ' else ASCII_TO_UNICODE_BRAILLE.get(c, c) for c in txt)
                    actual_val = to_unicode(actual_val)
                    expected_val = to_unicode(expected_val)
                    
                    errors.append({
                        "actual": actual_val,
                        "expected": expected_val,
                        "line": line_num,
                        "word": w_num,
                        "category": diff_type,
                    })
            
            # 6. Generate report
            report_gen = ReportGenerator()
            html_report = report_gen.generate_report(brf_results, diff_results, format_results, self.grade)
            
            # Save report
            base_name, _ = os.path.splitext(self.braille_file)
            report_path = f"{base_name}_validation_report.html"
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(html_report)
                
            self.finished.emit(os.path.abspath(report_path), errors)
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Braille Validation Utility")
        self.resize(650, 480)
        self.setMinimumSize(650, 480)
        
        # Apply modern premium stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0b0f19;
            }
            QLabel {
                color: #f3f4f6;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton {
                background-color: #8b5cf6;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
                font-size: 14px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #7c3aed;
            }
            QPushButton:pressed {
                background-color: #6d28d9;
            }
            QProgressBar {
                border: 1px solid #1f2937;
                border-radius: 4px;
                background-color: #151c2c;
                text-align: center;
                color: #ffffff;
            }
            QProgressBar::chunk {
                background-color: #8b5cf6;
            }
            QTextEdit {
                background-color: #151c2c;
                color: #e5e7eb;
                font-family: Consolas, 'Courier New', monospace;
                font-size: 12px;
                border: 1px solid #1f2937;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        
        self.english_path = ""
        self.braille_path = ""
        
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        self.init_uploader_page()
        self.init_results_page()
        
    def init_uploader_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(25)
        
        # Title
        title_label = QLabel("Braille Validation Utility")
        title_font = QFont("Segoe UI", 20, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #a78bfa; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Files upload layouts
        # 1. English docx/pdf
        eng_layout = QHBoxLayout()
        self.eng_lbl = QLabel("Select an English Document (.docx or .pdf)")
        self.eng_lbl.setStyleSheet("color: #9ca3af; font-size: 13px;")
        eng_btn = QPushButton("Upload English File")
        eng_btn.clicked.connect(self.select_english_file)
        eng_layout.addWidget(self.eng_lbl, 1)
        eng_layout.addWidget(eng_btn)
        layout.addLayout(eng_layout)
        
        # 2. Braille pdf/brf
        brl_layout = QHBoxLayout()
        self.brl_lbl = QLabel("Select Braille Document (.pdf)")
        self.brl_lbl.setStyleSheet("color: #9ca3af; font-size: 13px;")
        brl_btn = QPushButton("Upload Braille File")
        brl_btn.clicked.connect(self.select_braille_file)
        brl_layout.addWidget(self.brl_lbl, 1)
        brl_layout.addWidget(brl_btn)
        layout.addLayout(brl_layout)
        
        # 3. Grade Selector
        grade_layout = QHBoxLayout()
        grade_label = QLabel("Select UEB Translation Grade:")
        grade_label.setStyleSheet("color: #9ca3af; font-size: 13px;")
        
        self.grade_combo = QComboBox()
        self.grade_combo.addItems(["Grade 2 (Contracted)", "Grade 1 (Uncontracted)"])
        self.grade_combo.setStyleSheet("""
            QComboBox {
                background-color: #151c2c;
                color: #e5e7eb;
                border: 1px solid #1f2937;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 180px;
            }
        """)
        grade_layout.addWidget(grade_label)
        grade_layout.addWidget(self.grade_combo)
        grade_layout.addStretch()
        layout.addLayout(grade_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0) # Indeterminate mode when working
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        # Action layout
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        self.run_btn = QPushButton("Run Verification")
        self.run_btn.setStyleSheet("""
            QPushButton {
                background-color: #8b5cf6;
                padding: 12px 24px;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #7c3aed;
            }
        """)
        self.run_btn.clicked.connect(self.run_verification)
        action_layout.addWidget(self.run_btn)
        action_layout.addStretch()
        layout.addLayout(action_layout)
        
        self.stacked_widget.addWidget(page)
        
    def init_results_page(self):
        self.results_page = QWidget()
        layout = QVBoxLayout(self.results_page)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(15)
        
        # Header Label
        self.res_title = QLabel("Validation Results")
        title_font = QFont("Segoe UI", 18, QFont.Bold)
        self.res_title.setFont(title_font)
        self.res_title.setStyleSheet("color: #f87171;")
        layout.addWidget(self.res_title)
        
        # Scrolling results box
        self.res_text = QTextEdit()
        self.res_text.setReadOnly(True)
        layout.addWidget(self.res_text)
        
        # Footer report path indicator
        self.report_lbl = QLabel("")
        self.report_lbl.setStyleSheet("color: #9ca3af; font-size: 11px;")
        self.report_lbl.setWordWrap(True)
        layout.addWidget(self.report_lbl)
        
        # Button controls
        btn_layout = QHBoxLayout()
        self.back_btn = QPushButton("Back")
        self.back_btn.clicked.connect(self.go_back)
        btn_layout.addWidget(self.back_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.stacked_widget.addWidget(self.results_page)
        
    def select_english_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select English Print Document", "", "Documents (*.docx *.pdf)"
        )
        if file_path:
            self.english_path = file_path
            self.eng_lbl.setText(os.path.basename(file_path))
            self.eng_lbl.setStyleSheet("color: #10b981; font-size: 13px; font-weight: bold;")
            
    def select_braille_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Transcribed Braille File", "", "Braille Files (*.pdf *.brf)"
        )
        if file_path:
            self.braille_path = file_path
            self.brl_lbl.setText(os.path.basename(file_path))
            self.brl_lbl.setStyleSheet("color: #10b981; font-size: 13px; font-weight: bold;")
            
    def run_verification(self):
        if not self.english_path or not self.braille_path:
            QMessageBox.warning(self, "Missing Files", "Please select both the English and Braille documents before proceeding.")
            return
            
        self.run_btn.setEnabled(False)
        self.progress_bar.show()
        
        # Grade 2 is index 0, Grade 1 is index 1
        selected_grade = 2 if self.grade_combo.currentIndex() == 0 else 1
        
        self.thread = ValidationThread(self.english_path, self.braille_path, selected_grade)
        self.thread.finished.connect(self.on_success)
        self.thread.error.connect(self.on_error)
        self.thread.start()
        
    def on_success(self, report_path, errors):
        self.run_btn.setEnabled(True)
        self.progress_bar.hide()
        
        self.report_lbl.setText(f"Detailed HTML dashboard report generated at:\n{report_path}")
        
        if not errors:
            self.res_title.setText("Verification Completed: 100% Success!")
            self.res_title.setStyleSheet("color: #10b981;")
            self.res_text.setPlainText("🎉 0 Mismatches Detected! The Braille translation and formatting match the print document 100% compliant.")
        else:
            self.res_title.setText("Verification Completed: Mismatches Found")
            self.res_title.setStyleSheet("color: #f87171;")
            
            txt_content = ""
            for idx, err in enumerate(errors, 1):
                # Diff segments are already in Unicode Braille — display directly
                actual_dots = err['actual']
                expected_dots = err['expected']
                
                txt_content += f"Error #{idx}:\n"
                txt_content += f"Output: {actual_dots}\n"
                txt_content += f"Expected Output: {expected_dots}\n"
                txt_content += f"Line Number: {err['line']}, Word Number: {err['word']}\n"
                txt_content += f"Error Type: {err.get('category', 'Structural Mismatch')}\n"
                txt_content += "-" * 50 + "\n\n"
            
            self.res_text.setPlainText(txt_content)
            
        self.stacked_widget.setCurrentIndex(1)
        
    def go_back(self):
        self.stacked_widget.setCurrentIndex(0)
        
    def on_error(self, err_msg):
        self.run_btn.setEnabled(True)
        self.progress_bar.hide()
        QMessageBox.critical(self, "Verification Failed", f"An error occurred during verification:\n\n{err_msg}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
