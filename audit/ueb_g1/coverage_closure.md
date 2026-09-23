# UEB Grade 1 coverage closure

Authority: ICEB, *Rules of Unified English Braille, Third Edition 2024*, using the local PDF recorded in `environment.md`. Liblouis remains an implementation candidate only.

This closure was generated from the 77 `REQUIRED` rows in `standard_scope.csv` after executing the audit corpus through the vendored `unicode.dis,en-ueb-g1.ctb`. A coverage result means that evidence was run; it does not mean the output passed the standard.

`negative_or_mutation_case` means a focused boundary, near-neighbor, or observed-difference probe. `interaction_or_boundary_case` is deliberately narrower and is marked only where the test ID exercises a context-sensitive boundary. Policy-only rules are not promoted to COVERED merely because a related output exists.

## Coverage matrix

| Citation | Rule family | Executed test | Test IDs | Evidence tier | Positive | Negative/mutation | Interaction/boundary | Coverage | Notes |
|---|---|---|---|---|---|---|---|---|---|
| 2.3.1 | Follow print | YES | `word_braille_validator; punct_basic; cap_punctuation` | DERIVED | YES | YES | YES | PARTIAL | related rule-family evidence only; no test citation names this subrule |
| 2.4.1 | Indicators and modes | YES | `cap_isolated; grade1_numeric_hyphen_cap; typeform_number_symbol` | OFFICIAL | YES | YES | YES | PARTIAL | related rule-family evidence only; no test citation names this subrule; executed evidence includes an unresolved difference or source-policy case |
| 2.4.2 | Indicators and modes | YES | `num_zero; punct_basic; quote_curly_double` | OFFICIAL; DERIVED | YES | NO | NO | PARTIAL | related rule-family evidence only; no test citation names this subrule |
| 2.4.3 | Indicators and modes | YES | `num_zero; cap_all_word; typeform_passage` | OFFICIAL; DERIVED | YES | NO | NO | PARTIAL | related rule-family evidence only; no test citation names this subrule |
| 2.4.4 | Indicators and modes | YES | `grade1_plain_no_indicator; grade1_numeric_letters; cap_all_word` | OFFICIAL; DERIVED | YES | NO | NO | PARTIAL | related rule-family evidence only; no test citation names this subrule |
| 2.4.5 | Indicators and modes | YES | `typeform_number_symbol; cap_all_word` | OFFICIAL; DERIVED | YES | NO | NO | PARTIAL | related rule-family evidence only; no test citation names this subrule |
| 2.5.1 | Contractions disallowed in Grade 1 mode | YES | `word_ordinary; grade1_plain_no_indicator` | DERIVED; OFFICIAL | YES | NO | NO | PARTIAL | related rule-family evidence only; no test citation names this subrule |
| 2.5.2 | Uncontracted differs from Grade 1 mode | YES | `word_ordinary; grade1_plain_no_indicator` | DERIVED; OFFICIAL | YES | NO | NO | PARTIAL | related rule-family evidence only; no test citation names this subrule |
| 2.5.3 | Uncontracted differs from Grade 1 mode | YES | `num_zero; grade1_numeric_letters` | OFFICIAL | YES | NO | NO | PARTIAL | related rule-family evidence only; no test citation names this subrule |
| 2.5.4 | Uncontracted differs from Grade 1 mode | YES | `word_ordinary` | DERIVED | YES | NO | NO | PARTIAL | related rule-family evidence only; no test citation names this subrule |
| 2.5.5 | Uncontracted differs from Grade 1 mode | YES | `word_hello; word_braille_validator; word_ordinary; grade1_plain_no_indicator` | DERIVED; OFFICIAL | YES | NO | NO | COVERED |  |
| 2.6.1 | Standing alone | YES | `cap_word; grade1_plain_no_indicator` | DERIVED; OFFICIAL | YES | NO | NO | PARTIAL | related rule-family evidence only; no test citation names this subrule |
| 2.6.2 | Standing alone | YES | `quote_standing_alone_double; brackets_round; quote_ascii_single_pair` | DERIVED | YES | YES | YES | PARTIAL | executed evidence includes an unresolved difference or source-policy case |
| 2.6.3 | Standing alone | YES | `quote_standing_alone_double; punct_abbreviation_period; quote_nested; apostrophe_possessive_ascii` | DERIVED; OFFICIAL | YES | YES | YES | PARTIAL | executed evidence includes an unresolved difference or source-policy case |
| 2.6.4 | Standing alone | YES | `apostrophe_mid_ascii; apostrophe_possessive_ascii` | OFFICIAL | YES | NO | NO | PARTIAL | related rule-family evidence only; no test citation names this subrule |
| 2.6.5 | Standing alone | YES | `punct_question_standing_alone; quote_standing_alone_double` | OFFICIAL; DERIVED | YES | YES | YES | PARTIAL | related rule-family evidence only; no test citation names this subrule; executed evidence includes an unresolved difference or source-policy case |
| 3.1 | Ampersand | YES | `symbols_amp_at` | OFFICIAL | YES | NO | NO | COVERED |  |
| 3.5 | Bullet | YES | `symbols_bullet` | OFFICIAL | YES | NO | NO | COVERED |  |
| 3.7 | At, copyright, registered, trademark | YES | `symbols_amp_at` | OFFICIAL | YES | NO | NO | COVERED |  |
| 3.8 | At, copyright, registered, trademark | YES | `symbols_copyright_trademark` | OFFICIAL | YES | NO | NO | COVERED |  |
| 3.10 | Currency signs | YES | `num_currency; symbols_currency; symbols_currency_amount` | OFFICIAL; DERIVED | YES | NO | NO | COVERED |  |
| 3.11 | Degree and prime | YES | `symbols_degree_section; symbols_degree_prime` | OFFICIAL | YES | NO | NO | COVERED |  |
| 3.19 | Number, paragraph/section, percent | YES | `symbols_percent_hash; symbols_number_sign` | OFFICIAL | YES | NO | NO | COVERED |  |
| 3.20 | Number, paragraph/section, percent | YES | `symbols_degree_section` | OFFICIAL | YES | NO | NO | COVERED |  |
| 3.21 | Number, paragraph/section, percent | YES | `symbols_percent_hash` | OFFICIAL | YES | NO | NO | COVERED |  |
| 3.23 | Space | YES | `num_thousands_space; spacing_normal; spacing_multiple; spacing_nbsp; spacing_thin_zero_width` | DERIVED; OFFICIAL; CONSTRUCTED | YES | YES | YES | PARTIAL | executed evidence includes an unresolved difference or source-policy case |
| 4.1 | English alphabet | YES | `alphabet_lower_a; alphabet_lower_b; alphabet_lower_c; alphabet_lower_d; alphabet_lower_e; alphabet_lower_f; alphabet_lower_g; alphabet_lower_h; alphabet_lower_i; alphabet_lower_j; alphabet_lower_k; alphabet_lower_l; alphabet_lower_m; alphabet_lower_n; alphabet_lower_o; alphabet_lower_p; alphabet_lower_q; alphabet_lower_r; alphabet_lower_s; alphabet_lower_t; alphabet_lower_u; alphabet_lower_v; alphabet_lower_w; alphabet_lower_x; alphabet_lower_y; alphabet_lower_z; alphabet_upper_a; alphabet_upper_b; alphabet_upper_c; alphabet_upper_d; alphabet_upper_e; alphabet_upper_f; alphabet_upper_g; alphabet_upper_h; alphabet_upper_i; alphabet_upper_j; alphabet_upper_k; alphabet_upper_l; alphabet_upper_m; alphabet_upper_n; alphabet_upper_o; alphabet_upper_p; alphabet_upper_q; alphabet_upper_r; alphabet_upper_s; alphabet_upper_t; alphabet_upper_u; alphabet_upper_v; alphabet_upper_w; alphabet_upper_x; alphabet_upper_y; alphabet_upper_z; word_hello; word_braille_validator; word_ordinary` | OFFICIAL; DERIVED | YES | NO | NO | COVERED |  |
| 5.1 | Grade 1 symbol mode | YES | `punct_question_standing_alone` | OFFICIAL | YES | YES | YES | PARTIAL | related rule-family evidence only; no test citation names this subrule |
| 5.2 | Grade 1 symbol mode | YES | `punct_question_standing_alone; grade1_numeric_letters` | OFFICIAL | YES | YES | YES | PARTIAL | related rule-family evidence only; no test citation names this subrule |
| 5.3 | Grade 1 word/passage/terminator | NO | `` |  | NO | NO | NO | UNTESTED | requires explicit indicator/translator-option evidence not generated by plain-text en-ueb-g1 |
| 5.4 | Grade 1 word/passage/terminator | NO | `` |  | NO | NO | NO | UNTESTED | requires explicit indicator/translator-option evidence not generated by plain-text en-ueb-g1 |
| 5.5 | Grade 1 word/passage/terminator | NO | `` |  | NO | NO | NO | UNTESTED | requires explicit indicator/translator-option evidence not generated by plain-text en-ueb-g1 |
| 5.6 | Numeric indicator sets Grade 1 mode | YES | `grade1_numeric_letters; grade1_numeric_capital; grade1_numeric_hyphen_cap; num_zero` | OFFICIAL | YES | YES | YES | PARTIAL | executed evidence includes an unresolved difference or source-policy case |
| 5.7 | Grade 1 and capitalization | YES | `grade1_numeric_hyphen_cap` | OFFICIAL | YES | YES | YES | PARTIAL | related rule-family evidence only; no test citation names this subrule; executed evidence includes an unresolved difference or source-policy case |
| 5.8 | Grade 1 and capitalization | YES | `grade1_indicator_order` | DERIVED | YES | YES | NO | PARTIAL | executed evidence includes an unresolved difference or source-policy case |
| 5.10 | Optional Grade 1 indicator | YES | `grade1_plain_no_indicator` | OFFICIAL | YES | NO | NO | PARTIAL | related rule-family evidence only; no test citation names this subrule |
| 5.11 | Grade 1 text indicator policy | YES | `punct_comma_between_letters; grade1_plain_no_indicator; punct_question_standing_alone; num_lower_a_j` | DERIVED; OFFICIAL | YES | YES | YES | COVERED |  |
| 6.1 | Digits and numeric-mode symbols | YES | `num_zero; num_multi` | OFFICIAL | YES | NO | NO | COVERED |  |
| 6.2 | Digits and numeric-mode symbols | YES | `num_decimal; num_thousands_comma` | OFFICIAL | YES | NO | NO | COVERED |  |
| 6.3 | Numeric termination and letter interactions | YES | `cap_number_then_capital; num_time; num_decimal_lower` | DERIVED; OFFICIAL | YES | NO | NO | COVERED |  |
| 6.4 | Numeric termination and letter interactions | YES | `num_period_before_number` | OFFICIAL | YES | NO | NO | COVERED |  |
| 6.5 | Numeric termination and letter interactions | YES | `cap_number_then_word; num_lower_a_j; num_lower_k_z; num_decimal_lower; grade1_numeric_letters; grade1_numeric_capital; grade1_numeric_hyphen_cap; num_ordinal` | DERIVED; OFFICIAL | YES | YES | YES | PARTIAL | executed evidence includes an unresolved difference or source-policy case |
| 6.6 | Numeric spaces | YES | `num_thousands_space; num_clear_numeric_space; num_thousands_nbsp` | DERIVED; OFFICIAL | YES | YES | YES | PARTIAL | executed evidence includes an unresolved difference or source-policy case |
| 6.7 | Dates, time, coinage, ordinals | YES | `num_time; num_date; num_currency; symbols_currency_amount; num_ordinal` | OFFICIAL; DERIVED | YES | NO | NO | COVERED |  |
| 7.1 | General punctuation | YES | `punct_basic; punct_sentence; punct_abbreviation_period; punct_comma_between_letters; brackets_round; brackets_square; brackets_curly` | DERIVED | YES | YES | YES | COVERED |  |
| 7.2 | Hyphen, dash, long dash | YES | `dash_hyphenated; dash_en; dash_em; dash_print_double_hyphen` | DERIVED; OFFICIAL | YES | YES | YES | COVERED |  |
| 7.3 | Ellipsis, solidus, question mark | YES | `punct_ellipsis` | OFFICIAL | YES | NO | NO | COVERED |  |
| 7.4 | Ellipsis, solidus, question mark | YES | `punct_solidus` | OFFICIAL | YES | NO | NO | COVERED |  |
| 7.5 | Ellipsis, solidus, question mark | YES | `punct_question_standing_alone; punct_question_ordinary` | OFFICIAL | YES | YES | YES | COVERED |  |
| 7.6.1 | Quotation marks and apostrophe basics | YES | `quote_curly_double; quote_ascii_double; quote_next_punctuation` | OFFICIAL; DERIVED | YES | NO | NO | COVERED |  |
| 7.6.2 | Quotation marks and apostrophe basics | YES | `quote_curly_single; quote_ascii_single_pair` | OFFICIAL; DERIVED | YES | YES | YES | PARTIAL | executed evidence includes an unresolved difference or source-policy case |
| 7.6.3 | Quotation marks and apostrophe basics | YES | `quote_nested` | OFFICIAL | YES | YES | YES | PARTIAL | executed evidence includes an unresolved difference or source-policy case |
| 7.6.4 | Quotation marks and apostrophe basics | NO | `` |  | NO | NO | NO | UNTESTED | requires explicit indicator/translator-option evidence not generated by plain-text en-ueb-g1 |
| 7.6.5 | Quotation marks and apostrophe basics | YES | `quote_ascii_double` | DERIVED | YES | NO | NO | COVERED |  |
| 7.6.6 | Quotation marks and apostrophe basics | YES | `apostrophe_mid_ascii; apostrophe_possessive_ascii; apostrophe_mid_curly; apostrophe_possessive_curly` | OFFICIAL | YES | NO | NO | COVERED |  |
| 7.6.7 | Quote/apostrophe ambiguity avoidance | YES | `quote_internal_two_cell` | OFFICIAL | YES | YES | YES | PARTIAL | executed evidence includes an unresolved difference or source-policy case |
| 7.6.8 | Quote/apostrophe ambiguity avoidance | YES | `quote_standing_alone_double` | DERIVED | YES | YES | YES | PARTIAL | executed evidence includes an unresolved difference or source-policy case |
| 7.6.9 | Quote/apostrophe ambiguity avoidance | YES | `quote_g1_order` | DERIVED | YES | YES | YES | PARTIAL | executed evidence includes an unresolved difference or source-policy case |
| 7.6.10 | Quote/apostrophe ambiguity avoidance | YES | `quote_standing_alone_single` | DERIVED | YES | YES | YES | PARTIAL | executed evidence includes an unresolved difference or source-policy case |
| 7.6.12 | Translation-software quote/apostrophe guidance | NO | `` |  | NO | NO | NO | UNTESTED | requires explicit indicator/translator-option evidence not generated by plain-text en-ueb-g1 |
| 7.6.13 | Translation-software quote/apostrophe guidance | YES | `quote_ascii_single_pair; quote_nested` | DERIVED; OFFICIAL | YES | YES | YES | PARTIAL | related rule-family evidence only; no test citation names this subrule; executed evidence includes an unresolved difference or source-policy case |
| 7.6.14 | Translation-software quote/apostrophe guidance | YES | `apostrophe_leading_tis` | DERIVED | YES | NO | NO | PARTIAL | related rule-family evidence only; no test citation names this subrule |
| 7.6.15 | Translation-software quote/apostrophe guidance | YES | `quote_ascii_single_pair; apostrophe_mid_ascii; apostrophe_mid_curly; apostrophe_leading_tis` | DERIVED; OFFICIAL | YES | YES | YES | PARTIAL | executed evidence includes an unresolved difference or source-policy case |
| 8.1 | Capital letters and isolated capitals | YES | `cap_word; cap_isolated` | DERIVED; OFFICIAL | YES | NO | NO | COVERED |  |
| 8.2 | Capital letters and isolated capitals | YES | `cap_word; cap_multiple_words` | DERIVED | YES | NO | NO | PARTIAL | related rule-family evidence only; no test citation names this subrule |
| 8.3 | Capital letters and isolated capitals | YES | `cap_isolated; cap_word; cap_number_then_capital; alphabet_upper_a` | OFFICIAL; DERIVED | YES | NO | NO | COVERED |  |
| 8.4 | Capitalised word mode | YES | `cap_all_word; cap_multiple_words; cap_number_then_word; cap_punctuation` | DERIVED | YES | YES | YES | COVERED |  |
| 8.5 | Capitalised passage and terminator | YES | `cap_passage` | OFFICIAL | YES | NO | NO | PARTIAL | related rule-family evidence only; no test citation names this subrule |
| 8.6 | Capitalised passage and terminator | YES | `cap_passage` | OFFICIAL | YES | NO | NO | PARTIAL | related rule-family evidence only; no test citation names this subrule |
| 8.7 | Indicator placement and choice | YES | `cap_punctuation; cap_number_then_capital` | DERIVED | YES | YES | YES | COVERED |  |
| 8.8 | Indicator placement and choice | YES | `cap_all_word; cap_word` | DERIVED | YES | NO | NO | COVERED |  |
| 9.1 | Italic, bold, underline typeforms | YES | `typeform_italic; typeform_bold; typeform_underline` | DERIVED | YES | NO | NO | PARTIAL | related rule-family evidence only; no test citation names this subrule |
| 9.2 | Italic, bold, underline typeforms | YES | `typeform_number_symbol; typeform_italic` | OFFICIAL; DERIVED | YES | NO | NO | COVERED |  |
| 9.3 | Italic, bold, underline typeforms | YES | `typeform_number` | DERIVED | YES | NO | NO | COVERED |  |
| 9.4 | Italic, bold, underline typeforms | YES | `typeform_passage` | DERIVED | YES | NO | NO | COVERED |  |
| 9.7 | Typeform placement and multiple indicators | YES | `typeform_word_punctuation` | DERIVED | YES | NO | NO | COVERED |  |
| 9.8 | Typeform placement and multiple indicators | YES | `typeform_multiple` | DERIVED | YES | NO | NO | COVERED |  |

