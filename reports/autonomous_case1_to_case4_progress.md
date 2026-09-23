# Autonomous Case 1–4 progress — 2026-09-23

**Latest status (2026-09-23): CASE 3 — NUMBERS: PASS. CASE 4 — CORE PUNCTUATION: PASS. CASE 1–4 INDIVIDUAL FAMILY GATES: GREEN.** The final 2,000-action integration fixture has not been started. Historical entries below are chronological; later closure sections supersede earlier status snapshots. The Case 1+2 alignment/provenance/highlighting core remains frozen.

This durable record began with Case 1+2 closure and now includes the subsequent Case 3 and Case 4 work.

## Frozen diverse fixture

The accepted 1,000-mutation distribution was not regenerated or edited. SHA-256:

| File | Hash |
| --- | --- |
| `source/final_case1_case2_clean_50page.docx` | `8c53cec65b6dfbc21c072db1ceaa448db887974dbc386379ae4c66941c4b72f2` |
| `source/final_case1_case2_clean_50page.dxb` | `46a48b68a45f89c05cb2761d0c278ce42bf3ef8a029b5262e387e438f90ccad3` |
| `source/final_case1_case2_clean_50page.pdf` | `6cc4aa95843bd7ae29ffb110d14a26b3224b7d4214651a951a5fd44cc593e852` |
| `source/final_case1_case2_clean_50page (2).brf` | `48b0c2d3145dfab4d497a5b0b98c5b8633fd84369d5c78a250cf4109b9da2389` |
| `manifests/source_coverage_manifest.csv` | `d11c4d91f6cd2d1734a1deaa341f27f09e85e759d83312e8df1c3b1d11dd709d` |
| `manifests/diverse_mutation_manifest.csv` | `0517fb314d818500983e4f5ee9937b458e019565d0d7c54b79512159d333aab4` |
| `corrupted_diverse_final/final_case1_case2_diverse_1000.pdf` | `4492fdce40202a1ab84fce9149c20142daed2dafee2d3b108c58fea9fa1f209b` |
| `corrupted_diverse_final/final_case1_case2_diverse_1000.brf` | `c40c1a25e5fdb949853bfdd89b212b6cc93d3cc63b1e0eaa7dfe6e63319c61f7` |

The PDF cell stream had already been independently verified against the manifest, including the expected net −50 cells. No alternative distribution is a valid gate.

## Count-deficit accounting before the fix

The baseline had 1,000 injected mutations, 995 raw alignment differences, 838 reported findings, 0 reviews, and 157 ignored empty-expected insertions. Every ignored insertion was in a block whose rule list was `UEB_8, UEB_CASE2_SCOPE`; the first rule alone had controlled the insertion check. Five of those 157 were the clean Duxbury `^2` control pair (masks 24, 6), recurring at the start of pages 10, 20, 30, 40, and 50.

| Mutually exclusive source of the 162-finding count deficit | Count |
| --- | ---: |
| Mutation-induced raw differences suppressed by capitalization-rule ownership | 152 |
| Remaining net gap between 1,000 injected mutations and 990 mutation-induced raw differences; exact event-level cause not yet established | 10 |
| **Total count deficit** | **162** |

This is **count accounting**, not a claim that 838 findings matched 838 distinct mutations. Some raw opcodes represent shifted or merged regions. In the baseline, only 305 of 1,162 target cell slots were boxed, while 662 boxes were off target. The ten residual events must remain unknown at the event level until alignment and provenance are matched to manifest IDs. The same alignment/localization defect can also affect findings already counted among the 838.

Representative evidence: a single inserted `z` in source `Hello` produced one raw insertion and zero errors before the fix. A larger insertion opcode in repeated `Hello` text spanned 20 actual cells; that cannot be certified as one correctly localized injected insertion. These share the same coarse block alignment and rule ownership paths, but only the first is proven to be solely an ownership suppression.

## Scoped production correction

`src/braille_app/validation/api.py` now recognizes a passing `UEB_CASE1_SCOPE` or `UEB_CASE2_SCOPE` rule anywhere in a block's rule list when deciding whether an unexpected insertion is in supported uncontracted scope. It continues to exclude known Duxbury control pairs; the real clean document established `^2` (24, 6) as one such pair. No alignment algorithm, source extraction, fixture, or old validator path changed.

Focused tests in `tests/test_uncontracted_case2_capitalization.py` cover both the formerly suppressed extra letter in `Hello` and clean `^2` control handling.

## Exact before/after on the same diverse PDF

| Metric | Before | After |
| --- | ---: | ---: |
| Injected | 1,000 | 1,000 |
| Reported findings | 838 | 990 |
| Count deficit | 162 | 10 |
| Reviews | 0 | 0 |
| Duplicate issue IDs | 0 | 0 |
| Raw alignment differences | 995 | 995 |
| Ignored unmapped insertions | 157 | 0 |
| Matching cells | 8,025/10,591 | 8,025/10,591 |
| Entire source passages exactly aligned | 14/275 | 14/275 |
| Target cell slots boxed | 305/1,162 | 396/1,162 |
| Off-target blue boxes | 662 | 773 |
| Duplicate blue boxes | 0 | 0 |

After the fix, 345/1,000 mutation rows have every target slot boxed; 382 rows have at least one target slot boxed. Finding-count excess over 1,000 is zero, but actual false-positive findings cannot be declared zero without one-to-one mutation matching. The increase in off-target boxes confirms that alignment and localization remain open.

## Regression gates after the correction

| Gate | Result |
| --- | --- |
| Unchanged frozen 1,000-substitution PDF | 1,000/1,000 findings; 1,000/1,000 target boxes; 0 off-target boxes; 0 reviews/duplicates |
| Clean real Duxbury 50-page PDF | 0 errors; 0 reviews |
| Case 1 existing 500-error PDF | 500/500 detected and exactly localized; 0 false positives; clean 0 |
| Case 2 focused tests and 21 translator probes | PASS |
| Repeated-region tests | PASS |
| Old packaged validator | 185/185 detected and exact; clean 0 |
| Continuous/cross-page/repeated-operand/spacing acceptance | PASS (467/467 cross-page, 12/12 repeated operand, 15/15 cross-page PDF, 42/42 spacing) |

**Status: OPEN.** The exact diverse fixture remains the required gate. Do not call Case 1 + Case 2 combined closed and do not begin Numbers. The next work is event-level alignment/provenance diagnosis on this same frozen fixture, starting with the remaining count gap and the off-target boxes.

## Bounded fine-alignment recovery — still open

### Physical adjudication policy for the frozen diverse gate

