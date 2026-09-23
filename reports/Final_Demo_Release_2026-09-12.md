# Final Demo Release - 12 September 2026

Status: **FINAL DEMO BUILD READY - REALISTIC MULTI-PAGE VALIDATION VERIFIED**

## Build

- Executable: `O:\braille_0.2\dist\BrailleValidator\BrailleValidator.exe`
- Final ZIP: `O:\braille_0.2\dist\BrailleValidator_Final_2026-09-12.zip`
- Executable timestamp: 12 September 2026, 12:46:47 Asia/Calcutta
- ZIP timestamp: 12 September 2026, 13:03:20 Asia/Calcutta
- Executable SHA-256: `f84a68ee088523429168cb08e20b072a4ee14751143822dfb1015b95a88a9014`
- ZIP SHA-256: `1ff5b4c12de06fa667382f57099f0bcbbce2d00a520591b9a658490d35a9639f`

The final ZIP was extracted into a separate temporary directory. Every archived file matched the release folder. The packaged application then passed all demo cases and one realistic corrupted synthetic case while development-root file access was blocked.

## Verified acceptance

| Check | Result |
|---|---:|
| Known clean math fixture | 0 confirmed errors |
| Known math-corrupted fixture | 6/6 detected and highlighted |
| Known clean capitalization fixture | 0 confirmed errors |
| Known capitalization-corrupted fixture | 3/3 detected and highlighted |
| Duxbury spacing robustness | 42/42 passed |
| PDF-coordinate spacing cases | 42/42 passed |
| Additional guard checks | 68/68 passed |
| Partial alignment guard | 2 aligned evaluated; 1 unresolved internal review |
| Frozen application demo and export paths | Passed |

The normal zero-error wording is `No confirmed Braille errors detected.` The application does not claim that a document is fully correct.

## Realistic synthetic results

| Test | Source/Braille pages | Passages aligned | Math evaluated | Capitals evaluated | Confirmed errors | Unresolved |
|---|---:|---:|---:|---:|---:|---:|
| Test 1 | 5/15 | 115/115 | 93/93 | 111/111 | 0 | 0 |
| Test 2 | 5/15 | 121/121 | 93/93 | 106/106 | 0 | 0 |
| Test 3 | 5/14 | 122/122 | 98/98 | 110/110 | 0 | 0 |
| Test 4 | 5/10 | 118/118 | 115/115 | 154/154 | 0 | 0 |
| Test 5 | 5/10 | 116/116 | 150/150 | 71/71 | 0 | 0 |

Supported feature occurrences evaluated in each file:

| Test | PLUS | MINUS | NEGATIVE | MULTIPLY | DIVIDE | EQUALS |
|---|---:|---:|---:|---:|---:|---:|
| Test 1 | 43/43 | 40/40 | 25/25 | 7/7 | 8/8 | 85/85 |
| Test 2 | 18/18 | 13/13 | 30/30 | 32/32 | 39/39 | 90/90 |
| Test 3 | 36/36 | 26/26 | 29/29 | 24/24 | 22/22 | 94/94 |
| Test 4 | 45/45 | 30/30 | 40/40 | 40/40 | 30/30 | 95/95 |
| Test 5 | 45/45 | 45/45 | 55/55 | 45/45 | 35/35 | 120/120 |

Known spacing artifacts were exercised in 417 normalized spans, removing 1,430 comparison-only artifact cells while retaining raw PDF provenance. These cells were not reported as errors.

Test 3 retains one known extra terminating switch in the PDF. It is recorded internally as an unmatched switch marker. The current supported switching rule does not classify that source-less insertion as a confirmed error, so this finding remains outside the guaranteed scope rather than being described as correct.

## Corruption stress results

Four supported corruptions were injected into a copied Braille PDF for each synthetic document. The 20-error corpus covers PLUS, MINUS, unary NEGATIVE, MULTIPLY, DIVIDE, EQUALS, missing capital, wrong capital, and unnecessary capital cases. Original source, DXB and PDF files retained their hashes.

| Measurement | Result |
|---|---:|
| Injected supported errors | 20 |
| Detected | 20 |
| Missed | 0 |
| False positives | 0 |
| Exact localization successes | 20 |
| Wrong-page highlights | 0 |
| Duplicate reports | 0 |
| Supported cases skipped by alignment | 0 |
| Detection rate | 100% |
| Localization rate | 100% |

All five annotated corrupted PDFs were exported without changing their Braille content. Every error page was rendered and visually inspected. The frozen executable independently detected and localized all 20 corruptions. The final extracted ZIP was also tested against Synthetic Test 1's four-error copy.

The corruption manifest is `O:\braille_0.2\stress_test\corruption_manifest.json`. Machine-readable results are in `reports\corrupted_synthetic_acceptance.json` and `reports\corrupted_synthetic_frozen.json`.

## Remaining limitations

- Validation is limited to basic supported word-initial capitalization and the verified simple PLUS, binary MINUS, unary NEGATIVE, explicit MULTIPLY, explicit DIVIDE and simple EQUALS constructs.
- General Nemeth spacing mistakes are not validated. Only the known Duxbury operator-spacing artifact is tolerated for comparison.
- Fractions, complex scripts, named functions, general grouping and relations, set-builder notation, arbitrary radicals, spatial mathematics and other advanced notation are not guaranteed.
- A source or math span that cannot be aligned uniquely is counted as unresolved and retained as internal review. It is not treated as a pass.
- The Test 3 extra terminating switch remains outside the currently guaranteed switching case.
- The release does not provide full UEB, full Nemeth, or arbitrary Duxbury certification.

The presentation package includes the executable, its `_internal` dependencies, short operating instructions, known clean and corrupted demos, and `RELEASE_SCOPE.txt`. Realistic synthetic documents remain internal test evidence and are not included in the presentation ZIP.
