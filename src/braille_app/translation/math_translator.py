"""Explicit math-span normalization and Nemeth translation."""

from __future__ import annotations

from dataclasses import dataclass
import re

from .braille_cells import ascii_to_cells, cells_to_unicode
from .liblouis_translator import LiblouisTranslator
from .simple_math import expected as simple_expected


PRIVATE_MATH_TOKENS: dict[str, str] = {
    "...": "\uf10e",
    "=": "\uf100",
    "+": "\uf101",
    "<": "\uf102",
    ">": "\uf103",
    "{": "\uf104",
    "}": "\uf105",
    ":": "\uf106",
    "²": "\uf107",
    "³": "\uf108",
    "∈": "\uf109",
    "⇒": "\uf10a",
    "≤": "\uf10b",
    "≥": "\uf10c",
    "≠": "\uf10d",
}

# Nemeth Rule 14 level indicators.  These private tokens keep script cells
# separate from Liblouis' literary digit handling, so a simple script does
# not acquire an unrelated numeric indicator.  The table entries are the
# canonical Nemeth cells shown by the Rule 14 examples.
_SCRIPT_TOKENS: dict[str, str] = {
    "₀": "\uf120",
    "₁": "\uf121",
    "₂": "\uf122",
    "₃": "\uf123",
    "₄": "\uf124",
    "₅": "\uf125",
    "₆": "\uf126",
    "₇": "\uf127",
    "₈": "\uf128",
    "₉": "\uf129",
    "⁰": "\uf130",
    "¹": "\uf131",
    "⁴": "\uf134",
    "⁵": "\uf135",
    "⁶": "\uf136",
    "⁷": "\uf137",
    "⁸": "\uf138",
    "⁹": "\uf139",
    "ⁿ": "\uf13a",
    "⁻¹": "\uf13b",
}

_UNARY_NEGATIVE = re.compile(r"(^|[([{=+−*/,:])−(?=\d)")


@dataclass(frozen=True)
class NormalizationChange:
    source: str
    replacement: str
    reason: str


@dataclass(frozen=True)
class NormalizedMath:
    original: str
    table_input: str
    changes: tuple[NormalizationChange, ...]


@dataclass(frozen=True)
class MathTranslation:
    source: str
    normalized_source: str
    braille: str
    ascii_braille: str
    changes: tuple[NormalizationChange, ...]
    status: str = "PASS"


def normalize_math_source(text: str) -> NormalizedMath:
    current = text
    changes: list[NormalizationChange] = []

    if "–" in current:
        current = current.replace("–", "−")
        changes.append(
            NormalizationChange(
                "–", "−", "math subtraction/negative normalization"
            )
        )


    # Apply the combined negative superscript before the single-character
    # replacements.  These are the simple, first-order cases covered by
    # Nemeth 2022 Rule 14.4; more complex script hierarchies remain visible
    # to the rule engine for review.
    for source, replacement in sorted(_SCRIPT_TOKENS.items(), key=lambda item: -len(item[0])):
        count = current.count(source)
        if count:
            current = current.replace(source, replacement)
            changes.extend(
                NormalizationChange(source, replacement, "Nemeth Rule 14 simple script")
                for _ in range(count)
            )

    unary_matches = list(_UNARY_NEGATIVE.finditer(current))
    if unary_matches:
        current = _UNARY_NEGATIVE.sub(lambda match: f"{match.group(1)}− ", current)
        changes.extend(
            NormalizationChange(
                "−<digit>", "− <digit>", "Nemeth unary-negative spacing"
            )
            for _ in unary_matches
        )

    for source, replacement in PRIVATE_MATH_TOKENS.items():
        count = current.count(source)
        if count:
            current = current.replace(source, replacement)
            changes.extend(
                NormalizationChange(source, replacement, "Nemeth structural/operator token")
                for _ in range(count)
            )

    return NormalizedMath(text, current, tuple(changes))


def _suppress_collection_number_signs(ascii_braille: str) -> tuple[str, tuple[int, ...]]:
    """Match the validated Duxbury-compatible collection numeric mode."""

    chars = list(ascii_braille)
    drop: list[int] = []
    depth = 0
    condition_depths: set[int] = set()
    index = 0
    while index < len(chars):
        if index + 1 < len(chars) and chars[index:index + 2] == [".", "("]:
            depth += 1
            index += 2
            continue
        if depth and index + 1 < len(chars) and chars[index:index + 2] == ['"', "1"]:
            condition_depths.add(depth)
        if depth and chars[index] == "#" and depth not in condition_depths:
            drop.append(index)
        if depth and index + 1 < len(chars) and chars[index:index + 2] == [".", ")"]:
            condition_depths.discard(depth)
            depth -= 1
            index += 2
            continue
        index += 1
    if not drop:
        return ascii_braille, ()
    drop_set = set(drop)
    return "".join(char for pos, char in enumerate(chars) if pos not in drop_set), tuple(drop)


def _add_superscript_terminators(ascii_braille: str) -> tuple[str, int]:
    return re.subn(r"(\^[23])\.\)", r'\1".)', ascii_braille)


def translate_math(text: str, translator: LiblouisTranslator | None = None) -> MathTranslation:
    """Translate one explicitly identified math span.

    The function is deliberately explicit: it never tries to detect math in
    ordinary prose.  Unknown Liblouis escapes remain visible to the rule
    engine as a REVIEW result.
    """

    simple = simple_expected(text)
    if simple is not None:
        from .braille_cells import LIBLOUIS_MATH_DOTS, char_mask
        reverse = {char_mask(c, "liblouis_math"): c for c in LIBLOUIS_MATH_DOTS}
        return MathTranslation(
            source=text, normalized_source=text, braille=simple,
            ascii_braille="".join(reverse[ord(c) - 0x2800] for c in simple),
            changes=(NormalizationChange(text, simple,
                "Nemeth 3.3.1/3.4.1, 6.4.7, 20.1 and 21.13 closed linear grammar"),),
        )
    translator = translator or LiblouisTranslator()
    normalized = normalize_math_source(text)
    ascii_braille = translator.translate_math_ascii(normalized.table_input)
    ascii_braille, dropped = _suppress_collection_number_signs(ascii_braille)
    ascii_braille, superscript_terminators = _add_superscript_terminators(ascii_braille)
    changes = list(normalized.changes)
    changes.extend(
        NormalizationChange("#", "", "Duxbury-compatible collection numeric-mode calibration")
        for _ in dropped
    )
    changes.extend(
        NormalizationChange("", '"', "Duxbury-compatible superscript terminator calibration")
        for _ in range(superscript_terminators)
    )
    status = "REVIEW" if re.search(r"\\X[0-9A-F]{4,}", ascii_braille, re.I) else "PASS"
    return MathTranslation(
        source=text,
        normalized_source=normalized.table_input,
        braille=cells_to_unicode(ascii_to_cells(ascii_braille, "liblouis_math")),
        ascii_braille=ascii_braille,
        changes=tuple(changes),
        status=status,
    )
