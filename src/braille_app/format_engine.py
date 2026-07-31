import re
import difflib
from typing import List, Dict, Any, Union, Optional
from braille_app.diff_engine import DiffEngine

# =====================================================================
# DEFAULT BANA FORMATTING CONFIGURATION
# =====================================================================
# Rules marked "ASSUMED" need manual verification against BANA Braille Formats.
DEFAULT_BANA_CONFIG = {
    # Spacing Rules
    "h1_blank_lines_before": 2,      # ASSUMED — needs verification against BANA Braille Formats
    "h2_blank_lines_before": 1,      # ASSUMED — needs verification against BANA Braille Formats
    "h3_blank_lines_before": 1,      # ASSUMED — needs verification against BANA Braille Formats
    
    # Indentation Rules (1-based cell positions: cell 1 = 0 spaces, cell 3 = 2 spaces)
    "paragraph_first_indent": 3,     # SOURCED — Standard literary paragraph start
    "paragraph_runover_indent": 1,   # SOURCED — Standard literary paragraph runover
    
    # List Indentation Rules (1-based cell positions)
    "list_valid_starts": [1, 3],     # ASSUMED — needs verification against BANA Braille Formats
    "list_valid_runovers": [3, 5],   # ASSUMED — needs verification against BANA Braille Formats
}

