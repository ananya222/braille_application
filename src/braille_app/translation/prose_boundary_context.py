"""Conservative contextual *generation*, not standards certification.

Nemeth 4.6.5(b), example 4-31: attached surrounding-text punctuation
follows the terminator in UEB. UEB 7.1/7.5 and 2.6 distinguish attached
punctuation from standing-alone punctuation. Math is opaque to literary
translation: a neutral word models an occupied, nonnumeric item, never its
letters, capitalization or script state. Only mapped suffix output is used.
This is not a general quotation, list, numeric or persistent-mode resolver.
"""
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class ProseBoundaryContext:
    prose_view: str
    source_start: int
    source_end: int
    preceding_kind: str = "terminated_math"
    code: str = "UEB"


# UEB Section 7 common sentence punctuation. No cell replacement table.
ATTACHED_PUNCTUATION = frozenset(".,;:!?")
OPAQUE_ITEM = "math"


def contextualize_prose(spans, translator, profile):
    """Retain sentence neighbors when translating eligible post-math prose.

No generated-cell deletion/replacement heuristic: translate the contextual
source and select suffix cells through Liblouis's source-position map.
Require exact interval ownership and unchanged output beyond the initial
punctuation. Unknown/unsupported contexts retain the original candidate and
existing verifier policy. No rule is promoted here.
"""
    if (profile.switch_start, profile.switch_end) != ("⠸⠩", "⠸⠱"):
        return spans
    if not hasattr(translator, "translate_prose_with_positions"):
        return spans
    parts, intervals, cursor = [], [], 0
    for span in spans:
        part = OPAQUE_ITEM if span.kind == "math" else span.source
        parts.append(part)
        intervals.append((cursor, cursor + len(part)))
        cursor += len(part)
    prose_view = "".join(parts)
    # Quotes/typeforms, physical layout and attached words require more state.
    if any(c in prose_view for c in '\r\n\f"\'“”‘’') or any(ord(c) > 0xFFFF for c in prose_view):
        return spans
    candidates = []
    for i, span in enumerate(spans):
        if not i or span.kind != "text" or spans[i - 1].kind != "math":
            continue
        text = span.source
        if not text or text[0] not in ATTACHED_PUNCTUATION:
            continue
        if len(text) > 1 and not text[1].isspace():
            continue  # clusters, attached symbols, closing quotes, ellipses
        math = spans[i - 1]
        if not math.source or math.source != math.source.strip() or not math.braille:
            continue
        if i > 1 and (spans[i - 2].kind != "text" or not spans[i - 2].source.endswith(" ")):
            continue
        candidates.append((i, ProseBoundaryContext(prose_view, *intervals[i])))
    if not candidates:
        return spans
    cells, positions = translator.translate_prose_with_positions(prose_view)
    if (len(cells) != len(positions) or list(positions) != sorted(positions)
            or any(p < 0 or p >= len(prose_view) for p in positions)):
        return spans
    result = list(spans)
    for i, context in candidates:
        start, end = context.source_start, context.source_end
        indexes = [j for j, p in enumerate(positions) if start <= p < end]
        if not indexes or indexes != list(range(indexes[0], indexes[-1] + 1)):
            continue
        if positions[indexes[0]] != start:
            continue
        isolated, isolated_positions = translator.translate_prose_with_positions(spans[i].source)
        if isolated != spans[i].braille:
            continue
        suffix = cells[indexes[0]:indexes[-1] + 1]
        # Do not accept changes to words/modes downstream of the punctuation.
        rest = "".join(cells[j] for j in indexes if positions[j] > start)
        old_rest = "".join(c for c, p in zip(isolated, isolated_positions) if p > 0)
        if rest != old_rest:
            continue
        result[i] = replace(spans[i], braille=suffix)
    return result
