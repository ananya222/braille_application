# Chapter 1 Stabilization Audit

This report is a regression audit only.  No production rule depends on the
document name, page number, source offsets, block IDs, span count, or BRF
fragments listed here.

## Cell-count investigation

The historical count is exactly reproducible by disabling the generic Rule 14
script-token normalization:

| Measurement | Cells |
| --- | ---: |
| Previous count reproduced with script normalization disabled | 34,959 |
| Current expected stream | 33,744 |
| Difference | 1,215 |
| Simple numeric subscript normalization | 1,190 |
| Simple numeric superscript normalization | 12 |
| Negative superscript normalization | 13 |
| **Unexplained cell loss** | **0** |

Additional controls show that collection numeric-sign suppression accounts for
285 cells and superscript-terminator calibration adds 2 cells.  Those controls
are unchanged between the old and current counts; the full 1,215-cell delta is
the generic Rule 14 script normalization.  It replaces the previous candidate
stream's extra script/numeric cells with the cited simple-script cells.

## Fourteen former UEB differences

All 14 are insertions with no expected source cells.  Each actual slice
contains a numeric-sign cell (`3456`) at an alignment-sensitive BRF line
boundary.  They are therefore classified as `REVIEW_REQUIRED`, not as
standards-proven UEB errors.

| # | Source page | BRF page | Block | Source text | Expected | Actual canonical dots | Context | Rule/citation | Classification |
|---:|---:|---:|---:|---|---|---|---|---|---|
| 1 | 2 | 2 | 22 | Example 1 Let A be the set of all students of a boys school. Show that the relation R | ∅ | `3456 145` | UEB prose; line-end numeric-sign insertion | UEB_RULE_001; UEB 2024 §10, pp. 113–140 | REVIEW_REQUIRED |
| 2 | 2 | 2 | 34 | `[[*ts*]]a R b if and only if b = a + 1[[*te*]]` by many authors. We may also use this notation, as and when convenient. | ∅ | `15 3456` | UEB prose; line-end numeric-sign insertion | UEB_RULE_001; UEB 2024 §10, pp. 113–140 | REVIEW_REQUIRED |
| 3 | 5 | 5 | 5 | of this subset are odd. Similarly, all the elements of the subset `[[*ts*]]{2, 4, 6}[[*te*]]` are related to | ∅ | `3456 1 14` | UEB prose; line-end numeric-sign insertion | UEB_RULE_001; UEB 2024 §10, pp. 113–140 | REVIEW_REQUIRED |
| 4 | 6 | 6 | 10 | `[[*ts*]]R = {(a, b) : \|a − b\| is even}[[*te*]]`, is an equivalence relation. Show that all the | ∅ | `3456 1 124` | UEB prose; line-end numeric-sign insertion | UEB_RULE_001; UEB 2024 §10, pp. 113–140 | REVIEW_REQUIRED |
| 5 | 6 | 6 | 30 | (iv) Reflexive and transitive but not symmetric. | ∅ | `3456 1 1245` | UEB prose; line-end numeric-sign insertion | UEB_RULE_001; UEB 2024 §10, pp. 113–140 | REVIEW_REQUIRED |
| 6 | 7 | 7 | 27 | where we finished earlier. In this section, we would like to study different types of | ∅ | `3456 12 245` | UEB prose; line-end numeric-sign insertion | UEB_RULE_001; UEB 2024 §10, pp. 113–140 | REVIEW_REQUIRED |
| 7 | 10 | 10 | 15 | only one element. Therefore, the range set can have at the most two elements of the | ∅ | `3456 12 124` | UEB prose; line-end numeric-sign insertion | UEB_RULE_001; UEB 2024 §10, pp. 113–140 | REVIEW_REQUIRED |
| 8 | 11 | 11 | 38 | (C) f is one-one but not onto (D) f is neither one-one nor onto. | ∅ | `3456 14 245` | UEB prose; line-end numeric-sign insertion | UEB_RULE_001; UEB 2024 §10, pp. 113–140 | REVIEW_REQUIRED |
| 9 | 12 | 12 | 30 | function f to be invertible by showing that f is one-one and onto, specially when the | ∅ | `3456 14 12` | UEB prose; line-end numeric-sign insertion | UEB_RULE_001; UEB 2024 §10, pp. 113–140 | REVIEW_REQUIRED |
| 10 | 14 | 14 | 18 | Example 23 Let `[[*ts*]]A = {1, 2, 3}[[*te*]]`. Then show that the number of relations containing | ∅ | `3456 14 1245` | UEB prose; line-end numeric-sign insertion | UEB_RULE_001; UEB 2024 §10, pp. 113–140 | REVIEW_REQUIRED |
| 11 | 14 | 14 | 30 | Example 24 Show that the number of equivalence relation in the set `[[*ts*]]{1, 2, 3}[[*te*]]` containing | ∅ | `3456 14 125` | UEB prose; line-end numeric-sign insertion | UEB_RULE_001; UEB 2024 §10, pp. 113–140 | REVIEW_REQUIRED |
| 12 | 15 | 15 | 14 | Miscellaneous Exercise on Chapter 1 | ∅ | `3456 145 245` | UEB prose; line-end numeric-sign insertion | UEB_RULE_001; UEB 2024 §10, pp. 113–140 | REVIEW_REQUIRED |
| 13 | 16 | 16 | 15 | Empty relation is the relation R in X given by `[[*ts*]]R = φ ⊂ X × X[[*te*]]`. | ∅ | `3456 145 12` | UEB prose; line-end numeric-sign insertion | UEB_RULE_001; UEB 2024 §10, pp. 113–140 | REVIEW_REQUIRED |
| 14 | 17 | 17 | 8 | Gregory (1636-1675) in his work “Vera Circuli et Hyperbolae Quadratura” | ∅ | `3456 145 145` | UEB prose; line-end numeric-sign insertion | UEB_RULE_001; UEB 2024 §10, pp. 113–140 | REVIEW_REQUIRED |

