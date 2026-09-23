# English-letter/grouping pass — partial promotion

## Existing implementation audit

| Provision | Existing support | This pass |
| --- | --- | --- |
| 6.3.1 single-letter criteria | No source-context verifier; candidate table only | Typed decision; scoped whole-record proof |
| 6.4.8 both grouping contacts | Simple candidate cells already correct | Independent AST/cell equality permits dispatch |
| 6.4.9 one-sided contact | No generic effective-neighbor resolver | Typed decisions tested; mixed-source promotion deferred |
| 6.4.5 / 3.5.1 enclosed lists | Incomplete list/punctuation context | Explicit resolved-list predicate tested; list serialization not promoted |
| 6.4.7 comparisons | Candidate only | Typed suppression tested; general comparison/source routing deferred |
| 19.1.1 ordinary parentheses | Existing candidate mapping correct for accepted grammar | Exact source grouping proof |
| Square brackets | Existing candidate differs from normal Rule 19 cells | REVIEW retained; no new table mapping |
| 6.4.2 named functions | Other dependency | Out of scope; errata clarification inspected |

## Governing source

Nemeth 2022 §§6.3–6.4 were read in full (printed 6-6–6-15, PDF 91–100).
Relevant grouping signs and §§19.1.1–19.1.2 (19-1–19-4, PDF 253–256), enclosed
list definition and exclusions §§3.5.1–3.5.4 (3-15–3-19, PDF 42–46), and per-letter
capitalization §§5.1–5.3 (5-1–5-2, PDF 84–85) were checked. October 2025 errata
Rule 6.4.2 (printed p.8/PDF p.12) clarifies named-function terminology and is not
a rule for arbitrary single-letter applications. The errata contains no Rule 19
amendment or change to 6.4.8/6.4.9. Rendered PDF pages 99–100 were used to inspect
the one-/two-sided distinction and official examples.

## Promoted rule and structure

`NEMETH_LETTER_GROUP_001` operates on LetterNode, GroupNode, and syntactic FunctionCallNode
(single-letter callee, not a Rule 18 function name). Full metadata lives in the
runtime catalog. Regular unmodified letters, baseline Nemeth context, balanced
ordinary grouping, and exact candidate equality are required. The full source
record must parse; no partial-prefix replacement is allowed. Capitals remain
per-letter, and both-sided grouped letters omit the English-letter indicator.
A callee touching an opening group is not single under §6.3.1.

Dependencies: Rules 5, 6 and 19. §6.4.8 is the specific non-use provision overriding
the general §6.3.1 criterion. No state transition is introduced; proof ends at the
math record. Exclusions: numbers, scripts, fractions, punctuation/lists, narrative
words, named functions, typeforms, modified/enlarged/mixed grouping and any attached
outer prose token or punctuation. Source-marker/record order must agree exactly.

Improvement is **dispatcher/context coverage**, not a translation correction.
All candidate Braille cells, source math records, spacing and raw differences
remain identical. The existing broad gap predicate remains in place for every
unproved record. Mismatched candidates stay REVIEW rather than being silently
corrected or certified.

## Canary iterations

1. Unrestricted whole-math-record proof would resolve 3 blocks, but the block
   containing an outer question mark exposed one unrelated mismatch. It was
   tested only in memory and rejected; no unsafe production promotion retained.
2. Added a generic unresolved-boundary exclusion for all attached non-whitespace
   prose/punctuation (not a special case for '?'). Resolved 2 blocks
   with zero new classified mismatches. This gate was promoted.

## Delta

| Metric | Before | After |
| --- | ---: | ---: |
| Raw discrepancies | 772 | 772 |
| REVIEW blocks | 184 | 182 |
| Letter-containing grouping REVIEW bucket | 107 | 105 |
| Classified UEB/Nemeth errors | 0 | 0 |
| Missing inner spaces | 0 | 0 |
| Switches, each direction | 358 | 358 |
| Exclusions | 4 | 4 |
| Unaligned | 0 | 0 |
| Baseline corruption | 5/5 | 5/5 |

The grouping bucket is defined by letters adjacent to/inside grouping in any
math record of a REVIEW block; it is an audit inventory, not a production trigger.
It overlaps other families and is broader than the historical 52-parenthesis bucket.
Exactly 103 remaining bucket blocks carry at least one punctuation,
script/index, or fraction blocker. Individual counts overlap:

| Blocker | Blocks |
| --- | ---: |
| attached outer prose/punctuation dependency | 81 |
| fraction dependency | 13 |
| internal punctuation/list dependency | 80 |
| numeric context dependency | 59 |
| outside whole-record letter/group grammar | 103 |
| script/index dependency | 36 |

### Exact resolved Chapter 1 blocks

- Source page 15, block 21: 3. Given a non empty set X, consider [[*ts*]]P(X)[[*te*]] which is the set of all subsets of X.
- Source page 15, block 22: Define the relation R in [[*ts*]]P(X)[[*te*]] as follows:

## Tests and safeguards

- Official subexpression oracles: examples 6-42 (a), 6-43 [x], 6-44 P(A),
  19-29 f(x). The rest of those examples is not claimed as implemented.
- Synthetic full-cell oracles: q(z), H(B), (m), q(H(B)).
- Typed one-sided cases from 6-44/6-45/6-46, required standalone indicator from
  6-8, enclosed-list suppression from 6-23, negative unknown/typeform contexts.
- Candidate-cell corruption causes REVIEW in the proof checker, not a false PASS.
- P(X) followed by outer punctuation, f(1)=1, tuples, scripts, fractions and
  named functions remain excluded. Registry removal disables promotion.
- Production pipeline tests, ten-family existing detector checks, spacing
  canaries, experimental selftest, and clean/corrupted offscreen Qt workflow pass.
  The old extended detector tests only assert detection, not independent standards
  correctness of each mutated family.
- Broken-switch detection remains 17 records for one injected fault; unchanged,
  not treated as 17 independent corruptions. No cascade/classifier changes.
- GUI/serializer/highlighter/alignment files unchanged in this pass. The existing
  PDF fixture was read for diagnostics, not regenerated or visually recertified.
  Historical phase8b PDF tests and phase7c tests retain their historical baselines
  and are not included in this pass's test result.

## Accounting and safety

The earlier 41-record arithmetic residual is not a set of 41 identifiable error
records: 715 counts missing boundary blanks while 1446 and 772 count alignment
opcodes. Realignment split/merged/reclassified intervals. This pass preserves the
post-spacing ledger unchanged, with all 772 records regenerated in the JSON.
No source/BRF modification, raw discrepancy suppression, fixture-specific rule,
or Duxbury-as-authority inference was used. Literal fixture paths, pages and block
IDs appear only in regression/report code. Runtime scan found no Chapter 1/count
conditions; source offsets are used solely to check actual structural boundaries,
not fixed document coordinates. Full standards certification is still not claimed.

**PARTIALLY PROMOTED — SOME CONTEXTS REMAIN REVIEW**
