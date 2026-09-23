# Case 3 Numbers — standards and Liblouis audit

Status: pre-implementation audit; no production files changed at this stage.

## Authority and runtime

The authority is *The Rules of Unified English Braille*, Third Edition, 2024,
local copy [`Rules-of-Unified-English-Braille-2024.pdf`](../rules/Rules-of-Unified-English-Braille-2024.pdf).
Relevant printed pages and PDF pages are both noted below. Liblouis is only the
candidate translation engine.

Fresh probes were run by
[`probe_case3_numbers.py`](../stress_test/uncontracted_case3_numbers/probe_case3_numbers.py),
which invokes `LiblouisTranslator.translate_prose_with_positions(source)` and
therefore the vendored `louis.translate(['unicode.dis', 'en-ueb-g1.ctb'],
source)` call. There are no additional translation options. The translation
mode is the English uncontracted Grade 1 table.

- Liblouis: 3.38.0
- Runtime: `O:\braille_0.2\vendor\liblouis-win64\bin\liblouis.dll`
- Translation table: `O:\braille_0.2\vendor\liblouis-win64\share\liblouis\tables\en-ueb-g1.ctb`
- Display table: vendored `unicode.dis`
- Exact table list: `unicode.dis,en-ueb-g1.ctb`
- SHA-256 of `en-ueb-g1.ctb`: `446717b55e49ff41aef2c204b58ea1d2872a77a4473a821e766bffd51cee0b4d`

The probe records each complete source codepoint sequence, Unicode Braille
output, dot sequence for every cell, source positions, table list, and options.

## Minimum standards findings

| UEB 2024 rule | Finding for this release slice |
|---|---|
| 5.6.1–5.6.2 (print pp. 59–60; PDF pp. 87–88) | A numeric indicator starts Grade 1 mode; space, hyphen, dash, or a Grade 1 terminator ends it. |
| 5.8.1 (print p. 61; PDF p. 89) | A Grade 1 indicator comes before a capitalization indicator. |
| 6.1.1 and 6.2.1 (print pp. 65–66; PDF pp. 93–94) | Numeric indicators establish numeric mode; permitted numeric-mode symbols include digits, comma, period, numeric-space-plus-digit cells, and visible space. |
| 6.3.1 (print p. 67; PDF p. 95) | Space and symbols outside the numeric-mode list terminate numeric mode. A new number after a hyphen therefore gets a numeric indicator. |
| 6.4.1 (print p. 68; PDF p. 96) | A full stop before a following number takes a numeric indicator unless the context is a clear decimal. |
| 6.5.1–6.5.3 (print pp. 68–69; PDF pp. 96–97) | Numeric mode also sets Grade 1 mode; the rule gives explicit lowercase a–j cases after a digit, period, and comma. |
| 6.5.4 (print p. 69; PDF p. 97) | After a numeric hyphen/dash terminates Grade 1 mode, contraction-readable suffixes need Grade 1. Its examples distinguish `3-D`, `4-m`, `6-CD`, `20-yr` from `20yr` and `3-dimensional`. |
| 6.6.1 (print p. 70; PDF p. 98) | If spaces are clearly separators inside one number, each is represented with a numeric-space cell that combines the space and its following digit. If that relationship is unclear, retain an ordinary space. |
| 6.7.1 (print pp. 70–71; PDF pp. 98–99) | Dates, times, coinage, ordinals, postal codes, and phone numbers follow print punctuation and symbol order. Punctuation beyond numeric-mode punctuation remains outside this slice. |

The report paraphrases the rules; the section and page references above point
to the controlling PDF text and examples. No rule is inferred from Liblouis or
Duxbury output.

## Fresh Liblouis results against the controlling examples

All outputs below were freshly produced in isolation. The sentence probes
also reproduced the same relevant substrings, so no context-sensitive change
was observed in these cases.

| Source (codepoints) | Liblouis Unicode Braille | Dots by cell | UEB 2024 comparison |
|---|---|---|---|
| `3-D` (`0033 002D 0044`) | `⠼⠉⠤⠠⠙` | `3456, 14, 36, 6, 145` | §6.5.4 requires `⠼⠉⠤⠰⠠⠙`; gap is missing `⠰` before caps. |
| `4-m` (`0034 002D 006D`) | `⠼⠙⠤⠍` | `3456, 145, 36, 134` | §6.5.4 requires `⠼⠙⠤⠰⠍`; gap is missing `⠰`. |
| `6-CD` (`0036 002D 0043 0044`) | `⠼⠋⠤⠠⠠⠉⠙` | `3456, 124, 36, 6, 6, 14, 145` | §6.5.4 requires `⠼⠋⠤⠰⠠⠠⠉⠙`; §5.8.1 fixes the order. |
| `20-yr` (`0032 0030 002D 0079 0072`) | `⠼⠃⠚⠤⠽⠗` | `3456, 12, 245, 36, 13456, 1235` | §6.5.4 requires a Grade 1 indicator after the hyphen. |
| `20yr` (`0032 0030 0079 0072`) | `⠼⠃⠚⠽⠗` | `3456, 12, 245, 13456, 1235` | Matches the no-hyphen example in §6.5.4; do not add an indicator. |
| `3-dimensional` (`0033 002D 0064 … 006C`) | `⠼⠉⠤⠙⠊⠍⠑⠝⠎⠊⠕⠝⠁⠇` | `3456, 14, 36, 145, 24, 134, 15, 1345, 234, 24, 135, 1345, 1, 123` | Matches §6.5.4; do not add an indicator before an ordinary full word. |
| `4 500 000` (`0034 0020 0035 0030 0030 0020 0030 0030 0030`) | `⠼⠙⠀⠼⠑⠚⠚⠀⠼⠚⠚⠚` | `3456, 145, blank, 3456, 15, 245, 245, blank, 3456, 245, 245, 245` | §6.6.1 requires `⠼⠙⠐⠑⠚⠚⠐⠚⠚⠚`; each numeric-space cell replaces the blank and following numeric indicator. |
| `4 5` (`0034 0020 0035`) | `⠼⠙⠀⠼⠑` | `3456, 145, blank, 3456, 15` | Correct ordinary-space treatment; this short pattern is not enough to infer a single grouped number. |

