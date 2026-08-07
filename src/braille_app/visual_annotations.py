"""Presentation helpers for the PDF visual-results view.

This module intentionally consumes validator output; it does not participate in
translation, diffing, provenance resolution, or fixture/red detection.
"""

from dataclasses import dataclass, field
from pathlib import Path
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
    localization: str = "exact"
    marker: Optional[VisualBox] = None
    marker_style: str = "none"
    group_id: Optional[str] = None
    parent_diff_id: Optional[str] = None
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
            and 0 <= gap <= max(3.0, typical_width * 1.5)
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


def _small_marker(issue: dict, cells: list[dict]) -> Optional[VisualBox]:
    """Return a small anchor marker without representing a broad range."""
    anchor = next((provenance_cell_to_box(cell) for cell in cells), None)
    if anchor is not None:
        width = max(3.0, min(anchor.x1 - anchor.x0, 8.0))
        return VisualBox(anchor.page, anchor.x0, anchor.top, anchor.x0 + width, anchor.bottom)
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
    width = max(3.0, min(max(x1 - x0, 3.0), 8.0))
    return VisualBox(page, x0, top, x0 + width, bottom)


def visual_issues_from_cell_issues(cell_issues: Iterable[dict]) -> list[VisualIssue]:
    """Build visual records while keeping broad structural ranges unboxed."""
    visual = []
    for issue_id, issue in enumerate(cell_issues or [], 1):
        kind = issue.get("kind", "cell_issue")
        cells = list(issue.get("provenance_cells") or [])
        boxes = group_provenance_boxes(cells)
        is_group = kind == "structural_group"
        is_structural = kind in ("structural_review", "structural_group")
        # Small structural records can be shown as dashed exact/partial cells.
        # Broad records use only a small marker so the UI never implies a false
        # exact range for an unresolved parent mismatch.
        if is_group or (is_structural and (len(cells) > 8 or len(boxes) > 3)):
            # Broad structural provenance is deliberately side-panel only.
            # The first cell is not a trustworthy error location.
            marker = None
            boxes = []
            localization = "structural"
            marker_style = "none"
        elif is_structural:
            marker = None
            localization = "partial"
            marker_style = "none"
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
                localization=localization,
                marker=marker,
                marker_style=marker_style,
                group_id=issue.get("group_id"),
                parent_diff_id=issue.get("parent_diff_id"),
                child_issue_ids=list(issue.get("child_issue_ids") or []),
                child_count=int(issue.get("child_count", 0) or 0),
            )
        )
    return visual


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


def _pdf_overlay_stream(page_height: float, issue_records: Iterable[VisualIssue]) -> bytes:
    """Create a tiny content stream containing blue outline overlays."""
    commands = ["q", "0.12 0.48 1.0 RG", "1.5 w"]
    for issue in issue_records:
        for box in issue.boxes:
            y = page_height - box.bottom
            height = box.bottom - box.top
            width = box.x1 - box.x0
            if issue.localization == "partial":
                commands.append("[3 2] 0 d")
            else:
                commands.append("[] 0 d")
            commands.append(f"{box.x0:.3f} {y:.3f} {width:.3f} {height:.3f} re S")
        if issue.marker is not None:
            box = issue.marker
            x = box.x0
            y = page_height - box.bottom
            commands.append("[] 0 d")
            if issue.marker_style == "caret":
                center = x + max(1.5, (box.x1 - box.x0) / 2.0)
                commands.append(f"{center:.3f} {y:.3f} m {center:.3f} {y + (box.bottom - box.top):.3f} l S")
            else:
                commands.append(f"{x:.3f} {y:.3f} 5 5 re S")
    commands.append("Q")
    return ("\n".join(commands) + "\n").encode("ascii")


def export_annotated_pdf(input_path: str, output_path: str,
                         visual_issues: Iterable[VisualIssue]) -> str:
    """Write a new PDF with blue vector overlays, leaving the input untouched."""
    reader = PdfReader(input_path)
    writer = PdfWriter()
    records_by_page: dict[int, list[VisualIssue]] = {}
    for issue in visual_issues:
        for page in {box.page for box in issue.boxes} | ({issue.marker.page} if issue.marker else set()):
            records_by_page.setdefault(page, []).append(issue)

    for page_number, page in enumerate(reader.pages, 1):
        records = records_by_page.get(page_number, [])
        if records:
            page_height = float(page.mediabox.height)
            page_width = float(page.mediabox.width)
            background = DecodedStreamObject()
            background.set_data(
                f"q\n1 1 1 rg\n0 0 {page_width:.3f} {page_height:.3f} re f\nQ\n".encode("ascii")
            )
            background_ref = writer._add_object(background)
            overlay = DecodedStreamObject()
            overlay.set_data(_pdf_overlay_stream(page_height, records))
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
