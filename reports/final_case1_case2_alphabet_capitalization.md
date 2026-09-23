# Final combined closure test — Case 1 + Case 2

## Final status: FAIL

The clean real-Duxbury translation gate passed, and the isolated Case 1, Case 2, and old-validator gates passed. The required combined 1,000-mutation end-to-end gate did not pass:

- 1,000 deterministic semantic mutations were injected into copies of the real Duxbury BRF and PDF.
- 732 confirmed validator errors were returned.
- 268 mutations remained in unresolved source passages.
- 706/1,000 target cells received exact blue-box localization.
- 118 non-target blue boxes were emitted; duplicate blue boxes: 0.

The clean evidence and all frozen Duxbury inputs remain unchanged. Numbers, punctuation, and later UEB families were not started.

## Scope and authority

This closure covers only English-only uncontracted UEB / Grade 1:

- alphabetic `a-z` and `A-Z`
- ordinary English words
- isolated/basic capitalization
- ordinary capitalized words
- supported all-cap and internal-capital interactions already covered by Case 2

Authority: `rules/Rules-of-Unified-English-Braille-2024.pdf`, SHA-256 `bf742499ee2eb3cbdf4914d97bbf0b2857bd3e91621f04a4990091b64e5a105e`.

The validation path remains:

`master extraction → source normalization → vendored Liblouis → expected uncontracted Braille → existing continuous alignment → existing provenance mapping → existing PDF blue-box localization`

No document extraction, continuous alignment, provenance, PDF highlighting, or GUI rewrite was made.

## Audited translation runtime

- Liblouis version: `3.38.0`
- Table list: `unicode.dis,en-ueb-g1.ctb`
- DLL: `vendor/liblouis-win64/bin/liblouis.dll`
- Table: `vendor/liblouis-win64/share/liblouis/tables/en-ueb-g1.ctb`
- Table SHA-256: `446717b55e49ff41aef2c204b58ea1d2872a77a4473a821e766bffd51cee0b4d`
- Display table: `vendor/liblouis-win64/share/liblouis/tables/unicode.dis`

The validator used only the vendored runtime and table identity above.

## Real Duxbury artifact verification

Folder: `stress_test/final_case1_case2_alphabet_capitalization/source/`

- Frozen source DOCX: `final_case1_case2_clean_50page.docx`, 50 pages, SHA-256 `8c53cec65b6dfbc21c072db1ceaa448db887974dbc386379ae4c66941c4b72f2`
- Duxbury version: DBT 14.1, supplied project metadata
- Selected template evidence: DXB contains `Uncontracted`, `g1`, `nUncontracted`, and `nG1Passage` markers. No literal template filename was encoded in the DXB, so no stronger template-name claim is made.
- BRF: `final_case1_case2_clean_50page (2).brf`, 50 readable pages, SHA-256 `48b0c2d3145dfab4d497a5b0b98c5b8633fd84369d5c78a250cf4109b9da2389`
- DXB: `final_case1_case2_clean_50page.dxb`, SHA-256 `46a48b68a45f89c05cb2761d0c278ce42bf3ef8a029b5262e387e438f90ccad3`
- PDF: `final_case1_case2_clean_50page.pdf`, 50 readable pages, SHA-256 `6cc4aa95843bd7ae29ffb110d14a26b3224b7d4214651a951a5fd44cc593e852`

The BRF is the primary logical comparison. The PDF was used for visual/provenance verification. The DXB was retained as configuration evidence. The BRF and PDF contain the complete 50-page translated document and show no evidence of a contracted Grade 2 translation in this supported scope.

## Clean Liblouis versus Duxbury audit

The logical comparison used the BRF and removed only confirmed page furniture, line-layout separators, and 180 Duxbury typeform cells. The typeform cells are an out-of-scope source formatting/layout boundary, not silently accepted translation semantics.