## Case 3 feature audit and production action

| Feature/context | Representative print example | UEB 2024 citation | Fresh Liblouis / expected result | Audit status | Production action |
|---|---|---|---|---|---|
| Numeric indicator and digits | `0`, `1`–`9`, `1234567890`, repeated zeroes | 6.1.1, 6.2.1 | Correct leading `⠼` and continued digit cells | PASS | Liblouis directly |
| Numeric-mode continuation | `3,500`, `8.93`, `.7`, `,7`, `8,93` | 6.1.1, 6.2.1 | The cited comma/period signs and following digits are correct | PASS | Liblouis directly |
| Mode termination | `9-10`, `4 5`, then a letter after a space | 6.3.1 | New numeric indicator after hyphen; ordinary spaces retained | PASS | Liblouis directly |
| Full stop before a number | `No. 4` | 6.4.1 | The following `4` receives `⠼` | PASS | Liblouis directly |
| Lowercase a–j after digit/period/comma | `3b`, `4.b`; near neighbors `3k`, `4.m` | 6.5.2 | Required Grade 1 indicators and non-trigger cases match cited examples | PASS | Liblouis directly |
| Uppercase after digit/decimal point | `3B`, `4.B` | 6.5.2 | Capital indicator appears without an unnecessary Grade 1 indicator | PASS | Liblouis directly |
| Contraction-sensitive hyphen suffix | `3-D`, `4-m`, `6-CD`, `20-yr` | 6.5.4; 5.8.1 | Liblouis omits `⠰` in each; Grade 1 precedes capitals | GAP | Add source-mapped, cited narrow correction |
| Hyphen near-neighbors | `20yr`, `3-dimensional`, `4-bed`, `6-can` | 6.5.4 | Direct table output matches the standard's contrasts | PASS | Preserve Liblouis output |
| Clearly grouped thousands | `4 500 000`, `3 245 000` | 6.6.1 | Liblouis emits ordinary blank plus repeated `⠼`; standard uses combined numeric-space cells | GAP | Source-map each grouped space and following digit; replace blank and remove repeated prefix |
| Named phone/date/time/ISBN groupings | `date 1947 08 31`; `time 16 00`; `ISBN 978 1 55468 513 4`; `phone 61 3 1234 5678` | 6.6.1; 6.7.1 | Base table repeats `⠼` after each ordinary space; UEB uses numeric-space-plus-digit in these explicitly labeled single-number contexts | GAP | Apply the same mapped 6.6.1 correction only for these named numeric forms |
| Ambiguous spaced digits | `4 5`; irregular `77 777 77` | 6.6.1 | Ordinary space is correct when the input does not clearly denote one number | PASS | Preserve Liblouis output; do not guess numeric-space semantics |
| Number followed by another paragraph/line/page | Numeric text separated only by ordinary layout | 6.1.1, 6.3.1 | Focused pipeline tests show mode restarts at spaces and page/line layout separators do not change the logical stream | PASS (layout) | No alignment/provenance change |
| Number split across a Braille line | Long number requiring UEB continuation cells | 6.10.1–6.10.5 | Layout-dependent continuation cannot be determined from source text alone | OUT OF SCOPE | Do not certify split-number line continuation in this release slice |
| Date/time punctuation, coinage, ordinal symbol order | Slash dates, colon times, currency | 6.7.1 | General slash/colon/currency transcription is beyond numeric-only punctuation scope | OUT OF SCOPE | Reject unsupported source characters to Review |
| Numeric passages and spaced numeric indicator | Passage/spaced-number controls | 6.8.1–6.9.1 | Not part of this Case 3 implementation | OUT OF SCOPE | Do not infer passage semantics |
| Repeated numeric values | Same decimal or grouped integer occurs more than once | 6.1.1–6.6.1 | Liblouis is context-independent here; corruption must still be tied to its exact source occurrence | PASS (translation) | Preserve stream order and test repeated-region alignment |
| Extra/missing/wrong numeric indicators | Insert, delete, replace, or repeat `⠼` | 6.1.1 | Translator provides a stable expected prefix; generic prose guard initially suppressed extra prefixes | GAP (classification) | Case 3-owned numeric insertions are confirmed; generic review guard remains for other scopes |

The test-only context labels above are deliberately simple English labels,
not a new date/telephone punctuation grammar. Slash, colon, parentheses,
currency symbols, line-continuation, and passage forms remain unsupported.

The full probe output also confirms that Liblouis already matches the cited
examples for digits, decimal comma/full stop, leading decimal signs, numeric
termination at hyphen, ordinals, and lowercase/uppercase letter indicators
after digits or a decimal point. These are direct, no-override cases for this
tested subset.

## Implementation boundary informed by this audit

The evidence supports two small, standards-cited corrections: numeric-space
cells for a clearly grouped digit sequence, and a Grade 1 indicator for the
contraction-sensitive hyphen suffix patterns demonstrated by §6.5.4. The
corrections must use Liblouis source-position maps, preserve the source text,
and fail to review rather than guess when a correction cannot be mapped
unambiguously. Everything else must remain Liblouis output unless another
explicit UEB 2024 example proves a gap.

The audit does not authorize general date, time, currency, slash, colon,
arithmetic, numeric-passage, line-continuation, typeform, or unusual-whitespace
handling in Case 3.
