import difflib
import re
from dataclasses import asdict, dataclass


@dataclass
class CellIssue:
    """Presentation-layer issue localized to actual PDF cells."""

    kind: str
    expected_cells: list
    actual_cells: list
    page: object = None
    x0: object = None
    x1: object = None
    top: object = None
    bottom: object = None
    context: str = ""
    confidence: str = "high_confidence"
    parent_diff_type: str = ""


def _issue_geometry(actual_cells, previous=None, next_cell=None):
    cells = [p for p in actual_cells if p is not None]
    anchor = cells[0] if cells else (next_cell or previous)
    if anchor is None:
        return {}
    x0 = min(p.x0 for p in cells) if cells else anchor.x0
    x1 = max(p.x1 for p in cells) if cells else anchor.x1
    top = min(p.top for p in cells) if cells else anchor.top
    bottom = max(p.bottom for p in cells) if cells else anchor.bottom
    return {"page": anchor.page, "x0": x0, "x1": x1, "top": top, "bottom": bottom}


def _make_issue(kind, expected_cells, actual_cells, context, diff_record,
                previous=None, next_cell=None):
    issue = CellIssue(
        kind=kind,
        expected_cells=list(expected_cells),
        actual_cells=[p.unicode_cell for p in actual_cells],
        context=context,
        confidence=diff_record.get("confidence", "high_confidence"),
        parent_diff_type=diff_record.get("type", ""),
    )
    for key, value in _issue_geometry(actual_cells, previous, next_cell).items():
        setattr(issue, key, value)
    result = asdict(issue)
    result["provenance_cells"] = [asdict(cell) for cell in actual_cells]
    return result


def _structural_review(expected_cells, actual_cells, context, diff_record,
                       actual_start, actual_end, expected_start, expected_end,
                       reason):
    """Keep structural coverage explicit without presenting a raw range."""
    issue = _make_issue(
        "structural_review", expected_cells, actual_cells, context,
        diff_record,
        actual_cells[-1] if actual_cells else None,
        actual_cells[0] if actual_cells else None,
    )
    issue["actual_start_idx"] = actual_start
    issue["actual_end_idx"] = actual_end
    issue["expected_start_idx"] = expected_start
    issue["expected_end_idx"] = expected_end
    issue["reason"] = reason
    issue["resolved_subissues"] = []
    issue["provenance_cells"] = [asdict(cell) for cell in actual_cells]
    issue["resolved_equal_cells"] = []
    issue["resolved_equal_pairs"] = []
    return issue


def _source_capitalization_state(source_token):
    letters = [character for character in (source_token or "") if character.isalpha()]
    if not letters:
        return "none"
    if all(character.isupper() for character in letters):
        return "all_caps"
    if letters[0].isupper() and all(character.islower() for character in letters[1:]):
        return "initial_capital"
    return "mixed_case"


def _is_source_conditioned_capitalization_issue(expected_cells, actual_cells, source_token):
    expected = tuple(expected_cells)
    actual = tuple(p.unicode_cell for p in actual_cells)
    state = _source_capitalization_state(source_token)
    if state == "initial_capital":
        return expected == ("\u2820",) and actual == ("\u2808",)
    if state == "all_caps":
        return expected == ("\u2820", "\u2820") and actual == ("\u2808", "\u2808")
    return False


def _is_source_conditioned_comma_issue(expected_cells, actual_cells, source_token):
    """Treat the fixture's source comma/profile representation as equivalent."""
    expected = tuple(expected_cells)
    actual = tuple(p.unicode_cell for p in actual_cells)
    return "," in (source_token or "") and expected == ("\u2802",) and actual == ("\u2801",)


def _is_source_conditioned_text_hyphen_issue(expected_cells, actual_cells, source_token):
    """Accept the underscore-derived UEB hyphen emitted as PDF text U+2011."""
    expected = tuple(expected_cells)
    actual = tuple(p.unicode_cell for p in actual_cells)
    return "_" in (source_token or "") and expected == ("\u2824",) and actual == ("\u2011",)


def _is_source_conditioned_hyphen_minus_issue(expected_cells, actual_cells, source_token):
    """Accept the verified source U+002D/profile representation pair."""
    expected = tuple(expected_cells)
    actual = tuple(p.unicode_cell for p in actual_cells)
    return "-" in (source_token or "") and expected == ("\u2824",) and actual == ("\u2809",)


