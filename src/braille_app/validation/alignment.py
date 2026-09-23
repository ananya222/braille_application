"""Chunked canonical-cell alignment."""

from __future__ import annotations

from dataclasses import dataclass
import difflib


@dataclass(frozen=True)
class CellOpcode:
    tag: str
    expected_start: int
    expected_end: int
    actual_start: int
    actual_end: int


def _align_blank_only_difference(
    expected: tuple[int, ...], actual: tuple[int, ...]
) -> tuple[CellOpcode, ...] | None:
    """Align streams whose only differences are blank cells in linear time."""

    if tuple(cell for cell in expected if cell != 0) != tuple(
        cell for cell in actual if cell != 0
    ):
        return None
    opcodes: list[CellOpcode] = []

    def append(tag: str, expected_start: int, expected_end: int, actual_start: int, actual_end: int) -> None:
        if expected_start == expected_end and actual_start == actual_end:
            return
        if opcodes and opcodes[-1].tag == tag and opcodes[-1].expected_end == expected_start and opcodes[-1].actual_end == actual_start:
            previous = opcodes[-1]
            opcodes[-1] = CellOpcode(tag, previous.expected_start, expected_end, previous.actual_start, actual_end)
        else:
            opcodes.append(CellOpcode(tag, expected_start, expected_end, actual_start, actual_end))

    expected_pos = actual_pos = 0
    while expected_pos < len(expected) or actual_pos < len(actual):
        if (
            expected_pos < len(expected)
            and actual_pos < len(actual)
            and expected[expected_pos] == actual[actual_pos]
        ):
            append("equal", expected_pos, expected_pos + 1, actual_pos, actual_pos + 1)
            expected_pos += 1
            actual_pos += 1
        elif expected_pos < len(expected) and expected[expected_pos] == 0:
            append("delete", expected_pos, expected_pos + 1, actual_pos, actual_pos)
            expected_pos += 1
        elif actual_pos < len(actual) and actual[actual_pos] == 0:
            append("insert", expected_pos, expected_pos, actual_pos, actual_pos + 1)
            actual_pos += 1
        else:
            return None
    return tuple(opcodes)


def align_cells(expected: tuple[int, ...], actual: tuple[int, ...]) -> tuple[CellOpcode, ...]:
    if expected == actual:
        return (CellOpcode("equal", 0, len(expected), 0, len(actual)),)
    blank_only = _align_blank_only_difference(expected, actual)
    if blank_only is not None:
        return blank_only
    matcher = difflib.SequenceMatcher(None, expected, actual, autojunk=False)
    return tuple(CellOpcode(*opcode) for opcode in matcher.get_opcodes())


def _align_equal_width_cells(
    expected: tuple[int, ...], actual: tuple[int, ...]
) -> tuple[CellOpcode, ...] | None:
    """Align equal-width bounded blocks without repeated-token jumps."""

    if len(expected) != len(actual):
        return None
    opcodes: list[CellOpcode] = []
    start = 0
    while start < len(expected):
        tag = "equal" if expected[start] == actual[start] else "replace"
        end = start + 1
        while end < len(expected) and (
            ("equal" if expected[end] == actual[end] else "replace") == tag
        ):
            end += 1
        opcodes.append(CellOpcode(tag, start, end, start, end))
        start = end
    return tuple(opcodes)


