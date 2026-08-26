# gc_kr.txt Fresh Port Plan

## Objective

Prepare a fresh port plan for `gc_kr.txt` using the `ko.txt -> cafe_kr.txt` port-analysis artifacts and the current `cafe_kr.txt` result as reference patterns.

Do not use the older `20260531_gc_kr_patch_followups` artifact as source of truth. That artifact can be treated only as historical context; this task should re-analyze the current files and produce a new plan.

Primary artifact references for this fresh plan:

- `.codex/artifact/20260420_ko_cafe_diff_baseline/walkthrough.md`
- `.codex/artifact/20260420_cafe_kr_head_port_plan/implementation_plan.md`
- `.codex/artifact/20260420_cafe_kr_head_port_plan/item_code_inventory.md`

The April `ko -> cafe_kr` documents are especially important because they describe how to port current `ko.txt` shared features into a variant whose item IDs, stage data, and identity differ from the original restaurant build.

The `cafe_en` translation overlay artifact is intentionally not a source for this task. `gc_kr.txt` is a Korean gameplay variant, so English translation overlay mechanics are irrelevant here.

The goal is to update `gc_kr.txt` to the latest shared game systems while preserving Cook International / Global Cuisine-specific data and surface identity.

## Current File State

Observed on 2026-06-03:

- `gc_kr.txt` is still a `레스토랑(P6ZAA) v260212` build.
- It has 4 score/mode slots:
  - `연습 모드`
  - `없음`
  - `없음`
  - `없음`
- It still uses a 14-table model:
  - `Global.tableOrderCode = Array(... 14 entries ...)`
  - `Global.TABLE_POSITION` has 14 positions.
- It does not currently include the newer shared subroutines:
  - `gameSummaryTP`
  - `validateServe`
  - `changeHero`
  - `stageFail`
- It does not currently include the newer customer heroes:
  - `Hero(Jetpack Cat)`
  - `Hero(Junker Queen)`
  - current `Reinhardt` references are UI/control related, not the fully ported newer customer handling.
- It has no cafe-only systems:
  - no `ICE_NEEDED`
  - no `ICE_RESULT`
  - no `제빙기`
  - no `냉각총`
- It has GC station text:
  - `튀김기`
  - `솥`
  - `그릴`
  - `팬`

## Primary Strategy

Use the April `ko.txt -> cafe_kr.txt` artifact lessons as the main porting model:

- port current `ko.txt` shared behavior by feature group, not line-by-line.
- preserve variant item IDs, content arrays, and identity.
- remap touched item literals by semantic role.
- treat `CUSTOMER_LIST` / customer-wave scaffolding as more portable than `STAGE_CODE`.
- do not invent new variant `STAGE_CODE`; leave TODOs if user-owned design data is required.
- compare final structure with protected blocks masked, but without any English translation overlay concerns.

Execution model:

1. Back up the current target file into the artifact.
2. Pick a latest-logic source.
3. Override or reconstruct the target from the latest shared structure.
4. Restore preserved target-specific blocks.
5. Apply only verified structural/data substitutions.
6. Generate unresolved/diff lists before manual fixes.
7. Verify by normalized logic comparison with intentional GC exceptions masked.

For `gc_kr.txt`, this means:

- Use current `ko.txt` as the best source for shared restaurant systems and non-cafe station behavior.
- Use current `cafe_kr.txt` as the best reference for how the April `ko -> variant` port lessons were eventually resolved in a cafe-like item-index variant and for post-port follow-up fixes.
- Use current `gc_kr.txt` as the source of truth for Cook International data, item indexes, stage/menu data, visible identity, and station naming.

## Why This Is Not a Direct ko.txt Copy

Functionally, `gc_kr.txt` is close to `ko.txt`, but its data/index layout is not interchangeable with `ko.txt`.

Observed item/data differences:

- Parsed `ITEM_NAME` count:
  - `gc_kr.txt`: 463
  - `ko.txt`: 476
  - `cafe_kr.txt`: 399
- `gc_kr.txt` uses cafe-like early utility indexes:
  - knives and utility items are at low IDs.
  - `Global.KNIFE = Array(1, 6, 2, 3, 4, 5, 7)`
  - `Global.PERK_LIST = Array(Array(8, 9, 11, 12, 15, 16, 17), Array(10, 13, 14))`
- `ko.txt` uses much later utility IDs such as `352`, `357`, `361`, `433`, and `434`.

Therefore, any direct item code copied from `ko.txt` can silently break `gc_kr.txt`.

This is the same class of problem recorded in the April `ko -> cafe_kr` artifact:

- shared system behavior can be ported.
- raw item IDs cannot be ported.
- `STAGE_CODE` and menu graph data cannot be copied mechanically.
- direct `createItemData` literals require an explicit semantic remap table.

