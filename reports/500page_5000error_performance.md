# 500-page / 5,000-error performance acceptance

## Final result

**FINAL PERFORMANCE STATUS: PASS**

The current optimized packaged executable passed the complete workload under a
Windows process affinity mask of `0x3` (two logical processors). The benchmark
included source extraction, Braille PDF extraction, Liblouis translation,
normalization/alignment, rule validation, provenance localization, annotated
PDF generation, PDF save, and report export.

No production source or rule files were modified for this benchmark. The only
new code is audit/benchmark harness code under `scripts/`.

## Acceptance workload

| Field | Result |
|---|---:|
| Target hardware | Windows, 2 CPU cores, 8 GB RAM class |
| Pages | 500 |
| Errors per page | 10 |
| Total injected | 5,000 |
| Total Braille cells | 478,499 |
| Fixed seed | 20260921 |
| Affinity mask | `0x3` |

Every page contains exactly ten independent mutations. All seven supported
families occur throughout the document.

## Packaged EXE acceptance

Executable tested:

`O:\braille_0.2\dist\BrailleValidator\BrailleValidator.exe`

| Metric | Result |
|---|---:|
| Total wall time, EXE start to completed outputs | 52.217 s |
| Time per page | 0.104435 s |
| Findings per second | 95.7535 |
| Detected | 5,000 |
| Missed | 0 |
| False positives | 0 |
| Exact physical-cell localizations | 5,000/5,000 |
| Wrong-page highlights | 0 |
| Neighboring-cell highlights | 0 |
| Blank-cell highlights | 0 |
| Duplicate findings | 0 |
| Annotated PDF pages | 500 |
| Blue boxes | 5,000 |
| Report findings | 5,000 |
| Peak working set | 370,417,664 bytes (353.26 MiB) |

The EXE returned code 0 with no stderr output. The exported PDF and JSON
report were reopened and independently checked against the frozen manifest.

The source/API harness independently produced the same correctness result under
the same two-core mask. Its peak working set was 352,698,368 bytes (336.36
MiB), and its measured two-core CPU utilization was 48.97% average and 52.93%
peak.

## Stage profile

The isolated stage profile was run against the exact 500-page/5,000-error
corrupted PDF under affinity `0x3`. These timings are a separate diagnostic
pass and are not added to the acceptance wall time.

| Stage | Seconds | Share of isolated stage pass |
|---|---:|---:|
| Source extraction | 16.342 | 25.73% |
| Braille PDF extraction | 16.096 | 25.34% |
| Expected generation, Liblouis translation, and rules | 7.778 | 12.24% |
| Alignment and classification | 23.311 | 36.69% |
| Isolated stage total | 63.527 | 100.00% |

Normalization is performed inside the PDF-input and comparison paths and is not
exposed as a separate production stage timer. Finding adaptation is included in
the public validation call; the separate post-validation measurements were:

| Post-validation stage | Seconds |
|---|---:|
| Public validation call | 50.404 |
| Provenance/finding mapping | 0.861 |
| PDF annotation and save | 0.265 |
| Report JSON serialization/write | 0.155 |

The API harness’s full wall time including its clean preflight and independent
5,000-box audit was 125.698 seconds. The packaged EXE figure above is the
production acceptance timer because it measures the actual user-facing run and
ends after the annotated PDF and report are written.

## Before-profile baseline

The existing 500-page dense fixture with 2,000 injected errors was profiled
before creating this 5,000-error fixture. Its prior report is
`stress_test/large_documents/500_page_dense_report.json`.

The prior harness’s 201.144-second total included clean preflight, a repeated
stage pass, provenance checks, annotation, and an independent visual audit. Its
actual production validation call was 43.082 seconds.

| Existing dense stage | Seconds | Share of isolated stage pass |
|---|---:|---:|
| Source extraction | 19.219 | 27.60% |
| Braille PDF extraction | 18.395 | 26.42% |
| Expected generation and rules | 8.828 | 12.68% |
| Alignment and classification | 23.189 | 33.30% |
| Isolated stage total | 69.630 | 100.00% |

That baseline identified source/PDF parsing and document-stream comparison as
the dominant costs. Finding construction, provenance mapping, annotation, and
report writing were not the limiting costs at 2,000 findings.

## Finding-count complexity audit

