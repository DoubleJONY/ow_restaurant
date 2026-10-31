# Joseon Deluxe validation

Date: 2026-11-01 (Asia/Seoul)
Runtime: root Joseon_deluxe.ow, v261101.
Baseline: 7cea33b52bff2768373adb7c2e89f5e70544291c.
Status: implementation and static verification complete. In-game checks remain pending; the user authorized commit/push of third-edition data removal on 2026-11-01.

## Current third-edition removal (2026-11-01)

- Deleted GC init1/2/3 and their arrays from the authoritative runtime; removed
  unused subroutine declarations 34..36 without renumbering retained IDs.
- Both active edition data sets and common rules are unchanged. This supersedes
  all historical retained-placeholder statements below. The original GC init
  rules in kr_deluxe.ow remain valid references for N3's wait/stock-loop tests;
  they are not Joseon runtime data.
- Historical input/mapping/audit snapshots are intentionally retained as archive
  artifacts, not as runtime or generation inputs.
- Verified all six active init rules byte-for-byte against the previous commit;
  all decoded active tables are identical. Runtime diff permits only the three
  GC rules/declarations and edit-date labels; the source shrank by 41,300 bytes.
- Unit suite: 24 tests passed. Removal audit, all 26 active themes' ingredient
  reachability, 12 edition/mode combinations with 500 seeds each, six root syntax
  checks and git diff --check passed. Original Deluxe and legacy bytes match HEAD.
  Workshop import/actual element counts/in-game behavior remain unverified.

## Current initialization yields (2026-10-31)

- Restored 30 table-level 0.100-second waits: N3 follows original GC (8/6 in
  init1/2); Cafe follows original CAFE (10/6). The relocated lookup's original
  wait is adjacent to the score wait, as in the retained GC port. No table
  assignments were moved. Repeated-loop timing and counters match the original:
  no mixing batches, extra stock/customer waits or new variables remain.
- All decoded data and ordering, retained GC rules, tutorials, six-mode stage
  tables and practice menu-0 lock remain unchanged. stageTime is still assigned
  only after full initialization; no early readiness signal was introduced.
- Static unit suite: 24 tests passed. Full port audit: no unreachable orders
  across 26 active themes; 12 edition/mode combinations at 500 seeds each pass.
  Root syntax checks passed six files. In-game load/timing is not verified.
- The earlier sections below describe completed historical amendments; current
  initialization scheduling supersedes their unchanged-init-rule statements.

## Two-edition amendment (2026-10-31)

- Active editions are 0 (New Branch 3) and 1 (New Cafe). Edition 2 is deferred,
  not deleted. This supersedes historical statements below that it is selectable.
- Startup selection cycles modulo 2. Practice Other Menu cycles modulo 4 with
  N3, Cafe, external SPXXM and external 8MAAN, in that order. Only indexes 0..1
  enter dataInit; external indexes 2..3 have matching labels and codes.
- Removed all four GC init calls from the dispatcher and difficulty-up path.
  Retained GC declarations and all three init rules. All nine edition-specific
  init rules (N3/Cafe/GC, parts 1..3) are byte-identical to the pre-amendment rules.
- Eight runtime rules changed: Global: Setting, Player: Spawn, Player: Reload
  button, Deluxe dispatcher dataInit, Start stage, Head Chefs: Select Mode,
  Scoreboard and Other Menu. Every other runtime rule is unchanged. KR/EN/JP
  Deluxe files were verified unchanged from the start of this amendment.
- Item IDs, recipes, menus, stage tables, fridge/additional supplies, raw-score
  initialization *5, water 21, freezing and oven behavior are unchanged. The
  preceding per-player spacer HUD and casual-shop exclusions are preserved.
- Site-only setHint is unchanged, as are practice entry's menu construction,
  normal-menu refill and all six game modes. On switching either active edition,
  dataInit precedes stage reset to 0 and menuInit; ICE/mixing tables are rebuilt.
  Tutorial guidance never overrides orders, regardless of the tutorial setting.
- Unit regression suite after the declaration-indent follow-up: 20 passed,
  including the cross-Deluxe indentation test and five Joseon tests for initial
  selection, dispatch, practice/internal/external targets, display lists and all
  edition assignment entry paths.
- Full port audit: both active source mappings passed; retained placeholder
  passed with 465 items and empty recipes; all 26 active themes had no unreachable
  normal/Hazard/Lifeweaver orders. Checked 12 active edition/mode combinations
  with 500 deterministic seeds each. The historical audit_result.json remains
  the original 18-combination snapshot, not the current active-selection report.