## Why This Is Not a Direct cafe_kr.txt Copy

Structurally, current `cafe_kr.txt` is a very useful latest-system baseline, but it contains cafe-only systems that must not be introduced into `gc_kr.txt`.

Do not port:

- `ICE_NEEDED`
- `ICE_RESULT`
- ice-machine cooking flow
- cooling-gun item/perk behavior
- `제빙기`
- `냉각총`
- cafe item arrays, recipes, menu arrays, stage names, or fridge lists
- cafe station labels such as `튀김기&제빙기`

Keep GC station naming:

- `튀김기`
- `솥`
- `그릴`
- `팬`

## Data Blocks To Preserve From gc_kr.txt

Treat these as protected blocks unless a later count/structure audit proves a targeted edit is required:

- `Global.ITEM_NAME`
- `Global.ITEM_COLOR`
- `Global.ITEM_SCORE`
- `Global.RAW_MIX`
- `Global.RAW_RESULT`
- `Global.POT_TIME`
- `Global.POT_RESULT`
- `Global.PAN_NEEDED`
- `Global.PAN_RESULT`
- `Global.MENU_LIST`
- `Global.HAZARD_MENU_LIST`
- `Global.FRIDGE_LIST`
- `Global.ADDITIONAL_MATERIAL_LIST`
- `Global.WEAVER_MENU_LIST`
- `Global.STAGE_NAME`
- `Global.UPGRADE_CODE`
- `Global.KNIFE`
- `Global.PERK_LIST`
- `Global.KNIFE_AMOUNT`
- `Global.KNIFE_DECREASE`

`STAGE_CODE` must be treated as user-owned GC design data, not copied from `ko.txt` or `cafe_kr.txt`.

- If the six-mode scaffold requires two new mode entries and there is no verified GC design for them, write explicit TODO placeholders rather than inventing final stage-code arrays.
- This follows the April `cafe_kr` plan, which warned that variant menu graphs differ even when `CUSTOMER_LIST` can follow the shared wave pattern.

## Identity And Text To Preserve

Keep `gc_kr.txt` as the Cook International / Global Cuisine version:

- main workshop code: `P6ZAA`
- title wording: `레스토랑 - 쿡제요리` or equivalent existing GC wording
- recipe/book URL should remain GC-specific if present.
- cross-version code menu should remain intentional; do not blindly copy cafe or original restaurant code text.
- station labels must stay GC-appropriate:
  - `그릴`, not cafe `오븐` unless the surrounding GC text already intentionally uses `오븐`.
  - no `제빙기`.
  - no `냉각총`.

## High-Risk Areas

- `Global.totalScore`
  - expand to six mode entries.
  - do not copy unrelated high-score records from `ko.txt` or `cafe_kr.txt`.
  - add new slots as `Array(0, Custom String("없음"))` unless a GC-specific record is already known.
- mode arrays:
  - HUD color arrays
  - `Global.difficulty`
  - `Global.storageLevel`
  - `Global.stageTime`
  - `Global.failEnd`
  - mode rotation currently `% 4`, must become six-mode logic.
- table/customer model:
  - 14-table model must become latest 19-table system if matching current shared logic.
  - port Jetpack Cat / Reinhardt / Junker Queen behavior.
  - update `TABLE_PATH`, `TABLE_POSITION`, `tableOrderCode`, customer spawn ranges, serving-ball paths, and result scoreboard TP together.
- practice mode:
  - `gc_kr.txt` does not have `hintText` tutorial logic and should not receive it blindly.
  - compare with Cafe's non-tutorial practice handling rather than `ko.txt` tutorial handling.
  - verify direct `CUSTOMER_LIST` writes after tutorial index removal.
- item/perk indexes:
  - utility IDs must be role-remapped, not raw-copied.
  - no cafe cooling-gun perk index.
  - no original restaurant high item IDs for utility perks.
- additional material logic:
  - preserve GC-specific semantics.
  - compare current `gc_kr`, `ko`, and `cafe_kr` before simplifying.
  - do not import cafe-only removals unless they are clearly shared bug fixes.

## Concrete Plan From `ko -> cafe_kr` Precedent

The April `ko -> cafe_kr` artifacts split the port into feature groups and variant-owned data. Apply the same split to `gc_kr.txt`.

### A. Port As Shared Structure

These are shared system features from current `ko.txt` and should be ported into `gc_kr.txt`, with GC item/data remaps where needed:

- 19-table/customer-path model.
  - expand `Global.tableOrderCode` from 14 to 19 slots.
  - update `Global.TABLE_PATH`.
  - update `Global.TABLE_POSITION`.
  - update helper route offsets, especially old `+15` patterns that become `+20`.
  - update customer spawn ranges and delivery-lane routing.
