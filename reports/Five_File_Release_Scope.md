# Five-file release-scope test

**SUPPORTED CASES STILL FAIL ON SYNTHETIC FILES**

Current packaged GUI runs matched production API statistics for all five. No code or inputs changed.

| Test | Errors | Source math spans | Source uppercase sites | Equal math spans | Equal capital/letter anchors | Equal uppercase anchors | Reviews | Exclusions | Suppressed alignment findings | Ignored unmapped differences | Historical cross-page spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0 | 93 | 111 | 9 | 84 | 11 | 0 | 0 | 4 | 28 | 1 |
| 2 | 0 | 93 | 106 | 5 | 87 | 12 | 0 | 0 | 3 | 26 | 2 |
| 3 | 0 | 98 | 110 | 6 | 109 | 13 | 0 | 0 | 8 | 25 | 1 |
| 4 | 0 | 115 | 154 | 9 | 110 | 18 | 0 | 0 | 5 | 31 | 3 |
| 5 | 0 | 150 | 71 | 16 | 73 | 11 | 0 | 0 | 11 | 19 | 2 |

Completed-check counts are not exposed by production. Source counts mean recognized opportunities, not completed checks. Equal-alignment counts are diagnostic evidence, not certified successful semantic checks. Capital/letter anchors include lowercase controls. Historical cross-page counts concern the unchanged inputs.

## Findings

1. Supported-rule genuine errors: none confirmed; incomplete alignment prevents certifying their absence.
2. Unsupported constructs: zero REVIEW items emitted. This does not certify the unaligned remainder.
3. Alignment/mapping: each DOCX is treated as one source page on the public app path, versus 15/15/14/10/10 PDF pages. Every run flags incomplete coverage. All comparison views reject pairing with "Unpaired switches or source/actual span count mismatch". Zero spans normalized and zero artifact cells tolerated in every file.
4. Broken/cross-page math: present in every file according to the unchanged-file audit. Test 3 still has the extra `_:` at the beginning of PDF page 2 before `-#9 _:`. Re-reading confirms it; it is absent in the DXB. The current build does not report this extra terminator. This exact cross-page switching case is outside the guaranteed release scope, not correct.
5. Marker/source: no literal math-marker error emitted. Source page handling is an alignment issue, not evidence of malformed math markers.
6. Spacing outside verified tolerance: no isolated new spacing pattern established. Zero spacing-only confirmed errors. Whether spacing alone causes a particular skip cannot be isolated because passage pairing fails first; the known-spacing tolerance is not engaged for any span.
7. Other: no additional issue established.

## Acceptance answer

No: the current full-document runs do not establish reliable evaluation of all supported math and capitalization cases. The 42-case spacing matrix remains valid under its tested pairing conditions, but those conditions are not met by these realistic multi-page uploads. Zero displayed errors is not a clean-document verdict.

Files and source code were not modified. Raw output and input hashes are in five_file_current_release_scope.json. Packaged GUI runs are in five_file_release_run/Test_1.json through Test_5.json.

Executable SHA-256: 115ec43f545b0614b8cf0d8e98d1b40cf271de33917227a179e6c2ff6f0cec29