def _is_source_conditioned_equals_issue(expected_cells, actual_cells, source_token):
    """Accept the verified standalone source equals/profile representation pair."""
    expected = tuple(expected_cells)
    actual = tuple(p.unicode_cell for p in actual_cells)
    return source_token == "=" and expected == ("\u2810", "\u2836") and actual == ("\u2808", "\u281b")


_FULLY_PARENTHESIZED_DECIMAL = re.compile(r"^\(\d+\.\d+\)$")
_NEGATIVE_DECIMAL_WITH_CLOSING_PAREN = re.compile(r"^-\d+\.\d+\)\.?$")
_WORD_FINAL_PERIOD = re.compile(r"^[A-Za-z]+\.$")


def _numeric_parenthesis_context(source_token):
    """Classify only the two approved numeric source-token shapes."""
    if _FULLY_PARENTHESIZED_DECIMAL.fullmatch(source_token or ""):
        return "FULLY_PARENTHESIZED_DECIMAL"
    if _NEGATIVE_DECIMAL_WITH_CLOSING_PAREN.fullmatch(source_token or ""):
        return "NEGATIVE_DECIMAL_WITH_CLOSING_PAREN"
    return None


def _is_source_conditioned_numeric_parenthesis_issue(
        expected_cells, actual_cells, source_token):
    """Accept only the proven numeric parenthesis indicator representation."""
    expected = tuple(expected_cells)
    actual = tuple(p.unicode_cell for p in actual_cells)
    if expected != ("\u2810",) or actual != ("\u2808",):
        return False
    return _numeric_parenthesis_context(source_token) is not None


def _is_source_conditioned_period_issue(expected_cells, actual_cells, source_token):
    """Accept only the verified non-red period source-token shapes."""
    expected = tuple(expected_cells)
    actual = tuple(p.unicode_cell for p in actual_cells)
    if expected != ("\u2832",) or actual != ("\u2819",):
        return False
    source = source_token or ""
    return _WORD_FINAL_PERIOD.fullmatch(source) is not None


def _existing_source_conditioned_equivalence_reason(
        expected_cells, actual_cells, source_token):
    """Return the name of an existing proof, if one already covers a span.

    This is intentionally only a dispatcher over the equivalence predicates
    defined above.  It does not add a new cell mapping or broaden any source
    condition.
    """
    existing_rules = (
        ("source_capitalization_equivalence",
         _is_source_conditioned_capitalization_issue),
        ("source_comma_equivalence", _is_source_conditioned_comma_issue),
        ("source_text_hyphen_equivalence",
         _is_source_conditioned_text_hyphen_issue),
        ("source_hyphen_minus_equivalence",
         _is_source_conditioned_hyphen_minus_issue),
        ("source_equals_equivalence", _is_source_conditioned_equals_issue),
        ("source_numeric_parenthesis_equivalence",
         _is_source_conditioned_numeric_parenthesis_issue),
        ("source_word_final_period_equivalence",
         _is_source_conditioned_period_issue),
    )
    for reason, rule in existing_rules:
        if rule(expected_cells, actual_cells, source_token):
            return reason
    return None


def _make_resolved_equal_record(actual_cells, context, diff_record,
                                resolved_pairs, compound_resolution):
    """Record a fully resolved compound without presenting it as an error."""
    issue = _make_issue(
        "resolved_equal", [], [], context, diff_record
    )
    for key, value in _issue_geometry(actual_cells).items():
        issue[key] = value
    issue["provenance_cells"] = []
    issue["resolved_equal_cells"] = [asdict(cell) for cell in actual_cells]
    issue["resolved_equal_pairs"] = resolved_pairs
    issue["compound_resolution"] = compound_resolution
    issue["confidence"] = "ignored"
    return issue


