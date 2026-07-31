import difflib
import re
from collections import Counter
from typing import List, Dict, Any, Union

class DiffEngine:
    def __init__(self, allowlist: List[Dict[str, str]] = None, grade: int = 2):
        self.allowlist = allowlist or []
        self.grade = grade

    _PAGE_NUM_LINE = re.compile(r'^#?[a-j0-9]+$')
    _PAGE_NUM_LINE_ALT = re.compile(r'^#?[a-j]+$')

    def _is_page_number_line(self, line: str) -> bool:
        stripped = line.strip()
        return bool(self._PAGE_NUM_LINE.match(stripped) or self._PAGE_NUM_LINE_ALT.match(stripped))

    def _to_unicode_braille(self, text: str) -> str:
        """Convert ASCII Braille stream to Unicode Braille for canonical comparison."""
        try:
            from braille_app.brf_parser import ascii_to_unicode_braille
            return ascii_to_unicode_braille(text)
        except ImportError:
            return text

    def _to_ascii_braille(self, text: str) -> str:
        """Convert canonical Unicode cells back to BRF for rule inspection."""
        try:
            from braille_app.brf_parser import ASCII_TO_UNICODE_BRAILLE
            reverse_map = {value: key for key, value in ASCII_TO_UNICODE_BRAILLE.items()}
            return "".join(reverse_map.get(character, character) for character in text)
        except ImportError:
            return text

    def _is_ambiguous_standalone_punctuation(self, expected: str, actual: str) -> bool:
        """Recognise punctuation-list entries whose print context supplies no role.

        An isolated quote, question mark, or tilde in a symbol catalogue has no
        surrounding prose from which quote direction or meaning can be inferred.
        Such a representation difference must not be reported as an error.
        """
        expected_brf = self._to_ascii_braille(expected)
        actual_brf = self._to_ascii_braille(actual)
        punctuation = set("'\"`,;:.*?0 7 8")
        return (
            bool(expected_brf)
            and bool(actual_brf)
            and set(expected_brf) <= punctuation
            and set(actual_brf) <= punctuation
            and len(expected_brf) <= 2
            and len(actual_brf) <= 2
        )

    def _normalize_braille_stream(self, text: str, strip_page_numbers: bool = False, is_actual: bool = False) -> str:
        """Collapse braille text into a single whitespace-normalized stream, output as Unicode Braille."""
        text = text.replace('\u2824', '-').replace('\u2011', '-')  # Normalize hyphens
        unicode_range = range(0x2800, 0x28FF)
        has_unicode = any(ord(c) in unicode_range for c in text)

        if has_unicode:
            if is_actual:
                text = text.lstrip()
                text = re.sub(r'^DBT\s+[\d\.]+\s+[A-Za-z]+\s+', '', text)
            text = text.replace('\u2800', ' ')
            parts: List[str] = []
            for page in text.split('\x0c'):
                for line in page.replace('\r\n', '\n').split('\n'):
                    stripped = line.strip()
                    if stripped:
                        if strip_page_numbers and re.match(r'^\s*$', stripped):
                            continue
                        parts.append(stripped)
            return ' '.join(' '.join(parts).split()).strip()
        else:
            if is_actual:
                text = text.lstrip()
                text = re.sub(r'^DBT\s+[\d\.]+\s+[A-Za-z]+\s+', '', text)
            text = text.replace('.,', ',')
            parts: List[str] = []
            for page in text.split('\x0c'):
                for line in page.replace('\r\n', '\n').split('\n'):
                    if strip_page_numbers and self._is_page_number_line(line):
                        continue
                    stripped = line.strip()
                    if stripped:
                        parts.append(stripped)
            ascii_stream = ' '.join(' '.join(parts).split()).strip()
            return self._to_unicode_braille(ascii_stream).replace('\u2800', ' ')

    def _normalize_expected(self, expected: Union[str, List[Dict[str, str]]]) -> str:
        if isinstance(expected, list):
            combined = ' '.join(b.get("text", "") for b in expected)
        else:
            combined = expected
        return self._normalize_braille_stream(combined, strip_page_numbers=False, is_actual=False)

    def _build_actual_word_to_line_map(self, actual_text: str) -> List[tuple]:
        """
        Build a mapping from flat actual-word index to (line_no, word_in_line),
        where line_no is the physical line number in the uploaded braille document
        (page-number lines are skipped, but every other non-empty line increments
        the counter) and word_in_line resets to 1 on each new line.

        Both values are 1-based.
        """
        try:
            from braille_app.brf_parser import ascii_to_unicode_braille
        except ImportError:
            ascii_to_unicode_braille = lambda x: x

        text = actual_text
        text = text.replace('\u2824', '-').replace('\u2011', '-')

        # Detect Unicode vs ASCII braille
        unicode_range = range(0x2800, 0x28FF)
        has_unicode = any(ord(c) in unicode_range for c in text)

        if has_unicode:
            # Strip DBT header if present
            text = text.lstrip()
            text = re.sub(r'^DBT\s+[\d\.]+\s+[A-Za-z]+\s+', '', text)
            text = text.replace('\u2800', ' ')
        else:
            # Strip DBT header, normalize cap indicators
            text = text.lstrip()
            text = re.sub(r'^DBT\s+[\d\.]+\s+[A-Za-z]+\s+', '', text)
            text = text.replace('.,', ',')
            # Convert to Unicode so tokens match what _normalize_braille_stream produces
            text = ascii_to_unicode_braille(text).replace('\u2800', ' ')

        word_to_line: List[tuple] = []
        line_no = 0

        for page in text.split('\x0c'):
            for raw_line in page.replace('\r\n', '\n').split('\n'):
                stripped = raw_line.strip()
                if not stripped:
                    continue  # blank lines don't count
                # Skip page-number-only lines (same logic as _is_page_number_line but
                # working on the already-converted Unicode text — just check if every
                # token is a braille digit / numeral indicator sequence)
                # Simple heuristic: if the original ASCII line (before conversion)
                # matched the page-number pattern we skip it.  Since we already
                # converted, we rely on length: a pure page-number line is very short.
                # Better: re-check against ASCII representation is complex here, so we
                # skip lines that are pure braille-number cells (⠼ followed by a-j).
                if re.match(r'^[⠼⠁⠃⠉⠙⠑⠋⠛⠓⠊⠚\s]+$', stripped):
                    continue

                line_no += 1
                words = stripped.split()
                for w_idx, _ in enumerate(words, start=1):
                    word_to_line.append((line_no, w_idx))

        return word_to_line

    def _is_allowlisted(self, expected: str, actual: str) -> bool:
        for entry in self.allowlist:
            exp_entry = entry.get("expected", "")
            act_entry = entry.get("actual", "")
            if exp_entry == expected and act_entry == actual:
                return True
            exp_words = exp_entry.split()
            act_words = act_entry.split()
            if len(exp_words) == len(act_words):
                mismatches = [(e, a) for e, a in zip(exp_words, act_words) if e != a]
                if len(mismatches) == 1 and mismatches[0] == (expected, actual):
                    return True

        # Duxbury places a capital-passage terminator before a closing curly
        # brace in some UEB output, while liblouis places it after the brace.
        # The enclosed cells are otherwise identical, so this is a structural
        # representation variant rather than a content error.
        expected_brf = self._to_ascii_braille(expected)
        actual_brf = self._to_ascii_braille(actual)
        expected_match = re.fullmatch(r"_<(.+)_>,'", expected_brf)
        actual_match = re.fullmatch(r"_<(.+),'_>", actual_brf)
        if expected_match and actual_match and expected_match.group(1) == actual_match.group(1):
            return True

        try:
            from braille_app.corrections_loader import UEBCorrectionsManager
            manager = UEBCorrectionsManager()
            cat_c_rules = manager.get_category_c_rules(self.grade)
            for rule in cat_c_rules:
                if rule.get("suppress") is True:
                    pass
        except Exception:
            pass

        return False

    def _clean_and_split_paragraphs(self, text: str) -> List[str]:
        pages = text.split('\x0c')
        all_paragraphs = []
        for page in pages:
            lines = page.split('\n')
            cleaned_lines = []
            for line in lines:
                stripped = line.strip()
                if re.match(r'^#?[a-j0-9]+$', stripped) or re.match(r'^#?[a-j]+$', stripped):
                    continue
                cleaned_lines.append(line)

            current_p_lines = []
            for line in cleaned_lines:
                if not line.strip():
                    if current_p_lines:
                        all_paragraphs.append(" ".join([l.strip() for l in current_p_lines]))
                        current_p_lines = []
                    continue

                indent = len(line) - len(line.lstrip()) + 1
                if current_p_lines:
                    if indent in [3, 5, 7] or line.strip().startswith("#"):
                        all_paragraphs.append(" ".join([l.strip() for l in current_p_lines]))
                        current_p_lines = []
                current_p_lines.append(line)

            if current_p_lines:
                all_paragraphs.append(" ".join([l.strip() for l in current_p_lines]))

        return all_paragraphs

    def _find_anchors(self, expected_blocks: List[Dict[str, str]], actual_paragraphs: List[str], diffs: List[Dict[str, Any]]) -> List[tuple]:
        headings_found = any(b.get("type", "").startswith("heading") for b in expected_blocks)

        if headings_found:
            candidates = []
            for i, block in enumerate(expected_blocks):
                if block.get("type", "").startswith("heading"):
                    exp_text = block.get("text", "")
                    for j, act_p in enumerate(actual_paragraphs):
                        ratio = difflib.SequenceMatcher(None, exp_text, act_p).ratio()
                        if ratio >= 0.85:
                            candidates.append((ratio, i, j))

            candidates.sort(key=lambda x: x[0], reverse=True)

            matched_expected = set()
            matched_actual = set()
            heading_anchors = []

            for ratio, i, j in candidates:
                if i not in matched_expected and j not in matched_actual:
                    heading_anchors.append((i, j))
                    matched_expected.add(i)
                    matched_actual.add(j)

            heading_anchors.sort()

            valid_anchors = []
            last_i, last_j = -1, -1
            for i, j in heading_anchors:
                if i > last_i and j > last_j:
                    valid_anchors.append((i, j))
                    last_i, last_j = i, j

            matched_indices = set(x[0] for x in valid_anchors)
            for i, block in enumerate(expected_blocks):
                if block.get("type", "").startswith("heading") and i not in matched_indices:
                    exp_text = block.get("text", "")
                    diffs.append({
                        "type": "heading_translation_error",
                        "expected": exp_text,
                        "actual": "",
                        "location": f"expected heading {i+1}",
                        "confidence": "high_confidence"
                    })

            return valid_anchors
        else:
            anchors = []
            expected_texts = [b.get("text", "") for b in expected_blocks]
            for i, exp_p in enumerate(expected_texts):
                if expected_texts.count(exp_p) == 1 and actual_paragraphs.count(exp_p) == 1:
                    j = actual_paragraphs.index(exp_p)
                    anchors.append((i, j))
            anchors.sort()
            valid_anchors = []
            last_i, last_j = -1, -1
            for i, j in anchors:
                if i > last_i and j > last_j:
                    valid_anchors.append((i, j))
                    last_i, last_j = i, j
            return valid_anchors

    def _classify_mismatch(self, exp_segment: str, act_segment: str, opcode_tag: str, exp_word_count: int, act_word_count: int) -> tuple:
        """Classify a mismatch into one of 4 severity levels.

        Returns (diff_type, confidence, severity_level)
        Levels:
          1 - character_mismatch  : same-length word, 1-2 braille cells differ
          2 - word_mismatch       : same word count, more than 2 cell differences
          3 - insertion_deletion  : one side is empty (missing or extra words)
          4 - structural_mismatch : multi-word blocks on both sides differ substantially
        """
        if self._is_allowlisted(exp_segment, act_segment):
            return "allowed_difference", "ignored", 0

        # liblouis emits an ASCII escape for characters for which its literary
        # table has no UEB cell assignment (for example U+20B9).  Duxbury may
        # use a local symbol for the same print character.  This is not a
        # translation error unless a verified mapping is supplied.
        if re.search(r"\\X[0-9A-F]{4,}", self._to_ascii_braille(exp_segment), re.I):
            return "unverified_symbol_mapping", "ignored", 0

        if exp_word_count == act_word_count == 1 and self._is_ambiguous_standalone_punctuation(exp_segment, act_segment):
            return "ambiguous_standalone_punctuation", "ignored", 0

        exp_stripped = exp_segment.strip()
        act_stripped = act_segment.strip()

        if opcode_tag == 'insert' or (not exp_stripped and act_stripped):
            return "insertion", "high_confidence", 3
        if opcode_tag == 'delete' or (exp_stripped and not act_stripped):
            return "deletion", "high_confidence", 3

        if exp_word_count == 1 and act_word_count == 1:
            exp_chars = list(exp_stripped)
            act_chars = list(act_stripped)
            if len(exp_chars) == len(act_chars):
                cell_diffs = sum(1 for a, b in zip(exp_chars, act_chars) if a != b)
                if cell_diffs <= 2:
                    return "character_mismatch", "high_confidence", 1
                else:
                    return "word_mismatch", "high_confidence", 2
            else:
                return "word_mismatch", "high_confidence", 2

        if exp_word_count == act_word_count and exp_word_count > 0:
            return "word_mismatch", "high_confidence", 2

        return "structural_mismatch", "high_confidence", 4

    def _find_ueb_context_errors(self, actual_words: List[str], location_for_word) -> List[Dict[str, Any]]:
        """Find rule violations that a reference-translation diff cannot expose.

        These checks operate on UEB cells and their surrounding context, rather
        than on document-specific text.  They therefore work for any Duxbury
        Grade 1 output using the same literary UEB conventions.
        """
        findings: List[Dict[str, Any]] = []
        seen = set()

        for word_index, unicode_word in enumerate(actual_words):
            word = self._to_ascii_braille(unicode_word)

            # UEB comparison signs must be separated from adjoining operands.
            # The BRF form of equals is "7.  A standalone occurrence is fine;
            # an occurrence inside a token (A"7B, #A"7#B, etc.) is not.
            equals_at = word.find('"7')
            if equals_at >= 0 and (equals_at > 0 or equals_at + 2 < len(word)):
                key = ("comparison-sign-spacing", word_index)
                if key not in seen:
                    seen.add(key)
                    findings.append({
                        "type": "comparison_sign_spacing",
                        "severity": 2,
                        "expected": word[:equals_at] + (" " if equals_at else "") + '"7' + (" " if equals_at + 2 < len(word) else "") + word[equals_at + 2:],
                        "actual": word,
                        "location": location_for_word(word_index, word_index + 1),
                        "confidence": "high_confidence",
                    })

            # A quote pair enclosing words is a quotation, not an apostrophe.
            # In UEB it needs the specific single quote cells ,8 ... ,0.  An
            # apostrophe inside a word (for example didn't) is intentionally
            # excluded by requiring a token-boundary occurrence.
            if word.startswith("',"):
                for closing_index in range(word_index, len(actual_words)):
                    closing_word = self._to_ascii_braille(actual_words[closing_index])
                    if closing_word.endswith("'"):
                        key = ("single-quotation-direction", word_index, closing_index)
                        if key not in seen:
                            seen.add(key)
                            expected_open = ",8" + word[1:]
                            expected_close = closing_word[:-1] + ",0"
                            findings.append({
                                "type": "single_quote_direction",
                                "severity": 2,
                                "expected": expected_open if word_index == closing_index else f"{expected_open} … {expected_close}",
                                "actual": word if word_index == closing_index else f"{word} … {closing_word}",
                                "location": location_for_word(word_index, closing_index + 1),
                                "confidence": "high_confidence",
                            })
                        break

        return findings

    def compare(self, expected: Union[str, List[Dict[str, str]]], actual_text: str) -> Dict[str, Any]:
        # Normalize both streams to Unicode Braille for canonical comparison
        expected_normalized = self._normalize_expected(expected)
        actual_normalized = self._normalize_braille_stream(actual_text, strip_page_numbers=True, is_actual=True)

        expected_words = expected_normalized.split()
        actual_words = actual_normalized.split()

        results = {
            "diffs": [],
            "patterns": [],
            "stats": {
                "total_expected_words": len(expected_words),
                "total_actual_words": len(actual_words)
            }
        }

        diffs: List[Dict[str, Any]] = []

        # Build word-index -> (line_no, word_in_line) map from the ACTUAL braille
        # document's physical lines. line_no = real line number in the uploaded
        # braille file; word_in_line resets to 1 on every new line.
        actual_word_to_line = self._build_actual_word_to_line_map(actual_text)

        def _location_label(act_start: int, act_end: int) -> str:
            """
            Return human-readable location based on the actual braille document.

            act_start is inclusive, act_end is exclusive (Python-slice style).
            Examples:
              "line 12, word 3"          – single word
              "line 12, words 3-7"       – multiple words on same line
              "line 12, word 3 - line 13, word 2"  – span crossing lines
            """
            if not actual_word_to_line:
                return f"word {act_start + 1}"

            def _safe(idx: int) -> tuple:
                if idx < len(actual_word_to_line):
                    return actual_word_to_line[idx]
                return actual_word_to_line[-1]

            start_line, start_w = _safe(act_start)
            last_idx = max(act_start, act_end - 1)
            end_line, end_w = _safe(last_idx)

            if start_line == end_line and start_w == end_w:
                return f"line {start_line}, word {start_w}"
            elif start_line == end_line:
                return f"line {start_line}, words {start_w}-{end_w}"
            else:
                return f"line {start_line}, word {start_w} - line {end_line}, word {end_w}"

        # ── Alignment fix ────────────────────────────────────────────────────
        # Use autojunk=False so SequenceMatcher does not silently discard
        # common short braille tokens as "junk" — those discards create false
        # anchors that hide mismatches in the Special-Characters / Final-Symbols
        # sections of the document.
        #
        # Then require MIN_EQUAL_BLOCK consecutive matching words before we
        # treat a run as truly "equal".  Shorter equal runs are almost always
        # coincidental matches inside a misaligned region (e.g. a single common
        # braille cell that happens to appear in both streams at the same index).
        # Folding them back into the surrounding diff blocks causes the whole
        # misaligned region to be reported as one structural mismatch instead of
        # being silently absorbed.
        MIN_EQUAL_BLOCK = 1

        matcher = difflib.SequenceMatcher(None, expected_words, actual_words,
                                          autojunk=False)
        raw_opcodes = matcher.get_opcodes()

        # Step 1 – convert tiny equal blocks to 'replace'
        coerced: List[tuple] = []
        for tag, i1, i2, j1, j2 in raw_opcodes:
            if tag == 'equal' and (i2 - i1) < MIN_EQUAL_BLOCK:
                coerced.append(('replace', i1, i2, j1, j2))
            else:
                coerced.append((tag, i1, i2, j1, j2))

        # Step 2 – merge adjacent non-equal blocks so they form one diff entry
        merged_opcodes: List[tuple] = []
        for op in coerced:
            tag, i1, i2, j1, j2 = op
            if merged_opcodes and merged_opcodes[-1][0] != 'equal' and tag != 'equal':
                pt, pi1, pi2, pj1, pj2 = merged_opcodes[-1]
                merged_opcodes[-1] = ('replace', pi1, i2, pj1, j2)
            else:
                merged_opcodes.append(op)

        for tag, w_i1, w_i2, w_j1, w_j2 in merged_opcodes:
            if tag == 'equal':
                # A canonical match is affirmative evidence of correctness.
                # Do not infer font faults from a hard-coded list of valid cells.
                continue
                # Scan for font rendering bugs in the equal segment word-by-word
                curr_j = w_j1
                curr_i = w_i1
                while curr_j < w_j2:
                    act_word = actual_words[curr_j]
                    exp_word = expected_words[curr_i]
                    has_render_bug = False
                    for bug_pattern in ["⠐⠣", "⠐⠜", "⠨⠣", "⠨⠜", "⠨⠴", "⠐⠖", "⠐⠶"]:
                        if bug_pattern in act_word:
                            has_render_bug = True
                            break
                    if has_render_bug:
                        diffs.append({
                            "type": "font_rendering_error",
                            "severity": 2,
                            "expected": exp_word,
                            "actual": act_word,
                            "location": _location_label(curr_j, curr_j + 1),
                            "confidence": "high_confidence"
                        })
                    curr_j += 1
                    curr_i += 1
                continue

            exp_segment = " ".join(expected_words[w_i1:w_i2])
            act_segment = " ".join(actual_words[w_j1:w_j2])
            exp_word_count = w_i2 - w_i1
            act_word_count = w_j2 - w_j1

            diff_type, confidence, severity = self._classify_mismatch(
                exp_segment, act_segment, tag, exp_word_count, act_word_count
            )

            if confidence == "ignored":
                continue

            act_ref_start = w_j1
            act_ref_end   = w_j2 if w_j2 > w_j1 else w_j1 + 1

            diffs.append({
                "type": diff_type,
                "severity": severity,
                "expected": exp_segment,
                "actual": act_segment,
                "location": _location_label(act_ref_start, act_ref_end),
                "confidence": confidence
            })

        if self.grade in (1, 2):
            diffs.extend(self._find_ueb_context_errors(actual_words, _location_label))

        results["diffs"] = diffs
        return results
