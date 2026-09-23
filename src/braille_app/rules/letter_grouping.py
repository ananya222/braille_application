"""Source-structural proof for a deliberately small Rule 6/19 subset.

No translation rewrite. A candidate is eligible only when its whole math
record has this grammar and exactly matches a separately derived sequence.
Numbers, lists, operators, words, typeforms and punctuation remain outside
the promoted parser. Typed one-sided decisions below require caller-resolved
neighbors; they do not guess punctuation ownership from characters.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

from braille_app.translation.braille_cells import ascii_to_cells, cells_to_unicode
from .rule_catalog import ValidationContext
from .rule_result import RuleResult
from .sources import NEMETH_2022

RULE_ID = "NEMETH_LETTER_GROUP_001"


def record_promotion_contexts(block) -> tuple[bool, ...]:
    """Exact source-marker order, with unresolved adjacent prose excluded.

    This is NOT a punctuation ownership rule. Any non-whitespace character
    touching either outer marker is a dependency and retains REVIEW. It
    avoids promoting a whole block on a math-only proof when its code
    boundary carries punctuation or an unseparated prose token.
    """
    records = tuple(getattr(block, "math_records", ()))
    matches = tuple(re.finditer(r"\[\[\*ts\*\]\](.*?)\[\[\*te\*\]\]", block.source_text, re.S))
    if len(records) != len(matches) or any(r.source != m.group(1) for r,m in zip(records,matches)):
        return (False,) * len(records)
    return tuple(
        (m.start() == 0 or block.source_text[m.start()-1].isspace())
        and (m.end() == len(block.source_text) or block.source_text[m.end()].isspace())
        for m in matches
    )


@dataclass(frozen=True)
class LetterNode:
    value: str
    regular_type: bool = True
    modified: bool = False
    role: str = "mathematical_letter"


@dataclass(frozen=True)
class GroupNode:
    opening: str
    child: object
    closing: str


@dataclass(frozen=True)
class FunctionCallNode:
    # Syntactic application only: not an assertion about Rule 18.
    callee: LetterNode
    arguments: GroupNode


@dataclass(frozen=True)
class LetterEnvironment:
    contact: str = "outside"  # both / left / right / outside
    # Neighbors after ignoring the contacted grouping sign (6.4.9).
    left: str = "space"
    right: str = "space"
    enclosed_list: bool = False  # already established under 3.5.1
    comparison_adjacent: bool = False  # already resolved under 6.4.7
    grouping_modified: bool = False


@dataclass(frozen=True)
class IndicatorDecision:
    required: bool | None
    sections: tuple[str, ...]
    reason: str


def decide_indicator(letter: LetterNode, env: LetterEnvironment, context: ValidationContext) -> IndicatorDecision:
    if (context.code != "NEMETH" or context.script_level != 0 or context.numeric_mode or context.grade1_mode
            or not letter.regular_type or letter.modified
            or letter.role != "mathematical_letter"
            or not re.fullmatch("[A-Za-z]", letter.value)):
        return IndicatorDecision(None, ("6.3.1",), "Outside resolved regular unmodified English mathematical-letter scope")
    if env.contact not in {"both", "left", "right", "outside"}:
        return IndicatorDecision(None, ("6.4.9",), "Unresolved grouping relationship")
    if env.enclosed_list:
        return IndicatorDecision(False, ("6.4.5", "3.5.1"), "Item of a separately resolved enclosed list")
    if env.comparison_adjacent:
        return IndicatorDecision(False, ("6.4.7",), "Adjacent comparison suppresses the indicator")
    if env.contact == "both":
        return IndicatorDecision(False, ("6.4.8",), "Direct contact with both grouping signs")
    if env.contact in {"left", "right"} and env.grouping_modified:
        return IndicatorDecision(False, ("6.4.9",), "Contacted grouping sign has a prime or script")
    known = {"space", "punctuation", "letter", "operation", "group"}
    if env.left not in known or env.right not in known:
        return IndicatorDecision(None, ("6.3.1", "6.4.9"), "Effective neighbors need source-context resolution")
    required = env.left in {"space", "punctuation"} and env.right in {"space", "punctuation"}
    sections = ("6.3.1", "6.4.9") if env.contact in {"left", "right"} else ("6.3.1", "6.4.11")
    return IndicatorDecision(required, sections, "Apply single-letter criteria to the resolved effective neighbors")


_PAIRS = {"(": ")", "[": "]", "{": "}"}
_GROUP_ASCII = {"(": "(", ")": ")", "[": "@(", "]": "@)", "{": ".(", "}": ".)"}


def parse_letter_group(source: str):
    """Whole-record grammar: letter, group(atom), or single-letter application.

    Root must contain grouping. All whitespace and trailing punctuation are
    rejected, rather than discarded. Mixed grouping, words, scripts, primes,
    lists and numeric arguments require other rules and are not parsed here.
    """
    if not source or not re.fullmatch(r"[A-Za-z()\[\]{}]+", source):
        return None
    cursor = 0

    def group():
        nonlocal cursor
        opening = source[cursor]
        cursor += 1
        child = atom()
        if cursor >= len(source) or source[cursor] != _PAIRS[opening]:
            raise ValueError
        cursor += 1
        return GroupNode(opening, child, _PAIRS[opening])

    def atom():
        nonlocal cursor
        if cursor >= len(source):
            raise ValueError
        if source[cursor] in _PAIRS:
            return group()
        if not source[cursor].isascii() or not source[cursor].isalpha():
            raise ValueError
        letter = LetterNode(source[cursor])
        cursor += 1
        if cursor < len(source) and source[cursor] in _PAIRS:
            return FunctionCallNode(letter, group())
        return letter

    try:
        node = atom()
        return node if cursor == len(source) and not isinstance(node, LetterNode) else None
    except (ValueError, RecursionError):
        return None


def _letter_ascii(letter: LetterNode) -> str:
    # Nemeth 5.1.1 and 5.3.1: capital indicator applies to this letter only.
    return ("," if letter.value.isupper() else "") + letter.value.lower()


def expected_group_cells(node, context: ValidationContext) -> str | None:
    if (context.code != "NEMETH" or context.script_level or context.capitalization_mode is not None
            or context.numeric_mode or context.grade1_mode):
        return None

    def emit(item, enclosed=False):
        if isinstance(item, LetterNode):
            decision = decide_indicator(item, LetterEnvironment(contact="both" if enclosed else "outside"), context)
            if decision.required is None:
                raise ValueError
            return (";" if decision.required else "") + _letter_ascii(item)
        if isinstance(item, GroupNode):
            if _PAIRS.get(item.opening) != item.closing:
                raise ValueError
            return _GROUP_ASCII[item.opening] + emit(item.child, True) + _GROUP_ASCII[item.closing]
        if isinstance(item, FunctionCallNode):
            decision = decide_indicator(item.callee, LetterEnvironment(right="group"), context)
            if decision.required is not False:
                raise ValueError
            return _letter_ascii(item.callee) + emit(item.arguments)
        raise ValueError
    try:
        return cells_to_unicode(ascii_to_cells(emit(node), "duxbury"))
    except (ValueError, RecursionError):
        return None


def verify_record(record, context: ValidationContext, page=None, block_id=None) -> RuleResult | None:
    node = parse_letter_group(record.source)
    if node is None:
        return None
    expected = expected_group_cells(node, context)
    if expected is None:
        return None
    return RuleResult(
        rule_id=RULE_ID, status="PASS" if record.braille == expected else "REVIEW",
        source=record.source, original_braille=record.braille, corrected_braille=expected,
        page=page, block=block_id, standard_area="Nemeth", family="letter-grouping",
        source_document=NEMETH_2022, source_rule="6.3.1; 6.4.8; 6.4.11; 19.1.1; 5.1.1/5.3.1",
        source_page="6-6, 6-14–15; 19-1–2; 5-1–2 (PDF 91,99–100,253–254,84–85)",
        source_construct=type(node).__name__,
        explanation="Whole-record regular letter/group AST checked against independently derived canonical cells; no translation rewritten.",
        justification="No punctuation, numeric, script, typeform or named-function dependency in the accepted grammar.",
        original_cells=tuple(ord(c)-0x2800 for c in record.braille),
        expected_cells=tuple(ord(c)-0x2800 for c in expected),
        corrected_cells=tuple(ord(c)-0x2800 for c in expected),
    )
