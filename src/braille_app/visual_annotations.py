"""Presentation helpers for the PDF visual-results view.

This module intentionally consumes validator output; it does not participate in
translation, diffing, provenance resolution, or fixture/red detection.
"""

from dataclasses import dataclass, field, replace
from statistics import median
from pathlib import Path
import re
from typing import Iterable, Optional

from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, DecodedStreamObject, NameObject


@dataclass(frozen=True)
class VisualBox:
    """A provenance box in PDF points, using the reader's top-origin y-axis."""

    page: int
    x0: float
    top: float
    x1: float
    bottom: float


@dataclass
class VisualIssue:
    """The presentation contract for one validator issue."""

    issue_id: int
    page: Optional[int]
    type: str
    expected: str
    actual: str
    context: str
    confidence: str
    boxes: list[VisualBox] = field(default_factory=list)
    exact_boxes: list[VisualBox] = field(default_factory=list)
    localization: str = "exact"
    marker: Optional[VisualBox] = None
    markers: list[VisualBox] = field(default_factory=list)
    marker_style: str = "none"
    group_id: Optional[str] = None
    parent_diff_id: Optional[str] = None
    structural_lineage_id: Optional[str] = None
    presentation_role: str = ""
    child_issue_ids: list[int] = field(default_factory=list)
    child_count: int = 0


def provenance_cell_to_box(cell: dict) -> Optional[VisualBox]:
    """Convert one serialized PdfCellProvenance to a drawable box."""
    required = ("page", "x0", "x1", "top", "bottom")
    if any(cell.get(key) is None for key in required):
        return None
    try:
        page = int(cell["page"])
        x0 = float(cell["x0"])
        x1 = float(cell["x1"])
        top = float(cell["top"])
        bottom = float(cell["bottom"])
    except (TypeError, ValueError):
        return None
    if page < 1 or x1 <= x0 or bottom <= top:
        return None
    return VisualBox(page=page, x0=x0, top=top, x1=x1, bottom=bottom)


def _same_line(left: VisualBox, right: VisualBox) -> bool:
    left_center = (left.top + left.bottom) / 2.0
    right_center = (right.top + right.bottom) / 2.0
    return abs(left_center - right_center) <= max(
        2.5, min(left.bottom - left.top, right.bottom - right.top) * 0.35
    )


def group_provenance_boxes(cells: Iterable[dict | VisualBox]) -> list[VisualBox]:
    """Group adjacent cells only when they share a line and are near each other."""
    boxes = []
    for cell in cells:
        box = cell if isinstance(cell, VisualBox) else provenance_cell_to_box(cell)
        if box is not None:
            boxes.append(box)
    boxes.sort(key=lambda box: (box.page, box.top, box.x0))
    if not boxes:
        return []

    groups: list[list[VisualBox]] = [[boxes[0]]]
    for box in boxes[1:]:
        current = groups[-1]
        previous = current[-1]
        widths = [item.x1 - item.x0 for item in current]
        typical_width = sum(widths) / len(widths)
        gap = box.x0 - previous.x1
        if (
            box.page == previous.page
            and _same_line(previous, box)
            and -1e-6 <= gap <= max(3.0, typical_width * 1.5)
        ):
            current.append(box)
        else:
            groups.append([box])

    return [
        VisualBox(
            page=group[0].page,
            x0=min(box.x0 for box in group),
            top=min(box.top for box in group),
            x1=max(box.x1 for box in group),
            bottom=max(box.bottom for box in group),
        )
        for group in groups
    ]


def _single_provenance_region(cells: Iterable[dict]) -> list[VisualBox]:
    """Return one line-bounded region for a structural review span."""
    boxes = [provenance_cell_to_box(cell) for cell in cells]
    boxes = [box for box in boxes if box is not None]
    if not boxes:
        return []
    return [
        VisualBox(
            page=boxes[0].page,
            x0=min(box.x0 for box in boxes),
            top=min(box.top for box in boxes),
            x1=max(box.x1 for box in boxes),
            bottom=max(box.bottom for box in boxes),
        )
    ]


