"""Build and run the separate diverse Case 1/2 end-to-end fixture."""

from __future__ import annotations

import csv
import importlib.util
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

import pdfplumber
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, NameObject

ROOT = Path(__file__).resolve().parents[3]
BASE_SCRIPT = ROOT / "stress_test/final_case1_case2_alphabet_capitalization/scripts/final_combined_closure.py"
OUT = ROOT / "stress_test/final_case1_case2_alphabet_capitalization"
FIXTURE = OUT / "corrupted_diverse_final"
RESULTS = OUT / "results"
MANIFESTS = OUT / "manifests"
PROFILE = "uncontracted_case2_capitalization"

spec = importlib.util.spec_from_file_location("combined_closure", BASE_SCRIPT)
fc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = fc
assert spec.loader is not None
spec.loader.exec_module(fc)

SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from braille_app.translation.braille_cells import char_mask, unicode_to_cells
from braille_app.translation.liblouis_translator import LiblouisTranslator
from braille_app.translation.profiles import UNCONTRACTED_UEB_CASE2
from braille_app.validation.alignment import align_cells
from braille_app.validation.api import validate_document
from braille_app.validation.pdf_annotation_adapter import (
    ProvenanceAlignmentError,
    build_provenance_alignment,
    validation_errors_to_legacy_cell_issues,
)
from braille_app.visual_annotations import visual_issues_from_cell_issues


def semantic_pdf_items(page):
    """Exclude only confirmed DBT ^-control pairs; retain semantic blanks."""
    rows: list[list[int]] = []
    for index, char in enumerate(page.chars):
        if not rows or abs(char["top"] - page.chars[rows[-1][0]]["top"]) > 2.0:
            rows.append([index])
        else:
            rows[-1].append(index)
    masks: list[int] = []
    refs: list[int] = []
    for row in rows:
        row.sort(key=lambda index: page.chars[index]["x0"])
        text = "".join(page.chars[index]["text"] for index in row)
        if re.fullmatch(r"\s+#[A-Z]+", text):
            continue
        while row and page.chars[row[0]]["text"] == " ":
            row.pop(0)
        while row and page.chars[row[-1]]["text"] == " ":
            row.pop()
        if not row:
            continue
        if masks:
            masks.append(0)
            refs.append(-1)
        index = 0
        while index < len(row):
            char = page.chars[row[index]]["text"]
            if char == "^" and index + 1 < len(row) and page.chars[row[index + 1]]["text"] in "127'":
                index += 2
                continue
            masks.append(char_mask(char, "duxbury"))
            refs.append(row[index])
            index += 1
    return masks, refs


def expected_to_brf_refs(expected_page: str, raw_page: str) -> dict[int, tuple[int, int]]:
    expected = unicode_to_cells(expected_page)
    actual, refs = fc._brf_semantic_items(raw_page)
    mapping: dict[int, tuple[int, int]] = {}
    for opcode in align_cells(expected, tuple(actual)):
        if opcode.tag != "equal":
            continue
        for offset in range(opcode.expected_end - opcode.expected_start):
            ref = refs[opcode.actual_start + offset]
            if ref != (-1, -1):
                mapping[opcode.expected_start + offset] = ref
    return mapping


def _word_state(word: str) -> str:
    if word.isupper():
        return "isolated_capital" if len(word) == 1 else "all_cap_word"
    if word[:1].isupper() and any(char.islower() for char in word):
        return "capitalized_word"
    if any(char.isupper() for char in word[1:]):
        return "internal_capital"
    return "lowercase"


def _word_offset(text: str, source_index: int) -> int:
    for match in re.finditer(r"[A-Za-z]+", text):
        if match.start() <= source_index < match.end():
            return source_index - match.start()
    return 0


