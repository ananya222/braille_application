# Context-preserving UEB suffix generation

## Result

**GENERATOR CONTEXT FIX PROMOTED — BOUNDARY VERIFIER STILL REVIEW**

This is a narrowly scoped generator repair, not punctuation certification.
One Chapter 1 candidate block changes. No standards rule, REVIEW policy,
alignment, serializer, highlighter, GUI, source DOCX or input BRF was changed.

## Original pipeline trace

Input: `Is it [[*ts*]]H(B)[[*te*]]?`

| Source segment | Component | Context supplied | Original output |
| --- | --- | --- | --- |
| `Is it ` | Liblouis literary table `en-ueb-g2.ctb` | Independent fragment, default mode | `⠠⠊⠎⠀⠭⠀` |
| `H(B)` | Existing `translate_math` path | Independent math record; existing Nemeth normalization/table | `⠠⠓⠷⠠⠃⠾` |
| `?` | Liblouis literary table `en-ueb-g2.ctb` | Independent fragment, default mode; no preceding source item | `⠰⠦` |

The existing serializer adds `⠸⠩⠀` and `⠀⠸⠱` to the math payload.
Sentence context was discarded at each `translate_prose(fragment)` call.
An isolated question mark legitimately requires disambiguation; the error is
asking the translator to treat attached sentence punctuation as isolated.

## Authority and independent oracles

- Nemeth 2022 §4.6.5(b), printed 4-12 / PDF 65, Example 4-31:
  surrounding-text punctuation is UEB; sentence punctuation normally follows
  the terminator without a space. Official example ends `_:8` / `⠸⠱⠦`.
  The rendered page was visually inspected.
- Nemeth §4.2 as amended by October 2025 errata, printed errata p.4 / PDF 8:
  opening/termination scope and inner spaces. Existing serialization is retained.
- UEB 2024 Section 7 symbol table, printed 75 / PDF 103, and §7.1.1,
  printed 76 / PDF 104: individual comma, semicolon, colon, period and
  exclamation symbols; follow-print punctuation.
- UEB §§7.5.1–7.5.4, printed 81 / PDF 109: question-mark ambiguity,
  standing-alone and space/hyphen/dash exceptions. §§2.6.2–2.6.3,
  printed 16–17, and §§7.6.7–7.6.9, printed 85–86, clarify the relevant
  standing-alone and quote interactions. These exceptions are not globally
  overridden by this generator change.
- Entire October 2025 errata inspected. It does not replace §4.6.5(b).
  Amended §4.8.2 concerns physical placement/runovers, outside this patch.

The official 4-31 boundary integration test uses the official math payload
as input to the serializer/context path. It does NOT claim the existing
numeric generator reproduces that whole example. End-to-end numeric generation
already differs internally (extra spacing and numeric indicator); unchanged.

## Architecture and supported scope

`ProseBoundaryContext` retains the complete contextual prose view and each
text segment's source interval. Each explicitly delimited math record becomes
an opaque occupied-item placeholder (`math`) in that temporary view only.
Math letters, numeric state and capitalization are not translated as UEB.
The actual source and all math records remain unchanged.

Liblouis translates the contextual view with source-position information.
The generator selects only the eligible suffix interval through that mapping;
placeholder cells are never emitted. Synthetic tests vary the placeholder
spelling and length. There are no fixed cell offsets or cell-deletion rules.

Eligibility is a single immediately attached `.` `,` `;` `:` `!` or `?`,
followed by whitespace or end-of-text, after a nonempty trimmed math span.
The math begins the record or follows a space. The profile must use the
established UEB/Nemeth switch pair. Position mappings must be ordered, in
range, contiguous for the suffix, and begin at its exact source position.
All output after the initial punctuation must match the original suffix
translation; broader changes are rejected.

| Mark | Independent-fragment cells | Contextual attached cells |
| --- | --- | --- |
| `.` | `⠲` | `⠲` |
| `,` | `⠂` | `⠂` |
| `;` | `⠆` | `⠆` |
| `:` | `⠒` | `⠒` |
| `!` | `⠖` | `⠖` |
| `?` | `⠰⠦` | `⠦` |

The punctuation set is a source-context eligibility class, not an output
replacement table. Expectations for the five other marks come from UEB
Section 7, not inference from the question-mark example.

Excluded from this repair: quotes/apostrophes in the prose view, physical
line/page breaks, non-BMP prose (position-unit ambiguity), punctuation clusters,
ellipses, adjacent words/symbols, untrimmed/empty math, nonmatching profiles,
unreliable position maps, or broader suffix changes. Such cases retain the
previous candidate and existing validation policy. There is no new ownership
verifier, no automatic PASS, and no claim of general persistent-mode handling.
Internal Nemeth punctuation and non-boundary prose are not retranscribed.

