# UEB Grade 1 audit reconciliation

Date: 2026-09-22  
Authority: ICEB, *Rules of Unified English Braille, Third Edition 2024*, local file `rules/Rules-of-Unified-English-Braille-2024.pdf`.  Duxbury and Liblouis are implementation evidence only.

## Result

The disputed cases were re-run from a new process using only the vendored Liblouis runtime.  No existing Liblouis output or generated expected output was used for the translations.  The real Duxbury `.BRF` was read directly for the Duxbury cells; the PDF was not used for cell comparison.

The complete fresh per-call record is [reconciliation_fresh_raw.json](../stress_test/ueb_g1_duxbury_comparison/reconciliation_fresh_raw.json).  It contains, for every isolated/contextual call:

- the exact source and Unicode code-point array;
- the exact `louis.translateString(["unicode.dis", "en-ueb-g1.ctb"], source)` call;
- the table list and default/no-options mode;
- complete Unicode Braille output, output code points, and dot-cell notation.

## Runtime and Duxbury evidence

Fresh Liblouis call:

```text
louis.translateString(["unicode.dis", "en-ueb-g1.ctb"], source)
```

No flags, translation options, mode flags, or preprocessing were supplied.  The audited runtime was:

| Item | Value |
|---|---|
| Liblouis | 3.38.0 |
| DLL | `O:\braille_0.2\vendor\liblouis-win64\bin\liblouis.dll` |
| Table list | `unicode.dis,en-ueb-g1.ctb` |
| `en-ueb-g1.ctb` | `O:\braille_0.2\vendor\liblouis-win64\share\liblouis\tables\en-ueb-g1.ctb` |
| `en-ueb-g1.ctb` SHA-256 | `446717b55e49ff41aef2c204b58ea1d2872a77a4473a821e766bffd51cee0b4d` |
| `unicode.dis` SHA-256 | `28e39797dae5404cf3c0bdea3100f6da70eac8bdbd38a186d463462f4ace567c` |
| Duxbury | DBT 14.1 |
| Duxbury template/configuration | `Uncontracted` in the DXB evidence |
| BRF | `stress_test/ueb_g1_duxbury_comparison/ueb_g1_5page_stress.brf` |
| BRF SHA-256 | `15C1E8C6793C478B9EACBB8C265D7EC5AEC0B756EF66F6C967906A73560C0B4C` |
| DXB SHA-256 | `B0EDB711BCFA4893AD393AA955CBD1E93DED4C050ADE164A21055450DDBDE5A0` |
| PDF SHA-256 | `9D85F1F2BC7DE15E8D83B3485D0CD7F26E250FD38472A51F0D1CA06136E78F15` |

The BRF is readable, contains the complete five-page translated document, and contains no evidence of contracted Grade 2 output in the disputed strings.  The Duxbury PDF has five populated pages and was used only as a visual/reference check.

## Fresh translation results

These are the exact isolated results.  A blank cell is shown as `0` in dot notation.

