# Document-stream alignment release verification

Status: **DOCUMENT-STREAM ALIGNMENT RESTORED**

The validator now aligns one ordered source-cell stream with one ordered actual Braille-cell stream. Source page, block and rule ownership remain attached to expected offsets. Physical Braille pages remain separate in the raw input and are represented by document-global offsets that map back to page-local cell positions for the existing PDF highlighter.

Physical page boundaries contribute a line-break blank to matching but do not terminate a source passage or math span. No source-to-Braille page ratio is assumed. Supported validation rules, math generation, capitalization logic, Duxbury spacing normalization, and highlighting code are unchanged.

If actual math switches do not pair one-for-one with source spans, ordered source-guided matching retains every independently identifiable span. Unresolved source spans are counted and their overlapping raw differences are classified `REVIEW_REQUIRED` internally rather than confirmed as errors. A three-span guard with its middle passage removed reports 2 evaluated, 1 unresolved, and an internal review.

| Test | English pages | Braille pages | Passages | Math evaluated | Capitals evaluated | Normalized spans | Tolerated cells | Errors | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Test 1 | 5 | 15 | 115/115 | 93/93 | 111/111 | 82 | 277 | 0 | 0 |
| Test 2 | 5 | 15 | 121/121 | 93/93 | 106/106 | 84 | 282 | 0 | 0 |
| Test 3 | 5 | 14 | 122/122 | 98/98 | 110/110 | 91 | 307 | 0 | 0 |
| Test 4 | 5 | 10 | 118/118 | 115/115 | 154/154 | 102 | 378 | 0 | 0 |
| Test 5 | 5 | 10 | 116/116 | 150/150 | 71/71 | 58 | 186 | 0 | 0 |

Test 3 retains the previously observed extra terminating switch. It is recorded internally as one unmatched switch marker and does not invalidate the other spans. The current supported switching rule does not promote this source-less insertion to a confirmed error.

Regression results: clean fixtures pass; 6/6 math corruptions and 3/3 capitalization corruptions are detected; 42/42 spacing cases, 42/42 PDF-coordinate cases and 68/68 guard cases pass. A test-only source mutation on logical page 5 maps to the correct single cell on physical Braille page 13. The frozen executable passes all five full-document cases with the coverage shown above. All source and Braille inputs retained their hashes.

Evidence: `document_stream_acceptance.json`, `document_stream_frozen.json`, `duxbury_spacing_stream_final.json`, `duxbury_spacing_pdf_stream_final.json`, and `duxbury_spacing_guards.json`.

Delivery: `dist/BrailleValidator_Demo_2026-09-12.zip` (75,487,923 bytes), SHA-256 `8888fb333f11364c81cce3fde35a72b6480e71cde70aee4506b66e56daf358da`. Executable SHA-256: `f84a68ee088523429168cb08e20b072a4ee14751143822dfb1015b95a88a9014`. The previous delivery is retained in `_archive/release_before_document_stream_20260912`.