- Root syntax check: six files passed. git diff --check passed.
- Current runtime SHA-256 after third-edition removal: 18302ada9ab94154a7c2952ee524fbce246bc5f563b618028f698deb0bc9eebf.
- Workshop import, actual element budget and in-game smoke tests remain pending.
  No staging, commit or push was performed.

The following sections retain the original port verification history. Current
selection scope and runtime metadata are defined by the amendment above.

## Final layout

| Edition | Items | Themes | Mixed-recipe rows | Normal menu entries |
| --- | ---: | ---: | ---: | ---: |
| 0: New Branch 3 | 516 | 12 | 279 | 159 |
| 1: New Cafe | 522 | 14 | 335 | 202 |
| 2: retained placeholder | 465 | 12 | 0 | Retained original menus |

Common equipment codes 0..20 follow current Deluxe. Water is common code 21.
New Branch 3 mappings: old water 19 -> 21, old boiled water 20 -> 515,
old rice 21 -> 514. New Cafe mappings: old cooling gun 19 -> 20,
old water 20 -> 21, old boiled water 21 -> 521. Placeholder old gochujang
21 -> 464; other old food IDs retain their identities.

## Data verification

- Every migrated food record was parsed from the final .ow and compared against
  its source using the explicit mapping. Checked metadata, thresholds, result
  arrays (including multiple outputs), menu groups, ingredient supplies and
  both sides/results of every RAW_MIX row. Row order and duplicates are preserved
  except the three explicitly user-requested Cafe menu deduplications below.
- Common equipment metadata follows current Deluxe rather than legacy names.
  Water name, color and score are identical in all three edition layouts;
  water's cooking/freezing recipes remain edition-specific.
- All implemented-edition item tables have the correct item count, and every
  food/menu result code is in range. Equipment freezing results are neutral.
- Original kr_deluxe.ow matches its input snapshot byte-for-byte.
  Immutable inputs/n3_kr.ow and inputs/nc_kr.ow preserve the originals; root
  n3_kr.ow and deprecated/nc_kr.ow include user-approved corrections below. Manifest source
  hashes identify the immutable input snapshots.
- The snapshot's two malformed tab-prefixed zero tokens at original Cafe
  FRYING_RESULT indexes 374 and 482 resolved to -1. Both the edited legacy and
  the runtime now use their intended zero result. The user confirmed the
  original author intended raw score 4 at item 191 instead of ㅊ: edited legacy
  raw score is 4, runtime score is 20, and the workbook raw score is 4.
- Third-edition conversion outputs and RAW_MIX/RAW_RESULT are empty/neutral,
  including legacy per-index cutting overrides. Its stage/menu configuration
  remains present and selectable. It is intentionally not a playable edition.

## Runtime integration checks

- Water supply generates common code 21 directly in all three editions.
  No waterCode variable or edition gate remains. Source role limits and item-count
  limits remain in the pickup path. Sink disposal is an independent interaction.
- All three active tool pools, starter arrays, practice equipment and weighted
  purchase pools exclude preservation-box code 19. Cafe includes cooling gun 20;
  New Branch 3 and the placeholder do not. Shared rewards/merchant paths consume
  these edition-local pools. Box activation and its food-generation mapping
  were removed; the common slot remains reserved.
- Cafe cooling gun uses itemPerk 8, and freezing equipment is enabled only for
  Cafe. The migrated water recipe freezes into that edition's ice item.
- Classic's theme-11 ingredient injection, reservation supplies and customer cap
  were removed. Both variants retain Lifeweaver per-order extra ingredients.
  Classic-only melting behavior cannot affect New Branch 3 food codes.
- Data initialization resets ICE tables and rebuilds mixing arrays.
  Practice edition switching calls this same dispatcher before loading menus.
  Third-edition selection has no new block, fallback or warning.
- Site-only setHint changes hintText, never currentMenu/loadingMenu/currentCustomer.
  Tutorial on/off and practice entry preserve normal orders and refill data.
- New-map records initialize to zero/none; titles, mode/edition labels, credits,
  stage names and other-menu links refer to the new map/actual external targets.

## Reachability and stage checks

Checked all 26 implemented-edition themes. Starting from each theme's fridge
ingredients plus sink water, repeated cutting/impact/cooking/freezing and mixing
steps reach every normal and Hazard order. Lifeweaver orders were checked with
that specific order's additional ingredients. No unreachable orders were found.
This is a static existence check with replenishable ingredient supplies, not a
timed simulation or proof of every physical interaction.

Checked all 18 edition/mode combinations using 500 deterministic random seeds
per combination. Expected wave counts are practice 6, casual 15, fine 15,
bistro 15, master challenge 13 and head-chef challenge 20. Theme references stay
within their edition's theme count and stage entries are flat theme-ID groups.
New Cafe practice was expanded from 5 to 6 entries, and its challenge's two
nested randomized stage arrays were replaced by single random themes. New
Branch 3's missing six-mode arrangements use its own theme order and fusion
groups with Deluxe-compatible lengths.

