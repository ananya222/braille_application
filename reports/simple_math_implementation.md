# Simple math implementation handoff

Source backend tested; packaged EXE unchanged. Final milestone:
SIMPLE-MATH SCOPE PARTIALLY READY — square-root structural import and validation
are not available. See Simple_Math_Supported_Scope.md for the exact grammar.

## Implementation

| File | Purpose |
|---|---|
| src/braille_app/translation/simple_math.py | Closed token/node grammar, direct standards-derived baseline cells |
| src/braille_app/translation/math_translator.py | Route fully parsed simple expressions to that generator |
| src/braille_app/rules/nemeth_rules.py | Full-expression proof and conservative scope fallback; retain existing independent letter/group proof |
| src/braille_app/rules/catalog.py | Cited applicability entry for NEMETH_SIMPLE_LINEAR_001 |
| src/braille_app/rules/rule_engine.py | Enable new proof only when selected by registry |
| src/braille_app/validation/validator.py | Classify proven math payload by source interval, not corrupted switch-like cells |
| src/braille_app/validation/api.py | Attribute proven payload errors to the correct Nemeth rule |
| tests/test_simple_math_scope.py | Literal official/synthetic oracles, exclusions, actual-cell corruption and fallback |
| scripts/simple_math_acceptance.py | Reproducible seven-expression fixture and existing PDF highlighter acceptance |
| scripts/simple_math_regression.py | Chapter regression with per-payload generic-change attribution |
| scripts/simple_math_scope_pdf.py | Concise scope PDF builder |

## Verified evidence

19 literal expression oracles (7 official, 12 additional); 23 parser exclusions.
Every nonblank cell in these expression payloads separately substituted with
the full cell gave one localized NEMETH_ERROR using NEMETH_SIMPLE_LINEAR_001.
This is a substitution test, not exhaustive detection of every possible defect.

Public correct PDF: 118/118 cells; zero errors and reviews.
Public corrupted PDF: six substitutions, six errors, six exact blue boxes.
All original cells survive annotated export; unmatched provenance and unexplained
offsets are zero. The images of clean and annotated corrupted pages were inspected.

Tab, prose context, switch inner spacing, independent boundary and letter/group
focused suites pass. No assertion is made that the entire legacy test suite passes:
old broad Nemeth PASS assertions and the fixed 47-rule catalogue assertion do not
describe this new conservative scope (catalogue now 48 entries).

## Chapter 1

| Metric | Result |
|---|---:|
| Clean confirmed errors | 0 |
| REVIEW | 279 |
| Exclusions | 4 |
| Expected cells | 34,448 |
| Matching cells | 33,175 |
| Accuracy | 96.3046% |
| Raw differences | 780 |
| Opening / closing switches | 358 / 358 |
| Missing inner blanks | 0 |
| Changed generated math payloads | 5 |
| Older six-corruption fixture confirmed errors | 5 |

The REVIEW increase from 182 is deliberate rejection of unproved whole structures,
not new Braille errors. The old page-2 corruption is in set-builder notation;
that whole block is now REVIEW. The five generation changes are all independently
attributed in simple_math_regression.json. No input fixture was altered.

## Remaining acceptance limits

- Plain square-root text lacks vinculum/radicand metadata: unverified.
- Spacing-only defects and arbitrary insertions/deletions are not certified;
  existing alignment/filter behavior remains a limitation.
- Scope assumes regular-type linear math, with physical expressions kept on one
  line. The text importer does not prove arbitrary document typography.
- The new public source is TXT/structured JSON, not a native-equation DOCX.
- The packaged Windows EXE and GUI acceptance were not rebuilt/retested here.
  Do not present these source-backend results as frozen-app acceptance.
- New translator code has no Chapter 1 fixture strings, counts, paths, offsets
  or output fragments. Regression scripts reference fixtures only for testing.

Generated evidence is in reports/simple_math_acceptance.json and
reports/simple_math_regression.json. Public fixtures are in data/simple_math;
blue-box exports are in output/simple_math. Scope PDFs are in reports.