def _marker_box(anchor: VisualBox) -> VisualBox:
    """Return a compact printed marker anchored to trusted provenance."""
    width = max(5.0, min(anchor.x1 - anchor.x0, 7.0))
    height = max(5.0, min(anchor.bottom - anchor.top, 7.0))
    return VisualBox(
        anchor.page,
        anchor.x0,
        anchor.top,
        anchor.x0 + width,
        anchor.top + height,
    )


def _small_marker(issue: dict, cells: list[dict]) -> Optional[VisualBox]:
    """Return one compact anchor marker without representing a broad range."""
    anchor = next((provenance_cell_to_box(cell) for cell in cells), None)
    if anchor is not None:
        return _marker_box(anchor)
    if issue.get("page") is None or any(issue.get(key) is None for key in ("x0", "x1", "top", "bottom")):
        return None
    try:
        page = int(issue["page"])
        x0 = float(issue["x0"])
        x1 = float(issue["x1"])
        top = float(issue["top"])
        bottom = float(issue["bottom"])
    except (TypeError, ValueError):
        return None
    return _marker_box(VisualBox(page, x0, top, x1, bottom))


def _review_marker_records(issue: dict) -> list[dict]:
    """Return the retained child records that can anchor a Review marker."""
    if issue.get("kind") == "structural_group":
        return list(issue.get("child_records") or [])
    return [issue]


def _review_marker_boxes(issue: dict) -> list[VisualBox]:
    """Create a few local markers from provenance without drawing child spans.

    Marker clustering is deliberately presentation-only.  It uses the already
    retained PDF provenance and groups nearby boxes on the same rendered line;
    it never changes the child records, their ownership, or their report data.
    """
    entries: list[tuple[VisualBox, int]] = []
    for record in _review_marker_records(issue):
        role = record.get("presentation_role", "")
        # Prefer an ordinary localized structural child when a local cluster
        # contains one, then a localized Review child, then any retained cell.
        priority = {
            "structural_child": 0,
            "structural_review_child": 1,
        }.get(role, 2)
        for cell in record.get("provenance_cells") or []:
            box = provenance_cell_to_box(cell)
            if box is not None:
                entries.append((box, priority))
    if not entries:
        return []

    markers: list[VisualBox] = []
    for line in _boxes_by_rendered_line([box for box, _ in entries]):
        line_entries = sorted(
            (entry for entry in entries if entry[0] in line),
            key=lambda entry: entry[0].x0,
        )
        if line_entries:
            # One marker per rendered line and presentation lineage is the
            # compact UX boundary.  It avoids implying that every retained
            # child span is independently wrong, while separate lines and
            # separate structural groups remain independently actionable.
            anchor, _ = min(line_entries, key=lambda entry: (entry[1], entry[0].x0))
            markers.append(_marker_box(anchor))
    return markers


_SOURCE_BLANK_ANCHOR = re.compile(r"^\s*_+[.!?]?\s*$")


def _is_structural_placeholder_region(issue: dict) -> bool:
    """Recognize only an already-owned contracted blank review span.

    This is presentation metadata, not a validator equivalence.  The source
    anchor and PDF provenance must already identify the span as the contracted
    placeholder diagnostic; the unchanged client exception therefore remains
    a dashed Needs Review region instead of becoming an exact error.
    """
    if issue.get("kind") != "structural_review":
        return False
    if issue.get("parent_diff_type") != "contracted_source_placeholder_profile_difference":
        return False
    source_anchor = issue.get("source_blank_anchor") or issue.get("context")
    if not _SOURCE_BLANK_ANCHOR.fullmatch(str(source_anchor or "")):
        return False
    values = [cell.get("unicode_cell", "") for cell in issue.get("provenance_cells") or []]
    return (
        len(values) >= 7
        and values.count("\u2011") >= 3
        and values.count("\u2828") >= 3
        and values[-1:] == ["\u2832"]
    )


def _placeholder_region_cells(issue: dict) -> list[list[dict]]:
    """Return child provenance for presentation-only structural region boxes."""
    if issue.get("kind") == "structural_review":
        return [list(issue.get("provenance_cells") or [])] if _is_structural_placeholder_region(issue) else []
    if issue.get("kind") != "structural_group":
        return []
    return [
        list(child.get("provenance_cells") or [])
        for child in issue.get("child_records") or []
        if _is_structural_placeholder_region(child)
    ]


