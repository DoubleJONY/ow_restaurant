# Joseon Deluxe tasks

- [x] Inspect Deluxe dispatcher, shared logic and edition data structure.
- [x] Identify sink-water supply unique to the selected variants.
- [x] Archive new Cafe as deprecated/nc_kr.ow without changing its bytes/version.
- [x] Confirm n3_kr.ow is the New Branch 3 source, not attached message.txt.
- [x] Record final constraints and implementation plan.
- [x] Record HEAD, input hashes and immutable baseline snapshots.
- [x] Copy kr_deluxe.ow to Joseon_deluxe.ow.
- [x] Parse input data and write forward/inverse item mappings.
- [x] Port New Branch 3 item, recipe, menu and ingredient tables.
- [x] Port New Cafe item, recipe, menu and ingredient tables.
- [x] Adapt all six modes to actual theme ranges and fusion data.
- [x] Supply water code 21 in all three editions, without a waterCode variable or edition gate.
- [x] Audit every edition-0 branch and exclude preservation-box acquisition/use.
- [x] Align starts, shops, weighted drops, merchants and special-order materials.
- [x] Keep Cafe freezing and cooling-gun ordinal aligned with Deluxe.
- [x] Apply site-only tutorials without forced orders or Classic tutorial waves.
- [x] Align titles, UI, authors, score records and version strings.
- [x] Empty edition-2 recipe values while keeping selection and other settings (original 2026-10-17 state; superseded below).
- [x] Verify inverse-mapped data and ingredient reachability; statically trace edition initialization/switches.
- [x] Run syntax and diff checks; record static versus in-game test coverage.
- [x] Document remaining Workshop import/runtime checks and final changes.
- [x] Apply author-confirmed Cafe raw score 191 = 4 and remove two tab-prefixed zero tokens; preserve immutable input snapshots.
- [x] Align runtime score 191 = 20 and workbook raw score 191 = 4; retain unrelated zero-score/duplicate-menu settings.
- [x] Apply subsequent user request: N3 raw scores 46/111 = 3 (runtime 15) and stable-deduplicate Cafe menu entries 235/114/434; align the item workbook.
- [x] Restore original legacy version dates/patch text by explicit user request, retaining data corrections and leaving Joseon/workbook unchanged.
- [x] Restore all three Joseon score initializers to raw 0..9 plus initialization *5; verify identical runtime values and preserve approved data corrections.
- [x] Defer edition 2 on 2026-10-31: limit startup selection to N3/Cafe and remove GC dispatcher/difficulty-up calls; preserve GC init rules/data.
- [x] Compact practice Other Menu to two internal editions and two external links; align cycle, dispatch threshold, labels and link indexes.
- [x] Align edition labels, credits/difficulty and colors; add static edition-selection regression tests and recheck active data/stages.
- [x] After the temporary hold, restore original-compatible table waits only (N3 follows GC, Cafe follows CAFE); preserve original mixing/stock/customer loop behavior, counters, data and tutorial menu lock. The user explicitly requested commit/push.
- [ ] External verification: Workshop import, actual element count and in-game smoke tests.

Implementation and static validation are complete on 2026-10-17. In-game tests
are not claimed. See validation_report.md for scope and limitations.
Unrelated working-tree changes belong to their existing owners. The initial
commit/push prohibition was superseded by the user's explicit publication
request on 2026-10-31. Publish this completed Deluxe/Joseon work only, including
its code, tests, artifact and final workbooks; exclude unrelated site/audit work
and temporary output files. No force push or history rewriting is authorized.
