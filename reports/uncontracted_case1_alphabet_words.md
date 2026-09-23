# Uncontracted UEB Case 1: alphabet and ordinary words

Status: **PASS — implementation slice closed**

This slice implements only lowercase English alphabet cells, ordinary
lowercase words, and ordinary ASCII spaces. It does not implement
capitalization, numbers, punctuation, quotes, apostrophes, typeforms, numeric
spacing, or other later UEB families.

## Validation path

The new profile is `uncontracted_case1_alphabet_words`:

`master extraction -> source normalization -> vendored Liblouis
unicode.dis,en-ueb-g1.ctb -> expected uncontracted Braille -> existing
continuous alignment -> existing provenance -> existing PDF blue-box export`

The existing alignment, provenance, PDF reader, and GUI layers remain the
shared infrastructure. Case 1 adds only profile dispatch, lowercase-only
normalization, Case 1 scope results, Case 1 insertion promotion, logical
transposition de-duplication, and a deterministic deletion anchor for PDF
annotation. The old profile paths do not use those Case 1 branches.

## Audited Liblouis runtime

| Item | Value |
|---|---|
| Version | 3.38.0 |
| DLL | `O:\braille_0.2\vendor\liblouis-win64\bin\liblouis.dll` |
| Table list | `unicode.dis,en-ueb-g1.ctb` |
| Main table | `O:\braille_0.2\vendor\liblouis-win64\share\liblouis\tables\en-ueb-g1.ctb` |
| Main table SHA-256 | `446717b55e49ff41aef2c204b58ea1d2872a77a4473a821e766bffd51cee0b4d` |
| Display table | `O:\braille_0.2\vendor\liblouis-win64\share\liblouis\tables\unicode.dis` |

The focused runtime test confirms the version, exact table list, and table
hash. The validator fails rather than silently selecting a system runtime when
the vendored runtime is unavailable.

## Focused deterministic tests

`tests/test_uncontracted_case1_alphabet_words.py` passed 3/3. The existing
Phase 1 test file passed 3/3 in the same run.

Covered clean Case 1 values include:

- `abcdefghijklmnopqrstuvwxyz`
- short and repeated lowercase words
- `hello`, `braille`, `validator`, `ordinary`, `education`, `computer`
- longer ordinary words and lowercase sentences
- repeated-word and repeated-letter neighbors

Corrupted and near-neighbor behavior is covered by the 25-page fixture below
and by the unsupported-family checks for uppercase, digits, punctuation,
hyphens, apostrophes, tabs, and non-ASCII letters.

## End-to-end fixture

The deterministic fixture is in:

`O:\braille_0.2\stress_test\uncontracted_case1_alphabet_words\`

It contains 25 source pages with exactly 20 mutations per page: 500 injected
errors total. The mutation families are substitution, deletion, insertion,
and adjacent transposition, with repeated/similar words, long words, short
words, and word-boundary locations. The source content itself is limited to
lowercase ASCII letters and ordinary spaces.

| Artifact | SHA-256 |
|---|---|
| `case1_source.json` | `a3366631984b29459522e2fccb45eaf38ef4e507c4dad5e74217d126ef677df6` |
| `case1_clean.brf` | `b3d4bc4b6507b9adcfe91179807611638a2a1f46917bc2154994d6d1f76b5d81` |
| `case1_corrupted.brf` | `b63f86d329bd8fd916930538eca42180f907659133a89716cdce0a3b61213220` |
| `case1_clean.pdf` | `0638c5e2a8a49c4d64d8e89bf7b99c2174d758ddade70176b6c390f16e558be5` |
| `case1_corrupted.pdf` | `a5f6eee7a24ec26804a8bf0f3d8720bcc1c781ece9672d2a6e672f5033f2bb3d` |
| `case1_corrupted_annotated.pdf` | `2bab142b75fa13a51f27af5782edb306a48c619693863474757f473703a32d41` |

The PDF is the complete end-to-end acceptance input. BRF artifacts are emitted
from the same clean and corrupted logical cell streams for audit evidence.

### Results

| Check | Result |
|---|---:|
| Clean PDF confirmed errors | 0 |
| Clean PDF reviews | 0 |
| Corrupted PDF injected | 500 |
| Corrupted PDF detected | 500 |
| Missed | 0 |
| False positives | 0 |
| Duplicate findings | 0 |
| Exact physical page/cell localization | 500/500 |
| Correct blue-box locations | 500/500 |
| Blue boxes emitted | 500 |

Mutation breakdown: 275 substitutions, 100 deletions, 100 insertions, and 25
transpositions. The full machine-readable result is
`stress_test\uncontracted_case1_alphabet_words\expected_findings.json`; the
injection manifest is `mutation_manifest.csv`.

Measured validation time was approximately 1.8 seconds for the clean PDF and
57.5 seconds for the corrupted PDF in the bundled Python runtime.

## Unsupported and fail-closed behavior

Case 1 accepts only `a-z` and ordinary U+0020 spaces. Uppercase letters,
digits, punctuation, hyphens, apostrophes, tabs, and non-ASCII letters are
rejected by the explicit normalization boundary. Through the validator API,
unsupported source blocks produce a review and no confirmed error; they are not
silently translated as Case 1 and the document is not represented as fully
validated.

Capitalization is intentionally outside this profile. The existing
`uncontracted_phase1` capitalization behavior remains separate and its tests
still pass.

## Old-validator regression

The existing dense regression suite was rerun after the Case 1 changes:

| Fixture | Injected | Detected | Missed | False positives | Exact boxes |
|---|---:|---:|---:|---:|---:|
| Test 1 | 67 | 67 | 0 | 0 | 67 |
| Test 2 | 68 | 68 | 0 | 0 | 68 |
| Test 4 | 50 | 50 | 0 | 0 | 50 |
| **Total** | **185** | **185** | **0** | **0** | **185** |

Clean counterparts for Tests 1, 2, and 4 each returned zero confirmed errors
and zero reviews. Old-validator status: **PASS; no regression observed**.

## Files changed

Implementation and tests:

- `src/braille_app/translation/profiles.py`
- `src/braille_app/translation/source_normalization.py`
- `src/braille_app/translation/uncontracted_case1.py`
- `src/braille_app/translation/expected_document.py`
- `src/braille_app/translation/__init__.py`
- `src/braille_app/validation_profiles.py`
- `src/braille_app/validation/api.py`
- `src/braille_app/validation/pdf_annotation_adapter.py`
- `tests/test_uncontracted_case1_alphabet_words.py`
- `stress_test/uncontracted_case1_alphabet_words/run_case1.py`

Evidence and outputs:

- `reports/uncontracted_case1_alphabet_words.md`
- `stress_test/uncontracted_case1_alphabet_words/case1_source.json`
- `stress_test/uncontracted_case1_alphabet_words/mutation_manifest.csv`
- `stress_test/uncontracted_case1_alphabet_words/expected_findings.json`
- the clean/corrupted BRF, PDF, and annotated PDF artifacts listed above

## Stop boundary

Case 1 is closed at lowercase alphabet + ordinary lowercase words + ordinary
ASCII spaces. Numbers, punctuation, capitalization, quotes, apostrophes,
typeforms, numeric spacing, and other later UEB behavior were not added.