The current implementation was inspected for repeated full-document or
full-PDF work per finding.

- `export_annotated_pdf` groups records by physical page, opens the input PDF
  once, adds all page overlays in one pass, and writes once.
- The GUI reuses retained PDF provenance from validation; it does not perform a
  second full provenance parse before annotation.
- Provenance mapping builds page indexes once. At 5,000 findings it measured
  0.861 seconds.
- The validator performs one continuous document-stream alignment. It does not
  align independently for each finding or rule.
- No finding-squared or finding-times-full-PDF behavior appeared in the 5,000
  finding run. Remaining page/block lookup scans are small compared with source
  extraction, PDF extraction, and alignment.

The measured result did not justify another production optimization pass:
the existing optimized architecture already clears the acceptance target with
large memory headroom.

## Correctness and regression gates

### 5,000-error fixture

| Family | Injected | Detected | Missed | False positives | Exact localization |
|---|---:|---:|---:|---:|---:|
| PLUS | 763 | 763 | 0 | 0 | 763 |
| MINUS | 690 | 690 | 0 | 0 | 690 |
| NEGATIVE | 829 | 829 | 0 | 0 | 829 |
| MULTIPLY | 665 | 665 | 0 | 0 | 665 |
| DIVIDE | 669 | 669 | 0 | 0 | 669 |
| EQUALS | 690 | 690 | 0 | 0 | 690 |
| CAPITALIZATION | 694 | 694 | 0 | 0 | 694 |
| **TOTAL** | **5,000** | **5,000** | **0** | **0** | **5,000** |

The clean paired PDF returned zero confirmed errors.

### Existing dense regression gate

The current packaged EXE was run against the known-good clean fixture and dense
Test1, Test2, and Test4 fixtures:

| Fixture | Injected | Detected | Exact boxes |
|---|---:|---:|---:|
| Clean | 0 | 0 | 0 |
| Test1 | 67 | 67 | 67 |
| Test2 | 68 | 68 | 68 |
| Test4 | 50 | 50 | 50 |
| **Total** | **185** | **185** | **185** |

Combined family totals remained:

`PLUS 26/26`, `MINUS 25/25`, `NEGATIVE 22/22`, `MULTIPLY 27/27`,
`DIVIDE 29/29`, `EQUALS 27/27`, `CAPITALIZATION 29/29`.

Additional current-source checks passed:

- Duxbury spacing: 42/42
- repeated-operand semantic alignment: 12/12
- cross-page physical alignment cases: 15/15
- simple-math clean/corrupted acceptance: 0 and 6 errors as expected
- basic-capitalization clean/corrupted acceptance: 0 and 3 errors as expected

## Artifacts

- Master JSON: `O:\braille_0.2\stress_test\large_documents\500_page_5000_errors_master.json`
- Master DOCX: `O:\braille_0.2\stress_test\large_documents\500_page_5000_errors_master.docx`
- Clean PDF: `O:\braille_0.2\stress_test\large_documents\500_page_5000_errors_clean.pdf`
- Corrupted PDF: `O:\braille_0.2\stress_test\large_documents\500_page_5000_errors_corrupted.pdf`
- Frozen manifest CSV: `O:\braille_0.2\stress_test\large_documents\500_page_5000_errors_manifest.csv`
- Frozen manifest JSON: `O:\braille_0.2\stress_test\large_documents\500_page_5000_errors_manifest_PREVALIDATION.json`
- Source annotated PDF: `O:\braille_0.2\stress_test\large_documents\500_page_5000_errors_validator_output.pdf`
- Source report JSON: `O:\braille_0.2\stress_test\large_documents\500_page_5000_errors_report.json`
- Packaged EXE summary: `O:\braille_0.2\reports\5000_packaged_smoke\summary.json`
- Packaged annotated PDF: `O:\braille_0.2\reports\5000_packaged_smoke\localappdata\BrailleValidator\output\500_page_5000_errors_corrupted_validator_annotated.pdf`
- Packaged report JSON: `O:\braille_0.2\reports\5000_packaged_smoke\localappdata\BrailleValidator\output\500_page_5000_errors_corrupted_validator_report.json`
- Stage profile JSON: `O:\braille_0.2\stress_test\large_documents\500_page_5000_errors_stage_profile.json`

