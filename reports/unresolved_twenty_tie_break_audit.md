# Audit of the 20 unresolved diverse-fixture mutations

All 20 are accounted for: A=15, B=5, C=D=E=F=G=0. Production and fixture files were unchanged.

The diagnostic executed two controlled evaluations of the same frozen inputs. The pre variant removed only the latest identical-cell deletion branch in memory; post used the on-disk function unchanged. This is not the older global fallback. Both complete outputs are saved in `results/unresolved_twenty_trace/pre.json` and `post.json`; subsequent analysis reads those snapshots without rerunning validation. `integrity.json` records the removed branch and matching before/after SHA-256 hashes.

Pre: 989 policy-accepted mutations, 11 unresolved. Post: 980 accepted, 20 unresolved. The tie-break repairs six earlier deletion associations and regresses 15 previously exact deletion anchors: net -9 accepted mutations. The five insertion failures exist in both variants.

| Bucket | Count |
| --- | ---: |
| A. Regression caused by latest deletion tie-break | 15 |
| B. Valid identical-run equivalence rejected by evaluator | 5 |
| C. Evaluator association/consumption collision | 0 |
| D. Genuine pre-existing alignment defect | 0 |
| E. Correct alignment, wrong provenance | 0 |
| F. Correct provenance, wrong box | 0 |
| G. Other | 0 |
| Total | 20 |

A means regression against the established strict deletion-anchor policy. All 15 delete one of two identical expected cells; either deletion produces the same stream. The new branch selects the earlier cell, moving the gap and next-surviving-cell anchor one position earlier. Provenance and rectangles faithfully follow that new gap. No evidence supports a separate provenance or renderer defect. These cases have not been silently accepted under an expanded deletion-equivalence policy.

B is a concrete audit field error: `evaluate_frozen_diverse.py` compares the insertion mask to `row['actual_mask']`. In these five rows that is the original target `p` (15); the inserted `code_target` is `,` (32). The PDF contains a contiguous pair of identical capitalization cells. The unique available finding boxes the other member of that pair. Every existing equivalence condition passes when tested against the inserted cell. No candidate was consumed by another mutation. This report diagnoses the guard without changing it.

Coordinates: all spans are zero-based and half-open. E is expected page-local; a is actual validator page-local. Detailed alignment operations use document-global actual offsets and are saved with both coordinate systems. PDF character indices are zero-based on the corrupted PDF page. Boxes are `(x0, top, x1, bottom)` in points. Displayed coordinates are rounded to three decimals; JSON/CSV preserve full precision. Each reported box exactly equals its one provenance cell. `none` in the candidate columns means no finding meets the current literal evaluator predicates even before availability filtering. All same-page candidate checks, guard booleans, and consumption owners are preserved in `twenty_cases.json`.

| ID/type | Page / intended E | Pre finding: E; a; PDF char | Post finding: E; a; PDF char | Current compatible candidates pre / post | Proven equivalence candidate | Bucket |
| --- | --- | --- | --- | --- | --- | --- |
| DIV-0096 insertion | 6 / [2, 2] | VAL-ERR-0096: [1,1); [3, 4]; [[5]] | VAL-ERR-0096: [1,1); [3, 4]; [[5]] | none / none | VAL-ERR-0096 | B |
| DIV-0117 deletion | 7 / [127, 128] | VAL-ERR-0127: [127,128); [131, 131]; [[136]] | VAL-ERR-0127: [126,127); [130, 130]; [[135]] | VAL-ERR-0127 / none | none | A |
| DIV-0181 deletion | 9 / [367, 368] | VAL-ERR-0179: [367,368); [371, 371]; [[370]] | VAL-ERR-0179: [366,367); [370, 370]; [[369]] | VAL-ERR-0179 / none | none | A |
| DIV-0188 deletion | 10 / [50, 51] | VAL-ERR-0195: [50,51); [53, 53]; [[63]] | VAL-ERR-0195: [49,50); [52, 52]; [[62]] | VAL-ERR-0195 / none | none | A |
| DIV-0268 deletion | 14 / [32, 33] | VAL-ERR-0266: [32,33); [38, 38]; [[41]] | VAL-ERR-0266: [31,32); [37, 37]; [[40]] | VAL-ERR-0266 / none | none | A |
| DIV-0296 insertion | 16 / [2, 2] | VAL-ERR-0296: [1,1); [3, 4]; [[5]] | VAL-ERR-0296: [1,1); [3, 4]; [[5]] | none / none | VAL-ERR-0296 | B |
| DIV-0317 deletion | 17 / [127, 128] | VAL-ERR-0327: [127,128); [131, 131]; [[136]] | VAL-ERR-0327: [126,127); [130, 130]; [[135]] | VAL-ERR-0327 / none | none | A |
| DIV-0381 deletion | 19 / [367, 368] | VAL-ERR-0379: [367,368); [371, 371]; [[370]] | VAL-ERR-0379: [366,367); [370, 370]; [[369]] | VAL-ERR-0379 / none | none | A |
| DIV-0388 deletion | 20 / [50, 51] | VAL-ERR-0395: [50,51); [53, 53]; [[63]] | VAL-ERR-0395: [49,50); [52, 52]; [[62]] | VAL-ERR-0395 / none | none | A |
| DIV-0500 insertion | 26 / [2, 2] | VAL-ERR-0500: [1,1); [3, 4]; [[5]] | VAL-ERR-0500: [1,1); [3, 4]; [[5]] | none / none | VAL-ERR-0500 | B |
| DIV-0521 deletion | 27 / [127, 128] | VAL-ERR-0531: [127,128); [131, 131]; [[136]] | VAL-ERR-0531: [126,127); [130, 130]; [[135]] | VAL-ERR-0531 / none | none | A |
| DIV-0585 deletion | 29 / [367, 368] | VAL-ERR-0583: [367,368); [371, 371]; [[370]] | VAL-ERR-0583: [366,367); [370, 370]; [[369]] | VAL-ERR-0583 / none | none | A |
| DIV-0592 deletion | 30 / [50, 51] | VAL-ERR-0599: [50,51); [53, 53]; [[63]] | VAL-ERR-0599: [49,50); [52, 52]; [[62]] | VAL-ERR-0599 / none | none | A |
| DIV-0700 insertion | 36 / [2, 2] | VAL-ERR-0700: [1,1); [3, 4]; [[5]] | VAL-ERR-0700: [1,1); [3, 4]; [[5]] | none / none | VAL-ERR-0700 | B |
| DIV-0720 deletion | 37 / [127, 128] | VAL-ERR-0730: [127,128); [132, 132]; [[137]] | VAL-ERR-0730: [126,127); [131, 131]; [[136]] | VAL-ERR-0730 / none | none | A |
| DIV-0791 deletion | 40 / [50, 51] | VAL-ERR-0798: [50,51); [52, 52]; [[62]] | VAL-ERR-0798: [49,50); [51, 51]; [[61]] | VAL-ERR-0798 / none | none | A |
| DIV-0901 insertion | 46 / [2, 2] | VAL-ERR-0901: [1,1); [3, 4]; [[5]] | VAL-ERR-0901: [1,1); [3, 4]; [[5]] | none / none | VAL-ERR-0901 | B |
| DIV-0921 deletion | 47 / [127, 128] | VAL-ERR-0931: [127,128); [131, 131]; [[136]] | VAL-ERR-0931: [126,127); [130, 130]; [[135]] | VAL-ERR-0931 / none | none | A |
| DIV-0985 deletion | 49 / [367, 368] | VAL-ERR-0983: [367,368); [371, 371]; [[370]] | VAL-ERR-0983: [366,367); [370, 370]; [[369]] | VAL-ERR-0983 / none | none | A |
| DIV-0992 deletion | 50 / [50, 51] | VAL-ERR-0999: [50,51); [53, 53]; [[63]] | VAL-ERR-0999: [49,50); [52, 52]; [[62]] | VAL-ERR-0999 / none | none | A |

