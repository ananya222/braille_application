import sys
import os
import ctypes
import logging
import re
import json
from collections import Counter
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QMessageBox, QProgressBar,
    QTextEdit, QStackedWidget, QComboBox, QFrame, QSizePolicy, QSpacerItem,
    QScrollArea, QListWidget, QListWidgetItem, QSplitter, QCheckBox
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QRectF, QSize, QSizeF
from PySide6.QtGui import QFont, QColor, QPalette, QImage, QPainter, QPen, QBrush, QFontMetricsF
from PySide6.QtPdf import QPdfDocument

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)

if hasattr(sys, "_MEIPASS"):
    base_dir = sys._MEIPASS
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

tables_dir = os.path.join(base_dir, "vendor", "liblouis-win64", "share", "liblouis", "tables")
if not os.path.exists(tables_dir):
    tables_dir = os.path.abspath(os.path.join(base_dir, "vendor", "liblouis-win64", "share", "liblouis", "tables"))

os.environ["LOUIS_TABLEPATH"] = tables_dir
if sys.platform == "win32":
    try:
        ctypes.CDLL("msvcrt")._wputenv(f"LOUIS_TABLEPATH={tables_dir}")
    except Exception:
        pass

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
from braille_app.input_reader import read_braille_input, read_braille_pdf_with_provenance
from braille_app.diff_engine import DiffEngine
from braille_app.format_engine import FormatEngine
from braille_app.report_generator import ReportGenerator
from braille_app.provenance_resolver import localize_diff_records
from braille_app.presentation_grouping import (
    build_presentation_items,
    presentation_page_metrics,
)
from braille_app.validation_pipeline import run_validation_pipeline
from braille_app.visual_annotations import (
    VisualIssue,
    export_annotated_pdf,
    pdf_box_to_screen,
    visual_issues_from_cell_issues,
)


def build_display_errors(cell_issues, diff_records=None, already_presented=False):
    """Build the concise GUI payload from localized or presented issues."""
    presentation_items = (
        list(cell_issues or []) if already_presented
        else build_presentation_items(cell_issues, diff_records)
    )
    display_errors = []
    for issue in presentation_items:
        kind = issue.get("kind", "cell_issue")
        is_structural = kind in ("structural_review", "structural_group")
        is_group = kind == "structural_group"
        expected = "" if is_structural else "".join(issue.get("expected_cells", []))
        actual = "" if is_structural else "".join(issue.get("actual_cells", []))
        if not issue.get("expected_cells") and not is_structural:
            expected = issue.get("expected", "")
        if not issue.get("actual_cells") and not is_structural:
            actual = issue.get("actual", "")
        child_count = issue.get("child_count", 0)
        message = issue.get("message", "")
        if is_group:
            message = (
                f"{message} Internal structural segments: {child_count}. "
                f"Child IDs: {', '.join(map(str, issue.get('child_issue_ids', [])))}."
            )
        display_errors.append({
            "display_id": issue.get("display_id"),
            "issue_id": issue.get("issue_id", issue.get("display_id")),
            "source_issue_id": issue.get("source_issue_id"),
            "page": issue.get("page"),
            "kind": kind,
            "expected": expected,
            "actual": actual,
            "context": issue.get("source_summary", issue.get("context", "")),
            "confidence": issue.get("confidence", "high_confidence"),
            "message": message or (
                "Unable to reliably localize this broader mismatch."
                if is_structural else ""
            ),
            "presentation_kind": issue.get("presentation_kind", "structural" if is_structural else "exact"),
            "group_id": issue.get("group_id"),
            "parent_diff_id": issue.get("parent_diff_id"),
            "child_issue_ids": list(issue.get("child_issue_ids", [])),
            "child_count": child_count,
            "child_records": list(issue.get("child_records", [])),
            # The visual view consumes the same provenance that produced the
            # report row.  These fields are presentation data only.
            "provenance_cells": list(issue.get("provenance_cells") or []),
            "x0": issue.get("x0"),
            "x1": issue.get("x1"),
            "top": issue.get("top"),
            "bottom": issue.get("bottom"),
        })
    return display_errors


def _post_process_expected(ascii_brf: str, grade: int) -> str:
    return ascii_brf


# ─── Stylesheet ─────────────────────────────────────────────────────────────────

