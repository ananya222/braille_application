"""Presentation-only grouping for localized validator results.

The detector and provenance resolver deliberately keep every structural child
record.  This module creates a compact view for UI/report consumers without
mutating those records or changing ownership semantics.
"""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional


@dataclass
class GroupedStructuralIssue:
    """One page-scoped presentation group backed by structural child records."""

    group_id: str
    parent_diff_id: str
    page: Optional[int]
    child_issue_ids: list[int] = field(default_factory=list)
    child_records: list[dict[str, Any]] = field(default_factory=list)
    expected_summary: str = ""
    actual_summary: str = ""
    source_summary: str = ""
    localization_confidence: str = "structural"
    warning_text: str = "Exact error location could not be fully localized."

    @property
    def child_count(self) -> int:
        return len(self.child_issue_ids)

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": "structural_group",
            "presentation_kind": "structural",
            "display_kind": "structural",
            "group_id": self.group_id,
            "parent_diff_id": self.parent_diff_id,
            "page": self.page,
            "child_issue_ids": list(self.child_issue_ids),
            "child_count": self.child_count,
            "child_records": deepcopy(self.child_records),
            "expected_summary": self.expected_summary,
            "actual_summary": self.actual_summary,
            "source_summary": self.source_summary,
            "confidence": "needs_review",
            "localization": self.localization_confidence,
            "message": self.warning_text,
            # Structural groups intentionally carry no drawable provenance.
            "provenance_cells": [],
        }


def _range_contains(parent: dict, child: dict) -> bool:
    """Return whether a raw parent range contains one structural child."""
    parent_actual_start = parent.get("actual_start_idx")
    parent_actual_end = parent.get("actual_end_idx")
    child_actual_start = child.get("actual_start_idx")
    child_actual_end = child.get("actual_end_idx")
    if None in (parent_actual_start, parent_actual_end,
                child_actual_start, child_actual_end):
        return False
    if not (parent_actual_start <= child_actual_start <= child_actual_end <= parent_actual_end):
        return False

    parent_expected_start = parent.get("expected_start_idx")
    parent_expected_end = parent.get("expected_end_idx")
    child_expected_start = child.get("expected_start_idx")
    child_expected_end = child.get("expected_end_idx")
    if None in (parent_expected_start, parent_expected_end,
                child_expected_start, child_expected_end):
        return True
    return parent_expected_start <= child_expected_start <= child_expected_end <= parent_expected_end


def _parent_diff_id(issue: dict, diff_records: list[dict], child_issue_id: int) -> str:
    """Map a child to the unique raw diff whose ranges contain it."""
    candidates = [
        index for index, diff in enumerate(diff_records, 1)
        if _range_contains(diff, issue)
    ]
    if len(candidates) == 1:
        return f"diff-{candidates[0]}"

    # This fallback is intentionally non-merging: if provenance cannot prove
    # parentage, each child gets its own presentation group.
    return f"unmapped-child-{child_issue_id}"


def _summary(values: Iterable[str], limit: int = 3) -> str:
    unique = []
    for value in values:
        if value and value not in unique:
            unique.append(value)
        if len(unique) >= limit:
            break
    if len(unique) < limit:
        return " | ".join(unique)
    return " | ".join(unique) + " | …"


def build_presentation_items(
    cell_issues: Iterable[dict] | None,
    diff_records: Iterable[dict] | None = None,
) -> list[dict[str, Any]]:
    """Build compact presentation items without changing detector records.

    Normal and partial localized issues remain one item each.  Structural
    children are grouped by a provenance-derived raw diff ID and page.  The
    original child issue IDs and deep-copied records remain available under
    every group for detailed/debug views.
    """
    issues = list(cell_issues or [])
    diffs = list(diff_records or [])
    items: list[tuple[int, dict[str, Any]]] = []
    groups: "OrderedDict[tuple[str, Optional[int]], tuple[int, GroupedStructuralIssue]]" = OrderedDict()

    for source_issue_id, original in enumerate(issues, 1):
        kind = original.get("kind", "cell_issue")
        # These are proof/audit records, not user-facing issues.
        if kind == "resolved_equal":
            continue

        issue = deepcopy(original)
        if kind != "structural_review":
            issue["source_issue_id"] = source_issue_id
            issue["presentation_kind"] = "exact" if issue.get("provenance_cells") else "partial"
            issue["display_kind"] = "normal"
            items.append((source_issue_id, issue))
            continue

        parent_id = _parent_diff_id(original, diffs, source_issue_id)
        page = original.get("page")
        try:
            page = int(page) if page is not None else None
        except (TypeError, ValueError):
            page = None
        key = (parent_id, page)
        if key not in groups:
            group = GroupedStructuralIssue(
                group_id=f"{parent_id}-page-{page if page is not None else 'na'}",
                parent_diff_id=parent_id,
                page=page,
            )
            groups[key] = (source_issue_id, group)
            items.append((source_issue_id, group.as_dict()))
        first_order, group = groups[key]
        group.child_issue_ids.append(source_issue_id)
        child = deepcopy(original)
        child["source_issue_id"] = source_issue_id
        group.child_records.append(child)
        group.expected_summary = _summary(
            [group.expected_summary, "".join(original.get("expected_cells", []))]
        )
        group.actual_summary = _summary(
            [group.actual_summary, "".join(original.get("actual_cells", []))]
        )
        group.source_summary = _summary(
            [group.source_summary, original.get("context", "")]
        )
        # Refresh the dict already placed in the ordered item list.
        for index, (order, item) in enumerate(items):
            if order == first_order and item.get("group_id") == group.group_id:
                items[index] = (order, group.as_dict())
                break

    # A stable presentation order follows the first internal child position.
    items.sort(key=lambda pair: pair[0])
    output = []
    for display_id, (_, item) in enumerate(items, 1):
        item = deepcopy(item)
        item["display_id"] = display_id
        item["issue_id"] = display_id
        output.append(item)
    return output


def presentation_metrics(items: Iterable[dict] | None) -> dict[str, int]:
    """Return user-facing counts while keeping exact/partial distinct."""
    values = list(items or [])
    structural = [item for item in values if item.get("kind") == "structural_group"]
    exact = [item for item in values if item.get("presentation_kind") == "exact"]
    partial = [item for item in values if item.get("presentation_kind") == "partial"]
    normal = [item for item in values if item.get("kind") != "structural_group"]
    return {
        "normal_displayed": len(normal),
        "exact_displayed": len(exact),
        "partial_displayed": len(partial),
        "structural_groups": len(structural),
        "total_displayed": len(values),
        "structural_children": sum(item.get("child_count", 0) for item in structural),
    }


def presentation_page_metrics(
    cell_issues: Iterable[dict] | None,
    items: Iterable[dict] | None,
    pages: Iterable[int] = range(1, 10),
) -> dict[int, dict[str, int]]:
    """Return internal and presentation counts side by side for each page."""
    internal = list(cell_issues or [])
    presented = list(items or [])
    result = {}
    for page in pages:
        child_count = sum(
            1 for issue in internal
            if issue.get("kind") == "structural_review" and issue.get("page") == page
        )
        page_items = [item for item in presented if item.get("page") == page]
        result[int(page)] = {
            "normal": sum(item.get("kind") != "structural_group" for item in page_items),
            "partial": sum(item.get("presentation_kind") == "partial" for item in page_items),
            "structural_children": child_count,
            "structural_groups": sum(item.get("kind") == "structural_group" for item in page_items),
            "total_displayed": len(page_items),
        }
    return result
