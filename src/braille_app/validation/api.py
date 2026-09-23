"""Stable GUI-facing validation boundary.

The GUI receives plain immutable data structures from this module.  It does
not need to know about internal rule-engine or alignment classes.  In
particular, one REVIEW source block produces one GUI review item, regardless
of how many cell-alignment opcodes occur inside that block.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
import re
from typing import Any, Callable, Literal
from zipfile import ZipFile
from xml.etree import ElementTree as ET

from braille_app.translation.braille_cells import unicode_to_cells

from .validator import BrailleValidator, ValidationReport, _block_for_offset


IssueStatus = Literal["ERROR", "REVIEW", "EXCLUDED_OUT_OF_SCOPE"]
ProgressCallback = Callable[[str], None]


@dataclass(frozen=True)
class ValidationIssue:
    """UI-safe result item with no dependency on validator internals."""

    issue_id: str
    status: IssueStatus
    category: str
    rule_id: str
    source_document: str
    source_rule: str
    source_page: str
    source_page_number: int
    braille_page: int | None
    actual_page_number: int | None = None
    block_id: int | str | None = None
    span: dict[str, int] = field(default_factory=dict)
    source_text: str = ""
    actual_braille: tuple[int, ...] = ()
    expected_braille: tuple[int, ...] = ()
    explanation: str = ""
    review_reason: str = ""
    structural_subtype: str = ""
    rule_ids_considered: tuple[str, ...] = ()
    bbox: Any = None
    actual_cell_start: int | None = None
    actual_cell_end: int | None = None
    localized_actual_ranges: tuple[tuple[int, int, int], ...] = ()


@dataclass(frozen=True)
class ValidationResult:
    errors: tuple[ValidationIssue, ...]
    reviews: tuple[ValidationIssue, ...]
    exclusions: tuple[ValidationIssue, ...]
    statistics: dict[str, int | float]
    pages: dict[int, dict[str, int]]
    alignment_diagnostics: tuple[ValidationIssue, ...] = ()
    pdf_input: Any | None = field(default=None, repr=False, compare=False)


def _block_offset(page, block_id: int | str | None) -> tuple[int, int]:
    """Return this block's page-flattened cell span, if available."""

    cursor = 0
    for block in page.blocks:
        if not block.braille:
            continue
        end = cursor + len(block.braille)
        if block.source_block == block_id:
            return cursor, end
        cursor = end + 1
    return 0, 0


def _block_and_rule(report: ValidationReport, page_number: int, block_id):
    page = next(
        (candidate for candidate in report.expected_document.pages if candidate.number == page_number),
        None,
    )
    if page is None:
        return None, None, None
    block = next((candidate for candidate in page.blocks if candidate.source_block == block_id), None)
    if block is None:
        return page, None, None
    rule = next((item for item in block.rule_results if item.status == "REVIEW"), None)
    rule = rule or next(
        (item for item in block.rule_results if item.status == "EXCLUDED_OUT_OF_SCOPE"),
        None,
    )
    rule = rule or next(iter(block.rule_results), None)
    return page, block, rule


def _related_difference(report: ValidationReport, page_number: int, block_id):
    return next(
        (
            difference
            for difference in report.differences
            if difference.page == page_number and difference.block_id == block_id
        ),
        None,
    )


def _actual_range_for_expected_span(
    report: ValidationReport,
    page_number: int,
    expected_start: int,
    expected_end: int,
) -> tuple[int, int] | None:
    """Project a source block's expected span onto aligned actual cells.

    This uses the alignment opcodes already produced by validation.  It does
    not search the actual text or apply a document-specific offset.
    """

    page_index = page_number - 1
    if page_index < 0 or page_index >= len(report.page_alignments):
        return None
    left = max(0, int(expected_start))
    right = max(left, int(expected_end))
    actual_ranges: list[tuple[int, int]] = []
    for opcode in report.page_alignments[page_index]:
        overlaps = opcode.expected_end > left and opcode.expected_start < right
        insertion_inside = (
            opcode.tag == "insert"
            and left <= opcode.expected_start <= right
            and opcode.actual_end > opcode.actual_start
        )
        if overlaps or insertion_inside:
            actual_ranges.append((opcode.actual_start, opcode.actual_end))
    if not actual_ranges:
        return None
    return min(start for start, _ in actual_ranges), max(
        end for _, end in actual_ranges
    )