Logical errors and physical targets are counted separately. A substitution is one logical mutation and its changed surviving glyph is the physical target. An insertion is one logical mutation and the added glyph is its target. A deletion is one logical mutation with **no** surviving target glyph; the existing Case-1 highlighter convention anchors the gap to the next surviving cell, so the Case-2 path must be checked against that same convention rather than declaring a deleted glyph boxed. At end-of-line/page, an exact following-cell anchor may be unavailable; this requires explicit review, never a guessed previous-page box. An adjacent transposition is one logical mutation with two surviving target cells. The existing renderer groups adjacent provenance cells on the same line into one envelope box: the envelope is correct only when it covers exactly those two cells and no neighbor. Capitalization-indicator insertion, deletion, and replacement follow the same insert/delete/substitute physical policy, with the indicator counted as a cell, not a word. A multi-cell logical replacement may produce one grouped envelope per physical line, but the union of its provenance cells must equal the intended target cells. One logical error need not equal one box.

The independent evaluator will read the frozen manifest and corrupted PDF *outside* production validation. It will map each manifest expected index (and the second expected index for a transposition) to at most one finding's source-page expected span, then verify actual provenance cell identities against the shifted corrupted-PDF character indices. It will check that grouped boxes equal the envelope of precisely those cells. Unmatched findings are false positives, and a finding cannot be consumed by two mutation IDs. No manifest access is permitted in production code.

The 14/275 `source_passages_aligned` statistic means every cell in those passages is equal, not that only 14 passages were assigned to the right region. The manifest mutates 270 of 275 blocks, so this is not a coarse-region diagnostic. A page-1 trace found the first wrong stage inside a correctly assigned source block: `SequenceMatcher` aligned the first alphabet run to the second and produced a spurious 27-cell insertion and 27-cell deletion. Equal-width blocks with paired insertion/deletion instead collapsed the shifted portion into a wide replacement. PDF provenance itself mapped all 9,128 nonblank actual cells to rendered glyph geometry correctly.

For the 887 *physically present* mutation target slots (deletions have no target glyph), the pre-fix stage accounting was mutually exclusive: 460 target span aligned and boxed; 157 local offset drift and missed; 100 aligned target span but missed box; 79 wide aligned span and missed; 54 local drift but boxed; 25 wide span but boxed; 10 inserted targets incorrectly considered equal and missed; 1 wrong source block but boxed; 1 no alignment opcode and missed. Sum: 887. Separately, 122/275 deletion rows were recognized as single-cell deletes but left unboxed by the PDF adapter; other deletion rows were merged into wider edits or lacked an issue. The 100 aligned-but-missed box slots require transposition/envelope adjudication; they are not yet proven provenance failures.

The prior `blue_box_audit` compares against **clean** PDF coordinates. Insertions/deletions shift 5,182 surviving glyphs in the corrupted PDF, so its 396/1162 hit and 773 off-target figures are not a valid physical localization oracle for this fixture. This is an audit-method limitation, not a defect in the frozen fixture. With target coordinates taken from the corrupted PDF, the pre-fix result was 540/887 observable target slots boxed and 629 off-target boxes.

A bounded minimum-edit fine aligner now replaces positional/`SequenceMatcher` alignment only inside the selected uncontracted source block. Focused tests for paired indels, a repeated alphabet run, single insertion/deletion and transposition passed; they failed before the fix where expected. The same frozen diverse PDF was then validated once, without rewriting any fixture file:

| Metric | Before | After |
| --- | ---: | ---: |
| Findings | 990 | 997 |
| Finding-count gap | 10 | 3 |
| Reviews / duplicate issue IDs | 0 / 0 | 0 / 0 |
| Matching cells | 8,025 | 9,649 |
| Entirely equal source passages | 14/275 | 14/275 |
| Old clean-coordinate target audit | 396/1,162 | 455/1,162 |
| Old clean-coordinate off-target boxes | 773 | 333 |
| Corrected corrupted-coordinate observable target hits | 540/887 | 652/887 |
| Corrected corrupted-coordinate off-target boxes | 629 | 136 |
| Blue boxes | 1,169 | 788 |
| Validation runtime | — | 1.58 s |

The 235 remaining observable target-slot misses comprise 213 transposition slots, 20 insertion slots, and 2 substitution slots. A grouped blue-box envelope may cover two adjacent transposition cells without equaling either single-glyph rectangle; this requires per-cell provenance adjudication. Deletions also require a separate exact-anchor oracle. The 997 findings have **not** yet been matched one-to-one to 1,000 mutation IDs; missed mutations and false positives are therefore unknown, not `3` and `0` by assertion. Exact localization and zero off-target boxes are not achieved.

Post-fix smoke: 16 uncontracted unit tests pass; clean real-Duxbury PDF remains 0 findings/0 reviews; frozen substitution PDF remains 1,000 findings/0 reviews/0 duplicate IDs. Exact-box substitution, Case 1, old-validator, and other cross-page regression gates have not yet been rerun after this fine-alignment change. **Status remains OPEN; no Numbers work.**

## Remaining exact-localization audit — 2026-09-23

This section supersedes the earlier 997-finding diagnostic above. The frozen DOCX, BRF, PDF, and manifest hashes in the opening table were checked again and are unchanged. No fixture was regenerated. The independent read-only evaluator is `stress_test/final_case1_case2_alphabet_capitalization/scripts/evaluate_frozen_diverse.py`; run it with the bundled Python. It uses the manifest and clean PDF only as an *audit oracle*. Production validation receives only the frozen source and corrupted PDF.

### Policy and first incorrect stages

- Substitution: one logical mutation, one changed physical glyph. Insertion: one logical mutation, one added physical glyph. A capitalization indicator is a Braille cell under the same rule.
- Adjacent transposition: one logical mutation, two changed physical glyphs. Existing `group_provenance_boxes` may show one envelope when the two glyph boxes touch, or two boxes when they do not. Exactness means the box(es) cover precisely those two provenance cells and no neighbor.
- Deletion: one logical mutation, no changed glyph survives. Use the next surviving semantic cell on the deleted cell's physical line as the gap anchor; at the line end, use the previous surviving semantic cell on that line. Duxbury `^` control pairs and page-number footer cells are not valid anchors. This extends the existing Case-1 next-cell convention only where no next same-line semantic cell exists.
- Multi-cell replacement: one finding may group a continuous *logical* edit, but it cannot be assumed to represent multiple independently injected mutation IDs. The manifest-to-finding audit remains one-to-one.

The 213 apparent transposition target-slot misses in the old per-cell rectangle audit were largely box-envelope semantics. Before the adjacent-swap fix, 151/162 transpositions already had exact two-cell provenance and exact boxes (101 grouped into one envelope, 50 rendered separately); 11 were split by fine alignment, usually an indicator/letter swap adjoining an insertion. After the swap fix, all 162/162 have exact two-cell provenance and exact boxes (111 one-box envelopes, 51 two-box renderings). No transposition provenance or PDF-character mapping defect was found.