| Source | Source code points | Fresh Liblouis Unicode | Liblouis dots | Standards-backed result |
|---|---|---|---|---|
| `3-D` | `U+0033 U+002D U+0044` | `⠼⠉⠤⠠⠙` | `3456 14 36 6 145` | `⠼⠉⠤⠰⠠⠙` |
| `a,b` | `U+0061 U+002C U+0062` | `⠁⠰⠂⠃` | `1 56 2 12` | `⠁⠰⠂⠃` |
| `a.b` | `U+0061 U+002E U+0062` | `⠁⠲⠃` | `1 256 12` | `⠁⠲⠃` |
| `'hello'` | `U+0027 U+0068 U+0065 U+006C U+006C U+006F U+0027` | `⠄⠓⠑⠇⠇⠕⠄` | `3 125 15 123 123 135 3` | Policy-dependent; this is valid as nondirectional straight-quote output |
| `‘hello’` | `U+2018 U+0068 U+0065 U+006C U+006C U+006F U+2019` | `⠠⠦⠓⠑⠇⠇⠕⠠⠴` | `6 236 125 15 123 123 135 6 356` | `⠠⠦⠓⠑⠇⠇⠕⠠⠴` |
| `“She said, ‘yes’.”` | `U+201C U+0053 U+0068 U+0065 U+0020 U+0073 U+0061 U+0069 U+0064 U+002C U+0020 U+2018 U+0079 U+0065 U+0073 U+2019 U+002E U+201D` | `⠦⠠⠎⠓⠑⠀⠎⠁⠊⠙⠂⠀⠠⠦⠽⠑⠎⠄⠲⠴` | `236 6 234 125 15 0 234 1 24 145 2 0 6 236 13456 15 234 3 256 356` | Inner closing quote must be `⠠⠴` under 7.6.2/7.6.3 |
| `She said, “Read ‘Peter Rabbit’ again.”` | `U+0053 U+0068 U+0065 U+0020 U+0073 U+0061 U+0069 U+0064 U+002C U+0020 U+201C U+0052 U+0065 U+0061 U+0064 U+0020 U+2018 U+0050 U+0065 U+0074 U+0065 U+0072 U+0020 U+0052 U+0061 U+0062 U+0062 U+0069 U+0074 U+2019 U+0020 U+0061 U+0067 U+0061 U+0069 U+006E U+002E U+201D` | `⠠⠎⠓⠑⠀⠎⠁⠊⠙⠂⠀⠦⠠⠗⠑⠁⠙⠀⠠⠦⠠⠏⠑⠞⠑⠗⠀⠠⠗⠁⠃⠃⠊⠞⠠⠴⠀⠁⠛⠁⠊⠝⠲⠴` | `6 234 125 15 0 234 1 24 145 2 0 236 6 1235 15 1 145 0 6 236 6 1234 15 2345 15 1235 0 6 1235 1 12 12 24 2345 6 356 0 1 1245 1 24 1345 256 356` | Matches the quote markers required by 7.6.3 |

The same results were checked in isolation, an ordinary sentence, the exact coverage-closure source, and the exact Duxbury-corpus source.  `3-D`, `a,b`, `a.b`, ASCII straight quotes, and curly standalone quotes did not change across those contexts.  The nested curly quote did change: Liblouis emitted the inner closing quote correctly in the `Peter Rabbit` context but emitted apostrophe dot 3 in the earlier `yes` context.  The full sentence outputs for every context are in the JSON evidence file.

## Real BRF cell extraction

The following values are direct ASCII-BRF substrings, converted with the existing Duxbury BRF cell map.  They are not inferred from the PDF.

| Case | BRF location | Exact BRF substring | Unicode cells | Dots |
|---|---|---|---|---|
| `3-D` | page 2, raw BRF line 31, `LETTERS NEAR NUMBERS` | `#C-,D` | `⠼⠉⠤⠠⠙` | `3456 14 36 6 145` |
| `a,b` | page 3, raw BRF line 61, `INTERNAL PUNCTUATION` | `A1B` | `⠁⠂⠃` | `1 2 12` |
| `a.b` | page 3, raw BRF line 61, `INTERNAL PUNCTUATION` | `A4B` | `⠁⠲⠃` | `1 256 12` |
| `'hello'` | page 3, raw BRF line 57, `QUOTE CONTEXTS` | `'HELLO'` | `⠄⠓⠑⠇⠇⠕⠄` | `3 125 15 123 123 135 3` |
| nested quotation | page 3, raw BRF lines 59–60, `NESTED QUOTATION` | `,SHE SAID1 8,READ ,8,PETER ,RABBIT,0 AGAIN40` | `⠠⠎⠓⠑⠀⠎⠁⠊⠙⠂⠀⠦⠠⠗⠑⠁⠙⠀⠠⠦⠠⠏⠑⠞⠑⠗⠀⠠⠗⠁⠃⠃⠊⠞⠠⠴⠀⠁⠛⠁⠊⠝⠲⠴` | `6 234 125 15 0 234 1 24 145 2 0 236 6 1235 15 1 145 0 6 236 6 1234 15 2345 15 1235 0 6 1235 1 12 12 24 2345 6 356 0 1 1245 1 24 1345 256 356` |