def _structural_provenance_boxes(issue: dict) -> list[VisualBox]:
    """Return line-bounded boxes for already-owned structural provenance.

    Structural grouping is a presentation concern: the group itself has no
    single exact cell owner, but its child records still carry the actual PDF
    cells participating in the mismatch.  Preserve that ownership visually by
    grouping each child only across adjacent cells on the same PDF line.  This
    deliberately does not merge children or span unrelated lines/pages.
    """
    records = (
        issue.get("child_records") or []
        if issue.get("kind") == "structural_group"
        else [issue]
    )
    locality_aware = bool(
        issue.get("lineage_aware") or issue.get("compact_review_provenance")
    )
    locality_gap = _structural_locality_gap_limit(records)
    boxes = []
    for record in records:
        render_cells = record.get("provenance_cells") or []
        boxes.extend(
            _group_local_structural_child_boxes(render_cells, locality_gap)
            if locality_aware else group_provenance_boxes(render_cells)
        )

    unique = []
    seen = set()
    for box in boxes:
        key = (box.page, round(box.x0, 3), round(box.top, 3),
               round(box.x1, 3), round(box.bottom, 3))
        if key not in seen:
            seen.add(key)
            unique.append(box)
    if issue.get("lineage_aware"):
        # The parent identity is the ownership boundary, but it is not a
        # license to bridge otherwise unrelated child spans.  Flattening all
        # cells here fed the generic cell grouping a sequence that could jump
        # across one or more empty Braille cells.  Retain every child span,
        # then merge only touching/layout-adjacent child fragments.
        return _merge_same_line_structural_fragments(
            unique,
            gap_limit=locality_gap,
        )
    if issue.get("compact_review_provenance"):
        # The group identity is already issue-aware.  Merge only contiguous or
        # layout-adjacent fragments on the same PDF line.  This path used to
        # pass ``None`` and therefore bridge every child span on the line.
        # Separate lines, pages, and blank-cell-scale spans remain separate
        # Review regions.
        return _merge_same_line_structural_fragments(
            unique,
            gap_limit=locality_gap,
        )
    parent_types = {
        record.get("parent_diff_type")
        for record in records
        if record.get("parent_diff_type")
    }
    if parent_types == {"contracted_source_structure_review"}:
        return _merge_same_line_structural_fragments(unique)
    if (
            issue.get("kind") == "structural_group"
            and "structural_mismatch" in parent_types
            and any(
                record.get("allow_same_parent_fragment_merge")
                for record in records
            )
    ):
        return _merge_same_line_structural_fragments(unique)
    return unique


def _merge_same_line_structural_fragments(
        boxes: Iterable[VisualBox], gap_limit: float | None = 2.0) -> list[VisualBox]:
    """Collapse only continuous fragments owned by one structural parent.

    Contracted source-structure provenance is often emitted once per child
    while every child owns the same PDF row.  The cells in that row can have a
    tiny negative/positive gap from PDF layout padding, which otherwise
    creates one dashed rectangle per fragment.  Merge only boxes on the same
    PDF page and line when their horizontal gap is within the small padding
    limit.  Different lines, pages, and logical parents stay separate.
    """
    merged: list[VisualBox] = []
    for line in _boxes_by_rendered_line(boxes):
        for box in line:
            if not merged or merged[-1].page != box.page or not _same_line(merged[-1], box):
                merged.append(box)
                continue
            previous = merged[-1]
            horizontal_gap = max(0.0, box.x0 - previous.x1, previous.x0 - box.x1)
            if gap_limit is None or horizontal_gap <= gap_limit:
                merged[-1] = VisualBox(
                    page=previous.page,
                    x0=min(previous.x0, box.x0),
                    top=min(previous.top, box.top),
                    x1=max(previous.x1, box.x1),
                    bottom=max(previous.bottom, box.bottom),
                )
            else:
                merged.append(box)
    return merged