The 20 insertion misses were all in runs of identical cells. A deterministic first-equivalent-cell tie break correctly assigns some, but the final corrupted stream cannot identify which of several visually identical cells was the inserted physical instance. Eleven remain mismatched under the strict manifest target. The two substitution target-slot misses were upstream block-selection errors: the coarse `SequenceMatcher` score discarded a semantic continuation line in repeated text. Bounded edit-cost scoring fixes that Case-2 path; all 338 substitutions now match exactly. Case 1 retains its previous block scoring and fine alignment.

Deletion anchoring revealed three separate adapter defects: Case-2 scope findings had no anchor; `UEB_8` capitalization findings were skipped despite carrying Case-2 ownership; and terminal gaps could anchor to Duxbury controls or page footers. Focused tests cover each. The independent oracle uses the deleted glyph's original physical line only in audit, then checks the renderer's surviving-cell anchor. Production does not access that original glyph or the mutation manifest.

### Final diagnostic snapshot — not closure

| Logical mutation/finding metric | Result |
| --- | ---: |
| Injected logical mutations | 1,000 |
| Findings | 995 |
| One-to-one matched **and exactly localized** | 978 |
| Not one-to-one matched under the strict oracle | 22 |
| Unmatched findings (not certified false positives) | 17 |
| Reviews / duplicate issue IDs | 0 / 0 |
| Validation runtime | 8.96 s |

The 978 exact matches comprise 338 substitutions, 214 insertions, 264 deletions, and 162 transpositions. The 22 unmatched manifest IDs are mutually exclusive: 11 identical-run insertions; 5 second cells of adjacent deletion pairs merged with the first into one finding; 5 page-start deletions; and 1 other deletion (`DIV-0280`). The first two categories demonstrate a strict one-to-one/physical-identity limit in the final artifact: identical-cell insertion position is observationally ambiguous, and two adjacent deleted cells have the same final stream whether produced as one two-cell omission or two separate actions. Splitting or assigning them solely to hit manifest IDs would overfit the fixture. The last six deletions remain genuine unresolved diagnostics, not assumed fixed.

| Physical metric, corrupted-PDF coordinates | Result |
| --- | ---: |
| Intended physical target/anchor slots | 1,162 |
| Target slots present in finding provenance | 1,145 |
| Required grouped boxes (counting repeated anchors) | 1,051 |
| Required unique grouped boxes | 1,046 |
| Required box instances present | 1,034 / 1,051 |
| Actual blue boxes | 1,046 |
| Off-target blue boxes | 17 |
| Duplicate blue boxes | 0 |

The original clean-PDF-coordinate audit is not used for this physical result. `source_passages_aligned=14/275` remains an all-cells-equal statistic, not a block-placement metric.

### Changes and active controls

Files changed in this iteration: `src/braille_app/validation/alignment.py`, `src/braille_app/validation/validator.py`, `src/braille_app/validation/pdf_annotation_adapter.py`, `src/braille_app/visual_annotations.py`, `tests/test_uncontracted_alignment_indel_recovery.py`, `tests/test_uncontracted_deletion_anchor.py`, and the independent evaluator above. The visual change is only a `1e-6` overlap tolerance for adjacent PDF boxes whose floating-point edges differ at machine precision.

| Active gate | Latest result |
| --- | --- |
| Focused uncontracted tests | 26/26 pass, including swap contexts, indel recovery, deletion anchors, provenance grouping, and PDF rounding |
| Clean real-Duxbury 50-page PDF | 0 findings, 0 reviews, 0 duplicate IDs |
| Frozen 1,000-substitution PDF | 1,000 findings; 1,000/1,000 exact boxes; 0 off-target/duplicate boxes |
| Case 1 500-error PDF | 500 findings; 500/500 exact boxes; 0 off-target/duplicate boxes |
| Old contracted/Nemeth regression | **Not run**, per current instruction |
| Diverse 1,000-error fixture | **FAIL**, metrics above |

**Case 1 + Case 2 combined closure: FAIL.** No Numbers, Punctuation, or normalization work began. No final closure report was issued. Further production edits should not guess at identical-cell insertion identity or manufacture one issue per manifest row. The remaining six deletion diagnostics require a separate focused trace if work resumes; the strict physical-instance and independent-action requirements need an adjudication policy that acknowledges information absent from the corrupted artifact.

## Equivalence-policy continuation — frozen rerun completed, closure FAIL

The closure criterion now accepts two strictly bounded equivalences without changing production behavior to match mutation IDs:

1. **Identical-cell insertion.** The evaluator may associate one manifest insertion with one otherwise-unmatched insertion finding only when its actual mask agrees, the finding is on the same source/PDF page near the expected position, and its *single* provenance cell and exact box lie inside the contiguous, same-line run of visually identical PDF cells containing the manifest target. The match must be unique. Which indistinguishable instance was newly inserted is not asserted; a neighboring different cell, other line/page, multi-cell finding, or non-exact box is rejected. This changes physical-target adjudication, not validator output.
2. **Adjacent multi-cell deletion.** One zero-width deletion finding may cover multiple manifest IDs only when the finding's entire expected span is completely and contiguously covered by those deletion IDs, at least one ID was already exactly associated with that finding, and its one surviving-cell gap anchor is exact for every covered ID. It is one observable omission with multiple recorded mutation actions. A partial span, extra cell, unrelated source block, or wrong anchor is rejected. No duplicate finding is manufactured.

All other mutations retain strict one-finding/one-target matching. Every finding must be consumed by a strict or equivalence association; every box must lie in the strict target set or an explicitly proved identical-run alternative. `stress_test/final_case1_case2_alphabet_capitalization/scripts/evaluate_frozen_diverse.py` implements this independent audit. The production validator never reads the manifest or clean-PDF oracle.

The six deletion cases were traced separately before the full rerun. Five page-start cases (pages 5, 15, 25, 35, 45) contained three identical capitalization indicators followed by a substituted first letter. The bounded aligner formerly assigned “replace indicator, delete letter”; it now uses a general first-equivalent deletion tie-break and assigns “delete indicator, replace letter” on all five targeted page checks. `DIV-0280` was the same tie in the repeated `l` of `braille`; the targeted page-14 check now deletes the intended first equivalent `l` and recovers immediately. Focused tests were added for both patterns. The insertion tie-break and adjacent-swap logic remain in the Case-2-only bounded fine aligner; Case 1 keeps its prior alignment path. No fixture bytes changed.

The one authorized full frozen rerun after that change completed in 8.95 seconds. It **did not close**. The evaluator reports 995 findings, 0 reviews, 0 duplicate issue IDs, 980/1000 policy-accepted mutations, 20 unresolved mutations, and 20 unassociated findings. Its mutually exclusive mutation states are 969 strict exact, 6 equivalent identical-cell insertions, 5 equivalent adjacent-deletion actions, and 20 unresolved. The unresolved mutations comprise 15 deletions and 5 insertions; all 338 substitutions and all 162 transpositions remain strict exact. The physical audit reports 1142/1162 policy-satisfied target slots, 20 invalid/off-region boxes, 0 incorrect-page boxes, and 0 duplicate boxes. These 20 finding associations and boxes have **not** been demonstrated to be false positives or production defects; nor are they accepted as further equivalences without traces. The current evaluator's equivalence handling accounts for only 11 of the 16 previously identified information-limit actions (6/11 insertion, 5/5 adjacent deletion). In particular, the general deletion tie-break may have changed assignments of other repeated-cell deletions, but that is a hypothesis, not an established root cause. No second full frozen rerun or additional production adjustment was made.

