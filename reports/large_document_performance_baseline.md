# Large-document performance baseline

Baseline captured from the current production implementation before optimization. No production source was modified by this profile run.

Runtime: Python 3.12.14 bundled workspace runtime on Windows. Measurements are single-process wall-clock runs; peak working set is process high-water memory. The comparison-only stage reuses its already-generated expected document only to isolate alignment cost; end-to-end timings call the public API unchanged.

## Fixture summary

| Fixture | Source pages | Braille PDF pages | Source chars | Expected cells | Actual stream chars | Errors | Reviews |
|---|---:|---:|---:|---:|---:|---:|---:|
| test1_clean | 5 | 15 | 9975 | 7554 | 8569 | 0 | 0 |
| test1_corrupted | 5 | 15 | 9975 | 7554 | 8574 | 67 | 0 |

## Baseline timings

| Fixture | End-to-end | Master extraction | Braille extraction | Expected generation + rules | Comparison/alignment | Finding generation | Provenance mapping | PDF export | JSON serialization | Peak working set |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| test1_clean | 1.205s | 1.853s | 2.418s | 0.681s | 0.254s | 0.003s | 0.029s | 0.047s | 0.000s | 109.9 MiB |
| test1_corrupted | 1.247s | 1.922s | 2.469s | 0.454s | 0.282s | 0.014s | 0.030s | 0.051s | 0.004s | 132.4 MiB |

## Pipeline and observed cost centers

1. Source extraction is page/block based. DOCX extraction is paragraph-oriented; PDF source extraction uses `pdfplumber` word extraction and line regrouping.
2. Braille PDF extraction is expensive and memory-sensitive: it opens the PDF, inspects embedded fonts, renders glyph masks to infer dot maps, rebuilds lines, retains per-cell provenance, then normalizes and verifies word provenance.
3. Expected generation translates each source group and then runs the rule engine. `ExpectedBrailleDocument` retains every page, block, Braille string, rule result, math record and capitalization site for localization.
4. Validation flattens both logical documents into one continuous cell stream, runs `ComparisonView`, then `SequenceMatcher` through `align_cells`. It also retains page alignments, actual page offsets, actual stream cells, differences and provenance-relevant offsets.
5. Finding adaptation walks pages/blocks/differences repeatedly to produce UI-safe issues and exact physical ranges. PDF provenance is loaded again by the GUI worker before annotation, so the public GUI path parses the Braille PDF twice.
6. Annotation reads and writes the full PDF, including original page streams. JSON report serialization is proportional to finding volume and is not a leading cost in the baseline.

## Suspected bottlenecks requiring the next phase

- Continuous `SequenceMatcher(..., autojunk=False)` over the complete expected/actual document stream is the highest-risk scaling point. It is also correctness-critical and must not be replaced without large-corruption localization gates.
- PDF font/glyph inspection and provenance retention are repeated: the GUI first extracts the PDF for validation and later calls `load_pdf_provenance` again for annotation.
- `ExpectedBrailleDocument.blocks` flattens all blocks into a new tuple whenever accessed; validator and API helpers call related page/block traversals repeatedly.
- Several provenance helpers build temporary lists (`nonblank_positions`, selected ranges, page records) per lookup. This is likely secondary to full-stream alignment but should be measured on very large inputs.
- The GUI already moves validation to `ValidationThread`; responsiveness is therefore mainly threatened by worker duration, memory pressure, and the second PDF parse, not by validation executing on the Qt event loop.

## Correctness baseline

- `test1_clean`: 0 confirmed errors, 0 reviews, cell accuracy 1.000000, math aligned 93/93, source passages aligned 115/115, capitalization opportunities aligned 111/111.
- `test1_corrupted`: 67 confirmed errors, 0 reviews, cell accuracy 0.992175, math aligned 93/93, source passages aligned 66/115, capitalization opportunities aligned 111/111.

## Constraints for optimization

The next phase must preserve document-wide logical alignment across arbitrary physical page breaks, exact cell provenance, REVIEW/EXCLUDED handling, Duxbury spacing tolerance, operator-anchor behavior, and deterministic output. No page-ratio assumption, alignment rewrite, standards-rule change, or PDF graphics-state change is justified by this baseline alone.

Detailed cProfile output is in `reports/large_document_profile_work/`.
