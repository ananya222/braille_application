# Phase 7C Function-Application Parentheses Inventory

This is an experiment-only structural decomposition of the frozen
52-region Phase 7B bucket. It is not consumed by production code.
In particular, words before ordinary grouping such as `but (a, b)`
are not treated as function calls.

## Dependency filter

| Dependency | Count | Phase 7C eligibility |
| --- | ---: | --- |
| CLEAN_FUNCTION_PARENTHESIS | 16 | candidate only |
| SCRIPT_DEPENDENT | 9 | leave REVIEW |
| FRACTION_DEPENDENT | 3 | leave REVIEW |
| OTHER_DEPENDENCY | 24 | leave REVIEW |
| **Total** | **52** |  |

## Safe structural subtypes

| Subtype | Count | Example structure | Dependency | Governing rule |
| --- | ---: | --- | --- | --- |
| function application in textual or piecewise math | 3 | `f(x) = roll number of the student x` | OTHER_DEPENDENCY | Nemeth 8/19 or source-structure dependency (not a Phase 7C target) |
| function application with fraction dependency | 3 | `f(x) = (x − 2)/(x − 3)` | FRACTION_DEPENDENT | Nemeth 13; Rule 19 (dependency not yet verified) |
| function application with script dependency | 9 | `for every x₁, x₂ ∈ X, f(x₁) = f(x₂) implies x₁ = x₂` | SCRIPT_DEPENDENT | Nemeth 14; Rule 19 (dependency not yet verified) |
| multiple function applications in one expression | 7 | `f(1) = f(2) = 1 y ∈ N, y ≠ 1` | CLEAN_FUNCTION_PARENTHESIS | Nemeth 6.3.1; 19.1.1; 8.2.13/8.3.2 |
| nested or composed function applications | 2 | `gof(x) = g(f(x)), ∀ x ∈ A` | CLEAN_FUNCTION_PARENTHESIS | Nemeth 6.3.1; 19.1.1; 8.2.13/8.3.2 |
| non-function grouping or ordered-pair parentheses | 21 | `(L₁, L₂) ∈ R, (L₂, L₃) ∈ R but (L₁, L₃) ∉ R` | OTHER_DEPENDENCY | Nemeth 8/19 or source-structure dependency (not a Phase 7C target) |
| single-identifier function with grouped argument | 7 | `1 ∈ N f(x) = 2x = 1` | CLEAN_FUNCTION_PARENTHESIS | Nemeth 6.3.1; 19.1.1; 8.2.13/8.3.2 |
| **Total** | **52** |  |  |  |

## Rule basis for clean candidates

- Nemeth 6.3.1 (printed 6-6): a grouping sign is not punctuation
  for the single-English-letter indicator criteria.
- Nemeth 18.1 and 18.4 (printed 18-2 to 18-5): named/abbreviated
  functions are Nemeth, and their spacing follows the code's other
  spacing rules. Rule 18 applies only where a function name is
  actually established by source structure.
- Nemeth 19.1.1 (printed 19-2): grouping signs are transcribed
  wherever they occur in print.
- Nemeth 8.2.13 and 8.3.2 (printed 8-6 to 8-8): punctuation after
  a grouping symbol or word follows its contextual punctuation mode.

No production rule has been changed by this inventory. The detailed
JSON companion retains provenance, parsed FunctionCallNode records,
and the frozen candidate/actual cell evidence for each original case.

## Detailed accounting

