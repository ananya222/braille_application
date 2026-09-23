# Alignment suppression - 12 September 2026

Implemented in the source validator and source GUI. The existing packaged EXE
has not been rebuilt: the available Python 3.12 runtime lacks PyInstaller and
PySide6, and the Windows Python launcher finds no installed build interpreter.

Page-local differences are withheld from confirmed errors when whole-document
nonblank matching places their expected anchors exclusively on other physical
pages. They remain in `ValidationResult.alignment_diagnostics`, with original
source/actual evidence and an explicit unverified-region explanation. This is
not a whitelist of filenames, counts or error categories, and it does not
change any Braille rule.

The GUI and normal exported report omit alignment notices and suppressed
counts, per the follow-up user request. With zero confirmed errors, the title
is "No confirmed Braille errors detected." The separate diagnostic JSON and
backend result retain alignment evidence. Suppressed regions are not annotated
as confirmed errors. The normal results no longer display provenance counts.

## Verification

Run `scripts/alignment_suppression_acceptance.py` with the project dependencies.
Results are in `reports/alignment_suppression_acceptance.json`.

| Fixture | Confirmed errors after filtering | Alignment diagnostics |
|---|---:|---:|
| Test 1 | 0 | 4 |
| Test 2 | 0 | 3 |
| Test 3 | 0 | 8 |
| Test 4 | 0 | 5 |
| Test 5 | 0 | 11 |

Existing literal PDF acceptance fixtures still detect all six deliberate math
errors and all three capitalization errors. Clean acceptance fixtures remain
at zero. Synthetic checks cover page reflow, a real math error before a page
split, a missing initial capital, true truncation, and a missing operator with
an unrelated extra page. Syntax checks passed. All 25 audit input hashes are
unchanged; the historical clean-conversion audit was preserved.

## Limits

This change suppresses unreliable page-local claims; it does not implement
cross-page rule validation. A displaced range may contain real defects, so it
is explicitly unverified rather than passed. Test 3's large displaced range
contains one unmatched expected cell, retained in the diagnostic explanation.
The existing operation-spacing/insertion blind spots, incorrect semicolon
expectation, physical runover scope limits, and fixture conversion defects
are unchanged. Zero confirmed errors is not a clean-fixture certification.
