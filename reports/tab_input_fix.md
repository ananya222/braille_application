# DOCX tab crash fix

Liblouis preserves some source tabs in its output. The strict Unicode-cell
converter then rejected U+0009 while verifying the generated document.

`translation/liblouis_translator.py` now converts output tabs to one logical
blank in the literary, position-aware literary and ASCII math adapters. This
is horizontal-separator normalization, not physical tab-stop expansion. Source
text is unchanged; output length and source-position maps remain unchanged.
Unknown non-Braille symbols still fail strict cell conversion.

Tests:

- Three new `tests/test_translation_tabs.py` groups pass.
- Original `chap1ncert_english.docx` completes without the tab exception.
- Prepared master plus clean BRF: ERROR 0, REVIEW 182, exclusions 4; raw 771.
- Prepared master plus corrupted dots PDF: ERROR 6, REVIEW 182, exclusions 4;
  raw 777. Qt worker and automatic annotated PDF export pass.
- Existing prose-context 7/7, boundary verifier 5/5 with 8/8 corruptions,
  spacing and letter/grouping canaries pass.
- A new Windows build succeeds in `dist/tabfix_stage/BrailleValidator`.

The alternate DOCX is not the prepared demo master: its current import yields
one source page versus 17 Braille pages. Its 31 reported differences are not a
valid six-error demo result. This fix does not add source page reconstruction,
math annotation or standards coverage. Use the matching prepared DOCX for the
controlled demo.

After the user closed the previous application, the rebuilt release was moved
to `dist/BrailleValidator`. The old release is retained intact in
`dist/BrailleValidator_before_tab_fix`. The compiled adapter in the new EXE
was extracted read-only and its tab-normalization helper passed its cell test.