- New customer feature set.
  - `Hero(Jetpack Cat)`
  - `Hero(Reinhardt)`
  - `Hero(Junker Queen)`
  - reserved order behavior and special table ranges.
  - Reinhardt multi-serve / order-count behavior.
  - Junker Queen serve-fail disruption behavior.
  - Jetpack Cat movement/spawn handling and double-jump exception.
- Shared subroutine extraction.
  - add `validateServe`.
  - add `changeHero`.
  - add `stageFail`.
  - add/use `gameSummaryTP` if not already present.
  - replace older inline serve validation, hero change, stage fail, and scoreboard teleport duplication.
- Six-mode scaffold.
  - mode labels and descriptions.
  - mode color arrays.
  - `Global.totalScore` six entries.
  - `Global.difficulty`.
  - `Global.storageLevel`.
  - `Global.stageTime`.
  - `Global.failEnd`.
  - host mode rotation from `% 4` to six-mode logic.
  - rating threshold checks from old `stageMode == 3` style to current challenge-mode logic.
- Practice-mode structure, but without tutorial.
  - use non-tutorial practice handling similar to Cafe, not `ko.txt` tutorial/hintText handling.
  - preserve direct practice `CUSTOMER_LIST` index assumptions after removing tutorial mode.
  - include newer practice customer injection behavior only after verifying indexes.

### B. Preserve From `gc_kr.txt`

These are GC-owned and should not be copied from `ko.txt` or `cafe_kr.txt`:

- `Global.ITEM_NAME`
- `Global.ITEM_COLOR`
- `Global.ITEM_SCORE`
- recipe/result arrays.
- `Global.MENU_LIST`
- `Global.HAZARD_MENU_LIST`
- `Global.FRIDGE_LIST`
- `Global.ADDITIONAL_MATERIAL_LIST`
- `Global.WEAVER_MENU_LIST`
- `Global.STAGE_NAME`
- `Global.UPGRADE_CODE`
- `Global.KNIFE`
- `Global.PERK_LIST`
- `Global.KNIFE_AMOUNT`
- `Global.KNIFE_DECREASE`
- GC station labels:
  - `튀김기`
  - `솥`
  - `그릴`
  - `팬`
- GC identity:
  - `P6ZAA`
  - `레스토랑 - 쿡제요리`
  - GC cross-version code references.

### C. Leave As TODO Instead Of Inventing

The `ko -> cafe_kr` plan explicitly warned not to invent variant `STAGE_CODE`. Apply the same rule to GC:

- Do not copy `ko.txt` `Global.STAGE_CODE`.
- Do not copy `cafe_kr.txt` `Global.STAGE_CODE`.
- Preserve existing GC stage-code data for existing modes.
- For any required new six-mode entries that do not have confirmed GC design values, insert explicit TODO placeholders for the user.
- Record every TODO stage-code slot in the artifact.

### D. Build A GC Item-Code Remap Table

The April cafe inventory showed that direct literals must be mapped by role, not number. For GC, start from the current file's utility layout:

- `1`: mass-produced knife
- `2`: carbon steel knife
- `3`: portable knife
- `4`: sharp knife
- `5`: Genji dagger
- `6`: premium kitchen knife
- `7`: head chef knife
- `8`: energy drink
- `9`: suspicious drink
- `10`: jump boots
- `11`: seasoning pack
- `12`: cleaner
- `13`: dash boots
- `14`: teleport spell
- `15`: cooking copy spell
- `16`: torch
- `17`: serving ball
- `18`: `$100`

Initial role mapping from `ko.txt` shared logic to GC:

- `ko 357` cleaner -> `gc 12`
- `ko 434` serving ball -> `gc 17`
- `ko 361` torch -> `gc 16`
- `ko 358` dash boots -> `gc 13`
- `ko 360` cooking copy spell -> `gc 15`
- `ko 359` teleport spell -> `gc 14`
- `ko 63` portable knife -> `gc 3`
- `ko 354` head chef knife -> `gc 7`
- `ko 432` tip / money item -> `gc 18`
- `ko Random Integer(62, 65)` ordered standard knives -> `gc Random Integer(2, 5)`

Every touched `Global.createItemData = Array(..., <item>, ...)` line must be categorized before editing:

- shared structural item literal requiring remap.
- existing GC literal to preserve.
- array-driven value already safe through `Global.KNIFE`, `Global.PERK_LIST`, or `Global.UPGRADE_CODE`.
- food/material literal that belongs to protected GC data and must not be copied from another file.

### E. Remove Or Block Variant-Incompatible Imports

From `cafe_kr.txt`, do not import:

- `ICE_NEEDED`.
- `ICE_RESULT`.
- ice-machine processing branches.
- cooling-gun perk branches.
- item `351` as cafe cooling-gun/tool behavior.
- `튀김기&제빙기` UI.
- `제빙기` world text.
- `냉각총` text/item behavior.

