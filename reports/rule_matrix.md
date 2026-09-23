# Standards Rule Matrix

This matrix is the human-readable view of the runtime catalogue in
`src/braille_app/rules/catalog.py`.  The three local PDFs named below are the
only standards authorities used for these entries.  Liblouis and Duxbury are
implementation/testing aids only.

| Rule ID | Standard | Family | Source rule | Source page | Scope | Trigger | Priority | Status | Test status |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| UEB_1 | UEB | introduction | 1 | 1-1 | ueb_prose | introduction | 100 | PARTIAL | NOT_TESTED |
| UEB_2 | UEB | general/modes | 2 | 7 | ueb_prose | general/modes | 100 | SOURCE_REQUIRED | NOT_TESTED |
| UEB_3 | UEB | symbols/indicators | 3 | 21 | ueb_prose | symbols/indicators | 100 | PARTIAL | NOT_TESTED |
| UEB_4 | UEB | letters/modifiers | 4 | 45 | ueb_prose | letters/modifiers | 100 | PARTIAL | NOT_TESTED |
| UEB_5 | UEB | grade-1 | 5 | 57 | ueb_prose | grade-1 | 100 | SOURCE_REQUIRED | NOT_TESTED |
| UEB_6 | UEB | numeric | 6 | 65 | ueb_prose | numeric | 20 | PARTIAL | NOT_TESTED |
| UEB_7 | UEB | punctuation | 7 | 75 | ueb_prose | punctuation | 40 | PARTIAL | NOT_TESTED |
| UEB_8 | UEB | capitalisation | 8 | 89 | ueb_prose | capitalisation | 35 | PARTIAL | NOT_TESTED |
| UEB_9 | UEB | typeforms | 9 | 101 | ueb_prose | typeforms | 100 | SOURCE_REQUIRED | NOT_TESTED |
| UEB_10 | UEB | contractions | 10 | 113 | ueb_prose | contractions | 30 | PARTIAL | TESTED |
| UEB_11 | UEB | technical | 11 | 181 | ueb_prose | technical | 100 | PARTIAL | TESTED |
| UEB_12 | UEB | early-english | 12 | 193 | ueb_prose | early-english | 100 | OUT_OF_SCOPE | NOT_TESTED |
| UEB_13 | UEB | foreign-language | 13 | 197 | ueb_prose | foreign-language | 100 | OUT_OF_SCOPE | NOT_TESTED |
| UEB_14 | UEB | code-switching | 14 | 211 | ueb_boundary | code-switching | 10 | PARTIAL | NOT_TESTED |
| UEB_15 | UEB | scansion | 15 | 223 | ueb_prose | scansion | 100 | OUT_OF_SCOPE | NOT_TESTED |
| UEB_16 | UEB | line-mode | 16 | 229 | ueb_prose | line-mode | 100 | OUT_OF_SCOPE | NOT_TESTED |
| NEMETH_1 | NEMETH | principles | 1 | 1-1 | nemeth_math | principles | 100 | PARTIAL | NOT_TESTED |
| NEMETH_2 | NEMETH | indicators | 2 | 2-1 | nemeth_math | indicators | 20 | PARTIAL | TESTED |
| NEMETH_3 | NEMETH | numeric | 3 | 3-1 | nemeth_math | numeric | 20 | PARTIAL | TESTED |
| NEMETH_4 | NEMETH | switching | 4 | 4-1 | code_boundary | switching | 10 | IMPLEMENTED | TESTED |
| NEMETH_5 | NEMETH | capitalisation | 5 | 5-1 | nemeth_math | capitalisation | 35 | PARTIAL | NOT_TESTED |
| NEMETH_6 | NEMETH | alphabets | 6 | 6-1 | nemeth_math | alphabets | 100 | PARTIAL | TESTED |
| NEMETH_7 | NEMETH | typeforms | 7 | 7-1 | nemeth_math | typeforms | 100 | SOURCE_REQUIRED | NOT_TESTED |
| NEMETH_8 | NEMETH | punctuation | 8 | 8-1 | nemeth_math | punctuation | 40 | PARTIAL | NOT_TESTED |
| NEMETH_9 | NEMETH | reference-signs | 9 | 9-1 | nemeth_math | reference-signs | 100 | SOURCE_REQUIRED | NOT_TESTED |
| NEMETH_10 | NEMETH | abbreviations | 10 | 10-1 | nemeth_math | abbreviations | 100 | SOURCE_REQUIRED | NOT_TESTED |
| NEMETH_11 | NEMETH | omissions | 11 | 11-1 | nemeth_math | omissions | 100 | SOURCE_REQUIRED | NOT_TESTED |
| NEMETH_12 | NEMETH | cancellation | 12 | 12-1 | nemeth_math | cancellation | 100 | OUT_OF_SCOPE | NOT_TESTED |
| NEMETH_13 | NEMETH | fractions | 13 | 13-1 | nemeth_math | fractions | 60 | SOURCE_REQUIRED | TESTED |
| NEMETH_14 | NEMETH | scripts | 14 | 14-1 | nemeth_math | scripts | 60 | PARTIAL | TESTED |
| NEMETH_15 | NEMETH | modifiers | 15 | 15-1 | nemeth_math | modifiers | 100 | SOURCE_REQUIRED | NOT_TESTED |
| NEMETH_16 | NEMETH | radicals | 16 | 16-1 | nemeth_math | radicals | 70 | SOURCE_REQUIRED | NOT_TESTED |
| NEMETH_17 | NEMETH | shapes | 17 | 17-1 | nemeth_math | shapes | 100 | SOURCE_REQUIRED | NOT_TESTED |
| NEMETH_18 | NEMETH | functions | 18 | 18-1 | nemeth_math | functions | 70 | SOURCE_REQUIRED | NOT_TESTED |
| NEMETH_19 | NEMETH | grouping | 19 | 19-1 | nemeth_math | grouping | 50 | PARTIAL | NOT_TESTED |
| NEMETH_20 | NEMETH | operations | 20 | 20-1 | nemeth_math | operations | 45 | PARTIAL | NOT_TESTED |
| NEMETH_21 | NEMETH | comparison | 21 | 21-1 | nemeth_math | comparison | 45 | PARTIAL | NOT_TESTED |
| NEMETH_22 | NEMETH | arrows | 22 | 22-1 | nemeth_math | arrows | 100 | SOURCE_REQUIRED | NOT_TESTED |
| NEMETH_23 | NEMETH | miscellaneous | 23 | 23-1 | nemeth_math | miscellaneous | 100 | PARTIAL | TESTED |
| NEMETH_24 | NEMETH | multipurpose | 24 | 24-1 | nemeth_math | multipurpose | 100 | SOURCE_REQUIRED | NOT_TESTED |
| NEMETH_25 | NEMETH | spatial | 25 | 25-1 | nemeth_math | spatial | 100 | OUT_OF_SCOPE | NOT_TESTED |
| NEMETH_26 | NEMETH | format | 26 | 26-1 | nemeth_math | format | 100 | PARTIAL | NOT_TESTED |
| BANA_4_2 | BANA/errata | switching | Nemeth 4.2 | PDF p. 8 | mixed_boundary | opening/closing switch | 10 | IMPLEMENTED | TESTED |
| BANA_4_6_8_C | BANA/errata | single-word-switch | Nemeth 4.6.8.c | PDF p. 10 | mixed_boundary | single-word switch | 10 | SOURCE_REQUIRED | NOT_TESTED |

## Runtime applicability

- `RuleRegistry.rules_for()` selects candidates by source node type (`text`,
  `mixed`, `math`, or `boundary`) and persistent `ValidationContext`.
- UEB prose rules exclude explicit Nemeth math spans.
- Nemeth math rules exclude ordinary prose; switching rules apply only at a
  mixed/boundary node.
- Candidates are ordered by explicit `priority`, then stable rule ID.
- The registry does not infer math from user Braille and does not replace the
  specialised verifiers.

Applicability metadata currently contains triggers on 44/44 entries,
exclusions on 40/44, explicit dependencies on 8/44, non-default precedence
on 18/44, and persistent mode open/close declarations on 6/44.  The remaining
families are intentionally marked for source-backed implementation before
they receive more specific predicates.

## Source authority

- `rules/Rules-of-Unified-English-Braille-2024.pdf`
- `rules/Nemeth_2022.pdf`
- `rules/Errata Nemeth Code 2022 Approved 10-2025.pdf`