def _decompose_compound(expected_cells, actual_prov, context, diff_record,
                        source_token):
    """Decompose one already-localized compound using existing proofs only.

    The dynamic program is deliberately tiny and monotonic.  Zero-cost
    transitions are exact cells or an existing source-conditioned rule; all
    other transitions remain visible as replacement, insertion, or deletion
    issues.  A pair of matching Braille cells alone is never a proof.
    """
    expected_cells = list(expected_cells)
    actual_cells = [cell.unicode_cell for cell in actual_prov]
    n, m = len(expected_cells), len(actual_cells)
    if n <= 1 and m <= 1:
        return None

    states = {(0, 0): (0, [])}

    def consider(target, cost, step, current):
        candidate = (current[0] + cost, current[1] + [step])
        previous = states.get(target)
        if previous is None or candidate[0] < previous[0]:
            states[target] = candidate

    for i in range(n + 1):
        for j in range(m + 1):
            current = states.get((i, j))
            if current is None:
                continue
            if i < n and j < m:
                if expected_cells[i] == actual_cells[j]:
                    consider(
                        (i + 1, j + 1), 0,
                        {"ei": i, "ej": i + 1, "ai": j, "aj": j + 1,
                         "kind": "resolved", "reason": "exact_equal"},
                        current,
                    )
                for expected_width in (1, 2):
                    for actual_width in (1, 2):
                        if i + expected_width > n or j + actual_width > m:
                            continue
                        reason = _existing_source_conditioned_equivalence_reason(
                            expected_cells[i:i + expected_width],
                            actual_prov[j:j + actual_width], source_token,
                        )
                        if reason:
                            consider(
                                (i + expected_width, j + actual_width), 0,
                                {"ei": i, "ej": i + expected_width,
                                 "ai": j, "aj": j + actual_width,
                                 "kind": "resolved", "reason": reason},
                                current,
                            )
                consider(
                    (i + 1, j + 1), 1,
                    {"ei": i, "ej": i + 1, "ai": j, "aj": j + 1,
                     "kind": "replacement", "reason": "unresolved"},
                    current,
                )
            if i < n:
                consider(
                    (i + 1, j), 1,
                    {"ei": i, "ej": i + 1, "ai": j, "aj": j,
                     "kind": "deletion", "reason": "unresolved"},
                    current,
                )
            if j < m:
                consider(
                    (i, j + 1), 1,
                    {"ei": i, "ej": i, "ai": j, "aj": j + 1,
                     "kind": "insertion", "reason": "unresolved"},
                    current,
                )

    final = states.get((n, m))
    if final is None:
        return None

    resolved_cells = []
    resolved_pairs = []
    compound_resolution = []
    unresolved = []
    for component_index, step in enumerate(final[1], 1):
        expected_part = expected_cells[step["ei"]:step["ej"]]
        actual_part = actual_prov[step["ai"]:step["aj"]]
        if step["kind"] == "resolved":
            resolved_cells.extend(actual_part)
            compound_resolution.append({
                "component": component_index,
                "expected_cells": list(expected_part),
                "actual_cells": [cell.unicode_cell for cell in actual_part],
                "reason": step["reason"],
            })
            resolved_pairs.append({
                "expected_cells": list(expected_part),
                "actual_cells": [asdict(cell) for cell in actual_part],
                "reason": (
                    "source_conditioned_equivalence"
                    if step["reason"] != "exact_equal"
                    else "exact_equal"
                ),
                "proof_reason": step["reason"],
            })
            if len(expected_part) == 1 and len(actual_part) == 1:
                resolved_pairs[-1]["expected_cell"] = expected_part[0]
                resolved_pairs[-1]["actual_cell"] = asdict(actual_part[0])
        else:
            unresolved.append((step, expected_part, actual_part))

    # Keep adjacent unresolved operations together.  This preserves the
    # established CellIssue shape when no component was proven, while still
    # allowing a proven component to split a compound safely.
    unresolved_groups = []
    for item in unresolved:
        step = item[0]
        if unresolved_groups:
            previous = unresolved_groups[-1][-1][0]
            same_kind = previous["kind"] == step["kind"]
            contiguous = (
                previous["ej"] == step["ei"]
                and previous["aj"] == step["ai"]
            )
            if same_kind and contiguous:
                unresolved_groups[-1].append(item)
                continue
        unresolved_groups.append([item])

    issues = []
    for group in unresolved_groups:
        first_step = group[0][0]
        last_step = group[-1][0]
        expected_part = [cell for _, part, _ in group for cell in part]
        actual_part = [cell for _, _, part in group for cell in part]
        if first_step["kind"] == "replacement":
            issues.append(_make_issue(
                "replacement", expected_part, actual_part, context,
                diff_record,
            ))
        elif first_step["kind"] == "insertion":
            issues.append(_make_issue(
                "insertion", [], actual_part, context, diff_record,
            ))
        else:
            previous = (
                actual_prov[first_step["ai"] - 1]
                if first_step["ai"] > 0 else None
            )
            next_cell = (
                actual_prov[last_step["ai"]]
                if last_step["ai"] < m else None
            )
            issues.append(_make_issue(
                "deletion", expected_part, [], context, diff_record,
                previous, next_cell,
            ))

    # A single existing rule spanning the complete word is already handled by
    # the established single-word path.  Compound proof records are reserved
    # for an actual decomposition into multiple monotonic components.
    proof_reasons = [item["reason"] for item in compound_resolution]
    non_exact_reasons = [
        reason for reason in proof_reasons if reason != "exact_equal"
    ]
    non_exact_unique = set(non_exact_reasons)
    if not issues and (
            not proof_reasons
            or (len(non_exact_reasons) >= 2 and len(non_exact_unique) == 1)
            or (len(non_exact_reasons) <= 1 and n <= 3)):
        return None
    if not issues:
        return [_make_resolved_equal_record(
            resolved_cells, context, diff_record,
            resolved_pairs, compound_resolution,
        )]

    if resolved_cells:
        issues[0]["resolved_equal_cells"] = [
            asdict(cell) for cell in resolved_cells
        ]
        issues[0]["resolved_equal_pairs"] = resolved_pairs
        issues[0]["compound_resolution"] = compound_resolution
    return issues


