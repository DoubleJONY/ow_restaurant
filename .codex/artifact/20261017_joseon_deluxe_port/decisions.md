# Decisions and actions

2026-10-17, Asia/Seoul. Scope: this repository only.

## User-confirmed decisions

- Create Joseon_deluxe.ow from kr_deluxe.ow with three edition slots.
- Put New Branch 3 in edition 0, New Cafe in edition 1, leave edition 2 recipes empty.
- Edition 2 stays selectable with no extra unfinished-mode handling.
- Tutorial content is recipe-site guidance only, following GC.
- New Branch 3 must not inherit preservation boxes from Classic's edition 0.
- Use existing n3_kr.ow as the New Branch 3 input.
- Archive supplied message-2.txt as deprecated/nc_kr.ow for the New Cafe input.

## Completed actions

- Copied message-2.txt verbatim to deprecated/nc_kr.ow; cmp returned success.
- Preserved its internal v260613 version and STRAX workshop code.
- Read current Deluxe implementation and historical unification mapping notes.
- Wrote implementation_plan.md, task.md and this action record.
- Added a scoped Joseon port pointer and constraints to .codex/workspace.md.
- Recorded the user's project-path authorization in the local approval ledger.

## Implementation and user amendment

- The user paused work after the first runtime copy, then explicitly resumed it
  with the request to place water at common item code 21.
- Created Joseon_deluxe.ow, version v261017, with New Branch 3 in edition 0 and
  New Cafe in edition 1. Preserved shared runtime and the third edition slot.
- Common water metadata uses slot 21. New Branch 3 rice moved to 514, its
  boiled water to 515; New Cafe boiled water moved to 521; placeholder
  gochujang moved from 21 to 464 to preserve the existing food record.
- Normalized two tab-prefixed zero lookup tokens in the new Cafe source's
  FRYING_RESULT at original indexes 374 and 482. The legacy file is untouched.
- Neutralized non-food ICE results, removed Classic preservation-box use and
  Classic theme-11 supply/melting branches, and retained Lifeweaver supplies.
- Expanded Cafe practice to Deluxe's six slots and flattened two malformed
  random challenge wave expressions into single-theme waves.
- Completed static source/data/reachability/stage checks. Workshop import,
  actual element counts and in-game behavior are not verified.
- No stage, commit or push was performed. Unrelated project changes were left alone.

## Shared water follow-up

- The user confirmed the third edition will use water as well.
- Removed waterCode declaration/initialization and all water-supply edition gates.
- All three editions now display the water source and directly create item 21.
- Recipe contents and the third edition's unfinished status remain unchanged.

## Author-confirmed Cafe typo correction

- On 2026-10-17, the user reported the original author's intended raw score
  for item 191, chocolate-banana bingsu, is 4 instead of the malformed token ㅊ.
- Corrected deprecated/nc_kr.ow at that token and the two tab-prefixed zero
  tokens in FRYING_RESULT (374, 482). Its edit-date version is now v261017;
  CRLF line endings and all other source bytes are preserved.
- Corrected Joseon_deluxe.ow ITEM_SCORE[191] from -5 to 20 (raw 4 times 5).
  Its two frying results were already neutral zero and were not changed again.
- The item workbook displays raw score 4, not runtime score 20.
- Immutable inputs/nc_kr.ow remains the verbatim original snapshot. Original
  hashes in the manifest remain snapshot identifiers, not edited legacy hashes.
- Zero-score N3 orders and duplicate Cafe menu entries remain unchanged.
- No commit or push is authorized.

## User-requested menu deduplication and N3 scores

- On 2026-10-17, the user approved raw score 3 for N3 item 46 (sliced sundae)
  and item 111 (poached egg). Root n3_kr.ow now stores raw 3; Joseon stores
  runtime 15 and the item workbook displays 3. N3 edit-date versions are v261017.
- Deduplicated Cafe normal menu theme 7 item 235, Hazard theme 3 item 114,
  and Lifeweaver theme 3 item 434 in deprecated/nc_kr.ow and Joseon_deluxe.ow.
  Kept the first occurrence and the relative order of all other entries.
- This supersedes the earlier decision to leave zero-score/duplicate settings
  unchanged. Immutable input snapshots remain untouched.
- No recipes, ingredient supplies, stage order, tutorials, other scores or
  unrelated files were changed. No commit or push is authorized.

## Legacy metadata rollback

- The user explicitly requested legacy files retain original version dates and
  patch history while keeping approved data fixes. This overrides automatic
  edit-date version updates for these two legacy files.
