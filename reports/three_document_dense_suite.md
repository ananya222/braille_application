# Three-document dense stress suite

**THREE-DOCUMENT DENSE STRESS SUITE PASSED — BACKEND FROZEN**

Tests 1, 2 and 4 passed using frozen ground truth. Test 2 adds multiplication/division cases and Test 4 adds ordinary prose/capitalization cases. Clean Test 2 and Test 4 had complete supported coverage and no confirmed errors. Test 3 was not selected because of its previously known extra terminating switch.

| Test | Injected | Detected | Missed | False positives | Exact localized |
|---|---:|---:|---:|---:|---:|
| Test 1 | 67 | 67 | 0 | 0 | 67 |
| Test 2 | 68 | 68 | 0 | 0 | 68 |
| Test 4 | 50 | 50 | 0 | 0 | 50 |

Total injected: 185. Total detected and exactly localized: 185. Missed, false-positive, wrong-page, neighboring-cell, blank-cell, and duplicate counts: 0.

| Rule | Injected | Detected | Missed | False reports | Exact boxes |
|---|---:|---:|---:|---:|---:|
| CAPITALIZATION | 29 | 29 | 0 | 0 | 29 |
| EQUALS | 27 | 27 | 0 | 0 | 27 |
| MINUS | 25 | 25 | 0 | 0 | 25 |
| NEGATIVE | 22 | 22 | 0 | 0 | 22 |
| PLUS | 26 | 26 | 0 | 0 | 26 |
| DIVIDE | 29 | 29 | 0 | 0 | 29 |
| MULTIPLY | 27 | 27 | 0 | 0 | 27 |

The narrow semantic operator anchors apply only to already evaluated supported math with equal payload lengths and exact matching non-operator cells. Other constructs retain existing alignment and scope. No spacing rule or capitalization rule was broadened.

Regressions: 6/6 original math; 3/3 capitalization; 42/42 Duxbury spacing; 68/68 guards; clean fixtures; 5/5 exact prototype. Twelve additional repeated-operand paired-operator tests pass with and without Duxbury spacing.

Limitations: only the currently guaranteed simple math and ordinary single-capital scope is certified. Unsupported notation is not certified. Test 1 page 15 has no eligible target; Test 2 pages 9 and 15 have reduced target density.