audit_result.json records displayed stages, zero-based indexes and sampled theme
groups. Tutorial orders equal normal orders; there are no intentional tutorial
dish omissions. Tests for unaffected EN/JP tutorials were not needed because
those files were not edited.

## Commands and limits

```sh
python3 -B .codex/artifact/20261017_joseon_deluxe_port/audit_port.py
python3 -B scripts/check_ow_syntax.py '*.ow'
git diff --check
```

The audit passed. Syntax checks passed all six current root .ow files.
Whitespace checks passed, including the new runtime separately. New edition data
string segments are at most 90 characters. The largest rule is 37,457 UTF-8 bytes.
These source measurements do not establish Workshop's actual element count.

Pending external checks: import Joseon_deluxe.ow into Workshop, measure its
actual element budget, and play-test both implemented editions, water pickup,
freezing/oven behavior, equipment rewards and practice edition switching.
No in-game pass or game-import compatibility is claimed from static checks.

## Author-confirmed correction verification

- Legacy byte comparison permits only raw score 191 (ㅊ -> 4), two embedded
  tabs before zero, and the edit-date version v260613 -> v261017. CRLF and the
  original no-newline EOF are preserved. Immutable inputs/nc_kr.ow is unchanged.
- Runtime byte comparison permits only ITEM_SCORE[191] changing -5 -> 20.
- The updated workbook differs only at Cafe Q193 (ㅊ -> 4) and its score-source
  explanation; all other cell values and formulas are preserved. Full item
  tables, filters and frozen panes passed verification.
- The full port audit passed: data mappings, all 26 themes, no unreachable
  orders, and 18 edition/mode combinations with 500 random seeds each.
- Syntax passed all six root .ow files plus deprecated/nc_kr.ow; git diff
  --check passed. No in-game execution, staging, commit or push was performed.

## Menu deduplication and N3 score follow-up

- N3 raw score 46 (sliced sundae) and 111 (poached egg) changed from 0 to 3;
  Joseon runtime values are both 15. The two N3 version strings are v261017.
- Cafe theme 7 normal item 235, theme 3 Hazard item 114, and theme 3 Lifeweaver
  item 434 now appear once each. The first occurrence is retained and other
  entry order is unchanged. Normal/Hazard/Lifeweaver totals are 202/83/63.
- Verified original source edits and runtime edits against pre-change tables:
  only the two scores and three menu rows differ. Version metadata aside,
  no other source logic changed. Immutable inputs are preserved.
- Stage order, displayed stage indices, fridge supplies, additional supplies,
  tutorials, practice entry and normal-menu refill code are unchanged. Site-only
  Joseon guidance still cannot override currentMenu/loadingMenu; removing a
  repeated item does not omit any distinct dish from initial or refill cycles.
- Full static port audit passed all 26 themes with no unreachable orders and
  all 18 edition/mode combinations at 500 seeds each. Syntax passed all six root
  files and the edited legacy. In-game/timed behavior remains unverified.
- Workbook N3 O48/O113 now display raw score 3. Verified all 1,038 item rows,
  preserved every other cell value/formula, and visually checked both changed
  score ranges. No staging, commit or push was performed.

## Legacy metadata rollback verification

- By the user's explicit exception to edit-date versioning, n3_kr.ow retains
  v260827 at both labels and deprecated/nc_kr.ow retains v260613.
- With only approved data assignments excluded, each legacy file matches its
  original snapshot text exactly, including pre-existing patch descriptions.
- Scores and duplicate removal remain corrected; Joseon runtime and the item
  workbook were not edited. Manifest corrected-source hashes were refreshed.

## Score representation rollback verification

- All three Joseon ITEM_SCORE assignments use raw 0..9 strings with the original
  initialization-time *5 mapping. No score data contains pre-multiplied values.
- Compared all decoded tables before/after independently: N3 516, Cafe 522,
  placeholder 465 score entries and all other data are exactly equal.
- Only the three ITEM_SCORE assignment expressions differ in the runtime.
  N3 raw 46/111 = 3, Cafe raw 191 = 4, menu deduplication and all metadata remain.
- Existing kr/en/jp Deluxe files, both corrected legacy files and the workbook
  are unchanged. Manifest score corrections now also use raw units; audit code
  applies the same initialization multiplier for snapshot comparison.
- Re-ran the score-equivalence check, full port audit (26 themes, 18 mode/edition
  combinations, 500 seeds each), syntax checks on seven files and diff checks:
  all passed. The unchanged workbook matches all 1,038 item rows. No in-game
  execution, staging, commit or push was performed.