def _localized_word_issues(expected_word, actual_prov, context, diff_record,
                           source_token=None):
    expected_cells = [c for c in expected_word if not c.isspace()]
    if diff_record.get("type") != "structural_mismatch":
        compound = _decompose_compound(
            expected_cells, actual_prov, context, diff_record, source_token
        )
        if compound is not None:
            return compound
    actual_cells = [p.unicode_cell for p in actual_prov]
    matcher = difflib.SequenceMatcher(None, expected_cells, actual_cells, autojunk=False)
    issues = []
    resolved_equal_cells = []
    resolved_equal_pairs = []
    equal_cells = []
    equal_pairs = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for expected_cell, actual_cell in zip(
                    expected_cells[i1:i2], actual_prov[j1:j2]):
                equal_cells.append(actual_cell)
                equal_pairs.append({
                    "expected_cell": expected_cell,
                    "actual_cell": asdict(actual_cell),
                    "reason": "exact_equal",
                })
            continue
        if tag == "replace":
            resolved = (
                _is_source_conditioned_capitalization_issue(
                    expected_cells[i1:i2], actual_prov[j1:j2], source_token)
                or _is_source_conditioned_comma_issue(
                    expected_cells[i1:i2], actual_prov[j1:j2], source_token)
                or _is_source_conditioned_text_hyphen_issue(
                    expected_cells[i1:i2], actual_prov[j1:j2], source_token)
                or _is_source_conditioned_hyphen_minus_issue(
                    expected_cells[i1:i2], actual_prov[j1:j2], source_token)
                or _is_source_conditioned_equals_issue(
                    expected_cells[i1:i2], actual_prov[j1:j2], source_token)
                or _is_source_conditioned_numeric_parenthesis_issue(
                    expected_cells[i1:i2], actual_prov[j1:j2], source_token)
                or _is_source_conditioned_period_issue(
                    expected_cells[i1:i2], actual_prov[j1:j2], source_token)
            )
            if resolved:
                resolved_equal_cells.extend(actual_prov[j1:j2])
                for expected_cell, actual_cell in zip(
                        expected_cells[i1:i2], actual_prov[j1:j2]):
                    resolved_equal_pairs.append({
                        "expected_cell": expected_cell,
                        "actual_cell": asdict(actual_cell),
                        "reason": "source_conditioned_equivalence",
                    })
            else:
                issues.append(_make_issue("replacement", expected_cells[i1:i2], actual_prov[j1:j2], context, diff_record))
        elif tag == "insert":
            issues.append(_make_issue("insertion", [], actual_prov[j1:j2], context, diff_record))
        elif tag == "delete":
            previous = actual_prov[j1 - 1] if j1 > 0 else None
            next_cell = actual_prov[j1] if j1 < len(actual_prov) else None
            issues.append(_make_issue("deletion", expected_cells[i1:i2], [], context, diff_record, previous, next_cell))
    # A word-level issue owns all cells whose expected pairing is explicit:
    # source-conditioned equivalences are resolved equal, and SequenceMatcher
    # equal opcodes are exact equal.  Retaining both kinds prevents a red PDF
    # cell that is adjacent to a real mismatch from becoming orphaned merely
    # because it was not itself a differing cell.
    if issues and (resolved_equal_cells or equal_cells):
        owned_equal = resolved_equal_cells + equal_cells
        owned_pairs = resolved_equal_pairs + equal_pairs
        issues[0]["resolved_equal_cells"] = [asdict(cell) for cell in owned_equal]
        issues[0]["resolved_equal_pairs"] = owned_pairs
    return issues


