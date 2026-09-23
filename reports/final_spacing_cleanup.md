# Final backend cleanup — spacing fixed, backend frozen

## Root cause and trace

Explicit source markers → translated math record → `MixedTranslation.spans` →
direct `switch_start + payload + switch_end` concatenation → expected block →
rule verification → canonical comparison. The old switching verifier checked
pair counts, not inner separation. No grouping/function/token join caused these
defects. No canonicalization stripped these missing spaces: they were never emitted.

| Missing boundary | Original count | Generator component |
| --- | ---: | --- |
| After opening switch | 357 | mixed_translator span serialization |
| Before terminator | 358 | mixed_translator span serialization |
| Total | 715 | one generic concatenation cause |

All original cases with source/page/block/offset are in final_spacing_cleanup.json.
One boundary already had an inner blank supplied by the math payload; it is preserved.
Source coordinates in this regression report do not affect production behavior.

## Fix and scope

`BANA_4_2_INNER_SPACE`: amended Nemeth 4.2, October 2025 errata printed p.4,
PDF p.8. Adds a missing canonical blank after the opening and before the closing
switch of a nonempty explicitly selected linear math passage. Existing blanks,
interior cells, prose, and punctuation are unchanged. Other profiles, empty payloads,
and physical line/page layout are excluded. Mode is UEB → Nemeth → UEB; the
effect ends at that passage terminator. Routing is a precondition, not inferred here.
§4.6.8.c and §4.8.2 exclusions are not newly implemented by this fix.

Official errata example, fixture construct, synthetic passages, no-space interior
controls, existing blanks, other profiles and physical-layout exclusions pass in
tests/test_nemeth_boundary_spacing.py. Whole-Chapter assertions prove identical
math records, nonblank cells and block statuses, with exactly 715
inserted blanks. This is a serializer correction, not a new rule asserting user errors.

## Recomputed ledger

| Metric | Before | After |
| --- | ---: | ---: |
| Raw alignment discrepancies | 1446 | 772 |
| Missing inner boundaries | 715 | 0 |
| Confirmed errors (backend classification) | 0 | 0 |
| Internal REVIEW | 184 | 184 |
| Exclusions | 4 | 4 |
| Compared cells | 33744 | 34459 |
| Matching cells | 32418 | 33185 |

The 715 boundary defects were NOT 715 independently removable alignment opcodes.
The ledger was fully recomputed, not edited or suppressed. Agreement is now
96.30%; this is not standards certification.

| Remaining diagnostic construct/context | Count |
| --- | ---: |
| Whitespace alignment difference (placement not adjudicated) | 348 |
| Other cell/context difference requiring standards adjudication | 15 |
| Script/index dependency | 209 |
| Ordered-pair/tuple comma | 55 |
| Square grouping/context | 43 |
| Definition/condition colon context | 36 |
| Other unresolved technical/narrative context | 2 |
| Non-text exclusion | 4 |
| Fraction dependency | 14 |
| Letter/application grouping context (not assumed Rule 18) | 44 |
| Ellipsis context | 2 |

These clusters preserve uncertainty; they are not newly established standards rules.
Full independent adjudication is still pending. The previous standards-audit report
is historical pre-fix evidence; this ledger supersedes its discrepancy and generator
spacing counts. The 20 BRF line-separated boundaries remain placement-review items.

## Regression evidence

Full rendered Chapter 1 regression: classified UEB errors 0, classified Nemeth
errors 0, switch pair sequence 358/358, unaligned 0, baseline corruption 5/5.
The broken-switch corruption produces 17 mismatch records rather than the old 2:
it is still detected but record-level localization/count is fragmented; this is
not evidence of 17 independent corruptions. No alignment behavior was changed.
The ten-family existing extended detector tests pass, but only assert that a
difference exists, not family-specific standards conformance. Clean/corrupted
offscreen Qt tests pass with the error-only GUI and unchanged internal counts.
The catalog test was updated from 44 to 45 entries for the new scoped serializer
entry and explicitly checks its applicability, exclusions and tests.

## Freeze decision

No additional rule families promoted: the unresolved contexts still require more
structural applicability work. The deadline option to stop after spacing is used.
No Chapter-specific runtime conditions, REVIEW→PASS conversion, discrepancy
suppression, or Duxbury-derived rule was introduced. The original master and BRF
hashes are unchanged. GUI/highlighter/alignment code was not modified in this pass.

DEMO READY — SPACING FIXED