def _cap_cells(expected_page, translator, pdf_map):
    records = []
    cursor = 0
    for block_index, block in enumerate(expected_page.blocks):
        translated, positions = translator.translate_prose_with_positions(block.source_text)
        cells = unicode_to_cells(translated)
        if translated != block.braille:
            raise AssertionError(f"position translation mismatch: {block.source_text!r}")
        nonindicators = [i for i, mask in enumerate(cells) if mask not in {0, 32, 4}]
        first_letter = min(nonindicators, default=len(cells))
        last_letter = max(nonindicators, default=-1)
        for local, mask in enumerate(cells):
            if mask != 32:
                continue
            expected_index = cursor + local
            if expected_index not in pdf_map:
                continue
            source_index = positions[local]
            word, occurrence = fc._word_at(block.source_text, source_index)
            role = "prefix" if local < first_letter else "terminator" if local > last_letter else "internal"
            records.append({
                "page": expected_page.number,
                "block_index": block_index,
                "expected_index": expected_index,
                "token": word,
                "occurrence": occurrence,
                "source_char_index": source_index,
                "source_char": block.source_text[source_index] if source_index < len(block.source_text) else "",
                "state": _word_state(word) if word else "unknown",
                "role": role,
                "actual_token": pdf_map[expected_index],
                "actual_mask": mask,
                "block_text": block.source_text,
            })
        cursor += len(block.braille) + 1
    return records


def _next_letter(target, targets):
    return next((item for item in targets
                 if item.block_index == target.block_index
                 and item.source_char_index == target.source_char_index + 1
                 and item.token == target.token
                 and item.expected_index == target.expected_index + 1), None)


def _nearest(candidates, used_indices):
    available = [item for item in candidates if item["expected_index"] not in used_indices]
    if not available:
        raise AssertionError("ran out of distinct targets")
    return max(available, key=lambda item: (
        min((abs(item["expected_index"] - index) for index in used_indices), default=10**9),
        -item["expected_index"],
    ))


def _feature_tags(target, block_text, all_words, line_edges, first, last):
    word = target.token
    low = word.lower()
    offset = _word_offset(block_text, target.source_char_index)
    tags = {target.state, "first_letter" if offset == 0 else "middle_letter"}
    if offset == len(word) - 1:
        tags.add("final_letter")
    if len(word) <= 3:
        tags.add("short_word")
    if len(word) >= 8:
        tags.add("long_word")
    if target.occurrence:
        tags.add("repeated_word")
    if offset + 1 < len(word) and word[offset].lower() == word[offset + 1].lower():
        tags.add("repeated_letter")
    if offset and word[offset].lower() == word[offset - 1].lower():
        tags.add("repeated_letter")
    if any(other != low and len(other) >= 3 and other[:2] == low[:2] for other in all_words):
        tags.add("shared_prefix")
    if any(other != low and len(other) >= 3 and other[-2:] == low[-2:] for other in all_words):
        tags.add("shared_suffix")
    if sum(1 for other in all_words if other == low) > 1:
        tags.add("similar_word")
    if target.state != "lowercase":
        tags.add("combined_capitalization")
    if target.actual_token in line_edges[0]:
        tags.add("line_start")
    if target.actual_token in line_edges[1]:
        tags.add("line_end")
    if target.expected_index == first:
        tags.add("physical_page_start")
    if target.expected_index == last:
        tags.add("physical_page_end")
    if target.expected_index in {first, last}:
        tags.add("repeated_region_boundary")
    if target.page == 1 and target.expected_index == first:
        tags.add("document_start")
    if target.page == 50 and target.expected_index == last:
        tags.add("document_end")
    if target.page in {1, 50} and target.expected_index in {first, last}:
        tags.add("page_transition")
    if any(part in block_text.lower() for part in ("hello hello", "abc abc", "test test")):
        tags.add("repeated_region")
    if word and any(c.isupper() for c in word[1:]):
        tags.add("internal_capital_interaction")
    return sorted(tags)