## DIV-0096 — bucket B

Pre/post alignment, finding, provenance, and box are identical. One available insertion finding lies in the same contiguous two-comma run as the target and satisfies every equivalence guard except comparison against actual_mask=15 (the original target p). code_target=',' and the actual inserted PDF glyph both encode mask 32. The evaluator checks the wrong manifest field. The unique compatible finding has not been consumed by another mutation.

Expected mutation span: [2, 2]; target PDF char [6].

| Trace | Expected → actual masks | Actual span (page / document) | Provenance: PDF char, glyph, box |
| --- | --- | --- | --- |
| pre | [] → [32] | [3, 4] / [1099, 1100] | [[5]], `,`, (115.126, 68.274, 123.773, 80.251) |
| post | [] → [32] | [3, 4] / [1099, 1100] | [[5]], `,`, (115.126, 68.274, 123.773, 80.251) |

Required target/anchor: `,` at (123.781, 68.274, 132.429, 80.251).

Pre alignment: `[{"tag": "replace", "expected_start": 0, "expected_end": 1, "actual_start": 1098, "actual_end": 1099}, {"tag": "insert", "expected_start": 1, "expected_end": 1, "actual_start": 1099, "actual_end": 1100}, {"tag": "equal", "expected_start": 1, "expected_end": 12, "actual_start": 1100, "actual_end": 1111}]`

Post alignment: `[{"tag": "replace", "expected_start": 0, "expected_end": 1, "actual_start": 1098, "actual_end": 1099}, {"tag": "insert", "expected_start": 1, "expected_end": 1, "actual_start": 1099, "actual_end": 1100}, {"tag": "equal", "expected_start": 1, "expected_end": 12, "actual_start": 1100, "actual_end": 1111}]`

## DIV-0117 — bucket A

The only runtime change moves the deletion from the second to the first identical expected cell. The gap and its exact provenance/box move one surviving cell earlier. Pre is exact under the current deletion-anchor policy; post fails. This is a localization-policy regression, not downstream mapping corruption: deleting either identical expected cell produces the same cell stream. No evaluator-compatible candidate was consumed by another mutation.

Expected mutation span: [127, 128]; target PDF char [136].

| Trace | Expected → actual masks | Actual span (page / document) | Provenance: PDF char, glyph, box |
| --- | --- | --- | --- |
| pre | [32] → [] | [131, 131] / [1418, 1418] | [[136]], `c`, (80.655, 183.474, 89.303, 195.451) |
| post | [32] → [] | [130, 130] / [1417, 1417] | [[135]], `,`, (72.0, 183.474, 80.648, 195.451) |

Required target/anchor: `c` at (80.655, 183.474, 89.303, 195.451).

Pre alignment: `[{"tag": "equal", "expected_start": 119, "expected_end": 127, "actual_start": 1410, "actual_end": 1418}, {"tag": "delete", "expected_start": 127, "expected_end": 128, "actual_start": 1418, "actual_end": 1418}, {"tag": "equal", "expected_start": 128, "expected_end": 130, "actual_start": 1418, "actual_end": 1420}]`

