# gc_kr.txt Patch Implementation Plan

Date: 2026-05-31

Target file: `gc_kr.txt`

Goal: apply the same broad system patch now present in `cafe_kr.txt`, while treating `gc_kr.txt` as the Cook International / `P6ZAA` version and preserving its own recipe, menu, ingredient, and item-index data.

## Current Baseline

- `gc_kr.txt` is currently `레스토랑(P6ZAA) v260212`.
- The file is closer to the original `ko.txt` station model than the cafe variant:
  - no cafe-only ice-machine / cooling-gun station layer
  - uses fryer, pot, grill/oven naming, and pan style closer to original restaurant
  - no `ICE_NEEDED` / `ICE_RESULT` variables
- The file already has cafe-like item ordering in the sense that gameplay utility items occupy early item indexes before most food materials.
- `dataInit2` is `gc_kr`-owned data and must not be replaced with `ko.txt` or `cafe_kr.txt` data.

## Primary Sources

- Use `ko.txt` as the main source for shared system structure:
  - 6 `stageMode` scaffold
  - `gameSummaryTP`
  - `validateServe`
  - `stageFail`
  - `changeHero`
  - Jetpack Cat / Reinhardt / Junker Queen customer behavior
  - 19-table customer path model
- Use `cafe_kr.txt` as the source for follow-up bug fixes discovered during manual testing:
  - version-date handling
  - scoreboard TP consolidation
  - practice-mode text and non-tutorial treatment
  - Jetpack Cat jump exception
  - practice `CUSTOMER_LIST` index caution after tutorial removal
  - additional-material logic review
- Preserve `gc_kr.txt` as the source for:
  - `ITEM_NAME`
  - `ITEM_COLOR`
  - `ITEM_SCORE`
  - recipe/result tables
  - `MENU_LIST`
  - `HAZARD_MENU_LIST`
  - `FRIDGE_LIST`
  - `ADDITIONAL_MATERIAL_LIST`
  - `WEAVER_MENU_LIST`
  - `STAGE_NAME`
  - item, knife, perk, upgrade indexes

## Version Rule

Because this project uses edit-date versions, every visible `vYYMMDD` occurrence in `gc_kr.txt` must become `v260531` when the file is modified.

## Planned Changes

### 1. Shared Subroutines

Add and wire the newer subroutine structure:

- `gameSummaryTP`
- `validateServe`
- `changeHero`
- `stageFail`

Expected edits:

- add subroutine IDs after the existing `serveFail` path
- extract or port the corresponding rules from `ko.txt`
- replace inline repeated failure logic in `startStage` with `Call Subroutine(stageFail)`
- replace duplicated scoreboard teleport blocks with `Call Subroutine(gameSummaryTP)`

### 2. Six-Mode Scaffold

Expand `stageMode` from 4 modes to 6 modes:

- practice
- casual dining
- fine dining
- star bistro
- mastercook challenge
- head chef challenge

Expected edits:

- HUD labels and descriptions
- HUD color arrays
- `Global.totalScore`
- `Global.difficulty`
- `Global.storageLevel`
- `Global.stageTime`
- `Global.failEnd`
- mode rotation `% 6`
- rating thresholds using challenge-mode logic
- bonus-stage condition from `stageMode == 3` to the new mastercook index

### 3. Cook International Data Preservation

Do not overwrite these `gc_kr` arrays with restaurant or cafe values:

- `RAW_MIX`
- `RAW_RESULT`
- `POT_TIME`
- `POT_RESULT`
- `PAN_NEEDED`
- `PAN_RESULT`
- `MENU_LIST`
- `HAZARD_MENU_LIST`
- `FRIDGE_LIST`
- `ADDITIONAL_MATERIAL_LIST`
- `WEAVER_MENU_LIST`
- `STAGE_NAME`

When structure around these arrays changes, copy only the control flow and keep the actual `gc_kr` numbers.

### 4. Item Index Caution

`gc_kr.txt` has custom item indexes. Any touched literal item code must be checked semantically.

Known sensitive areas:

- starting items
- practice random item generation
- ordered knife delivery
- upgrade shop pools
- perk drop / re-drop
- serving-ball perk
- tip item / money item
- any branch using direct `itemPerk == n`
- any `Global.createItemData = Array(..., <item>, ...)` copied from `ko.txt`

The patch should not blindly copy food item IDs from `ko.txt` or `cafe_kr.txt`.

### 5. Customer And Table Model

Port the newer shared customer system:

- add `Jetpack Cat`
- add `Reinhardt`
- add `Junker Queen`
- expand `tableOrderCode`, `TABLE_PATH`, `TABLE_POSITION`
- update merchant fallback path indexes
- update serveBot path offsets
- update customer spawn ranges and special table ranges
- update customer score/order/time/by-order arrays
- update special failure and success branches

### 6. Practice Mode

`gc_kr.txt` does not have the `ko.txt` tutorial / `hintText` path, and the patch should not add it.

Expected handling:

- keep practice mode non-tutorial
- do not introduce `hintText` tutorial logic
- review current practice stage indexes before applying `ko.txt` logic
- keep the "other version code" menu intentionally pointing to different workshop versions
- because this file is Cook International, showing `변기클라우드-모듬회밥` as an external code target is valid

### 7. Additional Material Logic

This file is not cafe, so the cafe-only removal of all stage logic must not be copied blindly.

Review target behavior:

- LifeWeaver should create additional materials for LifeWeaver orders.
- If Cook International intentionally has menu/stage-specific additional materials, keep those semantics.
- Remove only logic that is demonstrably stale or belongs to another version.
- Compare with current `ko.txt` before changing:
  - customer-side spawn
  - reserved-customer central spawn
  - despawn slowdown
  - table throttling

### 8. Follow-Up Fixes To Recheck

Carry forward the lessons from `cafe_kr.txt`:

- update `v260212` to `v260531`
- avoid changing existing cross-version code text unless this version should advertise a different target
- add Jetpack Cat double-jump exception when Jetpack Cat behavior is introduced
- ensure practice `CUSTOMER_LIST` direct writes use the right indexes for this file's non-tutorial practice layout
- do not import cafe-specific cooling gun / ice-machine assumptions
- avoid accidental regression of `gc_kr` food and material arrays

## Static Verification Plan

After edits, run text checks for:

- stale `v260212`
- stale `% 4` mode rotation
- stale 4-entry `stageMode` arrays
- missing `gameSummaryTP`
- missing `validateServe`
- missing `stageFail`
- missing `changeHero`
- missing `Hero(Jetpack Cat)`
- missing `Hero(Reinhardt)`
- missing `Hero(Junker Queen)`
- missing Jetpack Cat exception in `Player: Double Jump`
- unintended replacement of `gc_kr` menu names
- unintended cafe-only terms such as ice-machine/cooling-gun station wording

No in-game Workshop runtime test can be performed from this environment.