**Current Case 1 + Case 2 combined closure: FAIL.** Exact blocker: 20 unresolved mutation-to-finding associations (15 deletion, 5 insertion) and 20 invalid/off-region boxes under the currently documented policy. The six targeted deletion traces pass, but the full fixture is not closed. Active controls listed above predate this latest one-line alignment change and must be rerun before any future PASS claim. The old contracted/Nemeth regression was not run, as instructed.

## Complete before/after accounting of the 20 unresolved IDs

The requested causal diagnostic is complete in [unresolved_twenty_tie_break_audit.md](unresolved_twenty_tie_break_audit.md). Every ID has pre/post findings and alignment operations, expected and actual spans, full-precision provenance and boxes, corrupted-PDF character indices, all compatible candidate findings, availability/consumption evidence, and a final mutually exclusive category. Machine-readable rows and all same-page candidate predicate checks are in `stress_test/final_case1_case2_alphabet_capitalization/results/unresolved_twenty_trace/twenty_cases.csv` and `twenty_cases.json`.

| Category | Count |
| --- | ---: |
| A. Regression caused by latest deletion tie-break | 15 |
| B. Valid identical-run equivalence rejected by evaluator | 5 |
| C. Evaluator association/consumption collision | 0 |
| D. Genuine pre-existing alignment defect | 0 |
| E. Correct alignment, wrong provenance | 0 |
| F. Correct provenance, wrong box | 0 |
| G. Other | 0 |
| Total | 20 |

**A is a regression under the current strict deletion-anchor policy.** In all 15 cases the pre branch deletes the second of two identical expected cells, with the required next surviving cell as anchor. The new tie branch deletes the first, so the actual gap, provenance cell, and exact box move one cell earlier. Both edit assignments produce the same Braille cell stream. The observed regression is in anchor selection relative to current policy; it is not proof that the alternative edit history is semantically impossible. No deletion-equivalence policy was broadened to accept these cases. Independent nonblank-cell-rank checks prove that provenance and boxes correctly follow the chosen actual position in all 40 pre/post traces.

**B is an evaluator field error in all five cases:** `DIV-0096`, `DIV-0296`, `DIV-0500`, `DIV-0700`, `DIV-0901`. The insertion equivalence predicate compares the finding's inserted cell to `actual_mask=15`, which records the original target `p`. The actual inserted `code_target=','` and corrupted PDF glyph encode mask 32. Each has exactly one available compatible insertion finding at the other member of the same contiguous two-capitalization-cell run. All other equivalence conditions pass. The pre/post findings and alignments are identical. No prior mutation consumed these findings.

Two controlled diagnostic evaluations were necessary to supply the requested pre/post evidence. The pre variant removed only the latest identical-deletion branch **in memory**; post ran the unchanged on-disk function. The older global fallback was not run. Both results are persisted (`pre.json`, `post.json`) so further analysis does not revalidate the fixture. Pre has 989 policy-accepted mutations; post has 980. The tie branch fixes `DIV-0083`, `DIV-0280`, `DIV-0283`, `DIV-0487`, `DIV-0687`, `DIV-0888`, but regresses the 15 A cases, yielding net -9 accepted mutations. Reverting it alone would restore those 15 and reintroduce six earlier failures.

Only diagnostic tooling and reports were added in this task. Production code and evaluator behavior were unchanged. `integrity.json` records identical before/after SHA-256 hashes for the frozen DOCX, diverse BRF/PDF, manifest, and three alignment/API/validator production files. The offline diagnostic script's assertions check all 20 classifications, uniqueness/availability of candidates, equivalent-cell identities, actual-to-PDF mapping, and exact box/provenance equality. All assertions pass. Closure remains **FAIL** pending a justified fix; no clean/control reruns, old contracted/Nemeth regression, Numbers, Punctuation, or normalization work were undertaken in this diagnostic task.

## Final observable-error closure — PASS

The two established causes were corrected without revisiting fixture validity or modifying provenance/highlighting. No source, BRF, PDF, or manifest fixture was regenerated or changed. No Numbers, Punctuation, normalization, or old contracted/Nemeth work was run.

### Small corrections and focused proof

1. **Insertion evaluator:** compare an insertion finding with the inserted `code_target` decoded in the Duxbury dialect, rather than the original target's `actual_mask`. The five rejected capitalization insertions insert mask 32 beside original mask 15. The existing unique-finding, expected-region, same-page, same-line identical-run, one-cell provenance, and exact-box restrictions remain. A focused regression failed before the one-line mask correction and passed afterward; different cells/pages/regions and inaccurate boxes remain rejected.
2. **Generic bounded alignment:** remove the unconditional first-equivalent-deletion preference. Preserve already matching prefix cells by default. For an optimal single deletion in an identical run, choose its leading gap only when the remaining identical cells separate that deletion from an optimal substitution of the immediately following, different cell. This keeps two observable edits separated by recovered matches and prevents their anchors collapsing onto one cell. The decision uses only bounded expected/actual cell sequences and edit costs—no rule-family, page, word, mutation-ID, manifest, or clean-PDF conditions.
3. **Genuinely indistinguishable deletion:** when either of two identical expected cells can be deleted with exactly the same resulting stream, retain the deterministic continuity-preserving alignment. The independent evaluator may accept the alternative gap only after proving a same-block expected run, exactly one missing cell, an intact surviving identical run on one physical line, a unique available deletion finding, and an exact box at a valid equivalent gap anchor. The allowed anchors are the surviving run and its immediate semantic successor on that line. A different line/page, Duxbury control/footer, altered run length, different block, inaccurate box, or unrelated finding is rejected. This narrowly resolves `DIV-0280`: either `l` deletion produces the same stream; the canonical surviving-cell anchor is the following `e`. It does not claim historical identity.

The unchanged deletion highlighting policy is: next surviving semantic cell on the deletion's physical line, otherwise the previous surviving semantic cell at line end; never a control/footer/other line/page. The equivalence proof concerns the ambiguous gap, not a change to that highlighting convention. Transpositions remain one logical mutation with two exact provenance cells, rendered as one envelope or two boxes by existing grouping.

Focused development considered two deletion placements. Preserving the matched run prefix even before a neighboring substitution made the deletion and substitution anchor to the same surviving cell; a focused test rejected that candidate before any full run. The final context-dependent rule separates those edits while preserving the 15 previously correct anchors. The tests cover the page-start indicator pattern and arbitrary non-indicator cells, repeated letters, unique deletions, deletions beside insertions/indicators, immediate recovery, terminal same-line anchors, controls, and unchanged substitution/insertion/transposition behavior.

