"""Qt front end for the stable standards-aware Braille validator."""

from __future__ import annotations

import os
from pathlib import Path
import sys
import json
from dataclasses import asdict

from PySide6.QtCore import QUrl, Qt, QThread, Signal
from PySide6.QtGui import QColor, QDesktopServices, QFont
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from braille_app.translation.braille_cells import cells_to_unicode, dots_for_cells
from braille_app.validation.api import ValidationIssue, ValidationResult, validate_document
from braille_app.runtime_paths import output_directory


class ValidationThread(QThread):
    """Run the validator off the Qt event loop so the UI stays responsive."""

    finished = Signal(object)
    failed = Signal(str)
    status_update = Signal(str)

    def __init__(self, english_file: str, braille_file: str):
        super().__init__()
        self.english_file = english_file
        self.braille_file = braille_file
        self.annotated_pdf_path: str | None = None
        self.diagnostic_pdf_path: str | None = None
        self.report_path: str | None = None
        self.diagnostic_report_path: str | None = None
        self.annotation_error: str | None = None
        self.provenance_alignment = None
        self.mapped_review_count = 0
        self.unmapped_review_count = 0
        self.rejected_over_broad_review_count = 0

    def run(self) -> None:
        result: ValidationResult | None = None
        try:
            result = validate_document(
                self.english_file,
                self.braille_file,
                progress=self.status_update.emit,
                retain_pdf_provenance=True,
            )
            if getattr(sys, 'frozen', False):
                print('Validation completed: ' + json.dumps(result.statistics), flush=True)
            if Path(self.braille_file).suffix.lower() == ".pdf" and result is not None:
                self.status_update.emit("Mapping confirmed errors to PDF cells...")
                from braille_app.validation.pdf_annotation_adapter import (
                    build_provenance_alignment,
                    load_pdf_provenance,
                    validation_errors_to_legacy_cell_issues,
                    validation_to_diagnostic_cell_issues,
                )
                from braille_app.visual_annotations import (
                    export_annotated_pdf,
                    export_diagnostic_pdf,
                    group_provenance_boxes,
                    visual_issues_from_cell_issues,
                )

                if result.pdf_input is not None:
                    _pdf_input = result.pdf_input
                    alignment = build_provenance_alignment(_pdf_input)
                else:
                    _pdf_input, alignment = load_pdf_provenance(
                        self.braille_file, profile="math"
                    )
                legacy_issues = validation_errors_to_legacy_cell_issues(
                    result, alignment
                )
                visual_issues = visual_issues_from_cell_issues(legacy_issues)
                output_dir = output_directory()
                output_path = output_dir / (
                    f"{Path(self.braille_file).stem}_validator_annotated.pdf"
                )
                self.status_update.emit("Writing annotated PDF...")
                export_annotated_pdf(
                    self.braille_file, str(output_path), visual_issues
                )
                self.annotated_pdf_path = str(output_path)
                self.provenance_alignment = alignment
                diagnostic_records, unmapped_reviews = (
                    validation_to_diagnostic_cell_issues(result, alignment)
                )
                self.mapped_review_count = sum(
                    record.get("status") == "REVIEW"
                    for record in diagnostic_records
                )
                self.unmapped_review_count = len(unmapped_reviews)
                self.rejected_over_broad_review_count = sum(
                    bool(item.get("rejected_over_broad"))
                    for item in unmapped_reviews
                )
                diagnostic_visual_issues = visual_issues_from_cell_issues(
                    diagnostic_records
                )
                diagnostic_path = output_dir / (
                    f"{Path(self.braille_file).stem}_validator_diagnostic.pdf"
                )
                self.status_update.emit("Saving diagnostic artifacts...")
                export_diagnostic_pdf(
                    self.braille_file,
                    str(diagnostic_path),
                    diagnostic_visual_issues,
                )
                self.diagnostic_pdf_path = str(diagnostic_path)
                report_path = output_dir / (
                    f"{Path(self.braille_file).stem}_validator_report.json"
                )
                report_issues = []
                for issue in (*result.errors, *result.reviews, *result.exclusions):
                    report_issues.append(
                        {
                            "issue_id": issue.issue_id,
                            "status": issue.status,
                            "category": issue.category,
                            "rule_id": issue.rule_id,
                            "source_page": issue.source_page_number,
                            "braille_page": issue.braille_page,
                            "source_text": issue.source_text,
                            "actual_braille_cells": list(issue.actual_braille),
                            "actual_braille_unicode": cells_to_unicode(issue.actual_braille),
                            "expected_braille_cells": list(issue.expected_braille),
                            "expected_braille_unicode": cells_to_unicode(issue.expected_braille),
                            "review_reason": issue.review_reason,
                            "explanation": issue.explanation,
                            "structural_subtype": issue.structural_subtype,
                            "actual_cell_start": issue.actual_cell_start,
                            "actual_cell_end": issue.actual_cell_end,
                        }
                    )
                report_path.write_text(
                    json.dumps(
                        {
                            "master": self.english_file,
                            "braille_input": self.braille_file,
                            "annotated_pdf": str(output_path),
                            "summary": {
                                "confirmed_errors": len(result.errors),
                                "unverified": len(result.reviews),
                                "excluded_non_text": len(result.exclusions),
                            },
                            "issues": report_issues,
                        },
                        indent=2,
                        ensure_ascii=False,
                    ),
                    encoding="utf-8",
                )
                self.report_path = str(report_path)
                diagnostic_report_path = output_dir / (
                    f"{Path(self.braille_file).stem}_validator_diagnostic_report.json"
                )
                records_by_review = {
                    record.get("validator_issue_id"): record
                    for record in diagnostic_records
                    if record.get("status") == "REVIEW"
                }
                unmapped_by_review = {
                    item.get("review_id"): item for item in unmapped_reviews
                }
                rejected_over_broad = sum(
                    bool(item.get("rejected_over_broad"))
                    for item in unmapped_reviews
                )
                diagnostic_reviews = []
                for issue in result.reviews:
                    record = records_by_review.get(issue.issue_id)
                    unmapped = unmapped_by_review.get(issue.issue_id)
                    coordinates = [
                        {
                            "page": cell.get("page"),
                            "x0": cell.get("x0"),
                            "x1": cell.get("x1"),
                            "top": cell.get("top"),
                            "bottom": cell.get("bottom"),
                        }
                        for cell in (record or {}).get("provenance_cells", [])
                    ]
                    rectangles = [
                        {
                            "page": box.page,
                            "x0": box.x0,
                            "top": box.top,
                            "x1": box.x1,
                            "bottom": box.bottom,
                        }
                        for box in group_provenance_boxes(
                            (record or {}).get("provenance_cells", [])
                        )
                    ]
                    diagnostic_reviews.append(
                        {
                            "review_id": issue.issue_id,
                            "pdf_page": issue.actual_page_number,
                            "source_page": issue.source_page_number,
                            "category": issue.category,
                            "structural_subtype": issue.structural_subtype,
                            "source_text": issue.source_text,
                            "actual_braille_cells": list(issue.actual_braille),
                            "actual_braille_unicode": cells_to_unicode(issue.actual_braille),
                            "candidate_braille_cells": list(issue.expected_braille),
                            "candidate_braille_unicode": cells_to_unicode(issue.expected_braille),
                            "review_reason": issue.review_reason,
                            "rule_ids_considered": list(issue.rule_ids_considered),
                            "actual_cell_start": (
                                (record or {}).get("actual_cell_ranges", [{}])[0].get("start")
                                if record
                                else None
                            ),
                            "actual_cell_end": (
                                (record or {}).get("actual_cell_ranges", [{}])[-1].get("end")
                                if record
                                else None
                            ),
                            "actual_cell_ranges": (record or {}).get(
                                "actual_cell_ranges", []
                            ),
                            "highlighted_cell_count": (record or {}).get(
                                "highlighted_cell_count", 0
                            ),
                            "coordinates": coordinates,
                            "rectangle_coordinates": rectangles,
                            "mapping_status": "MAPPED" if record else "UNMAPPED_REVIEW",
                            "unmapped_reason": (unmapped or {}).get("reason"),
                        }
                    )
                diagnostic_report_path.write_text(
                    json.dumps(
                        {
                            "master": self.english_file,
                            "braille_input": self.braille_file,
                            "normal_annotated_pdf": str(output_path),
                            "diagnostic_pdf": str(diagnostic_path),
                            "alignment_diagnostics": [asdict(issue) for issue in result.alignment_diagnostics],
                            "alignment_coverage_incomplete": bool(result.alignment_diagnostics),
                            "summary": {
                                "confirmed_errors": len(result.errors),
                                "review": len(result.reviews),
                                "excluded": len(result.exclusions),
                                "mapped_review": len(records_by_review),
                                "unmapped_review": len(unmapped_reviews),
                                "rejected_over_broad_review": rejected_over_broad,
                            },
                            "provenance_alignment": {
                                "validator_cells": alignment.validator_cell_count,
                                "pdf_cells": alignment.provenance_cell_count,
                                "unmatched_cells": alignment.unmatched_cells,
                                "unexplained_offsets": alignment.unexplained_offsets,
                            },
                            "reviews": diagnostic_reviews,
                        },
                        indent=2,
                        ensure_ascii=False,
                    ),
                    encoding="utf-8",
                )
                self.diagnostic_report_path = str(diagnostic_report_path)
            self.finished.emit(result)
        except Exception as exc:  # pragma: no cover - Qt delivery path
            if Path(self.braille_file).suffix.lower() == ".pdf" and result is not None:
                # Validation itself has already completed.  Keep its result
                # visible while reporting that coordinate-safe annotation did
                # not complete; never substitute guessed coordinates.
                self.annotation_error = str(exc)
                self.finished.emit(result)
            else:
                self.failed.emit(str(exc))