def _structural_locality_gap_limit(records: Iterable[dict]) -> float:
    """Return a small layout tolerance derived from the rendered cell width.

    A child box boundary can differ by a fraction of a point because PDF glyph
    geometry is rounded.  A blank Braille cell is roughly one rendered cell
    width, though, and must start a separate Review region.  A quarter-cell
    tolerance joins only the former.  The fallback preserves the historic
    compact-fragment tolerance for malformed provenance with no dimensions.
    """
    widths = []
    for record in records:
        for cell in record.get("provenance_cells") or []:
            box = provenance_cell_to_box(cell)
            if box is not None:
                widths.append(box.x1 - box.x0)
    if not widths:
        return 2.0
    return max(1.0, median(widths) * 0.25)


def _group_local_structural_child_boxes(
        cells: Iterable[dict | VisualBox], gap_limit: float) -> list[VisualBox]:
    """Group only contiguous cells inside one structural child provenance span."""
    boxes = []
    for cell in cells:
        box = cell if isinstance(cell, VisualBox) else provenance_cell_to_box(cell)
        if box is not None:
            boxes.append(box)
    groups: list[list[VisualBox]] = []
    for line in _boxes_by_rendered_line(boxes):
        for box in line:
            if not groups or groups[-1][0].page != box.page or not _same_line(groups[-1][0], box):
                groups.append([box])
                continue
            previous = groups[-1][-1]
            gap = max(0.0, box.x0 - previous.x1)
            if gap <= gap_limit:
                groups[-1].append(box)
            else:
                groups.append([box])
    return [
        VisualBox(
            page=group[0].page,
            x0=min(box.x0 for box in group),
            top=min(box.top for box in group),
            x1=max(box.x1 for box in group),
            bottom=max(box.bottom for box in group),
        )
        for group in groups
    ]


def _boxes_by_rendered_line(boxes: Iterable[VisualBox]) -> list[list[VisualBox]]:
    """Normalize small PDF y-coordinate jitter before horizontal clustering."""
    lines: list[list[VisualBox]] = []
    for box in sorted(boxes, key=lambda value: (value.page, (value.top + value.bottom) / 2.0)):
        if lines and box.page == lines[-1][0].page and _same_line(box, lines[-1][0]):
            lines[-1].append(box)
        else:
            lines.append([box])
    return [sorted(line, key=lambda box: box.x0) for line in lines]