def _localized_expected_ranges(block) -> tuple[tuple[int, int], ...]:
    """Locate each generated math record inside its containing block.

    The range is derived from the structured math translations already held
    by the expected block, never from a search through the user's PDF text.
    """

    if not block.math_records:
        return ()
    ranges: list[tuple[int, int]] = []
    cursor = 0
    for record in block.math_records:
        braille = getattr(record, "braille", "")
        if not braille:
            return ()
        start = block.braille.find(braille, cursor)
        if start < 0:
            return ()
        end = start + len(braille)
        ranges.append((start, end))
        cursor = end
    return tuple(ranges)


def _rule_issue(report: ValidationReport, page, block, rule, ordinal: int) -> ValidationIssue:
    """Adapt one rule-status source block into exactly one UI issue."""

    status: IssueStatus = (
        "REVIEW" if rule.status == "REVIEW" else "EXCLUDED_OUT_OF_SCOPE"
    )
    start, end = _block_offset(page, block.source_block)
    related = _related_difference(report, page.number, block.source_block)
    actual_range = _actual_range_for_expected_span(report, page.number, start, end)
    global_start = actual_range[0] if actual_range is not None else None
    global_end = actual_range[1] if actual_range is not None else None
    physical_ranges = report.actual_ranges(global_start, global_end) if actual_range is not None else ()
    actual_page = physical_ranges[0][0] if physical_ranges else page.number
    actual_start = physical_ranges[0][1] if physical_ranges else None
    actual_end = physical_ranges[0][2] if physical_ranges else None
    actual_braille = related.actual if related is not None else ()
    if actual_range is not None:
        actual_braille = report.actual_stream[global_start:global_end]
    localized_actual_ranges: list[tuple[int, int, int]] = []
    for localized_start, localized_end in _localized_expected_ranges(block):
        localized_range = _actual_range_for_expected_span(
            report, page.number, start + localized_start, start + localized_end
        )
        if localized_range is not None:
            localized_actual_ranges.extend(report.actual_ranges(*localized_range))
    return ValidationIssue(
        issue_id=f"VAL-{status[:3]}-{ordinal:04d}",
        status=status,
        category=rule.family,
        rule_id=rule.rule_id,
        source_document=rule.source_document,
        source_rule=rule.source_rule,
        source_page=rule.source_page,
        source_page_number=page.number,
        braille_page=actual_page,
        actual_page_number=actual_page,
        block_id=block.source_block,
        span={"expected_start": start, "expected_end": end},
        source_text=block.source_text,
        actual_braille=actual_braille,
        expected_braille=unicode_to_cells(block.braille),
        explanation=rule.explanation,
        review_reason=rule.explanation if status == "REVIEW" else "",
        structural_subtype=rule.source_construct,
        rule_ids_considered=tuple(item.rule_id for item in block.rule_results),
        actual_cell_start=actual_start,
        actual_cell_end=actual_end,
        localized_actual_ranges=tuple(localized_actual_ranges),
    )


