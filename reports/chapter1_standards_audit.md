# Chapter 1 standards audit — partial, not certification

## Scope and accounting

The English master is `chapter1_duxbury_ready_minus_fixed.docx` and the user output is `chapter1_duxbury_ready_minus_fixed.brf`.
The JSON companion records input hashes, every existing difference, all review records,
and all observed switch boundaries. Neither Duxbury nor Liblouis is a correctness oracle.

| Independently examined unit | Result |
| --- | ---: |
| Explicit switch-boundary facts confirmed correct | 696/716 |
| Line-separated boundary facts needing placement review | 20 |
| Confirmed user errors established by this limited audit | 0 |
| Coarse review records without deterministic construct-level expectation | 184 |
| Non-text exclusions (source text preserved in JSON) | 4 |
| Existing alignment differences still awaiting independent adjudication | 1446 |

These units overlap: a correct boundary can surround an unresolved expression.
They must NOT be added into a document accuracy or whole-expression PASS count.
The discrepancy ledger is explicitly pending, not falsely classified as correct or
indeterminate merely because it was not fully audited. The requested exhaustive
standards audit is **not complete**.

## Verified boundary property

Nemeth 2022 §4.2 (printed 4-1–4-2, PDF 54–55), replaced by October 2025 errata
printed p.4 / PDF p.8, requires opening cells ⠸⠩ followed by a blank and closing
cells ⠸⠱ preceded by a blank. The raw BRF was inspected before whitespace stripping.
Only explicit-boundary identity, order, and inner separation were checked. This does
not verify where switches were needed, contraction use, single-word switching,
punctuation ownership, or mathematics between switches.

Nearby applicable exceptions were read: amended §4.6.8.c (errata printed p.6 /
PDF p.10) and §4.8.2 (printed p.7 / PDF p.11); Nemeth §4.8.1–4.8.5
(printed 4-19–4-23 / PDF 72–76). A line-separated boundary is held for placement
review, not reported as a missing blank. Special-symbol specimens require a
different context and are excluded from this checker.

## Newly identified generator limitation

The current candidate generator has **715 switch boundaries without the
required inner blank**. `mixed_translator.translate_marked_text` directly concatenates
the switches with the math output. This is an expected-generator issue, NOT a user
BRF error. The current switch rule checks counts only. No automatic correction or
production rule promotion was made. An in-memory spacing candidate passed a prose
control and synthetic target and produced 33185/34459 matched cells,
184 REVIEW blocks and 0 classified error
details. Its opcode categories changed to {'LAYOUT_ONLY': 348, 'REVIEW_REQUIRED': 15, 'MANUAL_REVIEW': 405, 'EXCLUDED_OUT_OF_SCOPE': 4}. This is promising but does
not complete source-context verification or independently adjudicate those changes.
The monkeypatch was restored in a finally block; production remains unchanged.

## Other audit limitations

UEB_RULE_001 currently treats table-generated prose as PASS; that is not an independent
application of UEB 2024. Math calibration PASS likewise does not prove every applicable
standard. Broad function/punctuation labels are not rules. In particular, f(x) cannot
be presumed to be an abbreviated-function-name case under Rule 18.

The current review localization can identify a containing math span without locating
the unresolved construct. It cannot establish punctuation ownership or precise suspect
cells. No review was promoted to PASS/ERROR. All existing review and discrepancy
records remain in the JSON for a subsequent construct-level audit.

Existing generated `*_fixture*.pdf` files are synthetic export tests, not evidence that
the actual rendered Duxbury PDF was visually certified. Diagnostic amber output remains
separate and must not be treated as precise localization.

## Generic rules and tests

New production rules: **0**. The boundary checker is an experimental audit aid, not
a dispatcher rule or whole-document validator. Its official-example, synthetic,
missing-space, unresolved-context, and runover canaries pass. The real BRF is also
checked through the same generic checker; no Chapter-specific count affects behavior.
The full October 2025 errata was inspected; this pass only applied the above narrow
boundary requirements and does not claim complete errata implementation.

## GUI

Normal results show confirmed errors only. Review/exclusion counts, rows, diagnostic
button, and debug toggle are hidden. Internal objects and diagnostic files are retained.
Normal PDF export still receives ERROR objects only; no drawing logic was changed.
Zero errors is displayed as “No confirmed Braille errors detected.” A visible notice
states that the result is not certification of complete standards coverage.

## Baseline observed

ERROR 0, REVIEW 184, excluded 4.
Generator agreement 32418/33744
(96.07%), not standards accuracy.

## Confirmed user errors

None established in the narrowly checked property. This is **not** a finding that
all Chapter 1 prose and mathematics are correct. There is no confirmed-error table
because no fully adjudicated user error was established.

## Regression and demo qualification

The offscreen Qt workflow passed for the clean BRF and a temporary literary-cell
corruption: the latter remains UEB_ERROR / UEB_RULE_001 / source page 1. Hidden
controls cannot reveal review rows in the normal view. Production pipeline tests
and experimental selftest pass. The full rendered-BRF regression retains 358
switches each way, zero unaligned pages, zero classified true differences, and
5/5 baseline corruption detections. These are existing detector classifications,
not independent standards findings.

The existing extended ten-family corruption test passes, but it mutates the first
nonblank cell and only asserts a difference exists. It does NOT independently prove
correct family-specific Rule IDs or all ten intended constructs. Likewise the old
corruption harness forces REVIEW to PASS internally for detector testing. Neither
test should be presented as full standards conformance.

A recursive Python-source scan of src found no Chapter 1 filename/count/fix-ID
matches for chapter1, chapter.?1, 358, SPAN_142, or PAGE_7_FIX. This is a textual
scan, not a proof against every possible hard-coded condition. No rule behavior
was changed in this pass.

**DEMO READY WITH DECLARED INTERNAL LIMITATIONS** — error-only GUI workflow tested;
full independent standards audit and safe candidate-rule promotion remain unfinished.
