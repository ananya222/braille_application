# UEB Grade 1 / Liblouis audit

Authority: ICEB, *Rules of Unified English Braille, Third Edition 2024*, local PDF `rules/Rules-of-Unified-English-Braille-2024.pdf`. Liblouis is treated as the implementation candidate only.

Scope: English-only, uncontracted UEB / Grade 1. Contracted UEB, Nemeth, mathematics, chemistry, music and specialist notation are not production scope.

## Evidence boundary

The installed application path is the vendored Liblouis 3.38.0 DLL plus `unicode.dis,en-ueb-g1.ctb`. The separate `C:\liblouis` installation is also 3.38.0 but has a different `en-ueb-g1.ctb` hash; results below use the project-vendored runtime only.

Tests are focused probes, not a proof by percentage. Official rulebook examples that are contracted are marked `N/A-GRADE` and are never compared directly with Grade 1 output.

## Final evidence table

| Citation | Feature | Source | Expected | Liblouis | Evidence | Status | Existing upstream test | Gap classification | Notes |
|---|---|---|---|---|---|---|---|---|---|
| 4.1 | Alphabet | `a` | `1` | `1` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `b` | `12` | `12` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `c` | `14` | `14` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `d` | `145` | `145` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `e` | `15` | `15` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `f` | `124` | `124` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `g` | `1245` | `1245` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `h` | `125` | `125` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `i` | `24` | `24` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `j` | `245` | `245` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `k` | `13` | `13` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `l` | `123` | `123` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `m` | `134` | `134` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `n` | `1345` | `1345` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `o` | `135` | `135` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `p` | `1234` | `1234` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `q` | `12345` | `12345` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `r` | `1235` | `1235` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `s` | `234` | `234` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `t` | `2345` | `2345` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `u` | `136` | `136` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `v` | `1236` | `1236` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `w` | `2456` | `2456` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `x` | `1346` | `1346` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `y` | `13456` | `13456` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `z` | `1356` | `1356` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `A` | `6 1` | `6 1` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `B` | `6 12` | `6 12` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `C` | `6 14` | `6 14` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `D` | `6 145` | `6 145` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `E` | `6 15` | `6 15` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `F` | `6 124` | `6 124` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `G` | `6 1245` | `6 1245` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `H` | `6 125` | `6 125` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `I` | `6 24` | `6 24` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `J` | `6 245` | `6 245` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `K` | `6 13` | `6 13` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `L` | `6 123` | `6 123` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `M` | `6 134` | `6 134` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `N` | `6 1345` | `6 1345` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `O` | `6 135` | `6 135` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `P` | `6 1234` | `6 1234` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `Q` | `6 12345` | `6 12345` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `R` | `6 1235` | `6 1235` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `S` | `6 234` | `6 234` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `T` | `6 2345` | `6 2345` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `U` | `6 136` | `6 136` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `V` | `6 1236` | `6 1236` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `W` | `6 2456` | `6 2456` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `X` | `6 1346` | `6 1346` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `Y` | `6 13456` | `6 13456` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1 | Alphabet | `Z` | `6 1356` | `6 1356` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE | Direct alphabet table entry. |
| 4.1, 2.5.5 | Alphabet | `hello` | `125 15 123 123 135` | `125 15 123 123 135` | DERIVED | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE |  |
| 4.1, 2.5.5 | Alphabet | `Braille Validator` | `6 12 1235 1 24 123 123 15 0 6 1236 1 123 24 145 1 2345 135 1235` | `6 12 1235 1 24 123 123 15 0 6 1236 1 123 24 145 1 2345 135 1235` | DERIVED | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE |  |
| 4.1, 2.5.5 | Alphabet | `ordinary words` | `135 1235 145 24 1345 1 1235 13456 0 2456 135 1235 145 234` | `135 1235 145 24 1345 1 1235 13456 0 2456 135 1235 145 234` | DERIVED | PASS | en-ueb-symbols_harness.yaml (direct letters) | NONE |  |
| 8.3.1 | Capitalization | `A` | `6 1` | `6 1` | OFFICIAL | PASS | en-ueb-g1_harness.yaml; yaml/capitalization.yaml; yaml/capsword.yaml | NONE | Also covered by the alphabet list. |
| 8.1, 8.3.1 | Capitalization | `Hello` | `6 125 15 123 123 135` | `6 125 15 123 123 135` | DERIVED | PASS | en-ueb-g1_harness.yaml; yaml/capitalization.yaml; yaml/capsword.yaml | NONE |  |
| 8.4, 8.8 | Capitalization | `ALL` | `6 6 1 123 123` | `6 6 1 123 123` | DERIVED | PASS | en-ueb-g1_harness.yaml; yaml/capitalization.yaml; yaml/capsword.yaml | NONE | Capitalised word mode is the canonical form. |
| 8.4 | Capitalization | `AB CD` | `6 6 1 12 0 6 6 14 145` | `6 6 1 12 0 6 6 14 145` | DERIVED | PASS | en-ueb-g1_harness.yaml; yaml/capitalization.yaml; yaml/capsword.yaml | NONE |  |
| 6.5.2, 8.4 | Capitalization | `123 CARD` | `3456 1 12 14 0 6 6 14 1 1235 145` | `3456 1 12 14 0 6 6 14 1 1235 145` | DERIVED | PASS | en-ueb-g1_harness.yaml; yaml/capitalization.yaml; yaml/capsword.yaml | NONE |  |
| 6.3, 8.3.1 | Capitalization | `123Card` | `3456 1 12 14 6 14 1 1235 145` | `3456 1 12 14 6 14 1 1235 145` | DERIVED | PASS | en-ueb-g1_harness.yaml; yaml/capitalization.yaml; yaml/capsword.yaml | NONE |  |
| 8.5-8.6 | Capitalization | `CAUTION: WET PAINT!` | `6 6 6 14 1 136 2345 24 135 1345 25 0 2456 15 2345 0 1234 1 24 1345 2345 235 6 3` | `6 6 6 14 1 136 2345 24 135 1345 25 0 2456 15 2345 0 1234 1 24 1345 2345 235 6 3` | OFFICIAL | PASS | en-ueb-g1_harness.yaml; yaml/capitalization.yaml; yaml/capsword.yaml | NONE | Official passage example family; print source has three symbols-sequences. |
| 8.4, 8.7 | Capitalization | `Hello, WORLD!` | `6 125 15 123 123 135 2 0 6 6 2456 135 1235 123 145 235` | `6 125 15 123 123 135 2 0 6 6 2456 135 1235 123 145 235` | DERIVED | PASS | en-ueb-g1_harness.yaml; yaml/capitalization.yaml; yaml/capsword.yaml | NONE |  |
| 6.1 | Numeric | `0` | `3456 245` | `3456 245` | OFFICIAL | PASS | en-ueb-g1_harness.yaml; en-ueb-math.yaml; yaml/numericmode.yaml | NONE |  |
| 6.1-6.2 | Numeric | `1234567890` | `3456 1 12 14 145 15 124 1245 125 24 245` | `3456 1 12 14 145 15 124 1245 125 24 245` | OFFICIAL | PASS | en-ueb-g1_harness.yaml; en-ueb-math.yaml; yaml/numericmode.yaml | NONE |  |
| 6.2 | Numeric | `3.14` | `3456 14 256 1 145` | `3456 14 256 1 145` | OFFICIAL | PASS | en-ueb-g1_harness.yaml; en-ueb-math.yaml; yaml/numericmode.yaml | NONE |  |
| 6.2 | Numeric | `1,234` | `3456 1 2 12 14 145` | `3456 1 2 12 14 145` | OFFICIAL | PASS | en-ueb-g1_harness.yaml; en-ueb-math.yaml; yaml/numericmode.yaml | NONE |  |
| 6.6, 3.23 | Numeric | `1 234` | `3456 1 0 3456 12 14 145` | `3456 1 0 3456 12 14 145` | DERIVED | PASS-PROVISIONAL | en-ueb-g1_harness.yaml; en-ueb-math.yaml; yaml/numericmode.yaml | NONE | V1 plain-text policy: without explicit numeric-grouping semantics, treat the blank as an ordinary space. This is PASS-PROVISIONAL, not proof that every printed `1 234` is ordinary spacing. |
| 6.6, 6.6.1 | Numeric | `3 245 000` | `3456 14 5 12 145 5 245 245 245` | `3456 14 0 3456 12 145 15 0 3456 245 245 245` | DERIVED | FAIL | en-ueb-g1_harness.yaml; en-ueb-math.yaml; yaml/numericmode.yaml | TABLE_GAP | The source is explicitly treated as one grouped number for this probe, following the official population example; the plain-text Liblouis call has no semantic numeric-grouping input. |
| 6.6 | Numeric | `1 234` | `3456 1 5 12 14 145` | `3456 1 5 12 14 145` | OFFICIAL | PASS | en-ueb-g1_harness.yaml; en-ueb-math.yaml; yaml/numericmode.yaml | NONE | NBSP is used as an explicit numeric-space probe; expected is number sign, 1, numeric-space+2, 3, 4. |
| 6.3, 6.7 | Numeric | `7:30` | `3456 1245 25 3456 14 245` | `3456 1245 25 3456 14 245` | OFFICIAL | PASS | en-ueb-g1_harness.yaml; en-ueb-math.yaml; yaml/numericmode.yaml | NONE |  |
| 6.7 | Numeric | `12/31/2024` | `3456 1 12 456 34 3456 14 1 456 34 3456 12 245 12 145` | `3456 1 12 456 34 3456 14 1 456 34 3456 12 245 12 145` | OFFICIAL | PASS | en-ueb-g1_harness.yaml; en-ueb-math.yaml; yaml/numericmode.yaml | NONE |  |
| 3.10, 6.7 | Numeric | `$19.95` | `4 234 3456 1 24 256 24 15` | `4 234 3456 1 24 256 24 15` | OFFICIAL | PASS | en-ueb-g1_harness.yaml; en-ueb-math.yaml; yaml/numericmode.yaml | NONE |  |
| 6.5-6.7 | Numeric | `1st` | `3456 1 234 2345` | `3456 1 234 2345` | OFFICIAL | PASS | en-ueb-g1_harness.yaml; en-ueb-math.yaml; yaml/numericmode.yaml | NONE |  |
| 6.5.2 | Numeric | `3b` | `3456 14 56 12` | `3456 14 56 12` | OFFICIAL | PASS | en-ueb-g1_harness.yaml; en-ueb-math.yaml; yaml/numericmode.yaml | NONE |  |
| 6.5.2 | Numeric | `3m` | `3456 14 134` | `3456 14 134` | OFFICIAL | PASS | en-ueb-g1_harness.yaml; en-ueb-math.yaml; yaml/numericmode.yaml | NONE |  |
| 6.5.2 | Numeric | `4.2b` | `3456 145 256 12 56 12` | `3456 145 256 12 56 12` | OFFICIAL | PASS | en-ueb-g1_harness.yaml; en-ueb-math.yaml; yaml/numericmode.yaml | NONE |  |
| 6.4.1 | Numeric | `.7` | `3456 256 1245` | `3456 256 1245` | OFFICIAL | PASS | en-ueb-g1_harness.yaml; en-ueb-math.yaml; yaml/numericmode.yaml | NONE | Official rule 6.4.1 example family: a period before a number takes the numeric prefix before the period. |
| 7.1 | Punctuation | `comma, semicolon; colon:` | `14 135 134 134 1 2 0 234 15 134 24 14 135 123 135 1345 23 0 14 135 123 135 1345 25` | `14 135 134 134 1 2 0 234 15 134 24 14 135 123 135 1345 23 0 14 135 123 135 1345 25` | DERIVED | PASS | en-ueb-symbols_harness.yaml / en-ueb-g1_harness.yaml | NONE |  |
| 7.1 | Punctuation | `Full stop. Exclamation! Question?` | `6 124 136 123 123 0 234 2345 135 1234 256 0 6 15 1346 14 123 1 134 1 2345 24 135 1345 235 0 6 12345 136 15 234 2345 24 135 1345 236` | `6 124 136 123 123 0 234 2345 135 1234 256 0 6 15 1346 14 123 1 134 1 2345 24 135 1345 235 0 6 12345 136 15 234 2345 24 135 1345 236` | DERIVED | PASS | en-ueb-symbols_harness.yaml / en-ueb-g1_harness.yaml | NONE |  |
| 7.3 | Punctuation | `...` | `256 256 256` | `256 256 256` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml / en-ueb-g1_harness.yaml | NONE |  |
| 7.4 | Punctuation | `a/b` | `1 456 34 12` | `1 456 34 12` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml / en-ueb-g1_harness.yaml | NONE |  |
| 7.5.3 | Punctuation | `?` | `56 236` | `56 236` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml / en-ueb-g1_harness.yaml | NONE | Standalone question mark requires Grade 1 symbol indicator. |
| 7.1.1, 7.1.3, 10.6.2 | Punctuation | `a.b` | `1 256 12` | `1 256 12` | DERIVED | PASS | en-ueb-symbols_harness.yaml / en-ueb-g1_harness.yaml | NONE | No grade 1 indicator is required: the period is not a beginning-of-word dis groupsign position. |
| 7.1.3, 10.6.5, 5.11.1 | Punctuation | `a,b` | `1 56 2 12` | `1 56 2 12` | DERIVED | PASS | en-ueb-symbols_harness.yaml / en-ueb-g1_harness.yaml | NONE | The comma cell may also be a lower groupsign between letters, so grade 1 is required before the punctuation. |
| 7.5.1 | Punctuation | `what?` | `2456 125 1 2345 236` | `2456 125 1 2345 236` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml / en-ueb-g1_harness.yaml | NONE | Ordinary question-mark position: rule 7.5.1 says no grade 1 symbol indicator is normally required. |
| 7.6.1 | Quotes/apostrophes | `“hello”` | `236 125 15 123 123 135 356` | `236 125 15 123 123 135 356` | OFFICIAL | PASS | No dedicated quote/apostrophe file; partial en-ueb.yaml Grade 2 examples | NONE |  |
| 7.6.2 | Quotes/apostrophes | `‘hello’` | `6 236 125 15 123 123 135 6 356` | `6 236 125 15 123 123 135 6 356` | OFFICIAL | PASS | No dedicated quote/apostrophe file; partial en-ueb.yaml Grade 2 examples | NONE |  |
| 7.6.1, 7.6.5 | Quotes/apostrophes | `"hello"` | `236 125 15 123 123 135 356` | `236 125 15 123 123 135 356` | DERIVED | PASS | No dedicated quote/apostrophe file; partial en-ueb.yaml Grade 2 examples | NONE | Directional quote is inferred from ordinary prose context. |
| 7.6.2, 7.6.15 | Quotes/apostrophes | `'hello'` | `6 236 125 15 123 123 135 6 356` | `3 125 15 123 123 135 3` | DERIVED | FAIL | No dedicated quote/apostrophe file; partial en-ueb.yaml Grade 2 examples | LIBLOUIS_OUTDATED_RULE | Ordinary prose context calls for directional single quotes. |
| 7.6.6, 7.6.15 | Quotes/apostrophes | `can't` | `14 1 1345 3 2345` | `14 1 1345 3 2345` | OFFICIAL | PASS | No dedicated quote/apostrophe file; partial en-ueb.yaml Grade 2 examples | NONE |  |
| 7.6.6 | Quotes/apostrophes | `Jones'` | `6 245 135 1345 15 234 3` | `6 245 135 1345 15 234 3` | OFFICIAL | PASS | No dedicated quote/apostrophe file; partial en-ueb.yaml Grade 2 examples | NONE |  |
| 7.6.14-7.6.15 | Quotes/apostrophes | `'tis` | `3 2345 24 234` | `3 2345 24 234` | DERIVED | PASS | No dedicated quote/apostrophe file; partial en-ueb.yaml Grade 2 examples | NONE | Common leading-apostrophe dictionary word. |
| 7.6.6, 7.6.15 | Quotes/apostrophes | `can’t` | `14 1 1345 3 2345` | `14 1 1345 3 2345` | OFFICIAL | PASS | No dedicated quote/apostrophe file; partial en-ueb.yaml Grade 2 examples | NONE |  |
| 7.6.6 | Quotes/apostrophes | `Jones’` | `6 245 135 1345 15 234 3` | `6 245 135 1345 15 234 3` | OFFICIAL | PASS | No dedicated quote/apostrophe file; partial en-ueb.yaml Grade 2 examples | NONE | Curly print apostrophe still maps to apostrophe in UEB. |
| 7.6.3 | Quotes/apostrophes | `“She said, ‘yes’.”` | `236 6 234 125 15 0 234 1 24 145 2 0 6 236 13456 15 234 6 356 356` | `236 6 234 125 15 0 234 1 24 145 2 0 6 236 13456 15 234 3 256 356` | OFFICIAL | FAIL | No dedicated quote/apostrophe file; partial en-ueb.yaml Grade 2 examples | TABLE_GAP |  |
| 7.6.1 | Quotes/apostrophes | `"Hi!"` | `236 6 125 24 235 356` | `236 6 125 24 235 356` | DERIVED | PASS | No dedicated quote/apostrophe file; partial en-ueb.yaml Grade 2 examples | NONE |  |
| 7.6.7 | Quotes/apostrophes | `Franc“e”s` | `6 124 1235 1 1345 14 45 236 15 45 356 234` | `6 124 1235 1 1345 14 236 15 356 234` | OFFICIAL | FAIL | No dedicated quote/apostrophe file; partial en-ueb.yaml Grade 2 examples | TABLE_GAP | Official 7.6.7 example family: internal opening/closing double quotes require two-cell forms. |
| 2.6.2, 2.6.3, 7.6.8 | Quotes/apostrophes | `(“...”)` | `5 126 45 236 256 256 256 45 356 5 345` | `5 126 236 256 256 256 356 5 345` | DERIVED | FAIL | No dedicated quote/apostrophe file; partial en-ueb.yaml Grade 2 examples | TABLE_GAP | Standing-alone double quotation marks require the two-cell forms to avoid wordsign ambiguity. |
| 7.6.9 | Quotes/apostrophes | `Spell "W-a-l-k".` | `6 234 1234 15 123 123 0 236 56 56 6 2456 36 1 36 123 36 13 356 256` | `6 234 1234 15 123 123 0 236 6 2456 36 1 36 123 36 13 6 2356 256` | DERIVED | FAIL | No dedicated quote/apostrophe file; partial en-ueb.yaml Grade 2 examples | TABLE_GAP | The 2024 rule requires the opening double quote before the Grade 1 word indicator; the rest is rendered uncontracted for this probe. |
| 7.6.10 | Quotes/apostrophes | `‘ ’` | `56 6 236 0 56 6 356` | `6 236 0 6 356` | DERIVED | FAIL | No dedicated quote/apostrophe file; partial en-ueb.yaml Grade 2 examples | TABLE_GAP | Standing-alone single quotation marks need Grade 1 disambiguation; this is a focused symbol-level probe. |
| 7.2 | Hyphen/dash | `well-known` | `2456 15 123 123 36 13 1345 135 2456 1345` | `2456 15 123 123 36 13 1345 135 2456 1345` | DERIVED | PASS | en-ueb-symbols_harness.yaml / en-ueb-g1_harness.yaml | NONE |  |
| 7.2 | Hyphen/dash | `word – word` | `2456 135 1235 145 0 6 36 0 2456 135 1235 145` | `2456 135 1235 145 0 6 36 0 2456 135 1235 145` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml / en-ueb-g1_harness.yaml | NONE |  |
| 7.2 | Hyphen/dash | `word — word` | `2456 135 1235 145 0 6 36 0 2456 135 1235 145` | `2456 135 1235 145 0 6 36 0 2456 135 1235 145` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml / en-ueb-g1_harness.yaml | NONE |  |
| 7.2.6 | Hyphen/dash | `word -- word` | `2456 135 1235 145 0 36 36 0 2456 135 1235 145` | `2456 135 1235 145 0 36 36 0 2456 135 1235 145` | DERIVED | PASS | en-ueb-symbols_harness.yaml / en-ueb-g1_harness.yaml | NONE | Two adjacent print hyphens may remain two hyphens or be rendered as a dash. |
| 2.6, 7.1 | Brackets | `(hello)` | `5 126 125 15 123 123 135 5 345` | `5 126 125 15 123 123 135 5 345` | DERIVED | PASS | en-ueb-symbols_harness.yaml / en-ueb-g1_harness.yaml | NONE |  |
| 2.6, 7.1 | Brackets | `[hello]` | `46 126 125 15 123 123 135 46 345` | `46 126 125 15 123 123 135 46 345` | DERIVED | PASS | en-ueb-symbols_harness.yaml / en-ueb-g1_harness.yaml | NONE |  |
| 2.6, 7.1 | Brackets | `{hello}` | `456 126 125 15 123 123 135 456 345` | `456 126 125 15 123 123 135 456 345` | DERIVED | PASS | en-ueb-symbols_harness.yaml / en-ueb-g1_harness.yaml | NONE |  |
| 3.1, 3.7 | Symbols | `& @` | `4 12346 0 4 1` | `4 12346 0 4 1` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml | NONE |  |
| 3.19, 3.21 | Symbols | `% #` | `46 356 0 456 1456` | `46 356 0 456 1456` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml | NONE |  |
| 3.8 | Symbols | `© ® ™` | `45 14 0 45 1235 0 45 2345` | `45 14 0 45 1235 0 45 2345` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml | NONE |  |
| 3.10 | Symbols | `$ £ € ¥ ¢` | `4 234 0 4 123 0 4 15 0 4 13456 0 4 14` | `4 234 0 4 123 0 4 15 0 4 13456 0 4 14` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml | NONE |  |
| 3.11, 3.20 | Symbols | `° § ¶` | `45 245 0 45 234 0 45 1234` | `45 245 0 45 234 0 45 1234` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml | NONE |  |
| 3.11, 3.15 | Symbols | `6′ 9″` | `3456 124 2356 0 3456 24 2356 2356` | `3456 124 2356 0 3456 24 2356 2356` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml | NONE | Prime/minute/second signs follow print; included to close the prime half of the Section 3.11 scope row. |
| 3.5 | Symbols | `•` | `456 256` | `456 256` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml | NONE |  |
| 3.19 | Symbols | `#4` | `456 1456 3456 145` | `456 1456 3456 145` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml | NONE |  |
| 3.10, 6.7 | Symbols | `£7.50` | `4 123 3456 1245 256 15 245` | `4 123 3456 1245 256 15 245` | DERIVED | PASS | en-ueb-symbols_harness.yaml | NONE |  |
| 2.5.5, 5.11 | Grade-1 | `be` | `12 15` | `12 15` | OFFICIAL | PASS | en-ueb-g1_harness.yaml; en-ueb-math.yaml; yaml/numericmode.yaml | NONE | Uncontracted text does not require a Grade 1 indicator everywhere. |
| 5.6, 6.5.2 | Grade-1 | `22b` | `3456 12 12 56 12` | `3456 12 12 56 12` | OFFICIAL | PASS | en-ueb-g1_harness.yaml; en-ueb-math.yaml; yaml/numericmode.yaml | NONE |  |
| 5.6, 6.5.2 | Grade-1 | `22B` | `3456 12 12 6 12` | `3456 12 12 6 12` | OFFICIAL | PASS | en-ueb-g1_harness.yaml; en-ueb-math.yaml; yaml/numericmode.yaml | NONE |  |
| 5.6.2, 6.5.4 | Grade-1 | `3-D` | `3456 14 36 56 6 145` | `3456 14 36 6 145` | OFFICIAL | FAIL | en-ueb-g1_harness.yaml; en-ueb-math.yaml; yaml/numericmode.yaml | TABLE_GAP |  |
| 5.8.1 | Grade-1 | `3-D` | `3456 14 36 56 6 145` | `3456 14 36 6 145` | DERIVED | FAIL | en-ueb-g1_harness.yaml; en-ueb-math.yaml; yaml/numericmode.yaml | TABLE_GAP | The Grade 1 indicator precedes the capitals indicator after a numeric-mode terminator. |
| 3.23 | Spacing | `a b` | `1 0 12` | `1 0 12` | OFFICIAL | PASS | en-ueb-symbols_harness.yaml / en-ueb-g1_harness.yaml | NONE |  |
| 3.23 | Spacing | `a  b` | `1 0 12` | `1 0 0 12` | DERIVED | FAIL | en-ueb-symbols_harness.yaml / en-ueb-g1_harness.yaml | NORMALIZATION_PROBLEM | UEB 3.23.1 says the amount of ordinary print space is not important and variation is ignored; this is a normalization-layer case, not a numeric-space case. |
| 3.23 | Spacing | `a b` | `1 0 12` | `1 6 12` | DERIVED | FAIL | en-ueb-symbols_harness.yaml / en-ueb-g1_harness.yaml | NORMALIZATION_PROBLEM | V1 source-normalization policy: NBSP outside numeric context is mapped to an ordinary space before translation. Raw Liblouis output is not accepted without that normalization. |
| 3.23 | Spacing | `a b​a` | `1 0 12 0 1` | `1 0 12 0 1` | CONSTRUCTED | PASS-PROVISIONAL | en-ueb-symbols_harness.yaml / en-ueb-g1_harness.yaml | NONE | V1 source-normalization policy: U+2009 is ordinary spacing and U+200B is removed as an extraction separator in this plain-text probe; the resulting ordinary spaces are PASS-PROVISIONAL. |
| 9.2-9.4 | Typeforms | `italic` | `46 2 24 2345 1 123 24 14` | `46 2 24 2345 1 123 24 14` | DERIVED | PASS | en-ueb-g1_harness.yaml; en-ueb-g1_backward.yaml; yaml/emphasis.yaml | NONE |  |
| 9.2-9.4 | Typeforms | `bold` | `45 2 12 135 123 145` | `45 2 12 135 123 145` | DERIVED | PASS | en-ueb-g1_harness.yaml; en-ueb-g1_backward.yaml; yaml/emphasis.yaml | NONE |  |
| 9.2-9.4 | Typeforms | `under` | `456 2 136 1345 145 15 1235` | `456 2 136 1345 145 15 1235` | DERIVED | PASS | en-ueb-g1_harness.yaml; en-ueb-g1_backward.yaml; yaml/emphasis.yaml | NONE |  |
| 9.2.1 | Typeforms | `8` | `46 23 3456 125` | `46 23 3456 125` | OFFICIAL | PASS | en-ueb-g1_harness.yaml; en-ueb-g1_backward.yaml; yaml/emphasis.yaml | NONE | Official rule 9.2.1 example family: a typeform symbol indicator before a number. |
| 9.3.1 | Typeforms | `123` | `46 2 3456 1 12 14` | `46 2 3456 1 12 14` | DERIVED | PASS | en-ueb-g1_harness.yaml; en-ueb-g1_backward.yaml; yaml/emphasis.yaml | NONE | Rule 9.3.1 permits a typeform word indicator to set the typeform for the following numeric symbols-sequence. |
| 9.4 | Typeforms | `one two three` | `46 2356 135 1345 15 0 2345 2456 135 0 2345 125 1235 15 15 46 3` | `46 2356 135 1345 15 0 2345 2456 135 0 2345 125 1235 15 15 46 3` | DERIVED | PASS | en-ueb-g1_harness.yaml; en-ueb-g1_backward.yaml; yaml/emphasis.yaml | NONE | Three typeformed symbols-sequences exercise passage opening and termination. |
| 9.7.2 | Typeforms | `word!` | `46 2 2456 135 1235 145 46 3 235` | `46 2 2456 135 1235 145 46 3 235` | DERIVED | PASS | en-ueb-g1_harness.yaml; en-ueb-g1_backward.yaml; yaml/emphasis.yaml | NONE | Punctuation is outside the supplied word typeform, so the terminator precedes it. |
| 9.8.1 | Typeforms | `word` | `45 2 46 2 2456 135 1235 145` | `45 2 46 2 2456 135 1235 145` | DERIVED | PASS | en-ueb-g1_harness.yaml; en-ueb-g1_backward.yaml; yaml/emphasis.yaml | NONE | Two simultaneous typeforms; Liblouis chooses an order, while UEB does not prescribe one. |
| 4.1, 2.5 | N/A-GRADE | `A boy and his dog were on the path.` | `N/A-GRADE` | `6 1 0 12 135 13456 0 1 1345 145 0 125 24 234 0 145 135 1245 0 2456 15 1235 15 0 135 1345 0 2345 125 15 0 1234 1 2345 125 256` | N/A-GRADE | N/A-GRADE | en-ueb.yaml (Grade 2 only; not comparable) | N/A-GRADE | Rulebook example is contracted; deliberately not compared with en-ueb-g1. |
| 7.6 | N/A-GRADE | `“Why is that?” he asked.` | `N/A-GRADE` | `236 6 2456 125 13456 0 24 234 0 2345 125 1 2345 236 356 0 125 15 0 1 234 13 15 145 256` | N/A-GRADE | N/A-GRADE | en-ueb.yaml (Grade 2 only; not comparable) | N/A-GRADE | Rulebook example is contracted; deliberately not compared with en-ueb-g1. |
| 6.7 | N/A-GRADE | `The temperature was 100,000°C.` | `N/A-GRADE` | `6 2345 125 15 0 2345 15 134 1234 15 1235 1 2345 136 1235 15 0 2456 1 234 0 3456 1 245 245 2 245 245 245 45 245 6 14 256` | N/A-GRADE | N/A-GRADE | en-ueb.yaml (Grade 2 only; not comparable) | N/A-GRADE | Rulebook example is contracted; deliberately not compared with en-ueb-g1. |