**Local proof before the frozen run:** `verify_local_deletion_closure.py` replays bounded windows from the saved pre/post inputs without full document validation. All 26 required cases pass: 20 strict deletions (the 15 regressions plus five original page starts), five insertion equivalents, and one deletion equivalent (`DIV-0280`). Unknown/unresolved: 0. The original five page-start cases remain strict: `DIV-0083`, `DIV-0283`, `DIV-0487`, `DIV-0687`, `DIV-0888`. Local evidence is saved as `results/unresolved_twenty_trace/local_closure.json`.

### One full frozen run

Exactly one authorized full diverse validation was performed after the focused tests and local replay passed. Validator runtime: **9.189 seconds**. Full per-action outcomes, per-finding provenance/boxes, equivalence proof, and before/after fixture hashes are in `stress_test/final_case1_case2_alphabet_capitalization/results/frozen_observable_closure.json`.

| Logical mutation/action accounting | Result |
| --- | ---: |
| Injected actions | 1,000 |
| Strict exact observable matches | 983 |
| Identical-cell insertion equivalents | 11 |
| Additional actions covered by adjacent-deletion groups | 5 |
| Proven indistinguishable deletion-placement equivalents | 1 |
| Total actions correctly accounted for | **1,000 / 1,000** |
| Findings, all associated | 995 / 995 |
| Adjacent two-action deletion groups | 5 |
| Unresolved observable errors / missed actions | **0** |
| Unexplained/unmatched findings | **0** |
| Reviews / duplicate issue IDs | **0 / 0** |

The 995 findings are correct under the documented grouping policy: five findings each cover two adjacent deleted cells/actions. No finding is reused across unrelated actions. Substitutions: **338/338 strict exact**. Transpositions: **162/162 strict exact**. Insertions: **214 strict + 11 equivalent = 225/225**. Deletions: **269 strict + 5 grouped additional actions + 1 equivalent = 275/275**.

| Physical localization | Result |
| --- | ---: |
| Required physical target/anchor slots satisfied under policy | **1,162 / 1,162** |
| Exact historical-instance target slots present | 1,150 / 1,162 |
| Historical-instance differences proved equivalent | 12 (11 insertion, 1 deletion) |
| Actual blue boxes | 1,046 |
| Invalid/off-region boxes | **0** |
| Incorrect-page boxes | **0** |
| Unexplained boxes | **0** |
| Duplicate boxes | **0** |

The raw strict-oracle `off_target_boxes=12` field remains visible in the result; all 12 are explicitly explained by the proven identical-cell regions. It is not presented as zero strict historical-instance differences. The policy-aware invalid/off-region count is zero. Logical action count, physical slots, and grouped boxes remain separate quantities.

### Active controls after diverse PASS

| Gate | Result |
| --- | --- |
| Focused uncontracted tests | **29/29 PASS** |
| Independent equivalence policy tests | **4/4 PASS** |
| Clean real-Duxbury 50-page PDF | **0 findings, 0 reviews, 0 duplicate IDs** |
| Frozen 1,000-substitution PDF | **1,000 findings; 1,000/1,000 exact boxes; 0 off-target/duplicate boxes; 0 reviews/duplicate IDs** |
| Frozen Case 1 500-error PDF | **500 findings; 500/500 exact boxes; 0 off-target/duplicate boxes; 0 reviews/duplicate IDs** |
| Old contracted/Nemeth regression | **Not run**, as instructed |

Control details and unchanged input hashes are in `results/active_uncontracted_controls.json`. Case 1 uses its existing accepted physical target/anchor records as the regression oracle, not locations inferred from current output. The control runner reads existing fixture files and does not invoke their generation functions.

### Files changed in this closure iteration

- Production: `src/braille_app/validation/alignment.py` only.
- Independent evaluator: `stress_test/final_case1_case2_alphabet_capitalization/scripts/evaluate_frozen_diverse.py` (inserted mask, narrowly proved deletion equivalence, durable detailed outcomes).
- Focused tests: `tests/test_uncontracted_alignment_indel_recovery.py`, `tests/test_diverse_equivalence_policy.py`.
- Read-only verification runners: `scripts/verify_local_deletion_closure.py`, `scripts/run_frozen_observable_closure.py`, `scripts/verify_active_uncontracted_controls.py` under the combined fixture folder.
- This progress report and the generated result JSON files referenced above.

No changes to `validator.py`, `api.py`, provenance mapping, PDF rendering, or box grouping were needed. All eight frozen hashes in the opening table were verified immediately before and after the full run and remain identical, including DOCX `8c53cec65b6dfbc21c072db1ceaa448db887974dbc386379ae4c66941c4b72f2`, diverse PDF `4492fdce40202a1ab84fce9149c20142daed2dafee2d3b108c58fea9fa1f209b`, diverse BRF `c40c1a25e5fdb949853bfdd89b212b6cc93d3cc63b1e0eaa7dfe6e63319c61f7`, and manifest `0517fb314d818500983e4f5ee9937b458e019565d0d7c54b79512159d333aab4`.

**CASE 1 + CASE 2 COMBINED CORE: PASS**

Freeze fingerprints: `alignment.py` SHA-256 `2eb68cc012f76ed1b16d5bab5fce3e136640bd176ca215494aba5cf719d15a4b`; independent `evaluate_frozen_diverse.py` SHA-256 `a96e9484cfc4aeaf3334763bb780307f31e28fa0bff62b2d7070c1b9071f8972`. `validator.py` and `api.py` still match their pre-fix diagnostic hashes.

**ALIGNMENT / PROVENANCE / HIGHLIGHTING CORE IS FROZEN.**

**READY FOR CASE 3 — NUMBERS.** At the time of this historical checkpoint,
Case 3 had not yet been started.

### Case 3 stress alignment — active diagnostic

The frozen 500-action fixture and its nine recorded artifact hashes remain
unchanged. The first public-validator run completed in 24.9008 s (above the
18.378 s stop threshold derived from the 9.189 s Case 1+2 baseline), so it was
not used as a gate. Its result is preserved at
`stress_test/uncontracted_case3_numbers/results/case3_validation_result.json`:
128 findings, 0 reviews, only 3,857/22,125 matching cells, and 2/90 source
passages aligned. The independent evaluator matched 43 actions exactly,
classified 9 as detected/mislocalized, missed 448, and left 76 findings
unmatched; it measured 571 off-target boxes. No fixture file was changed.

Confirmed root cause: the public DOCX adapter presents this source as one
logical page; the Case 3 profile was not selected for the existing regional
alignment path, so 22,125 expected cells were compared globally against the
repeated numeric stream. That fallback took 24.9 s and lost correspondence.
The existing paragraph-to-line dynamic program was rejected: a bounded
10-paragraph/3-page experiment took 9.95 s. A bounded page-local experiment
instead cut the expected stream at nearest existing blank cells proportional
to physical page lengths and reused the unchanged `align_cells` routine: the
first three physical pages aligned in 0.064 s with 2,701/2,753 expected cells
matched.

