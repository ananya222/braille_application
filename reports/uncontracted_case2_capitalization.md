# Uncontracted UEB Case 2 Capitalization

## Final status

**INCOMPLETE — implementation and focused evidence pass; Duxbury conversion and the required 25-page end-to-end stress test are pending.** No Duxbury files were fabricated and no Numbers work was started.

## Authority and translation identity

- Standard: rules/Rules-of-Unified-English-Braille-2024.pdf
- Standard SHA-256: bf742499ee2eb3cbdf4914d97bbf0b2857bd3e91621f04a4990091b64e5a105e
- Translator: vendored Liblouis 3.38.0
- Table list: unicode.dis,en-ueb-g1.ctb
- DLL: vendor/liblouis-win64/bin/liblouis.dll
- Table: vendor/liblouis-win64/share/liblouis/tables/en-ueb-g1.ctb
- Table SHA-256: 446717b55e49ff41aef2c204b58ea1d2872a77a4473a821e766bffd51cee0b4d

The adapter verifies the binding, DLL, table directory, table list, Liblouis version, and table hash before translation. It does not fall back to system Liblouis.

## Exact new validation path

validate_document(..., profile="uncontracted_case2_capitalization") resolves the new validation profile, generates the expected document through generate_expected_braille, applies the Case 2 ASCII source boundary, and calls the vendored translator once for each ordinary source block:

source normalization -> Liblouis unicode.dis,en-ueb-g1.ctb -> continuous existing alignment -> existing provenance/PDF localization

The Case 2 translator deliberately translates a whole source block in one Liblouis context. This preserves Liblouis' contextual choice between a single capital indicator, capitalized-word mode, and capitalized-passage mode. Case 1 remains on its existing word-preserving path.

## UEB rules verified

The cited rules were checked against the local 2024 PDF, PDF pages 117-124:

- 8.1.1: follow print for the use of capital letters.
- 8.2.1: the capitals indicator determines the extent of capitals mode.
- 8.3.1: a capital letter is dot 6 followed by the lowercase letter form.
- 8.4.1-8.4.2: the capitalized-word indicator sets mode for the next letter-sequence and its extent ends at listed terminators such as a space or nonalphabetic symbol.
- 8.5.1-8.5.3: the capitalized-passage indicator sets passage mode and the passage is terminated by the capitals terminator.
- 8.6.1: the capitals terminator follows the final capitalized letter.

These rules justify direct use of the Liblouis candidate only for the audited ASCII-letter/ordinary-space scope. No punctuation, number, quote, typeform, or broader Grade 1 rule is enabled.

## Supported behavior

Supported and source-mapped in one ordinary source block:

- lowercase ASCII alphabet and ordinary lowercase words;
- isolated capitals such as A, B, and Z;
- ordinary capitalized words such as Hello, Braille, Validator, and Education;
- all-cap words such as NASA, UEB, PDF, and ABC;
- repeated capitalized words and isolated capitals;
- all-cap words adjacent to lowercase words;
- ASCII internal-capital forms such as iPhone, eBay, and McDonald;
- source-block beginnings and endings. Physical line and page placement remains handled by the existing document/PDF infrastructure.

Liblouis direct output was used; no capitalization override table was added. The existing capital-site locator is reused for unambiguous single-indicator sites, including word-initial and internal single-capital indicators.

## Liblouis probe evidence

The complete deterministic probe record is saved at stress_test/uncontracted_case2_capitalization/results/liblouis_capitalization_probes.json, SHA-256 2fdb705252ca715cfb78b9891f4281e84c7770447e9d70d4ef521864653f8aa3. Every row records source code points, the Liblouis API call, table list, translation call, complete Unicode Braille output, code points, dot masks, source positions, UEB citation, assessment, and custom-handling decision.

| Source | Liblouis Unicode Braille | Dot masks | Result |
|---|---|---|---|
| A | ⠠⠁ | 6 1 | PASS |
| B | ⠠⠃ | 6 12 | PASS |
| Z | ⠠⠵ | 6 1356 | PASS |
| Hello | ⠠⠓⠑⠇⠇⠕ | 6 125 15 123 123 135 | PASS |
| NASA | ⠠⠠⠝⠁⠎⠁ | 6 6 1345 1 234 1 | PASS |
| A B D Z | ⠠⠠⠠⠁ ⠃ ⠙ ⠵⠠⠄ | 6 6 6 1 blank 12 blank 145 blank 1356 6 3 | PASS |
| THIS IS ALL CAPS | ⠠⠠⠠⠞⠓⠊⠎ ⠊⠎ ⠁⠇⠇ ⠉⠁⠏⠎⠠⠄ | passage indicator and terminator | PASS |
| iPhone | ⠊⠠⠏⠓⠕⠝⠑ | 24 6 1234 125 135 1345 15 | PASS |
| eBay | ⠑⠠⠃⠁⠽ | 15 6 12 1 13456 | PASS |
| McDonald | ⠠⠍⠉⠠⠙⠕⠝⠁⠇⠙ | 6 134 14 6 145 135 1345 1 123 145 | PASS |

