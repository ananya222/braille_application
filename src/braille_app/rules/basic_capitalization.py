"""UEB 8.1.1, 8.3.1-3: narrow word-initial capital prefix verification.

The standard supplies dot 6. Liblouis supplies positions/contraction candidates,
not the decision whether a source capital is required. No generator changes.
"""
from dataclasses import dataclass, replace
import re
from .rule_result import RuleResult
from .sources import UEB_2024
from braille_app.translation.liblouis_translator import LiblouisTranslator
from braille_app.translation.braille_cells import unicode_to_cells

RULE_ID = 'UEB_8'


@dataclass(frozen=True)
class CapitalSite:
    word: str
    source_start: int
    expected_start: int
    uppercase: bool
    following_cell: int
    code: str = 'UEB'


def inspect_block(block, context):
    """Inspect ordinary prose runs before and after verified math passages."""
    prefix_sites, prefix_result = _inspect_prose(block, context)
    if not block.math_records or (prefix_result is not None and prefix_result.status != 'PASS'):
        return prefix_sites, prefix_result
    from braille_app.translation.mixed_translator import (
        translate_marked_text, serialize_nemeth_passage, MathMarkerError,
        START_MARKER, END_MARKER,
    )
    from braille_app.translation.profiles import CONTRACTED_UEB_BANA_NEMETH
    from braille_app.translation.simple_math import expected
    translator = LiblouisTranslator()
    try:
        mixed = translate_marked_text(block.source_text, translator)
    except MathMarkerError:
        return prefix_sites, prefix_result
    # Use exact generated run boundaries, never a search for repeated words.
    if mixed.braille != block.braille:
        return prefix_sites, prefix_result
    sites = []
    result = prefix_result
    source_offset = braille_offset = 0
    safe = True
    for span in mixed.spans:
        if span.kind == 'math':
            canonical = expected(span.source)
            safe = safe and canonical is not None and canonical == span.braille
            source_offset += len(START_MARKER) + len(span.source) + len(END_MARKER)
            braille_offset += len(serialize_nemeth_passage(span.braille, CONTRACTED_UEB_BANA_NEMETH))
            continue
        if safe:
            fragment = replace(block, source_text=span.source, braille=span.braille, math_records=())
            local_sites, local_result = _inspect_prose(fragment, context)
            if local_result is not None and local_result.status == 'PASS':
                sites.extend(replace(site, source_start=source_offset+site.source_start,
                                     expected_start=braille_offset+site.expected_start)
                             for site in local_sites)
                if result is None:
                    result = replace(local_result, source=block.source_text,
                        original_braille=block.braille, corrected_braille=block.braille,
                        original_cells=unicode_to_cells(block.braille),
                        expected_cells=unicode_to_cells(block.braille),
                        corrected_cells=unicode_to_cells(block.braille))
        source_offset += len(span.source)
        braille_offset += len(span.braille)
    return tuple(sites), result