Post alignment: `[{"tag": "equal", "expected_start": 119, "expected_end": 126, "actual_start": 1410, "actual_end": 1417}, {"tag": "delete", "expected_start": 126, "expected_end": 127, "actual_start": 1417, "actual_end": 1417}, {"tag": "equal", "expected_start": 127, "expected_end": 130, "actual_start": 1417, "actual_end": 1420}]`

## DIV-0181 — bucket A

The only runtime change moves the deletion from the second to the first identical expected cell. The gap and its exact provenance/box move one surviving cell earlier. Pre is exact under the current deletion-anchor policy; post fails. This is a localization-policy regression, not downstream mapping corruption: deleting either identical expected cell produces the same cell stream. No evaluator-compatible candidate was consumed by another mutation.

Expected mutation span: [367, 368]; target PDF char [370].

| Trace | Expected → actual masks | Actual span (page / document) | Provenance: PDF char, glyph, box |
| --- | --- | --- | --- |
| pre | [17] → [] | [371, 371] / [1984, 1984] | [[370]], `p`, (253.351, 321.714, 261.998, 333.691) |
| post | [17] → [] | [370, 370] / [1983, 1983] | [[369]], `e`, (244.695, 321.714, 253.343, 333.691) |

Required target/anchor: `p` at (253.351, 321.714, 261.998, 333.691).

Pre alignment: `[{"tag": "equal", "expected_start": 354, "expected_end": 367, "actual_start": 1971, "actual_end": 1984}, {"tag": "delete", "expected_start": 367, "expected_end": 368, "actual_start": 1984, "actual_end": 1984}, {"tag": "equal", "expected_start": 368, "expected_end": 381, "actual_start": 1984, "actual_end": 1997}]`

Post alignment: `[{"tag": "equal", "expected_start": 354, "expected_end": 366, "actual_start": 1971, "actual_end": 1983}, {"tag": "delete", "expected_start": 366, "expected_end": 367, "actual_start": 1983, "actual_end": 1983}, {"tag": "equal", "expected_start": 367, "expected_end": 381, "actual_start": 1983, "actual_end": 1997}]`

## DIV-0188 — bucket A

The only runtime change moves the deletion from the second to the first identical expected cell. The gap and its exact provenance/box move one surviving cell earlier. Pre is exact under the current deletion-anchor policy; post fails. This is a localization-policy regression, not downstream mapping corruption: deleting either identical expected cell produces the same cell stream. No evaluator-compatible candidate was consumed by another mutation.

Expected mutation span: [50, 51]; target PDF char [63].

| Trace | Expected → actual masks | Actual span (page / document) | Provenance: PDF char, glyph, box |
| --- | --- | --- | --- |
| pre | [32] → [] | [53, 53] / [2116, 2116] | [[63]], `a`, (97.966, 252.594, 106.614, 264.571) |
| post | [32] → [] | [52, 52] / [2115, 2115] | [[62]], `,`, (89.311, 252.594, 97.958, 264.571) |

Required target/anchor: `a` at (97.966, 252.594, 106.614, 264.571).

Pre alignment: `[{"tag": "equal", "expected_start": 47, "expected_end": 48, "actual_start": 2113, "actual_end": 2114}, {"tag": "equal", "expected_start": 48, "expected_end": 49, "actual_start": 2114, "actual_end": 2115}, {"tag": "equal", "expected_start": 49, "expected_end": 50, "actual_start": 2115, "actual_end": 2116}, {"tag": "delete", "expected_start": 50, "expected_end": 51, "actual_start": 2116, "actual_end": 2116}, {"tag": "equal", "expected_start": 51, "expected_end": 54, "actual_start": 2116, "actual_end": 2119}]`

Post alignment: `[{"tag": "equal", "expected_start": 47, "expected_end": 48, "actual_start": 2113, "actual_end": 2114}, {"tag": "equal", "expected_start": 48, "expected_end": 49, "actual_start": 2114, "actual_end": 2115}, {"tag": "delete", "expected_start": 49, "expected_end": 50, "actual_start": 2115, "actual_end": 2115}, {"tag": "equal", "expected_start": 50, "expected_end": 54, "actual_start": 2115, "actual_end": 2119}]`

## DIV-0268 — bucket A

The only runtime change moves the deletion from the second to the first identical expected cell. The gap and its exact provenance/box move one surviving cell earlier. Pre is exact under the current deletion-anchor policy; post fails. This is a localization-policy regression, not downstream mapping corruption: deleting either identical expected cell produces the same cell stream. No evaluator-compatible candidate was consumed by another mutation.

Expected mutation span: [32, 33]; target PDF char [41].

| Trace | Expected → actual masks | Actual span (page / document) | Provenance: PDF char, glyph, box |
| --- | --- | --- | --- |
| pre | [7] → [] | [38, 38] / [2979, 2979] | [[41]], `e`, (132.437, 91.314, 141.084, 103.291) |
| post | [7] → [] | [37, 37] / [2978, 2978] | [[40]], `l`, (123.781, 91.314, 132.429, 103.291) |

Required target/anchor: `e` at (132.437, 91.314, 141.084, 103.291).

Pre alignment: `[{"tag": "equal", "expected_start": 27, "expected_end": 32, "actual_start": 2974, "actual_end": 2979}, {"tag": "delete", "expected_start": 32, "expected_end": 33, "actual_start": 2979, "actual_end": 2979}, {"tag": "equal", "expected_start": 33, "expected_end": 42, "actual_start": 2979, "actual_end": 2988}]`

Post alignment: `[{"tag": "equal", "expected_start": 27, "expected_end": 31, "actual_start": 2974, "actual_end": 2978}, {"tag": "delete", "expected_start": 31, "expected_end": 32, "actual_start": 2978, "actual_end": 2978}, {"tag": "equal", "expected_start": 32, "expected_end": 42, "actual_start": 2978, "actual_end": 2988}]`

