"""Authoritative standards identifiers used by production rule results.

The application keeps the standards filenames and printed-page references
explicit so a rule decision never depends on an undocumented assumption.
"""

UEB_2024 = "Rules-of-Unified-English-Braille-2024.pdf"
NEMETH_2022 = "Nemeth_2022.pdf"
NEMETH_ERRATA_2025 = "Errata Nemeth Code 2022 Approved 10-2025.pdf"


def source_path(filename: str) -> str:
    return f"rules/{filename}"