## Standards check

The following are the minimum rules needed for these decisions, quoted from the local 2024 PDF.

- **5.8.1:** “A grade 1 indicator precedes a capitalisation indicator.”  This fixes the order in `3-D` as `⠰⠠`, not `⠠⠰`.
- **5.11.1:** “In a work entirely in grade 1 braille (that is, using no contractions), grade 1 indicators are not used except as required for other reasons.”  This is not a blanket permission to remove an indicator required by another rule.
- **6.5.4:** “Grade 1 mode is terminated by a hyphen or dash ... Therefore, a letter or letters that could read as a contraction will need the grade 1 indicator.”  The rulebook’s explicit example is `3-D   ⠼⠉⠤⠰⠠⠙`.
- **7.1.1:** “Follow print for the use of punctuation except for the specific provisions in the Punctuation rules which follow.”
- **7.1.3:** “Place a grade 1 symbol indicator before a punctuation mark which appears in a position where it would be read as a contraction.”  This supports `a,b` as `⠁⠰⠂⠃`; the Duxbury omission is not authoritative.
- **7.6.2:** “Use single quotation marks ⠠⠦ and ⠠⠴ for single quotation marks in the print text.”
- **7.6.3:** “Follow print for outer and inner quotation marks.”  The official `She said, “Read ‘Peter Rabbit’ again.”` example supports the current nested Duxbury quote markers.
- **7.6.5:** “Use braille nondirectional double or single quotation marks, ⠠⠶ or ⠄, for print quotation marks without any slant or curl.”  This is why the straight ASCII `'hello'` result cannot automatically be called a Liblouis error.
- **7.6.12–7.6.13:** Translation software may offer quote assignment options, and print may not adequately distinguish a single quote from an apostrophe; without professional intervention the distinction “cannot be wholly automated with complete accuracy.”
- **7.6.15:** Software may use context: a mark between letters is an apostrophe, a mark at the beginning of a word is an opening single quote, and “in all other contexts” it is a closing single quote.  The rule says “may,” so this is not a universal mandatory override for every straight ASCII input.

## Reconciliation table

| Case | Earlier audit | Current raw Liblouis | Duxbury | UEB 2024 expected | Final conclusion | Why audits differed |
|---|---|---|---|---|---|---|
| `3-D` | Liblouis `⠼⠉⠤⠠⠙`; marked missing `⠰`; expected `⠼⠉⠤⠰⠠⠙` | Fresh calls consistently `⠼⠉⠤⠠⠙` in isolation, ordinary sentence, coverage source, and Dux source | `⠼⠉⠤⠠⠙` (`#C-,D`) | `⠼⠉⠤⠰⠠⠙` | Both engines agree, but both fail the cited 6.5.4 example | No source, context, invocation, or stale-output difference. The current report treated engine equality as standards conformance; that is an audit-logic error. |
| `a,b` | Required `⠁⠰⠂⠃` | Fresh calls consistently `⠁⠰⠂⠃` | `⠁⠂⠃` (`A1B`) | `⠁⠰⠂⠃` under 7.1.3 | Earlier standards decision stands; Duxbury is wrong for this case | Raw outputs were different in both audits. The current C adjudication incorrectly made Duxbury the authority and over-read 5.11.1; this is a standards/audit-logic error, not a translation-context difference. |
| `a.b` | PASS, no grade-1 indicator | Fresh `⠁⠲⠃` in all contexts | `⠁⠲⠃` (`A4B`) | `⠁⠲⠃` | Both match | No contradiction; included as the near-neighbor control for `a,b`. |
| `'hello'` | Called a Liblouis difference because directional `⠠⠦...⠠⠴` was treated as required | Fresh `⠄⠓⠑⠇⠇⠕⠄` in all contexts | Same cells (`'HELLO'`) | Either nondirectional `⠄...⠄` for straight print under 7.6.5, or directional cells if a documented quote-assignment policy selects them | Engine agreement is real and standards-compatible under the nondirectional interpretation; do not promote it to a universal quote rule | Same source and same fresh output. The earlier audit omitted/underweighted 7.6.5 and treated the optional software context heuristic as mandatory. |
| curly single quotes | `‘hello’` was independently expected as `⠠⠦...⠠⠴` | Fresh `⠠⠦⠓⠑⠇⠇⠕⠠⠴` | No standalone BRF case; the nested BRF uses the same directional cells | `⠠⠦...⠠⠴` | Liblouis handles this direct curly case | No contradiction; the source Unicode is different from ASCII U+0027. |
| nested quotation | Earlier exact source `“She said, ‘yes’.”` failed at inner close: Liblouis `⠄` vs expected `⠠⠴` | For the earlier source it still fails; for the Dux source it emits the correct `⠠⠴` | Dux source `She said, “Read ‘Peter Rabbit’ again.”` has `⠠⠴` and agrees with fresh Liblouis | Follow print under 7.6.2/7.6.3; inner close is `⠠⠴` in both strings | Earlier failure remains real; current Dux corpus is a different, passing context | Different source strings and surrounding context: `‘yes’.”` closes before punctuation, while `‘Peter Rabbit’ again` closes before a space. Liblouis changes its heuristic result. The current report incorrectly generalized one exact corpus agreement to the earlier case. |

