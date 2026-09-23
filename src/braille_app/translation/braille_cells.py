"""Canonical Braille-cell helpers used by the production pipeline.

Liblouis ``text_nabcc.dis`` and Duxbury BRF use different printable spellings
for a few cells.  Production comparisons therefore use Unicode Braille cell
code points (or integer dot masks), never the source ASCII spelling.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Iterable


def _mask(dots: str) -> int:
    result = 0
    for dot in dots:
        if dot.isdigit() and 1 <= int(dot) <= 8:
            result |= 1 << (int(dot) - 1)
    return result


# Printable spellings used by Liblouis text_nabcc.dis.
LIBLOUIS_DOTS = {
    " ": "",
    "a": "1", "b": "12", "c": "14", "d": "145", "e": "15",
    "f": "124", "g": "1245", "h": "125", "i": "24", "j": "245",
    "k": "13", "l": "123", "m": "134", "n": "1345", "o": "135",
    "p": "1234", "q": "12345", "r": "1235", "s": "234", "t": "2345",
    "u": "136", "v": "1236", "w": "2456", "x": "1346", "y": "13456",
    "z": "1356",
    "A": "17", "B": "127", "C": "147", "D": "1457", "E": "157",
    "F": "1247", "G": "12457", "H": "1257", "I": "247", "J": "2457",
    "K": "137", "L": "1237", "M": "1347", "N": "13457", "O": "1357",
    "P": "12347", "Q": "123457", "R": "12357", "S": "2347", "T": "23457",
    "U": "1367", "V": "12367", "W": "24567", "X": "13467", "Y": "134567",
    "Z": "13567",
    "0": "356", "1": "2", "2": "23", "3": "25", "4": "256",
    "5": "26", "6": "235", "7": "2356", "8": "236", "9": "35",
    ".": "46", "+": "346", "-": "36", "*": "16", "/": "34",
    "(": "12356", ")": "23456", "&": "12346", "#": "3456",
    ",": "6", ";": "56", ":": "156", "!": "2346", "?": "1456",
    '"': "5", "'": "3", "`": "4", "^": "457", "~": "45",
    "[": "2467", "]": "124567", "{": "246", "}": "12456",
    "=": "123456", "<": "126", ">": "345", "$": "1246", "%": "146",
    "@": "47", "|": "1256", "\\": "12567", "_": "456",
}


# The project's BRF parser uses this standard six-dot NABCC sequence for
# printable BRF.  It differs from Liblouis' extended text_nabcc display map
# for several punctuation aliases (notably ``[``/``]`` and ``^``/``\\``).
# Build the BRF map from that same sequence instead of copying the Liblouis
# map, so rendered BRF is canonicalized to the physical cells it represents.
_STANDARD_BRF_SEQUENCE = (
    " a1b'k2l@cif/msp\"e3h9o6r^djg>ntq,*5<-u8v.%[$+x!&;:4\\0z7(_?w]#y)="
)


def _dots_for_mask(mask: int) -> str:
    return "".join(str(dot) for dot in range(1, 7) if mask & (1 << (dot - 1)))


BRF_DOTS = {
    char: _dots_for_mask(mask)
    for mask, char in enumerate(_STANDARD_BRF_SEQUENCE)
}
for _letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
    BRF_DOTS[_letter] = BRF_DOTS[_letter.lower()]
# In the translated Duxbury Nemeth regions, @ is the dot-4 spelling of the
# Nemeth relation/indicator cells, as established by the Phase 1C BRF test.
BRF_DOTS["@"] = "4"

# Math output from Liblouis uses extended text.nabcc aliases for a handful of
# cells that Duxbury emits using the six-dot BRF spellings.  Normalize those
# aliases only for the expected math stream; literary UEB keeps the ordinary
# Liblouis display mapping.
LIBLOUIS_MATH_DOTS = dict(LIBLOUIS_DOTS)
for _char in ("[", "]", "^", "\\"):
    LIBLOUIS_MATH_DOTS[_char] = BRF_DOTS[_char]
LIBLOUIS_MATH_DOTS["@"] = BRF_DOTS["@"]


@lru_cache(maxsize=None)
def char_mask(char: str, dialect: str = "liblouis") -> int:
    if dialect == "duxbury":
        table = BRF_DOTS
    elif dialect == "liblouis_math":
        table = LIBLOUIS_MATH_DOTS
    else:
        table = LIBLOUIS_DOTS
    try:
        return _mask(table[char])
    except KeyError as exc:
        raise ValueError(f"Unsupported printable Braille cell: {char!r}") from exc


def ascii_to_cells(text: str, dialect: str = "liblouis") -> tuple[int, ...]:
    """Convert a printable Braille ASCII stream into dot masks."""

    if dialect not in {"liblouis", "liblouis_math", "duxbury"}:
        raise ValueError(f"Unknown Braille ASCII dialect: {dialect}")
    return tuple(char_mask(char, dialect) for char in text)


def unicode_to_cells(text: str) -> tuple[int, ...]:
    """Convert Unicode Braille cells and ordinary blanks into dot masks."""

    cells: list[int] = []
    for char in text:
        if char == " " or char == "\u2800":
            cells.append(0)
        elif 0x2800 <= ord(char) <= 0x28FF:
            cells.append(ord(char) - 0x2800)
        else:
            raise ValueError(f"Expected Unicode Braille or blank, got {char!r}")
    return tuple(cells)


def cells_to_unicode(cells: Iterable[int]) -> str:
    return "".join(chr(0x2800 + int(cell)) for cell in cells)


def dots_for_cells(cells: Iterable[int]) -> tuple[str, ...]:
    return tuple(
        "".join(str(dot) for dot in range(1, 9) if cell & (1 << (dot - 1)))
        for cell in cells
    )


def normalize_braille_stream(text: str, dialect: str = "duxbury") -> str:
    """Return a Unicode-Braille stream while preserving page/line separators."""

    out: list[str] = []
    for char in text:
        if char in "\r\n\f":
            out.append(char)
        elif 0x2800 <= ord(char) <= 0x28FF:
            out.append(char)
        elif char == " ":
            out.append("\u2800")
        else:
            out.append(cells_to_unicode((char_mask(char, dialect),)))
    return "".join(out)
