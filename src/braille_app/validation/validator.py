"""Rule-aware expected-vs-actual Braille validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from braille_app.input_reader import read_braille_input
from braille_app.translation.braille_cells import (
    ascii_to_cells,
    unicode_to_cells,
)
from braille_app.translation.expected_document import (
    ExpectedBrailleDocument,
    ExpectedPage,
    generate_expected_braille,
)
from braille_app.translation.profiles import get_profile

from .alignment import CellOpcode, _align_bounded_block, align_cells, align_monotonic_page_regions
from .simple_math_comparison import ComparisonView, comparison_view, align_with_operator_anchors


@dataclass(frozen=True)
class CellDifference:
    page: int
    expected: tuple[int, ...]
    actual: tuple[int, ...]
    kind: str
    category: str
    explanation: str
    confidence: str
    expected_start: int = 0
    expected_end: int = 0
    actual_start: int = 0
    actual_end: int = 0
    block_id: int | str | None = None
    actual_page: int | None = None


@dataclass(frozen=True)
class ValidationReport:
    expected_document: ExpectedBrailleDocument
    differences: tuple[CellDifference, ...]
    total_expected_cells: int
    matching_cells: int
    pages: int
    actual_pages: tuple[tuple[int, ...], ...] = ()
    page_alignments: tuple[tuple[CellOpcode, ...], ...] = ()
    comparison_views: tuple[ComparisonView, ...] = ()
    actual_stream: tuple[int, ...] = ()
    actual_page_offsets: tuple[int, ...] = ()
    source_page_offsets: tuple[int, ...] = ()
    source_passages_total: int = 0
    source_passages_aligned: int = 0
    math_spans_total: int = 0
    math_spans_evaluated: int = 0
    capitalization_opportunities_total: int = 0
    capitalization_opportunities_evaluated: int = 0

    def actual_ranges(self, start: int, end: int) -> tuple[tuple[int, int, int], ...]:
        """Map a document-stream range back to physical page-local ranges."""
        if not self.actual_pages:
            return ()
        left, right = max(0, int(start)), max(0, int(end))
        if right == left:
            for index, (base, cells) in enumerate(zip(self.actual_page_offsets, self.actual_pages)):
                if base <= left <= base + len(cells):
                    return ((index + 1, min(left - base, len(cells)), min(left - base, len(cells))),)
            return ()
        ranges = []
        for index, (base, cells) in enumerate(zip(self.actual_page_offsets, self.actual_pages)):
            local_left = max(left, base)
            local_right = min(right, base + len(cells))
            if local_left < local_right:
                ranges.append((index + 1, local_left - base, local_right - base))
        return tuple(ranges)

    @property
    def cell_accuracy(self) -> float:
        return self.matching_cells / self.total_expected_cells if self.total_expected_cells else 1.0

    @property
    def true_translation_differences(self) -> int:
        return sum(
            difference.category
            not in {
                "LAYOUT_ONLY", "SPACING_ONLY", "ENCODING_ONLY",
                "MANUAL_REVIEW", "REVIEW_REQUIRED",
                "EXCLUDED_OUT_OF_SCOPE",
            }
            for difference in self.differences
        )


def _actual_page_lines(page_text: str) -> tuple[tuple[int, ...], ...]:
    # U+2800 is also used by the PDF provenance reader for rendered
    # whitespace while the visible cells may still be NABCC/ASCII.  Only a
    # nonblank Unicode Braille cell selects the Unicode path; a blank-only
    # mixed stream remains safely handled by the ASCII/NABCC path below.
    if any(0x2801 <= ord(char) <= 0x28FF for char in page_text):
        lines = [line.strip() for line in page_text.replace("\r", "").split("\n") if line.strip()]
        return tuple(unicode_to_cells(line) for line in lines)
    lines = [
        line.strip()
        for line in page_text.replace("\u2800", " ").replace("\r", "").split("\n")
        if line.strip()
    ]
    if not lines:
        return ()
    return tuple(ascii_to_cells(line, "duxbury") for line in lines)


def _actual_page_cells(page_text: str) -> tuple[int, ...]:
    lines = _actual_page_lines(page_text)
    return tuple(cell for index, line in enumerate(lines) for cell in ((*line, 0) if index + 1 < len(lines) else line))


def _strip_duxbury_typeforms(cells: tuple[int, ...]) -> tuple[int, ...]:
    """Remove Duxbury layout-control pairs from uncontracted alignment only."""
    markers = {(24, 2), (24, 54), (24, 4)}
    kept: list[int] = []
    index = 0
    while index < len(cells):
        if index + 1 < len(cells) and (cells[index], cells[index + 1]) in markers:
            index += 2
            continue
        kept.append(cells[index])
        index += 1
    return tuple(kept)


def _align_case3_physical_pages(
    expected: tuple[int, ...],
    actual_pages: tuple[tuple[int, ...], ...],
    actual_offsets: tuple[int, ...],
) -> tuple[CellOpcode, ...] | None:
    """Align numeric cells in page-sized regions without a document-wide diff."""
    page_count = len(actual_pages)
    if page_count < 2 or len(actual_offsets) != page_count:
        return None
    actual_total = sum(map(len, actual_pages)) + page_count - 1
    if actual_total <= 0 or len(expected) < page_count * 2 - 1:
        return None

    blank_positions = tuple(index for index, cell in enumerate(expected) if cell == 0)
    regions: list[tuple[int, ...]] = []
    expected_offsets: list[int] = []
    cursor = actual_prefix = 0
    for page_index, page in enumerate(actual_pages[:-1]):
        actual_prefix += len(page) + 1
        target = round(len(expected) * actual_prefix / actual_total) - 1
        remaining_pages = page_count - page_index - 1
        low = cursor + 1
        high = len(expected) - 2 * remaining_pages
        candidates = [index for index in blank_positions if low <= index <= high]
        if not candidates:
            return None
        # ponytail: score only nearby page-edge windows; widen this 32-cell
        # search only if a real layout drift defeats the local content anchors.
        context = 32
        nearby = [index for index in candidates if abs(index - target) <= context]
        if nearby:
            def edit_cost(left: tuple[int, ...], right: tuple[int, ...]) -> int:
                return sum(
                    max(op.expected_end - op.expected_start, op.actual_end - op.actual_start)
                    for op in _align_bounded_block(left, right)
                    if op.tag != "equal"
                )

            def boundary_cost(index: int) -> tuple[int, int, int]:
                left_expected = expected[max(cursor, index - context):index]
                right_expected = expected[index + 1:index + 1 + context]
                left_actual = actual_pages[page_index][-context:]
                right_actual = actual_pages[page_index + 1][:context]
                cost = edit_cost(left_expected, left_actual) + edit_cost(right_expected, right_actual)
                return cost, abs(index - target), index

            boundary = min(nearby, key=boundary_cost)
        else:
            boundary = min(candidates, key=lambda index: (abs(index - target), index))
        expected_offsets.append(cursor)
        regions.append(expected[cursor:boundary])
        cursor = boundary + 1
    expected_offsets.append(cursor)
    regions.append(expected[cursor:])

    # ponytail: proportional physical-page anchors keep repeated numeric cells
    # out of the quadratic whole-document matcher; content anchors are needed
    # only if real layouts drift far enough to defeat page-local alignment.
    result: list[CellOpcode] = []
    for page_index, (region, actual) in enumerate(zip(regions, actual_pages)):
        expected_base = expected_offsets[page_index]
        actual_base = actual_offsets[page_index]
        result.extend(
            CellOpcode(
                op.tag,
                expected_base + op.expected_start,
                expected_base + op.expected_end,
                actual_base + op.actual_start,
                actual_base + op.actual_end,
            )
            for op in _align_bounded_block(region, actual)
        )
        if page_index + 1 < page_count:
            result.append(CellOpcode(
                "equal",
                expected_offsets[page_index + 1] - 1,
                expected_offsets[page_index + 1],
                actual_offsets[page_index + 1] - 1,
                actual_offsets[page_index + 1],
            ))
    return tuple(result)


def _block_for_offset(page: ExpectedPage, offset: int) -> Any | None:
    cursor = 0
    for block in page.blocks:
        if not block.braille:
            continue
        end = cursor + len(block.braille)
        if cursor <= offset < end:
            return block
        cursor = end + 1  # page.flatten() inserts one blank between blocks
    return None


def _classify(opcode: CellOpcode, expected: tuple[int, ...], actual: tuple[int, ...], page: ExpectedPage) -> tuple[str, str]:
    expected_slice = expected[opcode.expected_start:opcode.expected_end]
    actual_slice = actual[opcode.actual_start:opcode.actual_end]
    if all(cell == 0 for cell in expected_slice + actual_slice):
        return "LAYOUT_ONLY", "Only blank layout cells differ."
    if tuple(cell for cell in expected_slice if cell) == tuple(cell for cell in actual_slice if cell):
        return "SPACING_ONLY", "Only blank-cell spacing differs after canonicalization."
    block = _block_for_offset(page, opcode.expected_start)
    if block is not None and block.rule_status == "REVIEW":
        return "MANUAL_REVIEW", "The expected source block is uncertain under the rule engine."
    if block is not None and block.rule_status == "EXCLUDED_OUT_OF_SCOPE":
        return "EXCLUDED_OUT_OF_SCOPE", "The source construct is outside the text validator scope."
    if block is not None and any(r.rule_id == "NEMETH_SIMPLE_LINEAR_001" and r.status == "PASS" for r in block.rule_results):
        # Ownership comes from generated math-record intervals, not from the
        # corrupted cell resembling a switch indicator or from block type.
        block_start = 0
        for candidate in page.blocks:
            if candidate is block:
                break
            if candidate.braille:
                block_start += len(candidate.braille) + 1
        cursor = 0
        for record in block.math_records:
            start = block.braille.find(record.braille, cursor)
            if start < 0:
                break
            end = start + len(record.braille)
            cursor = end
            if block_start + start <= opcode.expected_start < opcode.expected_end <= block_start + end:
                return "NEMETH_ERROR", "Actual cells differ inside a fully recognized simple-math payload (NEMETH_SIMPLE_LINEAR_001)."
    # A prose insertion consisting of a numeric sign plus cells at an
    # alignment boundary is not enough evidence for a definite UEB error.  It
    # may be line/page furniture or source-layout material, so preserve it as
    # review.  This is a generic alignment guard, not a document exception.
    # A supported Case 3 numeric block has an explicit UEB 6.1.1 ownership
    # result, so an inserted numeric indicator is a confirmable numeric error,
    # not the generic prose-boundary review condition below.
    if (
        opcode.tag == "insert"
        and not expected_slice
        and block is not None
        and not block.math_records
        and not any(
            result.rule_id == "UEB_CASE3_NUMERIC" and result.status == "PASS"
            for result in block.rule_results
        )
        and 60 in actual_slice  # Nemeth/UEB numeric indicator, dots 3456
    ):
        return "REVIEW_REQUIRED", "Numeric-sign insertion at a prose alignment boundary requires source/layout review."
    start_cells = tuple(ord(char) - 0x2800 for char in "⠸⠩")
    end_cells = tuple(ord(char) - 0x2800 for char in "⠸⠱")
    switch_cells = set(start_cells + end_cells)
    if (
        start_cells in _windows(expected_slice)
        or end_cells in _windows(expected_slice)
        or start_cells in _windows(actual_slice)
        or end_cells in _windows(actual_slice)
        or (block is not None and block.math_records and switch_cells.intersection(expected_slice + actual_slice))
    ):
        return "SWITCHING_ERROR", "A verified UEB/Nemeth boundary sequence differs."
    if block is not None and block.math_records:
        return "NEMETH_ERROR", "The differing cells belong to a block containing explicit math."
    return "UEB_ERROR", "The differing cells belong to contracted literary text."


def _windows(values: tuple[int, ...], width: int = 2):
    return (values[index:index + width] for index in range(max(0, len(values) - width + 1)))


class BrailleValidator:
    """Generate verified expected Braille and compare canonical cell streams."""

    def validate(
        self,
        master_document: Any,
        actual_braille: str | Path,
        profile: str = "contracted_ueb_bana_nemeth",
    ) -> ValidationReport:
        expected_document = generate_expected_braille(master_document, profile)
        is_path = isinstance(actual_braille, Path)
        if isinstance(actual_braille, str) and len(actual_braille) < 4096:
            try:
                is_path = Path(actual_braille).is_file()
            except OSError:
                is_path = False
        if is_path:
            actual_text = read_braille_input(str(actual_braille))
        else:
            actual_text = str(actual_braille)
        actual_page_texts = actual_text.split("\f")
        differences: list[CellDifference] = []
        actual_page_cells: list[tuple[int, ...]] = []
        page_alignments: list[tuple[CellOpcode, ...]] = []
        comparison_views: list[ComparisonView] = []
        matching = 0
        total = 0
        actual_page_lines = tuple(_actual_page_lines(text) for text in actual_page_texts)
        actual_page_cells = [_actual_page_cells(text) for text in actual_page_texts]
        actual_offsets = []
        physical_breaks = set()
        actual_stream_list = []
        for index, cells in enumerate(actual_page_cells):
            actual_offsets.append(len(actual_stream_list))
            actual_stream_list.extend(cells)
            if index + 1 < len(actual_page_cells):
                physical_breaks.add(len(actual_stream_list))
                actual_stream_list.append(0)  # physical page break behaves like a line break
        actual_stream = tuple(actual_stream_list)

        source_offsets = []
        source_stream_list = []
        all_blocks = []
        for index, page in enumerate(expected_document.pages):
            source_offsets.append(len(source_stream_list))
            page_cells = unicode_to_cells(page.flatten())
            source_stream_list.extend(page_cells)
            all_blocks.extend(page.blocks)
            if index + 1 < len(expected_document.pages):
                source_stream_list.append(0)
        expected_cells = tuple(source_stream_list)
        total = len(expected_cells)
        stream_page = ExpectedPage(1, tuple(all_blocks))
        view = comparison_view(stream_page, actual_stream, physical_breaks)
        comparison_views.append(view)
        selected_profile = get_profile(profile)
        has_multiple_source_blocks = any(
            sum(bool(block.braille) for block in page.blocks) > 1
            for page in expected_document.pages
        )
        use_monotonic_regions = (
            selected_profile.case2_scope
            or selected_profile.case3_scope
            or selected_profile.case4_scope
            or (
                (selected_profile.phase1_scope or selected_profile.case1_scope)
                and has_multiple_source_blocks
            )
        )
        alignment_actual_pages = tuple(actual_page_cells)
        alignment_actual_lines = actual_page_lines
        alignment_actual_offsets = tuple(actual_offsets)
        if use_monotonic_regions:
            alignment_actual_pages = tuple(
                _strip_duxbury_typeforms(page)
                for page in actual_page_cells
            )
            alignment_actual_lines = tuple(
                tuple(_strip_duxbury_typeforms(line) for line in page)
                for page in actual_page_lines
            )
            alignment_actual_offsets = []
            cursor = 0
            for page_index, page in enumerate(alignment_actual_pages):
                alignment_actual_offsets.append(cursor)
                cursor += len(page)
                if page_index + 1 < len(alignment_actual_pages):
                    cursor += 1
            normalized_raw_indices = []
            typeform_pairs = {(24, 2), (24, 54), (24, 4)}
            for page_index, raw_page in enumerate(actual_page_cells):
                dropped = {
                    marker
                    for marker in range(len(raw_page) - 1)
                    if (raw_page[marker], raw_page[marker + 1]) in typeform_pairs
                    for marker in (marker, marker + 1)
                }
                raw_base = actual_offsets[page_index]
                normalized_raw_indices.extend(
                    raw_base + raw_index
                    for raw_index in range(len(raw_page))
                    if raw_index not in dropped
                )
                if page_index + 1 < len(actual_page_cells):
                    normalized_raw_indices.append(raw_base + len(raw_page))
            view = ComparisonView(
                tuple(
                    cell
                    for page_index, page in enumerate(alignment_actual_pages)
                    for cell in (
                        (*page, 0)
                        if page_index + 1 < len(alignment_actual_pages)
                        else page
                    )
                ),
                tuple(normalized_raw_indices),
                len(actual_stream),
                view.normalized_spans,
                view.skipped_spans,
                view.evaluated_spans,
                view.source_span_evaluated,
                view.joined_page_breaks,
            )
        if selected_profile.case3_scope or selected_profile.case4_scope:
            bounded = _align_case3_physical_pages(
                expected_cells,
                alignment_actual_pages,
                tuple(alignment_actual_offsets),
            )
        elif use_monotonic_regions:
            bounded = align_monotonic_page_regions(
                tuple(unicode_to_cells(page.flatten()) for page in expected_document.pages),
                alignment_actual_pages,
                tuple(source_offsets),
                tuple(alignment_actual_offsets),
                expected_blocks=tuple(
                    tuple(unicode_to_cells(block.braille) for block in page.blocks if block.braille)
                    for page in expected_document.pages
                ),
                actual_line_pages=alignment_actual_lines,
                edit_block_alignment=selected_profile.case2_scope,
            )
        else:
            bounded = None
        opcodes = bounded or align_with_operator_anchors(expected_document, expected_cells, view)
        projected_opcodes = tuple(projected for opcode in opcodes for projected in view.project(opcode))
        matching = sum(op.expected_end - op.expected_start for op in opcodes if op.tag == "equal")
        equal_positions = {i for op in projected_opcodes if op.tag == "equal" for i in range(op.expected_start, op.expected_end)}

        math_intervals = []
        record_ordinal = 0
        for page_index, page in enumerate(expected_document.pages):
            block_cursor = source_offsets[page_index]
            for block in page.blocks:
                if not block.braille:
                    continue
                within = 0
                for record in block.math_records:
                    start = block.braille.find(record.braille, within)
                    end = start + len(record.braille)
                    within = end
                    tokenized = (record_ordinal < len(view.source_span_evaluated)
                                 and view.source_span_evaluated[record_ordinal])
                    exact = start >= 0 and all(i in equal_positions for i in range(block_cursor + start, block_cursor + end))
                    math_intervals.append((block_cursor + start, block_cursor + end, tokenized or exact))
                    record_ordinal += 1
                block_cursor += len(block.braille) + 1

        def source_location(offset):
            for page_index in range(len(source_offsets) - 1, -1, -1):
                base = source_offsets[page_index]
                if offset >= base:
                    return expected_document.pages[page_index], base, offset - base
            return expected_document.pages[0], 0, offset

        def actual_page_for(offset):
            for page_index in range(len(actual_offsets) - 1, -1, -1):
                if offset >= actual_offsets[page_index]:
                    return page_index + 1
            return 1

        for opcode in opcodes:
            if opcode.tag == "equal":
                continue
            category, explanation = _classify(opcode, expected_cells, view.cells, stream_page)
            if any(not resolved and opcode.expected_end > start and opcode.expected_start < end
                   for start, end, resolved in math_intervals):
                category = "REVIEW_REQUIRED"
                explanation = "Supported source math span could not be aligned uniquely; left unverified."
            projected = next(view.project(opcode))
            page, page_base, local_start = source_location(opcode.expected_start)
            local_end = max(local_start, opcode.expected_end - page_base)
            block = _block_for_offset(page, local_start)
            differences.append(CellDifference(
                page=page.number,
                expected=expected_cells[opcode.expected_start:opcode.expected_end],
                actual=actual_stream[projected.actual_start:projected.actual_end],
                kind={"replace":"SUBSTITUTION","delete":"DELETION","insert":"INSERTION"}[opcode.tag],
                category=category, explanation=explanation,
                confidence="manual_review" if category == "MANUAL_REVIEW" else "high",
                expected_start=local_start, expected_end=local_end,
                actual_start=projected.actual_start, actual_end=projected.actual_end,
                block_id=block.source_block if block is not None else None,
                actual_page=actual_page_for(projected.actual_start),
            ))

        # Per-source-page alignments retain page-local expected offsets while
        # actual offsets remain document-global. Existing one-page callers are unchanged.
        for page_index, page in enumerate(expected_document.pages):
            base = source_offsets[page_index]
            page_end = base + len(unicode_to_cells(page.flatten()))
            clipped = []
            for op in projected_opcodes:
                left, right = max(op.expected_start, base), min(op.expected_end, page_end)
                insertion = op.tag == "insert" and base <= op.expected_start <= page_end
                if left >= right and not insertion:
                    continue
                if op.tag == "equal":
                    aleft = op.actual_start + left - op.expected_start
                    aright = aleft + right - left
                else:
                    aleft, aright = op.actual_start, op.actual_end
                clipped.append(CellOpcode(op.tag, left-base, right-base, aleft, aright))
            page_alignments.append(tuple(clipped))

        passages_total = passages_aligned = math_total = math_aligned = caps_total = caps_aligned = 0
        for page_index, page in enumerate(expected_document.pages):
            cursor = source_offsets[page_index]
            for block in page.blocks:
                if not block.braille:
                    continue
                passages_total += 1
                passages_aligned += int(all(i in equal_positions for i in range(cursor, cursor + len(block.braille))))
                record_cursor = 0
                for record in block.math_records:
                    start = block.braille.find(record.braille, record_cursor)
                    end = start + len(record.braille)
                    record_cursor = end
                    math_total += 1
                for site in block.capital_sites:
                    if not site.uppercase:
                        continue
                    start = cursor + site.expected_start
                    caps_total += 1
                    # The following letter/contraction is the existing
                    # capitalization rule's required equal-cell anchor. The
                    # prefix itself may be the error under evaluation.
                    caps_aligned += int(start + 1 in equal_positions)
                cursor += len(block.braille) + 1
        math_aligned = sum(resolved for _start, _end, resolved in math_intervals)
        return ValidationReport(
            expected_document=expected_document,
            differences=tuple(differences),
            total_expected_cells=total,
            matching_cells=matching,
            pages=len(expected_document.pages),
            actual_pages=tuple(actual_page_cells),
            page_alignments=tuple(page_alignments),
            comparison_views=tuple(comparison_views),
            actual_stream=actual_stream,
            actual_page_offsets=tuple(actual_offsets),
            source_page_offsets=tuple(source_offsets),
            source_passages_total=passages_total,
            source_passages_aligned=passages_aligned,
            math_spans_total=math_total,
            math_spans_evaluated=math_aligned,
            capitalization_opportunities_total=caps_total,
            capitalization_opportunities_evaluated=caps_aligned,
        )
