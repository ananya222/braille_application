# Rule Implementation Status

Fast-track checkpoint.  `IMPLEMENTED` means the current deterministic subset
has production code and a regression test.  `PARTIAL` means only the listed
subset is deterministic.  `SOURCE_REQUIRED` is intentionally REVIEW-only;
`OUT_OF_SCOPE` is not claimed by the current textbook validator.

| Family | Matrix entries | Implemented/partial | Tested entries | Review/unsupported |
| --- | ---: | ---: | ---: | ---: |
| UEB | 16 | 9 | 2 | 7 |
| Nemeth | 26 | 13 | 7 | 13 |
| BANA/errata | 2 | 1 | 1 | 1 |
| **Total** | **44** | **23** | **10** | **21** |

## Current implementation checkpoint

- Rule model includes stable IDs, standard, family, source document/rule/page,
  scope, trigger, preconditions, exclusions, priority, dependencies, modes,
  required behaviour, and implementation/test status.
- `RuleRegistry` dispatches candidates from source structure and persistent
  UEB/Nemeth context before the existing verifiers run.
- The Nemeth 2025 errata file has 46 recorded table-of-change entries.  The
  runtime-affecting entries currently active in code are Rule 4.2 switching and
  the Rule 24.1.e deletion; other entries remain catalogued until their family
  is implemented.
- Verified switching cells remain `_%` / `⠸⠩` entering Nemeth and `_:` /
  `⠸⠱` returning to UEB.
- Simple first-order numeric/superscript script cases are deterministic under
  the cited Rule 14 subset.  Nested, letter-indexed, and context-dependent
  script cases remain REVIEW.
- Applicability coverage: triggers 44/44, exclusions 40/44, dependencies
  8/44, explicit precedence 18/44, and mode open/close declarations 6/44.

## Explicitly review-only or unsupported

Fractions, radicals, function-specific notation, nested/left/simultaneous
scripts, advanced typeforms, specialized symbols, spatial arrangements,
formatting mechanics, and unverified grade-1/capitalization/contraction edge
cases are not converted into definite production corrections.  They require
the cited source rule, deterministic implementation, and an independent test
oracle before promotion.

## Chapter 1 regression checkpoint

The rendered-BRF comparison completed after the dispatcher change without
altering the translation/alignment architecture:

| Measure | Result |
| --- | ---: |
| Physical cells compared | 33,744 |
| Exact cells | 32,418 |
| Physical-cell accuracy | 96.07% |
| Math spans | 358 |
| UEB-to-Nemeth switches | 358/358 |
| Nemeth-to-UEB switches | 358/358 |
| Prose cells excluding REVIEW | 12,970/12,970 (100.00%) |
| Math cells excluding REVIEW | 3,254/3,341 (97.40%) |
| Manual-review regions | 184 |
| Explicit out-of-scope regions | 4 |
| Unaligned regions | 0 |
| Controlled corruption checks | 5/5 |
| Unreviewed differences | 0 |

The 14 former UEB-side differences are now explicitly classified as
`REVIEW_REQUIRED`: each is a prose insertion containing a numeric-sign cell at
an alignment-sensitive BRF line boundary, with no expected source cells.  No
standards-backed UEB error was asserted.  Nemeth and switching differences
remain at zero; unsupported constructs stay in REVIEW.  The four genuinely
non-textual figure placeholders are explicitly `EXCLUDED_OUT_OF_SCOPE` under
generic `UEB_SCOPE_001`, not treated as PASS or ERROR.

## Phase 7 status

The original 188 unresolved regions are accounted for as 184 REVIEW plus 4
explicit exclusions. No Chapter 1-specific production condition was added;
the hardcoding scan found no Chapter 1 filename/page/offset/block/expression,
358-span count, or BRF fragment affecting rule behavior. The unresolved
construct families remain function/definition punctuation (116), indexed
symbol/function subscripts (8), fractions/slashes (3), ellipsis/punctuation
(2), other technical notation (4), textual indexed prose (39), and script
complexity (12).