The current Case 3-only production path applies those proportional physical-
page anchors and keeps every source/actual offset in the existing continuous
coordinate system. It does not modify `alignment.py`, provenance, or PDF box
rendering. Added a focused repeated-page test with an insertion and deletion;
all 15 Case 3 focused tests pass. The 25-page clean Case 3 PDF passes with
0 errors, 0 reviews, all 90/90 passages aligned, and 1.23 s runtime.

The one post-fix frozen 500-action validation and one-to-one physical evaluator
are prepared but not yet run. Case 3 closure and the active Case 1+2 regression
gates remain pending; no old contracted/Nemeth suite, Case 4, or normalization
work has been started.

## Case 3 — Numbers (active implementation)

Case 3 is now active. Case 1+2 remain PASS; their fixture/evaluator and
alignment core are untouched. The authoritative audit is in
[`uncontracted_case3_numbers_standard_audit.md`](uncontracted_case3_numbers_standard_audit.md).
Fresh probes use vendored Liblouis 3.38.0, exact table list
`unicode.dis,en-ueb-g1.ctb`, table SHA-256
`446717b55e49ff41aef2c204b58ea1d2872a77a4473a821e766bffd51cee0b4d`.

Confirmed standards gaps and corrections:

- UEB 6.6.1 requires a numeric-space cell for a clearly grouped thousands
  sequence. Liblouis emitted a visible blank plus a new numeric indicator;
  Case 3 now uses the Liblouis source-position map to combine the blank and
  following digit and remove that repeated indicator.
- UEB 6.5.4 requires Grade 1 for the cited contraction-sensitive suffixes
  after a numeric hyphen; 5.8.1 places Grade 1 before caps. Liblouis omitted
  it in `3-D`, `4-m`, `6-CD`, and `20-yr`. Case 3 adds a mapped indicator only
  for the cited narrow forms; `20yr` and `3-dimensional` remain unchanged.
- Fresh probes confirmed the cited direct cases for digits, decimals,
  comma-decimals, numeric-mode termination, a-j after digits/periods, and
  uppercase after a digit. Out-of-scope source characters fail closed to
  Review.

New Case 3 profile/translator and focused tests are present. Before the
profile-only adapter wiring, focused PDF reproductions proved two integration
gaps: extra insertions were silently ignored and deleted numeric cells had no
existing-policy anchor. The narrow wiring now routes Case 3 through the same
uncontracted insertion ownership and same-line deletion-anchor branches; the
alignment, provenance geometry, and box-rendering algorithms were not
changed. Focused tests currently pass for cited cells, direct/no-override
neighbors, clean/corrupt/BRF-equivalent one-page cases, fail-closed review,
vendored runtime identity, confirmed insertion ownership, and PDF deletion
anchoring. Corpus generation, diverse stress validation, active regressions,
and Duxbury status remain pending.

### Case 3 page-local transposition follow-up — frozen run completed

The Case 3 page-local route now calls the existing frozen
`alignment._align_bounded_block` for each physical-page region. This is the
same helper used by the Case 1+2 alignment core; its adjacent-swap branch
recognizes `expected[i] == actual[j+1]` and `expected[i+1] == actual[j]` and
emits one 2-by-2 `replace` opcode. `alignment.py` remains byte-for-byte
unchanged (SHA-256
`2eb68cc012f76ed1b16d5bab5fce3e136640bd176ca215494aba5cf719d15a4b`). The
focused Case 3 suite passes 15/15, including the page-local swap/recovery
regression. The clean frozen 25-page PDF returns 0 errors, 0 reviews, and
90/90 aligned source passages (9.0713 s).

The same frozen corrupted fixture was run once against this transposition-
aware path. The runner rechecked the frozen source/PDF hashes, and the
independent evaluator rechecked the BRF and mutation-manifest hashes. Runtime
was 8.5689 s; 507 findings, 0 reviews, and 0 duplicate issue IDs. All 40
`transpositions` mutations are now correctly detected and localized; the 20
capitalization-order transpositions that had previously split into two
single-cell findings are also recovered by the shared swap handling.

Independent one-to-one results (the run is **not closed**): 500 mutations =
470 correctly detected/localized + 24 detected/mislocalized + 6 missed;
0 association ambiguities; 13 validator findings remain unassociated (not yet
proven false positives). Physical audit: 560 required target cells, 531 with
finding provenance, 500 required boxes, 507 rendered boxes, 36 strict
off-target boxes, 1 duplicate box, and 0 incorrect-page boxes. The 24
mislocalized outcomes are all deletion operations: 12 ordinary cell deletions
and 12 capitalization-indicator deletions; their displayed anchor is one
cell to the right of the evaluator's target. Four of the six misses are
insertions into runs containing an identical Braille cell; the current Case
3 evaluator has not yet applied the Case 1+2 identical-run equivalence policy
to them. The remaining miss examples are a page-edge substitution and a
page-start numeric-indicator deletion, whose nearby findings are broad spans;
their exact alignment/association cause remains unproven.

The page-local path does therefore reuse the proven adjacent-swap handler,
and the frozen transposition cases verify its effect. Case 3 remains FAIL:
deletion-anchor localization, the four identical-run insertion adjudications,
the two other missed cases, and 13 unassociated findings still require
evidence-based resolution. No production behavior was changed to force
manifest IDs. The frozen fixture remains unchanged.

### Case 3 — numeric page-boundary refinement and closure (current)

This section supersedes the preceding pending Case 3 status. The Case 3
page-local route still uses the frozen `_align_bounded_block`; only its
Case-3-specific coarse page-boundary selection changed. Around the existing
proportional estimate, it scores up to 32 expected/actual cells on each side
of a candidate blank using that same frozen local aligner. If no nearby blank
exists it retains the proportional candidate. The accepted `alignment.py`
hash is unchanged.

The focused evidence isolated four misplaced page cuts. The old blank-cell
cuts after physical pages 2, 10, 16, and 17 were respectively 1819, 9084,
14554, and 15480; the local edge evidence selected 1823, 9078, 14545, and
15468. These shifts account for the previously unassociated cross-page
insertion/deletion clusters and put the page-edge substitution C3-0001 and
page-start deletion C3-0310 back into their correct physical regions. Other
page cuts remain at the proportional location. This was the first incorrect
stage; no provenance, PDF geometry, or classification changes were needed.

The independent evaluator was also corrected without changing production:
deletions use the product's next-semantic-cell anchor on the same actual PDF
line (skipping blank/control/footer cells, with the existing previous-cell
fallback), and inserted/deleted identical-cell runs use the already-tested
Case 1+2 equivalence constraints. Three evaluator-focused tests cover these
policies. On the old alignment result, these policy corrections alone
changed the audit from 470 direct + 24 mislocalized + 6 missed, 13 unmatched,
to 482 direct + 16 proven equivalents, 2 missed, and 9 unmatched. The page
boundary reproducer then passed before another full run.