class FormatEngine:
    def __init__(self, config: Dict[str, Any] = None, allowlist: List[Dict[str, Any]] = None):
        self.config = {**DEFAULT_BANA_CONFIG, **(config or {})}
        self.allowlist = allowlist or []
        self.diff_engine_helper = DiffEngine()

    def _parse_brf_layout(self, brf_text: str, expected_blocks: List[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        pages = brf_text.split('\x0c')
        if pages and not pages[-1].strip():
            pages.pop()
            
        paragraphs = []
        for p_idx, page in enumerate(pages, start=1):
            lines = page.splitlines()
            cleaned_lines = []
            
            for line in lines:
                stripped = line.strip()
                if re.match(r'^[ \t]*#?[a-j0-9]+[ \t]*$', line) or re.match(r'^[ \t]*#?[a-j]+[ \t]*$', line):
                    continue
                cleaned_lines.append(line)
                
            current_p_lines = []
            blank_before = 0
            consecutive_blanks = 0
            page_p_count = 0
            
            for line in cleaned_lines:
                if not line.strip():
                    if current_p_lines:
                        page_p_count += 1
                        paragraphs.append(self._build_p_meta(current_p_lines, blank_before, p_idx, page_p_count == 1))
                        current_p_lines = []
                    consecutive_blanks += 1
                    continue
                
                # Resilient paragraph block splitting without empty lines:
                # If a line starts with cell 3, 5, or 7 spacing, or heading prefixes,
                # we split it to preserve distinct block layouts for validation.
                starts_new = False
                indent = len(line) - len(line.lstrip()) + 1
                if current_p_lines:
                    # Paragraph/list transitions or numeric starts
                    if indent in [3, 5, 7] or line.strip().startswith("#"):
                        starts_new = True
                    # Fuzzy match expected headings to split side-positioned headings starting in cell 1
                    elif expected_blocks:
                        line_clean = " ".join(line.split()).strip().lower()
                        for exp_b in expected_blocks:
                            if exp_b.get("type", "").startswith("heading"):
                                exp_text_clean = exp_b.get("text", "").lower()
                                if exp_text_clean in line_clean or line_clean in exp_text_clean:
                                    starts_new = True
                                    break
                        
                if starts_new and current_p_lines:
                    page_p_count += 1
                    paragraphs.append(self._build_p_meta(current_p_lines, blank_before, p_idx, page_p_count == 1))
                    current_p_lines = []
                    blank_before = 0
                    
                if not current_p_lines:
                    blank_before = consecutive_blanks
                    consecutive_blanks = 0
                current_p_lines.append(line)
            
            if current_p_lines:
                page_p_count += 1
                paragraphs.append(self._build_p_meta(current_p_lines, blank_before, p_idx, page_p_count == 1))
                
        return paragraphs

    def _build_p_meta(self, lines: List[str], blank_before: int, page_idx: int, is_first_on_page: bool) -> Dict[str, Any]:
        text = " ".join([l.strip() for l in lines])
        first_line = lines[0]
        first_indent = len(first_line) - len(first_line.lstrip()) + 1
        
        runover_indents = []
        for l in lines[1:]:
            if l.strip():
                runover_indents.append(len(l) - len(l.lstrip()) + 1)
        avg_runover = runover_indents[0] if runover_indents else 1
        
        is_centered = False
        l_stripped = first_line.strip()
        if l_stripped:
            left_spaces = len(first_line) - len(first_line.lstrip())
            right_spaces = max(0, 40 - len(first_line))
            if left_spaces > 2 and abs(left_spaces - right_spaces) <= 4:
                is_centered = True
                
        return {
            "text": text,
            "raw_lines": lines,
            "blank_before": blank_before,
            "first_indent": first_indent,
            "runover_indent": avg_runover,
            "is_centered": is_centered,
            "page_index": page_idx,
            "is_first_on_page": is_first_on_page
        }

    def check_format(self, expected: Union[str, List[Dict[str, str]]], actual_text: str) -> Dict[str, Any]:
        # Parse expected blocks
        if isinstance(expected, list):
            expected_blocks = expected
            for b in expected_blocks:
                b["text"] = " ".join(b.get("text", "").split()).strip()
            expected_paragraphs = [b.get("text", "") for b in expected_blocks]
        else:
            raw_paragraphs = self.diff_engine_helper._clean_and_split_paragraphs(expected)
            expected_blocks = []
            for p in raw_paragraphs:
                btype = "heading1" if p.lower().startswith(("chapter", "section", "heading", "part")) else "body"
                expected_blocks.append({"type": btype, "text": p})
            expected_paragraphs = [b["text"] for b in expected_blocks]

        actual_layouts = self._parse_brf_layout(actual_text, expected_blocks)
        actual_texts = [p["text"] for p in actual_layouts]

        # PROMINENT WARNING BANNER ON RESULTS
        warning_banner = (
            "======================================================================\n"
            " WARNING: FORMATTING COMPLIANCE RULES ARE UNVERIFIED                  \n"
            "   Several rules (heading spacing, list indents) are provisional     \n"
            "   assumptions. Treat layout verification results as PROVISIONAL      \n"
            "   until rules are manual cross-checked against BANA standards.       \n"
            "======================================================================"
        )

        results = {
            "diffs": [],
            "patterns": [],
            "stats": {
                "total_expected_blocks": len(expected_paragraphs),
                "total_actual_paragraphs": len(actual_layouts)
            },
            "provisional_warning": warning_banner
        }

        diffs = []
        needs_review_types = []

        # Find anchors using DiffEngine helper
        anchors = self.diff_engine_helper._find_anchors(expected_blocks, actual_texts, diffs)
        
        # 1. Braille Page numbering check
        pages = actual_text.split('\x0c')
        if pages and not pages[-1].strip():
            pages.pop()
            
        braille_page_nums = []
        from braille_app.brf_parser import braille_number_to_int
        for p_idx, page in enumerate(pages, start=1):
            page_lines = [l.strip() for l in page.splitlines() if l.strip()]
            if page_lines:
                last_line = page_lines[-1]
                match = re.search(r'#([a-j0-9]+)$', last_line)
                if match:
                    val = braille_number_to_int('#' + match.group(1))
                    if val != -1:
                        braille_page_nums.append((p_idx, val))
                        
        last_num = None
        for p_idx, num in braille_page_nums:
            if last_num is not None and num != last_num + 1:
                diffs.append({
                    "type": "braille_page_gap",
                    "expected": f"Page {last_num + 1}",
                    "actual": f"Page {num}",
                    "location": f"page footer on page {p_idx}",
                    "confidence": "high_confidence"
                })
            last_num = num

        # Align expected and actual layouts
        boundaries = [(-1, -1)] + anchors + [(len(expected_paragraphs), len(actual_layouts))]
        pairs = []
        
        for k in range(len(boundaries) - 1):
            i_start, j_start = boundaries[k]
            i_end, j_end = boundaries[k+1]
            
            if i_start != -1:
                pairs.append((i_start, j_start))
                
            exp_slice = expected_paragraphs[i_start + 1 : i_end]
            act_slice = actual_layouts[j_start + 1 : j_end]
            
            slice_pairs = []
            if len(exp_slice) == len(act_slice):
                for idx in range(len(exp_slice)):
                    slice_pairs.append((idx, idx))
            else:
                act_texts = [act_p["text"] for act_p in act_slice]
                temp_matcher = difflib.SequenceMatcher(lambda x: not x.strip(), exp_slice, act_texts)
                for i1, j1, size in temp_matcher.get_matching_blocks():
                    for idx in range(size):
                        slice_pairs.append((i1 + idx, j1 + idx))
            
            matched_exp = {sp[0] for sp in slice_pairs}
            matched_act = {sp[1] for sp in slice_pairs}
            
            # 1. Process paired items only — no missing/extra paragraph layout errors
            for idx_exp, idx_act in slice_pairs:
                pairs.append((i_start + 1 + idx_exp, j_start + 1 + idx_act))

        heading_treatments = {}

        # Run formatting checks on all paired blocks
        for abs_i, abs_j in pairs:
            exp_b = expected_blocks[abs_i]
            act_p = actual_layouts[abs_j]
            
            b_type = exp_b.get("type", "body")
            text = exp_b.get("text", "")
            
            first_indent = act_p["first_indent"]
            runover_indent = act_p["runover_indent"]
            blank_before = act_p["blank_before"]
            is_centered = act_p["is_centered"]
            is_first_on_page = act_p.get("is_first_on_page", False)
            
            # check allowlist
            is_allowed = False
            for allowed in self.allowlist:
                if (allowed.get("expected_type") == b_type and 
                    allowed.get("actual_indent") == (first_indent, runover_indent) and 
                    allowed.get("is_centered") == is_centered):
                    diffs.append({
                        "type": "allowed_format_difference",
                        "expected": f"Type: {b_type}",
                        "actual": f"Indent: {first_indent}, runover: {runover_indent}",
                        "location": text[:30],
                        "confidence": "ignored"
                    })
                    is_allowed = True
                    break
            
            if is_allowed:
                continue
            
            if b_type.startswith("heading"):
                heading_treatments.setdefault(b_type, []).append((first_indent, is_centered))
                
                # BANA exception: if heading is the first block on a page, spacing check is bypassed
                if is_first_on_page:
                    continue
                
                # Heading spacing check using config values
                if b_type == "heading1":
                    expected_lines = self.config["h1_blank_lines_before"]
                    if blank_before < expected_lines:
                        confidence = "high_confidence" if blank_before < (expected_lines - 1) else "needs_review"
                        diff_type = "heading_spacing_error"
                        if confidence == "needs_review":
                            needs_review_types.append(diff_type)
                        diffs.append({
                            "type": diff_type,
                            "expected": f">= {expected_lines} blank lines",
                            "actual": f"{blank_before} blank lines",
                            "location": f"Heading 1: '{text[:25]}...'",
                            "confidence": confidence
                        })
                elif b_type == "heading2":
                    expected_lines = self.config["h2_blank_lines_before"]
                    if blank_before < expected_lines:
                        diffs.append({
                            "type": "heading_spacing_error",
                            "expected": f">= {expected_lines} blank line(s)",
                            "actual": f"{blank_before} blank lines",
                            "location": f"Heading 2: '{text[:25]}...'",
                            "confidence": "high_confidence"
                        })
                elif b_type == "heading3":
                    expected_lines = self.config["h3_blank_lines_before"]
                    if blank_before < expected_lines:
                        diffs.append({
                            "type": "heading_spacing_error",
                            "expected": f">= {expected_lines} blank line(s)",
                            "actual": f"{blank_before} blank lines",
                            "location": f"Heading 3: '{text[:25]}...'",
                            "confidence": "high_confidence"
                        })
                        
            elif b_type == "body" or b_type == "paragraph":
                exp_first = self.config["paragraph_first_indent"]
                exp_runover = self.config["paragraph_runover_indent"]
                if first_indent != exp_first or runover_indent != exp_runover:
                    # Minor variance (within 1 cell width of the starting indent) is flagged as needs_review
                    is_minor = (abs(first_indent - exp_first) <= 1 and runover_indent == exp_runover)
                    confidence = "needs_review" if is_minor else "high_confidence"
                    diff_type = "paragraph_indentation_error"
                    if confidence == "needs_review":
                        needs_review_types.append(diff_type)
                    diffs.append({
                        "type": diff_type,
                        "expected": f"indent {exp_first} (cell {exp_first}), runover {exp_runover} (cell {exp_runover})",
                        "actual": f"indent {first_indent}, runover {runover_indent}",
                        "location": f"Paragraph: '{text[:25]}...'",
                        "confidence": confidence
                    })
                    
            elif b_type.startswith("list"):
                valid_starts = self.config["list_valid_starts"]
                valid_runovers = self.config["list_valid_runovers"]
                if first_indent not in valid_starts or runover_indent not in valid_runovers:
                    diffs.append({
                        "type": "list_indentation_error",
                        "expected": f"start cell in {valid_starts}, runover cell in {valid_runovers}",
                        "actual": f"indent {first_indent}, runover {runover_indent}",
                        "location": f"List item: '{text[:25]}...'",
                        "confidence": "high_confidence"
                    })

        # Heading collapse check
        from collections import Counter
        heading_resolved = {}
        for htype, layouts in heading_treatments.items():
            if layouts:
                modal_layout = Counter(layouts).most_common(1)[0][0]
                heading_resolved[htype] = modal_layout
                
        h_types = list(heading_resolved.keys())
        for idx1 in range(len(h_types)):
            for idx2 in range(idx1 + 1, len(h_types)):
                t1, t2 = h_types[idx1], h_types[idx2]
                if heading_resolved[t1] == heading_resolved[t2]:
                    diffs.append({
                        "type": "heading_level_collapse",
                        "expected": f"distinct indentation/centering for {t1} vs {t2}",
                        "actual": f"both share layout {heading_resolved[t1]}",
                        "location": "document-wide",
                        "confidence": "high_confidence"
                    })

        # 30% Pattern collapse
        total_blocks = len(expected_paragraphs)
        if total_blocks > 0:
            counts = Counter(needs_review_types)
            for diff_type, count in counts.items():
                if count / total_blocks > 0.3:
                    results["patterns"].append({
                        "type": diff_type,
                        "message": f"PATTERN DETECTED: {count} of {total_blocks} blocks ({count/total_blocks*100:.0f}%) show a {diff_type}. Recommend reviewing for allowlist."
                    })
                    diffs = [d for d in diffs if d.get("type") != diff_type]

        results["diffs"] = diffs
        results["stats"]["total_blocks"] = total_blocks
        return results