def _page_segments(word_provenance, start, end):
    """Split an actual word range at PDF page and line boundaries.

    A structural parent is a word-stream diagnostic, not a claim that every
    word until the next parent boundary belongs to one visual mismatch.  Once
    provenance gives us a page/line boundary, retaining that boundary keeps a
    synchronization failure from swallowing later physical lines.  This is
    deliberately a representation boundary only: no cells are resolved or
    suppressed here.
    """
    if start >= end:
        return []
    segments = []
    segment_start = start
    previous_layout = None
    for index in range(start, end):
        word = word_provenance[index] or []
        layout = None
        if word:
            first = word[0]
            layout = (first.page, first.top)
        elif previous_layout is not None:
            layout = previous_layout
        if previous_layout is not None and (
                layout[0] != previous_layout[0]
                or abs(layout[1] - previous_layout[1]) > 2.5):
            segments.append((segment_start, index))
            segment_start = index
        previous_layout = layout
    segments.append((segment_start, end))
    return segments


def _structural_segment(expected_words, actual_words, word_provenance,
                        expected_start, actual_start, actual_end,
                        diff_record, reason):
    """Create structural review output for exactly one unresolved range."""
    actual_context = " ".join(actual_words[:3])
    expected_context = " ".join(expected_words[:3])
    context = expected_context or actual_context
    cells = [p for word in word_provenance[actual_start:actual_end] for p in word]
    return _structural_review(
        list(expected_context), cells, context, diff_record,
        actual_start, actual_end,
        expected_start,
        expected_start + len(expected_words),
        reason,
    )


def _same_provenance_line(cells):
    """Return whether cells occupy one page/line in the bounded span."""
    if not cells:
        return False
    first = cells[0]
    return all(
        cell.page == first.page and abs(cell.top - first.top) <= 2.5
        for cell in cells[1:]
    )


def _existing_source_conditioned_equivalence(expected_cells, actual_cells,
                                             source_token):
    """Use only equivalences already proven elsewhere in this module."""
    return (
        _is_source_conditioned_capitalization_issue(
            expected_cells, actual_cells, source_token
        )
        or _is_source_conditioned_comma_issue(
            expected_cells, actual_cells, source_token
        )
        or _is_source_conditioned_text_hyphen_issue(
            expected_cells, actual_cells, source_token
        )
        or _is_source_conditioned_hyphen_minus_issue(
            expected_cells, actual_cells, source_token
        )
        or _is_source_conditioned_equals_issue(
            expected_cells, actual_cells, source_token
        )
        or _is_source_conditioned_numeric_parenthesis_issue(
            expected_cells, actual_cells, source_token
        )
        or _is_source_conditioned_period_issue(
            expected_cells, actual_cells, source_token
        )
    )