def _error_issue(report: ValidationReport, difference, ordinal: int) -> ValidationIssue:
    _page, block, rule = _block_and_rule(report, difference.page, difference.block_id)
    if (
        block is None
        and difference.kind == "INSERTION"
        and not difference.expected
        and difference.expected_start > 0
        and 0 < difference.page <= len(report.expected_document.pages)
    ):
        previous = _block_for_offset(
            report.expected_document.pages[difference.page - 1],
            difference.expected_start - 1,
        )
        previous_rule = next(
            (
                item for item in (previous.rule_results if previous is not None else ())
                if item.rule_id in {"UEB_CASE1_SCOPE", "UEB_CASE2_SCOPE", "UEB_CASE3_SCOPE"}
            ),
            None,
        )
        if previous_rule is not None:
            block, rule = previous, previous_rule
    if block is not None and "NEMETH_SIMPLE_LINEAR_001" in difference.explanation:
        rule = next((item for item in block.rule_results
                     if item.rule_id == "NEMETH_SIMPLE_LINEAR_001" and item.status == "PASS"), rule)
    physical = report.actual_ranges(difference.actual_start, difference.actual_end)
    actual_page = physical[0][0] if physical else (difference.actual_page or difference.page)
    actual_start = physical[0][1] if physical else difference.actual_start
    actual_end = physical[0][2] if physical else difference.actual_end
    return ValidationIssue(
        issue_id=f"VAL-ERR-{ordinal:04d}",
        status="ERROR",
        category=difference.category,
        rule_id=rule.rule_id if rule is not None else "RULE_DISPATCH_001",
        source_document=rule.source_document if rule is not None else "",
        source_rule=rule.source_rule if rule is not None else "",
        source_page=rule.source_page if rule is not None else "",
        source_page_number=difference.page,
        braille_page=actual_page,
        actual_page_number=actual_page,
        block_id=difference.block_id,
        span={
            "expected_start": difference.expected_start,
            "expected_end": difference.expected_end,
            "actual_start": actual_start,
            "actual_end": actual_end,
        },
        source_text=block.source_text if block is not None else "",
        actual_braille=difference.actual,
        expected_braille=difference.expected,
        explanation=difference.explanation,
        structural_subtype=rule.source_construct if rule is not None else "",
        rule_ids_considered=tuple(item.rule_id for item in block.rule_results) if block is not None else (),
        actual_cell_start=actual_start,
        actual_cell_end=actual_end,
        localized_actual_ranges=physical if len(physical)>1 else (),
    )