## Required rows with no direct executed evidence

- `2.3.1` — Follow print
- `2.4.1` — Indicators and modes
- `2.4.2` — Indicators and modes
- `2.4.3` — Indicators and modes
- `2.4.4` — Indicators and modes
- `2.4.5` — Indicators and modes
- `2.5.1` — Contractions disallowed in Grade 1 mode
- `2.5.2` — Uncontracted differs from Grade 1 mode
- `2.5.3` — Uncontracted differs from Grade 1 mode
- `2.5.4` — Uncontracted differs from Grade 1 mode
- `2.6.1` — Standing alone
- `2.6.4` — Standing alone
- `2.6.5` — Standing alone
- `5.1` — Grade 1 symbol mode
- `5.2` — Grade 1 symbol mode
- `5.3` — Grade 1 word/passage/terminator
- `5.4` — Grade 1 word/passage/terminator
- `5.5` — Grade 1 word/passage/terminator
- `5.7` — Grade 1 and capitalization
- `5.10` — Optional Grade 1 indicator
- `7.6.4` — Quotation marks and apostrophe basics
- `7.6.12` — Translation-software quote/apostrophe guidance
- `7.6.13` — Translation-software quote/apostrophe guidance
- `7.6.14` — Translation-software quote/apostrophe guidance
- `8.2` — Capital letters and isolated capitals
- `8.5` — Capitalised passage and terminator
- `8.6` — Capitalised passage and terminator
- `9.1` — Italic, bold, underline typeforms