STYLESHEET = """
/* ── Base ─────────────────────────────── */
QMainWindow {
    background-color: #090b10;
}
QWidget {
    font-family: 'Segoe UI', 'SF Pro Display', system-ui, sans-serif;
    color: #e2e4e9;
}

/* ── Scroll Area / Text Edit ──────────── */
QTextEdit {
    background-color: #0d1117;
    color: #c9d1d9;
    border: 1px solid #21262d;
    border-radius: 10px;
    padding: 16px;
    font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
    font-size: 13px;
    selection-background-color: #383e4a;
}
QTextEdit:focus {
    border-color: #6366f1;
}

QScrollBar:vertical {
    background: #0d1117;
    width: 8px;
    margin: 4px 2px 4px 0;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #30363d;
    min-height: 30px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #484f58;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

/* ── Buttons ──────────────────────────── */
QPushButton {
    background-color: #6366f1;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 600;
    min-width: 100px;
}
QPushButton:hover {
    background-color: #818cf8;
}
QPushButton:pressed {
    background-color: #4f46e5;
}
QPushButton:disabled {
    background-color: #1f2335;
    color: #6b7280;
}

QPushButton#secondaryBtn {
    background-color: transparent;
    border: 1px solid #30363d;
    color: #8b949e;
}
QPushButton#secondaryBtn:hover {
    background-color: #1a1f2e;
    border-color: #6366f1;
    color: #c9d1d9;
}

QPushButton#uploadBtn {
    background-color: #0d1117;
    border: 2px dashed #30363d;
    border-radius: 12px;
    padding: 28px 20px;
    font-size: 13px;
    font-weight: 400;
    color: #8b949e;
}
QPushButton#uploadBtn:hover {
    border-color: #6366f1;
    background-color: #111827;
    color: #c9d1d9;
}

QPushButton#uploadBtnActive {
    background-color: #0a1219;
    border: 2px solid #10b981;
    border-radius: 12px;
    padding: 22px 20px;
    font-size: 13px;
    font-weight: 500;
    color: #10b981;
}
QPushButton#uploadBtnActive:hover {
    border-color: #34d399;
    color: #34d399;
}

/* ── Progress Bar ─────────────────────── */
QProgressBar {
    border: none;
    border-radius: 6px;
    background-color: #161b22;
    text-align: center;
    color: transparent;
    height: 4px;
    margin: 8px 0;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6366f1, stop:1 #a855f7);
    border-radius: 6px;
}

/* ── Combo Box ────────────────────────── */
QComboBox {
    background-color: #0d1117;
    color: #c9d1d9;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 13px;
    min-width: 190px;
}
QComboBox:hover {
    border-color: #6366f1;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border-left: 1px solid #21262d;
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
}
QComboBox QAbstractItemView {
    background-color: #0d1117;
    border: 1px solid #21262d;
    border-radius: 8px;
    selection-background-color: #1f2937;
    padding: 6px;
    outline: none;
}
QComboBox QAbstractItemView::item {
    padding: 8px 14px;
    border-radius: 6px;
}
QComboBox QAbstractItemView::item:hover {
    background-color: #161b22;
}

/* ── Cards / Frames ───────────────────── */
QFrame#card {
    background-color: #0d1117;
    border: 1px solid #21262d;
    border-radius: 16px;
    padding: 0px;
}

/* ── Labels ───────────────────────────── */
QLabel#subtitle {
    color: #6366f1;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 2px;
}

QLabel#statusBadge {
    background-color: #0d2b1e;
    color: #10b981;
    border: 1px solid #10b981;
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 12px;
    font-weight: 600;
}

QLabel#statusBadgeWarn {
    background-color: #2d1810;
    color: #f87171;
    border: 1px solid #f87171;
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 12px;
    font-weight: 600;
}
"""


class ValidationThread(QThread):
    finished = Signal(str, list)
    error = Signal(str)

    def __init__(self, english_file: str, braille_file: str, grade: int):
        super().__init__()
        self.english_file = english_file
        self.braille_file = braille_file
        self.grade = grade

    def run(self):
        try:
            result = run_validation_pipeline(
                self.english_file, self.braille_file, self.grade
            )
            brf_results = result["brf_results"]
            diff_results = result["diff_results"]
            format_results = result["format_results"]
            errors = build_display_errors(
                diff_results["presentation_items"], already_presented=True
            )
            html_report = result["report_html"]

            base_name, _ = os.path.splitext(self.braille_file)
            report_path = f"{base_name}_validation_report.html"
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(html_report)

            self.finished.emit(os.path.abspath(report_path), errors)
        except Exception as e:
            self.error.emit(str(e))


