# Independent boundary-punctuation verifier: partial implementation

**PARTIAL BOUNDARY VERIFIER — AMBIGUOUS CASES REMAIN REVIEW**

## Delivered versus not yet connected

The independently registered `NEMETH_BOUNDARY_PUNCT_001` has a local verifier
returning PASS / ERROR / REVIEW. Expected cells come from explicit standards
symbols, not Liblouis, the candidate generator, or Duxbury. Tests pass with
generator entry points patched to raise if called.

The production handoff is deliberately conservative. `ExpectedBlock` retains
math strings/records and block cells, but no independently established inherited
mode state, semantic sentence-punctuation role, or exact boundary-cell interval.
It is therefore not sufficient input for production PASS/ERROR decisions under
this rule. The adapter records this gap on already-REVIEW blocks; it does not
pretend the missing facts are known. It calls the independent checker with the
available context and receives REVIEW. No existing REVIEW reason is cleared.

**There is not yet automatic user-BRF error reporting from this new rule.**
The local checker detects deterministic corruptions when supplied independently
resolved context and exact physical-cell provenance. These are different claims.
Candidate-generator errors must also not be relabeled as user errors.

## Deterministic local scope

`BoundaryContext` explicitly supplies source-before/math/source-after, complete
math interpretation, exact source boundary, resolved sentence role, active code,
inherited grade-1/numeric/capitalization/typeform/script/punctuation state and
layout status. Unknown is the default, not normal mode. These are prerequisite
facts the caller must establish; boolean assertions are not evidence by themselves.

Supported: a source-resolved complete mathematical item followed by a single
sentence-ending `.`, `!`, or `?` belonging to surrounding UEB prose, with ordinary
known modes, resolved linear layout, and exact measured boundary range. The next
source character must be whitespace or end-of-text. Full math translation and
the rest of the prose are not certified by a boundary PASS.

| Source punctuation | Independently required local interval |
| --- | --- |
| `.` | `⠀⠸⠱⠲` |
| `!` | `⠀⠸⠱⠖` |
| `?` | `⠀⠸⠱⠦` |

Each interval begins at the end of the math payload and includes the inner blank,
terminator and attached punctuation, excluding later prose spacing. Endpoints
must be obtained from provenance; searching for the desired terminator or
punctuation does not establish provenance. Required cells never use actual cells.

REVIEW: unresolved ownership/modes/provenance, internal punctuation, standalone
question marks, quotes, enclosed lists, punctuation clusters, unknown layout,
and incomplete mathematical dependencies. Commas, colons and semicolons are not
implemented in this verifier. Unknown scripts/fractions/functions do not become
supported merely because a boundary candidate happens to match.

## Standards authority and applicability

- Nemeth 2022 §4.6.5(a–b), printed 4-11–4-12 / PDF 64–65, distinguishes
  inside-Nemeth punctuation from punctuation logically belonging to prose.
  Example 4-31 provides the official `_:8` / `⠸⠱⠦` boundary. The rendered
  example was visually inspected.
- Nemeth §4.2, printed 4-1–4-2, amended by October 2025 errata printed p.4 /
  PDF 8: mode termination and inner blank. This amendment takes precedence over
  the original wording. No generator or serializer behavior changed.
- UEB 2024 Section 7 table and §7.1.1, printed 75–76 / PDF 103–104,
  establish period and exclamation symbols and follow-print punctuation.
- UEB §§7.5.1–7.5.4, printed 81 / PDF 109, establish question-mark use and
  grade-1 exceptions. Relevant §§2.6.1–2.6.3 and §§7.6.7–7.6.9 were read;
  ambiguous/standalone/quoted cases remain out of this implementation's scope.
- Relevant errata inspected: amended §§4.2, 4.6.8.c, 4.8.2 and Rule 8
  corrections. No replacement for §4.6.5(b) is listed. Single-word switching,
  runover placement and internal Rule 8 punctuation are not implemented here.

Catalog entry records trigger, scope, preconditions, exclusions, dependencies
on `NEMETH_4` and `UEB_7`, state transition and termination of this proof at the
punctuation. Dispatcher sort priority is operational ordering, not an assertion
of additional standards precedence. No unrelated rule is overridden.

## Chapter 1 result

No block changed classification. The page 15/block 24 canary remains REVIEW:

`on [[*ts*]]P(X)[[*te*]]? Justify your answer.`