The full uppercase alphabet and mixed ordinary sentence probes also passed. The whole-source call is essential: a three-or-more all-cap sequence receives the passage indicator and terminator, while a one-word all-cap source receives capitalized-word mode.

## Source normalization and fail-closed behavior

Case 2 accepts only ASCII A-Z, a-z, and U+0020 ordinary spaces. It preserves the source text and rejects punctuation, digits, hyphens, quotes, apostrophes, tabs, line breaks, NBSP, and other unsupported characters. Through the current API, unsupported source blocks become REVIEW with zero confirmed errors; they are not silently reinterpreted.

Capitalized passage extent that depends on structure outside one source block, plus all punctuation-adjacent, numeric, typeform, unusual-whitespace, and broader Grade 1 interactions, remains fail-closed for later phases.

## Focused tests

tests/test_uncontracted_case2_capitalization.py: 10 tests passed.

Each supported family returned 0 errors and 0 reviews when clean, one confirmed error and 0 reviews after deliberate nonblank-cell corruption, and 0 errors and 0 reviews when represented as canonical six-dot BRF. A corrupted Hello indicator localized to the exact indicator cell with one UEB_8 finding and no duplicate.

## Duxbury source fixture

Created the clean English source for manual DBT conversion:

- stress_test/uncontracted_case2_capitalization/source/case2_capitalization_clean.docx
- SHA-256: 66c858d79533cb642710bace33a0e9bff76f609c0f141a6d32ae6c5b5bb48aed
- 8 logical source pages, with 7 explicit page breaks.
- Source text contains only ASCII letters and ordinary spaces.
- Includes alphabet, isolated capitals, capitalized words, repeated words, all-cap modes, internal-capital forms, lowercase near-neighbors, mixed sentences, and boundary cases.

No BRF, PDF, or DXB was synthesized. The bundled DOCX renderer could not run because no soffice.exe was available in the workspace runtime or PATH; the DOCX was structurally checked for the expected page breaks and source-character contract. Visual QA should be completed after the real Duxbury conversion is returned.

## Required stress test status

The required 25-page fixture, 500 deliberate mutations, clean-control run, exact blue-box run, and performance measurement were not started because the workflow requires real Duxbury DXB, BRF, and PDF output first. These are the remaining closure gates.

## Case 1 and old-validator regression

- Case 2 plus Case 1 plus existing Phase 1 focused tests: 10/10 passed in the latest combined run.
- Frozen old-validator dense regression after Case 2 changes:

| Fixture | Injected | Detected | Missed | False positives | Exact localization |
|---|---:|---:|---:|---:|---:|
| Test 1 | 67 | 67 | 0 | 0 | 67 |
| Test 2 | 68 | 68 | 0 | 0 | 68 |
| Test 4 | 50 | 50 | 0 | 0 | 50 |
| Total | 185 | 185 | 0 | 0 | 185 |

The existing Case 1 25-page generator was rerun after the Case 2 changes and completed without assertion failure; its established closure metrics remain 500/500 detected, 0 missed, 0 false positives, 0 duplicates, and 500/500 exact blue-box localization.

## Files changed

Production path:

- src/braille_app/translation/profiles.py
- src/braille_app/translation/source_normalization.py
- src/braille_app/translation/uncontracted_case2.py
- src/braille_app/translation/expected_document.py
- src/braille_app/translation/__init__.py
- src/braille_app/validation_profiles.py

Tests and audit/source evidence:

- tests/test_uncontracted_case2_capitalization.py
- stress_test/uncontracted_case2_capitalization/audit_capitalization.py
- stress_test/uncontracted_case2_capitalization/build_source_docx.py
- stress_test/uncontracted_case2_capitalization/results/liblouis_capitalization_probes.json
- stress_test/uncontracted_case2_capitalization/source/case2_capitalization_clean.docx
- reports/uncontracted_case2_capitalization.md

## Remaining closure defects

No defect was found in the implemented ASCII block-local capitalization slice. Case 2 cannot yet be called PASS because Duxbury evidence, the 25-page clean/corrupt end-to-end validator run, exact 500-cell localization, blue-box verification, and performance results remain outstanding.

Numbers are intentionally out of scope.