def _align_bounded_block(
    expected: tuple[int, ...], actual: tuple[int, ...]
) -> tuple[CellOpcode, ...]:
    """Minimum-edit alignment for a source block, without distant repeat jumps."""
    rows, cols = len(expected), len(actual)
    distance = [[0] * (cols + 1) for _ in range(rows + 1)]
    for i in range(rows, -1, -1):
        for j in range(cols, -1, -1):
            if i == rows:
                distance[i][j] = cols - j
            elif j == cols:
                distance[i][j] = rows - i
            elif expected[i] == actual[j]:
                distance[i][j] = distance[i + 1][j + 1]
            else:
                candidates = [
                    distance[i + 1][j + 1], distance[i + 1][j], distance[i][j + 1]
                ]
                if (i + 1 < rows and j + 1 < cols
                    and expected[i] == actual[j + 1]
                    and expected[i + 1] == actual[j]):
                    candidates.append(distance[i + 2][j + 2])
                distance[i][j] = 1 + min(candidates)

    def separates_neighbor_edit(i: int, j: int) -> bool:
        expected_end, actual_end = i, j
        while expected_end < rows and expected[expected_end] == expected[i]:
            expected_end += 1
        while actual_end < cols and actual[actual_end] == expected[i]:
            actual_end += 1
        return (expected_end - i == actual_end - j + 1
                and expected_end < rows and actual_end < cols
                and expected[expected_end] != actual[actual_end]
                and distance[expected_end][actual_end] == 1 + distance[expected_end + 1][actual_end + 1])

    opcodes: list[CellOpcode] = []
    i = j = 0
    while i < rows or j < cols:
        if (i < rows and j + 1 < cols
            and expected[i] == actual[j] == actual[j + 1]
            and distance[i][j] == 1 + distance[i][j + 1]):
            # Identical neighbors make insertion position unobservable from
            # cells alone; consistently assign the first equivalent slot.
            tag, next_i, next_j = "insert", i, j + 1
        elif (i + 1 < rows and j < cols
              and expected[i] == expected[i + 1] == actual[j]
              and distance[i][j] == 1 + distance[i + 1][j]
              and separates_neighbor_edit(i, j)):
            # Keep the surviving run between a deletion and a neighboring
            # substitution. Otherwise preserve already matching prefix cells.
            tag, next_i, next_j = "delete", i + 1, j
        elif i < rows and j < cols and expected[i] == actual[j] and distance[i][j] == distance[i + 1][j + 1]:
            tag, next_i, next_j = "equal", i + 1, j + 1
        elif (i + 1 < rows and j + 1 < cols
              and expected[i] == actual[j + 1]
              and expected[i + 1] == actual[j]
              and distance[i][j] == 1 + distance[i + 2][j + 2]):
            tag, next_i, next_j = "replace", i + 2, j + 2
        elif i < rows and j < cols and distance[i][j] == 1 + distance[i + 1][j + 1]:
            tag, next_i, next_j = "replace", i + 1, j + 1
        elif i < rows and distance[i][j] == 1 + distance[i + 1][j]:
            tag, next_i, next_j = "delete", i + 1, j
        else:
            tag, next_i, next_j = "insert", i, j + 1
        if opcodes and opcodes[-1].tag == tag:
            previous = opcodes[-1]
            opcodes[-1] = CellOpcode(tag, previous.expected_start, next_i, previous.actual_start, next_j)
        else:
            opcodes.append(CellOpcode(tag, i, next_i, j, next_j))
        i, j = next_i, next_j
    return tuple(opcodes)


