# Uncontracted UEB phase 1 — alphabet and capitalization

Scope: English-only uncontracted UEB / Grade 1, ICEB UEB 2024 authority.
Contracted UEB, Nemeth, mathematics, punctuation, quotes/apostrophes, typeforms, numeric semantics, and passage indicators are not implemented here.

## Files changed

- `src/braille_app/translation/profiles.py` — explicit phase-1 profile.
- `src/braille_app/translation/source_normalization.py` — fail-closed source boundary.
- `src/braille_app/translation/uncontracted_phase1.py` — word-local translation, scope, and basic capitalization proof.
- `src/braille_app/translation/expected_document.py` — phase-1 routing; existing extraction/alignment/provenance/highlighting reused.
- `src/braille_app/translation/liblouis_translator.py` — vendored runtime identity checks.
- `src/braille_app/validation_profiles.py` — profile aliases for phase-1 PDF normalization.
- `src/braille_app/validation/api.py` — explicit profile parameter; default path unchanged.
- `tests/test_uncontracted_phase1.py` and `scripts/uncontracted_phase1_acceptance.py` — deterministic/unit and PDF end-to-end checks.

## Validation path

`master extraction → phase-1 source normalization → unicode.dis,en-ueb-g1.ctb → expected uncontracted Braille → existing continuous alignment → existing provenance mapping → existing PDF blue-box localization`

## Liblouis identity

- Version: `3.38.0`
- Table list: `unicode.dis,en-ueb-g1.ctb`
- Table path: `O:\braille_0.2\vendor\liblouis-win64\share\liblouis\tables\en-ueb-g1.ctb`
- `en-ueb-g1.ctb` SHA-256: `446717b55e49ff41aef2c204b58ea1d2872a77a4473a821e766bffd51cee0b4d`
- `unicode.dis` path: `O:\braille_0.2\vendor\liblouis-win64\share\liblouis\tables\unicode.dis`

## Cases tested

| Family | Clean errors/reviews | Corrupted errors | Non-error neighbor |
|---|---:|---:|---:|
| lowercase alphabet a-z | 0/0 | 1 | 0 |
| uppercase alphabet A-Z | 0/0 | 1 | 0 |
| ordinary words | 0/0 | 1 | 0 |
| capitalized words | 0/0 | 1 | 0 |
| isolated capitals A/B/D/Z | 0/0 | 1 | 0 |
| supported ordinary sentence | 0/0 | 1 | 0 |

PDF fixture clean result: `0` confirmed errors, `0` reviews.
PDF fixture corrupted result: `4` detected, `0` false positives, `0` duplicates, `4` exact cell/page matches, `4` blue boxes.
The missing capital indicator is localized to its following actual letter cell; substitutions are localized to their changed actual cell. No blank or neighboring cell is boxed.

Exact corrupted-fixture localization:

| Finding | Rule | Physical page | Actual cell range |
|---|---|---:|---:|
| `VAL-ERR-0001` | `UEB_PHASE1_SCOPE` | 1 | `12-13` |
| `VAL-ERR-0002` | `UEB_8` | 1 | `157-158` |
| `VAL-ERR-0003` | `UEB_PHASE1_SCOPE` | 1 | `195-196` |
| `VAL-ERR-0004` | `UEB_PHASE1_SCOPE` | 1 | `214-215` |

## Unsupported/fail-closed behavior

Unsupported source is REVIEW-only and emits zero confirmed errors. Candidate translation is not generated for rejected source constructs; no unsupported construct is promoted to an error.

## Old validator regression

PASS — current packaged executable dense gate: 185/185 detected, 185/185 exact; clean 0 errors.

Numbers and punctuation were deliberately not started.