## DIV-0296 — bucket B

Pre/post alignment, finding, provenance, and box are identical. One available insertion finding lies in the same contiguous two-comma run as the target and satisfies every equivalence guard except comparison against actual_mask=15 (the original target p). code_target=',' and the actual inserted PDF glyph both encode mask 32. The evaluator checks the wrong manifest field. The unique compatible finding has not been consumed by another mutation.

Expected mutation span: [2, 2]; target PDF char [6].

| Trace | Expected → actual masks | Actual span (page / document) | Provenance: PDF char, glyph, box |
| --- | --- | --- | --- |
| pre | [] → [32] | [3, 4] / [3275, 3276] | [[5]], `,`, (115.126, 68.274, 123.773, 80.251) |
| post | [] → [32] | [3, 4] / [3275, 3276] | [[5]], `,`, (115.126, 68.274, 123.773, 80.251) |

Required target/anchor: `,` at (123.781, 68.274, 132.429, 80.251).

Pre alignment: `[{"tag": "replace", "expected_start": 0, "expected_end": 1, "actual_start": 3274, "actual_end": 3275}, {"tag": "insert", "expected_start": 1, "expected_end": 1, "actual_start": 3275, "actual_end": 3276}, {"tag": "equal", "expected_start": 1, "expected_end": 12, "actual_start": 3276, "actual_end": 3287}]`

Post alignment: `[{"tag": "replace", "expected_start": 0, "expected_end": 1, "actual_start": 3274, "actual_end": 3275}, {"tag": "insert", "expected_start": 1, "expected_end": 1, "actual_start": 3275, "actual_end": 3276}, {"tag": "equal", "expected_start": 1, "expected_end": 12, "actual_start": 3276, "actual_end": 3287}]`

## DIV-0317 — bucket A

The only runtime change moves the deletion from the second to the first identical expected cell. The gap and its exact provenance/box move one surviving cell earlier. Pre is exact under the current deletion-anchor policy; post fails. This is a localization-policy regression, not downstream mapping corruption: deleting either identical expected cell produces the same cell stream. No evaluator-compatible candidate was consumed by another mutation.

Expected mutation span: [127, 128]; target PDF char [136].

| Trace | Expected → actual masks | Actual span (page / document) | Provenance: PDF char, glyph, box |
| --- | --- | --- | --- |
| pre | [32] → [] | [131, 131] / [3595, 3595] | [[136]], `c`, (80.655, 183.474, 89.303, 195.451) |
| post | [32] → [] | [130, 130] / [3594, 3594] | [[135]], `,`, (72.0, 183.474, 80.648, 195.451) |

Required target/anchor: `c` at (80.655, 183.474, 89.303, 195.451).

Pre alignment: `[{"tag": "equal", "expected_start": 119, "expected_end": 127, "actual_start": 3587, "actual_end": 3595}, {"tag": "delete", "expected_start": 127, "expected_end": 128, "actual_start": 3595, "actual_end": 3595}, {"tag": "equal", "expected_start": 128, "expected_end": 130, "actual_start": 3595, "actual_end": 3597}]`

Post alignment: `[{"tag": "equal", "expected_start": 119, "expected_end": 126, "actual_start": 3587, "actual_end": 3594}, {"tag": "delete", "expected_start": 126, "expected_end": 127, "actual_start": 3594, "actual_end": 3594}, {"tag": "equal", "expected_start": 127, "expected_end": 130, "actual_start": 3594, "actual_end": 3597}]`

## DIV-0381 — bucket A

The only runtime change moves the deletion from the second to the first identical expected cell. The gap and its exact provenance/box move one surviving cell earlier. Pre is exact under the current deletion-anchor policy; post fails. This is a localization-policy regression, not downstream mapping corruption: deleting either identical expected cell produces the same cell stream. No evaluator-compatible candidate was consumed by another mutation.

Expected mutation span: [367, 368]; target PDF char [370].

| Trace | Expected → actual masks | Actual span (page / document) | Provenance: PDF char, glyph, box |
| --- | --- | --- | --- |
| pre | [17] → [] | [371, 371] / [4163, 4163] | [[370]], `p`, (253.351, 321.714, 261.998, 333.691) |
| post | [17] → [] | [370, 370] / [4162, 4162] | [[369]], `e`, (244.695, 321.714, 253.343, 333.691) |

Required target/anchor: `p` at (253.351, 321.714, 261.998, 333.691).

Pre alignment: `[{"tag": "equal", "expected_start": 354, "expected_end": 367, "actual_start": 4150, "actual_end": 4163}, {"tag": "delete", "expected_start": 367, "expected_end": 368, "actual_start": 4163, "actual_end": 4163}, {"tag": "equal", "expected_start": 368, "expected_end": 381, "actual_start": 4163, "actual_end": 4176}]`

Post alignment: `[{"tag": "equal", "expected_start": 354, "expected_end": 366, "actual_start": 4150, "actual_end": 4162}, {"tag": "delete", "expected_start": 366, "expected_end": 367, "actual_start": 4162, "actual_end": 4162}, {"tag": "equal", "expected_start": 367, "expected_end": 381, "actual_start": 4162, "actual_end": 4176}]`

## DIV-0388 — bucket A

The only runtime change moves the deletion from the second to the first identical expected cell. The gap and its exact provenance/box move one surviving cell earlier. Pre is exact under the current deletion-anchor policy; post fails. This is a localization-policy regression, not downstream mapping corruption: deleting either identical expected cell produces the same cell stream. No evaluator-compatible candidate was consumed by another mutation.

