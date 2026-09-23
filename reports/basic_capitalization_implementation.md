# Basic capitalization acceptance

Rule UEB_8 is reused, not duplicated. Authority: UEB 2024 8.1.1, 8.2.1,
8.3.1-3, printed 89-90 / PDF 117-118. Contraction-prefix behavior is included.

## Initial audit

Historical Note generated the correct dot-6 prefixes. A wrong prefix gave
UEB_RULE_001 and an exact cell range; a missing prefix gave an empty range;
an unnecessary prefix was suppressed as an unmapped insertion. These were
production API observations, not inferred from the catalogue.

## Implemented

CapitalSite preserves source word, source character start, expected cell start,
uppercase flag, following letter/contraction cell and UEB ownership. Applicable
context excludes numeric, grade-1, passage-capital and script modes. The source
case determines whether dot 6 is required; the translation map only locates it.

Missing indicator localization uses the following equal aligned actual cell,
verified against the mapped letter/contraction. No general alignment semantics
or PDF mapping were changed. The JSON explanation explicitly labels the box as
an insertion-point anchor. Wrong and extra indicators use their own actual cell.
Only these proved capitalization insertions bypass the old insertion filter.

Scope is word-initial titlecase/lowercase in plain regular prose, and isolated
A/I/O. Mixed blocks support their initial UEB prefix only. All-capital, internal
capital and other standalone capital-letter cases receive a capitalization REVIEW
when recognized by this restricted reader. Unsupported punctuation/typeform/source
mapping contexts are not promoted by the checker. Post-math capitals and arbitrary
document formatting are not claimed. No capitalization generator was changed.

## Tests

- 3 literal official examples from UEB 8.3 passed.
- 7 source contexts, including Historical Note and unseen sentence positions.
- 33 independent wrong/missing/extra prefix mutations: one correctly attributed
  and localized error each.
- 4 broader-capital source exclusions and 3 active-mode exclusions passed.
- PDF clean: 99/99 cells, 0 errors, 0 REVIEW.
- PDF corrupt: 3 errors; ranges [0,1), [16,17), [27,28) on page 1.
- 3 blue boxes visually checked; unmatched provenance/offsets 0.
- Annotated PDF preserves the original extracted Braille stream.
- Simple math: 19 oracle cases, exclusions, per-cell mutations and 6-error PDF
  acceptance unchanged. Square roots remain outside supported scope.
- Focused tab, prose-context, boundary-spacing, boundary-verifier and letter/group
  regression suites passed.

## Chapter 1 regression

Generation is unchanged: 34,448 expected / 33,175 matching; 780 raw differences;
96.3046% canonical agreement; 0 confirmed clean errors. REVIEW increases from 279
to 308 due to 29 recognized capitalization scope exclusions. Exclusions remain 4.
Switches 358 each way; missing inner blanks 0. Existing older corrupted fixture
still reports 5 confirmed errors, unchanged from the simple-math pass.

## Files

- src/braille_app/rules/basic_capitalization.py: source sites and local verifier.
- src/braille_app/rules/catalog.py: expand existing UEB_8 metadata.
- src/braille_app/rules/rule_engine.py: dispatch UEB_8 and preserve source sites.
- src/braille_app/translation/expected_document.py: metadata field only.
- src/braille_app/validation/api.py: capital-specific errors and missing anchor.
- tests/test_basic_capitalization.py: standards, synthetic and exception tests.
- scripts/capitalization_acceptance.py: reproducible PDF fixture and acceptance.
- scripts/capitalization_scope_pdf.py: public combined-scope handoff.

GUI and packaged EXE were not modified or rebuilt. This is source-backend
acceptance, not a new frozen-app or interactive-GUI acceptance claim.

BASIC CAPITALIZATION VALIDATION READY within the explicitly documented source scope.