def adapt_validation_report(
    report: ValidationReport,
    pdf_input: Any | None = None,
) -> ValidationResult:
    """Convert a report into non-duplicated Error/Review/Excluded UI data."""

    def logical_case1_report(current: ValidationReport) -> ValidationReport:
        # A two-cell transposition can be emitted by SequenceMatcher as an
        # insertion immediately followed by a deletion.  Case 1 owns that
        # bounded pair as one logical finding; other profiles retain their
        # historical raw-opcode behavior.
        collapsed = []
        index = 0
        while index < len(current.differences):
            first = current.differences[index]
            second = current.differences[index + 1] if index + 1 < len(current.differences) else None
            same_case1 = (
                second is not None
                and first.page == second.page
                and first.block_id == second.block_id
                and _block_and_rule(current, first.page, first.block_id)[2] is not None
                and _block_and_rule(current, first.page, first.block_id)[2].rule_id == "UEB_CASE1_SCOPE"
            )
            adjacent_swap = (
                same_case1
                and {first.kind, second.kind} == {"INSERTION", "DELETION"}
                and second.expected_start - first.expected_start in {-1, 0, 1}
                and abs(second.actual_start - first.actual_end) <= 1
            )
            if adjacent_swap:
                left, right = sorted((first, second), key=lambda item: item.expected_start)
                page_cells = unicode_to_cells(current.expected_document.pages[first.page - 1].flatten())
                collapsed.append(replace(
                    left,
                    expected=page_cells[left.expected_start:right.expected_end],
                    actual=current.actual_stream[min(left.actual_start, right.actual_start):max(left.actual_end, right.actual_end)],
                    kind="SUBSTITUTION",
                    expected_end=right.expected_end,
                    actual_start=min(left.actual_start, right.actual_start),
                    actual_end=max(left.actual_end, right.actual_end),
                    explanation="Adjacent Case 1 transposition cells are one logical finding.",
                ))
                index += 2
                continue
            collapsed.append(first)
            index += 1
        return replace(current, differences=tuple(collapsed))

    report = logical_case1_report(report)

    reviews: list[ValidationIssue] = []
    exclusions: list[ValidationIssue] = []
    special_block_keys: set[tuple[int, int | str]] = set()
    for page in report.expected_document.pages:
        for block in page.blocks:
            if block.rule_status not in {"REVIEW", "EXCLUDED_OUT_OF_SCOPE"}:
                continue
            rule = next(
                (
                    item for item in block.rule_results
                    if item.status == block.rule_status
                ),
                None,
            ) or next(iter(block.rule_results), None)
            if rule is None:
                continue
            special_block_keys.add((page.number, block.source_block))
            issue = _rule_issue(
                report,
                page,
                block,
                rule,
                len(reviews) + len(exclusions) + 1,
            )
            if issue.status == "REVIEW":
                reviews.append(issue)
            else:
                exclusions.append(issue)

    ignored_categories = {
        "LAYOUT_ONLY", "SPACING_ONLY", "ENCODING_ONLY",
        "MANUAL_REVIEW", "REVIEW_REQUIRED", "EXCLUDED_OUT_OF_SCOPE",
    }
    duxbury_typeforms = {(24, 2), (24, 6), (24, 54), (24, 4)}
    # Unaligned insertions in a supported uncontracted scope remain owned by
    # the source block. Duxbury's ^1/^7/^' pairs are layout controls, not
    # literary cells, regardless of which source rule owns the block.
    def is_uncontracted_alphabet_difference(difference) -> bool:
        _page, block, rule = _block_and_rule(report, difference.page, difference.block_id)
        if (
            rule is None
            and difference.kind == "INSERTION"
            and not difference.expected
            and difference.expected_start > 0
        ):
            # A layout-control payload can sit on the separator immediately
            # after its owning source block.
            previous = _block_for_offset(
                report.expected_document.pages[difference.page - 1],
                difference.expected_start - 1,
            )
            if previous is not None:
                rule = next(
                    (item for item in previous.rule_results if item.rule_id in {
                        "UEB_CASE1_SCOPE", "UEB_CASE2_SCOPE", "UEB_CASE3_SCOPE",
                        "UEB_CASE4_SCOPE",
                    }),
                    None,
                )
        actual = tuple(difference.actual)
        duxbury_typeform = any(
            actual[index:index + 2] in duxbury_typeforms
            for index in range(max(0, len(actual) - 1))
        )
        scope_rules = {"UEB_CASE1_SCOPE", "UEB_CASE2_SCOPE", "UEB_CASE3_SCOPE", "UEB_CASE4_SCOPE"}
        return duxbury_typeform or (
            rule is not None and rule.rule_id in scope_rules
        ) or (
            block is not None and any(
                item.rule_id in scope_rules and item.status == "PASS"
                for item in block.rule_results
            )
        )

    ignored_unmapped_insertions = sum(
        difference.kind == "INSERTION"
        and not difference.expected
        and not is_uncontracted_alphabet_difference(difference)
        for difference in report.differences
    )
    errors = []
    alignment_diagnostics = []
    from .alignment_diagnostics import displaced_difference_indices
    displaced = displaced_difference_indices(report)
    from braille_app.rules.basic_capitalization import localized_defect
    for index, difference in enumerate(report.differences, start=1):
        if (difference.page, difference.block_id) in special_block_keys:
            continue
        if (
            difference.kind == "INSERTION"
            and not difference.expected
            and is_uncontracted_alphabet_difference(difference)
            and any(
                tuple(difference.actual[index:index + 2]) in duxbury_typeforms
                for index in range(max(0, len(difference.actual) - 1))
            )
        ):
            continue
        if index - 1 in displaced and difference.category not in ignored_categories:
            evidence = displaced[index - 1]
            issue = _error_issue(report, difference, index)
            alignment_diagnostics.append(replace(
                issue, issue_id=f"VAL-ALIGN-{index:04d}",
                status="EXCLUDED_OUT_OF_SCOPE", category="ALIGNMENT_UNVERIFIED",
                rule_id="", source_document="", source_rule="", source_page="",
                explanation=(
                    "Page-local comparison is displaced: document-wide matching "
                    f"locates expected content on actual pages {evidence['actual_pages']}. "
                    "Suppressed from confirmed errors; this region is not certified. "
                    f"Unmatched nonblank cells: {evidence['unverified_nonblank_cells']}."
                ), structural_subtype="cross_page_alignment",
                actual_cell_start=None, actual_cell_end=None,
            ))
            continue
        page, block, _ = _block_and_rule(report, difference.page, difference.block_id)
        capital = None
        if block is not None:
            start, _ = _block_offset(page, block.source_block)
            capital = localized_defect(report, page, block, difference, start)
        if capital is not None:
            kind, left, right = capital
            issue = _error_issue(report, difference, index)
            physical = report.actual_ranges(left, right)
            if physical:
                _actual_page, left, right = physical[0]
            rule = next(r for r in block.rule_results if r.rule_id == 'UEB_8')
            errors.append(replace(issue, category='UEB_ERROR', rule_id='UEB_8',
                source_document=rule.source_document, source_rule=rule.source_rule, source_page=rule.source_page,
                explanation=kind + '; UEB 8.1.1 and 8.3.1-3.', structural_subtype=kind,
                actual_cell_start=left, actual_cell_end=right,
                span={**issue.span, 'actual_start':left, 'actual_end':right}))
            if difference.kind == 'INSERTION' and not difference.expected:
                ignored_unmapped_insertions -= 1
            continue
        if difference.category not in ignored_categories and not (
            difference.kind == 'INSERTION'
            and not difference.expected
            and not is_uncontracted_alphabet_difference(difference)
        ):
            errors.append(_error_issue(report,difference,index))
    page_stats: dict[int, dict[str, int]] = {}
    for issue in (*errors, *reviews, *exclusions):
        row = page_stats.setdefault(
            issue.source_page_number,
            {"errors": 0, "reviews": 0, "excluded": 0},
        )
        key = {
            "ERROR": "errors",
            "REVIEW": "reviews",
            "EXCLUDED_OUT_OF_SCOPE": "excluded",
        }[issue.status]
        row[key] += 1
    ignored_layout = sum(
        difference.category in {"LAYOUT_ONLY", "SPACING_ONLY", "ENCODING_ONLY"}
        for difference in report.differences
    )
    return ValidationResult(
        errors=tuple(errors),
        reviews=tuple(reviews),
        exclusions=tuple(exclusions),
        statistics={
            "pages": report.pages,
            "expected_cells": report.total_expected_cells,
            "matching_cells": report.matching_cells,
            "cell_accuracy": report.cell_accuracy,
            "raw_differences": len(report.differences),
            "ignored_layout_differences": ignored_layout,
            "ignored_unmapped_insertions": ignored_unmapped_insertions,
            "ignored_alignment_differences": len(alignment_diagnostics),
            "alignment_coverage_incomplete": int(bool(alignment_diagnostics)),
            "tolerated_duxbury_cells": sum(view.raw_length - len(view.cells) - view.joined_page_breaks for view in report.comparison_views),
            "joined_physical_page_breaks": sum(view.joined_page_breaks for view in report.comparison_views),
            "duxbury_normalized_spans": sum(len(view.normalized_spans) for view in report.comparison_views),
            "source_passages_total": report.source_passages_total,
            "source_passages_aligned": report.source_passages_aligned,
            "math_spans_total": report.math_spans_total,
            "math_spans_evaluated": report.math_spans_evaluated,
            "capitalization_opportunities_total": report.capitalization_opportunities_total,
            "capitalization_opportunities_evaluated": report.capitalization_opportunities_evaluated,
            "unresolved_math_spans": report.math_spans_total - report.math_spans_evaluated,
            "unresolved_source_passages": report.source_passages_total - report.source_passages_aligned,
            "unresolved_capitalization_opportunities": report.capitalization_opportunities_total - report.capitalization_opportunities_evaluated,
            "unmatched_switch_markers": sum(
                "switch" in reason.lower()
                for view in report.comparison_views
                for _start, _end, reason in view.skipped_spans
            ),
            "errors": len(errors),
            "reviews": len(reviews),
            "excluded": len(exclusions),
        },
        pages=page_stats,
        alignment_diagnostics=tuple(alignment_diagnostics),
        pdf_input=pdf_input,
    )