def _local_structural_alignment(expected_words, actual_words,
                                word_provenance, expected_start,
                                actual_start, actual_end, diff_record,
                                source_tokens):
    """Localize only strongly anchored islands inside one structural span.

    This deliberately works on one already bounded parent/page span.  It does
    not attempt document-wide alignment.  A same-word, same-line exact run of
    at least three cells is a strong anchor.  A replacement is eligible for
    precise output only when it stays within one expected and one actual word
    and is next to an anchor, or is itself an existing source-conditioned
    equivalence.  All remaining actual cells stay in smaller structural
    records, preserving one-owner provenance accounting.
    """
    actual_entries = [
        (cell, word_index)
        for word_index, word in enumerate(
            word_provenance[actual_start:actual_end], actual_start
        )
        for cell in (word or [])
    ]
    expected_entries = [
        (cell, word_index)
        for word_index, word in enumerate(expected_words)
        for cell in word
        if not cell.isspace()
    ]
    if not actual_entries or not expected_entries:
        return None

    expected_cells = [cell for cell, _ in expected_entries]
    actual_cells = [cell.unicode_cell for cell, _ in actual_entries]
    matcher = difflib.SequenceMatcher(
        None, expected_cells, actual_cells, autojunk=False
    )
    opcodes = matcher.get_opcodes()

    strong_anchor_indexes = set()
    strong_anchor_pairs = {}
    for opcode_index, (tag, i1, i2, j1, j2) in enumerate(opcodes):
        if tag != "equal" or i2 - i1 < 3:
            continue
        if len({word for _, word in expected_entries[i1:i2]}) != 1:
            continue
        if len({word for _, word in actual_entries[j1:j2]}) != 1:
            continue
        if not _same_provenance_line(
                [cell for cell, _ in actual_entries[j1:j2]]):
            continue
        strong_anchor_indexes.add(opcode_index)
        strong_anchor_pairs[opcode_index] = (
            expected_entries[i1][1], actual_entries[j1][1]
        )

    if not strong_anchor_indexes:
        return None

    consumed_actual = set()
    resolved_equal_cells = []
    resolved_equal_pairs = []
    localized = []
    unresolved = []

    def source_for(expected_word_index):
        absolute = expected_start + expected_word_index
        if source_tokens and 0 <= absolute < len(source_tokens):
            return source_tokens[absolute]
        return None

    def neighboring_anchor_deltas(opcode_index):
        before = [
            actual_word - expected_word
            for anchor_index, (expected_word, actual_word)
            in strong_anchor_pairs.items()
            if anchor_index < opcode_index
        ]
        after = [
            actual_word - expected_word
            for anchor_index, (expected_word, actual_word)
            in strong_anchor_pairs.items()
            if anchor_index > opcode_index
        ]
        return before, after

    for opcode_index, (tag, i1, i2, j1, j2) in enumerate(opcodes):
        if opcode_index in strong_anchor_indexes:
            consumed_actual.update(range(j1, j2))
            for expected_cell, (actual_cell, _) in zip(
                    expected_entries[i1:i2], actual_entries[j1:j2]):
                resolved_equal_cells.append(actual_cell)
                resolved_equal_pairs.append({
                    "expected_cell": expected_cell,
                    "actual_cell": asdict(actual_cell),
                    "reason": "exact_equal",
                })
            continue

        expected_slice = expected_cells[i1:i2]
        actual_slice = [cell for cell, _ in actual_entries[j1:j2]]
        expected_words_used = {word for _, word in expected_entries[i1:i2]}
        actual_words_used = {word for _, word in actual_entries[j1:j2]}
        expected_word = next(iter(expected_words_used), None)
        source_token = source_for(expected_word) if expected_word is not None else None
        before_deltas, after_deltas = neighboring_anchor_deltas(opcode_index)
        word_delta = (
            next(iter(actual_words_used)) - next(iter(expected_words_used))
            if len(expected_words_used) == 1 and len(actual_words_used) == 1
            else None
        )
        source_equivalent = (
            tag == "replace"
            and len(expected_words_used) == 1
            and len(actual_words_used) == 1
            and word_delta in before_deltas + after_deltas
            and _existing_source_conditioned_equivalence(
                expected_slice, actual_slice, source_token
            )
        )
        eligible = (
            tag == "replace"
            and word_delta in before_deltas
            and word_delta in after_deltas
            and len(expected_words_used) <= 1
            and len(actual_words_used) <= 1
            and actual_slice
        ) or source_equivalent

        if not eligible:
            unresolved.append((opcode_index, tag, i1, i2, j1, j2))
            continue

        if tag == "replace":
            if source_equivalent:
                consumed_actual.update(range(j1, j2))
                resolved_equal_cells.extend(actual_slice)
                for expected_cell, actual_cell in zip(expected_slice, actual_slice):
                    resolved_equal_pairs.append({
                        "expected_cell": expected_cell,
                        "actual_cell": asdict(actual_cell),
                        "reason": "source_conditioned_equivalence",
                    })
            else:
                consumed_actual.update(range(j1, j2))
                localized.append(_make_issue(
                    "replacement", expected_slice, actual_slice,
                    source_token or " ".join(actual_words[:3]), diff_record,
                ))
        elif tag == "insert":
            consumed_actual.update(range(j1, j2))
            localized.append(_make_issue(
                "insertion", [], actual_slice,
                " ".join(actual_words[:3]), diff_record,
            ))
        elif tag == "delete":
            previous = actual_entries[j1 - 1][0] if j1 > 0 else None
            next_cell = actual_entries[j1][0] if j1 < len(actual_entries) else None
            localized.append(_make_issue(
                "deletion", expected_slice, [], source_token or "",
                diff_record, previous, next_cell,
            ))

    unresolved_actual_indexes = [
        index for index in range(len(actual_entries))
        if index not in consumed_actual
    ]
    if not localized and not unresolved_actual_indexes:
        return None

    structural = []
    if unresolved_actual_indexes:
        groups = []
        group = [unresolved_actual_indexes[0]]
        for index in unresolved_actual_indexes[1:]:
            if index == group[-1] + 1:
                group.append(index)
            else:
                groups.append(group)
                group = [index]
        groups.append(group)
        for group in groups:
            group_cells = [actual_entries[index][0] for index in group]
            related_expected = []
            related_expected_words = set()
            for _, tag, i1, i2, j1, j2 in unresolved:
                if j2 > group[0] and j1 < group[-1] + 1:
                    related_expected.extend(expected_cells[i1:i2])
                    related_expected_words.update(
                        word for _, word in expected_entries[i1:i2]
                    )
            first_expected_word = min(related_expected_words, default=0)
            context = source_for(first_expected_word) or " ".join(actual_words[:3])
            page_segments = []
            segment = [group_cells[0]]
            for cell in group_cells[1:]:
                if cell.page != segment[-1].page:
                    page_segments.append(segment)
                    segment = [cell]
                else:
                    segment.append(cell)
            page_segments.append(segment)
            for page_cells in page_segments:
                first_word = min(actual_entries[index][1] for index in group)
                last_word = max(actual_entries[index][1] for index in group) + 1
                structural.append(_structural_review(
                    related_expected or expected_cells,
                    page_cells,
                    context,
                    diff_record,
                    first_word,
                    last_word,
                    expected_start + first_expected_word,
                    expected_start + max(
                        first_expected_word + 1, len(expected_words)
                    ),
                    "local cell alignment left an ambiguous subsegment",
                ))

    outputs = localized + structural
    if resolved_equal_cells and outputs:
        outputs[0]["resolved_equal_cells"] = [
            asdict(cell) for cell in resolved_equal_cells
        ]
        outputs[0]["resolved_equal_pairs"] = resolved_equal_pairs
    return outputs