| Measure | Result |
|---|---:|
| Logical pages compared | 50 |
| Expected semantic cells | 10,542 |
| Exact semantic cells | 10,542 |
| Semantic cell accuracy | 100% |
| Meaningful translation disagreements | 0 |
| Raw logical alignment disagreements | 0 |
| Duxbury typeform cells removed for comparison | 180 |
| Clean validator confirmed errors | 0 |
| Clean validator reviews | 0 |
| Clean validator false positives | 0 |
| Clean validator duplicate findings | 0 |

The physical clean validator run reports 10,591/10,591 matching expected cells on both the BRF and PDF paths. Its 91 raw layout differences comprise 75 recognized Duxbury typeform-control insertions and 16 ignored unmapped insertions; none is a confirmed semantic error.

## Combined corruption fixture

Derived files only; the real source artifacts above were not overwritten:

- BRF: `stress_test/final_case1_case2_alphabet_capitalization/corrupted/final_case1_case2_corrupted_1000.brf`, SHA-256 `d03096831fc335100d42f1314fb3708d0a4a0b76917284bf2a1dfbbaac5d7850`
- PDF: `stress_test/final_case1_case2_alphabet_capitalization/corrupted/final_case1_case2_corrupted_1000.pdf`, SHA-256 `88fa1d48f8ffaf98819fd19c26f46270f171684f15b66150a679c4f806b0a97e`
- Annotated PDF: `stress_test/final_case1_case2_alphabet_capitalization/corrupted/final_case1_case2_corrupted_1000_annotated.pdf`, SHA-256 `22745e4241e8acd07b80e84236130b12de9ca60d8f64837c0c75bad4e52069da`
- Manifest: `stress_test/final_case1_case2_alphabet_capitalization/manifests/mutation_manifest.csv`
- Result JSON: `stress_test/final_case1_case2_alphabet_capitalization/results/corruption_result.json`

The fixture contains 1,000 letter substitutions, 20 per physical page. Independent checks confirmed 1,000 changed PDF glyph tokens and 1,000 changed semantic BRF cells.

| Metric | Result |
|---|---:|
| Injected mutations | 1,000 |
| Confirmed validator errors | 732 |
| Reviews | 0 |
| Missed/unresolved mutations | 268 |
| Validator-count false positives | 0 |
| Validator duplicates | 0 |
| Blue-box instances | 828 |
| Exact target cells with a blue box | 706/1,000 |
| Missed target blue boxes | 294 |
| Non-target blue boxes | 118 |
| Duplicate blue boxes | 0 |

The same 732-error result was observed when validating the derived PDF and derived BRF. The corrupted run statistics were:

- expected cells: 10,591
- matching cells: 7,723
- raw differences: 792
- source passages: 275 total, 9 aligned, 266 unresolved
- capitalization opportunities: 350 total, 205 evaluated, 145 unresolved
- reviews: 0

Because unresolved regions are not confirmed errors, the result cannot be counted as 1,000/1,000 detection or exact localization.

## Failure cause

The fixture writer is not the cause. The copies contain exactly the planned 1,000 cell substitutions, and the clean artifacts remain intact.

The failure is an existing continuous-alignment limitation exposed by this repeated 50-page corpus. The source repeats the same five-page families across ten cycles. With 20 mutations on every page, the flattened document stream has multiple equally plausible repeated anchors. The current aligner relocates portions of corrupted content across repeated pages; the validator then leaves 266 source passages and 145 capitalization opportunities unresolved, corresponding to 268 missed mutation findings. The existing alignment diagnostics fail closed for those regions, so they are not falsely promoted to confirmed errors, but recall is incomplete and blue boxes can land on displaced/typeform cells.

Fixing this would require a scoped page/block alignment or provenance change, or a materially less dense mutation design. Broadly tolerating the unresolved regions or rewriting the proven continuous aligner was not allowed by this closure request. The combined closure therefore remains FAIL.

## Focused and regression gates