def visual_issues_from_cell_issues(cell_issues: Iterable[dict]) -> list[VisualIssue]:
    """Build visual records while keeping unresolved ranges compact.

    A source-backed contracted placeholder child is the one intentionally
    narrow structural exception: it receives dashed provenance boxes so the
    production UI makes the Needs Review region visible without claiming
    exact cell correspondence.  Other uncertain structural groups receive
    small local markers; their complete child provenance remains in the input
    record for reports and detailed inspection.
    """
    visual = []
    for issue_id, issue in enumerate(cell_issues or [], 1):
        kind = issue.get("kind", "cell_issue")
        cells = list(issue.get("provenance_cells") or [])
        boxes = group_provenance_boxes(cells)
        exact_boxes: list[VisualBox] = []
        is_group = kind == "structural_group"
        is_structural = kind in ("structural_review", "structural_group")
        marker = None
        markers: list[VisualBox] = []
        marker_style = "none"
        placeholder_regions = _placeholder_region_cells(issue)
        is_diagnostic_review = issue.get("status") == "REVIEW" or kind == "review"
        if is_diagnostic_review:
            # Diagnostic REVIEW records use the same provenance grouping as
            # confirmed errors.  The diagnostic exporter applies the distinct
            # dashed amber stroke; the normal exporter remains unchanged.
            boxes = group_provenance_boxes(cells)
            localization = "review"
        elif placeholder_regions:
            boxes = [
                box
                for region_cells in placeholder_regions
                for box in _single_provenance_region(region_cells)
            ]
            marker = None
            localization = "partial"
            marker_style = "none"
        elif is_structural:
            # Contracted and mixed-math profiles explicitly request detailed
            # structural provenance.  Keep that established path unchanged.
            if is_group and issue.get("show_structural_provenance", False):
                boxes = _structural_provenance_boxes(issue)
                localization = "partial" if boxes else "structural"
            else:
                # Uncertain structural presentation is intentionally compact.
                # The marker anchor is derived from retained provenance only;
                # no client-red or fixture-specific location is consulted.
                boxes = []
                exact_boxes = [
                    box
                    for child in issue.get("child_records") or []
                    if child.get("presentation_role") == "structural_child"
                    for box in group_provenance_boxes(
                        child.get("provenance_cells") or []
                    )
                ]
                markers = _review_marker_boxes(issue)
                if not markers:
                    review_cells = [
                        cell
                        for child in issue.get("child_records") or []
                        for cell in child.get("provenance_cells") or []
                    ] if is_group else cells
                    fallback = _small_marker(issue, review_cells)
                    if fallback is not None:
                        markers = [fallback]
                marker = markers[0] if markers else None
                localization = "structural"
                marker_style = "review_marker" if markers else "none"
        else:
            # Without actual provenance cells there is no safe on-page point.
            # This covers deletions whose gap was not explicitly resolved.
            marker = None
            localization = "exact" if boxes else "partial"
            marker_style = "none"
        visual.append(
            VisualIssue(
                issue_id=issue_id,
                page=issue.get("page"),
                type=kind,
                expected=issue.get("expected", ""),
                actual=issue.get("actual", ""),
                context=issue.get("context", ""),
                confidence=issue.get("confidence", ""),
                boxes=boxes,
                exact_boxes=exact_boxes,
                localization=localization,
                marker=marker,
                markers=markers,
                marker_style=marker_style,
                group_id=issue.get("group_id"),
                parent_diff_id=issue.get("parent_diff_id"),
                structural_lineage_id=issue.get("structural_lineage_id"),
                presentation_role=issue.get("presentation_role", ""),
                child_issue_ids=list(issue.get("child_issue_ids") or []),
                child_count=int(issue.get("child_count", 0) or 0),
            )
        )
    return visual


def page_specific_visual_issues(
    visual_issues: Iterable[VisualIssue],
) -> list[VisualIssue]:
    """Split drawable annotations by their authoritative PDF page.

    A logical structural review may span a page boundary.  Keep the logical
    ``VisualIssue`` available to the sidebar, but give the canvas one copy per
    PDF page so it never draws a child bbox on the group's earlier page.
    Issues without drawable provenance retain their existing logical page for
    status/list compatibility.
    """
    routed = []
    for issue in visual_issues or []:
        markers = list(issue.markers or ([] if issue.marker is None else [issue.marker]))
        pages = (
            {box.page for box in issue.boxes}
            | {box.page for box in issue.exact_boxes}
            | {marker.page for marker in markers}
        )
        if not pages:
            routed.append(issue)
            continue
        for page in sorted(pages):
            boxes = [box for box in issue.boxes if box.page == page]
            exact_boxes = [box for box in issue.exact_boxes if box.page == page]
            page_markers = [marker for marker in markers if marker.page == page]
            routed.append(replace(
                issue,
                page=page,
                boxes=boxes,
                exact_boxes=exact_boxes,
                marker=page_markers[0] if page_markers else None,
                markers=page_markers,
            ))
    return routed


def pdf_box_to_screen(box: VisualBox, page_width: float, page_height: float,
                      render_width: float, render_height: float) -> tuple[float, float, float, float]:
    """Map top-origin PDF points to top-origin rendered-image pixels."""
    if page_width <= 0 or page_height <= 0:
        raise ValueError("page dimensions must be positive")
    scale_x = render_width / page_width
    scale_y = render_height / page_height
    return (
        box.x0 * scale_x,
        box.top * scale_y,
        box.x1 * scale_x,
        box.bottom * scale_y,
    )