These are not silently counted as compliant. The main irreducible gaps are Grade 1 word/passage/terminator controls (5.3–5.5), print-quote assignment options (7.6.4 and 7.6.12), and any rule whose direct meaning depends on document structure rather than plain source text.

## Exact 2024 rule-text verification of the confirmed differences

### ASCII single quotation pair

Section 7.6.2 states: `Use single quotation marks ⠠⠦ and ⠠⠴ for single quotation marks in the print text.` Section 7.6.15 then permits the translation-software distinction to be made by context: a mark at the beginning of a word is an opening single quote, and `in all other contexts, treat the mark as a closing single quote`. For ASCII `'hello'`, the executed Liblouis result is apostrophe dot 3 on both sides; the derived 2024 contextual result is opening `⠠⠦` and closing `⠠⠴`. This is a confirmed implementation difference, but 7.6.13 expressly recognizes that ASCII print may be ambiguous, so it is not by itself proof of a mandatory Liblouis standards violation; our validator needs a documented contextual policy.

### Nested quotation closing context

Section 7.6.3 states: `Follow print for outer and inner quotation marks.` Its official example is `She said, “Read ‘Peter Rabbit’ again.”`, where the inner single quotation closes with the dot-6 two-cell single quote. The executed `quote_nested` case gives the inner opening quote correctly but translates the inner closing quote as apostrophe dot 3. That is a direct mismatch with the 2024 outer/inner quotation rule, independent of contracted-word differences.