The same frozen 500-action Case 3 fixture was run once after the production
boundary refinement. Runtime was **8.8142 s**; 500 findings, 0 reviews, and 0
duplicate IDs. One-to-one independent evaluation:

| Case 3 logical action result | Count |
| --- | ---: |
| Injected actions | 500 |
| Directly detected and localized | 484 |
| Proven identical-run equivalents | 16 (4 insertions, 12 capitalization-indicator deletions) |
| Total actions detected/localized | **500 / 500** |
| Missed / mislocalized / ambiguous | **0 / 0 / 0** |
| Unmatched findings | **0** |
| Reviews / duplicate issue IDs | **0 / 0** |

Physical audit: 560 required physical target cells; 544 have strict historical
provenance and the remaining 16 are satisfied by the proven identical-run
equivalences; all 500 required boxes are rendered. Strict historical-instance
box differences are 16 and all 16 are explicitly explained by those
equivalences. Policy-aware off-target boxes, invalid/off-region boxes,
incorrect-page boxes, and duplicate boxes are **0**. No box is unexplained.
Deletion semantics are same-line next semantic nonblank cell, previous
semantic cell when no next same-line cell exists, matching the current
uncontracted production adapter. Identical-cell equivalence remains confined
to a single intact/shortened same-line run with exact provenance and box.

After the production change, the clean Case 3 25-page PDF returned **0
findings, 0 reviews, 0 duplicate IDs**, with all 90/90 clean source passages
aligned (11.4321 s). Case 3 focused tests: **16/16 PASS**; Case 3 evaluator
policy tests: **3/3 PASS**.

Required active regression gates were rerun:

| Gate | Result |
| --- | --- |
| Frozen Case 1+2 diverse 1,000-action closure | **1,000/1,000 accounted; 0 unrelated findings; 0 reviews/duplicate IDs; 1,162/1,162 policy target slots; 0 invalid/off-region, wrong-page, or duplicate boxes** |
| Frozen 1,000-substitution control | **1,000/1,000 exact boxes; 0 misses, off-target boxes, duplicate boxes, reviews, or duplicate IDs** |
| Case 1 500-action regression | **500/500 exact boxes; 0 off-target/duplicate boxes, reviews, or duplicate IDs** |
| Clean real-Duxbury 50-page Case 1+2 control | **0 findings, 0 reviews, 0 duplicate IDs** |
| Relevant Case 1–3 focused/regression tests | **52/52 PASS** |
| Old contracted/Nemeth 185-case suite | **Not run** |

**CASE 3 — NUMBERS: PASS.** **CASE 1 + CASE 2 FROZEN CORE REMAINS GREEN.**
The Case 3 frozen artifacts remain unchanged. Frozen SHA-256 values:

- Source DOCX: `39466c3374a98af1fc3480f5a84e5b535cb72bf377e7f3eda6f1e2e8df8e3238`
- Expected metadata: `b59f8b597b9c14cc177b22cd129b702721185a7816d336b05b7211cf2e589257`
- Clean PDF / BRF: `e7f7da9ed253506600b7e665865852f1a94165f8257981150d9e52c4478ce930` / `577ab5ae5fbfd74f0b1fe2aee00214b42593af06616ec1d23585dda62984703d`
- Corrupted PDF / BRF: `3282b6bc10863e75a4fe86952cf761f80f93f79e4b692bc8b64760e71f8a0998` / `819643c2ec190dae5fe0a7734e7eaa7e7faad71309f1bb6d0a6dfee8a9d3d69d`
- Mutation manifest: `e01483f574424c3d9c36827624ee65187ef79847865e718e5e653e4669ab5fb2`
- Coverage manifest: `7217a2bb702136b805bbf11fba4326c683704c1a0b7fff093dba1441b59bc498`
- Fixture generator integrity: `4890c6eaeeabb4330f1400dcb0a5a90a0d82d120e5239ead75e5ab499aead6f0`

Files changed for this closure: `src/braille_app/validation/validator.py`
(Case-3-only boundary scoring); `stress_test/uncontracted_case3_numbers/run_case3_validator.py`
and `evaluate_case3_validation.py` (preserved old results under their old
names; new boundary-refinement result/evaluation files); and new
`tests/test_case3_observable_evaluator.py`. No Case 1+2 production or fixture
file was changed. The frozen Case 3 fixture remains byte-for-byte unchanged.

## Case 4 — core punctuation closure (2026-09-23)

**CASE 4 — CORE PUNCTUATION: PASS.** Scope is comma, period/full stop,
question mark, exclamation mark, colon, and semicolon only. Quotes,
apostrophes, general hyphens/dashes, brackets, miscellaneous symbols, and
typeforms remain unsupported. No final 2,000-action integration test or
normalization work was started.

### Standards and translation decisions

Authority is ICEB *Rules of Unified English Braille*, Third Edition (2024),
local PDF `rules/Rules-of-Unified-English-Braille-2024.pdf`:

- §§7.1.1–7.1.3 (printed pp. 75–78; PDF pp. 103–106): punctuation follows
  print, one braille blank follows punctuation, and Grade 1 symbol indication
  is required where punctuation could be read as a contraction.
- §§7.5.1–7.5.4 (printed p. 81; PDF p. 109): question-mark indicator
  contexts, including the after-hyphen/dash case.
- §6.4.1 (printed p. 68; PDF p. 96): numeric/full-stop interaction.

Fresh probes used only vendored Liblouis 3.38.0, table list
`unicode.dis,en-ueb-g1.ctb`, table path
`vendor/liblouis-win64/share/liblouis/tables/en-ueb-g1.ctb`, SHA-256
`446717b55e49ff41aef2c204b58ea1d2872a77a4473a821e766bffd51cee0b4d`.
Ordinary punctuation and tested indicator placements use Liblouis directly.
The only mapped corrections are the cited Grade 1 indicator before a
question mark after an in-scope numeric hyphen/dash and reduction of multiple
source blanks following punctuation to one braille blank. Unsupported
constructs fail closed to Review. Full probe/adjudication details are in
`reports/uncontracted_case4_punctuation_audit.md`.

### Frozen Case 4 fixture and independent integrity

The existing fixture remains frozen; no fixture writer was run after freeze.
Independent replay verified 500 unique actions, requested family totals,
26 physical pages, 22 natural and 3 manual page transitions, zero net cell
delta, exact clean/corrupted PDF↔BRF streams, manifest replay, resolvable
targets/sources, and zero out-of-scope/footer/control targets.

