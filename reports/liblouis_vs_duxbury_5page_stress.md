# Liblouis versus Duxbury five-page UEB Grade 1 stress audit

Status: **comparison completed; production changes intentionally not made**.

This is an evidence-gathering audit only. ICEB UEB 2024 is the authority. Liblouis and Duxbury are implementation evidence, not standards authorities. Contracted UEB, Nemeth, mathematics, and specialist notation remain out of production scope.

## Files and audited runtimes

Frozen source inputs were not modified:

- `stress_test/ueb_g1_duxbury_comparison/ueb_g1_5page_stress.docx`
- `stress_test/ueb_g1_duxbury_comparison/ueb_g1_5page_stress.txt`
- `stress_test/ueb_g1_duxbury_comparison/source_case_manifest.csv`
- existing `liblouis_output.txt` and `liblouis_output.brf`

The comparison outputs are:

- `stress_test/ueb_g1_duxbury_comparison/aligned_differences.csv`
- `stress_test/ueb_g1_duxbury_comparison/adjudicated_differences.csv`
- this report

The audit comparator is `stress_test/ueb_g1_duxbury_comparison/compare_outputs.py`. It is audit-only and does not enter the validator path.

Liblouis was the audited vendored runtime only:

- version: `3.38.0`
- table list: `unicode.dis,en-ueb-g1.ctb`
- DLL: `O:\braille_0.2\vendor\liblouis-win64\bin\liblouis.dll`
- table: `O:\braille_0.2\vendor\liblouis-win64\share\liblouis\tables\en-ueb-g1.ctb`
- `en-ueb-g1.ctb` SHA-256: `446717b55e49ff41aef2c204b58ea1d2872a77a4473a821e766bffd51cee0b4d`
- `unicode.dis` SHA-256: `28e39797dae5404cf3c0bdea3100f6da70eac8bdbd38a186d463462f4ace567c`

Duxbury evidence:

- version: DBT `14.1.0.7124` / DBT 14.1
- primary BRF: `stress_test/ueb_g1_duxbury_comparison/ueb_g1_5page_stress.brf`
- BRF SHA-256: `15C1E8C6793C478B9EACBB8C265D7EC5AEC0B756EF66F6C967906A73560C0B4C`
- project evidence: `stress_test/ueb_g1_duxbury_comparison/ueb_g1_5page_stress.dxb`
- DXB SHA-256: `B0EDB711BCFA4893AD393AA955CBD1E93DED4C050ADE164A21055450DDBDE5A0`
- visual/reference PDF: `stress_test/ueb_g1_duxbury_comparison/ueb_g1_5page_stress.pdf`
- PDF SHA-256: `9D85F1F2BC7DE15E8D83B3485D0CD7F26E250FD38472A51F0D1CA06136E78F15`

Recorded Duxbury configuration evidence: selected template/configuration `Uncontracted` as embedded in the DXB; language/output family English UEB; Grade 1/uncontracted with contractions disabled; no Nemeth or mathematics; `11_w` output configuration. The DXB contains 36 body-text records, five heading records, and four explicit page-break records. No separate template filename or standalone quote-preference field is recoverable from the binary. Quote behavior was therefore recorded from the BRF itself rather than guessed from a missing setting field.

The BRF is ASCII-readable, has five content pages plus a trailing form-feed, and contains all 36 manifest body cases in source order. The rendered PDF has exactly five pages; all five pages contain Braille content and page furniture, with no blank or neighboring page observed. No blue-box validation run was performed because this is a translation comparison and production code was not changed.

Corpus-level uncontracted check: the tested ordinary words, alphabet, capitals, numbers, symbols, and quote examples are letter-by-letter or use explicit UEB indicators; no Grade 2 contraction form appeared in the 36 compared case streams. This is evidence about this corpus, not a universal DBT certification.

The frozen manifest has a pre-existing CSV data-order anomaly: its first data rows put page then source text beneath headers named `source_text` then `page`. It was not modified. The comparator detected the numeric-versus-text pattern and recovered the intended mapping read-only; all case IDs, source strings, and citations below use that recovered mapping.

## Comparable logical streams

The BRF was primary. Conversion used the existing Duxbury BRF cell map, not PDF text extraction. Only confirmed layout material was removed:

- Duxbury page-number footer lines and form-feed page breaks were removed.
- Duxbury line wrapping and paragraph indentation were converted to logical separators.
- Leading/trailing layout blanks were removed.
- Braille cells, punctuation, indicators, and interior source spaces were retained.
- Repeated source spaces were not collapsed by the comparator; the observed Duxbury collapse is reported as a difference.

Liblouis page/line separators were converted to logical separators using the already generated raw output. No translation-cell replacement or standards-based correction was applied before alignment.

The raw alignment produced 15 opcode-level differences. These were grouped into seven meaningful disagreements in `aligned_differences.csv`: punctuation indicators at three distinct source tokens, two typeform-representation groups, and two whitespace-policy groups.