def localize_diff_records(diff_records, word_provenance, source_tokens=None):
    """Derive concise cell issues while retaining the original diff records."""
    issues = []
    for diff_record in diff_records:
        start = diff_record.get("actual_start_idx")
        end = diff_record.get("actual_end_idx")
        expected_words = diff_record.get("expected", "").split()
        actual_words = diff_record.get("actual", "").split()
        if start is None or end is None:
            continue

        # A one-word replacement is the precise path.  Equal cell opcodes are
        # intentionally omitted by _localized_word_issues.
        if len(expected_words) == 1 and len(actual_words) == 1 and end - start == 1:
            issues.extend(_localized_word_issues(
                expected_words[0], word_provenance[start], actual_words[0], diff_record,
                source_tokens[diff_record.get("expected_start_idx")]
                if source_tokens and diff_record.get("expected_start_idx") is not None
                and diff_record.get("expected_start_idx") < len(source_tokens) else None,
            ))
            continue

        # For broad records, align words first.  Only localized word pairs or
        # inserted/deleted words are emitted; unresolved ranges become one
        # concise structural review record.
        expected_start = diff_record.get("expected_start_idx", 0)
        # Only exact word runs are anchors.  Existing equivalences remain in
        # the normal CellIssue path; reusing them here could hide a real red
        # mismatch when source-token indexing is shifted by a broad parent.
        matcher = difflib.SequenceMatcher(
            None, expected_words, actual_words, autojunk=False
        )
        localized = []
        structural = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                continue
            actual_slice = word_provenance[start + j1:start + j2]
            if tag == "replace" and (i2 - i1) == (j2 - j1):
                for offset in range(j2 - j1):
                    localized.extend(_localized_word_issues(
                        expected_words[i1 + offset], actual_slice[offset],
                        actual_words[j1 + offset], diff_record,
                        source_tokens[diff_record.get("expected_start_idx", 0) + i1 + offset]
                        if source_tokens and diff_record.get("expected_start_idx") is not None
                        and diff_record.get("expected_start_idx") + i1 + offset < len(source_tokens)
                        else None,
                    ))
            elif tag == "insert":
                for offset, word_prov in enumerate(actual_slice):
                    localized.append(_make_issue(
                        "insertion", [], word_prov, actual_words[j1 + offset], diff_record
                    ))
            elif tag == "delete":
                for word in expected_words[i1:i2]:
                    previous = word_provenance[start - 1][-1] if start > 0 and word_provenance[start - 1] else None
                    next_cell = word_provenance[start][0] if start < len(word_provenance) and word_provenance[start] else None
                    localized.append(_make_issue("deletion", list(word), [], word, diff_record, previous, next_cell))
            else:
                unresolved_expected = expected_words[i1:i2]
                unresolved_actual_start = start + j1
                unresolved_actual_end = start + j2
                for page_start, page_end in _page_segments(
                        word_provenance, unresolved_actual_start,
                        unresolved_actual_end):
                    page_offset_start = page_start - unresolved_actual_start
                    page_offset_end = page_end - unresolved_actual_start
                    locally_aligned = _local_structural_alignment(
                        unresolved_expected,
                        actual_words[j1 + page_offset_start:j1 + page_offset_end],
                        word_provenance,
                        expected_start + i1,
                        page_start,
                        page_end,
                        diff_record,
                        source_tokens,
                    )
                    if locally_aligned is not None:
                        structural.extend(locally_aligned)
                    else:
                        structural.append(_structural_segment(
                            unresolved_expected, actual_words[j1:j2],
                            word_provenance, expected_start + i1,
                            page_start, page_end, diff_record,
                            "bounded word alignment was not reliable",
                        ))

        issues.extend(localized)
        issues.extend(structural)
    return issues