## Summary

Required UEB subrules audited: **77** scope rows (the finite rule-family checklist is in `standard_scope.csv`).

| Status | Count |
|---|---:|
| PASS | 121 |
| PASS-VARIANT | 0 |
| FAIL | 11 |
| UNCERTAIN | 0 |
| UNSUPPORTED | 0 |
| N/A-GRADE | 3 |
| PASS-PROVISIONAL | 2 |
| FAIL-PROVISIONAL | 0 |

`UNSUPPORTED` is zero in the executed corpus because its probes are either in-scope or deliberately `N/A-GRADE`; the out-of-scope families listed below are intended to be rejected by the V1 scope gate, not translated as proof of support.

### Coverage by family

| Family | Cases | PASS | PASS-VARIANT | PASS-PROVISIONAL | FAIL | FAIL-PROVISIONAL | UNCERTAIN | UNSUPPORTED | N/A-GRADE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Alphabet | 55 | 55 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Capitalization | 8 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Numeric | 15 | 13 | 0 | 1 | 1 | 0 | 0 | 0 | 0 |
| Grade-1 | 5 | 3 | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| Punctuation | 8 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Quotes/apostrophes | 15 | 9 | 0 | 0 | 6 | 0 | 0 | 0 | 0 |
| Hyphen/dash | 4 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Brackets | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Symbols | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Spacing | 4 | 1 | 0 | 1 | 2 | 0 | 0 | 0 | 0 |
| Typeforms | 8 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## 1. Reuse directly after verification