The local `⠀⠸⠱⠦` interval passes in a test with explicitly resolved normal
state and exact provenance. Production does not yet supply those proofs,
so the test cannot justify clearing the whole block. The generator remains fixed.

64 already-REVIEW blocks receive additional boundary-context diagnostics.
They are not 64 verified boundaries and do not create additional REVIEW items.

| Metric | Before | After |
| --- | ---: | ---: |
| Raw discrepancies | 771 | 771 |
| REVIEW | 182 | 182 |
| Confirmed errors | 0 | 0 |
| Switches into Nemeth | 358 | 358 |
| Switches out of Nemeth | 358 | 358 |
| Missing inner spaces | 0 | 0 |
| Exclusions | 4 | 4 |
| Unaligned | 0 | 0 |
| Baseline corruption detection | 5/5 | 5/5 |

Full registry-on/off runs use unchanged generation. Flattened candidate cells
and every discrepancy record compare equal. The JSON contains all 771 records,
diagnostic locations, and frozen generator/input SHA-256 hashes.

## Local corruption behavior

These tests supply a resolved ordinary sentence and exact local cell interval.
All require `⠀⠸⠱⠦` independently.

| Corruption | Actual interval | Result |
| --- | --- | --- |
| Wrong punctuation | `⠀⠸⠱⠲` | ERROR |
| Missing punctuation | `⠀⠸⠱` | ERROR |
| Extra grade-1 indicator | `⠀⠸⠱⠰⠦` | ERROR |
| Missing terminator | `⠀⠦` | ERROR |
| Malformed terminator | `⠀⠸⠲⠦` | ERROR |
| Punctuation before termination | `⠦⠀⠸⠱` | ERROR |
| Missing inner blank | `⠸⠱⠦` | ERROR |
| Extra outer blank | `⠀⠸⠱⠀⠦` | ERROR |

With unknown context or provenance these same observations remain REVIEW.
Legitimate grade-1 examples after space, in `[?]`, or after hyphen are not
rejected; they remain outside this narrow rule. No global grade-1 prohibition.

## Regression tests and known separate issues

- Independent verifier: 5/5 test groups; 8/8 local corruptions return ERROR.
- Official 4-31 local boundary, unseen `.?!` contexts with `q(z)`, `J(C)`,
  `(r)`, the Chapter 1 canary, prose continuation, inner punctuation, unknown
  modes, malformed ranges, and generator-independence checks included.
- Production pipeline, promoted letter/grouping checks, frozen generator context
  tests, missing-space checks and experimental selftest pass.
- Clean/corrupted offscreen Qt workflow passes; no GUI/highlighter code changes.
- Full `test_*.py` sweep: 47/57 pass. Same 10 pre-existing failures as the
  preceding pass: three legacy BRF-parser, six legacy diff-engine and one
  format-engine failure. No assertion was suppressed or weakened. The catalog
  count assertion alone changed from 46 to 47 for the new registered entry.
- The plain `10:30-?` result remains `⠼⠁⠚⠒⠼⠉⠚⠤⠦`: the documented
  UEB 7.5.4 gap is unchanged and not certified.
- Broken-switch baseline still yields 17 records for one injected corruption;
  unchanged, not 17 independent errors.
- Historical Phase 8B PDF-export tests with stale baselines were not rerun;
  no PDF output was regenerated or recertified.

## Files changed

- `src/braille_app/rules/boundary_punctuation.py`: independent checker and
  conservative production diagnostic handoff.
- `src/braille_app/rules/catalog.py`: independently registered partial rule.
- `src/braille_app/rules/rule_engine.py`: dispatch diagnostics on existing REVIEW.
- `tests/test_boundary_verifier.py`: independent local oracles/corruptions.
- `tests/test_production_pipeline.py`: new catalog-entry count only.
- `experiments/ueb_nemeth/boundary_verifier_report.py`: paired frozen-generation audit.
- `experiments/ueb_nemeth/context_regression_suite.py`: optional report filename
  prefix so prior baseline reports are preserved.
- This report, `boundary_verifier_regression.json`, and `boundary_verifier_tests.json`.

## Remaining integration requirement

Before automatic boundary PASS/ERROR can be promoted in document validation,
carry independently resolved semantic ownership, inherited modes and exact
boundary source-to-actual-cell provenance into the verifier. Do not substitute
default normal state, a containing-block range or a substring search. This work
was not silently folded into generator/alignment changes in this pass.
