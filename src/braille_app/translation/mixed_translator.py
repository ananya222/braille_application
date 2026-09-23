"""Translate explicitly marked UEB/Nemeth mixed source text."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .liblouis_translator import LiblouisTranslator
from .math_translator import MathTranslation, translate_math
from .profiles import CONTRACTED_UEB_BANA_NEMETH, TranslationProfile
from .prose_boundary_context import contextualize_prose


START_MARKER = "[[*ts*]]"
END_MARKER = "[[*te*]]"


def serialize_nemeth_passage(cells: str, profile: TranslationProfile) -> str:
    """BANA_4_2_INNER_SPACE: serialize an already-selected Nemeth passage.

    Authority: Nemeth 4.2, amended October 2025 errata p.4 (PDF p.8).
    Scope/trigger: explicit math span, canonical unformatted cells, entering
    Nemeth from UEB and returning to UEB at the end of this span.
    Preconditions: nonempty payload and the UEB/Nemeth switch pair.
    Exclusions: other profiles, empty payload, and physically laid-out text
    (placement/runovers require 4.8). This does not select code ownership,
    change interior spacing, or implement the 4.6.8.c single-word switch.
    Dependency: source routing has already selected a Nemeth span. Errata
    4.2 supersedes the base text; no precedence over internal math rules.
    Effect ends at the terminator. Existing boundary blanks are preserved.
    """
    if (profile.switch_start, profile.switch_end) != ("⠸⠩", "⠸⠱") or not cells or any(c in cells for c in "\r\n\f"):
        return profile.switch_start + cells + profile.switch_end
    left = "" if cells.startswith("⠀") else "⠀"
    right = "" if cells.endswith("⠀") else "⠀"
    return profile.switch_start + left + cells + right + profile.switch_end


class MathMarkerError(ValueError):
    """Raised when explicit source math markers are malformed."""


@dataclass(frozen=True)
class TranslatedSpan:
    kind: Literal["text", "math"]
    source: str
    braille: str
    math: MathTranslation | None = None


@dataclass(frozen=True)
class MixedTranslation:
    source: str
    spans: tuple[TranslatedSpan, ...]
    braille: str
    has_math: bool
    balanced: bool = True


def translate_marked_text(
    source: str,
    translator: LiblouisTranslator | None = None,
    profile: TranslationProfile = CONTRACTED_UEB_BANA_NEMETH,
) -> MixedTranslation:
    """Translate text containing explicit ``[[*ts*]]``/``[[*te*]]`` spans."""

    translator = translator or LiblouisTranslator(profile)
    spans: list[TranslatedSpan] = []
    output: list[str] = []
    cursor = 0
    in_math = False
    saw_math = False

    while cursor < len(source):
        marker = START_MARKER if not in_math else END_MARKER
        marker_pos = source.find(marker, cursor)
        other_marker = END_MARKER if not in_math else START_MARKER
        other_pos = source.find(other_marker, cursor)
        if other_pos >= 0 and (marker_pos < 0 or other_pos < marker_pos):
            raise MathMarkerError(f"Unexpected {other_marker} at source offset {other_pos}")

        if marker_pos < 0:
            tail = source[cursor:]
            if in_math:
                raise MathMarkerError("Unclosed math marker at end of source")
            if tail:
                braille = translator.translate_prose(tail)
                spans.append(TranslatedSpan("text", tail, braille))
                output.append(braille)
            cursor = len(source)
            break

        before = source[cursor:marker_pos]
        if before:
            if in_math:
                raise MathMarkerError("Nested math marker is not supported")
            braille = translator.translate_prose(before)
            spans.append(TranslatedSpan("text", before, braille))
            output.append(braille)

        cursor = marker_pos + len(marker)
        if not in_math:
            end = source.find(END_MARKER, cursor)
            if end < 0:
                raise MathMarkerError("Unclosed math marker")
            math_source = source[cursor:end]
            result = translate_math(math_source, translator)
            spans.append(TranslatedSpan("math", math_source, result.braille, result))
            output.append(serialize_nemeth_passage(result.braille, profile))
            saw_math = True
            cursor = end + len(END_MARKER)
        else:
            raise MathMarkerError("Unexpected nested math state")

    if source == "":
        spans.append(TranslatedSpan("text", "", ""))
    if saw_math:
        spans = contextualize_prose(spans, translator, profile)
        output = [
            span.braille if span.kind == "text" else serialize_nemeth_passage(span.braille, profile)
            for span in spans
        ]
    return MixedTranslation(source, tuple(spans), "".join(output), saw_math)
