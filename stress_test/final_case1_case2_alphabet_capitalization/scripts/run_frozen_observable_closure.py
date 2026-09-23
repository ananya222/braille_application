"""One read-only frozen validation, with durable per-action and per-finding evidence."""
import hashlib
import json
import re
from collections import defaultdict

import evaluate_frozen_diverse as audit


def main():
    progress = (audit.fc.ROOT / "reports/autonomous_case1_to_case4_progress.md").read_text(encoding="utf-8")
    frozen = {audit.BASE / path: digest for path, digest in re.findall(r"\| `([^`]+)` \| `([a-f0-9]{64})` \|", progress)}
    assert len(frozen) == 8
    before = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in frozen}
    assert all(before[str(path)] == digest for path, digest in frozen.items())
    result = audit.run()
    after = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in frozen}
    assert before == after
    result["frozen_hashes_before"] = before
    result["frozen_hashes_after"] = after
    owners = defaultdict(list)
    for outcome in result["outcomes"]:
        if outcome.get("issue_id"):
            owners[outcome["issue_id"]].append(outcome)
    shared = [items for items in owners.values() if len(items) > 1]
    groups_valid = all(sum(item["state"] == "correct" for item in items) == 1
                       and all(item["state"] in {"correct", "equivalent_adjacent_deletion"} for item in items)
                       for items in shared)
    physical, policy = result["physical"], result["policy"]
    result["closure_pass"] = (
        result["mutations"] == policy["accepted_mutations"] == 1000
        and policy["unresolved_mutations"] == policy["unrelated_findings"] == 0
        and result["reviews"] == result["duplicate_issue_ids"] == 0
        and physical["invalid_off_region_boxes"] == physical["incorrect_page_boxes"] == physical["duplicate_boxes"] == 0
        and physical["policy_target_slots_satisfied"] == physical["target_cell_slots"]
        and policy["unique_matched_findings"] == result["findings"]
        and result["by_operation"]["substitution"] == {"correct": 338}
        and result["by_operation"]["transposition"] == {"correct": 162}
        and groups_valid
    )
    result["grouped_deletion_findings"] = len(shared)
    path = audit.BASE / "results/frozen_observable_closure.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "closure_pass", "mutations", "findings", "reviews", "runtime_seconds", "duplicate_issue_ids",
        "policy", "states", "by_operation", "physical", "grouped_deletion_findings", "problem_ids")}, indent=2))
    assert result["closure_pass"], f"Frozen gate failed; full evidence saved to {path}"


if __name__ == "__main__":
    main()