def build_rows(master, expected, translator, pdf_pages, code_map):
    fc._page_pdf_items = semantic_pdf_items
    all_words = {
        match.group(0).lower()
        for page in expected.pages for block in page.blocks
        for match in re.finditer(r"[A-Za-z]+", block.source_text)
    }
    page_data = []
    for expected_page, pdf_page in zip(expected.pages, pdf_pages):
        mapping = fc._expected_to_pdf_tokens(expected_page, pdf_page)
        targets = fc._targets_for_page(expected_page, translator, pdf_page)
        cells = _cap_cells(expected_page, translator, mapping)
        rows: list[list[int]] = []
        for index, char in enumerate(pdf_page.chars):
            if not rows or abs(char["top"] - pdf_page.chars[rows[-1][0]]["top"]) > 2.0:
                rows.append([index])
            else:
                rows[-1].append(index)
        line_edges = (set(), set())
        for row in rows:
            visible = [index for index in row if pdf_page.chars[index]["text"] not in {"^", "1", "2", "7", "'", " "}]
            if visible:
                line_edges[0].add(visible[0])
                line_edges[1].add(visible[-1])
        meaningful = [item.expected_index for item in targets]
        page_data.append({
            "page": expected_page,
            "targets": targets,
            "caps": cells,
            "line_edges": line_edges,
            "first": min(meaningful),
            "last": max(meaningful),
            "mapping": mapping,
        })

    # Allocate 880 letter edits, weighted by page content, plus 120 cap edits.
    letter_total = 880
    base = 4 * len(page_data)
    weight_total = sum(len(item["targets"]) for item in page_data)
    shares = [((letter_total - base) * len(item["targets"]) / weight_total) for item in page_data]
    quotas = [4 + int(value) for value in shares]
    remainder = letter_total - sum(quotas)
    for index in sorted(range(len(shares)), key=lambda i: (shares[i] % 1, -i), reverse=True)[:remainder]:
        quotas[index] += 1

    cap_ops = ["substitution", "insertion", "deletion", "transposition"] * 30
    letter_ops = ["substitution", "insertion", "deletion", "transposition"] * 220
    cap_cursor = letter_cursor = 0
    rows_out = []
    for item, letter_quota in zip(page_data, quotas):
        page = item["page"].number
        targets = item["targets"]
        caps = item["caps"]
        selected_indices: set[int] = set()
        reserved_tokens: set[int] = set()

        if caps:
            if len(caps) < 3:
                raise AssertionError(f"page {page}: fewer than three capital indicators")
            for _ in range(3):
                kind = cap_ops[cap_cursor]
                cap_cursor += 1
                if kind == "insertion":
                    candidates = [target for target in targets
                                  if target.expected_index not in selected_indices
                                  and target.actual_token not in reserved_tokens]
                    target = max(candidates, key=lambda x: (
                        x.state != "lowercase", x.source_char_index > 0, -x.expected_index
                    ))
                    index = target.expected_index
                    record = {
                        **target.__dict__, "operation": kind, "mutation_category": "capitalization",
                        "mutation_subtype": "extra_or_mispositioned_capital_indicator",
                        "code_target": ",", "secondary_token": None,
                        "feature_tags": ["capital_indicator", "extra_capital_indicator",
                                         "wrong_capital_indicator_position" if target.source_char_index else "capital_transition"],
                    }
                    reserved_tokens.add(target.actual_token)
                    selected_indices.add(index)
                else:
                    pool = [cap for cap in caps if cap["actual_token"] not in reserved_tokens]
                    if kind == "transposition":
                        pool = [cap for cap in pool if item["mapping"].get(cap["expected_index"] + 1) is not None
                                and cap["expected_index"] + 1 in {t.expected_index for t in targets}]
                    cap = _nearest(pool, selected_indices)
                    record = {
                        **cap, "operation": kind, "mutation_category": "capitalization",
                        "mutation_subtype": {
                            "substitution": "wrong_capital_indicator_cell",
                            "deletion": "missing_capital_indicator",
                            "transposition": "mispositioned_capital_indicator",
                        }[kind],
                        "code_target": "x" if kind == "substitution" else None,
                        "secondary_token": None,
                        "feature_tags": ["capital_indicator", cap["state"], cap["role"]],
                    }
                    if kind == "transposition":
                        next_index = cap["expected_index"] + 1
                        record["secondary_expected_index"] = next_index
                        record["secondary_token"] = item["mapping"][next_index]
                        selected_indices.add(next_index)
                        reserved_tokens.add(record["secondary_token"])
                        record["feature_tags"].append("wrong_capital_indicator_position")
                    if cap["role"] == "terminator":
                        record["feature_tags"].append("capital_terminator")
                    if cap["state"] == "all_cap_word":
                        record["feature_tags"].append("all_caps_or_passage")
                    if cap["state"] == "internal_capital":
                        record["feature_tags"].append("internal_capital_error")
                    reserved_tokens.add(cap["actual_token"])
                    selected_indices.add(cap["expected_index"])
                record["expected_physical_pdf_char_index"] = record["actual_token"]
                record["secondary_physical_pdf_char_index"] = record.get("secondary_token")
                rows_out.append(record)

        # Always put mutations at the first and last source letters on each page.
        first_target = min(targets, key=lambda x: x.expected_index)
        last_target = max(targets, key=lambda x: x.expected_index)
        forced = [first_target]
        if last_target.expected_index != first_target.expected_index:
            forced.append(last_target)
        chosen = list(forced)
        chosen_expected = {target.expected_index for target in chosen}
        chosen_tokens = {target.actual_token for target in chosen}
        for _ in range(letter_quota - len(chosen)):
            candidates = [target for target in targets
                          if target.expected_index not in chosen_expected
                          and target.actual_token not in chosen_tokens
                          and target.actual_token not in reserved_tokens
                          and target.expected_index not in selected_indices]
            if not candidates:
                raise AssertionError(f"page {page}: unable to fill {letter_quota} letter targets")
            target = max(candidates, key=lambda x: (
                min((abs(x.expected_index - old) for old in chosen_expected | selected_indices), default=10**9),
                -x.expected_index,
            ))
            chosen.append(target)
            chosen_expected.add(target.expected_index)
            chosen_tokens.add(target.actual_token)

        for target in sorted(chosen, key=lambda x: x.expected_index):
            forced_boundary = target in forced
            kind = "substitution" if forced_boundary and target is first_target else "deletion" if forced_boundary else letter_ops[letter_cursor]
            if not forced_boundary:
                letter_cursor += 1
            next_target = _next_letter(target, targets) if kind == "transposition" else None
            if kind == "transposition" and (next_target is None or next_target.actual_token in reserved_tokens | chosen_tokens):
                # This target was included for distribution, not an eligible pair; use a cell substitution.
                kind = "substitution"
            if target.actual_token in reserved_tokens:
                raise AssertionError(f"page {page}: target overlaps a capitalization mutation")
            block_text = item["page"].blocks[target.block_index].source_text
            tagset = _feature_tags(target, block_text, all_words, item["line_edges"], item["first"], item["last"])
            if kind == "substitution":
                subtype = "wrong_repeated_cell" if "repeated_letter" in tagset else "letter_substitution"
            elif kind == "insertion":
                subtype = "repeated_letter_insertion" if "repeated_letter" in tagset else "letter_insertion"
            elif kind == "deletion":
                subtype = "repeated_letter_deletion" if "repeated_letter" in tagset else "letter_deletion"
            else:
                subtype = "adjacent_transposition"
            wrong = next(letter for letter in "zqyxmw" if letter != target.source_char.lower())
            record = {
                **target.__dict__,
                "operation": kind,
                "mutation_category": "alphabet+capitalization" if target.state != "lowercase" else "alphabet",
                "mutation_subtype": subtype,
                "code_target": target.source_char.lower() if kind == "insertion" and "repeated_letter" in tagset else wrong,
                "secondary_token": next_target.actual_token if kind == "transposition" else None,
                "secondary_expected_index": next_target.expected_index if kind == "transposition" else None,
                "secondary_physical_pdf_char_index": next_target.actual_token if kind == "transposition" else None,
                "feature_tags": tagset,
                "expected_physical_pdf_char_index": target.actual_token,
            }
            if kind == "transposition":
                record["secondary_source_char"] = next_target.source_char
            rows_out.append(record)

    if cap_cursor != 120 or letter_cursor != letter_total - 100:
        # The two forced boundary edits on each page are not part of the rotating queue.
        raise AssertionError((cap_cursor, letter_cursor))
    if len(rows_out) != 1000:
        raise AssertionError(f"expected 1000 mutations, got {len(rows_out)}")
    for index, row in enumerate(rows_out, 1):
        row["error_id"] = f"DIV-{index:04d}"
    counts = Counter(row["operation"] for row in rows_out)
    if sum(counts.values()) != 1000:
        raise AssertionError(counts)
    return rows_out


