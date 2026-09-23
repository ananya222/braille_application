# Liblouis upstream test coverage

Inspected source tree: `vendor/liblouis-src/liblouis-3.38.0/tests`.
These tests are evidence of implementation behavior only. They are not proof of compliance with ICEB, Rules of Unified English Braille, Third Edition 2024.
The UEB corpus comments describe the 2013 rulebook structure; the harnesses contain no claim that they were updated for the 2024 edition.

| File | Direction | Table | Count | 2024/V1 assessment |
|---|---|---|---:|---|
| `braille-specs/en-ueb-g1_harness.yaml` | forward | `en-ueb-g1.ctb` | 67 | 3.38.0 UEB harness; no 2024 citation |
| `braille-specs/en-ueb-g1_backward.yaml` | backward | `en-ueb-g1.ctb` | 26 | 3.38.0 backward harness; emphasis tests are engine tests |
| `braille-specs/en-ueb-symbols_harness.yaml` | forward | `en-ueb-g1.ctb` | 593 | 3.38.0 symbol harness; direct symbols, not contextual 2024 rules |
| `braille-specs/en-ueb-math.yaml` | forward | `en-ueb-g1.ctb` | 8 | 3.38.0 math-symbol smoke tests; out of V1 semantics |
| `braille-specs/en-ueb.yaml` | forward | `en-ueb-g2.ctb` | 2225 | Grade 2 / 2013-structured UEB corpus; not a G1 proof |
| `yaml/numericmode.yaml` | engine | `custom numeric tables` | 49 | Opcode engine tests, not ICEB UEB 2024 compliance |
| `yaml/capitalization.yaml` | engine | `custom capitalization tables` | 17 | Opcode engine tests, not ICEB UEB 2024 compliance |
| `yaml/emphasis.yaml` | engine | `custom emphasis tables` | 13 | Typeform engine tests, not ICEB UEB 2024 compliance |
| `yaml/capsword.yaml` | engine | `custom capitalization tables` | 25 | Capsword opcode tests, not ICEB UEB 2024 compliance |

## Requested files that are not present

The following names were not found in the Liblouis 3.38.0 checkout: `en-ueb-03-symbols`, `en-ueb-05-grade_1_mode`, `en-ueb-06-numeric_mode`, `en-ueb-08-capitalization`, `en-ueb-09-typeforms`, and dedicated quote/apostrophe test files. Their closest corresponding coverage is embedded in `en-ueb.yaml`, `en-ueb-symbols_harness.yaml`, `en-ueb-g1_harness.yaml`, and generic YAML engine tests.

## Coverage conclusion

`en-ueb-g1_harness.yaml` covers direct symbols, digits, some modifiers, four ordinal forms, and forward typeform examples. `en-ueb-g1_backward.yaml` covers digits, indicator backtranslation, and emphasis detection. `en-ueb-symbols_harness.yaml` is broad for one-symbol mappings but deliberately tests ASCII double quote as nondirectional (`⠠⠶`), which cannot establish the context-sensitive 2024 quote rules. The upstream tests do not provide a dedicated audit of 2024 numeric-space semantics, quote/apostrophe heuristics, Grade 1 optionality, or capital passage policy.
