import copy

from braille_app.presentation_grouping import (
    build_presentation_items,
    presentation_metrics,
)
from braille_app.report_generator import ReportGenerator
from braille_app.visual_annotations import visual_issues_from_cell_issues


def _child(page, actual_start, actual_end, expected_start, expected_end, context="segment"):
    return {
        "kind": "structural_review",
        "page": page,
        "actual_start_idx": actual_start,
        "actual_end_idx": actual_end,
        "expected_start_idx": expected_start,
        "expected_end_idx": expected_end,
        "expected_cells": ["⠁"],
        "actual_cells": ["⠃"],
        "provenance_cells": [],
        "context": context,
        "confidence": "needs_review",
    }


def _parent(actual_start, actual_end, expected_start, expected_end):
    return {
        "type": "structural_mismatch",
        "actual_start_idx": actual_start,
        "actual_end_idx": actual_end,
        "expected_start_idx": expected_start,
        "expected_end_idx": expected_end,
    }


def test_same_parent_and_page_becomes_one_recoverable_group():
    children = [_child(1, 0, 1, 0, 1), _child(1, 1, 2, 1, 2)]
    items = build_presentation_items(children, [_parent(0, 2, 0, 2)])

    assert len(items) == 1
    assert items[0]["kind"] == "structural_group"
    assert items[0]["parent_diff_id"] == "diff-1"
    assert items[0]["child_issue_ids"] == [1, 2]
    assert items[0]["child_count"] == 2
    assert [child["source_issue_id"] for child in items[0]["child_records"]] == [1, 2]


def test_different_parents_never_merge():
    children = [_child(1, 0, 1, 0, 1), _child(1, 2, 3, 2, 3)]
    items = build_presentation_items(children, [_parent(0, 1, 0, 1), _parent(2, 3, 2, 3)])

    assert [item["parent_diff_id"] for item in items] == ["diff-1", "diff-2"]


def test_same_parent_on_different_pages_gets_separate_groups():
    children = [_child(1, 0, 1, 0, 1), _child(2, 1, 2, 1, 2)]
    items = build_presentation_items(children, [_parent(0, 2, 0, 2)])

    assert len(items) == 2
    assert [item["page"] for item in items] == [1, 2]
    assert all(item["parent_diff_id"] == "diff-1" for item in items)


def test_normal_and_partial_items_remain_individual():
    exact = {
        "kind": "replacement",
        "expected_cells": ["⠁"],
        "actual_cells": ["⠃"],
        "provenance_cells": [{"page": 1}],
    }
    partial = {
        "kind": "deletion",
        "expected_cells": ["⠁"],
        "actual_cells": [],
        "provenance_cells": [],
    }
    items = build_presentation_items([exact, partial], [])

    assert [item["kind"] for item in items] == ["replacement", "deletion"]
    assert [item["presentation_kind"] for item in items] == ["exact", "partial"]
    assert presentation_metrics(items) == {
        "normal_displayed": 2,
        "exact_displayed": 1,
        "partial_displayed": 1,
        "structural_groups": 0,
        "total_displayed": 2,
        "structural_children": 0,
    }


def test_grouping_does_not_mutate_detector_records():
    children = [_child(1, 0, 1, 0, 1), _child(1, 1, 2, 1, 2)]
    before = copy.deepcopy(children)
    build_presentation_items(children, [_parent(0, 2, 0, 2)])
    assert children == before


def test_structural_group_has_no_fake_visual_boxes_but_children_are_available():
    group = build_presentation_items(
        [_child(1, 0, 1, 0, 1), _child(1, 1, 2, 1, 2)],
        [_parent(0, 2, 0, 2)],
    )
    visual = visual_issues_from_cell_issues(group)[0]

    assert visual.type == "structural_group"
    assert visual.localization == "structural"
    assert visual.boxes == []
    assert visual.marker is None
    assert visual.child_issue_ids == [1, 2]
    assert visual.child_count == 2


def test_report_uses_one_structural_group_and_keeps_debug_child_ids():
    items = build_presentation_items(
        [_child(6, 0, 1, 0, 1), _child(6, 1, 2, 1, 2)],
        [_parent(0, 2, 0, 2)],
    )
    html = ReportGenerator().generate_report(
        {"pages": []},
        {"diffs": [], "cell_issues": [], "presentation_items": items},
        {},
        1,
    )

    assert html.count("structural mismatch - needs review") == 1
    assert "Internal structural segments: 2" in html
    assert "Child IDs: 1, 2" in html