def mutate_pdf(rows, code_map):
    reader = PdfReader(str(fc.PDF))
    by_page = {}
    for row in rows:
        by_page.setdefault(row["page"], []).append(row)
    for page_number, edits in by_page.items():
        page = reader.pages[page_number - 1]
        data = page.get_contents().get_data()
        tokens = fc._code_tokens(data)
        changes = []
        for row in edits:
            token = tokens[row["actual_token"]]
            kind = row["operation"]
            if kind == "substitution":
                changes.append((token.start(1), token.end(1), code_map[row["code_target"]].encode("ascii")))
            elif kind == "insertion":
                code = code_map[row["code_target"]].encode("ascii")
                changes.append((token.start(), token.start(), b"<" + code + b">0.000000"))
            elif kind == "deletion":
                end = token.end()
                following = re.match(rb"\s*[-+0-9.]+", data[end:])
                if following:
                    end += following.end()
                changes.append((token.start(), end, b""))
            elif kind == "transposition":
                other = tokens[row["secondary_token"]]
                changes.extend(((token.start(1), token.end(1), other.group(1)),
                                (other.start(1), other.end(1), token.group(1))))
            else:
                raise AssertionError(kind)
        for start, end, value in sorted(changes, reverse=True):
            data = data[:start] + value + data[end:]
        stream = DecodedStreamObject()
        stream.set_data(data)
        page[NameObject("/Contents")] = stream
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    path = FIXTURE / "final_case1_case2_diverse_1000.pdf"
    with path.open("wb") as output:
        writer.write(output)
    return path