- Restored both n3_kr.ow version labels to v260827 and the nc_kr.ow label to
  v260613. Other patch descriptions already matched the original snapshots.
- Verified all non-data content matches the immutable originals; corrected
  scores, malformed-zero fixes and menu deduplication remain intact.
- Joseon_deluxe.ow and the item workbook are unchanged by this rollback.

## Score initialization representation rollback

- The user requested the original Deluxe score representation to avoid editing
  confusion. All three Joseon edition ITEM_SCORE assignments now store raw
  0..9 strings and decode with Index Of Array Value(...)*5 at initialization.
- This reverses only the port's precomputed score serialization. All evaluated
  item/recipe/menu tables are identical to the pre-change runtime.
- Approved raw scores remain N3 46/111 = 3 and Cafe 191 = 4. Cafe menu
  deduplication, legacy data fixes, original legacy dates and patch notes remain.
- The manifest's ITEM_SCORE corrections also use raw units; its read-only audit
  applies *5, matching source initialization. No .ow builder was revived.
- Existing Deluxe files, legacy files and the item workbook were not edited.

## Two-edition amendment (2026-10-31, Asia/Seoul)

- The user requested deferring unfinished edition 2 and approved the analyzed
  two-edition change. This supersedes the original selectable-placeholder policy.
- Startup cycles N3/Cafe only. Practice Other Menu has two internal editions
  and two external code references; its modulo, dispatch threshold and external
  indexes are aligned. Edition labels, credits/difficulty and colors use two entries.
- Removed all four calls to GC init subroutines from initialization and the
  difficulty-up path. Kept GC declarations and all three GC init rules/data intact.
- N3/Cafe init rules, shared water, recipes, scores, site-only hints, six modes,
  and the preceding HUD/shop fixes are unchanged. Other Deluxe and legacy files
  and immutable snapshots were not edited by this amendment.
- Added tests/test_joseon_editions.py and updated the read-only port audit to
  validate 12 active edition/mode combinations while checking retained GC data.
- No staging, commit, push or in-game execution is authorized or claimed.

## Publication approval (2026-10-31, Asia/Seoul)

- After completion and validation, the user explicitly requested commit/push.
  This supersedes the earlier publication prohibition for this completed work.
- Publish the four Deluxe runtimes, approved N3/Cafe legacy data fixes, Joseon
  tests/artifact, workspace guidance and the two final item/mix workbooks.
- Exclude unrelated recipe audit/site plan/site checkout, local permission
  ledger and temporary support/backups/previews. Leave them locally untouched.
- Push normally to origin/main without force or history rewriting. In-game
  verification remains pending; publication is not evidence of a runtime pass.
- Added targeted .gitattributes rules to preserve immutable input snapshots and
  the corrected Cafe legacy bytes despite core.autocrlf=input. Removed redundant
  blank lines at the end of read_tables.py found by the staged whitespace check.
- Before publication the user requested declaration indentation fixes before
  line 232 in all four Deluxe files. Converted the space-indented declarations
  at lines 17, 130 and 171..173 to two tabs, preserving IDs/names and all logic.
  Added a regression check and refreshed the Joseon runtime hash.

## Korean Cafe display name (2026-10-31, Asia/Seoul)

- The user requested the Korean edition-1 display name "카페&디저트" instead
  of "뉴 카페" in Joseon_deluxe.ow. Updated five display strings: selection,
  practice Other Menu, integration notice, player entry and scoreboard.
- The original New Cafe source identity, edition index 1, recipes, logic and
  the other Deluxe runtimes remain unchanged. Updated the display regression
  check and current runtime hashes. The user subsequently requested committing
  and pushing this follow-up on 2026-10-31; unrelated local work is excluded.

## Initialization yields (2026-10-31, Asia/Seoul)

- Following a temporary hold, the user explicitly requested adding initialization
  waits to the port and pushing. Scope is Joseon only; KR/EN/JP are inspection-only.
- The user then requested original-compatible loop timing. Removed the proposed
  mixing batches, extra stock/customer loop waits and dedicated counter before
  any commit. Original checkingIndex and all repeated-loop behavior are retained.
- Restored 30 Wait(0.100, Ignore Condition) statements only in the four active
  table init rules: N3 follows original GC (8/6); Cafe follows original CAFE
  (10/6). No extra wait follows the repeated part-2 lookup setup.