class FileDropButton(QPushButton):
    clicked = Signal()

    def __init__(self, placeholder_text: str, parent=None):
        super().__init__(parent)
        self._placeholder = placeholder_text
        self._selected = False
        self._build()

    def _build(self):
        self.setText(self._placeholder)
        self.setObjectName("uploadBtn")
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(100)

    def mark_selected(self, filename: str):
        self._selected = True
        self.setText(f"✓  {filename}")
        self.setObjectName("uploadBtnActive")
        self.style().unpolish(self)
        self.style().polish(self)

    def reset(self):
        self._selected = False
        self.setText(self._placeholder)
        self.setObjectName("uploadBtn")
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


def compose_pdf_page_on_white(rendered_image):
    """Composite QtPdf's transparent page render onto an opaque white page."""
    if rendered_image.isNull():
        return rendered_image
    page = QImage(rendered_image.size(), QImage.Format_ARGB32_Premultiplied)
    page.fill(QColor("white"))
    painter = QPainter(page)
    painter.drawImage(0, 0, rendered_image)
    painter.end()
    return page


class PdfPageCanvas(QWidget):
    """Rendered PDF page with transparent blue provenance overlays."""

    issueSelected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._image = QImage()
        self._page_size = QSizeF()
        self._issues = []
        self._selected_issue_id = None
        self._diagnostics_enabled = False
        self.setMouseTracking(True)

    def set_page(self, image, page_size, issues, selected_issue_id=None):
        self._image = image.copy()
        self._page_size = page_size
        self._issues = list(issues or [])
        self._selected_issue_id = selected_issue_id
        self.setFixedSize(self._image.size())
        self.update()

    def set_selected_issue(self, issue_id):
        self._selected_issue_id = issue_id
        self.update()

    def set_diagnostics(self, enabled):
        self._diagnostics_enabled = bool(enabled)
        self.update()

    def _screen_box(self, box):
        return pdf_box_to_screen(
            box,
            self._page_size.width(),
            self._page_size.height(),
            self.width(),
            self.height(),
        )

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("white"))
        painter.drawImage(QRectF(0, 0, self.width(), self.height()), self._image)
        blue = QColor("#248cff")
        selected = QColor("#65c7ff")
        diagnostic_font = QFont("Arial", 8, QFont.Bold)

        def draw_diagnostic_label(x0, top, text):
            if not self._diagnostics_enabled:
                return
            painter.setFont(diagnostic_font)
            label_top = max(0.0, top - 18.0)
            label_width = QFontMetricsF(diagnostic_font).horizontalAdvance(text) + 8
            label_rect = QRectF(x0 + 1, label_top, label_width, 16)
            painter.setPen(QPen(QColor("#123b66")))
            painter.setBrush(QBrush(QColor(255, 255, 255, 255)))
            painter.drawRect(label_rect)
            painter.setPen(QPen(blue))
            painter.drawText(label_rect, Qt.AlignLeft | Qt.AlignVCenter, text)
            painter.setBrush(QBrush(Qt.NoBrush))

        for issue in self._issues:
            pen = QPen(selected if issue.issue_id == self._selected_issue_id else blue)
            pen.setWidth(3 if issue.issue_id == self._selected_issue_id else 2)
            if issue.localization == "partial":
                pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            painter.setBrush(QBrush(Qt.NoBrush))
            for box in issue.boxes:
                x0, top, x1, bottom = self._screen_box(box)
                painter.drawRect(QRectF(x0, top, x1 - x0, bottom - top))
                painter.setPen(pen)
                draw_diagnostic_label(x0, top, f"#{issue.issue_id} {issue.localization}")
            if issue.marker is not None:
                x0, top, x1, bottom = self._screen_box(issue.marker)
                if issue.marker_style == "caret":
                    center = (x0 + x1) / 2.0
                    painter.drawLine(center, top, center, bottom)
                else:
                    painter.drawEllipse(QRectF(x0, top, max(7.0, x1 - x0), max(7.0, bottom - top)))
                draw_diagnostic_label(x0, top, f"#{issue.issue_id} {issue.localization}")

    def mousePressEvent(self, event):
        point = event.position()
        for issue in self._issues:
            candidate_boxes = list(issue.boxes)
            if issue.marker is not None:
                candidate_boxes.append(issue.marker)
            for box in candidate_boxes:
                x0, top, x1, bottom = self._screen_box(box)
                if QRectF(x0, top, x1 - x0, bottom - top).adjusted(-5, -5, 5, 5).contains(point):
                    self.issueSelected.emit(issue.issue_id)
                    return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        point = event.position()
        for issue in self._issues:
            for box in list(issue.boxes) + ([issue.marker] if issue.marker is not None else []):
                x0, top, x1, bottom = self._screen_box(box)
                if QRectF(x0, top, x1 - x0, bottom - top).adjusted(-5, -5, 5, 5).contains(point):
                    self.setToolTip(
                        f"Issue #{issue.issue_id}\n"
                        f"Localization: {issue.localization}\n"
                        f"PDF bbox: ({box.x0:.2f}, {box.top:.2f}, {box.x1:.2f}, {box.bottom:.2f})"
                    )
                    return
        self.setToolTip("")
        super().mouseMoveEvent(event)