def _format_cells(cells: tuple[int, ...]) -> str:
    if not cells:
        return "Not available for this region."
    return f"{cells_to_unicode(cells)}\nDots: {', '.join(dots_for_cells(cells))}"


class MainWindow(QMainWindow):
    """Existing two-page workflow, backed by the production validation API."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Braille Validation Utility")
        self.resize(980, 700)
        self.setMinimumSize(760, 560)
        self.english_path = ""
        self.braille_path = ""
        self.current_result: ValidationResult | None = None
        self.thread: ValidationThread | None = None
        self.annotated_pdf_path: str | None = None
        self.diagnostic_pdf_path: str | None = None
        self.report_path: str | None = None
        self.diagnostic_report_path: str | None = None
        self._apply_styles()

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        self.init_uploader_page()
        self.init_results_page()

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow { background-color: #0b0f19; }
            QLabel { color: #f3f4f6; font-family: 'Segoe UI', Arial, sans-serif; }
            QPushButton {
                background-color: #8b5cf6; color: #ffffff; border: none;
                border-radius: 6px; padding: 10px 16px; font-size: 14px;
                font-weight: bold; min-width: 100px;
            }
            QPushButton:hover { background-color: #7c3aed; }
            QPushButton:pressed { background-color: #6d28d9; }
            QProgressBar {
                border: 1px solid #1f2937; border-radius: 4px;
                background-color: #151c2c; color: #ffffff;
            }
            QProgressBar::chunk { background-color: #8b5cf6; }
            QTextEdit, QTreeWidget {
                background-color: #151c2c; color: #e5e7eb;
                font-family: Consolas, 'Courier New', monospace; font-size: 12px;
                border: 1px solid #1f2937; border-radius: 4px; padding: 6px;
            }
            QCheckBox { color: #fbbf24; font-weight: bold; }
            """
        )

    def init_uploader_page(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(22)

        title = QLabel("Braille Validation Utility")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #a78bfa; margin-bottom: 8px;")
        layout.addWidget(title)

        profile = QLabel("Profile: English (UEB) — BANA with Nemeth")
        profile.setAlignment(Qt.AlignmentFlag.AlignCenter)
        profile.setStyleSheet("color: #c4b5fd; font-size: 13px;")
        layout.addWidget(profile)

        eng_layout = QHBoxLayout()
        self.eng_lbl = QLabel("Select Duxbury-ready English master (.docx)")
        self.eng_lbl.setStyleSheet("color: #9ca3af; font-size: 13px;")
        eng_button = QPushButton("Upload English File")
        eng_button.clicked.connect(self.select_english_file)
        eng_layout.addWidget(self.eng_lbl, 1)
        eng_layout.addWidget(eng_button)
        layout.addLayout(eng_layout)

        brl_layout = QHBoxLayout()
        self.brl_lbl = QLabel("Select translated Braille output (.brf or .pdf)")
        self.brl_lbl.setStyleSheet("color: #9ca3af; font-size: 13px;")
        brl_button = QPushButton("Upload Braille File")
        brl_button.clicked.connect(self.select_braille_file)
        brl_layout.addWidget(self.brl_lbl, 1)
        brl_layout.addWidget(brl_button)
        layout.addLayout(brl_layout)

        self.progress_status = QLabel("")
        self.progress_status.setStyleSheet("color: #cbd5e1; font-size: 12px;")
        self.progress_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress_status)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        action_layout = QHBoxLayout()
        action_layout.addStretch()
        self.run_btn = QPushButton("Validate")
        self.run_btn.setStyleSheet(
            "QPushButton { background-color: #8b5cf6; padding: 12px 28px; font-size: 15px; }"
            "QPushButton:hover { background-color: #7c3aed; }"
        )
        self.run_btn.clicked.connect(self.run_verification)
        action_layout.addWidget(self.run_btn)
        action_layout.addStretch()
        layout.addLayout(action_layout)
        layout.addStretch()
        self.stacked_widget.addWidget(page)

    def init_results_page(self) -> None:
        self.results_page = QWidget()
        layout = QVBoxLayout(self.results_page)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        self.res_title = QLabel("Validation Results")
        self.res_title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.res_title.setStyleSheet("color: #f3f4f6;")
        layout.addWidget(self.res_title)

        summary_layout = QHBoxLayout()
        self.error_summary = self._summary_label("Confirmed Errors: 0", "#2563eb")
        self.review_summary = self._summary_label("Unverified / Needs Standards Coverage: 0", "#f59e0b")
        self.excluded_summary = self._summary_label("Excluded Non-Text: 0", "#94a3b8")
        summary_layout.addWidget(self.error_summary)
        summary_layout.addWidget(self.review_summary)
        summary_layout.addWidget(self.excluded_summary)
        # Coverage remains in the result/report, not in the normal demo UI.
        self.review_summary.hide()
        self.excluded_summary.hide()
        layout.addLayout(summary_layout)

        self.review_toggle = QCheckBox("Show unverified regions (development debug view)")
        self.review_toggle.setChecked(False)
        self.review_toggle.hide()
        self.review_toggle.stateChanged.connect(self.render_issue_list)
        layout.addWidget(self.review_toggle)

        self.visualization_note = QLabel(
            "Only confirmed errors are displayed. This result is not a certification "
            "of complete standards coverage. Coverage details remain in the diagnostic reports."
        )
        self.visualization_note.setWordWrap(True)
        self.visualization_note.setStyleSheet(
            "color: #cbd5e1; background-color: #111827; border: 1px dashed #475569; padding: 7px;"
        )
        layout.addWidget(self.visualization_note)
        self.visualization_note.hide()

        splitter = QSplitter(Qt.Orientation.Vertical)
        self.issue_tree = QTreeWidget()
        self.issue_tree.setHeaderLabels(["Status", "Page", "Block", "Category", "Rule / Coverage"])
        self.issue_tree.setColumnWidth(0, 145)
        self.issue_tree.setColumnWidth(1, 60)
        self.issue_tree.setColumnWidth(2, 70)
        self.issue_tree.setColumnWidth(3, 230)
        self.issue_tree.currentItemChanged.connect(self.show_issue_details)
        splitter.addWidget(self.issue_tree)

        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setPlaceholderText("Select a result to inspect its source, cells, and standards context.")
        splitter.addWidget(self.detail_text)
        splitter.setSizes([310, 220])
        layout.addWidget(splitter, 1)

        self.report_lbl = QLabel("")
        self.report_lbl.setStyleSheet("color: #9ca3af; font-size: 11px;")
        self.report_lbl.setWordWrap(True)
        layout.addWidget(self.report_lbl)

        controls = QHBoxLayout()
        self.back_btn = QPushButton("Back")
        self.back_btn.clicked.connect(self.go_back)
        controls.addWidget(self.back_btn)
        controls.addStretch()
        self.open_annotated_btn = QPushButton("Open Annotated PDF")
        self.open_annotated_btn.setEnabled(False)
        self.open_annotated_btn.clicked.connect(self.open_annotated_pdf)
        controls.addWidget(self.open_annotated_btn)
        self.open_diagnostic_btn = QPushButton("Open Diagnostic PDF")
        self.open_diagnostic_btn.setEnabled(False)
        self.open_diagnostic_btn.clicked.connect(self.open_diagnostic_pdf)
        controls.addWidget(self.open_diagnostic_btn)
        self.open_diagnostic_btn.hide()
        self.open_output_btn = QPushButton("Open Output Folder")
        self.open_output_btn.clicked.connect(self.open_output_folder)
        controls.addWidget(self.open_output_btn)
        layout.addLayout(controls)
        self.stacked_widget.addWidget(self.results_page)

    @staticmethod
    def _summary_label(text: str, color: str) -> QLabel:
        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet(
            f"color: {color}; background-color: #111827; border: 1px solid {color}; "
            "border-radius: 5px; padding: 8px; font-weight: bold;"
        )
        return label

    def select_english_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Duxbury-Ready English Master",
            "",
            "Duxbury-ready master (*.docx)",
        )
        if file_path:
            self.english_path = file_path
            self.eng_lbl.setText(os.path.basename(file_path))
            self.eng_lbl.setStyleSheet("color: #10b981; font-size: 13px; font-weight: bold;")

    def select_braille_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Translated Braille Output",
            "",
            "Braille Ready Files (*.brf *.pdf)",
        )
        if file_path:
            self.braille_path = file_path
            self.brl_lbl.setText(os.path.basename(file_path))
            self.brl_lbl.setStyleSheet("color: #10b981; font-size: 13px; font-weight: bold;")

    def run_verification(self) -> None:
        if not self.english_path or not self.braille_path:
            QMessageBox.warning(
                self,
                "Missing Files",
                "Select both a Duxbury-ready English master and a translated BRF or Braille PDF file.",
            )
            return
        self.run_btn.setEnabled(False)
        self.progress_status.setText("Starting validation...")
        self.progress_bar.show()
        self.thread = ValidationThread(self.english_path, self.braille_path)
        self.thread.status_update.connect(self.progress_status.setText)
        self.thread.finished.connect(self.on_success)
        self.thread.failed.connect(self.on_error)
        self.thread.start()

    def on_success(self, result: ValidationResult) -> None:
        self.current_result = result
        self.annotated_pdf_path = (
            self.thread.annotated_pdf_path if self.thread is not None else None
        )
        self.diagnostic_pdf_path = (
            self.thread.diagnostic_pdf_path if self.thread is not None else None
        )
        self.report_path = self.thread.report_path if self.thread is not None else None
        self.diagnostic_report_path = (
            self.thread.diagnostic_report_path if self.thread is not None else None
        )
        self.run_btn.setEnabled(True)
        self.progress_bar.hide()
        self.progress_status.setText("")
        self.error_summary.setText(f"Confirmed Errors: {len(result.errors)}")
        self.review_summary.setText(
            f"Unverified / Needs Standards Coverage: {len(result.reviews)}"
        )
        self.excluded_summary.setText(f"Excluded Non-Text: {len(result.exclusions)}")
        if result.errors:
            self.res_title.setText("Validation Complete — Confirmed Errors Found")
            self.res_title.setStyleSheet("color: #60a5fa;")
        else:
            self.res_title.setText("No confirmed Braille errors detected.")
            self.res_title.setStyleSheet("color: #10b981;")
        if self.annotated_pdf_path:
            self.report_lbl.setText(
                f"Annotated PDF saved to: {self.annotated_pdf_path}\n"
                f"Validation report saved to: {self.report_path}"
            )
            self.open_annotated_btn.setEnabled(True)
            self.open_diagnostic_btn.setEnabled(bool(self.diagnostic_pdf_path))
        elif self.thread is not None and self.thread.annotation_error:
            self.report_lbl.setText(
                "Validation completed, but the annotated PDF was not generated: "
                + self.thread.annotation_error
            )
            self.open_annotated_btn.setEnabled(False)
            self.open_diagnostic_btn.setEnabled(False)
        else:
            self.report_lbl.setText(
                "Live result from the standards-aware validator. Select the corresponding "
                "Braille PDF to generate coordinate-safe annotations."
            )
            self.open_annotated_btn.setEnabled(False)
            self.open_diagnostic_btn.setEnabled(False)
        self.render_issue_list()
        self.stacked_widget.setCurrentWidget(self.results_page)

    def render_issue_list(self) -> None:
        self.issue_tree.clear()
        self.detail_text.clear()
        if self.current_result is None:
            return
        groups: list[tuple[str, tuple[ValidationIssue, ...], str, QColor]] = [
            ("● Confirmed Errors", self.current_result.errors, "ERROR", QColor("#60a5fa")),
        ]
        # Deliberately ERROR-only regardless of hidden debug-control state.
        for label, issues, status, color in groups:
            parent = QTreeWidgetItem([f"{label} ({len(issues)})", "", "", "", ""])
            parent.setFirstColumnSpanned(True)
            parent.setForeground(0, color)
            parent.setExpanded(True)
            self.issue_tree.addTopLevelItem(parent)
            for issue in issues:
                item = QTreeWidgetItem(
                    [
                        {"ERROR": "● Confirmed Error", "REVIEW": "◇ Unverified", "EXCLUDED_OUT_OF_SCOPE": "○ Excluded"}[issue.status],
                        str(issue.source_page_number),
                        str(issue.block_id if issue.block_id is not None else "—"),
                        issue.structural_subtype or issue.category,
                        issue.rule_id,
                    ]
                )
                item.setData(0, Qt.ItemDataRole.UserRole, issue)
                for column in range(5):
                    item.setForeground(column, color)
                parent.addChild(item)
        self.issue_tree.expandAll()

    def show_issue_details(self, current: QTreeWidgetItem | None, _previous: QTreeWidgetItem | None) -> None:
        if current is None:
            return
        issue = current.data(0, Qt.ItemDataRole.UserRole)
        if not isinstance(issue, ValidationIssue):
            return
        review_note = ""
        if issue.status == "REVIEW":
            review_note = (
                "\nSTATUS: UNVERIFIED — this is not presented as an error.\n"
                "The candidate expected cells are diagnostic only and are not yet fully standards-confirmed.\n"
            )
        elif issue.status == "EXCLUDED_OUT_OF_SCOPE":
            review_note = "\nSTATUS: EXCLUDED NON-TEXT — not highlighted as an error.\n"
        bbox = "No PDF bounding box is available in this build."
        if issue.bbox is not None:
            bbox = str(issue.bbox)
        self.detail_text.setPlainText(
            f"Status: {issue.status}\n"
            f"Category: {issue.category}\n"
            f"Structural subtype: {issue.structural_subtype or 'Not available'}\n"
            f"Source page: {issue.source_page_number}\n"
            f"Braille page: {issue.braille_page if issue.braille_page is not None else 'Not available'}\n"
            f"Source block: {issue.block_id if issue.block_id is not None else 'Not available'}\n"
            f"Rule ID: {issue.rule_id}\n"
            f"Rules considered: {', '.join(issue.rule_ids_considered) or 'Not available'}\n"
            f"Standard source: {issue.source_document or 'Not available'}\n"
            f"Section/page: {issue.source_rule or 'Not available'} / {issue.source_page or 'Not available'}\n"
            f"Span: {issue.span or 'Not available'}\n"
            f"Bounding box: {bbox}\n"
            f"Reason: {issue.review_reason or issue.explanation or 'Not available'}\n"
            f"{review_note}\n"
            f"Source text:\n{issue.source_text or 'Not available'}\n\n"
            f"Actual Braille (aligned cells where available):\n{_format_cells(issue.actual_braille)}\n\n"
            f"Candidate expected Braille:\n{_format_cells(issue.expected_braille)}"
        )

    def go_back(self) -> None:
        self.stacked_widget.setCurrentIndex(0)

    def open_annotated_pdf(self) -> None:
        if self.annotated_pdf_path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.annotated_pdf_path))

    def open_diagnostic_pdf(self) -> None:
        if self.diagnostic_pdf_path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.diagnostic_pdf_path))

    def open_output_folder(self) -> None:
        output_dir = output_directory()
        output_dir.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(output_dir)))

    def on_error(self, message: str) -> None:
        self.run_btn.setEnabled(True)
        self.progress_bar.hide()
        self.progress_status.setText("")
        QMessageBox.critical(self, "Validation Failed", f"An error occurred during validation:\n\n{message}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    if "--packaging-smoke" in sys.argv and os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        # Offscreen Qt does not enumerate the Windows font registry.
        from PySide6.QtGui import QFontDatabase
        for font_name in ("segoeui.ttf", "segoeuib.ttf", "seguisym.ttf", "arial.ttf"):
            QFontDatabase.addApplicationFont(str(Path(os.environ.get("SystemRoot", "C:/Windows")) / "Fonts" / font_name))
    window = MainWindow()
    window.show()
    if "--packaging-smoke" in sys.argv:
        from braille_app.packaging_smoke import run
        sys.exit(run(app, window, sys.argv[1:]))
    sys.exit(app.exec())