- The numeric lookup already precedes metadata in the port. The original two
  score/lookup boundary waits therefore sit consecutively after ITEM_SCORE,
  before CUTTING_NEEDED, matching the retained GC port's existing convention.
  Table data and assignment order are not moved to copy the original layout.
- Dispatcher, stock/customer loops, declarations and retained GC init rules
  are byte-identical to the pre-change runtime.
- Data, score representation, recipes, stage tables, site-only hints, readiness
  gate and the practice tutorial's menu-0 lock are unchanged. No claim is made
  that the separately reported original-Deluxe startup fault is fixed.
- Added original-wait parity and readiness tests; game import, multi-player timing
  and actual server-load validation remain external checks.

## Remove third-edition data (2026-11-01, Asia/Seoul)

- The user requested removing the deferred third edition's arrays as well.
  Removed Deluxe GC init1/2/3, including all metadata, cooking, recipe, menu,
  ingredient, stock and stage arrays inside those rules. Removed unused
  subroutine declarations 34..36 without renumbering any retained identifier.
- This supersedes the earlier requirement to retain dormant GC rules/data.
  Historical immutable inputs, mapping snapshots and audit results remain
  archival records; they are not included in the authoritative runtime.
- N3/Cafe init rules, common runtime and data, shared water, all six modes,
  original-compatible waits and practice tutorial menu-0 lock are unchanged.
  KR/EN/JP Deluxe and legacy files are not modified.
- Updated removal regression tests, read-only audit, manifest and workspace
  guidance. Runtime version is v261101. The user subsequently authorized
  committing and pushing this removal on 2026-11-01; unrelated work is excluded.

## Original-style table compression (2026-11-01, Asia/Seoul)

- The user reported 33,715 Workshop elements and requested the original Deluxe
  compression pattern. Read current Joseon data only; did not regenerate the
  runtime from a historical builder or edit KR/EN/JP or immutable inputs.
- Changed 14 table expressions across the four active init1/2 rules. Scalar
  CUTTING_RESULT/ADDITIONAL_MATERIAL_LIST values use slash-separated Custom String
  chains, String Split and Index Of Array Value(Global.MIXING_RECIPE, ...).
  Nested outputs/material groups are restored with per-index Array assignments.
  Base False entries decode to numeric zero, following original Deluxe encoding.
- RAW_MIX first/second item codes are independently compressed and reconstructed
  using first * 1000 + second before the final RAW_RESULT assignment. Recipe
  orientation, order and duplicates are preserved. No oversized mixed-code lookup
  was introduced; every component fits the existing 0..699 lookup.
- MENU_LIST/HAZARD_MENU_LIST/FRIDGE_LIST/WEAVER_MENU_LIST use slash-separated rows
  and comma-separated codes, decoded with the original checkingIndex loop pattern.
  No new variables, Wait actions or batching were added. ITEM_SCORE retains raw
  0..9 times 5; active editions, water and tutorial menu-0 lock remain unchanged.
- Every decoded table matches its pre-compression value. Static regression suite
  has 27 passing tests, including compression structure/nested overrides and
  90-character string limits. Full data/reachability/stage audit passes.
- Read-only estimate_compression_elements.py compares the changed rules against
  commit 2716010 using the published element-cost model. Estimated saving is
  4,360; projected total is 29,355 only if the user's 33,715 baseline matches that
  commit. This is not a Workshop import, actual element count or load test.
- The user subsequently requested committing and pushing the completed
  compression change on 2026-11-01; unrelated site/analysis/temp work is excluded.

## Workshop publication code and KR menu link (2026-11-01, Asia/Seoul)

- User reported saving the Workshop as PG261. Record the edition name as
  레스토랑 - 헬JOSEON, but use only 헬JOSEON for the KR Other Menu label/message,
  following the user's later clarification.
- Restore Joseon game branding to 레스토랑(PG261), replace the unresolved code,
  and restore the original update-warning pattern with PG261.
- Insert the new external entry after GC (index 3). Retain SSZ1Z1/8MAAN at
  indexes 4/5, cycle modulo 6 and preserve internal dispatch threshold 2.
- KR edit-date labels are v261101. No recipes, score data, initialization waits,
  edition dispatch, tutorial text or practice tutorial menu-0 lock are changed.
- This amendment has no commit/push request; prior publication approvals apply
  only to the previously completed changes.
- The user subsequently requested pushing this amendment on 2026-11-01.
  Commit/push its two runtime files, focused regression test and four artifact
  records only; exclude unrelated site/audit work and temporary files.