- English a-z/A-Z cell mappings and ordinary letter-by-letter Grade 1 translation.
- Core digits, decimal/comma numeric cells, basic brackets, common symbol cells, ordinary punctuation, and direct hyphen/dash cells where the source has unambiguous print semantics.
- Liblouis's typeform API and its existing italic/bold/underline tables are usable as a low-level candidate, subject to the validator's structured typeform input.

## 2. Wrap / normalize / acceptance-set handling

- Treat the vendored runtime and table hashes as part of the expected-output contract; do not substitute the system table silently.
- Add a UEB-2024 contextual layer for quote/apostrophe classification, Grade 1 optionality, numeric spaces, punctuation standing-alone cases, and capitals word/passage boundaries.
- Preserve cited variants only: Grade 1 indicator omission/presence where 5.10 permits it, cap-word choice where 8.8 permits it, and the double-hyphen/dash choice in 7.2.6. Do not turn every Liblouis difference into a tolerance.
- Apply the recorded source policy before translation: collapse repeated ordinary spaces, map NBSP/thin spaces to ordinary spacing outside numeric contexts, and remove U+200B extraction separators; retain an explicit ambiguity path where source semantics are unavailable.

## 3. Override

The executed failures identify where the table's static rules do not satisfy the 2024 contextual requirement: ASCII directional single-quote inference, the closing single quote in nested curly-quote context, two-cell internal/standing-alone double-quote selection, and the required Grade 1 + capital ordering after a numeric-mode hyphen. Clear numeric-space grouping requires semantic input that the plain table call does not receive; repeated spaces and non-ordinary whitespace are handled by the recorded normalization policy. Typeform + number is resolved for the exercised cases. These are evidence-backed override candidates only; no production fix is proposed in this audit.

