# Phase 7C Function-Application Parentheses Burndown

This report covers only the frozen 52-region priority bucket. The bucket is a
regression priority, not a source of production-specific behavior.

| Iteration | Subtype | Before | PASS gained | ERROR gained | Remaining |
| --- | --- | ---: | ---: | ---: | ---: |
| Baseline | Broad Phase 7B parenthesis bucket | 52 | 0 | 0 | 52 |
| Decomposition | Structural FunctionCallNode audit only | 52 | 0 | 0 | 52 |
| Candidate 1 canary | Single identifier with one parenthesized argument | 52 | 0 | 0 | 52 |
| Candidate 1 full BRF gate | Same narrow subtype, rule-status promotion only | 52 | 7 | 2 | 45 |
| Reverted | Candidate exposed one Nemeth and one UEB difference | 52 | 0 | 0 | 52 |

## Structural accounting

| Dependency | Original | PASS | ERROR | REVIEW |
| --- | ---: | ---: | ---: | ---: |
| CLEAN_FUNCTION_PARENTHESIS | 16 | 0 | 0 | 16 |
| SCRIPT_DEPENDENT | 9 | 0 | 0 | 9 |
| FRACTION_DEPENDENT | 3 | 0 | 0 | 3 |
| OTHER_DEPENDENCY | 24 | 0 | 0 | 24 |
| **Total** | **52** | **0** | **0** | **52** |

Candidate 1 passed five structural positive canaries, six negative controls,
and the Rule 19 Example 19-29 `f(x)` cell check. It changed no expected
Braille cells and no non-target spans. The full rendered-BRF run nevertheless
made two previously REVIEW-suppressed target differences definite:

- page 9, `f(1) = 1`: an expected cell with dot pattern `3456` is absent from
  the BRF alignment (`NEMETH_ERROR`);
- page 15, `P(X)?`: an expected cell with dot pattern `56` is absent from the
  BRF alignment (`UEB_ERROR`).

The candidate is therefore removed. The baseline is restored rather than
assuming either rendered BRF difference is an authoritative error or
weakening the standards-backed gate.

## Regression safety

| Metric | Baseline | Candidate | Restored baseline |
| --- | ---: | ---: | ---: |
| Total REVIEW | 184 | 177 | 184 |
| Function-application REVIEW | 52 | 45 | 52 |
| Nemeth differences | 0 | 1 | 0 |
| UEB differences | 0 | 1 | 0 |
| Switching differences | 0 | 0 | 0 |
| Unaligned | 0 | 0 | 0 |
| Definite errors | 0 | 2 | 0 |

The detailed structural inventory is in
`reports/chapter1_function_parenthesis_inventory.md` and its JSON companion.
