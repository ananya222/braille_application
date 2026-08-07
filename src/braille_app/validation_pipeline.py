"""Shared validation pipeline used by the GUI and checkpoint parity checks."""

from __future__ import annotations

from braille_app.brf_parser import BRFParser
from braille_app.diff_engine import DiffEngine
from braille_app.doc_extractor import DocumentExtractor
from braille_app.format_engine import FormatEngine
from braille_app.input_reader import read_braille_input, read_braille_pdf_with_provenance
from braille_app.presentation_grouping import (
    build_presentation_items,
    presentation_metrics,
    presentation_page_metrics,
)
from braille_app.provenance_resolver import localize_diff_records
from braille_app.report_generator import ReportGenerator


def run_validation_pipeline(english_file: str, braille_file: str, grade: int) -> dict:
    """Run the current source pipeline and return detector plus presentation data."""
    import louis

    extractor = DocumentExtractor()
    extracted_data = extractor.extract(english_file)

    provenance_input = None
    if braille_file.lower().endswith(".pdf"):
        provenance_input = read_braille_pdf_with_provenance(braille_file)
        braille_content = provenance_input.content
    else:
        braille_content = read_braille_input(braille_file)

    brf_results = BRFParser().parse_content(braille_content)
    table_list = ["en-ueb-g2.ctb" if grade == 2 else "en-ueb-g1.ctb"]
    expected_blocks = []
    for page in extracted_data.get("pages", []):
        for block in page.get("blocks", []):
            text = block.get("text", "")
            translated_braille = louis.translateString(table_list, text) if text.strip() else ""
            expected_blocks.append({
                "type": block.get("type", "body"),
                "text": translated_braille,
                "source_text": text,
            })

    actual_content_text = "\x0c".join(
        "\n".join(page.get("raw_lines", []))
        for page in brf_results.get("pages", [])
    )
    diff_engine = DiffEngine(grade=grade)
    diff_results = diff_engine.compare(expected_blocks, actual_content_text)
    if provenance_input is not None:
        diff_results["cell_issues"] = localize_diff_records(
            diff_results.get("diffs", []),
            provenance_input.word_provenance,
            diff_engine._source_tokens_for_expected(expected_blocks),
        )
    else:
        diff_results["cell_issues"] = []

    diff_results["presentation_items"] = build_presentation_items(
        diff_results["cell_issues"], diff_results.get("diffs", [])
    )
    diff_results["presentation_page_counts"] = presentation_page_metrics(
        diff_results["cell_issues"], diff_results["presentation_items"]
    )
    format_results = FormatEngine().check_format(expected_blocks, actual_content_text)
    report_html = ReportGenerator().generate_report(
        brf_results, diff_results, format_results, grade
    )
    return {
        "brf_results": brf_results,
        "diff_results": diff_results,
        "format_results": format_results,
        "report_html": report_html,
        "presentation_metrics": presentation_metrics(diff_results["presentation_items"]),
        "presentation_page_counts": diff_results["presentation_page_counts"],
    }

