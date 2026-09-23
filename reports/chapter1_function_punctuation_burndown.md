# Phase 7B Function / Definition-Punctuation Burndown

This report tracks the original 116-region cluster. The cluster is a
regression priority, not a source of production-specific rule behavior.

| Iteration | Change | Before | PASS gained | ERROR gained | Still REVIEW |
| --- | --- | ---: | ---: | ---: | ---: |
| Baseline | Existing calibration guard | 116 | 0 | 0 | 116 |
| Inventory | Structural decomposition only | 116 | 0 | 0 | 116 |
| Candidate implementation | Generic Rules 6.3.1/8.5/8.6/18 colon/function path | 116 | 98 | 231 | 18 |
| Reverted | Full BRF regression found 230 Nemeth + 1 UEB mismatch | 116 | 0 | 0 | 116 |

The candidate implementation was removed. It passed focused synthetic checks but
failed the authoritative regression safety requirement, so none of its 98
provisional PASS results are retained.

## Decomposition

| Subcluster | Original count | PASS | ERROR | REVIEW |
| --- | ---: | ---: | ---: | ---: |
| Function application parentheses | 52 | 0 | 0 | 52 |
| Function/mapping definition colon | 40 | 0 | 0 | 40 |
| Set-builder condition colon | 12 | 0 | 0 | 12 |
| Ordered-pair or tuple comma | 9 | 0 | 0 | 9 |
| Definition/colon context | 2 | 0 | 0 | 2 |
| Logical/relation punctuation | 1 | 0 | 0 | 1 |
| **Total** | **116** | **0** | **0** | **116** |

The detailed 116-case inventory is in
`reports/chapter1_function_punctuation_inventory.json` and
`reports/chapter1_function_punctuation_inventory.md`.

## Standards blockers

The governing material was read from the local authoritative PDFs:

- Nemeth 6.3.1, printed page 6-6: single English-letter indicator criteria.
- Nemeth 8.5–8.6, printed pages 8-12 to 8-13: mathematical colon and comma
  ownership, spacing, and punctuation mode.
- Nemeth 18.1–18.5, printed pages 18-2 to 18-6: function names, abbreviated
  forms, spacing, and punctuation.
- Nemeth 19, printed pages 19-1 to 19-13: grouping interactions.
- Nemeth Rule 4 and the October 2025 errata: code-switch ownership and
  attached punctuation at UEB/Nemeth boundaries.

The 18 cases that looked like pure function/definition punctuation also contain
script or fraction constructs. They are therefore dependent on the unresolved
families and were not reclassified in this phase:

- script-dependent: 12
- fraction-dependent: 6

## Final invariant

For the original cluster:

`PASS 0 + ERROR 0 + EXCLUDED_OUT_OF_SCOPE 0 + REVIEW 116 = 116`

No case was suppressed or marked PASS after the regression failure.