def _inspect_prose(block, context):
    # Restrict mixed blocks to the initial UEB prefix. No inherited state
    # after an unsupported Nemeth passage is inferred.
    text = block.source_text.split('[[*ts*]]', 1)[0]
    if not text.strip():
        return (), None
    words = list(re.finditer(r'[A-Za-z]+', text))
    if not words:
        return (), None
    unsupported = (context.code not in {'UEB','MIXED'} or context.numeric_mode
                   or context.grade1_mode or context.capitalization_mode is not None
                   or context.script_level != 0) or any(sum(c.isupper() for c in w[0]) > 1 or
                      any(c.isupper() for c in w[0][1:]) or
                      (len(w[0]) == 1 and w[0].isupper() and w[0] not in 'AIO')
                      for w in words)
    # Restricted ordinary prose context; no typeforms/modifiers or numeric
    # grade-1 interaction. Lowercase standalone letters are not tested sites.
    restricted = bool(re.search(r'[^A-Za-z .,!?;:\n\r\t]', text))
    # Do not let punctuation or a digit hide an already recognized all-caps
    # or internal-capital exclusion (e.g. "NASA 2").
    if restricted and not any(sum(c.isupper() for c in w[0]) > 1 for w in words):
        return (), None
    translator = LiblouisTranslator()
    cells, positions = translator.translate_prose_with_positions(text)
    if not block.braille.startswith(cells) or len(cells) != len(positions):
        return (), None
    if list(positions) != sorted(positions):
        return (), None
    sites = []
    if not unsupported:
        for word in words:
            value = word[0]
            if len(value) == 1 and value not in 'AIOaio':
                continue
            indexes = [i for i,p in enumerate(positions) if p == word.start()]
            if not indexes:
                continue
            start = indexes[0]
            upper = value[0].isupper() and all(c.islower() for c in value[1:])
            following = start + int(upper)
            if following >= len(cells) or (upper and cells[start] != '⠠'):
                unsupported = True
                break
            if cells[following] in '⠀⠠⠰':
                unsupported = True
                break
            # Candidate-independent capitalization decision, with exact
            # source correspondence to the first letter/contraction.
            if positions[following] != word.start():
                unsupported = True
                break
            sites.append(CapitalSite(value,word.start(),start,upper,ord(cells[following])-0x2800))
    status = 'REVIEW' if unsupported else 'PASS'
    reason = ('Capitalization requires a mode/grade-1 case outside the basic single-capital scope.'
              if unsupported else 'Word-initial single-capital sites mapped in regular UEB prose; dot 6 required only where print is capitalized.')
    result = RuleResult(rule_id=RULE_ID,status=status,source=block.source_text,
        original_braille=block.braille,corrected_braille=block.braille,explanation=reason,
        page=block.source_page,block=block.source_block,standard_area='UEB',family='capitalisation',
        source_document=UEB_2024,source_rule='8.1.1; 8.2.1; 8.3.1-3',source_page='89-90 (PDF 117-118)',
        source_construct='word-initial single capital',original_cells=unicode_to_cells(block.braille),
        expected_cells=unicode_to_cells(block.braille),corrected_cells=unicode_to_cells(block.braille),
        justification='Dot 6 is prescribed by 8.3.1/8.3.2; contractions and position mapping are dependencies, not capitalization authority. The prefix affects the following letter only.')
    return (() if unsupported else tuple(sites)), result


def localized_defect(report, page, block, difference, block_start):
    """Return (kind, actual_start, actual_end), only with equal-cell anchor.

    Missing prefix: highlight the following actual letter/contraction cell.
    This is an insertion-point anchor, not a claim the anchored letter is wrong.
    """
    if block.rule_status == 'REVIEW':
        return None
    actual = report.actual_stream or report.actual_pages[page.number-1]
    for site in block.capital_sites:
        expected_at = block_start + site.expected_start
        if difference.expected_start != expected_at:
            continue
        if site.uppercase and difference.expected == (32,):
            if difference.kind == 'SUBSTITUTION' and len(difference.actual) == 1:
                kind, left, right = 'wrong capital indicator', difference.actual_start, difference.actual_end
                following_actual = right
            elif difference.kind == 'DELETION' and not difference.actual:
                kind = 'missing capital indicator; anchor is the following letter/contraction'
                left, right = difference.actual_start, difference.actual_start+1
                following_actual = left
            else:
                continue
            following_expected = expected_at+1
        elif not site.uppercase and difference.kind == 'INSERTION' and difference.actual == (32,):
            kind, left, right = 'unnecessary capital indicator', difference.actual_start, difference.actual_end
            following_actual, following_expected = right, expected_at
        else:
            continue
        # Prove the anchor belongs to the expected next letter using the
        # existing equal alignment opcode, not a text search or guessed offset.
        anchored = any(op.tag == 'equal' and op.expected_start <= following_expected < op.expected_end
                       and op.actual_start + following_expected - op.expected_start == following_actual
                       for op in report.page_alignments[page.number-1])
        if anchored and following_actual < len(actual) and actual[following_actual] == site.following_cell:
            return kind, left, right
    return None
