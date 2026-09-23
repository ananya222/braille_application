# Duxbury spacing release verification

Status: **SUPPORTED DETECTION ROBUST TO KNOWN DUXBURY SPACING**

## Baseline before production changes

All 42 cases returned the expected error counts, including wrong operators with spacing noise. There were no operator misses or spacing-only false positives in this matrix. However, 13 cases highlighted neighboring spacing/numeric-mode cells along with the wrong symbol. Only 29/42 passed exact localization. The PDF baseline independently reproduced those 13 failures. These results were reported before changing production code.

Evidence: `duxbury_spacing_baseline.json` and `duxbury_spacing_pdf_baseline.json`.

## Change

`src/braille_app/validation/simple_math_comparison.py` builds a separate comparison view for uniquely paired, complete, same-page supported math passages. It uses source operands as anchors and preserves actual operator cells, including incorrect symbols. A canonical-to-raw index map projects differences and equal anchors back to original cells. `validator.py` uses that view for alignment while retaining raw actual input and coordinates. `api.py` adds internal normalization counters. No translation grammar or supported rule was added.

Only a uniquely recognized pattern is normalized: at most one blank on each side of a supported binary operator, and an extra numeric indicator following the right artifact blank before a numeric operand. The verified unary pattern permits one blank after the sign before its numeric operand. Equality's required surrounding blanks and numeric restart remain intact. Other blanks, numeric indicators, prose, and unsupported structures are not globally stripped. Inputs and original PDFs are unchanged.

## Verification

- 42/42 comparison cases pass: six operators, clean/noisy correct and incorrect forms, repeated occurrences, prose boundaries, capitalization correct/missing/wrong/unnecessary, and unary spacing. Repeated equality uses two separate supported spans.
- 42/42 PDF cases pass exact original-cell coordinates; annotated exports preserve the Braille body. All 42 exports were visually inspected.
- 68/68 additional guards pass, including operator swaps of different widths, corruption of the first cell in two-cell symbols, capitals after noisy math, ambiguous/unsupported patterns, equality spacing preservation, and a 150-term supported chain.
- Original clean demos remain clean; the six deliberate math errors and three capitalization errors remain detected. The original demo and five synthetic conversion inputs were not modified.
- The shipping executable is tested through its actual Qt worker, result UI, JSON report export and PDF annotation paths. See `duxbury_spacing_frozen.json` and `../packaging/release_qa/frozen/acceptance.json` for executable identity and results.
- All 42 spacing cases also pass through the frozen executable, including exact raw error ranges and rule IDs. The final ZIP was extracted to a temporary folder, every file verified, and all four demos rerun with Python file access to the development root blocked. Portable acceptance: `../packaging/release_qa/portable_acceptance.json`.

The current delivery supersedes this spacing-only build; see `Document_Stream_Alignment.md` for current package hashes. The earlier spacing build remains archived.

## Remaining limits

This verifies the known spacing patterns in otherwise-supported inputs. Cross-page math, mismatched passage counts, broken math switches, altered operands, ambiguous patterns, and unverified spacing forms fall back to the existing comparison; detection in those cases is not certified by this change. Existing pagination/alignment limitations remain, including unchecked regions whose diagnostics are suppressed from the requested normal UI. A zero displayed-error count is not a certification of arbitrary Duxbury output. The five synthetic conversions were not cleaned or certified.

GUI acceptance uses the packaged executable with Qt's offscreen platform; PDFs were independently rendered. Opening an external system PDF viewer was not exercised.