Expected mutation span: [50, 51]; target PDF char [63].

| Trace | Expected → actual masks | Actual span (page / document) | Provenance: PDF char, glyph, box |
| --- | --- | --- | --- |
| pre | [32] → [] | [53, 53] / [4296, 4296] | [[63]], `a`, (97.966, 252.594, 106.614, 264.571) |
| post | [32] → [] | [52, 52] / [4295, 4295] | [[62]], `,`, (89.311, 252.594, 97.958, 264.571) |

Required target/anchor: `a` at (97.966, 252.594, 106.614, 264.571).

Pre alignment: `[{"tag": "equal", "expected_start": 47, "expected_end": 48, "actual_start": 4293, "actual_end": 4294}, {"tag": "equal", "expected_start": 48, "expected_end": 49, "actual_start": 4294, "actual_end": 4295}, {"tag": "equal", "expected_start": 49, "expected_end": 50, "actual_start": 4295, "actual_end": 4296}, {"tag": "delete", "expected_start": 50, "expected_end": 51, "actual_start": 4296, "actual_end": 4296}, {"tag": "equal", "expected_start": 51, "expected_end": 54, "actual_start": 4296, "actual_end": 4299}]`

Post alignment: `[{"tag": "equal", "expected_start": 47, "expected_end": 48, "actual_start": 4293, "actual_end": 4294}, {"tag": "equal", "expected_start": 48, "expected_end": 49, "actual_start": 4294, "actual_end": 4295}, {"tag": "delete", "expected_start": 49, "expected_end": 50, "actual_start": 4295, "actual_end": 4295}, {"tag": "equal", "expected_start": 50, "expected_end": 54, "actual_start": 4295, "actual_end": 4299}]`

## DIV-0500 — bucket B

Pre/post alignment, finding, provenance, and box are identical. One available insertion finding lies in the same contiguous two-comma run as the target and satisfies every equivalence guard except comparison against actual_mask=15 (the original target p). code_target=',' and the actual inserted PDF glyph both encode mask 32. The evaluator checks the wrong manifest field. The unique compatible finding has not been consumed by another mutation.

Expected mutation span: [2, 2]; target PDF char [6].

| Trace | Expected → actual masks | Actual span (page / document) | Provenance: PDF char, glyph, box |
| --- | --- | --- | --- |
| pre | [] → [32] | [3, 4] / [5499, 5500] | [[5]], `,`, (115.126, 68.274, 123.773, 80.251) |
| post | [] → [32] | [3, 4] / [5499, 5500] | [[5]], `,`, (115.126, 68.274, 123.773, 80.251) |

Required target/anchor: `,` at (123.781, 68.274, 132.429, 80.251).

Pre alignment: `[{"tag": "replace", "expected_start": 0, "expected_end": 1, "actual_start": 5498, "actual_end": 5499}, {"tag": "insert", "expected_start": 1, "expected_end": 1, "actual_start": 5499, "actual_end": 5500}, {"tag": "equal", "expected_start": 1, "expected_end": 12, "actual_start": 5500, "actual_end": 5511}]`

Post alignment: `[{"tag": "replace", "expected_start": 0, "expected_end": 1, "actual_start": 5498, "actual_end": 5499}, {"tag": "insert", "expected_start": 1, "expected_end": 1, "actual_start": 5499, "actual_end": 5500}, {"tag": "equal", "expected_start": 1, "expected_end": 12, "actual_start": 5500, "actual_end": 5511}]`

## DIV-0521 — bucket A

The only runtime change moves the deletion from the second to the first identical expected cell. The gap and its exact provenance/box move one surviving cell earlier. Pre is exact under the current deletion-anchor policy; post fails. This is a localization-policy regression, not downstream mapping corruption: deleting either identical expected cell produces the same cell stream. No evaluator-compatible candidate was consumed by another mutation.

Expected mutation span: [127, 128]; target PDF char [136].

| Trace | Expected → actual masks | Actual span (page / document) | Provenance: PDF char, glyph, box |
| --- | --- | --- | --- |
| pre | [32] → [] | [131, 131] / [5819, 5819] | [[136]], `c`, (80.655, 183.474, 89.303, 195.451) |
| post | [32] → [] | [130, 130] / [5818, 5818] | [[135]], `,`, (72.0, 183.474, 80.648, 195.451) |

Required target/anchor: `c` at (80.655, 183.474, 89.303, 195.451).

Pre alignment: `[{"tag": "equal", "expected_start": 119, "expected_end": 127, "actual_start": 5811, "actual_end": 5819}, {"tag": "delete", "expected_start": 127, "expected_end": 128, "actual_start": 5819, "actual_end": 5819}, {"tag": "equal", "expected_start": 128, "expected_end": 130, "actual_start": 5819, "actual_end": 5821}]`

Post alignment: `[{"tag": "equal", "expected_start": 119, "expected_end": 126, "actual_start": 5811, "actual_end": 5818}, {"tag": "delete", "expected_start": 126, "expected_end": 127, "actual_start": 5818, "actual_end": 5818}, {"tag": "equal", "expected_start": 127, "expected_end": 130, "actual_start": 5818, "actual_end": 5821}]`

## DIV-0585 — bucket A

The only runtime change moves the deletion from the second to the first identical expected cell. The gap and its exact provenance/box move one surviving cell earlier. Pre is exact under the current deletion-anchor policy; post fails. This is a localization-policy regression, not downstream mapping corruption: deleting either identical expected cell produces the same cell stream. No evaluator-compatible candidate was consumed by another mutation.