## Root causes by category

- **Different source Unicode:** ASCII U+0027 is not the same input as curly U+2018/U+2019. The curly standalone case is correctly directional; the straight ASCII case is covered by the nondirectional rule/policy path.
- **Different surrounding context:** `“She said, ‘yes’.”` and `She said, “Read ‘Peter Rabbit’ again.”` are not the same test. Liblouis emits different inner-closing cells for them.
- **Different Liblouis invocation:** none found. All fresh translations used the same vendored `translateString` call and table list.
- **Different translation option:** none found. No options or modes were supplied.
- **Normalization:** none was applied to the disputed isolated translations. BRF line wrapping was removed only when locating logical BRF substrings; it did not change cells.
- **Stale output:** not the cause of the disputed Liblouis results. The fresh run reproduced the earlier raw Liblouis cells.
- **Audit logic error:** caused the `3-D` “exact” conclusion to be mistaken for UEB correctness and caused the `a,b` Duxbury adjudication to override the standards-backed result.
- **Standards interpretation error:** caused the earlier ASCII `'hello'` result to be treated as an unconditional directional-quote requirement despite 7.6.5 and the qualified software guidance in 7.6.12–7.6.15.

## Production decisions

1. Do not change production code as part of this reconciliation.
2. When numbers/Grade 1 interactions enter scope, add the cited `3-D` rule: after numeric-mode termination by hyphen/dash, emit/validate grade 1 before a capital indicator.
3. When punctuation enters scope, retain the `a,b` grade-1 symbol-indicator requirement. Do not adopt the Duxbury `A1B` form as an acceptance variant without a new standards finding.
4. Keep `a.b` without a grade-1 symbol indicator.
5. Keep quote handling outside the current Phase 1 production slice. For ASCII straight quotes, require an explicit source/quote policy or fail closed; do not silently force directional or nondirectional output for every U+0027 case.
6. For curly quotation marks and nested quotation, preserve print direction and outer/inner structure. The `yes`-before-punctuation Liblouis behavior needs a cited override or manual-review path; the `Peter Rabbit` context is evidence of a passing case, not proof that the heuristic is safe generally.
7. Never use Duxbury agreement as the standards oracle. Use ICEB 2024 to classify both engine outputs.

## Reconciliation status

**RECONCILIATION STATUS: PASS** — every contradiction has an identified explanation: engine agreement versus standards conformance for `3-D`; a standards/audit-logic error for `a,b`; a 7.6.5 interpretation error for ASCII quotes; and different source/context strings plus Liblouis context sensitivity for nested quotation.