Result: unclassified differences `0`; standards-proven definite UEB errors `0`.

## REVIEW clustering

| Review reason | Count |
| --- | ---: |
| Unsupported notation/calibration | 133 |
| Figure/indexed prose (textual indexed prose still REVIEW) | 39 |
| Unsupported script complexity | 12 |
| **Current REVIEW regions** | **184** |

The four genuinely non-textual figure placeholders are now represented as
`EXCLUDED_OUT_OF_SCOPE` by generic `UEB_SCOPE_001` handling. They are not
claimed as PASS and do not create definite errors. Thus the original review
accounting is preserved as 184 REVIEW + 4 explicit exclusions = 188 regions.

### Unsupported notation/calibration subclusters

The original 133 `NEMETH_RULE_003` regions were partitioned before any new
implementation was considered. The partition is based on source constructs,
not on Chapter 1 identifiers or offsets.

| Generic construct subcluster | Count | Governing standards area | Current disposition |
| --- | ---: | --- | --- |
| Function/definition punctuation | 116 | Nemeth 18; related punctuation/context in Nemeth 8.2 and 20.1 | REVIEW; complete applicability and independent cell oracle still required |
| Indexed symbol/function subscript | 8 | Nemeth 14.6–14.8 and function interactions in 18 | REVIEW; simple numeric scripts are implemented, these context-dependent forms are not |
| Fraction or slash notation | 3 | Nemeth 13 and related operations/grouping in 20 | REVIEW; fraction hierarchy/termination is not yet complete |
| Ellipsis/punctuation | 2 | Nemeth 8.2.4 and 20.1 | REVIEW; context-dependent punctuation remains unsourced for promotion |
| Other technical notation | 4 | Nemeth Rules 1, 8, 19 and 23 as applicable | REVIEW; requires construct-specific source review |
| **Total** | **133** |  |  |

### Remaining script-complexity subclusters

The 12 script-complexity regions are construct-based: 10 involve square
bracket/grouping interaction with numeric context (Nemeth Rule 19 plus Rule 3),
one is a letter subscript (`ⱼ`), and one is an indexed modifier (`R_*`). A
direct square-bracket mapping was deliberately reverted after interaction
tests produced 15 Nemeth mismatches. These cases remain REVIEW rather than
being calibrated against Duxbury output.

Top patterns include `f :` (35), numeric subscript `₁` (23), coordinate-like
`(1,` (14), bracket/radical markers (11), `f(x)` (9), and indexed/function
forms such as `f(x₁)` (7).  These remain review-only because the complete
applicability and physical-cell behaviour has not yet been independently
implemented and tested.

## Dispatcher audit

| Route | Chapter 1 observations | Failures |
| --- | ---: | ---: |
| Prose → UEB candidate | 481 blocks | 0 |
| Number in prose → UEB numeric | 79 blocks | 0 |
| Math → Nemeth candidate | 358 spans | 0 |
| UEB/Nemeth boundary → switching | 260 mixed blocks | 0 |
| Number in math → Nemeth numeric | 223 spans | 0 |
| Script → Nemeth scripts | 54 spans | 0 |
| Fraction → Nemeth fraction/review | 16 spans | 0 |
| Radical → Nemeth radical/review | 0 spans | 0 |
| Relation → Nemeth comparison | 159 spans | 0 |
| Operator → Nemeth operations | 92 spans | 0 |

The same dispatcher paths were exercised with synthetic non-regression inputs
for unseen fractions, nested fractions, different scripts, scripted groups,
fraction/script combinations, radicals, embedded math, capitalization and
contraction interaction, and UEB numbers followed by letters.

## GUI backend boundary

The GUI can call:

```python
from braille_app.validation.api import validate_document

result = validate_document(master_path, braille_path)
```

The returned `ValidationResult` contains immutable `errors`, `reviews`,
`exclusions`, `statistics`, and per-page counts. Each `ValidationIssue` carries an issue ID,
status, category, rule ID, standards document/rule/page, source page, BRF page,
block ID, source text, canonical expected/actual cells, alignment span, and
explanation.  Layout-only, spacing-only, and encoding-only differences are
kept out of GUI error/review lists; non-provable numeric-sign insertions are
returned as `REVIEW_REQUIRED`.

## Phase 7 accounting

| State | Count |
| --- | ---: |
| PASS | 0 newly promoted from the unresolved review set |
| Definite ERROR | 0 |
| REVIEW | 184 |
| EXCLUDED_OUT_OF_SCOPE | 4 |
| Original review regions accounted for | 188 |

No document-specific rule was added. The production-code hardcoding scan found
no Chapter 1 filename, page number, fixed offset, block ID, expression,
358-span count, or BRF fragment affecting rule behavior.