def _pdf_overlay_stream(
    page_height: float,
    issue_records: Iterable[VisualIssue],
    diagnostic: bool = False,
) -> bytes:
    """Create a tiny content stream containing blue outline overlays."""
    commands = ["q"]
    if not diagnostic:
        commands.append("0.12 0.48 1.0 RG")
    commands.append("1.5 w")
    for issue in issue_records:
        is_review = diagnostic and issue.type == "review"
        if is_review:
            commands.append("1.0 0.55 0.0 RG")
        elif diagnostic:
            commands.append("0.12 0.48 1.0 RG")
        for box in issue.exact_boxes:
            y = page_height - box.bottom
            height = box.bottom - box.top
            width = box.x1 - box.x0
            commands.append("[] 0 d")
            commands.append(f"{box.x0:.3f} {y:.3f} {width:.3f} {height:.3f} re S")
        for box in issue.boxes:
            y = page_height - box.bottom
            height = box.bottom - box.top
            width = box.x1 - box.x0
            if is_review or issue.localization in ("partial", "structural"):
                commands.append("[3 2] 0 d")
            else:
                commands.append("[] 0 d")
            commands.append(f"{box.x0:.3f} {y:.3f} {width:.3f} {height:.3f} re S")
        markers = list(issue.markers or ([] if issue.marker is None else [issue.marker]))
        for box in markers:
            x = box.x0
            y = page_height - box.bottom
            if is_review or issue.localization in ("partial", "structural"):
                commands.append("[3 2] 0 d")
            else:
                commands.append("[] 0 d")
            if issue.marker_style == "caret":
                center = x + max(1.5, (box.x1 - box.x0) / 2.0)
                commands.append(f"{center:.3f} {y:.3f} m {center:.3f} {y + (box.bottom - box.top):.3f} l S")
            elif issue.marker_style == "review_marker":
                width = max(5.0, min(7.0, box.x1 - box.x0))
                height = max(5.0, min(7.0, box.bottom - box.top))
                commands.append(f"{x:.3f} {y:.3f} {width:.3f} {height:.3f} re S")
            else:
                commands.append(f"{x:.3f} {y:.3f} 5 5 re S")
    commands.append("Q")
    return ("\n".join(commands) + "\n").encode("ascii")


def export_annotated_pdf(
    input_path: str,
    output_path: str,
    visual_issues: Iterable[VisualIssue],
    diagnostic: bool = False,
) -> str:
    """Write a new PDF with blue vector overlays, leaving the input untouched."""
    reader = PdfReader(input_path)
    writer = PdfWriter()
    records_by_page: dict[int, list[VisualIssue]] = {}
    for issue in page_specific_visual_issues(visual_issues):
        markers = list(issue.markers or ([] if issue.marker is None else [issue.marker]))
        for page in (
            {box.page for box in issue.boxes}
            | {box.page for box in issue.exact_boxes}
            | {marker.page for marker in markers}
        ):
            records_by_page.setdefault(page, []).append(issue)

    for page_number, page in enumerate(reader.pages, 1):
        records = records_by_page.get(page_number, [])
        if records:
            page_height = float(page.mediabox.height)
            page_width = float(page.mediabox.width)
            background = DecodedStreamObject()
            background.set_data(
                # Isolate the original page's graphics state. Content-stream
                # array entries share a CTM: Duxbury leaves a scale/flip active,
                # while provenance boxes are already in physical PDF points.
                f"q\n1 1 1 rg\n0 0 {page_width:.3f} {page_height:.3f} re f\nQ\nq\n".encode("ascii")
            )
            background_ref = writer._add_object(background)
            overlay = DecodedStreamObject()
            overlay.set_data(
                b"Q\n" + _pdf_overlay_stream(page_height, records, diagnostic=diagnostic)
            )
            overlay_ref = writer._add_object(overlay)
            contents = page.get("/Contents")
            if contents is None:
                page[NameObject("/Contents")] = ArrayObject([background_ref, overlay_ref])
            elif isinstance(contents, ArrayObject):
                page[NameObject("/Contents")] = ArrayObject([background_ref, *contents, overlay_ref])
            else:
                page[NameObject("/Contents")] = ArrayObject([background_ref, contents, overlay_ref])
        writer.add_page(page)

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as stream:
        writer.write(stream)
    return str(destination)


def export_diagnostic_pdf(
    input_path: str,
    output_path: str,
    visual_issues: Iterable[VisualIssue],
) -> str:
    """Write the development diagnostic overlay without changing production output."""

    return export_annotated_pdf(
        input_path, output_path, visual_issues, diagnostic=True
    )