## Adjudication against ICEB UEB 2024

Every grouped disagreement has a row in `adjudicated_differences.csv`.

> **Superseded correction — G001 (`a,b`):** The original classification below and the corresponding `adjudicated_differences.csv` entry are preserved as historical evidence, but are superseded for this case by [`ueb_g1_audit_reconciliation.md`](ueb_g1_audit_reconciliation.md). UEB 2024 §7.1.3 requires the Grade 1 symbol indicator here: Liblouis `⠁⠰⠂⠃` matches, while Duxbury `⠁⠂⠃` omits it. Duxbury is not authoritative. This correction is limited to G001; G002-G003 are not re-adjudicated here.

- `G001-G003` (original adjudication): classification **C**, Duxbury matches the cited UEB 2024 treatment for these ordinary uncontracted punctuation contexts; Liblouis adds an extra grade-1 symbol indicator. Evidence: UEB 5.11.1, 7.1.1, and 7.1.3.
- `G004-G005`: classification **E**, input/normalization policy. Duxbury received DOCX typeform metadata; the Liblouis audit call received plain text. Their base literary cells agree after the typeform markers are accounted for. Evidence boundary: UEB 9.1.1-9.8.1.
- `G006`: classification **D**, permitted ordinary-spacing variant. UEB 3.23.1 states that the amount of ordinary print space is not important; the Duxbury single blank and Liblouis preserved repeated blank are not a semantic translation disagreement.
- `G007`: classification **E**, unsupported input/normalization policy. Zero-width space is not ordinary UEB print spacing. Duxbury emits a visible escaped/symbol sequence while the Liblouis logical stream has no distinct zero-width cell. Evidence boundary: UEB 3.23.1; no silent reinterpretation is permitted.

No disagreement was classified B, F, or G. “No F/G disagreement” does not certify the untested general rule families; it means the seven observed differences were adjudicated or explicitly routed to policy.

## Known risk cases

| Risk case | Result |
|---|---|
| `hello` | Exact agreement; ordinary letters, no contraction |
| nested single quotes | Exact agreement in the supplied nested quotation |
| internal/standing-alone quotes | Exact agreement for the ASCII and nested contexts tested; broad quote policy remains outside this release slice |
| `3-D` | Exact agreement; numeric termination and capital interaction matched |
| `22b` | Exact agreement |
| `22B` | Exact agreement |
| `a.b` | Exact agreement |
| `a,b` | Original audit adjudicated Duxbury as C; superseded for G001 by UEB 2024 §7.1.3 reconciliation (Liblouis matches; Duxbury omits the required indicator) |
| numeric-space examples | Exact agreement for `1 234` and `12 345`; this does not generalize numeric-space policy |
| capitalization interactions | Exact agreement for tested alphabet, words, acronyms, isolated capitals, and numeric-adjacent capitals |
| common symbols | Exact agreement for tested symbols and contexts |
| Grade-1-sensitive cases | Exact agreement for tested numeric/letter and standing-alone cases |
| typeforms | Raw difference is source metadata: Duxbury emits typeform indicators, Liblouis plain-text path does not |
| repeated spaces | Duxbury emits one blank; Liblouis preserves two; classified D under UEB 3.23.1 |
| NBSP | Both appear as ordinary blank in the compared output; source distinction is an input-normalization policy, not certified semantics |
| thin space | Both appear as ordinary blank in the compared output; source distinction is not certified |
| zero-width space | Duxbury emits a visible escaped/symbol sequence; Liblouis emits no distinct cell; classified E and fail-closed |

## Family summary

Counts below are descriptive case counts. Categories overlap where a case intentionally exercises more than one family; “Same” means exact after layout normalization, before typeform metadata is stripped.

| Family | Cases | Same | Liblouis supported | Duxbury supported | Variants | Policy/Ambiguous |
|---|---:|---:|---:|---:|---:|---:|
| alphabet | 2 | 2 | 2 | 2 | 0 | 0 |
| capitalization | 4 | 4 | 4 | 4 | 0 | 0 |
| numbers | 4 | 4 | 4 | 4 | 0 | 0 |
| numeric interactions | 6 | 6 | 6 | 6 | 0 | 0 |
| punctuation | 4 | 2 | 4 | 4 | 0 | 2 |
| hyphen/dash | 2 | 2 | 2 | 2 | 0 | 0 |
| brackets | 1 | 1 | 1 | 1 | 0 | 0 |
| quotes | 3 | 3 | 3 | 3 | 0 | 0 |
| apostrophes | 1 | 1 | 1 | 1 | 0 | 0 |
| common symbols | 3 | 3 | 3 | 3 | 0 | 0 |
| Grade-1 behaviour | 4 | 4 | 4 | 4 | 0 | 0 |
| typeforms | 2 | 0 raw / 2 base | 0 metadata | 2 | 0 | 2 |
| whitespace | 3 | 2 | 3 | 3 | 1 | 2 |
| mixed interactions | 4 | 3 | 4 | 4 | 0 | 1 |