def mutate_brf(rows, expected):
    pages = fc.BRF.read_text(encoding="latin1").split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    by_page = {}
    for row in rows:
        by_page.setdefault(row["page"], []).append(row)
    for page_number, edits in by_page.items():
        lines = pages[page_number - 1].splitlines()
        mapping = expected_to_brf_refs(expected.pages[page_number - 1].flatten(), pages[page_number - 1])
        for row in sorted(edits, key=lambda item: item["expected_index"], reverse=True):
            line_index, column = mapping[row["expected_index"]]
            chars = list(lines[line_index])
            kind = row["operation"]
            if kind == "insertion":
                chars.insert(column, row["code_target"])
            elif kind == "deletion":
                del chars[column]
            elif kind == "substitution":
                chars[column] = row["code_target"].upper()
            elif kind == "transposition":
                other_line, other_column = mapping[row["secondary_expected_index"]]
                if other_line != line_index:
                    raise AssertionError("transposition crosses BRF line")
                chars[column], chars[other_column] = chars[other_column], chars[column]
            lines[line_index] = "".join(chars)
        pages[page_number - 1] = "\n".join(lines)
    path = FIXTURE / "final_case1_case2_diverse_1000.brf"
    path.write_text("\f".join(pages) + "\f", encoding="latin1")
    return path


def write_manifest(rows):
    path = MANIFESTS / "diverse_mutation_manifest.csv"
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value, ensure_ascii=True) if isinstance(value, (list, dict)) else value
                             for key, value in row.items()})
    return path