class VisualResultsPage(QWidget):
    """Page-by-page PDF view backed exclusively by localized provenance."""

    detailedRequested = Signal()
    backRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.document = QPdfDocument(self)
        self.pdf_path = ""
        self.visual_issues = []
        self.issues_by_page = {}
        self.current_page = 1
        self.selected_issue_id = None
        self.zoom_factor = 1.0
        self.fit_mode = "page"
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Visual PDF Results")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        header.addWidget(title)
        header.addStretch()
        self.page_label = QLabel("Page 0 / 0")
        self.page_label.setStyleSheet("color: #8b949e; font-weight: 600;")
        header.addWidget(self.page_label)
        layout.addLayout(header)

        toolbar = QHBoxLayout()
        self.previous_btn = QPushButton("‹ Previous")
        self.previous_btn.setObjectName("secondaryBtn")
        self.previous_btn.clicked.connect(lambda: self.show_page(self.current_page - 1))
        toolbar.addWidget(self.previous_btn)
        self.next_btn = QPushButton("Next ›")
        self.next_btn.setObjectName("secondaryBtn")
        self.next_btn.clicked.connect(lambda: self.show_page(self.current_page + 1))
        toolbar.addWidget(self.next_btn)
        toolbar.addSpacing(8)
        zoom_out = QPushButton("−")
        zoom_out.setObjectName("secondaryBtn")
        zoom_out.setFixedWidth(42)
        zoom_out.clicked.connect(lambda: self._set_manual_zoom(self.zoom_factor - 0.15))
        toolbar.addWidget(zoom_out)
        zoom_in = QPushButton("+")
        zoom_in.setObjectName("secondaryBtn")
        zoom_in.setFixedWidth(42)
        zoom_in.clicked.connect(lambda: self._set_manual_zoom(self.zoom_factor + 0.15))
        toolbar.addWidget(zoom_in)
        fit_width = QPushButton("Fit width")
        fit_width.setObjectName("secondaryBtn")
        fit_width.clicked.connect(lambda: self._set_fit_mode("width"))
        toolbar.addWidget(fit_width)
        fit_page = QPushButton("Fit page")
        fit_page.setObjectName("secondaryBtn")
        fit_page.clicked.connect(lambda: self._set_fit_mode("page"))
        toolbar.addWidget(fit_page)
        self.diagnostics_checkbox = QCheckBox("Show annotation diagnostics")
        self.diagnostics_checkbox.setStyleSheet("color: #8b949e; font-size: 12px;")
        self.diagnostics_checkbox.toggled.connect(self._set_diagnostics)
        toolbar.addWidget(self.diagnostics_checkbox)
        toolbar.addStretch()
        self.export_btn = QPushButton("Export annotated PDF")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_pdf)
        toolbar.addWidget(self.export_btn)
        detail_btn = QPushButton("Detailed report")
        detail_btn.setObjectName("secondaryBtn")
        detail_btn.clicked.connect(self.detailedRequested.emit)
        toolbar.addWidget(detail_btn)
        back_btn = QPushButton("Upload another")
        back_btn.setObjectName("secondaryBtn")
        back_btn.clicked.connect(self.backRequested.emit)
        toolbar.addWidget(back_btn)
        layout.addLayout(toolbar)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        self.issue_list = QListWidget()
        self.issue_list.setMinimumWidth(270)
        self.issue_list.setMaximumWidth(360)
        self.issue_list.currentItemChanged.connect(self._on_issue_selected)
        splitter.addWidget(self.issue_list)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        self.canvas = PdfPageCanvas()
        self.canvas.issueSelected.connect(self.select_issue)
        self.scroll_area.setWidget(self.canvas)
        splitter.addWidget(self.scroll_area)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter, 1)

        self.status_label = QLabel("Select a report to view page annotations.")
        self.status_label.setStyleSheet("color: #8b949e; font-size: 12px;")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

    def set_data(self, pdf_path, cell_issues):
        self.pdf_path = pdf_path or ""
        self.visual_issues = visual_issues_from_cell_issues(cell_issues or [])
        self.issues_by_page = {}
        for issue in self.visual_issues:
            if issue.page is not None:
                self.issues_by_page.setdefault(int(issue.page), []).append(issue)
        self.issue_list.clear()
        for issue in self.visual_issues:
            if issue.type in ("structural_review", "structural_group"):
                detail = (
                    f"Issue #{issue.issue_id}  ·  Page {issue.page}\n"
                    "Needs review - structural mismatch\n"
                    f"{issue.child_count or 1} unresolved segment"
                    f"{'s' if (issue.child_count or 1) != 1 else ''}"
                )
                if issue.parent_diff_id:
                    detail += f"\nParent diff: {issue.parent_diff_id}"
            else:
                page = f"Page {issue.page}" if issue.page is not None else "Page N/A"
                detail = (
                    f"Issue #{issue.issue_id}  ·  {page}\n"
                    f"Expected: {issue.expected or '∅'}\n"
                    f"Found: {issue.actual or '∅'}"
                )
            item = QListWidgetItem(detail)
            item.setData(Qt.UserRole, issue.issue_id)
            self.issue_list.addItem(item)

        self.document.close()
        self.export_btn.setEnabled(False)
        if not self.pdf_path:
            self.status_label.setText("Visual PDF results are available only for PDF input.")
            self.page_label.setText("Page 0 / 0")
            return
        status = self.document.load(self.pdf_path)
        if status != QPdfDocument.Error.None_:
            self.status_label.setText(f"Could not render PDF: {status}")
            self.page_label.setText("Page 0 / 0")
            return
        self.export_btn.setEnabled(True)
        self.current_page = 1
        self.selected_issue_id = None
        self.fit_mode = "page"
        self._render_current_page()
        QTimer.singleShot(0, self._render_current_page)

    def _set_manual_zoom(self, value):
        self.fit_mode = "manual"
        self.zoom_factor = max(0.35, min(3.0, value))
        self._render_current_page()

    def _set_diagnostics(self, enabled):
        self.canvas.set_diagnostics(enabled)

    def _set_fit_mode(self, mode):
        self.fit_mode = mode
        self._render_current_page()

    def _render_current_page(self):
        if self.document.pageCount() <= 0:
            return
        page_index = max(0, min(self.document.pageCount() - 1, self.current_page - 1))
        point_size = self.document.pagePointSize(page_index)
        available = self.scroll_area.viewport().size()
        available_width = max(480, available.width() - 24)
        available_height = max(480, available.height() - 24)
        if self.fit_mode == "width":
            self.zoom_factor = available_width / max(1.0, point_size.width())
        elif self.fit_mode == "page":
            self.zoom_factor = min(
                available_width / max(1.0, point_size.width()),
                available_height / max(1.0, point_size.height()),
            )
        self.zoom_factor = max(0.35, min(3.0, self.zoom_factor))
        render_size = QSize(
            max(1, round(point_size.width() * self.zoom_factor)),
            max(1, round(point_size.height() * self.zoom_factor)),
        )
        image = compose_pdf_page_on_white(self.document.render(page_index, render_size))
        page_issues = self.issues_by_page.get(self.current_page, [])
        self.canvas.set_page(image, point_size, page_issues, self.selected_issue_id)
        self.page_label.setText(f"Page {self.current_page} / {self.document.pageCount()}")
        self.previous_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < self.document.pageCount())
        if page_issues:
            self.status_label.setText(
                f"{len(page_issues)} issue{'s' if len(page_issues) != 1 else ''} on this page. "
                "Blue outlines mark actual provenance; structural reviews remain side-panel only."
            )
        else:
            self.status_label.setText("No localized validator issues on this page.")

    def show_page(self, page_number):
        if self.document.pageCount() <= 0:
            return
        self.current_page = max(1, min(self.document.pageCount(), int(page_number)))
        self._render_current_page()

    def select_issue(self, issue_id):
        self.selected_issue_id = issue_id
        for index in range(self.issue_list.count()):
            item = self.issue_list.item(index)
            if item.data(Qt.UserRole) == issue_id:
                self.issue_list.setCurrentItem(item)
                break
        self.canvas.set_selected_issue(issue_id)
        issue = next((item for item in self.visual_issues if item.issue_id == issue_id), None)
        if issue is None or issue.page is None:
            return
        if issue.page != self.current_page:
            self.current_page = int(issue.page)
            self._render_current_page()
        boxes = list(issue.boxes)
        if issue.marker is not None:
            boxes.append(issue.marker)
        if boxes:
            box = boxes[0]
            x0, top, x1, bottom = pdf_box_to_screen(
                box,
                self.canvas._page_size.width(),
                self.canvas._page_size.height(),
                self.canvas.width(),
                self.canvas.height(),
            )
            self.scroll_area.horizontalScrollBar().setValue(max(0, int((x0 + x1) / 2 - self.scroll_area.viewport().width() / 2)))
            self.scroll_area.verticalScrollBar().setValue(max(0, int((top + bottom) / 2 - self.scroll_area.viewport().height() / 2)))

    def _on_issue_selected(self, current, previous):
        if current is not None:
            issue_id = current.data(Qt.UserRole)
            if issue_id != self.selected_issue_id:
                self.select_issue(issue_id)

    def export_pdf(self):
        if not self.pdf_path or not self.visual_issues:
            return
        base, extension = os.path.splitext(self.pdf_path)
        output_path = f"{base}_validator_annotated.pdf"
        try:
            export_annotated_pdf(self.pdf_path, output_path, self.visual_issues)
            self.status_label.setText(f"Annotated copy saved to: {output_path}")
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", f"Could not write annotated PDF:\n\n{exc}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Braille Validator")
        self.resize(720, 540)
        self.setMinimumSize(600, 460)

        self.setStyleSheet(STYLESHEET)

        self.english_path = ""
        self.braille_path = ""
        self.last_errors = []
        self.last_report_path = ""

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.init_uploader_page()
        self.init_results_page()
        self.init_visual_page()

    # ── Uploader Page ────────────────────────────────────────────

    def init_uploader_page(self):
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setObjectName("card")
        card.setFixedWidth(520)
        card_v = QVBoxLayout(card)
        card_v.setContentsMargins(40, 36, 40, 36)
        card_v.setSpacing(28)

        # Header
        header = QVBoxLayout()
        header.setSpacing(6)

        title = QLabel("Braille Validator")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #f0f6ff;")
        header.addWidget(title)

        subtitle = QLabel("UEB TRANSLATION & FORMAT VERIFICATION")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        header.addWidget(subtitle)

        card_v.addLayout(header)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet("border: none; background-color: #21262d; max-height: 1px;")
        card_v.addWidget(div)

        # File cards
        self.eng_btn = FileDropButton("Click to select English document (.docx / .pdf)")
        self.eng_btn.clicked.connect(self.select_english_file)
        card_v.addWidget(self.eng_btn)

        self.brl_btn = FileDropButton("Click to select Braille document (.pdf / .brf)")
        self.brl_btn.clicked.connect(self.select_braille_file)
        card_v.addWidget(self.brl_btn)

        # Grade selector row
        grade_row = QHBoxLayout()
        grade_row.setSpacing(16)

        grade_lbl = QLabel("UEB Grade")
        grade_lbl.setStyleSheet("font-size: 13px; font-weight: 500; color: #8b949e;")
        grade_row.addWidget(grade_lbl)

        self.grade_combo = QComboBox()
        self.grade_combo.addItems(["Grade 2 — Contracted", "Grade 1 — Uncontracted"])
        grade_row.addWidget(self.grade_combo)
        grade_row.addStretch()
        card_v.addLayout(grade_row)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        card_v.addWidget(self.progress_bar)

        # Run button
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.run_btn = QPushButton("Run Verification")
        self.run_btn.setCursor(Qt.PointingHandCursor)
        self.run_btn.setFixedSize(200, 44)
        self.run_btn.clicked.connect(self.run_verification)
        btn_row.addWidget(self.run_btn)

        btn_row.addStretch()
        card_v.addLayout(btn_row)

        outer.addWidget(card, alignment=Qt.AlignCenter)
        self.stacked_widget.addWidget(page)

    # ── Results Page ─────────────────────────────────────────────

    def init_results_page(self):
        self.results_page = QWidget()
        layout = QVBoxLayout(self.results_page)
        layout.setContentsMargins(48, 36, 48, 36)
        layout.setSpacing(20)

        # Header row: title + badge
        head_row = QHBoxLayout()
        self.res_title = QLabel("Results")
        self.res_title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        head_row.addWidget(self.res_title)

        head_row.addStretch()

        self.status_badge = QLabel("")
        self.status_badge.setObjectName("statusBadge")
        self.status_badge.setVisible(False)
        head_row.addWidget(self.status_badge)

        layout.addLayout(head_row)

        # Error count summary
        self.summary_lbl = QLabel("")
        self.summary_lbl.setStyleSheet("font-size: 13px; color: #8b949e;")
        layout.addWidget(self.summary_lbl)

        # Results text area
        self.res_text = QTextEdit()
        self.res_text.setReadOnly(True)
        layout.addWidget(self.res_text)

        # Report path footer
        self.report_lbl = QLabel("")
        self.report_lbl.setStyleSheet("font-size: 12px; color: #484f58; padding: 8px 0;")
        self.report_lbl.setWordWrap(True)
        layout.addWidget(self.report_lbl)

        # Bottom bar
        bot_row = QHBoxLayout()
        self.back_btn = QPushButton("←  New Validation")
        self.back_btn.setObjectName("secondaryBtn")
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.clicked.connect(self.go_back)
        bot_row.addWidget(self.back_btn)
        bot_row.addStretch()
        self.visual_btn = QPushButton("Visual PDF Results")
        self.visual_btn.setObjectName("secondaryBtn")
        self.visual_btn.setCursor(Qt.PointingHandCursor)
        self.visual_btn.clicked.connect(self.show_visual_results)
        self.visual_btn.setVisible(False)
        bot_row.addWidget(self.visual_btn)
        layout.addLayout(bot_row)

        self.stacked_widget.addWidget(self.results_page)

    def init_visual_page(self):
        self.visual_page = VisualResultsPage()
        self.visual_page.detailedRequested.connect(self.show_detailed_report)
        self.visual_page.backRequested.connect(self.go_back)
        self.stacked_widget.addWidget(self.visual_page)

    # ── File Selection ───────────────────────────────────────────

    def select_english_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select English Print Document", "",
            "Documents (*.docx *.pdf)"
        )
        if file_path:
            self.english_path = file_path
            self.eng_btn.mark_selected(os.path.basename(file_path))

    def select_braille_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Transcribed Braille File", "",
            "Braille Files (*.pdf *.brf)"
        )
        if file_path:
            self.braille_path = file_path
            self.brl_btn.mark_selected(os.path.basename(file_path))

    # ── Verification Logic ───────────────────────────────────────

    def run_verification(self):
        if not self.english_path or not self.braille_path:
            QMessageBox.warning(
                self, "Missing Files",
                "Please select both the English and Braille documents before proceeding."
            )
            return

        self.run_btn.setEnabled(False)
        self.progress_bar.show()

        selected_grade = 2 if self.grade_combo.currentIndex() == 0 else 1

        self.thread = ValidationThread(self.english_path, self.braille_path, selected_grade)
        self.thread.finished.connect(self.on_success)
        self.thread.error.connect(self.on_error)
        self.thread.start()

    def on_success(self, report_path, errors):
        self.run_btn.setEnabled(True)
        self.progress_bar.hide()

        self.last_errors = list(errors or [])
        self.last_report_path = report_path
        self.report_lbl.setText(f"Report saved to:\n{report_path}")
        is_pdf = self.braille_path.lower().endswith(".pdf")
        self.visual_btn.setVisible(is_pdf)
        if is_pdf:
            self.visual_page.set_data(self.braille_path, self.last_errors)

        if not errors:
            self.res_title.setText("Verification Passed")
            self.summary_lbl.setText("No mismatches detected — Braille matches the source document perfectly.")

            self.status_badge.setText("✓ PASSED")
            self.status_badge.setObjectName("statusBadge")
            self.status_badge.style().unpolish(self.status_badge)
            self.status_badge.style().polish(self.status_badge)
            self.status_badge.setVisible(True)

            self.res_text.setPlainText("")
        else:
            total = len(errors)
            self.res_title.setText(f"{total} Mismatch{'es' if total != 1 else ''} Found")
            self.summary_lbl.setText(
                f"{total} difference{'s' if total != 1 else ''} detected between Braille output and expected translation."
            )

            self.status_badge.setText(f"✗ {total} ISSUE{'S' if total != 1 else ''}")
            self.status_badge.setObjectName("statusBadgeWarn")
            self.status_badge.style().unpolish(self.status_badge)
            self.status_badge.style().polish(self.status_badge)
            self.status_badge.setVisible(True)

            txt_content = ""
            for idx, err in enumerate(errors, 1):
                page = err.get("page") if err.get("page") is not None else "N/A"
                kind = err.get("kind", "cell_issue")
                if kind in ("structural_review", "structural_group"):
                    txt_content += (
                        f"Issue #{idx}\n"
                        f"  Page            {page}\n"
                        "  Type            structural mismatch - needs review\n"
                        f"  Parent diff     {err.get('parent_diff_id', 'N/A')}\n"
                        f"  Unresolved segments {err.get('child_count', 1)}\n"
                        f"  Child IDs       {', '.join(map(str, err.get('child_issue_ids', [])))}\n"
                        f"  Context         {err.get('context', '')}\n"
                        f"  Message         {err.get('message', '')}\n"
                        f"  Confidence      {err.get('confidence', '')}\n\n"
                    )
                else:
                    txt_content += (
                        f"Issue #{idx}\n"
                        f"  Page            {page}\n"
                        f"  Type            {kind}\n"
                        f"  Expected        {err.get('expected', '')}\n"
                        f"  Actual          {err.get('actual', '')}\n"
                        f"  Context         {err.get('context', '')}\n"
                        f"  Confidence      {err.get('confidence', '')}\n\n"
                    )

            self.res_text.setPlainText(txt_content)

        if is_pdf:
            self.stacked_widget.setCurrentWidget(self.visual_page)
        else:
            self.stacked_widget.setCurrentWidget(self.results_page)

    def show_visual_results(self):
        if self.braille_path.lower().endswith(".pdf"):
            self.stacked_widget.setCurrentWidget(self.visual_page)

    def show_detailed_report(self):
        self.stacked_widget.setCurrentWidget(self.results_page)

    def go_back(self):
        self.stacked_widget.setCurrentIndex(0)
        self.visual_page.document.close()
        self.visual_page.issue_list.clear()
        self.visual_btn.setVisible(False)
        self.last_errors = []
        self.last_report_path = ""
        self.eng_btn.reset()
        self.brl_btn.reset()
        self.english_path = ""
        self.braille_path = ""

    def on_error(self, err_msg):
        self.run_btn.setEnabled(True)
        self.progress_bar.hide()
        QMessageBox.critical(
            self, "Verification Failed",
            f"An error occurred during verification:\n\n{err_msg}"
        )