From `ko.txt`, do not import:

- `hintText`.
- tutorial settings or tutorial stage logic.
- raw high utility IDs such as `352`, `357`, `361`, `433`, `434`.
- original restaurant `ITEM_NAME`, recipe, menu, fridge, or stage-name data.

### F. Verification Mirroring The Cafe Plan

Before finalizing a port, create artifact reports equivalent to the cafe preparation:

- protected block inventory with counts and line ranges.
- direct item literal remap table.
- structural feature checklist.
- unresolved TODO list for `STAGE_CODE`.
- forbidden-import scan:
  - `ICE_NEEDED`
  - `ICE_RESULT`
  - `제빙기`
  - `냉각총`
  - `튀김기&제빙기`
  - `hintText`
  - raw `ko` utility IDs in create-item or shop paths.
- normalized logic comparison against the chosen skeleton, with GC-protected blocks masked.

## Proposed Workflow

1. Back up current files into this artifact.
   - `gc_kr.before_port.txt`
   - `ko.logic_reference.txt`
   - `cafe_kr.patch_reference.txt`
   - current `git status`

2. Build a block inventory.
   - Parse and count protected GC arrays.
   - Record line ranges for all protected blocks.
   - Record key utility IDs and role mappings.

3. Build the feature-group diff map from the April precedent.
   - Map each `ko -> cafe_kr` feature group to one of:
     - `PORT_SHARED`
     - `PORT_WITH_GC_REMAP`
     - `PRESERVE_GC`
     - `TODO_USER_DATA`
     - `REJECT_CAFE_ONLY`
     - `REJECT_KO_TUTORIAL`
   - Save this as `feature_group_port_map.md`.

4. Build a direct item-literal inventory.
   - Scan all current and candidate `createItemData` sites.
   - Scan random tool/shoe/knife pools.
   - Scan `UPGRADE_CODE == ...` purchase branches.
   - Save this as `gc_item_remap_inventory.md`.

5. Build a latest-structure skeleton.
   - Start from feature groups identified in the April `ko -> cafe_kr` walkthrough:
     - 19-table/customer path model
     - `Jetpack Cat`, `Reinhardt`, `Junker Queen`
     - `validateServe`, `changeHero`, `stageFail`
     - 6-mode scaffold
     - stage-fail and scoreboard flow
   - Use current `ko.txt` for non-cafe shared logic where GC has no custom alternative.
   - Use current `cafe_kr.txt` to cross-check follow-up fixes and variant-index handling.
   - Replace or omit cafe-only systems with `ko.txt` / existing `gc_kr.txt` equivalents.
   - Preserve GC data blocks from the backup.

6. Restore GC identity.
   - `P6ZAA`
   - GC title/version wording.
   - GC station labels.
   - GC cross-version code text.

7. Restore or remap item-index-sensitive logic.
   - starting items
   - practice random generation
   - merchant knife delivery
   - upgrade shop pools
   - perk drop/re-drop
   - serving-ball support
   - tip/money item

8. Generate unresolved review lists before final edits.
   - cafe-only references still present
   - ko-only tutorial references accidentally introduced
   - direct item literals not in the approved GC utility map
   - protected block count changes
   - text strings that changed substantially from current `gc_kr`
   - `STAGE_CODE` entries that require user-authored GC design values

9. Final verification.
   - `rg "v260212"` should return none after actual port.
   - no `ICE_NEEDED`, `ICE_RESULT`, `제빙기`, `냉각총`, or cafe `튀김기&제빙기`.
   - no `hintText` tutorial path unless explicitly approved.
   - `gameSummaryTP`, `validateServe`, `changeHero`, and `stageFail` present and wired.
   - `Hero(Jetpack Cat)`, `Hero(Reinhardt)`, and `Hero(Junker Queen)` present where expected.
   - six mode labels and six high-score slots.
   - normalized logic comparison against the chosen latest skeleton, with protected GC blocks masked.

## Initial Todo

- [ ] Back up current `gc_kr.txt`.
- [ ] Extract protected block ranges and counts.
- [ ] Build GC utility item map from current file.
- [ ] Decide whether the implementation skeleton should start from `cafe_kr.txt` with cafe-only removal, or from `ko.txt` with GC data overlay.
- [ ] Build a feature-group diff map based on `.codex/artifact/20260420_ko_cafe_diff_baseline/walkthrough.md`.
- [ ] Draft a concrete remap table for every direct utility item literal.
- [ ] Identify all `STAGE_CODE` changes that must become TODO placeholders instead of inferred data.
- [ ] Produce a pre-edit diff map before modifying `gc_kr.txt`.
- [ ] Only then begin the actual port.