def blue_box_audit(rows, visuals):
    with pdfplumber.open(str(fc.PDF)) as pdf:
        targets = []
        for row in rows:
            indices = [row["actual_token"]]
            if row.get("secondary_token") is not None:
                indices.append(row["secondary_token"])
            targets.extend((row["page"], pdf.pages[row["page"] - 1].chars[index]) for index in indices)
    boxes = [box for issue in visuals for box in issue.boxes]

    def same(box, page, char):
        return box.page == page and all(
            abs(float(getattr(box, key)) - float(char[source])) < 0.02
            for key, source in (("x0", "x0"), ("x1", "x1"), ("top", "top"), ("bottom", "bottom"))
        )

    hits = sum(any(same(box, page, char) for box in boxes) for page, char in targets)
    non_target = sum(not any(same(box, page, char) for page, char in targets) for box in boxes)
    rounded = [(box.page, round(box.x0, 3), round(box.top, 3), round(box.x1, 3), round(box.bottom, 3)) for box in boxes]
    return {
        "target_cell_slots": len(targets),
        "target_slots_hit": hits,
        "target_slots_missed": len(targets) - hits,
        "blue_box_count": len(boxes),
        "non_target_blue_boxes": non_target,
        "duplicate_blue_boxes": len(rounded) - len(set(rounded)),
    }


def run():
    FIXTURE.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    MANIFESTS.mkdir(parents=True, exist_ok=True)
    master, expected = fc.master_and_expected()
    translator = LiblouisTranslator(UNCONTRACTED_UEB_CASE2)
    with pdfplumber.open(str(fc.PDF)) as pdf:
        original_reader = PdfReader(str(fc.PDF))
        code_map = fc._code_map(original_reader, pdf.pages)
        rows = build_rows(master, expected, translator, pdf.pages, code_map)
        base_cells = sum(sum(mask != 0 for mask in unicode_to_cells(page.flatten())) for page in expected.pages)
        coverage = 0
        for ep, page in zip(expected.pages, pdf.pages):
            mapping = fc._expected_to_pdf_tokens(ep, page)
            coverage += sum(1 for mask, index in zip(unicode_to_cells(ep.flatten()), range(len(unicode_to_cells(ep.flatten()))))
                            if mask != 0 and index in mapping)
        if coverage != base_cells:
            raise AssertionError(f"filtered PDF map covers {coverage}/{base_cells} semantic cells")
    write_manifest(rows)
    corrupted_pdf = mutate_pdf(rows, code_map)
    corrupted_brf = mutate_brf(rows, expected)

    clean_started = time.perf_counter()
    clean = validate_document(master, fc.PDF, profile=PROFILE)
    clean_seconds = time.perf_counter() - clean_started
    started = time.perf_counter()
    result = validate_document(master, corrupted_pdf, profile=PROFILE, retain_pdf_provenance=True)
    runtime = time.perf_counter() - started
    localization_error = None
    visuals = []
    try:
        provenance = build_provenance_alignment(result.pdf_input)
        cell_issues = validation_errors_to_legacy_cell_issues(result, provenance)
        visuals = visual_issues_from_cell_issues(cell_issues)
    except ProvenanceAlignmentError as exc:
        localization_error = str(exc)
    boxes = blue_box_audit(rows, visuals)
    family_counts = Counter(row["mutation_subtype"] for row in rows)
    operation_counts = Counter(row["operation"] for row in rows)
    tag_counts = Counter(tag for row in rows for tag in row["feature_tags"])
    summary = {
        "profile": PROFILE,
        "injected": len(rows),
        "detected": len(result.errors),
        "reviews": len(result.reviews),
        "missed": max(0, len(rows) - len(result.errors)),
        "false_positives_by_count": max(0, len(result.errors) - len(rows)),
        "duplicates": max(0, len(result.errors) - len(set(issue.issue_id for issue in result.errors))),
        "unresolved_injected_mutations": max(0, len(rows) - len(result.errors)),
        "clean": {"errors": len(clean.errors), "reviews": len(clean.reviews), "statistics": clean.statistics,
                  "runtime_seconds": clean_seconds},
        "corrupted_statistics": result.statistics,
        "blue_box_audit": boxes,
        "localization_error": localization_error,
        "operation_counts": dict(sorted(operation_counts.items())),
        "subtype_counts": dict(sorted(family_counts.items())),
        "feature_tag_counts": dict(sorted(tag_counts.items())),
        "runtime_seconds": runtime,
        "pdf": str(corrupted_pdf),
        "brf": str(corrupted_brf),
        "manifest": str(MANIFESTS / "diverse_mutation_manifest.csv"),
    }
    (RESULTS / "diverse_fixture_result.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