## 4. Implement ourselves

- A finite acceptance-set/standards-verification layer around Liblouis output; two cited alternatives are currently modeled in `accepted_variants.csv`, and neither was emitted by this run.
- Quote/apostrophe context classification with a small apostrophe-word dictionary and an explicit expert-review path for ambiguous print.
- Numeric-space intent and numeric-mode termination checks based on source semantics, not only codepoint mapping.
- Capital word/passage selection and terminator validation, including indicator ordering around numbers and punctuation.
- Fail-closed scope detection for specialist notation and unsupported non-ASCII material.

## 5. Unsupported for V1

Contracted UEB / Grade 2, Nemeth, mathematics semantics, chemistry, music, multiline/layout-dependent indicators, foreign-language braille, IPA, technical code switching, and transcriber-defined typeforms remain unsupported. The presence of `en-ueb-math.ctb` in the Grade 1 include closure is an implementation detail, not V1 scope support.

## Answers to the final questions

1. **Base generator?** Yes, conditionally: the vendored `en-ueb-g1.ctb` is a useful low-level BASE expected-Braille generator for ordinary alphabetic Grade 1 text and direct symbols, but not a correctness authority and not safe as the sole validator oracle.
2. **Correction/verification layer?** Required for quote/apostrophe context, numeric mode and 2024 numeric spaces, capitalization word/passage/terminator decisions, Grade 1 optionality/indicator ordering, punctuation standing-alone cases, spacing normalization, and typeform placement/variants.
3. **Remain unsupported?** Grade 2, Nemeth, mathematics/chemistry/music, foreign/specialist code switches, layout-dependent passages, and ambiguous source punctuation without expert or document context.
4. **Engineering remaining?** The core cell generator is reusable; credible shipping still requires a standards layer, fail-closed scope gate, acceptance-set model, quote/apostrophe dictionary/uncertainty path, numeric/capitalization verification, and a larger ICEB-2024 regression corpus. This audit does not claim ship readiness.

Supporting artifacts: `environment.md`, `standard_extract.txt`, `standard_scope.csv`, `liblouis_implementation_matrix.csv`, `upstream_test_coverage.md`, `corpus.csv`, `execution_results.csv`, `accepted_variants.csv`, `coverage_matrix.csv`, and `coverage_closure.md`.
