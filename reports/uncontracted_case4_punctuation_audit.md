# Case 4 — Core Punctuation Audit

**Scope:** comma, period/full stop, question mark, exclamation mark, colon,
semicolon, with already-supported English, numeric, capitalization, and the
narrow numeric-hyphen interactions needed by Case 3. Quotes, apostrophes,
other hyphens/dashes, brackets, symbols, and typeforms remain unsupported.

## Authority and implementation identity

Authority: ICEB, *Rules of Unified English Braille*, Third Edition (2024),
local source `rules/Rules-of-Unified-English-Braille-2024.pdf`. Section 7.1
requires print-following punctuation except where a specific rule applies,
limits punctuation-following braille spacing to one blank cell, and requires a
Grade 1 symbol indicator when punctuation would be read as a contraction
(printed pp. 75–78; PDF pp. 103–106). Section 7.5 gives the question-mark
indicator exceptions, including a mark after a space, hyphen, or dash (printed
p. 81; PDF p. 109). Numeric period interactions use §6.4.1 (printed p. 68;
PDF p. 96).

Fresh translation probes used the application’s audited vendored Liblouis
3.38.0 runtime. Call: `LiblouisTranslator.translate_prose_with_positions`,
which calls `louis.translate(["unicode.dis", "en-ueb-g1.ctb"], source)` with
default options. Table list: `unicode.dis,en-ueb-g1.ctb`. Table path:
`vendor/liblouis-win64/share/liblouis/tables/en-ueb-g1.ctb`. SHA-256:
`446717b55e49ff41aef2c204b58ea1d2872a77a4473a821e766bffd51cee0b4d`.

## Context audit

| Behavior | Example / required cells | UEB 2024 basis | Fresh Liblouis output | Decision |
|---|---|---|---|---|
| Ordinary comma | `Hello, world.` → `⠠⠓⠑⠇⠇⠕⠂⠀⠺⠕⠗⠇⠙⠲` | §§7.1.1–7.1.2 | Exact | Direct |
| Comma whose cell could read as a contraction | `a,b` → `⠁⠰⠂⠃` | §7.1.3 | Exact | Direct; preserve indicator |
| Sentence/full stop | `Hello.` → full-stop cell `⠲` | §§7.1.1–7.1.2 | Exact | Direct |
| Period before a number / decimal | `No. 4`; `8.93` | §§7.1.1, 6.4.1 | Exact | Direct; Case 3 numeric path retained |
| Ordinary question | `What?` → final `⠦` | §§7.5.1–7.5.2 | Exact | Direct |
| Standing-alone / space-following question | `?`; `? x`; `x ?` | §§7.5.3–7.5.4 | Exact, including required `⠰` in these contexts | Direct |
| Question after numeric hyphen/dash | `10:30-?` → `⠼⠁⠚⠒⠼⠉⠚⠤⠰⠦` | §7.5.4; §6.7.1 numeric time | Liblouis emits `...⠤⠦` without `⠰` | **Gap:** insert mapped `⠰` before `⠦` |
| Exclamation | `Stop!` → final `⠖` | §§7.1.1–7.1.3 | Exact | Direct |
| Colon | `The list: red.` → `⠒` | §§7.1.1–7.1.3 | Exact | Direct |
| Semicolon | `red; green.` → `⠆` | §§7.1.1–7.1.3 | Exact | Direct |
| Punctuation in contraction-sensitive position | `a;b`, `a:b`, `a!b`, `a?b` | §§7.1.3, 7.5.2 | Exact Grade 1 symbol indicator placement | Direct |
| Multiple print blanks after punctuation | `Hello,   world.` | §7.1.2 | Liblouis preserves three blank cells | **Gap:** remove mapped surplus blanks, keeping one |

The six punctuation cells are the standard forms listed on printed p. 75
(PDF p. 103): comma `⠂`, semicolon `⠆`, colon `⠒`, full stop `⠲`,
exclamation `⠖`, and question `⠦`. The tested contexts have one mandated
form; no permitted alternate was identified, so no acceptance set is used.
Question-mark indicator placement is not generalized beyond the cited UEB
contexts. The dash correction is enabled only when a numeric hyphen/dash is
followed by a supported question-mark context; unrelated hyphen/dash text is
review-only.

## Production action

Use Liblouis directly for ordinary punctuation and its tested Grade 1
indicator contexts. Apply two small source-position-mapped corrections only:

1. UEB §7.5.4: add `⠰` before a question mark following an in-scope numeric
   hyphen/dash (including cited punctuation intervening before `?`).
2. UEB §7.1.2: reduce consecutive source blanks immediately after a supported
   punctuation mark to one braille blank cell.

Unsupported characters and out-of-scope hyphen/dash contexts fail closed to
Review. They are not translated into confirmed errors. No alignment,
provenance, or PDF-highlighting algorithm is introduced for Case 4; validation
uses the existing bounded Case 3 physical-page path.

## Frozen end-to-end closure

The frozen fixture contains 500 actions: comma 80, period 80, question 70,
exclamation 70, colon 60, semicolon 60, punctuation Grade 1 40,
punctuation/capitalization/numeric interactions 20, repeated-context/boundary
20. It has 26 physical pages (22 natural and 3 manual transitions) and mixes
deletion, insertion, substitution, duplicate, and transposition actions. Its
independent integrity check recorded zero out-of-scope targets and exact
manifest replay. Frozen hashes and full physical checks are recorded in
`reports/autonomous_case1_to_case4_progress.md`.

The first full localization evaluation found 127 mislocalized deletions. All
127 had the correct logical/source finding, but no provenance or box: the
zero-width deletion adapter supported Case 1–3 and omitted Case 4. A focused
deleted-comma PDF regression reproduced the missing anchor, then passed after
adding Case 4 to the existing next-semantic-cell deletion policy. No alignment
code changed.

Final frozen run: 500 findings for 500 actions, 442 direct and 58 proven
identical-run equivalents, 0 missed, 0 mislocalized, 0 ambiguous, 0 unmatched,
0 reviews, and 0 duplicate issue IDs. There are 606 physical target-cell
slots; 548 have strict historical-cell provenance and the remaining 58 are
accounted for by the established identical-run insertion equivalence. All
500 action boxes are rendered; policy-unexplained/off-region, wrong-page,
duplicate, and invalid-provenance boxes are zero. The 58 strict box-key
differences are all explained by that equivalence. Clean Case 4: 0 findings,
0 reviews, 0 duplicates, all 145/145 source passages aligned.
Machine-readable evidence is in `stress_test/uncontracted_case4_punctuation/results/`:
`case4_validation_result_after_deletion_anchor.json`,
`case4_observable_evaluation_after_deletion_anchor.json`,
`case4_mutation_outcomes_after_deletion_anchor.csv`, and
`case4_clean_validation_after_deletion_anchor.json`.
Visual QA rendered the complete 26-page clean and corrupted PDFs as page
contact sheets and inspected full pages 1, 13, and 26 from both versions;
the Braille rows remained legible and within page margins, with no observed
clipping or overlap.

The production path still uses vendored Liblouis plus the two cited small
corrections described above and reuses Case 3 page-local alignment,
provenance, and PDF localization. Relevant focused/regression tests pass
58/58. Real Duxbury clean verification remains **PENDING**; this fixture's
end-to-end checks use its frozen generated PDF/BRF and do not claim a manual
DBT run.