def validate_document(
    master_path: Any,
    braille_path: str | Path,
    progress: ProgressCallback | None = None,
    retain_pdf_provenance: bool = False,
    profile: str = "contracted_ueb_bana_nemeth",
) -> ValidationResult:
    """Validate a master source and BRF/text input for GUI callers."""

    def notify(message: str) -> None:
        if progress is not None:
            progress(message)

    notify("Reading source...")
    master = master_path
    if isinstance(master_path, (str, Path)) and str(master_path).lower().endswith(".docx"):
        # The Duxbury-ready master uses explicit ``=== PAGE n ===`` source
        # markers. Reading raw paragraph text preserves those markers and all
        # inline technical markers exactly; style-oriented DOCX extraction
        # strips/renumbers that source and changes the validation baseline.
        master = _docx_paragraph_dict(Path(master_path))

    notify("Reading user Braille...")
    pdf_input = None
    if isinstance(braille_path, (str, Path)) and Path(braille_path).suffix.lower() == ".pdf":
        # Use the same historical PDF reader as the annotation adapter.  Its
        # content stream is the validator input; provenance is loaded later
        # only for confirmed-error coordinate mapping.
        from braille_app.input_reader import read_braille_pdf_with_provenance

        pdf_input = read_braille_pdf_with_provenance(
            str(braille_path), profile=profile
        )
        actual = pdf_input.content
    else:
        actual = _read_gui_braille_input(braille_path)
    notify("Generating expected Braille and applying standards rules...")
    report = BrailleValidator().validate(master, actual, profile=profile)
    notify("Aligning and classifying results...")
    return adapt_validation_report(
        report,
        pdf_input=pdf_input if retain_pdf_provenance else None,
    )


