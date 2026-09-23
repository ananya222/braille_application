"""Evidence for page-local differences caused by cross-page displacement.

This is a reporting guard, not a second standards validator. Unmatched cells
inside a displaced range remain unverified, never certified as correct.
"""

from bisect import bisect_left
from difflib import SequenceMatcher

from braille_app.translation.braille_cells import unicode_to_cells


def displaced_difference_indices(report):
    """Return differences whose global anchors belong to other actual pages.

    Blank cells are ignored only for locating content. No filenames, fixture
    counts, error categories or mathematical symbols drive suppression.
    A difference with any anchor on its nominal page stays in normal handling.
    Entirely unmatched (including genuinely missing) content also stays there.
    """
    # Document-stream alignment already permits content to cross arbitrary
    # physical pages. The old page-displacement suppression is only valid for
    # legacy page-local reports.
    if report.actual_stream:
        return {}
    if len(report.actual_pages) < 2:
        return {}
    expected = []
    offsets = {}
    bases = {}
    for page in report.expected_document.pages:
        bases[page.number] = len(expected)
        positions = []
        for offset, cell in enumerate(unicode_to_cells(page.flatten())):
            if cell:
                positions.append(offset)
                expected.append(cell)
        offsets[page.number] = positions
    actual = []
    actual_page_numbers = []
    for number, cells in enumerate(report.actual_pages, 1):
        for cell in cells:
            if cell:
                actual.append(cell)
                actual_page_numbers.append(number)
    anchors = {}
    for match in SequenceMatcher(None, expected, actual, autojunk=False).get_matching_blocks():
        for offset in range(match.size):
            anchors[match.a + offset] = actual_page_numbers[match.b + offset]
    displaced = {}
    for index, difference in enumerate(report.differences):
        positions = offsets.get(difference.page, ())
        start = bisect_left(positions, difference.expected_start)
        end = bisect_left(positions, difference.expected_end)
        base = bases.get(difference.page, 0)
        mapped = [anchors[i] for i in range(base + start, base + end) if i in anchors]
        nominal_page = difference.actual_page or difference.page
        if mapped and nominal_page not in mapped:
            displaced[index] = {
                "actual_pages": tuple(sorted(set(mapped))),
                "matched_nonblank_cells": len(mapped),
                "unverified_nonblank_cells": end - start - len(mapped),
            }
    return displaced