## Engineering impact

| Family | Required validator treatment |
|---|---|
| alphabet | **LIBLOUIS DIRECT** |
| capitalization | **LIBLOUIS DIRECT** for the tested basic word/letter cases |
| numbers | **LIBLOUIS DIRECT** for the tested forms; not a release-scope expansion yet |
| numeric interactions | **SOURCE POLICY REQUIRED** for numeric-space and broader Grade 1 context; the tested `3-D`, `22b`, `22B`, and letter cases agree |
| punctuation | **LIBLOUIS + SMALL OVERRIDE** may be needed for the observed extra indicator, but punctuation remains fail-closed in the current release slice |
| hyphen/dash | **LIBLOUIS DIRECT** for tested ordinary and numeric-adjacent hyphens |
| brackets | **LIBLOUIS DIRECT** for tested single-line brackets |
| quotes | **NOT ENOUGH EVIDENCE** for broad production support despite exact corpus agreement |
| apostrophes | **NOT ENOUGH EVIDENCE**; keep outside current scope |
| common symbols | **FAIL CLOSED / MANUAL REVIEW** until symbol context is explicitly in scope |
| Grade-1 behaviour | **LIBLOUIS DIRECT** for the tested cases, with a future acceptance/policy layer for optional indicators |
| typeforms | **SOURCE POLICY REQUIRED**; structured typeform input must exist or the source must route to review |
| whitespace | **SOURCE POLICY REQUIRED** for ordinary, numeric, NBSP, thin, zero-width, and repeated spaces |
| mixed interactions | **FAIL CLOSED / MANUAL REVIEW** until the combined families are separately scoped |

If Liblouis is the uncontracted base, the custom work still required is small but explicit:

1. A source-support and normalization gate that preserves ordinary word boundaries/capitalization and rejects unsupported Unicode constructs instead of silently translating them.
2. A provenance-aware policy layer for spaces, especially numeric spaces and unusual Unicode whitespace.
3. A standards-cited punctuation indicator override/acceptance layer if punctuation enters production scope; the three observed Liblouis indicators must not become rules without the cited UEB context.
4. A structured typeform path or a fail-closed/manual-review route. Plain-text Liblouis cannot infer DOCX bold, italic, or underline.
5. Later, separate quote/apostrophe and broader Grade 1 acceptance policies; this audit does not justify implementing them now.

## Final counts

**TOTAL DELIBERATE CASES:** 36

**EXACT LIBLOUIS/DUXBURY AGREEMENTS:** 31/36 case-level; 2,866 equal aligned cells out of 2,870 Liblouis logical cells and 2,897 Duxbury logical cells. This is a corpus comparison count, not a compliance percentage.

**MEANINGFUL DISAGREEMENTS:** 7 grouped disagreements across 5 source cases; 15 raw alignment opcodes.

**LIBLOUIS MATCHED UEB:** 0 disagreement groups where Liblouis alone matched the cited rule.

**DUXBURY MATCHED UEB (original audit tally):** 3 punctuation groups (`G001-G003`); superseded for G001 (`a,b`) by the cited reconciliation. G002-G003 are not re-adjudicated in this correction.

**PERMITTED VARIANTS:** 1 (`G006`, ordinary repeated-space amount).

**SOURCE/POLICY CASES:** 3 (`G004`, `G005`, `G007`), plus the spacing policy attached to `G006`.

**AMBIGUOUS/MANUAL:** 0 groups classified F; typeforms and unsupported whitespace are nevertheless routed to policy/manual handling rather than validated silently.

**UNRESOLVED:** 0 observed disagreement groups. Broad untested family behavior remains outside the evidence claim.

Old-validator regression was not rerun in this audit because no production files were changed. The frozen source, Liblouis output, and all Duxbury artifacts remain unchanged.

## LIBLOUIS BASE ASSESSMENT

**Moderate.** Liblouis is a strong direct base for this corpus's alphabet, ordinary words, basic capitalization, tested numeric interactions, symbols, and quote examples. It needs a small cited policy/override layer at punctuation boundaries and cannot, from plain text alone, carry typeforms or safely decide unsupported whitespace. This is an engineering assessment of the executed corpus, not a UEB certification.

## MINIMAL CUSTOM RULE FAMILIES REQUIRED

Source support/normalization; whitespace and numeric-space policy; future punctuation indicator override/acceptance; structured typeform handling or fail-closed review; later quote/apostrophe and Grade 1 acceptance policy.

## MOST IMPORTANT LIBLOUIS GAPS

Extra grade-1 indicators in the three observed punctuation contexts; no typeform semantics when given plain text; no safe semantic policy for zero-width and other unusual Unicode whitespace.

## AREAS LIBLOUIS ALREADY HANDLES WELL

English alphabet, ordinary uncontracted words, basic capitalization, isolated/consecutive capitals, tested numeric forms and Grade 1-sensitive letter interactions, common symbols, brackets, and the supplied quote/apostrophe examples.
