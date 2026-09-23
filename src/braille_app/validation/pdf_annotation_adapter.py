"""Adapter from the stable validator to the recovered PDF visual pipeline.

The legacy renderer deliberately remains unchanged.  This module owns only
the boundary between a confirmed validator error's aligned actual-cell range
and the historical ``PdfCellProvenance`` records extracted from the user's
Braille PDF.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from braille_app.input_reader import PdfBrailleInput, PdfCellProvenance
from braille_app.brf_parser import ASCII_TO_UNICODE_BRAILLE
from braille_app.translation.braille_cells import cells_to_unicode

from .api import ValidationIssue, ValidationResult
from .validator import _actual_page_cells


class ProvenanceAlignmentError(ValueError):
    """The PDF cell stream cannot be safely aligned to validator cells."""


MAX_REVIEW_ANNOTATION_CELLS = 256


@dataclass(frozen=True)
class ProvenancePage:
    page: int
    validator_cells: tuple[int, ...]
    provenance_cells: tuple[PdfCellProvenance, ...]


@dataclass(frozen=True)
class ProvenanceAlignment:
    pages: tuple[ProvenancePage, ...]
    validator_cell_count: int
    provenance_cell_count: int
    unmatched_cells: int
    unexplained_offsets: int

    @property
    def by_page(self) -> dict[int, ProvenancePage]:
        return {page.page: page for page in self.pages}

    def cells_for_span(self, page: int, start: int, end: int) -> list[PdfCellProvenance]:
        """Map a page-local validator span to exact nonblank PDF cells.

        The validator stream contains layout blanks between lines.  Historical
        provenance intentionally stores only rendered Braille cells, so the
        mapping removes only zero-dot blanks using the same page text that the
        validator compared.  No fixed or document-specific offset is applied.
        """

        record = self.by_page.get(page)
        if record is None:
            return []
        nonblank_positions = [
            index for index, cell in enumerate(record.validator_cells) if cell != 0
        ]
        left = max(0, int(start))
        right = max(left, int(end))
        selected_positions = [
            position
            for position in nonblank_positions
            if left <= position < right
        ]
        if not selected_positions and left < len(record.validator_cells):
            # A replacement normally has a nonblank actual span.  This is only
            # a safe exact-cell fallback for a zero-width edge range; it never
            # guesses from source text or searches for a matching occurrence.
            next_position = next(
                (position for position in nonblank_positions if position >= left),
                None,
            )
            if next_position is not None and next_position < right:
                selected_positions = [next_position]
        provenance = []
        for position in selected_positions:
            compact_index = nonblank_positions.index(position)
            if compact_index < len(record.provenance_cells):
                provenance.append(record.provenance_cells[compact_index])
        return provenance


def build_provenance_alignment(pdf_input: PdfBrailleInput) -> ProvenanceAlignment:
    """Verify and index the historical PDF provenance stream by page."""

    content_pages = pdf_input.content.split("\f")
    provenance_by_page: dict[int, list[PdfCellProvenance]] = {}
    for word in pdf_input.word_provenance:
        for cell in word or []:
            provenance_by_page.setdefault(int(cell.page), []).append(cell)

    pages: list[ProvenancePage] = []
    validator_count = 0
    provenance_count = 0
    unmatched = 0
    offsets = 0
    max_page = max(len(content_pages), max(provenance_by_page, default=0))
    for page_number in range(1, max_page + 1):
        page_text = content_pages[page_number - 1] if page_number <= len(content_pages) else ""
        # The historical PDF reader stores rendered Braille glyphs as ASCII
        # source characters, but uses U+2800 for PDF whitespace.  The
        # validator accepts either representation; normalize only that
        # representation difference before comparing streams.
        validator_page_text = page_text.replace("\u2800", " ")
        validator_cells = _actual_page_cells(validator_page_text)
        provenance_cells = tuple(provenance_by_page.get(page_number, ()))
        nonblank = tuple(cell for cell in validator_cells if cell != 0)
        validator_count += len(nonblank)
        provenance_count += len(provenance_cells)
        if len(nonblank) != len(provenance_cells):
            unmatched += abs(len(nonblank) - len(provenance_cells))
            offsets += 1
        else:
            for expected, actual in zip(nonblank, provenance_cells):
                # Some historical Braille PDFs expose their glyph character
                # as NABCC/printable ASCII (for example `,` for dots 3456),
                # while newer embedded-font PDFs expose Unicode Braille.
                # The reader preserves that source character in
                # ``unicode_cell``; canonicalize both representations here.
                unicode_cell = ASCII_TO_UNICODE_BRAILLE.get(
                    actual.unicode_cell, actual.unicode_cell
                )
                if not unicode_cell or not (0x2800 <= ord(unicode_cell) <= 0x28FF):
                    unmatched += 1
                    offsets += 1
                    continue
                actual_mask = ord(unicode_cell) - 0x2800
                if expected != actual_mask:
                    unmatched += 1
                    offsets += 1
        pages.append(
            ProvenancePage(
                page=page_number,
                validator_cells=tuple(validator_cells),
                provenance_cells=provenance_cells,
            )
        )
    if offsets:
        raise ProvenanceAlignmentError(
            f"PDF provenance mismatch: {unmatched} unmatched cells across {offsets} page(s)."
        )
    return ProvenanceAlignment(
        pages=tuple(pages),
        validator_cell_count=validator_count,
        provenance_cell_count=provenance_count,
        unmatched_cells=unmatched,
        unexplained_offsets=offsets,
    )


def validation_errors_to_legacy_cell_issues(
    validation_result: ValidationResult,
    provenance: ProvenanceAlignment,
) -> list[dict]:
    """Adapt confirmed errors to the recovered visual pipeline's input shape.

    REVIEW and EXCLUDED records are intentionally omitted.  A missing actual
    range is not turned into a guessed coordinate; it is reported as an
    unrenderable error to the caller.
    """

    cell_issues: list[dict] = []
    for issue in validation_result.errors:
        actual_page = issue.actual_page_number or issue.braille_page
        start = issue.actual_cell_start
        end = issue.actual_cell_end
        if actual_page is None or start is None or end is None:
            raise ProvenanceAlignmentError(
                f"{issue.issue_id} has no aligned actual-cell range."
            )
        ranges = issue.localized_actual_ranges or ((actual_page, start, end),)
        cells = [cell for page, left, right in ranges
                 for cell in provenance.cells_for_span(page, left, right)]
        if (
            issue.rule_id in {
                "UEB_CASE1_SCOPE", "UEB_CASE2_SCOPE", "UEB_CASE3_SCOPE", "UEB_CASE4_SCOPE"
            }
            and any(
                issue.actual_braille[index] == 24
                and issue.actual_braille[index + 1] not in {2, 54, 4}
                for index in range(max(0, len(issue.actual_braille) - 1))
            )
        ):
            # The caret is Duxbury control furniture; retain only the payload
            # cell for an unexpected control pair so localization stays on
            # the changed physical cell.
            cells = [cell for cell in cells if cell.source_char != "^"]
        # A genuine zero-width deletion has no physical actual glyph. Keep its
        # confirmed error record for reporting, but do not invent a PDF box or
        # let it prevent export of other localized errors. Supported capital
        # deletions already carry their deterministic following-cell anchor.
        unanchored_deletion = start == end and not issue.actual_braille
        # A deleted uncontracted cell has no glyph of its own.  Keep the exact
        # alignment insertion point drawable by anchoring it to the next
        # physical cell.  Other profiles retain the historic no-guess rule.
        if unanchored_deletion and (
            issue.rule_id in {
                "UEB_CASE1_SCOPE", "UEB_CASE2_SCOPE", "UEB_CASE3_SCOPE", "UEB_CASE4_SCOPE"
            }
            or "UEB_CASE1_SCOPE" in issue.rule_ids_considered
            or "UEB_CASE2_SCOPE" in issue.rule_ids_considered
            or "UEB_CASE3_SCOPE" in issue.rule_ids_considered
            or "UEB_CASE4_SCOPE" in issue.rule_ids_considered
        ):
            cells = []
            for page, left, _ in ranges:
                record = provenance.by_page.get(page)
                if record is None:
                    continue
                positions = [index for index, mask in enumerate(record.validator_cells) if mask]
                footer_tops = [cell.top for cell in record.provenance_cells if cell.source_char == "#"]
                semantic = []
                after_caret = False
                for position, cell in zip(positions, record.provenance_cells):
                    if cell.source_char == "^":
                        after_caret = True
                        continue
                    if after_caret:
                        after_caret = False
                        continue
                    if any(abs(cell.top - top) <= 2.5 for top in footer_tops):
                        continue
                    semantic.append((position, cell))
                following = [cell for position, cell in semantic if position >= left][:1]
                preceding = [cell for position, cell in semantic if position < left][-1:]
                if preceding and following and (
                    abs(preceding[0].top - following[0].top) > 2.5
                    and left > 0 and record.validator_cells[left - 1] != 0
                ):
                    cells.extend(preceding)
                else:
                    cells.extend(following or preceding)
        if not cells and not unanchored_deletion:
            raise ProvenanceAlignmentError(
                f"{issue.issue_id} actual range {actual_page}:{start}-{end} "
                "has no matching PDF provenance cells."
            )
        cell_issues.append(
            {
                "kind": "replacement" if issue.actual_cell_start != issue.actual_cell_end else "cell_issue",
                "page": actual_page,
                "expected": cells_to_unicode(issue.expected_braille),
                "actual": cells_to_unicode(issue.actual_braille),
                "context": issue.source_text,
                "confidence": "high_confidence",
                "provenance_cells": [asdict(cell) for cell in cells],
                "validator_issue_id": issue.issue_id,
                "category": issue.category,
                "rule_id": issue.rule_id,
                "localization_reason": (
                    "Unanchored deletion: no actual PDF cell to highlight."
                    if unanchored_deletion else ""
                ),
            }
        )
    return cell_issues


def validation_to_diagnostic_cell_issues(
    validation_result: ValidationResult,
    provenance: ProvenanceAlignment,
) -> tuple[list[dict], list[dict]]:
    """Adapt ERROR and safely mappable REVIEW records for diagnostics.

    The normal adapter above remains ERROR-only.  This diagnostic adapter
    adds REVIEW records with an explicit status so the renderer can apply a
    separate visual treatment.  Unmappable reviews are returned separately
    and are never assigned guessed coordinates.
    """

    cell_issues = validation_errors_to_legacy_cell_issues(
        validation_result, provenance
    )
    unmapped: list[dict] = []
    for issue in validation_result.reviews:
        ranges = tuple(issue.localized_actual_ranges)
        if not ranges:
            unmapped.append(
                {
                    "review_id": issue.issue_id,
                    "source_page": issue.source_page_number,
                    "braille_page": issue.braille_page,
                    "category": issue.category,
                    "structural_subtype": issue.structural_subtype,
                    "reason": "No exact localized actual-cell range was retained for this review.",
                }
            )
            continue
        cells: list[PdfCellProvenance] = []
        range_records: list[dict] = []
        failed_reason = None
        for actual_page, start, end in ranges:
            range_cells = provenance.cells_for_span(actual_page, start, end)
            if not range_cells:
                failed_reason = (
                    f"Localized range {actual_page}:{start}-{end} has no matching PDF provenance cells."
                )
                break
            range_records.append(
                {
                    "page": actual_page,
                    "start": start,
                    "end": end,
                    "cell_count": len(range_cells),
                }
            )
            cells.extend(range_cells)
        if failed_reason is not None:
            unmapped.append(
                {
                    "review_id": issue.issue_id,
                    "source_page": issue.source_page_number,
                    "braille_page": issue.braille_page,
                    "category": issue.category,
                    "structural_subtype": issue.structural_subtype,
                    "reason": failed_reason,
                }
            )
            continue
        if len(cells) > MAX_REVIEW_ANNOTATION_CELLS:
            unmapped.append(
                {
                    "review_id": issue.issue_id,
                    "source_page": issue.source_page_number,
                    "braille_page": issue.braille_page,
                    "category": issue.category,
                    "structural_subtype": issue.structural_subtype,
                    "reason": (
                        "Rejected by diagnostic locality guard: "
                        f"{len(cells)} cells exceeds the {MAX_REVIEW_ANNOTATION_CELLS}-cell limit."
                    ),
                    "rejected_over_broad": True,
                    "highlighted_cell_count": len(cells),
                }
            )
            continue
        cell_issues.append(
            {
                "kind": "review",
                "status": "REVIEW",
                "page": actual_page,
                "expected": cells_to_unicode(issue.expected_braille),
                "actual": cells_to_unicode(issue.actual_braille),
                "context": issue.source_text,
                "confidence": "unverified",
                "provenance_cells": [asdict(cell) for cell in cells],
                "validator_issue_id": issue.issue_id,
                "category": issue.category,
                "rule_id": issue.rule_id,
                "source_page": issue.source_page_number,
                "structural_subtype": issue.structural_subtype,
                "review_reason": issue.review_reason,
                "rule_ids_considered": list(issue.rule_ids_considered),
                "actual_cell_ranges": range_records,
                "highlighted_cell_count": len(cells),
            }
        )
    return cell_issues, unmapped


def load_pdf_provenance(pdf_path: str | Path, profile: str = "math") -> tuple[PdfBrailleInput, ProvenanceAlignment]:
    """Load the historical PDF cell stream and verify it before annotation."""

    from braille_app.input_reader import read_braille_pdf_with_provenance

    pdf_input = read_braille_pdf_with_provenance(str(pdf_path), profile=profile)
    return pdf_input, build_provenance_alignment(pdf_input)


__all__ = [
    "ProvenanceAlignment",
    "ProvenanceAlignmentError",
    "ProvenancePage",
    "build_provenance_alignment",
    "load_pdf_provenance",
    "validation_to_diagnostic_cell_issues",
    "validation_errors_to_legacy_cell_issues",
]