Expected mutation span: [367, 368]; target PDF char [370].

| Trace | Expected → actual masks | Actual span (page / document) | Provenance: PDF char, glyph, box |
| --- | --- | --- | --- |
| pre | [17] → [] | [371, 371] / [6387, 6387] | [[370]], `p`, (253.351, 321.714, 261.998, 333.691) |
| post | [17] → [] | [370, 370] / [6386, 6386] | [[369]], `e`, (244.695, 321.714, 253.343, 333.691) |

Required target/anchor: `p` at (253.351, 321.714, 261.998, 333.691).

Pre alignment: `[{"tag": "equal", "expected_start": 354, "expected_end": 367, "actual_start": 6374, "actual_end": 6387}, {"tag": "delete", "expected_start": 367, "expected_end": 368, "actual_start": 6387, "actual_end": 6387}, {"tag": "equal", "expected_start": 368, "expected_end": 381, "actual_start": 6387, "actual_end": 6400}]`

Post alignment: `[{"tag": "equal", "expected_start": 354, "expected_end": 366, "actual_start": 6374, "actual_end": 6386}, {"tag": "delete", "expected_start": 366, "expected_end": 367, "actual_start": 6386, "actual_end": 6386}, {"tag": "equal", "expected_start": 367, "expected_end": 381, "actual_start": 6386, "actual_end": 6400}]`

## DIV-0592 — bucket A

The only runtime change moves the deletion from the second to the first identical expected cell. The gap and its exact provenance/box move one surviving cell earlier. Pre is exact under the current deletion-anchor policy; post fails. This is a localization-policy regression, not downstream mapping corruption: deleting either identical expected cell produces the same cell stream. No evaluator-compatible candidate was consumed by another mutation.

Expected mutation span: [50, 51]; target PDF char [63].

| Trace | Expected → actual masks | Actual span (page / document) | Provenance: PDF char, glyph, box |
| --- | --- | --- | --- |
| pre | [32] → [] | [53, 53] / [6520, 6520] | [[63]], `a`, (97.966, 252.594, 106.614, 264.571) |
| post | [32] → [] | [52, 52] / [6519, 6519] | [[62]], `,`, (89.311, 252.594, 97.958, 264.571) |

Required target/anchor: `a` at (97.966, 252.594, 106.614, 264.571).

Pre alignment: `[{"tag": "equal", "expected_start": 47, "expected_end": 48, "actual_start": 6517, "actual_end": 6518}, {"tag": "equal", "expected_start": 48, "expected_end": 49, "actual_start": 6518, "actual_end": 6519}, {"tag": "equal", "expected_start": 49, "expected_end": 50, "actual_start": 6519, "actual_end": 6520}, {"tag": "delete", "expected_start": 50, "expected_end": 51, "actual_start": 6520, "actual_end": 6520}, {"tag": "equal", "expected_start": 51, "expected_end": 54, "actual_start": 6520, "actual_end": 6523}]`

Post alignment: `[{"tag": "equal", "expected_start": 47, "expected_end": 48, "actual_start": 6517, "actual_end": 6518}, {"tag": "equal", "expected_start": 48, "expected_end": 49, "actual_start": 6518, "actual_end": 6519}, {"tag": "delete", "expected_start": 49, "expected_end": 50, "actual_start": 6519, "actual_end": 6519}, {"tag": "equal", "expected_start": 50, "expected_end": 54, "actual_start": 6519, "actual_end": 6523}]`

## DIV-0700 — bucket B

Pre/post alignment, finding, provenance, and box are identical. One available insertion finding lies in the same contiguous two-comma run as the target and satisfies every equivalence guard except comparison against actual_mask=15 (the original target p). code_target=',' and the actual inserted PDF glyph both encode mask 32. The evaluator checks the wrong manifest field. The unique compatible finding has not been consumed by another mutation.

Expected mutation span: [2, 2]; target PDF char [6].

| Trace | Expected → actual masks | Actual span (page / document) | Provenance: PDF char, glyph, box |
| --- | --- | --- | --- |
| pre | [] → [32] | [3, 4] / [7679, 7680] | [[5]], `,`, (115.126, 68.274, 123.773, 80.251) |
| post | [] → [32] | [3, 4] / [7679, 7680] | [[5]], `,`, (115.126, 68.274, 123.773, 80.251) |

Required target/anchor: `,` at (123.781, 68.274, 132.429, 80.251).

Pre alignment: `[{"tag": "replace", "expected_start": 0, "expected_end": 1, "actual_start": 7678, "actual_end": 7679}, {"tag": "insert", "expected_start": 1, "expected_end": 1, "actual_start": 7679, "actual_end": 7680}, {"tag": "equal", "expected_start": 1, "expected_end": 12, "actual_start": 7680, "actual_end": 7691}]`

Post alignment: `[{"tag": "replace", "expected_start": 0, "expected_end": 1, "actual_start": 7678, "actual_end": 7679}, {"tag": "insert", "expected_start": 1, "expected_end": 1, "actual_start": 7679, "actual_end": 7680}, {"tag": "equal", "expected_start": 1, "expected_end": 12, "actual_start": 7680, "actual_end": 7691}]`

## DIV-0720 — bucket A

The only runtime change moves the deletion from the second to the first identical expected cell. The gap and its exact provenance/box move one surviving cell earlier. Pre is exact under the current deletion-anchor policy; post fails. This is a localization-policy regression, not downstream mapping corruption: deleting either identical expected cell produces the same cell stream. No evaluator-compatible candidate was consumed by another mutation.

Expected mutation span: [127, 128]; target PDF char [137].