| ID | Phase 7B ID | Source page | Block | Subtype | Dependency | Calls |
| --- | --- | ---: | --- | --- | --- | --- |
| FP-001 | FUNC-006 | 3 | 24 | non-function grouping or ordered-pair parentheses | OTHER_DEPENDENCY | `none` |
| FP-002 | FUNC-008 | 3 | 32 | non-function grouping or ordered-pair parentheses | OTHER_DEPENDENCY | `none` |
| FP-003 | FUNC-009 | 3 | 33 | non-function grouping or ordered-pair parentheses | OTHER_DEPENDENCY | `none` |
| FP-004 | FUNC-010 | 3 | 34 | non-function grouping or ordered-pair parentheses | OTHER_DEPENDENCY | `none` |
| FP-005 | FUNC-011 | 3 | 40 | non-function grouping or ordered-pair parentheses | OTHER_DEPENDENCY | `none` |
| FP-006 | FUNC-012 | 3 | 41 | non-function grouping or ordered-pair parentheses | OTHER_DEPENDENCY | `none` |
| FP-007 | FUNC-018 | 5 | 3 | non-function grouping or ordered-pair parentheses | OTHER_DEPENDENCY | `none` |
| FP-008 | FUNC-023 | 7 | 16 | non-function grouping or ordered-pair parentheses | OTHER_DEPENDENCY | `none` |
| FP-009 | FUNC-025 | 7 | 39 | function application with script dependency | SCRIPT_DEPENDENT | `f(x₁), f(x₂)` |
| FP-010 | FUNC-030 | 8 | 14 | function application in textual or piecewise math | OTHER_DEPENDENCY | `f(x)` |
| FP-011 | FUNC-032 | 8 | 25 | function application with script dependency | SCRIPT_DEPENDENT | `f(x₁), f(x₂)` |
| FP-012 | FUNC-033 | 8 | 26 | single-identifier function with grouped argument | CLEAN_FUNCTION_PARENTHESIS | `f(x)` |
| FP-013 | FUNC-035 | 9 | 4 | function application with script dependency | SCRIPT_DEPENDENT | `f(x₁), f(x₂)` |
| FP-014 | FUNC-037 | 9 | 14 | multiple function applications in one expression | CLEAN_FUNCTION_PARENTHESIS | `f(1), f(2)` |
| FP-015 | FUNC-038 | 9 | 15 | single-identifier function with grouped argument | CLEAN_FUNCTION_PARENTHESIS | `f(y + 1)` |
| FP-016 | FUNC-039 | 9 | 16 | single-identifier function with grouped argument | CLEAN_FUNCTION_PARENTHESIS | `f(1)` |
| FP-017 | FUNC-041 | 9 | 19 | function application with script dependency | SCRIPT_DEPENDENT | `f(x)` |
| FP-018 | FUNC-042 | 9 | 21 | multiple function applications in one expression | CLEAN_FUNCTION_PARENTHESIS | `f(− 1), f(1)` |
| FP-019 | FUNC-044 | 9 | 34 | function application in textual or piecewise math | OTHER_DEPENDENCY | `f(x)` |
| FP-020 | FUNC-045 | 10 | 7 | function application with script dependency | SCRIPT_DEPENDENT | `f(x₁), f(x₂)` |
| FP-021 | FUNC-057 | 11 | 7 | function application in textual or piecewise math | OTHER_DEPENDENCY | `f(x)` |
| FP-022 | FUNC-064 | 11 | 28 | function application with fraction dependency | FRACTION_DEPENDENT | `f(x)` |
| FP-023 | FUNC-069 | 12 | 6 | nested or composed function applications | CLEAN_FUNCTION_PARENTHESIS | `gof(x), g(f(x)), f(x)` |
| FP-024 | FUNC-071 | 12 | 13 | multiple function applications in one expression | CLEAN_FUNCTION_PARENTHESIS | `f(2), f(3), f(4), f(5), g(3), g(4), g(5), g(9)` |
| FP-025 | FUNC-072 | 12 | 15 | nested or composed function applications | CLEAN_FUNCTION_PARENTHESIS | `gof(2), g(f(2)), f(2), g(3), gof(3), g(f(3)), f(3), g(4), gof(4), g(f(4)), f(4), g(5), gof` |
| FP-026 | FUNC-074 | 12 | 18 | function application with script dependency | SCRIPT_DEPENDENT | `f(x), g(x)` |
| FP-027 | FUNC-075 | 12 | 20 | function application with script dependency | SCRIPT_DEPENDENT | `gof(x), g(f(x)), f(x), g(cos x)` |
| FP-028 | FUNC-076 | 12 | 21 | function application with script dependency | SCRIPT_DEPENDENT | `fog(x), f(g(x)), g(x), f(3x²), cos(3x²)` |
| FP-029 | FUNC-080 | 13 | 2 | function application with fraction dependency | FRACTION_DEPENDENT | `g(y), gof(x), g(f(x)), f(x), g(4x + 3)` |
| FP-030 | FUNC-081 | 13 | 12 | non-function grouping or ordered-pair parentheses | OTHER_DEPENDENCY | `none` |
| FP-031 | FUNC-082 | 13 | 13 | non-function grouping or ordered-pair parentheses | OTHER_DEPENDENCY | `none` |
| FP-032 | FUNC-083 | 13 | 17 | non-function grouping or ordered-pair parentheses | OTHER_DEPENDENCY | `none` |
| FP-033 | FUNC-084 | 13 | 19 | non-function grouping or ordered-pair parentheses | OTHER_DEPENDENCY | `none` |
| FP-034 | FUNC-085 | 13 | 20 | non-function grouping or ordered-pair parentheses | OTHER_DEPENDENCY | `none` |
| FP-035 | FUNC-086 | 13 | 21 | non-function grouping or ordered-pair parentheses | OTHER_DEPENDENCY | `none` |
| FP-036 | FUNC-089 | 14 | 7 | multiple function applications in one expression | CLEAN_FUNCTION_PARENTHESIS | `f(a), f(a)` |
| FP-037 | FUNC-090 | 14 | 8 | multiple function applications in one expression | CLEAN_FUNCTION_PARENTHESIS | `f(a), f(b), f(b), f(a)` |
| FP-038 | FUNC-091 | 14 | 9 | multiple function applications in one expression | CLEAN_FUNCTION_PARENTHESIS | `f(a), f(b), f(b), f(c), f(a), f(c)` |
| FP-039 | FUNC-092 | 14 | 19 | non-function grouping or ordered-pair parentheses | OTHER_DEPENDENCY | `none` |
| FP-040 | FUNC-094 | 14 | 31 | non-function grouping or ordered-pair parentheses | OTHER_DEPENDENCY | `none` |
| FP-041 | FUNC-095 | 14 | 34 | non-function grouping or ordered-pair parentheses | OTHER_DEPENDENCY | `none` |
| FP-042 | FUNC-096 | 14 | 36 | non-function grouping or ordered-pair parentheses | OTHER_DEPENDENCY | `none` |
| FP-043 | FUNC-099 | 15 | 21 | single-identifier function with grouped argument | CLEAN_FUNCTION_PARENTHESIS | `P(X)` |
| FP-044 | FUNC-100 | 15 | 22 | single-identifier function with grouped argument | CLEAN_FUNCTION_PARENTHESIS | `P(X)` |
| FP-045 | FUNC-101 | 15 | 24 | single-identifier function with grouped argument | CLEAN_FUNCTION_PARENTHESIS | `P(X)` |
| FP-046 | FUNC-103 | 15 | 29 | function application with fraction dependency | FRACTION_DEPENDENT | `f(x), g(x)` |
| FP-047 | FUNC-106 | 16 | 2 | non-function grouping or ordered-pair parentheses | OTHER_DEPENDENCY | `none` |
| FP-048 | FUNC-108 | 16 | 21 | non-function grouping or ordered-pair parentheses | OTHER_DEPENDENCY | `none` |
| FP-049 | FUNC-109 | 16 | 23 | non-function grouping or ordered-pair parentheses | OTHER_DEPENDENCY | `none` |
| FP-050 | FUNC-111 | 16 | 32 | function application with script dependency | SCRIPT_DEPENDENT | `f(x₁), f(x₂)` |
| FP-051 | FUNC-113 | 16 | 35 | single-identifier function with grouped argument | CLEAN_FUNCTION_PARENTHESIS | `f(x)` |
| FP-052 | FUNC-116 | 17 | 22 | multiple function applications in one expression | CLEAN_FUNCTION_PARENTHESIS | `f(x), F(x), φ(x)` |

Invariant: PASS 0 + ERROR 0 + EXCLUDED_OUT_OF_SCOPE 0 + REVIEW 52 = 52.
