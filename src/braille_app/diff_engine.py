import difflib
import re
from collections import Counter
from typing import List, Dict, Any, Union

class DiffEngine:
    def __init__(self, allowlist: List[Dict[str, str]] = None):
        self.allowlist = allowlist or []

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

    def _normalize_braille_stream(self, text: str, strip_page_numbers: bool = False, is_actual: bool = False) -> str:
        """Collapse braille text into a single whitespace-normalized stream, output as Unicode Braille."""
        # If the text already contains Unicode braille dots, work directly in Unicode
        unicode_range = range(0x2800, 0x28FF)
        has_unicode = any(ord(c) in unicode_range for c in text)

        if has_unicode:
            # Already Unicode — just strip the header and normalize whitespace
            if is_actual:
                text = text.lstrip()
                text = re.sub(r'^DBT\s+[\d\.]+\s+[A-Za-z]+\s+', '', text)
            # Replace Unicode braille space (U+2800) with ASCII space for tokenization
            text = text.replace('\u2800', ' ')
            parts: List[str] = []
            for page in text.split('\x0c'):
                for line in page.replace('\r\n', '\n').split('\n'):
                    stripped = line.strip()
                    if stripped:
                        # Skip pure page-number lines after space replacement
                        if strip_page_numbers and re.match(r'^\s*$', stripped):
                            continue
                        parts.append(stripped)
            return ' '.join(' '.join(parts).split()).strip()
        else:
            # ASCII Braille path
            if is_actual:
                text = text.lstrip()
                text = re.sub(r'^DBT\s+[\d\.]+\s+[A-Za-z]+\s+', '', text)
            # Normalize capitalization indicators (DBT uses ., for cap, liblouis uses ,)
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
            # Convert to Unicode Braille for canonical comparison,
            # then replace U+2800 (braille space) with ASCII space so .split() tokenizes correctly
            return self._to_unicode_braille(ascii_stream).replace('\u2800', ' ')

    def _normalize_expected(self, expected: Union[str, List[Dict[str, str]]]) -> str:
        if isinstance(expected, list):
            combined = ' '.join(b.get("text", "") for b in expected)
        else:
            combined = expected
        return self._normalize_braille_stream(combined, strip_page_numbers=False, is_actual=False)

    def _is_allowlisted(self, expected: str, actual: str) -> bool:
        for entry in self.allowlist:
            exp_entry = entry.get("expected", "")
            act_entry = entry.get("actual", "")
            if exp_entry == expected and act_entry == actual:
                return True
            # Full-block allowlist entries may cover a single word-level diff segment.
            exp_words = exp_entry.split()
            act_words = act_entry.split()
            if len(exp_words) == len(act_words):
                mismatches = [(e, a) for e, a in zip(exp_words, act_words) if e != a]
                if len(mismatches) == 1 and mismatches[0] == (expected, actual):
                    return True
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
        # Check allowlist first
        if self._is_allowlisted(exp_segment, act_segment):
            return "allowed_difference", "ignored", 0

        exp_stripped = exp_segment.strip()
        act_stripped = act_segment.strip()

        # Level 3: Insertion / Deletion — one side is completely empty
        if opcode_tag == 'insert' or (not exp_stripped and act_stripped):
            return "insertion", "high_confidence", 3
        if opcode_tag == 'delete' or (exp_stripped and not act_stripped):
            return "deletion", "high_confidence", 3

        # Count differing characters for same-length single words
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
                # Different lengths but same word count → word-level
                return "word_mismatch", "high_confidence", 2

        # Level 2: Word mismatch — same number of words on both sides
        if exp_word_count == act_word_count and exp_word_count > 0:
            return "word_mismatch", "high_confidence", 2

        # Level 4: Structural mismatch — multi-word blocks differ on both sides
        return "structural_mismatch", "high_confidence", 4

    def compare(self, expected: Union[str, List[Dict[str, str]]], actual_text: str) -> Dict[str, Any]:
        # Both streams are normalized to Unicode Braille for canonical comparison
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

        matcher = difflib.SequenceMatcher(None, expected_words, actual_words)
        for tag, w_i1, w_i2, w_j1, w_j2 in matcher.get_opcodes():
            if tag == 'equal':
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

            diffs.append({
                "type": diff_type,
                "severity": severity,
                "expected": exp_segment,
                "actual": act_segment,
                "location": f"word {w_i1 + 1}-{w_i2}",
                "confidence": confidence
            })



        results["diffs"] = diffs
        return results
