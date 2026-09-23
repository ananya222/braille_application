# Simple math: explicit scope and acceptance gate

Status: source-backend acceptance passed for the five explicit operator/relation
constructs below, including unary negative. Square roots are not supported.
The packaged Windows EXE has NOT been rebuilt. This document was initially
written before implementation and updated after independent production tests.

## Source contract

Use explicit `[[*ts*]]` and `[[*te*]]` math spans in the prepared master.
Each span must contain one complete expression. Ordinary prose and sentence
punctuation remain outside it. No automatic math detection is claimed.
Only regular-type, baseline, linear Nemeth is targeted. Meaningful font,
vector, matrix, spatial, or inherited script attributes are excluded.

## Accepted grammar

```text
expression := sum [ '=' sum ]
sum        := product { ('+' | '−') product }
product    := operand { ('×' | '÷') operand }
operand    := integer | lower_case_letter | '−' integer | '−' lower_case_letter
integer    := one or more ASCII digits 0 through 9
lower_case_letter := one ASCII letter a through z
```

Mixed letter/integer operands are targeted. Only one equality is allowed.
No grouping, adjacency/juxtaposition, unary plus, consecutive operator signs,
decimal numbers, numeric separators, or other tokens are admitted. In
particular, a negative right operand after an operator is outside this first
grammar; a negative operand at the beginning or after equality is targeted.
Ordinary spaces between tokens do not establish mathematical spacing.
Physical runover of an individual expression is outside this acceptance set.

| Construct | Supported forms | Explicitly unsupported forms | Fallback |
|---|---|---|---|
| Addition | `2 + 3`, `x + y`, `x + 2 = y` | Scripts, fractions, implicit multiplication, grouped or radical operands | REVIEW |
| Subtraction | `8 − 3`, `x − y` | Punctuation hyphen/dash; consecutive signs | REVIEW |
| Unary negative | `−2`, `−x`, `x = −2` | Repeated or consecutive signs; negative grouped term | REVIEW |
| Multiplication | `4 × 3`, `x × y` | `2x`, `·`, vectors, matrices | REVIEW |
| Division | `8 ÷ 2`, `x ÷ y` | `/`, built-up or nested fractions | REVIEW |
| Equality | `x = y`, `2 + 3 = 5` | Chained equality; other relations, membership, inequalities | REVIEW |
| Square root | None through the current plain-text master interface | All plain `√` forms with unknown vinculum/radicand structure | REVIEW |

## Radical limitation

Plain `√x`, `√5`, and `√(x + 1)` do not establish whether print has a
vinculum. They MUST NOT be certified by guessing. Nemeth 16.1.1 and 16.1.2
(printed pages 16-1 through 16-3) distinguish these forms. A future supported
source node must explicitly carry the radicand, vinculum presence and end.
No radical is in the public synthetic fixture until that source route and
its complete production acceptance tests exist.

## Standards to apply and verify

- Nemeth 2022, 3.3.1 and 3.4: numeric indicator use/non-use.
- Nemeth 2022, Rule 20 symbol list and 20.1: explicit operation cells and spacing.
- Nemeth 2022, Rule 21: equality cells and applicable comparison spacing.
- Nemeth 2022, Rule 6: applicable English-letter indicator conditions.
- October 2025 errata, amended 4.2: inner code-switch blanks.

The applicable numeric, operation-spacing, comparison-spacing and letter
indicator provisions were read with their surrounding conditions. Duxbury
and Liblouis are not the correctness oracle.

## Acceptance and failure behavior

Each promoted construct requires an independent standards oracle, unseen
examples, negative cases, clean actual Braille, corrupted actual Braille,
confirmed error classification, actual-cell range and blue-box verification.
Source outside this grammar cannot be certified by this new path. Existing
independently verified rules may apply separately; lack of an applicable
proof must remain REVIEW, not a confirmed user error.

No claim is made for arbitrary PDF source extraction, arbitrary DOCX equations,
all Nemeth, or every error type. Insertion/deletion and layout behavior must
be reported separately rather than inferred from substitution tests.

## Results and remaining limits

- 7 official and 12 synthetic literal-cell cases passed; every nonblank payload
  cell separately substituted produced one localized production Nemeth error.
- 23 parser exclusions passed; nonempty excluded expressions were also tested
  through production. Those without an existing independent whole-structure
  letter/group proof remained REVIEW even with deliberately corrupt cells.
- Public fixture: 118/118 correct cells, zero errors or reviews. Six controlled
  substitutions produced six confirmed errors, exact actual ranges and six
  visually inspected blue boxes; provenance unmatched/offsets both zero.
- Rule ID: NEMETH_SIMPLE_LINEAR_001. Scope fallback: NEMETH_SIMPLE_SCOPE_001.
- Existing spacing-only and pure-insertion filters are unchanged. This milestone
  does NOT certify arbitrary insertions, deletions or spacing-only defects.
- Chapter 1: 0 confirmed clean errors; REVIEW 182 -> 279; exclusions 4;
  780 raw differences; 33,175 / 34,448 matching cells (96.3046%). Five math
  payloads changed, all explained by the new generic numeric/operation rules.
  Switches remain 358 each way, with zero missing inner blanks.
- The older six-corruption Chapter 1 fixture now reports five confirmed errors.
  Page 2's containing block includes out-of-scope notation and is REVIEW.
  This is a conservative scope restriction, not proof that its corruption is
  correct. Do not use that old fixture as a six-error acceptance claim.
- The new seven-expression fixture is under data/simple_math. Its JSON master
  is the input to scripts/simple_math_acceptance.py; the TXT master can be pasted
  into Word, one paragraph per line. No native Word-equation import is claimed.

Evidence: reports/simple_math_acceptance.json and reports/simple_math_regression.json.
Final milestone: SIMPLE-MATH SCOPE PARTIALLY READY — square-root source structure
and its production validation remain unavailable.