### Grade 1/capital ordering in `3-D`

Section 6.5.4 states: `Grade 1 mode is terminated by a hyphen or dash ... Therefore, a letter or letters that could read as a contraction will need the grade 1 indicator.` The official example is `3-D   ⠼⠉⠤⠰⠠⠙`. Section 5.8.1 states: `A grade 1 indicator precedes a capitalisation indicator.` Liblouis emits `⠼⠉⠤⠠⠙`, omitting `⠰`; both `grade1_numeric_hyphen_cap` and `grade1_indicator_order` therefore fail the exact 2024 requirement.

## Evidence closure decisions

- ASCII single-quote pairs, nested single-quote closing context, internal double quotes, and standing-alone double quotes are confirmed contextual quote failures against the 2024 rules. The rulebook itself says quote/apostrophe distinction cannot be wholly automated without professional intervention (7.6.13).
- `a.b` and `a,b` are resolved as PASS: the period is not a beginning-of-word lower-groupsign position, while comma in `a,b` requires the Grade 1 symbol indicator because it can be read as the lower groupsign `be` between letters.
- Clear grouped numeric spaces are semantic: Section 6.6 says numeric-space signs mean `space and following digit` within a number and that an unclear separator is treated as an ordinary space; 6.6.1 says spaces within one number use those ten symbols. Plain text alone cannot establish grouping intent; the failed `num_clear_numeric_space` probe is therefore a wrapper/input-semantics gap, not proof that ordinary spaces are wrong. Under the recorded V1 policy, untagged `1 234` is treated as ordinary spacing and is PASS-PROVISIONAL.
- Repeated ordinary spaces, NBSP outside numbers, and thin/zero-width spaces are separated from UEB compliance by a recorded source-normalization policy. Section 3.23.1 says `The amount of space present is not considered important`; the V1 layer collapses repeated ordinary spaces, maps NBSP/thin space to ordinary spacing outside numeric contexts, and removes U+200B extraction separators. Raw NBSP remains a normalization-layer FAIL; the thin/zero-width probe is PASS-PROVISIONAL after that policy.
- Typeform + number is resolved for the exercised symbol, word, passage, punctuation, and multiple-typeform cases. Rule 9.3.1 permits a word typeform over a numeric symbols-sequence; Liblouis matched the derived result. No typeform bug is evidenced here.

