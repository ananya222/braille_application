# Large-document performance final report

## Outcome

The validator now scales through the supplied 1,000-source-page fixture without losing the existing correctness gates. The safe changes are limited to alignment fast paths, per-page PDF cache release, and GUI provenance reuse. No translation rules, issue categories, annotation geometry, or scope behavior were changed.

The 1,000-page fixture is not a fast interactive workload: it takes about 5.6 minutes and peaks at about 948.5 MiB. The current implementation is therefore materially safer for large documents, but it is not yet a streaming validator.

## Changes made

1. `src/braille_app/validation/alignment.py`
   - Returns one `equal` opcode for identical streams.
   - Uses a linear opcode walk when the nonblank cell sequences are identical and only blank cells differ.
   - Falls back to the existing `difflib.SequenceMatcher(..., autojunk=False)` for all other inputs.

2. `src/braille_app/doc_extractor.py` and `src/braille_app/input_reader.py`
   - Calls `pdfplumber.Page.close()` after each page has been converted into the retained application structures.
   - This releases cached layout/character graphs instead of retaining every parsed page until PDF close.

3. `src/braille_app/validation/api.py` and `main_gui.py`
   - Adds an opt-in `retain_pdf_provenance` API flag.
   - The GUI uses the provenance already loaded during validation instead of reparsing the PDF before annotation.
   - Default API calls do not retain the provenance object.

## Pre-change baseline

The audit-only baseline is recorded in `reports/large_document_performance_baseline.md`.

| Fixture | End-to-end | Peak working set | Result |
|---|---:|---:|---|
| Test 1 clean, 5 source pages | 1.205 s | 109.9 MiB | 0 errors, 1.000000 accuracy |
| Test 1 corrupted, 5 source pages | 1.247 s | 132.4 MiB | 67 errors, 0 reviews |
| Repeated 100-source-page clean, before change | 27.42 s | 457.4 MiB | 0 errors, 1.000000 accuracy |
| Repeated 250-source-page clean, before change | 71.91 s | 1,134.6 MiB | 0 errors, 1.000000 accuracy |

The baseline’s cProfile timings are explicitly separate from the wall-clock timings; cProfile inflated the 5-page runs to about 3.2 s.

## Final scaling results

Each fixture repeats the same verified five-source-page packet. Its clean Braille PDF repeats the corresponding 15-page packet. Sparse-corrupted variants substitute the known stress-test page into five packet positions: beginning, quarter, middle, three-quarter, and end. Each substituted page carries five known corruptions, for 25 expected errors.

| Source pages | Actual Braille pages | Variant | Runtime | Peak working set | Errors | Cell accuracy | Passages aligned |
|---:|---:|---|---:|---:|---:|---:|---:|
| 10 | 30 | clean | 3.34 s | 97.6 MiB | 0 | 1.000000 | 230/230 |
| 100 | 300 | clean | 27.77 s | 139.7 MiB | 0 | 1.000000 | 2300/2300 |
| 100 | 300 | sparse corruption | 27.97 s | 138.8 MiB | 25 | 0.999837 | 2280/2300 |
| 250 | 750 | clean | 70.35 s | 277.0 MiB | 0 | 1.000000 | 5750/5750 |
| 250 | 750 | sparse corruption | 67.75 s | 276.3 MiB | 25 | 0.999935 | 5730/5750 |
| 500 | 1500 | clean | 143.70 s | 502.0 MiB | 0 | 1.000000 | 11500/11500 |
| 500 | 1500 | sparse corruption | 113.05 s | 501.9 MiB | 25 | 0.999967 | 11480/11500 |
| 1000 | 3000 | clean | 336.24 s | 948.5 MiB | 0 | 1.000000 | 23000/23000 |
| 1000 | 3000 | sparse corruption | 335.07 s | 948.5 MiB | 25 | 0.999984 | 22980/23000 |

The sparse-corruption passage shortfall is expected: each corrupted page invalidates four source passages in the existing classification model. No review or exclusion was incorrectly promoted to a confirmed error.

Raw benchmark JSON and fixture manifests are in `reports/large_document_fixtures/`.

## Correctness gates executed

- Existing 5-page clean fixture: 0 errors, 0 reviews, 93/93 math spans, 111/111 capitalization opportunities, 115/115 source passages.
- Existing 5-page 67-error stress fixture: 67 errors, 0 reviews, 93/93 math spans and 111/111 capitalization opportunities; statistics match the pre-change baseline.
- Repeated clean fixtures at 10, 100, 250, 500, and 1,000 source pages: 0 errors and 1.000000 cell accuracy.
- Sparse corruption at 100, 250, 500, and 1,000 source pages: exactly 25 errors, 0 reviews, 0 exclusions.
- Retained-provenance GUI path: validator statistics match the legacy path; base provenance alignment reported 0 unmatched cells and 0 unexplained offsets.
- Randomized opcode reconstruction self-check: every generated blank-only alignment reconstructed both input streams exactly.
- `compileall` passed for `src` and all new benchmark scripts.

## Stage evidence

On the 100-page final-code stage run, without allocation tracing:

| Stage | Runtime | Peak working set |
|---|---:|---:|
| Master PDF extraction | 9.65 s | 47.4 MiB |
| Braille PDF extraction | 10.84 s | 111.3 MiB |
| Expected generation and rules | 3.91 s | 115.5 MiB |
| Comparison/alignment | 1.33 s | 139.2 MiB |

The major scaling risk was the retained PDF page cache, not the alignment path alone. After cache release, the 100-page peak fell from roughly 489 MiB in the isolated pre-change stage run to roughly 139 MiB. Alignment is now bounded for equal/nonblank-equivalent streams, while arbitrary substitutions still use the existing conservative matcher.

## Remaining limits

- Source and Braille PDF parsing remain CPU-heavy and are still proportional to page count.
- The validator retains the complete expected document, actual stream, provenance, page alignments, comparison views, and issue metadata. The 1,000-page run reaches roughly 1 GiB, so much larger documents should not be promised without a streaming or chunked-result design.
- The general `SequenceMatcher` fallback remains intentionally unchanged for nonblank substitutions, insertions, deletions, and ambiguous streams.
- The packaging build was not produced in this environment: the available `python` is MSYS Python 3.12.11 without PyInstaller, and the bundled workspace runtime also has no PyInstaller. No dependency installation was performed.

## Recommendation

The measured changes are suitable for the current release candidate after the normal application regression suite and a packaging build on the project’s Python 3.12 x64 build environment. Ship the cache-release and GUI-reuse changes. Keep the 1,000-page result as a stress ceiling, not as a latency promise. Do not replace the general matcher or introduce streaming state until a real workload demonstrates that the remaining extraction/retention ceiling is unacceptable.