| Trace | Expected → actual masks | Actual span (page / document) | Provenance: PDF char, glyph, box |
| --- | --- | --- | --- |
| pre | [32] → [] | [132, 132] / [7999, 7999] | [[137]], `c`, (80.655, 183.474, 89.303, 195.451) |
| post | [32] → [] | [131, 131] / [7998, 7998] | [[136]], `,`, (72.0, 183.474, 80.648, 195.451) |

Required target/anchor: `c` at (80.655, 183.474, 89.303, 195.451).

Pre alignment: `[{"tag": "equal", "expected_start": 118, "expected_end": 127, "actual_start": 7990, "actual_end": 7999}, {"tag": "delete", "expected_start": 127, "expected_end": 128, "actual_start": 7999, "actual_end": 7999}, {"tag": "equal", "expected_start": 128, "expected_end": 130, "actual_start": 7999, "actual_end": 8001}]`

Post alignment: `[{"tag": "equal", "expected_start": 118, "expected_end": 126, "actual_start": 7990, "actual_end": 7998}, {"tag": "delete", "expected_start": 126, "expected_end": 127, "actual_start": 7998, "actual_end": 7998}, {"tag": "equal", "expected_start": 127, "expected_end": 130, "actual_start": 7998, "actual_end": 8001}]`

## DIV-0791 — bucket A

The only runtime change moves the deletion from the second to the first identical expected cell. The gap and its exact provenance/box move one surviving cell earlier. Pre is exact under the current deletion-anchor policy; post fails. This is a localization-policy regression, not downstream mapping corruption: deleting either identical expected cell produces the same cell stream. No evaluator-compatible candidate was consumed by another mutation.

Expected mutation span: [50, 51]; target PDF char [62].

| Trace | Expected → actual masks | Actual span (page / document) | Provenance: PDF char, glyph, box |
| --- | --- | --- | --- |
| pre | [32] → [] | [52, 52] / [8700, 8700] | [[62]], `a`, (97.966, 252.594, 106.614, 264.571) |
| post | [32] → [] | [51, 51] / [8699, 8699] | [[61]], `,`, (89.311, 252.594, 97.958, 264.571) |

Required target/anchor: `a` at (97.966, 252.594, 106.614, 264.571).

Pre alignment: `[{"tag": "equal", "expected_start": 46, "expected_end": 48, "actual_start": 8696, "actual_end": 8698}, {"tag": "equal", "expected_start": 48, "expected_end": 49, "actual_start": 8698, "actual_end": 8699}, {"tag": "equal", "expected_start": 49, "expected_end": 50, "actual_start": 8699, "actual_end": 8700}, {"tag": "delete", "expected_start": 50, "expected_end": 51, "actual_start": 8700, "actual_end": 8700}, {"tag": "equal", "expected_start": 51, "expected_end": 54, "actual_start": 8700, "actual_end": 8703}]`

Post alignment: `[{"tag": "equal", "expected_start": 46, "expected_end": 48, "actual_start": 8696, "actual_end": 8698}, {"tag": "equal", "expected_start": 48, "expected_end": 49, "actual_start": 8698, "actual_end": 8699}, {"tag": "delete", "expected_start": 49, "expected_end": 50, "actual_start": 8699, "actual_end": 8699}, {"tag": "equal", "expected_start": 50, "expected_end": 54, "actual_start": 8699, "actual_end": 8703}]`

## DIV-0901 — bucket B

Pre/post alignment, finding, provenance, and box are identical. One available insertion finding lies in the same contiguous two-comma run as the target and satisfies every equivalence guard except comparison against actual_mask=15 (the original target p). code_target=',' and the actual inserted PDF glyph both encode mask 32. The evaluator checks the wrong manifest field. The unique compatible finding has not been consumed by another mutation.

Expected mutation span: [2, 2]; target PDF char [6].

| Trace | Expected → actual masks | Actual span (page / document) | Provenance: PDF char, glyph, box |
| --- | --- | --- | --- |
| pre | [] → [32] | [3, 4] / [9881, 9882] | [[5]], `,`, (115.126, 68.274, 123.773, 80.251) |
| post | [] → [32] | [3, 4] / [9881, 9882] | [[5]], `,`, (115.126, 68.274, 123.773, 80.251) |

Required target/anchor: `,` at (123.781, 68.274, 132.429, 80.251).

Pre alignment: `[{"tag": "replace", "expected_start": 0, "expected_end": 1, "actual_start": 9880, "actual_end": 9881}, {"tag": "insert", "expected_start": 1, "expected_end": 1, "actual_start": 9881, "actual_end": 9882}, {"tag": "equal", "expected_start": 1, "expected_end": 12, "actual_start": 9882, "actual_end": 9893}]`

Post alignment: `[{"tag": "replace", "expected_start": 0, "expected_end": 1, "actual_start": 9880, "actual_end": 9881}, {"tag": "insert", "expected_start": 1, "expected_end": 1, "actual_start": 9881, "actual_end": 9882}, {"tag": "equal", "expected_start": 1, "expected_end": 12, "actual_start": 9882, "actual_end": 9893}]`

## DIV-0921 — bucket A

The only runtime change moves the deletion from the second to the first identical expected cell. The gap and its exact provenance/box move one surviving cell earlier. Pre is exact under the current deletion-anchor policy; post fails. This is a localization-policy regression, not downstream mapping corruption: deleting either identical expected cell produces the same cell stream. No evaluator-compatible candidate was consumed by another mutation.

Expected mutation span: [127, 128]; target PDF char [136].