## Remaining corpus expansion boundary

The corpus was expanded only for representable closure gaps: prime signs (`3.11`) and the quote boundary rules (`7.6.9` and `7.6.10`). No synthetic expected form was used to claim that translation-software options or explicit Grade 1 passages are implemented by the forward generator.

## Final closure

- REQUIRED rows total: **77**
- Fully covered: **35**
- Partially covered: **37**
- Untested: **5**
- Executed corpus outcomes: PASS **121**; PASS-VARIANT **0**; PASS-PROVISIONAL **2**; FAIL **11**; UNCERTAIN **0**; UNSUPPORTED **0**; N/A-GRADE **3**.
- Confirmed Liblouis gaps: ASCII single-quote direction in prose context; nested single-quote closing context; two-cell internal and standing-alone double-quote selection; Grade 1 plus capital ordering after numeric-mode termination in `3-D`.
- Confirmed wrapper/normalization gaps: semantic numeric grouping for numeric spaces, repeated-space collapsing, and NBSP normalization outside numeric contexts.
- Unresolved standards questions: when ambiguous ASCII quote marks are assigned direction without transcriber context; explicit Grade 1 word/passage/terminator acceptance in a validator; and whether the product will expose 7.6.4/7.6.12 quote-assignment options. Whitespace handling is now a recorded source-normalization policy, not an unresolved UEB rule question.
- Exact minimal overrides we need to implement: (1) quote/apostrophe context and ambiguity handling with a small apostrophe dictionary and fail-closed path; (2) semantic numeric grouping that emits/accepts numeric-space cells and validates numeric-mode termination; (3) inject/accept Grade 1 before capital indicators after numeric hyphen/dash termination; (4) normalize or reject non-ordinary whitespace before Liblouis; (5) model only cited Grade 1/capital/typeform variants. No production code was changed by this audit.