def resolve_mismatch_provenance(diff_record, word_provenance):
    """
    Accepts a diff record and word_provenance list, and resolves actual-side provenance.
    
    For REPLACE, performs secondary cell-level alignment inside the word range for precise resolution.
    For INSERT, returns coordinates of inserted actual cells.
    For DELETE, returns a gap object with neighbors.
    """
    actual_start = diff_record.get("actual_start_idx")
    actual_end = diff_record.get("actual_end_idx")
    diff_type = diff_record.get("type")
    expected_segment = diff_record.get("expected", "")

    # If it's a deletion or actual slice is empty
    if actual_start == actual_end or diff_type == "deletion":
        prev_cell = None
        if actual_start > 0:
            prev_word = word_provenance[actual_start - 1]
            if prev_word:
                prev_cell = prev_word[-1]
        next_cell = None
        if actual_start < len(word_provenance):
            next_word = word_provenance[actual_start]
            if next_word:
                next_cell = next_word[0]
        return {
            "kind": "gap",
            "previous": prev_cell,
            "next": next_cell
        }

    # For INSERT
    if diff_type == "insertion":
        cells = []
        for idx in range(actual_start, actual_end):
            cells.extend(word_provenance[idx])
        return {
            "kind": "insertion",
            "cells": cells
        }

    # A broad word-level replacement cannot be localized safely by aligning
    # all cells across the complete multi-word segment.  The returned cells
    # identify the honest actual PDF range participating in the mismatch; they
    # are not claims that every cell in the range is independently erroneous.
    expected_word_count = len(expected_segment.split())
    actual_word_count = actual_end - actual_start
    if diff_type == "structural_mismatch" or expected_word_count != 1 or actual_word_count != 1:
        cells = []
        for idx in range(actual_start, actual_end):
            cells.extend(word_provenance[idx])
        return {
            "kind": "full_range",
            "cells": cells
        }

    # For a single-word replacement, use secondary cell-level alignment for
    # precise provenance.
    actual_cells_prov = []
    for idx in range(actual_start, actual_end):
        actual_cells_prov.extend(word_provenance[idx])

    actual_cells_chars = [p.unicode_cell for p in actual_cells_prov]
    expected_cells_chars = [c for c in expected_segment if not c.isspace()]

    # Run cell-level alignment
    matcher = difflib.SequenceMatcher(None, expected_cells_chars, actual_cells_chars)
    opcodes = matcher.get_opcodes()

    resolved_parts = []
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == 'equal':
            continue
        if tag == 'replace' or tag == 'insert':
            resolved_parts.append({
                "kind": "cell_" + tag,
                "cells": actual_cells_prov[j1:j2]
            })
        elif tag == 'delete':
            prev_cell = actual_cells_prov[j1 - 1] if j1 > 0 else None
            next_cell = actual_cells_prov[j1] if j1 < len(actual_cells_prov) else None
            if prev_cell is None and actual_start > 0:
                prev_word = word_provenance[actual_start - 1]
                if prev_word:
                    prev_cell = prev_word[-1]
            if next_cell is None and actual_end < len(word_provenance):
                next_word = word_provenance[actual_end]
                if next_word:
                    next_cell = next_word[0]
            resolved_parts.append({
                "kind": "cell_delete",
                "previous": prev_cell,
                "next": next_cell
            })

    if len(resolved_parts) == 1:
        return resolved_parts[0]
    
    # If there are multiple different edit operations, return a multi-cell replacement
    # containing all actual mismatched cells in the opcodes.
    all_cells = []
    for tag, i1, i2, j1, j2 in opcodes:
        if tag != 'equal':
            all_cells.extend(actual_cells_prov[j1:j2])
    
    if all_cells:
        return {
            "kind": "replacement",
            "cells": all_cells
        }

    return {
        "kind": "replacement",
        "cells": actual_cells_prov
    }