| Trace | Expected → actual masks | Actual span (page / document) | Provenance: PDF char, glyph, box |
| --- | --- | --- | --- |
| pre | [32] → [] | [131, 131] / [10201, 10201] | [[136]], `c`, (80.655, 183.474, 89.303, 195.451) |
| post | [32] → [] | [130, 130] / [10200, 10200] | [[135]], `,`, (72.0, 183.474, 80.648, 195.451) |

Required target/anchor: `c` at (80.655, 183.474, 89.303, 195.451).

Pre alignment: `[{"tag": "equal", "expected_start": 119, "expected_end": 127, "actual_start": 10193, "actual_end": 10201}, {"tag": "delete", "expected_start": 127, "expected_end": 128, "actual_start": 10201, "actual_end": 10201}, {"tag": "equal", "expected_start": 128, "expected_end": 130, "actual_start": 10201, "actual_end": 10203}]`

Post alignment: `[{"tag": "equal", "expected_start": 119, "expected_end": 126, "actual_start": 10193, "actual_end": 10200}, {"tag": "delete", "expected_start": 126, "expected_end": 127, "actual_start": 10200, "actual_end": 10200}, {"tag": "equal", "expected_start": 127, "expected_end": 130, "actual_start": 10200, "actual_end": 10203}]`

## DIV-0985 — bucket A

The only runtime change moves the deletion from the second to the first identical expected cell. The gap and its exact provenance/box move one surviving cell earlier. Pre is exact under the current deletion-anchor policy; post fails. This is a localization-policy regression, not downstream mapping corruption: deleting either identical expected cell produces the same cell stream. No evaluator-compatible candidate was consumed by another mutation.

Expected mutation span: [367, 368]; target PDF char [370].

| Trace | Expected → actual masks | Actual span (page / document) | Provenance: PDF char, glyph, box |
| --- | --- | --- | --- |
| pre | [17] → [] | [371, 371] / [10769, 10769] | [[370]], `p`, (253.351, 321.714, 261.998, 333.691) |
| post | [17] → [] | [370, 370] / [10768, 10768] | [[369]], `e`, (244.695, 321.714, 253.343, 333.691) |

Required target/anchor: `p` at (253.351, 321.714, 261.998, 333.691).

Pre alignment: `[{"tag": "equal", "expected_start": 354, "expected_end": 367, "actual_start": 10756, "actual_end": 10769}, {"tag": "delete", "expected_start": 367, "expected_end": 368, "actual_start": 10769, "actual_end": 10769}, {"tag": "equal", "expected_start": 368, "expected_end": 381, "actual_start": 10769, "actual_end": 10782}]`

Post alignment: `[{"tag": "equal", "expected_start": 354, "expected_end": 366, "actual_start": 10756, "actual_end": 10768}, {"tag": "delete", "expected_start": 366, "expected_end": 367, "actual_start": 10768, "actual_end": 10768}, {"tag": "equal", "expected_start": 367, "expected_end": 381, "actual_start": 10768, "actual_end": 10782}]`

## DIV-0992 — bucket A

The only runtime change moves the deletion from the second to the first identical expected cell. The gap and its exact provenance/box move one surviving cell earlier. Pre is exact under the current deletion-anchor policy; post fails. This is a localization-policy regression, not downstream mapping corruption: deleting either identical expected cell produces the same cell stream. No evaluator-compatible candidate was consumed by another mutation.

Expected mutation span: [50, 51]; target PDF char [63].

| Trace | Expected → actual masks | Actual span (page / document) | Provenance: PDF char, glyph, box |
| --- | --- | --- | --- |
| pre | [32] → [] | [53, 53] / [10902, 10902] | [[63]], `a`, (97.966, 252.594, 106.614, 264.571) |
| post | [32] → [] | [52, 52] / [10901, 10901] | [[62]], `,`, (89.311, 252.594, 97.958, 264.571) |

Required target/anchor: `a` at (97.966, 252.594, 106.614, 264.571).

Pre alignment: `[{"tag": "equal", "expected_start": 47, "expected_end": 48, "actual_start": 10899, "actual_end": 10900}, {"tag": "equal", "expected_start": 48, "expected_end": 49, "actual_start": 10900, "actual_end": 10901}, {"tag": "equal", "expected_start": 49, "expected_end": 50, "actual_start": 10901, "actual_end": 10902}, {"tag": "delete", "expected_start": 50, "expected_end": 51, "actual_start": 10902, "actual_end": 10902}, {"tag": "equal", "expected_start": 51, "expected_end": 54, "actual_start": 10902, "actual_end": 10905}]`

Post alignment: `[{"tag": "equal", "expected_start": 47, "expected_end": 48, "actual_start": 10899, "actual_end": 10900}, {"tag": "equal", "expected_start": 48, "expected_end": 49, "actual_start": 10900, "actual_end": 10901}, {"tag": "delete", "expected_start": 49, "expected_end": 50, "actual_start": 10901, "actual_end": 10901}, {"tag": "equal", "expected_start": 50, "expected_end": 54, "actual_start": 10901, "actual_end": 10905}]`

## Engineering conclusion

The dominant cause is the new global preference for the first deletable identical cell (15/20). The remaining 5/20 are rejected insertion equivalences caused by reading the original target mask. There is no association collision in this cohort, and no independent provenance or box defect. Any subsequent production fix must preserve the six repaired cases while addressing the 15 shifted anchors, or explicitly establish deletion equivalence before changing adjudication. Merely reverting the branch would restore those 15 but reintroduce the six earlier failures. The insertion evaluator can use the actual inserted cell independently of production. No production/evaluator behavior was changed in this diagnostic task. Combined closure remains FAIL.