def _run_headless_json(argv):
    """Write deterministic pipeline counts for source/packaged parity checks."""
    marker = "--headless-json"
    index = argv.index(marker)
    if len(argv) < index + 4:
        raise SystemExit(
            "Usage: --headless-json OUTPUT_JSON ENGLISH_FILE BRAILLE_FILE [GRADE]"
        )
    output_path, english_file, braille_file = argv[index + 1:index + 4]
    grade = int(argv[index + 4]) if len(argv) > index + 4 else 1
    result = run_validation_pipeline(english_file, braille_file, grade)
    diff_results = result["diff_results"]
    internal_counts = Counter(
        issue.get("kind") for issue in diff_results.get("cell_issues", [])
    )
    summary = {
        "raw_parent_diffs": len(diff_results.get("diffs", [])),
        "normal": sum(internal_counts[k] for k in ("replacement", "insertion", "deletion")),
        "structural_children": internal_counts["structural_review"],
        "resolved_equal": internal_counts["resolved_equal"],
        "presentation": result["presentation_metrics"],
        "page_counts": {str(k): v for k, v in result["presentation_page_counts"].items()},
    }
    output = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, "w", encoding="utf-8") as stream:
        json.dump(summary, stream, ensure_ascii=False, indent=2)
    report_path = os.path.splitext(output)[0] + "_validation_report.html"
    with open(report_path, "w", encoding="utf-8") as stream:
        stream.write(result["report_html"])
    return 0


if __name__ == "__main__" and "--headless-json" in sys.argv:
    raise SystemExit(_run_headless_json(sys.argv))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)

    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor("#090b10"))
    dark_palette.setColor(QPalette.WindowText, QColor("#e2e4e9"))
    dark_palette.setColor(QPalette.Base, QColor("#0d1117"))
    dark_palette.setColor(QPalette.AlternateBase, QColor("#161b22"))
    dark_palette.setColor(QPalette.Text, QColor("#c9d1d9"))
    dark_palette.setColor(QPalette.Button, QColor("#161b22"))
    dark_palette.setColor(QPalette.ButtonText, QColor("#c9d1d9"))
    dark_palette.setColor(QPalette.Highlight, QColor("#6366f1"))
    dark_palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    app.setPalette(dark_palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