def align_monotonic_page_regions(
    expected_pages: tuple[tuple[int, ...], ...],
    actual_pages: tuple[tuple[int, ...], ...],
    expected_offsets: tuple[int, ...],
    actual_offsets: tuple[int, ...],
    max_group: int = 3,
    expected_blocks: tuple[tuple[tuple[int, ...], ...], ...] | None = None,
    actual_line_pages: tuple[tuple[tuple[int, ...], ...], ...] | None = None,
    edit_block_alignment: bool = False,
) -> tuple[CellOpcode, ...] | None:
    """Align uncontracted pages in monotonic, repagination-tolerant regions.

    Page boundaries are soft anchors: a transition may consume one to three
    expected and actual pages.  The selected transitions are monotonic, and
    the existing cell aligner is then run only inside each selected region.
    ``None`` preserves the historical global fallback if the coarse problem
    cannot be solved.
    """

    while actual_pages and not actual_pages[-1]:
        actual_pages = actual_pages[:-1]
    if not expected_pages or not actual_pages:
        return None

    expected_count = len(expected_pages)
    actual_count = len(actual_pages)
    max_group = max(1, int(max_group))
    expected_totals = [0]
    actual_totals = [0]
    for page in expected_pages:
        expected_totals.append(expected_totals[-1] + len(page) + 1)
    for page in actual_pages:
        actual_totals.append(actual_totals[-1] + len(page) + 1)
    expected_total = max(1, expected_totals[-1] - 1)
    actual_total = max(1, actual_totals[-1] - 1)

    def segment(pages, start: int, end: int) -> tuple[int, ...]:
        cells: list[int] = []
        for index in range(start, end):
            if cells:
                cells.append(0)
            cells.extend(pages[index])
        return tuple(cells)

    def score(left: tuple[int, ...], right: tuple[int, ...]) -> float:
        if not left and not right:
            return 0.0
        matcher = difflib.SequenceMatcher(None, left, right, autojunk=False)
        matching = sum(block.size for block in matcher.get_matching_blocks())
        edits = len(left) + len(right) - 2 * matching
        return matching - 0.5 * edits

    def align_blocks(
        expected_group: tuple[tuple[int, ...], ...],
        actual_group: tuple[tuple[int, ...], ...],
        expected_base: int,
        actual_base: int,
    ) -> tuple[CellOpcode, ...] | None:
        """Keep fine alignment monotonic across repeated source blocks."""
        if not expected_group:
            return ()
        choices: dict[tuple[int, int], tuple[float, tuple[int, ...]]] = {}

        def solve(block_index: int, actual_cursor: int) -> tuple[float, tuple[int, ...]] | None:
            key = (block_index, actual_cursor)
            if key in choices:
                return choices[key]
            if block_index == len(expected_group):
                return 0.0, ()
            remaining = len(expected_group) - block_index - 1
            if len(actual_group) - actual_cursor <= remaining:
                return None
            best: tuple[float, tuple[int, ...]] | None = None
            max_lines = len(actual_group) - actual_cursor - remaining
            block = expected_group[block_index]
            for width in range(1, max_lines + 1):
                actual_end = actual_cursor + width
                actual_segment = segment(actual_group, actual_cursor, actual_end)
                tail = solve(block_index + 1, actual_end)
                if tail is None:
                    continue
                if edit_block_alignment:
                    fine = _align_bounded_block(block, actual_segment)
                    edit_cost = sum(
                        max(op.expected_end - op.expected_start, op.actual_end - op.actual_start)
                        for op in fine if op.tag != "equal"
                    )
                    block_score = len(block) - edit_cost
                else:
                    block_score = score(block, actual_segment)
                candidate_score = (
                    block_score
                    - 0.05 * width
                    - 0.75 * abs(len(block) - len(actual_segment))
                )
                ranked = (candidate_score + tail[0], tuple((width, *tail[1])))
                if best is None or ranked[0] > best[0] or (
                    ranked[0] == best[0] and ranked[1] < best[1]
                ):
                    best = ranked
            if best is not None:
                choices[key] = best
            return best

        selected = solve(0, 0)
        if selected is None:
            return None
        result: list[CellOpcode] = []
        actual_cursor = 0
        expected_cursor = 0
        for block_index, (block, actual_width) in enumerate(zip(expected_group, selected[1])):
            actual_segment = segment(actual_group, actual_cursor, actual_cursor + actual_width)
            chosen = (_align_bounded_block(block, actual_segment) if edit_block_alignment
                      else _align_equal_width_cells(block, actual_segment) or align_cells(block, actual_segment))
            result.extend(
                CellOpcode(
                    opcode.tag,
                    expected_base + expected_cursor + opcode.expected_start,
                    expected_base + expected_cursor + opcode.expected_end,
                    actual_base + sum(len(line) + 1 for line in actual_group[:actual_cursor]) + opcode.actual_start,
                    actual_base + sum(len(line) + 1 for line in actual_group[:actual_cursor]) + opcode.actual_end,
                )
                for opcode in chosen
            )
            expected_cursor += len(block)
            actual_cursor += actual_width
            if block_index + 1 < len(expected_group):
                result.append(
                    CellOpcode(
                        "equal",
                        expected_base + expected_cursor,
                        expected_base + expected_cursor + 1,
                        actual_base + sum(len(line) + 1 for line in actual_group[:actual_cursor]) - 1,
                        actual_base + sum(len(line) + 1 for line in actual_group[:actual_cursor]),
                    )
                )
                expected_cursor += 1
        return tuple(result)

    transitions: list[tuple[int, int, int, int]] | None = None
    if expected_count == actual_count and all(
        abs(len(expected) - len(actual)) <= max(20, len(expected) // 4)
        for expected, actual in zip(expected_pages, actual_pages)
    ):
        # Equal page counts plus close cumulative page sizes are evidence for
        # a stable page correspondence, not an assumption about pagination.
        transitions = [(index, index, 1, 1) for index in range(expected_count)]

    if transitions is None:
        # The DP stores only the best monotonic path to each page boundary.
        paths: dict[tuple[int, int], tuple[float, tuple[int, int, int, int] | None]] = {
            (0, 0): (0.0, None)
        }
        previous: dict[tuple[int, int], tuple[int, int, int, int]] = {}
        for expected_start in range(expected_count + 1):
            for actual_start in range(actual_count + 1):
                current = paths.get((expected_start, actual_start))
                if current is None:
                    continue
                current_score = current[0]
                for expected_width in range(1, max_group + 1):
                    expected_end = expected_start + expected_width
                    if expected_end > expected_count:
                        break
                    for actual_width in range(1, max_group + 1):
                        actual_end = actual_start + actual_width
                        if actual_end > actual_count:
                            break
                        # Keep the coarse path near cumulative document position.
                        # This is a soft band, not a page-number mapping; a
                        # genuinely repaginated region can still consume 1–3
                        # pages on either side.
                        expected_fraction = expected_totals[expected_end] / expected_total
                        actual_fraction = actual_totals[actual_end] / actual_total
                        if abs(expected_fraction - actual_fraction) > 0.12:
                            continue
                        left = segment(expected_pages, expected_start, expected_end)
                        right = segment(actual_pages, actual_start, actual_end)
                        candidate_score = (
                            current_score
                            + score(left, right)
                            - 0.2 * abs(expected_width - actual_width)
                            - 4.0 * (expected_width + actual_width - 2)
                        )
                        key = (expected_end, actual_end)
                        old = paths.get(key)
                        tie_break = -abs(expected_width - actual_width)
                        old_tie_break = (
                            -abs(old[1][2] - old[1][3]) if old and old[1] else -999
                        )
                        if old is None or (candidate_score, tie_break) > (old[0], old_tie_break):
                            paths[key] = (candidate_score, (expected_start, actual_start, expected_width, actual_width))
                            previous[key] = (expected_start, actual_start, expected_width, actual_width)

        terminal = (expected_count, actual_count)
        if terminal not in previous:
            return None
        transitions = []
        cursor = terminal
        while cursor != (0, 0):
            transition = previous.get(cursor)
            if transition is None:
                return None
            transitions.append(transition)
            cursor = (transition[0], transition[1])
        transitions.reverse()

    result: list[CellOpcode] = []
    for index, (expected_start, actual_start, expected_width, actual_width) in enumerate(transitions):
        expected_base = expected_offsets[expected_start]
        actual_base = actual_offsets[actual_start]
        block_result = None
        if expected_blocks is not None and actual_line_pages is not None:
            expected_group = tuple(
                block
                for page in expected_blocks[expected_start:expected_start + expected_width]
                for block in page
            )
            actual_group = tuple(
                line
                for page in actual_line_pages[actual_start:actual_start + actual_width]
                for line in page
            )
            block_result = align_blocks(expected_group, actual_group, expected_base, actual_base)
        if block_result is None:
            expected_segment = segment(expected_pages, expected_start, expected_start + expected_width)
            actual_segment = segment(actual_pages, actual_start, actual_start + actual_width)
            block_result = tuple(
                CellOpcode(
                    opcode.tag,
                    expected_base + opcode.expected_start,
                    expected_base + opcode.expected_end,
                    actual_base + opcode.actual_start,
                    actual_base + opcode.actual_end,
                )
                for opcode in align_cells(expected_segment, actual_segment)
            )
        result.extend(block_result)
        if index + 1 < len(transitions):
            next_expected_start = transitions[index + 1][0]
            next_actual_start = transitions[index + 1][1]
            expected_boundary = expected_offsets[next_expected_start] - 1
            actual_boundary = actual_offsets[next_actual_start] - 1
            if expected_boundary >= 0 and actual_boundary >= 0:
                result.append(CellOpcode("equal", expected_boundary, expected_boundary + 1, actual_boundary, actual_boundary + 1))
    return tuple(result)
