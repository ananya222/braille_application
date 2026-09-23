# CPU optimization baseline

This is a second-pass CPU profile of the post-large-document-optimization application. It makes no production changes. The profiled fixture is the deterministic 100-source-page repeated real-document pair.

Logical CPU count: 16. CPU percentages are process CPU normalized across all logical cores; peak is the highest 250 ms sample. cProfile timings include profiler overhead and are used for attribution, not headline wall-clock claims.

## Stage measurements

| Stage | Wall time | Process CPU | Avg CPU | Peak CPU | Peak RAM |
|---|---:|---:|---:|---:|---:|
| master_extraction | 19.333s | 19.312s | 6.2% | 6.6% | 54.1 MiB |
| braille_pdf_extraction | 21.663s | 21.594s | 6.2% | 6.5% | 111.8 MiB |
| expected_generation_and_rules | 4.731s | 4.719s | 6.2% | 6.6% | 116.6 MiB |
| comparison_alignment | 2.385s | 2.391s | 6.2% | 6.3% | 139.0 MiB |
| finding_generation | 0.007s | 0.016s | 0.0% | 0.0% | 139.0 MiB |
| provenance_mapping | 0.305s | 0.312s | 6.4% | 6.4% | 139.0 MiB |
| annotated_pdf_generation | 0.296s | 0.266s | 5.6% | 5.6% | 139.0 MiB |

## Liblouis translation attribution

- prose calls: 6140
- math calls: 0
- prose process CPU: 0.609s
- math process CPU: 0.000s

## Profiling evidence

Per-stage cProfile top-30 reports are in `reports/cpu_optimization_profile_work/`. These are the evidence source for any follow-up optimization; no optimization is justified by a function name alone without a correctness rerun.

The previous pass already added exact/nonblank-equivalent alignment fast paths and per-page PDF cache release. This baseline is intended to identify remaining CPU work after those changes.