def _docx_paragraph_dict(path: Path) -> dict:
    """Small dependency-free DOCX fallback for the GUI boundary."""

    namespace = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    with ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    blocks: list[dict[str, str]] = []
    for paragraph in root.findall(f".//{{{namespace}}}p"):
        parts: list[str] = []
        for node in paragraph.iter():
            if node.tag == f"{{{namespace}}}t":
                parts.append(node.text or "")
            elif node.tag == f"{{{namespace}}}tab":
                parts.append("\t")
            elif node.tag in {f"{{{namespace}}}br", f"{{{namespace}}}cr"}:
                parts.append("\n")
        blocks.append({"text": "".join(parts)})
    return {"pages": [{"print_page_number": 1, "blocks": blocks}]}


def _read_gui_braille_input(path_or_text: str | Path) -> str:
    """Normalize Duxbury BRF page furniture before validation."""

    if not isinstance(path_or_text, (str, Path)):
        return str(path_or_text)
    path = Path(path_or_text)
    if not path.is_file() or path.suffix.lower() != ".brf":
        return str(path_or_text)
    raw = path.read_text(encoding="latin1")
    headers = list(re.finditer(r"(?m)^[^\r\n]*,,PAGE [^\r\n]*\r?\n", raw))
    if not headers:
        return raw
    pages: list[str] = []
    footer = re.compile(r"\s{8,}#[A-Z0-9]+$")
    for index, header in enumerate(headers):
        end = headers[index + 1].start() if index + 1 < len(headers) else len(raw)
        body = raw[header.end():end].replace("\x0c", "\n").replace("\r", "")
        lines = [footer.sub("", line) for line in body.split("\n") if line.strip()]
        pages.append("\n".join(lines))
    return "\f".join(pages)


__all__ = [
    "ValidationIssue",
    "ValidationResult",
    "adapt_validation_report",
    "validate_document",
]