| Gate | Result |
|---|---|
| Case 1 unit tests | 3/3 tests passed |
| Case 1 independent PDF stress | 500/500 detected, 500/500 exact, 0 false positives, 500 blue boxes |
| Case 2 unit tests | 4/4 tests passed; clean/corrupt/near-neighbor families covered |
| Case 2 Liblouis capitalization probes | 21/21 probes passed |
| Acceptance guard suite | PASS; five fixtures, existing math 6/6, capitalization 3/3, 25 inputs unchanged |
| Old validator clean | 0 errors |
| Old validator dense regression | 185/185 detected, 185/185 exact localization, 0 missed, 0 false positives, 0 duplicates |

The small production change in `src/braille_app/validation/api.py` makes unaligned alphabet insertions owned by both `UEB_CASE1_SCOPE` and `UEB_CASE2_SCOPE`; unrelated profiles retain the historical layout guard. The old 185-case suite passed after this change.

## Unsupported and fail-closed behavior

This profile supports only ASCII letters, ordinary spaces, and the supported English word/capitalization cases. Numbers, punctuation, quotes, apostrophes, hyphens/dashes, brackets, symbols, typeforms, unusual whitespace, passage indicators, contracted UEB, Nemeth, and mathematics are not part of this release slice.

Unsupported source constructs are rejected by source normalization and routed as review/unsupported according to the existing architecture; they are not translated into confirmed errors. Duxbury typeform controls are stripped only at the explicit logical-comparison boundary and do not constitute production typeform support.

## Files changed for this closure

- `src/braille_app/validation/api.py` — scoped Case 2 alphabet ownership guard.
- `stress_test/final_case1_case2_alphabet_capitalization/scripts/final_combined_closure.py` — deterministic real-artifact audit, faithful BRF derivative mapping, mutation manifest, and blue-box audit.
- `reports/final_case1_case2_alphabet_capitalization.md` — this report.
- Derived audit outputs under `stress_test/final_case1_case2_alphabet_capitalization/corrupted/`, `manifests/`, and `results/`.

## Required totals

TOTAL DELIBERATE CASES: 1,000 combined corruption mutations

EXACT LIBLOUIS/DUXBURY AGREEMENTS: 10,542/10,542 logical semantic cells; 0 meaningful disagreements

MEANINGFUL DISAGREEMENTS: 0 clean; combined corruption is a validator/localization stress failure, not a translation disagreement

LIBLOUIS MATCHED UEB: 10,542 logical semantic cells in the clean audit

DUXBURY MATCHED UEB: 10,542 logical semantic cells in the clean audit

PERMITTED VARIANTS: 0 identified in this scope

SOURCE/POLICY CASES: Duxbury typeform/layout controls only; 180 logical-comparison cells, 75 recognized typeform-control insertions, and 16 ignored unmapped insertions were kept at the explicit layout boundary

AMBIGUOUS/MANUAL: 266 unresolved source passages and 145 unresolved capitalization opportunities in the combined dense corruption run

UNRESOLVED: 268 injected mutations; 294 target cells lacked exact blue-box localization; 118 non-target blue boxes

LIBLOUIS BASE ASSESSMENT: Strong for clean Case 1/2 translation in this scope; combined dense end-to-end recall is not closed because of alignment ambiguity

MINIMAL CUSTOM RULE FAMILIES REQUIRED: existing source normalization and capitalization ownership; no translation override was required by the clean Duxbury comparison

MOST IMPORTANT LIBLOUIS GAPS: none demonstrated for the supported alphabet/word/capitalization clean corpus

AREAS LIBLOUIS ALREADY HANDLES WELL: alphabet, ordinary words, isolated capitals, capitalized words, all-cap interactions, internal capitals, and repeated clean source content

Numbers and punctuation remain deliberately unstarted. Do not mark Case 1 + Case 2 as fully closed until the combined 1,000-mutation gate is rerun and reaches 1,000/1,000 confirmed, exact, non-duplicate blue boxes with zero false positives.