| Frozen artifact | SHA-256 |
| --- | --- |
| Source DOCX | `7d1e63cc5dd2dc6dc2a4dfccb2508670cf530068794c1cd7768f789b40f92009` |
| Expected metadata | `348d5c722bd1518b389a24be31332ea61c80b1ed627dcb10629d8f6c80784ad2` |
| Coverage manifest | `da8e78f61f5331423f0c1769ff76a797449f3c55934eb6df7bdb09892e564f4f` |
| Clean PDF / BRF | `e58434bb347dc397033e4cc599fa6b8c11cfa5a7000ebed446be8ee11f76bed7` / `25c222be83ad0dea2b1aa11307bfcc187545cc2ce0bc79857c599344303a9693` |
| Corrupted PDF / BRF | `b0dbc83da9674cc0cdba169ef312ae9b1b7c03bb1e2dd6603d5cb8e7ac821049` / `789b2f8b3c437448765a55df8e68bef0624f979da999394f3fd638960ffc7df4` |
| Mutation manifest | `64c22dbb49f4992d57b8b74d05e952de3fecbe0e4fa2a8dde0c3ab6b0b4009d5` |
| Fixture integrity record | `b8fbf2a6227a6801ef35852c185c94f65fcfcc38e8a6dbcde242ddd4166314b9` |

### Root cause and focused proof

Before the final localization fix (after the Case 4 insertion-ownership fix),
the frozen run had 500 findings, 0 reviews, and 0 duplicate IDs. The evaluator
matched 315 directly and 58 through the established identical-run policy;
the remaining 127 were all deletions. Their source spans/findings were
correct, but the zero-width actual ranges had no provenance cells or boxes.
The first incorrect stage was the shared PDF annotation adapter: its
uncontracted deletion-anchor eligibility listed Case 1–3 scopes but omitted
Case 4. Alignment, classification, and source provenance were not the cause.

A one-page PDF regression failed before the fix with 0 provenance cells for
a deleted comma. The smallest production change added Case 4 scope to the
adapter's existing deletion-anchor policy (next semantic nonblank cell on
the same physical line; previous semantic cell when no following same-line
cell exists). The strengthened regression now verifies the exact anchor
cell, page, and rendered box geometry. No alignment code changed.

### Frozen Case 4 result

The same frozen 500-action PDF/BRF/manifest passed one-to-one evaluation:

| Metric | Result |
| --- | ---: |
| Injected logical actions | 500 |
| Validator findings | 500 |
| Directly detected and localized | 442 |
| Proven identical-run equivalents | 58 |
| Missed / mislocalized / ambiguous / unmatched | 0 / 0 / 0 / 0 |
| Reviews / duplicate issue IDs | 0 / 0 |
| Required physical target cells | 606 |
| Target cells with strict historical provenance | 548 (58 are proven equivalents) |
| Rendered boxes / required logical-action boxes | 500 / 500 |
| Policy-unexplained / invalid-provenance / wrong-page / duplicate boxes | 0 / 0 / 0 / 0 |
| Strict box-key differences explained by equivalence | 58 |
| Runtime | 8.8731 s |

Family outcomes (direct + equivalent): comma 70+10; period 70+10;
question 61+9; exclamation 61+9; colon 53+7; semicolon 53+7; punctuation
Grade 1 40+0; punctuation/capitalization/numeric interactions 14+6;
repeated-context/boundary 20+0. The 500 findings are associated one-to-one
under the documented identical-cell insertion equivalence; there are no
unmatched findings.

The post-fix clean Case 4 PDF returned 0 findings, 0 reviews, and 0 duplicate
IDs, with 145/145 source passages aligned and exact PDF provenance (8.7472 s).
PDF QA rendered all 26 clean and corrupted pages as contact sheets and full
pages 1, 13, and 26 at readable resolution; Braille rows remained legible,
within margins, and free of clipping/overlap. This checks PDF layout, not a
manual Duxbury retranslation.

### Active Case 1–3 controls rerun after the Case 4 production change

| Gate | Result |
| --- | --- |
| Frozen Case 1 500-action regression | 500 findings; 500 exact boxes; 0 off-target or duplicate boxes; 0 reviews/duplicate IDs (26.502 s) |
| Frozen Case 1+2 diverse 1,000-action fixture | Closure PASS; 1,000 actions accounted; 995 findings with 983 direct + 17 policy-equivalent actions; 0 unresolved/unrelated findings; 0 reviews/duplicate IDs; 1,162/1,162 policy target slots; 0 invalid/off-region, wrong-page, or duplicate boxes. The raw strict target-key comparison reports 12 geometry differences; these are within the evaluator's policy-allowed set. |
| Frozen Case 1+2 1,000-substitution control | 1,000 findings and target boxes; 0 misses, non-target boxes, or duplicate boxes; 0 reviews/duplicate IDs (9.258 s) |
| Clean real-Duxbury Case 1+2 50-page control | 0 findings, 0 reviews, 0 duplicate IDs (9.220 s) |
| Frozen Case 3 500-action fixture | 500 findings; 484 direct + 16 proven equivalents; 0 missed/mislocalized/ambiguous/unmatched; 0 reviews/duplicate IDs; 500/500 logical boxes; 0 off-target/wrong-page/duplicate boxes (9.0139 s) |
| Clean Case 3 control | 0 findings/reviews/duplicates; 90/90 source passages aligned; no unmatched provenance (8.8558 s) |
| Clean Case 4 control | 0 findings/reviews/duplicates; 145/145 source passages aligned |
| Relevant focused/regression tests | 58/58 PASS |
| Old contracted/Nemeth 185-case suite | Not run, as instructed |

Case 4 production files: `src/braille_app/translation/profiles.py`,
`src/braille_app/validation_profiles.py`,
`src/braille_app/translation/source_normalization.py`,
`src/braille_app/translation/uncontracted_case3.py`, new
`src/braille_app/translation/uncontracted_case4.py`,
`src/braille_app/translation/expected_document.py`,
`src/braille_app/validation/validator.py`,
`src/braille_app/validation/api.py`, and
`src/braille_app/validation/pdf_annotation_adapter.py`. The focused test is
`tests/test_uncontracted_case4_punctuation.py`. Fixture/evaluation tooling is
`stress_test/uncontracted_case4_punctuation/build_case4_fixture.py`,
`verify_case4_fixture.py`, `run_case4_validator.py`, and
`evaluate_case4_validation.py`. Run-specific JSON/CSV results use the
`*_after_deletion_anchor*` names; earlier evaluation results were preserved.
No cell-alignment implementation was modified for Case 4. Case 4 real-Duxbury manual
verification remains **PENDING**; DOCX visual rendering was unavailable
because LibreOffice is not installed, and no software was installed.

**CASE 3 — NUMBERS: PASS. CASE 4 — CORE PUNCTUATION: PASS.**
**CASE 1–4 INDIVIDUAL FAMILY GATES: GREEN.** READY FOR THE FINAL 2,000-ACTION
CASE 1–4 INTEGRATION TEST in the next session. It was not started here.
