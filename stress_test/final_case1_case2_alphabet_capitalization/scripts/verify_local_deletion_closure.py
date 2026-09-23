"""Replay saved local cell windows; this script never validates the full PDF."""
import json
from dataclasses import asdict
from types import SimpleNamespace

import evaluate_frozen_diverse as audit
from braille_app.validation.alignment import _align_bounded_block
from braille_app.visual_annotations import VisualBox

OUT = audit.BASE / "results/unresolved_twenty_trace"


def replay(row, snapshot):
    page = snapshot["pages"][row["page"] - 1]
    index = row["expected_index"]
    equal = [op for op in page["alignment"] if op["tag"] == "equal"]
    left = max((op["expected_start"] for op in equal if op["expected_start"] < index), default=0)
    right = next((op["expected_end"] for op in equal if op["expected_start"] > index), len(page["expected"]))

    def boundary(position):
        for op in equal:
            if op["expected_start"] <= position <= op["expected_end"]:
                return op["actual_start"] + position - op["expected_start"] - page["actual_offset"]
        for op in page["alignment"]:
            if position == op["expected_start"]:
                return op["actual_start"] - page["actual_offset"]
            if position == op["expected_end"]:
                return op["actual_end"] - page["actual_offset"]
        raise AssertionError((row["error_id"], position))

    aleft, aright = boundary(left), boundary(right)
    raw = page["actual"]
    dropped = {j for i in range(aleft, aright - 1) if tuple(raw[i:i + 2]) in {(24, 2), (24, 54), (24, 4)}
               for j in (i, i + 1)}
    raw_indices = [i for i in range(aleft, aright) if i not in dropped]
    expected = tuple(page["expected"][left:right])
    actual = tuple(raw[i] for i in raw_indices)
    opcodes = _align_bounded_block(expected, actual)
    positions = raw_indices + [aright]
    projected = [{"tag": op.tag, "expected_start": op.expected_start + left, "expected_end": op.expected_end + left,
                  "actual_start": positions[op.actual_start], "actual_end": positions[op.actual_end]}
                 for op in opcodes]
    return {"window": [left, right], "expected": expected, "actual": actual, "opcodes": projected}


def main():
    pre = json.loads((OUT / "pre.json").read_text(encoding="utf-8"))
    post = json.loads((OUT / "post.json").read_text(encoding="utf-8"))
    cases = json.loads((OUT / "twenty_cases.json").read_text(encoding="utf-8"))["cases"]
    original_six = {"DIV-0083", "DIV-0280", "DIV-0283", "DIV-0487", "DIV-0687", "DIV-0888"}
    rows = {row["error_id"]: row for row in pre["manifest"]}
    _, expected_document = audit.fc.master_and_expected()
    results = []
    with audit.pdfplumber.open(str(audit.PDF)) as pdf:
        for error_id in [case["id"] for case in cases] + sorted(original_six):
            row = rows[error_id]
            page = row["page"]
            chars = pdf.pages[page - 1].chars
            if row["operation"] == "insertion":
                finding = next(case["post"]["finding"] for case in cases if case["id"] == error_id)
                target = post["targets"][error_id][1][0]
                target_index = next(i for i, char in enumerate(chars) if all(abs(char[k] - target[k]) < .02 for k in ("x0", "x1", "top", "bottom")))
                run = audit.identical_run(chars, target_index)
                compatible = [candidate for candidate in post["findings"] if audit.identical_insertion_candidate(
                    SimpleNamespace(**candidate), row, [chars[i] for i in run], candidate["provenance"],
                    [VisualBox(**box) for box in candidate["boxes"]])]
                assert len(compatible) == 1 and compatible[0]["issue_id"] == finding["issue_id"]
                results.append({"id": error_id, "result": "insertion_equivalent", "finding": finding["issue_id"]})
                continue
            trace = replay(row, pre)
            expected_cells = pre["pages"][page - 1]["expected"]
            index = row["expected_index"]
            mask = expected_cells[index]
            left, right = index, index + 1
            while left and expected_cells[left - 1] == mask:
                left -= 1
            while right < len(expected_cells) and expected_cells[right] == mask:
                right += 1
            candidates = [op for op in trace["opcodes"] if op["tag"] == "delete" and left <= op["expected_start"] < right
                          and op["expected_end"] == op["expected_start"] + 1]
            assert len(candidates) == 1, (error_id, trace)
            chosen = candidates[0]
            reference = post if error_id in original_six and error_id != "DIV-0280" else pre
            finding = next(candidate for candidate in reference["findings"]
                           if candidate["source_page_number"] == page and not candidate["actual_braille"]
                           and all(candidate["span"][key] == chosen[key] for key in ("expected_start", "expected_end", "actual_start", "actual_end")))
            proof = None
            if error_id == "DIV-0280":
                target = pre["targets"][error_id][1][0]
                target_index = next(i for i, char in enumerate(chars) if all(abs(char[k] - target[k]) < .02 for k in ("x0", "x1", "top", "bottom")))
                cursor = 0
                for block in expected_document.pages[page - 1].blocks:
                    if not block.braille:
                        continue
                    end = cursor + len(block.braille)
                    if cursor <= index < end:
                        break
                    cursor = end + 1
                proof = audit.identical_deletion_candidate(SimpleNamespace(**finding), row, expected_cells, (cursor, end),
                        chars, [target_index], finding["provenance"], [VisualBox(**box) for box in finding["boxes"]])
                assert proof
            else:
                assert chosen["expected_start"] == index, (error_id, chosen)
            results.append({"id": error_id, "result": "deletion_equivalent" if proof else "strict_deletion",
                            "trace": trace, "finding": finding["issue_id"], "proof": proof})
    assert len(results) == 26
    summary = {"cases": 26, "strict_deletions": sum(r["result"] == "strict_deletion" for r in results),
               "insertion_equivalents": sum(r["result"] == "insertion_equivalent" for r in results),
               "deletion_equivalents": sum(r["result"] == "deletion_equivalent" for r in results), "unresolved": 0}
    (OUT / "local_closure.json").write_text(json.dumps({"summary": summary, "cases": results}, indent=2), encoding="utf-8")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
