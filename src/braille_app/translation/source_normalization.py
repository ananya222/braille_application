"""Explicit source boundary for the first uncontracted UEB slice."""

from __future__ import annotations

import re


class UnsupportedSourceError(ValueError):
    """The source contains a construct outside the phase-1 contract."""


_PHASE1_SOURCE = re.compile(r"[A-Za-z ]*")
_CASE1_SOURCE = re.compile(r"[a-z ]*")
_CASE2_SOURCE = re.compile(r"[A-Za-z ]*")
_CASE4_SOURCE = re.compile(r"[A-Za-z0-9 ,.!?:;–—-]*")
_CASE4_DASH_TAIL = re.compile(r"[,.!:;]*[A-Za-z0-9?]")
_CASE3_SOURCE = re.compile(r"[A-Za-z0-9 ,.\-–—]*")


def normalize_uncontracted_phase1(text: str) -> str:
    """Validate and preserve ASCII English letters and ordinary spaces."""

    value = str(text)
    if _PHASE1_SOURCE.fullmatch(value) is None:
        for offset, char in enumerate(value):
            if not ("A" <= char <= "Z" or "a" <= char <= "z" or char == " "):
                raise UnsupportedSourceError(
                    f"Unsupported phase-1 source character U+{ord(char):04X} "
                    f"at offset {offset}: {char!r}"
                )
        raise UnsupportedSourceError("Unsupported phase-1 source construct")
    return value


def normalize_uncontracted_case1(text: str) -> str:
    """Validate and preserve lowercase English letters and ASCII spaces only."""

    value = str(text)
    if _CASE1_SOURCE.fullmatch(value) is None:
        for offset, char in enumerate(value):
            if not ("a" <= char <= "z" or char == " "):
                raise UnsupportedSourceError(
                    f"Unsupported Case 1 source character U+{ord(char):04X} "
                    f"at offset {offset}: {char!r}"
                )
        raise UnsupportedSourceError("Unsupported Case 1 source construct")
    return value


def normalize_uncontracted_case2(text: str) -> str:
    """Validate and preserve ASCII English letters and ordinary spaces."""

    value = str(text)
    if _CASE2_SOURCE.fullmatch(value) is None:
        for offset, char in enumerate(value):
            if not ("A" <= char <= "Z" or "a" <= char <= "z" or char == " "):
                raise UnsupportedSourceError(
                    f"Unsupported Case 2 source character U+{ord(char):04X} "
                    f"at offset {offset}: {char!r}"
                )
        raise UnsupportedSourceError("Unsupported Case 2 source construct")
    return value


def normalize_uncontracted_case3(text: str) -> str:
    """Preserve supported English/numeric text; reject other constructs."""

    value = str(text)
    if _CASE3_SOURCE.fullmatch(value) is None:
        for offset, char in enumerate(value):
            if not (
                "A" <= char <= "Z"
                or "a" <= char <= "z"
                or "0" <= char <= "9"
                or char in " ,.-–—"
            ):
                raise UnsupportedSourceError(
                    f"Unsupported Case 3 source character U+{ord(char):04X} "
                    f"at offset {offset}: {char!r}"
                )
        raise UnsupportedSourceError("Unsupported Case 3 source construct")
    return value


def normalize_uncontracted_case4(text: str) -> str:
    """Preserve Case 1–3 text plus core punctuation; restrict dash contexts."""
    value = str(text)
    if _CASE4_SOURCE.fullmatch(value) is None:
        for offset, char in enumerate(value):
            if not (
                "A" <= char <= "Z" or "a" <= char <= "z"
                or "0" <= char <= "9" or char in " ,.!?:;–—-"
            ):
                raise UnsupportedSourceError(
                    f"Unsupported Case 4 source character U+{ord(char):04X} "
                    f"at offset {offset}: {char!r}"
                )
    for offset, char in enumerate(value):
        if char in "-–—" and not (
            offset > 0 and value[offset - 1].isdigit()
            and _CASE4_DASH_TAIL.match(value[offset + 1:]) is not None
        ):
            raise UnsupportedSourceError(
                f"Unsupported Case 4 hyphen/dash context at offset {offset}"
            )
    return value