## Complete canary

Before: `⠠⠊⠎⠀⠭⠀⠸⠩⠀⠠⠓⠷⠠⠃⠾⠀⠸⠱⠰⠦`

After: `⠠⠊⠎⠀⠭⠀⠸⠩⠀⠠⠓⠷⠠⠃⠾⠀⠸⠱⠦`

The suffix is produced by contextual translation, not by deleting `⠰`.
Required indicators for isolated `?`, `[?]`, and later standalone question
marks in prose remain present.

## Full Chapter 1 paired regression

The before run disables only the new contextualization call in memory.
Both runs use the same current rules and source/input files. The new JSON
contains all 771 discrepancy records and the complete changed-block inventory.

| Metric | Before | After |
| --- | ---: | ---: |
| Raw discrepancies | 772 | 771 |
| REVIEW blocks | 182 | 182 |
| Classified errors | 0 | 0 |
| Switches into Nemeth | 358 | 358 |
| Switches out of Nemeth | 358 | 358 |
| Missing inner spaces | 0 | 0 |
| Exclusions | 4 | 4 |
| Unaligned records | 0 | 0 |
| Baseline corruption detection | 5/5 | 5/5 |

### Every changed production record (one)

Source page 15, block 24:

`on [[*ts*]]P(X)[[*te*]]? Justify your answer.`

Before:
`⠕⠝⠀⠸⠩⠀⠠⠏⠷⠠⠭⠾⠀⠸⠱⠰⠦⠀⠠⠚⠥⠌⠊⠋⠽⠀⠽⠗⠀⠁⠝⠎⠺⠻⠲`

After:
`⠕⠝⠀⠸⠩⠀⠠⠏⠷⠠⠭⠾⠀⠸⠱⠦⠀⠠⠚⠥⠌⠊⠋⠽⠀⠽⠗⠀⠁⠝⠎⠺⠻⠲`

Expected change under Nemeth 4.6.5(b) and UEB 7.5. It remains REVIEW.
No other candidate block changed. All source fields, math records and block
statuses compare equal. Input DOCX/BRF SHA-256 hashes are preserved in JSON.
One MANUAL_REVIEW discrepancy disappears (405 to 404); all other ledger
category counts stay unchanged. This reduction is not the correctness oracle.

## Tests and limitations

- Seven new test groups pass: complete canary, official boundary integration,
  six punctuation types/start and middle positions, legitimate grade-1/plain
  prose, multiple math spans/prose continuation, exclusions/source integrity,
  placeholder independence and invalid mapping rejection.
- Existing production generator/verifier tests, letter/grouping tests,
  inner-spacing tests and experimental selftest pass.
- Offscreen clean/corrupted Qt workflow passes; no GUI code changes.
- Full `test_*.py` function sweep: before 35/45 pass; after 42/52 pass.
  The same ten failures occur in both runs (three legacy BRF-parser tests,
  six legacy diff-engine tests, one format-engine test). Exact results and
  tracebacks are in `prose_context_tests_before.json` and
  `prose_context_tests.json`. No failures were suppressed or test assertions
  weakened. Pytest is unavailable; a zero-fixture function harness was used.
- Historical Phase 8B PDF smoke has stale 184/159 expectations and was not
  run; this pass does not regenerate or visually recertify PDF exports.
- Existing controlled corruption tests remain 5/5. One broken switch still
  produces 17 detected records, not 17 independent corruptions; unchanged.
- Additional pre-existing standards gap observed: plain `10:30-?` produces
  `⠼⠁⠚⠒⠼⠉⠚⠤⠦`, missing the grade-1 indicator specified by UEB 7.5.4.
  It is unchanged and explicitly NOT certified by this repair.
- Runtime scan of the changed translation files found no chapter filenames,
  page/block constants, exact fixture expressions, 358-span checks or
  grade-1 deletion logic. Fixed fixture references occur only in reports/tests.

## Change inventory

- `src/braille_app/translation/liblouis_translator.py`: position-aware literary
  translation API; existing APIs unchanged.
- `src/braille_app/translation/prose_boundary_context.py`: contextual source
  view, typed suffix context, mapped candidate selection and conservative guards.
- `src/braille_app/translation/mixed_translator.py`: invoke contextual generation
  after segmentation; reuse unchanged math serializer.
- `tests/test_prose_boundary_context.py`: independent oracles and safeguards.
- `experiments/ueb_nemeth/prose_context_report.py`: paired ledger and inventory.
- `experiments/ueb_nemeth/context_regression_suite.py`: pytest-free test harness.
- This report and the three accompanying regression/test JSON reports.

No boundary verifier was registered or promoted. A separate independently
derived verification pass is still required before clearing the REVIEW.
